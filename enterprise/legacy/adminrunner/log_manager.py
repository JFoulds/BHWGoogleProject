#!/usr/bin/python2.4
#
# Copyright 2002-2005 Google inc.
# cpopescu@google.com
# pn@google.com
#
# This contains code to run and coordinate the log processing operations
#
###############################################################################

import string
import os
import threading
import commands
import urllib
import re
import fnmatch
import time

from google3.pyglib import gfile
from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.logs import liblog
import tempfile

###############################################################################

true  = 1
false = 0

# Limit number of raw reports or summary reports. Adjust the numbers
# if they appears to be too low or too high.
MAX_REPORT_COUNT = { liblog.RAW_REPORT : 100,
                     liblog.SUMMARY_REPORT: 500
                    }

# A period of 180 minutes for system commands
COMMAND_TIMEOUT_PERIOD = 180 * 60

# State machine of report generation and report update.
#
#                \-------> gone! <--//
#             (cancel)         (delete)
#                 \                //
# UNKNOWN --> PENDING --> COMPLETE <---> COMPLETE_REGENERATE
#               ^                  /          |
#               |----> FAILURE >---/ <--------|
#
# report generation complete state
UNKNOWN  = '0'; # First initialized
PENDING  = '1'; # Report entry registered. Report is being generated.
COMPLETE = '2'; # Report completed.
COMPLETE_REGENERATE = '3'  # Non-final Complete report being regenerated
FAILURE  = '4'; # Last report generation failed. An update request move it
                # to PENDING state


###############################################################################
# This class represent a report form. Its serialized format should be idential
# to that of LogReportFormData.java.

class LogReport:
  def __init__(self, reportName, collection,
               reportType, creationDate,
               isFinal, reportDate, completeState,
               withResults, topCount, diagnosticTerms):
    self.reportName = reportName
    self.collection = collection
    self.reportType = reportType
    self.creationDate = creationDate
    self.isFinal = isFinal
    self.reportDate = reportDate
    self.completeState = completeState
    self.withResults = withResults
    self.topCount = topCount
    self.diagnosticTerms = diagnosticTerms

  def toString(self):
    return ('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %
            (urllib.quote(self.reportName),
             self.collection, self.reportType,
             self.creationDate, self.isFinal,
             self.reportDate, self.completeState,
             self.withResults,
             self.topCount, self.diagnosticTerms))

def StringToLogReportForm(line):
  (reportName, collection, reportType, creationDate,
   isFinal, reportDate, completeState, withResults,
   topCount, diagnosticTerms) = string.split(line, '\t', 9)
  return LogReport(urllib.unquote(reportName), collection,
                   reportType, creationDate, isFinal,
                   reportDate, completeState, withResults,
                   topCount, diagnosticTerms)

def ReportToString(report):
  return ('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %
          (urllib.quote(report.reportName), report.collection,
           report.reportType, report.creationDate, report.isFinal,
           report.reportDate, report.completeState, report.withResults,
           report.topCount, report.diagnosticTerms))


###############################################################################

class LogManager:

  def __init__(self, cfg):
    self.cfg = cfg    # configurator object
    self.entConfig = cfg.globalParams
    # locks for updating the report lists
    self.logreplock = threading.RLock()
    self.logdir = self.cfg.getGlobalParam('LOGDIR')
    liblog.MakeDir(liblog.get_click_dir(self.entConfig))
    liblog.MakeDir(liblog.get_collect_dir(self.entConfig))
    liblog.MakeDir(liblog.get_apache_dir(self.entConfig))
    liblog.MakeDir(liblog.get_partition_dir(self.entConfig))
    liblog.MakeGoogleDir(self.entConfig, liblog.get_report_dir(self.entConfig))
    collection_dir_map_file = liblog.get_directory_map_file(self.entConfig)

    if not os.path.exists(collection_dir_map_file):
      open(collection_dir_map_file, 'w').close()  # a trick to touch a file.
    self.reportCount = { liblog.RAW_REPORT:  0,
                         liblog.SUMMARY_REPORT: 0, }
    self.sanitizeReportList(liblog.RAW_REPORT)
    self.sanitizeReportList(liblog.SUMMARY_REPORT)

    self.joblock = threading.Lock()
    self.runningJobs = {}

  #############################################################################
  # Main methods provided to log_handler.

  def generateReport(self, reportForm):
    """Generate a new report."""
    self.logreplock.acquire()
    try:
      if self.hasReachedLimit(reportForm.reportType):
        return C.REPORT_LIST_TOO_MANY

      reports = self.getLogReports(reportForm.collection,
                                   reportForm.reportType)
      for report in reports:
        if reportForm.reportName == report.reportName:
          logging.error('Cannot generate new report with existing name %s' %
                        report.reportName)
          return C.REPORT_NAME_EXISTS
      ret = self.generateReportNolock(reportForm, update=false)
      if ret != C.REPORT_OK:
        return ret
      reports.append(reportForm)
      if not self.setLogReports(reportForm.reportType,
                                reportForm.collection, reports):
        logging.error('Failed to update report list.')
        return C.REPORT_INTERNAL_ERROR
      self.reportCount[reportForm.reportType] += 1
    finally:
      self.logreplock.release()
    return C.REPORT_OK

  def getReportForm(self, collection, reportType,
                    reportName):
    """Return a report form in serialized format.
    Or empty string if not found."""
    reports = self.getLogReports(collection, reportType)
    found = false
    for report in reports:
      if reportName == report.reportName:
        found = true
        break

    if not found:
      logging.error('Report not found.')
      return ''
    return report.toString()

  def updateReport(self, collection, reportType,
                   reportName, updateDate, isFinal):
    """Update an existing non-final complete report."""

    self.logreplock.acquire()

    try:
      reports = self.getLogReports(collection, reportType)
      found = false
      for report in reports:
        if reportName == report.reportName:
          if report.isFinal == 1:
            logging.error('Report %s is already final' % reportName)
            return C.REPORT_ALREADY_FINAL
          elif (report.completeState == PENDING or
                report.completeState == COMPLETE_REGENERATE):
            logging.error('Report %s is generating. Can\'t update' % reportName)
            return C.REPORT_INCOMPLETE
          found = true
          break

      if not found:
        logging.error('Report not found.')
        return C.REPORT_NOT_FOUND

      if report.completeState == FAILURE:
        report.completeState = PENDING
        report.creationDate = updateDate
        report.isFinal = isFinal
      elif report.completeState == COMPLETE:
        report.completeState = COMPLETE_REGENERATE
        report.creationDate = '%s|%s' % (report.creationDate,
                                         updateDate)
        report.isFinal = '%s|%s' % (report.isFinal, isFinal)

      if not self.setLogReports(report.reportType,
                                report.collection, reports):
        logging.error('Failed to update report list.')
        return C.REPORT_INTERNAL_ERROR

      ret = self.generateReportNolock(report, update=true)

      if ret != C.REPORT_OK:
        logging.error('Failed to regenerate report %s' % reportName)
        return ret
    finally:
      self.logreplock.release()
    return C.REPORT_OK

  def deleteReport(self, collection, reportType,
                   reportName, doCancel=false):
    """Delete a complete report or cancel a pending report."""

    self.logreplock.acquire()
    (html_file, valid_file) = liblog.get_report_filenames(self.entConfig,
                                      reportType, reportName, collection)
    try:
      found = false
      reportList = self.getLogReports(collection, reportType)
      for report in reportList:
        if reportName == report.reportName:
          found = true
          break
      if not found:
        logging.error('Report not found')
        return C.REPORT_NAME_NOT_FOUND

      if (doCancel and not (report.completeState == PENDING or
                            report.completeState == COMPLETE_REGENERATE)):
        # doCancel should apply for running report only.
        return C.REPORT_ALREADY_COMPLETE

      if (not doCancel and not (report.completeState == COMPLETE or
                                report.completeState == FAILURE)):
        # delete (doCancel==false) should apply for complete/failed report only.
        return C.REPORT_INCOMPLETE

      if doCancel:
        self.stopRunningJob(self.jobName(report))

      if report.completeState == COMPLETE_REGENERATE:
        # Just recover original state, don't delete the old report.
        report.completeState = COMPLETE
        report.isFinal = string.split(report.isFinal, '|')[0]
        report.creationDate = string.split(report.creationDate, '|')[0]
      else:
        self.reportCount[report.reportType] -= 1
        reportList.remove(report)
        self.RemoveReportFiles(html_file, valid_file)

      if not self.setLogReports(reportType, collection, reportList):
        logging.error('Failed to update report list.')
        return C.REPORT_INTERNAL_ERROR
    finally:
      self.logreplock.release()
    return C.REPORT_OK

  def getReport(self, collection, reportName):
    """Return body of a summary report."""
    self.logreplock.acquire()
    try:
      reports = self.getLogReports(collection, liblog.SUMMARY_REPORT)
      found = false
      incomplete = false
      for report in reports:
        if report.reportName == reportName:
          found = true
          if (report.completeState != COMPLETE and
              report.completeState != COMPLETE_REGENERATE):
            incomplete = true
          break

      if not found:
        logging.error('Report %s not found' % reportName)
        return (C.REPORT_NAME_NOT_FOUND, None, None)
      elif incomplete:
        logging.error('Report %s is incomplete' % reportName)
        return (C.REPORT_INCOMPLETE, report.toString(), None)

      (html_file, _) = liblog.get_report_filenames(self.entConfig,
                       liblog.SUMMARY_REPORT, reportName, collection)
      try:
        reportContents = gfile.GFile(html_file, 'r').read()
      except IOError:
        return (C.REPORT_INTERNAL_ERROR, report.toString(), None)

    finally:
      self.logreplock.release()
    return (C.REPORT_OK, report.toString(), reportContents)

  #############################################################################
  #  Internal helper functions

  def jobName(self, reportForm):
    """Return a unique name a report generation thread."""
    return '%s.%s.%s' % (reportForm.reportType,
                         urllib.quote(reportForm.collection),
                         urllib.quote(reportForm.reportName))

  def hasReachedLimit(self, reportType):
    """Return true if the system has reached the limit number of that
    type of report."""
    return self.reportCount[reportType] >= MAX_REPORT_COUNT[reportType]

  def RemoveReportFiles(self, html_file, valid_file):
    """Remove report and its valid file."""
    (err, out) = E.run_fileutil_command(self.entConfig, 'rm -f %s %s' % \
                                        (html_file, valid_file))
    if err:
      logging.error('Failed to remove report files: %s and %s' % \
                    (html_file, valid_file))

  def setReportCompleteState(self, reportType, collection,
                             reportName, completeState,
                             takeOldRecord=false):
    """This should be called by a worker thread to set complete state of
    report generation. If takeOldRecord is true, we restore the old
    creationDate and old isFinal for the report entry."""

    self.logreplock.acquire()
    try:
      reports = self.getLogReports(collection, reportType)
      found = false
      for i in range(len(reports)):
        if reports[i].reportName == reportName:
          if reports[i].completeState == COMPLETE_REGENERATE:
            if takeOldRecord:
              keptIdx = 0
            else:
              keptIdx = 1
            reports[i].isFinal = string.split(reports[i].isFinal, '|')[keptIdx]
            reports[i].creationDate = string.split(reports[i].creationDate,
                                                   '|')[keptIdx]
          reports[i].completeState = completeState
          found = true
          break

      if found:
        try:
          self.setLogReports(reportType, collection, reports)
        except IOError:
          logging.error('Fail to write report list.')
          return false
      else:
        logging.error('Cannot find the report % in %s' % (
          reportName, liblog.get_report_list_filename(self.entConfig,
                                                      reportType, collection)))
        return false
    finally:
      self.logreplock.release()
    return true

  def generateReportNolock(self, reportForm, update):
    """Generating report. Common code shared between generateReport()
    and updateReport()."""

    self.joblock.acquire()
    try:
      jobToken = time.time()
      self.runningJobs[self.jobName(reportForm)] = jobToken
      try:
        thread.sleep(1)  # a cheap way to make jobToken unique
      except:
        pass
    finally:
      self.joblock.release()

    if reportForm.reportType == liblog.RAW_REPORT:
      t = threading.Thread(target=self.doLogDump,
                           args=(self.jobName(reportForm),
                                 jobToken,
                                 reportForm.collection,
                                 reportForm.reportName,
                                 reportForm.reportDate,
                                 update))
    elif reportForm.reportType == liblog.SUMMARY_REPORT:
      t = threading.Thread(target=self.doLogReport,
                           args=(self.jobName(reportForm),
                                 jobToken,
                                 reportForm.collection,
                                 reportForm.reportName,
                                 reportForm.reportDate,
                                 reportForm.withResults,
                                 reportForm.topCount,
                                 reportForm.diagnosticTerms,
                                 update))
    else:
      logging.info('Unknown report type %s' % reportForm.reportType)
      return C.REPORT_INTERNAL_ERROR

    t.start()

    logging.info('Start thread to generate report, type = %s' %
                 reportForm.reportType)
    return C.REPORT_OK

  def doLogReport(self, jobName, jobToken, collection, reportName, reportDate,
                  withResults, topCount, diagnosticTerms, update):
    """The actual work done in a worker thread to generate a summary report."""

    (html_file, valid_file) = liblog.get_report_filenames(self.entConfig,
                    liblog.SUMMARY_REPORT, reportName, collection)
    liblog.MakeGoogleDir(self.entConfig, os.path.dirname(html_file))

    new_html_file = tempfile.mktemp('.report')
    new_valid_file = tempfile.mktemp('.report_valid')

    args = []
    args.append(commands.mkarg(self.entConfig.GetEntHome()))
    args.append(commands.mkarg(collection))
    args.append(commands.mkarg(reportDate))
    args.append(withResults)
    args.append(topCount)
    args.append(commands.mkarg(diagnosticTerms))
    args.append(commands.mkarg(html_file))
    args.append(commands.mkarg(valid_file))
    args.append(commands.mkarg(new_html_file))
    args.append(commands.mkarg(new_valid_file))

    cmd = ('. %s && cd %s/enterprise/legacy/logs && '
           'alarm %s nice -n 15 ./log_report.py %s' %
           (self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
            self.cfg.getGlobalParam('MAIN_GOOGLE3_DIR'),
            COMMAND_TIMEOUT_PERIOD, string.join(args, ' ')))
    logging.info('doLogReport(): CMD = %s' % cmd)
    returnCode = E.system(cmd)

    self.handleResult(jobName, jobToken, returnCode, liblog.SUMMARY_REPORT,
                      collection, reportName, update,
                      html_file, valid_file, new_html_file, new_valid_file)


  def doLogDump(self, jobName, jobToken, collection, reportName,
                reportDate, update):
    """The actual work done in a worker thread to generate a raw log report."""

    (html_file, valid_file) = liblog.get_report_filenames(self.entConfig,
                                 liblog.RAW_REPORT, reportName, collection)
    liblog.MakeGoogleDir(self.entConfig, os.path.dirname(html_file))

    # (TODO): Change this once the we move to python2.4 to use a safer call to
    # mkstemp which accepts the target directory name as an argument
    new_html_temp = tempfile.mktemp('.log')
    # create file in /export/hda3 instead of /tmp. The / partition is very
    # small compared to the /export/hda3
    new_html_file = '/export/hda3' + new_html_temp
    # need to perform a check about file existance
    while os.path.exists(new_html_file):
      new_html_temp = tempfile.mktemp('.log')
      new_html_file = '/export/hda3' + new_html_temp

    new_valid_file = tempfile.mktemp('.log_valid')

    args = []
    args.append(commands.mkarg(collection))
    args.append(commands.mkarg(reportDate))
    args.append(commands.mkarg(html_file))
    args.append(commands.mkarg(valid_file))
    args.append(commands.mkarg(new_valid_file))

    cmd = ('(. %s && cd %s/enterprise/legacy/logs && '
           'alarm %s nice -n 15 ./apache_log.py %s %s) > %s' %
           (self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
            self.cfg.getGlobalParam('MAIN_GOOGLE3_DIR'),
            COMMAND_TIMEOUT_PERIOD,
            commands.mkarg(self.cfg.globalParams.GetEntHome()),
            string.join(args, ' '),
            commands.mkarg(new_html_file)))
    logging.info('doLogDump(): CMD = %s' % cmd)
    returnCode = E.system(cmd)

    self.handleResult(jobName, jobToken, returnCode, liblog.RAW_REPORT,
                      collection, reportName, update,
                      html_file, valid_file, new_html_file, new_valid_file)


  def handleResult(self, jobName, jobToken, returnCode, reportType,
                   collection, reportName, update,
                   html_file, valid_file, new_html_file, new_valid_file):
    """This is like a callback method to take care of the result of
    doLogDump() or doLogReport(). This method is executed in a worker thread."""

    self.joblock.acquire()
    try:
      # if abandoned, don't report.
      if (not self.runningJobs.has_key(jobName) or
          self.runningJobs[jobName] != jobToken):
        logging.info('Running job for report %s complete, '
                     'but it was abandoned.' % reportName)
        self.RemoveReportFiles(new_html_file, new_valid_file)
        return
      else:
        del self.runningJobs[jobName]
    finally:
      self.joblock.release()

    exited = os.WIFEXITED(returnCode)
    if exited:
      returnCode = os.WEXITSTATUS(returnCode)

    # good path.
    if (exited and (returnCode == liblog.STILL_VALID or
                    returnCode == liblog.SUCCESS)):
      logging.info('Log report %s for collection %s generated correctly' % \
                   (reportName, collection))
      if returnCode == liblog.SUCCESS:
        (err, _) = E.run_fileutil_command(self.entConfig, 'copy %s %s' % \
                                          (new_valid_file, valid_file),
                                          COMMAND_TIMEOUT_PERIOD)
        if err:
          # This may make the report invalid next time we try to update,
          # but it's ok to use.
          logging.error('Failed to copy report valid file %s to %s' % \
                        (new_valid_file, valid_file))

        (err, _) = E.run_fileutil_command(self.entConfig, 'copy %s %s' % \
                                          (new_html_file, html_file),
                                          COMMAND_TIMEOUT_PERIOD)
        if err:
          self.RemoveReportFiles(new_html_file, new_valid_file)
          logging.error('Failed to copy complete report %s to %s' % \
                       (new_html_file, html_file))
          # change returnCode to execute the failure path.
          returnCode = liblog.FAILURE
        else:
          self.setReportCompleteState(reportType, collection,
                                      reportName, COMPLETE)

          if self.entConfig.var('GFS_ALIASES') and \
                 reportType == liblog.RAW_REPORT:
            self.CopyRawReportFromGfsToLocal(reportName, collection)
      else:
        self.setReportCompleteState(reportType, collection,
                                      reportName, COMPLETE)


    # failure path.
    if not exited or returnCode == liblog.FAILURE:
      logging.error('Error running log report command for report %s' % \
                    reportName)
      self.RemoveReportFiles(new_html_file, new_valid_file)

      if update:
        # if we fail to update, leave the old one untouched.
        self.setReportCompleteState(reportType, collection,
                                    reportName, COMPLETE,
                                    takeOldRecord=true)
      else:
        self.setReportCompleteState(reportType, collection,
                                    reportName, FAILURE)
        self.logreplock.acquire()
        try:
          self.reportCount[liblog.RAW_REPORT] -= 1
        finally:
          self.logreplock.release()

  def stopRunningJob(self, jobName):
    """Stop the running thread that generates a log report."""
    self.joblock.acquire()
    try:
      if self.runningJobs.has_key(jobName):
        # Note: I used to lie here, I didn't actually stop the thread. There is no
        # safe way in python to do this. All I do is just remove the running
        # job from the hash table so when it complete, it doesn't store its
        # result.
        # TODO(pn): Figure a way to stop the running job so not to waste
        # resources.
        logging.info('About to abandon the running job. jobName = %s, '
                     'jobToken = %d' % (jobName, self.runningJobs[jobName]))
        del self.runningJobs[jobName]
      else:
        logging.error('Found a pending report with no running thread.')
    finally:
      self.joblock.release()

  def deleteCollection(self, collection):
    """Delete all reports and logs for a particular collection."""
    self.logreplock.acquire()
    try:
      for reportType in [liblog.RAW_REPORT, liblog.SUMMARY_REPORT]:
        reports = self.getLogReports(collection, reportType)
        for report in reports:
          # stop running job if report is being (re)generated.
          if report.completeState != COMPLETE:
            self.stopRunningJob(self.jobName(report))

          # delete data files if any.
          (html_file, valid_file) = liblog.get_report_filenames(self.entConfig,
                                     reportType, report.reportName, collection)
          self.RemoveReportFiles(html_file, valid_file)
        self.reportCount[reportType] -= len(reports)
        logging.info('Delete total %d reports of type %s for collection %s.' % (
          len(reports), reportType, collection))
        listfile = liblog.get_report_list_filename(self.entConfig,
                                                   reportType, collection)
        (err, out) = E.run_fileutil_command(self.entConfig,
                                            'rm -f %s' % listfile)
        if err:
          logging.error('Cannot remove list file %s.' % listfile)

      report_collection_dir = liblog.get_report_collection_dir(self.entConfig,
                                                               collection)
      (err, out) = E.run_fileutil_command(self.entConfig,
                                          'rmdir %s' % report_collection_dir)
      if err:
        logging.error('Cannot delete unused directory %s' % \
                      report_collection_dir)
    finally:
      self.logreplock.release()

  def getLogReports(self, collection, reportType):
    """Return a list of reports of given reportType on given collection."""
    listFile = liblog.get_report_list_filename(self.entConfig, reportType,
                                               collection)
    reports = []
    try:
      lines = gfile.GFile(listFile, 'r').readlines()
      for line in lines:
        if line[-1] == '\n':
          line = line[:-1]
        (reportName, collection, creationDate,  isFinal,
         reportType, reportDate, completeState,
         withResults, topCount,
         diagnosticTerms) = string.split(line, '\t', 9)
        reports.append(LogReport(urllib.unquote(reportName),
                                 collection, creationDate, isFinal,
                                 reportType, reportDate, completeState,
                                 withResults, topCount, diagnosticTerms))

    except IOError:
      return []
    except ValueError:
      return []
    return reports

  def setLogReports(self, reportType, collection, reports):
    """Set the file content for list of reports of given reportType
    on given collection."""
    try:
      listfile = liblog.get_report_list_filename(self.entConfig, reportType,
                                                 collection)
      gfile.GFile(listfile, 'w').write(
        string.join(map(ReportToString, reports), '\n'))
    except IOError:
      logging.error('Cannot write new LogReport')
      return false

    return true

  def sanitizeReportList(self, reportType):
    if reportType == liblog.RAW_REPORT:
      pattern = 'logdump_*_list'
    else:
      pattern = 'logreport_*_list'

    files = gfile.ListDir(liblog.get_report_dir(self.entConfig))
    files = fnmatch.filter(files, pattern)

    if not files:
      return

    if reportType == liblog.RAW_REPORT:
      pattern = 'logdump_(.*)_list'
    else:
      pattern = 'logreport_(.*)_list'
    regex = re.compile(pattern)

    for file in files:
      m = regex.match(os.path.basename(file))
      collection = m.group(1)
      reports = self.getLogReports(collection, reportType)
      for i in range(len(reports)):
        if reports[i].completeState == PENDING:
          reports[i].completeState = FAILURE
        if reports[i].completeState == COMPLETE_REGENERATE:
          reports[i].isFinal = string.split(reports[i].isFinal, '|')[0]
          reports[i].creationDate = string.split(reports[i].creationDate, '|')[0]
          reports[i].completeState = COMPLETE
        if reports[i].completeState != FAILURE:
          self.reportCount[reportType] += 1
      self.setLogReports(reportType, collection, reports)

  def CopyRawReportFromGfsToLocal(self, reportName, collection):
    """Make a local copy of a raw report so file_handler can use."""
    (remoteName, _) = liblog.get_report_filenames(self.entConfig,
                                     liblog.RAW_REPORT, reportName, collection)
    localName = liblog.get_local_raw_report_filename(self.entConfig,
                                                     reportName, collection)
    liblog.MakeDir(os.path.dirname(localName))
    (err, out) = E.run_fileutil_command(self.entConfig, 'copy -f %s %s' % \
                                        (remoteName, localName),
                                        COMMAND_TIMEOUT_PERIOD)
    if err:
      logging.error('Failed to make copy from gfs for %s. Error: %s' % \
                    (localName, out))
      return false
    return true


###############################################################################

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

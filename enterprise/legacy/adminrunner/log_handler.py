#!/usr/bin/python2.4
#
# Copyright 2002-2205 Google inc.
# cpopescu@google.com from LogReportHandler bty davidw@google.com
#
# The log report commands
# pn@google.com
###############################################################################

import string
import threading
import urllib

from google3.enterprise.tools import M
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
from google3.enterprise.legacy.logs import liblog
from google3.enterprise.legacy.adminrunner import log_manager

###############################################################################
true  = 1
false = 0

class LogReportsHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      'list':          admin_handler.CommandInfo(
      2, 0, 0, self.list),
      'start':         admin_handler.CommandInfo(
      0, 1, 0, self.start),
      'update':        admin_handler.CommandInfo(
      5, 0, 0, self.update),
      'getform':        admin_handler.CommandInfo(
      3, 0, 0, self.getform),
      'delete':        admin_handler.CommandInfo(
      3, 0, 0, self.delete),
      'cancel':        admin_handler.CommandInfo(
      3, 0, 0, self.cancel),
      'view':        admin_handler.CommandInfo(
      2, 0, 0, self.view),
     }

  #############################################################################

  def list(self, collection, reportType):
    """Return list of reports."""
    reportList = self.cfg.logmanager.getLogReports(collection, reportType)
    result = string.join(map(log_manager.ReportToString, reportList), '\n')
    return result

  def start(self, reportFormStr):
    """Generate a new report."""
    reportForm = log_manager.StringToLogReportForm(reportFormStr)
    reportForm.completeState = log_manager.PENDING
    status = self.cfg.logmanager.generateReport(reportForm)
    if status == C.REPORT_OK:
      msg = M.MSG_LOG_GENERATE_REPORT % (reportForm.reportName)
    else:
      msg = M.MSG_LOG_GENERATE_REPORT_FAILED % (reportForm.reportName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def update(self, collection, reportType, reportName, updateDateStr, isFinal):
    """Update an existing report."""
    # We need to pass an entire record since we want adminrunner to treat
    # some fields like creationDate and isFinal as opaque
    status = self.cfg.logmanager.updateReport(collection, reportType,
                                           urllib.unquote(reportName),
                                           urllib.unquote(updateDateStr),
                                           isFinal)

    if status == C.REPORT_OK:
      msg = M.MSG_LOG_UPDATE_REPORT % (reportName)
    else:
      msg = M.MSG_LOG_UPDATE_REPORT_FAILED % (reportName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def getform(self, collection, reportType, reportName):
    """Return one report form in its serialized format. This gives
    convenience for update action."""
    return self.cfg.logmanager.getReportForm(collection, reportType,
                                             urllib.unquote(reportName))

  def delete(self, collection, reportType, reportName):
    """Delete a complete or failed report."""
    status = self.cfg.logmanager.deleteReport(collection, reportType,
                                              urllib.unquote(reportName),
                                              doCancel=false)

    if status == C.REPORT_OK:
      msg = M.MSG_LOG_DELETE_REPORT % (reportName)
    else:
      msg = M.MSG_LOG_DELETE_REPORT_FAILED % (reportName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def cancel(self, collection, reportType, reportName):
    """Cancel a running report."""
    status = self.cfg.logmanager.deleteReport(collection, reportType,
                                              urllib.unquote(reportName),
                                              doCancel=true)

    # TODO(pn): Use correct message after 4.6.0.S release.
    # messages should be able cancel, not delete.
    if status == C.REPORT_OK:
      msg = M.MSG_LOG_DELETE_REPORT % (reportName)
    else:
      msg = M.MSG_LOG_DELETE_REPORT_FAILED % (reportName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def view(self, collection, reportName):
    """ Returns the body of a report, prepend by its status and form data.
    The first line of the result is the status, which can be:
    REPORT_NAME_NOT_FOUND, REPORT_INCOMPLETE, REPORT_INTERNAL_ERROR,
    or REPORT_OK.
    The second line is the report form data.
    The rest is report body in ad-hoc format.
    """
    (status, reportForm, contents) = self.cfg.logmanager.getReport(collection,
                                                     urllib.unquote(reportName))
    if status == C.REPORT_OK:
      return '%d\n%s\n%s' % (C.REPORT_OK, reportForm, contents)
    else:
      return '%d' % status

###############################################################################

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

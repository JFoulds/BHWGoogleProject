#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.
# Author: pn@google.com (Phuong Nguyen)
#
# This script preprocess logs: partition by collections, converting to
# apache format.
#
# The main method of this script is PartitionLogs. It does the following:
# - Lock the partition directory: At most one thread can be
#   running this method at a time.
# - Read the last checkpoint file and construct partitioning state: That
#   includes building the list of unpartitioned collected logs and the hashes
#   of target files (partitioned, apache) with their size after last good
#   checkpoint. The checkpoint also includes a map from collection name to
#   list of site-param fingerprints, used as partitioned directory names.
#   Also, we need to recover target files to clean state if it was
#   dirty by resizing them to those in the above hash.
# - Partition unpartitioned collected logs: Process those unpartitioned log
#   entries in collect_dir and append to target files.
# - Along with that partition, write to apache log files, partitioned by
#   collections.
# - Write the checkpoint file. This step may happen more frequent
#   to incrementally save our work.

###############################################################################
"""
Usage:
    preprocess_logs.py <enthome>
"""
###############################################################################

import os
import sys
import string
import glob
import re
import time

from google3.base import pywrapbase
from google3.pyglib import logging
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.util import find_main
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.logs import liblog
from google3.enterprise.legacy.logs import ClickEvent_pb
from google3.enterprise.legacy.adminrunner import entconfig
from google3.file.base import pywrapfile
from google3.file.base import pywraprecordio
from google3.file.base import recordio
from google3.logs.analysis.lib import libgwslog
from google3.net.proto import ProtocolBuffer

true  = 1
false = 0
# Calculate UTC timezone offsets
utc_hour = -1 * (int(time.timezone / 3600) % 24)
utc_min = int(time.timezone / 60) % 60
utc_offset = '%+0.2d%0.2d' % (utc_hour, utc_min)

APACHE_LINE_FORMAT = '%s - - [%s %s] "%s %s %s" %d %d %d %0.2f\n'

CLICK_LINE_FORMAT_MAJOR_VERSION = 1
CLICK_LINE_FORMAT_MINOR_VERSION = 1
CLICK_LINE_FORMAT = 'asr %d.%d %ld %s %s %s %s %d %d %s %s %s\n'
# Fields:
#   1.  The token `asr' so these lines may be recognized in any context.
#   2.  A version number for the line format.
#   3.  Long timestamp to nearest 100th second.
#   4.  Time and date in same format as apache line.
#       NOTE:  THIS FIELD MUST BE THE SAME BETWEEN THE
#       CLICK LINE FORMAT AND APACHE_LINE_FORMAT FOR COLLATION.
#   5.  The IP address
#   6.  The session id
#   7.  Click type
#   8.  Click start
#   9.  Click rank
#  10.  Click data
#  11.  Click query
#  12.  Click URL
#
# The values of these fields are taken from the ClickEvent protocol
# buffer (q.v. google3/enterprise/apps/clicklog/clickevent.proto), but
# they are not necessarily layed out in the same order.
#
# The format has a major and minor version.  The minor version is to
# be incremented whenever a field is added at the end.  If an existing
# field is deleted or moved, the minor version goes to zero and the
# major version is incremented.
#
# If you change the format in any way, be sure to adjust the
# CLICK_LINE_FORMAT_MAJOR_ and MINOR_ VERSION appropriately.
#
# The format as supplied here is what is manipulated internally.  It
# is specifically designed to allow the collation process to be shared
# between the apache logs and the click logs.  If you change it, you
# may break it.  To be excruciatingly exact:  the timestamp in field
# four must be the fourth space-delimited field and it must be in the
# same date format as the Apache logs.  Further processing at export
# time will remove unnecessary data and change the format from
# space-delimited to comma-delimited.
#
###############################################################################


def _FormatDate(date):
  """Format a date in Apache log style."""
  return time.strftime('%d/%b/%Y:%H:%M:%S', time.localtime(date))


def _FormatIPAddress(ipaddr):
  """Take a 32-bit unsigned integer representation of an IP address
     and format it in dotted quad notation."""
  (q1, byte1) = divmod(ipaddr, 256)
  (q2, byte2) = divmod(q1, 256)
  (q3, byte3) = divmod(q2, 256)
  (q4, byte4) = divmod(q3, 256)

  return '%d.%d.%d.%d' % (byte4, byte3, byte2, byte1)


def _FormatApacheEntry(entry):
  """Convert an gws log entry into apache format."""
  return APACHE_LINE_FORMAT % (entry.ipaddr,
                               _FormatDate(entry.when),
                               utc_offset,
                               entry.method,
                               entry.url,
                               entry.http_version,
                               entry.response_code,
                               entry.response_bytes,
                               entry.response_numresults,
                               entry.elapsed_server)


def _FormatClickEvent(clickEvent):
  """Convert a clickEvent into a log entry."""
  return CLICK_LINE_FORMAT % (CLICK_LINE_FORMAT_MAJOR_VERSION,
                              CLICK_LINE_FORMAT_MINOR_VERSION,
                              clickEvent.time100(),
                              _FormatDate(round(clickEvent.time100()/100)),
                              _FormatIPAddress(clickEvent.ip_address()),
                              clickEvent.session_id(),
                              clickEvent.click_type(),
                              clickEvent.start(),
                              clickEvent.rank(),
                              clickEvent.click_data(),
                              clickEvent.query(),
                              clickEvent.url())


def _LogsToBeRead(collect_dir, lastSources):
  """Get the list of partnerlogs in collect_dir and its last read position."""
  logfiles = glob.glob('%s/*/partnerlog.*' % collect_dir)
  logfiles += glob.glob('%s/*/clicklog.*' % collect_dir)
  logsToBeRead = {}
  for logfile in logfiles:
    if not lastSources.has_key(logfile):
      logsToBeRead[logfile] = 0
    elif lastSources[logfile] < os.path.getsize(logfile):
      logsToBeRead[logfile] = lastSources[logfile]
  return logsToBeRead


def _CleanTargetFiles(target_dir, lastTargets):
  """Clean target files in target directory based on last checkpoint.
  Unknown files are removed. File with bigger size will be truncated to
  checkpointed size.
  """

  logfiles = glob.glob('%s/*/*/partnerlog.*' % target_dir)
  logfiles += glob.glob('%s/*/*/clicklog.*' % target_dir)
  logfile = ''
  try:
    for logfile in logfiles:
      if not lastTargets.has_key(logfile):
        try:
          os.unlink(logfile)
        except OSError:
          pass
      elif lastTargets[logfile] < os.path.getsize(logfile):
        fp = open(logfile, 'r+')
        fp.truncate(lastTargets[logfile])
        fp.close()
    return true
  except IOError:
    logging.error('Failed to truncate file %s' % logfile)
    return false


def PartitionLogs(entConfig):
  """Read unconsumed log entries from collect_dir based on checkpoint
  to partition into partition_dir by collections. Also this method will
  emit Apache format entries into appropriate files in apache_dir.
  """

  collect_dir = liblog.get_collect_dir(entConfig)
  partition_dir = liblog.get_partition_dir(entConfig)
  apache_dir = liblog.get_apache_dir(entConfig)
  click_dir = liblog.get_click_dir(entConfig)
  directory_map_file = liblog.get_directory_map_file(entConfig)

  checkpoint_file = '%s/.checkpoint' % partition_dir
  lockfile = '%s/.lock' % partition_dir

  lock = E.acquire_lock(lockfile, 1, breakLockAfterGracePeriod=0)
  if lock == None:
    logging.error('Cannot grab the lock. Exiting!')
    return

  (lastSources,
   lastPartitioned,
   lastApacheTargets,
   lastClickTargets) = _ReadLogCheckpoint(checkpoint_file)
  collDirectoryMap = liblog.CollectionDirectoryMap(directory_map_file)

  logs_changed = _SanitizeLogCheckpointData(lastSources,
                                            lastPartitioned,
                                            lastApacheTargets,
                                            lastClickTargets)

  logsToBeRead = _LogsToBeRead(collect_dir, lastSources)
  _CleanTargetFiles(partition_dir, lastPartitioned)
  _CleanTargetFiles(apache_dir, lastApacheTargets)
  _CleanTargetFiles(click_dir, lastClickTargets)

  count = 0
  # this regex to extract from an absolute filename the machine_n_filename
  # part such as 'ent1/partnerlog.from_ent1.port8888.start20060125'
  reg = re.compile('.*/(?P<machine_n_filename>.*/.*)')
  for rawFile in logsToBeRead.keys():
    # maps from collections to filenames.
    partitionedFilenames = {}
    apacheFilenames = {}
    clickFilenames = {}
    # maps from filenames to OutputLog objects.
    partitionedLogs = {}
    apacheLogs = {}
    clickLogs = {}

    m = reg.match(rawFile)
    if not m or not m.group('machine_n_filename'):
      logging.error('Unrecognized filename: %s' % rawFile)
      continue
    machine_n_filename = m.group('machine_n_filename')

    isClicklog = (machine_n_filename.find('clicklog') != -1)

    logging.info('Opening input file %s at position %d' % (
        rawFile, logsToBeRead[rawFile]))

    if isClicklog:
      # Process a clicklog
      rr = recordio.RecordReader(rawFile)
      # Seek past the elements we have already read.
      # This seek should not fail because the file can only grow.
      rr.Seek(logsToBeRead[rawFile])

      for buf in rr:
        clickEvent = ClickEvent_pb.ClickEvent(buf)

        collection = clickEvent.site()
        if not collDirectoryMap.hasSite(collection):
          collDirectoryMap.addSiteParam(collection)

        subdirName = collDirectoryMap.makeDirectoryName(collection)
        if not partitionedFilenames.has_key(subdirName):
          partitionedFilenames[subdirName] = os.path.join(
              partition_dir, subdirName, machine_n_filename)
        filename = partitionedFilenames[subdirName]

        # Append the click event to the partitioned log.
        # This is done via a record writer so we get a valid copy.
        if not partitionedLogs.has_key(filename):
          (dir, file) = os.path.split(filename);
          liblog.MakeDir(dir)
          partitionedLogs[filename] = pywraprecordio.RecordWriter(
              pywrapfile.File_OpenOrDie(filename, "a"), 65536,  # mem budget
              pywraprecordio.RecordWriter.AUTO, 0)              # aio budget
        partitionedLogs[filename].WriteRecord(clickEvent.Encode())

        if not clickFilenames.has_key(subdirName):
          clickFilenames[subdirName] = os.path.join(
              click_dir, subdirName, machine_n_filename)
        filename = clickFilenames[subdirName]

        if not clickLogs.has_key(filename):
          clickLogs[filename] = OutputLog(filename)

        clickLogs[filename].append(_FormatClickEvent(clickEvent))
        # End of for loop on each click entry

      lastSources[rawFile] = rr.Tell()
      rr.Close()
      # end of clicklog case

    else:
      # Process a partnerlog
      rawFp = open(rawFile, 'r')
      # Should not fail because log cannot shrink.
      rawFp.seek(logsToBeRead[rawFile])

      # read first line of rawFile.
      lastLine = ''
      line = string.strip(rawFp.readline())
      entry = None
      while line:
        try:
          entry = libgwslog.parse_logline(line, 'weblog')
          count = count + 1
        except Exception, e:
          logging.error('Exception found: %s' % e)
          logging.info('Cannot parse one line: %s' % line)
          entry = None

        if entry and entry.args:
          # process this entry.
          if len(entry.args.site) > 0 and \
                 liblog.IsValidSiteParam(entConfig.var('ENT_COLLECTIONS')
                                         .keys(), entry.args.site):
            collection = entry.args.site
          else:
            collection = C.NO_COLLECTION
          if not collDirectoryMap.hasSite(collection):
            collDirectoryMap.addSiteParam(collection)

          subdirName = collDirectoryMap.makeDirectoryName(collection)
          if not partitionedFilenames.has_key(subdirName):
            partitionedFilenames[subdirName] = os.path.join(
                partition_dir, subdirName, machine_n_filename)
          filename = partitionedFilenames[subdirName]

          if not partitionedLogs.has_key(filename):
            partitionedLogs[filename] = OutputLog(filename)
          partitionedLogs[filename].append(line + '\n')

          if not apacheFilenames.has_key(subdirName):
            apacheFilenames[subdirName] = os.path.join(
                apache_dir, subdirName, machine_n_filename)
          filename = apacheFilenames[subdirName]

          if not apacheLogs.has_key(filename):
            apacheLogs[filename] = OutputLog(filename)

          apacheLogs[filename].append(_FormatApacheEntry(entry))

        # read the next line
        lastLine = line
        line = string.strip(rawFp.readline())
        # End of while loop.

      # Save the rawFp position and close it.
      if entry == None:
        lastSources[rawFile] = rawFp.tell() - len(lastLine)
      else:
        lastSources[rawFile] = rawFp.tell()
      rawFp.close()
      # End of partnerlog case

    # Done processing one rawFile. Now doing some cleaning work.
    for filename in partitionedLogs.keys():
      partitionedLogs[filename].Flush()
      lastPartitioned[filename] = partitionedLogs[filename].Tell()
      partitionedLogs[filename].Close()
      del partitionedLogs[filename]

    for filename in apacheLogs.keys():
      apacheLogs[filename].Flush()
      lastApacheTargets[filename] = apacheLogs[filename].Tell()
      apacheLogs[filename].Close()
      del apacheLogs[filename]

    for filename in clickLogs.keys():
      clickLogs[filename].Flush()
      lastClickTargets[filename] = clickLogs[filename].Tell()
      clickLogs[filename].Close()
      del clickLogs[filename]

    if count > 10000:  # better save our work
      logging.info('write checkpoint since count = %d' % count)
      count = 0
      _WriteLogCheckpoint(checkpoint_file, lastSources,
                          lastPartitioned, lastApacheTargets, lastClickTargets)
  # end of for loop on rawFiles from logsToBeRead.

  if len(logsToBeRead) != 0 or logs_changed:
    _WriteLogCheckpoint(checkpoint_file, lastSources,
                        lastPartitioned, lastApacheTargets, lastClickTargets)
    if collDirectoryMap.hasChanged():
      collDirectoryMap.saveToDisk()

  lock.close()
  os.unlink(lockfile)


def _SanitizeLogCheckpointDataHelper(logs):
  """Helper function for _SanitizeLogCheckpointData()."""
  changed = false
  for logname in logs.keys():
    if not os.path.exists(logname):
      logging.info('File %s has been removed. Clean checkpoint data.' % logname)
      del logs[logname]
      changed = true
  return changed


def _SanitizeLogCheckpointData(lastSources,
                               lastPartitioned,
                               lastApacheTargets,
                               lastClickTargets):
  """Remove from checkpoint those entries that no longer exists on disk."""
  source_changed = _SanitizeLogCheckpointDataHelper(lastSources)
  partitioned_changed = _SanitizeLogCheckpointDataHelper(lastPartitioned)
  apache_changed = _SanitizeLogCheckpointDataHelper(lastApacheTargets)
  click_changed = _SanitizeLogCheckpointDataHelper(lastClickTargets)
  return source_changed or partitioned_changed or apache_changed or click_changed


def _ReadLogCheckpointHelper(lineIdx, lines, regex):
  """Helper function for _SanitizeLogCheckpointData()."""
  result = {}
  while lineIdx < len(lines):
    m = regex.match(lines[lineIdx])
    if m:
      result[m.group(2)] = int(m.group(1))
      lineIdx = lineIdx + 1
    else:
      break
  return (lineIdx, result)


def _ReadLogCheckpoint(checkpoint_file):
  """Read the checkpoint file of log preprocessing."""
  # pattern for input files in collect dir
  rawRegex = re.compile('COLLECT: ([0-9]+)\t(.+)')
  # pattern for output files in partition dir
  partitionedRegex = re.compile('PARTITIONED: ([0-9]+)\t(.+)')
  # pattern for output files in apache dir
  apacheRegex = re.compile('APACHE: ([0-9]+)\t(.+)')
  # pattern for output files in click dir
  clickRegex = re.compile('CLICK: ([0-9]+)\t(.+)')

  try:
    file = open(checkpoint_file, 'r')
    lines = file.readlines()
    idx = 0
    (idx, lastSources) = _ReadLogCheckpointHelper(idx, lines, rawRegex)
    (idx, lastPartitioned) = _ReadLogCheckpointHelper(idx, lines,
                                                      partitionedRegex)
    (idx, lastApacheTargets) = _ReadLogCheckpointHelper(idx, lines, apacheRegex)
    (idx, lastClickTargets) =  _ReadLogCheckpointHelper(idx, lines, clickRegex)
    return (lastSources, lastPartitioned, lastApacheTargets, lastClickTargets)
  except IOError, e:
    logging.info(e)
  return ({}, {}, {}, {})


def _WriteLogCheckpoint(checkpoint_file, lastSources,
                        lastPartitioned, lastApacheTargets,
                        lastClickTargets):
  """Write the checkpoint file for log preprocessing."""
  try:
    tmpFilename = '%s.tmp' % checkpoint_file
    logging.info('sizeof(partitioned) = %d, sizeof(apache) = %d, sizeof(click) = %d' % (
        len(lastPartitioned), len(lastApacheTargets), len(lastClickTargets)))
    tmpFile = open(tmpFilename, 'w')
    for name in lastSources.keys():
      tmpFile.write('COLLECT: %d\t%s\n' % (lastSources[name], name))
    for name in lastPartitioned.keys():
      tmpFile.write('PARTITIONED: %d\t%s\n' % (lastPartitioned[name], name))
    for name in lastApacheTargets.keys():
      tmpFile.write('APACHE: %d\t%s\n' % (lastApacheTargets[name], name))
    for name in lastClickTargets.keys():
      tmpFile.write('CLICK: %d\t%s\n' % (lastClickTargets[name], name))
    tmpFile.close()

    os.rename(tmpFilename, checkpoint_file)
    return true
  except IOError, e:
    logging.info('IOError: %s' % e)
    return false


###############################################################################
class OutputLog:
  WRITE = 'w'
  APPEND = 'a'

  def __init__(self, file):
    self.file = file
    self.mode = None
    self.fd = None
    self.count = 0
    self.buffer = []

  def open(self, mode=APPEND):
    if not self.fd:
      (dir, file) = os.path.split(self.file)
      liblog.MakeDir(dir)
      self.fd = open(self.file, mode)
      self.mode = mode
    elif self.mode != mode:
      self.close()
      self.open(mode)
    return self.fd

  def append(self, line):
    self.buffer.append(line)
    self.count = self.count + 1
    if self.count >= 1000:
      self.Flush()

  # These are Capitalized so we can call them the same
  # way we call the recordio writer.
  def Flush(self):
    if not self.fd:
      self.open(self.APPEND)
    self.fd.writelines(self.buffer)
    self.buffer = []
    self.count = 0

  def Close(self):
    if self.count != 0:
      self.Flush()
    if self.fd:
      self.fd.close()
      self.fd = None

  def Tell(self):
    return self.fd.tell()

###############################################################################

if __name__ == '__main__':
  sys.exit('Import this module')

###############################################################################

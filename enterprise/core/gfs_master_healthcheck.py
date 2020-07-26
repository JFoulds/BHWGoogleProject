#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.
#

""" print RESTART if gfs_main needs to be restarted.

Usage:   gfs_main_healthcheck.py [gfs_main_port] [ver]
Example: gfs_main_healthcheck.py 3830 '4.6.5'

"""

__author__ = 'wanli@google.com (Wanli Yang)'

import sys
import commands
import time
import os
from google3.enterprise.legacy.scripts import check_healthz

def GetLogDir(ver):
  """ returns the log dir of gfs_main

  Arguments:
    ver: '4.6.5'
  Returns:
    '/export/hda3/4.6.5/logs'
  """
  return '/export/hda3/%s/logs' % ver

def GetLogEtime(ver, logtype):
  """ if a type of gfs_main log exists, return the # of seconds
  since last modification. Otherwise, return time().

  Arguments:
    ver: '4.6.5'
    logtype: 'INFO', 'FATAL', or 'ERROR'
  Returns:
    300
  """

  log_name = '%s/gfs_main.%s' % (GetLogDir(ver), logtype)
  if os.path.exists(log_name):
    mtime = os.path.getmtime(log_name)
  else:
    mtime = 0
  return int(time.time() - mtime)

def SearchStringInLogs(ver, logtype, string_to_search, mmin=None):
  """ find out the number of gfs_main logs of a particular type
  contains a particular string

  Arguments:
    ver: '4.6.5'
    logtype: 'INFO', 'FATAL', or 'ERROR'
    string_to_search: 'Acquired main lock but can not control logs'
    mmin: only look at files modified within since mmin minutes ago
          None if don't care about the time
  Returns:
    3
  """

  find_cmd = 'find %s -name "gfs_main*.%s.*"' % (GetLogDir(ver), logtype)
  if mmin:
    find_cmd = '%s -mmin -%d' % (find_cmd, mmin)
  find_cmd = '%s |xargs grep -l "%s"' % (find_cmd, string_to_search)
  status, output = commands.getstatusoutput(find_cmd)
  if status == 0:
    return len(output.splitlines())
  return 0

def main(argv):
  if len(argv) < 2:
    sys.exit(__doc__)

  try:
    port = int(argv[0])
  except ValueError:
    sys.exit(__doc__)

  ver = argv[1]
  # first check if it is responding to the healthz check
  if check_healthz.CheckHealthz(port):
    sys.exit(0)

  # if there are processes listening on the port, check
  # if there is any recent fatal errros. If the last FATAL log
  # was 30 minutes ago, and the last INFO log is pretty new,
  # gfs_main is probably still restarting and cannot answer
  # healthz check (bug 234769)
  if (GetLogEtime(ver, 'FATAL') > 1800 and GetLogEtime(ver, 'INFO') < 300):
    sys.exit(0)

  print 'RESTART'

if __name__ == '__main__':
  main(sys.argv[1:])

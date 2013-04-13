#!/usr/bin/python2.4
#
# Copyright 2000-2006 Google Inc. All Rights Reserved.
# davidw@google.com
# pn@google.com
#
# This script collects and processes logs from all available machines
#
# This script does:
#   - collect raw log records from gws node(s) and update log_apache
#           directory if needed
#   - check for validity of existing report if any, if there exists a report
#           that's still valid, return STILL_VALID
#   - simply do a dump all log records in log_apache directory for given
#         client within given date range without doing update.
#
# Note: Please see note in log_report.py, where we do similar thing for summary report.
#       If there doesn't exist a valid report, this process use shell command tac
#       to generate the dump in reverse order and the result is dump to stdout.
###############################################################################
"""
Usage:
    apache_log.py <enthome> <client> <date_arg> <html_file> <valid_file> <new_valid_file>
     date_arg: after split('_')
      all
      date <MM> <DD> <YYYY>
      month <MM> <YYYY>
      year <YYYY>
      range <MM> <DD> <YY> <MM> <DD> <YYYY>
    Return: STILL_VALID: if old report exists and is still valid.
            SUCCESS: if new report is successfully generated.
            FAILURE: if failed to generate a new report.
"""
###############################################################################

import commands
import os
import string
import sys
import tempfile

from google3.base import pywrapbase
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.logs import collect_logs
from google3.enterprise.legacy.logs import liblog
from google3.enterprise.legacy.logs import preprocess_logs
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.pyglib import gfile
from google3.pyglib import logging

###############################################################################
true = 1
false = 0

# Dump all records in those files, represented by
# @apache_log - the list of Log objects, in reversed order.
def DumpApacheAndClickLogs(apache_logs, click_logs):
  """Dump all files in @apache_logs and sort in reverse order."""
  apache_loglist = tempfile.mktemp('.apache_loglist')
  try:
    loglist_file = open(apache_loglist, 'w+')
    for apache_log in apache_logs:
      loglist_file.write(apache_log.file + "\n")
    for click_log in click_logs:
      loglist_file.write(click_log.file + "\n")
    loglist_file.close()
    cmd = './sort_apache_logs.py --from_file %s' % \
          commands.mkarg(apache_loglist)
    logging.info(cmd)
    os.system(cmd)
  finally:
    os.system('rm -f %s' % commands.mkarg(apache_loglist))

def main(argv):
  argc = len(argv)

  if argc < 6:
    sys.exit(__doc__)

  config = entconfig.EntConfig(argv[0])
  if not config.Load():
    sys.exit(__doc__)

  pywrapbase.InitGoogleScript('', ['foo',
          '--gfs_aliases=%s' % config.var("GFS_ALIASES"),
          '--bnsresolver_use_svelte=false',
          '--logtostderr'], 0)
  gfile.Init()

  client = argv[1]
  date_arg = argv[2]
  html_file = argv[3]
  valid_file = argv[4]
  new_valid_file = argv[5]

  # extract tag and date_range from command line args
  date_fields = string.split(date_arg, '_')
  date_range = liblog.ParseDateRange(date_fields[0], date_fields[1:])

  if not date_range:
    sys.exit(__doc__)

  first_date, last_date, printable_date, file_date = date_range

  if last_date.as_int() < first_date.as_int():
    sys.exit(__doc__)

  gws_log_dir = liblog.get_gws_log_dir(config)
  click_dir = liblog.get_click_dir(config)
  collect_dir = liblog.get_collect_dir(config)
  apache_dir = liblog.get_apache_dir(config)
  directory_map_file = liblog.get_directory_map_file(config)

  # we need to collect logs first from all gws nodes and preprocess
  # logs first to make sure logs are up to date.
  all_machines = config.var('MACHINES')
  collect_logs.CollectLogs(all_machines, gws_log_dir, collect_dir)
  preprocess_logs.PartitionLogs(config)

  # make a vector of Log objects for all apache_logs and click_logs matching
  # the given date range and client.
  apache_logs = liblog.FindClientLogFiles(apache_dir, directory_map_file,
                                          client, first_date, last_date)
  click_logs = liblog.FindClientLogFiles(click_dir, directory_map_file,
                                          client, first_date, last_date)

  # If we have valid file and report file, we check to see if the data in
  # apache_dir has been changed and if the report is still valid.
  if (gfile.Exists(html_file) and gfile.Exists(valid_file) and
      liblog.checkValid(html_file, valid_file, apache_logs)):
    logging.info('%s still valid.' % html_file)
    sys.exit(liblog.STILL_VALID)

  # if there is no valid report, we create a new one
  DumpApacheAndClickLogs(apache_logs, click_logs)
  if not liblog.makeValid(new_valid_file, apache_logs):
    logging.error('Error validating %s' % html_file)
    sys.exit(liblog.FAILURE)

  logging.info('done apache_log, new_valid_file: %s' % new_valid_file)
  sys.exit(liblog.SUCCESS)


###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

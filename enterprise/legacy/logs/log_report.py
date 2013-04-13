#!/usr/bin/python2.4
#
# Copyright 2000-2006 Google Inc. All Rights Reserved.
# davidw@google.com
# pn@google.com
#
# This script collects and processes logs from all available machines
#
# (pn): The process of generating report is somewhat expensive, so we avoid
# unnecessary duplicate work by using the valid file for each report generated.
# For each report request, we first check for existence of the report and
# whether it's still valid against its input.
# If there is existing valid report, we just return STILL_VALID
# Otherwise, we try to generate new report.
# On successfully generating a report, we return SUCCESS.
# Otherwise, we return FAILURE.
# Note: We dont deal with gfs backup here any more, that's now done
# log_manager.
###############################################################################
"""
Usage:
    log_report.py <enthome> <client> <date_arg> <withResults> <topCount> \
                  <diagnosticTerms> <html_file> <valid_file> <new_html_file> \
                  <new_valid_file>
      date_arg: (after split('_'))
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

import sys
import string
import os
import commands

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

def CreateLogReport(config, date_str, logs, main_google3_dir,
                    withResults, topCount, diagnosticTerms,
                    html_file, valid_file,
                    new_html_file, new_valid_file):
  """This method generate an aggregate report on search queries over a
  period of days."""

  logging.info('Creating log report for %s' % date_str)

  # see if the report is already valid
  if (liblog.checkValid(html_file, valid_file, logs) and
      gfile.Exists(html_file)):
    logging.info('%s is already valid' % html_file)
    return liblog.STILL_VALID

  # build the list of args
  args = [date_str, new_html_file, withResults, topCount,
          diagnosticTerms]
  args.extend(map(lambda(x): x.file, logs))

  arg_str = string.join( map(commands.mkarg, args) )

  stats_cmd = ('cd %s/enterprise/legacy/analyzelogs/scripts; '
               './enterprise_stats.py %s' % (main_google3_dir, arg_str))

  (status, output) = liblog.DoCommand(stats_cmd)

  if status != 0:
    logging.error('Error running enterprise_stats: %s' % output)
    return liblog.FAILURE

  # make valid file
  if not liblog.makeValid(new_valid_file, logs):
    logging.error('Error making valid file %s' % new_html_file)
    return liblog.FAILURE

  logging.info('Done log_report for %s' % new_html_file)
  return liblog.SUCCESS


def main(argv):
  argc = len(argv)

  if argc < 10:
    sys.exit(__doc__)

  config = entconfig.EntConfig(argv[0])
  if not config.Load():  sys.exit(__doc__)

  pywrapbase.InitGoogleScript('', ['foo',
          '--gfs_aliases=%s' % config.var("GFS_ALIASES"),
          '--bnsresolver_use_svelte=false',
          '--logtostderr'], 0)
  gfile.Init()

  client = argv[1]
  date_fields = string.split(argv[2], '_')
  date_range = liblog.ParseDateRange(date_fields[0], date_fields[1:])

  withResults = argv[3]
  topCount = argv[4]
  diagnosticTerms = argv[5]

  html_file = argv[6]
  valid_file = argv[7]
  new_html_file = argv[8]
  new_valid_file = argv[9]

  if not date_range:
    sys.exit(__doc__)

  first_date, last_date, printable_date, file_date = date_range

  if last_date.as_int() < first_date.as_int():
    logging.fatal('invalid date range')

  gws_log_dir = liblog.get_gws_log_dir(config)
  collect_dir = liblog.get_collect_dir(config)
  partition_dir = liblog.get_partition_dir(config)
  directory_map_file = liblog.get_directory_map_file(config)

  # Collect logs first from all gws nodes and preprocess
  # logs to make sure logs are up to date.
  all_machines = config.var('MACHINES')
  collect_logs.CollectLogs(all_machines, gws_log_dir, collect_dir)
  preprocess_logs.PartitionLogs(config)

  gws_logs = liblog.FindClientLogFiles(partition_dir, directory_map_file,
                                       client, first_date, last_date)

  # note that collection (client) has been factored into gwslog_dir.
  result = CreateLogReport(config, printable_date, gws_logs,
                           config.var('MAIN_GOOGLE3_DIR'),
                           withResults, topCount, diagnosticTerms,
                           html_file, valid_file,
                           new_html_file, new_valid_file)

  if result == liblog.FAILURE:
    logging.error('CreateLogReport Failed')

  sys.exit(result)


###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

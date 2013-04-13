#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Ben Polk
#
# replace_set_start_daily.py - Command for config manager replace_set command
# that just runs startdaily.py
#

import commands
import string
import sys

from google3.enterprise.legacy.production.babysitter import configutil
from google3.enterprise.legacy.setup import prodlib

def main():

  # Get the command line options.
  opt_list = [
    'new_config_file=', 'datadir=', 'segment=', 'staging_dir=', 'norun']
  options = prodlib.GetOptionsDict(opt_list)

  # Get the file name for the full path of the little active file that
  # specifies which daily file is active and the datadir. This needs the
  # datadir, which we get from the end of the config file name.
  new_config_file = options['new_config_file']
  file_parts = string.split(new_config_file, '.')

  datacenter = file_parts[-1]
  base_fn = 'config.www.lvl1.' + datacenter
  config_fn = options['staging_dir'] + 'daily-staging/' + base_fn

  datadir = options['datadir']
  configutil.WriteConfigActiveFile(config_fn, datadir, new_config_file)

  # Create and run the startdaily.py command.
  start_daily_args_list = [
    '--workdir=/export/hda3/tmp',
    '--report_email=incremental-admin',
    '--control_file=/root/google/webserver/incremental_control.web'
    ]
  start_daily_args = string.join(start_daily_args_list)
  start_daily_cmd = ('/root/google3/enterprise/legacy/setup/startdaily.py %s' %
                     start_daily_args)

  rc = 0
  if options.has_key('norun'):
    print '--norun prevents execution of: ' + start_daily_cmd
  else:
    (rc, output) = commands.getstatusoutput(start_daily_cmd)
    if rc:
      print 'Error status (%s) running: %s' % (rc, start_daily_cmd)

    print output

  sys.exit(rc)

if __name__ == '__main__':
  main()

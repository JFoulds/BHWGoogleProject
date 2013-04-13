#!/usr/bin/python2.4
#
# Copyright 2002-2003 Google, Inc.
# cpopescu@google.com
#
'''
Runs adminrunner.py in a loop.

Usage:
       loop_AdminRunner <enthome> [flags...]

'''

import sys
import os
import time
import string
import commands
import subprocess
from google3.enterprise.legacy.util import python_kill

from google3.enterprise.legacy.scripts import check_healthz
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import reset_index

SLEEP_AFTER_RESTART = 300
CHECK_RESTART_INTERVAL = 10
MAX_CONSECUTIVE_KILLS_TO_SKIP = 30
MAX_RESET_INDEX_CONSECUTIVE_KILLS_TO_SKIP = 90

def main(argv):
  if len(argv) < 1:
    sys.exit(__doc__)

  pidfile = E.GetPidFileName('loop_AdminRunner')
  E.WritePidFile(pidfile)

  ENTERPRISE_HOME = commands.mkarg(argv[0])
  # ENTERPRISE_HOME are like "'/export/hda3/4.6.0.G.35'".
  # removing the "'" at the beginning and the end.
  ent_home = ENTERPRISE_HOME.split("'")[1]
  adminrunner_dir = ent_home + '/local/google3/enterprise/legacy/adminrunner'
  keys_dir = os.path.expanduser('~/.gnupg')
  restart_command = ['./adminrunner.py']
  restart_command.extend(argv[1:])
  restart_command.extend(['--log_dir=/export/hda3/logs',
                          '--box_keys_dir=' + keys_dir,
                          '--license_keys_dir=' + keys_dir])
  consecutive_kills_skipped = 0
  while True:
    if not check_healthz.CheckHealthz(2100):
      # If AdminRunner process exists, give it some time
      if reset_index.IsResetIndexInProgress(ent_home):
        # Everything may be slower during reset index.
        limit = MAX_RESET_INDEX_CONSECUTIVE_KILLS_TO_SKIP
      else:
        limit = MAX_CONSECUTIVE_KILLS_TO_SKIP
      if consecutive_kills_skipped < limit:
        # Check if adminrunner process exists
        (err, pidstring) = python_kill.Kill('adminrunner.py', '2100',
                                            print_only=1)
        # if there is no err and pidstring is '', adminrunner is gone.
        # otherwise, we assume it is alive and wait for a while
        if err != 0 or pidstring != '':
          consecutive_kills_skipped += 1
          time.sleep(CHECK_RESTART_INTERVAL)
          continue

      # Start/restart adminrunner, clear ResetIndexInProgress status
      consecutive_kills_skipped = 0
      reset_index.ClearResetIndexStatus(ent_home)
      print "Killing adminrunner..."
      python_kill.Kill('adminrunner.py', '2100')
      print "Restarting adminrunner..."
      subprocess.Popen(restart_command, cwd=adminrunner_dir)
      # Give it some extra time after startup.  Loading and validating
      # large number of collections and frontends with all large number of
      # keymatches etc can take a long time and adminrunner doesn't respond
      # to health checks during this time.
      time.sleep(SLEEP_AFTER_RESTART)
    else:
      consecutive_kills_skipped = 0
      time.sleep(CHECK_RESTART_INTERVAL)

if __name__ == '__main__':
  main(sys.argv[1:])

#!/usr/bin/python2.4
#
# (c) 2001-2007 Google Inc.
# sanjeev@google.com
#
# Simple cron command wrapper
#
###############################################################################
"""
Usage:
     run_cron_command.py <command>
     e.g.: run_cron_command.py "/etc/rc.d/init.d/logcontrol_4.6.4 babysit"
"""
###############################################################################


import sys
import string
import commands
import socket
import os

from google3.pyglib import logging

def run_command(command):
  status = os.system('( %s ) 2>&1 </dev/null' % (command))
  if status != 0:
    cmd_line = string.join(map(commands.mkarg, sys.argv), ' ')
    logging.error('cron command failed on %s. Command run: %s, Status: %s' %
                  (socket.gethostname(), cmd_line, status))

if __name__ == '__main__':
  if len(sys.argv) == 2:
    cmd = sys.argv[1]
    logfile = '/tmp/cron_command.log'
    if not os.path.exists(logfile):
      logging.set_logfile(open(logfile, 'w'))
      os.chmod(logfile, 0666)
    else:
      logging.set_logfile(open(logfile, 'a'))
    run_command(cmd)
  else:
    # Don't use sys.exit(__doc__) because this script must always return 0
    print __doc__
  sys.exit(0)

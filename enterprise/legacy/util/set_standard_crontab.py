#!/usr/bin/python2.4
#
# (c) 2000 Google inc
# first version: cpopescu@google.com
# rewrite by: naga@google.com
#
# This sets a standard crontab for a standard machine -
#
# ----- ONLY collect_logs and syslog_logs are left here ----->
#  TODO: move them in cron.5min
#
###############################################################################
"""
Usage:
      set_standard_crontab.py <enthome>
"""
###############################################################################

import commands
import os
import pwd
import string
import sys

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import entconfig

###############################################################################

# cmds will be run from MAIN_GOOGLE3_DIR/enterprise/legacy/scripts, so no need
# to have an explicit cd cmd as the first one
def CronTabEntry(config, timespec, cmds, log_file, source_env):
  cmd = "(" + string.join(cmds, '; ') + ") >& " + log_file
  script_dir = config.var('MAIN_GOOGLE3_DIR') + "/enterprise/legacy/util"
  str = "( %s; cd %s && ./run_cron_command.py %s ) &> /dev/null" % (
    source_env, script_dir, commands.mkarg(cmd))
  str = "\n\n" + timespec + '\t ' + str + '\n'
  return str

###############################################################################

def main(enthome):

  config = entconfig.EntConfig(enthome)
  if not config.Load():  sys.exit(__doc__)

  user = pwd.getpwuid(os.getuid())
  if (user[0] != config.var('ENTERPRISE_USER')):
    sys.exit("user %s cannot run this script; expected user is %s"%(
      user[0], config.var('ENTERPRISE_USER')))

  ENTID_TAG = "ENT_ID=%s_crawl" % config.var('VERSION')
  tabs = []
  logging.info("starting to fill tabs..")
  # Setup standard jobs
  every_ten_minutes = "*/10 * * * *"
  conf_dir = config.var('ENTERPRISE_HOME') + "/local/conf"
  source_env = ". /etc/profile; . %s/ent_bashrc " % conf_dir

  logging.info("preparing collect_logs.py entry..")
  log_collect_cmd = "cd ../logs;"\
                    "%s ./collect_logs.py %s" % (ENTID_TAG, enthome)
  log_collect_log_file = "/%s/cronLogCollectOut_%s" % (
    config.var('LOGDIR'), config.var('VERSION'))

  tabs.append( CronTabEntry(config, every_ten_minutes,
                            (source_env, log_collect_cmd),
                            log_collect_log_file, source_env))

  logging.info("preparing syslog_logs.py entry..")
  syslog_log_cmd = "cd ../logs;"\
                   "%s ./syslog_logs.py %s" % (ENTID_TAG, enthome)
  syslog_log_logfile = "/%s/cronSyslogLogOut_%s" % (
    config.var('LOGDIR'), config.var('VERSION'))

  tabs.append( CronTabEntry(config, every_ten_minutes,
                            (source_env, syslog_log_cmd),
                            syslog_log_logfile, source_env))

  # write out a temp cron tab
  tmp_cron_file = "%s/tmp/crawl_cron_%s" % (
    config.var('ENTERPRISE_HOME'), config.var('VERSION'))
  fout = open(tmp_cron_file, "w")
  fout.write(string.join(tabs))
  fout.close();
  os.system("crontab -l|grep -v %s| cat - %s > %s_" % (ENTID_TAG,
                                                       tmp_cron_file,
                                                       tmp_cron_file))
  #user_arg = "-u %s " % crontab_user
  os.system("crontab %s_" % tmp_cron_file)
  #os.system("rm -f %s" % tmp_cron_file)  # remove temp file

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1])

###############################################################################

#!/usr/bin/python2.4
#
# Copyright 2001-2003 Google, Inc.
# naga@google.com
#
###############################################################################

import time
import os
import string
import commands

from google3.enterprise.legacy.scripts import ent_service
from google3.enterprise.legacy.util import E
from google3.pyglib import logging

from google3.enterprise.legacy.util import port_talker
from google3.enterprise.legacy.util import find_main
from google3.enterprise.legacy.util import python_kill
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.core import core_utils

# We force restart every so often
FORCED_RESTART_INTERVAL = 3600 * 24 # 1 day

###############################################################################

class web_service(ent_service.ent_service):

  def __init__(self):
    # Run web_service on all nodes, but it will only run Admin Console
    # on the main
    ent_service.ent_service.__init__(self, "web", 0, "2minly", 1, 3600)

  # Override init_service to set some members
  def init_service(self, ent_home):
    ent_service.ent_service.init_service(self, ent_home)

    self.status_file = "%s/last_web_restart_%s" % (self.tmpdir, self.version)
    self.loopAdminConsole_pid_file = E.GetPidFileName('loop_AdminConsole')
  #############################################################################

  # Operation overrides
  
  def activate(self):
    """ Override this for some extra links to be done / crontab"""
    self.record_restart()
    return ent_service.ent_service.activate(self)

  def deactivate(self):
    ent_service.ent_service.deactivate(self)

    return 1

  def stop(self):
    return self._stop(op="stop")


  def babysit(self):
    if self.local_machine_is_main:
      if self.is_time_to_restart():
        self.record_restart()
        self._stop(op="babysit")
        # adjust gsa main node. This only applies to clusters, as
        # desired_gsa_main_node will be None for one-way.
        desired_gsa_main_node = core_utils.DesiredMainNode()
        if (desired_gsa_main_node != None and
            desired_gsa_main_node != self.local_machine):
          is_testver = install_utilities.is_test(self.version)
          find_main.ForceMain(desired_gsa_main_node, is_testver)
          return 1
      return self._start(op="babysit")
    else:
      return self._stop(op="babysit")

  def start(self):
    logging.info(" -- starting web service -- ")
    if self.local_machine_is_main:
      logging.info("(%s) I am the main restarting loop_AdminConsole.py" % (
        self.main_machine))
      self._start(op="start")
    return 1

  def is_time_to_restart(self):
    """
    This is a very innocent way to restart webservice once a day.
    We restart http and tomcat once every day between 12 AM and 5 AM.
    We save the time of the last restart in a file.
    """
    now = time.time()
    hour_now = string.atoi(time.strftime("%H", time.localtime(now)))
    try:
      last_time = string.atof(open(self.status_file, "r").read())
    except:
      return 1
    return ( now - last_time > FORCED_RESTART_INTERVAL ) and ( hour_now < 5 )

  def record_restart(self):
    # Record the restart
    open(self.status_file, "w").write("%s" % time.time())

  def is_admin_console_alive(self, sleep_time):
    """Check whehter AdminConsole is alive on the localhost."""
    # This just tries to establish a connection to verify whether it is alive
    status, response = port_talker.TCPTalk('localhost', 8000, sleep_time)
    return not status

  def find_and_kill_loop_adminconsole(self):
    # Command line to list pid's associated with loop_AdminConsole
    FIND_LOOP_ADMINCONSOLE_CMD = ("ps -e -o pid,args --width 100 | "
                                  "grep loop_AdminConsole.py | grep -v grep | "
                                  "awk '{print $1}' | tr '\n' ' '")
    pids = commands.getoutput(FIND_LOOP_ADMINCONSOLE_CMD)
    if len(pids) > 0:
      kill_cmd = 'kill -9 %s' % (pids)
      logging.info("Running: %s" % kill_cmd)
      os.system(kill_cmd)

  def kill_adminconsole(self):
    python_kill.KillServicesListeningOn(['8000', '9411'])
    time.sleep(3.0)
    python_kill.KillServicesListeningOn(['8000', '9411'], signal='-KILL')

  def _start(self, op):
    """ Called by both babysit and stop operations:
    Args:
        op: If op ==  "start", use ps to kill loop so that all
        loops are caught. For regular babysits, dont use ps.
    Returns: 1 always (legacy reasons. TODO(vish): fix later)
    """
    if op == 'start':
      self.find_and_kill_loop_adminconsole()
      self.kill_adminconsole()
    
    else:
      try:
        loopAdminConsole_pid = string.atoi(open(self.loopAdminConsole_pid_file, "r").read())
      except IOError:      # it is OK if the pid file has been removed
        pass
      else:
        if loopAdminConsole_pid:
          kill_cmd = "kill -9 %d" % loopAdminConsole_pid
          logging.info("Running: %s" % kill_cmd)
          os.system(kill_cmd)

    sso_rules_log_file = self.cp.var('SSO_RULES_LOG_FILE')
    sso_log_file = self.cp.var('SSO_LOG_FILE')
    sso_serving_efe_log_file = self.cp.var('SSO_SERVING_EFE_LOG_FILE')
    sso_serving_headrequestor_log_file = self.cp.var('SSO_SERVING_HEADREQUESTOR_LOG_FILE')
    # on one-way, gfs_aliases = ''
    gfs_aliases = self.cp.var('GFS_ALIASES')
    external_web_ip = self.cp.var('EXTERNAL_WEB_IP')
    sitesearch_interface = self.cp.var('SITESEARCH_INTERFACE')
    license_notices = self.cp.var('LICENSE_NOTICES')

    try:
      os.system('cd %s ; ./loop_AdminConsole.py %s %s %s %s %s %s %s %s>> '
                '/%s/loop_AdminConsole  2>&1 &' % (self.scripts_dir,
                             sso_rules_log_file,
                             sso_log_file,
                             sso_serving_efe_log_file,
                             sso_serving_headrequestor_log_file,
                             external_web_ip,
                             sitesearch_interface,
                             license_notices,
                             gfs_aliases,
                             self.logdir))
    except:
      logging.error("Restarting loop admin console failed. Exception: %s" % str(sys.exc_info()[:2]))
      return 1
    return 1

  def _stop(self, op):
    """ Called by both babysit and stop operations:
    Args:
        op:
            On Main: if op == "stop", kill the adminconsole also.
            If op is babysit, just restart the loop. The loop will overwrite
            the pid file.
            On non-mains: If pid file exists, kill entire process group (include loop and admin console)
            Remove pid file.
    Returns:
        1 always (legacy reasons. TODO(vish): fix later)
    """

    # kill the loop_AdminConsole process and remove the pid file, if
    # the pid in loop_AdminConsole.pid is a pid of a loop_AdminConsole
    # process
    try:
      loopAdminConsole_pid_str = open(self.loopAdminConsole_pid_file,
                                      "r").read()
      if not self.local_machine_is_main:
        logging.info('Killing admin console and loop')
      try:
        while 1:
          pid_cmdline = open('/proc/%s/cmdline' % loopAdminConsole_pid_str,
                             'r').read()
          if (pid_cmdline.find('loop_AdminConsole.py') != -1
              and len(loopAdminConsole_pid_str) > 0):
            kill_cmd = "kill -9 %s" % loopAdminConsole_pid_str
            logging.info("Running: %s" % kill_cmd)
            os.system(kill_cmd)
            time.sleep(1)
          else:
            break
      except IOError:                      # the process does not exist
        pass
      os.system("rm -f %s" % self.loopAdminConsole_pid_file)
    except IOError:                        # the pid file does not exist
      pass

    if self.local_machine_is_main:
      try:
        if op == 'stop':
          self.find_and_kill_loop_adminconsole()
          self.kill_adminconsole()
          return 1
      except:
        logging.error("Stopping loop admin console failed. Exception: %s" % str(sys.exc_info()[:2]))
        return 1
    else:
      # this machine is not main.
      # Just be doubly sure, kill any rogue loops and the admin console using ps
      # even though we have the pid
      # Make really really sure that admin console is dead for 5 s
      while 1:
        self.find_and_kill_loop_adminconsole()
        self.kill_adminconsole()
        time.sleep(5)
        ac_alive = self.is_admin_console_alive(1) # check if admin console is alive. give it
                                                  # 1s to respond.
        if ac_alive:
          logging.info('admin console is not dead. Trying again after 5s.')
        else:
          # Ok, now we are really sure admin console and loop are dead.
          break

      return 1

###############################################################################

if __name__ == "__main__":
  import sys
  web = web_service()
  web.execute(sys.argv)

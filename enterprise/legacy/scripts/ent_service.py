#!/usr/bin/python2.4
#
# (c) 2002 and onwards Google, Inc.
# cpopescu@google.com
#
# A base class for enterprise services.
# Enterprise services are system services that can be activated/deactivated,
# started/stopped and babysat.
#
# The stub that resides in /etc/rc.d/init.d call the actual script that resides
# under <enthome>/local/google3/enterprise/legacy/scripts.
# This stub is invoked periodically by crom from another stub in
# /etc/crond.Xminly with 'babysit' mode.
#
# Enterprise services in are responsible for starting/stopping and managing
# parts of the entire system. The way to implement this is by defining children
# of ent_service (defined in this file) and overriding various functions to
# start/stop/babysit your part of the system.
# ent_system provides activation/deactivation, initialization and the actual
# execution of the requests. Part of initilaization is the reading of the
# crawl parameters that are held in the self.cp member.
#
# The constructor of a child service should call the ent_service constructor
# to inform about the specifics of the service (like the service name etc).
#
# If you want to construct a service please follow the example of one of the
# other existing services, like cm_service.py
#
###############################################################################

import sys
import string

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.util import find_master
from google3.enterprise.legacy.util import E
from google3.pyglib import logging

from google3.enterprise.core import core_utils
###############################################################################

class ent_service:

  def __init__(self, service_name, performs_only_on_master, service_cron_time,
               check_previous_cron_job=0, secs_to_kill_previous_job=1800):
    """
    Initializes the service. The children have to call this in order to
    initialize some basic facts about the service:

    service_name -- the name of the service ('serve'/'crawl' etc)
    performs_only_on_master -- if the service performs other operations
                               than activet/deactivate only on master machine
    service_cron_time -- the dir where the cron script kicks in
                         (5minly/2minly etc)
    check_previous_cron_job -- if the previous cron job is running, don't
                               run this one
    secs_to_kill_previous_job -- kill the previous cron job if it has
                                 been running for this many seconds. (Only
                                 meaningful when check_previous_cron_job
                                 is true)
    """
    self.service_name = service_name
    self.performs_only_on_master = performs_only_on_master
    self.service_cron_time = service_cron_time
    self.flags = None  # extra flags for this
    self.check_previous_cron_job = check_previous_cron_job
    self.secs_to_kill_previous_job = secs_to_kill_previous_job

  def execute(self, argv):
    """
    This executes the service given the command line arguments.
    The first two argument are 'ent_home' and 'task' than is it's the
    children job to parse the extra args if it wants by overriding parse_args
    """

    # Args parsing
    if len(argv) < 3:
      sys.exit(self.usage())

    # Get the first two arguments and intitialize
    self.init_service(argv[1])
    self.task = string.strip(argv[2])

    # Get the other arguments and call the parsing function
    flags_argv = [argv[0]]
    flags_argv.extend(argv[3:])
    self.parse_args(flags_argv)

    # Extra checks
    if not self.service_to_be_up():
      sys.exit('%s not active' % self.service_name)

    # check if the node is enabled
    testver = install_utilities.is_test(self.version)
    if core_utils.AmIDisabled(self.version, testver):
      logging.error('I am disabled.')
      sys.exit(-1)

    if (self.performs_only_on_master and
        self.task not in ("activate", "deactivate")):
      if not self.local_machine_is_master:
        logging.error('I am not the master')
        self.nop()
        sys.exit(0)


    if not self.task:
      sys.exit(self.usage())

    # Execute the operations behind a lock
    lockfile = "%s/%s_service_lock_%s" % (self.tmpdir,
                                          self.service_name,
                                          self.version)
    pidfile = "%s/%s_service_pid_%s" % (self.tmpdir,
                                          self.service_name,
                                          self.version)

    # Execute the task: unlocked on activate/deactivate /
    # locked else
    if self.task in ["activate", "deactivate"]:
      do_task(self, self.task)
    else:
      if self.check_previous_cron_job:
        # kill previous cron job if lockfile timestamp is too old
        valid_lock_duration = self.secs_to_kill_previous_job
        # for "stop" and "restart" task, do it immediately
        if self.task in ["stop", "restart"]:
          valid_lock_duration = 0
        E.exec_locked(lockfile, 1, do_task, (self, self.task,), {},
                      valid_lock_duration, pidfile)
      else:
        # Lock will time out after 60 rounds of 10 seconds
        E.exec_locked(lockfile, 60, do_task, (self, self.task,))

  def init_service(self, ent_home):
    """
    Does the actual initialization. Reads the config file in the
    cp (EntConfig) member and initializes some members for easy access
    to usual parameters
    """

    self.cp = entconfig.EntConfig(ent_home)
    if not self.cp.Load():
      sys.exit("Cannot load the config file %s" % self.cp.GetConfigFileName())

    # Get some params for easy access
    self.configfile    = self.cp.GetConfigFileName()
    self.version       = str(self.cp.var("VERSION"))
    self.entid_tag     = "ENT_ID=%s_%s" % (self.version, self.service_name)
    self.ent_user      = self.cp.var("ENTERPRISE_USER")
    self.ent_group     = self.cp.var("ENTERPRISE_GROUP")
    self.ent_bashrc    = self.cp.var("ENTERPRISE_BASHRC")
    self.ent_home      = self.cp.var("ENTERPRISE_HOME")
    self.googlebot_dir = self.cp.var("GOOGLEBOT_DIR")
    self.version_tmpdir= "%s/tmp" % self.cp.var("ENTERPRISE_HOME")
    self.tmpdir        = self.cp.var("TMPDIR")
    self.logdir        = self.cp.var("LOGDIR")
    self.datadir       = self.cp.var("DATADIR")
    self.scripts_dir   = ("%s/local/google3/enterprise/legacy/scripts" %
                          self.ent_home)
    self.util_dir      = ("%s/local/google3/enterprise/legacy/util" %
                          self.ent_home)
    self.machines      = self.cp.var("MACHINES")

    # The master depends on the install state : for active / test / install
    # we have the adminrunner on the master, else we get it from MASTER
    # parameter
    self.install_state = install_utilities.install_state(
      self.version, rootdir = self.cp.var('ENT_DISK_ROOT'))
    self.local_machine  = E.getCrtHostName()
    testver = install_utilities.is_test(self.version)
    if self.install_state in ["ACTIVE", "TEST", "INSTALL"]:
      try:
        self.master_machine = find_master.FindMasterUsingChubby(self.cp.var('VERSION'))
      except core_utils.EntMasterError, e:
        # Something is seriously wrong.
        logging.error("ERROR: Couldn't determine master")
        # Assume we aren't master, so we can at least do inactivate
        self.master_machine = None
    else:
      self.master_machine = self.cp.var("MASTER")

    self.local_machine_is_master = (self.local_machine == self.master_machine)

  def service_to_be_up(self):
    """
    Check if the service is ok to be up, by looking at the current
    state (active/inactive/testing etc)
    """
    services = install_utilities.state_services_to_start(
      install_utilities.install_state(
        self.version, rootdir = self.cp.var('ENT_DISK_ROOT')),
      self.machines)
    return self.service_name in services

  def activate(self):
    """
    activates this service and makes it's periodic cron script executable
    """
    E.exe_or_fail("/sbin/chkconfig --add %s_%s" % (
      self.service_name, self.version))
    E.exe_or_fail("chmod 755 /etc/cron.%s/cron_%s_%s" % (
      self.service_cron_time, self.service_name, self.version))

  def deactivate(self):
    """
    deactivate this service and macke the cron script unexecutable
    """
    E.exe_or_fail("/sbin/chkconfig --del %s_%s" % (
      self.service_name, self.version))
    E.exe_or_fail("chmod 644 /etc/cron.%s/cron_%s_%s" % (
      self.service_cron_time, self.service_name, self.version))

  def restart(self):
    """
    restarts the service (stop + start)
    """
    return self.stop() and self.start()

  def parse_args(self, argv):
    """ Parse extra args after the traditional first two args """
    return

  def nop(self):
    """
    Runs when the script is not supposed to run because the machine
    is not the master machine
    """
    return

  def usage(self):
    """ overide this if you support extra params """
    return """
Usage:
    %s_service.py <ent_home> <task> [<extra>]

task := start|stop|restart|babysit|activate|deactivate

extra :=
%s
    """ % (self.service_name, self.flags)

  #############################################################################

  # You MUST override these:

  def start(self):
    raise "Unimplemented", "Implemnet start"

  def stop(self):
    raise "Unimplemented", "Implemnet stop"

  def babysit(self):
    raise "Unimplemented", "Implemnet babysit"

###############################################################################

def do_task(service, task):
  """
  This is called after we aquired the service lock to perform the actual
  task
  """
  if   task == "babysit":    service.babysit()
  elif task == "start":      service.start()
  elif task == "stop":       service.stop()
  elif task == "activate":   service.activate()
  elif task == "deactivate": service.deactivate()
  elif task == "restart":    service.restart()
  else:
    sys.exit(service.usage())

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

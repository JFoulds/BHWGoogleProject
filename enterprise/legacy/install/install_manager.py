#!/usr/bin/python2.4
# Copyright (C) 2001 and onwards Google, Inc.

"""\
 This script is used to make a specific install active/inactive/serve on a
 cluster. This is needed as there may be more than one version of software
 present on a cluster..

 Typical Usage:
 ==============
    Say you installed version 2.5-1 using install.py, the next step would be
    logging onto one of the cluster machines, go into
    /export/hda3/2.5-1/local/google/enterprise/install directory and
    activate the install like this:

       ./install_manager.py --enthome=/export/hda3/2.5-1/ --makeactive
"""

__author__ = 'naga sridhar kataru <naga@google.com>'

import commands
import os
import string
import sys
import threading
import time

# This code allows execution of install_manager.py without first sourcing
# ent_bashrc (which sets GOOGLEBASE and PYTHONPATH). This is a convieniance for
# developers
if __name__ == "__main__":
  try:
    import sitecustomize
    googlebase = filter(None, string.split(sitecustomize.GOOGLEBASE, "/"))
    crt_path = filter(None, string.split(os.getcwd(), "/"))
    do_restart = googlebase[0:3] != crt_path[0:3]
  except:
    do_restart = 1

  if do_restart:
    cmd = ". %s/../../../../conf/ent_bashrc && cd %s && %s" % (
      os.getcwd(), os.getcwd(), string.join(map(commands.mkarg, sys.argv)))
    sys.exit(os.WEXITSTATUS(os.system(cmd)))

from google3.pyglib import logging
from google3.pyglib import flags
FLAGS = flags.FLAGS

from google3.enterprise.core import core_utils
from google3.enterprise.core import gfs_utils
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.install import version_utilities
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import find_master
from google3.enterprise.legacy.util import reconfigurenet_util
from google3.enterprise.legacy.util import svs_utilities
from google3.enterprise.util import borgmon_util
from google3.enterprise.util import sessionmanager_util

flags.DEFINE_string("enthome", None,
                    "Enterprise Home Directory (define this or config)")
flags.DEFINE_string("config", None,
                    "Config File Name (define this or enthome)")
flags.DEFINE_string("machines", None,
                    "Comma sepparated list of machines to take action for")
flags.DEFINE_boolean("makeactive", 0,
                     "Changes the state to active")
flags.DEFINE_boolean("makeserve", 0,
                     "Changes the state to serve")
flags.DEFINE_boolean("makeinactive", 0,
                     "Changes the state to inactive")
flags.DEFINE_boolean("maketesting", 0,
                     "Changes the state to testing")
flags.DEFINE_boolean("makeinstall", 0,
                     "Changes the state to install")
flags.DEFINE_boolean("list", 0,
                     "Lists the states")
flags.DEFINE_string("docoreop", None,
                    "Run a core op on all nodes concurrently. Core ops include "
                    "activate, inactivate, info, clean, init_dns, test_gfs "
                    "activate_gfs, inactivate_gfs, int_gfs, start_gfs, etc")
flags.DEFINE_boolean("coreonly", 0,
                     "Apply activate and inactivate operation to core services"
                     " only. Useful for debugging core service activation and "
                     "inactivation.")
flags.DEFINE_boolean("nonecoreonly", 0,
                     "Apply activate and inactivate operation to non-core "
                     "services only. Useful for debugging non-core service "
                     "activation and inactivation.")
flags.DEFINE_boolean("retry", 0,
                     "Retry connecting to a node if it is down.")
flags.DEFINE_boolean("reinitok", 0,
                     "OK to reinitialize core service data files. Useful when "
                     "core services cannot start up and it is OK to lose user "
                     "data")

class NodeInstallManager(threading.Thread):
  """Executes necessary operations for a particular node to activate/inactivate
  the node. It excludes any core services like chubby, chubby DNS etc..
  """
  def __init__(self, machine, ts, version, start_servs, stop_servs):
    threading.Thread.__init__(self)
    self.machine_ = machine
    self.services_to_start_ = start_servs
    self.services_to_stop_ = stop_servs
    self.version_ = version
    self.target_state_ = ts
    self.err_ = 0
    self.msg_ = None
    self.started_ = []
    self.stopped_ = []

  def stop_service(self, service):
    """
    Stops and deactivates the given service on the given machine
    """
    logging.info("DEACTIVATE: %s service %s on %s" % (
      service, self.version_, self.machine_))
    cmd = E.nonblocking_cmd("/etc/rc.d/init.d/%s_%s deactivate" % (
      service, self.version_))
    ret = E.exe("ssh %s %s" % (self.machine_, commands.mkarg(cmd)))
    if ret == 0:
      logging.info("STOP: %s service %s on %s" % (
          service, self.version_, self.machine_))
      cmd = E.nonblocking_cmd(
          "/etc/rc.d/init.d/%s_%s stop" % (service, self.version_))
      ret = E.exe("ssh %s %s" % (self.machine_, commands.mkarg(cmd)))
    return ret

  def start_service(self, service):
    """
    Activates and starts the given service on the given machine
    """
    logging.info("ACTIVATE: %s service %s on %s" % (
      service, self.version_, self.machine_))
    cmd = E.nonblocking_cmd(
      "/etc/rc.d/init.d/%s_%s activate" % (service, self.version_))
    ret = E.exe("ssh %s %s" % (self.machine_, commands.mkarg(cmd)))
    if ret == 0:
      logging.info("START: %s service %s on %s" % (
          service, self.version_, self.machine_))
      cmd = E.nonblocking_cmd(
          "/etc/rc.d/init.d/%s_%s start" % (service, self.version_))
      ret = E.exe("ssh %s %s" % (self.machine_, commands.mkarg(cmd)))
    return ret

  def run(self):
    # Stop all services on all machines
    ret = None
    for service in self.services_to_stop_:
      logging.info("STATUS: STOP %s service %s on %s" % (
        service, self.version_, self.machine_))
      func = lambda: self.stop_service(service)
      ret = try_repeatedly(func, success=0)
      if ret:
        self.msg_ = "Error stopping %s on %s." % (service, self.machine_)
        logging.error("STATUS: %s" % self.msg_)
        self.err_ = ret
        return
      self.stopped_.extend([service])
    # Change the STATE file
    # TODO(zsyed): Move STATE file to chubby.
    logging.info("STATE: version %s on %s: %s" % (
      self.version_, self.machine_, self.target_state_))
    if not install_utilities.set_install_state(
      self.machine_, E.getEnterpriseHome(), self.target_state_):
      # Well here is not clear that we want to exit half way ..
      logging.error("ERROR changing state on machine %s. " \
                    "Please rollback and try again" % self.machine_ )
      self.err_ = ret
      self.msg_ = "Cannot change STATE file."
      return
    # Start all services to be started
    for service in self.services_to_start_:
      logging.info("STATUS: START %s service %s on %s" % (
          service, self.version_, self.machine_))
      func = lambda: self.start_service(service)
      ret = try_repeatedly(func, success=0)
      if ret:
        self.msg_ = "Error starting %s on %s" % (service, self.machine_)
        logging.error("STATUS: %s" % self.msg_)
        self.err_ = ret
        return
      self.started_.extend([service])

  def print_status(self):
    """Prints the status of thread.
    """
    logging.info("NODE STATUS: %s: Ret Code: %s" %
                  (self.machine_, self.err_))
    logging.info("NODE STATUS: %s:  Message: %s" %
                  (self.machine_, self.msg_))
    logging.info("NODE STATUS: %s:  Started: %s" %
                  (self.machine_, self.started_))
    logging.info("NODE STATUS: %s:  Stopped: %s" %
                  (self.machine_, self.stopped_))

def verify_master(ver, testver):
  """Once GSA master has been elected, it will update chubby DNS to indicate the
  new master. This routine checks the DNS entry and makes sure the master is up.
  """
  master = core_utils.GetGSAMaster(ver, testver)
  if not master:
    logging.error('Error getting current GSA master from chubby.')
    return 0
  logging.info('%s is current GSA master.' % master)
  return 1

def intersection(l1, l2):
  """Returns common elements in two lists.
  """
  ret = []
  count = {}
  for l in l1:
    count[l] = 1

  for l in l2:
    if count.has_key(l):
      ret.append(l)

  return ret

def try_repeatedly(func, success=0, num_retry=3, delay=15, comment=''):
  """Execute func repeatedly, up to num_retry times or until the value
  success is obtained.  Delays by delay before retrying.
  Returns: last return value from func"""

  for i in range(0, num_retry):
    ret = func()
    if ret == success:
      return ret
    if i < num_retry-1:
      logging.error('%sError.  Retrying...' % comment)
      time.sleep(delay)
  return ret

# The GSA version that starts using the new NTP option
# Upgrading from older version than this requires the NTP options to be reset
NEW_NTP_OPTION_GSA_VERSION = '4.6.4'

class InstallManager:
  def __init__(self):
    self.cp_           = None
    self.machines_     = None
    self.target_state_ = None
    self.version_      = None
    self.enthome_      = None
    self.core_only_    = None
    self.nonecore_only_    = None
    self.retry_        = None
    self.core_op_      = None
    self.reinitok_     = None

  def parse_cmd_line_args(self, argv):
    try:
      argv = FLAGS(argv)  # parse flags
    except flags.FlagsError, e:
      sys.exit("%s\nUsage: %s ARGS\n%s" % (e, argv[0], FLAGS))

    if ( (FLAGS.enthome and FLAGS.config) or
         (not FLAGS.enthome and not FLAGS.config) ):
      sys.exit("Please specify only one of --enthome and --config")

    if FLAGS.makeactive:
      self.target_state_ = "ACTIVE"
    elif FLAGS.makeserve:
      self.target_state_ = "SERVE"
    elif FLAGS.makeinactive:
      self.target_state_ = "INACTIVE"
    elif FLAGS.maketesting:
      self.target_state_ = "TEST"
    elif FLAGS.makeinstall:
      self.target_state_ = "INSTALL"
    elif FLAGS.list:
      self.target_state_ = "LIST"
    elif FLAGS.docoreop:
      self.core_op_ =  FLAGS.docoreop
    if FLAGS.coreonly:
      self.core_only_ = 1
    if FLAGS.nonecoreonly:
      self.nonecore_only_ = 1
    if FLAGS.retry:
      self.retry = 1
    if FLAGS.reinitok:
      self.reinitok_ = 1

    if not self.target_state_ and not FLAGS.docoreop:
      sys.exit("Please specify one and only one of "\
               "--makeactive --makeserve --makeinactive "\
               "--maketesting --makeinstall --list or --docoreop")

    if self.core_only_ and self.nonecore_only_:
      sys.exit("Please specify only one of --coreonly and --nonecoreonly")

    if FLAGS.enthome:
      self.cp_ = entconfig.EntConfig(FLAGS.enthome)
    else:
      cf = config_factory.ConfigFactory()
      self.cp_ = cf.CreateConfig(FLAGS.config)

    if not self.cp_.Load():
      sys.exit("ERROR: Cannot load the config file")

    if FLAGS.machines:
      self.machines_ = map(string.strip, string.split(FLAGS.machines, ","))
    else:
      self.machines_ = self.cp_.var("MACHINES")

    self.version_ = self.cp_.var('VERSION')
    self.enthome_ = self.cp_.GetEntHome()
    E.ENTERPRISE_HOME = self.enthome_

  def change_install_state(self):
    """
    Tries to change the state of the present version to target_state.
    Returns true in case of success.
    Here is sumary of what it does:
      1. Get list of active nodes
      2. Get list of services to start and stop
      3. In case there is something to start
          a. reconfigure's net on all nodes after verifying quorum
          b. starts core servics
      4. Verifies there is a master elected.
      5. Starts thread for each node to start and stop the needed services
      6. Waits for output from each thread
      7. Calculates success of failure based on thread results
      8. Asks each thread to print its status regarding what services
         it actually started or stopped and what was the return code and
         error message if any.
    """
    if not install_utilities.safe_transition(self.version_,
                                             self.target_state_):
      return 0

    current_state = install_utilities.install_state(self.version_)

    start = time.time()
    # make sure svs is running
    svs_utilities.CheckSvsAlive(self.machines_)

    # get list of active nodes
    active_nodes = core_utils.GetLiveNodes(logging, self.retry_)
    ignore = core_utils.GetNodeFailures(core_utils.GetTotalNodes())
    # account for already inactive nodes
    ignore = ignore - (core_utils.GetTotalNodes() - len(active_nodes))
    ver = self.version_
    home = self.enthome_

    # See what we have to start / stop
    services_to_start = install_utilities.state_services_to_start(
      self.target_state_, self.machines_)
    services_to_stop = install_utilities.state_services_to_stop(
      install_utilities.install_state(self.version_), self.machines_)

    # Make some decisions
    total_nodes = len(self.cp_.var('ENT_ALL_MACHINES'))
    onebox = (total_nodes == 1)
    startcore = services_to_start and not onebox and not self.nonecore_only_
    checkquorum = startcore
    stopcore =  (services_to_stop and not onebox and not self.nonecore_only_
                 and self.target_state_ == 'INACTIVE')
    doservices = (not self.core_only_
                  and (services_to_start or services_to_stop))
    if self.target_state_ in ['INACTIVE']:
      # ent_core does not really know the state. install_manager
      # has to tell ent_core when "makeinactive"
      testver = install_utilities.install_state(self.version_)
    else:
      testver = self.target_state_ in ['TEST', 'INSTALL']
    # If it is onebox and target state is INSTALL, do not run reconfigure_net
    # This is to support pre 4.4 version migration code.
    reconfigurenet_enabled = not (onebox and (self.target_state_ == 'INSTALL'))

    # if stop coreonly services, check if none-core components are running
    if (install_utilities.install_state(self.version_) == 'ACTIVE' and
        self.target_state_ == 'INACTIVE' and self.core_only_):
      logging.fatal("cannot stop core services while none core services "\
                    "are running")

    # Execute the decisions
    if checkquorum:
      # We check quorum only when services are to be started.
      # We mainly need quorum for core services. For non core services like
      # crawl, logcontrol etc. we use users specified machines.
      core_utils.VerifyQuorum(active_nodes)

    # check if syslogd.conf and klogd.conf exist
    install_utilities.check_klogd_syslogd_conf(active_nodes, home)

    # Kill any spurious adminrunner/adminconsole processes if we are entering
    # TEST or ACTIVE mode.
    if self.target_state_ in ['TEST', 'ACTIVE']:
      install_utilities.kill_service(['adminrunner', 'adminconsole'],
                                     core_utils.GetNodes(1))

    # reconfigure without restarting gems
    success = 1
    if reconfigurenet_enabled and services_to_start:
      # check if we need to force NTP reconfig if this is to upgrade from 4.4
      force_ntp_reconfig = 0
      if self.target_state_ in ['TEST', 'ACTIVE']:
        last_version = install_utilities.get_latest_version(except_for=1)
        if (last_version is None or
            version_utilities.CmpVersions(last_version,
                                          NEW_NTP_OPTION_GSA_VERSION) > 0):
          force_ntp_reconfig = 1
      success = reconfigurenet_util.doReconfigureNet(self.cp_,
                  active_nodes, force_ntp_reconfig=force_ntp_reconfig)
      if not success:
        logging.error('reconfigurenet failed.')

    # if start nonecore services, check if core services are running
    if (not onebox and self.nonecore_only_ and
        self.target_state_ in ['TEST', 'ACTIVE']):
      core_running = install_utilities.is_core_running(ver, home,
                         active_nodes, ignore=ignore, testver=testver)
      if not core_running:
        logging.fatal("cannot start none core services "\
                      "when core services are not running")

    # start core services if needed
    if startcore and success:
      # Retry 3 times for master verification failures
      num_retry = 3
      # it is always OK to reinit core services if the version is in
      # INSTALLED state
      self.reinitok_ = install_utilities.reinit_core_ok(ver, home,
                         active_nodes, ignore=ignore, testver=testver)
      i = 1
      while i <= num_retry:
        # stop core services when retrying
        if i > 1:
          time.sleep(15)
          install_utilities.stop_core(ver, home, active_nodes, testver=testver)
          time.sleep(15)
        i = i + 1
        # Run ent_core --ver=<ver> --activate --gfs=0 through install_utilities.py
        success = install_utilities.start_core(ver, home, active_nodes,
                                               ignore=ignore,
                                               testver=testver,
                                               gfs=0)
        if not success:
          if i <= num_retry:
            logging.error('Error activating core services. Retrying...')
          elif self.reinitok_:
            # it is OK to ignore errors when trying to re-init core services
            install_utilities.reinit_core(ver, home, active_nodes, ignore=1,
                                          testver=testver)
            i = 1
            self.reinitok_ = None
          else:
            logging.error('Error activating core services.')
        else:
          # Make sure a master has been elected. If we go ahead without
          # verifying the master then it will take very long time for
          # services to be started. Making sure master is elected by now
          # results in very quick adminrunner startup.
          success = verify_master(ver, testver)
          if success:
            if not core_utils.InitDeadNodes(ver, testver, logging) == 0:
              logging.fatal('Error updating dead nodes to the lockserver.')
            break
          if i <= num_retry:
            logging.error('Error verifying the master. Retrying...')
          elif self.reinitok_:
            # it is OK to ignore errors when trying to re-init core services
            install_utilities.reinit_core(ver, home, active_nodes, ignore=1,
                                          testver=testver)
            i = 1
            self.reinitok_ = None
          else:
            raise core_utils.EntMasterError, ('Error getting current GSA master'
                                              ' from chubby.')
      # force gsa master on the desired node
      desired_gsa_master_node = core_utils.DesiredMasterNode()
      if desired_gsa_master_node is None:
        logging.fatal('No suitable node to run GSA master')
      logging.info('Forcing %s to become GSA master' % desired_gsa_master_node)
      find_master.ForceMaster(desired_gsa_master_node, testver)

      # make sure the transaction logs are in sync and start gfs
      success = install_utilities.start_gfs(ver, home, active_nodes,
                                            ignore=ignore,
                                            testver=testver)

      # make sure gfs master is not the GSA master node
      logging.info('Ensuring %s not to become GFS master' %
                   desired_gsa_master_node)
      gfs_utils.AvoidGFSMasterOnNode(ver, testver, desired_gsa_master_node)

    if doservices and success:
      node_threads = {}
      for n in self.machines_:
        node_threads[n] = NodeInstallManager(n, self.target_state_,
                                             self.version_,
                                             services_to_start,
                                             services_to_stop)

      # start node threads
      for (n, t) in node_threads.items():
        logging.info('STATUS: Starting thread for %s' % n)
        t.start()

      # wait for threads
      for (n,t) in node_threads.items():
        t.join()
        success = success and (t.err_ == 0)

      for (n,t) in node_threads.items():
        t.print_status()

    if stopcore and success:
      func = lambda: install_utilities.stop_core(ver, home, active_nodes,
                                          testver=testver)
      success = try_repeatedly(func, success=1)
      if not success:
        logging.error('Error inactivating core services.')

    # Start/Stop Borgmon and Reactor
    if self.cp_.var('ENT_ENABLE_EXTERNAL_BORGMON'):
      enable_external_borgmon = '--enable_external'
    else:
      enable_external_borgmon = '--noenable_external'
    borgmon_cmd = (
        "/export/hda3/%s/local/google3/enterprise/util/borgmon_util.py "
        "--ver %s --logtostderr %s" %
        (self.version_, self.version_, enable_external_borgmon))
    if success and current_state != self.target_state_:
      # 1) Stop Borgmon and Reactor if required
      if current_state in ['SERVE', 'TEST', 'ACTIVE']:
        E.execute(self.machines_,
                  "%s --mode %s --stop" % (borgmon_cmd, current_state),
                  None, 0)
      # 2) Start Borgmon and Reactor if required
      logging.info("target_state: %s" % self.target_state_)
      if self.target_state_ in ['SERVE', 'TEST', 'ACTIVE']:
        E.execute(self.machines_,
                  "%s --mode %s --start" % (borgmon_cmd, self.target_state_),
                  None, 0)

    # Start/Stop Session Manager only for oneways
    if core_utils.GetTotalNodes() == 1:
      if self.target_state_ in ['SERVE', 'TEST', 'ACTIVE']:
        sessionmanager_util.ActivateSessionManager(ver, testver)
      if self.target_state_ == 'INACTIVE' and success:
        sessionmanager_util.DeactivateSessionManager(ver, testver)

    # Kill any spurious adminrunner/adminconsole processes if we are entering
    # INACTIVE or SERVE mode.
    if self.target_state_ in ['SERVE', 'INACTIVE']:
      install_utilities.kill_service(['adminrunner', 'adminconsole'],
                                     core_utils.GetNodes(1))

    if self.target_state_ == 'INACTIVE' and success and not self.nonecore_only_:
      install_utilities.InactivateCleanup(ver, home, active_nodes)

    end = time.time()
    diff = (end - start)/60
    logging.info("STAT: change_install_state took %.2f minutes." % diff)
    return success

  def list(self):
    """
    Lists all versions
    """
    for version in install_utilities.get_installed_versions_list():
      print "%s: %s" % (version, install_utilities.install_state(version))
    return 1

  def do_core_op(self):
    """ Run a core op on all nodes concurrently.

    Core ops include activate, inactivate, info, clean, init_dns, test_gfs,
    activate_gfs, inactivate_gfs, int_gfs, start_gfs, etc.

    Returns:
      1 - successful. 0 - otherwise.
    """

    live_nodes = core_utils.GetLiveNodes(logging, self.retry_)
    active_nodes = intersection(live_nodes, self.machines_)

    ver = self.version_
    home = self.enthome_

    # Run the core op
    return install_utilities.do_core_op(self.core_op_, ver, home, active_nodes)

  def execute(self, argv):
    """
    Executes the requested command -- list or state transition
    """
    self.parse_cmd_line_args(argv)
    if self.target_state_ == "LIST":
      return self.list()
    elif self.core_op_:
      return self.do_core_op()
    else:
      return self.change_install_state()


if __name__=='__main__':

  im = InstallManager()
  ok = im.execute(sys.argv)
  if not ok:
    sys.exit("Install Manager failed")
  logging.info("STAT: install operation successful")
  sys.exit(0)

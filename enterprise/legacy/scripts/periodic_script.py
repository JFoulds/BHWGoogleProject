#!/usr/bin/python2.4
#
# (c) 2000 Google inc
# initial version: cpopescu@google.com
# rewrite by     : naga@google.com
# A script that is run when the machine starts and then periodically
#
###############################################################################
"""
Usage:
   periodic_script.py <enthome>
"""
###############################################################################

import commands
import sys
import os
import string
import traceback
import time
import httplib
import socket

from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import find_master
from google3.enterprise.legacy.util import port_talker
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import adminrunner_client
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.util import svs_utilities
import exceptions
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.util import os_utils
from google3.enterprise.legacy.util import reconfigurenet_util
from google3.enterprise.core import core_utils
from google3.enterprise.core import gfs_utils
from google3.enterprise.legacy.util import admin_runner_utils

GSA_MONITOR_COMMUNITY = 'gsa-monitor-community'

## Exceptions used ##
class Error(exceptions.Exception):
  """base error exception.
  """
  pass

###############################################################################

def sshd_alive_check(config):
  return 0 == os.system(". %s && alarm 90 ssh $HOSTNAME hostname" % (
    config.ENTERPRISE_BASHRC))

###############################################################################

def DetectMaster(machines, max_tries, time_sleep, ver):
  """Detects Master using chubby.

  Returns:
    master machine's name or None (if none found).
  """
  try_count = 0
  master = None
  while (try_count < max_tries) and (master is None):
    master = find_master.FindMasterUsingChubby(ver)
    if master is None:
      try_count += 1
      logging.info('Could not find master, sleeping for %d seconds...',
                   time_sleep)
      time.sleep(time_sleep)

  return master

###############################################################################


def IncreaseMasterCounter():
  ar = adminrunner_client.AdminRunnerClient("localhost", 2100)
  ar.IncreaseCounter(5 * 60 * 1000) # 5 minutes

###############################################################################


def IsAdminRunnerAlive(max_tries, sleep_time):
  """Check whehter AdminRunner is alive on the localhost."""

  try_count = 0
  is_alive = 0
  while try_count < max_tries:
    # This just tries to establish a connection to verify whether it is alive
    status, response = port_talker.TCPTalk('localhost', 2100, sleep_time)
    if status == 0:
      is_alive = 1
      break
    else:
      try_count += 1
      logging.info('Could not connect to adminrunner on localhost, '
                   'sleeping for %d seconds...', sleep_time)
      time.sleep(sleep_time)

  return is_alive

def StartAdminLoop(config, op='start'):
  """Start AdminRunner Loop as well as Loop for initial_config_Server"""

  install_state = install_utilities.install_state(config.VERSION)

  logging.info("Starting the AdminRunner")
  ar_args = []
  ar_args.append("--port=2100")
  ar_args.append("--enthome=%s" % config.ENTERPRISE_HOME)
  ar_args.append("--installstate=%s" % install_state)
  ar_args.append("--reset_status_cache_timeout=60")

  restart_loop_AdminRunner = 0
  if op == 'babysit':
    pidfile = E.GetPidFileName('loop_AdminRunner')
    pid = E.ReadPidFile(pidfile)
    if os_utils.GetAttr('pid', pid=pid, fallback_to_ps=0) == None:
      restart_loop_AdminRunner = 1

  if op == 'start' or restart_loop_AdminRunner:
    E.su_exe_or_fail(
      config.ENTERPRISE_USER,
      """ ps axwwwww | fgrep AdminRunner | fgrep -v fgrep | \
      colrm 7 | xargs kill -9 2> /dev/null; \
      . %(eb)s; \
      cd %(eh)s/local/google3/enterprise/legacy/scripts/ &&  \
      ENT_ID=%(v)s_crawl ./loop_AdminRunner.py \
      %(eh)s %(args)s >> \
      /%(ld)s/loop_AdminOut_`whoami` 2>&1 &""" % {
      'eh' : config.ENTERPRISE_HOME,
      'eb' : config.ENTERPRISE_BASHRC,
      'v' : config.VERSION,
      'ld' : config.LOGDIR,
      'args' : string.join(map(commands.mkarg, ar_args))
      })

  restart_loop_webserver_config = 0
  if op == 'babysit':
    pidfile = E.GetPidFileName('loop_webserver_config')
    pid = E.ReadPidFile(pidfile)
    if os_utils.GetAttr('pid', pid=pid, fallback_to_ps=0) == None:
      restart_loop_webserver_config = 1

  if (install_state != "INSTALL" and
      (op == 'start' or restart_loop_webserver_config)):
    logging.info("Starting webserver_config")
    E.su_exe_or_fail(
      config.ENTERPRISE_USER,
      """ ps axwwwww | fgrep webserver_config.py | fgrep -v fgrep \
      | colrm 7 | xargs kill -9 2> /dev/null; \
      . %s; \
      cd %s/enterprise/legacy/scripts/ && \
      ENT_ID=%s_crawl ./loop_webserver_config.py %s \
      >> /%s/loop_WebserverConfig_`whoami` 2>&1 &""" % (
      config.ENTERPRISE_BASHRC,
      config.MAIN_GOOGLE3_DIR, config.VERSION,
      config.GetConfigFileName(), config.LOGDIR))

###############################################################################

def BecomeMaster(config):
  """Becomes master -- runs set_standard_crontab.py and starts AdminRunner"""

  # Start our stuff
  StartAdminLoop(config)

  # Wait for adminrunner to start up
  if not IsAdminRunnerAlive(12, 10):  # max_tries, sleep_time
    raise Error, 'I am the master but could not start AdminRunner.'

  # start snmpd when becoming master
  enableSnmp()

  # Write NTP parameters of master into /etc/ntp.conf
  SetMasterNTP(config)

###############################################################################
def SetMasterNTP(config):
  """ Rewrite the content of the master-node /etc/ntp.conf file """

  global_file = config.GetConfigFileName()

  # full_config contains all the Enterprise environment variables.
  full_config = config_factory.ConfigFactory().CreateConfig(global_file)
  if not full_config.Load():
    logging.error("Cannot read file %s " % global_file)
  else:
    if full_config.var('NTP_SERVERS'):
      ntp_server_list = full_config.var('NTP_SERVERS')
      reconfigurenet_util.AddDefaultNTPServer(ntp_server_list)
      # combine list of NTP servers into a single comma-separated string.
      server_arg = ','.join(ntp_server_list)
      # Run a set-uid program to rewrite /etc/ntp.conf
      os.system("/usr/local/sbin/reconfigure_net NTP %s" % server_arg)
    else:
      logging.error("Missing variable NTP_SERVERS. Can not set master NTP. ")

###############################################################################

def AvoidGFSMasterOnNode(config, node):
  """ avoiding running primary gfs master on a node

  Arguments:
    config: instance of entconfig
    node:   'ent1'
  """

  ver = config.VERSION
  testver = install_utilities.is_test(ver)
  # first make sure there is a primary master
  out = gfs_utils.EnsureGFSMasterRunning(ver, testver)
  if out is not None:
    logging.error("GFSMaster_NoMaster alert detected, "
                  "but fix was not successful. Error message: [%s]" % out)
  else:
    gfs_utils.AvoidGFSMasterOnNode(ver, testver, node)
  # ensure gfs chunkservers are added after gfs master is running
  gfs_utils.AddGFSChunkservers(ver, testver, config.MACHINES)

def SetNonMasterNTP(master):
  """ Rewrite the content of the nonmaster-node /etc/ntp.conf file

  Args:
    master - "ent1"
  """

  os.system("/usr/local/sbin/reconfigure_net NTP %s" % master)

###############################################################################
def KillRedundantServices(config):

  crt_machine = E.getCrtHostName()
  servers = config.SERVERS

  for server_port, server_machines in servers.items():

    if crt_machine not in server_machines:
      response = port_talker.Talk("localhost", server_port, "v", 40)
      # kill the server if it is not supposed to run on the localhost
      if response[0]:
        server_to_kill = servertype.GetPortType(server_port)
        logging.info("kill service: %s" % server_to_kill)
        servertype.KillServer(server_to_kill, config, crt_machine,
                              server_port)

###############################################################################

def MasterKillMyself(config):

  util_dir = "%s/local/google3/enterprise/legacy/util" % config.ENTERPRISE_HOME

  # Stop AdminRunner
  for script in ["loop_AdminRunner.py",
                 "adminrunner.py",
                 "loop_webserver_config.py",
                 "webserver_config.py"]:
    E.su_exe_or_fail(config.ENTERPRISE_USER,
                     ". %s && cd %s && ./python_kill.py --binname=%s "\
                     "--kill_by_group" %
                     (config.ENTERPRISE_BASHRC, util_dir, script))

  KillProcessIfNotMaster(config)

###############################################################################
def KillProcessIfNotMaster(config):
  # kill babysitter
  util_dir = "%s/local/google3/enterprise/legacy/util" % config.ENTERPRISE_HOME
  E.killBabysitter(util_dir, config.GetConfigFileName(), config.VERSION)

  # stop snmpd when not a master
  disableSnmp()

###############################################################################

def ResyncWithMaster(google_config_file,
                     enterprise_home,
                     enterprise_user,
                     master) :

  scripts_dir = "%s/local/google3/enterprise/legacy/scripts" % enterprise_home

  enterprise_bashrc = "%s/local/conf/ent_bashrc" % enterprise_home
  E.su_exe_or_fail(
    enterprise_user,
    ". %s && cd %s && alarm 600 ./replicate_config.py %s %s" %
    (enterprise_bashrc, scripts_dir, master, google_config_file))
  SetNonMasterNTP(master)

###############################################################################

def WarmIndex(config):
  """ Warm the Enterprise FrontEnd and Index to prevent cold query latency.

  Forks another process at OS level instead of spawning another thread
  at Python runtime process level.  This is done to ensure any negative
  effects of the index warmer will not kill or hang the rest of periodic script.
  """
  file_location = ("%s/local/google3/enterprise/legacy/util/index_warmer.py"
                   % config.ENTERPRISE_HOME)
  os.system("%s &" % file_location)

###############################################################################

def GetAliveMachinesWithVersions(machines, config):
  cmd = ". %s; cd %s/enterprise/legacy/util; ./get_config_version.py %s" % (
    config.ENTERPRISE_BASHRC, config.MAIN_GOOGLE3_DIR, config.ENTERPRISE_HOME)

  (err, out) = commands.getstatusoutput(
    ". %s;cd %s/enterprise/legacy/util; ./ent_exec.py -q -a60 -b "\
    " -m \"%s\" -x \"%s\"" % (
      config.ENTERPRISE_BASHRC, config.MAIN_GOOGLE3_DIR,
      string.join(machines, " "), cmd))

  out = string.split(out, "\n")
  out = map(lambda p: string.split(p, "-"), out)
  out = filter(lambda p: len(p) == 2, out)

  ret = []
  for (version, machine) in out:
    try:
      ret.append((int(version), string.strip(machine)))
    except ValueError:
      # An Invalid answer is punished
      ret.append((0, string.strip(machine)))

  #  if we have less than 1/2 of machines, something is wrong... return Nonr
  if len(machines)/2 >= len(ret):
    return None

  #  else we return what we got
  ret.sort()
  return ret


###############################################################################
# SNMP Monitoring Utilities

def getSnmpStatus():
  '''Snmp Status as configured on GSA Box
  using Global Param ENT_ENABLE_SNMP
  Returns '1' if SNMP enabled, '0' otherwise'''
  try:
    host = 'localhost'
    port = 2100
    url = '/legacyCommand'
    postData = 'params get ENT_ENABLE_SNMP\n'
    h = httplib.HTTPConnection(host, port)
    h.request('POST', url, postData)
    r = h.getresponse()
    response = r.read()
    # remove last two line (ACKGoogle)
    lines = string.split(response, "\n")
    enabled = '0'
    if len(lines) > 2 and "NACKgoogle" != string.strip(lines[-2]):
      response = string.join(lines[:-2], "\n")
      try:
        dummy = {}
        exec(response, dummy)
        value = dummy['ENT_ENABLE_SNMP']
        enabled = '%s' %value
      except KeyError: pass
    return enabled
  except socket.error:
    # An exception is most likely because of adminrunner not running
    # in which case SNMP can be assumed to be disabled
    return '0'

def enableSnmp():
  '''Start the SNMP daemon if it is not runnning
     or not responding to queries '''
  try:
    r = os.popen('/etc/rc.d/init.d/snmpd status', 'r')
    l = r.readline()
    r.close()
    if l.find('running') == -1:
      os.system('/etc/rc.d/init.d/snmpd start > /dev/null')
    else:
      # status says running, try sending a query
      r = os.popen('snmpget -v 2c -c %s localhost \
          -t 5 .1.3.6.1.4.1.11129.1.1.1.0' % GSA_MONITOR_COMMUNITY, 'r')
      l = r.readline()
      if l.find('Timeout') != -1 or l.find('-1') != -1:
        # error SNMP agent not responding to known valid query
        os.system('/etc/rc.d/init.d/snmpd restart > /dev/null')
  except OSError:
    pass

def disableSnmp():
  '''Stop SNMP daemon if not master or not enabled'''
  os.system('/etc/rc.d/init.d/snmpd stop > /dev/null')

def monitorSnmp():
  '''See if snmp should be running
     if so start it, else stop it'''
  if getSnmpStatus() == '1':
    enableSnmp()
  else:
    disableSnmp()

def EnableGFS(config):
  """ Remove the DISABLED flag if GFS has disabled itself."""
  try:
    disabled_file = '%s/data/ent.gfsdata/DISABLED' % config.ENTERPRISE_HOME
    os.unlink(disabled_file)
    logging.error('GFS had disabled itself.  Removed %s' % disabled_file)
  except OSError:
    # File doesn't exist; this is good
    pass
  try:
    disabled_file = ('%s/data/gfs_master/ent.gfsmaster/DISABLED' %
                     config.ENTERPRISE_HOME)
    os.unlink(disabled_file)
    logging.error('GFS had disabled itself.  Removed %s' % disabled_file)
  except OSError:
    # File doesn't exist; this is good
    pass

def EnableNamed():
  """ Restart named if it is not running or not healthy. """
  os.system('(dig @127.0.0.1 -x 127.0.0.1 || service named restart) '
            '> /dev/null 2>&1')

def DnsConfig(config):
  """ On the virtual GSA, patch in DNS configuration. """
  product = config.ENT_CONFIG_TYPE
  if product == 'LITE' or product == 'FULL':
    change_ip_cmd = ('%s/support-tools/change_ip.par --use_current' %
                     config.ENTERPRISE_HOME)
    os.system(change_ip_cmd)

###############################################################################

def PeriodicScript(config):
  """
  If we have the FANCY_CLUSTER flag on we perform some master election
  """
  global apacheRecheck

  machines = config.MACHINES

  # The two determinants : if we run sshd and the list of active AdminRunners
  sshd_alive = sshd_alive_check(config)
  tries = 6
  sleep_time = 10
  master = DetectMaster(machines, tries, sleep_time, config.var('VERSION'))
  if master is None:
    raise Error, 'Could not find master in %d tries.' % tries

  logging.info('%s is the master' % master)

  if not sshd_alive:
    # No ssh running. I restart sshd
    # sshd is not running!? ..too bad
    logging.error("sshd is not running on this machine. "\
                  "restarting sshd.")
    os.system("/etc/rc.d/init.d/sshd restart >&/dev/null </dev/null");

  # The name of this machine
  crt_machine = E.getCrtHostName()
  if master == crt_machine:  # I am the master
    # make sure gfs master is not running on the same node on clusters
    if len(machines) > 1:
      AvoidGFSMasterOnNode(config, crt_machine)

    if IsAdminRunnerAlive(6, 10):  # max_tries, sleep_time
      # Lincense stuff -- incrrease the serving time count
      IncreaseMasterCounter()
      # babysit loop_AdminRunner and loop_webserve_config
      StartAdminLoop(config, op='babysit')
    else:  # I am the master but adminrunner does not seem to be running
      logging.info('I (%s) am the master but adminrunner does not seem to be'
                   'running.' % crt_machine)
      BecomeMaster(config)
  else:   # I am not the master
    resync_with_master = 1
    if core_utils.CanRunGSAMaster(crt_machine):
      if IsAdminRunnerAlive(1, 0):   # max_tries, sleep_time
        # Kills adminrunner related processes, webconfig.py
        # calls KillProcessIfNotMaster
        MasterKillMyself(config)
        resync_with_master = 0
      else:
        KillProcessIfNotMaster(config)
    if resync_with_master:
      ResyncWithMaster(config.GetConfigFileName(), config.ENTERPRISE_HOME,
                       config.ENTERPRISE_USER, master)

  # check all services and kill services I am not supposed to run
  KillRedundantServices(config)

###############################################################################

def main(argv):
  """ runs PeriodicScript() function in a loop"""
#  global MACHINES
#  global MAIN_GOOGLE3_DIR

  if len(argv) != 1:
    sys.exit(__doc__)

  try:
    logging.info("Running periodic_script (pid = %d)..." % os.getpid())
    config = entconfig.EntConfig(argv[0]) # user config
    if not config.Load():
      sys.exit("Cannot load the config file %s" % argv[0])

    PeriodicScript(config)
    svs_utilities.CheckSvsAlive(["localhost"])
    monitorSnmp()
    EnableGFS(config)
    EnableNamed()
    DnsConfig(config)
    admin_runner_utils.SyncOneboxLog(config)
    WarmIndex(config)
    logging.info("Finished periodic_script.")
  except:
    # collect the exception traceback so we know what went wrong
    (t, v, tb) = sys.exc_info()
    logging.error(
      "\nPeriodic script: Fatal Error:\n" + "=======================\n" +
      string.join(traceback.format_exception(t, v, tb)))

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

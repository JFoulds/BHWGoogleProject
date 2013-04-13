#!/usr/bin/python2.4
#
# Copyright 2005 Google Inc.
# All Rights Reserved.

"""
Utility functions for reconfigure_net

Refactored from params_handler.py
"""

__author__ = 'nshah@google.com (Nirav Shah)'

import sys
import string
import commands
import threading
import os
import time
import random
import copy

from google3.pyglib import logging
from google3.enterprise.legacy.checks import network_diag

from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E

def ExecuteWrapper(machines, commandLine, out, alarm, verbose = 1,
                   forceRemote = 0, enthome=None, num_tries=1):
  """Thin wrapper over E.execute as we need process's return code (parameter to
  exit()) and E.execute returns exit status. Too late to modify E.execute()
  method implementation as there is a lot of code that already calls this method.
  Can't confirm whether any code has come to rely on the fact that E.execute
  returns exit status code instead of process's return code. Refer E.execute()
  for it's documentation"""
  ret = 0
  for trial in range(num_tries):
    ret = E.execute(machines, commandLine, out,
                    alarm, verbose, forceRemote, enthome)
    if os.WIFEXITED(ret):
      # child process exit codes are multiplied by 256, so undo this
      ret = os.WEXITSTATUS(ret)
    if ret == 0 or (trial + 1) == num_tries:
      # either we succeed or this was the last try (there is no point in
      # sleeping after the last try)
      break
    logging.warn('%d: Execution of %s failed. Sleeping for 5 seconds...' %
                 (trial, commandLine))
    time.sleep(5)
  return ret

def FindDefaultNTPServer():
  """ Find a default public NTP server.

  For now, we just use "pool.ntp.org" as the default NTP servers.
  "pool.ntp.org" uses DNS round robin to make a random selection from a pool
  of time server.
  Returns:
    'pool.ntp.org'
  """

  return 'pool.ntp.org'

def AddDefaultNTPServer(ntp_server_list):
  """ check to see if a default ntp server needs to be added to the list

  Args:
    ntp_server_list: ['time1.corp.google.com', 'time2.corp.google.com']
  """

  any_good_ntp = 0
  for ntp_server in ntp_server_list:
    (stat, out) = network_diag.check_ntpdate_output(ntp_server)
    if stat == 0 and 'stratum' in out and int(out['stratum']) < 15:
      any_good_ntp = 1
      break
    else:
      logging.warn('Bad NTP server: %s (stat=%d, %s)' % (ntp_server, stat, out))
  if not any_good_ntp:
    default_ntp_server = FindDefaultNTPServer()
    if default_ntp_server not in ntp_server_list:
      ntp_server_list.append(default_ntp_server)

def doReconfigureNet(config, machines=None, i_am_master=1,
                     force_ntp_reconfig=0):
  """ reconfigure serveriron, DNS, NTPs, iptables, timezone as needed.
  Force NTP server reconfiguration if force_ntp_reconfig=1
  """

  # first we need to reconfigure our external IP address
  ret1 = ret2 = ret4 = ret5 = ret6 = ret8 = 0

  configType = config.var('ENT_CONFIG_TYPE')
  ent_home = E.getEnterpriseHome()
  if not machines:
    machines = config.var('MACHINES')

  # Sanity check
  if not config.var('EXTERNAL_WEB_IP'):
    logging.error('config file is missing EXTERNAL_WEB_IP, probably corrupt')
    raise Exception, 'config file is missing EXTERNAL_WEB_IP, probably corrupt'

  if config.var('USE_DHCP') is None:
    logging.error('config file is missing USE_DHCP, probably corrupt')
    raise Exception, 'config file is missing USE_DHCP, probably corrupt'

  if config.var('DNS_DHCP') is None:
    logging.error('config file is missing DNS_DHCP, probably corrupt')
    raise Exception, 'config file is missing DNS_DHCP, probably corrupt'

  tries = 3 # default for CLUSTER and PILE configuration
  if configType in ["SUPER", "ONEBOX", "MINI", "LITE", "FULL"]:
    tries = 1
    # reconfigure eth0 to dhcp mode
    if config.var('USE_DHCP') == 1:
      ret1 = ExecuteWrapper(
        machines,
        "%s LOCALNET DHCP %s" % (
        C.RECONFIGURE_COMMAND % ent_home,
        config.var('ONEBOX_NETCARD_SETTINGS'),
        ), None, 600, num_tries = tries)
      logging.info("reconfigure eth0 IP to dhcp mode: %s" % ret1)
    else:
      ret1 = ExecuteWrapper(
        machines,
        "%s LOCALNET %s %s %s %s" % (
        C.RECONFIGURE_COMMAND % ent_home,
        config.var('EXTERNAL_WEB_IP'),
        config.var('EXTERNAL_NETMASK'),
        config.var('EXTERNAL_DEFAULT_ROUTE'),
        config.var('ONEBOX_NETCARD_SETTINGS'),
        ), None, 600, num_tries = tries)
      logging.info("reconfigure eth0 IP address: %s" % ret1)
  elif "CLUSTER" == configType:
    # reconfigure serveriron IP address
    cmd = "(sleep 5; %s SERVERIRON %s %s %s %s %s %s %s %s %s >&/dev/null " \
          "</dev/null)" % (
      C.RECONFIGURE_COMMAND % ent_home,
      "%s/local/conf/defaults/" % ent_home,
      commands.mkarg(config.var("EXTERNAL_SWITCH_IP")),
      commands.mkarg(config.var("EXTERNAL_WEB_IP")),
      commands.mkarg(config.var("EXTERNAL_CRAWL_IP")),
      commands.mkarg(config.var("EXTERNAL_NETMASK")),
      commands.mkarg(config.var("EXTERNAL_DEFAULT_ROUTE")),
      commands.mkarg(str(config.var("EXTERNAL_WEB_PORT"))),
      commands.mkarg(str(config.var("SERVERIRON_AUTONEGOTIATION"))),
      commands.mkarg(str(config.var("ENT_ENABLE_EXTERNAL_SSH"))),
      )
    t = threading.Thread(target=E.execute,
                         args=([E.getCrtHostName()], cmd, None, 60))
    t.start()
    logging.info("serveriron IP address reconfigured")


  # we don't want to change ANYTHING on PILE clusters
  if "PILE" != configType:
    # DNS needs to be set everywhere
    dns_server = "\"\""
    dns_searchpath = "\"\""
    if config.var('BOT_DNS_SERVERS') != None:
      dns_server = config.var('BOT_DNS_SERVERS')
    if config.var('DNS_SEARCH_PATH') != None:
      dns_searchpath = config.var('DNS_SEARCH_PATH')
    if config.var('DNS_DHCP') != 1:
      ret8 = ExecuteWrapper(
          machines,
          "%s DNSMODE STATIC" % (
          C.RECONFIGURE_COMMAND % ent_home
          ),  None, 600, num_tries = tries)
      logging.info("setting DNS mode to STATIC: %s" % ret8)
      ret2 = ExecuteWrapper(
        machines,
        "%s DNS %s %s" % (
        C.RECONFIGURE_COMMAND % ent_home,
        commands.mkarg(dns_server),
        commands.mkarg(dns_searchpath),
        ), None, 600, num_tries = tries)
      logging.info("reconfigure DNS: %s" % ret2)
    else:
      ret8 = ExecuteWrapper(
          machines,
          "%s DNSMODE DHCP" % (
          C.RECONFIGURE_COMMAND % ent_home
          ),  None, 600, num_tries = tries)
      logging.info("setting DNS mode to DHCP: %s" % ret8)

    # NTP is special: all machines but the master must set their
    # NTP server to the master, the master to the external one.
    # However, It can take 3 minutes for the stratum level of the master
    # node to be set. Before that, non-master nodes using the master
    # node to do "ntpdate" may return "no server suitable for synchronization
    # found" error.
    # To fix the problem, we just use the external ntp servers for all nodes.
    # Later, periodic script will set the non-master nodes to use the master
    # node. (periodic script will only set it once as long as master does
    # not switch)
    ntpServers = "\"\""
    if config.var('NTP_SERVERS') != None:
      ntp_server_list = copy.copy(config.var('NTP_SERVERS'))
      AddDefaultNTPServer(ntp_server_list)
      ntpServers = string.join(ntp_server_list, ",")

    if i_am_master:
      ret4 = ExecuteWrapper(
        machines,
        "%s NTP %d %s" % (
        C.RECONFIGURE_COMMAND % ent_home,
        force_ntp_reconfig,
        commands.mkarg(ntpServers)),
        None, 600, num_tries = tries)
      logging.info("reconfigure NTP: %s" % ret4)

  # whenever we print dates, we want to include the timezone. Since
  # the timezone may change on the machine (through config interface),
  # and java VM does not pick this change up automatically,
  # we keep track of the timezone here
  ret5 = ExecuteWrapper(
    machines,
    "%s TIMEZONE %s" % (
    C.RECONFIGURE_COMMAND % ent_home,
    commands.mkarg(config.var('TIMEZONE'))),
    None, 600, num_tries = tries)
  logging.info("reconfigure TIMEZONE: %s" % ret5)

  # iptables
  if configType in ["SUPER", "ONEBOX", "LITE", "FULL"]:
    iptables_file = "%s/local/conf/defaults/iptables.onebox" % ent_home
  elif "MINI" == configType:
    iptables_file = "%s/local/conf/defaults/iptables.mini" % ent_home
  elif "CLUSTER" == configType:
    iptables_file = "%s/local/conf/defaults/iptables.cluster" % ent_home
  else:
    iptables_file = "%s/local/conf/defaults/iptables.open" % ent_home
  ret6 = ExecuteWrapper(
    machines,
    "%s IPTABLES %s %s %s" % (
    C.RECONFIGURE_COMMAND % ent_home,
    iptables_file,
    commands.mkarg(str(config.var("ENT_ENABLE_EXTERNAL_SSH"))),
    commands.mkarg(str(config.var("ENT_ENABLE_EXTERNAL_BORGMON"))),
    ), None, 600, num_tries = tries)
  logging.info("reconfigure IPTABLES: %s" % ret6)

  # return value from each reconfigurenet call is:
  # 0 : no change
  # 1 : changed
  # 2+: error (but we report no errors)

  # _our_ return value is if any of them failed
  ret = (ret1 <= 1 and ret2 <= 1 and ret4 <= 1 and
         ret5 <= 1 and ret6 <= 1 and ret8 <= 1)
  return ret


if __name__ == '__main__':
  sys.exit('Import this module')

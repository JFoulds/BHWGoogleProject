#!/usr/bin/python2.4
#
# (c) 2000 Google inc
# sanjeevk@google.com
# A set of utilities to start the svs and parse its output
# When run with enthome and a machine name it restarts
# svs on that machine. If machine name is not specified
# it restarts svs on the local machine
# Usage is
# ./svs_utilities.py <enthome> [machine]

import sys
import string
import time
from google3.enterprise.legacy.util import port_talker

from google3.pyglib import logging
import commands

from google3.enterprise.core import core_utils
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.util import os_utils

##
## We expect to receive this from the svs in order to validate the svs version
##
## NOTE: Please modify as necessary (from monitoring rpm)
##
SVS_VERSION = [1, 2, 15]
# Desired nice value for SVS.
SVS_NICE_VALUE = -15
SVS_PID_FILE = '/var/run/system_variable_server.pid'

# Takes the v command output from the svs
# and checks if the version of svs running
# is >= SVS_VERSION
def CheckSvsVersion(response):
  response = string.split(response, '\n')
  try:
    for line in response:
      elements = string.split(line, " ")
      if elements[0] != "svs-version": continue
      ver = string.split(elements[1][1:-1], "-")
      ver[0] = map(string.atoi, string.split(ver[0], "."))

      # special case to handle the 2.3-2gsa patch version
      if ver[1][-3:] == 'gsa':
        ver[1] = ver[1][0:-3]
      ver[1] = string.atoi(ver[1])
      ver = [ver[0][0], ver[0][1], ver[1]]
      if ver == SVS_VERSION: return 1
      for ndx in range(len(ver)):
        if SVS_VERSION[ndx] < ver[ndx]:
          return 1
        elif SVS_VERSION[ndx] > ver[ndx]:
          return 0
  except:
    return 0

# this function talks to the svs and returns true
# if the right svs version is running.
def PingAndCheckSvsVersion(ent_bashrc, enthome, machine):
  cmd = ". %s; cd %s/local/google3/enterprise/legacy/util && " \
        "./port_talker.py %s 3999 'v' %d" % (
      ent_bashrc, enthome, machine, 60) # 1 min timeout
  try:
    err, strout = commands.getstatusoutput(cmd)
  except:
    strout = ""
    err = 1
  if err != 0:
    logging.info("Could not talk to the svs on %s" % machine)
    return 0
  if not CheckSvsVersion(strout):
    logging.info("SVS on %s not the right version" % machine)
    return 0
  return 1


def renice_svs(machine, new_priority=SVS_NICE_VALUE):
  """Renices svs on 'machine' with new_priority.

  Returns 0 on failure, 1 on success.
  """
  pid = None
  ret = 0
  # Get pid of svs.
  try:
    pid = open(SVS_PID_FILE, 'r').read()
  except:
    err = str(sys.exc_info()[:2])
    logging.error('Error reading SVS pid from %s: %s' % (SVS_PID_FILE, err) )

  if pid is not None:
    # Get nice value for pid
    old_priority = os_utils.GetAttr('nice', int(pid))
    if old_priority is not None and int(old_priority) != new_priority:
      logging.info('Renicing SVS to %d.' % new_priority)
      # Get group id from pid.
      pgid = os_utils.GetAttr('pgid', int(pid))
      # Renice the whole group.
      cmd = 'renice %d -g %d' % (new_priority, int(pgid))
      rc = E.execute([machine], cmd, None, 1)
      if rc == 0:
        ret = 1
      else:
        logging.error('Error renicing SVS: %d' % ret)
  return ret


def restart_svs(machine):
  cmd = 'service monitoring restart > /dev/null 2>&1'
  ret = E.execute([machine], cmd, None, 1)

def svs_alive_check(machine):
  """ check if svs is live on a machine

  Argumentts:
    machine: 'ent1'
  Returns:
    1 - alive. 0 - otherwise.
  """

  (status, response) = port_talker.Talk(machine, 3999, "v", 40)
  if not status: return 0

  return CheckSvsVersion(response)

def CheckSvsAlive(machines):
  """ check if svs is running on machines and try to restart them

  Arguments
    machines: ['ent1', 'ent2']
  """

  for mach in machines:
    ## Check the svs server - 3 checks 10 secs apart
    svs_checks = 3
    svs_alive = 0
    while svs_checks > 0 and not svs_alive:
      svs_checks = svs_checks - 1
      svs_alive = svs_alive_check(mach)
      if svs_checks > 0 and not svs_alive:
        time.sleep(5)

    if not svs_alive:
      # restart svs
      restart_svs(mach)
    else:
      # Renice SVS because it may have died and got restarted by the hourly
      # monitoring cron job.
      renice_svs(mach)


def main():
  # on the GSA-Lite, there is no SVS, so just return
  if core_utils.GetEntConfigVar('ENT_CONFIG_TYPE') == 'LITE':
    return 0

  enthome = sys.argv[1]
  if len(sys.argv) > 2:
    machine = sys.argv[2]
  else:
    machine = E.getCrtHostName()
  cfg = entconfig.EntConfig(enthome)
  if not cfg.Load():
    return 1
  restart_svs(machine)
  return 0

if __name__ == '__main__':
  if len(sys.argv) < 2:
    sys.exit("Should atleast specify enthome")
  sys.exit(main())

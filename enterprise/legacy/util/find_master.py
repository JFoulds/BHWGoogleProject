#!/usr/bin/python2.4
#
# Copyright 2000-2003 Google, Inc.
# cpopescu@google.com
#

'A script that finds where the master is.'

import signal
import urllib
import sys

from google3.enterprise.legacy.util import port_talker
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.install import install_utilities

True = 1
False = 0

def AlarmHandler(signum, frame):
  raise IOError, 'Host not responding'

def FindMachinesAlive(port, machines, cmd):
  '''
  Finds the machines that answer on a port to a command.
  '''

  master = []

  # Looking for a master.

  for machine in machines:
    response = port_talker.TCPTalk(machine, port, 40, cmd, max_len=sys.maxint)
    if 0 == response[0]:
      master.append(machine)

  return master

def GetConfigVersion(machine, port, timeout):
  signal.signal(signal.SIGALRM, AlarmHandler)
  try:
    try:
      signal.alarm(timeout)
      return (True,
              int(urllib.urlopen('http://%s:%d/configversion' % (machine, port)
                                 ).read()))
    finally:
      signal.alarm(0)
  except IOError:
    pass
  except ValueError:
    pass
  return (False, None)

#TODO(nshah): Eventually, we need to phase this one out with
# FindMasterUsingChubby. Unfortunately, there
# are quite a few scripts that use this just to get a machine on which
# adminrunner is currently running. Hence, not quite straightforward to just
# replace those usages with FindMasterUsingChubby
def FindMaster(port, machines):
  '''
  Find the master machines. Return a list of machines.

  Args:
  machines: [ 'ent1', 'ent2', ... ]
  '''
  master = []
  for machine in machines:
    ok, response = GetConfigVersion(machine, port, 40)
    if ok:
      master.append(machine)

  return master

def FindMasterAndVersion(port, machines):
  '''
  Find the master machines. Return a list of tuples of config version and
  machine.
  '''

  master = []
  for machine in machines:
    ok, response = GetConfigVersion(machine, port, 40)
    if ok:
      try:
        master.append((response, machine))
      except ValueError:
        master.append((0, machine))
  master.sort()
  return master

def FindMasterUsingChubby(ver):
  """
  Find the master using chubby based master election.
  """
  return core_utils.GetGSAMaster(ver, install_utilities.is_test(ver))

def ForceMaster(node, is_testver):
  """ Force a node to become GSA master

  Arguments:
    node: 'ent2'
    is_testver: 0
  """
  gsaport = core_utils.GSAMasterPort(is_testver)
  # ignore the result of forcemaster
  port_talker.TCPTalk(node, gsaport, 30, command='GET /forcemaster\n')

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

#!/usr/bin/python2.4
#
# Copyright 2000-2003 Google, Inc.
# cpopescu@google.com
#

'A script that finds where the main is.'

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

  main = []

  # Looking for a main.

  for machine in machines:
    response = port_talker.TCPTalk(machine, port, 40, cmd, max_len=sys.maxint)
    if 0 == response[0]:
      main.append(machine)

  return main

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
# FindMainUsingChubby. Unfortunately, there
# are quite a few scripts that use this just to get a machine on which
# adminrunner is currently running. Hence, not quite straightforward to just
# replace those usages with FindMainUsingChubby
def FindMain(port, machines):
  '''
  Find the main machines. Return a list of machines.

  Args:
  machines: [ 'ent1', 'ent2', ... ]
  '''
  main = []
  for machine in machines:
    ok, response = GetConfigVersion(machine, port, 40)
    if ok:
      main.append(machine)

  return main

def FindMainAndVersion(port, machines):
  '''
  Find the main machines. Return a list of tuples of config version and
  machine.
  '''

  main = []
  for machine in machines:
    ok, response = GetConfigVersion(machine, port, 40)
    if ok:
      try:
        main.append((response, machine))
      except ValueError:
        main.append((0, machine))
  main.sort()
  return main

def FindMainUsingChubby(ver):
  """
  Find the main using chubby based main election.
  """
  return core_utils.GetGSAMain(ver, install_utilities.is_test(ver))

def ForceMain(node, is_testver):
  """ Force a node to become GSA main

  Arguments:
    node: 'ent2'
    is_testver: 0
  """
  gsaport = core_utils.GSAMainPort(is_testver)
  # ignore the result of forcemain
  port_talker.TCPTalk(node, gsaport, 30, command='GET /forcemain\n')

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

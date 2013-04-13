#!/usr/bin/python2.4
#
# (c) 2006 and onwards Google inc
# wanli@google.com
#
# Simple library/utility to read svs facts
# This is derived from get_gems_fact.py.
#
###############################################################################
import math
import string
import sys

from google3.enterprise.core import core_utils
from google3.enterprise.legacy.setup import asyncli
from google3.enterprise.util import get_loki_param
from google3.pyglib import logging

###############################################################################


###############################################################################

def InitMdb(hostname_list=None, mdb=None):
  """ Init Machine Database by reading from svs

  Arguments:
    hostname_list: ['ent1', 'ent2']
    mdb: for unittest only. The mdb to be returned by the function.

  Returns:
    The machine database, which is a dictionary.
    If SVS on a machine is not accessible, its entry will be None.
    {'ent1': {'hdcnt': '4', 'disk_size_GB': 'map:disk hda3:225.376007 hdb3\
              :227.246372 hdc3:227.246372 hdd3:227.246372 sda1:3.845303', ...
             },
     'ent2': None
    }
  """

  if mdb is not None:
    return mdb
  if hostname_list is None:
    hostname_list = core_utils.GetEntConfigVar('MACHINES')

  ent_config = core_utils.GetEntConfigVar('ENT_CONFIG_TYPE')
  if ent_config == 'LITE' or ent_config == 'FULL':
    mdb = get_loki_param.InitMdb()
  else:
    mdb = MachineInfo(hostname_list)

  logging.info('Init Machine Database from SVS for %s\n' % hostname_list)
  logging.info('mdb = %s\n' % mdb)
  return mdb

def GetFact(mdb, factname, machine):
  """ Get a fact of a machine from the machine database

  Arguments:
    mdb: {'ent1': {'hdcnt': '4', ...}, ...}
    factname: 'hdcnt'
    machine: 'ent1'

  Returns:
    The value of the fact
  """

  machine_facts = mdb.get(machine)
  if machine_facts:
    val = machine_facts.get(factname)
  else:
    val = None
  if val:
    try:
      val_eval = eval(val)
      val = val_eval
    finally:
      return val
  return val

# MachineInfo is from setupmachlib.py, and is moved here to cut down on
# dependencies.
# This code is probably overkill for the number of hosts in a cluster.
def MachineInfo(hosts):
  """Get machine information for hosts via SVS.
  Args:
    hosts: ['hosts'] - hosts to query
  Returns:
    { 'host' : { 'key' : 'val' } } - map of host to machine information.
    The dictionary is None if an error occurred retrieving data.
  """

  svs_port = 3999
  num_slots = 100

  mach_info = {}

  # Do at most 100 at a time so that we don't kill asyncli and run
  # out of sockets.
  num_passes = math.ceil(float(len(hosts)) / float(num_slots))

  for i in range(num_passes):

    cur_hosts = hosts[i*num_slots:(i+1)*num_slots]
    hostports = []
    for host in cur_hosts:
      hostports.append((host, svs_port))

    clients = asyncli.AsynRequest(hostports, 'v\n', 30, 2)
    try:
      for client in clients:

        # Test failure
        if client.failed():
          mach_info[client.host()] = None
          continue

        # Parse data
        data = {}

        for line in string.split(client.getdata(), '\n'):
          if line == 'NACKgoogle':
            data = None
            break
          elif line == 'ACKgoogle':
            break
          else:
            # Parse result.  Find the first space and treat first field
            # as the key.  Remaining is the data.  We strip this and
            # remove any double quotes around strings.
            idx = string.find(line, ' ')
            if idx == -1 or idx == 0: continue
            key = string.strip(line[:idx])
            val = string.strip(line[idx:])
            if val and val[0] == '"' and val[-1] == '"':
              val = val[1:-1]
            data[key] = val

        mach_info[client.host()] = data
    finally:
      for client in clients: client.close()

  return mach_info

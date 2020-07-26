#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.
#

""" This module contains all the logic for deciding the problems in the GSA.
    The logic is from gems_handler.py, which is removed by the "Removal of
    GEMS and MySQL Server" project.
    https://writely.corp.google.com/Doc?id=cd47rjk_14dhpkdb

    The problems and their logic are:
    (1) Machine Status:
    Compute the minimum number of machines required based on the maximum
    number of documents in million allowed by license, memory required per
    million documents, and memory total per machine.
    If the number of live machines are less than (1 + 5%) of the minimum,
    the machine status is "panic".
    Otherwise, if the number of live machines is between (1 + 1/5) and
    (1 + 5%) of the minimum, the machine status is "warning".
    Otherwise, the machine status is "healthy".

    (2) Disk Status:
    Compute the average disk used percent of all disks of all machines. If
    the average is > 85%, the status is "panic". If the average is between
    65% and 85%, the status is "warning".
    We also look for disk errors in SVS, any such error and the status is
    updated according to severity of the issue.
    A fs_error in either oneway or cluster would lead to yellow light
    A hdfail for hda3 would lead to Red for both oneway and clusters, hdfail on
    other disks will lead to red in case of oneway and yellow for clusters


    (3) Temperature Status:
    If the temperature of some machine is > 69, the status is "panic".
    Otherwise, if the temperature of some machine is between 64 and 69,
    the status is "warning". Otherwise, the status is "healthy"

    (4) Raid Status:
    For oneway: report array errors and drive errors. If >1 drives are
    missing, the status is "panic". If 1 drive is missing, the status is
    "warning". Otherwise, the status is "healthy"
    For clusters: report array errors, JBOD errors, and drive errors.
    If > 40% of JBODS are mssing, or >>4/>>3(12way/5way) arrays have been
    degraded, the status is "panic". Otherwise, if 25% ~ 40% of JBODS are
    missing, or at least one array has been degraded, the status is "warning".
    Otherwise, the status is "healthy".

    (5) System Health Status:
    If any of the "machine status", "disk status", "temperature status", and
    "raid status" is "panic", then the system health status is "panic".
    If everything is "healthy", the system health status is "healthy".
    Otherwise, the system health status is "warning".

    Please update the following wiki page if you change the logic in this
    module:
    http://wiki.corp.google.com/twiki/bin/view/Main/
           EnterpriseAdminConsoleStatusBehavior
"""

__author__ = 'wanli@google.com (Wanli Yang)'

import sys
import time
import os
import popen2
import re
import math

from google3.pyglib import logging
from google3.enterprise.tools import M
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.install import install_utilities

class GSAStatusLogic:
  """ GSA Status Logic class.

  This class contains the logic for machine status, disk status, temperature
  status, and raid status.
  """

  HW_MANIFEST_PATH = '/etc/google/hw_manifest.py'

  # default ENTCONFIG
  RAID_DEFAULT_CTRL = '0'
  WARN_MISSING_JBODS_PERCENT=.25
  CRITICAL_MISSING_JBODS_PERCENT=.40

  # set total degraded parameters for cluster type
  # 12 way: 0 = GREEN, 1-3 = YELLOW, 4> = RED
  # 5 way: 0 = GREEN, 1-2 = YELLOW, 3> = RED
  CLUSTER_DEGRADED_CRITICAL = {
    12: 4,
    5: 3,
  }

  DISKFULL_WARNING_THRESHOLD  = 80.0
  DISKFULL_CRITICAL_THRESHOLD = 90.0

  # The constructor below calls core_utils.GetLiveNodes() which does an ssh
  # to the nodes to check if they are live or not. Doing this for each
  # adminconsole request is pretty costly, more so on clusters. So we only
  # do this once every 15 minutes. Here are a set of variables to keep track
  # of when we checked the live nodes last time, so that we dont need to do
  # it for each request.
  live_nodes = ''
  live_node_check_time = 0
  kLiveNodeCheckIntervalSecs = 900  # 15 minutes

  def __init__(self, cfg):
    """ initializes parameters from /etc/google/hw_manifest.py and
    # uses defaults if manifest has errors. The hw_manifest.py is
    installed by the enterprise-os rpm.

    Args:
      cfg: an instance of the configurator class.
      For unittests, set cfg to None so that the instance can be initialized.
    """

    self._cfg = cfg
    if cfg:
      # status params are: ['Machines', 'Disks', 'Temperatures', 'Raid']
      self.status_params_ = self._cfg.getGlobalParam('ENT_SYSTEM_STATUS_PARAMS')
      # config type
      self._ent_config = self._cfg.getGlobalParam(C.ENT_CONFIG_TYPE)
      # get total nodes
      self._ent_all_machines = core_utils.GetNodes()
      if (time.time() - GSAStatusLogic.live_node_check_time >
          GSAStatusLogic.kLiveNodeCheckIntervalSecs):
        GSAStatusLogic.live_nodes = core_utils.GetLiveNodes(logging)
        GSAStatusLogic.live_node_check_time = time.time()
      self._live_machines = GSAStatusLogic.live_nodes
      # import hw manifest
      self._ImportHWManifest(self.HW_MANIFEST_PATH)
      self._DetectPlatform()
      self._is_DELL = self._IsDELLPlatform()
      self._is_virtual = self._IsVirtualPlatform()
      if self._is_DELL:
        logging.info('Dell platform detected\n')


  def _DetectPlatform(self):
    """Read /etc/google/enterprise_sysinfo to determine what platform
    we are. Sets self.ent_platform.
    """
    ENT_SYSINFO_PATH = '/etc/google/enterprise_sysinfo'
    # get platform information from file
    ent_sysinfo = {}
    try:
      execfile(ENT_SYSINFO_PATH, {}, ent_sysinfo)
    except Exception:
      pass

    self.ent_platform = ent_sysinfo.get('PLATFORM', 'oneway')


  def _IsDELLPlatform(self):
    """ Returns True if the box is a DELL machine, false otherwise"""
    if self.ent_platform in ('oneway5', 'cluster5', 'super'):
      return 1 # for python 2.2

    return 0


  def _IsVirtualPlatform(self):
    """ Returns True if this is a virtual machine, false otherwise."""
    if self.ent_platform == 'vmw':
      return 1 # for python 2.2

    return 0


  def GetHealth(self):
    """Returns a value indicate the healthy level of the whole system

    Return:
      0, 1, or 2.
      value= 0 -- healthy,
      value= 1 -- warning,
      value= 2 -- panic,
    """

    system_status = self.GetSystemStatusMap()
    # maximum of the status value for each component
    health = max(map(lambda (x,y): y[0], system_status.items()))

    return health

  def GetSystemStatus(self):
    """
    returns a python string that represents the current system status:
    Health = <health_value>
    SystemStatusValues = <health values of different components>
    SystemStatusDescription = <descriptions of different components>
    e.g. Health = 0
         SystemStatusValues  =  {'Disks':  0,  'Raid':  0,  'Temperatures':  0,
                                 'Machines': 0}
         SystemStatusDescriptions  =  {'Disks': '', 'Raid': '',
                                       'Temperatures':  '', 'Machines': ''}
    """
    result = []
    system_status = self.GetSystemStatusMap()
    health = max(map(lambda (x,y): y[0], system_status.items()))
    result.append("Health = %d" % health)
    values = {}
    descriptions = {}
    for param, status in system_status.items():
      values[param] = status[0]
      descriptions[param] = status[1]
    result.append("SystemStatusValues = %s" % repr(values))
    result.append("SystemStatusDescriptions = %s" % repr(descriptions))
    return "\n".join(result)

  def GetSystemStatusMap(self):
    """
    returns a map of the current system status
    {<component>: Status, ...}
    e.g.  {"Machines": [0, ""], "Disks": [0, ""], ... }
    """
    status = {}
    for param in self.status_params_:
      if param == "Machines":
        status[param] = self.GetMachinesStatus()
      elif param == "Disks":
        status[param] = self.GetDisksStatus()
      elif param == "Temperatures":
        status[param] = self.GetTemperatureStatus()
      elif param == "Raid":
        status[param] = self.GetRaidStatus()
      else:
        status[param] = [0, ""]
    return status

  def GetMachinesStatus(self):
    """ check and return the current machine status

    Returns:
      value, description
      value= 0 -- healthy, value= 1 -- warning, value= 2 -- panic
      description: (string)
    """
    min_machs_status, min_machs_desc = self.MinMachsStatus()
    svs_error_status, svs_error_desc = self.SVSErrorsStatus()
    status = max(min_machs_status, svs_error_status)
    desc = min_machs_desc + svs_error_desc
    return status, "\n".join(desc)

  def _GetStatusFromAverage(self, average):
    """From the average disk usage, determine the status indicator.

    Args:
      average: average disk used as a percentage

    Returns:
      a value where
        value = 0 -- enough space
        value = 1 -- more than 65% and less than 85% full
        value = 2 -- more than 85% full
    """
    status = 0
    if average > 85:
      status = 2
    elif average > 65:
      status = 1
    return status

  def GetDisksStatus(self, full_disk_machines=None,
                     halffull_disk_machines=None, bad_disk_machines=None):
    """ check and return the current disk status of the live machines.

    Args:
      full_disk_machines: ['ent1'] (for unit test only)
      halffull_disk_machines: ['ent3', 'ent4'] (for unit test only)
      bad_disk_machines: ['ent5'] (for unit test only)
    Returns:
      (value, description) pair (e.g. (0, ''))
        value = 0 -- enough space and no disk errors, filesystem errors
        value = 1 -- more than DISKFULL_WARNING_THRESHOLD% usage on any
                     disk or some not critical disk errors
        value = 2 -- more than DISKFULL_CRITICAL_THRESHOLD% usage on any
                     disk or some critical disk errors
    """
    if full_disk_machines is None and halffull_disk_machines is None:
      (full_disk_machines, halffull_disk_machines) = (
          self.CalMaxDiskUsage())

    # get the status value
    desc = []
    status = 0

    if len(full_disk_machines) > 0:
      status = 2
    elif len(halffull_disk_machines) > 0:
      status = 1

    if bad_disk_machines is None:
      bad_disk_status, bad_disk_desc = self.GetBadDiskMachines()
    else:
      bad_disk_status, bad_disk_desc = bad_disk_machines

    if bad_disk_status > 0:
      status = max(status, bad_disk_status)

    # generate the description.
    if status > 0:
      desc.append(M.MSG_DISK_PROBLEMS)
      if bad_disk_status > 0:
        desc.append(bad_disk_desc)
      if len(full_disk_machines) > 0:
        desc.append(M.MSG_FULLDISK_MACHINES % ",".join(full_disk_machines))
      if len(halffull_disk_machines) > 0:
        desc.append(M.MSG_HALFFULLDISK_MACHINES %
                    ",".join(halffull_disk_machines))

    return status, '\n'.join(desc)

  def GetTemperatureStatus(self):
    """ check and return the current temperature status.
    Note:
      the current SVS supports cpu-temp1 and cpu-temp2. So the temperature
      status is always OK. The logic in this function is from the legacy
      gems_handler.py.

    TODO(wanli): This function needs to be fixed or removed.
      Once it is fixed,
      http://wiki.corp.google.com/twiki/bin/view/Main/
      EnterpriseAdminConsoleStatusBehavior wiki page should be updated.

    Returns:
      (value, description) pair e.g. (0, '')
        value = 0 -- OK
        value = 1 -- some machine temperature > 64
        value = 2 -- some machine temperature > 69
    """

    status = 0
    desc = ""

    max_temperature = 0
    for machine in self._live_machines:
      for temp_fact in ["cpu-temp1", "cpu-temp2"]:
        factval = self._cfg.mach_param_cache.GetFact(temp_fact, machine)
        if factval:
          # Bad sensor returns 0 or 127 (Bug 37525)
          if factval == 0 or factval == 127:
            if status == 0:
              status = 1
              desc = M.MSG_BAD_TEMPERATURE_SENSOR
          else:
            max_temperature = max(max_temperature, factval)

    if max_temperature > 69:
      status = 2
      desc = M.MSG_MACHINE_TOO_HOT_WARNING
    elif max_temperature > 64:
      status = 1
      desc = M.MSG_MACHINE_TOO_WARM_WARNING

    return status, desc

  # 3ware raid status related regular expressions
  _3ware_ok_re = re.compile(r'OK')
  _3ware_rebuild_re = re.compile(r'REBUILDING')
  _3ware_unit_re = re.compile(r'OK\(unit (?P<id>\d)\)')
  _3ware_degraded_re = re.compile(r'DEGRADED')
  _3ware_nounit_re = re.compile(r'NO UNIT')

  # Mega raid status related regular expressions
  _mega_rebuild_re = re.compile(r'Rebuilding')
  _mega_online_unit_re = re.compile(r'Online\(unit (?P<id>\d)\)')
  _mega_hotspare_unit_re = re.compile(r'Hotspare\(unit (?P<id>\d)\)')

  def GetOnewayRaidStatus(self):
    """ Retrieves oneways raid status

      This function is adapted from the legacy gems_handler.py, it has been
      modified to support Dell platform alongwith the original gigabyte
      platform code. The corresponding functions are invoked depending on the
      platform.

    Returns:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down
    """

    if not self._is_DELL:
      return self.GetGBOnewayRaidStatus()
    else:
      return self.GetDELLOnewayRaidStatus()

  def GetSuperGSARaidStatus(self, svs_drive_map=None):
    """ Retrieves Super GSA raid status

    The SuperGSA box has a MegaCli Raid Controller, the code has some
    similarities to that of DellOneway, but the difference is that for SuperGSA
    the hard disks are also organized into arrays and all are not equivalent.
    SuperGSA has 6 physical disks which are organized in to three disk
    groups(units/arrays) each containing 2 disks in a Raid1 configuration. So
    we would expect 3 arrays and 6 physical disks.
    Loosing a single disk from any array makes the System Critical, because if
    the second disk in the same array goes down before rebuilding the first
    there will be a definite data loss.
    """

    machines = self._live_machines
    status = 0
    desc = []

    # this loop is just to keep the code logic similar across oneways and
    # clusters, the oneway will have one machine only
    for machine in machines:
      good_drives = 0
      online_drives = []
      hotspare_drives = []

      # initialize the drive count to zero for all array, then count for drives
      # in each array if count == 2 we are good, else we have problems
      array_drives_count = {}
      for i in xrange(self._raid_num_arrays):
        array_drives_count[i] = 0
      for i in xrange(self._raid_num_drives):
        drive = 'drive%d' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(drive, machine)
        else:
          result = svs_drive_map.get((drive, machine), '')
        if result:
          matchobj = self._mega_online_unit_re.search(result)
          if matchobj:
            online_drives.append(i)
            array_unit = int(matchobj.group('id'))
            array_drives_count[array_unit] += 1
            good_drives += 1

          # no drive should be a anything other than online for SuperGSA
          else:
            desc.append('%s %s' % (drive, result))

      missing_drives = self._raid_num_drives - good_drives
      if missing_drives > 0:
        logging.error('Expected %d drives from SVS, but only parsed %d' %
                      (self._raid_num_drives, good_drives))
      for array_unit in xrange(self._raid_num_arrays):

        # checking array status reported by SVS
        array = 'array%d' % array_unit
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(array, machine)
        else:
          result = svs_drive_map.get((array, machine), '')
        if result != 'Optimal':
          logging.error('Array %d not Optimal. Status=%s' % (array_unit,
                                                             result))
        if array_drives_count[array_unit] < 2:
          status = max(status, 2)
          if array_drives_count[array_unit] == 1:
            desc.append(' one drive down in array %s' % array_unit)
          else:
            desc.append(' two drives down in array %s' % array_unit)
          logging.error('CRITICAL: %d drive(s) down for array %s' %
                        (2 - array_drives_count[array_unit], array_unit))

    return status, ", ".join(desc)

  # Gigabyte specific code
  def GetGBOnewayRaidStatus(self, svs_drive_map=None):
    """ Retreives oneway raid status for a Gigabyte box
    svs_drive_map (for unittest only): The dictionary with drive status as
      would be returned by GetFact method.

    Return:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down
    """
    machines = self._live_machines
    status = 0
    desc = []

    # this loop is just to keep the code logic similar across oneways and
    # clusters, the oneway will have one machine only
    for machine in machines:
      live_arrays = []
      good_drives = 0
      # check drive status
      for i in xrange(self._raid_num_drives):
        drive = 'drive%d' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(drive, machine)
        else:
          result = svs_drive_map.get((drive, machine), '')
        if result:
          try:
            tw_cli_port_line = result
            matchobj = self._3ware_unit_re.match(tw_cli_port_line)
          except (TypeError, IndexError):
            if status == 0:
              status = 1
              desc.append('%s, get raid status error' % machine)
              continue
          if matchobj:
            try:
              array_unit = matchobj.group('id')
            except IndexError:
              if status == 0:
                status = 1
              desc.append('%s, get raid status array match error' % machine)
              continue
            if array_unit not in live_arrays:
              live_arrays.append(array_unit)
            good_drives += 1
          else:
            desc.append('%s: %s ' % (drive, tw_cli_port_line))

      # check array status
      for i in live_arrays:
        array = 'array%s' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(array, machine)
        else:
          result = svs_drive_map.get((array, machine), '')
        if result:
          try:
            tw_cli_array_line = result
            if self._3ware_rebuild_re.match(tw_cli_array_line):
              if status == 0:
                status = 1
              desc.append('%s %s %s.' % (machine, array, tw_cli_array_line))
            elif self._3ware_degraded_re.match(tw_cli_array_line):
              status = 2
              desc.append('%s %s %s.' % (machine, array, tw_cli_array_line))
            elif self._3ware_ok_re.match(tw_cli_array_line):
              pass
            else: # wierd case
              status = 2
              desc.append('%s %s %s.' % (machine, array, result))
          except (TypeError, IndexError):
            if status == 0:
              status = 1
            desc.append('%s, check array status error' % machine)
            continue

      missing_drives = self._raid_num_drives - good_drives
      if missing_drives == 1:
        status = 1
        desc.append(' one drive down ')
        logging.error('WARNING: one drive down ')
      elif missing_drives > 1:
        status = 2
        desc.append(' two or more drives down ')
        logging.error('CRITICAL: two or more drives down ')

    return status, ", ".join(desc)


  def GetDELLOnewayRaidStatus(self, svs_drive_map=None):
    """ Returns the Raid Status for a Dell Oneway machine
    Params:
      svs_drive_map (for unit test only): The dictionary with drive status as
      would be returned by GetFact method.

    As far as hw_manifest configuration is considered we only need the
    self._raid_num_drives variable for this function.
    There is no separate Array behaviour check unlike Gigabyte code as the new
    raid config for oneways has only a single Logical drive (call it array) for
    all the drives which are kept in a RAID5 config.

    Return:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down
    """
    machines = self._live_machines
    status = 0
    desc = []

    # this loop is just to keep the code logic similar across oneways and
    # clusters, the oneway will have one machine only
    for machine in machines:
      good_drives = 0
      good_drives = 0
      online_drives = []
      hotspare_drives = []

      for i in xrange(self._raid_num_drives):
        drive = 'drive%d' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(drive, machine)
        else:
          result = svs_drive_map.get((drive, machine), '')
        if result:
          matchobj = self._mega_online_unit_re.search(result)
          if matchobj:
            online_drives.append(i)
            good_drives += 1
          elif self._mega_hotspare_unit_re.match(result):
            hotspare_drives.append(i)
            good_drives += 1
          else:
            desc.append('%s %s' % (drive, result))

      missing_drives = self._raid_num_drives - good_drives
      if missing_drives == 1:
        if status == 0:
          status = 1
        desc.append(' one drive down ')
        logging.error('WARNING: one drive down ')
      elif missing_drives > 1:
        status = 2
        desc.append(' two or more drives down ')
        logging.error('CRITICAL: two or more drives down ')

    return status, ", ".join(desc)

  def GetClusterRaidStatus(self):
    """
    Checks the status of the raid. The method delegates the task to the
    corresponding functions depending on hardware

    Returns:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down

    """
    # return appropriate method's output
    if self._is_DELL:
      return self.GetDELLClusterRaidStatus()
    else:
      return self.GetGBClusterRaidStatus()

  def GetDELLClusterRaidStatus(self, svs_drive_map=None):
    """
    Raid Configuration logic for DELL Clusters.
    The logic is very simple for the new RAID config
    The drivex x = 0,1 are part of Disk Grp 0
        drivex x = 2-5 are part of Disk Grp 1
    if any disk in grp 0 goes bad we have a status = 1
    the disks in group 1 are part of JBOD grp, there logic
    is just dependent on a total count

    Params:
      svs_drive_map (for unit test only): The dictionary with drive status as
      would be returned by GetFact method.

    Returns:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down

    """

    machines = self._live_machines
    status = 0
    desc = list()
    total_good_jbods = 0  # total jbods across nodes
    total_nodes = len(self._ent_all_machines)

    for machine in machines:
      good_jbod_drives = 0  # jbods in this machine
      good_system_drives = 0  # OS drives in this machine
      # see all drive health
      for i in xrange(self._raid_num_drives):
        drive = 'drive%d' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(drive, machine)
        else:
          result = svs_drive_map.get((drive, machine), '')
        # the first two drives have a raid-1 for the os partition
        if result:
          matchobj = self._mega_online_unit_re.search(result)
          if matchobj:
            if i < 2:
              good_system_drives += 1
            # the drives 2-6 are jbods for gsa data
            else:
              good_jbod_drives += 1
          else:
            desc.append('%s %s %s' % (machine, drive, result))

      if good_system_drives < 2:
        desc.append('system drives have problems')
        status = 1
      # This situation should not arrive ? (the node should be down already)
      if good_system_drives < 1:
        status = 2
      # calculate the total number of Jbods up
      total_good_jbods += good_jbod_drives

    # check GFS drives
    try:
      missing_jbods = self._raid_total_jbods - total_good_jbods
      if (float(missing_jbods)/float(self._raid_total_jbods) >
          self.CRITICAL_MISSING_JBODS_PERCENT): # red
        status = 2
        desc.append('%s data drives missing ' % missing_jbods)
        logging.error('CRITICAL: %s data drive(s) out of %s missing ' %
                      (missing_jbods, self._raid_total_jbods))
      elif (float(missing_jbods)/float(self._raid_total_jbods) >
          self.WARN_MISSING_JBODS_PERCENT): # yellow
        status = 1
        desc.append('%s data drives missing ' % missing_jbods)
        logging.error('WARNING: %s data drive(s) out of %s missing ' %
                      (missing_jbods, self._raid_total_jbods))
    except ZeroDivisionError:
      status = 2
      desc.append('Unexpected 0 good or 0 total arrays')

    return status, ", ".join(desc)

  def GetGBClusterRaidStatus(self, svs_drive_map=None):
    """
      Warning: this code will break if you ever have two different disk
      configs in a cluster.  This code is not cluster aware and assumes
      that the disk configuration is the same in every node as the node
      adminrunner runs on (main).  A better way to do this is to get the
      manifest from each node and calculate the total.

      How it works:  This code starts with the total number of JBODS
      that a cluster should have.  This is based on the hw_manifest.
      It then counts all the JBODS it finds.  They could be missing
      because NO UNIT, a down node, or simply gone missing.  Any
      disk that isnt part of a unit causes a YELLOW and a description
      is printed so the customer can see which disk on what node
      has failed.

      It then counts the total number of degraded arrays.  Only
      RAID 1 or 5 can go DEGRADED.  Therefore this must be the
      system disk.

      After getting both JBODS and DEGRADED disks it first checks
      the the percentage of JBODS that are "missing".  If its
      over the threshold it reports YELLOW or RED.

      It checks degraded arrays and if they are over threshold
      it goes YELLOW or RED based on the threshold.

    Params:
      svs_drive_map (for unit test only): The dictionary with drive status as
      would be returned by GetFact method.

    Returns:
      (status, desc) pair. e.g (0, '')
        status = 0: OK
        status = 1: 1 drive is down
        status = 2: 2 or more drives are down

    """

    machines = self._live_machines
    status = 0
    desc = list()
    good_jbods = 0
    degraded = 0
    total_nodes = len(self._ent_all_machines)

    for machine in machines:
      live_arrays = []

      # get total arrays
      for i in xrange(self._raid_num_drives):
        drive = 'drive%d' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(drive, machine)
        else:
          result = svs_drive_map.get((drive, machine), '')
        if result:
          try:
            tw_cli_port_line = result
            matchobj = self._3ware_unit_re.match(tw_cli_port_line)
          except (TypeError, IndexError):
            if status == 0:
              status = 1
            desc.append('%s, get drive information error' % machine)
            continue
          if matchobj: # has a UNIT assignment
            try:
              array_unit = matchobj.group('id')
            except IndexError:
              if status == 0:
                status = 1
              desc.append('%s, drive unit match error - array match invalid' %
                          machine)
              continue
            if array_unit not in live_arrays:
              live_arrays.append(array_unit)
              try:
                array_unit = int(array_unit)
              except (ValueError, TypeError): # integer cast exception
                if status == 0:
                  status = 1
                desc.append('%s, invalid array error - array_unit invalid' %
                            machine)
                continue
              controller_specs = self._raid_specs.get(self.RAID_DEFAULT_CTRL,
                  None)
              if controller_specs:
                try:
                  type, disks = controller_specs.get(array_unit, None)
                  if type == 'jbod':
                    good_jbods += 1
                except TypeError:
                  if status == 0:
                    status = 1
                  desc.append('%s, unexpected UNIT error: %s ' % (machine,
                              tw_cli_port_line))
          else: # usually NO UNIT
            status = 1
            desc.append('%s: %s %s ' % (machine, drive, tw_cli_port_line))


        # check array status
      for i in live_arrays:
        array = 'array%s' % i
        if svs_drive_map is None:
          result = self._cfg.mach_param_cache.GetFact(array, machine)
        else:
          result = svs_drive_map.get((array, machine), '')
        if result:
          try:
            tw_cli_array_line = result
            if self._3ware_rebuild_re.match(tw_cli_array_line):
              if status == 0:
                status = 1
              desc.append('%s: %s - %s ' % (machine, array, tw_cli_array_line))
            elif self._3ware_degraded_re.match(tw_cli_array_line):
              desc.append('%s: %s - %s ' % (machine, array, tw_cli_array_line))
              degraded += 1
            elif self._3ware_ok_re.match(tw_cli_array_line):
              pass
            else: # wierd case, capture it
              status = 2
              desc.append('%s %s %s %s. ' % (desc, machine, array, result))
          except (TypeError, IndexError) :
            if status == 0:
              status = 1
            desc.append('%s, get array information error' % machine)
            continue

    # check GFS arrays
    try:
      missing_jbods = self._raid_total_jbods - good_jbods
      if (float(missing_jbods)/float(self._raid_total_jbods) >
          self.CRITICAL_MISSING_JBODS_PERCENT): # red
        status = 2
        desc.append('%s data drives missing ' % missing_jbods)
        logging.error('CRITICAL: %s data drive(s) out of %s missing ' %
                      (missing_jbods, self._raid_total_jbods))
      elif (float(missing_jbods)/float(self._raid_total_jbods) >
          self.WARN_MISSING_JBODS_PERCENT): # yellow
        status = 1
        desc.append('%s data drive(s) missing ' % missing_jbods)
        logging.error('WARNING: %s data drive(s) out of %s missing ' %
                      (missing_jbods, self._raid_total_jbods))
    except ZeroDivisionError:
      status=2
      desc.append('Unexpected 0 good or 0 total arrays')

    if degraded: # any degraded arrays
      if self.CLUSTER_DEGRADED_CRITICAL.has_key(total_nodes):
        degraded_critical = self.CLUSTER_DEGRADED_CRITICAL[total_nodes]
        if degraded < degraded_critical:
          status = 1
        else:
          status = 2
        desc.append('%d system array(s) degraded' % degraded)
      else:
        status = 1
        desc.append('%d amount of nodes unexpected is this a 5 or 12way?' % (
          total_nodes))
    # else no degraded arrays we are all good.

    return status, ", ".join(desc)

  def GetRaidStatus(self):
    """ Check and return the current RAID status

    value = 0 -- OK
    value = 1 -- some arrays rebuilding
    value = 2 -- degraded arrays or missing drives or arrays

    Returns:
      (value, description) pair
    """
    if self._ent_config == 'ONEBOX':
      return self.GetOnewayRaidStatus()
    elif self._ent_config == 'SUPER':
      return self.GetSuperGSARaidStatus()
    elif self._ent_config == 'CLUSTER':
      return self.GetClusterRaidStatus()
    elif self._ent_config == 'FULL':
      return [0, ''] # Virtual GSAFull has no RAID
    else:
      logging.error('Bad ent_config type %s' % self._ent_config)
      return [0, '']


  def _ImportHWManifest(self, hw_manifest_path, raid_specs=None):
    """ Import HW manifest file, and count the number of arrays and disks.

    The default RAID specs will be used if the HW manifest file cannot be
    imported.

    Args:
      hw_manifest_path: '/etc/google/hw_manifest.py'
    """

    RAID_SPECS_NAME = 'RAID_SPECS'

    # default RAID_SPECS for oneways:
    #   two mirrors and a hot spare with a total of 5 disks.
    DEFAULT_ONEWAY_RAID_SPECS = {
      # controller
      #      array  type       disks
      '0': {
             0: (   'raid1',   [ 0, 1, ], ),
             2: (   'raid1',   [ 2, 3, ], ),
             4: (   'spare',   [ 4, ], ),
      },
    }

    DEFAULT_SUPER_RAID_SPECS = {
      # controller
      #      array  type       disks
      '0': {
             0: (   'raid1',   [ 0, 1, ], ),
             2: (   'raid1',   [ 2, 3, ], ),
             4: (   'raid1',   [ 4, 5, ], ),
      },
    }

    DEFAULT_CLUSTER_RAID_SPECS = {
      # controller
      #      array  type       disks
      '0': {
             0: (   'raid1', [ 0, 1, ], ),
             2: (   'jbod',  2, ),
             3: (   'jbod',  3, ),
             4: (   'jbod',  4, ),
      },
    }

    manifest_locals = {}
    try:
      execfile(hw_manifest_path, {}, manifest_locals)
    except Exception:
      # almost anything could be wrong, so survive the most general exception
      logging.error('HW manifest file %s cannot be imported, the default '
                    'RAID SPECS are used'  % hw_manifest_path)
    if self._ent_config == 'ONEBOX':
      default_raid_specs = DEFAULT_ONEWAY_RAID_SPECS
    elif self._ent_config == 'SUPER':
      default_raid_specs = DEFAULT_SUPER_RAID_SPECS
    else:
      default_raid_specs = DEFAULT_CLUSTER_RAID_SPECS

    if raid_specs is None:
      self._raid_specs = manifest_locals.get(RAID_SPECS_NAME,
                                             default_raid_specs)
    else:
      self._raid_specs = raid_specs
    self._CountArraysAndDrives()

  def _CountArraysAndDrives(self):
    """ Count Arrays and Drives

    determine how many arrays (RAID, JBOD, SPARE, etc.) and drives to expect
    by scanning RAID_SPECS (see format example in ONEWAY_RAID_SPECS above)
    """

    num_arrays = 0
    num_drives = 0
    num_jbods_per_node = 0
    num_raids_per_node = 0
    total_jbods = 0
    controllers = self._raid_specs.keys()

    # NOTE:  SVS currently only supports one RAID controller, but this code
    #   does not necessarily know the name of that controller, so loop through
    for controller in controllers:
      array_info = self._raid_specs[controller]
      arrays = array_info.keys()

      for array in arrays:
        num_arrays += 1
        type, disks = array_info[array]
        # type can be 'raid1' or 'raidX'
        if type.find('raid') >= 0:
          num_raids_per_node += 1
        if type == 'jbod':
          if isinstance(disks, list):
            num_jbods_per_node += len(disks)
          else:
            num_jbods_per_node += 1
        if isinstance(disks, list):
          num_drives += len(disks)
        else:
          # should always be a list, but for some reason, sometimes is scalar
          num_drives += 1
    self._num_raids_per_node = num_raids_per_node
    self._num_jbods_per_node = num_jbods_per_node
    self._raid_num_arrays = num_arrays
    self._raid_num_drives = num_drives
    self._raid_total_jbods = num_jbods_per_node *len(self._ent_all_machines)
    logging.info('Number of drives detected=%s, jbods=%s' %
        (self._raid_num_drives, num_jbods_per_node))


  def SVSErrorsStatus(self, lockserv_cmd_out=None):
    """ Check SVS errors recorded by gsa-main

    Args:
      lockserv_cmd_out: {'ent1': 'machine problem Unknown\n'}
        (for unit test only)
    Return: status, desc (e.g. 0, []).
            status is 1 if there are SVS erros. Otherwise, status is 0.
    """

    # Add any SVS errors (from gsa-main) to the problem list
    all_machs_status = 0
    desc = []
    if self._ent_config == 'CLUSTER':
      if lockserv_cmd_out is None:
        version = self._cfg.getGlobalParam('VERSION')
        lockserv_cmd_prefix = core_utils.GetLSClientCmd(version,
          install_utilities.is_test(version))
      for machine in self._live_machines:
        if lockserv_cmd_out is None:
          chubby_file = '/ls/%s/svs_%s' % (core_utils.GetCellName(version),
                                           machine)
          lockserv_cmd = '%s cat %s' % (lockserv_cmd_prefix, chubby_file)
          out = []
          lockserv_status = E.execute(['localhost'], lockserv_cmd, out, 60)
        else:
          lockserv_status = 0
          if machine in lockserv_cmd_out:
            out = [lockserv_cmd_out[machine]]
          else:
            out = []
        if lockserv_status == 0 and len(out) > 0 and out[0] != '':
          errors = out[0].splitlines()
          status = 0
          for i in range(0, len(errors)):
            if (errors[i].find('unrecoverable error') >= 0 or
                errors[i].find('file system error') >= 0):
              errors[i] = '' # Ignore this error
            else:
              status = 1 # Show an error
          if status:
            # A svs error has been recorded
            all_machs_status = max(all_machs_status, status)
            errors = [e for e in errors if e != '']
            # add machine name
            desc.append('%s: %s' % (machine, ' '.join(errors)))
    return all_machs_status, desc

  def CalcMinMachsRequired(self, max_docs_allowed=None, mem_for_mil_docs=None,
                           mem_total_per_mach=None):
    """ Calculate Minimum Machines Required

    This is based on the maximum number of documents in million allowed,
    by license, memory required for per million docs, and memory total
    per machine.

    Args:
      max_docs_allowed: 15000000. used for unit test only
      mem_for_mil_docs: 3000 (MB). used for unit test only
      mem_total_per_mach: 12478856(k). used for unit test only
    """

    if max_docs_allowed is None:
      license_info = self._cfg.getGlobalParam('ENT_LICENSE_INFORMATION')
      max_docs_allowed = license_info.get('ENT_LICENSE_MAX_PAGES_OVERALL')
    # maximum number of documents in million allowed by license
    max_docs_overall = (max_docs_allowed + 999999) / 1000000

    if mem_for_mil_docs is None:
      mem_for_mil_docs = self._cfg.getGlobalParam(
        'ENT_MEMORY_REQUIRED_PER_MIL_DOCS')

    if mem_total_per_mach is None:
      mem_total_per_mach = self._cfg.getGlobalParam('MEMORY_TOTAL_PER_MACHINE')

    min_machs_required = int(math.ceil((max_docs_overall * mem_for_mil_docs /
                                       (mem_total_per_mach / 1024.0))))
    return min_machs_required

  def MinMachsStatus(self, min_machs_required=None):
    """ Return minimum machines status

    critical if less than (1+%5) of minimum requirement,
    caution if less than (1+1/5) of minimum requirement.

    Args:
      min_machs_required: 4 (for unit test only)
    Return:
      status, desc
      status can be 0 ("healthy"), 1 ("warning"), or 2 ("panic")
      desc can be [], or
        ['The following machines have been removed from the cluster '
         'configuration: ent1, ent2, ent3',
         'Please contact Google technical support immediately.']
    """

    desc = []
    if min_machs_required is None:
      min_machs_required = self.CalcMinMachsRequired()
    dead_machines = [x for x in self._ent_all_machines
                     if x not in self._live_machines]
    num_live_machines = len(self._live_machines)
    num_dead_machines = len(dead_machines)
    status = 0

    if num_dead_machines > 0:
      status = 1
      desc.append(M.MSG_MACHINES_DOWN % ','.join(dead_machines))
      # critical if less than (1+%5) of minimum requirement
      if num_live_machines < (min_machs_required * 21 + 19)/20:
        status = 2
        desc.append(M.MSG_MACHINES_WARNING)
      elif num_live_machines < (min_machs_required * 6  + 4)/5 :
        # caution if less than (1+1/5) of minimum requirement
        desc.append(M.MSG_MACHINES_CAUTION)

    return status, desc

  def GetDiskUsage(self, machine, svs_fact=None):
    """
    Get the disk usage of a machine.

    All disks (sda1, hda3, hdb3, etc..) are included.

    Args:
      machine: 'ent1'
      svs_fact: 'map:disk hda3:4 hdb3:1' (for unit test only)
    Returns:
      {'hda3': 65, 'hdb3': 32} (hda3 is 65% used, hdb3 is 32% used)
      None if the disk usage information is not available
    """

    disks_usage_map = {}
    if svs_fact is None:
      svs_fact = self._cfg.mach_param_cache.GetFact(
                          "disk_used_df_percent", machine)
    if svs_fact is None:
      return None
    all_disks_usage = svs_fact.split()
    for disk_usage in all_disks_usage:
      try:
        colon_index = disk_usage.find(':')
        disks_usage_map[disk_usage[:colon_index]] = float(
          disk_usage[(colon_index + 1):])
      except (TypeError, ValueError):
        pass
    return disks_usage_map

  def CalMaxDiskUsage(self, machs_disk_usage=None):
    """ Returns machines that are above disk usage threasholds. Per machine, we
    consider the disk with the maximum usage.

    Dead machines are ignored. (Another way to calculate is to assume
    tht the disk usage is 100% for bad machines. But I think that is
    misleading.)

    Args:
      machs_disk_usage: {'ent1': {'hda3': 95.0, 'hdb3': 97.0, 'hdc3': 58.0},
                         'ent2': {'hda3': 5.0, 'hdb3': 6.0},
                         'ent3': {'hda3': 67.0, 'hb3': 68.0}}
      for unit test only
    Return:
      (['ent1'], ['ent3'])
      meaning: ent1 is over DISKFULL_CRITICAL_THRESHOLD% full,
      ent3 is over DISKFULL_WARNING_THRESHOLD% full.
    """

    full_disk_machines = []
    halffull_disk_machines = []
    avg_disk_usage_sum = 0
    for machine in self._live_machines:
      if machs_disk_usage is None:
        # TODO(moberoi): After this CL has been D/I to the cluster branch,
        # remove GetDiskUsage method and use install_utilities.get_disk_usage()
        # instead (it doesn't work on clusters) to standardize.
        disks_usage = self.GetDiskUsage(machine)
      else:
        disks_usage = machs_disk_usage[machine]
      if disks_usage:
        max_disk_usage = max(disks_usage.values())
        if max_disk_usage > self.DISKFULL_CRITICAL_THRESHOLD:
          full_disk_machines.append("%s" % machine)
          logging.info("Machine %s reported max_disk_usage (%s) higher than "
                       "critical threshold (%s). Complete usage: %s",
                       machine, max_disk_usage,
                       self.DISKFULL_CRITICAL_THRESHOLD, disks_usage)
        elif max_disk_usage > self.DISKFULL_WARNING_THRESHOLD:
          halffull_disk_machines.append("%s" % machine)
          logging.info("Machine %s reported max_disk_usage (%s) higher than "
                       "warning threshold (%s). Complete usage: %s",
                       machine, max_disk_usage,
                       self.DISKFULL_WARNING_THRESHOLD, disks_usage)
    return (full_disk_machines, halffull_disk_machines)

  def GetBadDiskMachines(self, svs_bad_disks_map=None):
    """ Check var_log_badhds of each machine, return machines with bad disks.

    This is the behaviour we want
    1) Oneway:
      fs_error is yellow
      hdfail is red

    2) Cluster:
      fs_error is yellow
      hdfail is red if / or hda3 has gone bad, yellow if other disks
      (used by data has gone bad)

    Args:
      bad_disks_map: Unit tests only, A map of (fact, machine) to the value as
      reported by SVS

    Return:
      Status, Description where the values are set according to conditions
      above.
    """

    status = 0
    desc = ''
    machine_desc = []
    fserrors_exists = 0

    for machine in self._live_machines:
      bad_disks = None
      bad_disks_severity = 0
      errors = []
      fserrors = None
      # when we query for var_log_hdfail_hdaX the fact may not be existent in
      # SVS, the current implementation of get_svs_param will however return
      # None and not throw any error, which is okay
      disks = ('hda3', 'hdb3', 'hdc3', 'hdd3', 'hde3')
      for disk in disks:
        svs_fact_name = 'var_log_hdfail_%s_since_reboot' % disk
        if not svs_bad_disks_map:
          bad_disks = self._cfg.mach_param_cache.GetFact(svs_fact_name,
              machine)
        else:
          bad_disks = svs_bad_disks_map.get((svs_fact_name, machine))

        if bad_disks:
          # A hda3 error is always red status, any hdfail on oneway is critical
          if disk == 'hda3' or self._ent_config in ('ONEBOX', 'SUPER'):
            bad_disks_severity = 2
          else:
            bad_disks_severity = max(bad_disks_severity, 1)

      if bad_disks_severity > 0:
        errors.append('disk failure')
        status = max(status, bad_disks_severity)

      # check for fserrors
      svs_fact_name = 'var_log_fserror_since_reboot'
      if not svs_bad_disks_map:
        fserrors = self._cfg.mach_param_cache.GetFact(svs_fact_name, machine)
      else:
        fserrors = svs_bad_disks_map.get((svs_fact_name, machine))

      if fserrors:
        status = max(status, 1)
        errors.append('file system errors')
        fserrors_exists = 1

      if errors:
        machine_desc.append('%s %s' % (machine, ', '.join(errors)))

    desc = ', '.join(machine_desc)

    if fserrors_exists:
      desc += '. Please reboot the appliance to clear file system errors'

    return (status, desc)

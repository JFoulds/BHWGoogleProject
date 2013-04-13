#!/usr/bin/python2.4
#
# machinelib.py - machine objects and management.
#
# Copyright 2002 and onwards, Google
# Original Author: Eugene Jhong
#
# Based on Daniel Dulitz's verifyconfig.py.
#       and Bogdan Cocosel's add_capacity.py.
#
# This is currently an object oriented wrapper around the
# machine information.  Get information from SVS for enterprise.
#
# TODO:
#
# - add class for rack information
# - enhance and rework method of generic querying
# - add add/update/del for hardware information
# - add methods for the updating into the base class (but this
#   is not necessary now - will take care of later)
# - maybe add is_valid methods to Hardware/Problems/Uses/Machine
#   to test if fields set are valid values?
#

import time
import sys
import string
import math
import copy

from google3.enterprise.legacy.production.common import cachelib
from google3.enterprise.legacy.util import get_svs_param


class Error(Exception):
  """Base class for machinelib exceptions."""
  pass

#------------------------------------------------------------------------------
# Machine Information
#------------------------------------------------------------------------------

_default_mach_mgr = None

def InstallDefaultMachineManager(mach_mgr):
  global _default_mach_mgr
  """  Make the given machine manager the default.  After installing a non-null
  default machine manager, calls to MachineManagerFactory will not cause a new
  MachineManager to be created.  Instead, the default manager will be returned.
  """
  _default_mach_mgr = mach_mgr


def MachineManagerFactory():
  if _default_mach_mgr:
    return _default_mach_mgr
  else:
    return MachineManagerSvsDirect() 

#
# MachineManager
#
# Class for managing and querying machine information -
# machines, hardware, problems and uses.
#
class MachineManager:

  # Sets the module to be used to get machine data
  def __init__(self, module):
    self.db_ = module
    self.user_ = None

  # Get machine object by machine name.
  # Force causes reload of all information for this machine from the DB
  # (including use/problem/hardware).
  def Machine(self, machname, force=0):
    return self.MachineList([machname], force=force)[0]

  # Efficiently get a list of machine objects by machine names.
  def MachineList(self, machnames, load_hardware=0,
                  load_uses=0, load_problems=0, force=0):
    machnames = machnames
    load_hardware = load_hardware
    load_uses = load_uses
    load_problems = load_problems
    force = force
    return []

  # Get list of hosts from machine objects.  Commonly needed operation.
  def HostList(self, machs):
    return map(lambda x: x.name(), machs)

  # Get hardware object by macaddr.
  # Force causes reload from the DB.
  def Hardware(self, macaddr, force=0):
    return self.HardwareList([macaddr], force=force)[0]

  # Efficiently get a list of hardware objects by macaddrs.
  def HardwareList(self, macaddr, force=0):
    macaddr = macaddr
    force = force
    return []

  # Get list of uses by machine name.
  # Force causes reload from the DB for uses for this machine.
  def Uses(self, machname, force=0):
    return self.UsesList([machname], force=force)[0]

  # Efficiently get a list of use objects by machine names.
  def UsesList(self, machnames, force=0):
    machnames = machnames
    force = force
    return []

  # Get list of problems by macaddr.
  # Force causes reload from the DB for problems for this machine.
  def Problems(self, macaddr, force=0):
    return self.ProblemsList([macaddr], force=force)[0]

  # Efficiently get a list of problem objects by macaddrs.
  def ProblemsList(self, macaddrs, force=0):
    macaddrs = macaddrs
    force = force
    return []

  # Get the list of machine given the criteria
  def SelectMachineNames(self, patterns,
                         used = '', problems = '',
                         project = '', owner='', servertype=''):
    patterns = patterns
    used = used
    problems = problems
    project = project
    owner = owner
    servertype = servertype
    return []


#
# MachineManagerSvsDirect
#
# Class for managing and querying machine information -
# machines, hardware, current hardware utilization
# It uses SVS directly to access the data
# It is mostly copied from MachineManagerGEMS
#
class MachineManagerSvsDirect(MachineManager):

  def __init__(self, unittest_mdb):
    MachineManager.__init__(self, get_svs_param)
    self.mdb_ = self.db_.InitMdb(mdb=unittest_mdb)
    self.Init()

  def Init(self):
    # Cache of machine names to machine objects.
    self.machine_cache_ = cachelib.Cache()
    # Cache of machine names to hardware objects.
    self.hardware_cache_ = cachelib.Cache()

  def MachineList(self, machnames, load_hardware=0,
                  load_uses=0, load_problems=0, force=0):
    """ get a list of machine objects by machine names

    Machine objects not cached will be cached.

    Arguments:
      machnames: ['ent1', 'ent2']
      load_hardware: 1 - preload hardware. Currently not implemented.
      load_uses:  1 - preload uses. Currently not implemented.
      load_problems: 1 - preload problems. Currently not implemented.
      force: 1 - don't use the cached machine objects. 0 - otherwise.

    Returns:
      a list of machine objects by machine names.
    """

    # Find machines that are not yet cached.
    allmachnames = machnames
    if not force:
      machnames = filter(lambda x, y=self.machine_cache_: not y.has_key(x),
                         machnames)
    for machname in machnames:
      mach = Machine(self)
      mach.set_name(machname)
      mach.set_macaddr(machname) # We don't really need macaddr
      mach.hardware()            # sets the hardware params
      self.machine_cache_[machname] = mach

    allmachs = map(lambda x, y=self.machine_cache_: y[x], allmachnames)

    return allmachs

  def HardwareList(self, machnames, force=0):
    """ Find hardware that is not yet cached.

    Use svs to get the disk, cpu, memory, and load info.

    Arguments:
      machnames: ['ent1', 'ent2']
      force: 1 - don't use the cached machine objects. 0 - otherwise.

    Returns:
      a list of hardware objects by macaddrs.
    """

    allmachnames= machnames
    if not force:
      machnames = filter(lambda x, y=self.hardware_cache_: not y.has_key(x),
                         machnames)
    for machname in machnames:
      try:
        hdw = Hardware(self)
        hdw.set_macaddr(machname)

        # Get all the disk params
        disk_names = self.db_.GetFact(self.mdb_, 'disk-names', machname)
        disk_names = string.split(disk_names, ' ')
        disk_sizes = self.db_.GetFact(self.mdb_, 'disk-sizes', machname)
        if type(disk_sizes) == float:
          disk_sizes = [str(disk_sizes)]
        else:
          disk_sizes = string.split(disk_sizes, ' ')
        disk_useds = self.db_.GetFact(self.mdb_, 'disk-useds', machname)
        if type(disk_useds) == float:
          disk_useds = [str(disk_useds)]
        else:
          disk_useds = string.split(disk_useds, ' ')

        disk_used_map = {}
        disk_total_map = {}
        for i in range(len(disk_names)):
          disk_used_map[disk_names[i]] = disk_useds[i]
          disk_total_map[disk_names[i]] = disk_sizes[i]

        all_disks = self.db_.GetFact(self.mdb_, 'mounted-drives', machname)
        all_disks = string.split(all_disks, ' ')

        # filter out the bad disks
        bad_disks = self.db_.GetFact(self.mdb_, 'var_log_badhds', machname)
        bad_disks = string.split(bad_disks, ' ')
        good_disks = filter(lambda x, y=bad_disks: x not in y, all_disks)

        # set the total/used disk size
        hdsize = 0
        hdused = 0
        hdcnt = 0
        for disk in good_disks:
          disk_dev_name = '/dev/%s3' % disk
          if not disk_total_map.has_key(disk_dev_name):
            disk_dev_name = '/dev/%s1' % disk
          hdsize = hdsize + long(eval(disk_total_map[disk_dev_name]))
          hdused = hdused + long(eval(disk_used_map[disk_dev_name]))
          hdcnt = hdcnt + 1
        hdw.set_hdsize(int(hdsize >> 20))
        hdw.set_hdused(int(hdused >> 20))
        hdw.set_hdcnt(hdcnt)

        cpumhz = self.db_.GetFact(self.mdb_, 'cpu-mhz', machname)
        hdw.set_cpumhz(int(cpumhz))

        cpucnt = self.db_.GetFact(self.mdb_, 'cpucnt', machname)
        hdw.set_cpucnt(int(cpucnt))

        ram = self.db_.GetFact(self.mdb_, 'memory-total', machname)
        hdw.set_ram(int(long(ram) >> 10)) # in MB

        ramused = self.db_.GetFact(self.mdb_, 'memory-used', machname)
        hdw.set_ramused(int(long(ramused) >> 10)) # in MB

        load = self.db_.GetFact(self.mdb_, 'load3', machname)
        hdw.set_load(float(load))

        self.hardware_cache_[machname] = hdw
      except TypeError:
        self.hardware_cache_[machname] = None
      except AttributeError:
        self.hardware_cache_[machname] = None

    allmachs = map(lambda x, y=self.hardware_cache_: y[x], allmachnames)
    return allmachs


#
# Machine
#
# Represents a machine.
#
class Machine:

  def __init__(self, manager):

    self.manager_ = manager
    self.name_ = None
    self.macaddr_ = None
    self.msvid_ = None
    self.colo_ = None
    self.rack_ = None
    self.num_ = None
    self.crawlnet_ = None

  def name(self):
    return self.name_

  def set_name(self, name):
    self.name_ = name

  def macaddr(self):
    return self.macaddr_

  def set_macaddr(self, macaddr):
    self.macaddr_ = macaddr

  def msvid(self):
    return self.msvid_

  def set_msvid(self, msvid):
    self.msvid_ = msvid

  def colo(self):
    return self.colo_

  def set_colo(self, colo):
    self.colo_ = colo

  def rack(self):
    return self.rack_

  def set_rack(self, rack):
    self.rack_ = rack

  def num(self):
    return self.num_

  def set_num(self, num):
    self.num_ = num

  def crawlnet(self):
    return self.crawlnet_

  def set_crawlnet(self, crawlnet):
    self.crawlnet_ = crawlnet

  # Get hardware info, reloads from DB if force = 1.
  def hardware(self, force=0):
    hdw = self.manager_.Hardware(self.macaddr_, force)
    if hdw: hdw.set_machine(self.name())
    return hdw

  # Get use info, reloads from DB if force = 1.
  def uses(self, force=0):
    uses = self.manager_.Uses(self.name_, force)
    for use in uses: use.set_machine(self.name())
    return uses

  # Get list of owners.
  def owners(self, force=0, do_prod_hack=1):
    owners = {}
    for use in self.uses(force=force):
      owner = use.assignedto()
      # TODO: At least centralize this horrible hack for sending mail.
      # We need to update the DB to set owner appropriately to
      # production-team, but we must search for all the dependencies
      # first.
      if owner == 'production' and do_prod_hack:
        owner = 'prod-requests'
      owners[owner] = 1
    return owners.keys()

  # Get problem info, reloads from DB if force = 1.
  #
  #   problem_type: limit to type of problem specified.
  #   status: limit to status specified.
  #
  def problems(self, problem_type=None, status=None, force=0):
    problems = self.manager_.Problems(self.macaddr_, force)
    if problem_type:
      problems = filter(lambda x, y=problem_type: x.type() == y,
                        problems)
    if status:
      problems = filter(lambda x, y=status: x.status() == y,
                        problems)
    for problem in problems: problem.set_machine(self.name())
    return problems

  # Return a string representing the machine attributes that
  # are relevant to the use of this machine.  This is so that
  # machines can easily be clustered.  This makes assignment
  # much more efficient by reducing the number of free machines
  # to be examined.  TODO: This can be improved by ignoring
  # small insignificant variances in these values.
  def ClassString(self):
    """Get a string summarizing all the relevant attributes for
       a machine that will affect its ability to be assigned for a
       particular use."""
    str = '%s_%s_%s_%s_%s_%s_%s_%s_%s' % (
      self.colo(),
      self.rack(),
      self.hardware().cpumhz(),
      self.hardware().cpucnt(),
      self.hardware().hdcnt(),
      self.hardware().hdsize(),
      self.hardware().ram(),
      self.hardware().swap(),
      self.crawlnet(),
    )
    return str

  def __str__(self):
    return self.name_

#
# Hardware
#
# Represents machine hardware information.
#
class Hardware:

  def __init__(self, manager):
    self.manager_ = manager
    self.machine_ = None
    self.macaddr_ = None
    self.cpumhz_ = None
    self.cpucnt_ = None
    self.hdtype_ = None
    self.hdmounted_ = None
    self.hdcnt_ = None
    self.hdsize_ = None
    self.ram_ = None
    self.swap_ = None
    self.motherboard_ = None

    # Current observed state (optional)
    self.ramused_ = None
    self.hdused_ = None
    self.load_ = None

  def machine(self):
    return self.machine_

  def set_machine(self, machine):
    self.machine_ = machine

  def macaddr(self):
    return self.macaddr_

  def set_macaddr(self, macaddr):
    self.macaddr_ = macaddr

  def cpumhz(self):
    return self.cpumhz_

  def set_cpumhz(self, cpumhz):
    self.cpumhz_ = cpumhz

  def cpucnt(self):
    return self.cpucnt_

  def set_cpucnt(self, cpucnt):
    self.cpucnt_ = cpucnt

  def hdtype(self):
    return self.hdtype_

  def set_hdtype(self, hdtype):
    self.hdtype_ = hdtype

  def hdmounted(self):
    return self.hdmounted_

  def set_hdmounted(self, hdmounted):
    # Machine DB initializes unknown hdmounted to '-1'.
    # Seems cleaner to set this to the empty string.
    if hdmounted == '-1': hdmounted = ''
    self.hdmounted_ = hdmounted

  def hdcnt(self):
    return self.hdcnt_

  def set_hdcnt(self, hdcnt):
    self.hdcnt_ = hdcnt

  def hdsize(self):
    return self.hdsize_

  def set_hdsize(self, hdsize):
    self.hdsize_ = hdsize

  def ram(self):
    return self.ram_

  def set_ram(self, ram):
    self.ram_ = ram

  def swap(self):
    return self.swap_

  def set_swap(self, swap):
    self.swap_ = swap

  def motherboard(self):
    return self.motherboard_

  def set_motherboard(self, motherboard):
    self.motherboard_ = motherboard

  def hdused(self):
    return self.hdused_

  def set_hdused(self, hdused):
    self.hdused_ = hdused

  def ramused(self):
    return self.ramused_

  def set_ramused(self, ramused):
    self.ramused_ = ramused

  def load(self):
    return self.load_

  def set_load(self, load):
    self.load_ = load

  # CPU used is estimated from load observed on the machine
  def cpuused(self):
    if self.load_:
      return self.cpumhz_ * self.load_
    return None

  # TODO need to do a better job here. Use hdparm values?
  def hdutil(self):
    return None
    #if self.load_:
    #      return 1 - math.pow(math.e, -1.0 * self.load_/4.0)


  def __str__(self):
    return 'cpucnt:%s,cpumhz:%s,hdcnt:%s,hdsize:%s,ram:%s,swap:%s' % (
      self.cpucnt(), self.cpumhz(), self.hdcnt(),
      self.hdsize(), self.ram(), self.swap()
    )

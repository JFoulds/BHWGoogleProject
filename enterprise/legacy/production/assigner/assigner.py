#!/usr/bin/python2.4
#
# assigner.py - perform assignment operations.
#
# Copyright 2002 and onwards, Google
# Original Author: Eugene Jhong
#
# Simplified by Wanli Yang in 2007: 
#   GSAs use a very simple machine manager: MachineManagerSvsDirect()
#   There is no need to use the database, p4, and gfs. All the corresponding
#   redundant functions are removed from the origial assigner.py.

import os
import sys
import time
import traceback
import string
import random
import socket
import glob
import commands
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.production.common import setlib
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.production.babysitter import serverlib
from google3.enterprise.legacy.production.machinedb import machinelib
import types

class Error(Exception):
  """Assigner base error."""
  pass


# Split an argument string into a list.
# Arg lists can either be space separated within quotes or comma separated.
def _StringToList(arg):
  # Split on space.
  arg = string.strip(arg)
  list = string.split(arg)
  if len(list) == 1:
    # If there was only element, maybe it is comma separated.
    list = string.split(arg, ',')
  return map(string.strip, list)


def _PromptUser(msg):
  """Utility function to prompt user."""
  print msg,
  answer = sys.stdin.readline()
  if answer and answer[0] in ['y','Y']: return 1
  return 0


def _ServersFromSpecs(server_specs, srv_mgr):
  """Get list of server objects from server specifications.
  If srv_mgr is given, these servers are pulled from the given
  server manager.  Else, they are created.
  """
  servers = []
  for spec in server_specs:
    if srv_mgr and srv_mgr.ServersForSpec(spec):
      servers.extend(srv_mgr.ServersForSpec(spec))
    else:
      server = serverlib.Server()
      server.InitFromName(spec)
      server.set_srv_mgr(srv_mgr)
      servers.append(server)
  return servers

class Assigner:
  """
  Class for performing server assignments.
  """

  #-----------------------------------------------------------------------+
  # Constructor                                                           |
  #-----------------------------------------------------------------------+

  def __init__(self, unittest_mdb=None):
    """
    Initialize assigner object
    Args:
      unittest_mdb: {'ent1': {'hdcnt': '4',
                              'disk_size_GB': 'map:disk hda3:225.376007'}}
                    (for unit test only)
    """

    # Verbose output
    self._verbose = 0
    # Test level: 0 - none, 1 - sping, 2 - fulltest.
    self._test = 0
    # Machines to exclude from being used as candidate repl.
    self._exclude = []
    # Whether to prompt.
    self._force = 0
    # Whether to consider used machines for sharing repl.
    self._used = 1
    # Hosts already used in configs.
    self._used_hosts = []
    # Specified free machines.
    self._free = None
    # Whether to save out config.
    self._save = 1
    # Whether to setup servers.
    self._setup = 0
    # Whether to start servers.
    self._startup = 0

    self._mach_mgr = machinelib.MachineManagerSvsDirect(unittest_mdb)
    machinelib.InstallDefaultMachineManager(self._mach_mgr)

    # Initialize free pool cache.
    self._free_pools = {}

  def Connect(self):
    self._mach_mgr = machinelib.MachineManagerSvsDirect(unittest_mdb)
    machinelib.InstallDefaultMachineManager(self._mach_mgr)

  def Disconnect(self):
    pass

  #-----------------------------------------------------------------------+
  # Options                                                               |
  #-----------------------------------------------------------------------+

  def SetVerbose(self, val):
    self._verbose = val

  def SetTest(self, val):
    self._test = val

  def SetExclude(self, val):
    self._exclude = val

  def SetForce(self, val):
    self._force = val

  def SetUsed(self, val):
    self._used = val

  def SetOwner(self, val):
    self._owner = val

  def SetFree(self, val):
    self._free = val

  def SetSSHUser(self, val):
    self._ssh_user = val

  def SetSave(self, val):
    self._save = val

  def SetStartup(self, val):
    self._startup = val

  def Operations(self):
    return ['replace', 'repair', 'add',
            'remove', 'swap', 'addsets',
            'removesets', 'removenum']

  #-----------------------------------------------------------------------+
  # Allocation Methods                                                    |
  #-----------------------------------------------------------------------+

  def _ClassifyFree(self, free, pool_name):

    # Ensure free machines are unique.
    free = setlib.make_dict(free)
    free = free.keys()
    free.sort()

    inter = setlib.intersect(free, self._used_hosts)
    if inter:
      prodlib.log('Ignoring used machines: %s' % string.join(inter))
      free = setlib.diff(free, inter)

    # Preload hardware data.
    self._mach_mgr.MachineList(free, load_hardware=1)

    # Group free machines by their defining characteristics.  This
    # allows us to examine a smaller set of free machines as
    # candidates for a replacement.
    freedict = {}

    # Prune out free without hardware information.
    for host in free:
      mach = self._mach_mgr.Machine(host)
      if not mach or not mach.hardware(): continue
      freedict.setdefault(mach.ClassString(), []).append(mach.name())

    prodlib.log('Found %d free machs from %s.\n' % (len(free), pool_name))

    return freedict

  def _FreePools(self, server):
    """
    Get free pools associated with server.
    """
    if self._free is not None:
      return ['specified']
    else:
      pools = server.property('free_pool')
      if not pools: pools = ['global']
      return pools

  def _FreeDict(self, coloc, pool_name):
    """
    Get a free dictionary corresponding to the pool name and coloc.
    Args:
      coloc: coloc
      pool: pool name
    Returns:
      { 'free_class' : ['mach'] }
    """

    # Specified pools are not restricted by coloc.
    if pool_name == 'specified': coloc = None

    pool = self._free_pools.get((coloc, pool_name))
    if pool is not None: return pool

    # Find free machines if not specified by user.
    if pool_name == 'specified':
      pool = self._ClassifyFree(self._free, pool_name)
    else:
      prodlib.log('Finding free machs from %s:%s.' % (coloc, pool_name))
      free = []
      pool = self._ClassifyFree(free, pool_name)

    self._free_pools[(coloc, pool_name)] = pool
    return pool

  def _RemainingFree(self):
    """
    If using a specified free pool, return a list of remaining
    free servers.  Else return None.
    """
    if self._free is None:
      return None
    ret = []
    for machs in self._FreeDict(None, 'specified').values():
      ret.extend(machs)
    return ret

  def _AllocateHost(self, srv_mgr, server, force=0, exclude=None):
    """
    Allocate a machine for the passed in server.
    """

    for pool in self._FreePools(server):
      free_dict = self._FreeDict(server.property('coloc'), pool)
      repl = self._AllocateHostFromFreePool(srv_mgr, server,
                                            pool, free_dict, force=force,
                                            exclude=exclude)
      if repl: return repl

    return None

  def _AllocateHostFromFreePool(self, srv_mgr, server, pool,
                                free_dict, force=0, exclude=None):
    """
    Allocate a machine for the passed in server from specific pool.
    """

    cnstr_mgr = srv_mgr.constraint_mgr()

    # Find currently used compatible machines.
    used_hosts = {}
    if self._used:
      used_hosts = cnstr_mgr.Constraint('sharing').CompatibleHosts(srv_mgr,
                                                                   server)

    # Find free machine set from the free_dict - we get one of each class
    # of machines and save the others in its class.  We know that we can
    # rank members of the same class with the same score.
    free = {}
    for (machclass, hosts) in free_dict.items():
      if not hosts: continue
      free[hosts[0]] = hosts

    prodlib.log(' Allocating server for %s (used=%d, free=%d, pool=%s)' % \
          (server, len(used_hosts), len(free), pool))

    hosts = used_hosts.keys() + free.keys()
    # Exclude optional excludes.
    if self._exclude: hosts = setlib.diff(hosts, self._exclude)
    # Exclude locally specified excludes.
    if exclude: hosts = setlib.diff(hosts, exclude)
    random.shuffle(hosts)

    # Save the original host.
    orig_host = server.host()

    results = []
    failed = []

    # Assign weights and prune out ones that don't fit.
    for host in hosts:
      # Replace the server's host with the candidate host and verify.
      if self._verbose: prodlib.log('    ranking candidate: %s' % host)
      srv_mgr.ReplaceServer(server, host)
      servers = [server] + used_hosts.get(host, [])
      ver_results = cnstr_mgr.VerifyServer(srv_mgr, server,
                                           servers=servers,
                                           force=force)

      if self._verbose:
        for res in ver_results:
          if res.error(): status = 'fail'
          else: status = 'ok'
          prodlib.log('      %s: %s' % (status, res))

      if ver_results[-1].error():
        failed.append(host)
      else:
        # Compute total weight assigned to machine.
        weight = 0.0
        for res in ver_results:
          weight = weight + res.weight()
        if self._verbose:
          prodlib.log('      weight: %.2f' % weight)
        # Append results for machine.  We augment the hosts with
        # free machines of the same class since these should receive
        # the same score.
        if free.has_key(host):
          for free_host in free[host]:
            results.append((free_host, weight))
        else:
          results.append((host, weight))

    # Sort the results by highest weight to find the best candidate.
    results.sort(lambda x,y: -cmp(x[1], y[1]))

    for (host, weight) in results:

      prodlib.log(' Trying %s (%.2f)' % (host, weight))

      # Set server to new host.
      srv_mgr.ReplaceServer(server, host)

      if not used_hosts.has_key(host):
        # Remove the machine from the free list if necessary.
        key = self._mach_mgr.Machine(host).ClassString()
        hosts = free_dict[key]
        hosts.remove(host)
        if hosts == []: del(free_dict[key])

      # Return the server with its newly allocated host.
      prodlib.log(' Allocated %s (%.2f)' % (server, weight))
      return server

    # Failed so replace old host.
    srv_mgr.ReplaceServer(server, orig_host)

    prodlib.log(' Unable to allocate server.')
    return None

  #-----------------------------------------------------------------------+
  # Operation Methods                                                     |
  #-----------------------------------------------------------------------+

  # Replace all the specified machine names.
  def Replace(self, srv_mgr, names):

    prodlib.log('Beginning Replacements:\n')

    replaced = []
    succeeded = []
    failed = []

    # Find hosts to replace so we can exclude these from
    # being used as candidates.
    replace_hosts = []
    for name in names:
      servers = srv_mgr.ServersForSpec(name)
      for server in servers: replace_hosts.append(server.host())

    for name in names:

      # Find servers for name.  We copy this since the internal
      # array is modified when servers get replaced.
      servers = srv_mgr.ServersForSpec(name)[:]
      if not servers:
        prodlib.log('WARNING: no servers matched: %s' % name)

      for server in servers:
        if server.property('auto_assigned'): continue
        orig = '%s' % server
        if not self._AllocateHost(srv_mgr, server, exclude=replace_hosts):
          failed.append(orig)
        else:
          succeeded.append(orig)
          replaced.append('%s' % server)

    prodlib.log('\nreplace="%s"' % string.join(replaced))
    prodlib.log('success="%s"' % string.join(succeeded))
    prodlib.log('fail="%s"' % string.join(failed))
    if self._free:
      prodlib.log('free="%s"' % string.join(self._RemainingFree()))
    return (replaced, succeeded, failed, self._RemainingFree())


  # Repair all problems in configuration file.
  def Repair(self, srv_mgr, tries=10):

    cnstr_mgr = srv_mgr.constraint_mgr()

    prodlib.log('Beginning Repair:\n')

    replaced = []
    succeeded = []
    failed = {}
    seen_replaced = {}

    # Try to repair a fixed number of rounds.
    # We just repair one server from each problem each round.
    # This should fix most problems but for distribution/sharing
    # violations, multiple fixes for the problem may be needed.
    for _ in range(tries):

      # Find constraint violations.
      ver_results = cnstr_mgr.VerifyServers(srv_mgr)
      if not ver_results:
        prodlib.log('\nNo more problems to repair.')
        break
      replacements = []

      # Find new machines to try and fix.
      any_left = 0
      for res in ver_results:
        server = res.servers()[0]
        if not seen_replaced.has_key('%s' % server):
          any_left = 1
          replacements.append(server)
          seen_replaced['%s' % server] = 1

      # We tried all these before.
      if not any_left:
        prodlib.log('\nUnable to make further progress.')
        break

      # Fix problems by replacing the server.
      for server in replacements:
        if server.property('auto_assigned'): continue
        orig = '%s' % server
        if not self._AllocateHost(srv_mgr, server):
          failed[orig] = 1
        else:
          succeeded.append(orig)
          replaced.append('%s' % server)

    failed = failed.keys()

    prodlib.log('\nreplace="%s"' % string.join(replaced))
    prodlib.log('success="%s"' % string.join(succeeded))
    prodlib.log('fail="%s"' % string.join(failed))
    if self._free:
      prodlib.log('free="%s"' % string.join(self._RemainingFree()))

    ver_results = cnstr_mgr.VerifyServers(srv_mgr)
    if ver_results:
      prodlib.log('Unable to fully repair: Still more errors in config.\n')
      for res in ver_results:
        prodlib.log(' %s' % res)
    else:
      prodlib.log('Succesfully repaired')
    return (replaced, succeeded, failed, self._RemainingFree())


  # Remove the specified servers.
  def Remove(self, srv_mgr, names):

    # Silence pychecker.
    removed = []

    prodlib.log('Beginning Removal:\n')
    for name in names:
      # Make a copy since the servers for host will be internally modified.
      servers = srv_mgr.ServersForSpec(name)[:]
      if not servers:
        prodlib.log('WARNING: no servers matched: %s' % name)

      for server in servers:
        if server.property('auto_assigned'): continue
        prodlib.log(' Removing %s' % server)
        srv_mgr.RemoveServer(server)
        removed.append('%s' % server)
    prodlib.log('\nFinished Removal.')

    return (removed, [])


  # Add the specified servers.
  def Add(self, srv_mgr, names):

    cnstr_mgr = srv_mgr.constraint_mgr()

    added = []

    prodlib.log('Beginning Add:\n')
    for name in names:
      server = serverlib.Server()
      server.InitFromName(name)
      prodlib.log(' Adding %s' % server)
      srv_mgr.AddServer(server)
      if server.property('auto_assigned'):
        raise Error, 'Cannot add auto assigned server: %s' % server
      added.append('%s' % server)
      results = cnstr_mgr.VerifyServer(srv_mgr, server, errors_only=1)
      if results: prodlib.log(' WARNING: %s' % results[0])
    prodlib.log('\nFinished Add.')

    return (added, [])


  # Swap the specified host/server with given host.
  def Swap(self, srv_mgr, src, dst):

    cnstr_mgr = srv_mgr.constraint_mgr()

    added = []
    removed = []

    prodlib.log('Beginning Swap:\n')
    for server in srv_mgr.ServersForSpec(src):
      if server.property('auto_assigned'): continue
      prodlib.log(' Swapping %s with %s' % (server, dst))
      removed.append('%s' % server)
      srv_mgr.ReplaceServer(server, dst)
      added.append('%s' % server)
      results = cnstr_mgr.VerifyServer(srv_mgr, server, errors_only=1)
      if results: prodlib.log(' WARNING: %s' % results[0])
    prodlib.log('\nFinished Swap.')

    return (added, removed, [])


  # Given a new host, this function migrates some of the servers
  # from the existing machines to this new machine
  # We dont migrate 'excluded_server' servers
  # We first get the load on the new machine and all existing machines
  # We calculate a median load and aim for the new machine
  # to be loaded till that. We start migrating services one by one
  # until the load on the new machine exceeds the median load.
  # How do we choose which service and from what machine to migrate
  # next? We do it as follows:
  # For all the machines, we have the list of the services that it is
  # currently running. We chose that service that will lead in the
  # maximum benefit if it is taken from that machine and assigned
  # to the new one. We chose the global maximum on all the machine
  # and try to migrate that service.
  # PS: This hasnt been tested on production settings.
  # The only project using right now is enterpise. If you want to use
  # it and have any questions please contact sanjeevk@google.com
  def Rebalance(self, srv_mgr, new_host, excluded_servers=[]):
    cnstr_mgr = srv_mgr.constraint_mgr()

    # First get the load on the new machine
    load_on_new_machine = cnstr_mgr.GetLoad(srv_mgr, new_host, force=1)
    if load_on_new_machine.error():
      load_on_new_machine = 1.0
    else:
      load_on_new_machine = load_on_new_machine.weight()

    # calculate the hostloads on all the machines
    failed_replacements = []
    median_load = []
    for host in srv_mgr.Hosts():
      if host == new_host: continue
      load = cnstr_mgr.GetLoad(srv_mgr, host, force=1)
      if not load.error():
        median_load.append(load.weight())
    median_load.sort()

    # calculate the median load
    if len(median_load) == 0:
      # we assume that all machines are loaded to full
      median_load = 0.1
    else:
      median_load = median_load[len(median_load)/2]

    # Begin the cycle of rebalance
    added = []
    replaced = []
    tried_replaced = []
    while load_on_new_machine > median_load:
      server = None
      server = self._ChooseHostServerToRemove(srv_mgr, new_host,
                                              excluded_servers,
                                              failed_replacements)
      if not server: break
      replacement_server = str(server)
      replaced_host = server.host()
      tried_replaced.append(replacement_server)
      srv_mgr.ReplaceServer(server, new_host)
      results = cnstr_mgr.VerifyServer(srv_mgr, server)
      if results[-1].error():
        # we cannot migrate this service to the new machine
        # so backoff
        failed_replacements.append(replacement_server)
        srv_mgr.ReplaceServer(server, replaced_host)
      else:
        # We succeeded in replacing the service
        added.append(str(server))
        replaced.append(replacement_server)
        load_on_new_machine = cnstr_mgr.GetLoad(srv_mgr, new_host, force=1)
        load_on_new_machine = load_on_new_machine.weight()

    return (added, replaced, tried_replaced)


  # TODO: make this faster/more intelligent?
  # This decides a host port to replace to the new machine
  # For all the machines, we have the list of the services that it is
  # currently running. We chose that service that will lead in the
  # maximum benefit if it is taken from that machine and assigned
  # to the new one. We chose the global maximum on all the machine
  # and try to migrate that service.
  def _ChooseHostServerToRemove(self, srv_mgr, new_host, excluded_servers,
                                do_not_replace):
    cnstr_mgr = srv_mgr.constraint_mgr()
    hosts = srv_mgr.Hosts()
    max_benefit = 0
    max_benefit_server = None
    for host in hosts:
      if host == new_host: continue
      if len(srv_mgr.ServersForSpec(host)) <= 1:
        # there is just one service on this machine. So no sense to replace
        continue
      for server in srv_mgr.ServersForSpec(host):
        if server.property('auto_assigned'): continue
        if str(server) in excluded_servers: continue
        compatible_hosts = cnstr_mgr.Constraint('sharing').CompatibleHosts(
                             srv_mgr, server)
        compatible_hosts = compatible_hosts.keys()
        if not new_host in compatible_hosts:
          continue
        if str(server) in do_not_replace: continue

        # calculate the benefit if i remove this server from this machine
        benefits = cnstr_mgr.BenefitFromRemove(srv_mgr, server)
        total_benefit = 0
        for benefit in benefits:
          total_benefit = total_benefit + benefit.weight()

        # We also weigh the benefit in proportion to the number of services
        # that this machine is running
        total_benefit = total_benefit * len(srv_mgr.ServersForSpec(host))
        if total_benefit > max_benefit:
          max_benefit = total_benefit
          max_benefit_server = server

    return max_benefit_server


  # Add servers of specified type to reach specified number of sets.
  #
  #   srv_mgrs: May be a single server manager or a list. Lists are
  #     supported so that allocations may be done fairly and
  #     evenly between multiple sets of server managers which
  #     is useful for example with BART configs.
  #
  #   srvsetnums: This is a list of server set names potentially followed
  #     by the number of servers to allocate. For example:
  #   - 'doc:3,3 index:4,5'  would specify exactly 3 doc servers and
  #     minimum of 4 index servers but 5 desired index servers.  If the
  #     numbers are not specified, then the values specified in the
  #     shardlen constraint is used.  If the value of this var is None,
  #     then the method tries to allocate all sets according to the
  #     shardlen constraint
  #   - 'doc:3 index:4 is equivalent to 'doc:3,3 index:4,4'
  #
  #   TODO: Also add the ability to remove allocations that exceed the
  #   desired shardlength. [Easy]
  #
  #   TODO: Also add the ablility to balance shards per server bases.
  #   There is not point in having 3 rtslaves on shard 1 and 2 on shard 0.
  #   [Difficult]
  #
  def AddSets(self, srv_mgrs, srvsetnums, do_min=0):

    # Allow interface to take a single server manager.
    if type(srv_mgrs) != types.ListType:
      srv_mgrs = [srv_mgrs]

    # Find free dictionary for this set.
    srv_mgr = srv_mgrs[0]
    cnstr_mgr = srv_mgr.constraint_mgr()

    # Set up the sets to process from constraints if not specified.
    if not srvsetnums:
      srvsetnums = {}

      # First iterate through all existing sets and add those sets
      # that have a shard length constraint.  Note that if the shardlen
      # constraint is specified in defaults this will add all currently
      # created sets.
      for set in srv_mgr.Sets():
        if set.property('auto_assigned'): continue
        if cnstr_mgr.Constraint('shardlen').Constraint(set.name()):
          srvsetnums[set.name()] = 1

      # There may be some sets specified that are not currently in
      # existance.  Iterate through the list of explicitly specified
      # shardlen constraints and add sets for their types.
      for srvset in cnstr_mgr.Constraint('shardlen').server_sets():
        srvsetnums[srvset] = 1

      srvsetnums = srvsetnums.keys()
      srvsetnums.sort()

    # Set up the number of each type to add.
    tmp = []
    for srvsetnum in srvsetnums:
      if string.find(srvsetnum, ':') == -1:
        # TODO: Right now we're storing constraint descs in the constraint
        # manager.  This will move in another checkin to the server sets
        # and will be more readable when accessing.
        vals = cnstr_mgr.Constraint('shardlen').Constraint(srvsetnum)
        # If no shardlen constrs were specified for this type then ignore.
        if not vals:
          prodlib.log('Cannot add sets for %s - no shardlen constraint' %
                      srvsetnum)
          continue
        srvsetnum = '%s:%s,%s' % (srvsetnum, vals[0], vals[1])
      tmp.append(srvsetnum)
    srvsetnums = tmp

    prodlib.log('Beginning AddSet:\n')

    added = []
    failed = []
    tried = []

    for srvsetnum in srvsetnums:

      (srvset, num) = string.split(srvsetnum, ':')
      num = string.split(num, ',')
      if len(num) == 2:
        min = int(num[0])
        max = int(num[1])
      else:
        min = int(num[0])
        max = min

      if do_min:
        cnt = min
      else:
        cnt = max

      # For balancer sets, we add these with the same port range as the
      # balanced set if they were not present in the server manager object.
      if srvset[0] == '+':
        for srv_mgr in srv_mgrs:
          balset = srv_mgr.Set(srvset[1:])
          if not balset:
            raise Error, 'Cannot add set %s: no balanced set' % srvset
          set = srv_mgr.AddSet(srvset, balset.level())
          # Ensure port ranges are matched to balanced set.
          for port in balset.Ports(): set.AddPort(port)

      # Build union of all ports for this type.
      ports = {}
      for srv_mgr in srv_mgrs:
        set = srv_mgr.Set(srvset)
        if set != None:
          cur_ports = set.Ports()
          for port in cur_ports: ports[port] = 1
      ports = ports.keys()
      ports.sort()

      # Iterate up the slices so that we replace short shards first.
      for i in range(cnt+1):

        # To check if all allocations failed on the ports.
        every_port_failed = 1

        # For each port check if this shard is short.
        for port in ports:
          for srv_mgr in srv_mgrs:

            cnstr_mgr = srv_mgr.constraint_mgr()
            set = srv_mgr.Set(srvset)
            if set.property('auto_assigned'): continue
            if port not in set.Ports(): continue

            # If we have enough servers just skip.
            num = len(set.ServersForPort(port))
            if num >= i:
              every_port_failed = 0
              continue

            # Create a placeholder server object.
            server = serverlib.Server()
            server.InitFromName('%s%s:%s' % (srvset, i, port))
            srv_mgr.AddServer(server)
            # Try and allocate a host for it.
            force = 0
            if num < min: force = 1
            if self._AllocateHost(srv_mgr, server, force):
              every_port_failed = 0
              added.append('%s' % server)
            else:
              # Failed so remove it from the map.
              srv_mgr.RemoveServer(server)
              if force:
                failed.append('%s' % server)
              else:
                tried.append('%s' % server)

        # Break if we tried every port for this server manager and
        # could not allocate anything.
        if every_port_failed: break

    prodlib.log('\nsuccess="%s"' % string.join(added))
    prodlib.log('failed="%s"' % string.join(failed))
    prodlib.log('tried="%s"' % string.join(tried))
    if self._free:
      prodlib.log('free="%s"' % string.join(self._RemainingFree()))
    return (added, failed, tried, self._RemainingFree())


  # Remove servers of specified type to reach specified number of sets.
  def RemoveSets(self, srv_mgr, srvsetnums):

    prodlib.log('Beginning RemoveSet:\n')
    removed = []

    for srvsetnum in srvsetnums:

      (srvset, num) = string.split(srvsetnum, ':')
      num = int(num)
      set = srv_mgr.Set(srvset)
      if set.property('auto_assigned'): continue
      ports = set.Ports()

      # For each port, cut off servers that are located > num.
      for port in ports:
        servers = set.ServersForPort(port)
        cnt = len(servers) - num
        if cnt <= 0: continue

        for _ in range(cnt):
          server = servers[-1]
          removed.append('%s' % server)
          prodlib.log(' Removed server %s' % server)
          srv_mgr.RemoveServer(server)

    prodlib.log('\nremoved="%s"' % string.join(removed))
    prodlib.log('\nFinished RemoveSet.')
    return (removed, [])


  # Remove specified number of servers from the given server sets.
  # Servers are removed from the right most column, and largest port num.
  def RemoveNum(self, srv_mgr, srvsetnums):

    prodlib.log('Beginning RemoveNum:\n')
    removed = []

    for srvsetnum in srvsetnums:

      (srvset, num) = string.split(srvsetnum, ':')
      num = int(num)
      set = srv_mgr.Set(srvset)
      if set.property('auto_assigned'): continue
      indices = set.Indices()[:]
      indices.reverse()

      for index in indices:
        servers = set.ServersForIndex(index)[:]
        servers.reverse()
        # TODO: We may want to be less strict about not allowing
        # servers to be removed.
        for server in servers:
          if len(srv_mgr.ServersForHost(server.host())) > 1:
            raise Error, '%s has multiple roles' % server
          if num <= 0: break
          removed.append('%s' % server)
          srv_mgr.RemoveServer(server)
          prodlib.log(' Removed server %s' % server)
          num = num-1
        if num <= 0: break

    prodlib.log('\nremoved="%s"' % string.join(removed))
    prodlib.log('\nFinished RemoveNum.')
    return (removed, [])

  #-----------------------------------------------------------------------+
  # Main Interface
  #-----------------------------------------------------------------------+

  def RunOperation(self, configs, operation, args):
    """Assign machines to config.
    Args:
      configs: [googleconfig.Config, ...] - config objects to repair.
      operation: 'op' - assignment operation to perform.
      args: [arg1, ...] - arguments for the operation.
    Returns:
      changes: [(config, add, rem, fail), ...]

        config - googleconfig.Config object with respective changes.
        add - ['spec', ... ] - added servers or None for a removal.
        rem - ['spec', ... ] - removed servers or None for an addition.
        fail - ['spec', ... ] - failed to operate on these specs.

      add and rem are lists of changes to the config.  Entries in add and
      rem correspond.  For a replacement, both are not None.  For an
      addition, the corresponding entry in rem is None.  For a removal
      the corresponding entry in add is None.
    """

    # Make sure we have defined constraints in the configs.
    for config in configs:

      srv_mgr = config.GetServerManager()

      if not srv_mgr.constraint_mgr().HasConstraints():
        raise Error, 'No constraints defined in: %s' % \
          config.GetConfigFileName()

      self._used_hosts.extend(srv_mgr.Hosts())

    self._used_hosts = setlib.make_set(self._used_hosts)

    # Preload hardware info.
    self._mach_mgr.MachineList(self._used_hosts, load_hardware=1)

    # Results.
    changes = []

    # Replace Operation
    if operation == 'replace':
      names = _StringToList(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (added, removed, fail, free) = self.Replace(srv_mgr, names)
        changes.append((config, added, removed, fail))

    # Repair Operation
    elif operation == 'repair':
      tries = 10
      if len(args) > 1: tries = int(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (added, removed, fail, free) = self.Repair(srv_mgr, tries)
        changes.append((config, added, removed, fail))

    # Add Operation
    elif operation == 'add':
      names = _StringToList(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (added, fail) = self.Add(srv_mgr, names)
        changes.append((config, added, [], fail))

    # Remove Operation
    elif operation == 'remove':
      names = _StringToList(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (removed, fail) = self.Remove(srv_mgr, names)
        changes.append((config, [], removed, fail))

    # Swap Operation
    elif operation == 'swap':
      name0 = args[0]
      name1 = args[1]
      for config in configs:
        srv_mgr = config.GetServerManager()
        (added, removed, fail) = self.Swap(srv_mgr, name0, name1)
        changes.append((config, added, removed, fail))

    # Add Sets Operation
    elif operation == 'addsets':
      srvsetnums = None
      if args:
        srvsetnums = _StringToList(args[0])
      srv_mgrs = map(lambda x: x.GetServerManager(), configs)
      (added, fail, tried, free) = self.AddSets(srv_mgrs, srvsetnums)

      # Associate additions/failures with proper config
      fail = fail + tried
      for config in configs:
        srv_mgr = config.GetServerManager()
        cur_added = []
        cur_fail = []
        for spec in added:
          if srv_mgr.ServersForSpec(spec): cur_added.append(spec)
        for spec in fail:
          if srv_mgr.ServersForSpec(spec): cur_fail.append(spec)
        changes.append((config, cur_added, [], cur_fail))

    # Remove Sets Operation
    elif operation == 'removesets':
      srvsetnums = _StringToList(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (removed, fail) = self.RemoveSets(srv_mgr, srvsetnums)
        changes.append((config, [], removed, fail))

    # Remove Num Operation
    elif operation == 'removenum':
      srvsetnums = _StringToList(args[0])
      for config in configs:
        srv_mgr = config.GetServerManager()
        (removed, fail) = self.RemoveNum(srv_mgr, srvsetnums)
        changes.append((config, [], removed, fail))

    sys.stdout.flush()

    # Return config file changes.
    return changes

  def Assign(self, configs, operation, args):
    """Run assigner.
    Args:
      configs: [googleconfig.Config, ...] - config objects to repair.
      operation: 'op' - assignment operation to perform.
      args: [arg1, ...] - arguments for the operation.
    Returns:
      0 on successful replacements
      1 on no changes could be made
    """

    # Check if we have multiple configs with crawl, and get common owner.
    # Unowned machines that have servers reserved on them are
    # assigned to owner.
    is_crawl_config = 0
    for c in configs:
      cfg_owner = c.GetServerManager().property('owner')
      if self._owner is None:
        self._owner = cfg_owner
      elif self._owner != cfg_owner:
        prodlib.log("Can't deal with multiple owners in cfgs: %s vs. %s" %
                    (self._owner, cfg_owner))
        return 1
      if not is_crawl_config:
        is_crawl_config = c.var('CRAWLMASTER') != None
      # endif
    # endfor
    if is_crawl_config and len(configs) > 1:
      prodlib.log('More than one config specified per crawl change.'
                  ' Can\'t deal with this yet')
      return 1
    # endif

    # Perform requested operation.
    config_changes = self.RunOperation(configs, operation, args)

    changes = []

    # Create final change list and save config.
    for (config, add, rem, fail) in config_changes:

      srv_mgr = config.GetServerManager()

      if not add and not rem:
        prodlib.log('No changes for %s.' % config.GetConfigFileName())
        continue

      for (add_srv, rem_srv) in map(lambda x, y: (x, y), add, rem):
        if add_srv: add_srv = _ServersFromSpecs([add_srv], srv_mgr)[0]
        if rem_srv: rem_srv = _ServersFromSpecs([rem_srv], srv_mgr)[0]
        changes.append((add_srv, rem_srv, _GetGFSCluster(config)))

      if self._save:
        out_file = os.path.basename(config.GetConfigFileName()) + '.out'
        config.SaveServers(out_file)
        prodlib.log('Saved to %s.' % out_file)

    if not changes:
      prodlib.log('No changes for any configs.')
      return 1

    # Find added servers.
    new_servers = [i for (i, _, _) in changes if i is not None]

    fail = []

    # Remove these allocated from pending changes.
    new_changes = []
    for (add_srv, rem_srv, gfs_cluster) in changes:
      if add_srv in fail: continue
      new_changes.append((add_srv, rem_srv, gfs_cluster))
    changes = new_changes

    # Return failure if any setup failed.
    if fail:
      return 1
    else:
      return 0


# Usage: Print out usage information.
def Usage(msg=''):
  print """
  %s [options] <configfile> <operation> [args]

  Performs operations on servers in a config file.

  Saves modified config into <configfile>.out.

  Allocation Options:

    --free="host ..."     Use given list as set of free candidate machines
                          instead of using free machines from DB.  Note
                          that if this is not specified then the
                          machines are taken from the global free pool
                          unless LOCAL_FREE_POOL=1 is set in the config.
                          If this is the case, servers at the coloc whose
                          project is PROJECT, owner is OWNER and
                          servertype is 'freepool' are considered.

    --exclude="host ..."  Exclude given hosts as replacements.

    --noused              Do not share machines when allocating.

  Saving Options:

    --nosave              Do not save out config file in the current dir.
                          By default we save files in current dir with
                          '.out' extension.

  Diagnosis Options:

    --test                Do simple pingability test on candidates.

    --fulltest            Fully test all newly allocated hosts - requires
                          ssh access to machines.

    --ssh_user=<user>     The ssh user to access remote hosts to
                          perform diagnoses when running fulltest.

  Setup and Startup Options:

    --setup               Setup the assigned servers - requires ssh access
                          to machines.

    --startup             Startup the assigned servers - requires ssh access
                          to machines.

  Other Options:

    --force               Do not prompt before any operations.

  Operations:

    replacebad [maxrepl]
        Replace hosts that are diagnosed to be bad using the diagnoser.
        Will replace up to <maxrepl> servers (default = 10).

    replace "<host|[+]host:port> ..."
        Replace specified hosts/servers with free conforming hosts.

    repair [tries]
        Repair server constraint allocation problems in config.
        Tries up to <tries> iterations (default = 10).

    add "<[+]host:port> ..."
        Add specified servers at end of shard.

    remove "<host|[+]host:port> ..."
        Remove specified hosts/servers.

    swap <host|[+]host:port> <host>
        Swap specified host/server with new host.

    removenum "<[+]setname:num> ..."
        Remove num servers starting from end of servers for specified set.

    addsets "<[+]setname:num> ..."
        Add servers to try and reach specified number of slices for type.

    removesets "<[+]setname:num> ..."
        Remove servers to reach specified number of slices for type.

  Notes:

    - <configfile> may be specified with multiple files in double quotes.
      This is most useful for adding types for services with multiple
      sets.  This will allow you to add machines evenly between the
      sets.  For example:

      "config.a config.b" addsets "rtslave:30"

      Will take free machines and distribute them evenly between
      the two configs to try and reach up to 30 rtslaves.

  Examples:

    # Assign cache servers and index bals using machines from DB.
    assigner.py config.www.oct02.ex addsets cache:2,+index:3

    # Add doc balancers from existing doc servers.
    assigner.py --free="" config.www.oct02.ex addsets +doc:3

    # Replace some lousy machines.
    assigner.py --free="$free" config.www.oct02.ex replace "exa1 exa2"

  """ % os.path.basename(sys.argv[0])

  if msg: sys.stderr.write('ERROR: %s\n\n' % msg)

  sys.exit(1)


# Parse arguments and run program.
if __name__ == '__main__':

  try:

    assigner = Assigner()

    if sys.argv[1:]:
      import getopt
      (optlist, args) = getopt.getopt(sys.argv[1:], '', ['free=', 'noused',
                        'exclude=', 'fulltest', 'test', 'nosave',
                        'setup', 'startup',
                        'force', 'ssh_user=', 'auto',
                        'verbose'])

      for flag, value in optlist:
        if flag == '--free':
          assigner.SetFree(_StringToList(value))
        elif flag == '--noused':
          assigner.SetUsed(0)
        elif flag == '--nosave':
          assigner.SetSave(0)
        elif flag == '--test':
          assigner.SetTest(1)
        elif flag == '--fulltest':
          assigner.SetTest(2)
        elif flag == '--startup':
          assigner.SetStartup(1)
        elif flag == '--exclude':
          assigner.SetExclude(_StringToList(value))
        elif flag == '--force':
          assigner.SetForce(1)
        elif flag == '--ssh_user':
          assigner.SetSSHUser(value)
        elif flag == '--verbose':
          assigner.SetVerbose(1)

      if len(args) < 2:
        Usage()

      configfiles = _StringToList(args[0])
      operation = args[1]

      if operation not in assigner.Operations():
        Usage('UNKNOWN OPERATION: %s' % operation)

      # Load config file and perform assignment operations.
      configs = []
      for configfile in configfiles:
        configs.append(googleconfig.Load(configfile))

      retval = assigner.Assign(configs, operation, args[2:])
      sys.exit(retval)

    else:
      Usage()

  except SystemExit, e:
    sys.exit(e)
  except:
    traceback.print_exc()
    sys.exit(1)

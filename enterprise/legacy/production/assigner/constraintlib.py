#!/usr/bin/python2.4
#
# constraintlib.py - constraint objects and management.
#
# Copyright 2002 and onwards, Google
# Original Author: Eugene Jhong
#
# Based on Daniel Dulitz's verifyconfig.py.
#       and Bogdan Cocosel's add_capacity.py.
#
# This file manages the specification of constraints regarding
# the allocation of machines as servers.  The ConstraintManager
# loads data from a file which contains the following structure:
#
# Set of constraints specified per-type (no support for levels
# since these are going away).  If a constraint is
# specified in 'default' type, it applies to all types.
# To override the default, declare the constraint within the
# type (possibly setting the value to None to turn it off).
# Current constraint types are described below.  Balancer types
# are specified with a '+' prepended to the balanced type:
#
# CONSTRAINT_GENERAL = {
#   'default' : { 'distshard' : [0.34] },
#   'web' : { 'machine' : [ 'cpumhz:300,hdcnt:6', 'hdcnt:4', ] },
#   '+doc' : { 'machine' : [ 'cpucnt:2' ] },
#   ...
# }
#
# Following specifies allowable sharing of servers on a particular
# type of machine.  The types of machines should be listed in
# order of preference - i.e. first share on 6disks, then 4disks, etc..
# If the list is the empty list ([]), then sharing will be allowed
# on all machine types.
#
# CONSTRAINT_SHARING = {
#  'doc, doc, +doc' : ['cpumhz:500+|hdcnt:6', 'cpumhz:500+|hdcnt:4'],
#  'lcaserver, lcaserver, lcaserver, lcaserver, lcaserver' : ['hdcnt:4'],
#   ...
# }
#
# TODO: Share this map with the binpusher and other things that need
# to know about shared servers on a machine.
#
# A constraint violation may be suppressed from verification by
# placing the host or [+]host:port specification into the exceptions
# map below.  A complete type of constraint violation may be suppressed
# by stating the constraint name with a value of 'None'.
#
# CONSTRAINT_EXCEPTIONS = {
#   'sharing' : 'exb7',
#   'machine' : '+exbb12:4000 exj7:9400 exe34',
# }
#
# Current types of constraints:
#
# Host Constraint:
#
#   'host' : [ 'regex1', 'regex2', ... ]
#
# The given srvset can only run on hostnames matching one of the listed
# regular expressions.  For assignment it will prefer machines types
# listed earlier in the list.
#
# Machine Constraint:
#
#   'machine' : [ 'srvset1', 'srvset2', ... ]
#
# The given srvset can only run on machines of the specified type.
# For assignment it will prefer machines types listed earlier in the list.
#
# Sharing Constraint:
#
# This is described above under the CONSTRAINT_SHARING map.
# For assignment, sharing will always be prefered to using a new machine.
#
# Distribution Constraints:
#
#   'distshard' : [max]
#   'distslice' : [max]
#   'distset' : [max]
#
# For the given type, specifies a limit on how many machines
# from each rack can be in the given group (shard / slice / set).
# A shard is servers on a port.  A slice is servers of the same
# type in the same column.  A set is all servers of a given type.
# If max <= 1.0, then the value is treated as a maximum percentage.
# If max > 1, then the value is treated as an absolute number.
# Note however, that this restriction is relaxed if there are
# not enough servers in the group to meet the restriction (i.e
# max is 0.33 but there are only 2 servers in the set - best you
# can do is 0.5).
#
# Shard Constraints:
#
#   'numshards' : ['relprime', '<type>']  # rel prime with other type
#   'numshards' : ['equals', '<type>']    # numshards equals other type
#   'numshards' : [min, max]              # numshards in range
#
# Verifies number of shards.
#
#

import string
import copy
import math
import types
import re
from google3.enterprise.legacy.production.babysitter import masterconfig
from google3.enterprise.legacy.production.common import cachelib
from google3.enterprise.legacy.production.babysitter import serverlib
from google3.enterprise.legacy.production.machinedb import machinelib

#------------------------------------------------------------------------------
# Constraints
#------------------------------------------------------------------------------


class Error(Exception):
  """Constraint lib exception base class."""
  pass


# ERROR indicates a constraint violation.
ERROR = -1.0

#
# Result
#
# Class holds the result of a constraint check.  It contains
# the name of the constraint, the weight of the configuration,
# (i.e. how well it passed - this is used for assignment)
# a description and the set of servers that were involved in
# the decision.  Note that servers can be a list of server
# objects or a list of hostnames (some constraint checks don't
# apply to servers but hosts).
#
class Result:

  def __init__(self, name, weight, desc, servers):
    self.name_ = name
    self.weight_ = weight
    self.desc_ = desc
    self.servers_ = servers

  def name(self):
    return self.name_

  def set_name(self, name):
    self.name_ = name

  def weight(self):
    return self.weight_

  def set_weight(self, weight):
    self.weight_ = weight

  def desc(self):
    return self.desc_

  def set_desc(self, desc):
    self.desc_ = desc

  def servers(self):
    return self.servers_

  def set_servers(self, servers):
    self.servers_ = servers

  def error(self):
    return self.weight_ == ERROR

  def __str__(self):
    return '%s: %s (%.2f) %s' % (self.name(), self.desc(), self.weight(),
                                 map(lambda x: str(x), self.servers()))

#
# Constraint
#
# This is a base class for all constraints.  A constraint
# should subclass off this and override the
# VerifyServer[s]/BenefitFromRemove methods.
#
class Constraint:

  def __init__(self, name):
    # Name of the constraint.
    self.name_ = name
    # Scale factor for this constraint.  The result weights
    # are multiplied by this factor to balance importance.
    self.scale_ = 1.0
    # Map of type names to the constraint data for this constraint.
    self.constraints_ = {}
    # Is this constraint for verification only?
    self.ver_only_ = 0
    # Machine manager.
    self.mach_mgr_ = None
    # Machine type manager.
    self.machtype_mgr_ = None
    # Resource Manager
    self.resrc_mgr_ = None

  def name(self):
    return self.name_

  def mach_mgr(self):
    return self.mach_mgr_

  def set_mach_mgr(self, mach_mgr):
    self.mach_mgr_ = mach_mgr

  def machtype_mgr(self):
    return self.machtype_mgr_

  def set_machtype_mgr(self, machtype_mgr):
    self.machtype_mgr_ = machtype_mgr

  def resrc_mgr(self):
    return self.resrc_mgr_

  def set_resrc_mgr(self, resrc_mgr):
    self.resrc_mgr_ = resrc_mgr

  def scale(self):
    return self.scale_

  def set_scale(self, scale):
    self.scale_ = scale

  def server_sets(self):
    return self.constraints_.keys()

  # Add a constraint.  Constraints with 'None' data are not added.
  # This is how a constraint can be overriden in a including config
  # file.
  def AddConstraint(self, srvset, constraint):
    if srvset != 'default' and not serverlib.IsValidSetName(srvset):
      raise Error, 'Invalid set name: %s in constraint' % srvset
    if constraint != None:
      self.constraints_[srvset] = constraint

  # Get a constraint for given type.  If the type is not
  # found then return the 'default' constraint if any.
  def Constraint(self, srvset):
    if self.constraints_.has_key(srvset):
      return self.constraints_[srvset]
    elif self.constraints_.has_key('default'):
      return self.constraints_['default']
    else:
      return []

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  # Verify if a server passes the constraint.
  # Return a Result object. Force will make the it use less stingent
  # criterion while calculating the weight. Currently this is only used
  # for ResourceConstraint.
  #
  # The servers param is an override for all servers on the
  # host of the server to verify.  This is used by the sharing
  # constraint to check compatible servers.  If it is not specified
  # then srv_mgr is queried.  This is used to support externally
  # referenced sharing constraints.
  def VerifyServer(self, srv_mgr, server, servers=None, force=0):
    # Silence pychecker.
    srv_mgr = srv_mgr
    servers = servers
    server = server
    force = force
    return self.Result(1.0, '', [])

  # Verify all servers pass constraints.
  # Return a list of Result objects for each violation/pass.
  def VerifyServers(self, srv_mgr, force=0):
    # Silence pychecker.
    srv_mgr = srv_mgr
    force = force
    return []

  # Test if this constraint is to be used for verification only
  # and not for assignment.
  def VerifyOnly(self):
    return self.ver_only_

  # Test if this constraint has a constraint for any type.
  def HasConstraints(self):
    return len(self.constraints_) > 0

  # Utility method to create a Result object.
  def Result(self, weight, desc, servers):
    weight = self.scale_ * weight
    return Result(self.name_, weight, desc, servers)

  # Utility method to create a Result object that indicates an error.
  def Error(self, desc, servers):
    return Result(self.name_, ERROR, desc, servers)

#
# HostConstraint
#
# Format: 'host' : ['regex1', 'regex2', ... ]
#
# Check if hostname matches regex.  Matches early in the list are weighted
# higher.
#
class HostConstraint(Constraint):

  def __init__(self):
    Constraint.__init__(self, 'host')

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServer(self, _, server, servers=None, force=0):

    # Silence pychecker.
    force=force
    servers=servers

    # Get list of machine types for this type.
    host_regexes = self.Constraint(server.srvset())
    if not host_regexes:
      return self.Error('no host regexes for %s' % server.srvset(), [server])

    # See if the server's machine satisfies any of the available types.
    match = None
    for regex in host_regexes:
      if re.match(regex, server.host()):
        match = regex
        break

    if not match:
      return self.Error('no match in %s' % server.srvset(), [server])
    else:
      return self.Result(calc_listpos_weight(host_regexes, match),
                         'match %s' % match, [server])

  def VerifyServers(self, srv_mgr, force=0):
    force = force
    results = []
    for server in srv_mgr.Servers():
      results.append(self.VerifyServer(srv_mgr, server))
    return results

#
# MachineConstraint
#
# Format: 'machine' : ['constraints1', 'constraints2', ... ]
#
# Check if machine satisfies specified machine types for servertype.
# For assignment machines early in the list are weighted higher.
#
class MachineConstraint(Constraint):

  def __init__(self):
    Constraint.__init__(self, 'machine')

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServer(self, _, server, servers=None, force=0):

    # Silence pychecker.
    force=force
    servers=servers

    # Get list of machine types for this type.
    machtypes = self.Constraint(server.srvset())
    if not machtypes:
      return self.Error('no mach types for %s' % server.srvset(), [server])

    # See if the server's machine satisfies any of the available types.
    mach = self.mach_mgr().Machine(server.host())
    (machtype, desc) = self.machtype_mgr().FindMachineType(mach, machtypes)

    if not machtype:
      return self.Error('no match in %s (%s) - %s' % (server.srvset(),
                                                      mach.hardware(), desc), [server])
    else:
      return self.Result(calc_listpos_weight(machtypes, machtype),
                         'match %s (%s)' % (machtype, mach.hardware()), [server])

  def VerifyServers(self, srv_mgr, force=0):
    force = force
    results = []
    for server in srv_mgr.Servers():
      results.append(self.VerifyServer(srv_mgr, server))
    return results

#
# SharingConstraint
#
# Format: CONSTRAINT_SHARING = { 'doc, doc, +doc':['hdcnt:6', 'hdcnt:4'], ... }
#
# Check if servers have allowable sharing.  The uses must be in
# the specified allowed uses and on the appropriate types of machines.
# For assignment, we prefer to share, and we prefer machine types
# early on in the list.  A blank list for machine types indicates
# that sharing is allowed on any available machine.
#
class SharingConstraint(Constraint):

  def __init__(self):
    Constraint.__init__(self, 'sharing')
    # Use an array of constraints rather than a map from types.
    self.constraints_ = []
    self.strict_ = 1

  # Set whether to do strict checking.  Non-strict checking does
  # not care what the hardware requirements are but only that
  # the types specified are compatible.
  def set_strict(self, strict):
    self.strict_ = strict

  # Get whether to do strict checking.  See above for explanation.
  def strict(self):
    return self.strict_

  # Add a constraint.  srvsets is a string of server srvsets and machtypes
  # is a list of machine constraints.
  def AddConstraint(self, srvsets, machtypes):

    srvsets = map(lambda x: string.strip(x), string.split(srvsets, ','))

    tmp = []
    for srvset in srvsets:
      service = None
      if string.find(srvset, ':') != -1:
        (service, srvset) = string.split(srvset, ':')
      tmp.append((srvset, service))
    srvsets = tmp
    srvsets.sort()

    for (srvset, service) in srvsets:
      if srvset != 'default' and not serverlib.IsValidSetName(srvset):
        raise Error, 'Invalid set name: %s in constraint' % srvset

    if machtypes != None:
      self.constraints_.append((srvsets, machtypes))

  # Find a list of sharing constraints containing the given
  # srvset.
  def Constraints(self, srvset):
    constraints = []
    for (srvsets, machtypes) in self.constraints_:
      if serverlib.is_contained([srvset], map(lambda x: x[0], srvsets)):
        constraints.append((srvsets, machtypes))
    return constraints

  # Verify whether the host has allowed uses.  We use the passed
  # in allowable shared types if specified.
  def VerifyHost(self, srv_mgr, host, servers, constraints=None):

    # Get list of all ports that this server listens on.  Currently
    # just used to handle the hacky rtslaves that listen on 3 different ports.
    def used_ports(srv_mgr, server):
      ports = [server.port()]
      if server.servertype() == 'rtslave':
        base_ports = srv_mgr.config().var('RT_BASE_PORTS')
        if base_ports:
          for (mtype, port) in base_ports.items():
            shard = srv_mgr.Set(server.srvset()).Shard(server.port())
            ports.append(port + shard)
      return ports

    # Test if we should use the passed in constraints or all constraints.
    if not constraints:
      constraints = self.constraints_

    # One use cannot violate sharing constraints.
    if len(servers) <= 1:
      return self.Result(0.0, 'host has one use', servers)

    seen_ports = {}
    ports = []
    # Build list of existing ports used by existing servers on host.
    for server in servers:
      ports.extend(used_ports(srv_mgr, server))

    for port in ports:
      if seen_ports.has_key(port):
        return self.Error('duplicate port: %s' % port, servers)
      seen_ports[port] = 1

    # Find the currently used types for this host.
    srvsets = map(lambda x: x.srvset(), servers)
    srvsets.sort()

    machtype = None

    # Iterate through the compatible allowed types and see
    # if the current usage is within one of these.
    for (compatible_srvsets, machtypes) in constraints:

      # Test if the uses are listed in compatible uses.
      if not serverlib.is_contained(srvsets,
                                    map(lambda x: x[0], compatible_srvsets)):
        continue

      # If sharing is allowed on any machine, we're done.
      if machtypes == [] or not self.strict_:
        return self.Result(1.0,
          'compatible uses: %s on %s' % (srvsets, machtype), servers)

      mach = self.mach_mgr().Machine(host)
      (machtype, desc) = self.machtype_mgr().FindMachineType(mach, machtypes)
      # Ensure that the machine fits the specified criteria.
      if machtype:
        # If we're OK with the sharing, score based on which type of
        # machine we've hit in the machtypes.
        return self.Result(calc_listpos_weight(machtypes, machtype),
          'compatible uses: %s on %s - %s' % (srvsets, machtype, desc), servers)

    return self.Error('incompatible uses: %s' % srvsets, servers)

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServer(self, srv_mgr, server, servers=None, force=0):
    force = force
    if not servers: servers = srv_mgr.ServersForHost(server.host())
    return self.VerifyHost(srv_mgr, server.host(), servers)

  def VerifyServers(self, srv_mgr, force=0):
    force = force
    results = []
    for host in srv_mgr.Hosts():
      # TODO: Remove this once the 'none' hack is removed from blimpie.
      if host[:4] == 'none': continue
      results.append(self.VerifyHost(srv_mgr, host,
                                     srv_mgr.ServersForHost(host)))
    return results

  # Find the set of hosts currently used in server manager,
  # that are running servers that are compatible with the passed
  # in server's type.  This method returns a dictionary mapping
  # hosts to servers that currently run on that host.  These hosts
  # have an available slot for the "new_server".
  def CompatibleHosts(self, srv_mgr, new_server):

    # Find if this srvset supports any sharing.
    constraints = self.Constraints(new_server.srvset())
    if not constraints: return {}

    coloc = srv_mgr.property('coloc')
    hosts = {}

    # Find the list of hosts/servers from each compatible set.
    # This basically parses a key of the form '[<service>]:srvset, ...'
    # and loads in the servers from the specified sets.  All these
    # servers comprise the candidate list of servers to use when
    # judging sharing constraints.
    constraints = copy.deepcopy(constraints)
    seen_srvsets = {}
    for (srvsets, _) in constraints:
      for (srvset, service) in srvsets:
        servers = None
        # We've already loaded servers from this set.
        if seen_srvsets.has_key((srvset, service)): continue
        seen_srvsets[(srvset, service)] = 1
        if service and service != srv_mgr.config().GetServiceName():
          # The server set is in an external set.
          servers = masterconfig.GetServers(service, srvset, colos=[coloc])
        else:
          # The server set is in the local set.
          set = srv_mgr.Set(srvset)
          if set: servers = set.Servers()
        if servers:
          for server in servers:
            hosts.setdefault(server.host(), []).append(server)

    # Iterate through hosts and find compatible ones.
    compatible = {}
    for host, servers in hosts.items():
      # Don't want to consider myself.
      if new_server.host() == host:
        continue
      # Incompatible ports.
      ports = map(lambda x: x.port(), servers)
      if new_server.port() in ports:
        continue
      # Check if the host has compatible uses.
      res = self.VerifyHost(srv_mgr, host, servers + [new_server], constraints)
      if res.error():
        continue
      compatible[host] = servers

    return compatible

#
# DistributionConstraint
#
# Format: 'distshard' : [max]
#         'distslice' : [max]
#         'distset'   : [max]
#
# Specifies an upper limit on the amount of each rack in a
# given group (shard/slice/set) (defined above).
#
class DistributionConstraint(Constraint):

  def __init__(self, name):
    Constraint.__init__(self, name)

  # Split set of servers into a dictionary of server lists keyed by rack.
  def SplitByRack(self, servers):
    racks = {}
    for server in servers:
      rack = server.rack()
      tmp = racks.get(rack, [])
      tmp.append(server)
      racks[rack] = tmp
    return racks

  # Checks whether a given group satisfies the constraint.
  # The servers are given in group.  Size is the size of the
  # group (in case the group has empty slots).  The wanted fields
  # are to focus the attention of this method only on the specified
  # host and rack.
  def VerifyGroup(self, group, size, wanted_host = None, wanted_rack = None,
                  duphost_check = 1):

    # Test if only has one host.
    if len(group) <= 1:
      return [self.Result(1.0, 'one or less in group', group)]

    # Test if there exist any constraints.
    max = self.Constraint(group[0].srvset())
    if not max:
      return [self.Result(1.0, 'no cnstrs for %s' % group[0].srvset(), group)]

    results = []

    # Find out if any host is repeated 2x in this group.
    # If so return an error.
    host2count = {}
    for server in group:
      tmp = host2count.get(server.host(), [])
      tmp.append(server)
      host2count[server.host()] = tmp

    if duphost_check:
      for (host, servers) in host2count.items():
        if wanted_host and host != wanted_host: continue
        if len(servers) > 1:
          results.append(self.Error('dup host in group: %s' % host, servers))
          if wanted_host: return results

    # Split group by racks.
    racks = self.SplitByRack(group)
    max_pct = float(max[0])

    # Convert absolute number to relative percentage.
    # This is to support the syntax that if max < 1.0, it is treated
    # as a percentage.  Else, it is treated as an absolute number.
    if (max_pct > 1.0): max_pct = float(max_pct) / size
    # Check if the max percent is too large for the length of this group.
    # For example, if max_pct is 0.33, but there are only 2 servers
    # in the group, it would be impossible to satisfy the constraint.
    if max_pct < 1.0 / size:
      max_pct = 1.0 / size

    for (rack, rackservers) in racks.items():
      if wanted_rack and rack != wanted_rack: continue
      count = len(rackservers)
      pct = float(count) / float(size)
      if pct > max_pct:
        desc = '%% on %s: %.2f > %.2f' % (rack, pct, max_pct)
        results.append(self.Error(desc, rackservers))
      else:
        # Weight is normalized to "good" range.
        weight = 1.0 - (pct / max_pct)
        desc = '%% on %s: %.2f <= %.2f' % (rack, pct, max_pct)
        results.append(self.Result(weight, desc, rackservers))

    return results

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServer(self, srv_mgr, server, servers=None, force=0):
    force = force
    servers = servers

    if self.name_ == 'distshard':
      set = srv_mgr.Set(server.srvset())
      group = set.ServersForPort(server.port())
      size = len(group)
      duphost_check = 1
    elif self.name_ == 'distslice':
      set = srv_mgr.Set(server.srvset())
      group = set.ServersForIndex(server.index())
      size = set.NumShards()
      duphost_check = 0
    else:
      set = srv_mgr.Set(server.srvset())
      group = set.Servers()
      size = len(group)
      duphost_check = 0

    result = self.VerifyGroup(group, size, wanted_host = server.host(),
                              wanted_rack = server.rack(),
                              duphost_check = duphost_check)
    return result[0]

  def VerifyServers(self, srv_mgr, force=0):
    force = force

    results = []
    if self.name_ == 'distshard':
      for set in srv_mgr.Sets():
        for port in set.Ports():
          group = set.ServersForPort(port)
          results.extend(self.VerifyGroup(group, len(group), duphost_check = 1))
    elif self.name_ == 'distslice':
      for set in srv_mgr.Sets():
        for index in set.Indices():
          group = set.ServersForIndex(index)
          results.extend(self.VerifyGroup(group, set.NumShards(),
                                          duphost_check = 0))
    else:
      for set in srv_mgr.Sets():
        group = set.Servers()
        results.extend(self.VerifyGroup(group, len(group), duphost_check = 0))

    return results

#
# ShardLenConstraint
#
# Format: 'shardlen' : [min, desired]
#
# Verifies shard lengths.
#
class ShardLenConstraint(Constraint):

  def __init__(self):
    Constraint.__init__(self, 'shardlen')
    self.ver_only_ = 1

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServers(self, srv_mgr, force=0):
    force = force
    results = []

    for set in srv_mgr.Sets():
      cnstr = self.Constraint(set.name())
      if not cnstr: continue

      for port in set.Ports():
        shardlen = len(set.ServersForPort(port))
        if shardlen < cnstr[0]:
          results.append(self.Error('#%s:%s (%d) out of range [%d %d]' % \
            (set.name(), port, shardlen, cnstr[0], cnstr[1]), []))

    return results

#
# NumShardsConstraint
#
# Format: 'numshards' : ['relprime', '<type>']  # rel prime with other type
#         'numshards' : ['equals', '<type>']    # numshards equals other type
#         'numshards' : [min, max]              # numshards in range
#
# Verifies number of shards.
#
class NumShardsConstraint(Constraint):

  def __init__(self):
    Constraint.__init__(self, 'numshards')
    self.ver_only_ = 1

  def BenefitFromRemove(self, srv_mgr, server):
    # silence the pychecker
    srv_mgr = srv_mgr
    server = server
    return self.Result(0.0, '', [])

  def VerifyServers(self, srv_mgr, force=0):
    force = force

    # Greatest Common Divisor
    def gcd(a, b):
      while a != 0:
        a, b = b%a, a
      return b

    results = []

    for set in srv_mgr.Sets():
      cnstr = self.Constraint(set.name())
      if not cnstr: continue

      numshards = set.NumShards()
      if cnstr[0] == 'relprime':
        other = cnstr[1]
        othernumshards = srv_mgr.Set(other).NumShards()
        if numshards > 1 and othernumshards > 1 and \
          gcd(numshards, othernumshards) != 1:
          results.append(self.Error('#%s (%d) and #%s (%d) not rel prime' % \
            (set.name(), numshards, other, othernumshards), []))
      elif cnstr[0] == 'equals':
        other = cnstr[1]
        othernumshards = srv_mgr.Set(other).NumShards()
        if numshards != othernumshards:
          results.append(self.Error('#%s (%d) != #%s (%d)' % \
            (set.name(), numshards, other, othernumshards), []))
      else:
        if numshards < cnstr[0] or numshards > cnstr[1]:
          results.append(self.Error('#%s (%d) out of range [%d %d]' % \
            (set.name(), numshards, cnstr[0], cnstr[1]), []))

    return results

#
# ResourceConstraint
#
# Format: 'resource' : ['constraint']
#
# Check if machine has enough resources left to satisfy the given
# servertype.
#
class ResourceConstraint(Constraint):
  def __init__(self):
    Constraint.__init__(self, 'resource')

  # the benefit from removing a server is the calculcated as
  # (current_load - estimated_load_on_removal) / current_load
  def BenefitFromRemove(self, srv_mgr, server):
    current_load = self.GetLoad(srv_mgr, server.host(), force=1)
    srv_mgr.RemoveServer(server)
    estimated_load = self.GetLoad(srv_mgr, server.host(), force=1)
    srv_mgr.AddServer(server)
    if current_load.error() or estimated_load.error():
      return self.Error('Cant determine benefit for %s' % \
                         server.srvset(), [server])
    benefit = (estimated_load.weight() -
                        current_load.weight())/current_load.weight()
    return self.Result(benefit, '', [])

  def GetLoad(self, srv_mgr, host, force=1):
    servers = srv_mgr.ServersForHost(host)
    resources = []
    for srvr in servers:
      resources = resources + self.Constraint(srvr.srvset())
    mach = self.mach_mgr().Machine(host)
    load = self.resrc_mgr().ComputeLoad(mach, resources, "", force)
    if load > 0.0:
      return self.Result(load, 'estimated load', servers)
    else:
      return self.Error('too high load for %s' % host, [])


  # See all the services assigned to this server's host and return the
  # estimated load if we assign this server to it's host. We assume that
  # the server is not yet assigned to the host while computing load
  def VerifyServer(self, srv_mgr, server, servers=None, force=1):

    # remove the server and then add it back. Since servers point to the
    # internal data structures of srv_mgr, we need to do a copy
    if server in srv_mgr.Servers():
      srv_mgr.RemoveServer(server)
      servers = srv_mgr.ServersForHost(server.host())[:]
      srv_mgr.AddServer(server)
    else:
      servers = srv_mgr.ServersForHost(server.host())

    resources = []
    for srvr in servers:
      resources = resources + self.Constraint(srvr.srvset())

    server_res = self.Constraint(server.srvset())
    if server_res == []: server_res = ""
    else: server_res = server_res[0]

    mach = self.mach_mgr().Machine(server.host())

    try:
      load = self.resrc_mgr().ComputeLoad(mach, resources, server_res, force)
    except AttributeError:
      # this usually means that the facts abt this machine are not available
      return self.Error('No facts available for machine %s' % \
                                                      mach.name(), [server])
    if load > 0.0:
      return self.Result(load, 'estimated load', servers)
    else:
      return self.Error('too high load for %s' % server.srvset(), [server])

  # Verify the given assignment of servers
  def VerifyServers(self, srv_mgr, force=1):
    results = []
    for host in srv_mgr.Hosts():
      fakeserver = serverlib.Server()
      fakeserver.set_host(host)
      results.append(self.VerifyServer(srv_mgr, fakeserver, force))
    return results

#------------------------------------------------------------------------------
# Constraint Manager
#------------------------------------------------------------------------------

#
# ConstraintManager
#
# Manages loading constraints and verification of all relevant
# constraints.
#
class ConstraintManager:

  def __init__(self):

    # Register constraint types.
    self.constraint_list_ = [
      MachineConstraint(),
      DistributionConstraint('distshard'),
      DistributionConstraint('distslice'),
      DistributionConstraint('distset'),
      SharingConstraint(),
      NumShardsConstraint(),
      ShardLenConstraint(),
      ResourceConstraint(),
      HostConstraint(),
    ]

    # Create a dictionary for fast lookup.
    self.constraints_ = {}
    for cnstr in self.constraint_list_:
      self.constraints_[cnstr.name()] = cnstr

    # Exceptions stores a map of constraint types to
    # a dictionary whose keys are server names that are allowed
    # to violate the constraint.
    self.exceptions_ = {}

    self.machtype_mgr_ = None
    self.resrc_mgr_ = None

  def mach_mgr(self):
    return self.mach_mgr_

  def set_mach_mgr(self, mach_mgr):
    self.mach_mgr_ = mach_mgr

  def machtype_mgr(self):
    return self.machtype_mgr_

  def set_machtype_mgr(self, machtype_mgr):
    self.machtype_mgr_ = machtype_mgr

  def resrc_mgr(self):
    return self.resrc_mgr_

  def set_resrc_mgr(self, resrc_mgr):
    self.resrc_mgr_ = resrc_mgr

  # Load constraints from a config object.
  def LoadConstraints(self, cnstr_data):

    # We need access to a machine manager.
    self.set_mach_mgr(machinelib.MachineManagerFactory())

    # We need access to machine type manager and resource manager.
    self.set_machtype_mgr(MachineTypeManager(self.mach_mgr()))
    self.set_resrc_mgr(ResourceManager(self.mach_mgr()))
    for cnstr in self.constraint_list_:
      cnstr.set_mach_mgr(self.mach_mgr())
      cnstr.set_machtype_mgr(self.machtype_mgr())
      cnstr.set_resrc_mgr(self.resrc_mgr())

    # Add some default constraints for non enterprise configs
    # so that no sharing is allowed by default and no machine type matches.
    if not cnstr_data.var('ENTERPRISE'):
      self.Constraint('sharing').AddConstraint('default', [])
      self.Constraint('machine').AddConstraint('default', ['cpucnt:0,ram:0'])
      self.Constraint('distshard').AddConstraint('default', [1.0])
      self.Constraint('distslice').AddConstraint('default', [1.0])

    sharing_constraints = cnstr_data.var('CONSTRAINT_SHARING', {})
    auto_assign_sets = cnstr_data.var('AUTO_ASSIGN_SETS', {})
    general_constraints = cnstr_data.var('CONSTRAINT_GENERAL', {})
    exceptions = cnstr_data.var('CONSTRAINT_EXCEPTIONS', {})
    weights = cnstr_data.var('CONSTRAINT_WEIGHTS', {})

    # Set weights.
    for cnstr, scale in weights.items():
      self.Constraint(cnstr).set_scale(scale)

    # Process exceptions into quick lookup dictionary.
    # Exceptions are server/host violations that are to be ignored.
    self.exceptions_ = {}
    for (cnstrname, servernames) in exceptions.items():
      if servernames == None:
        self.exceptions_[cnstrname] = None
        continue
      servernames = string.split(servernames)
      serverdict = {}
      for name in servernames: serverdict[name] = 1
      self.exceptions_[cnstrname] = serverdict

    # Read in sharing constraints.
    for (uses, machtypenames) in sharing_constraints.items():
      self.Constraint('sharing').AddConstraint(uses, machtypenames)

    # Read in servertype constraints.
    for (srvset, cnstr_descs) in general_constraints.items():
      for cnstr_type, cnstr_desc in cnstr_descs.items():
        # Add constraints for any auto assigned sets as well.
        for set in [srvset] + auto_assign_sets.get(srvset, []):
          self.Constraint(cnstr_type).AddConstraint(set, cnstr_desc)

    # Add in sharing constraints for auto assigned sets.
    for (master_set, slave_sets) in auto_assign_sets.items():
      shared_sets = string.join([master_set] + slave_sets, ',')
      self.Constraint('sharing').AddConstraint(shared_sets, [])

  # Test if any constraints were defined.
  def HasConstraints(self):
    for cnstr in self.constraint_list_:
      if cnstr.HasConstraints(): return 1
    return 0

  # Get a constraint object given the name.
  def Constraint(self, cnstr_type):
    try:
      return self.constraints_[cnstr_type]
    except KeyError:
      raise RuntimeError('Unknown constraint type: %s' % cnstr_type)

  # Only for ResourceConstraint
  def GetLoad(self, srv_mgr, host, force=1):
    for cnstr in self.constraint_list_:
      if cnstr.name() == 'resource':
        return cnstr.GetLoad(srv_mgr, host, force=force)
    raise RuntimeError('no resource constraint for host %s' % host)

  # Try to gauge the benefit from removing a particular
  # server from a host. Basically that host becomes less loaded
  # and the benefit is some extra breathing space
  # for the other servers on this machine
  def BenefitFromRemove(self, srv_mgr, server):
    ret = []
    for cnstr in self.constraint_list_:
      result = cnstr.BenefitFromRemove(srv_mgr, server)
      if not result.error():
        ret.append(result)
    return ret


  # Verify a server against the constraints.  This should return
  # at least one value whether the server passes or fails.
  # If break_early = 1, stop after any violation.
  # If ver_only = 1, run for verification.
  # If errors_only = 1, just return error results.
  def VerifyServer(self, srv_mgr, server, servers=None, force=0,
                   break_early=1, ver_only=0, errors_only=0,
                   constraint_types=None):
    ret = []
    for cnstr in self.constraint_list_:

      # Test if any constraints defined.
      if not cnstr.HasConstraints(): continue

      # Test if this is a desired constaint.
      if constraint_types and not cnstr.name() in constraint_types: continue

      # Test if requested non-verification only and only for verification.
      if not ver_only and cnstr.VerifyOnly(): continue

      result = cnstr.VerifyServer(srv_mgr, server, servers=servers,
                                  force=force)
      if result.error() or not errors_only:
        ret.append(result)
      if break_early and result.error():
        break
    return ret

  # Verify a set of servers against the constraints.
  # If ver_only = 1, run for verification.
  # If errors_only = 1, just return error results.
  def VerifyServers(self, srv_mgr, force=0, ver_only=0, errors_only=1,
                    constraint_types=None):

    ret = []
    for cnstr in self.constraint_list_:

      # Test if any constraints defined.
      if not cnstr.HasConstraints(): continue

      # Test if this is a desired constaint.
      if constraint_types and not cnstr.name() in constraint_types: continue

      # Test if requested non-verification only and only for verification.
      if not ver_only and cnstr.VerifyOnly(): continue

      # Test if this constraint type is completely excepted.
      if self.exceptions_.has_key(cnstr.name()) and \
         self.exceptions_[cnstr.name()] == None: continue

      # Find issues.
      results = cnstr.VerifyServers(srv_mgr, force=force)

      # Test return results.
      for result in results:
        if errors_only and not result.error(): continue
        if not cnstr.VerifyOnly():
          servers = self.PruneExcepted(cnstr.name(), result.servers())
          if servers == []: continue
          result.set_servers(servers)
        ret.append(result)

    return ret

  # Prune out servers that should be excepted from a results
  # servers list.
  def PruneExcepted(self, cnstrname, servers):

    ret = []

    cnstr_except = self.exceptions_.get(cnstrname, {})
    dflt_except = self.exceptions_.get('default', {})

    for server in servers:
      if cnstr_except.has_key(str(server)): continue
      if dflt_except.has_key(str(server)): continue

      host = server
      if type(server) != types.StringType: host = server.host()

      if cnstr_except.has_key(host): continue
      if dflt_except.has_key(host): continue
      ret.append(server)

    return ret

#------------------------------------------------------------------------------
# Machine Types
#------------------------------------------------------------------------------

#
# Machine types group classes of machines together.
#
#   'cpucnt:1-2,cpumhz:800+,ram:500+,hdcnt:3-4,hdsize:40+'
#
# This representation is stored in a MachineType object which
# will allow you to verify whether a machine object meets
# the stored criteria.  The MachineTypeManager manages a set
# of different machine types.
#

#
# Machine Type
#
class MachineType:

  VALID_FIELDS = ['crawlnet', 'cpucnt', 'cpumhz', 'hdcnt', 'hdsize',
                  'ram', 'swap']

  # Create a machine type with constraints 'cnstrs'.
  #
  # The constraints are a string of the following format:
  #
  #   'field:min[+|-max], ....
  #
  # For example:
  #
  #   'cpucnt:1-2 cpumhz:800+ ram:500+ hdcnt:3-4 hdsize:40+'
  #
  def __init__(self, cnstrs):

    # Dictionary of constraints keyed by field name with min/max vals.
    self.str_ = cnstrs
    self.cnstrs_ = {}

    # If crawlnet is not specified, then default it to noncrawl machines.
    self.cnstrs_['crawlnet'] = [0, 0]

    # Split the constraints by ' ,' characters.
    cnstrs = string.split(cnstrs, ',')
    for cnstr in cnstrs:
      if cnstr == '': continue
      try:
        cnstr = string.strip(cnstr)
        (field, range) = string.split(cnstr, ':')
        field = string.strip(field)
        range = string.strip(range)
        if field not in MachineType.VALID_FIELDS:
          raise KeyError, 'Invalid field name: %s' % field
        if string.find(range, '-') != -1:
          (minval, maxval) = string.split(range, '-')
          minval = int(minval)
          maxval = int(maxval)
        elif range[-1] == '+':
          minval = int(range[:-1])
          maxval = None
        else:
          minval = int(range)
          maxval = minval
        self.cnstrs_[field] = [minval, maxval]
      except (KeyError, ValueError, TypeError, AttributeError), e:
        raise Error, 'Cannot parse machine type: %s - %s' % (cnstr, e)

  # Verify that a particular machine field value satisfies
  # the constraint.
  def VerifyConstraint(self, mach, field, min, max):
    if field == 'crawlnet':
      val = mach.crawlnet()
    else:
      val = mach.hardware().__dict__[field + '_']
    desc = '%s: %s <= %s (%s) <= %s' % \
      (self.str_, min, field, val, max)
    if min != None and val < min:
      return (0, desc)
    if max != None and val > max:
      return (0, desc)
    return (1, desc)

  # Verify that a given machine satisfies all the constraints for this
  # machine type.
  def Verify(self, mach):
    if not mach or not mach.hardware():
      name = 'unknown'
      if mach: name = mach.name()
      return (0, 'no hardware information for %s' % name)
    for (field, values) in self.cnstrs_.items():
      (status, desc) = self.VerifyConstraint(mach, field, values[0], values[1])
      if not status:
        return (status, desc)
    return (1, '')


#
# Machine Type Manager
#
class MachineTypeManager:

  def __init__(self, mach_mgr):
    # Machine manager.
    self.mach_mgr_ = mach_mgr
    # Cache of machine types.
    self.machtype_cache_ = cachelib.Cache()
    # Cache of machine / machine type compatibility.
    self.status_cache_ = cachelib.Cache()

  # Given a list of possible machine types, return the first
  # type that the machine machname satisfies.  If none are
  # compatible, return None.  Also returns a reason for the
  # match or non-match.
  def FindMachineType(self, mach, possible_types):

    if not mach: return None

    failed_descs = []

    for machtypestr in possible_types:

      # See if the result is cached.
      if self.status_cache_.has_key((mach.name(), machtypestr)):
        (status, desc) = self.status_cache_.get((mach.name(), machtypestr))
      else:
        # Lookup machine type.
        machtype = self.machtype_cache_.get(machtypestr)
        if not machtype:
          machtype = MachineType(machtypestr)
          self.machtype_cache_[machtypestr] = machtype

        (status, desc) = machtype.Verify(mach)
        self.status_cache_[(mach.name(), machtypestr)] = (status, desc)

      if status == 1:
        return (machtypestr, desc)
      else:
        failed_descs.append(desc)

    return (None, '%s' % string.join(failed_descs, ','))


# DO NOT CHANGE THE ORDER OF THIS LIST
# The list  [ MHz       GB        fraction  MB  ]
RESLIST =   ['cpumhz', 'hdsize', 'hdutil', 'ram']
MIN_USAGE = [ 0.001,    0.001,    0.001,    0.001] # To avoid division by zero
#
# Resource
#
class Resource:
  # Creates a resource with requirements 'reqmnts'.
  # The constraints are a string of the following format:
  #
  #    'resource:reqmnt, ....'
  #
  # For example:
  #         'cpumhz:800, hdutil:1.3'
  #
  # NOTE: hdutil can be more than 1.0. The idea is that a 6 disk machine will
  # be considered loaded when the total estimated hdutil reaches 6.0

  def __init__(self, reqmnts):

    self.str_ = reqmnts
    # Dictionary of resource usage keyed by resource
    self.resrc_map_ = {}
    for i in range(len(RESLIST)):
      self.resrc_map_[RESLIST[i]] = MIN_USAGE[i]

    reqmnts = string.strip(reqmnts)
    if reqmnts == "": return

    # Split the usage by ',' characters.
    reqmnts = string.split(reqmnts, ',')
    for reqmnt in reqmnts:
      reqmnt = string.strip(reqmnt)
      (field, value) = string.split(reqmnt, ':')
      field = string.strip(field)
      value = string.strip(value)
      if field in RESLIST:
        self.resrc_map_[field] = float(value)

  def Add(self, resrc):
    for resrctype in RESLIST:
      self.resrc_map_[resrctype] = self.resrc_map_[resrctype] + \
                                   resrc.resrc_map_[resrctype]

  def Set(self, cpumhz, hdsize, hdutil, ram):
    self.resrc_map_['cpumhz'] = cpumhz
    self.resrc_map_['hdsize'] = hdsize
    self.resrc_map_['hdutil'] = hdutil
    self.resrc_map_['ram'] = ram

  # Helper to fill in values that are none.
  def FillDefaults(self, default):

    def get(a, b):
      if a: return a
      else: return b

    for res in RESLIST:
      self.resrc_map_[res] = get(self.resrc_map_[res], default.resrc_map_[res])

  # Returns the maximum of all the ratios. Maximum is what we are interested
  # in from allocation point of view. If a machine has all it's CPUs exhausted,
  # it doesn't matter if RAM is still available or not.
  def Div(self, resrc):
    ratios = []

    for res in RESLIST:
      ratios.append(self.resrc_map_[res]/resrc.resrc_map_[res])

    return max(ratios)


#
# ResourceManager
#
class ResourceManager:

  def __init__(self, mach_mgr):
    # Machine manager.
    self.mach_mgr_ = mach_mgr
    # Cache of resouce types.
    self.resource_cache_ = cachelib.Cache()

  # Figures out if the given machine (mach), which has already been used
  # (used_resrcs), can satisfy the given resource requirement
  # (reqr_resrc)
  def ComputeLoad(self, mach, used_resrcs, reqr_resrc, force):
    # Get the current estimated usage
    estimated_usage = Resource("")
    for used_resrc_str in used_resrcs:
      # Lookup resource usage
      used_resrc = self.resource_cache_.get(used_resrc_str)
      if used_resrc == None:
        used_resrc = Resource(used_resrc_str)
        self.resource_cache_[used_resrc_str] = used_resrc
      # Add usage
      estimated_usage.Add(used_resrc)

    # Get the actual usage
    actual_usage = Resource("")
    hdw = mach.hardware()
    actual_usage.Set(hdw.cpuused(),  hdw.hdused(), hdw.hdutil(), hdw.ramused())

    # We assume our estimated_usage is correct if we don't have any
    # observed values. For MachineManagerDB, this would make sure that our
    # actual usage is the same as the estimated usage.
    actual_usage.FillDefaults(estimated_usage)

    # Get the factor by which our estimate is wrong
    error_factor = actual_usage.Div(estimated_usage)

    # We do not trust wild error estimates
    if error_factor > 2.0 or error_factor < 0.5:
      error_factor = 1.0

    # Add the load that will be generated, if we add the new server
    estimated_usage.Add(Resource(reqr_resrc))

    # Get the total resources available
    total_available = Resource("")
    hdw = mach.hardware()
    total_available.Set(hdw.cpumhz() * hdw.cpucnt(), hdw.hdsize(), hdw.hdcnt(),
                        hdw.ram())

    # Now estimate the load
    load = estimated_usage.Div(total_available)

    # Correct by the error factor
    load = load * error_factor

    # If we are not forcing, we don't want to return machines with high load
    if load > 1.1 and not force:
      return 0.0
    else:
      # Return the value in the expected range
      return math.pow(math.e, -1.0 * load)


#------------------------------------------------------------------------------
# Utility Methods
#------------------------------------------------------------------------------

# Calculate a weight based on the position of the elment in
# the list.  The first element gets a weight of 1.0, last
# gets a weight of 1/len.
def calc_listpos_weight(list, element):
  return 1.0 - (float(list.index(element)) / float(len(list)))

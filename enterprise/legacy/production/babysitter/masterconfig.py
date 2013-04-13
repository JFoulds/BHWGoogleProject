#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# The masterconfig object encapsulates the data stored in the services.??
# files - service names and babysat config files.
#
# There is a services config file for every datacenter (usually called
# services.<dc> ). It should contain 1) a dictionary (SERVICES) that maps
# service names (eg 'www', 'image', 'usenet') to corresponding config file
# names, 2) a list of service names (BABYSIT) that are to be babysat and
# 3) a list of additional service names (MONITOR) that are to be monitored.
# All services in BABYSIT and MONITOR will be monitored by the concentrator
# and GEMS.
#
# The services files are used for two purposes. First, to allow scripts
# and configs to reference the current configuration file for a given service.
# For example, this is useful when we want to "include" a config file
# in another config file but we don't want to hard code the included config
# file name into the including config file.  For example,
# config.site.www includes servers from the current
# 'www' service where 'www' may be a service alias for 'config.www.apr02.ex'.
# When we switch the config to 'config.www.may02.ex', we only have to
# update the services.ex file rather than all the including configs.
#
# Second, the services file specifies the list of configuration files
# that are to be babysat.  The following is an example of a services file:
#
# SERVICES = {
#       'service1': 'config.service1.ex',
#       'service2': 'config.service2.ex',
#       'service_group': ['service1', 'service2'],
#     }
#
#     BABYSIT = [
#       'service_group'
#     ]
#

import os
import sys
import types
import string
import traceback

# Hack to enable circular imports
import google3.enterprise.legacy.production.babysitter
google3.enterprise.legacy.production.babysitter.masterconfig = \
    sys.modules[__name__]

from google3.enterprise.legacy.production.babysitter import configutil
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.production.babysitter import segment_data


# ignore inconsistent return types. ConfigFactory does this by definition.
__pychecker__ = 'no-returnvalues'


# Cache for holding config file data.  The key is (config_dir, filename)
# for each config file.  Each entry is a tuple of (googleconfig.Config,
# [mtime1, mtime2, ...] where each mtime corresponds to the modification
# time of the respective file in the list of files returned
# from GetLoadedFiles() of the config object.  The cache
# is refreshed for a configfile if any of the mtimes is out of date
# or the data is not present for a configfile.
_CONFIG_CACHE = {}

def GetCache(key):
  """
  Get an item from the cache.  We return None if there was
  no hit or the stored modtimes differ from the current modtimes
  of the files in the fnames list.
  """
  global _CONFIG_CACHE

  # Return None if not in cache.
  if not _CONFIG_CACHE.has_key(key):
    return None

  # Return None if file times have changed.
  (data, fnames, mtimes) = _CONFIG_CACHE[key]
  cur_mtimes = map(os.path.getmtime, fnames)
  if mtimes != cur_mtimes:
    return None

  # Return data hit.
  return data

def AddCache(key, data, fnames):
  """
  Add an item to the cache.  The data is associated with
  a key and the mod times of the given files.
  """
  global _CONFIG_CACHE
  _CONFIG_CACHE[key] = (data, fnames, map(os.path.getmtime, fnames))


# Initialize the master factory object for the specified coloc based
# on data from the corresponding "services" config file.
def Init(coloc, config_dir = None, services_file = None):
  scope = {}
  if not services_file:
    config_file = "services.%s" % coloc
  else:
    config_file = services_file
  scope = configutil.ExecFile(config_file, config_dir = config_dir)

  # instantiate a factory object for specified coloc
  global _CONFIG_FACTORY
  _CONFIG_FACTORY[(coloc, config_dir)] = ConfigFactory(coloc,
                                                      scope['BABYSIT'],
                                                      scope['SERVICES'],
                                                      scope.get('MONITOR', []),
                                                      config_dir = config_dir)

# Forces a reload of all factory objects.  This is done
# by clearing the _CONFIG_FACTORY cache.  Forcing a reload
# is useful if the services files change.
def Reload():
  global _CONFIG_FACTORY
  _CONFIG_FACTORY = {}

# Return a factory object for the given coloc.  Factories
# are cached after initial load.  To force a reload on the
# next call to this, call Reload.
_CONFIG_FACTORY = {}
def Factory(coloc, config_dir = None, services_file = None):
  global _CONFIG_FACTORY
  if not _CONFIG_FACTORY.has_key((coloc, config_dir)):
    Init(coloc, config_dir = config_dir, services_file = services_file)

  return _CONFIG_FACTORY[(coloc, config_dir)]

# Get list of active colocs.  If service is specified,
# limit the list to those colocs that have the service defined.
def GetColocs(service = None, config_dir = None):
  colocs = map(lambda x: x[-2:], configutil.ListFiles('services.??',
                                                      config_dir = config_dir))
  if service:
    colocs = filter(lambda c,s=service:
                    s in Factory(c).GetServices(expand = 0), colocs)
  return colocs

# Get a list of all servers in active colocs for a given service, server type
# and optionally port number. If the port is not given, all ports will be
# retrieved.
#
# Returns a list of serverlib.Server objects, which are sorted so that it won't
# return servers in random order even when the list remains the same.
#
# If colo is specified, then the servers are limited to the specified
# colos.
def GetServers(service_name, server_type, port = -1, colos=None):
  all_servers = []
  if not colos:
    colos = GetColocs(service_name)
  for colo in colos:
    configs = Factory(colo).GetConfigs(service_name)
    for dc_config in configs:
      server_set = dc_config.GetServerManager().Set(server_type)
      if server_set:
        if port == -1:
          servers = server_set.Servers()
        else:
          servers = server_set.ServersForPort(port)
        all_servers = all_servers + servers

  all_servers.sort()
  return all_servers

# The master factory holds various info about the configuration files
# and all necessary accessors to get to this data.
#
# We define methods to get all configs for a given colocation, and to
# get a single config by coloc/name.
class ConfigFactory:
  def __init__(self, coloc,
               babysit,        # <=> BABYSIT variable
               services,       # <=> SERVICES variable
               monitor,        # <=> MONITOR variable
               config_dir = None):
    self.coloc = coloc
    self.babysit = babysit
    self.services = services
    self.monitor = monitor
    self.config_dir = config_dir

    # Convert segment data information into config file information.
    #
    # An entry of the format <service>:<data.*> will be mapped to
    # the following:
    #
    # Lettered service names for each individual set of server configs.
    #
    #   <service>_a: servers...
    #   <service>_b: servers...
    #   <service>_c: servers...
    #   ...
    #
    # Mapping from segmented service names.
    #
    #   <service>_0: [<service>_a]
    #   <service>_1: [<service>_a]
    #   <service>_2: [<service>_a]
    #   ...
    #
    # Idle set.
    #
    #   <service>_idle: servers...
    #
    # Group of all active segements.
    #
    #   <service>: [<service>_0, <service>_1, ... ]
    #
    for (service, child) in self.services.items():
      if type(child) != types.StringType: continue
      if string.find(child, 'data.') == 0:
        try:
          key = (config_dir, child)
          segdata = GetCache(key)
          if not segdata:
            segcfg = googleconfig.Load(child, config_dir=self.config_dir)
            segdata = segment_data.SegmentData(segcfg)
            AddCache(key, segdata, segcfg.GetLoadedFiles())
          active_names = []
          for i in segdata.segs():
            id = segdata.id(i)
            seg_service = service + '_%s' % id
            if i == -1:
              seg_alias = service + '_idle'
            else:
              seg_alias = service + '_%s' % i
            config_file = segdata.config_file(id)
            self.services[seg_service] = config_file
            self.services[seg_alias] = [seg_service]
            if i != -1: active_names.append(seg_alias)
          self.services[service] = active_names
        except (ValueError, segment_data.Error), e:
          raise RuntimeError('Error loading segment data file: %s - %s' %
                             (child, e))

    # Create a mapping from service to its immediate parent.
    self.parents = {}
    for (service, children) in services.items():
      # Handle the leaf config level.
      if type(children) == types.StringType:
        children = [children]
      for child in children:
        if self.parents.has_key(child):
          raise RuntimeError('Child %s has multiple parents: %s %s' %
                             (child, service, self.parents[child]))
        self.parents[child] = service

  # Get list of services.
  # If the service arg is not specified, all services in the
  # SERVICES map are returned.  The service arg may be
  # a list of services to expand or a single service name.
  # If expand is set to 0, the services are returned with groups
  # not expanded into their leaf components.  If expand is set to 1
  # the method returns only leaf services.
  def GetServices(self, service = None, expand = 1):
    if not service: service = self.services.keys()
    elif type(service) == types.StringType: service = [service]
    return self.get_services(service, expand)

  # Get config filenames from a servicename.
  # If the service arg is not specified, config files for all services in the
  # SERVICES map are returned.  The service arg may be
  # a list of services or a single service name.
  #
  # The expand_active option is useful for determining the underlying
  # file containing SERVERS when used with active glue files.  For
  # example:
  #
  #   GetConfigFiles('usenet_daily', expand_active = 0) returns
  #     'config.usenet.lvl1.ex'.
  #   GetConfigFiles('usenet_daily', expand_active = 1) may return
  #     'config.usenet.lvl1.a.ex'.
  #
  # The expand active option is only useful for assignment
  # of servers.
  #
  def GetConfigFiles(self, service = None, expand_active = 0):
    services = self.GetServices(service)
    configfiles = {}
    for service in services:
      try:
        configfile = self.services[service]

        # TODO: This expand active crud can go away after we switch
        # everyone to use the shared data files.
        if expand_active:
          config = self.GetConfigs(service)[0]
          if config.GetCurrentConfigFile():
            configfile = config.GetCurrentConfigFile()
        configfiles[configfile] = 1
      except KeyError:
        raise KeyError('Unknown service: %s' % service)
    configfiles = configfiles.keys()
    configfiles.sort()
    return configfiles

  # Get configs from a servicename.
  # If the service arg is not specified, configs for all services in the
  # SERVICES map are returned.  The service arg may be
  # a list of services or a single service name.
  def GetConfigs(self, service = None):
    # Don't expand active when getting config file names here.
    filenames = self.GetConfigFiles(service, expand_active = 0)
    configs = []
    for file in filenames:
      cache_key = (self.config_dir, file)
      config = GetCache(cache_key)
      if not config:
        config = googleconfig.Load(file, config_dir = self.config_dir)
        AddCache(cache_key, config, config.GetLoadedFiles())
      configs.append(config)
    return configs

  # Return the service name of a config file.
  # If no service, returns None.
  def GetServiceName(self, configfilename):
    if self.services.has_key(configfilename):
      raise RuntimeError('%s is not a configfile name' % configfilename)
    return self.parents.get(configfilename)

  # Return the top level group name of a config file.
  # If no group, returns None.
  def GetGroupName(self, configfilename):
    if self.services.has_key(configfilename):
      raise RuntimeError('%s is not a configfile name' % configfilename)
    group = self.parents.get(configfilename)
    while group and self.parents.has_key(group):
      group = self.parents.get(group)
    return group

  # Return all the service groupings that this configfile/service is
  # a member of.
  def GetServiceGroups(self, name):
    groups = []
    while self.parents.has_key(name):
      name = self.parents[name]
      groups.append(name)
    return groups

  # Returns list of babysat services.
  # If expand is set to 1, any service groups are expanded to
  # their leaf services.
  def GetBabysatServices(self, expand = 1):
    return self.GetServices(self.babysit, expand = expand)

  # Gets list of monitored services
  # This is the same as GetServices() except it gets all files that
  # are listed in SERVICES and MONITOR.
  def GetMonitoredServices(self, expand = 1):
    return self.GetServices(self.babysit + self.monitor,
                            expand = expand)

  # Get servers dependent on a modified server.  Given the
  # service name, server set name and port of the modified server,
  # returns a list of tuples (coloc, service, setname, port) showing the
  # dependent servers.  The port value may be None indicating
  # all servers in the set should be restarted.
  #
  # For example:
  #
  #   GetDependentServers('www_base', 'index', 4000)
  #   returns the index balancers on port 4000.
  #
  #   GetDependentServers('www_base', '+index', 4000)
  #   returns the mixers.
  #
  # CAVEAT: This does not detect cross-coloc dependencies.
  # That would be very simple to do - just iterate over all
  # known colocs.  However, this would slow this call down a lot.
  # We can decide to do it that way if we want to.
  def GetDependentServers(self, mod_service, mod_srvset, mod_port):

    # List of dependent servers.
    dep_servers = []

    # Find full set specification from arguments.
    config = self.GetConfigs(mod_service)[0]
    srv_mngr = config.GetServerManager()
    mod_set = srv_mngr.Set(mod_srvset)

    if not mod_set:
      raise KeyError('Unable to locate set for: %s:%s:%s' % \
                     (mod_service, mod_srvset, mod_port))

    mod_shard = mod_set.Shard(mod_port)

    # If this is a balancer set, remove the preceding '+' from
    # the setname since dependencies in the 'backends' property
    # do not specify dependencies on balancers, but the balanced type.
    if mod_set.isbaltype():
      mod_srvset = mod_set.balsrvset()

    # Create full server set name of the modified set.
    mod_spec = '%s:%s:%s' % (self.coloc, mod_service, mod_srvset)

    # Look for sets that depend on this dep_spec.
    services = self.GetBabysatServices()
    found_bals = 0
    for service in services:
      config = self.GetConfigs(service)[0]
      srv_mngr = config.GetServerManager()
      for set in srv_mngr.Sets():
        for backend_info in set.property('backends', []):
          # Build a full set specification string.
          spec = backend_info.get('set')
          fields = string.split(spec, ':')
          if len(fields) == 1:
            spec = '%s:%s:%s' % (self.coloc, service, spec)
          elif len(fields) == 2:
            spec = '%s:%s' % (self.coloc, spec)
          elif len(fields) != 3:
            raise RuntimeError('Invalid set spec: %s' % spec)

          # If not a match continue.
          if spec != mod_spec: continue

          # If the modified set was a balancer set and
          # the current set is a balancer set, then ignore this set.
          if mod_set.isbaltype() and set.isbaltype(): continue

          # We found a match.
          servers = None
          if backend_info.get('per_shard') == 1:
            # Dependency is per shard so only append servers from
            # corresponding shard.
            port = set.PortBase() + mod_shard
            if set.ServersForPort(port):
              servers = (self.coloc, service, set.name(),
                         set.PortBase() + mod_shard)
          else:
            # Dependency is for all servers.
            if set.Servers():
              servers = (self.coloc, service, set.name(), None)

          if servers:
            dep_servers.append(servers)
            if set.isbaltype(): found_bals = 1

    # For non-balancers, if any of the dependent sets was a balancer type
    # remove all the non-balancers since these are actually
    # dependent on the balancers and not the underlying servers.
    if not mod_set.isbaltype() and found_bals:
      servers = dep_servers
      dep_servers = []
      for (coloc, service, setname, port) in servers:
        if setname[0] == '+':
          dep_servers.append((coloc, service, setname, port))

    return dep_servers

  # Helper function for traversing a hierarchy of services
  # and potentially expanding service groups into leaf services.
  def get_services(self, service_names, expand, seen_services = []):
    ret_services = {}
    for service in service_names:
      if service in seen_services:
        continue
      value = self.services.get(service)
      if value == None:
        ret_services[service] = 1
      elif expand and type(value) != types.StringType:
        seen_services = seen_services + [service]
        child_services = self.get_services(value, expand, seen_services)
        for child_service in child_services:
          ret_services[child_service] = 1
      else:
        ret_services[service] = 1

    ret_services = ret_services.keys()
    ret_services.sort()
    return ret_services

# Print usage information.
def Usage():
  print "Usage: %s [--coloc=<coloc> --service=<service>] <cmd>" % sys.argv[0]
  print " cmds:"
  print "  colocs - returns list of active colocs - if service"
  print "    is specified, returns only colocs that have the specified service"
  print "  babysatfiles - returns the babysat config files for coloc"
  print "    or for all colocs if none specified."
  print "  configfile - translates service name to config file name for coloc"
  print "    or for all colocs if none specified."

if __name__ == '__main__':
  try:
    if sys.argv[1:]:
      import getopt
      (optlist, args) = getopt.getopt(sys.argv[1:], '',
                                      ['colocs=', 'service='])

      colocs = GetColocs()
      service = None

      for flag,value in optlist:
        if flag == '--colocs':
          colocs = [value]
        elif flag == '--service':
          service = value

      cmd = args[0]

      # run command
      if cmd == 'colocs':
        if service:
          colocs = GetColocs(service)
        print string.join(colocs)
      elif cmd == 'babysatfiles':
        babysatfiles = []
        for coloc in colocs:
          factory = Factory(coloc)
          services = factory.GetBabysatServices()
          babysatfiles.extend(factory.GetConfigFiles(services))
        print string.join(babysatfiles)
      elif cmd == 'configfile':
        configfiles = []
        for coloc in colocs:
          # Do not expand services so that we can list configs
          # for groups (i.e. 'www') as well as leaves (i.e. 'www_base')
          if service in Factory(coloc).GetServices(expand = 0):
            configfiles.extend(Factory(coloc).GetConfigFiles(service))
        print string.join(configfiles)
      else:
        Usage()
      sys.exit(0)
    else:
      Usage()
  except SystemExit, e:
    sys.exit(e)
  except:
    traceback.print_exc()            # so we know what went wrong
    sys.exit(2)

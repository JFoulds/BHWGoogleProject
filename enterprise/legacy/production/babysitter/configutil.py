#!/usr/bin/python2.4
#
# configutil.py - utility function for messing with config files
#
# TODO: This file is probably going to be obsolete and almost all
# of these functions are going to be moved into googleconfig where
# they belong.  The rationale for this is that there should be just
# one module for dealing with config files and server maps.  Right
# now there is not much logical consistency between the separation
# and people have to import both to do most things.  The main driving
# theme between what is here is that 1) Config object is in googleconfig.
# 2) Module level functions are here.  We've mostly kept to this
# theme but they should merge.
#
# TODO: Most of the "writing config file" functionality in this module
# will be supplanted most likely by the googleconfig.Save method in
# a later checkin.
#

import sys
import commands
import os
import socket
import string
import types
import copy
import glob
import sys

# Hack to enable circular imports
import google3.enterprise.legacy.production.babysitter
google3.enterprise.legacy.production.babysitter.configutil = \
    sys.modules[__name__]

from google3.enterprise.legacy.production.common import setlib
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import segment_data
# Note that config_namespace is a circular import
from google3.enterprise.legacy.production.babysitter import config_namespace

#
# We preload  a small number of variables with commonly used values
# that people often use code in config files for. All keys should be
# prefixed by "PRELOADED_"; values should be information to be extracted
# from environment (os, environ etc).
#
def GetPreloadedScope():
  scope = {
      'PRELOADED_CWD' : os.getcwd() + '/'
    }
  return scope

#
# We restrict server.* files only to a set of limited variables
# since these files do not go through human integration.
#
def AllowedServerConfigVars():
  return [
    'INCLUDES', 'SERVERS', 'COLOC', 'PROJECT', 'OWNER',
    'SYNCDB_RESERVED_HOSTS', 'SEGMENT_SET', 'NOBABYSIT_HOSTS', 'REPLACEMENTS',
  ]

#
# FilterServerMap - given a server map of { port : "hosts", ... } where
# hosts are a list of hosts, filter to only the wanted types.
#
# servers: { port : "hosts", ... } dictionary.
# wanted_types: array from servertype.CollectTypes. {} indicates all.
#
# Returns a filtered server map of { port : "hosts", ... }.
# Returns the original map if wanted_types is empty.
# If it filters, it will return a map with the original host lists
# (does not copy the host lists).
#
def FilterServerMap(servers, wanted_types = {}):
  if not wanted_types:
    return servers
  ret = {}
  for (port, hosts) in servers.items():
    typelvl = servertype.GetTypeLevel(port)
    if not servertype.WantedType(typelvl, wanted_types): continue
    ret[port] = hosts
  return ret

#
# MergeServerList - given a list of server dictionaries return a dictionary that
# merges all their contents.  If overlapping ports exist, merge
# the servers on those ports.  Return new dictionary.
#
def MergeServerList(server_map_list):
  res = {}
  for servers in server_map_list:
    for port in servers.keys():
      existing = res.get(port, [])
      res[port] = existing + servers[port][:]
  return res

#
# MergeServers - given two server dictionaries return a dictionary that
# merges all their contents.  If overlapping ports exist, merge
# the servers on those ports.  Return new dictionary.
#
def MergeServers(srv_a, srv_b):
  return MergeServerList([srv_a, srv_b])

#
# Compute number of shards of each typelvl for servertype.
#
def GetNumShards(servers):
  ports = servers.keys()
  ports.sort()
  ports.reverse()               # now sorted in descending order
  lastport = maxport = -1
  maxports = {}
  for p in ports:
    if p >= 40000 or p != lastport-1:    # sitesearch, or not consecutive
      maxport = p            # so we start a new series -- we're the maxport
    maxports[p] = maxport
    lastport = p
  res = {}
  for p in servers.keys():
    tl = servertype.GetTypeLevel(p)
    mtype = servertype.GetPortType(p)
    base_port = servertype.GetPortBase(tl)
    if not res.has_key(tl):
      res[tl] = (maxports[p] + 1) - base_port
    else:
      res[tl] = max(res[tl],(maxports[p] + 1 - base_port))
    # never sharded despite what portrange may imply.
    if not servertype.IsSharded(mtype):
      res[tl] = 1
  return res

#
# GetHostPorts - get a tuple of (host, port) pairs for a given type
# from a server map.
#
def GetHostPorts(servers, port_or_typelvl):

  # We build an array of results to preserve order which is important
  # for host lists.  If we just used unique_hosts.keys() ordering is
  # not guaranteed.
  unique_hosts = {}
  result = []

  if type(port_or_typelvl) == types.IntType:
    port = port_or_typelvl
    if servers.has_key(port):
      for host in servers[port]:
        if not unique_hosts.has_key((host, port)):
          result.append((host, port))
          unique_hosts[(host, port)] = 1

  else:

    ports = servers.keys()
    ports.sort()
    typelvl = servertype.NormalizeTypeLevel(port_or_typelvl)

    # Keep the machines on the requested port.
    for port in ports:
      if not servertype.IsType(port, typelvl): # Not wanted port?
        continue                           # Drop them
      for host in servers[port]:
        if not unique_hosts.has_key((host, port)):
          result.append((host, port))
          unique_hosts[(host, port)] = 1

  return result

#
# AddHost - add a server to a servermap.  Raises a runtime
# error if a duplicate server is added.
#
def AddHost(servers, port, machine):
  # init if needed
  servers[port] = servers.get(port, [])
  # test for duplicates
  if not machine in servers[port]:
    servers[port].append(machine)
  else:
    raise RuntimeError("%s is specified at port %s multiple times." % \
                       (machine, port))

#
# MergeScopes - merge scope a into scope b.  If duplicates_ok is
# false, and a variable is declared in both scopes a runtime error
# is raised.  Else, scope b's value is preserved.  Dictionaries
# are loaded recursively meaning that if scope a and scope b both
# declare the same dictionary, the resulting dictionary contains
# the data from both scopes merged together.  For example if
# scope a has foo = { 'x' : 0 } and scope be has foo = { 'y' : 0 }
# the returned scope ahs foo = { 'x' : 0, 'y' : 0 }.  Conflicting
# keys are handle according to duplicates_ok. Return the merged scope.
#
def MergeScopes(scope_a, scope_b, duplicates_ok = 0):
  ret = {}
  if scope_a:
    ret.update(scope_a)
  preloaded_keys = GetPreloadedScope().keys()
  for key, value in scope_b.items():
    if type(value) == types.DictionaryType:
      if not ret.has_key(key): ret[key] = {}
      ret[key] = MergeScopes(ret[key], value, duplicates_ok)
    else:
      if not key in preloaded_keys and not duplicates_ok \
         and ret.has_key(key) \
         and ret[key] != value:
        raise RuntimeError("Unable to merge scopes, %s is in both" % key)
      ret[key] = value
  return ret

#
# SplitServersByLevel - insert the machines into the servers dict for the
# level the machine is in.
#
# Always stores the machines as one string, converting from a list if needed.
#
# The main data structure is the server_level_dict:
#   server_level_dict[level][port]->machines string
#
def SplitServersByLevel(server_level_dict, testserver_scope):
  for (port, hosts) in testserver_scope['SERVERS'].items():

    try:
      lvl = servertype.GetLevel(port)
    except:
      lvl = 0  # If we don't know better, assume it is level 0

    if not server_level_dict.has_key(lvl):
      server_level_dict[lvl] = {}

    if type(hosts) == type([]):
      hosts = string.join(hosts)
    server_level_dict[lvl][port] = hosts


#
# WriteConfigHeader - write out the first constant part of the config file.
#
def WriteConfigHeader(fd, comment = None):
  fd.write('# #-*-Python-*-\n\n')

  if comment:
    fd.write('# ' + comment)


#
# WriteValueToFile - write a value into an open file. Uses lineprefix
# at the front of multiline items (dict and list elements). Defaults
# to use '%s' format for unknown types. Will fail is a type passed in
# can't be converted to string (like modules).
#
def WriteValueToFile(file, value, lineprefix):
  if type(value) == type([]):
    file.write("[")
    for item in value:
      WriteValueToFile(file, item, lineprefix)
      file.write(", ")
    file.write("]")
  elif type(value) == type({}):
    file.write("{\n")
    keys = value.keys()
    keys.sort()
    for key in keys:
      file.write("%s" % lineprefix)
      WriteValueToFile(file, key, lineprefix)
      file.write(" : ")
      WriteValueToFile(file, value[key], "%s\t" % lineprefix)
      file.write(",\n")
    file.write("}\n")
  elif type(value) == type(1):
    file.write("%d" % value)
  elif type(value) == type(1L):
    file.write("%s" % repr(value))
  elif type(value) == type(""):
    file.write("%s" % repr(value))
  elif type(value) == type(1.0):
    file.write("%s" % repr(value))
  else:
    file.write("%s" % repr(value))


#
# WriteConfigVariables - write the variables into the file.
#   variables to never include are specified in skip_vars
#   if include_only is specified, only write these variables to the file
#
def WriteConfigVariables(fd, scope, skip_vars=[], include_only_vars=None):

  #
  # Sort the variables into dicts and non-dicts, then alpha within those types.
  #
  def DictFirstCmp(l1, l2):
    type1 = type(l1[1])
    type2 = type(l2[1])
    type_dict = type({})

    if type1 == type_dict and type2 != type_dict:
      return -1
    if type1 != type_dict and type2 == type_dict:
      return 1

    return cmp(l1, l2)
  #----------------------- end DictFirstCmp() function

  #
  # Grab the variables we want to keep into a dict
  #
  keep_vars = {}
  for name, value in scope.items():
    if not name in skip_vars:
      if include_only_vars == None or name in include_only_vars:
        keep_vars[name] = value

  #
  # After we've gotten all the variable values from the file, go through
  # the VARIABLES_TO_SET, set evertying in there.
  #
  # NOTE: We do this step after the previous so VARIABLES_TO_SET override
  # actual assignments in the file!
  #
  vars_to_set = scope.get('VARIABLES_TO_SET')
  if vars_to_set:
    for vars_to_set_name, vars_to_set_value in vars_to_set.items():
      if not vars_to_set_name in skip_vars:
        if include_only_vars == None or vars_to_set_name in include_only_vars:
          keep_vars[vars_to_set_name] = vars_to_set_value

  keep_vars_list = keep_vars.items()
  keep_vars_list.sort(DictFirstCmp)

  for (name,value) in keep_vars_list:
    if type(value) == type(sys):
      continue # Don't try to print modules.
    fd.write('%s = ' % name)
    WriteValueToFile(fd, value, '\t')
    fd.write('\n')


#
# WriteConfigServers - write out the SERVERS part of the file.
#
def WriteConfigServers(fd, servers_in, balancer_dict = None):
  def MaybeListToStr(list_or_str):
    if type(list_or_str) == types.ListType:
      return string.join(list_or_str)
    else:
      return list_or_str
  # end def
  def Plusser(n):
    if n[0] == '+': return n
    else: return '+' + n
  # end def

  fd.write('\nSERVERS = {\n')
  last_type = ''
  has_web = 0

  server_dict = servers_in.copy()
  if balancer_dict:
    for (port, v) in balancer_dict.items():
      names = string.join(map(Plusser, string.split(MaybeListToStr(v))))
      if server_dict.has_key(port):
        server_dict[port] = "%s %s" % (names, MaybeListToStr(server_dict[port]))
      else: server_dict[port] = names

  ports = server_dict.keys()
  ports.sort()
  for port in ports:
    #
    # Write the machines in port order, except for the webservers
    #
    server_type = servertype.GetPortType(port)
    if server_type == 'balancer': continue # don't write balancers explicitly
    if server_type == 'web':
      has_web = 1 # special case: web goes last
      continue
    if server_type != last_type:
      fd.write("\n  # " + string.upper(server_type) + " SERVERS\n")
      last_type = server_type
    fd.write('  %d: " %s",\n' % (port, MaybeListToStr(server_dict[port])))

  # Do the webserver last
  if has_web:
    fd.write("\n  # WEBSERVERS\n")
    for port in ports:
      server_type = servertype.GetPortType(port)
      if server_type == 'web':
        v = server_dict[port]
        if v:           # empty for docfetchservers, eg
          fd.write('  %d: " %s ",\n' % (port, MaybeListToStr(v)))

  fd.write('}\n\n')

#
# WriteConfigFile - write a config file with the specified servers and
# variables.
#
# Raises an IOError exception if it can't open or write to the specified file.
#
def WriteConfigFile(out_fn, servers, vars):

  # Open the file and write the header
  fd = open(out_fn, 'w')
  try:
    WriteConfigHeader(fd, comment = 'Warning: generated config\n\n')

    # Write the variables into the file, sorting them by their name.
    WriteConfigVariables(fd, vars, skip_vars=['SERVERS'])

    # Write the servers last
    WriteConfigServers(fd, servers)
  finally: fd.close()

#
# WriteConfigFileFromConfig
#
# Writes a config file from an already-loaded config.  Only works if the
# config doesn't have servers that would cause autoassignment.  Servers
# may be assigned either by a SERVERS variable, or by the standard
# servers mechanism (GetServerMap()) but not both.
#
# Note that the generated config file will contain many values that
# were defaults in config.
#
def WriteConfigFileFromConfig(out_fn, config, servermap = {}):
  servers = config.GetServerMap()
  if servermap and servers: raise Exception, "cannot reassign server configs"
  else: pass
  if config.var('GFS_ALIASES', ""):
    has_gfs = 1
  else:
    has_gfs = 0
  for name in servertype.GetAutoAssignMap().keys() + \
      servertype.GetNeedRFServerTypes(has_gfs):
    for port in xrange(servertype.GetPortMin(name),
                       servertype.GetPortMax(name)):
      if servers.has_key(port):
        raise Exception, "cannot write config with auto-assigned servers"
      else: pass
    # end for
  # end for
  fd = open(out_fn, 'w')
  try:
    WriteConfigHeader(fd, comment = 'Warning: generated config from obj\n\n')

    # Write the variables into the file, sorting them by their name.
    WriteConfigVariables(fd, config.data_, skip_vars=['SERVERS'])

    # Write the servers last
    if servers: WriteConfigServers(fd, servers, config.GetBalancerMap())
    else:       WriteConfigServers(fd, servermap)
  finally: fd.close()

#
# WriteConfigActiveFile - write a config wrapper file
#
# This interface allows one of multiple files equivelent files to be
# specified through this wrapper file. The file specifies the DATADIRS,
# and which file is active, and also does an execfile on that file.
#
def WriteConfigActiveFile(out_fn, datadirs, file_to_exec):

  fd = open(out_fn, 'w')

  WriteConfigHeader(fd)

  fd.write("CURRENT_CONFIG = '%s'\n\n" % file_to_exec)

  fd.write("DATA_DIRS = ")
  WriteValueToFile(fd, datadirs, "\t")

  fd.close()


#
# ReadConfigActiveFile - read a config wrapper file
#
# Returns the DATA_DIRS and the included file from the specified
# wrapper file.
#
def ReadConfigActiveFile(in_fn):

  # TODO: it would be nice is some ways to use Load(), but it would mean
  # we would actually pull in everything in the include chain, when all we
  # want are the DATA_DIRS and CURRENT_FILE. This function is used by
  # scripts flinging these files around where the full config context is
  # not available, so it's not clear that the full Load() is appropriate...
  #config = googleconfig.Load(in_fn)
  #return(config.var('CURRENT_FILE'), config.var('DATA_DIRS')

  scope = ExecFile(in_fn)
  if scope.has_key('CURRENT_CONFIG'):
    current_config = scope['CURRENT_CONFIG']
  else:
    include_files = scope['INCLUDES'].keys()
    assert len(include_files) == 1
    current_config = include_files[0]
  return(current_config, scope['DATA_DIRS'])

#
# CopyRemoteFile - copies a file from remote machine to local machine.
#
def CopyRemoteFile(machine, fromfile, tofile):
  thishost = string.split(socket.gethostname(), '.')[0]
  if machine == thishost:
    cmd = 'cp %s %s' % (fromfile, tofile)
  else:
    SSH_USER = 'google'
    cmd = 'alarm 60 scp %s@%s:%s %s' % (SSH_USER, machine, fromfile, tofile)
  (status, out) = commands.getstatusoutput(cmd)
  if status:
    return (status, 'Copy failed: ' + cmd + '\n' + out)
  return (0, None)


#
# FindActiveConfig - figure out which file a wrapper redirect file is
# pointing to, and return the file name and the DATADIRS for that file.
# File can be a network spec (sjbaby:/root/google/config/config.daily).
#
# Returns (rc, result):
#   where:
#     rc of 0 means success
#     rc of 1 means the file was found, but an error occurred
#     rc of -1 means an error happened, and we don't know if file exists or not
#
#     If success, result is (filename, DATADIRS)
#     If error, result is an error string
#
# Note: you can specify the file as a full path, but you must be able to
# execfile the file from the directory specified.
#
def FindActiveConfig(wrapper_file, config_dir=None):

  #
  # Copy the file to the local /tmp directory
  #
  split_wrapper_file = string.split(wrapper_file, ':')

  if len(split_wrapper_file) == 1:
    # local file
    mach = string.split(socket.gethostname(), '.')[0]
    file_path = wrapper_file
  elif len(split_wrapper_file) == 2:
    # looks like <machine>:<filepath> form
    mach = split_wrapper_file[0]
    file_path = split_wrapper_file[1]
  else:
    # bad file format
    results = 'bad file specification: %s' % wrapper_file
    return (-1, results)

  dir = os.path.dirname(file_path)
  filename = os.path.basename(file_path)

  if not dir:
    if config_dir != None:
      dir = config_dir
    else:
      dir = '/root/google/config'

  src_fn = '%s/%s' % (dir, filename)
  dst_fn = '/tmp/%s.%s' % (filename, os.getpid())

  # put the file in the tmp dir
  (rc, out) = CopyRemoteFile(mach, src_fn, dst_fn)
  if rc:
    return (-1, out)

  (current_file, data_dirs) = ReadConfigActiveFile(dst_fn)

  os.system('mv -f %s /tmp/findactive.old' % dst_fn)

  return (0, (current_file, data_dirs))

#
# NewStyleConfigs - function to tell whether the file passed in is a new
# 'config' file, or an old 'testserver' file. Based on the name of the file.
#
def NewStyleConfigs(filename):
  base_fn = os.path.basename(filename)
  if string.find(base_fn, 'config') == 0:  # Does it start with 'config'?
    return 1
  else:
    return 0

# Get config file path using location independent mechanism using
# sitecustomize to point to the root of the P4 tree.
def GetConfigFilePath(config_file, config_dir = None):
  filename = config_file
  if os.path.basename(filename) == filename:
    # simple filename. Try to locate it.
    if config_dir != None:
      configfile = "%s/%s" % (config_dir, filename)
    else:
      import sitecustomize
      configfile = "%s/google/config/%s" % (sitecustomize.GOOGLEBASE, filename)
  else:
    # user specified an absolute or relative path. Assume user knows better.
    configfile = filename
  return os.path.abspath(configfile)

# ExecFile - simple wrapper around the built-in execfile() (or exec) to provide
# location-independent execs of config files. Depends on the standard
# sitecustomize mechanism to point to the root of the P4 tree.
#
# config_file may be either a filename or a file-like object.

def ExecFile(config_file, config_dir = None):
  if type(config_file) != types.StringType:
    # file-like object
    scope = GetPreloadedScope()
    exec config_file.read() in scope
    del scope['__builtins__']  # exec adds this crap for some reason
    return scope

  configfile = GetConfigFilePath(config_file, config_dir = config_dir)

  # We preload  a small number of variables with commonly used values
  # that people often use code in config files for.

  scope = GetPreloadedScope()

  if not os.access(configfile, os.O_RDONLY):
    raise IOError, "unable to locate a readable %s" % configfile
  execfile(configfile, scope)
  del scope['__builtins__']  # execfile adds this crap for some reason

  return scope

# ListFiles - list config files that match glob pattern for files.
# For example: ListFiles('services.??') returns [ 'services.ab',
# 'services.dc', ... ]
def ListFiles(file_pattern, config_dir=None):
  if not config_dir:
    import sitecustomize
    pattern = "%s/google/config/%s" % (sitecustomize.GOOGLEBASE, file_pattern)
  else:
    pattern = "%s/%s" % (config_dir, file_pattern)
  return glob.glob(pattern)

#
# LoadConfigData - routine to load raw data declared in a configuration
# file.  This essentially execs the file but also processes include
# directives if do_includes = 1.  See the top of googleconfig.py
# for an explanation of the INCLUDES directive.
#
# This method returns (data, shared_ports) where data is
# the config data, and shared_ports are those ports that were loaded
# that are not owned (i.e. ownservers was '0').
#
# You should not use this method to load config data, but rather use
# the googleconfig.Config object.  seen_files is only for loop detection.
#
# config_file is either a filename or a file-like object.
#
# NOTE: How we do it
#
#    Prepare base_data with all values from base_scope
#      (passed from earlier includes - eventually this may include defaults)
#    Update base_data with values from config_file
#    Prepare an empty update_data
#    for all I in INCLUDES:
#      Load I into update_data
#      Merge include_data into update_data and override vars in update_data
#    by now update_data will contain the sum of all includes, later overriding
#      earlier
#    Merge update_data into base_data
#
def LoadConfigData(config_file,
                   do_includes=0, seen_files=[], config_load_dir=None,
                   base_scope=None):

  # We copy base scope (which we're going to exec over)
  # since we're going to delete some protected vars that shouldn't
  # be shared.
  if base_scope is None: base_scope = {}
  base_scope = copy.deepcopy(base_scope)
  original_base_scope = copy.deepcopy(base_scope)

  # Delete vars from the base_scope which should not be propagated.
  # INCLUDES and CURRENT_CONFIG are deleted, since we don't want to
  # be affected by earlier peoples includes when we actively process
  # includes below.  Servers defined in one file aren't made
  # available either - at some point only TOP level files will have
  # servers (except for glue files).
  protected_vars = [ 'INCLUDES', 'CURRENT_CONFIG', 'SERVERS', ]
  for var in protected_vars:
    if base_scope.has_key(var): del base_scope[var]

  # The files that we load
  loaded_files = []

  # Load the raw data over base_scope.  This allows variables from
  # earlier includes to be available and referenced in later includes.
  base_data = config_namespace.ConfigNameSpace(base_scope)
  if config_file:
    try:
      base_data.ExecFile(config_file, config_dir=config_load_dir)
      if type(config_file) == types.StringType:
        loaded_files.append(GetConfigFilePath(config_file,
                                              config_dir=config_load_dir))
    except IOError:
      raise IOError('unable to load config %s' % config_file)

  shared_ports = []

  orig_servers = base_data.namespace.get('SERVERS', {})

  # Find out directory of current config file.
  if type(config_file) == types.StringType:
    (config_dir, config_name) = os.path.split(config_file)
  else:
    config_name = '<>UNNAMED<>'

  # We only allow certain variables in servers.* files.
  allowed_vars = AllowedServerConfigVars() + \
                 GetPreloadedScope().keys()
  if config_name[:len('servers.')] == 'servers.':
    my_vars = setlib.diff(base_data.namespace.keys(),
                          original_base_scope.keys())
    if setlib.diff(my_vars, allowed_vars):
      raise RuntimeError('Server file %s has vars outside allowed set: %s.'
                         ' bad vars: %s'
                         % (config_file, AllowedServerConfigVars(),
                            setlib.diff(my_vars, allowed_vars)))

  # Clone seen_files to silence pycheck
  seen_files = seen_files + [config_name]

  update_data = config_namespace.ConfigNameSpace(base_data.namespace)

  # INCLUDES is a list of files to include.  For backwards compatibility
  # support this as a dictionary as well.  However, INCLUDES as a dictionary
  # is DEPRECATED.
  include_specs = []
  if do_includes:
    includes = base_data.namespace.get('INCLUDES', {})
    if type(includes) == types.ListType:
      tmp = {}
      for source in includes:
        include_specs.append((source, {'ownservers' : 1, 'include_vars' : 1}))
        tmp[source] = { 'ownservers' : 1, 'include_vars' : 1 }
      # For now convert it in the actual data to a dictionary.
      # This is necessary if there are multiple levels of includes
      # and we try to merge different types.  Once we are no longer
      # using the dictionary type include, then get rid of this
      # and a lot of this other crap can be removed.
      base_data.namespace['INCLUDES'] = tmp
    else:
      include_specs = includes.items()

    # Extend includes with the active config file.
    active_config = base_data.namespace.get('CURRENT_CONFIG')
    if active_config:
      include_specs.append((active_config,
                           {'ownservers' : 1, 'include_vars' : 1}))

  for (source, options) in include_specs:

    if source in seen_files:
      raise RuntimeError("Detected loop while loading %s: %s already in %s" %
                         (config_name, source, string.join(seen_files)))

    # Test if this is a service name.
    if type(source) == types.TupleType:
      colo = source[0]
      source = source[1]
      from google3.enterprise.legacy.production.babysitter import masterconfig
      factory = masterconfig.Factory(colo, config_dir = config_load_dir)
      source = factory.GetConfigFiles(source)[0]

    # Load the included data and remove servers.
    (include_data, _, lf) = LoadConfigData(source,
                                           do_includes=do_includes,
                                           seen_files=seen_files,
                                           config_load_dir=config_load_dir,
                                           base_scope=update_data.namespace)
    # Update the loaded files list
    for f in lf:
      if f not in loaded_files: loaded_files.append(f)

    include_servers = include_data.namespace.get('SERVERS', {})
    if include_data.namespace.has_key('SERVERS'):
      del include_data.namespace['SERVERS']

    # Process the merging options.
    server_option = options.get('ownservers', 0)
    types_option = options.get('wantedtypes', [])
    include_vars = options.get('include_vars', 1)
    server_types = servertype.CollectTypes(types_option, {})

    # Handle server merge.
    for (port, servers) in include_servers.items():

      typelvl = servertype.GetTypeLevel(port)
      if not servertype.WantedType(typelvl, server_types): continue

      if orig_servers.has_key(port):
        raise RuntimeError("Attempt to overwrite %s servers (port %s) "
                           "for service %s." % (typelvl, port, source))
      elif server_option == 0:
        shared_ports.append(port)

      orig_servers[port] = copy.deepcopy(servers)

    # Handle variable merge.
    if include_vars:

      # Apply any included segment specific variables to the top level
      # if this is a segment.  This allows us to define in one file,
      # all differing per-segment variables.
      if base_data.namespace.has_key('SEGMENT_SET') and \
         include_data.namespace.has_key('SEGMENT_SET_VARS'):

         segment = base_data.namespace['SEGMENT_SET']
         vars = include_data.namespace['SEGMENT_SET_VARS']
         if not vars.has_key(segment):
           raise RuntimeError('Segment %s data not found in SEGMENT_SET_VARS '
                              'for %s' % (segment, source))
         vars = vars[segment]

         # We change the variable values here for purposes of
         # regression testing.  This makes data.* files return
         # standard values.
         if segment_data.UseFakeData():
           vars = segment_data.MakeFakeSetVars(vars, segment)
         tmp_data = config_namespace.ConfigNameSpace(vars)
         include_data.MergeNamespace(tmp_data, 1)

      update_data.MergeNamespace(include_data, 1)

  # Merge included data into the params which contains the defaults.
  update_data.MergeNamespace(base_data, 1)
  shared_ports.sort()

  # Convert the final servers map into lists (if needed) and save it.
  update_data.namespace['SERVERS'] = GetServers(orig_servers)

  return (update_data, shared_ports, loaded_files)

# GetServers - Convert a SERVERS map from port->"host1 host2 ..." into
# port->["host1", "host2", ...] as expected by various scripts.
def GetServers(servers):
  for port, machines in servers.items():
    if type(machines) == types.StringType:
      servers[port] = string.split(machines)

  return servers

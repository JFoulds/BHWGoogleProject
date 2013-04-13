#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# Server type information.
#
# These methods provide access to the data in configuration files
# servertype_data.py, servertype_prod.py and servertype_crawl.py

import commands
import exceptions
import os
import re
import signal
import socket
import string
import sys
import types
import validatorlib

# Hack to enable circular imports
import google3.enterprise.legacy.production.babysitter
google3.enterprise.legacy.production.babysitter.servertype = \
    sys.modules[__name__]

from google3.enterprise.legacy.production.common import cli
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.setup import serverflags
from google3.pyglib import logging

__pychecker__ = 'maxargs=20'

# Import raw server type data.  These were defined in a separate file
# for easier updating (don't have to look through any code).
# The underscores are used so that people don't try and directly
# access the data structures.
from google3.enterprise.legacy.production.babysitter.servertype_data import \
  _SERVER_TYPE_PORTS_, \
  _SERVER_TYPE_DEFAULTS_, \
  _SERVER_TYPE_PROPERTIES_NON_OVERRIDABLE_, \
  _SERVER_TYPE_PROPERTIES_, \
  _AUTOASSIGN_MAP_, \
  _NEED_RFSERVER_TYPES_, \
  _DEFAULT_RFSERVER_PORT_, \
  _SUPPORT_BINARIES_, \
  _CROSS_INDEX_STORE_DATA_TYPES_, \
  _BALANCER_PASS_THROUGH_PROPERTIES_

# NOT INTENDED FOR USE IN PRODUCTION!
# Must be a non-negative integer < 1000.
_SANDBOX_OFFSET_ = 0

#
# Methods for getting information about server types.
# All these methods accept a servertype arg "mtype" - i.e. "index", "doc".
#

#
# Get complete list of server types.
#
def GetServerTypes():
  return _SERVER_TYPE_PORTS_.keys()

#
# Return 1 if this is a valid servertype.
#
def IsValidServerType(mtype):
  return _SERVER_TYPE_PORTS_.has_key(mtype)

#
# Get min port for a server type.
#
def GetPortMin(mtype):
  return _SERVER_TYPE_PORTS_[mtype][0]

#
# Given a server type, return the high end of the port range for
# that type. Note that this is 1 more than the highest numbered port
# that can actually be used by that type. E.g. if the allowed ports
# are 4000 to 4999, this returns 5000.
#
def GetPortMax(mtype):
  return _SERVER_TYPE_PORTS_[mtype][1]

#
# Get server type property.  This method should not be directly
# called by clients in general.  You should use the 'property()'
# method from the serverlib.ServerSet object.  This allows
# overriding of servertype properties in config files.
#
def GetProperty(mtype, key, dflt = None):
  props = _SERVER_TYPE_PROPERTIES_.get(mtype, {})
  val = props.get(key, _SERVER_TYPE_DEFAULTS_.get(key, None))
  if val != None:
    return val
  else:
    return dflt

#
# Get property names.
#
def GetPropertyNames():
  return _SERVER_TYPE_DEFAULTS_.keys()

#
# Test if this server type supports shards.
#
def IsSharded(mtype):
  return GetProperty(mtype, 'is_sharded')

#
# Test if this server type supports levels.
#
def IsLeveled(mtype):
  return GetProperty(mtype, 'is_leveled')

#
# Get the level size.
#
def GetLevelSize(mtype):
  if not IsLeveled(mtype):
    return 0
  return GetProperty(mtype, 'level_size')

#
# Test if this server type has a datadir.
#
def HasDataDir(mtype):
  return GetProperty(mtype, 'has_datadir')

#
# Get name of binary.  Defaults to server type name.
#
def GetBinaryName(mtype):
  return GetProperty(mtype, 'binary_name', mtype)

#
# Get timeouts of server type name.
#
def GetTestTimeouts(mtype):
  return GetProperty(mtype, 'test_timeouts')

def GetBinaryFiles(mtype, expand_aliases = 1, seen = None, getrealfiles = 0):
  """Get the binary files for a servertype.

  Given a machine type it will return the list of binaries that the
  machine is supposed to have to work properly. We define a special
  type: "support" as a placeholder for binaries (like filesum) that
  should be present on all machines so standard copy code works
  fine. We also take into account common setups (like docservers
  may serve as balancers too)

  Args:
    mtype: 'servertype' - the desired servertype.
    expand_aliases: 0|1|2 - controls what is returned:

      0 - no expansion. Strict, per-type, binaries names only are returned.
      1 - alias expansion. multi-use machines get binaries for all types
          they accept sharing with (eg. doc+balancer).
      2 - expand mtype in the binary name too (so we know where
          the binary came from) This includes expansion for #1

    getrealfiles:  If 1, return binary_files as is (e.g., if binary_files is [],
                   simply return []).  This allows for seperation between
                   babysitter kill commands and files that actually get
                   binchecked.
  Returns:
    ['file1', ...] - list of binary files

  """

  # To prevent infinite loops.
  if seen is None: seen = []
  if mtype in seen:
    raise RuntimeError, 'Circular dependencies for binary files: %s %s' % \
                        (mtype, seen)
  else:
    seen = seen + [mtype]

  # Check if this binary inherits from another type.
  inherit_mtype = GetProperty(mtype, 'binary_files_inherit')

  if inherit_mtype:

    # Ensure they haven't specified binary files.
    if GetProperty(mtype, 'binary_files'):
      raise RuntimeError, ('%s sets both binary_files and '
                           'binary_files_inherit' % mtype)

    # Return the binary files of the inherited type.
    return GetBinaryFiles(inherit_mtype, expand_aliases=expand_aliases,
                          seen=seen)

  # Get list of binary files
  if mtype == 'support':
    binary_files = _SUPPORT_BINARIES_
  elif getrealfiles and GetProperty(mtype, 'binary_files') is not None:
    binary_files = GetProperty(mtype, 'binary_files')
  elif GetProperty(mtype, 'binary_files') == []:
    binary_files = [GetBinaryName(mtype)]
  else:
    binary_files = GetProperty(mtype, 'binary_files', [GetBinaryName(mtype)])

  # Expansion of binary files into type/binname.
  # For example: ['file1', 'file2', 'file3'] =>
  #              [ 'mtype/file1', 'mtype/file2', 'mtype/file3' ]
  if expand_aliases == 2:
    binary_files = map(lambda b,t=mtype: '%s/%s' % (t, b), binary_files)

  # Extend the list of binaries with additional binary files from
  # other servertypes.  This is used for commonly shared servers.
  # It isn't really strictly necessary but for convenience in binpushing.
  if expand_aliases:
    for addl in GetProperty(mtype, 'binary_files_addl', []):
      binary_files.extend(GetBinaryFiles(addl, expand_aliases=expand_aliases,
                                         seen=seen))

  return binary_files

#
# Get request information.
#
def GetRequestInfo(mtype):
  return (GetProperty(mtype, 'request_info'),
          GetProperty(mtype, 'response_len'))

#
# Get restart command.
#
def GetRestartCmd(mtype, config, host, port):
  restartfn = GetProperty(mtype, 'restart_function')
  if restartfn:
    return restartfn(config, host, port)
  else:
    return None

#
# Get data file localization info
# Returns a list of
#   (srcpath, targetpath, [files])
# tuples
#
def GetLocalDataFileInfo(mtype):
  prop_info = GetProperty(mtype, 'local_data_files')
  src_target_files_list = []
  # now fill in the default values
  if prop_info:
    for p_dict in prop_info:
      src_target_files_list.append( (p_dict.get('srcpath',    ''),
                                     p_dict.get('targetpath', ''),
                                     p_dict.get('files',      ['*']))
                                  )
    #end for
  else:
    prodlib.log('No local_data_files for %s.' % mtype)
  # end if
  return src_target_files_list
#end GetLocalDataFileInfo()

#
# Given a type and a list of types and negatives ("-index == all but
# index"), I return true or false depending if the type should be kept
# or not
#
def WantedType(typelvl, types):
  return prodlib.WantedType(typelvl, types)

#
# Map a list of types so we can use them as filters. Input like
# "index,-doc,link" means "all index, no doc, all link". We take
# into account levels too. If not specified all regular types are
# considered part of level 0.
#
def CollectTypes(typelist, types):
  return prodlib.CollectTypes(typelist, types)

#
# Methods for converting and correlating ports, levels, typelevels and types.
#

#
# Test if a port is of a given type. The argument may be a type
# without a level (will match any levels) or a typelvl argument.
#
def IsType(port, type_or_typelvl):
  (mtype, level) = (type_or_typelvl, None)
  if string.find(type_or_typelvl, ':') != -1:
    (mtype, level) = SplitTypeLevel(type_or_typelvl)

  if level == None or not IsLeveled(mtype):
    if level and level > 0:
      # Level must be 0 for non leveled types.  We have three options
      # for level > 0 for non-leveled types:
      #
      # - raise an error
      # - return true - i.e. IsType(9400, 'mixer:1') == 1
      # - return false - i.e. IsType(9400, 'mixer:1') == 0
      #
      # We've chosen the third option.  This means that for non-leveled
      # types, the entire port range counts as level 0.  This is more
      # consistent with the choices made in WantedTypes and NormalizeTypes
      # below.
      #
      return 0
    if mtype == 'web' and port == 80:
      # Hack to make web servers also on port 80 in addition to their range.
      return 1
    try:
      # Ensure port is in port range.
      (minport, maxport) = _SERVER_TYPE_PORTS_[mtype]
      return port >= minport and port < maxport
    except KeyError:
      # For unknown types we return 0.
      return 0
  else:
    # Leveled type.
    base = GetPortBase(type_or_typelvl)
    return port >= base and port < base + GetLevelSize(mtype)

#
# Get name of server type from port.
#

class PortTypeMapper:
  """Implement reasonably fast reverse mapping from ports to types.

  We create a single instance of this class and call it GetPortType;
  it can be called to map a port into a server type.
  """

  def __init__(self, type_to_bounds):
    self.type_to_bounds = type_to_bounds
    self.port_to_type = {}         # cache for mappings already computed
    self.port_to_type[80] = 'web'  # convenient place for this hack
    self.bounds_array = None       # these two are set up
    self.lower_bound_to_type = {}  #   by initialize_search()

  def __call__(self, port, hint=None):
    """Map a port into its associated server type."""

    mtype = self.port_to_type.get(port, None)
    if mtype is not None:
      return mtype

    # The hint optional parameter speeds up code in serverlib.py, because it
    # runs through ports in sorted order, and some mtypes have many shards.
    if hint is not None:
      (lower_bound, upper_bound) = self.type_to_bounds[hint]
      if lower_bound <= port < upper_bound:
        mtype = hint
        self.port_to_type[port] = mtype
        return mtype

    if self.bounds_array is None:
      self.initialize_search()

    # Binary search:
    if port < self.bounds_array[0]:  # first, a sanity check
      prodlib.log('WARNING: returning unknown servertype for: %d' % port)
      return 'unknown'
    first_possible = 0
    n_possible = len(self.bounds_array)
    while n_possible > 1:
      n_first_half = int(n_possible / 2.0)
      probe = first_possible + n_first_half
      if port < self.bounds_array[probe]:
        n_possible = n_first_half
      else:
        n_possible = n_possible - n_first_half
        first_possible = first_possible + n_first_half
    lower_bound = self.bounds_array[first_possible]
    mtype = self.lower_bound_to_type.get(lower_bound, 'unknown')
    self.port_to_type[port] = mtype

    if mtype == 'unknown':
      prodlib.log('WARNING: returning unknown servertype for: %d' % port)
    return mtype

  def initialize_search(self):
    all_bounds = {}
    for mtype, bounds in self.type_to_bounds.items():
      (lower_bound, upper_bound) = bounds
      all_bounds[lower_bound] = 1
      all_bounds[upper_bound] = 1
      self.lower_bound_to_type[lower_bound] = mtype
    self.bounds_array = all_bounds.keys()
    self.bounds_array.sort()

GetPortType = PortTypeMapper(_SERVER_TYPE_PORTS_)

#
# Given a port, return the corresponding shard number.
#
def GetPortShard(port):

  mtype = GetPortType(port)

  if mtype == 'unknown':
    return 0 # no magic ports anyway

  if not IsSharded(mtype):
    return 0

  shard = port - _SERVER_TYPE_PORTS_[mtype][0]
  if IsLeveled(mtype):
    # levels are "mod 'level_size'" apart (usually "mod 100")
    shard = shard % GetLevelSize(mtype)
  return shard

#
# Given a port, return the index level which this backend
# operates at.
#

# This is a cache of a mapping between ports and levels for the
# GetLevel method.
_LEVEL_CACHE_ = {}

def GetLevel(port):

  global _LEVEL_CACHE_
  if _LEVEL_CACHE_.has_key(port):
    return _LEVEL_CACHE_[port]

  mtype = GetPortType(port)
  if not IsLeveled(mtype):
    lvl = 0
  else:
    lvl = (port - GetPortMin(mtype))/GetLevelSize(mtype)

  _LEVEL_CACHE_[port] = lvl
  return lvl

#
# Return a canonical type-level labelling for the port.
# The canonical form is <type>:<level>
#

#
# Normalize a typelvl.
#
def NormalizeTypeLevel(typelvl):
  cnt = string.count(typelvl, ':')
  # typelvl is in correct format (i.e. 'mtype:lvl')
  if cnt == 1:
    return typelvl
  # force typelvl (i.e. 'mtype')
  elif cnt == 0:
    return typelvl + ':0'            # assume lvl 0 if unknown
  # invalid format (i.e. 'mtype::lvl')
  else:
    prodlib.log("Invalid typelvl format: %s" % typelvl)
    raise RuntimeError

# This is a cache of a mapping between ports and typelevels for the
# GetTypeLevel method.  While the method is not doing much, constantly
# building many strings is inefficient.
_TYPE_LEVEL_CACHE_ = {}

def GetTypeLevel(port):

  global _TYPE_LEVEL_CACHE_
  if _TYPE_LEVEL_CACHE_.has_key(port):
    return _TYPE_LEVEL_CACHE_[port]

  typelvl = "%s:%d" % (GetPortType(port), GetLevel(port))
  _TYPE_LEVEL_CACHE_[port] = typelvl
  return typelvl

#
# Separates index:1 into ('index', 1) Assume L0 if no level is specified
#
def SplitTypeLevel(typelvl, strict=0):
  if string.find(typelvl, ':') == -1 and not strict:
    typelvl = NormalizeTypeLevel(typelvl)
  fields = string.split(typelvl, ':')
  if len(fields) != 2:
    raise RuntimeError, "servertype.SplitTypeLevel: invalid param %s" % typelvl
  (mtype, lvl) = fields
  return (mtype, int(lvl))

#
# Given a type:lvl spec, it return the lowest port number for that
# type for the given level. In other words, return port number for
# shard 0 in that level.
#
def GetPortBase(typelvl):
  (mtype, lvl) = SplitTypeLevel(typelvl)
  return _SERVER_TYPE_PORTS_[mtype][0] + int(lvl)*GetLevelSize(mtype)

#
# Return true if this mtype is a balancing type of server.
#
def IsBalancerType(mtype):
  return mtype in ['balancer', 'transbal']

#
# Return the type of balancer that balances a given type of server.
#
def GetBalancerType(mtype):
  if mtype == 'translation':
    return 'transbal'    # use transbal for translation backends
  else:
    return 'balancer'    # balancers for everyone else

#
# Return a statusz port for a balancer.  Theoretically now this
# could just be 9420 all the time and really, eventually we don't
# really even need a separate statusz port from the balanced port
# if we ever went to separate balancer processes.  For backwards
# compatibility though, we do the level offsetting.
#
def GetBalancerPort(balanced_port):
  basemtype = GetBalancerType(GetPortType(balanced_port))
  level = GetLevel(balanced_port)
  return GetPortBase('%s:%s' % (basemtype, level))

#
# Return list of properties that should be passed through
# from balanced types to the balancers.
#
def GetBalancerPassThroughProperties():
  return _BALANCER_PASS_THROUGH_PROPERTIES_

#
# Get the auto assignment map.
#
def GetAutoAssignMap():
  return _AUTOASSIGN_MAP_

#
# Get the non overridable server properties as a list.
#
def GetNonOverridableServerProperties():
  return _SERVER_TYPE_PROPERTIES_NON_OVERRIDABLE_

#
# Get list of types which need rfservers.
#
def GetNeedRFServerTypes(has_gfs):
  if has_gfs:
    return _NEED_RFSERVER_TYPES_['gfs']
  else:
    return _NEED_RFSERVER_TYPES_['nogfs']

#
# Get default rfserver port for above types.
#
def GetDefaultRFServerPort():
  return _DEFAULT_RFSERVER_PORT_

#
# Get cross index store data types.
#
def GetCrossIndexStoreDataTypes():
  return _CROSS_INDEX_STORE_DATA_TYPES_

#
# Set the sandbox offset.
#
def SetSandBoxOffset(offset):
  global _SANDBOX_OFFSET_
  _SANDBOX_OFFSET_ = offset

#
# Get the sandbox offset.
#
def GetSandBoxOffset():
  global _SANDBOX_OFFSET_
  return _SANDBOX_OFFSET_

#
# Translate a magic port to the actual tcp/ip port used by the server.
# Normally this is the identity function, but for preprod sandboxes
# it isn't.
#
# WARNING: DO NOT alter or use port_offset without talking to Euguene.
#
def GetServingPort(port):
  global _SANDBOX_OFFSET_
  return port + _SANDBOX_OFFSET_

#
# build the server backend flags
#
def GetShardInfoBackends(config, srvname, level, protocol, num_conns,
                         segment=None):
  backends = serverflags.Backends()
  shardinfo = serverflags.ShardInfo()
  hp_pairs = config.GetServerHostPorts(srvname)
  for (h,p) in hp_pairs:
    backends.AddBackend(h, p, level, srvname, segment)

  type_level = srvname + ":%d" % level
  shardinfo.set_min_port(type_level, segment,
                         config.GetPortList(srvname)[0])
  shardinfo.set_max_port(type_level, segment,
                         config.GetPortList(srvname)[-1])
  shardinfo.set_protocol(type_level, segment, protocol)
  if num_conns:
    shardinfo.set_num_conns(type_level, segment, num_conns)
  return (shardinfo, backends)



#
# Methods for starting/stopping/checkpointing/testing server.
# If you want to run restart/kill methods, you need to first
# call servertype.LoadRestartInfo() to load the restart methods found
# in servertype_prod and servertype_crawl.
#

#
# Register restart function.
#
def RegisterRestartFunction(mtype, restart_function, kill_function = None):
  assert(not _SERVER_TYPE_PROPERTIES_[mtype].has_key('restart_function'))
  _SERVER_TYPE_PROPERTIES_[mtype]['restart_function'] = restart_function
  _SERVER_TYPE_PROPERTIES_[mtype]['kill_function'] = kill_function

#
# Load restart information into server types.
#
def LoadRestartInfo():

  # Import restart/kill functions.  These modules declare the
  # restarts and then call RegisterRestartFunction.
  from google3.enterprise.legacy.production.babysitter import servertype_prod
  from google3.enterprise.legacy.production.babysitter import servertype_crawl

  # To silence pychecker.
  servertype_prod = servertype_prod
  servertype_crawl = servertype_crawl

#
# Restart the server.
# mode: 0 - run command 1 - print only 2 - just return command
#
def RestartServer(mtype, config, host, port, mode=0,
                  ssh_user=None, server=None):

  if server:
    cmd = server.start_cmd()
    kill_cmd = server.stop_cmd()
    kill_delay = server.property('kill_delay')
    if server.isbal(): port = server.balport()
  else:
    cmd = GetRestartCmd(mtype, config, host, port)
    kill_cmd = GetKillCmd(mtype, port)
    kill_delay = GetProperty(mtype, 'kill_delay')

  if not cmd: return ""

  pre_cmd = None
  if mode == 1:
    pre_cmd = 'echo "%s:%s:%s"' % (os.path.basename(config.GetConfigFileName()),
                                   mtype, port)

  # this is pretty gross - maybe specify as parameter?
  local = config.var('RUN_LOCALLY', 0)
  keep_output = config.var('KEEP_OUTPUT', 0)
  bashrc_file = config.var('BASHRC_FILE')

  return RunCommand(host, port, cmd, local, pre_cmd, mode, keep_output,
                    background=1, bashrc_file=bashrc_file, ssh_user=ssh_user,
                    kill_cmd=kill_cmd, kill_delay=kill_delay)

#
# Get kill command.
#
# default is to take the signal from mtype
def GetKillCmd(mtype, port, signal = None):

  if port != 80 and (port <= 1024 or port >= 65536): return None

  killfn = GetProperty(mtype, 'kill_function')
  delay = GetProperty(mtype, 'kill_delay')
  if signal == None:
    signal = GetProperty(mtype, 'kill_signal')
  noport = GetProperty(mtype, 'kill_noport')

  if killfn != None:
    # user wanted full control. Let 'em have it.
    return killfn (port, delay, signal)

  elif noport:
    # special kill for a few (rare) servers that don't have the port
    # num on the cmd line. This uses killall and it's a *dangerous*
    # operation. Avoid if possible!
      return GetKillSigOnDelay(mtype, delay, signal)

  else:
    # Normal kill.

    # Locate binaries to kill.
    kill_bins = GetBinaryFiles(mtype, expand_aliases = 0)

    # we got our binary list. Add a complete kill command for *each* of them
    cmd = []
    for binname in kill_bins:
      cmd.append(GetKillSigOnPortDelay(binname,
                                       port,
                                       delay, signal))
    return string.join(cmd, '')

#
# Kill server.
# mode: 0 - run command 1 - print only 2 - just return command
#
# default is to take signal from mtype
def KillServer(mtype, config, host, port, do_checkpoint = 0,
               checkpoint_time = 1200, mode=0, signal=None,
               background=1, ssh_user=None, server=None):

  if server:
    cmd = server.stop_cmd()
    if server.isbal(): port = server.balport()
  else:
    cmd = GetKillCmd(mtype, port, signal=signal)
  if not cmd: return None

  pre_cmd = None
  if do_checkpoint and GetProperty(mtype, 'checkpoint_info') != None:
    pre_cmd = GetCheckpointCmd(mtype, host, port, checkpoint_time)

  local = config.var('RUN_LOCALLY')
  keep_output = config.var('KEEP_OUTPUT', 0)
  bashrc_file = config.var('BASHRC_FILE')

  return RunCommand(host, port, cmd, local, pre_cmd, mode,
                    keep_output, background, bashrc_file, ssh_user=ssh_user)

#
# Get command to execute to cause server to checkpoint.
#
def GetCheckpointCmd(mtype, host, port, checkpoint_time=1200):
  checkpoint_info = GetProperty(mtype, 'checkpoint_info')

  if not checkpoint_info:
    return None

  return "python -c 'import servertype; servertype.SendCommandToServer(\"%s\", %d, \"%s\", 1, %d)'; sleep 5" % (host, port, checkpoint_info, checkpoint_time)


class NetworkError(exceptions.Exception):
  def __init__(self, args=None):
    exceptions.Exception.__init__(self)
    self.args = args

def connect_alarm_handler(signum, frame):
  raise NetworkError, "timeout"

#
# Quick check to see if server is listening in on port.
#
def CheckServer(host, port):

  # A short timeout on the connect
  signal.signal(signal.SIGALRM, connect_alarm_handler)
  signal.alarm(3)
  connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  connector.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, -1)
  try:
    connector.connect((host, port))
    signal.alarm(0)
  except socket.error:
    signal.alarm(0)
    # We failed to connect. Probably nobody is listening at the
    # other end.
    return 1
  except NetworkError:
    # Timed out
    return 2

  connector.close()
  return 0


#
# Get server variable value from v or varz command.
#
# Raises:
#
#  - IOError if any networking errors occur.
#  - ValueError if a NACKGoogle was received or other error occurs retrieving
#    value.
def GetServerVariable(machine, port, varname, timeout=10, use_http=0):

  if use_http:
    cmd = 'GET /varz?output=text&var=%s HTTP/1.0\r\n\r\n' % varname
  else:
    cmd = 'v %s\n' % varname
  (status, output) = SendCommandToServer(machine, port, cmd, 1, timeout=timeout)

  # Parse output appropriately.
  if status:
    raise IOError('Error talking to server %s:%s - %s' %
                  (machine, port, status))

  output = string.split(output, '\n')

  if use_http:

    # Parse the header.
    for i in range(len(output)):
      line = output[i]
      if line == '\r': return output[i+1]
      fields = string.split(line)
      if len(fields) < 2: continue
      if fields[0] == 'HTTP/1.0' and fields[1] != '200':
        raise ValueError('Bad HTTP response code from %s:%s - %s' %
                         (machine, port, fields[1]))
    raise ValueError('Malformed HTTP response from %s:%s - %s' %
                     (machine, port, string.join(output)))
  else:
    if len(output) < 3 or output[-2] != 'ACKgoogle':
      raise ValueError('Unexpected response from %s:%s - %s' %
                       (machine, port, string.join(output)))
    return output[0]

#
# Send a command to a server.  Returns a tuple (status, output).
# If an error has occurred, status is non-zero and output is None.
#
def SendCommandToServer(machine, port, cmd, waitforreply, timeout=10):

  # A short timeout on the connect
  signal.signal(signal.SIGALRM, connect_alarm_handler)
  signal.alarm(3)
  connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  connector.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, -1)
  try:
    connector.connect((machine, port))
    signal.alarm(0)
  except socket.error:
    signal.alarm(0)
    # We failed to connect. Probably nobody is listening at the
    # other end.
    return 1, None
  except NetworkError:
    # Timed out
    return 2, None

  # Now we're connected.
  signal.alarm(timeout)
  res = None
  try:
    ok = (connector.send(cmd) == len(cmd))
    if (not ok):
      # For some reason, we didn't send as much as we expected.
      # This really shouldn't happen unless sending a large command
      # and the receiver dies half way through. I'm not even sure
      # If that would to it. However, it isn't a good sign.
      signal.alarm(0)
      return 3, None

    if (waitforreply): # Wait till we get a [N]ACKgoogle
      res =""
      ack_str = "ACKgoogle\n"
      while res[-len(ack_str):] != ack_str:
        output = connector.recv(1024)
        if not output: break
        res = res + output
    signal.alarm(0)
  except socket.error, e:
    # some network problem (server closes connection on us, for example)
    signal.alarm(0)
    return 4, e

  except NetworkError:
    # Timed out
    return 2, None

  connector.close()
  # Request-reply exchange complete

  return 0, res

#
# To kill a binary, we kill all procs in its process group. Since
# many servers may be on the same machine, we match port number too.
# In addition, swapped-out programs are shown in brackets but
# without args (eg "[docserver]"). We kill all such, to be safe.
# Note1: we ignore the loop.XXX processes. They get automatically
#   killed when we kill their process group (which includes the
#   loop, the binary and all its threads) However, if the loops are
#   not babysitting anything, they may get ignored. So we do a
#   second pass and grab all loop.XXX that are alone in their
#   group. All these loops are killed regardless.
# Note2: "ps axwwwwo pgid,pid,args" will return the gpid and the full
#   command line. Order is important as initial fields are trimmed!
# Note3: kernel only guarantees to keep the first 15 chars of
#   the exec-name for zombie and swapped out programs.
# Note4: the [^ ] distinguishes "if [ -x server ];" from "[server]"
# Note5: the funny sed command appends - to all gpids to make them
#   suitable for the kill command (-PID means "kill by process group")
# Note6: the egrep -v egrep is very important -- we're not suicidal!
# Note7: we have to disable patterns :port because
# these might be in the command line of another server and we can
# kill also that server
# Note8: We also kill commands which match the binary name, but have
# no commandline arguments. There seems to be a bug where some processes
# do not display commandline arguments with the ps command.
#
def GetKillSigOnPortDelay(binname, magic_port, delay, sig):

  KILL_SIG_ON_PORT_DELAY = (
    # prepare the reduced strings that match kernel limitations
    # TODO: drop this echo %(binname)s crap and pass the 15 char
    # biname directly. This is a function now so this hack is no
    # longer needed. To be done after we switch to the new code (or
    # regression tests will fail)
    'binname=$(echo %(binname)s | cut -b1-15); ' +
    # collect the ps data.
    'psoutfile=/tmp/tmppsout.$$; ' +
    'ps axwwwwo pgid,pid,args | egrep "${binname}" ' +
    '| egrep "[^1-9:.-,_]%(port)s|[^ ]\]|[0-9]+ +[0-9]+ +[^ ]+$" ' +
    '|  fgrep -v egrep > $psoutfile; ' +
    # grab the GPIDs for the babysat binaries. Ignore loops!
    'gpids=`cat $psoutfile | fgrep -v " loop." ' +
    '| cut -b1-6 | sort -n | uniq | sed "s/[0-9]/-&/"`; ' +
    # collect lonely loops PIDs too (loops that are not babysitting anything)
    'looppids=`cat $psoutfile | sort -n -k1,6 | uniq -c -w6 ' +
    '| cut -b1-7,14-19 | grep "^ \\+1 " | cut -b8-13`; ' +
     # cleanup
    'rm -f $psoutfile; ' +
    # start killing things
    'kill -%(sig)s $gpids $looppids;'
  )

  # for STOP and CONT, we don't want kill -9, thank you very much
  if sig in ['KILL', 'TERM', 'INT', 'QUIT'] and delay != -1:
    KILL_SIG_ON_PORT_DELAY = (
      KILL_SIG_ON_PORT_DELAY + ' sleep %(delay)s; kill -9 $gpids $looppids; ')

  # magic_port can be something else than an integer .. (like a normal string
  # that we want to have in the args of the name
  if isinstance(magic_port, types.IntType):
    magic_port = GetServingPort(magic_port)

  return KILL_SIG_ON_PORT_DELAY % {'sig': sig,
                                   'delay' : delay,
                                   'binname' : binname,
                                   'port' : magic_port}

#
# Kill for those servers that don't have a port.  This is
# here because of the CRAWL_SERVERS_TO_KILL_WITH_DIRECT_KILLALL
# code.  Note: this will ONLY work if you don't run multiple copies
# of same binary on the same machine.
#
def GetKillSigOnDelay(server_type, delay, sig):

  KILL_SIG_ON_DELAY = (
    'alarm %(delay)s killall -%(sig)s -w -g %(server)s || killall -9 -g %(server)s; '
  )
  return KILL_SIG_ON_DELAY % {'sig': sig,
                              'delay' : delay,
                              'server' : GetBinaryName(server_type)}

#
# Whenever we restart a service, we run this command.
# We run the passed-in command (2nd %s) in its own shell so it
# can redirect its own I/O if it wants to.  The $$ stuff around
# it is to make sure somebody else isn't restarting the same
# program at the same time.  The sleep is for start-up time.
# The alarm is for dead hosts; 20 seconds is longer than the sleep!
# We also do an fping to make sure the machine is alive first
# (it returns 0 if machine is alive, 1 if not, 3 if you're not root).
def RunCommand(host, port, cmd, local=0, pre_cmd=None, mode=0,
               keep_output=0, background=1, bashrc_file='/etc/profile',
               ssh_user=None, kill_cmd=None, kill_delay=None):

  if background:
    background_string = " &"
  else:
    background_string = ""

  if not ssh_user:
    ssh_user = ""
  else:
    ssh_user = '%s@' % ssh_user

  # If kill_cmd is specified, then compose the command to run a bit differently.
  # After the kill command we again make sure that the /tmp/restart file still
  # has our process id. We do this because executing kill command can sometime
  # take too long under load conditions and the restart file may have gotten
  # removed.
  if not kill_cmd is None:
    run_cmd = (
      "(%(kill_cmd)s); "
      "if test $$ -eq `cat /tmp/restart.%(port)d`; then"
      "  (%(cmd)s); "
      "fi ;"
      ) % {'port': GetServingPort(port),
           'cmd': cmd,
           'kill_cmd': kill_cmd,
          }
  else:
    run_cmd = cmd

  # run locally
  LOCAL_COMMAND = "(%(run_cmd)s) "
  if not keep_output:
     LOCAL_COMMAND = LOCAL_COMMAND + "> /dev/null 2>&1 "
  LOCAL_COMMAND = LOCAL_COMMAND + background_string

  # sshcmd is a parameter to ssh that need to be mkarg-ed
  REMOTE_COMMAND = (
    "fping -r1 %(host)s >/dev/null; test $? != 1 && "
    "alarm 20 ssh -P -n -q %(ssh_user)s%(host)s %(sshcmd)s" + background_string
  )
  sleep_time = 10
  if not kill_delay is None:
    sleep_time += kill_delay
  SSHCMD = (
    # Note we use a /tmp/restart.<port> file, which contains the current pid,
    # to serve as a lock against multiple instances of this code from
    # restarting the same server at the same time. However, the instance that
    # created the lock file may itself be killed (e.g. babysitter restarts and
    # kills its previous instance every 15 minutes) while holding the lock.
    # Therefore it's necessary to have a stale lock file removal logic to deal
    # with this rare race condition.
    ". %(bashrc_file)s; "
    "echo Running on `hostname`:%(port)d; "
    "pid=`cat /tmp/restart.%(port)d 2>/dev/null`; "
    "if ! test -z $pid; then "
    "  if ! test -d /proc/$pid; then "
    "    echo Stale lock file from pid $pid found. Removing...;"
    "    rm -f /tmp/restart.%(port)d; "
    "  fi; "
    "fi; "
    "set -o noclobber; echo $$ > /tmp/restart.%(port)d; "
    "if ! test -s /tmp/restart.%(port)d; then"
    "  echo Out of space on `hostname`, not running; "
    "elif test $$ -eq `cat /tmp/restart.%(port)d`; then "
    " (%(run_cmd)s) > /dev/null 2>&1 &"
    "  sleep %(sleep_time)d; rm -f /tmp/restart.%(port)d; "
    "fi"
  )

  if local:
    ret = LOCAL_COMMAND % { 'run_cmd' : run_cmd }
  else:
    ret = REMOTE_COMMAND % {
      'host': host,
      'ssh_user' : ssh_user,
      'sshcmd' : commands.mkarg(SSHCMD % {'port': GetServingPort(port),
                                          'run_cmd': run_cmd,
                                          'bashrc_file' : bashrc_file,
                                          'sleep_time': sleep_time,
                                          }
                                ),
    }

  if pre_cmd:
    ret = pre_cmd + "; " + ret

  if mode == 0: os.system(ret)
  elif mode == 1: print ret
  return ret

# unique identifier for an rtserver in a config
def GenRTIdentifier(machine_type, shard, num_shards):
  template = "%s%%03d-of-%03d" % (string.replace(machine_type,"_","-"),
                                  num_shards)
  if shard != -1:
    return template % (shard)
  else:
    return template   #  let others to fill in shard info
# end def

# src_machine_type is the machine that generates the data
# data generated by each rtserver lives in its own directory for GFS
def GenNamespacePrefix(config, src_machine_type, shard, num_shards):
  if not config.var('GFS_ALIASES'):
    return config.var('NAMESPACE_PREFIX')
  else:
    if config.has_var('GLOBAL_SERVERS') and \
       src_machine_type in config.var('GLOBAL_SERVERS'):# global servers
      namespace_prefix = (
        config.var('OUTPUT_NAMESPACE_PREFIX').get(
        src_machine_type, config.var('GLOBAL_NAMESPACE_PREFIX')))
    else:
      namespace_prefix = config.var('NAMESPACE_PREFIX')
    return "%s%s/" %  (namespace_prefix,
                       GenRTIdentifier(src_machine_type, shard,
                                       num_shards))

# Helper function to generate logfile basenames compatible with what
# is produced by the LogWriterSet class in io/logwriterset.h.  If the
# src_index is >= 0 we include it in the filename (typically only used
# if gfs is not present).
def GenLogfileBasename(rootname, target_shard, num_target_shards, src_index):
  if '@' in rootname:  # priority info is present
    (root, p) = string.split(rootname, '@')
    priority_str = '@' + p
  else:
    root = rootname
    priority_str = ''
  # end if
  if src_index < 0:
    return "%s-%03d-of-%03d%s" % (root, target_shard,
                                num_target_shards, priority_str)
  else:
    return "%s-from-%05d-%03d-of-%03d%s" % (root,
                                            src_index,
                                            target_shard,
                                            num_target_shards,
                                            priority_str)

# Gets ths rfserver bank args for the current config
def GetRfserverBankArgs(config):
  args = []
  if not config.var('GFS_ALIASES'):
    hosts = config.GetServerHosts('rfserver_bank')
    if hosts:
      args.append("--rfserver_bank=%s" % \
                  string.join(hosts, ","))

    if config.GetNumShards('rfserver_replica_bank') > 0:
      hosts = config.GetServerHosts('rfserver_replica_bank')
      if hosts:
        args.append("--rfserver_replica_bank=%s" % \
                    string.join(hosts, ","))

  return args


# EXPAND_CUTOFF
#  given a cutoff value, expands suffix shortcuts (M=millions,
#  K=thousands, etc.)  Default is base 10, but if the quantity
#  is bytes (KB, MB, GB), then it uses base 2 (1024, etc).
#  e.g.:
#    5M ->  5000000
#    5MB -> 5242880
# TODO: handle "BB"?
cutoff_re = re.compile('([^a-z]+)([bmkg]b?)$', re.IGNORECASE)  # cache regexp
def ExpandCutoff(cutoff):
  def repl_suffix(m):
    base = m.group(1)
    multiplier = 1
    if string.lower(m.group(2)) == 'b':        # billions
      multiplier = 1e9
    elif string.lower(m.group(2)) == 'm':      # millions
      multiplier = 1e6
    elif string.lower(m.group(2)) == 'k':      # thousands
      multiplier = 1e3
    elif string.lower(m.group(2)) == 'gb':     # gigabytes
      multiplier = 1 << 30
    elif string.lower(m.group(2)) == 'mb':     # megabytes
      multiplier = 1 << 20
    elif string.lower(m.group(2)) == 'kb':     # kilobytes
      multiplier = 1 << 10
    return "%.0f" % (float(base) * multiplier)

  # expand suffix if any
  cutoff = cutoff_re.sub(repl_suffix, str(cutoff))

  # return value AS TEXT because it may not be in the int() range
  return cutoff

# It converts a google_arg like , --datadir=/export/hda3/ , to
# --datadir='/export/hda3'. We do this to plug a potential
# security hazard for enterprise. If asked to, we bypass
# the conversion for arguments that are already quoted.

# note: we do with with a list of things that _do not need to be
# escape; it's much safer than the opposite.
doesnt_need_mkarg_re = re.compile('^[A-Za-z0-9-_.=/:,@]*$')
def mkarg(google_arg, escape_quoted=1):
  google_arg = string.strip(google_arg)

  do_escape = 1

  # if we were asked to not escape quoted args, dont do it
  if not escape_quoted:
    if google_arg[:1] in ("'", '"'):    # is already quoted
      do_escape = 0
    elif google_arg[:1] == "-":         # is a flag (-foo or --foo)
      split_arg = string.split(google_arg, "=", 1)
      if (len(split_arg) == 2 and                # has a foo=value value
          split_arg[1][0:1] in ("'", '"')):      # value is already quoted
        do_escape = 0

  # if it doesn't contain something that needs escaping, don't do it
  if do_escape and doesnt_need_mkarg_re.match(google_arg) != None:
    do_escape = 0

  if do_escape:
    google_arg = string.strip(commands.mkarg(google_arg))

  return google_arg

# convenience function to avoid quoting arguments that are already quoted
#
def mkarg_single_escape_only(google_arg):
  return mkarg(google_arg, escape_quoted=0)


##
## TODO: we need to implemtent something for this. This is used to determine
##       which servers need to be restarted because parmaters have changed.
##       - For now we don't restart anything because paramters changed..
##       A static map will do it but is unmainteinable.
##

# Returns the parameters that require server restarts when they are changed
def GetParamsToRestartTypes():
  return []

# Returns the sets to restart when a given parameter changes
def GetRestartTypesForParam(param):
  # Silence pychecker
  param = param
  return []

# Returns the string form of the long passed in - handles difference between
# Python 1.5 and 2.X (1L vs 1).
def LongToStr(long_var):
  assert type(long_var) == types.LongType
  strrep = str(long_var)
  if strrep[-1] == 'L': strrep = strrep[0:-1]
  return strrep
#end LongToStr

def BuildFlagArgs(config, var_name_and_flags):
  """var_name_and_flags is a list of (var_name, var_flags[, var_value]),
     If var_name is not None and var_value is not specified, we use
     var_value = config.var(var_name), then we add:
     var_flag=var_value if the var_value is not None.
     Currently supported types are
        IntType, FloatType, LongType, StringType,
     and
        ListType(t), where t is one of above types and
        the ListType(t) will produce a comma separated string list
        for the argument value.
  """


  command_line = cli.CommandLine()
  for args in var_name_and_flags:
    if len(args) == 3:
      (var_name, flag_name, var_value) = args
      assert not var_name
    else:
      (var_name, flag_name) = args
      var_value = config.var(var_name)
    # endif
    if var_value == None: # not set
      continue
    # endif

    var_type = type(var_value)
    if var_type == types.IntType:
      if ( var_name and
           isinstance(config.get_validator(var_name), validatorlib.Bool) ):
        # boolean
        if var_value:
          command_line.Add(flag_name)
        else:
          # We want to put 'no' in front of flag_name.
          # But we need to skip the initial '-' or '--' first.
          skip = 1
          if flag_name[:2] == '--': skip = 2
          # TODO:BWOLEN NO_UPINTEGRATE
          # change to make diff easier
          command_line.Add("--no%s" % flag_name[skip:])
          # command_line.Add("--%s=false" % flag_name[skip:])
        #endif
      else: # integer
        command_line.Add("%s=%d" % (flag_name, var_value))
    elif var_type == types.FloatType:
      command_line.Add("%s=%f" % (flag_name, var_value))
    elif var_type == types.LongType:
      command_line.Add("%s=%s" % (flag_name, LongToStr(var_value)))
    elif var_type == types.StringType:
      command_line.Add("%s=%s" % (flag_name, var_value))
    elif var_type == types.ListType:
      # validatorlib.py will make sure var_value is a list of the
      # same type.  hence we only need to test the first elt
      # for the type.  Also, even though map(str, ...) probably
      # works for any types, we intentionally force explicit
      # support not to have any surprises. (e.g., LongType won't
      # work well because of trailing L)
      if len(var_value) == 0:
        var_value_as_string = ""
      elif ((type(var_value[0]) == types.StringType) or
            (type(var_value[0]) == types.IntType) or
            (type(var_value[0]) == types.FloatType)):
        var_value_as_string = string.join(map(str, var_value), ',')
      elif type(var_value[0]) == types.LongType:
        var_value_as_string = string.join(map(LongToStr, var_value), ',')
      else:
        raise TypeError, ("List of %s is not supported. (flag %s, value %s)" %
                          (type(var_value[0]), flag_name, var_value))
      command_line.Add("%s=%s" % (flag_name, var_value_as_string))
    else:
      raise TypeError, ("type %s is not supported. (flag %s, value %s)" %
                        (var_type, flag_name, var_value))
    #endif
  #endfor
  return command_line.Args()
#enddef



def BuildOneFlagArg(config, var_name, var_flag):
  """return var_flag=config.var(var_name) if the variable's value is not None.
     Currently supported types are
        IntType, FloatType, LongType, StringType
     Note: google boolean flags will be treated as integers 0 or 1.
  """
  return BuildFlagArgs(config, [(var_name, var_flag)])
#enddef

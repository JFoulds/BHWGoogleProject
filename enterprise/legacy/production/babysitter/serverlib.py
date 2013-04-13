#!/usr/bin/python2.4
#
# serverlib.py - server objects and management.
#
# Copyright 2002 and onwards, Google
# Original Author: Eugene Jhong
#
# TODO:
#
# - This class will encapsulate all server info and replace what
#   is in googleconfig/configutil.
# - Need to generalize the concept of the server role (this will
#   allow us to do sets / servertype-port independence sometime)
#

import string
import types
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.production.common import setlib
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.setup import serverflags
from google3.enterprise.legacy.production.babysitter import masterconfig
from google3.enterprise.legacy.production.babysitter import segment_data
from google3.enterprise.legacy.setup import asyncli


class Error(Exception):
  """Base error class for serverlib."""


def GetPropertyNames():
  """Get valid server property names."""
  # We eventually want to not expose servertype
  # so don't force people to import servertype.
  return servertype.GetPropertyNames()


#------------------------------------------------------------------------------
# Server Information
#------------------------------------------------------------------------------

#
# Server
#
# Represents a server.
#
# The Server class has all the information about the server in the
# the context of the server manager.  Most of these fields are
# set by the ServerManager class.
#
# Most fields are self explanatory.  The 'index' field is the index
# of the slice on which the server resides in the config file.
# Slices are often not that important but sometimes come into play
# for example with primary balancers.  The 'balport' field' specifies
# the balanced port if the server is a balancer.
#

class Server:

  def __init__(self):
    self.srv_mgr_ = None
    self.host_ = None
    self.port_ = None
    self.srvset_ = None
    self.servertype_ = None
    self.index_ = None
    self.balport_ = None
    self.isbal_ = 0
    self.coloc_ = None
    self.rack_ = None
    self.statuszport_ = None
    self.auto_assigned_servers_ = []
    self.properties_ = {}

  # Initialize from a string of format '[+]host:port'.
  # Throws a ValueError if it is not able to parse properly.
  # This does not set the 'index' field.
  def InitFromName(self, name):
    self.set_isbal(0)
    if name[0] == '+':
      self.set_isbal(1)
      name = name[1:]
    (host, port) = string.split(name, ':')
    self.set_host(host)
    self.set_port(port)
    self.set_srvset(servertype.GetPortType(self.port()))
    if self.isbal():
      self.set_servertype(servertype.GetBalancerType(self.srvset()))
      self.set_srvset('+' + self.srvset())
      self.set_balport(servertype.GetBalancerPort(self.port()))
    else:
      self.set_servertype(self.srvset())
      self.set_balport(self.port())
    self.set_index(None)

  def srv_mgr(self):
    return self.srv_mgr_

  def set_srv_mgr(self, srv_mgr):
    self.srv_mgr_ = srv_mgr

  def property(self, key, dflt=None):
    """Return a property of the server.

    Args:
      key: 'string' - the name of the property.
      dflt: any - any default value.
    Returns:
      value: any - the value of the property.

    Currently, we don't support the flexibility of per-server properties.
    All properties are inherited from the server set.
    """
    return self.properties_.get(key,
             self.srv_mgr_.Set(self.srvset_).property(key, dflt=dflt))

  def set_property(self, key, val):
    self.properties_[key] = val

  def host(self):
    return self.host_

  def coloc(self):
    return self.coloc_

  def rack(self):
    return self.rack_

  def set_host(self, host):
    self.host_ = host
    self.coloc_ = ''
    self.rack_ = ''

  def port(self):
    return self.port_

  def set_port(self, port):
    self.port_ = int(port)

  def srvset(self):
    return self.srvset_

  def set_srvset(self, srvset):
    self.srvset_ = srvset

  def servertype(self):
    return self.servertype_

  def set_servertype(self, servertype):
    self.servertype_ = servertype

  def index(self):
    return self.index_

  def set_index(self, index):
    self.index_ = index

  def balport(self):
    return self.balport_

  def set_balport(self, balport):
    self.balport_ = int(balport)

  # returns the statusz port. We allow specific overwrites but, if not
  # set, we default to standard values: balancer port (if balancer),
  # statusz_port (if specified), or the actual port (for everything
  # else. eg. mixers, web).
  def statuszport(self):
    statuszport = self.statuszport_
    if not statuszport:
      statuszport = servertype.GetProperty(self.servertype(), 'statusz_port')
      if not statuszport:
        if self.isbal():
          statuszport = servertype.GetBalancerPort(self.port())
          if self.srvset() == '+index2':
            # BLIMPIE hack to get +index2 to avoid status port conflicts
            # with +index.
            statuszport = statuszport + servertype.GetPortBase('index2') - \
                          servertype.GetPortBase('index')
        else:
          statuszport = self.port()     # else default to serving port
    return statuszport

  def set_statuszport(self, statuszport):
    self.statuszport_ = int(statuszport)

  def isbal(self):
    return self.isbal_

  def set_isbal(self, isbal):
    self.isbal_ = isbal

  def level(self):
    return servertype.GetLevel(self.port())

  def datadir(self):
    if not servertype.HasDataDir(self.servertype()):
      return None
    return self.srv_mgr().config().GetDataDir(self.port())

  def auto_assigned_servers(self):
    return self.auto_assigned_servers_

  def set_auto_assigned_servers(self, servers):
    self.auto_assigned_servers_ = servers

  def __getitem__(self, key):

    set = self.srv_mgr().Set(self.srvset())
    vars = {}
    (shardinfo, backends) = set.BackendInfo(use_versions=0)
    shardinfo = shardinfo.AsString()
    if backends.HasBackEnds():
      backends = backends.AsString()
    else:
      backends = ''

    vars['port'] = self.port()
    vars['host'] = self.host()
    vars['shard'] = set.Shard(self.port())
    vars['datadir'] = self.datadir()
    vars['shardinfo'] = shardinfo
    vars['backends'] = backends
    vars['numshards'] = set.NumShards()

    if vars.has_key(key): return vars[key]
    return self.property(key)

  def start_cmd(self):
    """
    Return command to start server.
    """
    # If explicitly specified use, the explicit start_cmd property.
    if self.property('start_cmd'):
      return self.property('start_cmd') % self
    else:
      if self.isbal():
        port = self.balport()
      else:
        port = self.port()
      return servertype.GetRestartCmd(self.servertype(),
                                      self.srv_mgr().config(),
                                      self.host(), port)

  def stop_cmd(self, signal=None):
    """
    Return command to stop server.
    """
    # If explicitly specified use, the explicit stop_cmd property.
    if self.property('stop_cmd'):
      return self.property('stop_cmd') % self
    else:
      if self.isbal():
        port = self.balport()
      else:
        port = self.port()
      return servertype.GetKillCmd(self.servertype(), port, signal=signal)

  def Start(self, mode=0, ssh_user=None):
    """
    Start a server.
    Args:
      mode: 0 = start, 1 = print 2 = return cmd
      ssh_user: the ssh user to go in as
    """
    return servertype.RestartServer(self.servertype(),
                                    self.srv_mgr().config(),
                                    self.host(), self.port(),
                                    mode=mode, ssh_user=ssh_user,
                                    server=self)

  def Stop(self, mode=0, ssh_user=None,
           do_checkpoint=0, checkpoint_time=1200):
    """
    Kill a server.
    Args:
      mode: 0 = start, 1 = print 2 = return cmd
      ssh_user: the ssh user to go in as
      do_checkpoint: deprecated
      checkpoint_time: deprecated
    """
    return servertype.KillServer(self.servertype(),
                                 self.srv_mgr().config(),
                                 self.host(), self.port(),
                                 mode=mode, ssh_user=ssh_user,
                                 do_checkpoint=do_checkpoint,
                                 checkpoint_time=checkpoint_time,
                                 server=self)

  # Equality of servers based on field settings.  This allows
  # us to compare 2 server objects based on the values of their
  # pertinent field settings.
  def __cmp__(self, other):
    if other == None:
      return 1
    val = cmp(self.srvset(), other.srvset())
    if val: return val
    val = cmp(self.port(), other.port())
    if val: return val
    val = cmp(self.isbal(), other.isbal())
    if val: return val
    val = cmp(self.host(), other.host())
    if val: return val
    return 0

  def __str__(self):
    str = '%s:%s' % (self.host_, self.port_)
    if self.isbal_: str = '+' + str
    return str

  def __hash__(self):
    return hash(str(self))

#
# ServerSet
#
# Represents a set of servers.
#
class ServerSet:

  def __init__(self, srv_mgr, name, level):

    # Server manager of this set.
    self.srv_mgr_ = srv_mgr

    # Set name.  Currently this is either the servertype or
    # '+servertype' if this is a balancer set.  At some point
    # we may want srvset to be independent of servertype
    # if we allow sets of a servertype with different attributes
    # from the servertype defaults (i.e. changing portbase).
    # However, for now keep it the same.
    self.name_ = name

    # The servertype of this set.  Derive from the name.
    if name[0] == '+':
      self.servertype_ = servertype.GetBalancerType(name[1:])
    else:
      self.servertype_ = name

    # The level of this set.  Currently we store levels.
    # At some point however, we should eliminate levels which
    # will simplify things.  Levels should be differentiated
    # in front ends by the srvset.
    self.level_ = level

    # Servers in this set.
    self.servers_ = []

    # Map of ports to servers on that port.
    self.port2servers_ = {}

    # Map of indices (vertical slices) to servers on that index.
    self.index2servers_ = {}

    # Properties built from SERVER_SETS config variable.
    # These properties should eventually be used to be able to
    # override values of the underlying servertype.
    self.properties_ = {}

    # Set default backends for balancer.
    if self.isbaltype():
      self.set_property('backends', [ { 'set' : self.name()[1:],
                                        'per_shard' : 1 } ])

  def srv_mgr(self):
    return self.srv_mgr_

  def set_srv_mgr(self, srv_mgr):
    self.srv_mgr_ = srv_mgr

  def name(self):
    return self.name_

  def set_name(self, name):
    self.name_ = name

  def servertype(self):
    return self.servertype_

  def set_servertype(self, servertype):
    self.servertype_ = servertype

  def typelvl(self):
    return '%s:%s' % (self.servertype_, self.level_)

  def level(self):
    return self.level_

  def property(self, key, dflt=None):
    """Get a property of this set.

    Args:
      key: 'string' - the name of the property.
      dflt: any - any default value.
    Returns:
      value: any - the value of the property.

    The sequence of lookups is:
      - first look in SERVER_SETS for an explicit setting for the set.
      - next look in SERVER_SETS['default'] for an explicit default setting.
      - fall back to the servertype defined properties.
      - if none is found, return the passed in default.
    """

    ret = self.properties_.get(key)
    if ret is not None: return ret
    ret = self.srv_mgr_.property(key)
    if ret is not None: return ret
    return servertype.GetProperty(self.servertype(), key, dflt)

  def set_property(self, key, val):
    if key in servertype.GetNonOverridableServerProperties():
      raise KeyError, 'Server property %s is non-overridable.' % key
    self.properties_[key] = val

    # Balancers must balance same type of backend for now
    # (this is checked in the restart method).  We derive
    # balancer properties from the first specified set of backends
    # and for now at least that set must be local.
    if self.isbaltype() and key == 'backends':
      # The setname of the must be local to the config (i.e. not contain
      # a colon in the specification).
      if string.find(val[0]['set'], ':') != -1:
        raise Error('Balancer %s must balance local set first: %s' %
                    (self.name(), val))

  def isbaltype(self):
    return servertype.IsBalancerType(self.servertype())

  # Return the servertype of the balanced set if this is a
  # set of balancers.  If 'serve_as' has been used (for rtslaves)
  # we return the serve_as type.
  def balsrvset(self):
    if not self.isbaltype():
      raise ValueError('Set %s is not a balancer set' % self.name())
    backend_info = self.property('backends')[0]
    return backend_info.get('serve_as', backend_info['set'])

  # Get all servers in this set.
  def Servers(self):
    return self.servers_

  # Get all hosts in this set.
  def Hosts(self):
    return setlib.make_set(map(lambda x: x.host(), self.servers_))

  # Add a port.
  def AddPort(self, port):
    if not self.port2servers_.has_key(port):
      self.port2servers_[port] = []

  # Get sorted list of ports.
  def Ports(self):
    ret = self.port2servers_.keys()
    ret.sort()
    return ret

  # Get the port base for this server set.
  def PortBase(self):
    return self.Ports()[0]

  # Get number of shards.
  def NumShards(self):
    return len(self.Ports())

  # Get shard of a port.
  def Shard(self, port):
    return port - self.PortBase()

  # Get servers for particular port.
  def ServersForPort(self, port):
    return self.port2servers_.get(port, [])

  # Get sorted list of ports.
  def Indices(self):
    ret = self.index2servers_.keys()
    ret.sort()
    return ret

  # Get servers for particular index.
  def ServersForIndex(self, index):
    return self.index2servers_.get(index, [])

  # Replace a server's host with the given host.  Note: the
  # server object that is passed in is actually modified to
  # have the updated host.  Use this method instead of setting
  # the host field directly as the internal maps of the
  # manager must be updated.
  def ReplaceServer(self, server, host):
    server.set_host(host)

  # Adds a server.  Updates internal data structures.
  def AddServer(self, server):
    server.set_srv_mgr(self.srv_mgr())
    self.AddPort(server.port())
    self.servers_.append(server)
    append_dictlist(self.port2servers_, server.port(), server)
    server.set_index(len(self.port2servers_[server.port()]) - 1)
    append_dictlist(self.index2servers_, server.index(), server)

  # Removes a server.  Updates internal data structures.
  def RemoveServer(self, server):

    # Update internal data structures.
    self.servers_.remove(server)
    remove_dictlist(self.index2servers_, server.index(), server)

    # Since a server was removed, any server with a higher index
    # on this port should be reduced by 1.
    servers = self.port2servers_[server.port()]
    num = len(servers)
    index = servers.index(server)
    del(servers[index])
    for i in range(index, num-1):
      moved = servers[i]
      remove_dictlist(self.index2servers_, moved.index(), moved)
      moved.set_index(i)
      append_dictlist(self.index2servers_, moved.index(), moved)

  # Get offset to apply to port that a backend serves on.
  def _BackendPortOffset(self, backend_info, set):

    minport = set.PortBase()
    offset = 0
    serve_as = backend_info.get('serve_as')

    if serve_as and servertype.IsValidServerType(serve_as):
      # This set is serving as another type so adjust the port base if
      # this is a true babysitter servertype.
      offset = servertype.GetLevelSize(serve_as) * set.level() + \
               servertype.GetPortBase(serve_as) - minport
    else:
      # Otherwise use normal port base but take into account exceptions.
      # For example mixers always serve on 4000.
      offset = offset + (set.property('backend_port_base', minport) - minport)

    # Shift if specified.
    offset = offset + backend_info.get('port_shift', 0)

    # Explicit port base setting overrides everything.
    if backend_info.get('port_base'):
      offset = backend_info.get('port_base', minport) - minport

    return offset

  # Get backend servers for a server set.
  # GetBackendInfo should be used in favor of this method.
  # This is for servers that don't accept standard shardinfo/backends flags.
  # Returns backend servers for this set.
  def BackendHostPorts(self, tagname, port = None):
    ret = []
    for backend_info in self.property('backends', []):
      set = self.srv_mgr().BackendSet(backend_info.get('set'))
      if not set: continue

      name = set.name()
      if set.isbaltype(): name = set.balsrvset()
      name = backend_info.get('tag', name)
      if (tagname != name and
          tagname != backend_info.get('serve_as')):
        continue

      # Find backend server type and port offset.
      minport = set.PortBase()
      offset = self._BackendPortOffset(backend_info, set)

      if backend_info.get('per_shard', 0) and port:
        shard = self.Shard(port)
        servers = set.ServersForPort(minport + shard)
      else:
        servers = set.Servers()
      hostports = map(lambda x, o=offset: (x.host(),
                      servertype.GetServingPort(x.port() + o)), servers)
      ret.extend(hostports)
    return ret

  # Get backend information.  Returns serverflags shardinfo and backends
  # objects for the set.
  #
  # Uses the 'backends' specification in the SERVER_SETS config variable
  # to figure out the proper backends for a server set.
  #
  # If ports are specified, the backends are limited to the given
  # ports if the backend type is also specified to be 'per_shard'.
  #
  # Port offset can be used to change the port passed as a backend.
  # This should not be used - it's just to accomodate GWS needing
  # to think mixers are on port 4000.
  def BackendInfo(self, port = None, use_versions = 1):

    shardinfo = serverflags.ShardInfo()
    backends = serverflags.Backends()

    # Set proper default values if args are not specified.
    numconns = self.property('numconns')
    dflt_numconn = self.property('dflt_numconn', 3)
    schedtypes = self.property('schedtypes')

    # Build shardinfo and backends.
    backend_infos = self.property('backends', [])
    for backend_info in backend_infos:

      # Find the backend set.
      setspec = backend_info.get('set')
      usebal = not self.isbaltype()
      set = self.srv_mgr().BackendSet(setspec, consider_bals = usebal)

      if not set: continue

      mtype = set.servertype()
      if set.isbaltype():
        mtype = set.balsrvset()
      level = set.level()
      minport = set.PortBase()
      if set.NumShards() == 0:
        maxport = minport
      else:
        maxport = minport + set.NumShards() - 1

      level = backend_info.get('level', level)

      # Adjust mtype if we are serving as another type.
      mtype = backend_info.get('serve_as', mtype)

      # Find offset to apply to ports.
      offset = self._BackendPortOffset(backend_info, set)

      minport = minport + offset
      maxport = maxport + offset

      # TODO: DWG HACK! to allow running two servers on a single machine
      # at ports 9900 and 9930
      if mtype == 'translation':
        maxport = minport + 30

      # Set shardinfo data.
      num = backend_info.get('numconn', numconns.get(mtype, dflt_numconn))
      sched = backend_info.get('schedtype', schedtypes.get(mtype,
                               schedtypes.get('default')))
      protocol = backend_info.get('protocol', set.property('protocol'))

      backend_config = set.srv_mgr().config()

      # Error out if any of the segments have test mode set - this means
      # we were started with an invalid data.* file.
      if segment_data.DisallowTestMode() and \
         backend_config.var('SEGMENT_TEST_MODE'):
        raise Error, 'ERROR: set %s has SEGMENT_TEST_MODE set' % set.name()

      # Compute segment information.  We exclude balancers since they
      # don't want the segment information.
      segment = None
      if not self.isbaltype():
        segment = backend_info.get('segment', backend_config.var('SEGMENT'))

      config = self.srv_mgr().config()

      # Compute the statusz port for servers that can handle it.
      # If balancer processes are separate do not set the single status
      # port since each balancer may have different status ports.
      # Instead just use the serving port.  TODO: If we ever use
      # separate balancer processes in general, and not just the
      # specialized case for blimpie, we'll have to revisit this
      # code since we have the potential for status port conflicts.
      statusz_port = backend_info.get('statusz_port', 0)   # override?
      if set.property('supports_http_statusz') and not statusz_port:
        # Get a statusz port per-type. This is *not* fully accurate as
        # the statusz port is a property of the backend not a property
        # of the type. But ... the statusz support in the binaries was
        # placed in --shardinfo instead of --backends so we are kinda
        # stuck for now.
        # Note: we use the *real* port not minport to catch mixers
        #       which serve on 4000 for gws purposes.
        # TODO: reimplement this when --shardinfo is cleaned up
        if not statusz_port:
          servers = set.ServersForPort(set.PortBase())
          if servers:
            statusz_port = servers[0].statuszport()

      # These are hard coded mixer values.  Ultimately it will be better
      # to really have these explicitly set and constraint verified
      # but for now for backwards compatibility, set them here.
      if self.servertype() == 'mixer':

        # Default to round robin for non-balancer backends to mixer.
        if not sched and not set.isbaltype():
          sched = 'rr'

        # If inmemory to index we hard code some settings.
        # TODO: It's probably better to get rid of this hardcoding
        # at some point and go with explicit settings.
        if mtype == 'index' and config.var('INMEMORY_INDEX').get(level):
          if not backend_info.get('schedtype'):
            sched = 'rr'
          if not backend_info.get('numconn'):
             num = 3

      # Hack to support dual form of LCA, Link, Related servers.
      if config.var('USE_SORTED_MAP_SERVER').get(mtype):
        protocol = 'http'

      # Another horrible bigindex hack.  We need mixer shardinfo for bigindex
      # to contain both index shard specifications.  The current shardinfo
      # structure is a hashtable on typelvl, so it's impossible to add
      # to different index specs.  We do this by hacking index2 to
      # to be converted to index in serverflags.py.
      if set.name() == '+index2': mtype = 'index2'

      # Horrible bigindex hack to convert from regular types to
      # bigindex types.  This was done because from the mixer point
      # of view, it was easiest to just add a new servertype.  From
      # the babysitter point of view, this was considered bad
      # so we come to this.
      if backend_info.get('bigindex'):
        bigindex_mtype = 'big%s' % mtype
        if serverflags.ShortType(bigindex_mtype): mtype = bigindex_mtype

      typelvl = '%s:%s' % (mtype, level)

      shardinfo.set_min_port(typelvl, segment,
                             servertype.GetServingPort(minport))
      shardinfo.set_max_port(typelvl, segment,
                             servertype.GetServingPort(maxport))
      shardinfo.set_num_conns(typelvl, segment, num)
      if sched: shardinfo.set_schedule_type(typelvl, segment, sched)
      if protocol: shardinfo.set_protocol(typelvl, segment, protocol)
      if statusz_port: shardinfo.set_statusz_port(typelvl, segment,
                                                  statusz_port)
      if segment != None: shardinfo.set_segment(typelvl, segment)

      if use_versions:
        data_version = set.property('data_version')
        if data_version is None:
          raise Error, 'ERROR: data version is not set for %s' % typelvl
        shardinfo.set_data_version(typelvl, segment, data_version)

      # Filter by ports if requested.
      if backend_info.get('per_shard', 0) and port:
        # We accept a list because of a hack with balancers for translation
        # to balance multiple different ports.
        ports = port
        if type(port) != types.ListType:
          ports = [port]
        servers = []
        for port in ports:
          shard = self.Shard(port)
          servers.extend(set.ServersForPort(set.PortBase() + shard))
      else:
        servers = set.Servers()

      # Add backends.
      for server in servers:
        backends.AddBackend(server.host(),
                            servertype.GetServingPort(server.port() + offset),
                            level, mtype, segment)

    return (shardinfo, backends)

#
# ServerManager
#
# Manages a set of servers forming a serving configuration.  Allows
# you to examine and query the servers as well as methods for
# modifying the server sets.
#
# Note: This class is the replacement for all the deprecated server related
# methods in googlconfig/configutil.
#
class ServerManager:

  def __init__(self):

    # Config object reference (if loaded from a config).
    self.config_ = None
    # Constraint manager reference.
    self.cnstr_mgr_ = None

    # Properties of this server manager.
    self.properties_ = {}
    # Sets that are auto assigned.
    self.auto_assign_sets_ = {}
    # Determine whether to auto assign servers.
    self.auto_assign_ = 0
    # Determine whether to auto assign rfservers.
    self.auto_assign_rfservers_ = 0

    # List of servers.
    self.servers_ = []
    # Map of hosts to server lists.
    self.host2servers_ = {}
    # Map of setnames to sets.
    self.sets_ = {}
    # Map of replica setnames to replica sets.
    self.rep_sets_ = {}

  def InitFromConfig(self, config):
    """Initialize server manager from config object.
    Args:
      config: googleconfig.Config - config object.
    """
    self.config_ = config

    # TODO: Project/Service transition.  As we transition
    # to not depending on PROJECT, we will set the PROJECT
    # name to what is specified in the config file if that
    # is available.  Otherwise we pull it from the
    # services file name.  Ultimately, we will be removing
    # support for both the PROJECT variable and the 'project'
    # server property specified below.
    self.set_property('service', config.GetServiceName())
    if config.has_var('PROJECT') and config.var('PROJECT'):
      self.set_property('project', config.var('PROJECT'))
    else:
      self.set_property('project', config.GetServiceName())
    if config.has_var('OWNER'):
      self.set_property('owner', config.var('OWNER'))
    if config.has_var('COLOC'):
      self.set_property('coloc', config.var('COLOC'))
    if config.has_var('LOCAL_FREE_POOL'):
      self.set_property('free_pool', config.var('LOCAL_FREE_POOL'))

    if config.var('BALANCER_SEPARATE_PROCESSES', 0):
      self.set_property('balancer_separate_processes', 1)

    if config.has_var('AUTO_ASSIGN_SETS'):
      self.auto_assign_sets_ = config.var('AUTO_ASSIGN_SETS')
      # Do some sanity checking on the auto assigned sets.
      # We disallow an auto assigned type to ever serve as a key.
      keys = self.auto_assign_sets_.keys()
      for assigned_sets in self.auto_assign_sets_.values():
        for assigned_set in assigned_sets:
          if assigned_set in keys:
            raise Error, 'Assigned set %s cannot have assigned servers' % \
                          assigned_set

    # TODO: Deprecate the following.
    if config.var('USE_AUTOASSIGN_MAP', 1):
      self.auto_assign_ = 1

    if config.var('AUTO_ASSIGN_RFSERVERS', 1):
      if config.var('GFS_ALIASES', ''):
        self.auto_assign_rfservers_ = 'gfs'
      else:
        self.auto_assign_rfservers_ = 'nongfs'

    if config.has_var('SERVERS'):
      self.InitFromServerMap(config.var('SERVERS'))

    if config.has_var('SERVER_SETS'):
      server_sets = config.var('SERVER_SETS', {})
      for (srvset, properties) in server_sets.items():
        # Set properties.
        if srvset == 'default':
          # TODO: Comment out reading of default properties till
          # we can have consensus on whether we will use it or not.
          for (key, val) in properties.items():
            if key not in servertype.GetNonOverridableServerProperties():
              self.set_property(key, val)
        else:
          set = self.Set(srvset)
          if not set: continue
          for (key, val) in properties.items():
            set.set_property(key, val)

    for set in self.Sets():

      srcset = set

      if set.isbaltype():
        # Find the balanced set by examining the backends property
        # of the balancer set.  We don't call balsrvset since that
        # may give us the balanced type (with the serve_as override).
        srcset = self.Set(set.property('backends')[0]['set'])

        # Set properties that are passed through to balancers.
        for prop in servertype.GetBalancerPassThroughProperties():
          set.set_property(prop, srcset.property(prop))

      # Set the data version and data dir.
      set.set_property('data_version', '')
      if config.has_var('DATA_DIRS') and set.property('supports_dataversion'):
        # To keep backwards compatibility, for now ignore errors.
        try:
          set.set_property('data_version',
                           config.GetDataVersion(srcset.typelvl()))
        except (NameError, RuntimeError):
          pass

    # Set the binrepo.
    if config.has_var('BINREPO'):
      binrepo = config.var('BINREPO')
    elif config.has_var('INDEXNAME'):
      binrepo = config.var('INDEXNAME')
    else:
      binrepo = 'production'

    self.set_property('binrepo', binrepo)

    # Save the config directory of the config for referencing
    # backend sets.
    self.set_property('config_dir', config.GetConfigDir())

  # Initialize from a server map object.
  def InitFromServerMap(self, srvmap):
    self.__construct(srvmap)

  # Get server/balancer maps.  This is for backwards compatibility.
  def ServerMaps(self, wanted_types=None, auto_assigned=0):

    if wanted_types is None: wanted_types = {}

    srvmap = {}
    balmap = {}
    repmap = {}

    for set in self.Sets():

      # Ignore auto assigned sets.
      if not auto_assigned and set.property('auto_assigned', 0):
        continue

      for port in set.Ports():
        srvmap[port] = srvmap.get(port, [])
        for server in set.ServersForPort(port):
          if server.isbal():
            append_dictlist(balmap, port, server.host())
            if not self.property('balancer_separate_processes'):
              if server.host() not in srvmap.get(server.balport(), []):
                append_dictlist(srvmap, server.balport(), server.host())
          else:
            append_dictlist(srvmap, port, server.host())

    for set in self.ReplicaSets():
      if not auto_assigned and set.property('auto_assigned', 0):
        continue
      for port in set.Ports():
        for server in set.ServersForPort(port):
          append_dictlist(repmap, port, server.host())

    srvmap = filter_server_map(srvmap, wanted_types)
    balmap = filter_server_map(balmap, wanted_types)
    repmap = filter_server_map(repmap, wanted_types)

    return (srvmap, balmap, repmap)

  # Get combined server map.  This is for backwards compatibility.
  def CombinedServerMap(self, wanted_types = {}, auto_assigned = 0):

    servers = {}
    (srvmap, balmap, repmap) = self.ServerMaps(wanted_types = wanted_types,
                                               auto_assigned = auto_assigned)

    for port in srvmap.keys():

      # Do not add balancer ports since these are reflected with the '+'
      # on the balanced port.
      if servertype.IsBalancerType(servertype.GetPortType(port)):
        continue

      srvs = srvmap.get(port, [])
      bals = balmap.get(port, [])
      reps = repmap.get(port, [])
      for i in xrange(len(reps)):
        if i >= len(srvs):
          break
        srvs[i] = '%s+%s' % (srvs[i], reps[i])
      servers[port] = map(lambda x: '+%s' % x, bals) + srvs
    return servers

  def config(self):
    """Get config object."""
    return self.config_

  def property(self, key, dflt=None):
    """Get a default property setting for server sets.
    Args:
      key: 'string' - the name of the property.
      dflt: any - any default value.
    Returns:
      value: any - the value of the property.

    This is used to set a default value for all sets in this server manager.
    """
    return self.properties_.get(key, dflt)

  def set_property(self, key, val):
    if key in servertype.GetNonOverridableServerProperties():
      raise KeyError, 'Server property %s is non-overridable.' % key
    self.properties_[key] = val

  # Get constraint manager.
  def constraint_mgr(self):
    # TODO: I'm planning on merging constraint variable data into SERVER_SETS.
    # Once that is done we don't really need the handle to the config object
    # and the constraint manager can be created based on data in this server
    # manager.  I'm doing it this way for now since I don't want to add a
    # dependency on the machinelib till machinedb is integrated into prod
    # release branch.
    if self.cnstr_mgr_: return self.cnstr_mgr_

    from google3.enterprise.legacy.production.assigner import constraintlib
    self.cnstr_mgr_ = constraintlib.ConstraintManager()
    self.cnstr_mgr_.LoadConstraints(self.config_)

    # Preload machine information.
    self.cnstr_mgr_.mach_mgr().MachineList(self.Hosts(), load_hardware=1,
                                            load_uses=1)

    return self.cnstr_mgr_

  # Get list of server objects.  The list can be pruned by
  # wanted sets, wanted ports, wanted indices, wanted hosts.
  #
  # The argument types may be:
  #   a string or list as accepted by prodlib.CollectTypes OR
  #   a dictionary as a result of calling prodlib.CollectTypes
  #
  # We accept both types for convenience and backwards compatibility.
  # Many scripts call this having already converted the argument strings.
  # However, it is more convenient usually to not have the caller
  # have to worry about this.
  def Servers(self, wanted_sets=None, wanted_ports=None, wanted_indices=None,
              wanted_hosts=None):

    def convert_arg(arg):
      """Convert argument to dictionary type as produced by
         prodlib.CollectTypes"""
      if arg is None: arg = {}
      if type(arg) != types.DictionaryType:
        arg = prodlib.CollectTypes(arg, {})
      return arg

    # Convert arguments to proper format.
    wanted_sets = convert_arg(wanted_sets)
    wanted_ports = convert_arg(wanted_ports)
    wanted_indices = convert_arg(wanted_indices)
    wanted_hosts = convert_arg(wanted_hosts)

    # Quick exit if no pruning set.
    if not wanted_sets and not wanted_ports and not wanted_indices and \
       not wanted_hosts:
      return self.servers_

    servers = []

    for set in self.Sets():
      # Ensure this is a wanted set - we support either the
      # setname match or servertype match if it's a balancer type.
      # This is for backwards compatibility with previous wanted type versions.
      setlvl = '%s:%s' % (set.name(), set.level())
      typelvl = '%s:%s' % (set.servertype(), set.level())
      if (not prodlib.WantedType(setlvl, wanted_sets) and
          (not set.isbaltype() or
           not prodlib.WantedType(typelvl, wanted_sets))):
        continue
      for port in set.Ports():
        # Ensure this is a wanted port.
        if not prodlib.WantedType(str(port), wanted_ports):
          continue
        for server in set.ServersForPort(port):
          # Ensure these are wanted indices.
          if not prodlib.WantedType(str(server.index()), wanted_indices):
            continue
          if not prodlib.WantedType(server.host(), wanted_hosts):
            continue
          servers.append(server)

    return servers

  # Get list of hostnames.
  def Hosts(self):
    return self.host2servers_.keys()

  # Get list of servers for given name.  Name is a string of
  # the form 'host' or '[+]host:port'.  This method will parse
  # the string and lookup the corresponding servers.
  def ServersForSpec(self, spec):
    if string.find(spec, ':') == -1:
      return self.ServersForHost(spec)
    tmp = Server()
    tmp.InitFromName(spec)
    servers = self.host2servers_.get(tmp.host(), [])
    for server in servers:
      if tmp == server:
        return [server]
    return []

  # Get list of servers for given hostname.
  def ServersForHost(self, host):
    return self.host2servers_.get(host, [])

  # Get list of server sets.
  def Sets(self):
    return self.sets_.values()

  # Get a server set.
  def Set(self, srvset):
    return self.sets_.get(srvset)

  # Add a server set if not already present.
  def AddSet(self, name, lvl):
    set = self.sets_.get(name)
    if not set:
      set = ServerSet(self, name, lvl)
      self.sets_[name] = set
    return set

  # Remove a server set.
  def RemoveSet(self, name):
    # TODO: this should remove each individual server first.
    del self.sets_[name]

  # Get full set specification.
  def BackendSet(self, setspec, consider_bals = 1):
    spec = string.split(setspec, ':')
    if len(spec) == 1:
      srv_mgr = self
      srvset = setspec
    elif len(spec) == 2:
      (service, srvset) = spec
      factory = masterconfig.Factory(self.property('coloc'),
                                     config_dir=self.property('config_dir'))
      srv_mgr = factory.GetConfigs(service)[0].GetServerManager()
    elif len(spec) == 3:
      (coloc, service, srvset) = spec
      factory = masterconfig.Factory(coloc,
                                     config_dir=self.property('config_dir'))
      srv_mgr = factory.GetConfigs(service)[0].GetServerManager()
    else:
      raise ValueError('Invalid set spec: %s' % setspec)

    if consider_bals:
      set = srv_mgr.Set('+%s' % srvset)
      if set and set.Servers(): return set
    return srv_mgr.Set(srvset)

  # Replace a server's host with the given host.  Note: the
  # server object that is passed in is actually modified to
  # have the updated host.  Use this method instead of setting
  # the host field directly as the internal maps of the
  # manager must be updated.
  def ReplaceServer(self, server, host):
    remove_dictlist(self.host2servers_, server.host(), server)
    append_dictlist(self.host2servers_, host, server)
    set = self.Set(server.srvset())
    set.ReplaceServer(server, host)
    for assigned_server in server.auto_assigned_servers():
      self.ReplaceServer(assigned_server, host)

  # Adds a server.  Updates internal data structures.
  def AddServer(self, server):
    self.servers_.append(server)
    append_dictlist(self.host2servers_, server.host(), server)
    set = self.AddSet(server.srvset(), server.level())
    set.AddServer(server)
    if self.property('balancer_separate_processes', 0):
      server.set_balport(server.port())

    # Add auto assigned servers
    assigned_setnames = self.auto_assign_sets_.get(set.name(), [])
    for assigned_setname in assigned_setnames:

      # Add the auto assigned set.
      assigned_set = self.AddSet(assigned_setname, 0)
      assigned_set.set_property('auto_assigned', 1)

      # Determine the appropriate port for the balancer.
      if assigned_set.isbaltype():
        mtype = assigned_set.name()[1:]
      else:
        mtype = assigned_set.servertype()
      try:
        if assigned_setname == 'rfserver':
          # TODO: Remove this hardcoding either by changing crawl
          # to use 3851 or moving up rfserver port base to 3899.
          port_base = servertype.GetDefaultRFServerPort()
        else:
          port_base = servertype.GetPortBase(mtype)
      except KeyError:
        raise Error, 'Invalid setname for AUTO_ASSIGN_SETS: %s' % \
                     assigned_setname
      if servertype.IsSharded(mtype):
        port = port_base + set.Shard(server.port())
      else:
        port = port_base

      # Add the assigned server.
      assigned_server = Server()
      if assigned_set.isbaltype():
        srv_name = '+%s:%s' % (server.host(), port)
      else:
        srv_name = '%s:%s' % (server.host(), port)
      assigned_server.InitFromName(srv_name)
      server.auto_assigned_servers().append(assigned_server)
      self.AddServer(assigned_server)

  # Removes a server.  Updates internal data structures.
  def RemoveServer(self, server):
    self.servers_.remove(server)
    remove_dictlist(self.host2servers_, server.host(), server)
    set = self.Set(server.srvset())
    set.RemoveServer(server)
    for assigned_server in server.auto_assigned_servers():
      self.RemoveServer(assigned_server)
    server.set_auto_assigned_servers([])

  # Get string format of server set (saves as a dictionary).
  def AsString(self, auto_assigned = 0):

    # TODO: build this without relying on servertype.GetPortType.
    servers = self.CombinedServerMap(auto_assigned = auto_assigned)
    ret = []
    ret.append('{')
    ports = servers.keys()
    ports.sort()
    prv_mtype = None
    for port in ports:
      cur_mtype = servertype.GetPortType(port)
      if cur_mtype != prv_mtype:
        ret.append('\n  # %s' % string.upper(cur_mtype))
        prv_mtype = cur_mtype
      ret.append('%s%s : " %s ",' % (' ' * 2, port,
                                     string.join(servers[port], ' ')))
    ret.append('\n}')
    return string.join(ret, '\n')

  # Replica support.  Someday it would be nice to be free of this
  # concept - but here it is for now.

  # Get list of replica sets.
  def ReplicaSets(self):
    return self.rep_sets_.values()

  # Get a replica set.
  def ReplicaSet(self, srvset):
    return self.rep_sets_.get(srvset)

  # Add a replica set if not already present.
  def AddReplicaSet(self, name, lvl):
    set = self.rep_sets_.get(name)
    if not set:
      set = ServerSet(self, name, lvl)
      self.rep_sets_[name] = set
    return set

  # Remove a replica set.
  def RemoveReplicaSet(self, name):
    del self.rep_sets_[name]

  #
  # Private Methods.
  #

  # Create all internal data structures from the servermap.
  def __construct(self, srvmap):

    self.servers_ = []
    self.sets_ = {}
    self.rep_sets_ = {}
    self.host2servers_ = {}

    ports = srvmap.keys()
    ports.sort()

    prev_mtype = None  # used as a "hint" to GetPortType
    for port in ports:

      mtype = servertype.GetPortType(port, hint=prev_mtype)
      prev_mtype = mtype

      # Ignore balancers since we're processing the balancer map.
      if servertype.IsBalancerType(mtype): continue

      lvl = servertype.GetLevel(port)

      # Initialize sets here.  We don't initialize on demand during the
      # machine add phase since we would like sets added for any specified
      # ports even if there are no machines specified on those ports.
      # This is useful for the assigner (i.e. start with a blank
      # SERVERS map with only ports and empty strings specified).
      set = self.AddSet(mtype, lvl)
      set.AddPort(port)

      # Add servers.
      hosts = srvmap.get(port, [])
      if type(hosts) == types.StringType:
        hosts = string.split(hosts)

      for i in range(len(hosts)):

        host = hosts[i]
        replica = None

        # Drop -mach.
        if host[0] == '-': continue

        # Test for replicas.
        fields = string.split(host, '+')
        # we need to check len(fields[0]) > 0 to handle balancers which have
        # a '+' prefix and splitting them result in an empty fields[0]
        if len(fields) > 1 and len(fields[0]) > 0:
          # add the server and its replica
          host = fields[0]
          replica = fields[1]

        server = Server()
        server.InitFromName('%s:%s' % (host, port))
        self.AddServer(server)

        # Replica processing.
        if replica:
          server = Server()
          server.InitFromName('%s:%s' % (replica, port))
          set = self.AddReplicaSet(server.srvset(), lvl)
          set.AddServer(server)

    # Perform auto assignment
    self.__auto_assign()

    # For any balancer sets make sure we've added ports for all
    # ports in this type's port range.  This is just to support
    # shards without bals + some shards with bals - a very rare
    # occurrance - mostly only for some test setups.
    prev_mtype = None  # used as a "hint" to GetPortType
    for port in ports:
      mtype = servertype.GetPortType(port, hint=prev_mtype)
      prev_mtype = mtype
      set = self.Set('+%s' % mtype)
      if set:
        set.AddPort(port)

  # Automatically assign servers based on auto assign map and
  # assign rfservers settings.
  # TODO: REMOVE THIS CODE ONCE CONVERSION TO AUTO_ASSIGN_SETS IS COMPLETE
  def __auto_assign(self):

    def assign(mgr, assign2name, name2use, pri2use, rep2use,
               startfrom, stopat, singleport):

      # Get the number valid shards.
      n_shards = 0
      srcset = mgr.Set(name2use)
      if not srcset: return
      srcrepset = mgr.ReplicaSet(name2use)
      n_shards = srcset.NumShards()

      # Compute the start/stop shards.
      startfrom = int(startfrom * n_shards)
      if stopat > 0 and stopat <= 1:
        stopat = int(stopat * n_shards)
      else:
        stopat = stopat + 1

      # We want to stop either at the stop pattern or when we run out.
      stopat = min(stopat, n_shards)

      # Get the valid shards to map.
      for shard in xrange(startfrom, stopat):

        if singleport:
          shard = 0

        srcport = shard + srcset.PortBase()
        dstport = shard + servertype.GetPortMin(assign2name)

        # Find the primary on the source port.
        servers = srcset.ServersForPort(srcport)
        if not servers: continue
        primary = Server()
        primary.InitFromName('%s:%s' % (servers[0].host(), dstport))

        # Find the replica on the source port.
        if srcrepset and srcrepset.ServersForPort(srcport):
          servers = srcrepset.ServersForPort(srcport)
          replica = Server()
          replica.InitFromName('%s:%s' % (servers[0].host(), dstport))
        else:
          replica = None

        # Assign based on the map.
        if primary.host() == 'localhost':
          set = mgr.AddSet(assign2name, 0)
          set.set_property('auto_assigned', 1)
          set.AddServer(primary)
        else:
          if pri2use == 'primary':
            set = mgr.AddSet(assign2name, 0)
            set.set_property('auto_assigned', 1)
            set.AddServer(primary)
          elif pri2use != None and replica != None:
            set = mgr.AddSet(assign2name, 0)
            set.set_property('auto_assigned', 1)
            set.AddServer(replica)
          if rep2use == 'replica' and replica != None:
            set = mgr.AddReplicaSet(assign2name, 0)
            set.set_property('auto_assigned', 1)
            set.AddServer(replica)
          elif rep2use != None:
            set = mgr.AddReplicaSet(assign2name, 0)
            set.set_property('auto_assigned', 1)
            set.AddServer(primary)

    if self.auto_assign_:
      # TODO: REMOVE THIS CODE ONCE CONVERSION TO AUTO_ASSIGN_SETS IS COMPLETE
      # Automatically assign various servers on machines already assigned
      # explicitly before.  This auto assignment will not override
      # any servers already manually assigned.
      for name in servertype.GetAutoAssignMap().keys():
        (name2use, pri2use, rep2use, startfrom, stopat, singleport) = \
                   list(servertype.GetAutoAssignMap()[name])
        port2check = servertype.GetPortMin(name)
        set = self.Set(name)
        if not set or not set.ServersForPort(port2check):
          assign(self, name, name2use, pri2use, rep2use,
                 startfrom, stopat, singleport)

    if self.auto_assign_rfservers_:
      # TODO: REMOVE THIS CODE ONCE CONVERSION TO AUTO_ASSIGN_SETS IS COMPLETE
      # Automatically assign rfservers for specified types.
      if self.auto_assign_rfservers_ == 'gfs':
        has_gfs = 1
      else:
        has_gfs = 0
      mtypes = servertype.GetNeedRFServerTypes(has_gfs)
      hosts = {}
      for mtype in mtypes:
        set = self.Set(mtype)
        if set:
          for server in set.Servers(): hosts[server.host()] = 1
        set = self.ReplicaSet(mtype)
        if set:
          for server in set.Servers(): hosts[server.host()] = 1

      # Find the rfserver port and set to add to.
      if hosts:
        port = servertype.GetDefaultRFServerPort()
        set = self.AddSet('rfserver', 0)
        set.set_property('auto_assigned', 1)
        for host in hosts.keys():
          server = Server()
          server.InitFromName('%s:%s' % (host, port))
          set.AddServer(server)


#------------------------------------------------------------------------------
# useful functions
#------------------------------------------------------------------------------

def IsValidSetName(setname):
  """Test if a server set name is valid.
  Args:
    setname: 'name' - Set name to test.
  Returns:
    0|1 - returns 1 if is valid, else 0.
  """
  if not setname: return 0
  if setname[0] == '+': setname = setname[1:]
  return servertype.IsValidServerType(setname)

# Gets the servers that should be monitored at the given coloc and service.
# If the config file for the service is for the given coloc, return all the
# servers.  Otherwise, restrict them to the list of types that have
# the property "external_monitor" set to 1.
# If default_types_to_load is not None, it always load all the types given.
# If default_types_not_to_load is not None, it'll load all the types that
# should be loaded minus those in this list.  This list should looks like:
# ['-apache', '-related'].
# The return type is:
# { 'config': { port: [host] } }
#
def GetServersMonitoredForColocService(coloc, service, default_types_to_load,
                                       default_types_not_to_load):
  config_mach_dict = {}
  factory = masterconfig.Factory(coloc)
  configs = factory.GetConfigs(service)
  for config in configs:
    types_to_load = default_types_to_load
    srv_mngr = config.GetServerManager()

    # if it ends of .coloc, find the coloc
    if config.has_var('COLOC'):
      config_coloc = config.var('COLOC')
    else:
      # pretend it is at the right coloc
      # TODO: remove this case.  We should fix all config files and remove
      # this test.
      config_coloc = coloc

    if types_to_load == None:
      if config_coloc != coloc:
        # restrict to set that has external_monitor property set to i
        types_to_load = []
        for set in srv_mngr.Sets():
          external_monitor = set.property('external_monitor', 0)
          if external_monitor:
            types_to_load.append(set.servertype())

    # nothing?  skip
    if types_to_load == []:
      continue

    if types_to_load == None:
      types_to_load = []

    # remove types that we do not want
    if default_types_not_to_load != None:
      types_to_load.extend(default_types_not_to_load)

    t = servertype.CollectTypes(types_to_load, {})

    # get old style server map from server manager limited to types.
    machs = srv_mngr.CombinedServerMap(wanted_types = t, auto_assigned=1)

    # Return the machines, indexed by the Config object
    config_mach_dict[config] = machs

  return config_mach_dict


#------------------------------------------------------------------------------
# Utility Methods
#------------------------------------------------------------------------------

#
# These should probably go into a "set"/"list" operation library - we
# should make a standard lib.
#

# Assuming lists are ordered, it determines whether all the elements
# of list1 are found in list2.
def is_contained(list1, list2):
  len1 = len(list1)
  len2 = len(list2)
  if len2 < len1: return 0
  j = 0
  for i in range(len1):
    match = 0
    for j in range(j, len2):
      if list1[i] == list2[j]:
        j = j+1
        match = 1
        break
    if not match: return 0
  return 1

# Append to a list in dictionary.  Creates list if not present.
def append_dictlist(dict, key, val):
  vals = dict.get(key, [])
  vals.append(val)
  dict[key] = vals

# Remove from a list in dictionary.  Delete list if empty.
def remove_dictlist(dict, key, val):
  dict[key].remove(val)
  if dict[key] == []:  del(dict[key])

# Given a server map of { port : "hosts", ... } where
# hosts are a list of hosts, filter to only the wanted types.
#
# servers: { port : "hosts", ... } dictionary.
# wanted_types: array from servertype.CollectTypes. {} indicates all.
#
# Returns a filtered server map of { port : "hosts", ... }.
# Returns the original map if wanted_types is empty.
# If it filters, it will return a map with the original host lists
# (does not copy the host lists).
def filter_server_map(servers, wanted_types = {}):
  if not wanted_types:
    return servers
  ret = {}
  for (port, hosts) in servers.items():
    typelvl = servertype.GetTypeLevel(port)
    if not prodlib.WantedType(typelvl, wanted_types): continue
    ret[port] = hosts
  return ret

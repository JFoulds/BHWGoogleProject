#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
# Author: Anurag Acharya
#
# Implements the shardinfo and backends classes.
# Makes it easy to generate shardinfo/backends arguments for various servers.
#
# Example usage:
#   shardinfo = serverflags.ShardInfo()
#   backends = serverflags.Backends()
#   for port, hosts in servers.items():
#      typelvl = typelevel(port)
#      (mtype, lvl) = splittypelvl(typelvl)
#      baseport = portbase(typelvl)               # needed by balancers
#      maxport = baseport + numshards[typelvl] - 1)
#      balconns = balconnsmap.get(typelvl, scope['DEFAULT_BALANCER_NUMCONNS'])
#
#      for host in hosts:
#        backends.AddBackend(host, port, lvl, mtype)
#     shardinfo.set_min_port(typelvl, segment, baseport)
#     shardinfo.set_max_port(typelvl, segment, maxport)
#     shardinfo.set_num_conns(typelvl, segment, balconns)
#   args = " --backends=%s --shardinfo=%s" %  \
#          (backends.AsString(), shardinfo.AsString())
#
#

import string
import sys

# Hack to enable circular imports
import google3.enterprise.legacy.setup
google3.enterprise.legacy.setup.serverflags = sys.modules[__name__]

# to parse typelvl-s (servertype imports serverflags too!)
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.setup import prodlib      # for DNS lookups
import socket

# Try to fully qualify hostname if we can.
# This is mostly for Java processes that use XBill DNSJava.
# see bug 162191.
def TryQualifyHostnameFully(host):
  if prodlib.IsIP(host):
    # This is necessary in cases where a process is configured to talk
    # to specific nameservers, and cannot resolve internal names.
    # They must be handed IPs instead. Bot is a special case like this.
    return host
  else:
    return socket.getfqdn(host)

# Method for generating an arg string from a list of (host, port) tuples.
# The string is generated in the form "host:port,host:port,...".
def MakeHostPortsArg(hostports, sep=',', qualify=1):
  if qualify == 1:
    return string.join(map(lambda x: '%s:%s' % ( TryQualifyHostnameFully(x[0]),
                                                 x[1] ),
                           hostports), sep)
  else:
    return string.join(map(lambda x: '%s:%s' % ( x[0], x[1] ),
                           hostports), sep)

class ShardInfo :
  def __init__(self):
    self.shardinfo_map_ = {}

  # Maps typelvl as known by servertype.py to (<short_type>, <lvl>) pair
  # expected format of typelvl is "<type>:<lvl>"
  def ConvertTypeLevel(self, typelvl):
    from google3.enterprise.legacy.production.babysitter import servertype   # to parse typelvl-s (servertype imports serverflags too!)
    (mtype, lvl) = servertype.SplitTypeLevel(typelvl)
    stype = ShortType(mtype)
    if not stype:                   # we don't know about this type
      raise RuntimeError, "Invalid type %s in %s" % (mtype, typelvl)
    if lvl < 0:                     # we don't know no negative levels :)
      raise RuntimeError, "Invalid level %d in %s" % (lvl, typelvl)

    return (stype, lvl)

  # internal class to record information for a single shard
  class OneShard :
    def __init__(self):
      # required values - set to invalid values
      self.server_type_ = "unknown"
      self.min_port_ = -1
      self.max_port_ = -1
      self.level_ = -1
      # optional values
      self.num_conns_ = ""
      self.data_version_ = ""
      self.binary_version_ = ""
      self.schedule_type_ = ""
      self.protocol_ = ""
      self.statusz_port_ = ""
      self.segment_ = None

    def set_server_type(self, server_type):
      self.server_type_ = server_type
    def set_min_port(self, min_port):
      self.min_port_ = min_port
    def set_max_port(self, max_port):
      self.max_port_ = max_port
    def set_level(self, level):
      self.level_ = level
    def set_num_conns(self, num_conns):
      self.num_conns_ = num_conns
    def set_data_version(self, data_version):
      self.data_version_ = data_version
    def set_binary_version(self, binary_version):
      self.binary_version_ = binary_version
    def set_schedule_type(self, schedule_type):
      self.schedule_type_ = schedule_type
    def set_protocol(self, protocol):
      self.protocol_ = protocol
    def set_statusz_port(self, statusz_port):
      self.statusz_port_ = statusz_port
    def set_segment(self, segment):
      self.segment_ = segment
    def AsString(self):
      # make sure required values have been initialized
      if self.server_type_ == "unknown":
        raise RuntimeError, "Uninitialized server type"
      if self.level_ == -1:
        raise RuntimeError, "Uninitialized level"
      if self.min_port_ <= 0:
        raise RuntimeError, "Invalid min_port %d" % self.min_port_
      if self.max_port_ <= 0:
        raise RuntimeError, "Invalid max_port %d" % self.max_port_
      if self.min_port_ > self.max_port_:
        raise RuntimeError, "min port (%d) must be <= max_port (%d)" \
              % (self.min_port_, self.max_port_)
      servertype_spec = GetServerTypeSpec(self.server_type_,
                                          self.level_,
                                          self.segment_)
      return "%s:%s:%s:%s:%s:%s:%s:%s:%s" % (servertype_spec,
                                             self.min_port_,
                                             self.max_port_,
                                             self.data_version_,
                                             self.binary_version_,
                                             self.num_conns_,
                                             self.schedule_type_,
                                             self.protocol_,
                                             self.statusz_port_)

  def GetShard(self, typelvl, segment):
    if not self.shardinfo_map_.has_key( (typelvl, segment) ):
      shard_desc = ShardInfo.OneShard()
      (stype, lvl) = ShardInfo.ConvertTypeLevel(self, typelvl)
      shard_desc.set_server_type(stype)
      shard_desc.set_level(lvl)
      self.shardinfo_map_[ (typelvl, segment) ] = shard_desc
    return self.shardinfo_map_[ (typelvl, segment) ]

  def HasShard(self, typelvl, segment):
    return self.shardinfo_map_.has_key( (typelvl, segment) )

  def set_min_port(self, typelvl, segment, min_port):
    if min_port <= 0:
      raise RuntimeError, "Invalid min_port %d" % min_port
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_min_port(min_port)

  def set_max_port(self, typelvl, segment, max_port):
    if max_port <= 0:
      raise RuntimeError, "Invalid max_port %d" % max_port
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_max_port(max_port)

  def set_num_conns(self, typelvl, segment, num_conns):
    if num_conns <= 0:
      raise RuntimeError, "Invalid num_conns %d" % num_conns
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_num_conns(num_conns)

  def set_data_version(self, typelvl, segment, data_version):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_data_version(data_version)

  def set_binary_version(self, typelvl, segment, binary_version):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_binary_version(binary_version)

  def set_schedule_type(self, typelvl, segment, schedule_type):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_schedule_type(schedule_type)

  def set_protocol(self, typelvl, segment, protocol):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_protocol(protocol)

  def set_statusz_port(self, typelvl, segment, statusz_port):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_statusz_port(statusz_port)

  def set_segment(self, typelvl, segment):
    shard_desc = ShardInfo.GetShard(self, typelvl, segment)
    shard_desc.set_segment(segment)

  def AsString(self):
    # generate a shardinfo description for all shards in our map
    shardinfo_strings = []
    for key in self.shardinfo_map_.keys():
      shardinfo_strings.append(self.shardinfo_map_[key].AsString())

    # For regression testing purposes, sort to give
    # a deterministic order.
    shardinfo_strings.sort()

    return string.join(shardinfo_strings, ",")

class Backends:
  def __init__(self):
    # Map of (shorttype, port, level, segment) -> host names on that shard.
    self.backends_ = {}
  def AddBackend(self, host, port, level, server_type, segment):
    # Thanks to preprod sandbox support, the level *is* out-of-sync
    # with the port in --sandbox mode. So ... we can't assert. :-(
    #
    ##assert level == servertype.GetLevel(port), \
    ##       "BUG: level (%s) inconsistent with port (%s)" % (level, port)

    shorttype = ShortType(server_type)
    backendkey = (shorttype, port, level, segment)
    backends = self.backends_.get(backendkey, [])
    backends.append(host)
    self.backends_[backendkey] = backends

  def NumBackEnds(self):
    # count backends by summing up the length of the backend lists
    return reduce(lambda x,y: x+len(y), self.backends_.values(), 0)

  # simple emptiness check. Should be used instead of NumBackEnds()
  # if only boolean info is needed (less expensive)
  def HasBackEnds(self):
    return (self.backends_ != {})  # != so we can force a boolean reply

  def AsString(self):
    if not self.backends_:
      raise TypeError

    # For regression testing purposes, sort to give
    # a deterministic order.  We group by type/level/port but
    # preserve the ordering of backends within this group based
    # on the "AddBackend" order.  This is important for determining
    # primary/backup balancers for example.

    backends = []
    shards = self.backends_.keys()
    shards.sort()

    for shardkey in shards:
      (shorttype, port, level, segment) = shardkey
      hosts = self.backends_[shardkey]   # raises IndexError if key is missing
      for host in hosts:
        # Disable IP lookups for now. The standard balancers can't handle it.

        ## # lookup the IP so the backends don't have to. The babysitter
        ## # uses a caching DNS anyway.
        ## (fullname, aliaslist, ipaddrlist) = prodlib.DNSLookup(host)
        ## if ipaddrlist:
        ##   ip = ipaddrlist[0]
        ##   ipstr = ":%s" % ipaddrlist[0]
        ## else:
        ##   # DNS lookup error. Skip the IP field completely.
        ##   ipstr = ""
        ipstr = ""
        host = TryQualifyHostnameFully(host)
        # add the backend spec
        servertype_spec = GetServerTypeSpec(shorttype, level, segment)
        backends.append('%s%s:%s:%s' % (host, ipstr, port, servertype_spec))

    return string.join(backends, ",")

# For internal use and unittests use only. DO NOT call directly!
def short_type_map():
  # map for moving standard types to the short server types
  # shardinfo uses. This needs to stay in sync with definitions
  # in google2/clients/serverflags.{h,cc}
  SERVER_TYPE_MAP = {
    "mixer" : "mi",
    "mergeserver" : "mr",
    "index" : "i",
    "index2" : "i",
    "doc"  : "d",
    "docfetch" : "df",
    "related" : "r",
    "ad"  : "a", # TODO: Remove once removed from serverflags.cc
    "cache" : "c",
    "onebox" : "o",
    "lexserver" : "l",
    "adpinger" : "ap",
    "translation" : "tr",
    "lcaserver" : "lca",
    "link" : "ln",
    "imagedoc" : "m",
    "directory" : "di",
    "headrequestor": "hr",
    "authzchecker" : "authz",
    "adslater" : "adl", # TODO: Remove once removed from serverflags.cc
    "admixer" : "adm",
    "adshard" : "ads",
    "deli_adshard" : "dads",
    "adexperiment" : "ade",
    "anchor" : "an",
    "dupserver" : "dup",
    "rtdupserver" : "rtdup",
    "urlhistory_processor": "rthist",
    "forwardmap": "fwdmap",
    "base_indexer": "bidx",
    "contentfilter" : "ctf",
    "urlmanager" : "urlm",
    "scanjpg3" : "sjpg3",
    "scanjpg2" : "sjpg2",
    "scanjpg6" : "sjpg6",
    "scanjpg20" : "sjpg20",
    "scaninfo" : "sinf",
    "oneboxnews" : "obnews",
    "oneboxwpres" : "obwpres",
    "oneboxwpbiz" : "obwpbiz",
    "oneboxspell" : "obsp",
    "oneboxsage" : "obsage", # TODO: Remove once removed from serverflags.cc
    "oneboxlocal" : "oblocal",
    "oneboxenterprise" : "obent",
    "odpcat"  : "obodp",
    "phil"  : "phil",
    "spellmixer" : "spellmix",
    "cafe" : "cafe",
    "content_ad_mixer": "cam",
    "content_ad_shard": "cas",
    "caanchor_server": "caa",
    "rtserver"  : "rt",
    "ffe" : "ffe",
    "kwls"  : "kwls",
    "kwls-mixer" : "kwlsm",
    "froogle_imgfreq_server" : "ifreq",
    "froogle_imgdoc" : "fd",
    "froogleimgproxy" : "fips",
    "hlserver"  : "hls",
    "netmon" : "nm",
    "concentrator": "con",
    "global_hostid2ip" : "gh2ip",
    "urlfiledataserver" : "ufds",
    "categorymapserver": "category",
    "prserver" : "prs",
    "hostid2ip_server" : "h2ips",
    "linkdrop_server" : "lnds",
    "siteid2data_server" : "s2ds",
    "urlfp2siteid_server" : "u2ss",
    "normalhttp" : "nhttp",
    "mysql" : 'sq',
    "filesyncmain" : "fsm",
    "qrewrite" : "qr",
    "geomap" : "gm",
    "twiddleserver" : "tw",
    "gfe_backend_server" : "gfeb",
    "gslb" : "gslb",
    "denial_of_service_server" : "dos",
    "sorted-map-server" : "sms",
    "bigindex" : "bi",
    "bigindex2" : "bi",
    "bigdoc" : "bd",
    "biglink" : "bl",
    "bigcache" : "bc",
    "bigmixer" : "bm",
    "fastnetserver": "fns",
    "fastnetindex" : "fni",
    "fastnetarchive" : "fna",
    "fastnetfetcher" : "fnf",
    "pred-shard" : "preds",
    "pred-mixer" : "predm",
    "urltracker_server" : "urlt",
    "refinementserver" : "refine",
    "hrserver" : "hrs",
    "pageranker" : "pr",
    "newsarticle_logprocessor" : "nalp",
    "prserver" : "prs",
    "hostid2ip_server" : "h2ips",
    "linkdrop_server" : "lnds",
    "gaiastorage" : "gss",
    "gaiaserver" : "gs",
    "oneboxdefinition" : "obdef",
    "siteid2data_server" : "s2ds",
    "urlfp2siteid_server" : "u2ss",
    "news_imgdoc_server" : "nid",
    "news_imglink_server" : "niln",
    "deli_feederfunnel_server" : "dff",
    "news_front_end" : "nfe",
    "smartass-server" : "sas",
    "smartass-lookup-server" : "sls",
    "groups2_facetserver" : "g2facet",
    "clustering_server" : "entclstr",
    "ent_fedroot" : "sr",
    "sessionmanagerserver" : "sm",
    "fsgw" : "entfg",
    "registryserver" : "reg",
  }

  return SERVER_TYPE_MAP


# computes the shardinfo-ready short type: 'index' -> 'i'. Includes a
# number of pretty ugly babysitter-level hacks to make things work properly.
# TODO: clean this up
def ShortType(longtype):
  SERVER_TYPE_MAP = short_type_map()

  # rtmains & rtsubordinates are just rtservers.  cpp end has no notion of these
  # babysitter types that essentially wrap rtservers.
  SERVER_TYPE_MAP["rtmain"] = SERVER_TYPE_MAP["rtserver"]
  SERVER_TYPE_MAP["rtsubordinate"] = SERVER_TYPE_MAP["rtserver"]

  return SERVER_TYPE_MAP.get(longtype, None)


# Helper function to compute "<lvl><shorttype>[+<segment>] specs as
# required by the binaries.
def GetServerTypeSpec(shorttype, level, segment):
  servertype_spec = "%s%s" % (level, shorttype)
  if segment != None:
    servertype_spec = "%s+%s" % (servertype_spec, segment)
  return servertype_spec

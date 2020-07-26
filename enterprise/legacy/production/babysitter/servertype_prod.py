#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# servertype_prod.py and servertype_crawl.py contain the command line arguments
# for Enterprise servers monitored by Babysitter. It is not as scary as it
# looks! Read on...
#
# In a nutshell, each server has a restart function like:
#
#   def restart_foo(config, host, port)
#
# that returns a restart command as a string. Immediately after each restart_*
# function there is a command:
#
#   servertype.RegisterRestartFunction('foo', restart_foo)
#
# Which registers it with servertype.
#
# 'host' is a string hostname, such as 'ent1'
# 'port' is the integer port number.
# 'config' is an EntConfig (entconfig.py) object, which contains a giant
# dictionary (config.var) of global Enterprise parameters. These parameters are
# used to help construct a command line.
#
# Items in the config.var dictionary are built from the following files:
# enterprise/legacy/config/config.default
# enterprise/legacy/config/config.default.enterprise.m4
# enterprise/legacy/adminrunner/entconfig.py, see update_derived_info()
#
# To actually get Babysitter to run a server you will need to look at
# servertype_data.py
#
# Recommendations:
# - Do not import this module directly. It executes code at the top level. For
#   access to a restart string use servertype.GetRestartCmd()
# - Treat this like a configuration file, and try to minimize complex logic.
#   The restart functions should be based on data from config.var where
#   possible.
#
# HISTORY:
# This file was branched from production in 2004.
# - Nick Pelly

import commands
import os
import re
import socket
import string
import time
import types
import urllib

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.production.common import cli
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter.servertype_crawl import shardset_output_log_name
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.setup import serverflags

# Same as the value of MAX_INT in Java (32-bit)
JAVA_MAX_LOG_SIZE = 2147483647

# Use data versioning by default, unless --nodataversions specified.
USE_VERSIONS = 1

LOCK_SERVICE_FLAGS = [ '--lockservice_use_loas=false',
                       '--svelte_servers=localhost:6297',
                       '--svelte_retry_interval_ms=2147483647' ]

#------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#------------------------------------------------------------------------------

def no_data_versions():
  global USE_VERSIONS
  USE_VERSIONS = 0

def CommandLineExtend(command_line, arguments):
  for argument in arguments:
    command_line.Add(argument)

# Given a server set name, return the beginning of the command we want
# to use to start the server.  The optional args only have effect
# when we're in USE_LOOP mode. TODO: some day all of this
# should be shared with crawl restarts.
#
# Note the setname is usually synonymous with the servertype except
# for balancers where the setname is +balancedtype.  In the ideal
# world we would be passing in the server object with the restart
# method to generalize all of this, but it requires a significant
# amount of cleanup which will need to be done later.
#
# binary_override can be used to overrided the binary used.  This
# is for cases where we have shared servertypes (i.e. scanjpg types
# call rtmain methods) and servertypes that have multiple binaries
# (i.e. rpcbalancer v. balancer).
def ServerExecutablePrefix(config, setname, args="", binary_override=""):

  srv_mgr = config.GetServerManager()
  set = srv_mgr.Set(setname)

  if not set:
    raise RuntimeError('ERROR: Could not find server set for: %s' % setname)

  # Find the binary directory.
  bindir = set.property('bin_dir')
  if not bindir:
    bin_dirs = config.var('BIN_DIRS', {})
    bindir = bin_dirs.get(setname, bin_dirs.get('google', None))

  # Find the run directory, user, group and binary name from properties.
  rundir = set.property('run_dir')
  user = set.property('binary_user')
  group = set.property('binary_group')
  prog = set.property('binary_name', setname)

  # Allow caller to override for those hacky cases of shared servertypes
  # (i.e. scanjpg types) and multiple binary names for a servertype
  # (i.e. rpcbalancer).
  if binary_override: prog = binary_override

  if config.var('USE_LOOP'):
    if args: args = args + " "
    if bindir: args = args + "--bindir=%s " % bindir
    if rundir: args = args + "--rundir=%s " % rundir
    if user: args = args + "--user=%s " % user
    if group: args = args + "--group=%s " % group
    cmd = config.var('LOOP_SH_PATH') + " " + args + prog
  else:
    if not bindir: bindir = "%s/google/bin" % os.environ['HOME']
    cmd = "cd %s; ./%s" % (bindir, prog)

  if config.var('CHROOT') and config.var('CHROOT').has_key(setname):
    # add an environment var and a flag that says to look at that var
    cmd = "CHROOT=%s %s --chroot=env" % \
    (config.var('CHROOT').get(setname), cmd)

  default_vm_limit = config.var('DEFAULT_MAX_VIRTUAL_MEMORY_KB')
  vm_limit = config.var('SERVER_MAX_VIRTUAL_MEMORY_KB').get(setname,
                                                            default_vm_limit)
  if vm_limit:
    cmd = "ulimit -HSv %s && %s" % (vm_limit, cmd)

  return cmd

# Get the ulimit prefix which depends on the ALLOW_COREFILES
# setting in the config.  This is split out
# as a separate method so that the enterprise methods below
# which don't call ServerExecutablePrefix can get this
# functionality. TODO: why don't the enterprise methods
# call ServerExecutablePrefix?
def UlimitPrefix(config):
  if config.var('ALLOW_COREFILES'):
    return ''
  else:
    return 'ulimit -c 0 && '

# Given a server type that's executed by an interpreter (e.g. java, python),
# return the begining of the command we want to use to start the server. In
# addition to the 'binary_name' server property, you also need to specify
# the 'interpreter' server property in servertype_data.
#
# For example, if your server type property 'binary_name' is 'foo.bar' and
# 'interpreter' is '/usr/bin/bar', this function will return:
#
#  /usr/bin/bar [interpreterflags] foo.bar
#
# Or if USE_LOOP is true:
#
#  /path/to/loop.sh [loopflags] --exec='/usr/bin/bar [interpreterflags]' foo.bar
#
def InterpretedServerExecutablePrefix(config, server_type, interpreterflags='',
                                      loopflags='', no_loop=None):
  # First construct the loop independent part of the command
  srv_mngr = config.GetServerManager()
  interpreter_cmd = srv_mngr.Set(server_type).property('interpreter')
  if not interpreter_cmd:
    raise RuntimeError('The server property "interpreter" is not specified'
                       ' for an interpreted server type')
  interpreter_cl = cli.CommandLine()
  interpreter_cl.Add(interpreter_cmd)
  if interpreterflags:
    interpreter_cl.Add(interpreterflags)

  # Now see if we need loop
  if config.var('USE_LOOP') and no_loop == None:
    loop_cl = cli.CommandLine()
    if loopflags:
      loop_cl.Add(loopflags)
    loop_cl.Add("--exec='%s'" % interpreter_cl.ToString())
    return ServerExecutablePrefix(config, server_type, loop_cl.ToString())
  else:
    return (interpreter_cl.ToString() + ' '
            + servertype.GetBinaryName(server_type))

# Given a server type, return the begining of the command we want to use to
# start a "standard" Java server (i.e. running the "java" command). By
# standard, we mean the single jar file approach where the jar file is the
# binary and embeds a MANIFEST.MF file to specify the main java class file.
# The single jar file is probably generated by autojar.
#
# For example, if your server type property 'binary_name' is 'foo.jar' and
# 'interpreter' is '/usr/bin/java', this function will return:
#
#   /usr/bin/java -jar [jvmflags] foo.jar
#
# Or if USE_LOOP is true:
#
#   /path/to/loop.sh --nobody --exec='/usr/bin/java -jar [jvmflags]' foo.jar
#
# The --nobody flag is needed for java programs because java can't switch to
# nobody in the application (unless you hack with JNI).
#
# java_max_heap_mb: If specified, this will override the value of
# config.var('JAVA_MAX_HEAP_MB').
#
def JavaServerExecutablePrefix(config, server_type, jvmflags='', loopflags='',
                               run_as_nobody_by_loop=1, no_loop=None,
                               run_as_class=None, java_max_heap_mb=None):
  # Construct JVM flags
  jvm_cl = cli.CommandLine()
  if not run_as_class:
    jvm_cl.Add('-jar')
  if jvmflags:
    jvm_cl.Add(jvmflags)

  # Specific JVM flags taken from configs
  # On the memory-constrained virtual GSA, we omit "-server" to conserve RAM.
  # TODO(haldar): Do this on the physical too, and just let the JVM decide.
  if (config.var('ENT_CONFIG_TYPE') not in ('LITE', 'FULL')
      and config.var('JAVA_USE_SERVER_VM')):
      jvm_cl.Add('-server')
  if java_max_heap_mb == None:
    java_max_heap_mb = config.var('JAVA_MAX_HEAP_MB')
  if java_max_heap_mb:
    jvm_cl.Add('-Xmx%sm' % java_max_heap_mb)
  if config.var('JAVA_MIN_HEAP_MB'):
    jvm_cl.Add('-Xms%sm' % config.var('JAVA_MIN_HEAP_MB'))
  if config.var('JAVA_STACK_KB'):
    jvm_cl.Add('-Xss%sk' % config.var('JAVA_STACK_KB'))
  if config.var('JAVA_ENDORSED_DIRS'):
    jvm_cl.Add('-Djava.endorsed.dirs=%s' % config.var('JAVA_ENDORSED_DIRS'))
  if config.var('JAVA_DNS_TTL_SEC'):
    jvm_cl.Add('-Dsun.net.inetaddr.ttl=%s' % config.var('JAVA_DNS_TTL_SEC'))
  if config.var('JAVA_SUN_DEFAULT_CONNECT_TIMEOUT_MS'):
    jvm_cl.Add('-Dsun.net.client.defaultConnectTimeout=%s' %\
               config.var('JAVA_SUN_DEFAULT_CONNECT_TIMEOUT_MS'))
  if config.var('JAVA_SUN_DEFAULT_READ_TIMEOUT_MS'):
    jvm_cl.Add('-Dsun.net.client.defaultReadTimeout=%s' %\
               config.var('JAVA_SUN_DEFAULT_READ_TIMEOUT_MS'))
  if config.var('JAVA_HEADLESS'):
    jvm_cl.Add('-Djava.awt.headless=true') # testme

  # Construct loop script flags
  loop_cl = cli.CommandLine()
  if loopflags:
    loop_cl.Add(loopflags)
  if run_as_nobody_by_loop:
    loop_cl.Add('--nobody')

  return InterpretedServerExecutablePrefix(config, server_type,
                                           jvm_cl.ToString(),
                                           loop_cl.ToString(),
                                           no_loop)

# Return the flags for GSE. You should call this instead of constructing the
# flags yourself, so that when new flags are added to GSE or better production
# values are discovered, they can be easily applied to all GSE apps here.
#
# Note: Some of the flags have default behavior that's different from giving
#       an empty flag. For example, "--contextbase=" is different from not
#       specifying the flag at all.
#
def GseFlags(config, server_port):
  cl = cli.CommandLine()
  if config.var('GSE_SERVE_STATIC_FILES'):
    cl.Add('--servestaticfiles')
  cl.Add('--secureheader=X-GFE-SSL')
  cl.Add('--useripheader=X-USER-IP')
  cl.Add('--lameduckinterval=12000')  # milliseconds
  cl.Add('--stderr_level=OFF')
  cl.Add('--logfile_level=ALL')
  cl.Add('--logfile_name=%s' % config.var('GSE_LOG_FILE'))
  cl.Add('--keepalive=%d' % config.var('GSE_KEEPALIVE_TIMEOUT'))

  if config.var('GSE_CONTEXT_BASE_DIR'):
    cl.Add('--contextbase=%s' % config.var('GSE_CONTEXT_BASE_DIR'))
  else:
    cl.Add('--contextbase=')

  if config.var('GSE_TEMP_DIR'):
    cl.Add('--tempdir=%s' % config.var('GSE_TEMP_DIR'))

  if config.var('GSE_CONTEXT_PATH'):
    cl.Add('--contextpath=%s' % config.var('GSE_CONTEXT_PATH'))
  else:
    cl.Add('--contextpath=')

  if config.var('GSE_DEFAULT_FILE') is not None:
    cl.Add('--defaultfile=%s' % config.var('GSE_DEFAULT_FILE'))

  if config.var('GSE_GWS_LOG_PREFIX'):
    cl.Add('--gwslog_prefix=%s' % config.var('GSE_GWS_LOG_PREFIX'))

  if config.var('GSE_LOG_FLUSH_INTERVAL'):
    cl.Add('--logfile_flush_interval=%s' % config.var('GSE_LOG_FLUSH_INTERVAL'))

  if config.var('GSE_MAXREQUESTS'):
    cl.Add('--maxrequests=%s' % config.var('GSE_MAXREQUESTS'))

  if config.var('GSE_SESSION_COOKIE_DOMAIN') is not None:
    cl.Add('--session_cookie_domain=%s' % config.var('GSE_SESSION_COOKIE_DOMAIN'))

  if config.var('GSE_DISABLE_HEALTHZ_LOGGING'):
    cl.Add('--no_healthz_logging')
  if config.var('GSE_DISABLE_STATUSLOG'):
    cl.Add('--no_statuslog')
  if config.var('GSE_STATUSLOG_PREFIX'):
    cl.Add('--statuslog_prefix=%s' % config.var('GSE_STATUSLOG_PREFIX'))

  if config.var('GSE_COMPRESS_RESPONSES'):
    cl.Add("--compress_responses")

  if config.var('GSE_SERVERTYPE'):
    cl.Add('--servertype=%s' % config.var('GSE_SERVERTYPE'))

  if config.var('GSE_MAXPOSTSIZE'):
    cl.Add('--maxpostsize=%s' % config.var('GSE_MAXPOSTSIZE'))

  cl.Add('--port=%s' % server_port)
  return cl.ToString()

def kill_java_with_stack_trace(port, delay, signal,
                               num_traces=1, trace_delay=5):
  mtype = servertype.GetPortType(port)
  kill_bins = servertype.GetBinaryFiles(mtype, expand_aliases=0)

  cmd = []
  for binname in kill_bins:
    for i in range(num_traces):
      if i != 0:
        cmd.append("sleep %d; " % trace_delay)
      cmd.append(servertype.GetKillSigOnPortDelay(binname, port, -1, 'QUIT'))
    cmd.append(servertype.GetKillSigOnPortDelay(binname, port, delay, signal))
  return string.join(cmd, '')

#------------------------------------------------------------------------------
# INDEX
#------------------------------------------------------------------------------

# Lexserver arguments passed to index servers are of the form
# <hostname>:<port>,... of each of the lex servers.)
def get_lexargs(config):

  srv_mngr = config.GetServerManager()
  hostports = srv_mngr.Set('index').BackendHostPorts('lexserver')
  arg = serverflags.MakeHostPortsArg(hostports)
  if arg:
    return '-lexserver=' + arg
  else:
    return ''

# Hostidserver arguments passed to index servers are of the form
# <hostname>:<port>,... of each hostid server shard which corresponds to
# this index server shard
def get_hostidargs(config, index_port):

  srv_mngr = config.GetServerManager()
  hostports = srv_mngr.Set('index').BackendHostPorts('hostid', port=index_port)
  arg = serverflags.MakeHostPortsArg(hostports)
  if arg:
    return '-hostidservers=' + arg
  else:
    return ''

def get_indexargs(config, index_port):

  num_shards = config.GetNumShards(index_port)
  index_level = servertype.GetLevel(index_port)
  ret = ''
  if config.var('INMEMORY_INDEX')[index_level] > 0:
    ret = ret + "-serverthreads=%s -inmemory_index " % config.var('NUM_THREADS_INMEMORY')
    ret = ret +"-lexserver=local --num_microshards=8 "
    # Note on "--num_microshards=8": indexservers from 20030715 on treat
    # this flag as a maximum: they will not try to load more microshards
    # than they have memory for.  This flag prevents us from running into
    # Bios-reserved address space on 4G Xeons; we are likely to implement
    # a different, better, fix for this problem at some point. [pjensen]

    # Add dev mem state file arg if explicitly stated.
    if config.var('INDEXSERVER_DEV_MEM_STATE_FILE'):
      ret = ret + ('--dev_mem_state_file=%s ' %
                   config.var('INDEXSERVER_DEV_MEM_STATE_FILE'))
  else:
    ret = ret + "-serverthreads=%d " % (config.var('NUM_THREADS'))
  if config.var('INDEXSERVER_CACHE')[index_level] != '0':
    ret = ret + "-memcache_size=%s " % config.var('INDEXSERVER_CACHE')[index_level]
    ret = ret + "-cachelistlen=%d " % config.var('INDEX_BALANCER_AMOUNT_TO_CACHE')[index_level]
  if config.var('INDEXSERVER_NUM_RESULTS_TO_SCORE')[index_level] != 0:
    ret = ret + "--max_results_to_score=%s " % (
      config.var('INDEXSERVER_NUM_RESULTS_TO_SCORE')[index_level])
  if config.var('INDEXSERVER_MAX_RESULTS_PER_TIER')[index_level] != 0:
    ret = ret + "--max_results_per_tier=%s " % (
      config.var('INDEXSERVER_MAX_RESULTS_PER_TIER')[index_level])
  if config.var('INDEXSERVER_RAWIO')[index_level] > 0:
    ret = ret + "-mmap_index=3 "
    ret = ret + "-stalled_read_size_with_seek=1048576 "
    ret = ret + "-stalled_read_size_without_seek=1048576 "
    ret = ret + "-prefetch_read_size_without_seek=262144 "
    if config.var('SERVING_USENET'):
      # usenet posting lists are longer and we go deeper in them so
      # we need more arena memory (18MB default -> 28MB)
      ret = ret + "--rawio_arena_block_count=112 "
  else:
    # The new indexserver defaults to rawio on, so we want to turn it
    # off explicitly if INDEXSERVER_RAWIO is not set (except for
    # inmemory which ignores mmap_index anyways)
    if config.var('INMEMORY_INDEX')[index_level] == 0:
      ret = ret + "-mmap_index=2 "
  if config.var('SERVING_USENET'):
    ret = ret + "--usenet "
    # we can afford to score more on higher (smaller) index levels
    max_results = 1000
    if (index_level == 1):
      max_results = 2000
    elif (index_level > 1):
      max_results = 5000
    # how big the results array (per tier) in the qserver should be
    ret = ret + "--max_results_to_score=%d " % max_results
    # max_results_per_tier is for the whole index level, so to take
    # advantage of max_results_to_score above, we need to multiply this
    # by the number of shards on this index level
    ret = ret + "--max_results_per_tier=%d " % (max_results * num_shards)
  if config.var('NEW_SCORING'):
    ret = ret + "--new_scoring "
  if config.var('IMAGE_SCORING'):
    ret = ret + "--image_scoring "
  if config.var('IMAGE_SEARCH'):
    ret = ret + "--image_search "
  if config.var('MICROSHARD_MEMORY_FRACTION')[index_level]:
    ret = ret + "-microshard_memory_fraction=%f " % \
                config.var('MICROSHARD_MEMORY_FRACTION')[index_level]
  if config.var('MAX_MLOCK_FAILURE')[index_level]:
    ret = ret + "-max_mlock_failure=%d " % \
                config.var('MAX_MLOCK_FAILURE')[index_level]
  if config.var('ENABLE_FIELD_SEARCH'):
    ret = ret + "--fieldsearch_enabled "
  if config.var('USE_GLOBAL_DOCIDS').get(index_level):
    ret = ret + "--use_global_docids "

  # extract froogle scoring args for scoring.
  if config.var('FROOGLE_EXTRACT_SCORING_PARAMETERS'):
    ret = ret + '--froogle_extract_scoring_parameters '

  # use froogle specific scoring weights.
  if config.var('FROOGLE_SCORING'):
    ret = ret + '--froogle_scoring '

  # use principal word scoring.
  if config.var('PRINCIPALWORD_SCORING'):
    ret = ret + '--principalword_scoring '

  # use chinese scoring
  if config.var('CHINESE_SCORING'):
    ret = ret + '--chinese_scoring '

  # load perdocdata
  if config.var('LOAD_PERDOCDATA'):
    ret = ret + '--load_perdocdata '

  # compute phil match
  if config.var('COMPUTE_PHIL_MATCH'):
    ret = ret + '--compute_phil_match '

  # Maximum normalized activation of one document phil cluster
  if config.var('PHIL_MAX_DOC_ACTIVATION') != None:
    ret = ret + (' --phil_max_doc_activation=%f' % (
      config.var('PHIL_MAX_DOC_ACTIVATION')))

  return ret

def restart_index(config, host, port):
  command_line = cli.CommandLine()
  num_shards = config.GetNumShards(port)
  # I think USE_LEXSERVER and USE_HOSTIDSERVER are obsolete, so I've dropped
  # the test. If servers are present in the config, they will be passed.
  lexargs = get_lexargs(config)
  hostidargs = get_hostidargs(config, port)
  indexargs = get_indexargs(config, port)
  my_data_dir = config.GetDataDir(port)

  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "index"))
  command_line.Add("-lockmem")
  command_line.Add(indexargs)
  command_line.Add(lexargs)
  command_line.Add(hostidargs)
  command_line.Add(servertype.GetServingPort(port))
  command_line.Add(my_data_dir)
  command_line.Add("search")
  command_line.Add(servertype.GetPortShard(port))
  command_line.Add(num_shards)


  return command_line.ToString()

servertype.RegisterRestartFunction('index', restart_index)

#------------------------------------------------------------------------------
# RegistryServer
#------------------------------------------------------------------------------

def restart_registryserver(config, host, port):
  command_line = cli.CommandLine()
  command_line.Add(UlimitPrefix(config))

  binary_name = servertype.GetBinaryName('registryserver')
  libsdirs = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name))
  libsdirs = '%s:%s' % (os.path.join(config.var('MAINDIR'), 'bin'), libsdirs)

  classpath = ('%s/bin/RegistryServer.jar' % config.var('MAINDIR'))
  jvm_cl = cli.CommandLine()
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.library.path=%s' % libsdirs)

  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('registryserver')

  command_line.Add(JavaServerExecutablePrefix(config, 'registryserver',
                   jvm_cl.ToString(), run_as_class=1))

  command_line.Add('--port=%d' % port)

  command_line.Add('--enthome=%s' % config.var('ENTERPRISE_HOME'))

  # This flag controls the logging of classes under com.google.enterprise
  command_line.Add('--enterprise_log_level=INFO')
  # This flag controls the logging of all other classes
  command_line.Add('--log_level=INFO')

  # on the virtual GSALite, keep logs small (10MB)
  if config.var('ENT_CONFIG_TYPE') == 'LITE' or \
     config.var('ENT_CONFIG_TYPE') == 'FULL':
    command_line.Add('--log_file_limit=%d' % 10000000)
  else:
    # By default, previous logs are deleted. These flags are similar to what is
    # in logcontrol. Note that we have to pass the value of Integer.MAX_VALUE in
    # Java (32-bit), so we can't pass 2200000000 (value in logcontrol)
    command_line.Add('--log_file_count=%d' % 20)
    command_line.Add('--log_file_limit=%d' % JAVA_MAX_LOG_SIZE)

  return command_line.ToString()

servertype.RegisterRestartFunction('registryserver', restart_registryserver)

#------------------------------------------------------------------------------
# CACHE
#------------------------------------------------------------------------------

def restart_cache(config, host, port):
  command_line = cli.CommandLine()
  my_data_dir = config.GetDataDir(port)
  num_shards = config.GetNumShards(port)
  level = servertype.GetLevel(port)

  # TODO: for right now we have to turn off num-shards sanity checking
  # because cacheserver uses unsigned ints while mixer uses signed.
  # Once we run google2 cacheserver everywhere, we should change the mixer.
  command_line.Add(UlimitPrefix(config))
  command_line.Add(
    ServerExecutablePrefix(config, servertype.GetPortType(port), "--nooutput"))
  command_line.Add("--port=%d" % servertype.GetServingPort(port))
  command_line.Add("--shard=%d" % servertype.GetPortShard(port))
  command_line.Add("--numshards=-1")
  command_line.Add("--datadir=%s" % my_data_dir)
  command_line.Add("--nologging")
  command_line.Add("--nokeep_all_logs")

  if config.var('ENTERPRISE'):
    command_line.Add("--mem_use_MB=20")
    command_line.Add("--mem_use_pct=0")
    command_line.Add("--valuesize_MB=500")
    command_line.Add("--valuesize_pct=0")
    command_line.Add("--pct_of_blocks_not_to_gc=0")

  if config.var('PREDICTO'):
    command_line.Add("--pct_of_blocks_not_to_gc=0")

    command_line.Add("--checkpoint_interval=10")

  if config.var('CACHESERVER_TENURE_PCT') != None:
    command_line.Add("--pct_of_blocks_not_to_gc=%s" %
                     config.var('CACHESERVER_TENURE_PCT'))

  # Limit the disk usage of the cacheserver in MB, if
  # specified.  Default value of 0 means no hard limit.
  # Limits mean that the cacheserver will store less data,
  # but can be useful for preventing the cacheservers from
  # seeking to death when they get "too full".
  #     We must set valuesize_pct=0, because the cacheserver
  # will not start if given both an absolute and relative
  # limit.
  # TODO: integrate enterprise limits (above).
  disk_limit = config.var('CACHESERVER_DISK_LIMIT').get(level, '')
  if disk_limit:
    # decode "GB", "MB", etc..
    disk_limit = servertype.ExpandCutoff(disk_limit)

    # convert to megabytes (cacheserver's expected unit)
    # Use long to handle >2GB, int to print nicely
    disk_limit_MB = int(long(disk_limit) >> 20)

    command_line.Add("--valuesize_MB=%s" % disk_limit_MB)
    command_line.Add("--valuesize_pct=0")

    # Check that there's no conflict between absolute and
    # relative non-zero disk limits.
    cmdstr = command_line.ToString()
    if (re.search("valuesize_pct=[1-9.]", cmdstr) and
        re.search("valuesize_MB=[1-9.]", cmdstr)):
      raise RuntimeError("cacheserver needs valuesize specified "+
                         "in _pct or _MB, not but not both.")

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add("--trusted_clients=%s" %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'),
                                 ','))

  # TODO: remove this when the dependency between the cacheserver and
  # chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('cache', restart_cache)

#------------------------------------------------------------------------------
# GLOBAL WORKQUEUE MASTER
#------------------------------------------------------------------------------

def restart_workqueue_main(config, host, port):
  srv_mngr = config.GetServerManager()
  subordinates = srv_mngr.Set('workqueue-main').BackendHostPorts('workqueue-subordinate')
  subordinatestring = serverflags.MakeHostPortsArg(subordinates)

  command_line = cli.CommandLine()
  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "workqueue-main"))
  command_line.Add("--port=%d" % servertype.GetServingPort(port))
  command_line.Add("--checkpoint=%s" % config.var('WORKQUEUE_MASTER_CHECKPOINT'))
  command_line.Add("--cluster_name=%s" % config.var('WORKQUEUE_MASTER_CLUSTER_NAME'))
  command_line.Add("--max_tasks_per_processor=%s" % config.var('WORKQUEUE_MASTER_MAX_TASKS_PER_CPU'))
  command_line.Add("--ideal_load=%d" % config.var('WORKQUEUE_MASTER_IDEAL_LOAD'))

  if config.var('WORKQUEUE_MASTER_SLAVES_FLAG'):
    command_line.Add("--subordinates=%s" % subordinatestring)
  command_line.Add(config.var('WORKQUEUE_MASTER_OTHER_OPTIONS'));

  if config.var('WORKQUEUE_MASTER_RESERVE_BY_TIMEOUT'):
    command_line.Add("--reserve_machines_by_timeout");

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add("--trusted_clients=%s" % string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  if config.var('WORKQUEUE_MASTER_UID'):#
    command_line.Add('--uid=%s' % config.var('WORKQUEUE_MASTER_UID'))

  if config.var('WORKQUEUE_MASTER_SLAVE_TIMEOUT_SECS'):#
    command_line.Add("--subordinate_timeout=%s" %
                     config.var('WORKQUEUE_MASTER_SLAVE_TIMEOUT_SECS'))

  if config.var('WORKQUEUE_MASTER_NAMED_PID_FILE'):#
    command_line.Add('--named_pid_file=%s' %
                     config.var('WORKQUEUE_MASTER_NAMED_PID_FILE'))
  if config.var('WORKQUEUE_MASTER_NAMED_ZONE_FILE'):#
    command_line.Add("--named_zone_file=%s" %
                     config.var('WORKQUEUE_MASTER_NAMED_ZONE_FILE'))
  if config.var('WORKQUEUE_MASTER_MEMORY_OVERCOMMIT_FACTOR'):
    command_line.Add('--memory_overcommit_factor=%s' %
                     config.var('WORKQUEUE_MASTER_MEMORY_OVERCOMMIT_FACTOR'))
  if config.var('WORKQUEUE_MASTER_CLUSTER_SUBDOMAIN'):
    command_line.Add('--cluster_subdomain=%s' %
                     config.var('WORKQUEUE_MASTER_CLUSTER_SUBDOMAIN'))
  if config.var('WORKQUEUE_MASTER_AUTO_DELETE_SECS'):
    command_line.Add('--auto_delete_period=%s' %
                     config.var('WORKQUEUE_MASTER_AUTO_DELETE_SECS'))
  if config.var('GFS_ALIASES'):
    command_line.Add(servertype.mkarg("--bnsresolver_use_svelte=false"))
    command_line.Add(servertype.mkarg("--gfs_aliases=%s" % \
                                       config.var('GFS_ALIASES')))

  # TODO: remove this when the dependency between the workqueue and
  # chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('workqueue-main',
                                   restart_workqueue_main)

#------------------------------------------------------------------------------
# GLOBAL WORKQUEUE SLAVE
#------------------------------------------------------------------------------

def restart_workqueue_subordinate(config, host, port):
  command_line = cli.CommandLine()
  srv_mngr = config.GetServerManager()
  servers = srv_mngr.Set('workqueue-subordinate').BackendHostPorts('workqueue-main')

  if len(servers) != 1:
    raise RuntimeError("workqueue subordinate requires exactly one main")

  (main, main_port) = servers[0]
  main = config.var('GSA_MASTER')
  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "workqueue-subordinate"))
  command_line.Add("--port=%d" % servertype.GetServingPort(port))
  command_line.Add("--workqueue_main=%s:%d" % (main, main_port))
  command_line.Add("--subordinatedir=%s" % config.var('WORKQUEUE_SLAVE_SLAVEDIR'))
  command_line.Add("--reserved_memory=%d" % config.var('WORKQUEUE_SLAVE_RESERVED_MEMORY'));
  command_line.Add("--reserved_disk=%d" % config.var('WORKQUEUE_SLAVE_RESERVED_DISK'));
  command_line.Add(config.var('WORKQUEUE_SLAVE_OTHER_OPTIONS'));
  if config.var('GFS_ALIASES'):
    command_line.Add(servertype.mkarg("--bnsresolver_use_svelte=false"))
    command_line.Add(servertype.mkarg("--gfs_aliases=%s" % \
                                       config.var('GFS_ALIASES')))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add("--trusted_clients=%s" % string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))
  if config.var('WORKQUEUE_SLAVE_CHILD_NICE') != None:
    command_line.Add("--child_nice=%d" % config.var('WORKQUEUE_SLAVE_CHILD_NICE'))

  if config.has_var('WORKQUEUE_SLAVE_DATADISKS') and config.var('WORKQUEUE_SLAVE_DATADISKS'):
    command_line.Add('--disks=%s' % string.join(
      config.var('WORKQUEUE_SLAVE_DATADISKS')[host], ','))
  elif config.has_var('DATACHUNKDISKS'):
    command_line.Add('--disks=%s' % string.join(
      config.var('DATACHUNKDISKS')[host], ','))

  if config.var('WORKQUEUE_SLAVE_UID'):
    command_line.Add('--uid=%s' % config.var('WORKQUEUE_SLAVE_UID'))

  if config.var('WORKQUEUE_SLAVE_USE_RSS'):
    command_line.Add('--user_rss_for_memory_usage')

  if config.has_var('WORKQUEUE_SLAVE_NETWORK_SPEED'):
    command_line.Add('--network_speed=%s' % config.var('WORKQUEUE_SLAVE_NETWORK_SPEED'))

  if config.var('WORKQUEUE_SLAVE_TAG_PROCESSES'):
    command_line.Add('--tag_processes=%s' %
                     config.var('WORKQUEUE_SLAVE_TAG_PROCESSES'))

  if config.var('WORKQUEUE_SLAVE_IGNORE_ALL_SVS_PROBLEMS'):
    command_line.Add('--ignore_all_svs_problems')

  # TODO: remove this when the dependency between the workqueue and
  # chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('workqueue-subordinate', restart_workqueue_subordinate)

#------------------------------------------------------------------------------
# WORKSCHEDULER SERVER
#------------------------------------------------------------------------------

def feeddocdeleter_log_info_arg(config, host, port):
  components = []
  # make sure we have at least one of the document processors
  if (config.var('NEED_RTSERVER') and
     config.GetNumShards('base_indexer') == 0 and
     config.GetNumShards('daily_indexer') == 0 and
     config.GetNumShards('rt_indexer') == 0):
     print('At least one of base_indexer, daily_indexer'
           ' and rt_indexer machines  must be specified')
     sys.exit(1)


  # if RTLOG_FEED_DOC_DELETER_SUFFIX are set,
  # allow feed_doc_deleter to talk to rtserver through rtlogs
  if config.var('RTLOG_FEED_DOC_DELETER_SUFFIX'):
    # make sure RTSERVER_LOGS is defined
    if not config.var('RTSERVER_LOGS'):
      print 'Need RTSERVER_LOGS for indexer logfile names'
      sys.exit(1)
    # end if
    # Need a seperate log file for feeder_doc_deleter
    sfx = config.var('RTLOG_FEED_DOC_DELETER_SUFFIX')
    for indexer_type in ('base_indexer', 'rt_indexer', 'urlhistory_processor',
                         'daily_indexer', 'urlmanager', 'tracker_gatherer'):
      output_log = shardset_output_log_name(config, indexer_type, host , port,
                                            config.GetNumShards(indexer_type),
                                            sfx)
      if output_log:
        components.append(output_log)
      # end if
    # end for
  # end if

  return string.join(components, ',')

def restart_workschedulerserver(config, host, port):
  command_line = cli.CommandLine()
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('workschedulerserver')
  servers = set.BackendHostPorts('workqueue-main')

  if len(servers) != 1:
    raise RuntimeError("workqueue subordinate requires exactly one main")

  (main, main_port) = servers[0]
  my_data_dir = config.GetDataDir(port)
  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "workschedulerserver"))
  command_line.Add("--port=%d" % servertype.GetServingPort(port))
  command_line.Add("--workqueue_main=%s:%d" % (main, main_port))
  command_line.Add("--datadir=%s" % my_data_dir)

  if config.var('NAMESPACE_PREFIX'):
    command_line.Add("--namespace_prefix=%s" % config.var('NAMESPACE_PREFIX'))
  if config.var('WORKSCHEDULER_JOB_PREFIX'):
    command_line.Add("--workscheduler_job_prefix=%s" % \
                     config.var('WORKSCHEDULER_JOB_PREFIX'))
  if config.var('WORKSCHEDULER_GLOBALDIR'):
    command_line.Add("--workscheduler_globaldir=%s" % \
                     config.var('WORKSCHEDULER_GLOBALDIR'))
  if config.var('ENTERPRISE_HOME'):
    command_line.Add("--enterprise_home=%s" %
                     config.var('ENTERPRISE_HOME'))
  if config.var('GFS_ALIASES'):
    command_line.Add(servertype.mkarg("--bnsresolver_use_svelte=false"))
    command_line.Add(servertype.mkarg("--gfs_aliases=%s" % \
                                      config.var('GFS_ALIASES')))
  if config.var('GFS_USER'):
    command_line.Add("--gfs_user=%s" % config.var('GFS_USER'))
  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    command_line.Add("--keep_checksum_for_checkpoints=false")

  if config.var('ENABLE_WORKSCHEDULER_COLLECTIONS'):
    if not config.var('ENTERPRISE_COLLECTIONS_DIR'):
      raise ValueError, "Must specify collections directory for collections"
    command_line.Add("--collections")
    command_line.Add("--collections_directory=%s" %
                     config.var('ENTERPRISE_COLLECTIONS_DIR'))
    command_line.Add("--restricts_rtupdate_prefix=%s" %
                     config.var('WORKSCHEDULER_COLLECTIONS_LOG_PREFIX'))
    if config.var('WORKSCHEDULER_RESTRICT_UPDATE_INTERVAL'):
      command_line.Add("--restrict_update_interval=%d" % \
                       config.var('WORKSCHEDULER_RESTRICT_UPDATE_INTERVAL'))
    if config.var('WORKSCHEDULER_RESET_UPDATE_LIMIT_INTERVAL'):
      command_line.Add("--reset_update_limit_interval=%d" % \
                       config.var('WORKSCHEDULER_RESET_UPDATE_LIMIT_INTERVAL'))
    if config.var('WORKSCHEDULER_MAX_RESTRICT_UPDATE_PER_PERIOD'):
      command_line.Add("--max_restrict_updates_per_period=%d" % \
                       config.var(
        'WORKSCHEDULER_MAX_RESTRICT_UPDATE_PER_PERIOD'))
    if config.var('WORKSCHEDULER_MIN_RATIO_OF_COLLECTION_CHANGE'):
      command_line.Add("--min_ratio_of_collection_change_before_update=%f" % \
                       config.var(
        'WORKSCHEDULER_MIN_RATIO_OF_COLLECTION_CHANGE'))

  if config.var('ENABLE_WORKSCHEDULER_COLLECTIONS') or \
     config.var('ENABLE_WORKSCHEDULER_FROOGLE_SCHEDULER') or \
     config.var('ENABLE_WORKSCHEDULER_FEED_DOC_DELETER'):
    command_line.Add('--num_index_shards=%s' % config.var('NUM_INDEX_SHARDS'))
    command_line.Add('--cjk_config=%s' % config.var('CJKCONFIGDIR'))
    command_line.Add('--bt_version=%s' % config.var('BTVERSION'))
    command_line.Add('--rtrepos=%s' % config.var('RTSERVER_INDEX_PREFIX'))
    command_line.Add('--num_rt_doc_shards=%s' % \
                     config.var('WORKSCHEDULER_NUM_DOC_SHARDS'))
    if (config.var('RTSERVER_DOCID_LEVELS') and
        config.var('RTSERVER_DOCID_LEVELS') > 0):
      command_line.Add('--num_docid_levels=%d' %
                       config.var('RTSERVER_DOCID_LEVELS'))
  #endif
  if config.var('ENABLE_WORKSCHEDULER_FEED_DOC_DELETER'):
    command_line.Add('--enable_feeddocdeleter')
    if not config.var('WORKSCHEDULER_FEED_DOC_DELETER_BINARY'):
      raise ValueError, 'Must specify feed doc deleter binary'
    command_line.Add('--feed_doc_deleter_bin=%s' %
                   config.var('WORKSCHEDULER_FEED_DOC_DELETER_BINARY'))
    if config.var('URLTRACKER_SHARD_BY_URL') == 1:
      command_line.Add("--urltracker_shard_by_url")
    # multiple maps for clusters
    num_feeder_shards = config.GetNumShards("feeder")
    feedmaps = []
    for i in xrange(num_feeder_shards):
      feedmaps.append('%sfeed_datasource_map%03d-of-%03d' % (
                       config.var('NAMESPACE_PREFIX'), i,
                       num_feeder_shards))
    command_line.Add('--feed_datasource_map=%s' % string.join(feedmaps, ','))

    log_info_arg = feeddocdeleter_log_info_arg(config, host, port)
    command_line.Add('--feed_doc_deleter_log_info=%s' % log_info_arg)
    command_line.Add('--feed_doc_deleter_interval_secs=%d' %
                     config.var('WORKSCHEDULER_FEED_DOC_DELETER_RUNINTERVAL'))

    num_doc_shards = config.var('WORKSCHEDULER_NUM_DOC_SHARDS')
    if num_doc_shards > 1:
      namespaces = []
      filesets = []
      for shard in xrange(0, num_doc_shards):
        namespace = servertype.GenNamespacePrefix(config, 'base_indexer',
                                                  shard, num_doc_shards)
        namespaces.append(namespace)
        filesets.append('%sFILESET_rt%s_%d' % \
                        (namespace, config.var('RTSERVER_INDEX_PREFIX'),
                         shard))
      # end for
      command_line.Add('--feed_doc_deleter_namespaces=%s' % \
                       string.join(namespaces, ','))
      command_line.Add('--feed_doc_deleter_filesets=%s' % \
                       string.join(filesets, ','))
    # end if
  # endif ENABLE_WORKSCHEDULER_FEED_DOC_DELETER

  if config.var('ENABLE_WORKSCHEDULER_COLLECTIONS'): # or any other rippers
    if not config.var('WORKSCHEDULER_RIPPER_BINARY'):
      raise ValueError, "Must specify ripper binary for workscheduler rippers"
    command_line.Add("--ripper_bin=%s" %
                     config.var('WORKSCHEDULER_RIPPER_BINARY'))
    num_doc_shards = config.var('WORKSCHEDULER_NUM_DOC_SHARDS')
    if num_doc_shards > 1:
      files = []
      for doc_shard in xrange(0, num_doc_shards):
        files.append(servertype.GenNamespacePrefix(config, "base_indexer",
                                                   doc_shard, num_doc_shards))
      command_line.Add("--ripper_namespaces=%s" % string.join(files, ","))

    if config.var('ENABLE_WORKSCHEDULER_REMOVEDOC_SCHEDULER'):
      command_line.Add("--removedoc_scheduler")
      command_line.Add("--starturls_file=%s" % config.var('STARTURLS'))
      command_line.Add("--goodurls_pat=%s" % config.var('GOODURLS'))
      command_line.Add("--badurls_pat=%s" % config.var('BADURLS'))
      command_line.Add("--removedoc_rtupdate_prefix=%s" %
                     config.var('WORKSCHEDULER_REMOVEDOC_LOG_PREFIX'))
      command_line.Add("--removedoc_uhpupdate_prefix=%s" %
                     config.var('WORKSCHEDULER_REMOVEDOC_UHP_LOG_PREFIX'))
      command_line.Add("--removedoc_trackerupdate_prefix=%s" %
                     config.var('WORKSCHEDULER_REMOVEDOC_TRACKER_LOG_PREFIX'))
      command_line.Add("--num_tracker_shards=%d" %
                       config.GetNumShards('tracker_gatherer'))
      command_line.Add("--removedoc_runinterval=%d" %
                       config.var('WORKSCHEDULER_REMOVEDOC_RUNINTERVAL'))
      command_line.Add("--removedoc_umupdate_prefix=%s" %
                       config.var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX'))
      command_line.Add("--num_um_shards=%d " %
                       config.GetNumShards('urlmanager'))
      command_line.Add("--removedoc_info_dump_file=%s" %
                       config.var('WORKSCHEDULER_REMOVEDOC_INFO_DUMP_FILE'))
      command_line.Add("--removedoc_keep_doc_file=%s" %
                       config.var('WORKSCHEDULER_REMOVEDOC_KEEP_DOC_FILE'))
      command_line.Add("--removedoc_max_keep_docs=%d" %
                       config.var('WORKSCHEDULER_REMOVEDOC_MAX_KEEP_DOCS'))
      if config.var('URLTRACKER_SHARD_BY_URL') == 1:
        command_line.Add("--urltracker_shard_by_url")

    if config.var('ENABLE_REALTIME_SEKULITE') and \
       config.var('CRAWL_USERPASSWD_CONFIG') or \
       config.var('ENABLE_SINGLE_SIGN_ON') and \
       config.var('SSO_PATTERN_CONFIG'):
      command_line.Add("--sekure_rtupdate_prefix=%s" %
                       config.var('WORKSCHEDULER_SEKURE_LOG_PREFIX'))

      if config.var('ENABLE_SINGLE_SIGN_ON') and \
         config.var('SSO_PATTERN_CONFIG') :
        command_line.Add("--sso_pattern_config=%s" %
                         config.var('SSO_PATTERN_CONFIG'))
      if config.var('ENABLE_REALTIME_SEKULITE') and \
         config.var('CRAWL_USERPASSWD_CONFIG') :
        command_line.Add("--sekulite_userpasswd_config=%s" %
                         config.var('CRAWL_USERPASSWD_CONFIG'))

  # enterprise spell data generator
  if config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_LANGS'):
    command_line.Add("--ent_spelling_langs=%s" %
                     config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_LANGS'))

  if config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_INTERVAL'):
    command_line.Add("--ent_spelling_interval=%s" %
                     config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_INTERVAL'))

  if config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_INITIAL_START'):
    command_line.Add("--ent_spelling_initial_start=%s" %
                  config.var('WORKSCHEDULER_ENTERPRISE_SPELLING_INITIAL_START'))

  # enterprise specific epoch advance
  if config.var('ENABLE_WORKSCHEDULER_ENTERPRISE_EPOCHADVANCE'):
    command_line.Add("--enable_enterprise_epochadvance=true")
    command_line.Add("--epoch_advance_period=%d" %
                     config.var('ENTERPISE_INDEX_EPOCH_ADVANCE_PERIOD'))

  # enterprise status report
  if config.var('ENABLE_ENTERPRISE_STATUS_REPORT'):
    command_line.Add("--enable_enterprise_statusreport")

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add("--trusted_clients=%s" %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  if config.var('ENABLE_WORKSCHEDULER_FROOGLE_SCHEDULER'):
    command_line.Add("--enable_froogle_scheduler")

    # FroogleDeleteScheduler flags
    num_doc_shards = config.var('WORKSCHEDULER_NUM_DOC_SHARDS')
    if num_doc_shards > 1:
      namespaces = []
      filesets = []
      for shard in xrange(0, num_doc_shards):
        namespace = servertype.GenNamespacePrefix(config, "rtmain",
                                                  shard, num_doc_shards)
        namespaces.append(namespace)
        filesets.append("%sFILESET_rt%s_%d" % \
                        (namespace, config.var('RTSERVER_INDEX_PREFIX'),
                         shard))
      command_line.Add("--froogle_delete_namespaces=%s" % \
                       string.join(namespaces, ","))
      command_line.Add("--froogle_delete_filesets=%s" % \
                       string.join(filesets, ","))

    command_line.Add("--froogle_delete_log_info=converted:%sconverted@%d" % \
                     (config.var('CONVERTER_OUTPUT_LOGFILE_PREFIX'),
                      num_doc_shards))
    if config.var('FROOGLE_FEED_DELETER_MAP'):
      command_line.Add("--froogle_delete_feed_deleter_map=%s" % \
                       config.var('FROOGLE_FEED_DELETER_MAP'));
    if config.var('FROOGLE_CRAWL_DELETER_MAP'):
      command_line.Add("--froogle_delete_crawl_deleter_map=%s" % \
                       config.var('FROOGLE_CRAWL_DELETER_MAP'));
    if config.var('FROOGLE_DELETE_LOG_DIR'):
      command_line.Add("--froogle_delete_logs_dir=%s" % \
                       config.var('FROOGLE_DELETE_LOG_DIR'))
    command_line.Add("--froogle_delete_use_rtstate_snapshot_files")

  if config.var('ENABLE_WORKSCHEDULER_SORTBYDATE'):
    command_line.Add("--enable_sortbydate_scheduler")
    command_line.Add("--extractdate_config=%s" % \
                     config.var('DATEPATTERNS'))
    command_line.Add("--sortbydate_interval=%s" % \
                     config.var('WORKSCHEDULER_SORTBYDATE_INTERVAL'))
    command_line.Add("--sortbydate_initial_start=%s" % \
                     config.var('WORKSCHEDULER_SORTBYDATE_INITIAL_START'))
    if not config.var('WORKSCHEDULER_FIELDBUILDER_BINARY'):
      raise ValueError, "Must specify fieldbuilder binary"
    command_line.Add("--fieldbuilder_bin=%s" % \
                     config.var('WORKSCHEDULER_FIELDBUILDER_BINARY'))
    command_line.Add("--datefield_rtupdate_prefix=%s" % \
                     config.var('WORKSCHEDULER_DATEFIELD_LOG_PREFIX'))
    # remove the following after complete debugging
    command_line.Add("--date_fieldbuilder_readable")
    command_line.Add("--extractdate_readable_output")

  command_line.Add("--workqueue_type_borg=false")

  if config.var('ENTERPRISE'):
    command_line.Add("--googletags=true")

  # TODO: remove this line when the dependency between the
  # workscheduler and chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  # TODO(tianyu): Below code only passes one shard of rtsubordinate for now.
  rtsubordinate_servers = srv_mngr.Set('rtsubordinate').Servers()
  if len(rtsubordinate_servers):
    command_line.Add('--rtsubordinate_host_port=%s:%d' % (rtsubordinate_servers[0].host(),
                                                    rtsubordinate_servers[0].port()))

  return command_line.ToString()

servertype.RegisterRestartFunction('workschedulerserver',
                                   restart_workschedulerserver)

#------------------------------------------------------------------------------
# ONEBOX
#------------------------------------------------------------------------------

def get_oneboxargs(config):
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('onebox')

  (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

  command_line = cli.CommandLine()
  if backends.HasBackEnds():
    command_line.Add(" --backends=%s" % backends.AsString())

  command_line.Add(" --shardinfo=%s " % shardinfo.AsString())

  if config.var('ONEBOX_FROOGLE_SILENT_MODE'):
    command_line.Add("--froogle_silent_mode")

  if config.var('USE_ONEBOXSYNONYM'):
    if config.var('ONEBOX_SYNONYMDIR'):
      command_line.Add(
          "--synonym_file_dir=%s" % config.var('ONEBOX_SYNONYMDIR'))
    if config.var('ONEBOX_SYNONYM_INTERVAL'):
      command_line.Add(
          "--synonym_refresh_interval=%d" % config.var(
              'ONEBOX_SYNONYM_INTERVAL'))
      command_line.Add("--synonyms_refresh_only_if_changed")

  if config.var('ONEBOX_CITYZIPDATA'):
    command_line.Add("--cityzipdata=%s" % config.var('ONEBOX_CITYZIPDATA'))

  if config.var('ONEBOX_RTNEWS_LIMIT_TO_GOLDENS'):
    command_line.Add("--rtnews_limit_to_goldens")

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add('--trusted_clients=%s' %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'),
                                 ','))
  command_line.Add('--onebox_blacklist_files=')

  if config.has_var('ENTERPRISE_HOME'):
    # note that oneboxserver will crash if cjk_config isn't specified
    if config.var('CJKCONFIGDIR'):
      command_line.Add("--cjk_config=%s" % config.var('CJKCONFIGDIR'))
    if config.var('BTVERSION'):
      command_line.Add("--bt_version=%s" % config.var('BTVERSION'))
    if config.var('CJKSEGMENTER'):
      command_line.Add("--cjk_segmenter=%s" % config.var('CJKSEGMENTER'))
    command_line.Add("--breaking_news=false")
    command_line.Add("--disable_seti=true")

  # TODO: remove this when the dependency between onebox and chubby
  # has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

def restart_onebox(config, host, port):
  command_line = cli.CommandLine()
  my_data_dir = config.GetDataDir(port)

  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "onebox"))
  command_line.Add("-port=%d" % servertype.GetServingPort(port))
  command_line.Add("-datadir=%s" % my_data_dir)
  command_line.Add("--nobinarylog")
  command_line.Add(get_oneboxargs(config))

  return command_line.ToString()

servertype.RegisterRestartFunction('onebox', restart_onebox)

#------------------------------------------------------------------------------
# SPELLMIXER
#------------------------------------------------------------------------------

# As of March 2008, spelling corrections in all languages are handled by a
# single process, the Enterprise spellmixer.

def restart_spellmixer(config, host, port):
  command_line = cli.CommandLine()
  data_dir = config.GetDataDir(port)

  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "spellmixer"))
  command_line.Add("-port=%d" % servertype.GetServingPort(port))
  command_line.Add("-datadir=%s" % data_dir)

  command_line.Add("--cjk_segmenter=%s" % config.var("CJKSEGMENTER"))

  # Specify where to find the spelling data files.
  command_line.Add("--spellingdatafactorytype=enterprise")
  command_line.Add("--langs=de,en,es,fr,it,nl,pt")
  if config.has_var('SPELL_DIR'):
    command_line.Add("--spelldir=%s" % config.var('SPELL_DIR'))
  # Specify the language mapping file.
  if config.has_var('ENTERPRISE_HOME'):
    googledata_dir = config.var('GOOGLEDATA') + '/enterprise/data'
    command_line.Add("--langmapping=%s/spellmixer_mappings.txt" %
                     googledata_dir)

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add("--trusted_clients=%s" %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))
  if config.var('GFS_ALIASES'):
    command_line.Add(servertype.mkarg("--bnsresolver_use_svelte=false"))
    command_line.Add(servertype.mkarg("--gfs_aliases=%s" %
                                       config.var('GFS_ALIASES')))
  # We need force_load for performance on the oneways.
  # Force_load also mlocks.  Mini will thrash, so we turn it off.
  # TODO(mgp): a Mini3 will probably not thrash, so we could remove this.
  if config.var('ENT_CONFIG_TYPE') == 'MINI':
    command_line.Add("--noforce_load")

  # TODO(mgp): the prebuilt spelling RPMs don't have the localization
  # files.  When they are rebuilt, toggle this switch.
  command_line.Add("--enable_localized_filters=false")

  # TODO(mgp): remove this when the dependency between the spellmixer and
  # chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('spellmixer', restart_spellmixer)

#------------------------------------------------------------------------------
# ONEBOX ENTERPRISE
#------------------------------------------------------------------------------

def get_oneboxenterpriseargs(config):
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('oneboxenterprise')

  (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

  command_line = cli.CommandLine()
  if backends.HasBackEnds():
    command_line.Add(" --backends=%s" % backends.AsString())

  command_line.Add(" --shardinfo=%s " % shardinfo.AsString())

  gws_set = srv_mngr.Set('web')
  servers = gws_set.Servers()

  for server in servers:
    command_line.Add('--start_gws_url=http://%s:%s/' % (server.host(),
                                                        server.port()))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add('--trusted_clients=%s' %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'),
                               ','))

  command_line.Add('--use_certificate_dir=%s' %
                   config.var('BOT_SSL_CERTIFICATE_DIR'))
  command_line.Add('--use_certificate_file=%s' %
                   config.var('BOT_SSL_CERTIFICATE_FILE'))
  command_line.Add('--private_rsa_key_file=%s' %
                   config.var('BOT_SSL_KEY_FILE'))
  command_line.Add('--noenable_CRL')

  if config.var('AUTHENTICATE_ONEBOX_SERVER_CERT'):
    command_line.Add('--enable_CRL_PEM')
    command_line.Add('--CA_CRL_dir=%s' %
                     config.var('BOT_CA_CRL_DIR'))
    # This is hack to make minimal changes to google ssl library.
    # It needs a CA file when authenticating peer. So passing a gsa's
    # own cert as a dummy CA file.
    # Enterprise code will use a CA directory instead.
    command_line.Add('--CA_certificate_file=%s' %
                     config.var('BOT_SSL_CERTIFICATE_FILE'))
    command_line.Add('--authenticate_onebox_providers');
  else:
    command_line.Add("--CA_CRL_dir=/dev/null")
    command_line.Add("--CA_certificate_file=")
    if config.var('BOT_SSL_CIPHER_LIST'):
      command_line.Add('--ssl_cipher_list=%s' %
                  config.var('BOT_SSL_CIPHER_LIST'))

  command_line.Add('--web_search_base_url=http://%s:%d/' %
         (config.var('EXTERNAL_WEB_IP'), config.var('ENTFRONT_EXTERNAL_PORT')))

  # TODO: remove this when the dependency between onebox and chubby
  # has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

def restart_oneboxenterprise(config, host, port):
  command_line = cli.CommandLine()
  my_data_dir = config.GetDataDir(port)

  command_line.Add(UlimitPrefix(config))
  command_line.Add(ServerExecutablePrefix(config, "oneboxenterprise"))
  command_line.Add("-port=%d" % servertype.GetServingPort(port))
  command_line.Add("-datadir=%s" % my_data_dir)
  command_line.Add(get_oneboxenterpriseargs(config))

  if config.var('ENTFRONT_FRONTENDS_DIR'):
    command_line.Add(servertype.mkarg("--frontenddir=%s" %
                                      config.var('ENTFRONT_FRONTENDS_DIR')))
  if config.var('ONEBOX_BACKEND_CONFIG'):
    command_line.Add(servertype.mkarg("--onebox_modules=%s" %
                                      config.var('ONEBOX_BACKEND_CONFIG')))

  command_line.Add('--nobinarylog')

  # Enterprise uses text logs, not Sawmill
  command_line.Add('--enterpriselog_writetext')
  command_line.Add('--enterpriselog_writeproto=false')
  command_line.Add('--enterpriselog_writeproto_all=false')
  command_line.Add('--enterpriselog_rotate_daily')
  command_line.Add('--enterpriselog_rotate_size=16000000')

  return command_line.ToString()

servertype.RegisterRestartFunction('oneboxenterprise', restart_oneboxenterprise)

#------------------------------------------------------------------------------
# WEB
#------------------------------------------------------------------------------

# webargs are <hostname>:<ip>:<port> for every backend (almost!).
# we need the [webserver] host because we'll shuffle around sitesearch
# back ends based on what host it is
def get_webargs(config, web_host):

  global USE_VERSIONS

  # TODO: todo what about entmixer in all this code?
  # It should work to just point the 'backends' map in the config
  # to the entmixers explicitly.

  # Setup shardinfo data.
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('web')

  set.set_property('numconns', {'onebox' : 10, 'ent_fedroot' : 1, 'mixer' :
                   config.var('GWS_MIXER_NUMCONN')})
  set.set_property('dflt_numconn', config.var('GWS_DEFAULT_NUMCONN'))

  # Mixers answer on port 4000 for GWS purposes.
  (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

  args = ''

  if backends.HasBackEnds():
    # guard against no backends (eg. GFE)
    # TODO: a nicer way would be to allow empty "--backends=" flag spec
    args = args + " --backends=%s" % backends.AsString()

  args = args + " --shardinfo=%s" % (shardinfo.AsString())
  return args

def restart_web(config, host, port):
  command_line = cli.CommandLine()
  webargs = get_webargs(config, host)

  if config.var('ENTERPRISE'):
    progname = ("%(main_google3_dir)s/enterprise/legacy/setup/loop.sh "
                "%(maindir)s/bin/gws " % {
                  'maindir' : config.var('MAINDIR'),
                  'main_google3_dir': config.var('MAIN_GOOGLE3_DIR')
                  })
  else:
    progname = ServerExecutablePrefix(config, "web", "--nobody") + " "


  ########################################
  # Do not add any new flags before this #
  ########################################
  if config.var('GWS_FLAGS_OVERRIDE'):
    return progname + config.var('GWS_FLAGS_OVERRIDE') + webargs

  if config.var('SERVING_IMAGE'):
    my_datadir = "../../googledata/image/"
  else:
    my_datadir = "../../googledata/gws/"
  try:
    # We need a datadir to know where gwd-directoryinfo lives
    datadirversion = config.GetDataDir(port)
    # But we only care about the dirname part, eg "may01index"
    dirname = googleconfig.GetDirName(datadirversion)
    my_datadir = my_datadir + dirname
  except NameError:                      # can't find data dir? Then ...
    my_datadir = my_datadir              # ... assume it's in gws datadir but

  command_line.Add("-port=%d" % servertype.GetServingPort(port))
  command_line.Add("-datadir=%s" % my_datadir)

  if config.var('DISABLE_NAGLE'):
    command_line.Add("--disable_nagle")

  # Always include the google_keepalive_timeout flag
  command_line.Add("--google_keepalive_timeout=%d" %
                   config.var("GOOGLE_KEEPALIVE_TIMEOUT"))

  if config.var('EXTENDED_SNIPPET_PARAMS'):
    command_line.Add(config.var('EXTENDED_SNIPPET_PARAMS'))

  if config.var('GWS_FILTER_EMPTY_DOCUMENT'):
    command_line.Add("--filter_empty_document")

  if config.var('TRANSLATION_CONSOLE'):
    # The path after "-translationconsole" is appended to
    # /root/googledata/html/intl.  On exsite, /root/googledata
    # is a symlink to /export/hda3/googledata.  TC messages files
    # live at /export/hda3/local/translationConsole/intl1.cl
    command_line.Add("-translationconsole=/../../../local/translationConsole/intl1 ")
  if config.var('CJK_CONFIG'):
    command_line.Add("-cjk_config=%s " % config.var('DATA_DIRS')['cjk_config_gws'])
  if config.var('BTVERSION'):
    command_line.Add("-bt_version=%s " % config.var('BTVERSION'))
  if config.var('USE_TRANSLATION'):
    command_line.Add("-translation=%d " % config.var('USE_TRANSLATION'))
  if config.var('USE_RESULTLOG'):
    command_line.Add("-writeresultlog ")
  if config.var('USE_RESULTLOG_SAMPLING'):
    command_line.Add("-resultloginterval=%d " % config.var('USE_RESULTLOG_SAMPLING'))
  if config.var('USE_SESSIONINFO_LOGGING'):
    command_line.Add("-writeresultstourllog ")
  if config.var('USE_ADS'):
    command_line.Add("-ads=%d " % config.var('USE_ADS'))
  # TODO: Remove obsolete USE_ADSLATER and "-adslater" after gws push end of Nov 2002
  if config.var('USE_ADSLATER'):
    command_line.Add("-adslater=%d " % config.var('USE_ADSLATER'))
  if config.var('USE_CONTENT_AD'):
    command_line.Add("-contentad=%d " % config.var('USE_CONTENT_AD'))
  if config.var('CONTENT_AD_TIMEOUT'):
    command_line.Add("-content_ads_timeout=%d " % config.var('CONTENT_AD_TIMEOUT'))
  if config.var('USE_CATS'):
    command_line.Add("-cats=%d " % config.var('USE_CATS'))
  if config.var('USE_CATRESTRICT_BYNAME'):
    command_line.Add("-use_catrestrict_byname")
  if config.var('USE_ODPCAT'):
    command_line.Add("-nb_cats=%d " % config.var('USE_ODPCAT'))
  if config.var('TRACE_FREQ'):
    command_line.Add("-tracefreq=%d " % config.var('TRACE_FREQ'))
  if config.var('USE_ONEBOX'):
    command_line.Add("-onebox=%d " % config.var('USE_ONEBOX'))
  if config.var('USE_ONEBOXWPRES'):
    command_line.Add("-onebox_res_whitepages=%d " % config.var('USE_ONEBOXWPRES'))
  if config.var('USE_ONEBOXWPBIZ'):
    command_line.Add("-onebox_biz_whitepages=%d " % config.var('USE_ONEBOXWPBIZ'))
  if config.var('USE_ONEBOX_O3_COMMAND'):
    command_line.Add("-gws_onebox_use_o3_command")
  if config.var('USE_GLOSSARY'):
    command_line.Add("-glossary")
  if config.var('USE_QUICKLINKS'):
    command_line.Add("-quicklinks")
  if config.var('USE_FROOGLE'):
    command_line.Add("-froogle")
  if config.var('USE_ENTERPRISE_ONEBOX'):
    command_line.Add("-onebox_enterprise=%d " % config.var('USE_ENTERPRISE_ONEBOX'))
  if config.var('MAX_FILTERED_RESULTS'):
    command_line.Add("-max_filtered_results=%d " % config.var('MAX_FILTERED_RESULTS'))
  if config.var('MAX_APPROX_DUPS_DIST'):
    command_line.Add("-maxapproxdupsdist=%d " % config.var('MAX_APPROX_DUPS_DIST'))
  if config.var('CUTOFF_FOR'):
    command_line.Add("-cutoff_for=%s " % config.var('CUTOFF_FOR'))
  if config.var('NO_HOSTIDS'):
    command_line.Add("-nohostids")
  if config.var('SERVING_USENET'):
    command_line.Add("-isusenet -postinghost=posting.google.com")
    command_line.Add("-badips_fn=../usenet_badips")
  if config.var('SERVING_NEWS'):
    command_line.Add("-isnews")
  if config.var('SERVING_ADVANCED_NEWS_SEARCH'):
    command_line.Add("-adv_news_search")
  if config.var('USE_64BIT_DOCIDS'):
    command_line.Add("-use_64bit_docids")
  if config.var('ALL_SERVICES_FOR_64BIT_DOCIDS'):
    command_line.Add("-all_services_for_64bit_docids")
  if config.var('SERVING_IMAGE'):
    command_line.Add("-isimages")
  if config.var('USE_NEW_IMAGE_UI'):
    command_line.Add("-show_new_image_ui")
  if config.var('GWS_ROTATE_LOGS'):
    # on the virtual GSALite, keep logs small (10MB)
    if config.var('ENT_CONFIG_TYPE') == 'LITE':
      command_line.Add("-gwslog_rotate_size=10000000")
    else:
      command_line.Add("-gwslog_rotate_daily")
  if config.var('GWS_NO_DEFAULT_DEBUGIPS'):
    command_line.Add("-noload_int_debugips")
  if not config.var('KEEP_STOPWORDS'):
    command_line.Add("-obeystopwordsinphrases")
  if not config.var('THE_IS_SPECIAL'):
    command_line.Add("-notheisspecial")
  if config.var('CHINESE_NAME_HACK'):
    command_line.Add("-chinesenamefix=1")
  if config.var('GWS_HEALTHZ_IGNORES_BAD_BACKENDS'):
    command_line.Add("-healthz_ignores_bad_backends")
  if config.var('GWS_NUMBERINDEX'):
    command_line.Add("--numberindex=%s" % config.var('GWS_NUMBERINDEX'))
  if config.var('PARTIAL_BACKEND_RESULTS_ALLOWED'):
    command_line.Add("--partial_backend_results_allowed")
  if config.var('GWS_FORCED_HEALTH_PAGE'):
    command_line.Add("-forced_health_page")
  if config.var('GWS_WEB_MAXRESULTS_PER_PAGE'):
    command_line.Add("--web_maxresults_per_page=%s" % \
                     config.var("GWS_WEB_MAXRESULTS_PER_PAGE"))
  if config.var('GWS_YAHOO_WEB_MAXRESULTS_PER_PAGE'):
    command_line.Add("--yahoo_web_maxresults_per_page=%s" % \
                     config.var("GWS_YAHOO_WEB_MAXRESULTS_PER_PAGE"))
  if config.var('GWS_PARTNER_WEB_MAXRESULTS_PER_PAGE'):
    command_line.Add("--partner_web_maxresults_per_page=%s" % \
                     config.var("GWS_PARTNER_WEB_MAXRESULTS_PER_PAGE"))
  if config.var('GWS_PARTNER_MAX_RESULTS'):
    command_line.Add("--partner_max_results=%s" % \
                     config.var("GWS_PARTNER_MAX_RESULTS"))
  if config.var('GWS_YAHOO_MAX_RESULTS'):
    command_line.Add("--yahoo_max_results=%s" % \
                     config.var("GWS_YAHOO_MAX_RESULTS"))
  if config.var('GWS_MAX_PARTNER_DOCFETCH'):
    command_line.Add("--max_partner_docfetch=%s" % \
                     config.var("GWS_MAX_PARTNER_DOCFETCH"))
  if config.var('GWS_APPLY_QREWRITE'):
    command_line.Add("--apply_qrewrite")
  if config.var('GWS_FULL_STEMMING'):
    command_line.Add("--full_stemming")
  if config.var('GWS_USE_ENGLISH_SYNS'):
    command_line.Add("--use_english_syns")
  if config.var('GWS_INDEX_PROTO_TO_MIXER'):
    command_line.Add("--send_indexcommand_proto_to_mixer")
  if config.var('GWS_PARSEDQUERYBEFOREREWRITE'):
    command_line.Add("--send_parsedquerybeforerewrite")
  if config.var('GWS_SEXPR_TO_DOCSERVER'):
    command_line.Add("--sexpr_to_docserver")
  if config.var('MAX_QUERY_TERMS'):
    command_line.Add("-max_terms=%d " % config.var('MAX_QUERY_TERMS'))
  if config.var('EXTRA_GWS_ARGS'):
    command_line.Add(config.var('EXTRA_GWS_ARGS'))
  if config.var('GWS_TIMEOUT_PROPAGATION'):
    command_line.Add("-timeout_propagation")
  if config.var('ENCRYPTED_IPS_SUFFICE'):
    command_line.Add("-encrypted_ips_suffice")
  if config.var('SHOW_REGION_NAMES'):
    command_line.Add("--show_local_geo_targets")
  if config.var('USE_CJK_UNIGRAM_MODEL'):
    command_line.Add("--use_cjk_unigram_model")
  if config.var('USE_NAV_BOOST'):
    command_line.Add("-use_nav_boost")
  if config.var('USE_PHIL_BOOST'):
    command_line.Add("-use_phil_boost")
  if config.var('USE_LANG_DEMOTION'):
    command_line.Add("-langdemotion")
  if config.var('USE_FUZZY_OPERATOR'):
    command_line.Add("-allow_fuzzy_operator")
  if not config.var('USE_C2C'):
    command_line.Add("-c2c=false ")
  if not config.var('USE_JA_VARIANTS'):
    command_line.Add("-nousejavariants")
  if config.var('USE_GERMAN_VARIANTS'):
    command_line.Add("-use_devariants")
  if config.var('REMOVE_CHINESE_INVISIBLE_QUOTE'):
    command_line.Add("-remove_chinese_invisible_quote")
  if config.var('REMOVE_JAPANESE_INVISIBLE_QUOTE'):
    command_line.Add("-remove_japanese_invisible_quote")
  if config.var('REMOVE_KOREAN_INVISIBLE_QUOTE'):
    command_line.Add("--remove_korean_invisible_quote")
  if config.var('USE_KOREAN_STEMMING'):
    command_line.Add("--use_korean_stemming")
  if config.var('I18NPORN_DEMOTION'):
    command_line.Add("--i18nporn_demotion")
  if config.var('USE_SEXPRESSIONS'):
    command_line.Add("--always_sexpr")
  if config.var('USE_EXPLICIT_NODE_TAGS'):
    command_line.Add("-use_explicit_node_tags")
  if config.var('USE_CATALOGS'):
    if config.var('SCAN_DB'):
      command_line.Add("-catalog=%s " % config.var('SCAN_DB'))
    else:
      command_line.Add("-catalog= ")
  if config.var('LOAD_BALANCE'):
    command_line.Add("--loadbalance=%d " % config.var('LOAD_BALANCE'))
  if config.var('USE_RTSIGNALS')['gws']:
    command_line.Add("--rtsignals ")
  if config.var('USE_COMMERCIAL_FILTER'):
    command_line.Add("--use_commercial_filter ")
  if config.var('COMMERCIAL_FILTER_VERSION'):
    command_line.Add("--commercial_filter_version=%d " % config.var('COMMERCIAL_FILTER_VERSION'))
  if config.var('COMMERCIAL_FILTER'):
    command_line.Add("--commercial_filter=%s " % config.var('COMMERCIAL_FILTER'))
  if config.var('USE_GERMAN_COMMERCIAL_FILTER'):
    command_line.Add("--use_german_commercial_filter ")
  if config.var('USE_CLUSTER_DEMOTION'):
    command_line.Add("--use_cluster_demotion ")
  if config.var('REDIRECT_UNTRUSTED_CONTENT'):
    # We redirect untrusted content to an IP address to protect our cookies
    try:
      command_line.Add("-untrusted_content_host=%s " % IPOfLocalVIP("gfe"))
    except ValueError:
      raise ValueError, "Can't redirect untrusted content"
  if config.var('USE_SITE_AS_MAPRESTRICT'):
    command_line.Add("--site_as_maprestrict ")

  if config.var('DO_PATH_CLUSTERING'):
    command_line.Add("-path_clustering ")

  if config.var('MAX_CROWDING_DEPTH'):
    command_line.Add("--max_crowding_depth=%d" %
                     config.var('MAX_CROWDING_DEPTH'))

  # add timeouts if specified
  if config.var('GWS_BACKEND_TIMEOUTS_IN_SEC'):
    timeouts = config.var('GWS_BACKEND_TIMEOUTS_IN_SEC')
    timeout_specs = []
    for key in timeouts.keys():
      timeout_specs.append("%s:%s" % (key, timeouts[key]))
    # endfor key
    if timeout_specs:
      command_line.Add("--backend_timeouts_in_sec=%s" %
                       string.join(timeout_specs, ","))
    # endif timeout_specs
  # endif GWS_BACKEND_TIMEOUTS_IN_SEC
  if config.var('ISSUE_64_BIT_LINK_REQUESTS'):
    command_line.Add("--issue_64_bit_link_requests")

  if config.var('I18N_ONEBOXNEWS'):
    command_line.Add("--enable_foreign_onebox_news")

  if config.var('I18N_ONEBOXNEWS_LANGUAGENAME_LIST'):
    command_line.Add("--onebox_news_foreign_languages=%s" % config.var('I18N_ONEBOXNEWS_LANGUAGENAME_LIST'))

  if config.var('NEWS_EMERGENCY_MODE'):
    command_line.Add("--news_emergency_mode")

  # provide the sekulite config filename for gws.
  if config.var('ENABLE_REALTIME_SEKULITE') and \
     config.var('CRAWL_USERPASSWD_CONFIG'):
    command_line.Add("--sekulite_userpasswd_config=%s" %
                     config.var('CRAWL_USERPASSWD_CONFIG'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and \
     config.var('SSO_PATTERN_CONFIG'):
    command_line.Add("--sso_pattern_config=%s" %
                     config.var('SSO_PATTERN_CONFIG'))

  if config.var('GWS_USE_BLOBS_FOR_DOCCOMMAND'):
    command_line.Add("--use_blobs_for_doccommand")

  if config.var('APPEND_BIGINDEX_RESULTS')['gws']:
    command_line.Add("--append_bigindex_results")

  if config.var('DISPLAY_SUPPLEMENTAL_TAG'):
    command_line.Add("--display_supplemental_tag")

  if config.var('GWSLOG_WRITEPROTO'):
    command_line.Add("--gwslog_writeproto")

  if config.var('GWSLOG_WRITEPROTO_ALL'):
    command_line.Add("--gwslog_writeproto_all")

  if config.var('GWS_USE_CALCULATOR'):
    command_line.Add("--calc")

  if config.var('NEWS_EDITIONS'):
    command_line.Add("--news_editions=%s " % config.var('NEWS_EDITIONS'));

  if config.var('NEWSALERTS_LANGUAGES'):
    command_line.Add("--newsalerts_languages=%s " % \
                     config.var('NEWSALERTS_LANGUAGES'));

  if config.var('USE_MIXER_FOR_RELATED'):
    command_line.Add('--use_mixer_for_related')

  if config.var('ALWAYS_RESOLVE_HOSTNAME'):
    command_line.Add("--always_resolve_hostname=true ");

  if config.var('CAN_GEOSEARCH'):
    command_line.Add("--can_geosearch=true ");

  if config.var('MAPURL_PREFIX'):
    command_line.Add("--mapurl_prefix=%s " % config.var('MAPURL_PREFIX'));

  if config.var('NUMRANGE'):
    command_line.Add("--allow_numrange_queries ");

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add('--trusted_clients=%s' %
                     string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'),
                                 ','))

  if config.var('ENTERPRISE'):
    # Enterprise uses text logs, not Sawmill
    command_line.Add('--gwslog_writetext')
    command_line.Add('--gwslog_writeproto=false')
    command_line.Add('--gwslog_writeproto_all=false')
    # Don't use google.com sites: news, catalogs, images, etc.
    command_line.Add('--use_google_sites=false')
    # Don't validate top level domain names:
    command_line.Add('--validate_tld=false')
    command_line.Add('--rewrite_language')
    command_line.Add('--show_result_cache_encoding_in_xml=true')
    command_line.Add('--enable_spellmixer=true')

  command_line.Add('--load_experiment_defaults_only')
  command_line.Add('--disable_misconfigured_experiments_on_load')

  # In enterprise, we limit the size of the indexed page to 2.5M,
  # so we unset this limit in gws.
  command_line.Add('--max_cache_page_size_to_show_link=-1')

  if config.var('GWS_USE_SUPERROOT'):
    command_line.Add('--enable_superroot=true')
    command_line.Add('--test_superroot=true')
    command_line.Add('--superroot_name=EntFedRoot')
    command_line.Add('--superroot_timeout_in_ms=10000')
  # sleep for 11s before kill -9 to allow enough time for query drain
  return progname + command_line.ToString() + webargs

servertype.RegisterRestartFunction('web', restart_web)

#------------------------------------------------------------------------------
# MIXER
#------------------------------------------------------------------------------

def get_mixerargs(config):

  srv_mngr = config.GetServerManager()
  cmdline = cli.CommandLine()

  levels_with_64bit_docids = []

  if config.var('MIXER_LEVELS_WITH_64BIT_DOCIDS'):
    for (lvl, has_64bit_docids) in \
        config.var('MIXER_LEVELS_WITH_64BIT_DOCIDS').items():
      if has_64bit_docids:
        levels_with_64bit_docids.append(str(lvl))
  else:
    # Figure out which levels are rtservers, and so require setting their level
    # in the levels_with_64bit_docids flag:
    # Get base ports of the levels we care about, and see if it's in servers.
    # (Starting mixers on these rt servers is for BART testing.)
    # HACK: Each rttype corresponds to a distinct level
    # so use the sequence in the rtlevels list to determine this.
    RTLEVELS = [ 'base_indexer', 'daily_indexer', 'rt_indexer' ]
    for level in xrange(len(RTLEVELS)):
      bartx = RTLEVELS[level]
      if srv_mngr.Set(bartx):
        levels_with_64bit_docids.append(str(level))

  if len(levels_with_64bit_docids) > 0:
    cmdline.Add("--levels_with_64bit_docids=%s" % \
                string.join(levels_with_64bit_docids, ','))

  # Get backends for mixer.
  set = srv_mngr.Set('mixer')
  (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

  if config.var('USE_MIXER_DUPS'):
    cmdline.Add("-local_duphosts=/bigfile/dups")

  if config.var('USE_TWIDDLESERVER'):
    if config.var('TWIDDLE_CONFIG'):
      cmdline.Add("-twiddle_config=%s" % config.var('TWIDDLE_CONFIG'))

  if config.var('USE_MIXER_NUMBER_DICTIONARY'):
    cmdline.Add("-numberindex=number_dictionary_packed")

  cmdline.Add("--backends=%s" % backends.AsString())
  cmdline.Add("--shardinfo=%s" % shardinfo.AsString())

  if config.var('USE_RTSIGNALS')['mixer']:
    cmdline.Add("--rtsignals")

  # Adjust port ranges for preprod sandboxes.
  sandbox_offset = servertype.GetSandBoxOffset()
  if sandbox_offset:
    cmdline.Add("-port=%d" % (4000 + sandbox_offset))

  # optimization to reduce cpu load on usenet mixers. usenet has no
  # categories anyways
  if config.var('SERVING_USENET'):
    cmdline.Add("--scavenge_category_results=false")

    # turn on long doc caching (the new threads interface is doc hungry)
    cmdline.Add("--cache_long_doc_results")

  # TODO: Remove this when we no longer do this in the mixer.
  if config.var('MERGE_MAX_IR'):
    cmdline.Add("--merge_max_ir")

  # Limit the throughput of the mixer. This is mainly used to limit the
  # throughput of the quality mixer.
  if config.var('MIXER_LIMIT_REQUESTS'):
    cmdline.Add("--limit_requests")

  if config.var('BIGINDEX_RATE_LIMIT'):
    cmdline.Add("--limit_requests")
    cmdline.Add("--max_indexrequests_hour=36000")
    cmdline.Add("--max_indexrequests_minute=1200")
    cmdline.Add("--max_docfetches_hour=36000")
    cmdline.Add("--max_docfetches_minute=1200")
    cmdline.Add("--max_docrequests_hour=36000")
    cmdline.Add("--max_docrequests_minute=1200")
    cmdline.Add("--max_linkrequests_hour=900000")
    cmdline.Add("--max_linkrequests_minute=20000")

  if config.var('MIXER_USE_BIGINDEX'):
    cmdline.Add("--use_bigindex=true")

  if config.var('MAX_RESULTS_TO_USE_BIGINDEX'):
    cmdline.Add("--max_results_to_use_bigindex=%d" %
                config.var('MAX_RESULTS_TO_USE_BIGINDEX'))

  if config.var('DONT_USE_BIGINDEX_IF_ZERO_RESULTS'):
    cmdline.Add("--use_bigindex_if_zero_results=false")

  bigindex_timeouts = config.var('BIGINDEX_TIMEOUTS_IN_MS')
  if bigindex_timeouts['index']:
    cmdline.Add("--bigindex_index_timeout_in_ms=%d" %
                bigindex_timeouts['index'])
  if bigindex_timeouts['doc']:
    cmdline.Add("--bigindex_doc_timeout_in_ms=%d" %
                bigindex_timeouts['doc'])
  if bigindex_timeouts['cache']:
    cmdline.Add("--bigindex_cache_timeout_in_ms=%d" %
                bigindex_timeouts['cache'])

  if config.var('APPEND_BIGINDEX_RESULTS')['mixer']:
    cmdline.Add("--append_bigindex_results")

  if config.var('BIGINDEX_MIXER'):
    cmdline.Add("--bigindex_mixer")

  if config.var('MIXER_CLIENT_PRIORITIES'):
    cmdline.Add("--client_priorities=%s" %
                config.var('MIXER_CLIENT_PRIORITIES'))

  if config.var('MIXER_QOS_LATENCY_PADDING'):
    cmdline.Add("--latency_padding=%s" %
                config.var('MIXER_QOS_LATENCY_PADDING'))

  return cmdline.ToString()

# This sets the params for enterprise mixer.
# - we answer on only one port and we compute the ports differently
# - we run a mixer per indexserver/docserver/linkserver set
# - we also have to change the portbase in mixer to specify where to look
# for our doc/index/link server ports
#
# enterprise is converted to shardinfo style arguments. Ok'ed by
# cpopescu.
def get_ent_mixerargs(config, mixhost, mixport):

  # TODO:
  # The following is forcing the 'backends' map for this
  # to a specific value.  It's probably better to use the defaults
  # for mixer or explicitly define this in the config - but this
  # is up to ENTERPRISE to test and try out.

  # Get backends for mixer.
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('mixer')
  port_shift = 100 * (set.PortBase() - servertype.GetPortBase('mixer'))

  if 'rtsubordinate' in map(lambda x: x.name(), srv_mngr.Sets()):
    rt_backends = [
      { 'set' : 'rtsubordinate', 'serve_as' : 'index', 'numconn' :
          config.var('MIXER_INDEX_NUMCONN'), 'level' : 0 },
      { 'set' : 'rtsubordinate', 'serve_as' : 'doc', 'numconn' :
          config.var('MIXER_DOC_NUMCONN'), 'level' : 0 },
      { 'set' : 'rtsubordinate', 'serve_as' : 'link', 'numconn' :
          config.var('MIXER_LINK_NUMCONN'), 'level' : 0 },
      { 'set' : 'cache',
        'level' : 0, 'protocol' : 'http' },
    ]
  else:
    # We talk to base_indexer only if we don't have any rtsubordinates left
    rt_backends = [
      { 'set' : 'base_indexer', 'serve_as' : 'index', 'numconn' : 3,
        'level' : 0, 'port_shift' : port_shift },
      { 'set' : 'base_indexer', 'serve_as' : 'doc', 'numconn' : 3,
        'level' : 0, 'port_shift' : port_shift },
      { 'set' : 'base_indexer', 'serve_as' : 'link', 'numconn' : 3,
        'level' : 0, 'port_shift' : port_shift },
      { 'set' : 'cache',
        'level' : 0, 'protocol' : 'http' },
    ]
  set.set_property('backends', rt_backends)

  set.set_property('numconns',
      {'index': config.var('MIXER_INDEX_NUMCONN'),
       'doc': config.var('MIXER_DOC_NUMCONN'),
       'link': config.var('MIXER_LINK_NUMCONN'),
       'cache': config.var('MIXER_CACHE_NUMCONN')})
  set.set_property('dflt_numconn', config.var('MIXER_DEFAULT_NUMCONN'))

  (shardinfo, backends) = set.BackendInfo(use_versions = 0)

  ### FIXIT: data version is kind of messy and needs a global cleanup
  ### now just hack the way through for enterprise
  real_data_version = '/export/hda3/enterprise-data'
  segment = set.property('segment')
  for i in (0, 1):
    if shardinfo.HasShard('index:%d' % i, segment):
      shardinfo.set_data_version('index:%d' % i, segment, real_data_version)
    if shardinfo.HasShard('doc:%d' % i, segment):
      shardinfo.set_data_version('doc:%d' % i, segment, real_data_version)
    if shardinfo.HasShard('link:%d' % i, segment):
      shardinfo.set_data_version('link:%d' % i, segment, real_data_version)

  cmdline = cli.CommandLine()

  if backends.HasBackEnds():
    cmdline.Add("--backends=%s" % backends.AsString())
    cmdline.Add("--shardinfo=%s" % shardinfo.AsString())

  cmdline.Add("--port=%d" % (mixport))
  cmdline.Add("--levels_with_64bit_docids=0,1")
  # ports where to answer status - default port + 2
  cmdline.Add("--status_port=%d" % (mixport + 2))
  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    cmdline.Add("--trusted_clients=%s" %
            string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # Set proper mixer retry count at ClientRPCID::CLONESET_LEVEL.
  # In case of failures, we will retry (number of RTSubordinate clones - 1) times.
  tmp_entconfig = entconfig.EntConfig(ent_home = None, writable = 0)
  num_retries = tmp_entconfig.GetNumRTSubordinateClones(len(srv_mngr.Hosts())) - 1
  cmdline.Add("--ent_cloneset_num_retries_on_timeout=%d" % num_retries)
  cmdline.Add("--ent_cloneset_num_retries_on_error=%d" % num_retries)

  # Set Enterprise specific timeout values for RTSubordinate index server and
  # RTSubordinate doc server, so that the above retries will be meaningful.
  if len(srv_mngr.Hosts()) > 1:
    # Set shorter timeouts on cluster, because we can retry on clones
    cmdline.Add("--ent_index_server_timeout_in_ms=%d" % 5000)
    cmdline.Add("--ent_doc_server_timeout_in_ms=%d" % 5000)
  else:
    # Set longer timeouts on oneways and minis
    cmdline.Add("--ent_index_server_timeout_in_ms=%d" % 20000)
    cmdline.Add("--ent_doc_server_timeout_in_ms=%d" % 20000)

  if config.var('USE_RTSIGNALS')['mixer']:
    cmdline.Add("--rtsignals")

  # Since we only have 1 backend shard (no clusters), mixer should
  # always stay healthy. It minimizes number of useless restarts
  # and open/closed connections. See CL 7261625 for more info.
  cmdline.Add("--required_fraction_shards_healthy=0")

  return cmdline.ToString()

def restart_mixer(config, host, port):
  command_line = cli.CommandLine()
  if config.var('ENTERPRISE'):
    mixer_args = get_ent_mixerargs(config, host, port)
  else:
    mixer_args = get_mixerargs(config)

  my_data_dir = config.GetDataDir(port)

  cutoff_list = []
  if config.var('DOCID_CUTOFFS') != None:
    cutoffs = config.var('DOCID_CUTOFFS')        # just as a shortcut
    for qos_class in cutoffs.keys():
      # get the cutoff (expand shortcuts if needed) and append it to the list
      cutoff = servertype.ExpandCutoff(cutoffs[qos_class])
      cutoff_list.append("%s:%s" % (qos_class, cutoff))

  percentage_cutoff_list = []
  if config.var('MIXER_CLIENT_PERCENTAGE_CUTOFFS') != None:
    cutoffs = config.var('MIXER_CLIENT_PERCENTAGE_CUTOFFS')# just as a shortcut
    for client_string in cutoffs.keys():
      percentage_cutoff_list.append("%s:%s" %
                                    (client_string, cutoffs[client_string]))
  #endif

  command_line.Add(ServerExecutablePrefix(config, "mixer", "--nobody"))
  command_line.Add("--status_port=%d" % servertype.GetServingPort(port))
  command_line.Add("--datadir=%s" % my_data_dir)
  if not config.var('USE_LCA'):
    command_line.Add("--use_lca=false")             # disable LCA scoring boost
  else:
    if config.var('USE_SORTED_MAP_SERVER').get('lcaserver', 0):
      # Enable sorted map server communication + disable the host id to map
      # because the sorted map server provides the ips also
      command_line.Add("--use_sorted_map_servers_for_lca")

  if config.var('TAINTED_DOCS_THRESHOLD'):
    command_line.Add("--tainted_percentdocs_threshold=%d" %
                     config.var('TAINTED_DOCS_THRESHOLD'))

  if cutoff_list:
    cutoff_list.sort()   # enforce deterministic order to keep regtest happy
    command_line.Add("--qos_cutoffs=%s" % string.join(cutoff_list, ','))

  if percentage_cutoff_list:
    percentage_cutoff_list.sort()   # enforce deterministic order
    command_line.Add("--client_cutoffs=%s" %
                     string.join(percentage_cutoff_list, ','))
  # endif percentage_cutoff_list:

  command_line.Add(mixer_args)
  if config.var('MIXER_TALK_TO_IMGFREQ_SERVER'):
    command_line.Add("--talk_to_imgfreq_server")
  command_line.Add(config.var('EXTRA_MIXER_ARGS'))

  # If we serve links with sorted map servers, enable that kind of communication
  if config.var('USE_SORTED_MAP_SERVER').get('link', 0):
    command_line.Add("--use_sorted_map_servers_for_link")

  if config.var('MIXER_LCA_PAGERANK_CUTOFF'):
    command_line.Add("--lca_pagerank_cutoff=%s" %
                     config.var('MIXER_LCA_PAGERANK_CUTOFF'))

  if config.var('MILLION_DOCS_IN_REPOS'):
    command_line.Add("--n_million_docs_in_repository=%s" %
                     config.var('MILLION_DOCS_IN_REPOS'))

  if config.var('MIXER_MEMORY_FRACTION'):
    command_line.Add("--memory_fraction=%s" % config.var('MIXER_MEMORY_FRACTION'))

  if config.var('SEND_BACK_ALL_INDEX_RESULTS'):
    command_line.Add("--send_back_all_index_results")

  if config.var('MIXER_MAX_RESULTS'):
    command_line.Add("--max_results=%s" % config.var('MIXER_MAX_RESULTS'))

  if config.var('MIXER_LEVELS_INDEX_CACHE_EXP_IN_SEC'):
    list_items = map(
      lambda x: "%d:%d" % (x[0], x[1]),
      config.var('MIXER_LEVELS_INDEX_CACHE_EXP_IN_SEC').items())
    command_line.Add('--levels_index_cache_exp_in_sec=%s' % \
                     string.join(list_items, ','))

  if config.var('MIXER_DOC_CACHE_CHECK_DOCVERSIONID'):
    command_line.Add('--doc_cache_check_docversionid')

  # TODO: remove this when the dependency between the mixer and chubby
  # has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('mixer', restart_mixer)


#------------------------------------------------------------------------------
# CLUSTERINGSERVER (aka, clustering_server)
#------------------------------------------------------------------------------

def restart_clustering_server(config, host, port, sitename=None):
  set = config.GetServerManager().Set('clustering_server')

  args = (
    ' --port=%d' % servertype.GetServingPort(port) +
    ' --stopword_list_dir=%s/enterprise/data/' % config.var('GOOGLEDATA') +
    ' --nobinarylog')
  if config.var('CJKSEGMENTER'):
    args = args + (" --cjk_segmenter=%s" % config.var('CJKSEGMENTER'))
  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args = args + (" --trusted_clients=%s" %
            string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  webservers = serverflags.MakeHostPortsArg(
    set.BackendHostPorts('web'))
  if webservers:
    args = args + (
      ' --gws_servers=%s' % (webservers))

  # TODO: remove this when the dependency between the clustering
  # server and chubby has been broken.
  args += ' ' + string.join(LOCK_SERVICE_FLAGS)

  return (UlimitPrefix(config) +
          ServerExecutablePrefix(config, "clustering_server") + args)

servertype.RegisterRestartFunction('clustering_server', restart_clustering_server)


#------------------------------------------------------------------------------
# REWRITESERVER (aka, qrewrite)
#------------------------------------------------------------------------------

def restart_qrewrite(config, host, port, sitename=None):
  set = config.GetServerManager().Set('qrewrite')
  (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

  my_data_dir = config.var('GOOGLEDATA') + '/enterprise/qrewrite'

  cjk_config = config.var('QREWRITE_CJK_CONFIG')
  if cjk_config == None:
    cjk_config = config.var('GOOGLEDATA') + '/BasisTech'
  bt_version = config.var('BTVERSION')
  if bt_version == None:
    bt_version = ""

  args = (
    ' --port=%d' % servertype.GetServingPort(port) +
    # ' --datadir=%s' % my_data_dir +
    ' --nobinarylog')

  # These command-line parameters are intended for use in an ENTERPRISE
  # configuration (triggered by config.var('ENTERPRISE')).
  # The parameters used for qrewrite in production were removed, to
  # avoid obfuscation of this code, and also because they would soon
  # become obsolete, for they are not being updated for scripts in
  # enterprise/legacy.
  args = args + ( ' --rewrite_syns=true' +
    ' --prob_path=%s' % os.path.join(my_data_dir, 'ProbTerm.fp') +
    ' --querylangdist_path=%s' % os.path.join(my_data_dir, 'languages.txt') +
    # ' --googleclient_debugging=true' +
    # ' --httpclient_debugging=true' +
    # ' --logreq=true' +
    ' --rewrite_spelling=false' +
    ' --synonyms_mmap_bytes=2000000000' +
    ' --named_entities_num=20' +
    ' --name_bonus=0.500000' +
    ' --query_classifier_specs="Prob"' +
    ' --dont_req_orig=true' +
    ' --rtsignals=true' +
    ' --optionalize_words=true' +
    ' --name_to_non_name_synonyms=true'
    )
  # Note that if the compiled synonyms or blacklist files do not exist,
  # qrewrite continues harmlessly.
  # TODO(erocke): Do we need any of the context_syns_ flags set with special
  # values for enterprise search?  (Removing all & using defaults for now).
  qe_local, qe_contextual, qe_langs = config.GetQueryExpansionCapabilities()
  if qe_local:
    args = args + (
      ' --custom_syn_file=%s' % config.var('QUERY_EXP_COMPILED_SYNONYMS') +
      ' --custom_syn_languages=%s' % qe_langs +
      ' --syn_blacklist_file=%s' % config.var('QUERY_EXP_COMPILED_BLACKLIST') +
      ' --syn_blacklist_languages=%s' % qe_langs
      )

  if not qe_contextual:
    args = args + ( ' --cjk_config=/dev/null' +
      ' --detect_query_language=false' +
      ' --change_query_language=false' +
      ' --diacriticals_for_context_synonyms=false'
      )
  else:
    args = args + (' --cjk_config=%s' % cjk_config +
      ' --bt_version=%s' % bt_version +
      ' --context_syns_data_file=%s' % os.path.join(my_data_dir,
                                        'context_syns.sstable') +
      ' --diacriticals_syn_file=%s' % os.path.join(my_data_dir,
                                        'diacriticals.sstable') +
      ' --idf_sstable=true' +
      ' --syn_idf_filename=%s' % os.path.join(my_data_dir,
                                        'idf_table_nb.sstable') +
      ' --idf_filename=%s' % os.path.join(my_data_dir,
                                  config.var('QREWRITE_IDF_TABLE')) +
      ' --shared_per_lang_idf_table_filename=%s' % (
        os.path.join(my_data_dir, 'per_lang_idf_table.sstable')) +
      ' --shared_per_lang_doc_count_filename=%s' % (
        os.path.join(my_data_dir, 'per_lang_doc_count.sstable')) +
      ' --detect_query_language=true' +
      ' --change_query_language=true' +
      ' --syn_min_concepts_before_unrequire=0' +
      ' --diacriticals_for_context_synonyms' +
      ' --context_syns_max_source_len=2'
      )
    if config.var('QREWRITE_NB_IDF_TABLE') != None:
      args = args + (' --nb_idf_filename=%s' % os.path.join(my_data_dir,
                                            config.var('QREWRITE_NB_IDF_TABLE')))

    if config.var('QREWRITE_MAX_ALTS_PER_CONCEPT') != None:
      args = args + (' --max_alts_per_concept=%d' % (
        config.var('QREWRITE_MAX_ALTS_PER_CONCEPT')))

    if config.var('QREWRITE_SYN_ALT_CUTOFF') != None:
      args = args + (' --syn_alt_cutoff=%f' % (
        config.var('QREWRITE_SYN_ALT_CUTOFF')))
  # end of ENTERPRISE specific parameters.

  if config.var('CJKSEGMENTER') != None:
    args = args + (' --cjk_segmenter=%s' % config.var('CJKSEGMENTER'))

  if config.var('QREWRITE_ENFORCE_MAXTERMS') != None:
    if config.var('QREWRITE_ENFORCE_MAXTERMS'):
      args = args + (' --enforce_maxterms=true')
    else:
      args = args + (' --enforce_maxterms=false')

  if config.var('QREWRITE_FORCE_LOAD') != None:
    if config.var('QREWRITE_FORCE_LOAD') == 1:
      args = args + ' --force_load=true'
    else:
      args = args + ' --force_load=false'

  if config.var('QREWRITE_SYN_POSTERIOR_RESCALING') != None:
    args = args + (' --syn_posterior_rescaling=%f' % (
      config.var('QREWRITE_SYN_POSTERIOR_RESCALING')))

  if config.var('QREWRITE_MULTIWORD_CUTOFF_FUNCTION') != None:
    args = args + (' --multiword_cutoff_function=%s' % (
      config.var('QREWRITE_MULTIWORD_CUTOFF_FUNCTION')))

  if config.var('QREWRITE_SYN_CONTEXT_DB_FILENAME') != None:
    args = args + (' --syn_context_db_filename=%s' % os.path.join(
      my_data_dir,
      config.var('QREWRITE_SYN_CONTEXT_DB_FILENAME')))

  if config.var('QREWRITE_SYN_DB_FILENAME') != None:
    args = args + (' --syn_db_filename=%s' % os.path.join(
      my_data_dir,
      config.var('QREWRITE_SYN_DB_FILENAME')))

  if config.var('QREWRITE_SYN_MIN_CONCEPTS_BEFORE_UNREQUIRE') != None:
    args = args + (' --syn_min_concepts_before_unrequire=%d' % (
      config.var('QREWRITE_SYN_MIN_CONCEPTS_BEFORE_UNREQUIRE')))

  if config.var('QREWRITE_MAPNAMES') != None:
    args = args + (' --mapnames=%s' % (
      config.var('QREWRITE_MAPNAMES')))

  if config.var('QREWRITE_SUPPORT_PARSING') is not None:
    if config.var('QREWRITE_SUPPORT_PARSING'):
      args = args + (' --support_parsing=true')
    else:
      args = args + (' --support_parsing=false')

  if config.var('QREWRITE_USE_DEV_MEM') is not None:
    if config.var('QREWRITE_USE_DEV_MEM'):
      args = args + (' --use_dev_mem=true')
    else:
      args = args + (' --use_dev_mem=false')

  if config.var('QREWRITE_DEV_MEM_STATE_FILE') is not None:
    args = args + (' --dev_mem_state_file=%s' % (
      config.var('QREWRITE_DEV_MEM_STATE_FILE')))

  if config.var('QREWRITE_REMOVE_DUPS_FAST'):
    args = args + (' --remove_dups_fast')

  # Enable when rewrite server starts talking with phil
  if config.var('QREWRITE_PHIL_STOP_CLUSTERS_FILE') != None:
    args = args + (' --stop_clusters_file=%s' %
                   os.path.join(my_data_dir,
                               config.var('QREWRITE_PHIL_STOP_CLUSTERS_FILE')))

  if config.var('QREWRITE_PHIL_IDF_FILE') != None:
    args = args + (' --clusters_frequency_file=%s' %
                   os.path.join(my_data_dir,
                                config.var('QREWRITE_PHIL_IDF_FILE')))

  if config.var('QREWRITE_PHIL_IDF_SLOPE') != None:
    args = args + (' --idf_slope=%f' % (
      config.var('QREWRITE_PHIL_IDF_SLOPE')))

  if config.var('QREWRITE_PHIL_IDF_MIDPOINT') != None:
    args = args + (' --idf_midpoint=%f' % (
      config.var('QREWRITE_PHIL_IDF_MIDPOINT')))

  if config.var('QREWRITE_PHIL_ADDITIVE_ACTIVATION') != None:
    args = args + (' --additive_activation=%f' % (
      config.var('QREWRITE_PHIL_ADDITIVE_ACTIVATION')))

  if config.var('QREWRITE_PHIL_ACTIVATION_SQUASHING') != None:
    args = args + (' --activation_squashing=%f' % (
      config.var('QREWRITE_PHIL_ACTIVATION_SQUASHING')))

  if config.var('QREWRITE_PHIL_TIMEOUT_IN_MS') != None:
    args = args + (' --phil_timeout_ms=%d' % (
      config.var('QREWRITE_PHIL_TIMEOUT_IN_MS')))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args = args + (" --trusted_clients=%s" %
                   string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'),
                               ','))

  # TODO: remove this when the dependency between the qrewrite server
  # and chubby has been broken.
  args += ' ' + string.join(LOCK_SERVICE_FLAGS)

  if backends.HasBackEnds():
    args = args + (
      ' --backends=%s' % (backends.AsString()) +
      ' --shardinfo=%s' % (shardinfo.AsString()))

  return (UlimitPrefix(config) +
          ServerExecutablePrefix(config, "qrewrite") + args)

servertype.RegisterRestartFunction('qrewrite', restart_qrewrite)

#------------------------------------------------------------------------------
# ENTFRONTEND
#------------------------------------------------------------------------------

def restart_entfrontend(config, host, port):
  cl = cli.CommandLine()
  cl.Add(UlimitPrefix(config))

  binary_name = servertype.GetBinaryName('entfrontend')
  libsdirs = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name))

  libsdirs = '%s:%s' % (os.path.join(config.var('MAINDIR'), 'bin'), libsdirs)
  swigdeps = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name),
                          'EnterpriseFrontend_swigdeps.so')

  # Generate the Java command to execute
  classpath = ('%s/bin/EnterpriseFrontend.jar:'
               '%s/third_party/java/saxon/saxon.jar') % (
                     config.var('MAINDIR'), config.var('MAINDIR'))
  jvm_cl = cli.CommandLine()
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.security.manager')
  jvm_cl.Add('-Djava.security.policy=%s/bin/java.policy' %
             config.var('MAINDIR'))
  jvm_cl.Add('-Djavax.xml.parsers.SAXParserFactory='
             'com.icl.saxon.aelfred.SAXParserFactoryImpl')
  jvm_cl.Add('-Djava.library.path=%s' % libsdirs)
  jvm_cl.Add('-Dswigdeps=%s' % swigdeps)
  # EnterpriseFrontend uses java.util.logging, but also uses libraries that
  # still use Log2.  Setting this causes Log2 log records to use
  # java.util.logging, so that things will get logged to the same set of log
  # files.  See
  # http://wiki.corp.google.com/twiki/bin/view/Main/JavaLogging
  # #3_2_Log2_Command_Line_Options for details.
  jvm_cl.Add('-Dgoogle.log2UseJavaLog=true')

  cl.Add(JavaServerExecutablePrefix(config, 'entfrontend', jvm_cl.ToString(),
         '--rundir=%s --lognamesuffix=jar' % config.var('MAINDIR'),
         run_as_class=1))

  # Add the EnterpriseFrontend options
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('entfrontend')
  webservers = set.BackendHostPorts('web')
  feedergateservers = set.BackendHostPorts('feedergate')
  enttableservers = set.BackendHostPorts('enttableserver')
  fsgws = set.BackendHostPorts('fsgw')
  clusteringservers = set.BackendHostPorts('clustering_server')

  # All things related to personalization (and User Account
  # Management)
  if config.var('UAM_DIR'):
    cl.Add('--personalization_dir=%s' % config.var('UAM_DIR'))
  if config.var('ALERTS2') == 1:
    cl.Add('--alerts2=true')
  else:
    cl.Add('--alerts2=false')
  if config.var('CLICKLOGGING') == 1:
    cl.Add('--clicklogging=true')
  else:
    cl.Add('--clicklogging=false')
  if config.var('ENTERPRISE_COLLECTIONS_DIR'):
    cl.Add("--collections_directory=%s" %
           config.var('ENTERPRISE_COLLECTIONS_DIR'))
  else:
    raise ValueError("Must specify collections directory for collections")

  cl.Add('--port=%d' % servertype.GetServingPort(port))
  cl.Add("--gws_servers=%s" % serverflags.MakeHostPortsArg(webservers))
  cl.Add("--feedergate_servers=%s" %
         serverflags.MakeHostPortsArg(feedergateservers))
  if len(enttableservers) > 0:
    cl.Add('--table_server=%s' %
           serverflags.MakeHostPortsArg(enttableservers))
  cl.Add('--filesystem_servers=%s' %
         serverflags.MakeHostPortsArg(fsgws))
  if clusteringservers:
    cl.Add('--clustering_server=%s' %
          serverflags.MakeHostPortsArg(clusteringservers))

  # Number of threads to talk to backends
  cl.Add('--num_threads=%d' % config.var('ENTFRONT_NUM_THREADS'))
  # Reject new connections if backlog is full.
  cl.Add('--max_backlogged_connections=%d' % config.var('ENTFRONT_NUM_THREADS'))

  # following flags are for SSL connections both as a server,
  # and as a client (to LDAP server).
  cl.Add("--keystore=%s" % config.var('ENTFRONT_KEY_STORE'))
  cl.Add('--trustedca_path=%s' % config.var('TRUSTED_CA_DIRNAME'))
  cl.Add('--crl_path=%s' % config.var('CRL_DIRNAME'))

  if config.var('AUTHENTICATE_CLIENT_CERT'):
    cl.Add('--require_client_auth')

  if config.var('ENTFRONT_EXTERNAL_PORT'):
    cl.Add("--external_port=%d" % config.var('ENTFRONT_EXTERNAL_PORT'))

  if ( config.var('ENTFRONT_SSL_PORT') and config.var('ENTFRONT_KEY_STORE') ):
    cl.Add("--ssl_port=%d" % config.var('ENTFRONT_SSL_PORT'))
    if config.var('ENTFRONT_EXTERNAL_SSL_PORT'):
      cl.Add("--external_ssl_port=%d" %
             config.var('ENTFRONT_EXTERNAL_SSL_PORT'))

    if config.var('FORCE_HTTPS') != None:
      cl.Add("--force_serving_https=%s" % config.var('FORCE_HTTPS'))

  if config.var('DISABLE_SEKULITE_AUTHZ'):
    cl.Add("--sekulite_authz=false")

  if config.var('CJK_UNIGRAM_MODEL'):
    cl.Add("--cjk_unigram_model=%s" % config.var('CJK_UNIGRAM_MODEL'))

  if config.var('ENABLE_REALTIME_SEKULITE') and \
     config.var('CRAWL_USERPASSWD_CONFIG'):
    cl.Add("--sekulite_userpasswd_config=%s" %
           config.var('CRAWL_USERPASSWD_CONFIG'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('SSO_SERVING_CONFIG'):
    cl.Add("--sso_serving_config=%s" % config.var('SSO_SERVING_CONFIG'))
    if config.var('USER_AGENT_TO_SEND'):
      cl.Add(servertype.mkarg("--user_agent='%s'" %
                              config.var('USER_AGENT_TO_SEND')))
  else:
    cl.Add("--sso_serving_config=")

  if config.var('PROXY_CONFIG'):
    cl.Add("--proxy_config=%s" % config.var('PROXY_CONFIG'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('SSO_PATTERN_CONFIG'):
    cl.Add("--sso_pattern_config=%s" % config.var('SSO_PATTERN_CONFIG'))

  if config.var('ENTFRONT_EXTRA_PORTS'):
    cl.Add("--extra_ports=%s" % string.join(
      map(str, config.var('ENTFRONT_EXTRA_PORTS')), ','))

  if config.var('LDAP_CONFIG'):
    cl.Add(" --ldap_config=%s" % config.var('LDAP_CONFIG'))

  if config.var('ENTFRONT_MESSAGE_FILE'):
    cl.Add(servertype.mkarg("--messages_file=%s" %
                            config.var('ENTFRONT_MESSAGE_FILE')))

  if config.var('ENTFRONT_STATICFILES_DIR'):
    cl.Add(servertype.mkarg("--static_files_dir=%s" %
                            config.var('ENTFRONT_STATICFILES_DIR')))

  if config.var('ENTFRONT_STYLESHEETS_DIR'):
    cl.Add(servertype.mkarg("--localstylesheetdir=%s" %
                            config.var('ENTFRONT_STYLESHEETS_DIR')))

  if config.var('ENTFRONT_TEST_STYLESHEETS_DIR'):
    cl.Add(servertype.mkarg("--localteststylesheetdir=%s" %
                            config.var('ENTFRONT_TEST_STYLESHEETS_DIR')))

  if config.var('ENTFRONT_FRONTENDS_DIR'):
    cl.Add(servertype.mkarg("--frontenddir=%s" %
                            config.var('ENTFRONT_FRONTENDS_DIR')))

  if config.var('CRAWL_LOGDIR'):
    cl.Add(servertype.mkarg("--log_file=%s/enterprisefrontend" %
                            config.var('CRAWL_LOGDIR')))

  # to turn on more verbose logging, this can be set to FINER, ALL, etc.
  cl.Add(servertype.mkarg("--log_level=INFO"))

  # on the virtual GSALite, keep logs small (10MB)
  if config.var('ENT_CONFIG_TYPE') == 'LITE':
    cl.Add('--log_file_limit=%d' % 10000000)
  else:
    # By default, previous logs are deleted. These flags are similar to what is
    # in logcontrol. Note that we have to pass the value of Integer.MAX_VALUE in
    # Java (32-bit), so we can't pass 2200000000 (value in logcontrol)
    cl.Add('--log_file_count=%d' % 20)
    cl.Add('--log_file_limit=%d' % JAVA_MAX_LOG_SIZE)

  if config.var('CJKCONFIGDIR'):
    cl.Add("--cjk_config=%s" % config.var('CJKCONFIGDIR'))

  if config.var('BTVERSION'):
    cl.Add("--bt_version=%s" % config.var('BTVERSION'))

  if config.var('GFS_ALIASES'):
    cl.Add(servertype.mkarg('--bnsresolver_use_svelte=false'))
    cl.Add(servertype.mkarg('--gfs_aliases=%s' % config.var('GFS_ALIASES')))

  if config.var('ENTFRONT_COLLECTION_EPOCH_PATTERNS'):
    cl.Add(servertype.mkarg("--collection_epoch_pattern=%s" %
                            config.var('ENTFRONT_COLLECTION_EPOCH_PATTERNS')))

  if config.var('DEFAULT_SEARCH_URL'):
    cl.Add(servertype.mkarg("--default_search_url=%s" % urllib.quote(config.var(
      'DEFAULT_SEARCH_URL'))))

  if config.var('ENT_LOG_QUERY_TIMINGS'):
    cl.Add('--log_efe_timings')

  if config.var('ENABLE_SINGLE_SIGN_ON') and \
     config.var('DO_SSO_SERVING_LOGGING'):
    cl.Add(servertype.mkarg("--do_sso_serving_logging"))
    cl.Add(servertype.mkarg("--sso_serving_efe_log_file=%s" %
                config.var('SSO_SERVING_EFE_LOG_FILE')))

  if config.var('AUTHN_LOGIN_URL'):
    cl.Add('--user_login_url=%s' % config.var('AUTHN_LOGIN_URL'))

  if config.var('AUTHN_ARTIFACT_SERVICE_URL'):
    cl.Add('--artifact_service_url=%s' %
           config.var('AUTHN_ARTIFACT_SERVICE_URL'))

  if config.var('AUTHN_COOKIE_TTL'):
    cl.Add('--authn_spi_cookie_ttl=%s' % config.var('AUTHN_COOKIE_TTL'))

  if config.var('CONNECTOR_CONFIGDIR'):
    cl.Add(servertype.mkarg('--connector_config_dir=%s' %
                                      config.var('CONNECTOR_CONFIGDIR')))

  if config.var('GSA_MASTER'):
    cl.Add('--gsa_main=%s' % config.var('GSA_MASTER'))

  if config.var('SESSIONMANAGER_ALIASES'):
    cl.Add('--sessionmanager_server=%s' %
           config.var('SESSIONMANAGER_ALIASES'))

  return cl.ToString()

servertype.RegisterRestartFunction('entfrontend', restart_entfrontend)

#------------------------------------------------------------------------------
# COMMON RT ROUTINES
#------------------------------------------------------------------------------

# calculate_rt_ports() - calculate the index/doc/link ports for the real time
# server. Each type has a base port specified in a dict called
# RT_BASE_PORTS.
#
# Returns a dictionary of type->port.
# Example, given port=31402 (rtsubordinate, level 1, shard 2) and
# RT_BASE_PORTS={'index':4000, 'doc':5000})
# Result is type_port_dict = {'index':4102, 'doc':5102, 'link':0}
#
def calculate_rt_ports(config, port):

  shard = servertype.GetPortShard(port)
  lvl = servertype.GetLevel(port)
  type_port_dict = {}
  required_types = ['index', 'doc', 'link'] # Add a 0 port for these if not set

  # First pass, set any required types to 0
  # TODO: the only reason for this bogosity is to allow get_oneboxargs
  # to say "if type_port_dict['index'] and type_port_dict['doc']"
  # without checking if the entries exist in the map. :-( This change
  # is already too complex to fix this crap too.
  for stype in required_types:
    type_port_dict[stype] = 0

  # Second pass, set the port
  for stype,base_port in config.var('RT_BASE_PORTS').items():

    lvl_size = servertype.GetLevelSize(stype)
    serving_port = base_port + shard + lvl*lvl_size
    # TODO: unify the port calculations across different server types
    type_port_dict[stype] = serving_port

  return type_port_dict

def get_rt_genericargs(config, host, port):

  global USE_VERSIONS

  # Create the args list, and put in the port argument.
  args = []
  shard = servertype.GetPortShard(port)

  if servertype.GetPortType(port) in ('scanjpg2', 'scanjpg3', 'scanjpg6',
                                      'scanjpg20', 'scandjvu', 'scaninfo',
                                      'scanjpg2main', 'scanjpg3main',
                                      'scanjpg6main', 'scanjpg20main',
                                      'scandjvumain', 'scaninfomain'):
    # if scanning rtserver, respond _only_ as a docserver on that port
    args.append('--docserver_port=%d' % servertype.GetServingPort(port))
    # Also, don't do any indexing, don't run index or link,
    # don't store repository, and aggressively cleanup.
    args.append('--indexserver_port=0')
    args.append('--linkserver_port=0')
    args.append('--rt_index=false')
    args.append('--rt_aggressive_cleanup=true')
  else:
    args.append('--port=%d' % servertype.GetServingPort(port))
    # Get a dict of the type/ports served by this rtserver, and create a
    # command line argument for each one:
    # For each type X in type_port_dict, create an --Xserver_port=<port> arg
    # (for example, --indexserver_port=4150)
    type_port_dict = calculate_rt_ports(config, port)
    for stype,sport in type_port_dict.items():
      args.append('--%sserver_port=%s' % (stype, sport))

  if (config.var('INDEXSERVER_ALARM_DELAY')):
    args.append('--alarm_delay=%s' % config.var('INDEXSERVER_ALARM_DELAY'))

  num_shards = config.GetNumShards(port)
  # Set the shard arguments (doc shard -- index shard is fixed to 0 for now)
  #
  args.append('--rt_doc_shard=%s' % shard)
  args.append('--num_rt_doc_shards=%s' % num_shards)

  if config.var('MAX_SNIPPET_DOCLEN'):
    args.append("--max_snippet_doclen=%s" % config.var('MAX_SNIPPET_DOCLEN'))

  if config.var('NAMESPACE_PREFIX'):
    if config.var('MACHINE_TYPE_FILESET'):
      machtype = config.var('MACHINE_TYPE_FILESET')
      args.append("--namespace_prefix=%s" % \
                  servertype.GenNamespacePrefix(config, machtype, shard,
                                                num_shards))
    elif config.var('RTSERVER_NAMESPACE_PREFIX_FROM_SERVERTYPE'):
      machtype = servertype.GetPortType(port)
      args.append("--namespace_prefix=%s" % \
                  servertype.GenNamespacePrefix(config, machtype, shard,
                                                num_shards))

  # Maybe add rfserver banks (if they are in the config)
  args = args + servertype.GetRfserverBankArgs(config)

  # Fetch values from datadirs that require special handling.
  #
  datadir = config.GetDataDir(port)
  if config.var('DATA_DIRS').has_key('cjk_config_rt'):
    cjk_dir = config.var('DATA_DIRS')['cjk_config_rt']
  else:
    cjk_dir = datadir
  args.append('--datadir=%s' % datadir)

  # Set the data_version
  #
  if USE_VERSIONS:
    dirname = googleconfig.GetDirName(datadir)
    data_version = '/export/hda3/%s-data' % \
                   googleconfig.GetShortDirName(dirname)
  else:
    data_version = ''
  args.append(" --data_version=%s" % data_version)

  args.append('--cjk_config=%s' % cjk_dir)
  args.append('--bt_version=%s' % config.var('BTVERSION'))
  args.append('--cjk_segmenter=%s' % config.var('CJKSEGMENTER'))

  if config.var('RTSERVER_ALSO_LOG_TO_STDERR') == 0:
    args.append('--alsologtostderr=false')
  else:
    args.append('--alsologtostderr')

  # Add more items that depend on config attributes.
  #
  index_prefix = config.var('INDEX_PREFIX')
  if config.var('INDEX_PREFIX_INCLUDES_SHARD'):
    index_prefix = '%s%s' % (index_prefix, servertype.GetPortShard(port))
  args.append('--index_prefix=%s' % index_prefix)
  args.append('--num_index_shards=%s' % config.var('NUM_INDEX_SHARDS'))
  args.append('--workerthreads=%s' % config.var('WORKERTHREADS'))
  if config.var('INDEX_WORKERTHREADS'):
    args.append('--index_workerthreads=%s' % config.var('INDEX_WORKERTHREADS'))
  args.append('--max_checkpoints_before_deletion=%s' %
                 config.var('MAX_CHECKPOINTS_BEFORE_DELETION'))

  if config.var('RTSERVER_NO_LOGGING') != None and config.var('RTSERVER_NO_LOGGING') == 1:
    args.append('--nologging') # we don't really care that we've opened another bigfile

  args.append('--nobinarylog')

  if config.var('RTSERVER_IGNORE_DOCID_SERVERS') == 0:
    args.append('--ignore_docidservers=false')
  else:
    args.append('--ignore_docidservers')

  if config.var('URLS_TO_IGNORE'):
    args.append('--urls_to_ignore=%s' % config.var('URLS_TO_IGNORE'))
  if config.var('BADURLS_NOPROPAGATE'):
    args.append('--badurls_nopropagate=%s' % config.var('BADURLS_NOPROPAGATE'))
  if config.var('BADURLS_DEMOTE'):
    args.append('--badurls_demote=%s' % config.var('BADURLS_DEMOTE'))
  if config.var('ENABLE_FIELD_SEARCH'):
    args.append("--fieldsearch_enabled")
  if config.var('RTSERVER_PROCESS_DOCS_IMMEDIATELY'):
    args.append('--process_docs_immediately')
  if config.var('RT_LOGREQ'):
    args.append('--logreq=true')
  if config.var('NUM_DOCID_LEVELS'):
    args.append('--num_docid_levels=%s' % config.var('NUM_DOCID_LEVELS'))
  if config.var('OVERRIDE_CHECKPOINT_NAMESPACE_PREFIX'):
    args.append('--override_checkpoint_namespace_prefix')
  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))
  if config.var('GFS_ALIASES'):
    args.append(servertype.mkarg("--bnsresolver_use_svelte=false"))
    args.append(servertype.mkarg('--gfs_aliases=%s' % \
                                 config.var('GFS_ALIASES')))
  if config.var('GFS_USER'):
    args.append('--gfs_user=%s' % config.var('GFS_USER'))
  if config.var('ENTERPRISE'):
    args.append("--enterprise=true")
  if config.var('FROOGLE_EXTRACT_SCORING_PARAMETERS'):
    args.append('--froogle_extract_scoring_parameters')
  if config.var('USE_CREATION_TIME') != None:
    if config.var('USE_CREATION_TIME'):
      args.append('--use_creation_time')
    else:
      args.append('--nouse_creation_time')
  if config.var('RTSERVER_TEMP_FILE_DIRECTORY'):
    args.append('--temp_file_directory=%s' %
                config.var('RTSERVER_TEMP_FILE_DIRECTORY'))

  # use froogle specific scoring weights.
  if config.var('FROOGLE_SCORING'):
    args.append('--froogle_scoring')

  # use principal word scoring.
  if config.var('PRINCIPALWORD_SCORING'):
    args.append('--principalword_scoring')

  if config.var('PR_WEIGHT_EQ_PAGERANK'):
    args.append('--pr_weight_eq_pagerank')

  if config.var('RTSERVER_MAX_RESULTS_PER_TIER'):
    args.append('--max_results_per_tier=%s' %
                config.var('RTSERVER_MAX_RESULTS_PER_TIER'))

  # don't use softfilelocks to lock the files before deleting.
  if config.var("RTSERVER_NOLOCK_FILE_BEFORE_DELETE"):
    args.append('--nolock_file_before_delete')

  # ignore cross epoch file failures?
  if config.var("RTSERVER_NOIGNORE_CROSS_EPOCH_FILES_ON_CHECKPOINT_RECOVERY"):
    args.append("--noignore_cross_epoch_files_on_checkpoint_recovery")

  if config.var('ENTERPRISE'):
    args.append("--googletags=true")

  return args

# Is the given result biasing policy valid and enabled?
def result_biasing_policy_enabled(policy):
  if (policy and policy.get('patterns') and policy['patterns'][0] != '0' and
      len(policy['patterns']) > 1):
    return True
  return False

# Is the result biasing feature enabled on this GSA?  In other words, are there
# any valid and enabled result biasing policies configured for this GSA?
def result_biasing_feature_enabled(config):
  # Check default_policy.
  if result_biasing_policy_enabled(config.var('ENT_SCORING_ADJUST')):
    return True
  # Check all user added policies.
  if config.var('ENT_SCORING_ADDITIONAL_POLICIES'):
    for policy in config.var('ENT_SCORING_ADDITIONAL_POLICIES').values():
      if result_biasing_policy_enabled(policy):
        return True
  return False

#------------------------------------------------------------------------------
# RTSLAVE
#------------------------------------------------------------------------------

def get_rt_subordinateargs(config, host, port):

  args = []
  args.append('--subordinate')

  machtype = servertype.GetPortType(port)
  if machtype not in ['rtsubordinate',
                      'scanjpg3', 'scanjpg2', 'scanjpg6',
                      'scanjpg20', 'scaninfo', 'scandjvu']:
    raise ValueError, "Wrong machine type %s" % machtype

  generic_rt_args = get_rt_genericargs(config, host, port)
  args = args + generic_rt_args

  MMAP_BUDGET = str(config.var('MMAP_BUDGET'))
  if MMAP_BUDGET:
    args.append('--mmap_budget=%s' % servertype.ExpandCutoff(MMAP_BUDGET))

  if config.var('INDEX_MAX_MEMBLOCK_SIZE'):
    args.append('--index_max_memblock_size=%d' % (
      config.var('INDEX_MAX_MEMBLOCK_SIZE')))

  if config.var('RTSERVER_SERVING_MAPS_ALWAYS_MMAP'):
    maps = config.var('RTSERVER_SERVING_MAPS_ALWAYS_MMAP')
    # If result biasing feature is enabled, we want to mmap entscoringmetadata
    # map files for rtsubordinate to improve serve latency.
    if result_biasing_feature_enabled(config):
      maps = maps + ',entscoringmetadata'
    args.append('--maps_always_mmap=%s' % maps)

  if config.var('RTSERVER_SERVING_MAPS_PRELOAD'):
    maps = config.var('RTSERVER_SERVING_MAPS_PRELOAD')
    # If result biasing feature is enabled, we want to preload
    # entscoringmetadata map files for rtsubordinate to improve serve latency.
    if result_biasing_feature_enabled(config):
      maps = maps + ',entscoringmetadata'
    args.append('--maps_preload=%s' % maps)

  if config.var('RTSERVER_PRELOAD_SERVING_STATE') and \
     config.var('RTSERVER_LAME_DUCK_STATE_ADVANCE'):
    raise RuntimeError('Only one of RTSERVER_PRELOAD_SERVING_STATE and '
                       'RTSERVER_LAME_DUCK_STATE_ADVANCE should be set')

  if config.var('RTSERVER_PRELOAD_SERVING_STATE'):
    args.append('--preload_serving_state')

  if config.var('RTSERVER_LAME_DUCK_STATE_ADVANCE'):
    args.append('--lame_duck_state_advance')

  if config.var('RTSERVER_PRELOAD_STARTUP_STATE'):
    args.append('--preload_startup_state')

  if config.var('RTSERVER_MIN_CHECKPOINT_POSITION'):
    position = "%s" % config.var('RTSERVER_MIN_CHECKPOINT_POSITION')
    # strip the trailing L in python 1.5
    if position[-1] == 'L':
      position = position[:-1]
    args.append('--min_checkpoint_position=%s' % position)

  if config.var('RTSERVER_CACHE_FULLINDEX'):
    args.append('--cache_fullindex')

  if config.var('RTSERVER_CACHE_FULLINDEX_PREFILL_RATIO') != None:
    args.append('--cachingfullindex_prefill_ratio=%f' %
                config.var('RTSERVER_CACHE_FULLINDEX_PREFILL_RATIO'))

  if config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_SIZE'):
    args.append('--querytermfrequencystats_size=%d' %
                config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_SIZE'))

  if config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_OUTPUTFILE_PREFIX'):
    args.append(
      '--querytermfrequencystats_outputfile=%s.%d' %
      (config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_OUTPUTFILE_PREFIX'),
       servertype.GetServingPort(port)))

  if config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_INPUTFILE_PREFIX'):
    args.append(
      '--querytermfrequencystats_inputfile=%s.%d' %
      (config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_INPUTFILE_PREFIX'),
       servertype.GetServingPort(port)))

  if config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_SAVE_INTERVAL'):
    args.append('--querytermfrequencystats_saveinterval=%d' %
                config.var('RTSERVER_QUERYTERMFREQUENCYSTATS_SAVE_INTERVAL'))

  if config.var('RTSLAVE_MAX_MMAP_MEMORY'):
    args.append(
      '--max_mmap_memory=%s' %
      prodlib.int_to_string(config.var('RTSLAVE_MAX_MMAP_MEMORY')))

  if config.var('RTSLAVE_MAX_INDEX_BYTES'):
    args.append(
      '--max_index_bytes=%s' %
      prodlib.int_to_string(config.var('RTSLAVE_MAX_INDEX_BYTES')))

  if config.var('RTSLAVE_LOCAL_CACHE_DIR'):
    args.append(
      '--rt_local_cache_dir=%s' % config.var('RTSLAVE_LOCAL_CACHE_DIR'))

  if config.var('RTSLAVE_MAX_FILE_SIZE_FOR_CACHE'):
    args.append(
      '--max_file_size_for_cache=%s' %
      config.var('RTSLAVE_MAX_FILE_SIZE_FOR_CACHE'))

  if config.var('RTSLAVE_RAM_DIR_FOR_INDEX_CACHING'):
    args.append('--rt_ram_dir=%s' %
                config.var('RTSLAVE_RAM_DIR_FOR_INDEX_CACHING'))
    if config.var('RTSLAVE_RAMDIR_LOCKFILE'):
      args.append('--rt_ram_lockfile=%s' %
                  config.var('RT_RAMFS_LOCKFILE'))
    if config.var('RTSLAVE_RAMFS_MAX_USAGE'):
      args.append('--rt_ramfs_max_usage=%s' %
                  config.var('RTSLAVE_RAMFS_MAX_USAGE'))

  if config.var('RTSERVER_ALWAYS_MMAP_LEXICON'):
    args.append('--always_mmap_lexicon')

  if config.var('ENT_CONFIG_TYPE') != 'MINI':
    if config.var('RTSLAVE_MLOCK_FILES'):
      args.append('--mlock_files')

  if config.var('RTSLAVE_MALLOC_IF_MLOCK_FAILS'):
    args.append('--malloc_if_mlock_fails')

  if config.var('RTSLAVE_CLEANUP_UNNECESSARY_FILES') != None:
    args.append('--cleanup_unnecessary_files=%d' %
                config.var('RTSLAVE_CLEANUP_UNNECESSARY_FILES'))

  if not config.var('RTSLAVE_VERIFY_MAPS_BY_LOADING'):
    args.append('--noverify_maps_by_loading')

  if config.var('RTSLAVE_SERVE_LATEST_EPOCHS') != None:
    args.append('--serve_latest_epochs=%d' %
                config.var('RTSLAVE_SERVE_LATEST_EPOCHS'))

  if config.var('RTSLAVE_CHECKPOINT_REFRESH_INTERVAL'):
    args.append('--checkpoint_refresh_interval=%d' %
                config.var('RTSLAVE_CHECKPOINT_REFRESH_INTERVAL'))

  if config.var('RTSLAVE_CHECKPOINTWATCHER_NICE_LEVEL'):
      args.append('--rtcheckpointwatcher_nice_level=%d' %
                config.var('RTSLAVE_CHECKPOINTWATCHER_NICE_LEVEL'))

  if config.var('RTSLAVE_MAX_CACHE_IDLE_TIME'):
    args.append('--max_cache_idle_time=%d' %
                config.var('RTSLAVE_MAX_CACHE_IDLE_TIME'))

  if config.var('RTSLAVE_MERGER') != None:
    if config.var('RTSLAVE_MERGER'):
      args.append('--merger')
    else:
      args.append('--merger=false')

  if config.var('RTSLAVE_LOG_DIR'):
    args.append('--log_dir=%s' %
                config.var('RTSLAVE_LOG_DIR'))

  if config.var('RTSLAVE_SKIP_TITLE_TIER') != None:
    if config.var('RTSLAVE_SKIP_TITLE_TIER'):
      args.append('--skip_title_tier')
    else:
      args.append('--skip_title_tier=false')

  if config.var('RTSLAVE_WATCH_FOR_CHECKPOINTS') != None:
    if config.var('RTSLAVE_WATCH_FOR_CHECKPOINTS'):
      args.append('--watch_for_checkpoints')
    else:
      args.append('--watch_for_checkpoints=false')

  if (config.var('GFS_ALIASES') and
      config.var('RTSLAVE_GFS_CELL_ARGS')):
    args.append(servertype.mkarg("--bnsresolver_use_svelte=false"))
    args.append('--gfs_cell_args=%s' % config.var('RTSLAVE_GFS_CELL_ARGS'))

  # Set the checksum verification threshold. (This is not in the common
  # section because mains and subordinates want to do this differently -
  # verifying can hurt for serving, but it may be ok for indexing)
  if config.var('RTSLAVE_VERIFY_THRESHOLD') != None:
    args.append('--verify_threshold=%d' %\
                config.var('RTSLAVE_VERIFY_THRESHOLD'))

  if config.var('DOCSERVER_USE_CRAWLTIME_AS_DOCVERSIONID'):
    args.append('--docserver_use_crawltime_as_docversionid')

  if config.var('RTINDEX_USE_CREATIONTIME_AS_DOCVERSIONID'):
    args.append('--rtindex_use_creationtime_as_docversionid')

  if config.var('RTSERVER_MAX_MAP_FILES') != None:
    args.append('--max_map_files=%d' % config.var('RTSERVER_MAX_MAP_FILES'))

  if config.var('ENT_LOG_QUERY_TIMINGS'):
    args.append('--log_doc_timings')
    args.append('--log_index_timings')

  if config.var('ENT_SCORING_CONFIG'):
    args.append("--enterprise_scoring_config=%s" %\
                config.var('ENT_SCORING_CONFIG'))

  if config.var('RTSLAVE_CHECK_BASE_INDEXER_COMMITTED_POSITION') and \
     config.GetServerManager().Set('base_indexer') != None:
    args.append("--check_base_indexer_committed_position")

    # Only pass in additional --base_indexer_host_port flag when
    # --check_base_indexer_committed_position is enabled.
    rtsubordinate_shard = servertype.GetPortShard(port)
    for rtserver in config.GetServerManager().Set('base_indexer').Servers():
      if servertype.GetPortShard(rtserver.port()) == rtsubordinate_shard:
        args.append('--base_indexer_host_port=%s:%d' % (rtserver.host(),
                                                        rtserver.port()))
        break

  return string.join(args)

def restart_rt_subordinate(config, host, port, server_type="rtsubordinate"):
  command_line = cli.CommandLine()
  command_line.Add(UlimitPrefix(config))
  rt_args = get_rt_subordinateargs(config, host, port)
  command_line.Add(ServerExecutablePrefix(config, server_type))
  command_line.Add(rt_args)

  # TODO: remove this when the dependency between the rtsubordinate server
  # and chubby has been broken.
  CommandLineExtend(command_line, LOCK_SERVICE_FLAGS)

  return command_line.ToString()

servertype.RegisterRestartFunction('rtsubordinate', restart_rt_subordinate)

#-----------------------------------------------------------------------------
# CONFIG MANAGER
#-----------------------------------------------------------------------------
def restart_config_manager(config, host, port):

  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('config_manager')
  servers = set.ServersForPort(port)
  shard = servertype.GetPortShard(port)
  # there should be at most one configmgr servers defined for config_mgr
  if len(servers)>1:
    raise RuntimeError, "Too many config managers port %s: %s" % (port,
                                                                  servers)
  # endif

  pyargs = []
  pyargs.append('--configmgr_request_dir=%s' %
                config.var('CONFIG_MANAGER_REQUEST_DIR'))
  pyargs.append('--working_dir=%s' %
                config.var('CONFIG_MANAGER_WORKING_DIR'))
  if config.var('CONFIG_MANAGER_STAGING_DIR'):
    pyargs.append('--staging_dir=%s' %
                  config.var('CONFIG_MANAGER_STAGING_DIR'))
  # endif

  logfile_dir = None
  if config.has_var('ENTERPRISE_HOME'):
    # Enterprise specific stuff
    logfile_dir = config.var('LOGDIR')
    pyargs.append(
        '--cwd=%s/local/google3/enterprise/legacy/production/configmgr' %
        config.var('ENTERPRISE_HOME'))
  else:
    logfile_dir = '/export/hda3/tmp'
    pyargs.append('--cwd=/root/google3/enterprise/legacy/production/configmgr')
  # endif
  if config.var('CONFIG_MANAGER_DATED_LOGFILE'):
    pyargs.append('--logfile=%s/configmgr_out_%s' % (
      logfile_dir, time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))))
  else:
    pyargs.append('--logfile=%s/configmgr_out' % logfile_dir)
  # endif
  if config.has_var('CONFIG_REPLICAS'):
    if config.var('CONFIG_MANAGER_RSYNCTO_REPLICAS'):
      pyargs.append('--replication_machines=%s' %
                    string.join(config.var("CONFIG_REPLICAS"), ","))
    # endif
  # endif
  if config.var('CONFIG_MANAGER_P4ENABLED'):
    pyargs.append('--p4_user=%s' % config.var('CONFIG_MANAGER_P4USER'))
    pyargs.append('--p4_client=%s' % config.var('CONFIG_MANAGER_P4CLIENT'))
    pyargs.append('--p4_config=%s' % config.var('CONFIG_MANAGER_P4CONFIG'))
    pyargs.append('--p4_depot_dir=%s' % config.var('CONFIG_MANAGER_P4DEPOTDIR'))
    pyargs.append('--p4_branch=%s' % string.join(
      config.var('CONFIG_MANAGER_P4BRANCH'), ","))
  # endif
  if config.var('CONFIG_MANAGER_MACHINEDBENABLED'):
    pyargs.append('--machinedb_enable')
  # endif
  if config.var('CONFIG_MANAGER_PEEK_REQUETS'):
    peeks = []
    for mach, dir in config.var('CONFIG_MANAGER_PEEK_REQUETS').items():
      peeks.append("%s:%s" % (mach, dir))
    pyargs.append('--peek_extra_requests=%s' %string.join(peeks, ","))
  # endif
  if config.var('CONFIG_MANAGER_INTERMEDIATE_MACHINE'):
    pyargs.append('--intermediate_production_machine=%s' %
                  config.var('CONFIG_MANAGER_INTERMEDIATE_MACHINE'))
  # endif
  if config.var('CONFIG_MANAGER_INTERMEDIATE_USER'):
    pyargs.append('--intermediate_production_user=%s' %
                  config.var('CONFIG_MANAGER_INTERMEDIATE_USER'))
  # endif
  if config.var('CONFIG_MANAGER_PERIODIC_REQUESTS'):
    periodic_dirs = []
    for (t, d) in config.var('CONFIG_MANAGER_PERIODIC_REQUESTS').items():
      periodic_dirs.append('%d:%s' % (t, d))
    # endfor
    pyargs.append('--periodic_requests_dirs=%s' % string.join(periodic_dirs))
  # endif

  args = map(lambda arg: commands.mkarg(arg), pyargs)

  args.append("--port=%d" % port)

  loopflags = '--rundir=%(home)s/local' % {'home' : config.var('ENTERPRISE_HOME')}
  pythonpath = 'PYTHONPATH=%s/local/google3/enterprise/legacy/setup' % config.var('ENTERPRISE_HOME')
  cmd_parts = [pythonpath, InterpretedServerExecutablePrefix(config, 'config_manager', loopflags=loopflags)]
  cmd_parts.extend(args)
  cmd = ' '.join(cmd_parts)
  return cmd
# enddef

servertype.RegisterRestartFunction('config_manager', restart_config_manager)

#-----------------------------------------------------------------------------
# PYSERVERIZER
#-----------------------------------------------------------------------------

def restart_pyserverizer(config, host, port):

  if config.var("GOOGLEBASE"):
    cmd = 'export GOOGLEBASE=%s; ' % config.var("GOOGLEBASE")
  else:
    cmd = ''
  cmd = cmd + ServerExecutablePrefix(config, "pyserverizer") + " "

  args = []
  args.append(" --port=%d " % (port))
  if config.var("PS_PYTHONCODE"):
    args.append("--pythoncode=%s" % config.var("PS_PYTHONCODE"))

  # NOTE: We were not able to get a white space character to work as the
  #       delimiter.
  if config.var("PS_ARGDELIMITER"):
    argdelimiter = config.var("PS_ARGDELIMITER")
  else:
    argdelimiter = ';'
  args.append("--argdelimiter=%s" % argdelimiter)

  if config.var("PS_PYTHONARGS"):
    args.append("--pythonargs=%s" %
                 string.join(config.var("PS_PYTHONARGS"), argdelimiter))

  if config.var("PS_UID") != None:
    args.append("--uid=%s" % config.var("PS_UID"))

  if config.var("PS_AUTORUN") != None:
    args.append("--autorun")

  if config.var("GFS_USER"):
    args.append("--gfs_user=%s" % config.var("GFS_USER"))

  if config.var("GFS_ALIASES"):
    args.append(servertype.mkarg("--bnsresolver_use_svelte=false"))
    args.append("--gfs_aliases=%s" % config.var("GFS_ALIASES"))

  cmd = cmd + string.join(map(lambda arg: commands.mkarg(arg), args))

  return cmd

servertype.RegisterRestartFunction('pyserverizer', restart_pyserverizer)

#------------------------------------------------------------------------------
# HEADREQUESTOR
#------------------------------------------------------------------------------

def restart_headrequestor(config, host, port):
  command_line = cli.CommandLine()
  command_line.Add(ServerExecutablePrefix(config, "headrequestor"))
  command_line.Add("--port=%d" % port)

  # These flags are needed to tell SSLContext to not use a certificate file,
  # allowing the headrequestor to use SSLContext to make SSL
  # (non-client-certificates) client connections
  command_line.Add("--use_certificate_dir=/dev/null")
  command_line.Add("--CA_CRL_dir=/dev/null")
  command_line.Add("--private_rsa_key_file=")
  command_line.Add("--use_certificate_file=")
  command_line.Add("--CA_certificate_file=")

  if USE_VERSIONS:
    data_version = config.GetDataDir(port)
  else:
    data_version = 'whatever'   # 'whatever' means accept any data version
  command_line.Add("--data_version=%s" % data_version)

  if config.var('HEADREQUESTOR_DEFAULT_HOSTLOAD'):
    command_line.Add("--default_max_hostload=%d" % \
                     config.var('HEADREQUESTOR_DEFAULT_HOSTLOAD'))

  if config.var('HOSTLOAD_DIE_ON_INCOMPLETE_HOST_SPECIFICATION') == 0:
    command_line.Add("--die_on_incomplete_host_specification=false")

  if config.var('HEADREQUESTOR_INDIV_REQUEST_TIMEOUT'):
    command_line.Add("--connection_timeout=%d" % \
                 int(1000 * config.var('HEADREQUESTOR_INDIV_REQUEST_TIMEOUT')))
  if config.var('HEADREQUESTOR_REQUEST_BATCH_TIMEOUT'):
    command_line.Add("--request_timeout=%d" % \
                 int(1000 * config.var('HEADREQUESTOR_REQUEST_BATCH_TIMEOUT')))

  # if 0, we still want to include the command line flag
  if config.var('HEADREQUESTOR_CACHE_ENTRY_TIMEOUT') != None:
    command_line.Add("--url_cache_entry_timeout=%s " % \
                     config.var('HEADREQUESTOR_CACHE_ENTRY_TIMEOUT'))

  # Send the proxy mapping file to Head Requestor.
  if config.var('PROXY_CONFIG'):
    command_line.Add("--proxy_config=%s" % config.var('PROXY_CONFIG'))

  # needed for the GFS file initialization used for logging headrequestor log
  if config.var('GFS_ALIASES'):
    command_line.Add(servertype.mkarg('--bnsresolver_use_svelte=false'))
    command_line.Add(servertype.mkarg('--gfs_aliases=%s' %
      config.var('GFS_ALIASES')))

  if config.var('HEADREQUESTOR_ENABLE_SLOW_HOST_CACHE') and \
     config.var('HEADREQUESTOR_HOST_CACHE_ENTRY_TIMEOUT') != 0:
    command_line.Add("--host_cache_entry_timeout=%d" % \
                     config.var('HEADREQUESTOR_HOST_CACHE_ENTRY_TIMEOUT'))
    if config.var('HEADREQUESTOR_SLOW_HOST_NUM_URLS'):
      command_line.Add("--slow_host_num_urls=%d" % \
                       config.var('HEADREQUESTOR_SLOW_HOST_NUM_URLS'))
    if config.var('HEADREQUESTOR_SLOW_HOST_DURATION'):
      command_line.Add("--slow_host_duration=%d" % \
                       config.var('HEADREQUESTOR_SLOW_HOST_DURATION'))
  else:
    command_line.Add("--host_cache_entry_timeout=0")

  if config.var('USER_AGENT_TO_SEND'):
    command_line.Add("--useragent=%s" % config.var('USER_AGENT_TO_SEND'))

  if config.var('AUTHZ_SERVICE_URL') or config.var('CONNECTOR_CONFIGDIR'):
    srv_mngr = config.GetServerManager()
    set = srv_mngr.Set('headrequestor')

    (shardinfo, backends) = set.BackendInfo(use_versions = USE_VERSIONS)

    # If we ever shard or replicate the AuthzChecker the headrequestor
    # should be changed to use --backends and --shardinfo.  But since
    # using those is a pain, we just do this for now
    list = backends.AsString().split(':')
    host = list[0]
    port = list[1]

    command_line.Add("--authzchecker_host=%s" % host)
    command_line.Add("--authzchecker_port=%s" % port)

  if config.var('ENABLE_SINGLE_SIGN_ON') and \
     config.var('DO_SSO_SERVING_LOGGING'):
    command_line.Add("--do_sso_serving_logging")
    command_line.Add("--sso_serving_headrequestor_log_file=%s" %
                config.var('SSO_SERVING_HEADREQUESTOR_LOG_FILE'))

  return command_line.ToString()

servertype.RegisterRestartFunction('headrequestor', restart_headrequestor)

#------------------------------------------------------------------------------
# TABLESERVER
#------------------------------------------------------------------------------

THIRD_PARTY_JDBC_JARS = [
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/mysql/mysql-3.0.14.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/db2/db2java.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/oracle/ojdbc14.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/oracle/orai18n.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/postgres/pgjdbc2.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/sqlserver/v2005/sqljdbc.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/sybase/jTDS2.jar',
  '%(GOOGLEBASE)s/google/third_party/java/jdbc/sybase/jconn2.jar',
]

def restart_tableserver(config, host, port):
  cl = cli.CommandLine()
  cl.Add(UlimitPrefix(config))
  binary_name = servertype.GetBinaryName('enttableserver')
  libsdir=os.path.join(config.var('MAINDIR'), 'bin',
                       '%s_libs' % binary_name)
  swigdeps = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name),
                          'TableServer_swigdeps.so')
  jdbcjars=''
  for jar in THIRD_PARTY_JDBC_JARS:
    realpath=(jar % os.environ)
    jdbcjars=('%s:%s' % (jdbcjars, realpath))

  jvm_cl = cli.CommandLine()
  classpath = ('%s/bin/TableServer.jar:'
               '%s/third_party/java/saxon/saxon.jar') % (
                     config.var('MAINDIR'), config.var('MAINDIR'))
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.security.manager')
  jvm_cl.Add('-Djava.security.policy=%s/bin/java.policy' %
             config.var('MAINDIR'))
  jvm_cl.Add('-Djavax.xml.parsers.DocumentBuilderFactory='
             'com.icl.saxon.om.DocumentBuilderFactoryImpl')
  jvm_cl.Add('-Djavax.xml.transform.TransformerFactory='
             'com.icl.saxon.TransformerFactoryImpl')
  jvm_cl.Add('-Djavax.xml.parsers.SAXParserFactory='
             'com.icl.saxon.aelfred.SAXParserFactoryImpl')
  jvm_cl.Add('-Xbootclasspath/a:%s' % jdbcjars)
  jvm_cl.Add('-Djava.library.path=%s' % libsdir)
  jvm_cl.Add('-Dswigdeps=%s' % swigdeps)
  cl.Add(JavaServerExecutablePrefix(config, 'enttableserver',
    jvm_cl.ToString(),
    '--lognamesuffix=jar',
    run_as_class=1))

  cl.Add('--maxthreads=5')
  cl.Add('--cachingtransformerfactory_capacity=10')
  # borrow AdminConsole's ipwhitelist for now
  cl.Add('--ipwhitelist=%(GOOGLEBASE)s/conf/AdminConsole_ipwhitelist'
         % os.environ)
  cl.Add('--dbinfo=%s' % config.var('DATABASES'))
  if config.var('DATABASE_STYLESHEET_DIR'):
    cl.Add('--stylesheet_dir=%s' % config.var('DATABASE_STYLESHEET_DIR'))
  cl.Add('--port=%d' % servertype.GetServingPort(port))
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('enttableserver')
  webservers = serverflags.MakeHostPortsArg(
    set.BackendHostPorts('web'))
  if webservers:
    cl.Add("--gws_servers=%s" % webservers)
  cl.Add("--serveprefix=googledb://")
  return cl.ToString()

servertype.RegisterRestartFunction('enttableserver', restart_tableserver)

#-------------------------------------------------------------------------------
# FilesystemGateway
#-------------------------------------------------------------------------------
def restart_fsgw(config, host, port):
  cl = cli.CommandLine()
  cl.Add(UlimitPrefix(config))

  binary_name = servertype.GetBinaryName('fsgw')

  # Generate the Java command to execute
  classpath = '%s/bin/FileSystemGateway.jar:' % config.var('MAINDIR')
  swigdeps = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name),
                          'FileSystemGateway_swigdeps.so')
  libsdir=os.path.join(config.var('MAINDIR'), 'bin',
                       '%s_libs' % binary_name)

  jvm_cl = cli.CommandLine()
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.security.manager')
  jvm_cl.Add('-Djava.security.policy=%s/bin/java.policy' %
             config.var('MAINDIR'))
  jvm_cl.Add('-Dswigdeps=%s' % swigdeps)
  jvm_cl.Add('-Djava.library.path=%s' % libsdir)

  cl.Add(JavaServerExecutablePrefix(config, 'fsgw', jvm_cl.ToString(),
         '--rundir=%s --lognamesuffix=jar' % config.var('MAINDIR'),
         run_as_class=1))

  # Now for the options for the server itself
  cl.Add('--port=%d' % servertype.GetServingPort(port))
  cl.Add('--maxthreads=5')
  # borrow AdminConsole's ipwhitelist for now
  cl.Add('--ipwhitelist=%(GOOGLEBASE)s/conf/AdminConsole_ipwhitelist'
         % os.environ)
  cl.Add('--mimeTypesPath=%s/mime.types' % config.var('ENTERPRISEDATA'))
  cl.Add('--smbHelperPath=%s/bin/smbhelper' % config.var('MAINDIR'))

  if config.var('CRAWL_USERPASSWD_CONFIG'):
    cl.Add("--accessInfoFile=%s" % (
           config.var('CRAWL_USERPASSWD_CONFIG')))

  # datadir, gfs_aliases and shard
  cl.Add("--datadir=" + config.var('DATADIR'))
  if config.var('GFS_ALIASES'):
    cl.Add(servertype.mkarg("--gfs_aliases=%s" % config.var('GFS_ALIASES')))
    if config.var('GFS_USER'):
      cl.Add('--gfs_user=%s' % config.var('GFS_USER'))
  else:
    cl.Add("--shard=%d" % servertype.GetPortShard(port))

  return cl.ToString()

servertype.RegisterRestartFunction('fsgw', restart_fsgw)


#------------------------------------------------------------------------------
# AuthzChecker
#------------------------------------------------------------------------------

def restart_authzchecker(config, host, port):
  command_line = cli.CommandLine()
  command_line.Add(UlimitPrefix(config))

  binary_name = servertype.GetBinaryName('authzchecker')
  libsdirs = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name))
  libsdirs = '%s:%s' % (os.path.join(config.var('MAINDIR'), 'bin'), libsdirs)
  swigdeps = os.path.join(config.var('MAINDIR'), 'bin',
                          os.path.basename('%s_libs' % binary_name),
                          'AuthzChecker_swigdeps.so')

  classpath = ('%s/bin/AuthzChecker.jar' % config.var('MAINDIR'))
  jvm_cl = cli.CommandLine()
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.library.path=%s' % libsdirs)
  jvm_cl.Add('-Dswigdeps=%s' % swigdeps)

  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('authzchecker')
  (shardinfo, backends) = set.BackendInfo(use_versions = 0)

  command_line.Add(JavaServerExecutablePrefix(config, 'authzchecker',
                   jvm_cl.ToString(), run_as_class=1))

  command_line.Add('--port=%d' % port)

  if backends.HasBackEnds():
    command_line.Add('--backends=%s' % backends.AsString())

  if config.has_var('HEADREQUESTOR_CACHE_ENTRY_TIMEOUT'):
    command_line.Add("--cache_entry_timeout=%s " % \
      config.var('HEADREQUESTOR_CACHE_ENTRY_TIMEOUT'))

  if config.var('HEADREQUESTOR_REQUEST_BATCH_TIMEOUT'):
    command_line.Add("--request_timeout=%d" % \
                 int(1000 * config.var('HEADREQUESTOR_REQUEST_BATCH_TIMEOUT')))

  if config.var('AUTHZ_SERVICE_URL'):
    command_line.Add("--authz_url=%s " % config.var('AUTHZ_SERVICE_URL'))

  command_line.Add("--trustedca_path=%s" % config.var('TRUSTED_CA_DIRNAME'))
  command_line.Add("--crl_path=%s" % config.var('CRL_DIRNAME'))

  if config.var('ENTFRONT_KEY_STORE'):
    command_line.Add("--keystore=%s" % config.var('ENTFRONT_KEY_STORE'))

  # This flag controls the logging of classes under com.google.enterprise
  command_line.Add('--enterprise_log_level=INFO')
  # This flag controls the logging of all other classes
  command_line.Add('--log_level=INFO')

  # on the virtual GSALite, keep logs small (10MB)
  if config.var('ENT_CONFIG_TYPE') == 'LITE':
    command_line.Add('--log_file_limit=%d' % 10000000)
  else:
    # By default, previous logs are deleted. These flags are similar to what is
    # in logcontrol. Note that we have to pass the value of Integer.MAX_VALUE in
    # Java (32-bit), so we can't pass 2200000000 (value in logcontrol)
    command_line.Add('--log_file_count=%d' % 20)
    command_line.Add('--log_file_limit=%d' % JAVA_MAX_LOG_SIZE)

  if config.var('CRAWL_LOGDIR'):
    command_line.Add(servertype.mkarg('--log_file=%s/authzchecker' %
                                      config.var('CRAWL_LOGDIR')))

  if config.var('CONNECTOR_CONFIGDIR'):
    command_line.Add(servertype.mkarg('--connector_config_dir=%s' %
                                      config.var('CONNECTOR_CONFIGDIR')))

  if config.var('SESSIONMANAGER_ALIASES'):
    command_line.Add('--sessionmanager_server=%s' %
                     config.var('SESSIONMANAGER_ALIASES'))

  fsgws = set.BackendHostPorts('fsgw')
  command_line.Add('--filesystem_servers=%s' %
                   serverflags.MakeHostPortsArg(fsgws))

  # ACL checking config files
  # we turn these on by default and leave it to the AuthzChecker to not use
  # the feature if the files are not found
  command_line.Add(servertype.mkarg('--acl_groups_file=%s' %
                                      config.var('ACL_GROUPS_FILE')))
  command_line.Add(servertype.mkarg('--acl_urls_file=%s' %
                                      config.var('ACL_URLS_FILE')))

  return command_line.ToString()

servertype.RegisterRestartFunction('authzchecker', restart_authzchecker)

#------------------------------------------------------------------------------
# Connectormgr
#------------------------------------------------------------------------------

def restart_connectormgr(config, host, port):
  command_line = cli.CommandLine()
  command_line.Add(UlimitPrefix(config))

  binary_name = servertype.GetBinaryName('connectormgr')

  if port == 7886:
    catalina_base = os.path.join(config.var('MAINDIR'), 'bin', 'connectormgr-prod')
  else:
    catalina_base = os.path.join(config.var('MAINDIR'), 'bin', 'connectormgr-test')

  enterprise_home = config.var("ENTERPRISE_HOME")
  appbase = "%s/local/google/webapps" % enterprise_home

  classpath = ('/usr/local/tomcat55/bin/bootstrap.jar:'
               '/usr/local/tomcat55/bin/commons-logging-api.jar:')
  jvm_cl = cli.CommandLine()
  jvm_cl.Add('-classpath %s' % classpath)
  jvm_cl.Add('-Djava.util.prefs.userRoot'
             '=%s' % appbase)
  jvm_cl.Add('-Djava.util.logging.manager'
             '=org.apache.juli.ClassLoaderLogManager')
  jvm_cl.Add('-Djava.util.logging.config.file'
             '=%s/conf/logging.properties' % catalina_base)
  jvm_cl.Add('-Djava.endorsed.dirs'
             '=/usr/local/tomcat55/common/endorsed')
  jvm_cl.Add('-Dcatalina.home'
             '=/usr/local/tomcat55')
  jvm_cl.Add('-Dcatalina.base'
             '=%s' % catalina_base)
  jvm_cl.Add('-Djava.io.tmpdir'
             '=%s/temp' % catalina_base)
  # the 'port' parameter is currently ignored,
  # but we need to include it so babysitter can kill the process
  # see bug #735729
  jvm_cl.Add('-Dport=%s' % port)

  command_line.Add(JavaServerExecutablePrefix(
    config, 'connectormgr', jvm_cl.ToString(),
    '--rundir=%s --lognamesuffix=jar' % config.var('MAINDIR'),
    run_as_class=1))

  command_line.Add('start')

  start_cmd = command_line.ToString()

  # calculate import_cmd

  command_line = cli.CommandLine()

  google3_dir = "%s/local/google3" % enterprise_home
  import_script = (
    "%s/enterprise/connector/connector_import_export.py" % google3_dir)
  command_line.Add(import_script)

  java = config.GetServerManager().Set('connectormgr').property('interpreter')
  command_line.Add(java)

  command_line.Add(appbase)

  java_options = '-Djava.util.prefs.userRoot=%s' % appbase
  command_line.Add(java_options)

  command_line.Add("import")

  connectors_config_file = config.var("CONNECTORS")
  command_line.Add(connectors_config_file)

  import_cmd = command_line.ToString()

  # port_cmd:
  # update connector manager config file (connector/managers.xml)
  # with the internal connector manager's port number
  # so other processes can find it

  perl = "/usr/bin/perl"
  # note: we assume the internal connector manager's URL starts with 'http://ent1:'.
  match_pattern = "^(\s*<Url>http://ent1:)(\d+)(.*)$"
  replace_pattern = "${1}%s${3}" % port
  connector_config_dir = config.var('CONNECTOR_CONFIGDIR')
  connector_manager_config_file = "%s/managers.xml" % connector_config_dir
  port_cmd = "%s -pi -e 's#%s#%s#' %s" % (
    perl, match_pattern, replace_pattern, connector_manager_config_file)

  return "%s && %s && %s" % (import_cmd, port_cmd, start_cmd)

servertype.RegisterRestartFunction('connectormgr', restart_connectormgr)

#------------------------------------------------------------------------------
# ent_fedroot
#------------------------------------------------------------------------------

def restart_ent_fedroot(config, host, port):
  command_line = cli.CommandLine()
  command_line.Add(ServerExecutablePrefix(config, 'ent_fedroot'))

  binary_name = servertype.GetBinaryName('ent_fedroot')
  # TODO:
  # The following is copied from get_ent_mixer_args. It
  # seems to be a gross hack.

  # Get backends for mixer.
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('ent_fedroot')

  if 'rtsubordinate' in map(lambda x: x.name(), srv_mngr.Sets()):
    rt_backends = [
      { 'set' : 'rtsubordinate',
        'serve_as' : 'index',
        'numconn' : 3,
        'level' : 0
      },
      { 'set' : 'rtsubordinate',
        'serve_as' : 'doc',
        'numconn' : 3,
        'level' : 0
      },
      { 'set' : 'rtsubordinate',
        'serve_as' : 'link',
        'numconn' : 3,
        'level' : 0
      },
      { 'set' : 'cache',
        'level' : 0,
        'protocol' : 'http'
      },
    ]
  else:
    # We talk to base_indexer only if we don't have any rtsubordinates left
    rt_backends = [
      { 'set' : 'base_indexer',
        'serve_as' : 'index',
        'numconn' : 3,
        'level' : 0,
        'port_shift' : port_shift
      },
      { 'set' : 'base_indexer',
        'serve_as' : 'doc',
        'numconn' : 3,
        'level' : 0,
        'port_shift' : port_shift
      },
      { 'set' : 'base_indexer',
        'serve_as' : 'link',
        'numconn' : 3,
        'level' : 0,
        'port_shift' : port_shift
      },
      { 'set' : 'cache',
        'level' : 0,
        'port_shift' : port_shift,
        'protocol' : 'http'
      },
    ]
  set.set_property('backends', rt_backends)

  (shardinfo, backends) = set.BackendInfo(use_versions = 0)

  ### FIXIT: data version is kind of messy and needs a global cleanup
  ### now just hack the way through for enterprise
  real_data_version = '/export/hda3/enterprise-data'
  segment = set.property('segment')
  for i in (0, 1):
    if shardinfo.HasShard('index:%d' % i, segment):
      shardinfo.set_data_version('index:%d' % i, segment, real_data_version)
    if shardinfo.HasShard('doc:%d' % i, segment):
      shardinfo.set_data_version('doc:%d' % i, segment, real_data_version)
    if shardinfo.HasShard('link:%d' % i, segment):
      shardinfo.set_data_version('link:%d' % i, segment, real_data_version)

  if backends.HasBackEnds():
    command_line.Add('--backends=%s' % backends.AsString())
    command_line.Add('--shardinfo=%s' % shardinfo.AsString())

  command_line.Add('--port=%d' % (port))
  # TODO(vish): command_line.Add('--levels_with_64bit_docids=0,1')

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    command_line.Add('--trusted_clients=%s' %
            string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  command_line.Add('--use_mixer=false')
  command_line.Add('--superroot_params=EntCorpusRoot:,EntFedRoot:')
  googledata_dir = config.var('GOOGLEDATA') + '/enterprise/data'
  command_line.Add('--sr_static_config_files=%s/federation_root.cfg' %
                     googledata_dir)
  command_line.Add('--corpus_name=%s' % config.var('EXTERNAL_WEB_IP'))

  return command_line.ToString()

servertype.RegisterRestartFunction('ent_fedroot', restart_ent_fedroot)

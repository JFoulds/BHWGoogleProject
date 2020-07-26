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
# This file was branched from production in 2004
# - Nick Pelly

import commands
import glob
import os
import re
import socket
import string
import sys
import time
import types
import urllib

from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.setup import serverflags

# TODO!!!!!! : all sys.exit() need to go! we can't do crawl babysitting
# if the babysitter dies on us!

# TODO!!!!!! : all sys.exit() need to go! we can't do crawl babysitting
# if the babysitter dies on us!


# TODO: Perhaps this should move the log files to an 'oldlogs/' subdirectory,
# rather than deleting them entirely.
DELETE_LOGS = "rm -f {/export/hda3/tmp/,/tmp/}%s*INFO* "

# This is a list of servers which we allow to be run within a
# looping auto-restart  script if the config file requests it. No entry
# implies it is unsafe to use a loop.  New pageranker does not use loop.
ALLOW_LOOP = [
  "rfserver", "urlmanager", "urlmanager_log_rewriter", "urlserver",
  "bot", "contentfilter",
  "tracker_gatherer",
  "urltracker_server",
  "base_indexer", "rt_indexer",
  "urlhistory_processor",
  "web",
  "urlscheduler", "feedergate", "feeder",
  "pr_main",
  "supergsa_main",
]

DictExt = {
  'FLASH'     :          ["swf"],
  'PDF'       :          ["pdf"],
  'PS'        :          ["ps"],   # eps and ai are graphics files
  'PSGZ'      :          ["ps.gz"],
  'MS-EXCEL'  :          ["xls", "xlw"],
  'RTF'       :          ["rtf"],
  'MSWORD'    :          ["doc"],
  'MS-PPT'    :          ["ppt"],
  'OTHER'     :          ["wpd"], # and many more...
  'EVERYTHING':          ["pdf", "ps", "eps", "ai", "xls", "xlw", "rtf", "doc", "ppt", "swf", "wpd"],
}

# The web server accept type for each filetype
AcceptMime = {
  'FLASH'     :         ["application/x-shockwave-flash"],
  'PDF'       :         ["application/pdf"],
  'PS'        :         ["application/postscript"],
  'PSGZ'      :         ["application/x-gzip", "application/octet-stream"],
  'MS-EXCEL'  :         ["application/vnd.ms-excel"],
  'RTF'       :         ["application/rtf"],
  'MSWORD'    :         ["application/msword"],
  'MS-PPT'    :         ["application/vnd.ms-powerpoint"],
  'XML'       :         ["application/xml"],
  'OTHER'     :         ["application/*"],
  'IMAGE'     :         ["image/*"],
  # well, everything except images
  'EVERYTHING':         ["application/*"],
}

# The types the content filter should allow in, this includes both the normal
# mime type and the internal mime types of the converted documents from the
# history crawl.
GoogleLocalMime = {
  'FLASH'     :         ["application/x-shockwave-flash", "text/x-shockwave-flash"],
  'PDF'       :         ["application/pdf", "text/pdf"],
  'PS'        :         ["application/postscript", "text/postscript"],
  'PSGZ'      :         ["application/x-gzip", "application/octet-stream", "text/postscript"],
  'MS-EXCEL'  :         ["application/vnd.ms-excel", "text/vnd.ms-excel"],
  'RTF'       :         ["application/rtf", "text/rtf"],
  'MSWORD'    :         ["application/msword", "text/msword"],
  'MS-PPT'    :         ["application/vnd.ms-powerpoint", "text/vnd.ms-powerpoint"],
  'XML'       :         ["application/xml"],
  'OTHER'     :         ["application/", "text/other"], # "google/other" is added by default
  'IMAGE'     :         ["image/", "image/jpeg", "google/image-thumbnail"],
  # well, everything except images
  'EVERYTHING':         ["application/x-shockwave-flash", "text/x-shockwave-flash", "application/pdf", "text/pdf", "application/postscript", "text/postscript", "application/x-gzip", "application/octet-stream", "application/vnd.ms-excel", "text/vnd.ms-excel", "application/rtf", "text/rtf", "application/msword", "text/msword", "application/vnd.ms-powerpoint", "text/vnd.ms-powerpoint", "text/other"],}

INSO_TYPES = ['MS-EXCEL', 'RTF', 'MSWORD', 'MS-PPT', 'OTHER']

LOCK_SERVICE_FLAGS = [ '--lockservice_use_loas=false',
                       '--svelte_servers=localhost:6297',
                       '--svelte_retry_interval_ms=2147483647' ]

#-------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#-------------------------------------------------------------------------------

# Removes any bigfile extension on the give filename, if present.  If no
# bigfile extension is present, returns "name"
#
def remove_bigfile_extension(name):
  m = re.search(r'(?P<basename>.*)\.(\d+|hdr)', name)
  if m != None:
    return m.group("basename")
  else:
    return name

# argument used for replication
#
def replicas_arg(config, port):
  type = servertype.GetPortType(port)

  replicas = config.GetReplica(type, port)

  if replicas:
    # Replicas should not be on the same machines as the servers
    replicas = filter(lambda r, s = config.GetServerMap()[port]: not r in s, replicas)
    return " --replicas=%s" % string.join(replicas, ',')
  else:
    return " --replicas="

# if a server has replica, use its replica
# otherwise, do pairwise replication
#            ==> must have even number of servers
def replicas_arg_pairwise_replication(config, port):
  if config.GetReplicaMap().has_key(port):
    return replicas_arg(config, port)

  srv_type = servertype.GetPortType(port)   # derive server type
  # compute my partner in pair-wise replication
  num_srvs = config.GetNumShards(srv_type)

  if num_srvs == 1: # no replication. need this to run local crawl
    return ""

  if (num_srvs & 0x1): # odd number of servers
    sys.exit("ERROR - %s must have even # of shards for pairwise "
             "replication. currently %d.\n"
             "        (pairwise replication is used because no replica "
             "are specified in the config file).\n"
              % (srv_type, num_srvs))

  if (port & 0x1): # odd shard
    rep_port = port - 1
  else: # even shard
    rep_port = port + 1
  return " --replicas=%s" % config.GetServerMap()[rep_port][0]


def check_variable(varname, value):
  if value == None:
    raise "%s: did not set required variable" % (varname)

# generate remote file name
# This wrapper is mainly for getting the GFS name right
#
def gen_remote_file_prefix(remote_host, namespace_prefix):
  gfs_prefix = '/gfs/'
  if (namespace_prefix[:len(gfs_prefix)] == gfs_prefix):
    return namespace_prefix
  else: # RFS based filename
    return "%s:%s" % (remote_host, namespace_prefix)


def output_log_name(config, machine_type, hash_str):
  """Return the log file for 'machine_type' to be used by writer.
     Log subsharding is used when there are too many concurrent writers
       for the filesystem to handle.  The basic idea is to have the
       writer randomly choose one of the subsharded logs to write to
       and the reader will read all subshards.  If this is enabled,
       hash_str is used to determine which subshard to use.
     This also supports changing outputs from global logs
       to local logs for testing mode.
  """
  rtlog = config.var('RTSERVER_LOGS')[machine_type]
  # rewrite global->local namespace prefix if in testing mode
  if machine_type in config.var('SERVERS_FORCING_LOCAL_LOGS'):# force local log
    output_dict = config.var('OUTPUT_NAMESPACE_PREFIX')
    global_prefix = config.var('GLOBAL_NAMESPACE_PREFIX')
    global_namespace_prefix = output_dict.get(machine_type, global_prefix)
    assert(rtlog[:len(global_namespace_prefix)] == global_namespace_prefix), \
      "type=%s, rtlog=%s" % (machine_type, rtlog)

    rtlog = config.var('NAMESPACE_PREFIX') + \
            rtlog[len(global_namespace_prefix):]
  #if need to rewrite global->local namespace prefix

  # do log subsharding
  num_subshards = config.var('RTSERVER_LOG_SUBSHARDS').get(machine_type)
  if num_subshards:  # do subsharding.  pick a random shard for writer
    assert (machine_type not in config.var('GLOBAL_SERVERS')), \
           "Log subsharding is not supported for global servers yet. " \
           "Because change of subsharding info can cause serious problems"
    assert hash_str, \
           "hash_str(%s) musts be non-empty with subsharding" % hash_str

    if config.var('RTSERVER_LOG_SUBSHARDS_DISABLE_WRITERS_FOR_DEBUGGING'):
      # for GFS debugging all writers write to subshard 0
      subshard = 0
    else:
      subshard = hash(hash_str) % num_subshards
    rtlog = rtlog + ("_subshard%03d" % subshard)
  #endif
  return rtlog
#enddef


def shardset_output_log_name(config, machine_type, host, port,
                             num_shards = None,
                             additional_suffix=""):
  """Generate output log name based on shardset, <type>:name:<#shards>,
     if num_shards > 0.  Otherwise, return empty string "".
     If num_shards is not specified, #shards for machine_type will be used.
     Note: additional_suffix is a hack to support mutilple servertype
           (e.g., contentfilter and urlmanager) writing to the same
           log file without GFS.  eventually, we should get rid of
           this hack by creating unique log names based on
              <servertype, shard>
     TODO: once every writer uses the shardset syntax, merge this with
           output_log_name
  """
  if num_shards == None: # determined by the config
    num_shards = config.GetNumShards(machine_type)
  #endif

  if num_shards <= 0:
    return ""
  else:
    hp = "%s:%d" % (host, port)  # used to randomize subsharding
    if machine_type == 'urlmanager_log_rewriter': # HACK :(
      m_type_prefix = 'urlmanager'
    else:
      m_type_prefix = machine_type
    return "%s:%s%s@%d" % (m_type_prefix,
                           output_log_name(config, machine_type, hp),
                           additional_suffix,
                           num_shards)
  #endif
#enddef



def get_reader_rt_logs_for_src_index(config, machine_type,
                                     shard_num, num_shards, src_index,
                                     logbasename=None,
                                     priority=None):
  """Return the RT logs for reader of (shard_num, num_shards, src_index)
     src_index is used to support mutliple writers in absense of GFS.
       If GFS is used, src_index should be set to -1
     If log subsharding is used, then the server will read from all subshards.
     If logbasename is not specified, the log names will be based on
       config.var('RTSERVER_LOGS')[machine_type]
     NOTE:
       This does NOT change outputs from global logs to local logs because
       in testing mode, writer will write to local logs and global server
       will continue to read from global logs. Hence, changes of test crawl
       won't modify global server behaviors
  """

  if logbasename == None: # no user override
    logbasename = config.var('RTSERVER_LOGS')[machine_type]
  #endif

  if priority == None:
    priority_str = ""
  else:
    priority_str = "@%d" % priority

  # take care of subsharding and priority
  rtlogs = []
  num_subshards = config.var('RTSERVER_LOG_SUBSHARDS').get(machine_type)
  if num_subshards:  # do subsharding.  pick a random shard for writer
    assert (machine_type not in config.var('GLOBAL_SERVERS')), \
           "Log subsharding is not supported for global servers yet. " \
           "Because change of subsharding info can cause serious problems"
    for i in xrange(num_subshards):
      rtlogs.append(logbasename + ("_subshard%03d%s" % (i, priority_str)))
    #endfor
  else:
    rtlogs = [logbasename + priority_str]
  #endif

  # convert base name to sharded input log names
  input_logs = []
  for rtlog in rtlogs:
    input_logs.append(
      servertype.GenLogfileBasename(rtlog, shard_num, num_shards, src_index))
  #end for

  return input_logs
#end get_reader_rt_logs_for_src_index


def get_reader_rt_logs(config, machine_type,
                       shard_num, num_reader_shards,
                       num_writer_shards,
                       log_basename=None, priority=None):
  """Return the RT logs for reader.
     o If not using GFS, automatically add src_index to support multiple writers
     o If log subsharding is used, then the server will read from all subshards.
     o If log_basename is not specified, the log names will be gotten from
       config.var('RTSERVER_LOGS')[machine_type]
     NOTE:
       This does NOT change outputs from global logs to local logs because
       in testing mode, writer will write to local logs and global server
       will continue to read from global logs.
       (i.e., changes won't affect global logs)
  """
  if config.var('GFS_ALIASES'): # using GFS=> no src_index needed
    src_indices = [-1]
  else:
    src_indices = xrange(num_writer_shards)
  #endif
  files = []
  for src_index in src_indices:
    files = files + get_reader_rt_logs_for_src_index(config, machine_type,
                                                     shard_num,
                                                     num_reader_shards,
                                                     src_index, log_basename,
                                                     priority)
  #endfor
  return files
#end def get_reader_rt_logs

# should we localize the server?
def IsServerLocalized(config, servertype):
  return servertype in config.var('CRAWL_SERVERTYPES_TO_LOCALIZE')
# end IsServerLocalized

# get binary's full path name
def GetBinaryPathAndName(config, server_type):
  if config.var('CRAWLMASTER'): # crawl config
    if IsServerLocalized(config, server_type):
      path = config.var('DATADIR')
    else:
      path = '%s/%s' % (config.var('MAINDIR'),
                        servertype.GetProperty(servertype, 'relative_bin_dir'))
    #endif
  else: # production config
    import sitecustomize
    path = "%s/google/%s" % (sitecustomize.GOOGLEBASE,
                             servertype.GetProperty(servertype, 'relative_bin_dir'))
  # endif

  return "%s/%s" % (path, servertype.GetBinaryName(server_type))
#end GetBinaryPathAndName()


# get all the necessary arguments for url canonicalization
def GetUrlCanonicalizationArgs(config, localized):
  args = []
  if localized:
    if config.var('DUPHOSTS') == '/dev/null': # disabled
      args.append("--duphosts=" + config.var('DUPHOSTS'))
    else:
      args.append("--duphosts=%s/duphosts" % config.var('DATADIR'))
    if config.var('URL_REWRITE_CRAWL_RULES_BASENAME'):
      args.append("--url_rewrites=%s/%s" % (
        config.var('DATADIR'), config.var('URL_REWRITE_CRAWL_RULES_BASENAME')))
  else:
    args.append("--duphosts=" + config.var('DUPHOSTS'))
    if config.var('URL_REWRITE_CRAWL_RULES_BASENAME'):
      args.append("--url_rewrites=%s/%s" % (
        config.var('GOOGLEDATA'),
        config.var('URL_REWRITE_CRAWL_RULES_BASENAME')))
  #endif localized

  return args
#end GetUrlCanonicalizationArgs


def get_gfs_args(config):
  """define GFS arguments"""
  var_name_and_flags = [
    ('GFS_ALIASES',           '--gfs_aliases'),
    ('GFS_USER',              '--gfs_user'),
    ('GFS_MAX_IDLE_TIME',     '--gfs_max_idle_time')
    ]
  args = servertype.BuildFlagArgs(config, var_name_and_flags)
  args.append(servertype.mkarg('--bnsresolver_use_svelte=false'))
  return args
#end

def common_pyserverizer_args(config, script_path, port, pyargs):
  maindir = config.var('MAINDIR')
  if not maindir: maindir = '/root'
  if config.var('PYTHON_VERBOSITY'):
    pyargs = ['--verbosity=%d' % config.var('PYTHON_VERBOSITY')] + pyargs
  args = [
    "--port=%d" % port,
    "--pythoncode=%s/%s" % (maindir, script_path),
    "--argdelimiter=+",
    "--pythonargs='%s'" % string.join(pyargs, '+'),
    "--autorun",     # automatically start executing
    "--uid="         # needs to run as root to run ssh
    ]
  args = args + get_gfs_args(config)
  return args
# end common_pyserverizer_args


#-------------------------------------------------------------------------------
# RESTART WRAPPER
#-------------------------------------------------------------------------------

# convert an NFS path to remote path if possible
# e.g.,    /import/sjz2/hda3/shared/googledata
# becomes  sjz2:/export/hda3/shared/googledata
def nfs_to_remote_path(config, nfs_path):
  nfs_prefix = '/import/%s/' % config.var('CRAWLMASTER')
  if nfs_path[:len(nfs_prefix)] != nfs_prefix: # unknown. return old path
    return "%s:%s" % (config.var('CRAWLMASTER'), nfs_path)
  else:
    return "%s:/export/%s" % (config.var('CRAWLMASTER'), nfs_path[len(nfs_prefix): ])


# NOTE: 'environment' argument is a manual integrate (see environment
# usage below).
def restart_wrapper(name, config, host, port, user_args,
  run_as="nobody", google2=1, additional_args=[], environment={}):

  # Get the set for this server set name so we can grab server properties
  # such as the binary user.
  srv_mgr = config.GetServerManager()
  set = srv_mgr.Set(name)

  if not set:
    raise RuntimeError('ERROR in restart_wrapper - '
                       'Could not find server set for: %s' % name)

  # Find the binary user if one is specified.  If we are using a binary
  # user to specify the user rather than the regular run_as argument
  # for now we assume that this is for AM capable machines and that
  # we need to use prodsu.  Clean this up to always use prodsu when
  # we are converted over.
  user = set.property('binary_user')
  use_prodsu = 0
  if user:
    run_as = user
    use_prodsu = 1

  temp_buf = "%f" % time.time()
  start_timestamp = temp_buf[:string.find(temp_buf, ".")]

  binary_to_use = set.property('binary_name', name)

  # keep rsync for localizing gws.  One of these days, when
  # the production world is ready, we will move it all out.
  rsync_cmd = ""
  # we will use "rsync" like this
  rsync_bin = '/usr/bin/rsync -t -e "ssh -c none"'
  if (name == 'web'):
    rsync_cmd = rsync_cmd + rsync_bin + " -a google@main.prodz:/root/googledata/ /root/googledata/ && "

  # append common arguments
  args = user_args
  if google2 and servertype.GetProperty(name, 'supports_google2_args'):
    # skip this flag for cookieserver
    if name != "cookieserver":
      args.append("--bigfile_smallbuf")

    if config.var('CRAWL_LOGDIR'):
      args.append("--log_dir=" + config.var('CRAWL_LOGDIR'))

    if config.var('ILLEGAL_FILENAME_PREFIXES'):
      args.append("--illegal_filename_prefixes=%s" %
                  config.var('ILLEGAL_FILENAME_PREFIXES'))

    if config.var('USE_XTERM'):                 # Show output when it will be visible
      args.append("--alsologtostderr")

    nice_level = 0
    if config.var('NICE_PRIORITY_LEVEL'):
      nice_level = config.var('NICE_PRIORITY_LEVEL')
    if name in ('base_indexer', 'daily_indexer', 'rt_indexer') and \
       config.var('RTSERVER_NICE_LEVEL') != None:
      nice_level = config.var('RTSERVER_NICE_LEVEL')
    if nice_level > 0:
      args.append("--nice_priority_level=%d" % config.var('NICE_PRIORITY_LEVEL'))

    if config.var('FATAL_LOGGING_EMAIL'):
      args.append("--logemaillevel=3")
      args.append("--alsologtoemail=" + config.var('FATAL_LOGGING_EMAIL'))

  # we use mkarg_single_escape_only() to protect arguments that have already
  # been escaped (eg --if_modified_since for the bot).
  arglist = map(servertype.mkarg_single_escape_only, args)

  pre_cmd = ''

  # These ulimits can fail silently. That is not particularly
  # good. However, we need something that works in the local
  # as well as remote case.
  if config.var('NO_COREDUMP_FOR') and name in config.var('NO_COREDUMP_FOR'):
    pre_cmd = pre_cmd + 'ulimit -c 0; '
  else:
    pre_cmd = pre_cmd + 'ulimit -c unlimited ; '

  default_vm_limit = config.var('DEFAULT_MAX_VIRTUAL_MEMORY_KB')
  vm_limit = config.var('SERVER_MAX_VIRTUAL_MEMORY_KB').get(name,
                                                            default_vm_limit)
  if vm_limit:
    pre_cmd = pre_cmd + 'ulimit -HSv %s; ' % vm_limit
  pre_cmd = pre_cmd + 'ulimit -HSn 8192 ; '

  if name == 'contentfilter' and config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'):
    pre_cmd = 'mkdir -p %s; chmod a+rxw %s; export TMPDIR=%s; %s ' %(
      config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'),
      config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'),
      config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'), pre_cmd)

  # MANUAL INTEGRATE of rt_index_branch babysitter code for exporting
  # environment variables.  Needed for pyserverizer (and rt_index_branch
  # is the only other branch that uses it -- see, ex., bartcontroller)
  for (env_var, value) in environment.items():
    pre_cmd = pre_cmd + 'export %s=%s; ' % (env_var, value)
  # end for
  # END MANUAL INTEGRATE

  if config.var('DO_DELETE_LOGS'):
    pre_cmd = DELETE_LOGS % (binary_to_use) + " ; "

  if (name == 'web'):
    # gws must run in /root/google/bin until dirinfo_root gets fixed
    pre_cmd = pre_cmd + " cd /root/google/bin ; "

  if rsync_cmd:
    pre_cmd = pre_cmd + rsync_cmd + ' true; ' # the last one terminates '&&'

  do_su = 0
  # Support the old style su for AM transition.
  if run_as != "root" and os.getuid() == 0 and not use_prodsu:
    pre_cmd = pre_cmd + 'su  %s -c ' % run_as
    do_su = 1
  # Run with new style prodsu.
  elif use_prodsu:
    pre_cmd = pre_cmd + 'prodsu %s sh -c ' % run_as
    do_su = 1

  cmd = ''

  # Determine the binary path
  binary_path = GetBinaryPathAndName(config, name)

  if (config.var('CRAWLER_LOOP_COUNT') and
      config.var('CRAWLER_LOOP_COUNT') > 0 and
      (name in ALLOW_LOOP or
        ( name == 'pr_main' and
          (config.GetNumShards("pr_main") == 1
           or not config.var('PAGERANKER_RECOVER_ON_RESTART')))
      ) ):
    cmd = cmd + '%sloop.crawl.py --count=%d --crawlname=%s --start_time=%s ' \
          % (config.var('GOOGLEBOT_DIR'), config.var('CRAWLER_LOOP_COUNT'),
             config.var('BASE_CRAWL_NAME'), start_timestamp)

    if config.var('CRAWL_EMAIL'):
      cmd = cmd + ' --email=%s ' % (config.var('CRAWL_EMAIL'))
    if "--noport" in additional_args:
      cmd = cmd + ' --noport '

    # loop require another layer for escaping
    # TODO - runcrawler has a bug where this is assigned to
    # argslist instead of arglist - if we fix it here we get
    # additional double quotes around our single quotes
    arglist = map(servertype.mkarg, arglist)

  # end if needs to wrap in loop

  # add in the acutal command
  # TODO - not using the executable call here
  # localized_bin = IsServerLocalized(config, name)
  # cmd = cmd + ' %s %s ' % (executable(binary_to_use, localized_bin, 1),
  #                          string.join(arglist))
  cmd = cmd + ' %s %s ' % (binary_path, string.join(arglist))

  if do_su: # su needs another layer of escaping
    cmd = pre_cmd + commands.mkarg(cmd)
  else:
    cmd = pre_cmd + cmd

  if config.var('CRAWL_LOGDIR'):
    logfile = "%s/out_%s_%s_%s" % (config.var('CRAWL_LOGDIR'), name, host, port)
    cmd = cmd + ' >> %s 2>&1 ' % logfile
  if not config.var('RUN_LOCALLY'):
    cmd = ('cd %s; ' % config.var('MAINDIR')) + cmd

  return cmd

#-------------------------------------------------------------------------------
# Args Common
#-------------------------------------------------------------------------------

def args_crawl_server_common(config, srvname, port):
  num_shards = config.GetNumShards(srvname)
  shard_num = servertype.GetPortShard(port)
  args = [
    "--port=%d" % (port),
    "--datadir=" + config.var('DATADIR'),
    "--commandflagsdumpfile=%s_cmdflg_%03d_of_%03d" % (srvname, shard_num, num_shards),
    ]

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES') and (srvname != 'rtdupserver'):
    args.append("--keep_checksum_for_checkpoints=false")

  return args

#-------------------------------------------------------------------------------
# URLSERVER
#-------------------------------------------------------------------------------

def args_urlserver(config, port):

  urlmanagers = serverflags.MakeHostPortsArg(
    config.GetServerHostPorts('urlmanager')
  )

  args =  [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--datadir=" + config.var('DATADIR'),
    "--port=%d" % (port),
    "--url_managers=%s" % (urlmanagers),
    "--default_fetchtime=200",
    "--max_fetchtime=%d" % (config.var('URLSERVER_MAX_FETCHTIME')), # In msecs
    "--max_url_manager_request_size=%d" % \
      config.var('URLSERVER_MAX_URLMANAGER_REQUEST_SIZE'),
    "--urlserver_max_hosts=%d" % (config.var('URLSERVER_MAX_HOSTS')),
    "--report_interval=60",
    ]

  var_and_flags = [
    ('URLSERVER_REQUERY_BLOCKED_URLMANAGER_INTERVAL',
     '--requery_blocked_urlmanager_interval'),
    ]
  args = args + servertype.BuildFlagArgs(config, var_and_flags)

  if config.var('URLSERVER_PAUSED'):
    args.append("--pause")

  if config.var('URLSERVER_DYNAMIC_MAX_INFLIGHT_PER_HOST'):
    args.append("--dynamic_max_inflight_per_host")

  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_protocolbuffers")
  if config.var('LOG_OUTGOING_PROTOCOLBUFFERS'):
    args.append("--log_outgoing_protocolbuffers")

  if config.var('URLSERVER_ADJUST_MIN_MEMORY_DYNAMICALLY'):
    args.append("--adjust_min_mem_dynamically")

  if config.var('URLSERVER_FETCHTIME_AVERAGE_SMOOTHING_WEIGHT'):
    args.append("--fetchtime_average_smoothing_weight=%f" % (
      config.var('URLSERVER_FETCHTIME_AVERAGE_SMOOTHING_WEIGHT')))

  if config.var('URLSERVER_URLMANAGER_EQUALIZATION_FRACTION'):
    # TODO -- poorly named arg to the urlserver, it is actually a fraction
    args.append("--url_manager_percent_url_request_to_equalize=%f" % \
      config.var('URLSERVER_URLMANAGER_EQUALIZATION_FRACTION'))

  if config.var('URLSERVER_URLMANAGER_REQUEST_QUORUM'):
    args.append("--urlmanager_request_quorum=%d" % \
      config.var('URLSERVER_URLMANAGER_REQUEST_QUORUM'))

  if config.var('URLSERVER_URLMANAGER_TIMEOUT'):
    args.append("--urlmanager_timeout=%d" % (
      config.var('URLSERVER_URLMANAGER_TIMEOUT')))

  if config.var('URLSERVER_URLMANAGER_MIN_REQUEST_SIZE') != None:
    args.append("--min_url_manager_request_size=%d" % (
      config.var('URLSERVER_URLMANAGER_MIN_REQUEST_SIZE')))

  if config.var('URLSERVER_ACCEPTABLE_URLMANAGER_SKEW'):
    args.append("--url_manager_acceptable_crawled_url_skew=%d" % \
      config.var('URLSERVER_ACCEPTABLE_URLMANAGER_SKEW'))

  if config.var('URLSERVER_DROP_READY_URLS_THRESHOLD') != None:
    args.append("--drop_ready_urls_threshold=%f" % \
      config.var('URLSERVER_DROP_READY_URLS_THRESHOLD'))
  if config.var('URLSERVER_DROP_READY_URLS_PERCENTAGE') != None:
    args.append("--drop_urls_percentage=%f" %
      config.var('URLSERVER_DROP_READY_URLS_PERCENTAGE'))
  if config.var('URL_DISABLE_INFINITE_SPACE_CHECK'):
    args.append("--disable_infinitespace_check")
  if config.var('URLSERVER_MAX_MEMORY') != None:
    args.append("--urlserver_max_memory=%d" % config.var('URLSERVER_MAX_MEMORY'))
  if config.var('MAX_INFLIGHT_PER_HOST') != None:
    args.append("--max_inflight_per_host=%d" % config.var('MAX_INFLIGHT_PER_HOST'))
  if config.var('DEFAULT_GOAL_INFLIGHT_PER_HOST'):
    args.append("--default_goal_inflight_per_host=%d" %
                config.var('DEFAULT_GOAL_INFLIGHT_PER_HOST'))
  if config.var('URLSERVER_LOAD_LOG_FACTOR') != None:
    args.append("--load_log_factor=%d" % config.var('URLSERVER_LOAD_LOG_FACTOR'))
  if config.var('URLSERVER_LOAD_LOG_MULTIPLIER') != None:
    args.append("--load_log_multiplier=%f" % \
      config.var('URLSERVER_LOAD_LOG_MULTIPLIER'))

  if config.var('HOSTLOAD_DIE_ON_INCOMPLETE_HOST_SPECIFICATION') == 0:
    args.append("--die_on_incomplete_host_specification=false")

  if config.var('CRAWL_SCHEDULE_BITMAP') != None:
    args.append("--batch_crawl_schedule_bitmap_file=%s" %
                config.var('CRAWL_SCHEDULE_BITMAP'))

  if config.var('ENTERPRISE_SCHEDULED_CRAWL_MODE'):
    args.append("--enterprise_batch_crawl_mode")

  if config.var('REUSE_CRAWL'):
    if config.var('URLSERVER_URLFP_AS_DOCID'):
      args.append("--urlfp_as_docid")
    else:
      historyservers_and_ports = serverflags.MakeHostPortsArg(
        config.GetServerHostPorts('historyserver')
        )
      if (not config.var('URLMANAGER_URLS_SCHEDULED') and
          not config.var('ENTERPRISE') and
          not historyservers_and_ports):
        # If we are not using urlscheduler and not enterprise,
        # then we need historyservers for reuse.
        sys.exit("REUSE_CRAWL flag set but no historyservers specified and "
                 "URLMANAGER_URLS_SCHEDULED is not set")
      if historyservers_and_ports:
        args.append("--historyservers=" + historyservers_and_ports)
        args.append("--conn_per_backend=%d" %
                    config.var('CONNS_PER_HISTORYSERVER'))
        args.append("--historyserver_timeout=%d" %
                    config.var('HISTORYSERVERCLIENT_TIMEOUT'))
        args.append("--historyserver_queue_len=%d " %
                    config.GetNumShards('urlmanager'))
      # end if
    if config.var('RTINDEXER_FOR_SERVING'):
      args.append("--docserver_shards=%d" % config.GetNumShards('base_indexer'))
    elif config.var('RTSLAVE_FOR_SERVING'):
      shards = config.GetNumShards('rtsubordinate')
      if shards == 0:
        # No shards, so check if there are any shards for the port-shifted
        # rtsubordinate; GSA shifts ports when running in TEST mode.
        shards = config.GetNumShards('rtsubordinate:1')
      args.append("--docserver_shards=%d" % shards)
    else:
      # otherwise just see how many docservers the bot talks to
      # TODO: ejhong says this is the best way to do this right now, but it
      # is kind of ugly because it involves us grovelling through ports
      srv_mngr = config.GetServerManager()
      set = srv_mngr.Set('bot')
      doc_ports = {}
      for (host,port) in set.BackendHostPorts('doc'): doc_ports[port] = 1
      args.append("--docserver_shards=%d" % len(doc_ports.keys()))

  if config.var('URLSERVER_MAX_SLACKING_URLMANAGERS') != None:
    args.append("--max_slacking_urlmanagers=%d" %
                config.var('URLSERVER_MAX_SLACKING_URLMANAGERS'))

  if config.var('URLSERVER_SLACKING_URLMANAGER_REQUEST_SIZE_MULTIPLIER'):
    args.append("--slacking_urlmanager_request_size_multiplier=%f" %
                config.var('URLSERVER_SLACKING_URLMANAGER_REQUEST_SIZE_MULTIPLIER'))

  if config.var('URLSERVER_URL_SIZE_GROUP_THRESHOLD') != None:
    args.append("--url_size_group_threshold=%d" %
                config.var('URLSERVER_URL_SIZE_GROUP_THRESHOLD'))

  if config.var('URLSERVER_FILTER_DUPLICATE_URLS'):
    args.append("--filter_duplicate_urls")

  ### Hostload stuff

  args.append("--default_hostload=%f" % config.var('URLSERVER_DEFAULT_HOSTLOAD'))
  args.append("--hostloadfile=%s" % config.var('HOSTLOADS'))

  if config.var('URLSERVER_MAX_HOSTLOAD') != None:
    args.append("--max_hostload=%f" % config.var('URLSERVER_MAX_HOSTLOAD'))
  if config.var('URLSERVER_HOSTLOAD_SPLIT_FACTOR'):
    args.append("--split_factor=%f" %
                config.var('URLSERVER_HOSTLOAD_SPLIT_FACTOR'))
  if config.var('URLSERVER_I_REALLY_WANT_NO_HOSTLOAD_SERVER'):
    args.append("--i_really_want_no_hostload_server")

  # Add the hostload server backends. Since the hostload servers may not
  # be in the specified in the same config file and they are
  # global (hlserver0.prods., etc) we may have them in a special param
  if config.GetNumShards('hlserver') > 0:
    (shardinfo, backends) = servertype.GetShardInfoBackends(
      config, 'hlserver', 0, 'http',
      config.var('URLSERVER_HLSERVER_NUM_CONNECTIONS'))
  elif config.var('URLSERVER_HLSERVERS'):
    #
    # We need this because the hlservers are global, and between colocs,
    # so we cannot use services file ..
    #
    backends = serverflags.Backends()
    shardinfo = serverflags.ShardInfo()
    minport = 1000000
    maxport = 0
    # segment for backends/shardinfo is unrelevant here, using 0
    for l in config.var('URLSERVER_HLSERVERS'):
      (h,p) = string.split(l, ":")
      p = string.atoi(p)
      if p < minport: minport = p
      if p > maxport: maxport = p
      backends.AddBackend(h, p, 0, 'hlserver', 0)
    type_level = 'hlserver:0'
    shardinfo.set_min_port(type_level, 0, minport)
    shardinfo.set_max_port(type_level, 0, maxport)
    shardinfo.set_protocol(type_level, 0, 'http')
    shardinfo.set_num_conns(type_level, 0,
                            config.var('URLSERVER_HLSERVER_NUM_CONNECTIONS'))
  else:
    backends = None
    shardinfo = None

  if not config.var('URLSERVER_DISABLE_HOSTLOAD_SERVER'):
    args.append("--hostload_server_client_id=%s_%s" % (
      config.var('CRAWL_CLASS'), config.var('BASE_CRAWL_NAME')))
  if backends and backends.NumBackEnds() > 0:
    args.append("--backends=%s" % backends.AsString())
    args.append("--shardinfo=%s" % shardinfo.AsString())

  return args

def restart_urlserver(config, host, port):
  args = args_urlserver(config, port)
  return restart_wrapper("urlserver", config, host, port, args)

servertype.RegisterRestartFunction('urlserver', restart_urlserver)

#-------------------------------------------------------------------------------
# RFSERVER
#-------------------------------------------------------------------------------

def restart_empty(config, host, port):
  print "%s:%d has nothing to restart" % (host, port)

def args_rfserver(config, port):
  args = [
    "--datadir=" + config.var('DATADIR'),
    "--port=%d" % (port),
    "--nologging"     # we don't really care that we've opened another bigfile
    ]
  if config.var('RFSERVER_LOG_REQUEST_HDRS'):
    args.append("--log_request_hdrs")
  if config.var('RFSERVER_MAX_MEMORY_IN_MB'):
    args.append("--max_memory=%d" % config.var('RFSERVER_MAX_MEMORY_IN_MB'))
  return args

def restart_rfserver(config, host, port):
  args = args_rfserver(config, port)
  return restart_wrapper("rfserver", config, host, port, args)

servertype.RegisterRestartFunction('rfserver', restart_rfserver)
servertype.RegisterRestartFunction('rfserver_bank', restart_empty)
servertype.RegisterRestartFunction('rfserver_replica_bank', restart_empty)

#-------------------------------------------------------------------------------
# URLMANAGER
#-------------------------------------------------------------------------------

def args_urlmanager(config, host, port, use_base_crawl):
  num_shards = config.GetNumShards('urlmanager')
  shard_num = servertype.GetPortShard(port)
  urls_per_shard = (config.var('TOTAL_URLS_EXPECTED') / \
    config.GetNumShards('urlmanager'))
  # Round urls_per_shard up to a number of buckets figure, to get the
  # hash tables sized correctly
  num_buckets = 2
  while num_buckets < urls_per_shard:
    num_buckets = num_buckets * 2
  num_buckets = num_buckets + 1  # Bump up to next bucket level

  # compute the argument that specifies all of the group fractions
  groups = ""
  if config.var('INTERNATIONAL_FRACTION'):
    groups = groups + ("international=%0.4f," % config.var('INTERNATIONAL_FRACTION'))
  if config.var('WESTERN_EUROPE_FRACTION'):
    groups = groups + ("western_europe=%0.4f," % config.var('WESTERN_EUROPE_FRACTION'))
  if config.var('CGI_FRACTION'):
    groups = groups + ("cgi=%0.4f," % config.var('CGI_FRACTION'))
  if config.var('FILETYPE_FRACTION'):
    groups = groups + ("filetype=%0.4f," % config.var('FILETYPE_FRACTION'))
  if config.var('IMAGE_FRACTION'):
    groups = groups + ("image=%0.4f," % config.var('IMAGE_FRACTION'))


  args = args_crawl_server_common(config, 'urlmanager', port)
  args = args + [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--shard_num=%d" % shard_num,
    "--url_manager_num_shards=%d" % config.GetNumShards('urlmanager'),
    "--urls_expected_per_shard=%d" % (num_buckets),
    "--checkpoints_to_keep=%d" % (config.var('URLMANAGER_CHECKPOINTS_TO_KEEP')),
    "--keep_every_nth_old_checkpoint=%d" %
    (config.var('URLMANAGER_KEEP_EVERY_NTH_OLD_CHECKPOINT')),
    "--checkpoint_interval=%d" % (config.var('URLMANAGER_CHECKPOINT_INTERVAL')),
    "--report_interval=%d" % (config.var('URLMANAGER_REPORT_INTERVAL')),
    "--retry_interval=%d" % (config.var('URLMANAGER_RETRY_INTERVAL')),
    "--min_time_between_computations=%d" %
    (config.var('URLMANAGER_REUSE_RESULTS_TIME')),
    "--badurls=" + config.var('BADURLS_URLMANAGER'),
    "--retry_error_urls=0", # No retrying of error URLs
    ]
  if config.var('STARTURLS'):
    args.append("--starturls=%s" % config.var('STARTURLS'))

  localized = IsServerLocalized(config, 'urlmanager')
  args = args + GetUrlCanonicalizationArgs(config, localized)

  if config.var('URLMANAGER_URLS_NONTERMINAL_FREQ') >= 0:
    args.append("--urls_nonterminal_freq=%d" %
                config.var('URLMANAGER_URLS_NONTERMINAL_FREQ'))
  else: # auto
    if urls_per_shard < 2000000: # small number of URLs
      args.append("--urls_nonterminal_freq=0") # disable non-terminal support
    else:
      args.append("--urls_nonterminal_freq=8") # used by main crawl

  if config.var('URLMANAGER_READ_PR_INTERVAL'):
    args.append("--read_pagerank_interval=%d" % (
      config.var('URLMANAGER_READ_PR_INTERVAL')))

  if config.var('URLMANAGER_PAGERANK_HISTO_INTERVAL'):
    args.append("--pagerank_histo_interval=%d" % (
      config.var('URLMANAGER_PAGERANK_HISTO_INTERVAL')))

  if config.var('CRAWL_ID_STRING') and not use_base_crawl:
    args.append("--crawl_id_string=%s" % config.var('CRAWL_ID_STRING'))

  if config.var('URLMANAGER_MIN_PAGERANK_TO_CRAWL'):
    args.append("--min_pr_to_crawl=%d" %
                config.var('URLMANAGER_MIN_PAGERANK_TO_CRAWL'))

  if config.var('URLMANAGER_FIXED_STARTURL_PR'):
    args.append("--fixed_starturl_pr=%d" %
                config.var('URLMANAGER_FIXED_STARTURL_PR'))

  if config.var('URLMANAGER_MIN_PR_DELTA_TO_RECRAWL'):
    args.append("--min_pr_delta_to_recrawl=%d" %
                config.var('URLMANAGER_MIN_PR_DELTA_TO_RECRAWL'))

  if config.var('URLMANAGER_USE_URLMANAGER_PR_FOR_NEW_URL') != None:
    if config.var('URLMANAGER_USE_URLMANAGER_PR_FOR_NEW_URL'):
      args.append("--use_urlmanager_pr_for_new_url")
    else:
      args.append("--use_urlmanager_pr_for_new_url=false")
  # end if URLMANAGER_USE_URLMANAGER_PR_FOR_NEW_URL is defined

  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_protocolbuffers")
  if config.var('LOG_OUTGOING_PROTOCOLBUFFERS'):
    args.append("--log_outgoing_protocolbuffers")

  if config.var('URLMANAGER_SKIP_FIRST_PAGERANK_ITERATION'):
    args.append("--skip_first_pagerank_iteration")

  if config.var('URLMANAGER_ENABLE_OLDPR'):
    oldpr_var_and_flags = [
      ('URLMANAGER_ENABLE_OLDPR',    '--old_pagerank_enable'),
      ('URLMANAGER_MIN_OLDPR',       '--old_pagerank_min_pr'),
      ('URLMANAGER_RECORD_DROPPED_FPPR_DURING_STATUS_TABLE_LOAD',
       '--record_dropped_fppr_during_status_table_load'),
      ('URLMANAGER_RECORD_UNKNOWN_FPPR_DURING_INITIAL_PR_UPDATE',
       '--record_unknown_fppr_during_initial_pr_update'),
      ]
    args = args + servertype.BuildFlagArgs(config, oldpr_var_and_flags)
  #endif oldpr

  if config.var('URLMANAGER_SCALE_BUCKETS_BY_HOSTLOAD'):
    args.append("--default_hostload=%f" % (config.var('URLSERVER_DEFAULT_HOSTLOAD')))
    args.append("--hostloadfile=%s" % (config.var('HOSTLOADS')))

  if config.var('URLMANAGER_DOMAIN_BUCKETS'):
    args.append("--use_domain_buckets")

  if config.var('URLMANAGER_EVENT_BUFFER_SIZE'):
    args.append("--event_buffer_size=%d" %
                (config.var('URLMANAGER_EVENT_BUFFER_SIZE')))

  if config.var('URLMANAGER_GENERATE_DUPS_FILE') \
     and (config.var('URLMANAGER_GENERATE_DUPS_FILE') >= 1):
    args.append("--generate_dups_file")

  if config.GetNumShards("limitd") > 0:
    args.append("--limited_urls=%s" % (config.var('LIMITD_LIMITED_URLS')))

  if config.var('URLMANAGER_GARBAGE_COLLECT_STATE_FILES'):
    args.append("--garbage_collect_state_files")

  if config.var('URLMANAGER_GARBAGE_COLLECT_INCOMING_LOGS'):
    args.append("--garbage_collect_incoming_logs")

  # always pass these variables because they are used to convert pageranks
  # to and from log space.
  args.append("--pr_num_pages=%s" %
              (prodlib.int_to_string(config.var('TOTAL_URLS_EXPECTED'))))
  args.append("--pr_num_pages_normalization=%d" % (config.var('PR_NUM_PAGES_NORM')))

  if config.var('USE_PAGERANK'):
    pr_mains = serverflags.MakeHostPortsArg(config.GetServerHostPorts('pr_main'))
    args.append("--pr_machines=%s" % (pr_mains))
    args.append("--pr_num_par=%d" % num_pageranks(config.var('PAGERANKER_STARTURLS')))
    args.append("--pr_num_subshards=%d" % (config.var('PAGERANKER_NUM_SUBSHARDS')))
    args.append("--pr_shard=%d" % shard_num)
#    pr_replicas =  serverflags.MakeHostPortsArg(config.GetServerHostPorts('urlmanager'))
#    args.append("--pr_replicas=%s" % (pr_replicas))
    if config.var('RTSERVER_LOGS') and config.var('PAGERANKER_READ_LINKMAPS'):
      # doing continous crawl. Read prs from all pr_mains
      args.append("--proutput_shards=%d" % config.GetNumShards('urlmanager'))
      # pageranker do not read links from urlmanager
      args.append("--disable_link_output")

      # compute number of pagerankers mapped to a single linkserver
      link_server_type = get_global_link_machine_type(config)
      num_links = config.GetNumShards(link_server_type)
      num_prs = config.GetNumShards('pr_main')
      # verify num_prs is a multiple of num_links
      if num_prs % num_links != 0:
        print "No. of prs: %d is not a multiple of No. of global links: %d" % (
          num_prs, num_links)
        sys.exit(1)

      ratio = num_prs / num_links
      args.append("--pagerankers_per_linkmap=%d" % ratio)
    # end if config.var('RTSERVER_LOG') ...
  else:
    args.append("--no_pageranker")

  if not config.var('URLMANAGER_RELOAD_INPUT_URLS_IF_CHANGED'):
    args.append("--noreload_input_urls_if_changed")

  mustcrawlurls = config.var('MUSTCRAWLURLS')
  if mustcrawlurls and mustcrawlurls['filename']:
    if mustcrawlurls['sharded']:
      filename = "%s-%03d-of-%03d" % (mustcrawlurls['filename'],
                                      shard_num, num_shards)
    else:
      filename = mustcrawlurls['filename']
    # end if mustcrawlurls['sharded']
    args.append('--mustcrawlurls=%s' % filename)
  # endif mustcrawlurls

  if not config.var('URLMANAGER_RELOAD_INPUT_URLS_IF_CHANGED'):
    args.append("--noreload_input_urls_if_changed")


  if config.var('PAGERANKER_USE_WTD_LINKS'):
    args.append("--use_wtd_links")
  if config.var('MAX_INFLIGHT_PER_HOST') != None:
    args.append("--max_inflight_per_host=%d" % config.var('MAX_INFLIGHT_PER_HOST'))
  if config.var('DEFAULT_GOAL_INFLIGHT_PER_HOST'):
    args.append("--default_goal_inflight_per_host=%d" %
                config.var('DEFAULT_GOAL_INFLIGHT_PER_HOST'))
  args.append("--group_fractions=%s" % (groups))
  if config.var('URLMANAGER_RESTRICT_URLS'):
    args.append("--restricturls=" + config.var('URLMANAGER_RESTRICT_URLS'))
  if config.var('URLMANAGER_FAST_RETRY_URLS'):
    args.append("--fast_retry_urls=" + config.var('URLMANAGER_FAST_RETRY_URLS'))
  if config.var('TRACE_URLS'):
    args.append("--trace_urls=" + config.var('TRACE_URLS'))
  if config.var('URLMANAGER_UNREACHABLE_RETRY_PROBABILITY') != None:
    args.append("--unreachable_retry_probability=%.4f" %
                config.var('URLMANAGER_UNREACHABLE_RETRY_PROBABILITY'))
  if config.var('COMPLETEHOSTS') != None:
    args.append("--completehosts=%s" % config.var('COMPLETEHOSTS'))
  if config.var('COMPLETEDOMAINS') != None:
    args.append("--completedomains=%s" % config.var('COMPLETEDOMAINS'))
  if config.var('DEPTH0HOSTS') != None:
    args.append("--depth0_hosts=%s" % config.var('DEPTH0HOSTS'))
  if config.var('DEPTH1HOSTS') != None:
    args.append("--depth1_hosts=%s" % config.var('DEPTH1HOSTS'))
  if config.var('DISABLE_URL_NORMALIZATION'):
    args.append("--nonormalize_urls")
  if config.var('FEED_URLS'):
    args.append("--feededurls=%s" % config.var('FEED_URLS'))
  if config.var('ARCHIVE_URLS'):
    args.append("--archiveurls=%s" % config.var('ARCHIVE_URLS'))
  if not config.var('URLMANAGER_CRAWL_NEW_ARCHIVES'):
    args.append("--nocrawl_new_archives")

  if config.var('URLMANAGER_FULL_HOSTS_MULTIPLIER'):
    args.append("--full_hosts_multiplier=%f" %
                config.var('URLMANAGER_FULL_HOSTS_MULTIPLIER'))
  if config.var('URLMANAGER_FULL_DOMAINS_MULTIPLIER'):
    args.append("--full_domains_multiplier=%f" %
                config.var('URLMANAGER_FULL_DOMAINS_MULTIPLIER'))

  if config.var('URLMANAGER_HEAP_MULTIPLIER') and \
     (config.var('URLMANAGER_HEAP_MULTIPLIER') > 0):
    args.append("--heap_multiplier=%d" %
                config.var('URLMANAGER_HEAP_MULTIPLIER'))

  if config.var('URLMANAGER_MIN_HEAP_SIZE_LIMIT'):
    args.append("--min_heap_size_limit=%d" % \
                config.var('URLMANAGER_MIN_HEAP_SIZE_LIMIT'))

  # handle --max_crawled_urls
  if config.var('URLMANAGER_MAX_CRAWLED_URLS'): # explicitly set
    args.append("--max_crawled_urls=%d" %
                (config.var('URLMANAGER_MAX_CRAWLED_URLS') / num_shards))
    # else do auto setting
  elif (config.var('URLMANAGER_LIMIT_MAX_CRAWLED_URLS') and
        config.var('MAX_CRAWLED_URLS') and
        config.var('MAX_CRAWLED_URLS') > 0):
    max_crawled_urls = config.var('MAX_CRAWLED_URLS')
    # set the crawl limit for each urlmanager so that
    # each url manager will not have 110% x max_crawled_urls/num_shards
    # and the total crawled urls won't exceed
    # max_crawled_urls * (num_shards + 1) / num_shards.
    # The latter makes sure that we won't run into the situation when
    # urls from one urlmanager are completely uncrawled.
    max_urls_per_mgr = (max_crawled_urls / num_shards * (num_shards + 1)
                        / num_shards)
    if max_urls_per_mgr > max_crawled_urls * 11 / num_shards / 10:
      max_urls_per_mgr = max_crawled_urls * 11 / num_shards / 10
    args.append("--max_crawled_urls=%s" % prodlib.int_to_string(max_urls_per_mgr))
  # end if config.var('URLMANAGER_LIMIT_MAX_CRAWLED_URLS')...


  if config.var('URLMANAGER_LIMIT_MAX_CRAWLED_URLS') and \
     config.var('MAX_CRAWLED_URLS') and \
     config.var('MAX_CRAWLED_URLS') > 0:
    max_urls_per_mgr = config.var('MAX_CRAWLED_URLS') / num_shards
    # set the crawl limit for each urlmanager so that
    # each url manager will have at most
    # min(1.1, (num_shards + 1)/ num_shards) x max_crawled_urls/num_shards crawled urls.
    redundency_rate = float(num_shards + 1) / num_shards
    if redundency_rate > 1.1:
      redundency_rate = 1.1
    max_urls_per_mgr = int(max_urls_per_mgr * redundency_rate)
    args.append("--max_crawled_urls=%d" % max_urls_per_mgr)

  if config.var('URLTRACKER_FILTER_FILE'):
    args.append("--urltracker_filter_file=%s" % config.var('URLTRACKER_FILTER_FILE'))

  num_shards = config.GetNumShards('urlmanager')
  if not config.var('LOGS_REWRITER_TYPE'):
    num_writer_shards = config.GetNumShards('contentfilter')
  else:
    # if we are using log rewriters the number of input logs
    # logs is the nubmer of log rewriters (not contentfilters).
    num_writer_shards = config.GetNumShards('urlmanager_log_rewriter')
  #endif
  files = get_reader_rt_logs(config, 'urlmanager',
                             shard_num, num_shards,
                             num_writer_shards)
  if not config.var('GFS_ALIASES'):
    if config.var('ENABLE_WORKSCHEDULER_REMOVEDOC_SCHEDULER') or \
       config.var('ENABLE_CRAWLMANAGER_REMOVEDOC'):
      # this log will contain removedoc logs from the ripper process
      # if not gfs, only one shard
      files.append(servertype.GenLogfileBasename(
        config.var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX'),
        shard_num, num_shards, 0))
    if config.var('URLMANAGER_URLSCHEDULER_LOG_PREFIX'):
      # if we accept urlscheduler logs as input
      # no gfs so only one urlmgr shard.
      files.append(servertype.GenLogfileBasename(
        "%s%s" % ('/bigfile/',
                  config.var('URLMANAGER_URLSCHEDULER_LOG_PREFIX')),
        shard_num, num_shards, 0))

  # For feeder and feeder_doc_deleter, must have seperate logs even for GFS
  #feed doc deleter->urlmanager logs
  if config.var('ENABLE_WORKSCHEDULER_FEED_DOC_DELETER'):
    if (config.var('RTSERVER_LOGS') and
        config.var('RTLOG_FEED_DOC_DELETER_SUFFIX')):
      logbasename = (config.var('RTSERVER_LOGS')['urlmanager'] +
                     config.var('RTLOG_FEED_DOC_DELETER_SUFFIX'))
      files.extend(get_reader_rt_logs(config, 'urlmanager',
                                      shard_num, num_shards,
                                      1,  # 1 writer
                                      logbasename))
  #endif feed doc deleter->urlmanager logs
  #For feeder->urlmanager logs
  if config.var('RTSERVER_LOGS') and \
     config.var('RTLOG_FEEDER_SUFFIX'):
    logbasename = (config.var('RTSERVER_LOGS')['urlmanager'] +
                   config.var('RTLOG_FEEDER_SUFFIX'))
    files.extend(get_reader_rt_logs(config, 'urlmanager',
                                    shard_num, num_shards,
                                    config.GetNumShards('feeder'),
                                    logbasename))
  #endif feeder->rtindexers logs

  args.append('--incoming_log_filenames=%s' % \
              string.join(files, ","))

  if not config.var('GFS_ALIASES'):
    args.append(replicas_arg_pairwise_replication(config, port))
  # endif

  # add rfserver bank if specified
  args = args + servertype.GetRfserverBankArgs(config)

  if config.var('RESET_TO_UNCRAWLED_INTERVAL'):
    args.append("--reset_to_uncrawled_interval=%d" %
                config.var('RESET_TO_UNCRAWLED_INTERVAL'))

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    args.append("--keep_checksum_for_checkpoints=false")

  if config.var('URLMANAGER_FAST_RETRY_BOOST'):
    args.append("--fast_retry_boost=%f" % config.var('URLMANAGER_FAST_RETRY_BOOST'))

  if config.var('URLMANAGER_FAST_RETRY_HOMEPAGE_BOOST'):
    args.append("--fast_retry_homepage_boost=%f" % \
                config.var('URLMANAGER_FAST_RETRY_HOMEPAGE_BOOST'))

  if config.var('URLMANAGER_RETRY_UNREACHABLE_URLS'):
    args.append("--retry_unreachable_urls=%d" % \
                config.var('URLMANAGER_RETRY_UNREACHABLE_URLS'))

  # RT crawl/index related flags
  var_and_flags = [
    ('RT_EPOCH',                          '--epoch'),
    ('RT_SEGMENT',                        '--rt_segment'),
    ('RT_NUM_SEGMENTS',                   '--rt_num_segments'),
    ('URLMANAGER_VALID_RT_LEVELS_MASK',   '--valid_rt_levels_mask'),
    ('URLMANAGER_URL_CRAWL_STATUS_URLFPS_TO_RESET_IF_BAD',
     '--url_crawl_status_urlfps_to_reset_if_bad'),
    ('URLMANAGER_URL_CRAWL_STATUS_BACKWARD_COMPATIBLE_VERIFICATION',
     '--url_crawl_status_backward_compatible_verification'),

    ('URLMANAGER_COLLECT_LOGS_EPOCH',     '--collect_logs_epoch'),
    ('URLMANAGER_LOG_POSITIONS_CHECKPOINT_EPOCH',
     '--log_positions_checkpoint_epoch'),
    ]

  if config.var('URLMANAGER_COLLECT_LOGS_EPOCH') != None:
    args.append("--collect_logs_epoch=%d" %
                config.var('URLMANAGER_COLLECT_LOGS_EPOCH'))

  if config.var('URLMANAGER_LOG_POSITIONS_CHECKPOINT_EPOCH') != None:
    args.append("--log_positions_checkpoint_epoch=%d" %
                config.var('URLMANAGER_LOG_POSITIONS_CHECKPOINT_EPOCH'))

  if config.var('URLMANAGER_URLS_SCHEDULED'):
    assert(config.var('URLSCHEDULER_NAMESPACE_PREFIX') != None)
    assert(config.var('RT_SEGMENT') != None)
    args.append("--urls_scheduled=%s%s%02d_%03d_of_%03d" % (
      config.var('URLSCHEDULER_NAMESPACE_PREFIX'),
      config.var('URLMANAGER_URLS_SCHEDULED'),
      config.var('RT_SEGMENT'),
      shard_num, num_shards))

    var_and_flags = var_and_flags + [
      ('URLMANAGER_CANONICALIZE_SCHEDULED_URLS',
      '--canonicalize_scheduled_urls'),
      ('URLMANAGER_SKIP_CANONICALIZING_SCHEDULED_HOMEPAGES',
       '--skip_canonicalizing_scheduled_homepages'),
      ('URLMANAGER_MAX_NONCANONICALIZE_SCHEDULED_URLS',
       '--max_noncanonicalize_scheduled_urls'),
      ('URLMANAGER_TEST_MAX_SCHEDULED_URLS', '--test_max_scheduled_urls'),
      ('URLMANAGER_EXPECTED_NUM_URLS_IN_SCHEDULE',
       '--expected_num_urls_in_schedule'),
      ('URLMANAGER_MAX_PERCENTAGE_DELTA_FOR_SCHEDULED_URLS',
       '--max_percentage_delta_for_scheduled_urls'),
      ]
    #endif
  #end if url schedule specified
  if config.var('URLMANAGER_EXTRA_URLS_SCHEDULED'):
    # It doesn't make sense if EXTRA_URLS_SCHEDULED is defined
    # without defining URLS_SCHEDULED
    assert config.var('URLMANAGER_URLS_SCHEDULED')
    args.append("--extra_urls_scheduled=%s%02d_%03d_of_%03d" % (
      config.var('URLMANAGER_EXTRA_URLS_SCHEDULED'),
      config.var('RT_SEGMENT'),
      shard_num, num_shards))
  # end if

  if config.var('URLMANAGER_DRAIN_SKIP_STATUSTABLE_STAGE'):
    # we want to skip the statustable stage, don't bother with all the params
    args.append("--dm_crawl_percentage_for_dump_statustable_stage=-1")

  if ( config.var('URLMANAGER_AUTOMATE_RT_PARAMETERS') and
       config.var('NAMESPACE_PREFIX') ):
    if config.var('RT_INTERSEGMENT_DATA_PREFIX'):
      namespace_prefix = config.var('RT_INTERSEGMENT_DATA_PREFIX')
    else:
      namespace_prefix = config.var('NAMESPACE_PREFIX')
    if config.var('RT_PREVIOUS_EPOCH') != None:
      args.append("--input_url_status_table=" +
                  "%surlmanager_out_table_%02d_of_%02d_epoch%010d" % (
        namespace_prefix,
        shard_num, num_shards, config.var('RT_PREVIOUS_EPOCH')))
    else:
      args.append("--require_input_url_status_table=false")
    # end if
    args.append("--output_url_status_table=" +
                "%surlmanager_out_table_%02d_of_%02d_epoch%010d" % (
      namespace_prefix,
      shard_num, num_shards, int(config.var('RT_EPOCH'))))

  else:
    # no automated crawl status relaying

    if (config.var('URLMANAGER_INPUT_URL_STATUS_TABLE') != None and
        config.var('RT_EPOCH') != None):
      args.append("--input_url_status_table=%s_%02d_of_%02d_epoch%010d" %
                  (config.var('URLMANAGER_INPUT_URL_STATUS_TABLE'),
                   shard_num, num_shards,
                   config.var('RT_EPOCH')))

    if config.var('URLMANAGER_REQUIRE_INPUT_URL_STATUS_TABLE') == 0:
      args.append("--require_input_url_status_table=false")
    # end if

    if (config.var('URLMANAGER_OUTPUT_URL_STATUS_TABLE') != None and
        config.var('RT_EPOCH') != None):
      args.append("--output_url_status_table=%s_%02d_of_%02d_epoch%010d" %
                  (config.var('URLMANAGER_OUTPUT_URL_STATUS_TABLE'),
                   shard_num, num_shards, config.var('RT_EPOCH')))

    # end if
  # end if
  storedata_path = get_urlmanager_storedata_namespace_prefix(config,
                                                             shard_num,
                                                             num_shards)
  if storedata_path: args.append("--storedata_path=%s" % storedata_path)

  if config.var('URLMANAGER_RT_IGNORE_UNSCHEDULED_KNOWN_URLS') == 0:
    args.append("--nort_ignore_unscheduled_known_urls")
  # end if
  elif config.var('URLMANAGER_RT_IGNORE_UNSCHEDULED_KNOWN_URLS') != None:
    args.append("--rt_ignore_unscheduled_known_urls")
  # end if
  if config.var('URLMANAGER_RT_UNSPECIFIED_URLS_DEFAULT_LEVEL') != None:
    args.append("--rt_unspecified_urls_default_level=%d" %
                config.var('URLMANAGER_RT_UNSPECIFIED_URLS_DEFAULT_LEVEL'))
  # end if

  if config.var('URLMANAGER_DM_PERCENTAGE_FOR_REUSE') != None:
    args.append('--dm_crawl_percentage_for_reuse_stage=%d' %
                config.var('URLMANAGER_DM_PERCENTAGE_FOR_REUSE'))
  # end if
  if config.var('URLMANAGER_DM_PERCENTAGE_FOR_DUMP_UNCRAWLED') != None:
    args.append('--dm_crawl_percentage_for_dump_uncrawled_stage=%d' %
                config.var('URLMANAGER_DM_PERCENTAGE_FOR_DUMP_UNCRAWLED'))
  # end if
  if config.var('URLMANAGER_DM_PERCENTAGE_FOR_DUMP_STATUSTABLE') !=None:
    args.append('--dm_crawl_percentage_for_dump_statustable_stage=%d' %
                config.var('URLMANAGER_DM_PERCENTAGE_FOR_DUMP_STATUSTABLE'))
  # end if
  if config.var('URLMANAGER_UNCRAWLED_HIGHPR_URLS_DUMP_THRESHOLD'):
    args.append('--uncrawled_highpr_urls_dump_threshold=%d' %
                config.var('URLMANAGER_UNCRAWLED_HIGHPR_URLS_DUMP_THRESHOLD'))
  #end if
  if config.var('URLMANAGER_TOTAL_LOGREADER_MEMORY_IN_MB'):
    args.append("--total_logreader_memory_in_MB=%d" %
                config.var('URLMANAGER_TOTAL_LOGREADER_MEMORY_IN_MB'))
  # end if
  if config.var('URLMANAGER_MAX_LOGREADER_STALL_SECONDS'):
    args.append("--max_logreader_stall_seconds=%d" %
                config.var('URLMANAGER_MAX_LOGREADER_STALL_SECONDS'))
  #end if
  if config.var('URLMANAGER_USE_URLS_FILES'):
    args.append("--goodurls=%s" % (config.var('GOODURLS')))

  if config.var('URLMANAGER_NO_PR0_URLS_IN_NONTERMINALS'):
    args.append("--nowrite_pr0_urls_to_nonterminals")

  #end if
  # news crawl:
  if config.var('NEWS_CRAWL'):
    args.append("--news_mode")
    args.append("--newshub_file=%s" % config.var('NEWS_SOURCE_FILE'))
    args.append("--min_news_interval=%d" % config.var('MIN_NEWS_CRAWL_INTERVAL'))
    if config.var('MAX_NEWS_CRAWL_INTERVAL'):
      args.append("--max_news_interval=%d" %
                  config.var('MAX_NEWS_CRAWL_INTERVAL'))
    if config.var('MAX_NEWS_CRAWL_INTERVAL_NON_GOLDEN'):
      args.append("--max_news_interval_non_golden=%d" %
                  config.var('MAX_NEWS_CRAWL_INTERVAL_NON_GOLDEN'))
    if config.var('NEWS_CRAWL_HUBPAGE_FIRST_TIME'):
      args.append("--crawl_hubpage_first_time")

  if config.var('URLMANAGER_REFRESHTABLE_STRATEGY'):
    args.append("--refresh_strategy=%s" % \
                config.var('URLMANAGER_REFRESHTABLE_STRATEGY'))

  if config.var('URLMANAGER_REFRESH_URLS'):
    args.append('--multiclass_refresh_class_file=%s' % \
                config.var('URLMANAGER_REFRESH_URLS'))
  if config.var('URLMANAGER_REFRESHURL_LIMIT'):
    args.append('--multiclass_refresh_url_limit=%s' % \
                config.var('URLMANAGER_REFRESHURL_LIMIT'))
  if config.var('URLMANAGER_REFRESHCLASS_PERIODS'):
    args.append('--multiclass_refresh_class_definition=%s' % \
                config.var('URLMANAGER_REFRESHCLASS_PERIODS'))
  if config.var('URLMANAGER_REFRESHCLASS_DEFAULT'):
    args.append('--multiclass_default_refresh_class=%s' % \
                config.var('URLMANAGER_REFRESHCLASS_DEFAULT'))

  # support GFS or other name space
  if config.var('NAMESPACE_PREFIX'):
    args.append("--namespace_prefix=%s" % config.var('NAMESPACE_PREFIX'))
  # end if

  pr_prog = config.var('PAGERANKER_PROG')
  if config.var('OUTPUT_NAMESPACE_PREFIX').has_key(pr_prog):
    args.append("--pr_namespace_prefix=%s" %
                config.var('OUTPUT_NAMESPACE_PREFIX')[pr_prog])

  # end if
  args = args + get_gfs_args(config)

  if config.var('GFS_USER'):
    args.append('--gfs_user=%s' % config.var('GFS_USER'))

  if config.var('URLMANAGER_VERBOSE_ON_GIVEN_URLS'):
    args.append("--verbose_on_given_urls")
  # end if

  # if URLMANAGER_WRITE_TO_INDEXERS or RTLOG_URLMANAGER_MODE_SUFFIX are set,
  # allow urlmanager to talk to rtserver through rtlogs written by urlmanager
  if (config.var('URLMANAGER_WRITE_TO_INDEXERS') or
      config.var('RTLOG_URLMANAGER_MODE_SUFFIX')):
    # if either of the two is defined, make sure RTSERVER_LOGS is defined
    if not config.var('RTSERVER_LOGS'):
      print "Need RTSERVER_LOGS for indexer logfile names"
      sys.exit(-1)
    # end if
    files = []
    sfx = ''
    if config.var('RTLOG_URLMANAGER_MODE_SUFFIX'):
      sfx = config.var('RTLOG_URLMANAGER_MODE_SUFFIX')
    for indexer_type in ('base_indexer', 'daily_indexer', 'rt_indexer'):
      output_log = shardset_output_log_name(config, indexer_type, host , port,
                                            config.GetNumShards(indexer_type),
                                            sfx)
      if output_log: files.append(output_log)
    # end for
    args.append("--outgoing_log_info=%s" % string.join(files, ","))
  # end if
  if config.var('URLMANAGER_FORCE_ANCHOR_RELOADS') and \
     config.var('URLMANAGER_FORCE_ANCHOR_RELOADS') == 1:
    args.append("--force_anchor_reloads=true")
  # end if

  if config.var('URLMANAGER_LOG_SEEK_TO_END_IF_NO_CHECKPOINT') and \
     config.var('URLMANAGER_LOG_SEEK_TO_END_IF_NO_CHECKPOINT') == 1:
    args.append("--log_seek_to_end_if_no_checkpoint=true")

  if config.var('URLMANAGER_MAX_DISCOVERED_URLS') != None:
    args.append("--max_discovered_urls=%s" %
                prodlib.int_to_string(config.var('URLMANAGER_MAX_DISCOVERED_URLS')
                              / num_shards))
  if config.var('URLMANAGER_MAX_DISCOVERED_CRAWLED_URLS') != None:
    args.append("--max_discovered_crawled_urls=%s" %
                prodlib.int_to_string(config.var('URLMANAGER_MAX_DISCOVERED_CRAWLED_URLS')
                       / num_shards))

  if config.var('URLMANAGER_ISSUE_ANCHOR_REQUESTS'):
    assert config.GetNumShards('docidserver') == 0, (
           "cant use docidserver to do urlfp->docid translations " +
           "because urlmanagers only know urlfps. ")
    # TODO: handle anchor requests for daily indexers, too?
    assert config.GetNumShards('daily_indexer') == 0
    assert config.GetNumShards('rt_indexer') == 0
    args.append('--anchor_logfiles=%s' %
                sharded_rtanchor_log_args(config, 'base_indexer'))
    args.append('--nodm_replace_anchors_for_uncrawled') # disable anchorreplace

    intermediate_log_id_str = config.var('ANCHORREQ_INTERMEDIATE_LOG_ID')
    if intermediate_log_id_str:
      # write requests for scheduled urls to intermediate log files
      log_args = sharded_rtanchor_log_args(config, 'base_indexer',
                                           id_string=intermediate_log_id_str)
      args.append('--scheduled_urls_anchor_logfiles=%s' % log_args)
    #end if intermediate_log_id_str
  # end if config.var('URLMANAGER_ISSUE_ANCHOR_REQUESTS')

  if ( config.var('RT_ALL_PREVIOUS_EPOCHS_FOR_CYCLE') and
       config.var('URLMANAGER_USE_PREVIOUS_EPOCHS_DISCOVERED') ):
    (files, file_to_drop) = get_urlmanager_previous_discovered_files(
                                     config, shard_num, num_shards)
    if len(files) > config.var('RT_NUM_SEGMENTS'):
      raise 'We ended up with too many discovered files from previous segments.'\
            ' Something is fishy .. quiting now'
    # endif
    if file_to_drop:
      args.append('--discovered_urls_file_to_drop_nonterminals=%s' %
                  file_to_drop)
    # endif
    if files:
      args.append('--previously_discovered_urls_to_include=%s' %
                  string.join(files, ','))
    # endif
  # endif

  if config.var('HOSTLOAD_DIE_ON_INCOMPLETE_HOST_SPECIFICATION') == 0:
    args.append("--die_on_incomplete_host_specification=false")

  if config.var('URLMANAGER_FAILED_TOPPAGES_FILE_PREFIX'):
    toppages_base = '%s-%03d-of-%03d' % (
      config.var('URLMANAGER_FAILED_TOPPAGES_FILE_PREFIX'),
      shard_num, num_shards)
    if storedata_path:
      toppages_out = "%s/%s" % (storedata_path, toppages_base)
    else:
      toppages_out = toppages_base
    args.append('--failed_toppages=%s' % toppages_out)
  #endif FAILED_TOPPAGES_FILE_PREFIX

  if config.var('URLMANAGER_TRIGGER_FRACTION_FOR_CHECKERS'):
    trigger_num_urls = ((config.var('URLMANAGER_TRIGGER_FRACTION_FOR_CHECKERS') *
                         config.var('MAX_CRAWLED_URLS')) / num_shards)
    args.append('--trigger_point_for_checkers=%d' % int(trigger_num_urls))
  # endif trigger_fraction

  # NOTE: new urlmanager flags should try to use BuildFlagArgs
  #       to simplify
  var_and_flags = var_and_flags + [
    ('URLMANAGER_TOPPAGES_FILE',              '--toppages'),
    ('URLMANAGER_MAX_FAILED_TOPPAGES_CHECKS', '--max_failed_toppages_checks'),
    ('URLMANAGER_CHECKERS_TO_RUN',            '--checkers_to_run'),
    ('URLMANAGER_DISTRIBUTION_CHECK_CONFIG',  '--distribution_check_config'),
    ('URLMANAGER_MIN_PR_FOR_TOPPAGES',        '--min_pr_for_toppages'),

    ('URLMANAGER_CRAWL_ALL_HOMEPAGES',        '--crawl_all_homepages'),
    ('URLMANAGER_MAX_DASHES_FOR_HOMEPAGE_BOOST',
     '--max_dashes_for_homepage_boost'),
    ('URLMANAGER_GENERATE_DISCOVERED_URLS',   '--generate_discovered_urls'),
    ('URLMANAGER_GENERATE_DROPPED_DISCOVERED_URLS',
     '--generate_dropped_discovered_urls'),

    ('URLMANAGER_USE_YAHOO_GROUPS_REWRITER', '--use_yahoo_groups_rewriter'),

    ('URLMANAGER_MAX_MISSHARDED_URLS',        '--max_missharded_urls'),
    ('URLMANAGER_MAX_INCONSISTENT_ATTEMPTED_URLS',
     '--max_inconsistent_attempted_urls'),
    ('URLMANAGER_DISABLE_CHECK_DISCOVERED_URLS_FILES_SIZE',
     '--disable_check_discovered_urls_files_size'),
    ('URLMANAGER_DISCARD_UNKNOWN_FP_PRS_THRESHOLD',
     '--discard_unknown_fp_prs_threshold'),
    ('URLMANAGER_UNREAD_BYTES_MIN_RECOMPUTE_TIME',
     '--unread_bytes_min_recompute_time'),
    ('URLMANAGER_MODE_CONTROL_FILE',        '--urlmanager_mode_control_file'),
    ('URLMANAGER_MAX_PR_FOR_LIMITED_URLS',  '--max_pagerank_for_limited_urls'),
    ('URLMANAGER_SCHEDULED_PR_DECAY_RATE',  '--scheduled_pr_decay_rate'),
    ('URLMANAGER_MAX_SCHEDULED_URL_SUPPLIED_PR',
     '--max_scheduled_url_supplied_pr'),
    ('URLMANAGER_FORCE_SITEMAP_CRAWL', '--force_sitemap_crawl'),
    ('URLMANAGER_SITEMAP_URLS', '--sitemap_urls'),
    ('URLMANAGER_PREFETCH_REQUEST_SIZE',    '--prefetch_request_size'),
    ('URLMANAGER_IGNORE_NON_UNCRAWLED_URLS_WHEN_SENDTOURLSERVER',
     '--ignore_non_uncrawled_urls_when_sendtourlserver'),
    ('URLMANAGER_MIN_TIME_BETWEEN_RESPOND_SEND_TO_URLSERVER',
     '--min_time_between_respond_send_to_urlserver'),
    ]
  args = args + servertype.BuildFlagArgs(config, var_and_flags)

  # warnings about deprecated flags
  if config.has_var('URLMANAGER_DISCARD_UNKNOWN_FP_PRS'):
    print "Error: URLMANAGER_DISCARD_UNKNOWN_FP_PRS is deprecated"
    print "       Please use URLMANAGER_DISCARD_UNKNOWN_FP_PRS_THRESHOLD instead"
    sys.exit(-1)
  # end if

  return args

def gen_rtserver_urlmgr_log_config(config, machine_type):
  num_shards = config.GetNumShards(machine_type)
  if num_shards > 0:
    return "%s:%s%s@%d" % (machine_type,
                            config.var('RTSERVER_LOGS')[machine_type],
                            config.var('RTLOG_URLMANAGER_MODE_SUFFIX'),
                            num_shards)
  else:
    return ""


# Enterprise specific crawlmanager
def args_crawlmanager(config, port):
  num_shards = config.GetNumShards('urlmanager')
  shard_num = servertype.GetPortShard(port)
  urls_per_shard = (config.var('TOTAL_URLS_EXPECTED') /
                    config.GetNumShards('urlmanager'))

  args = args_crawl_server_common(config, 'urlmanager', port)
  args = args + [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--url_canonicalize_to_punycode",
    "--shard_num=%d" % shard_num,
    "--url_manager_num_shards=%d" % config.GetNumShards('urlmanager'),
    "--urls_expected_per_shard=%d" % (urls_per_shard),
    "--checkpoints_to_keep=%d" % (config.var('URLMANAGER_CHECKPOINTS_TO_KEEP')),
    "--checkpoint_interval=%d" % (config.var('URLMANAGER_CHECKPOINT_INTERVAL')),
    "--badurls=" + config.var('BADURLS_URLMANAGER'),
    # We attempt to crawl pages at least twice as fast as they are changing:
    "--default_high_ranking_url_change_interval=%d" % \
    (4 * 24 * 3600),   # crawl every ~2 days.
    "--default_low_ranking_url_change_interval=%d" % \
    (20 * 24 * 3600),  # crawl every ~10 days.
    "--max_high_ranking_url_change_interval=%d" % \
    (6 * 24 * 3600),   # crawl every ~3 days.
    "--max_low_ranking_url_change_interval=%d" % \
    (40 * 24 * 3600),  # crawl every ~20 days.
    "--crawl_frequently_change_interval=%d" % \
    (2 * 24 * 3600),   # crawl every at least once a day.
    "--crawl_seldom_change_interval=%d" % \
    (180 * 24 * 3600)  # crawl every ~3 months.
    ]

  if config.var('ENTERPRISE_SCHEDULED_CRAWL_MODE'):
    args.append("--enterprise_batch_crawl_mode")

  if config.var('STARTURLS'):
    args.append("--starturls=%s" % config.var('STARTURLS'))
  if config.var('URLMANAGER_REFRESH_URLS'):
    args.append("--crawl_frequently_urls=%s" %
                config.var('URLMANAGER_REFRESH_URLS'))
  if config.var('URLSCHEDULER_ARCHIVE_URLS'):
    args.append("--crawl_seldom_urls=%s" %
                config.var('URLSCHEDULER_ARCHIVE_URLS'))

  if config.var('CONTENTFILTER_KEEP_ROBOTS_PAGE'):
    args.append('--keep_robots_page')
  else:
    args.append('--nokeep_robots_page')

  if config.var('IF_MODIFIED_SINCE'):
    # note: use urllib.quote() in case IF_MODIFIED_SINCE has spaces
    args.append("--if_modified_since=%s" %
                urllib.quote(config.var('IF_MODIFIED_SINCE')))

  localized = IsServerLocalized(config, 'urlmanager')
  args = args + GetUrlCanonicalizationArgs(config, localized)

  if config.var('URLMANAGER_READ_PR_INTERVAL'):
    args.append("--read_pagerank_interval=%d" % (
      config.var('URLMANAGER_READ_PR_INTERVAL')))

  if config.var('URLMANAGER_FIXED_STARTURL_PR'):
    args.append("--fixed_starturl_pr=%d" %
                config.var('URLMANAGER_FIXED_STARTURL_PR'))

  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_protocolbuffers")
  if config.var('LOG_OUTGOING_PROTOCOLBUFFERS'):
    args.append("--log_outgoing_protocolbuffers")

  if config.var('URLMANAGER_EVENT_BUFFER_SIZE'):
    args.append("--event_buffer_size=%d" %
                (config.var('URLMANAGER_EVENT_BUFFER_SIZE')))

  # always pass these variables because they are used to convert pageranks
  # to and from log space.
  args.append("--pr_num_pages=%s" %
              (prodlib.int_to_string(config.var('TOTAL_URLS_EXPECTED'))))
  args.append("--pr_num_pages_normalization=%d" %
              (config.var('PR_NUM_PAGES_NORM')))

  if config.var('USE_PAGERANK'):
    # bug 192688: we cannot use fully-qualified hostname for pr_machines flag
    pr_mains = \
             serverflags.MakeHostPortsArg(config.GetServerHostPorts('pr_main'),
                                          sep=',', qualify=0)
    args.append("--pr_machines=%s" % (pr_mains))
    args.append("--pr_num_par=%d" %
                num_pageranks(config.var('PAGERANKER_STARTURLS')))
    args.append("--pr_num_subshards=%d" %
                (config.var('PAGERANKER_NUM_SUBSHARDS')))
    args.append("--pr_shard=%d" % shard_num)
    if config.var('RTSERVER_LOGS') and config.var('PAGERANKER_READ_LINKMAPS'):
      # doing continous crawl. Read prs from all pr_mains
      args.append("--proutput_shards=%d" % config.GetNumShards('urlmanager'))

      # compute number of pagerankers mapped to a single linkserver
      link_server_type = get_global_link_machine_type(config)
      num_links = config.GetNumShards(link_server_type)
      num_prs = config.GetNumShards('pr_main')
      # verify num_prs is a multiple of num_links
      if num_prs % num_links != 0:
        print "No. of prs: %d is not a multiple of No. of global links: %d" % (
          num_prs, num_links)
        sys.exit(1)

      ratio = num_prs / num_links
      args.append("--pagerankers_per_linkmap=%d" % ratio)
    # end if config.var('RTSERVER_LOG') ...
    pr_prog = config.var('PAGERANKER_PROG')
    if config.var('OUTPUT_NAMESPACE_PREFIX').has_key(pr_prog):
      args.append("--pr_namespace_prefix=%s" %
                  config.var('OUTPUT_NAMESPACE_PREFIX')[pr_prog])
  else:
    args.append("--no_pageranker")

  # handle crawl limits: We have two limit:
  # - hard limit which is never exceeded and is the license limit + 20%.
  # - soft limit which is the license limit. we will continue crawling high
  #   ranking URLs even past this limit.
  if (config.var('MAX_CRAWLED_URLS') and config.var('MAX_CRAWLED_URLS') > 0):
    max_crawled_urls = config.var('MAX_CRAWLED_URLS')
    hard_limit = (max_crawled_urls * 12) / (num_shards * 10)  # +20%
    soft_limit = max_crawled_urls / num_shards
    args.append("--urls_hard_limit=%d" % hard_limit)
    args.append("--urls_soft_limit=%d" % soft_limit)

  num_shards = config.GetNumShards('urlmanager')
  if not config.var('LOGS_REWRITER_TYPE'):
    num_writer_shards = config.GetNumShards('contentfilter')
  else:
    # if we are using log rewriters the number of input logs
    # logs is the nubmer of log rewriters (not contentfilters).
    num_writer_shards = config.GetNumShards('urlmanager_log_rewriter')
  #endif
  files = get_reader_rt_logs(config, 'urlmanager',
                             shard_num, num_shards,
                             num_writer_shards)
  if not config.var('GFS_ALIASES'):
    if config.var('ENABLE_WORKSCHEDULER_REMOVEDOC_SCHEDULER') or \
       config.var('ENABLE_CRAWLMANAGER_REMOVEDOC'):
      # this log will contain removedoc logs from the ripper process
      # if not gfs, only one shard
      files.append(servertype.GenLogfileBasename(
        config.var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX'),
        shard_num, num_shards, 0))
    # change intervals from crawlscheduler.
    files.append(servertype.GenLogfileBasename("/bigfile/changeintervals",
      shard_num, num_shards, 0))

  # For feeder and feeder_doc_deleter, must have seperate logs even for GFS
  #feed doc deleter->crawlmanager logs
  if config.var('ENABLE_WORKSCHEDULER_FEED_DOC_DELETER'):
    if (config.var('RTSERVER_LOGS') and
        config.var('RTLOG_FEED_DOC_DELETER_SUFFIX')):
      logbasename = (config.var('RTSERVER_LOGS')['urlmanager'] +
                     config.var('RTLOG_FEED_DOC_DELETER_SUFFIX'))
      files.extend(get_reader_rt_logs(config, 'urlmanager',
                                      shard_num, num_shards,
                                      1,  # 1 writer
                                      logbasename))
  #endif feed doc deleter->crawlmanager logs

  #feeder->crawlmanager logs
  if config.var('RTSERVER_LOGS') and \
     config.var('RTLOG_FEEDER_SUFFIX'):
    logbasename = (config.var('RTSERVER_LOGS')['urlmanager'] +
                   config.var('RTLOG_FEEDER_SUFFIX'))
    files.extend(get_reader_rt_logs(config, 'urlmanager',
                                    shard_num, num_shards,
                                    config.GetNumShards('feeder'),
                                    logbasename))
  #endif feeder->crawlmanager logs

  args.append('--incoming_log_filenames=%s' %
              string.join(files, ","))

  if not config.var('GFS_ALIASES'):
    args.append(replicas_arg_pairwise_replication(config, port))
  # endif

  # add rfserver bank if specified
  args = args + servertype.GetRfserverBankArgs(config)

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    args.append("--keep_checksum_for_checkpoints=false")

  if config.var('URLMANAGER_USE_URLS_FILES'):
    args.append("--goodurls=%s" % (config.var('GOODURLS')))

  # support GFS or other name space
  if config.var('NAMESPACE_PREFIX'):
    args.append("--namespace_prefix=%s" % config.var('NAMESPACE_PREFIX'))
  # end if

  # GFS arguments:
  args = args + get_gfs_args(config)
  if config.var('GFS_USER'):
    args.append('--gfs_user=%s' % config.var('GFS_USER'))

  if config.var('ENABLE_CRAWLMANAGER_REMOVEDOC'):
    args.append('--removedoc_rtupdate_prefix=%s' %
                config.var('WORKSCHEDULER_REMOVEDOC_LOG_PREFIX'))
    args.append('--removedoc_uhpupdate_prefix=%s' %
                config.var('WORKSCHEDULER_REMOVEDOC_UHP_LOG_PREFIX'))
    args.append('--removedoc_trackerupdate_prefix=%s' %
                config.var('WORKSCHEDULER_REMOVEDOC_TRACKER_LOG_PREFIX'))
    args.append('--num_tracker_shards=%d' %
                config.GetNumShards('tracker_gatherer'))
    args.append('--removedoc_runinterval=%d' %
                config.var('WORKSCHEDULER_REMOVEDOC_RUNINTERVAL'))
    args.append('--removedoc_umupdate_prefix=%s' %
                config.var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX'))
    args.append('--num_um_shards=%d ' %
                config.GetNumShards('urlmanager'))
    if config.var('URLTRACKER_SHARD_BY_URL') == 1:
        args.append('--urltracker_shard_by_url')
  return args  # end args_crawlmanager()

# Babysitter thinks that crawlmanager is urlmanager, so use args_crawlmanager()
# to make restart_urlmanager()
def restart_urlmanager(config, host, port):
  if config.var('ENTERPRISE_CRAWL'):
    # use enterprise specific crawling components. for now this
    # does not work on clusters.
    args = args_crawlmanager(config, port)
  else:
    # 0 -> use crawl id if is specified
    args = args_urlmanager(config, host, port, 0)

    # We need to run as root so mlockall() works
  return restart_wrapper("urlmanager", config, host, port, args, run_as="root")

servertype.RegisterRestartFunction('urlmanager', restart_urlmanager)

#-----------------------------------------------------------------------------
# COOKIESERVER
#-----------------------------------------------------------------------------

def args_cookieserver(config, host, port):
  args = [
    "--port=%d" % (port),
    "--ares_dns_servers=%s" % (config.var('BOT_DNS_SERVERS')),
    "--dns_cache_size=%d" % (config.var('BOT_DNS_CACHE_SIZE')),
    "--ares_num_tries=%d" % (config.var('BOT_DNS_RETRIES')),
    "--dns_timeout=%d" % (config.var('BOT_DNS_TIMEOUT')),
    "--dns_expiration=%d" % (config.var('BOT_DNS_EXPIRATION')),
    "--httpbotfetcher_follow_off_domain_redirects",
    ]
  if(config.var('COOKIE_RULES')):
    args.append("--cookierulespath=%s" %
                config.var('COOKIE_RULES'))

  if (config.var('IGNORE_CANONICAL_TARGET_IN_REDIRECT_FOR_COOKIESERVER')):
    args.append("--ignore_canonical_target_in_redirect")

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('SSO_PATTERN_CONFIG'):
    args.append("--sso_pattern_config=%s" % config.var('SSO_PATTERN_CONFIG'))

  if config.var('COOKIESERVER_HANDLE_301'):
    args.append("--handle_301=true")

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('DO_SSO_LOGGING'):
    args.append("--do_sso_logging=true")
    args.append("--sso_log_file=%s" % config.var('SSO_LOG_FILE'))

  if config.var('COOKIESERVER_VERBOSITY'):
    args.append("--v=%d" % (config.var('COOKIESERVER_VERBOSITY')))
  if config.var('COOKIESERVER_HTTP_TIMEOUT'):
    args.append("--httptimeout=%d" % (config.var('COOKIESERVER_HTTP_TIMEOUT')))
  if config.var('CRAWL_HTTPS'):
    args.append("--crawlhttps")
    if config.var('BOT_SSL'):
      if config.var('BOT_SSL_CIPHER_LIST'):
        args.append('--ssl_cipher_list=%s' %
                    config.var('BOT_SSL_CIPHER_LIST'))
      if config.var('BOT_CA_CRL_DIR'):
        args.append('--CA_CRL_dir=%s' %
                    config.var('BOT_CA_CRL_DIR'))
      if config.var('BOT_SSL_CERTIFICATE_DIR'):
        args.append('--use_certificate_dir=%s' %
                    config.var('BOT_SSL_CERTIFICATE_DIR'))
      args.append('--use_certificate_file=%s' %
                  config.var('BOT_SSL_CERTIFICATE_FILE'))
      args.append('--private_rsa_key_file=%s' %
                  config.var('BOT_SSL_KEY_FILE'))
      args.append('--noenable_CRL')

  if config.var('BOT_PROXY'):
    args.append("--proxy=%s" % (config.var('BOT_PROXY')))
  if config.var('COOKIESERVER_IGNORE_ROBOTS'):
    args.append("--nouse_robots_files")
  if config.var('PROXY_CONFIG'):
    args.append("--proxy_config=%s" % (config.var('PROXY_CONFIG')))
  if config.var('EXTRA_HTTP_HDRS_CONFIG'):
    args.append("--urlspecific_http_hdrs_config=%s" %
                (config.var('EXTRA_HTTP_HDRS_CONFIG')))
  if config.var('CRAWL_SECURE_CONTENT'):
    args.append("--crawl_secure")
  if config.var('CRAWL_USERPASSWD_CONFIG'):
    args.append("--crawl_userpasswd_config=%s" % (
      config.var('CRAWL_USERPASSWD_CONFIG')))
  if config.var('USER_AGENTS_TO_OBEY_IN_ROBOTS'):
    args.append("--useragent=%s" % config.var('USER_AGENTS_TO_OBEY_IN_ROBOTS'))
  if config.var('USER_AGENT_TO_SEND'):
    args.append("--useragent_to_send=%s" % config.var('USER_AGENT_TO_SEND'))
  if config.var('USER_AGENT_COMMENT'):
    args.append("--useragent_comment=%s" % config.var('USER_AGENT_COMMENT'))
  if config.var('USER_AGENT_EMAIL'):
    args.append("--useragent_email=%s" % config.var('USER_AGENT_EMAIL'))
  if config.var('BOT_ADDITIONAL_REQUEST_HDRS'):
    args.append("--extra_http_hdrs=%s" % config.var('BOT_ADDITIONAL_REQUEST_HDRS'))
  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))
  if config.var('BOT_EXCLUDE_PRIVATE_NETWORKS'):
    args.append("--exclude_private_networks")
  else:
    args.append("--noexclude_private_networks")

  # TODO: remove this when the dependency between the cookieserver and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  return args

def restart_cookieserver(config, host, port):
  args = args_cookieserver(config, host, port)
  return restart_wrapper("cookieserver", config, host, port, args)

servertype.RegisterRestartFunction('cookieserver', restart_cookieserver)

#-------------------------------------------------------------------------------
# BOT
#-------------------------------------------------------------------------------

def GetMimeTypesFromFileTypes(filetypes, mimetype_dict):
  # use a dictionary here to avoid adding duplicates to the filter string
  mimetypes = {}

  for filetype in filetypes:
    for mimetype in mimetype_dict[filetype]:
      mimetypes[mimetype] = 1
  return mimetypes.keys()


def args_bot(config, host, port):

  urlservers = serverflags.MakeHostPortsArg(
    config.GetServerHostPorts('urlserver')
  )

  cookieserver = serverflags.MakeHostPortsArg(
    config.GetServerHostPorts('cookieserver')
  )

  # A quick func to convert hostname to ip adress in a tuple.
  # bot uses admin-controlled dns servers, so lets resolve the
  # host right here and use ip address.
  def by_ip(tup):
    return socket.gethostbyname(tup[0]), tup[1]

  fsgw_hostports = config.GetServerHostPorts('fsgw');
  # Choose the first host & port since bot does it that way
  fsgw = serverflags.MakeHostPortsArg([by_ip(fsgw_hostports[0])]);

  args = [
    "--datadir=" + config.var('DATADIR'),
    "--port=%d" % (port),
    "--commandflagsdumpfile=bot_cmdflg",
    "--urlserver=" + urlservers,
    "--maxconnections=%d" % (config.var('BOT_MAX_CONNECTIONS')),
    "--contentfilter_connections=%d" % (config.var('CONTENTFILTER_CONNECTIONS')),
    "--maxfilterqueue=%d" % (config.var('BOT_FILTER_QUEUE')),
    "--maxfilterbackoff=%d" % (config.var('BOT_FILTER_MAXBACKOFF')),
    "--max_urls_per_request=%d" % (config.var('BOT_MAX_URLS_PER_REQUEST')),
    "--report_interval=10",
    "--dns_cache_size=%d" % (config.var('BOT_DNS_CACHE_SIZE')),
    "--ares_num_tries=%d" % (config.var('BOT_DNS_RETRIES')),
    "--dns_timeout=%d" % (config.var('BOT_DNS_TIMEOUT')),
    "--dns_expiration=%d" % (config.var('BOT_DNS_EXPIRATION')),
    "--docserver_timeout=%d" % config.var('DOCSERVER_TIMEOUT'),
    "--httpbotfetcher_follow_off_domain_redirects",
    "--use_ares=false",
  ]

  # on the virtual line, we need to tell the bot to ignore
  # low memory and crawl anyway
  ent_cfg_type = config.var('ENT_CONFIG_TYPE')
  if ent_cfg_type in ('LITE', 'FULL'):
    args.append("--ignore_lowmem")

  # construct a list of the filetypes we want to handle
  filetypes = config.var_copy('BOT_FILE_TYPES_TO_ACCEPT')
  if config.var('CRAWL_IMAGE'):
    filetypes.append('IMAGE')

  contentfilter_mimetypes = (
    ["text/plain", "google/empty", "google/error", "google/other"] +
    GetMimeTypesFromFileTypes(filetypes, GoogleLocalMime) +
    GetMimeTypesFromFileTypes(filetypes, AcceptMime)
    )
  accept_mimetypes = GetMimeTypesFromFileTypes(filetypes, AcceptMime)


  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_protocolbuffers")
  if config.var('LOG_OUTGOING_PROTOCOLBUFFERS'):
    args.append("--log_outgoing_protocolbuffers")

  if config.var('BOT_TESTURLS'):
    args.append("--testurl=%s" % (config.var('BOT_TESTURLS')))
    if config.var('BOT_WEAK_URLTEST'):
      args.append("--urltest_failure_fraction=0.9")

  if config.var('BOT_DNSRESOLUTION'):
     args.append("--bot_dnsresolution=%s" % config.var('BOT_DNSRESOLUTION'))

  if config.var('BOT_URLSERVER_REQUEST_INTERVAL'):
    args.append("--urlserver_request_interval=%d" % (
      config.var('BOT_URLSERVER_REQUEST_INTERVAL')))

  if config.var('BOT_FATAL_TIMEOUT'):
    args.append("--fatal_timeout=%d" % config.var('BOT_FATAL_TIMEOUT'))
  if config.var('COOKIE_RULES'):
    args.append("--cookierulespath=%s" % config.var('COOKIE_RULES'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('SSO_PATTERN_CONFIG'):
    args.append("--sso_pattern_config=%s" % config.var('SSO_PATTERN_CONFIG'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('DO_SSO_LOGGING'):
    args.append("--do_sso_logging=true")
    args.append("--sso_log_file=%s" % config.var('SSO_LOG_FILE'))

  if fsgw != "":
    filesystem_proxy_url = "http://%s/getFile" % fsgw
    args.append("--filesystem_proxy_url=%s" % filesystem_proxy_url)

  if cookieserver != "":
    args.append("--cookieserver=%s" % cookieserver)
  if config.var('ABSOLUTE_MAX_MEMORY'):
    args.append("--absolute_max_memory=%d" % config.var('ABSOLUTE_MAX_MEMORY'))
  if config.var('ABSOLUTE_GOAL_MEMORY'):
    args.append("--absolute_goal_memory=%d" % config.var('ABSOLUTE_GOAL_MEMORY'))

  if config.GetNumShards("dnscache") > 0:
    hostports = serverflags.MakeHostPortsArg(
      config.GetServerHostPorts('dnscache')
    )
    args.append("--cacheservers=%s" % hostports)
  if config.var('DNSCACHE_MACHINES_PER_SHARD') != None:
    args.append("--cachebackups=%d" % (config.var('DNSCACHE_MACHINES_PER_SHARD')))
  if config.var('BOT_HTTP_TIMEOUT'):
    args.append("--httptimeout=%d" % (config.var('BOT_HTTP_TIMEOUT')))
  if ( config.var('BOT_MAXCONNECTION_THROTTLE_FACTOR')
       and not config.var('MAX_BPS') ):
    args.append("--maxconnection_throttle_factor=%f" % (
      config.var('BOT_MAXCONNECTION_THROTTLE_FACTOR')))
  if config.var('DISALLOW_IS_NOINDEX'):
    args.append('--disallow_is_noindex')
  if config.var('CRAWL_HTML'):
    contentfilter_mimetypes.append("text/html")
  if config.var('CRAWL_XML'):
    contentfilter_mimetypes.append("text/xml")
    contentfilter_mimetypes.append("application/xml")
    contentfilter_mimetypes.append("application/atom+xml")
    contentfilter_mimetypes.append("application/rdf+xml")
    contentfilter_mimetypes.append("application/rss+xml")
    contentfilter_mimetypes.append("application/xhtml+xml")
  if config.var('BOT_MAXFILETYPE_DOWNLOAD'):
    args.append("--max_filetype_len=%d" % (config.var('BOT_MAXFILETYPE_DOWNLOAD')))
    # this assumes BOT_MAXFILETYPE_DOWNLOAD is the biggest document
    # we are willing to pick up. This is ok for forseeeable future.
    # TODO: enforce this constraint.
    args.append("--max_data_accepted_by_httpclientconn=%d" % \
                config.var('BOT_MAXFILETYPE_DOWNLOAD'))
    args.append("--httpclientconn_max_uncompress_bytes_per_response=%d" % \
                config.var('BOT_MAXFILETYPE_DOWNLOAD'))

  # TODO: All bots built from the main branch after Jan. 13 2003
  # should enable this parameter.
  if config.var('BOT_ALLOWBOGUSCONTENTLENGTH'):
    args.append("--allowboguscontentlength")
  if config.var('CRAWL_WML'):
    contentfilter_mimetypes.append("text/vnd.wap.wml")
    args.append("--crawlwml")
  if config.var('CRAWL_HDML'):
    contentfilter_mimetypes.append("text/x-hdml")
    args.append("--crawlhdml")
  if config.var('CRAWL_HTTPS'):
    args.append("--crawlhttps=true")
    # https accept mime type
    https_accept_mimetypes = ["text/html", "text/plain"] + accept_mimetypes
    args.append("--https_accept_mimetypes=" +
                string.join(https_accept_mimetypes, ","))
    if config.var('BOT_SSL'):
      if config.var('AUTHENTICATE_SERVER_CERT'):
        args.append('--require_server_auth')
        args.append('--enable_CRL_PEM')
        # This is hack to make minimal changes to google ssl library.
        # It needs a CA file when authenticating peer. So passing a gsa's
        # own cert as a dummy CA file.
        # Enterprise code will use a CA directory instead.
        args.append('--CA_certificate_file=%s' %
                    config.var('BOT_SSL_CERTIFICATE_FILE'))
      else:
        # cipher list provided is not equal to the default cipher list needed
        # for authenticating the server.
        if config.var('BOT_SSL_CIPHER_LIST'):
          args.append('--ssl_cipher_list=%s' %
                      config.var('BOT_SSL_CIPHER_LIST'))
      args.append('--noenable_CRL')
      if config.var('BOT_CA_CRL_DIR'):
        args.append('--CA_CRL_dir=%s' %
                    config.var('BOT_CA_CRL_DIR'))
      if config.var('BOT_SSL_CERTIFICATE_DIR'):
        args.append('--use_certificate_dir=%s' %
                    config.var('BOT_SSL_CERTIFICATE_DIR'))
      args.append('--use_certificate_file=%s' %
                  config.var('BOT_SSL_CERTIFICATE_FILE'))
      args.append('--private_rsa_key_file=%s' %
                  config.var('BOT_SSL_KEY_FILE'))

  if config.var('BOT_ACCEPT_GZIP'):
    args.append("--accept_gzip")

  filters = config.GetServerHostPorts("contentfilter")
  max_filters_num = config.var('BOT_MAX_CONTENTFILTERS_PER_BOT')  # shortcut

  # if there are many contentfilters, use only up to max_filters_num
  num_filters = len(filters)
  if num_filters > max_filters_num:
    # Round-robin assignments of contentfilters to bot.
    # "num_wraps" allow us to shift when we wrap around in assignments.
    # This way we won't have same set of backends for any two bots.
    all_bots = config.GetServerHostPorts("bot")
    bot_idx = all_bots.index((host, port))
    num_wraps = (bot_idx * max_filters_num) / num_filters
    start_idx = (bot_idx * max_filters_num + num_wraps) % num_filters
    newfilters = filters[start_idx : start_idx + max_filters_num]
    if len(newfilters) < max_filters_num:
      # too few at the end, wrap to beginning
      need = max_filters_num - len(newfilters)
      newfilters = newfilters + filters[:need]
    #endif
    assert len(newfilters) == max_filters_num
    filters = newfilters
  # endif

  filters_as_strings = map(lambda hp: "%s:%d" % (hp[0], hp[1]), filters)
  filterstring = ("--filters=" + string.join(contentfilter_mimetypes, ",") +
                  ":" + string.join(filters_as_strings, ","))
  args.append(filterstring)

  if config.var('BOT_PROXY'):
    args.append("--proxy=%s" % (config.var('BOT_PROXY')))
  if config.var('BOT_INIT_CONNECTIONS'):
    args.append("--init_connections=%d" % (config.var('BOT_INIT_CONNECTIONS')))
  if config.var('MAX_BPS') != 50000000:
    args.append("--maxbps=%d" % (config.var('MAX_BPS')))
  if config.var('IN_CRAWL_SWITCH_IP'):
    args.append("--in_switchip=%s" % (config.var('IN_CRAWL_SWITCH_IP')))
  if config.var('IN_CRAWL_SWITCH_PORT'):
    args.append("--in_switchport=%d" % (config.var('IN_CRAWL_SWITCH_PORT')))
  if config.var('IN_CRAWL_SWITCH_OID'):
    args.append("--in_switch_oid=%s" % (config.var('IN_CRAWL_SWITCH_OID')))
  if config.var('OUT_CRAWL_SWITCH_IP'):
    args.append("--out_switchip=%s" % (config.var('OUT_CRAWL_SWITCH_IP')))
  if config.var('OUT_CRAWL_SWITCH_PORT'):
    args.append("--out_switchport=%d" % (config.var('OUT_CRAWL_SWITCH_PORT')))
  if config.var('OUT_CRAWL_SWITCH_OID'):
    args.append("--out_switch_oid=%s" % (config.var('OUT_CRAWL_SWITCH_OID')))
  if config.var('BOT_IGNORE_ROBOTS'):
    args.append("--nouse_robots_files")

  if config.var('BOT_EXCLUDE_PRIVATE_NETWORKS'):
    args.append("--exclude_private_networks=true")
  else:
    args.append("--exclude_private_networks=false")

  if config.var('BOT_INCLUDE_ONLY_PRIVATE_NETWORKS'):
    args.append("--include_only_private_networks=true")

  if config.var('BOT_VALID_IP_ADDRESSES'):
    args.append("--valid_ip_addresses=%s" %
                (config.var('BOT_VALID_IP_ADDRESSES')))

  if config.var('BOT_VALID_PORT'):
    args.append("--valid_port=%d" %
                (config.var('BOT_VALID_PORT')))

  if config.var('PROXY_CONFIG'):
    args.append("--proxy_config=%s" % (config.var('PROXY_CONFIG')))
  if config.var('EXTRA_HTTP_HDRS_CONFIG'):
    args.append("--urlspecific_http_hdrs_config=%s" %
                (config.var('EXTRA_HTTP_HDRS_CONFIG')))

  if config.var('CRAWL_SECURE_CONTENT'):
    args.append("--crawl_secure")
  if config.var('CRAWL_USERPASSWD_CONFIG'):
    args.append("--crawl_userpasswd_config=%s" % (
      config.var('CRAWL_USERPASSWD_CONFIG')))

  if config.has_var('USER_AGENT'):
    # we check USER_AGENT differently as we check other variables (using
    # has_key()) because we want it to go away (It shouldnt exist)
    print "Error: Using USER_AGENT to set FLAGS_useragent_to_send is now deprecated."
    print "Please use USER_AGENTS_TO_OBEY_IN_ROBOTS to specify a list of comma separated useragent names that the crawlers follow, and use USER_AGENT_TO_SEND to specify a useragent name that we send out to the world."
    sys.exit(-1)

  if config.var('USER_AGENTS_TO_OBEY_IN_ROBOTS'):
    args.append("--useragent=%s" % config.var('USER_AGENTS_TO_OBEY_IN_ROBOTS'))

  if config.var('USER_AGENT_TO_SEND'):
    args.append("--useragent_to_send=%s" % config.var('USER_AGENT_TO_SEND'))

  if config.var('USER_AGENT_COMMENT'):
    args.append("--useragent_comment=%s" % config.var('USER_AGENT_COMMENT'))

  if config.var('USER_AGENT_EMAIL'):
    args.append("--useragent_email=%s" % config.var('USER_AGENT_EMAIL'))

  if config.var('BOT_URLSERVER_BACKOFF'):
    args.append("--urlserverbackoff=%d" % (config.var('BOT_URLSERVER_BACKOFF')))

  if config.var('BOT_ADDITIONAL_REQUEST_HDRS'):
    args.append("--extra_http_hdrs=%s" % config.var('BOT_ADDITIONAL_REQUEST_HDRS'))

  # http accept mime types
  http_accept_mimetypes = ["text/html", "text/plain"] + accept_mimetypes
  args.append("--http_accept_mimetypes=" +
              string.join(http_accept_mimetypes, ","))

  if config.var('CRAWL_IMAGE'):
    # some images are very large. So increase the maxhttplen value
    args.append("--maxhttplen=5000000") # 5M
  elif config.var('BOT_MAXHTTPREQ_SIZE'):
    args.append("--maxhttplen=%d" % (config.var('BOT_MAXHTTPREQ_SIZE')))

  if config.var('BOT_EXPECTED_FILE_SIZE'):
    args.append("--expectedfilesize=%d" % (config.var('BOT_EXPECTED_FILE_SIZE')))

  if config.var('BOT_DNS_PAGES_EXPIRATION'):
    args.append("--dns_count_expiration=%d" % (config.var('BOT_DNS_PAGES_EXPIRATION')))
  if config.var('BOT_ROBOTS_PAGES_EXPIRATION'):
    args.append("--robots_count_expiration=%d" %
                (config.var('BOT_ROBOTS_PAGES_EXPIRATION')))

  if None != config.var('URL_REWRITE_ORIG2STAGING'):
    args.append( "--transparent_url_rewrites=%s" % (
      config.var('URL_REWRITE_ORIG2STAGING') ))
  if None != config.var('URL_REWRITE_STAGING2ORIG'):
    args.append( "--staging2originalservers=%s" % (
      config.var('URL_REWRITE_STAGING2ORIG')))
  if config.var('BYPASS_ROBOTS'):
    args.append("--bypassrobots_file=%s" % config.var('BYPASS_ROBOTS'))
  if config.var('DOCSERVER_SHARDING_METHOD'):
    args.append("--docserver_sharding_method=%s" %
                config.var('DOCSERVER_SHARDING_METHOD'))
  if config.var('REUSE_CRAWL'):
    srv_mngr = config.GetServerManager()
    set = srv_mngr.Set('bot')
    docservetype = 'doc'
    if config.var('BOT_IMS_TALK_TO_MIXSERVERS'):
      # we prefer talking to the mixservers
      docservetype = 'mixer'
    # end if

    docservers_and_ports = serverflags.MakeHostPortsArg(
                                       set.BackendHostPorts(docservetype))
    if (not docservers_and_ports):
      sys.exit("REUSE_CRAWL flag set but no doc servers specified")

    args.append("--docservers=%s" % docservers_and_ports)
    # how many connections to reuse-docserver
    args.append("--conn_per_backend=%d" % config.var('CONNS_PER_REUSE_DOCSERVER') )

  if config.var('BOT_RECOMPUTE_IMS'):
    args.append("--recompute_IMS=%d" % config.var('BOT_RECOMPUTE_IMS'))
  if config.var('IF_MODIFIED_SINCE'):
    # note: use urllib.quote() in case IF_MODIFIED_SINCE has spaces
    args.append("--if_modified_since=%s" % urllib.quote(config.var('IF_MODIFIED_SINCE')))
  if config.var('BOT_MAX_WEBSERVER_CLOCKSKEW'):
    args.append("--max_webserver_clockskew=%d" %
                config.var('BOT_MAX_WEBSERVER_CLOCKSKEW'))
  if config.var('URLS_REMOTE_FETCH_ONLY'):
    args.append("--urls_remote_fetch_only=" + config.var('URLS_REMOTE_FETCH_ONLY'))
  if config.var('URLS_LOCAL_FETCH_ONLY'):
    args.append("--urls_local_fetch_only=" + config.var('URLS_LOCAL_FETCH_ONLY'))
  if config.var('BOT_DONT_CRAWL_IMS_HOSTS_FASTER'):
    args.append("--nocrawl_ims_hosts_faster")
  if config.var('BOT_FRACTION_MAX_MEMORY'):
    args.append("--fraction_max_memory=%s" % config.var('BOT_FRACTION_MAX_MEMORY'))
  if config.var('BOT_FRACTION_GOAL_MEMORY'):
    args.append("--fraction_goal_memory=%s" % config.var('BOT_FRACTION_GOAL_MEMORY'))

  if config.var('DOMINO_OPTIMIZE'):
    args.append("--domino_optimize=true")

  if config.var('URLTRACKER_FILTER_FILE'):
    args.append("--urltracker_filter_file=%s" % config.var('URLTRACKER_FILTER_FILE'))

  if config.var('BOT_HANDLE_301'):
    args.append("--handle_301")

  if config.var('BOT_ROBOTS_EXPIRATION'):
    args.append("--robots_expiration=%d" % config.var('BOT_ROBOTS_EXPIRATION'))

  if config.var('BOT_CHECKPOINT_FILE_PREFIX'):
    checkpoint_name = '%s-%s-%s' % (config.var('BOT_CHECKPOINT_FILE_PREFIX'),
                                        host, port)
    args.append('--checkpoint_filename=%s' % checkpoint_name)
    if not config.var('CHECKSUM_CHECKPOINT_FILES'):
      args.append("--keep_checksum_for_checkpoints=false")
  # endif BOT_CHECKPOINT_FILE_PREFIX

  if config.var('BOT_TRACK_IMS_FOR_HOST'):
    args.append('--track_IMS_for_host=%s' % config.var('BOT_TRACK_IMS_FOR_HOST'))
  # endif BOT_TRACK_IMS_FOR_HOST

  if (config.var('UNREACHABLE_HOST_DELAY_IN_MS')):
    args.append('--unreachable_host_delay_in_ms=%d' %
                config.var('UNREACHABLE_HOST_DELAY_IN_MS'))

  # since we may have checkpoints.
  args = args + get_gfs_args(config)

  if config.var('BOT_GFS_CELL_ARGS'):
    args.append('--gfs_cell_args=%s' %
                config.var('BOT_GFS_CELL_ARGS'))

  if config.var('BOT_EXCLUDE_IPANDMASKS'):
    args.append('--exclude_ipandmasks=%s' %
                config.var('BOT_EXCLUDE_IPANDMASKS'))

  return args

def restart_bot(config, host, port):
  args = args_bot(config, host, port)
#  args.append("--v=2")
  return restart_wrapper("bot", config, host, port, args)

servertype.RegisterRestartFunction('bot', restart_bot)

#-------------------------------------------------------------------------------
# CONTENTFILTER
#-------------------------------------------------------------------------------
def get_global_link_machine_type(config):
  if config.var('NEED_GLOBAL_LINK'):
    return 'global_link'
  else:
    return 'base_indexer'

def contentfilter_log_info_arg(config, host, port):
  components = []
  error = 0
  # make sure we have at least one of the document processors
  if config.var('NEED_RTSERVER') and \
     config.GetNumShards('base_indexer') == 0 and \
     config.GetNumShards('daily_indexer') == 0 and \
     config.GetNumShards('rt_indexer') == 0 and \
     (config.var('CONTENTFILTER_DOCUMENT_LOG') == '' or \
      config.var('CONTENTFILTER_NUM_DOCUMENT_LOG_SHARDS') == 0):
     print("""At least one of base_indexer, daily_indexer
           and rt_indexer machines  must be specified or
           CONTENTFILTER_DOCUMENT_LOG and CONTENTFILTER_NUM_DOCUMENT_LOG_SHARDS
           must be specified""")
     error = 1
  if config.var('NEED_GLOBAL_LINK') and \
     config.GetNumShards('global_link') == 0:
    print("We must have at least one global_link server")
    error = 1
  if config.var('CONTENTFILTER_MIN_LCA_PAGERANK') != None and \
     config.GetNumShards('global_lca_link') == 0:
    print("We must have at least one global_lca_link server")
    error = 1
  if config.var('CONTENTFILTER_MIN_HOSTID2IP_PAGERANK') != None and \
     config.GetNumShards('global_hostid2ip') == 0:
    print("We must have at least one global_hostid2ip server")
    error = 1
  if config.var('CONTENTFILTER_MIN_RELATED_PAGERANK') != None and \
     config.var('NUM_RELATED_SHARDS') == None:
    print("NUM_RELATED_SHARDS must be set")
    error = 1
  if config.GetNumShards('urlmanager') == 0:
    print("We must have at least one urlmanager server")
    error = 1

  if (config.var('CONTENTFILTER_DOCUMENT_LOG') != '' and
      config.var('CONTENTFILTER_NUM_DOCUMENT_LOG_SHARDS') > 0):
    if config.GetNumShards('base_indexer') != 0 or \
       config.GetNumShards('daily_indexer') != 0 or \
       config.GetNumShards('rt_indexer') != 0:
      print """Cannot specify base/daily/rt_indexer with
               CONTENTFILTER_DOCUMENT_LOG"""
      error = 1
    else:
      # assume that it is the base_indexer
      components = components + \
                   ["base_indexer:%s@%d" %
                    (config.var('CONTENTFILTER_DOCUMENT_LOG'),
                     config.var('CONTENTFILTER_NUM_DOCUMENT_LOG_SHARDS'))]

  if error:
    sys.exit(1)

  def gen_log_config(config, machine_type, host, port):
    if machine_type == 'global_link':
      num_shards = config.GetNumShards(get_global_link_machine_type(config))
    elif machine_type == 'urlhistory_processor' and \
       config.var('RTINDEXER_AS_URLHISTORY_PROCESSOR'):
      num_shards = config.GetNumShards('base_indexer')
    elif machine_type == 'global_related':
      num_shards = config.var('NUM_RELATED_SHARDS')
    elif machine_type == 'archive':
      num_shards = config.GetNumShards('feeder')
    elif machine_type == 'rejected_urls' or machine_type == 'seen_hosts':
      if config.var('RTSERVER_LOGS').has_key(machine_type):
        num_shards = config.GetNumShards('urlmanager')
      else:
        num_shards = 0
    else:
      num_shards = config.GetNumShards(machine_type)
    #endif num_shards computataion
    rtserver_log = shardset_output_log_name(config, machine_type, host, port,
                                            num_shards)
    if rtserver_log:
      return [ rtserver_log ]
    else:
      return []
  #end gen_log_config
  if config.var('NEED_RTSERVER') :
    components = components + gen_log_config(config, 'base_indexer', host, port)
    components = components + gen_log_config(config, 'daily_indexer', host, port)
    components = components + gen_log_config(config, 'rt_indexer', host, port)
  if config.var('LOGS_REWRITER_TYPE'):
    components = components + gen_log_config(config, 'urlmanager_log_rewriter',
                                             host, port)
  else:
    components = components + gen_log_config(config, 'urlmanager', host, port)

  if config.var('CONTENTFILTER_GEN_GLOBAL_LINK_LOGS'):
    components = components + gen_log_config(config, 'global_link', host, port)
  if config.var('CONTENTFILTER_MIN_LCA_PAGERANK') != None:
    components = components + gen_log_config(config, 'global_lca_link', host, port)
  if config.var('CONTENTFILTER_MIN_HOSTID2IP_PAGERANK') != None:
    components = components + gen_log_config(config, 'global_hostid2ip', host, port)
  if config.var('CONTENTFILTER_MIN_RELATED_PAGERANK') != None:
    components = components + gen_log_config(config, 'global_related', host, port)
  if config.var('CONTENTFILTER_GEN_URLHISTORY_LOGS'):
    components = components + gen_log_config(config, 'urlhistory_processor',
                                             host, port)
  components = components + gen_log_config(config, 'clusterer', host, port)
  if config.var('CONTENTFILTER_GEN_URLTRACKER_LOGS'):
    components = components + gen_log_config(config, 'tracker_gatherer', host, port)
  if config.GetNumShards('feeder') > 0:
    components = components + gen_log_config(config, 'feeder', host, port)
  if config.var('CONTENTFILTER_GEN_ARCHIVE_LOGS'):
    components = components + gen_log_config(config, 'archive', host, port)
  components = components + gen_log_config(config, 'rejected_urls', host, port)
  components = components + gen_log_config(config, 'seen_hosts', host, port)

  # hack so contentfilter writes out crawl results to enterprise specific
  # crawlscheduler:
  # TODO: fix this for clusters.
  # currently we only use crawlscheduler's batch mode.
  #components = components + \
  #             ["crawlscheduler:/bigfile/enterprise_crawlscheduler@1"]

  return string.join(components, ",")

# This is a bit tricky.  For recovery purposes, it's easiest if we have all
# storeservers present in the servers array, even if we don't want them to
# be actively used.  To prevent new documents from being added to disabled
# storeservers, however, we only pass the enabled storeservers to the
# content filters.  We still start up the disabled storeservers and let
# the url managers know about them, however.
def get_active_storeservers(config):
  # we cache this because it is used so often
  ret = config.get_cache("get_active_storeservers", "cache")
  if ret: return ret

  # we filter by disabled storeserver ports
  disabled = config.var('DISABLED_STORESERVER_PORTS')
  hostports = filter(lambda x, d=disabled: x[1] not in d,
                     config.GetServerHostPorts('storeserver'))
  ret = serverflags.MakeHostPortsArg(hostports)

  # cache and return value
  config.put_cache("get_active_storeservers", "cache", ret)
  return ret


def args_contentfilter(config, host, port):
  args = [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--datadir=" + config.var('DATADIR'),
    "--port=%d" % (port),
    "--report_interval=120",    # Don't flush files too often
    "--commandflagsdumpfile=contentfilter_cmdflg",
    "--storeservers="+get_active_storeservers(config),
    "--max_buffered_documents=%d" % (config.var('CONTENTFILTER_MAXBUFDOCS')),
    "--max_buffered_bytes=%d" % (config.var('CONTENTFILTER_MAXBUFBYTES')),
    "--storeserver_connections=%d" % (config.var('CONTENTFILTER_STORESERVER_CONN')),
    "--badurls="  + config.var('BADURLS'),
    "--badurls_linkspam=" + config.var('BADURLS_LINKSPAM'),
    "--badurls_nopropagate=" + config.var('BADURLS_NOPROPAGATE'),
    "--badurls_demote=" + config.var('BADURLS_DEMOTE'),
    "--url_canonicalize_to_punycode",
    ]

  base_indexers = \
      serverflags.MakeHostPortsArg(config.GetServerHostPorts('base_indexer'))
  if config.var('CONTENTFILTER_USE_BASEINDEXER_FEEDBACK'):
    args.append("--ent_base_indexers=%s" % base_indexers)

  # Crawl xml as text/plain.
  # xml_parser and parse_xml_as_text_plain can't be both set.
  if config.var('CRAWL_XML'):
    args.append("--parse_xml_as_text_plain")

  if config.var('GOODURLS'):
    if config.var('GOODPROTS'):
      args.append("--goodurls=%s,%s" % (config.var('GOODURLS'), config.var('GOODPROTS')))
    else:
      args.append("--goodurls=" + config.var('GOODURLS'))
  else:
    if config.var('GOODPROTS'):
      args.append("--goodurls=" + config.var('GOODPROTS'))

  if config.var('LINK_DROPPER'):
    args.append("--link_dropper=" + config.var('LINK_DROPPER'))

  if config.var('CONTENTFILTER_DELETE_URL_ERROR'):
    args.append("--delete_error_documents")

  if config.var('CONTENTFILTER_LOGROLLBACKS'):
    args.append("--logrollbacks")

  if not config.var('REMOVE_HOMEPAGE_CONTENTDUPS'):
    args.append("--nocontentfps_for_homepages")

  if config.var('CHECKSUM_EVERYTHING'):
    args.append("--checksumeverything")

  if config.var('MAX_CONVERTER_DATA_SIZE'):
    args.append("--maxconverterdatasize=%d" % (config.var('MAX_CONVERTER_DATA_SIZE')))


  localized = IsServerLocalized(config, 'contentfilter')
  args = args + GetUrlCanonicalizationArgs(config, localized)

  args.append("--use_langid_langencdet=1")
  datadir = config.var('DATADIR')
  if localized:
    args.append("--cjk_config=%s/BasisTech/" % datadir)
    args.append("--langid_model_dir=%s/langid/" % datadir)
    # Keep compatible with googlebot/contentfilter
    args.append("--google_langid_config=/")
  else:
    args.append("--cjk_config=%s" % (config.var('CJKCONFIGDIR')))
    args.append("--langid_model_dir=%s" % config.var('LANGID_CONFIG'))
    # Keep compatible with googlebot/contentfilter
    args.append("--google_langid_config=/")
  #end if localize contentfilter
  args.append("--bt_version=%s" % config.var('BTVERSION'))
  args.append("--cjk_segmenter=%s" % config.var('CJKSEGMENTER'))

  if config.var('CONTENTFILTER_LANGUAGENAME_LIST'):
    args.append("--acceptable_languagenames=%s" % config.var('CONTENTFILTER_LANGUAGENAME_LIST'))

  if config.var('CONTENTFILTER_MEMORY_FRACTION'):
    args.append("--memory_fraction=%f" % (config.var('CONTENTFILTER_MEMORY_FRACTION')))

  if config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'):
    args.append("--external_converter_temp_dir=%s" %
                config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'))

  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_protocolbuffers")
  if config.var('LOG_OUTGOING_PROTOCOLBUFFERS'):
    args.append("--log_outgoing_protocolbuffers")

  # If BOT_FILE_TYPES_TO_ACCEPT has one of INSO_TYPES, INSO_LIB is enabled.
  do_inso = filter(lambda x, y = config.var('BOT_FILE_TYPES_TO_ACCEPT'):
                   x in y,
                   INSO_TYPES + ['EVERYTHING'])

  if do_inso:
    if config.var('GS_LOCATION'):
      args.append("--ps_converter_bin=%s" % (config.var('GS_LOCATION')))
    else:
      args.append("--ps_converter_bin=/usr/bin/gs")
    #endif
  #endif

  if do_inso:
    if localized:
      # INSO file types
      # in localized mode, inso template must not change location
      assert (config.var('INSO_TEMPLATE_BASENAME') == \
              "googlebot/inso_template.htm"), \
              'Localized mode must not set special INSO_TEMPLATE_BASNAME. ' + \
              'Expect only inso_template.htm'
    # endif localized

    # INSO filetypes
    args.append("--inso_lib=%s/third_party/Inso" % config.var('MAINDIR'))
    args.append("--misc_converter_bin=%s/bin/convert_to_html" %
                config.var('MAINDIR'))
    args.append("--misc_converter_cfg=%s/googlebot/inso.cfg" %
                (config.var('GOOGLEDATA')))
    args.append("--misc_converter_template=%s/%s" %
                (config.var('GOOGLEDATA'),
                 config.var('INSO_TEMPLATE_BASENAME')))
    args.append("--swf_converter_arg1=--logtostderr")

    # PDF
    args.append("--pdf_converter_bin=%s/bin/pdftohtml" %
                config.var('MAINDIR'))
    args.append("--pdf_langs_dir=%s/third_party/pdftohtml/langs" %
                config.var('MAINDIR'))

    # PS/PSGZ
    args.append("--ps_converter_script=%s/converter/gps2ascii.ps" % \
                (config.var('MAINDIR')))

    # SWF
    args.append("--swf_converter_bin=%s/bin/swfparsetxt" %
                (config.var('MAINDIR')))
    args.append("--swf_converter_arg1=--logtostderr")

  # endif do_inso

  # NOTE: new contentfilter flags should try to use BuildFlagArgs
  var_and_flags = [
    ('GZ_CONVERTER_BIN', "--gz_converter_bin"),
    ('GZ_CONVERTER_TIMEOUT', "--gz_converter_timeout"),
    ('GZ_CONVERTER_MAXSIZE', "--max_gz_text_size"),
    ]
  args = args + servertype.BuildFlagArgs(config, var_and_flags)

  # hostids -> pathids
  if config.var('GENERATE_PATH_HOST_IDS') != None:
    if config.var('GENERATE_PATH_HOST_IDS'):
      args.append("--generate_pathfp")
    else:
      args.append("--nogenerate_pathfp")

  if config.var('MAX_CROWDING_DEPTH'):
    args.append("--max_crowding_depth=%d" % config.var('MAX_CROWDING_DEPTH'))

  if config.var('BOT_MAXFILETYPE_DOWNLOAD'):
    args.append("--max_filetype_raw_len=%d" % config.var('BOT_MAXFILETYPE_DOWNLOAD'))

  if config.var('FILETYPE_PREFIX_TO_STORE'):
    args.append("--max_misc_text_size=%d" % (config.var('FILETYPE_PREFIX_TO_STORE')))
    args.append("--max_pdf_text_size=%d" % (config.var('FILETYPE_PREFIX_TO_STORE')))
    args.append("--max_swf_text_size=%d" % (config.var('FILETYPE_PREFIX_TO_STORE')))

  if config.var('CRAWL_IMAGE'):
    if localized:
      args.append("--image_thumbnail_bin=%s/magick-converter" % datadir)
    else:
      args.append("--image_thumbnail_bin=%s/bin/magick-converter" %
                  (config.var('MAINDIR')))

    if config.var('IMAGE_CONVERT_PARAMS'):
      args.append("--image_convert_params=%s" %
                  (config.var('IMAGE_CONVERT_PARAMS')))

  if config.var('URL_DISABLE_INFINITE_SPACE_CHECK'):
    args.append("--disable_infinitespace_check")

  # NOTE: new contentfilter flags should try to use BuildFlagArgs
  #       to simplify. Args are appended onto this list and processed at
  #       the end by BuildFlagArgs
  var_and_flags = [
    ('CHINESE_NAME_HACK', '--chinesenamefix'),
    ('CONTENTFILTER_STORE_PERMANENT_REDIRECTS', '--store_perm_redirects'),
    ('CONTENTFILTER_USE_C_PARSER', '--use_c_parser'),
    ('CONTENTFILTER_IGNORE_SECOND_TITLE', '--ignore_second_title'),
    ('BLOG_MODE', '--blog_mode'),
    ('CONTENTFILTER_ENABLE_XML_PARSER', '--xml_parser'),
    # add more pairs after here
    ]

  # get the shardinfo and backends objects from the config
  srv_mngr = config.GetServerManager()
  set = srv_mngr.Set('contentfilter')
  (shardinfo, backends) = set.BackendInfo(use_versions = 0)

  # make sure only one kind of dupserver is in use
  use_rtdupserver = shardinfo.HasShard('rtdupserver:0', None) # no segment
  assert not (use_rtdupserver and \
              config.var('USE_DUPSERVERS') and \
              config.var('USE_DUPSERVERS') >= 1), \
              "do not set USE_DUPSERVERS when rtdupserver is configured"

  if use_rtdupserver or config.var('USE_DUPSERVERS'):
    # dupserver (of either type) enabled ...

    # first, set arguments that apply to both dupserver and rtdupserver ...
    var_and_flags = var_and_flags + [
      ('CONTENTFILTER_DUPSERVER_TIMEOUT',      '--dupserver_timeout'),
      ('CONTENTFILTER_MAX_DUPSERVER_DELAY',    '--max_dupserver_delay'),
      ('CONTENTFILTER_CANONICALIZE_HOMEPAGES', '--canonicalize_homepages'),
      ('CONTENTFILTER_KEEP_NONCANONICAL_HOMEPAGE',
       '--keep_noncanonical_homepage')
      ]

    if use_rtdupserver :  # RT dupserver
      # In RT-mode, contentdup needs to be done here also
      # so default => drop dups
      var_and_flags = var_and_flags + [
        ('CONTENTFILTER_MAX_DUPSERVER_HTTP_QUEUE_SIZE',
         '--max_dupserver_http_queue_size'),
        ('CONTENTFILTER_DROP_LINKS_FROM_DUPS', '--drop_dup_outlinks'),
        ('CONTENTFILTER_DROP_DUP_DOCS',        '--drop_dup_pages'),
        ('CONTENTFILTER_REQUEST_OUTGOING_LINK_DUP_INFO',
         '--request_outgoing_link_dup_info'),
        ('DUPSERVER_NUM_TIMEOUT_RETRIES',  '--dupserver_num_timeout_retries')
        ]
    # end if use_rtdupserver
  # end of dupserver enabled

  var_and_flags = var_and_flags + [
    ('CONTENTFILTER_KEEP_ROBOTS_PAGE', '--keep_robots_page'),
    ('CONTENTFILTER_KEEP_UNCRAWLED_PAGE', '--keep_uncrawled_page')
    ]

  # TODO: Change the rest to use var_and_flags

  # Disable these google.com URL rewriters
  args.append('use_cvs_rewrites=false')
  args.append('use_yahoo_groups_rewriter=false')
  args.append('domino_rewrites=false')

  if config.var('PAGERANKER_USE_WTD_LINKS'):
    args.append("--use_wtd_links")
  if config.var('RAW_URL_REWRITE_RULES_BASENAME'):
    args.append("--url_rewrites=%s" % (
      config.var('RAW_URL_REWRITE_RULES_BASENAME')))
  if config.var('DISABLE_URL_NORMALIZATION'):
    args.append("--nonormalize_urls")
  if config.var('REWRITE_NONQUALIFIED_HOSTS'):
    args.append("--rewrite_nonqualified_hostnames")
  if config.var('ENABLE_NONCLICKABLE_LINKS'):
    args.append("--enable_nonclickable_links")

  if config.var('URLTRACKER_FILTER_FILE'):
    args.append("--urltracker_filter_file=%s" % config.var('URLTRACKER_FILTER_FILE'))

  if config.var('URLTRACKER_SHARD_BY_URL') == 1:
    args.append('--urltracker_shard_by_url')

  if config.var('EXTERNAL_CONVERTER_STARTUP_TIMEOUT'):
    args.append("--external_converter_startup_timeout=%d" % (
      config.var('EXTERNAL_CONVERTER_STARTUP_TIMEOUT')))

  if config.var('URLLOC_USE_GEO_LOCTIONS'):
    args.append("--geolib_data_path=%s/gws/" % config.var('GOOGLEDATA'))

  if config.var('RTSERVER_LOGS'):
    # generate the log info argument - do necessary checks
    log_info_arg = contentfilter_log_info_arg(config, host, port)
    args.append("--log_info=%s" % log_info_arg)
    if config.var('LOGS_REWRITER_TYPE') and \
       config.var('LOGS_REWRITER_TYPE') == "rewrite_rules":
      args.append('--urlmanager_logs_shard_by_urlfp=false')
    # add rfserver bank if specified
    args = args + servertype.GetRfserverBankArgs(config)

    args = args + get_gfs_args(config)
    if config.var('GFS_ALIASES'):
      args.append("--have_gfs")

      if config.var('GFS_USER'):
        args.append('--gfs_user=%s' % config.var('GFS_USER'))

    else:
      args.append("--have_gfs=false")
      args.append("--shard=%d" % servertype.GetPortShard(port))
    # endif GFS_ALIASES


    # ensure that only one type of category server is in use
    use_categorymapserver = shardinfo.HasShard('categorymapserver:0',
                                               None) # no segment
    assert not ((config.GetNumShards('categoryserver') > 0) and \
                use_categorymapserver), \
                "configure EITHER categoryserver OR categorymapserver"

    # add category servers if specified. category servers are only applicable
    # to realtime crawl (RTSERVER_LOGS is present)
    if use_categorymapserver:
      args.append("--use_categorymap_server")
    elif config.GetNumShards('categoryserver') > 0:
      host_ports = []
      for cat_host in config.GetServerHosts('categoryserver'):
        host_ports.append("%s:%d" % (cat_host, config.var('CATEGORYSERVER_REQUEST_PORT')))
      args.append("--categoryservers=%s" % string.join(host_ports, ','))
      var_and_flags.append(('CONTENTFILTER_CATEGORYSERVER_CONNECTIONS',
                            '--categoryserver_connections'))

    # add docid servers if specified. docid servers are only applicable
    # to realtime crawl (RTSERVER_LOGS is present) for urlfp->docid translation
    if config.GetNumShards('docidserver') > 0:
      servers = serverflags.MakeHostPortsArg(config.GetServerHostPorts('docidserver'))
      args.append("--docidservers=%s" % servers)

    if config.var('CONTENTFILTER_GEN_URLTRACKER_LOGS'):
      args.append("--url_tracker_sampling=%d" %
                  config.var('URLTRACKER_TRACK_EVERY'))
  # end if RTSERVER_LOGS

  replace_old_anchors = 1
  if (config.var('CONTENTFILTER_RTUPDATE_REPLACE_OLD_ANCHORS') == 0 or
     config.var('URLMANAGER_ISSUE_ANCHOR_REQUESTS')):
    replace_old_anchors = 0
  # end if
  if replace_old_anchors:
    args.append("--rtupdate_replace_old_anchors")
  else:
    args.append("--nortupdate_replace_old_anchors")

  if config.var('NEWS_CRAWL'):
    args.append("--news_mode")
    args.append("--news_stopwords=%s" % config.var('NEWS_STOPWORDS'))
    args.append("--newshub_file=%s" % config.var('NEWS_SOURCE_FILE'))
    if config.var('NEWS_ALLOW_TITLE_FAIL'):
      args.append("--allow_title_fail")

  if config.var('EPOCH_SIZE_IN_SECS') != None: # 0 is valid value
    args.append("--epoch_size_in_secs=%s" % config.var('EPOCH_SIZE_IN_SECS'))

  if (config.var('CONTENTFILTER_AUTO_ADD_HEARTBEAT_TO_LOGS_INTERVAL') != None):
    args.append("--auto_add_heartbeat_to_logs_interval=%d" %
                config.var('CONTENTFILTER_AUTO_ADD_HEARTBEAT_TO_LOGS_INTERVAL'))

  if config.var('CONTENTFILTER_FLUSHLOG_MAXDOCS_PER_INDEXER'):
    args.append("--flushlogs_max_documents_per_indexer=%d" %
                config.var('CONTENTFILTER_FLUSHLOG_MAXDOCS_PER_INDEXER'))

  if config.var('CONTENTFILTER_FLUSHLOG_INTERVAL_SECS'):
    args.append("--flushlogs_interval_secs=%d" %
                config.var('CONTENTFILTER_FLUSHLOG_INTERVAL_SECS'))

  # If we are using the urlmanager_log_rewriter in rewrite_rules mode
  # we need to compute content SimHash values for crawled documents.
  if config.var('LOGS_REWRITER_TYPE') and \
     config.var('LOGS_REWRITER_TYPE') == "rewrite_rules":
    args.append("--compute_simhash")

  if config.var('CONTENTFILTER_DUPCHECKS_OPTIONAL') == 1:
    args.append("--dupcheck_optional=true")

  if config.var('CONTENTFILTER_NO_DUPCHECK_PATTERNS'):
    args.append("--no_dupcheck_patterns=%s" % config.var('CONTENTFILTER_NO_DUPCHECK_PATTERNS'))

  if config.var('CONTENTFILTER_NO_DUPCHECK_FILE_TYPES'):
    mime_types = GetMimeTypesFromFileTypes(
      config.var('CONTENTFILTER_NO_DUPCHECK_FILE_TYPES'), GoogleLocalMime)
    args.append("--no_dupcheck_content_types=%s" % string.join(mime_types, ","))

  if config.var('ARCHIVE_URLS'):
    args.append("--archiveurls=%s" % config.var('ARCHIVE_URLS'))

  if config.var('RT_EPOCH') != None:
    args.append("--archive_epoch=%d" % config.var('RT_EPOCH'))

  if config.var('ARCHIVE_FEED'):
    args.append("--archive_feed")

  if config.var('CONTENTFILTER_MIN_LCA_PAGERANK') != None:
    args.append("--min_lca_pagerank=%d" %
                config.var('CONTENTFILTER_MIN_LCA_PAGERANK'))
  if config.var('CONTENTFILTER_MIN_HOSTID2IP_PAGERANK') != None:
    args.append("--min_hostid2ip_pagerank=%d" %
                config.var('CONTENTFILTER_MIN_HOSTID2IP_PAGERANK'))
  if config.var('CONTENTFILTER_MIN_RELATED_PAGERANK') != None:
    args.append("--min_related_pagerank=%d" %
                config.var('CONTENTFILTER_MIN_RELATED_PAGERANK'))

  if config.var('CONTENTFILTER_CHECKPOINT_FILE_PREFIX'):
    checkpoint_name = '%s-%s-%s' % (
      config.var('CONTENTFILTER_CHECKPOINT_FILE_PREFIX'), host, port)
    args.append('--checkpoint_filename=%s' % checkpoint_name)
    if not config.var('CHECKSUM_CHECKPOINT_FILES'):
      args.append("--keep_checksum_for_checkpoints=false")
  # endif CONTENTFILTER_CHECKPOINT_FILE_PREFIX

  # Build flags from arguments accumulated in var_and_flags
  args = args + servertype.BuildFlagArgs(config, var_and_flags)

  # Finally collect all server_flags info and append those flags
  if backends.HasBackEnds():
    args.append("--backends=%s" % backends.AsString())
    args.append("--shardinfo=%s" % shardinfo.AsString())

  if config.var('CONTENTFILTER_PDF_CONVERT_TIMEOUT'):
    args.append("--pdf_convert_timeout=%d"
                 % config.var("CONTENTFILTER_PDF_CONVERT_TIMEOUT"))

  if config.var('CONTENTFILTER_PS_CONVERT_TIMEOUT'):
    args.append("--ps_convert_timeout=%d"
                 % config.var("CONTENTFILTER_PS_CONVERT_TIMEOUT"))

  if config.var('CONTENTFILTER_MISC_CONVERT_TIMEOUT'):
    args.append("--misc_convert_timeout=%d"
                 % config.var("CONTENTFILTER_MISC_CONVERT_TIMEOUT"))

  if config.var('CONTENTFILTER_SET_DOC_CREATIONTIME'):
    args.append("--set_doc_creationtime")

  if config.var('ENTERPRISE'):
    args.append("--googletags=true")

  # For enterprise, retain multiple anchors connecting the same pair of docs
  if config.var('ENTERPRISE'):
    args.append("--retain_all_links=true")

  return args

def kill_contentfilter(port, delay, signal):
  """ Blow away any convert_to_html procesess, as well as regular kills"""
  mtype = servertype.GetPortType(port)

  # Locate binaries to kill.
  kill_bins = servertype.GetBinaryFiles(mtype, expand_aliases = 0)

  # we got our binary list. Add a complete kill command for *each* of them
  cmd = []
  for binname in kill_bins:
    cmd.append(servertype.GetKillSigOnPortDelay(binname,
                                                port,
                                                delay, signal))

  # Above is regular GetKillCmd code, now add convert_to_html
  cmd.append('killall -9 -g convert_to_html')
  return string.join(cmd, '')

def restart_contentfilter(config, host, port):

  args = args_contentfilter(config, host, port)
  return restart_wrapper("contentfilter", config, host, port, args)

servertype.RegisterRestartFunction('contentfilter', restart_contentfilter,
                                   kill_function=kill_contentfilter)

#-------------------------------------------------------------------------------
# TRACKER_GATHERER
#-------------------------------------------------------------------------------

def args_tracker_gatherer(config, port):
  num_shards = config.GetNumShards('tracker_gatherer')
  shard_num = servertype.GetPortShard(port)

  # we MUST be sharded the same way as our servers
  assert( num_shards == config.GetNumShards('urltracker_server') )

  args = [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--datadir="                + config.var('DATADIR'),
    "--port=%d"                 % (port),
    "--shard_num=%d"            % (shard_num),
    "--num_shards=%d"           % (num_shards),
    "--namespace_prefix=%s"     % (config.var('NAMESPACE_PREFIX')),
    "--urltracker_directory=%s" % (config.var('URLTRACKER_DIRECTORY')),
    "--goodurls=%s"             % (config.var('GOODURLS')),
    "--badurls=%s"              % (config.var('BADURLS')),
    ]

  if config.var('URLTRACKER_SHARD_BY_URL') == 1:
    args.append('--urltracker_shard_by_url')

  if config.var('URLTRACKER_MAX_MERGE_INDEX_BYTES'):
    args.append("--max_merge_index_bytes=%d" % (config.var('URLTRACKER_MAX_MERGE_INDEX_BYTES')))

  args = args + get_gfs_args(config)
  if config.var('GFS_ALIASES'): args.append('--have_gfs')

  #TODO: clean this up to use input_log_names()
  input_log_files = [ config.var('RTSERVER_LOGS')['tracker_gatherer'] ]
  # For feeder and feeder_doc_deleter, must have seperate logs even for GFS
  if config.var('RTLOG_FEEDER_SUFFIX'):
    input_log_files.append("%s%s" % (config.var('RTSERVER_LOGS')['tracker_gatherer'],
                                     config.var('RTLOG_FEEDER_SUFFIX')))
  if config.var('RTLOG_FEED_DOC_DELETER_SUFFIX'):
    input_log_files.append("%s%s" % (config.var('RTSERVER_LOGS')['tracker_gatherer'],
                                     config.var('RTLOG_FEED_DOC_DELETER_SUFFIX')))
  if not config.var('GFS_ALIASES'):
    # in GFS, we do not need a special remove doc tracker log file,
    # since the remove doc ripper can write to the main tracker input log
    # file, as more than one process can write to the same file.
    input_log_files.append(config.var('WORKSCHEDULER_REMOVEDOC_TRACKER_LOG_PREFIX'))

  args.append("--urltracker_log_base=%s" % string.join(input_log_files, ","))


  if config.var('ENTERPRISE_COLLECTIONS_DIR'):
    args.append("--collections_directory=%s" %
                config.var('ENTERPRISE_COLLECTIONS_DIR'))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    args.append("--keep_checksum_for_checkpoints=false")

  # TODO: remove this when the dependency between the trackergatherer
  # and chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  # TODO(tianyu): temporary workaround for the mmap memory issue
  args.append('--mmap_urls=false')
  args.append('--mmap_sums=false')

  return args

def restart_tracker_gatherer(config, host, port):
  args = args_tracker_gatherer(config, port)
  return restart_wrapper("tracker_gatherer", config, host, port, args)

servertype.RegisterRestartFunction('tracker_gatherer', restart_tracker_gatherer)

#-------------------------------------------------------------------------------
# URLTRACKER_SERVER
#-------------------------------------------------------------------------------

def args_urltracker_server(config, port):
  num_shards = config.GetNumShards('urltracker_server')
  shard_num = servertype.GetPortShard(port)

  if config.var('GFS_ALIASES'):
    dirprefix = "urltracker"
  else:
    dirprefix = ""

  args = [
    "--nologging",     # we don't really care that we've opened another bigfile
    "--datadir="                + config.var('DATADIR'),
    "--port=%d"                 % (port),
    "--shard_num=%d"            % (shard_num),
    "--num_shards=%d"           % (num_shards),
    "--namespace_prefix=%s"     % (config.var('NAMESPACE_PREFIX')),
    "--urltracker_directory=%s" % (config.var('URLTRACKER_DIRECTORY')),
    "--urltracker_dirprefix=%s" % (dirprefix),
    ]

  if config.var('URLTRACKER_SERVER_REFRESH_TIME'):
    args.append('--data_refresh_time=%d' %
                config.var('URLTRACKER_SERVER_REFRESH_TIME'))

  if config.var('URLTRACKER_SERVER_LOAD_BEFORE_DELETE'):
    args.append('--load_before_delete')

  if config.var('URLTRACKER_SERVER_MMAP_DATA'):
    args.append("--mmap_data")
    # downgrade to buffered access if mmap fails
    if config.var('URLTRACKER_SERVER_ALLOW_BUFFERED_ACCESS'):
      args.append("--allow_buffered")

  args = args + get_gfs_args(config)
  if config.var('GFS_ALIASES'):
    if config.var('URLTRACKER_GFS_CELL_ARGS'):
      args.append('--gfs_cell_args=%s' %
                  config.var('URLTRACKER_GFS_CELL_ARGS'))

  (shardinfo, backends) = servertype.GetShardInfoBackends(
    config, 'urltracker_server', 0, 'http', 2)
  if backends.HasBackEnds():
    args.append("--backends=%s" % backends.AsString())
    args.append("--shardinfo=%s" % shardinfo.AsString())

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # TODO: remove this when the dependency between the urltracker and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  # TODO(tianyu): temporary workaround for the mmap memory issue
  args.append('--mmap_urls=false')
  args.append('--mmap_sums=false')

  return args

def restart_urltracker_server(config, host, port):
  args = args_urltracker_server(config, port)
  return restart_wrapper("urltracker_server", config, host, port, args)

servertype.RegisterRestartFunction('urltracker_server',
                                   restart_urltracker_server)

# -----------------------------------------------------------------------
# These are general purpose functions - we need to group them somewhere
# -----------------------------------------------------------------------

def gen_request_log_file_name(namespace, id, priority=None):
  if priority:
    return "%sreq-%s@%d" % (namespace, id, priority)
  else:
    return "%sreq-%s" % (namespace, id)

def gen_response_log_file_name(namespace, id, priority=None):
  if priority:
    return "%sresp-%s@%d" % (namespace, id, priority)
  else:
    return "%sresp-%s" % (namespace, id)


# given a (var, key) pair, if the variable is a map,
# return var[key], otherwise return var.
def get_scalar_or_map_value(var, key):
  if type(var) == types.DictionaryType:
    return var.get(key)
  else:
    return var
#end def

#-------------------------------------------------------------------------------
# PR_MAIN
#-------------------------------------------------------------------------------

def num_pageranks(starturls):
  return len(string.split(starturls, ','))

# Pagerank derives its host port list for communication with the
# pagerank main by adding 500 to the ports specified for the
# pagerankers The actual ports used by the pagerankers are used for
# health checks
def pagerank_host_port_list(name, config):

  # we cache this because it is used so often
  ret = config.get_cache("pagerank_host_port_list", "cache")
  if ret: return ret

  # we add 500 to the host ports and build the arg string
  hostports = map(lambda x: (x[0], x[1]+500), config.GetServerHostPorts(name))
  # we cannot use fully-qualified hostname for pr_machines flag
  ret = serverflags.MakeHostPortsArg(hostports, sep=',', qualify=0)

  # cache and return value
  config.put_cache("pagerank_host_port_list", "cache", ret)
  return ret

# Compute pr replicas
#   If not reading link maps from link processors, then there is a one-to-one
#   correspondence between urlmanagers and pagerankers and we use urlmanagers
#   as pr replicas.
#   Otherwise, if a specific replica is defined for a pr, use that replica.
#              Otherwise, set up pairwise replication.
def pr_main_replicas(config):
  if not config.var('PAGERANKER_READ_LINKMAPS'):
    return serverflags.MakeHostPortsArg(
      config.GetServerHostPorts('urlmanager')
    )

  # set up pr replicas pairwise
  replicas = []
  hostports = config.GetServerHostPorts('pr_main')
  num_prs = config.GetNumShards("pr_main")
  baseport = config.GetPortList('pr_main')[0]

  for (host, port) in hostports:
    if config.GetReplicaMap().has_key(port):  # a replica is defined for host
      replicas.append("%s:%d" %(config.GetReplicaMap()[port][0], port))
    else:
      if not (port & 0x1):   # even shard
        if num_prs == (port - baseport) + 1:
          sys.exit("ERROR - can't find pr replica for port: %d. \
                    Since the number of prs is odd, you can't rely on pairwise \
                    replication. Please add a specific replica for \
                    this machine." % port)
        rep_port = port + 1  # use next host as its replica
      else:
        rep_port = port - 1  # use the prev host as its replica
      replicas.append("%s:%d" %(config.GetServerMap()[rep_port][0], rep_port))
  return string.join(replicas, ',')

def args_pr_main(config, port, use_base_crawl):
  shard_num = servertype.GetPortShard(port)
  args = [
    "--datadir=" + config.var('DATADIR'),
    "--pr_shard=%d" % shard_num,
    "--pr_num_subshards=%d" % (config.var('PAGERANKER_NUM_SUBSHARDS')),
    "--pr_machines=%s" % pagerank_host_port_list("pr_main", config),
    "--port=%d" % (port),
    "--pr_num_pages=%s" % (
    prodlib.int_to_string(config.var('TOTAL_URLS_EXPECTED'))),
    "--pr_num_pages_normalization=%d" % (config.var('PR_NUM_PAGES_NORM')),
    "--pr_num_par=%d " % num_pageranks(config.var('PAGERANKER_STARTURLS')),
    "--crawl_start_urls=%s" % config.var('PAGERANKER_STARTURLS'),
    "--pr_depth=%d" % (config.var('PAGERANKER_DEPTH')),
    "--nologging",
    "--url_canonicalize_to_punycode",
    ]

  if config.var('PAGERANKER_REMOTE_READ_THREADS'):
    args.append("--pr_remote_read_threads=%d" %
                config.var('PAGERANKER_REMOTE_READ_THREADS'))

  if config.var('PAGERANKER_FIXUP_DECLINES') == 0:
    args.append("--nofixup_declines")

  if not config.var('PAGERANKER_KEEP_100TH_ITERATION'):
    args.append("--nokeep_100th_iteration")

  if config.var('PAGERANKER_SLEEP_BETWEEN_ITERATIONS'):
    args.append("--sleep_between_iterations=%d" %
                config.var('PAGERANKER_SLEEP_BETWEEN_ITERATIONS'))

  if config.var('CRAWL_ID_STRING') and not use_base_crawl:
    args.append("--crawl_id_string=%s" % config.var('CRAWL_ID_STRING'))

  # For one shard prefetching does not have much advantage. This flag
  # saves memory for Enterprise.
  if (config.var('PAGERANKER_SUBSHARD_PREFETCH') == 0) or \
     (config.var('ENTERPRISE') and config.GetNumShards("pr_main") == 1):
    args.append("--nosubshard_prefetch")

  if config.var('PAGERANKER_RELOAD_START_URLS_IF_CHANGED') and \
     config.var('PAGERANKER_RELOAD_START_URLS_IF_CHANGED') == 1:
    args.append("--pr_reload_start_urls_if_changed=true")

  if config.var('PAGERANKER_WEAK_CONVERGENCE_FRACTION'):
    args.append("--pr_weak_converge_fraction=%f" %
                config.var('PAGERANKER_WEAK_CONVERGENCE_FRACTION'))
  if config.var('PAGERANKER_CONVERGENCE_FRACTION'):
    args.append("--pr_converge_fraction=%f" %
                config.var('PAGERANKER_CONVERGENCE_FRACTION'))
  # In depth mode, we need the starturls file to set
  # their depth properly
  if config.var('PAGERANKER_DEPTH') > 0:
    args.append("--depth_starturls=" + config.var('STARTURLS'))

  if config.var('PAGERANKER_NON_PROPAGATE_URLS'):
    args.append("--pr_non_propagate_file="+config.var('PAGERANKER_NON_PROPAGATE_URLS'))
  if config.var('PAGERANKER_USE_WTD_LINKS'):
    args.append("--use_wtd_links")

  if config.var('PAGERANKER_REPLICAS'):
    args.append("--pr_replicas=%s" % pr_main_replicas(config))
  if not config.var('PAGERANKER_USE_URLMGR'):
    args.append("--nouse_urlmgr")
  if not config.var('PAGERANKER_GEN_URLIDX'):
    args.append("--nogenerate_url_idx")
  if config.var('PAGERANKER_BATCHURLS_PREFIX'):
    args.append("--pr_batchmode")
    if string.find(config.var('PAGERANKER_BATCHURLS_PREFIX'), "/") == 0:
      args.append("--pr_batch_prefix=%s" % config.var('PAGERANKER_BATCHURLS_PREFIX'))
    else:
      args.append("--pr_batch_prefix=%s/%s"
                  % (config.var('GOOGLEDATA'), config.var('PAGERANKER_BATCHURLS_PREFIX')))
  if config.var('PAGERANKER_COMPUTE_HIGHPRS'):
    args.append("--compute_highprs")

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    args.append("--keep_checksum_for_checkpoints=false")

  if config.var('PAGERANKER_READ_LINKMAPS'):
    link_server_type = get_global_link_machine_type(config)
    num_links = config.GetNumShards(link_server_type)
    num_prs = config.GetNumShards('pr_main')
    # verify num_prs is a multiple of num_links
    if num_prs % num_links != 0:
      print "No. of prs: %d is not a multiple of No. of global links: %d" % (
        num_prs, num_links)
      sys.exit(1)

    ratio = num_prs / num_links
    my_linkshard = shard_num / ratio
    # note that GenNamespacePrefix takes the machine_type that
    # generates the logfiles.  In this case, we read from global_link's
    # sorted map
    args.append("--links_fileset=%sFILESET_rt%s_links" % \
                (servertype.GenNamespacePrefix(config, link_server_type,
                                               my_linkshard, num_links),
                 config.var('RTSERVER_INDEX_PREFIX')))
    if config.var('PAGERANKER_LINKS_LOCKS_FILE'):
      args.append("--links_locks_file=%spr_main_links_locks_file_%d" % \
                  (servertype.GenNamespacePrefix(config, link_server_type,
                                               my_linkshard, num_links),
                   port))
    args.append("--pagerankers_per_linkmap=%d" % ratio)
    args.append("--proutput_shards=%d" % config.GetNumShards('urlmanager'))

  args.append("--barrier_name_prefix=%sbarriers" % \
              config.var('NAMESPACE_PREFIX'))

  args = args + get_gfs_args(config)


  if config.var('GFS_USER'):
    args.append('--gfs_user=%s' % config.var('GFS_USER'))

  if config.var('OUTPUT_NAMESPACE_PREFIX').has_key('pr_main'):
    args.append("--pr_namespace_prefix=%s" %
                config.var('OUTPUT_NAMESPACE_PREFIX')['pr_main'])
    # NOTE: all the pagerankers must have the same pr_namespace_prefix !!!

  if config.var('PAGERANKER_INPUT_PRVEC_SHARDS') > 0:
    args.append("--input_prvec_shards=%d" % \
                config.var('PAGERANKER_INPUT_PRVEC_SHARDS'))

  if config.var('PAGERANKER_RECOVER_ON_RESTART'):
    args.append("--run_recover_mode_on_restart")

  if config.var('PAGERANKER_RETRY_DELAY'):
    # Cause the pageranker to keep retrying instead of aborting on certain
    # error conditions such as no crawl start points.
    # The argument is how long we wait, in seconds
    args.append("--retry_delay=%d" % config.var('PAGERANKER_RETRY_DELAY'))

  if config.var('LABS_PAGERANK_INJECTION'):
    # Experimental (labs) feature: specify the file for pagerank injection
    args.append("--pr_injection_file=%s" % \
                config.var('LABS_PAGERANK_INJECTION'))

  if config.var('PAGERANKER_MAX_UNCONSUMED_ITERATIONS'):
    args.append("--max_unconsumed_iterations=%d" % \
                config.var('PAGERANKER_MAX_UNCONSUMED_ITERATIONS'))

  # add rfserver bank if specified
  args = args + servertype.GetRfserverBankArgs(config)

  return args

def restart_pr_main(config, host, port):
  if config.var('USE_PAGERANK') and \
     config.var('PAGERANKER_PROG') == 'pr_main':
    args = args_pr_main(config, port, 0)  # 0 -> use crawl id if one specified
    return restart_wrapper("pr_main", config, host, port, args)
  else:
    print "NOT USING PR_MAIN! Flag not set"
    return ""

servertype.RegisterRestartFunction('pr_main', restart_pr_main)

#-------------------------------------------------------------------------------
# COMMON INDEXER ARGS
#-------------------------------------------------------------------------------

def is_single_link_processing_system(config):
  return ((config.GetNumShards("global_link") == 1) and
          (config.GetNumShards("global_anchor") == 0))

def anchor_request_log_prefix(config, anchor_server_type):
  prefix_dict = config.var('OUTPUT_NAMESPACE_PREFIX')
  if prefix_dict and prefix_dict.get(anchor_server_type):
    return prefix_dict[anchor_server_type]
  else:
    return config.var('GLOBAL_NAMESPACE_PREFIX')

def anchorresp_merger_input_logfile(config, port, filetype):
  """
  Given a filetype (src_req_log or dest_resp_log), return
  the log file name of that filetype.
  """
  srvtype = 'anchorresp_merger'
  indexer_type = 'base_indexer' # we only handle base_indexer for now
  shard = servertype.GetPortShard(port)
  num_shards = config.GetNumShards(srvtype)
  if filetype == 'src_req_log':
    return "%s%s/%s-request-log" % (
      anchor_request_log_prefix(config, srvtype),
      servertype.GenRTIdentifier(srvtype, shard, num_shards),
      indexer_type)
  elif filetype == 'dest_resp_log':
    return "%sresponse-log" % (gen_anchorlogs_prefix(config, srvtype,
                                                     'global_anchor',
                                                     shard, num_shards))
  else:
    assert 0, "Bad filetype: %s" % filetype
  # end if

def input_log_names(config, machine_type, port):
  """
  Return the list of input log names for *machine_type* and *port*
  NOTE: The first one in the list MUST be the primary log.
  """
  if machine_type in ['docidserver', 'urlserver',
                      'bot', 'contentfilter', 'limitd',
                      'pr_main', 'categoryserver', 'rtdupserver',
                      'rfserver', 'anchorreq_forwarder', 'doc',
                      'rtduphistory_converter', 'categorymapserver',
                      'dnscache', 'historyserver',
                      'linkdrop_server']:
    return [] # no input logs
  #endif

  # TODO: Once we have GFS, remove the per-indexer/per-linkprocessor
  # log files, and allow all of this to happen through a single
  # log file (except possible for a single additional high-priority
  # log file to allow high priority requests to make it throught the
  # system more quickly).

  # Start with the single primary log file
  files = []
  if machine_type == 'rejected_urls' or machine_type == 'seen_hosts':
    num_shards = config.GetNumShards('urlmanager')
  else:
    num_shards = config.GetNumShards(machine_type)
  shard = servertype.GetPortShard(port)

  if machine_type == 'anchorresp_merger':
    # Add input logfiles (src_req_log and dest_resp_log) to files
    # We add them so that bartcontroller can figure out
    # what directories need to be created.
    files.append(anchorresp_merger_input_logfile(config, port, 'src_req_log'))
    files.append(anchorresp_merger_input_logfile(config, port,
                                                 'dest_resp_log'))
    return files
  # end if

  # Global anchor processors read the sharded logs generated by the link
  # processors.
  # TODO: for transition period, urlhistory_processor's log will be
  #       generated by urlhistory2log machines
  # Everyone else reads logs generated by the content filter.
  if machine_type == "global_anchor":
    num_src_shards = config.GetNumShards(get_global_link_machine_type(config))
  elif ( config.var('URLHISTORY_TRANSITION') and
         machine_type == 'urlhistory_processor' ): # Temporary transition
    num_src_shards = config.GetNumShards('urlhistory2log')
  else:
    num_src_shards = config.GetNumShards('contentfilter')
  #endif

  if config.var('GFS_ALIASES'):
    assert config.var('RTSERVER_LOGS').has_key(machine_type), \
           "Please set RTSERVER_LOGS['%s']" % machine_type
  #endif

  files = files + get_reader_rt_logs(config, machine_type,
                                     shard, num_shards, num_src_shards)

  # indexers sometimes play multiple roles.
  if machine_type in ('base_indexer', 'daily_indexer', 'rt_indexer'):
    # are indexers used as process link logs?
    # Yes, if we don't use anchor processors.
    # (it is sort of confusing, but well... I am just writing comments)
    if (not config.var('RTINDEXER_USE_ANCHOR_PROCESSOR') and
        config.var('RTINDEXER_AS_ANCHOR_PROCESSOR')):
      # For multi-sharded system, anchor logs generated by link processor
      # need to be processed. For single sharded systems, link processor
      # takes care of generating anchors directly.
      if num_shards > 1:
        files = files + get_reader_rt_logs(config, 'global_anchor',
                                           shard, num_shards,
                                           num_src_shards)
      if config.var('GFS_ALIASES'):
        files = files + get_reader_rt_logs(config, 'global_link',
                                           shard, num_shards,
                                           num_src_shards)
      else:
        # add in link logs because the indexer will be processing the links
        # directly
        num_link_shards = config.GetNumShards(
          get_global_link_machine_type(config))
        for dest_index in xrange(num_link_shards):
          files = files + get_reader_rt_logs(config, 'global_link',
                                             dest_index, num_link_shards,
                                             num_src_shards)
        #endfor
      #endif GFS
    #end if indexers are used as process link logs

    # if we use urlhistory_processor as part of base_indexer
    # then we need to append its logs too
    if config.GetNumShards('urlhistory_processor') == 0 and \
       config.var('RTINDEXER_AS_URLHISTORY_PROCESSOR') == 1:

      if config.var('GFS_ALIASES'):
        files = files + get_reader_rt_logs(config, 'urlhistory_processor',
                                           shard, num_shards,
                                           num_src_shards)
      else:
        num_history_shards = config.GetNumShards(machine_type)
        for dest_index in xrange(num_history_shards):
          files = files + get_reader_rt_logs(config, 'urlhistory_processor',
                                             dest_index, num_history_shards,
                                             num_src_shards)
        #endfor
      #endif using gfs or not
    #endif indexers also process urlhistory info
  #end if indexers

  # Add the anchor
  if config.var('GFS_ALIASES'):
    separator = '/'   # only gfs supports '/'
  else:
    separator = '-'
  if ((machine_type == "global_anchor") or
      (machine_type == "global_link" and is_single_link_processing_system(config))):
    priority = 2
    anchor_requestors = ['base_indexer', 'daily_indexer', 'rt_indexer']
    if config.GetNumShards('anchorresp_merger') > 0:
      # there are anchorresp mergers running, also need to read
      # request logs from them.
      # NOTE: anchorresp_merger is added to the head of the list
      # because we want it to have the lowest priorities among
      # the request logs (The next loop assign priorities to request logs
      # in increasing order). The main reason for this is that
      # anchor requests in base_indexer and other indexer logs may by
      # sorted. Requests in anchorresp_merger logs are normally not sorted
      # and we don't want to mix sorted requests with unsorted requests
      # during anchor lookups.
      anchor_requestors = ['anchorresp_merger']  + anchor_requestors
    # end if
    for anchor_requestor_type in anchor_requestors:
      to_id = servertype.GenRTIdentifier(machine_type, shard, num_shards)
      if priority == None: prioritystring = ""
      else: prioritystring = "@%s" % priority
      files.append("%s%s%s%s-request-log%s" % (
        anchor_request_log_prefix(config, 'global_anchor'), to_id, separator,
        anchor_requestor_type, prioritystring))
      priority = priority + 1
    # end for
  elif (config.var('RTINDEXER_USE_ANCHOR_PROCESSOR') or \
        config.var('RTINDEXER_AS_ANCHOR_PROCESSOR')) and \
       (machine_type in  ('base_indexer', 'daily_indexer', 'rt_indexer')):

    # if running base_indexer also as global_anchor, append anchor request log
    if config.var('RTINDEXER_AS_ANCHOR_PROCESSOR'):
      to_id = servertype.GenRTIdentifier('global_anchor', shard, num_shards)
      files.append("%s%s%s%s-request-log@2" % (
        anchor_request_log_prefix(config, 'global_anchor'),
        to_id, separator, machine_type))

    # append anchor response log. If there are anchorresp_mergers
    # running, then indexers may be waiting for responses from anchorresp
    # mergers, too.
    anchor_servers = ['global_anchor']
    if config.GetNumShards('anchorresp_merger') > 0:
      anchor_servers.append('anchorresp_merger')
    # endif
    for srv in anchor_servers:
      num_link_shards = config.GetNumShards(srv)
      if (num_link_shards == 0):
        num_link_shards = config.GetNumShards(
          get_global_link_machine_type(config))
      # end if
      namespace = gen_anchorlogs_prefix(config, machine_type, srv,
                                        shard, num_shards)
      if config.var('GFS_ALIASES'):
        # we only need one response log
        files.append("%sresponse-log@5" % namespace)
      else:
        for link_shard in xrange(0, num_link_shards):
          to_id = servertype.GenRTIdentifier(srv, link_shard, num_link_shards)
          files.append("%s%s%sresponse-log@5" % (config.var('NAMESPACE_PREFIX'),
                                                 to_id, separator))

        #endfor
      #endif GFS
    # end for srv
  #end dealing anchors

  # WORKESCHEDULER stuff
  if machine_type in ['base_indexer', 'daily_indexer', 'rt_indexer']:
    log_basenames = []
    if config.var('ENABLE_WORKSCHEDULER_COLLECTIONS'):
      log_basenames.append(config.var('GLOBAL_NAMESPACE_PREFIX') +
                           config.var('WORKSCHEDULER_COLLECTIONS_LOG_PREFIX'))
    #endif
    if config.var('ENABLE_WORKSCHEDULER_REMOVEDOC_SCHEDULER') or \
       config.var('ENABLE_CRAWLMANAGER_REMOVEDOC'):
      # this log will contain removedoc logs from the ripper process
      # that the workscheduler-rippers will will run
      # it will be sharded for each rt_doc_shard
      log_basenames.append(config.var('GLOBAL_NAMESPACE_PREFIX') +
                           config.var('WORKSCHEDULER_REMOVEDOC_LOG_PREFIX'))
    #endif
    if config.var('ENABLE_WORKSCHEDULER_SORTBYDATE'):
      # this log will contain date field logs from the ripper process
      # that the workscheduler-rippers will run
      # it will be sharded for each rt_doc_shard
      log_basenames.append(config.var('GLOBAL_NAMESPACE_PREFIX') +
                           config.var('WORKSCHEDULER_DATEFIELD_LOG_PREFIX'))
    #endif
    for logbasename in log_basenames:
      files = files + get_reader_rt_logs(config, "", # no machine type
                                         shard, num_shards,
                                         1, # one writer
                                         logbasename,
                                         priority=5)
    #endfor
  #endif

  # For urlhistory_processor to receive DeleteDoc command so that it can
  # garbage collect urlhistory records
  if (machine_type == 'urlhistory_processor'):
    if config.var('ENABLE_WORKSCHEDULER_REMOVEDOC_SCHEDULER') or \
       config.var('ENABLE_CRAWLMANAGER_REMOVEDOC'):
      files = files + get_reader_rt_logs(config, '', # no machine type
                           shard, num_shards,
                           1, # one writer
                           config.var('GLOBAL_NAMESPACE_PREFIX') +
                           config.var('WORKSCHEDULER_REMOVEDOC_UHP_LOG_PREFIX'),
                           priority=5)
    #endif WORKSCHEDULER stuff
  #endif

  # For feed doc deleter->rtindexers logs
  if config.var('ENABLE_WORKSCHEDULER_FEED_DOC_DELETER'):
    if (config.var('RTSERVER_LOGS') and
       config.var('RTLOG_FEED_DOC_DELETER_SUFFIX') and
       machine_type in ('base_indexer', 'rt_indexer', 'urlhistory_processor',
                        'daily_indexer', 'urlmanager', 'tracker_gatherer')):
      logbasename = config.var('RTSERVER_LOGS')[machine_type] + \
                    config.var('RTLOG_FEED_DOC_DELETER_SUFFIX')
      files = files + get_reader_rt_logs(config, machine_type,
                                         shard, num_shards,
                                         1,  # 1 writer
                                         logbasename)
  #endif feed doc deleter->rtindexers logs

  if config.var('ENABLE_REALTIME_SEKULITE') or \
     config.var('ENABLE_SINGLE_SIGN_ON'):
    # this log will contain unsecure terms which go to the main rtserver
    # it will be sharded for each rt_doc_shard
    if machine_type in ['base_indexer', 'daily_indexer', 'rt_indexer']:
      files = files + get_reader_rt_logs(config, "", # no machine type
                                         shard, num_shards,
                                         1, # one writer
                                         config.var('GLOBAL_NAMESPACE_PREFIX') +
                                         config.var('WORKSCHEDULER_SEKURE_LOG_PREFIX'),
                                         priority=5)
    #end if indexer
  #endif SEKULITE

  # For urlmgr->rtindexers logs
  if config.var('RTSERVER_LOGS') and \
     config.var('RTLOG_URLMANAGER_MODE_SUFFIX') and \
     machine_type in ('base_indexer', 'daily_indexer', 'rt_indexer'):
    logbasename = config.var('RTSERVER_LOGS')[machine_type] + \
                  config.var('RTLOG_URLMANAGER_MODE_SUFFIX')
    files = files + get_reader_rt_logs(config, machine_type,
                                       shard, num_shards,
                                       config.GetNumShards('urlmanager'),
                                       logbasename)
  #endif urlmgr->rtindexers logs

  # For feeder, must have seperate logs even for GFS
  #For feeder->rtindexers logs
  if config.var('RTSERVER_LOGS') and \
     config.var('RTLOG_FEEDER_SUFFIX') and \
     machine_type in ('base_indexer', 'daily_indexer', 'rt_indexer',
                        'urlhistory_processor'):
    logbasename = config.var('RTSERVER_LOGS')[machine_type] + \
                  config.var('RTLOG_FEEDER_SUFFIX')
    files = files + get_reader_rt_logs(config, machine_type,
                                       shard, num_shards,
                                       config.GetNumShards('feeder'),
                                       logbasename)
  #endif feeder->rtindexers logs

  return files
#end input_log_names

def get_storedata_namespace_prefix(config, type, shard_num, num_shards,
                                   epoch_str=None):
  """construct the storedata namespace prefix for servertype 'type'
     Return None, if STOREDATA_NAMESPACE_PREFIX[type] is undefined.
  """
  storedata_path = config.var('STOREDATA_NAMESPACE_PREFIX').get(type)
  if not storedata_path:
    return None
  if epoch_str == None:
    epoch_str = '%04d-%02d-%02d-%02d-%02d' % \
                (config.var('RT_START_YEAR'),
                 config.var('RT_START_MONTH'),
                 config.var('RT_START_DAY'),
                 config.var('RT_START_VERSION'),
                 config.var('RT_SEGMENT'))
  # endif
  return "%s%s/%s/%03d_of_%03d/" % (storedata_path, epoch_str, type,
                                    shard_num, num_shards)
#end get_storedata_namespace_prefix


def get_urlmanager_storedata_namespace_prefix(config, shard_num, num_shards):
  """construct storedata namespace prefix for urlmanager
     This case is pull out so that it can be shared by readers of
     urls_* logs
  """
  if config.var('URLMANAGER_AUTOMATE_RT_PARAMETERS'):
    storedata_path = get_storedata_namespace_prefix(config, 'urlmanager',
                                                    shard_num, num_shards)
    assert storedata_path  # must be set in auto mode
  else: # no automated crawl status relaying
    # set storedata_path.  default value: namespace_prefix
    storedata_dict = config.var('STOREDATA_NAMESPACE_PREFIX')
    storedata_path = storedata_dict.get('urlmanager',
                                        config.var('NAMESPACE_PREFIX'))
  # end if
  return storedata_path
#end

def get_urlmanager_previous_discovered_files(config, shard, num_shards):
  """ Returns the previous discovered url files in previous epochs --
  the list is in epoch order """
  def _get_discovered_file_name(config, shard, num_shards, epoch):
    prefix = get_storedata_namespace_prefix(
      config, 'urlmanager', shard, num_shards,
      epoch_str=config.var('RT_ALL_PREVIOUS_EPOCHS_FOR_CYCLE')[epoch])
    return "%surls_discovered_%02d_of_%02d_epoch%010d" % (
      prefix, shard, num_shards, epoch)


  if not config.var('URLMANAGER_AUTOMATE_RT_PARAMETERS'):
    raise (
      "We don't know to deal with RT_ALL_PREVIOUS_EPOCHS_FOR_CYCLE unless "
      "the urlmanager parameters are automated")
  # endif
  epochs = config.var('RT_ALL_PREVIOUS_EPOCHS_FOR_CYCLE').keys()
  epochs.sort()
  ret = []
  files = []
  file_to_drop = None
  if len(epochs) == config.var('RT_NUM_SEGMENTS'):
    file_to_drop = _get_discovered_file_name(config, shard,
                                             num_shards, epochs[0])
    epochs = epochs[1:]
  # endif
  min_epoch = config.var('URLMANAGER_MINIMUM_EPOCH_USED_FOR_DISCOVERED')
  for e in epochs:
    if min_epoch and min_epoch > e:
      continue
    files.append(_get_discovered_file_name(config, shard, num_shards, e))
  # endfor
  return (files, file_to_drop)
# endif

# TODO: TODO - this is copied from preprod.py since apparently shared
# with the rippers - if that changes this has to change!!!
# args shared by rtserver and ripper for building doc restricts
def gen_restrict_args(config):
  # construct url pattern based restrict names
  restrict_files = []
  if None == config.var('RESTRICT_PATTERN'):
    restrict_files = glob.glob(config.var('GOOGLEDATA')+"find/restrict-*.pat")
  else :
    restrict_files = glob.glob(config.var('RESTRICT_PATTERN'))
  if None != config.var('RESTRICT_PATTERN_FILES'):
    for file in config.var('RESTRICT_PATTERN_FILES'):
      if file not in restrict_files: restrict_files.append(file)

  url_restrict_args = [
    # url-based restricts
    "--restricts=%s" % (string.join(restrict_files, ',')),
    ]
  if config.var('RESTRICT_LOAD_BAD_PATTERNS'):
    url_restrict_args.append('--load_bad_restrict_patterns')

  geo_restrict_args = [
    # ip based geolocation/geotargetting restricts.
    "--restricts_geo_countries",
    "--geolib_data_path=%sgws/" % config.var('GOOGLEDATA'),
    "--restricts_prefix_geo=country",
    ]
  lang_restrict_args = [
    # language restricts
    "--langenc_rprefix=lang",
    ]
  main_index_restrict_args = [
    # mac restrict
    "--mac=mac",
    # trafficcounter restrict
    "--tffc=tffc",
    # microsoft restrict
    "--microsoft=microsoft",
    "--microsoft_pat=%s/find/microsoft.pat" % config.var('GOOGLEDATA'),
    # noarchive restrict
    "--noarchive=noarchive",
    # main adult restrict
    "--familywords=%sfind/mainfamily.wordweights" % config.var('GOOGLEDATA'),
    # OEM family restrict
    "--oemfamily=adult",     # "safesearch strict"
    "--oemfamilythreshold=0.05",            # associated with --oemfamily
    "--small_index_cutoff=%d" % config.var('SUBSET_MAX_DOCID'),
    # Filetypes restricts
    "--filetypes=filetypes",
    # Shopping restrict
    "--shopping_restrict=shopping"
    ]
  porn_adult_common_restrict_args = [
    # main adult restrict (common stuff)
    "--family=mainadult",    # restrict for "safesearch on"
    "--familywhitelist=%sfind/family.whitelist" % config.var('GOOGLEDATA'),
    "--familyblacklist=%sfind/family.blacklist" % config.var('GOOGLEDATA'),
    "--familythreshold=0.25",                  # associated with --family
    "--empty=empty",         # some other porn thing
    # porn restrict
    "--porn=porn",           # a separate porn list
    "--pornwords=%sfind/porn.wordweights" % config.var('GOOGLEDATA'), #
    "--pornwhitelist=%sfind/family.whitelist" % config.var('GOOGLEDATA'),
    "--pornblacklist=%sfind/porn.blacklist" % config.var('GOOGLEDATA'),
  ]

  i18nporn_langs = ("spanish,german,french,italian,portuguese,japanese,"
                    "chinese,chineset,korean,dutch")
  i18nporn_restrict_args = [
    "--i18nporn", #creates restricts "i18nporn1", "i18nporn2", "i18nporn4"
                  #for 8 levels of porn cutoffs (for now -- just testing).
                  #and "i18nshort" for pages with few words (maybe not safe)
    "--frames",   #pages with frames may not be safe
    "--i18n_porn_languages=%s" % i18nporn_langs,
    "--classify_feature_file=%s/i18nporn/features" % config.var('GOOGLEDATA'), #prefix for each language
    "--max_terms_per_doc=30" # look at only first 30 terms (based on training).
    ]

  progandargs = lang_restrict_args   # always build lang restricts

  if config.var('MAIN_INDEX_RESTRICTS_ON'):
    progandargs = progandargs + main_index_restrict_args

  if config.var('MAIN_INDEX_RESTRICTS_ON') or config.var('CRAWL_USENET'):
    progandargs =  progandargs + porn_adult_common_restrict_args + \
                   i18nporn_restrict_args

  if config.var('GEO_RESTRICTS_ON') or config.var('MAIN_INDEX_RESTRICTS_ON'):
    progandargs = progandargs + geo_restrict_args

  if config.var('URL_RESTRICTS_ON') or config.var('MAIN_INDEX_RESTRICTS_ON'):
    progandargs = progandargs + url_restrict_args

  return progandargs

# turn off index/doc/link serving
def args_nosvc_indexer():
  return [
    "--indexserver_port=0",
    "--docserver_port=0",
    "--linkserver_port=0",
  ]

def args_docshard_indexer(config, machine_type, port):
  return [
    "--rt_doc_shard=%d" % servertype.GetPortShard(port),
    "--num_rt_doc_shards=%d" % config.GetNumShards(machine_type),
  ]

def get_oldest_epoch_to_serve(config, machine_type):
  oldest_epoch = config.var('RTSERVER_OLDEST_EPOCH_TO_SERVE').get(machine_type)
  if oldest_epoch:
    if oldest_epoch < 0:
      prev_epochs = config.var('RT_ALL_PREVIOUS_EPOCHS_FOR_2CYCLES').keys()
      if len(prev_epochs) < -oldest_epoch:
        raise "Not enough previous epochs for relative "\
              "oldest epoch: %s - %s" % (len(prev_epochs), -oldest_epoch)
      # endif
      prev_epochs.sort()
      oldest_epoch = prev_epochs[oldest_epoch]
    # endif
  # end if
  return oldest_epoch

def get_epochs_not_to_serve(config, machine_type):
  return config.var('RTSERVER_EPOCHS_NOT_TO_SERVE').get(machine_type, [])


def args_common_indexer(config, machine_type, port):
  num_shards = config.GetNumShards(machine_type)
  shard = servertype.GetPortShard(port)
  input_logs = input_log_names(config, machine_type, port)

  if config.var('RTSERVER_UPDATE_LOGNAME'):
    update_log = "%s%s_%s_%03d" % (
      config.var('NAMESPACE_PREFIX'),
      config.var('RTSERVER_UPDATE_LOGNAME'),
      machine_type, shard)
    input_logs.append(update_log)
  else:
    update_log = ""

  args = [
    # TODO: --port is temporary - so that the rtserver gets killed
    #       This must be at the beginning to ensure ps auxwwww will capture it
    "--port=%d" % port,
    "--datadir=%s" % config.var('DATADIR'),
    "--logfiles=%s" % string.join(input_logs, ","),
    "--cmd_flush_interval=%d" % config.var('RTSERVER_CMD_FLUSH_INTERVAL'),
    "--merger",
    "--num_index_shards=1",
    "--max_checkpoints_before_deletion=%d" \
       % config.var('RTSERVER_MAX_CHECKPOINTS_BEFORE_DELETION'),
    "--ignore_docidservers",
    "--workerthreads=%d" % config.var('RTSERVER_NUM_WORKER_THREADS'),
    "--update_logfile=%s" % update_log,
    "--num_checkpoints_to_save=20",
    ]

  if not config.var("RTSERVER_NOLOCK_FILE_BEFORE_DELETE"):
    args.append('--lock_file_before_delete')

  # need outgoing_anchor_logfiles flag only for multi-sharded system.
  if machine_type in ('base_indexer', 'daily_indexer', 'rt_indexer'):
    if (not config.var('RTINDEXER_USE_ANCHOR_PROCESSOR') and
          config.var('RTINDEXER_AS_ANCHOR_PROCESSOR')):
      # Number of anchor shards is same as that of indexer as indexer is acting
      # as anchor processor.
      nanchor_shards = config.GetNumShards(machine_type)
      if nanchor_shards > 1:
        files = []
        num_src_shards = config.GetNumShards('contentfilter')
        for anchorshard in xrange(0, nanchor_shards):
          files = files + get_reader_rt_logs(config, 'global_anchor',
                               anchorshard, nanchor_shards, num_src_shards)
        #endfor
        args.append("--outgoing_anchor_logfiles=" + string.join(files, ","))
      #endif
    #endif
  #endif

  if config.var('CRAWL_USERPASSWD_CONFIG'):
    args.append("--sekulite_userpasswd_config=%s" %
                config.var('CRAWL_USERPASSWD_CONFIG'))

  if config.var('ENABLE_SINGLE_SIGN_ON') and config.var('SSO_PATTERN_CONFIG'):
    args.append("--sso_pattern_config=%s" %
                config.var('SSO_PATTERN_CONFIG'))

  if config.var('LINK_DROPPER'):
    args.append("--link_dropper=" + config.var('LINK_DROPPER'))

  # continue, even if all checkpoint files are corrupted.
  if config.var('RTSERVER_IGNORE_CORRUPTED_CHECKPOINTS'):
      args.append("--ignore_corrupted_checkpoints")

  # don't load url patterns in global_rtduphistory because it doesn't
  # need them and they take 200MB of memory
  if machine_type != 'global_rtduphistory':
    args.extend([
      "--urls_to_ignore=%s" % config.var('BADURLS'),
      "--badurls_nopropagate=%s" % config.var('BADURLS_NOPROPAGATE'),
      "--badurls_demote=%s" % config.var('BADURLS_DEMOTE'),
    ])
  else:
    args.extend([
      "--urls_to_ignore=//dev/null", # clever rtserver barfs on /dev/null :)
      "--badurls_nopropagate=/dev/null",
      "--badurls_demote=/dev/null",
    ])
  # end if

  max_bytes_buffered = None
  if config.var('RTSERVER_MAX_BYTES_BUFFERED_BY_TYPE').has_key(machine_type):
    max_bytes_buffered = (
      config.var('RTSERVER_MAX_BYTES_BUFFERED_BY_TYPE')[machine_type])
  else:
    max_bytes_buffered =  config.var('RTSERVER_MAX_BYTES_BUFFERED')
  # end if
  assert max_bytes_buffered != None
  args.append("--max_rt_bytes_buffered=%d" % max_bytes_buffered)

  # The index_prefix needs to be special for urlhistory_processor
  if config.var('RTSERVER_INDEX_PREFIX_EXCEPTIONS').has_key(machine_type):
    args.append("--index_prefix=%s" % config.var(
      'RTSERVER_INDEX_PREFIX_EXCEPTIONS')[machine_type])
  else:
    args.append("--index_prefix=%s" % config.var('RTSERVER_INDEX_PREFIX'))
  # end if
  # add rfserver bank if specified
  args = args + servertype.GetRfserverBankArgs(config)

  if IsServerLocalized(config, machine_type):
    args.append("--cjk_config=%s/BasisTech/" % config.var('DATADIR'))
  else:
    args.append("--cjk_config=%s" % (config.var('CJKCONFIGDIR')))
  #end if localize
  args.append("--bt_version=%s" % config.var('BTVERSION'))

  # Merge parameters :
  if machine_type in config.var('RTSERVER_ENABLE_MULTI_MERGE'):
    args.append("--multi_merge")
  # end if
  var_and_flags = [
    ('CHINESE_NAME_HACK', '--chinesenamefix'),
    ('RTSERVER_DELETE_MULTI_EPOCH_MAPS_UNSERVED',
     '--delete_multi_epoch_maps_unserved'),
    ('RTSERVER_AVG_EPOCH_DELETION_INTERVAL',
     '--avg_epoch_deletion_interval'),
    ('RTSERVER_MINIMUM_SAVED_TIME',
     '--minimum_saved_time'),
    ('RTSERVER_MAX_NUM_CONSECUTIVE_FILES_FOR_INTEREPOCH_MERGE',
     '--max_num_consecutive_files_for_interepoch_merge'),
    ('RTSERVER_MINIMUM_EPOCH_TO_MERGE',
     '--minimum_epoch_to_merge'),
    ('RTSERVER_MERGE_SCHEDULER_NEW_MERGE_OP_TIME',
     '--new_merge_op_time'),
    ('RTSERVER_MERGE_SCHEDULER_NORMAL_MERGE_OP_TIME',
     '--normal_merge_op_time'),
    (None, '--inter_epoch_properties_to_merge',
     config.var('RTSERVER_INTER_EPOCH_PROPERTIES_TO_MERGE').get(
       machine_type)),
    (None, '--max_concurrent_merges',
     config.var('RTSERVER_MAX_CONCURRENT_MERGES').get(machine_type)),
    (None, '--max_concurrent_inter_epoch_merges',
     config.var('RTSERVER_MAX_CONCURRENT_INTER_EPOCH_MERGES').get(
       machine_type)),
  ]
  args = args + servertype.BuildFlagArgs(config, var_and_flags)

  if config.var('RTSERVER_MAXIMUM_MAPS_SIZES').has_key(machine_type):
    prop_sizes = []
    for prop, max_size in \
        config.var('RTSERVER_MAXIMUM_MAPS_SIZES')[machine_type].items():
      prop_sizes.append(("%s:%s" % (prop, max_size))[:-1])
    # end for
    args.append("--maximum_maps_sizes=%s" % string.join(prop_sizes, ','))
  # end if

  # Describe setup of processing machines in arguments, to make it easy
  # to navigate among them for /info requests.
  arg = serverflags.MakeHostPortsArg(config.GetServerHostPorts('global_link'))
  if arg: args.append("--display_link_machines=%s" % arg)
  arg = serverflags.MakeHostPortsArg(config.GetServerHostPorts('global_anchor'))
  if arg: args.append("--display_anchor_machines=%s" % arg)
  arg = serverflags.MakeHostPortsArg(
    config.GetServerHostPorts('urlhistory_processor')
  )
  if arg: args.append("--display_urlhistory_machines=%s" % arg)

  if machine_type in config.var('RTSERVER_AUTO_ADD_HEARTBEAT_TYPES'):
    args.append("--auto_add_heart_beat_to_primary_logs")
  if machine_type in config.var('RTSTATEBASE_SERVERS_ALWAYS_CREATE_NEW_FILESET'):
    args.append("--always_create_new_fileset")
  # Flush every so often
  flush_time = config.var('RTSERVER_FLUSH_TIME_INTERVAL').get(machine_type)
  if flush_time != None:
    args.append("--max_rt_flush_interval=%d" % flush_time)

  # Assign the oldest epoch to serve
  oldest_epoch = get_oldest_epoch_to_serve(config, machine_type)
  if oldest_epoch:
    args.append("--oldest_epoch_to_serve=%d" % oldest_epoch)
  # endif

  # Assign the list of epochs not to serve
  skip_epochs = get_epochs_not_to_serve(config, machine_type)
  if oldest_epoch:
    # the abandoned list can be quite long; include only the epochs that
    # would otherwise be served
    skip_epochs = filter(lambda x, emin=oldest_epoch: x >= emin, skip_epochs)
  # end if
  if skip_epochs:
    args.append("--epochs_not_to_serve=%s" %
                string.join(map(str, skip_epochs), ","))

  if config.var('LOG_INCOMING_PROTOCOLBUFFERS'):
    args.append("--log_incoming_updates")

  if config.var('RTMASTER_VERIFY_THRESHOLD') != None:
    args.append("--verify_threshold=%d" % config.var('RTMASTER_VERIFY_THRESHOLD'))

  rt_max_bytes_queued = None
  if config.var('RTPROCESSOR_MAX_BYTES_IN_LOGQUEUES_BY_TYPE').has_key(
    machine_type):
    rt_max_bytes_queued = (
      config.var('RTPROCESSOR_MAX_BYTES_IN_LOGQUEUES_BY_TYPE')[machine_type])
  elif config.var('RTPROCESSOR_MAX_BYTES_IN_LOGQUEUES') > 0:
    rt_max_bytes_queued = config.var('RTPROCESSOR_MAX_BYTES_IN_LOGQUEUES')
  # end if
  if rt_max_bytes_queued != None:
    args.append("--max_bytes_in_logqueues=%d" % rt_max_bytes_queued)
  # end if

  if config.var('NAMESPACE_PREFIX'):
    # TODO: hack - use INDEXER_NAMESPACE_PREFIX instead
    # to override NAMESPACE_PREFIX
    if config.var('RTSERVER_INDEX_ON_LOCAL_DISK'):
      args.append("--namespace_prefix=/bigfile/")
    else:
      args.append("--namespace_prefix=%s" % \
                  servertype.GenNamespacePrefix(config, machine_type,
                                                shard, num_shards))
  #endif namespace_prefix

  args = args + get_gfs_args(config)

  if config.var('RTSERVER_LOG_READ_SIZE'):
    args.append("--log_read_buffer_size=%d" %
                config.var('RTSERVER_LOG_READ_SIZE'))
  if config.var('RTSERVER_LOG_WRITE_SIZE'):
    args.append("--log_write_buffer_size=%d" %
                config.var('RTSERVER_LOG_WRITE_SIZE'))

  aggr_wait_time = get_scalar_or_map_value(
    config.var('RTSERVER_AGGRESSIVE_MERGE_ON_PER_TYPE_BASIS'),
    machine_type)
  if aggr_wait_time:
    args.append("--aggressive_merge_if_maps_unchanged_for_secs=%d" %
                aggr_wait_time)
  #endif
  never_aggr = get_scalar_or_map_value(
    config.var('RTSERVER_MERGES_NEVER_AGGRESSIVE'),
    machine_type)
  if never_aggr: args.append('--merges_never_aggressive')

  if machine_type in ['base_indexer', 'daily_indexer', 'rt_indexer']:
    if config.var('GENERATE_LINKS_FILESET'):
      args.append('--generate_links_fileset')

    if config.var('RTSERVER_SUPPORTS_NICE_LEVEL'):
      args = args + [
        "--rtprocessor_nice_level=%d" % config.var('RTSERVER_PROCESSOR_NICE_LEVEL'),
        "--rtcheckpointwatcher_nice_level=%d" % config.var('RTSERVER_CHECKPOINTWATCHER_NICE_LEVEL'),
        "--rtmerger_nice_level=%d" % config.var('RTSERVER_MERGER_NICE_LEVEL'),
        ]
    if config.var('INDEX_METATAGS'):
      args.append('--index_metatag_restricts')
      if config.var('ENTERPRISE'):
        args.append("--parse_allmetatags")
        args.append("--parse_metatag_value")
        args.append("--index_metatag_words")
        args.append("--attach_external_metadata")

    if config.var('RTSERVER_INDEXER_URLFP_FOR_ANCHOR_DATA_REQUEST'):
      args.append("--urlfp_for_anchor_data_request")

    if not config.var('NEWS_CRAWL') and not config.var('FROOGLE_CRAWL'):
      # no restricts yet for news or froogle
      # (except for the language restrict for news, see below)
      args = args + gen_restrict_args(config)

    if config.var('NEWS_CRAWL'):
      # in order to support international news, the language restrict must be on
      args.append("--langenc_rprefix=lang")

    args.extend(args_docshard_indexer(config, machine_type, port))

    if config.var('RTSERVER_MAX_INDEX_BYTES'):
      args.append("--max_index_bytes=%d" % config.var('RTSERVER_MAX_INDEX_BYTES'))
    # only indexers need docid levels. Others use the default value
    if config.var('RTSERVER_DOCID_LEVELS') and config.var('RTSERVER_DOCID_LEVELS') > 0:
      args.append("--num_docid_levels=%d" % config.var('RTSERVER_DOCID_LEVELS'))
    if config.var('RTSERVER_ASSIGN_DOCIDS_IN_ASCENDING_ORDER'):
      args.append("--assign_docids_in_ascending_order")

    # docid level scaling factor
    if config.var('RTSERVER_LEVEL_BUCKET_SCALE_FACTOR'):
      args.append("--level_bucket_scale_factor=%f" %
                  config.var('RTSERVER_LEVEL_BUCKET_SCALE_FACTOR'))

    if config.var('RTSERVER_MERGE_MAX_CONTENTMAP_SIZE') != None:
      args.append('--merge_max_contentmap_size=%s' %
                  prodlib.int_to_string(config.var('RTSERVER_MERGE_MAX_CONTENTMAP_SIZE')))
    #end if

    # subset docid assignment
    if config.var('DOCID_ASSIGNMENT_CONFIG_FILE'):
      args.append("--subsetindex_config_file=%s" \
                         % config.var('DOCID_ASSIGNMENT_CONFIG_FILE'))
      if config.var('DOCID_ASSIGNMENT_ALLOW_EXCEED_TARGETS'):
        args.append("--subset_allow_exceed_target")
    # end DOCID_ASSIGNMENT_CONFIG_FILE

    # generate site: for all paths ?
    if config.var('INDEX_PATH_IN_SITE'):
      args.append("--index_path_in_site")

    # For enterprise, do not index content date for daterange
    if config.var('ENTERPRISE'):
      args.append("--index_content_date=false")

    # For enterprise, retain multiple anchors connecting the same pair of docs
    if config.var('ENTERPRISE'):
      args.append("--retain_all_anchors=true")

    # see if we have the to create the restricts handler anyway
    if config.var('FORCE_RESTRICTS_HANDLER'):
      args.append("--force_restricts_handler")

    if config.var('RT_RESTRICTS_INDEX_PREFIX'):
      args.append("--restricts_prefix=%s" %
                  config.var('RT_RESTRICTS_INDEX_PREFIX'))
    if config.var('RTINDEXER_MAX_MERGE_WIDTH'):
      args.append("--max_merge_width=%d" %
                  config.var('RTINDEXER_MAX_MERGE_WIDTH'))
    if config.var('RTINDEXER_MIN_MERGE_WIDTH'):
      args.append("--min_merge_width=%d" %
                  config.var('RTINDEXER_MIN_MERGE_WIDTH'))

    # compute index level
    level = 0
    if machine_type == 'daily_indexer':
      level = 1
    elif machine_type == 'rt_indexer':
      level = 2
    # end if
    # add ports for serving.
    if config.var('RTSERVER_FOR_INDEX_SERVING').get(machine_type, 0):
      args.append("--indexserver_port=%d" %
                  (servertype.GetPortBase('index:%d' % level) + shard))
    else:
      args.append("--indexserver_port=0")
    if config.var('RTSERVER_FOR_DOC_SERVING').get(machine_type, 0):
      args.append("--docserver_port=%d" %
                (servertype.GetPortBase('doc:%d' % level) + shard))
    else:
      args.append("--docserver_port=0")
    #
    # NOTE: when the same  rtserver is running as
    #         indexer, global anchor, global link
    #       we will need to have linkserver_port.
    #       However, currently the code is not setup to support this
    #       So, disable and fix everything together
    # NOTE: if 0
    #  |
    #  v
    if 0 and config.var('RTSERVER_FOR_LINK_SERVING').get(machine_type, 0):
      args.append("--linkserver_port=%d" %
                  (servertype.GetPortBase('index:%d' % level) + shard))
    else:
      args.append("--linkserver_port=0")


    args.append("--eager_anchor_requests")

    # to customize scoring for enterprise
    if config.var('ENTERPRISE'):
      args.append("--enterprise=true")
      args.append("--index_number_ranges=true")
      args.append("--enterprise_index_date_ranges=true")
      args.append("--max_index_title_words=25")

    # Specify anchor log file pairs if using remote or local anchor processor
    if config.var('RTINDEXER_USE_ANCHOR_PROCESSOR') or \
       config.var('RTINDEXER_AS_ANCHOR_PROCESSOR'):
      log_args = rtanchor_log_args(config, machine_type, 'global_anchor',shard)
      if log_args:
        args.append('--anchor_logfiles=%s' % log_args)
    # end if config.var()
    assert (not config.var('REQUESTOR_FOR_FORWARDED_ANCHORS') or
            config.var('REQUESTOR_FOR_FORWARDED_ANCHORS') == 'base_indexer'), \
            "Bad type: %s" % config.var('REQUESTOR_FOR_FORWARDED_ANCHORS')
    # For now, we only allow rtserver to issue requests for forwarded anchors.
    # The change is temporary and we don't want to pollute urlmanager
    # code with such code.
    if config.var('REQUESTOR_FOR_FORWARDED_ANCHORS') == 'base_indexer':
      args.append("--forward_anchordata_from_dups")
      args.append("--forwarded_anchor_logfiles=%s" % (
        rtanchor_log_args(config, machine_type, 'anchorresp_merger',shard)))
    # end if
    args = args + servertype.BuildOneFlagArg(
      config,
      'RTINDEXER_COLLAPSETYPES',
      "--collapsetypes")
  # endif machine_type are indexers

  if config.var('RT_LAZY_MERGE_RATIO'):
    args.append("--lazy_merge_ratio=%s" % config.var('RT_LAZY_MERGE_RATIO'))

  if config.var('RTSERVER_LOGREADER_PROBE_MAX_DELAY').get(machine_type):
    args.append('--logreader_probe_max_delay=%d' %
                config.var('RTSERVER_LOGREADER_PROBE_MAX_DELAY').get(machine_type))
  if config.var('RTSERVER_LOGREADER_PROBE_DELAY_INCREMENT').get(machine_type):
    args.append('--logreader_probe_delay_increment=%d' %
                config.var('RTSERVER_LOGREADER_PROBE_DELAY_INCREMENT').get(machine_type))

  if config.var('RTSERVER_CLEANUP_UNNECESSARY_FILES') != None:
    args.append("--cleanup_unnecessary_files=%d" %
                config.var('RTSERVER_CLEANUP_UNNECESSARY_FILES'))

  if config.var('RTSERVER_MIN_FILE_SIZE_FOR_MERGE_RATIO'):
    args.append("--min_file_size_for_merge_ratio=%s" % (
       config.var('RTSERVER_MIN_FILE_SIZE_FOR_MERGE_RATIO')))

  if config.var('RTSERVER_MAX_OUTSTANDING_INDEX_FILES'):
    args.append("--max_outstanding_index_files=%s" % (
      config.var('RTSERVER_MAX_OUTSTANDING_INDEX_FILES')))

  if config.var('RTSERVER_RECYCLE_DELETED_DOCIDS'):
    args.append("--recycle_deleted_docids")

  mmap_budget = None
  if config.var('RTSERVER_MMAP_BUDGET_BY_TYPE').has_key(machine_type):
    mmap_budget = config.var('RTSERVER_MMAP_BUDGET_BY_TYPE')[machine_type]
  elif config.var('RTSERVER_MMAP_BUDGET'):
    mmap_budget = config.var('RTSERVER_MMAP_BUDGET')
  # end if
  if mmap_budget != None:
    args.append("--mmap_budget=%s" % (servertype.ExpandCutoff(mmap_budget)))

  if config.var('RTMASTER_STARTPOS_IF_NO_CHKPT'):
    args.append("--startpos_if_no_chkpt=%s" % (
       prodlib.int_to_string(config.var('RTMASTER_STARTPOS_IF_NO_CHKPT'))))

  if config.var('RTSERVER_ENABLE_SERVING'):
    indexing_maps = config.var('RTSERVER_INDEXING_MAPS_ALWAYS_MMAP')
    serving_maps = config.var('RTSERVER_SERVING_MAPS_ALWAYS_MMAP')
    if serving_maps and indexing_maps:
      args.append('--maps_always_mmap=%s,%s' % (serving_maps, indexing_maps))
    elif serving_maps:
      args.append('--maps_always_mmap=%s' % serving_maps)
    elif indexing_maps:
      args.append('--maps_always_mmap=%s' % indexing_maps)

    if config.var('RTSERVER_SERVING_MAPS_PRELOAD'):
      args.append('--maps_preload=%s' % (
        config.var('RTSERVER_SERVING_MAPS_PRELOAD')))

    if config.var('RTSERVER_PRELOAD_SERVING_STATE'):
      args.append('--preload_serving_state')

    if config.var('RTSERVER_PRELOAD_STARTUP_STATE'):
      args.append('--preload_startup_state')


    if config.var('RTSERVER_ALWAYS_MMAP_LEXICON'):
      args.append('--always_mmap_lexicon')

  else:
    indexing_maps = config.var('RTSERVER_INDEXING_MAPS_ALWAYS_MMAP')
    if indexing_maps:
      args.append('--maps_always_mmap=%s' % indexing_maps)

  if config.var('RTSERVER_MLOCK_FILES'):
    args.append('--mlock_files')

  if config.var('REWRITE_FILESET_EVERY'):
    args.append("--rewrite_fileset_every=%s" % (
      config.var('REWRITE_FILESET_EVERY')))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  if config.var('SORTEDMAP_ITERATOR_CHECKSUMS') != None:
    if config.var('SORTEDMAP_ITERATOR_CHECKSUMS'):
      args.append("--sortedmap_iterator_checksums")
    else:
      args.append("--nosortedmap_iterator_checksums")

  if config.var('RTSERVER_SHARDED_FILESET'):
    # Similar to rtserver's construction of a filesetname (uses index prefix)
    args.append("--filesetname=%sFILESET_rt%s_%d" %
                (servertype.GenNamespacePrefix(config, machine_type,
                                               shard, num_shards),
                 config.var('RTSERVER_INDEX_PREFIX'), shard))

  if config.var('RESTRICT_REMEMBER'):
    args.append("--remember_restricts")

  if config.var('RTSERVER_ANCHOR_RELOAD_INTERVAL_BASE').get(machine_type, None):
    args.append("--anchor_reload_interval_base=%d" %
                config.var('RTSERVER_ANCHOR_RELOAD_INTERVAL_BASE').get(machine_type))

  if config.var('RTSERVER_NUM_ANCHORS_TO_RELOAD_BASE'):
    args.append("--num_anchors_to_reload_base=%d" %
                config.var('RTSERVER_NUM_ANCHORS_TO_RELOAD_BASE'))

  if config.var('RTSERVER_MAX_ANCHOR_RELOAD_ITER'):
    args.append("--max_anchor_reload_iter=%d" %
                config.var('RTSERVER_MAX_ANCHOR_RELOAD_ITER'))

  if config.var('RTSERVER_GARBAGE_COLLECT_LOGS'):
    args.append("--garbage_collect_logs")

  if config.var('RTSERVER_NOALLOW_DISCARDS_AFTER_CURRENT_EPOCH'):
    args.append("--noallow_discards_after_current_epoch")

  if config.var('RTSERVER_ALWAYS_KEEP_AT_LEAST_NUM_EPOCHS'):
    args.append("--always_keep_at_least_num_epochs=%d" % \
                config.var('RTSERVER_ALWAYS_KEEP_AT_LEAST_NUM_EPOCHS'))

  if config.var('RTINDEXER_COMPRESS_COMMON_MAP_DELETIONS'):
    args.append("--compress_common_map_deletions")

  if config.var('ENABLE_FIELD_SEARCH'):
    args.append("--fieldsearch_enabled")

  if config.var('ENABLE_WORKSCHEDULER_SORTBYDATE'):
    args.append("--learn_dates")
    args.append("--extractdate_config=%s" % config.var('DATEPATTERNS') )
    args.append("--use_datestatsfiles")
    args.append("--extractdate_outfile=%sdateout_%02d" % \
                ( config.var('GLOBAL_NAMESPACE_PREFIX'), shard) )

  if machine_type in config.var('RTSERVER_INDEX_NUMBER_RANGES'):
    args.append("--index_number_ranges")

  if config.var('ENTERPRISE'):
    args.append("--googletags=true")
    # in enterprise we do not keep checksums in .attr files, since this
    # only adds a point of failure. not much to do if file is corrupted anyway.
    args.append("--keep_checksum_for_filesets=false")

  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    # in enterprise, there is nothing to be done for corrupted checkpoints.
    # keeping checksum in attribute file adds a point of failure.
    args.append("--keep_checksum_for_checkpoints=false")

  # TODO(tianyu): remove the following temporary flag for SuperGSA specific merge
  args.append("--supergsa_merge")

  return args


# not a "traditional" prefix. Returns something like
#   /gfs/bart/apr02crawl/dailytest1/global-anchor
# or
#   /gfs/bart/apr02crawl/global-anchor
# is used to create names for anchor logfiles, such as
#   /gfs/bart/apr02crawl/dailytest1/daily-indexer-001of009/global-anchor000-of-020/response-log
#
def gen_anchorlogs_prefix(config, src_machine_type, anchor_srv_type,
                          shard, num_shards):
  """
  Generate prefix for anchor_logfiles. If shard is -1,
  a place holder: %03d will be left in anchor_log_string for filling
  in shard info later.
  """
  # replace '_' in anchor_srv_type with '-' to generate anchor_srv_id
  # NOTE: there is really no benefit of doing that other than for
  # backward compatibility
  anchor_srv_id = string.replace(anchor_srv_type, '_', '-')
  if not config.var('GFS_ALIASES'):
    if src_machine_type != None:
      return "%s%s-" % \
             (config.var('NAMESPACE_PREFIX'),
              servertype.GenRTIdentifier(anchor_srv_type, shard, num_shards))
    else:
      return "%s%s" % (anchor_request_log_prefix(config, anchor_srv_type),
                       anchor_srv_id)

  else:
    if src_machine_type != None:
      return "%s%s/%s" % (config.var('NAMESPACE_PREFIX'),
                          servertype.GenRTIdentifier(src_machine_type, shard,
                                                     num_shards),
                          anchor_srv_id)
    else:
      return "%s%s" % (anchor_request_log_prefix(config, anchor_srv_type),
                       anchor_srv_id)

def rtanchor_log_args(config, machine_type, anchor_srv_type,
                      shard, id_string=''):
  """
  Generate values for anchor_logfiles arg. If shard is -1,
  a place holder: %03d will be left in anchor_log_string for filling
  in shard info later.
  """
  reqlog_prefix = gen_anchorlogs_prefix(config, None, anchor_srv_type,
                                        None, None)
  resplog_prefix = gen_anchorlogs_prefix(config,
    machine_type, anchor_srv_type, shard, config.GetNumShards(machine_type))
  num_link_shards = config.GetNumShards(anchor_srv_type)
  if (num_link_shards == 0):
    num_link_shards = config.GetNumShards(get_global_link_machine_type(config))

  # request and response logs reside possibly in different places:
  # request logs are supposed to be in the global namespace prefix, so that
  # the anchor processors can pick 'em up.
  #
  # Response logs will be in the local namespace of the indexer that uses it.

  anchor_log_string = '%s:%s:%s:%s:%s' % (
    reqlog_prefix, "%s-request-log%s" % (machine_type, id_string),
    resplog_prefix, "response-log",
    num_link_shards
    )

  if num_link_shards == 0:
    return ""
  else:
    return anchor_log_string

def sharded_rtanchor_log_args(config, machine_type, id_string=''):
  # -1 will cause rtanchor_log_args() to leave a '%03d' in log_args.
  # This is a place holder for requestor shard info to be filled in later
  log_args = rtanchor_log_args(config, machine_type, 'global_anchor',
                               -1, id_string)
  assert log_args
  # append indexer shard info
  log_args = log_args + ":%d" % config.GetNumShards(machine_type)
  return log_args

#------------------------------------------------------------------------------
# BASE_INDEXER
#------------------------------------------------------------------------------

def restart_base_indexer(config, host, port):
  args = args_common_indexer(config, 'base_indexer', port)
  shard = servertype.GetPortShard(port)

  args.append("--nologging")  # Don't want bigfile open/close messages.

  # TODO: remove this when the dependency between the base_indexer and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  if config.var('RTSERVER_ANCHOR_MERGED_ANCHORS_MEM_USAGE_CUTOFF'):
    args.append("--merged_anchors_mem_usage_cutoff=%d" %
                config.var('RTSERVER_ANCHOR_MERGED_ANCHORS_MEM_USAGE_CUTOFF'))

  # expected docs to crawl
  if config.var('RTSERVER_BASE_EXPECTED_DOCS'):
    args.append("--docs_to_crawl=%s" % config.var('RTSERVER_BASE_EXPECTED_DOCS'))
  return restart_wrapper("base_indexer", config, host, port, args)

servertype.RegisterRestartFunction('base_indexer', restart_base_indexer)

#-------------------------------------------------------------------------------
# RT_INDEXER
#-------------------------------------------------------------------------------

def restart_rt_indexer(config, host, port):
  args = args_common_indexer(config, 'rt_indexer', port)
  shard = servertype.GetPortShard(port)

  # expected docs to crawl
  if config.var('RTSERVER_RT_EXPECTED_DOCS'):
    args.append("--docs_to_crawl=%s" % config.var('RTSERVER_RT_EXPECTED_DOCS'))

  return restart_wrapper("rt_indexer", config, host, port, args)

servertype.RegisterRestartFunction('rt_indexer', restart_rt_indexer)

#-------------------------------------------------------------------------------
# URLHISTORY_PROCESSOR
#-------------------------------------------------------------------------------

def restart_urlhistory_processor(config, host, port):
  args = args_common_indexer(config, 'urlhistory_processor', port)

  args.append("--nologging")  # Don't want bigfile open/close messages.

  # turn off index/doc/link serving
  args.append("--indexserver_port=0")
  args.append("--docserver_port=0")
  args.append("--linkserver_port=0")

  # if started in serving_only mode, we don't merge and we don't process_logs
  if config.var('URLHISTORY_PROCESSOR_QUERY_ONLY'):
    args.append("--subordinate")
    args.append("--nomerger")
  else:
    # We want to merge wider -- override default set earlier
    args.append("--max_merge_width=32")

    # we want to ignore "RemoveEpochBoundary" markers until merge bugs
    # have been fixed
    args.append("--ignore_remove_epoch_boundary")
  # end if

  # TODO: remove this when the dependency between the
  # urlhistory_processor and chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  if config.var("URLHISTORY_SERVE_LATEST_EPOCHS"):
    args.append("--serve_latest_epochs=%d" %
                config.var("URLHISTORY_SERVE_LATEST_EPOCHS"))
  # end if
  return restart_wrapper("urlhistory_processor", config, host, port, args)

servertype.RegisterRestartFunction('urlhistory_processor',
                                   restart_urlhistory_processor)

#------------------------------------------------------------------------------
# OLD URLSCHEDULER
#------------------------------------------------------------------------------

def args_urlscheduler(config, port):
  shard_num  = servertype.GetPortShard(port)
  args = args_crawl_server_common(config, 'urlscheduler', port)

  urlscheduler_urlschedule_prefix = config.var(
    'URLSCHEDULER_URLSCHEDULE_PREFIX')
  if config.var('URLMANAGER_URLSCHEDULER_LOG_PREFIX'):
    urlscheduler_urlschedule_prefix = config.var(
      'URLMANAGER_URLSCHEDULER_LOG_PREFIX')
  args.extend([
    "--nologging",     # we don't really care that we've opened another bigfile
    '--num_urlmanager_shards=%s' % config.GetNumShards('urlmanager'),
    '--num_urlscheduler_shards=%s' % config.GetNumShards('urlscheduler'),
    '--urlscheduler_shard=%s' % shard_num,
    '--url_limit=%s' %  config.var('URLSCHEDULER_URL_LIMIT'),
    '--crawl_limit=%s' % config.var('URLSCHEDULER_CRAWL_LIMIT'),
    '--num_samples=%s' % config.var('URLSCHEDULER_NUM_SAMPLES'),
    '--num_examples=%s' %config.var('URLSCHEDULER_NUM_EXAMPLES'),
    '--serverizer_checkpoint=%sserverizer_urlscheduler_chkpt-%s' % (
       urlscheduler_urlschedule_prefix, shard_num),
    '--checkpoint_filename=%surlscheduler_chkpt-%s' % (
       urlscheduler_urlschedule_prefix, shard_num),
    '--namespace_prefix=%s' % config.var('URLSCHEDULER_NAMESPACE_PREFIX'),
    '--urlschedule_prefix=%s' % config.var('URLMANAGER_URLSCHEDULER_LOG_PREFIX'),
    '--homepage_boostfactor=%s' % config.var('URLSCHEDULER_HOMEPAGE_BOOST'),
    '--print_statistics',
    ])

  if config.var('URLSCHEDULER_LIMIT_EXCEPTIONS'):
    args = args.append('--limit_exceptions=%s' %
                       config.var('URLSCHEDULER_LIMIT_EXCEPTIONS'))

  if config.var('URLSCHEDULER_PRINT_STATS'):
    args.append('--print_statistics=true')

  if config.var('RTINDEXER_AS_URLHISTORY_PROCESSOR'):
    args.append('--use_base_indexer=true')
    typ = 'base_indexer'
  else:
    typ = 'urlhistory_processor'
  shardinfo, backends = servertype.GetShardInfoBackends(config, typ,
                                                        0, 'http',1)
  args.append("--backends=%s" % backends.AsString())
  args.append("--shardinfo=%s" % shardinfo.AsString())
  args = args + get_gfs_args(config)

  if config.var('URLSCHEDULER_ROBOT_BACKOFF'):
    args.append('--robot_backoff=%s' %
                config.var('URLSCHEDULER_ROBOT_BACKOFF'))

  if config.var('URLSCHEDULER_ERROR_BACKOFF'):
    args.append('--error_backoff=%s' %
                config.var('URLSCHEDULER_ERROR_BACKOFF'))

  if config.var('URLSCHEDULER_NOCONTENT_BACKOFF'):
    args.append('--nocontent_backoff=%s' % \
                config.var('URLSCHEDULER_NOCONTENT_BACKOFF'))

  if config.var('URLSCHEDULER_OLD_DATA_SCALE'):
    args.append('--old_data_scale=%s' % \
                config.var('URLSCHEDULER_OLD_DATA_SCALE'))

  if config.var('GOODURLS'):
    args.append('--goodurls=%s' % config.var('GOODURLS'))

  if config.var('BADURLS'):
    args.append('--badurls=%s' % config.var('BADURLS'))

  if config.var('URLSCHEDULER_SERVERIZE'):
    args.append('--port=%d' % port)
    args.append('--move_schedule=true')
    args.append('--delete_checkpoint=true')
    args.append('--serverizer_checkpoint='\
                '%surlscheduler_serverizer_ckpt-%d' % (
      config.var('NAMESPACE_PREFIX'), shard_num))

    if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
      args.append("--trusted_clients=%s" %
                  string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  if config.var('URLSCHEDULER_MOVED_CHECKPOINT_DIR'):
    args.append('--moved_checkpoint_dir=%s' %
                config.var('URLSCHEDULER_MOVED_CHECKPOINT_DIR'))

  if config.var('DUPHOSTS'):
    args.append('--duphosts=%s' % config.var('DUPHOSTS'))

  if config.var('URLSCHEDULER_ARCHIVE_URLS'):
    args.append('--archiveurls=%s' % \
                config.var('URLSCHEDULER_ARCHIVE_URLS'))
  if config.var('URLMANAGER_REFRESH_URLS'):
    args.append('--refresh_urls=%s' % \
                config.var('URLMANAGER_REFRESH_URLS'))
  if config.var('URLMANAGER_REFRESHURL_LIMIT'):
    args.append('--refreshurl_urllimit=%s' % \
                config.var('URLMANAGER_REFRESHURL_LIMIT'))
  if config.var('URLMANAGER_REFRESHCLASS_PERIODS'):
    args.append('--refreshclass_periods=%s' % \
                config.var('URLMANAGER_REFRESHCLASS_PERIODS'))
  if config.var('URLMANAGER_REFRESHCLASS_DEFAULT'):
    args.append('--default_refresh_class=%s' % \
                config.var('URLMANAGER_REFRESHCLASS_DEFAULT'))

  if config.var('URLSCHEDULER_MIN_CRAWL_DELTA'):
    args.append('--min_crawl_delta=%d' %
                config.var('URLSCHEDULER_MIN_CRAWL_DELTA'))
  if config.var('URLSCHEDULER_MAX_CRAWL_DELTA'):
    args.append('--max_crawl_delta=%d' %
                config.var('URLSCHEDULER_MAX_CRAWL_DELTA'))
  if config.var('URLSCHEDULER_MUST_RECRAWL_AGE'):
    args.append('--must_recrawl_age=%d' %
                config.var('URLSCHEDULER_MUST_RECRAWL_AGE'))


  if config.var('URLSCHEDULER_USE_IMS_WHEN_IN_REPOSITORY'):
    args.append('--use_ims_when_in_repository')
  if config.var('URLSCHEDULER_OLD_REPOSITORY_AGE_IN_DAYS'):
    args.append('--old_repository_age_in_days=%d' %
                config.var('URLSCHEDULER_OLD_REPOSITORY_AGE_IN_DAYS'))
  if config.var('URLSCHEDULER_RANDOM_GENERATOR_SEED'):
    args.append('--random_generator_seed=%d' %
                config.var('URLSCHEDULER_RANDOM_GENERATOR_SEED'))

  return args


# Enterprise specific crawling component.
def args_crawlscheduler(config, port):
  args = args_crawl_server_common(config, 'urlscheduler', port)
  args.extend([
    # currently we only use crawlscheduler's batch mode.
    #'--trigger_log=%s' % \
    #servertype.GenLogfileBasename("/bigfile/enterprise_crawlscheduler",
    #                              0, 1, 0),
    "--nologging",     # we don't really care that we've opened another bigfile
    '--num_crawlmanager_shards=%s' % config.GetNumShards('urlmanager'),
    '--num_crawlscheduler_shards=%s' % config.GetNumShards('urlscheduler'),
    '--crawlscheduler_shard=%s' %  servertype.GetPortShard(port),
    '--namespace_prefix=%s' % config.var('URLSCHEDULER_NAMESPACE_PREFIX')
    ])

  # output log from crawlscheduler to crawlmanager:
  if config.var('GFS_ALIASES'):
    # on clusters we use GFS, which handles multiple writers to the same file.
    # so there is a single input log for every crawlmanager.
    schedule_log_prefix = ("/gfs/ent/%s" %
                           config.var('URLMANAGER_URLSCHEDULER_LOG_PREFIX'))
  else:
    # enterprise oneway configuration:
    schedule_log_prefix = "/bigfile/changeintervals"
  args.append('--schedule_log_prefix=%s' % schedule_log_prefix)

  # URL history servers information:
  shardinfo, backends = servertype.GetShardInfoBackends(config,
                                                        'urlhistory_processor',
                                                        0, 'http',1)
  args.append("--backends=%s" % backends.AsString())
  args.append("--shardinfo=%s" % shardinfo.AsString())
  args = args + get_gfs_args(config)

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # TODO: remove this when the dependency between the crawlscheduler
  # and chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  return args

# Babysitter thinks that crawlscheduler is called urlscheduler (the legacy
# google.com scheduler). So use args_crawlscheuduler() to make
# restart_urlscheduler()
def restart_urlscheduler(config, host, port):
  if config.var('ENTERPRISE_CRAWL'):
    # use enterprise specific crawling components. for now this
    # does not work on clusters.
    args = args_crawlscheduler(config, port)
  else:
    args = args_urlscheduler(config, port)

  # TODO: remove this when the dependency between the urlscheduler and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  return restart_wrapper('urlscheduler', config, host, port, args)

servertype.RegisterRestartFunction('urlscheduler', restart_urlscheduler)

#-------------------------------------------------------------------------------
# WEB
#-------------------------------------------------------------------------------

def args_rtweb(config, port):
  args = [
    "-port=%d" % (port),
    "-use_64bit_docids",
    "-cjk_config=%s" % config.var('CJKCONFIGDIR'),
    "-snippetnum=3",
    "-snippetline=80",
    "-snippetlength=160",
    "-titleinhash=0",
    "-approxdups=1",
    "-translation=1",
    "-writeresultlog",
    "-resultloginterval=10",
    "-writeresultstourllog",
    "-dupplusconns=6",
    "-chinesenamefix=1",
    "-use_catrestrict_byname",
    "-use_docid_tiebreaker=false",
    ]
  num_mixers = config.GetNumShards('mixer')
  if num_mixers > 0:
    # talk to mixers directly
    indexer_port = servertype.GetPortBase('index:0')
    for host in config.GetServerHosts('mixer'):
      args.append('@%s:%d' % (host, indexer_port))
  else:
    # no mixers available. Talk to the doc and index backends directly
    rtlevels = ['base_indexer', 'daily_indexer', 'rt_indexer']
    for level in xrange(len(rtlevels)):
      indexer_type = rtlevels[level]
      num_index_shards = config.GetNumShards(indexer_type)
      if not num_index_shards:  # ignore empty servers
        continue

      start_indexer_port = servertype.GetPortBase('index:%d' % level)
      start_doc_port = servertype.GetPortBase('doc:%d' % level)
      for host, port in config.GetServerHostPorts(indexer_type):
        shard = servertype.GetPortShard(port)
        args.append('%s:%d' % (host, start_indexer_port + shard))
        args.append('%s:%d' % (host, start_doc_port + shard))

  return args

def restart_web(config, host, port):
  if config.var('RTSERVER_LOGS'): # only active in RT mode
    args = args_rtweb(config, port)
    return restart_wrapper("web", config, host, port, args, google2=0)
  else:
    return ""

#-------------------------------------------------------------------------------
# FEEDERGATE
#-------------------------------------------------------------------------------
def args_feedergate(config, port):

  num_feeder_shards = config.GetNumShards("feeder")

  if num_feeder_shards < 1:
    num_feeder_shards = 1

  args = [
    "--port=%d" % servertype.GetServingPort(port),
    "--datadir=%s" % config.var('DATADIR'),
    "--num_feeder_shards=%d" % num_feeder_shards,
    "--nologging"     # we don't really care that we've opened another bigfile
    ]

  if config.var('FEEDS_DIR'):
    args.append("--feeds_dir=%s" % config.var('FEEDS_DIR'))

  if config.var("FEED_CONTENTFEEDS_LOG_INFO_PREFIXES"):
    loginfo = []
    for k, v in config.var("FEED_CONTENTFEEDS_LOG_INFO_PREFIXES").items():
      loginfo.append("%s:%s" % (k, v))
    args.append("--contentfeeds_log_info=%s" % string.join(loginfo, ","))
  if config.var("FEED_URLFEEDS_LOG_PREFIX"):
    args.append("--urlfeeds_log_prefix=%s" % (
      config.var("FEED_URLFEEDS_LOG_PREFIX")))

  if config.var('FEED_URLS'):
    args.append("--feededurls=%s" % config.var('FEED_URLS'))
  if config.var('GOODURLS'):
    args.append("--goodurls=%s" % config.var('GOODURLS'))
  if config.var('BADURLS'):
    args.append("--badurls=%s" % config.var('BADURLS'))
  if config.var('FEEDER_GOODIPS'):
    args.append("--goodips=%s" % config.var('FEEDER_GOODIPS'))

  if config.var('FEED_MAX_LOG_DIR_WIDTH'):
    args.append("--max_log_dir_width=%s" % config.var('FEED_MAX_LOG_DIR_WIDTH'))
  if config.var('FEED_MAX_LOG_DIR_DEPTH'):
    args.append("--max_log_dir_depth=%s" % config.var('FEED_MAX_LOG_DIR_DEPTH'))

  args = args + get_gfs_args(config)

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # XMLFeed will only be acceptible from these IP/Masks.
  trusted_clients = ""
  if config.var('FEEDER_TRUSTED_CLIENTS'):
    trusted_clients = string.join(config.var('FEEDER_TRUSTED_CLIENTS'), ',')
  if config.var('FEEDER_CONNECTOR_MANAGER_TRUSTED_CLIENTS'):
    cm_trusted_clients = string.join(config.var('FEEDER_CONNECTOR_MANAGER_TRUSTED_CLIENTS'), ',')
    if len(trusted_clients) == 0:
      trusted_clients = cm_trusted_clients
    else:
      if trusted_clients != "all":
        trusted_clients = "%s,%s" % (trusted_clients, cm_trusted_clients)

  if len(trusted_clients) > 0:
    args.append("--feeder_trusted_clients=%s" % trusted_clients)

  # TODO: remove this when the dependency between the feedergate and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  return args

def restart_feedergate(config, host, port):
  args = args_feedergate(config, port)
  return restart_wrapper('feedergate', config, host, port, args)

servertype.RegisterRestartFunction('feedergate', restart_feedergate)

#-------------------------------------------------------------------------------
# FEEDER
#-------------------------------------------------------------------------------
def feeder_log_info_arg(config, host, port):
  components = []
  # make sure we have at least one of the document processors
  if (config.var('NEED_RTSERVER') and
     config.GetNumShards('base_indexer') == 0 and
     config.GetNumShards('daily_indexer') == 0 and
     config.GetNumShards('rt_indexer') == 0):
     print('At least one of base_indexer, daily_indexer'
           ' and rt_indexer machines  must be specified')
     sys.exit(1)

  if config.GetNumShards('urlmanager') == 0:
    print('We must have at least one urlmanager server')
    sys.exit(1)

  # For feeder, must have seperate logs even for GFS
  # if RTLOG_FEEDER_SUFFIX are set,
  # allow feeder to talk to rtserver through rtlogs written by feeder
  if config.var('RTLOG_FEEDER_SUFFIX'):
    # make sure RTSERVER_LOGS is defined
    if not config.var('RTSERVER_LOGS'):
      print 'Need RTSERVER_LOGS for indexer logfile names'
      sys.exit(1)
    # end if
    # For feeder, must have seperate logs even for GFS
    sfx = config.var('RTLOG_FEEDER_SUFFIX')
    for indexer_type in ('base_indexer', 'rt_indexer', 'urlhistory_processor',
                         'daily_indexer', 'urlmanager', 'tracker_gatherer'):
      output_log = shardset_output_log_name(config, indexer_type, host , port,
                                            config.GetNumShards(indexer_type),
                                            sfx)
      if output_log:
        components.append(output_log)
    # end for
  # end if

  return string.join(components, ',')


def args_feeder(config, host, port):
  shard_num = servertype.GetPortShard(port)
  num_feeder_shards = config.GetNumShards("feeder")

  args = [
    "--port=%d" % port,
    "--datadir=%s" % config.var('DATADIR'),
    "--shard=%d" % shard_num,
    "--num_feeder_shards=%d" % num_feeder_shards,
    "--acks_log_prefix=%s" % config.var('RTSERVER_LOGS')['feeder'],
    "--nologging"     # we don't really care that we've opened another bigfile
    ]

  log_info_arg = feeder_log_info_arg(config, host, port)
  args.append('--log_info=%s' % log_info_arg)

  # Location for storing feed statuses.
  if config.var("FEED_STATUS_DIR"):
    args.append("--feedstatus_dir=%s" % config.var("FEED_STATUS_DIR"));

  # multiple datasource maps for clusters.
  args.append('--datasource_map=%sfeed_datasource_map%03d-of-%03d' %
        (config.var('NAMESPACE_PREFIX'), shard_num, num_feeder_shards))

  # good/bad url patterns
  if config.var('GOODURLS'):
    args.append("--goodurls=%s" % config.var('GOODURLS'))
  if config.var('BADURLS'):
    args.append("--badurls=%s" % config.var('BADURLS'))

  # dtd for validating xml feeds:
  if config.var('FEED_DTD'):
    args.append("--dtd=%s" % config.var('FEED_DTD'))

  localized = IsServerLocalized(config, 'feeder')
  args = args + GetUrlCanonicalizationArgs(config, localized)

  backends_list = []
  shardinfo_list = []

  if config.GetNumShards('contentfilter') > 0:
    (shardinfo, backends) = servertype.GetShardInfoBackends(
      config, 'contentfilter', 0, 'google',
      config.var('FEEDER_CONTENTFILTER_CONNECTIONS'))
    if backends.HasBackEnds():
      backends_list.append(backends.AsString())
      shardinfo_list.append(shardinfo.AsString())

  if config.GetNumShards('urlmanager') > 0:
    (shardinfo, backends) = servertype.GetShardInfoBackends(
      config, 'urlmanager', 0, 'google', 1)
    if backends.HasBackEnds():
      backends_list.append(backends.AsString())
      shardinfo_list.append(shardinfo.AsString())

  if backends_list:
    args.append("--backends=%s" % string.join(backends_list, ','))
    args.append("--shardinfo=%s" % string.join(shardinfo_list, ','))

  if config.var("FEED_CONTENTFEEDS_LOG_INFO_PREFIXES"):
    loginfo = []
    for k, v in config.var("FEED_CONTENTFEEDS_LOG_INFO_PREFIXES").items():
      gc = config.var("FEED_CONTENTFEEDS_LOG_INFO_GC").get(k, 0)
      t = config.var("FEED_CONTENTFEEDS_LOG_INFO_TYPE").get(k, 0)
      loginfo.append("%s:%s:%s:%s" % (k, v, gc, t))

    args.append("--contentfeeds_log_info=%s" % string.join(loginfo, ","))
  if config.var("FEED_URLFEEDS_LOG_PREFIX"):
    args.append("--urlfeeds_log_prefix=%s" % (
      config.var("FEED_URLFEEDS_LOG_PREFIX")))

  if config.var("FEED_URLFEEDS_LOG_COLLECT"):
    args.append("--urlfeeds_log_collect")

  if config.var("HTTP_HEADER_TIME_FORMAT"):
    args.append("--http_header_time_format=%s"
                % config.var('HTTP_HEADER_TIME_FORMAT'))
  if config.var("FEEDER_CONTENTFILTER_DOC_TIMEOUT"):
    args.append("--contentfilter_doc_timeout=%d" % (
      config.var("FEEDER_CONTENTFILTER_DOC_TIMEOUT")))
  if config.var("FEED_LEVEL") != None:
    args.append("--feed_level=%d" % ( config.var("FEED_LEVEL") ))
  if config.var("FEED_SEGMENT") != None:
    args.append("--feed_segment=%d" % ( config.var("FEED_SEGMENT") ))
  if config.var("FEEDER_CONTENTFILTER_BACKOFF"):
    args.append("--contentfilter_initial_backoff_ms=%s" % (
      config.var("FEEDER_CONTENTFILTER_BACKOFF")))
  if config.var("FEEDER_CONTENTFILTER_MAX_BACKOFF"):
    args.append("--contentfilter_max_backoff_ms=%s" % (
      config.var("FEEDER_CONTENTFILTER_MAX_BACKOFF")))
  if config.var("FEEDER_COMMAND_BUFFERSIZE"):
    args.append("--feedcommand_buffersize=%s" % (
                config.var("FEEDER_COMMAND_BUFFERSIZE")))
  if config.var("FEEDER_NUM_CHECKPOINTS"):
    args.append("--num_checkpoints=%s" % (
      config.var("FEEDER_NUM_CHECKPOINTS")))
  if config.var("FEEDER_CHECKPOINT_INTERVAL"):
    args.append("--checkpoint_interval=%s" % (
      config.var("FEEDER_CHECKPOINT_INTERVAL")))

  if config.var('FEEDARCHIVER_CONFIG_FILE'):
    args.append("--feedarchiver_config_file=%s"
                % config.var('FEEDARCHIVER_CONFIG_FILE'))

  if config.var("FEEDER_LOG_INFO_PREFIXES"):
    loginfo = []
    for k, v in config.var("FEEDER_LOG_INFO_PREFIXES").items():
      # TODO: get num shards based on server type for froogle_delete_log
      loginfo.append("%s:%s" % (k, v))
    args.append("--log_info=%s" % string.join(loginfo, ","))

  if config.var("FROOGLEFEEDSREADER_LOG_TO_FILE"):
    args.append("--frooglefeedsreader_log_to_file=%s"
                % config.var("FROOGLEFEEDSREADER_LOG_TO_FILE"))

  if config.var("FROOGLEFEEDSREADER_LOG_TO_FILE_MAX_ERRORS"):
    args.append("--frooglefeedsreader_log_to_file_max_errors=%d"
                % config.var("FROOGLEFEEDSREADER_LOG_TO_FILE_MAX_ERRORS"))

  args = args + get_gfs_args(config)
  if config.var('NAMESPACE_PREFIX'):
    args.append("--namespace_prefix=%s" % config.var('NAMESPACE_PREFIX'))

  if config.var('HTTPSERVER_TRUSTED_CLIENTS'):
    args.append("--trusted_clients=%s" %
                string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))

  # TODO: CL 6977124 removed the old basistech library which used to provide
  # the --cjk_config and --bt_version flags. We remove the flags below in
  # order to allow feeder to start. However, we need to investigate more on
  # how to add cjk segmenter back to feeder.

  # if config.var('CJKCONFIGDIR'):
  #   args.append("--cjk_config=%s" % config.var('CJKCONFIGDIR'))

  # if config.var('BTVERSION'):
  #   args.append("--bt_version=%s" % config.var('BTVERSION'))

  # Archive crawling
  if config.var('RT_EPOCH') != None:
    args.append("--archive_epoch=%d" % config.var('RT_EPOCH'))

  # TODO: this is temporary till attr file replication is fixed
  if not config.var('CHECKSUM_CHECKPOINT_FILES'):
    args.append("--keep_checksum_for_checkpoints=false")

  # TODO: remove this when the dependency between the feeder and
  # chubby is broken.
  args.extend(LOCK_SERVICE_FLAGS)

  return args

def restart_feeder(config, host, port):
  args = args_feeder(config, host, port)
  return restart_wrapper('feeder', config, host, port, args)

servertype.RegisterRestartFunction('feeder', restart_feeder)


#------------------------------------------------------------------------------
# SUPERGSA_MAIN  (only used on SuperGSA)
#------------------------------------------------------------------------------

def restart_supergsa_main_server(config, host, port):
  set = config.GetServerManager().Set('supergsa_main')

  # Choose the first host & port since bot does it that way.
  fsgw_host, fsgw_port = config.GetServerHostPorts('fsgw')[0];
  fsgw = "%s:%s" %(socket.gethostbyname(fsgw_host), fsgw_port)

  # construct a list of the filetypes we want to handle
  filetypes = config.var_copy('BOT_FILE_TYPES_TO_ACCEPT')
  if config.var('CRAWL_IMAGE'):
    filetypes.append('IMAGE')

  contentfilter_mimetypes = (
    ["text/plain", "google/empty", "google/error", "google/other"] +
    GetMimeTypesFromFileTypes(filetypes, GoogleLocalMime) +
    GetMimeTypesFromFileTypes(filetypes, AcceptMime)
    )

  if config.var('CRAWL_HTML'):
    contentfilter_mimetypes.append("text/html")
  if config.var('CRAWL_XML'):
    contentfilter_mimetypes.append("text/xml")
    contentfilter_mimetypes.append("application/xml")
    contentfilter_mimetypes.append("application/atom+xml")
    contentfilter_mimetypes.append("application/rdf+xml")
    contentfilter_mimetypes.append("application/rss+xml")
    contentfilter_mimetypes.append("application/xhtml+xml")

  contentfilter_mimetypes_string = string.join(contentfilter_mimetypes, ",")

  # TODO(moberoi): Set default values in binary where possible and
  # remove settings from here.
  # TODO(moberoi): Work with the team to make sure flags are correct for
  # indexer and other components.
  args = [
      "--port=%d" % servertype.GetServingPort(port),
      "--datadir=%s" % config.var('DATADIR'),
      "--nologging",  # we don't really care that we've opened another bigfile
      "--namespace_prefix=%s" % config.var('NAMESPACE_PREFIX'),

      # Relevent flags from crawlmanager.
      "--starturls=%s" % config.var('STARTURLS'),
      "--goodurls=%s" % config.var('GOODURLS'),
      "--badurls=%s"  % config.var('BADURLS'),
      "--crawl_frequently_urls=%s" % config.var('URLMANAGER_REFRESH_URLS'),
      "--crawl_seldom_urls=%s" % config.var('URLSCHEDULER_ARCHIVE_URLS'),
      "--duphosts=%s" % config.var('DUPHOSTS'),
      "--url_canonicalize_to_punycode",
      # TODO(moberoi): supergsa_main needs to support these 2 flags.
      # "--crawl_frequently_change_interval=%d" % (2 * 24 * 3600), # once a day.
      # "--crawl_seldom_change_interval=%d" % (180 * 24 * 3600)  # ~3 months.


      # Relevent flags from urlserver.
      "--disable_infinitespace_check",
      "--hostloadfile=%s" % config.var('HOSTLOADS'),

      # Relevent flags from bot.
      "--httpdocfetcher_follow_off_domain_redirects",
      "--testurl=%s" % config.var('BOT_TESTURLS'),
      "--urltest_failure_fraction=%f" % 0.9,
      "--cookierulespath=%s" % config.var('COOKIE_RULES'),
      "--sso_pattern_config=%s" % config.var('SSO_PATTERN_CONFIG'),
      "--filesystem_proxy_url=http://%s/getFile" % fsgw,
      # TODO(moberoi): Are we going to use these mem args (I doubt it)?
      # --absolute_max_memory
      # --absolute_goal_memory
      # --fraction_max_memory
      # --fraction_goal_memory
      "--httptimeout=%d" % config.var('BOT_HTTP_TIMEOUT'),
      "--max_filetype_len=%d" % config.var('BOT_MAXFILETYPE_DOWNLOAD'),
      # This assumes BOT_MAXFILETYPE_DOWNLOAD is the biggest document
      # we are willing to pick up. This is ok for forseeeable future.
      # TODO: enforce this constraint.
      "--max_data_accepted_by_httpclientconn=%d" %
      config.var('BOT_MAXFILETYPE_DOWNLOAD'),
      "--httpclientconn_max_uncompress_bytes_per_response=%d" %
      config.var('BOT_MAXFILETYPE_DOWNLOAD'),
      "--allowboguscontentlength",
      "--crawlhttps=true",
      "--http_accept_mimetypes=%s" % "text/html,text/plain,application/*",
      "--https_accept_mimetypes=%s" % "text/html,text/plain,application/*",
      "--accept_gzip=true",
      "--filters=%s" % contentfilter_mimetypes_string,
      "--exclude_private_networks=false",
      "--proxy_config=%s" % config.var('PROXY_CONFIG'),
      "--crawl_secure",
      "--crawl_userpasswd_config=%s" % config.var('CRAWL_USERPASSWD_CONFIG'),
      # useragent and useragent_to_send are same for us.
      "--useragent_to_send=%s" % config.var('USER_AGENT_TO_SEND'),
      "--useragent=%s" % config.var('USER_AGENT_TO_SEND'),
      "--useragent_comment=%s" % config.var('USER_AGENT_COMMENT'),
#      "--useragent_email=%s" % config.var('USER_AGENT_EMAIL'),
      "--maxhttplen=%d" % config.var('BOT_MAXHTTPREQ_SIZE'),
      "--dns_count_expiration=%d" % config.var('BOT_DNS_PAGES_EXPIRATION'),
      # NOTE: CL 6410569 made this change to respect DNS TTL. Should we now
      # remove TODOs from hostinfo.cc ?
      "--use_ares",  # respect DNS TTL? but =false cause FATAL crash !!!
      "--robots_count_expiration=%d" %
      config.var('BOT_ROBOTS_PAGES_EXPIRATION'),
      "--dont_send_ims_header_patterns_file=%s" %
      config.var('URLS_REMOTE_FETCH_ONLY'),
      "--robots_expiration=%d" % config.var('BOT_ROBOTS_EXPIRATION'),
      "--dns_expiration=%d" % config.var('BOT_DNS_EXPIRATION'),
      # TODO(moberoi): supergsa_main may need to support this.
      # Low priority, but a good idea.
      #'--unreachable_host_delay_in_ms=%d' %
      #config.var('UNREACHABLE_HOST_DELAY_IN_MS'),
      "--exclude_ipandmasks=%s" % config.var('BOT_EXCLUDE_IPANDMASKS'),
      "--noenable_CRL",
      "--CA_CRL_dir=%s" % config.var('BOT_CA_CRL_DIR'),
      "--use_certificate_dir=%s" % config.var('BOT_SSL_CERTIFICATE_DIR'),
      "--use_certificate_file=%s" % config.var('BOT_SSL_CERTIFICATE_FILE'),
      "--private_rsa_key_file=%s" % config.var('BOT_SSL_KEY_FILE'),

      # Relevent flags from cookieserver.
      "--ignore_canonical_target_in_redirect",

      # Relevent flags from contentfilter.
      "--badurls_linkspam=%s" % config.var('BADURLS_LINKSPAM'),
      "--badurls_nopropagate=%s" % config.var('BADURLS_NOPROPAGATE'),
      "--badurls_demote=%s" % config.var('BADURLS_DEMOTE'),
      "--parse_xml_as_text_plain",
#      "--delete_error_documents",  # TODO(moberoi): Confirm with Alpha.
      "--logrollbacks",
      "--cjk_config=%s" % config.var('CJKCONFIGDIR'),
      "--cjk_segmenter=%s" % config.var('CJKSEGMENTER'),
      "--use_langid_langencdet=1",
      "--langid_model_dir=%s" % config.var('LANGID_CONFIG'),
      "--bt_version=%s" % config.var('BTVERSION'),
      "--external_converter_temp_dir=%s" %
      config.var('EXTERNAL_CONVERTER_CLEAN_TEMP_DIR'),
      "--inso_lib=%s/third_party/Inso" % config.var('MAINDIR'),
      "--misc_converter_bin=%s/bin/convert_to_html" % config.var('MAINDIR'),
      "--misc_converter_cfg=%s/googlebot/inso.cfg" % config.var('GOOGLEDATA'),
      "--misc_converter_template=%s/%s" %
      (config.var('GOOGLEDATA'), config.var('INSO_TEMPLATE_BASENAME')),
      "--pdf_converter_bin=%s/bin/pdftohtml" % config.var('MAINDIR'),
      "--pdf_langs_dir=%s/third_party/pdftohtml/langs" % config.var('MAINDIR'),
      "--ps_converter_script=%s/converter/gps2ascii.ps" % config.var('MAINDIR'),
      "--swf_converter_bin=%s/bin/swfparsetxt" % config.var('MAINDIR'),
      "--generate_pathfp",
      "--max_crowding_depth=%d" % config.var('MAX_CROWDING_DEPTH'),
      "--max_filetype_raw_len=%d" % config.var('BOT_MAXFILETYPE_DOWNLOAD'),
      "--use_cvs_rewrites=false",
      "--use_yahoo_groups_rewriter=false",
      "--domino_rewrites=false",
      "--url_rewrites=%s" % config.var('RAW_URL_REWRITE_RULES_BASENAME'),
      "--rewrite_nonqualified_hostnames",
      "--enable_nonclickable_links",
      "--external_converter_startup_timeout=%d" %
      config.var('EXTERNAL_CONVERTER_STARTUP_TIMEOUT'),
#      "--have_gfs=false",
#      "--shard=%d" % 0,
      "--chinesenamefix=%d" % config.var('CHINESE_NAME_HACK'),
      "--googletags=true",
      # See comment in --retain_all_anchors as to why this is turned off.
      "--retain_all_links=false",

      # Relevent flags from base_indexer.
#      "--cmd_flush_interval=%d" % config.var('RTSERVER_CMD_FLUSH_INTERVAL'),
      "--merger",
      "--num_index_shards=1",
      "--max_checkpoints_before_deletion=%d"
      % config.var('RTSERVER_MAX_CHECKPOINTS_BEFORE_DELETION'),
      "--num_checkpoints_to_save=%d" % 20,
      "--ignore_corrupted_checkpoints",
      "--ignore_docidservers",
#      "--workerthreads=%d" % config.var('RTSERVER_NUM_WORKER_THREADS'),
      #"--update_logfile=%s" % update_log,
      "--lock_file_before_delete",
      "--sekulite_userpasswd_config=%s" % config.var('CRAWL_USERPASSWD_CONFIG'),
      "--urls_to_ignore=%s" % config.var('BADURLS'),
      "--index_prefix=%s" % config.var('RTSERVER_INDEX_PREFIX'),
      "--nodelete_multi_epoch_maps_unserved",
      "--verify_threshold=%d" % config.var('RTMASTER_VERIFY_THRESHOLD'),
#      "--merges_never_aggressive",
      "--generate_links_fileset",
#      "--rtprocessor_nice_level=%d" %
#      config.var('RTSERVER_PROCESSOR_NICE_LEVEL'),
#      "--rtcheckpointwatcher_nice_level=%d" %
#      config.var('RTSERVER_CHECKPOINTWATCHER_NICE_LEVEL'),
#      "--rtmerger_nice_level=%d" % config.var('RTSERVER_MERGER_NICE_LEVEL'),
      "--index_metatag_restricts",
      "--parse_allmetatags",
      "--parse_metatag_value",
      "--index_metatag_words",
#      "--attach_external_metadata",
#      "--langenc_rprefix=lang",
      "--restricts=",
      "--collections_directory=%s" % config.var('ENTERPRISE_COLLECTIONS_DIR'),
      "--load_bad_restrict_patterns",
      "--rt_doc_shard=%d" % 0,
      "--num_rt_doc_shards=%d" % 1,
      "--num_docid_levels=%d" % config.var('RTSERVER_DOCID_LEVELS'),
      "--merge_max_contentmap_size=%d" % 0,
      "--index_path_in_site",
      "--index_content_date=false",
      # This is turned off because the fix (http://b/19047) had a major bug.
      # See the bug report for details.
      "--retain_all_anchors=false",
      "--force_restricts_handler",
#      "--indexserver_port=%d" % 0,
#      "--docserver_port=%d" % 0,
#      "--linkserver_port=%d" % 0,
#      "--eager_anchor_requests",
#      "--enterprise=true",
      "--index_number_ranges=true",
      "--enterprise_index_date_ranges=true",
      "--max_index_title_words=%d" % 25,
      "--nocollapsetypes",
#      "--lazy_merge_ratio=%s" % config.var('RT_LAZY_MERGE_RATIO'),
#      "--cleanup_unnecessary_files=%d" %
#      config.var('RTSERVER_CLEANUP_UNNECESSARY_FILES'),
      "--min_file_size_for_merge_ratio=%s" %
      config.var('RTSERVER_MIN_FILE_SIZE_FOR_MERGE_RATIO'),
      "--max_outstanding_index_files=%s" %
      config.var('RTSERVER_MAX_OUTSTANDING_INDEX_FILES'),
      "--mmap_budget=%d" % 209715200,
      "--maps_always_mmap=common,global2local",
      "--trusted_clients=%s" %
      string.join(config.var('HTTPSERVER_TRUSTED_CLIENTS')),
      "--remember_restricts",
#      "--anchor_reload_interval_base=%d" % 300,
#      "--num_anchors_to_reload_base=%d" % 1000,
#      "--max_anchor_reload_iter=%d" % 10,
      # This is something we have done in the field due to bug 667742
      # where indexer runs out of memory. Do we need this?
      "--merged_anchors_mem_usage_cutoff=%d" % 50000000,
      "--garbage_collect_logs",
      "--compress_common_map_deletions",
#      "--fieldsearch_enabled",
      "--learn_dates",
      "--extractdate_config=%s" % config.var('DATEPATTERNS'),
      "--use_datestatsfiles",
      "--extractdate_outfile=%s" % "/bigfile/dateout_00",
      "--keep_checksum_for_filesets=false",
      "--keep_checksum_for_checkpoints=false",
#      "--supergsa_merge",

      # Relevant flags for spelling data generation.
      "--extract_langs=de,es,en,fr,it,nl,pt",
      # fix for bug 976513
      "--max_map_files=500",
      ]

  if config.var('AUTHENTICATE_SERVER_CERT'):
    args.append('--require_server_auth')
    args.append('--enable_CRL_PEM')
    # This is hack to make minimal changes to google ssl library.
    # It needs a CA file when authenticating peer. So passing a gsa's
    # own cert as a dummy CA file.
    # Enterprise code will use a CA directory instead.
    args.append('--CA_certificate_file=%s' %
                config.var('BOT_SSL_CERTIFICATE_FILE'))
  else:
    # cipher list provided is not equal to the default cipher list needed
    # for authenticating the server.
    if config.var('BOT_SSL_CIPHER_LIST'):
      args.append('--ssl_cipher_list=%s' % config.var('BOT_SSL_CIPHER_LIST'))

  if config.var('BOT_ADDITIONAL_REQUEST_HDRS'):
    args.append("--extra_http_hdrs=%s" %
                config.var('BOT_ADDITIONAL_REQUEST_HDRS'))

  # On the virtual line, we need to ignore low memory constraints and crawl
  # anyway, and lower a number of other params.
  ent_cfg_type = config.var('ENT_CONFIG_TYPE')
  if ent_cfg_type in ('LITE', 'FULL'):
    args.append("--ignore_lowmem")
    args.append("--init_connections=10")
    args.append("--maxconnections=10")
    args.append("--maximum_inflight_urls=3000")
    args.append("--target_num_inflight_urls=3000")
    args.append("--max_urls_beyond_shortplanner=15")

  # Set doc_processing_threads based on the number of CPUs available.
  if ent_cfg_type in ('LITE', 'FULL'):
    args.append("--doc_processing_threadpool_size=2")
  elif ent_cfg_type in ('ONEWAY', 'ONEBOX'):
    args.append("--doc_processing_threadpool_size=3")
  elif ent_cfg_type in ('SUPER'):
    args.append("--doc_processing_threadpool_size=6")
  else:
    args.append("--doc_processing_threadpool_size=10")

  # TODO(tianyu): Today, we assume only ONE shard of SuperGSA.
  urls_per_shard = config.var('TOTAL_URLS_EXPECTED')
  args.append("--urls_expected_per_shard=%d" % urls_per_shard)

  # MAX_CRAWLED_URLS is the smaller of true license limit or user defined limit.
  if (config.var('MAX_CRAWLED_URLS') and config.var('MAX_CRAWLED_URLS') > 0):
    max_crawled_urls = config.var('MAX_CRAWLED_URLS')
    # TODO(tianyu): Today, we assume only ONE shard of SuperGSA.
    soft_limit = max_crawled_urls
    args.append("--urls_soft_limit=%d" % soft_limit)

  if config.var('CRAWL_SCHEDULE_BITMAP') != None:
    args.append("--crawl_schedule_bitmap_file=%s" %
                config.var('CRAWL_SCHEDULE_BITMAP'))

  # For developers with unlimited license (0) we want that all DEVCHECK
  # immediately crash. For customers we will log an error and try to continue.
  if (config.var('ENT_LICENSE_INFORMATION') and
      config.var('ENT_LICENSE_INFORMATION').get(
                 'ENT_LICENSE_MAX_PAGES_OVERALL', 0) != 0):
    args.append("--nocrash_early_and_often")

  args.append("--google_config=%s/../conf/google_config" %
              config.var('MAINDIR'))

  # Flags from feeder.
  # TODO(moberoi): Find out if we can make the 2 flags below generic.
  args.append("--contentfeeds_log_info=1:/bigfile/normal_feeds:1:3")
  args.append("--datasource_map=/bigfile/feed_datasource_map000-of-001")
  args.append("--dtd=%s" % config.var('FEED_DTD'))
  args.append("--feedstatus_dir=%s" % config.var("FEED_STATUS_DIR"))

  # Slow down merge activity.
  args.append("--map_merge_activity_fraction=0.50")
  args.append("--index_merge_activity_fraction=1.00")

  args.extend(LOCK_SERVICE_FLAGS)

  return restart_wrapper('supergsa_main', config, host, port, args)

servertype.RegisterRestartFunction('supergsa_main',
                                   restart_supergsa_main_server)

#!/usr/bin/python2.4
#
# Copyright 2002-2004 Google Inc. All Rights Reserved.

"""
Use configurator if you want to deal with creating, deleting, managing
EntConfig and other administrative jobs.
"""
__author__ = 'cpopescu@google.com (Catalin Popescu)'
__owner__ = 'hareesh@google.com'

import sys
import string
import threading
import time
import commands
import traceback

from google3.pyglib import logging

from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import data_directory
from google3.enterprise.legacy.adminrunner import ar_exception
from google3.enterprise.legacy.adminrunner import crawlqueue_manager
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import license_manager
from google3.enterprise.legacy.adminrunner import log_manager
from google3.enterprise.legacy.adminrunner import user_manager
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.production.assigner import assigner
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.tools import M
from google3.enterprise.util import borgmon_util
from google3.enterprise.util import machine_param_cache

# For creating a default collection/frontend
from google3.enterprise.legacy.collections import ent_collection

# For creating default query expansion entry
from google3.enterprise.legacy.adminrunner import query_expansion_handler

true  = 1
false = 0

GRAPH_URL = "http://%(borgmon_host)s:%(borgmon_port)s/graph?expr=" \
            "%(rules)s" \
            "&grid&yrange=[0:%(yrange)s]" \
            "&nokey&palette=red,gold&with=lines+linewidth+%(width)s" \
            "&xtics=7200&yformat=%(yformat)s&gmt=%(gmt)s"

GRAPH_FILE = "%s/enterprise/statichtml/images/graphs/%s"
ENTERPRISE_GFS_SETUP_ARGS = "-p -empty -gfsuser=nobody -gfsgroup=nobody " \
                            "-email=none"

class configurator:
  """
  This class holds the global parameters and knows how to manipulate
  EntConfig in general.
  Use it if you want to deal with EntConfig. It knows how to load/save,
  modify, delete, create EntConfig.
  It manipulates the globalParameters.
  One of this guys should exist in the servlet and also in AdminRunner

  Since it has to share the globalParams, many methods are synchronized.
  """

  def __init__(self, enthome,
               box_keys_dir = "",
               license_keys_dir = "",
               install_state = 'ACTIVE',
               startup_mode = 0):
    self.entHome = enthome
    self.install_state = install_state
    self.globalLock = threading.Lock()
    # Init the global params
    self.mach_param_cache = machine_param_cache.MachineParamCache()
    self.globalParams = entconfig.EntConfig(self.entHome, 1) # Allow writes
    if not self.globalParams.Load():
      logging.error(
        "Cannot load the global parameters - think about reinstall")

    if install_state != 'INSTALL':
      if not self.globalParams.ValidateAll():
        logging.error("Global parameters were not validated correctly")

    # The operator log file
    oplogname = "%s/AdminRunner.OPERATOR.%s" % (
      self.globalParams.var("LOGDIR"),
      time.strftime("%Y_%m_%d_%H_%M_%S",
                    E.getLocaltime(time.time())))
    self.oplog = open(oplogname, "w")

    self.lm = license_manager.LicenseManager(self,
                                             box_keys_dir,
                                             license_keys_dir)
    self.um = user_manager.UserManager(self)
    self.logmanager = log_manager.LogManager(self)
    self.crawlqueuemanager = crawlqueue_manager.CrawlQueueManager(self)
    self.startup_mode = startup_mode # statup in startup mode
    self.startup_time = int(time.time())
    self.graphs = {
      'SUM_URLS_TOTAL': self.graph_data(
        file_name = "sumurlstotalgraph.png",
        vars = ["num_urls_in_index_total[24h]",
                "num_urls_available_total[24h]"],
        last_modified = -1),
      'SUM_URLS_CRAWLED': self.graph_data(
        file_name = "sumurlscrawledgraph.png",
        vars = ["num_urls_in_index_total[24h]"],
        last_modified = -1),
      'SUM_URLS_AVAILABLE': self.graph_data(
        file_name = "sumurlsavailablegraph.png",
        vars = ["num_urls_available_total[24h]"],
        last_modified = -1),
      'QUERIES_PER_MINUTE': self.graph_data(
        file_name = "queriesperminutegraph.png",
        vars = ["gws_searches_per_minute[24h]"],
        last_modified = -1),
      'SUM_URLS_TOTAL_THUMBNAIL': self.graph_data(
        file_name = "sumurlstotalthumb.png",
        vars = ["num_urls_in_index_total[24h]",
                "num_urls_available_total[24h]"],
        last_modified = -1),
      'QUERIES_PER_MINUTE_THUMBNAIL': self.graph_data(
        file_name = "queriesperminutethumb.png",
        vars = ["gws_searches_per_minute[24h]"],
        last_modified = -1),
      'TMP_GRAPH' : self.graph_data(
        file_name = "tmp_graph.png",
        vars = [],
        last_modified = -1),
      'ERROR_TEXT' : self.graph_data(
        file_name = "errortext.png",
        vars = [],
        last_modified = -1),
    }
    self.graphs_lock_ = threading.Lock();

  def hasGlobalParam(self, name):
    """ Returns whether the named global parameter exists """
    return self.globalParams.has_var(name)

  def getGlobalParam(self, name):
    """ Get a global parameter """
    return self.globalParams.var_copy(name)

  def setGlobalParam(self, name, value):
    """ sets a global parameter in the safe way (saving it via AdminRunner """
    if ( not self.globalParams.set_var(name, value, true) in
         validatorlib.VALID_CODES ):
      return false
    self.saveParams()
    return true

  def saveParams(self, retry=0):
    """ saves the parameters on the disk """
    try:
      newVersion = self.getGlobalParam("CONFIGVERSION") + 1
      self.globalParams.set_var("CONFIGVERSION", newVersion, true)
      if not self.globalParams.Save():
        self.writeAdminRunnerOpMsg(M.ERR_SAVEPARAMETERS % "")
        raise ar_exception.ARException(ar_exception.SAVEPARAMS,
                                       M.ERR_SAVEPARAMETERS % "")
      self.globalParams.DistributeAll(retry)
    except IOError:
      self.writeAdminRunnerOpMsg(M.ERR_SAVEPARAMETERS % "")
      raise ar_exception.ARException(ar_exception.SAVEPARAMS,
                                     M.ERR_SAVEPARAMETERS % "")


  ############################################################################
  #
  # Helpers to access specific machine mapped structures
  #
  def replicateConfigOnMachine(self, machine):
    """ This runs replicate_machine on another machine to copy the
    configuration from this machine """
    return self.replicateConfig([machine]);

  def replicateConfig(self, machines):
    """ Replicates the config to a list of machines """
    cmd = (". %s && cd %s/local/google3/enterprise/legacy/scripts && "
           "./replicate_config.py %s %s" % (
      self.getGlobalParam("ENTERPRISE_BASHRC"), self.entHome,
      E.getCrtHostName(), self.globalParams.GetConfigFileName()))
    return E.execute(machines, cmd, None, true)

  #############################################################################
  #
  # Directory creation / deletion / init
  #

  def createDataDirs(self, machines, onlyifneeded=false, node_replacement=0):
    """
    Create the directories for an index.
    Note that this function will get executed when a node is added back to the
    cluster.
    Input: onlyifneeded: If true, createDataDirs will only proceed if necessary;
      if search.config is missing, we assume enterprise-data needs to be re-created
    @return boolean Success status
    """
    if onlyifneeded:
      # The presence or absence of search.config indicates if we need to
      # re-create the directories
      config = '%s/search.config' % self.getGlobalParam(C.DATADIR)
      if E.access(machines, config, 'f'):
        logging.info('createDataDirs: search.config already exists')
        return true
      else:
        logging.info("createDataDirs: search.config doesn't exist; re-creating")
    logging.info("Create enterprise datadir...")
    if not data_directory.create(
      self.getGlobalParam(C.DATADISK),
      self.getGlobalParam("ENT_BIGFILE_DATADISKS"),
      self.getGlobalParam(C.DATACHUNK_PREFIX),
      "enterprise",
      self.getGlobalParam(C.BIN_DIRS),
      machines):
      logging.error("Error creating datadir")
      return false

    logging.info("Create querycache datadir...")
    if not data_directory.create(
      "%s/../querycache" % self.getGlobalParam(C.DATADISK),
      self.getGlobalParam("ENT_BIGFILE_DATADISKS"),
      "%s/../querycache" % self.getGlobalParam(C.DATACHUNK_PREFIX),
      "cache",
      self.getGlobalParam(C.BIN_DIRS),
      machines):
      logging.error("Error creating datadir")
      return false


    # Create FEEDS_DIR and FEED_STATUS_DIR for one-way
    if not self.getGlobalParam(C.GFS_CELL):
      cmnd = "mkdir -p %s; mkdir -p %s" % (self.getGlobalParam('FEEDS_DIR'),
                                     self.getGlobalParam('FEED_STATUS_DIR'))
      res = E.exe(cmnd)
      logging.info("Result of command %s is %d" % (cmnd, res))

    # Create ONEBOX_LOGS_DIR for one-way
    if not self.getGlobalParam(C.GFS_CELL):
      cmnd = "mkdir -p %s" % self.getGlobalParam('ONEBOX_LOGS_DIR')
      res = E.exe(cmnd)
      logging.info("Result of command %s is %d" % (cmnd, res))

    # Create directory for rt-index cache
    if self.getGlobalParam('RTSLAVE_LOCAL_CACHE_DIR'):
      d = self.getGlobalParam('RTSLAVE_LOCAL_CACHE_DIR')
      out = []
      cmd = "mkdir -p %s; test -d %s" % (d,d)
      if E.ERR_OK != E.execute(machines, cmd, out, false):
        logging.error("Error creating cache directory for rtslave: %s" % out)
        return false

    # Ram cache directory is the mount point itself, so we don't need to create it.
    #self.getGlobalParam('RTSLAVE_RAM_DIR_FOR_INDEX_CACHING')

    return true

  def deleteDataDirs(self, machines):
    """
    Delete the directories for an index.
    @return boolean Success status
    """
    logging.info("Delete enterprise datadir...")
    if not data_directory.delete(
      self.getGlobalParam(C.DATADISK),
      self.getGlobalParam("ENT_BIGFILE_DATADISKS"),
      self.getGlobalParam(C.DATACHUNK_PREFIX),
      "enterprise",
      machines):
      return false

    logging.info("Delete querycache datadir...")
    if not data_directory.delete(
      "%s/../querycache" % self.getGlobalParam(C.DATADISK),
      self.getGlobalParam("ENT_BIGFILE_DATADISKS"),
      "%s/../querycache" % self.getGlobalParam(C.DATACHUNK_PREFIX),
      "cache",
      machines):
      return false

    # Don't delete GFS master and chunkserver dirs

    return true

  def createGFSChunkSubDirs(self, reset_index=0):
    """
    Creates GFS subdirectories for base indexer and anchor processing
    Args:
      reset_index: 1, if this is for resetting index. Some dirs may exist
                   0, otherwise.
    Return:
      true  - successful
      false - otherwise
    """
    ##
    def execMultiTimes(self, to_exec, max_tries=10):
      """ exec a gfs command by trying multiple  times """
      try_num = 0
      while try_num < max_tries:
        err, out = E.run_fileutil_command(self.globalParams, to_exec)
        if E.ERR_OK == err:
          return true
        time.sleep(10)
        try_num = try_num + 1
        logging.error("Error executing %s" % to_exec)
      return false
    ##

    def createGFSDir(self, dir_name, reset_index):
      """ create a GFS Dir.

      if this is for reset index, the dir may already
      exist. So just try it once and ignore any error.
      Args:
        dir_name: '/gfs/ent/feeds'
        reset_index: 1 - during reset index
                     0 - othewise
      Return:
        true  - successful
        false - otherwise
      """
      if reset_index:
        execMultiTimes(self, "mkdir -p %s" % dir_name, max_tries=1)
        return true
      else:
        return execMultiTimes(self, "mkdir -p %s" % dir_name)

    num_shards = self.globalParams.GetEntNumShards()
    namespace_prefix = self.getGlobalParam('NAMESPACE_PREFIX')
    pr_namespace_prefix = self.getGlobalParam('OUTPUT_NAMESPACE_PREFIX')['pr_main']

    # This also waits for the gfs master to come up.
    if not execMultiTimes(self, "mkdir -p %s" % E.normpath(
      "%s/tmp" % namespace_prefix), 30):
      return false

    # Create the pr_main subdir for pr_main to write to.
    if not execMultiTimes(self, "mkdir -p %s" % E.normpath(
      "%s/pr_main" % pr_namespace_prefix), 30):
      return false

    # Create FEEDS_DIR (feeds), a directory where uploaded feeds will get stored
    if not createGFSDir(self, self.getGlobalParam('FEEDS_DIR'), reset_index):
      return false

    # Create FEED_STATUS_DIR (feedstatus), a directory to store feed status
    if not createGFSDir(self, self.getGlobalParam('FEED_STATUS_DIR'),

                        reset_index):
      return false

    # Create SSO_LOG_DIR, a directory to store sso logging output files
    if not createGFSDir(self, self.getGlobalParam('SSO_LOG_DIR'),
                        reset_index):
      return false

    # Create LOG_REPORT_DIR (log_report), a directory to
    # store raw and summary reports
    if not createGFSDir(self, self.getGlobalParam('LOG_REPORT_DIR'),
                        reset_index):
      return false

    # Create CRAWLQUEUE_DIR (crawlqueue), a directory to store crawlqueue data
    if not createGFSDir(self, self.getGlobalParam('CRAWLQUEUE_DIR'),
                        reset_index):
      return false

    # Create SYSLOG_CHECKPOINTS_DIR (syslog_checkpoints)
    # a directory to store syslog checkpoint files
    if not createGFSDir(self, self.getGlobalParam('SYSLOG_CHECKPOINTS_DIR'),
                        reset_index):
      return false

    # Create directories for base_indexer, global_anchor and
    # global-link.
    dirs = ['base-indexer', 'global-anchor', 'global-link', 'urlhistory-processor']
    for i in range(num_shards):
      for dir in dirs:
        if not execMultiTimes(self, "mkdir -p %s%s%03d-of-%03d" % (
          namespace_prefix, dir, i, num_shards)):
          return false

      # Inside the base-indexer directories we create directories for
      # global anchor command  logs
      for j in range(num_shards):
        if not execMultiTimes(
          self,
          "mkdir -p %sbase-indexer%03d-of-%03d/global-anchor%03d-of-%03d" % (
          namespace_prefix, i, num_shards, j, num_shards)):
          return false

    num_tracker_shards = self.globalParams.GetNumShards('urltracker_server')
    for i in range(num_tracker_shards):
      if not execMultiTimes(self,
                            "mkdir -p %surltracker%03d-of-%03d" % (
        namespace_prefix, i, num_tracker_shards)):
        return false

    return true

  def writeAdminRunnerOpMsg(self, msg):
    msg = "@ %s: %s\n" % (
      time.strftime("%Y/%m/%d %H:%M:%S",
                    E.getLocaltime(time.time())),
      msg)
    self.oplog.write(msg)
    self.oplog.flush() # in case of log(s) smaller than buffer size

  #############################################################################


  # counts the number of spelling files in the specified directory
  def CountSpellingFiles(self, fileutil_args, path):
    cmnd = "fileutil %s ls %s" % (fileutil_args, path)
    res_str = commands.getoutput(cmnd)
    num_files = string.count(res_str, ".spelling.")
    logging.info("found %d files" % num_files)
    return num_files


  # ensures that the specified directory exists
  # note that the parent of the directory must exist
  def EnsureDirectory(self, fileutil_args, path):
    logging.info("ensuring directory %s" % path)
    if string.find(path, "/gfs/") == 0:
      # string starts with /gfs/ so path is gfs directory
      cmnd = "fileutil %s -f mkdir -p %s" % (fileutil_args, path)
    else:
      cmnd = "mkdir -p %s" % path
    res = E.exe(cmnd)
    logging.info("Result of command %s is %d" % (cmnd, res))



  def EnsureSpellingData(self, reset = 0):
    """
    This ensures that initial spelling data is present.
    If reset is set we clear ENT_SPELL_SERVING_ID and revert
    files to initial state.
    """

    logging.info("ensuring presence of initial spelling data")
    serving_id_cfg_name = 'ENT_SPELL_SERVING_ID'

    # if reset is set - blow away runtime dictionary version. (this is
    # useful after index has been reset).
    if self.hasGlobalParam(serving_id_cfg_name) and (reset == 1):
      self.setGlobalParam(serving_id_cfg_name, 0);

    if (self.hasGlobalParam(serving_id_cfg_name)) and \
       (self.getGlobalParam(serving_id_cfg_name) == 0):
      fileutil_args = ""
      if self.hasGlobalParam('GFS_ALIASES'):
        fileutil_args = "--gfs_aliases='%s'" % \
                        self.getGlobalParam('GFS_ALIASES')
        fileutil_args += " --bnsresolver_use_svelte=false"
      if self.hasGlobalParam('DATADIR'):
        fileutil_args = "%s --datadir=%s" % \
                        (fileutil_args, self.getGlobalParam('DATADIR'))
      # note: assumes that the parent of spell_root exists
      spell_root = self.getGlobalParam('ENT_SPELL_ROOT_DIR')
      end = len(spell_root) - 1
      if spell_root[end] == '/':
        spell_root = spell_root[0:end]
      target_path = "%s/spell-0" % \
                    self.getGlobalParam('ENT_SPELL_ROOT_DIR')
      self.EnsureDirectory(fileutil_args, spell_root)
      self.EnsureDirectory(fileutil_args, "%s" % spell_root)
      self.EnsureDirectory(fileutil_args, "%s" % target_path)
      logging.info("ensuring files")
      if not self.hasGlobalParam('ENTERPRISE_HOME'):
        logging.fatal("No ENTERPRISE_HOME config parameter")
        return
      src_path = "%s/../spelling-data/runtime" % \
                 self.getGlobalParam('ENTERPRISE_HOME')
      cmnd = "(cd %s ; " % src_path
      cmnd = cmnd + "for f in *.spelling.* ; "
      cmnd = cmnd + "do fileutil %s -f cp %s/$f %s/$f; done)" % \
                    (fileutil_args, src_path, target_path)
      res = E.exe(cmnd)
      logging.info("Result of command %s is %d" % (cmnd, res) )
      # ensure spelling data is present
      num_src_files = self.CountSpellingFiles(fileutil_args, src_path)
      logging.info("There are %d spelling files in the source directory" % \
                   num_src_files)
      num_target_files = \
                       self.CountSpellingFiles(fileutil_args, target_path)
      logging.info("There are %d spelling files in the target directory"% \
                   num_target_files)
      if num_src_files == num_target_files:
        logging.info("spelling data present")
      else:
        logging.fatal("failed to ensure presence of spelling data")
        return

    else:
      logging.info("no config param %s, or it's not 0" % serving_id_cfg_name)
      logging.info("skipping spelling data check")


  #############################################################################
  def CheckMachineMemory(self):
    """
    This checks/sets MEMORY_TOTAL_PER_MACHINE, which is used by rtslave
    to set RTSLAVE_MAX_MMAP_MEMORY. This function used to set
    GFS_GLOBAL_RESERVED_GB. But since GFS is now part of the core services,
    it does not need to set GFS_GLOBAL_RESERVED_GB.
    """

    orig_memory_total = self.globalParams.var('MEMORY_TOTAL_PER_MACHINE')
    logging.info("old MEMORY_TOTAL_PER_MACHINE is: %s" % orig_memory_total)

    param_value = self.GetMachineParams("memory-total")
    if not param_value:
      return 0
    memory_total = int(param_value)
    if orig_memory_total != memory_total:
      self.setGlobalParam('MEMORY_TOTAL_PER_MACHINE', memory_total)
      logging.info("current MEMORY_TOTAL_PER_MACHINE is: %s" % memory_total)
    return 1

  #############################################################################
  def GetMachineParams(self, fact_name):
    """ Get facts from the machine parameter cache

    Arguments:
      fact_name: 'memory-total'
    Returns:
      12430580
    """

    return self.mach_param_cache.GetFact(fact_name, E.getCrtHostName())

  #############################################################################
  def DoMachineAllocation(self, serversets=None):
    """ This allocates the machines in the cluster

    Arguments:
      serversets: ['workqueue-slave'] or None (allocate all servers)

    Returns:
      1 - successful. 0 - otherwise.
    """

    logging.info("Starting the assigner")

    # Get all machines from in SERVERS that are not in machines and remove
    # them from servers
    used_machines = []
    servers = self.globalParams.var('SERVERS')

    for p, s in servers.items():
      for m in s:
        if m not in used_machines: used_machines.append(m)
    machines = self.globalParams.var('MACHINES')
    for m in used_machines:
      if m not in machines:
        self.globalParams.ReplaceVarInParam("SERVERS", None, m)
    free_machines = [m for m in machines if m not in used_machines]
    logging.info('used_machines: %s\n' % used_machines)
    logging.info('free_machines: %s\n' % free_machines)

    #
    # Now, reallocate the empty spaces
    #
    srvr_mgr = self.globalParams.GetServerManager()
    try:
      assn = assigner.Assigner()
      assn.SetFree(free_machines)
      assn.SetVerbose(1)
      (success, fail, tried, free) = assn.AddSets(srvr_mgr, serversets)
    except:
      exc = sys.exc_info()
      logging.error('\n' + string.join(
        traceback.format_exception(exc[0], exc[1], exc[2]), ''))
      logging.error("ERROR: Machine reallocation failed")
      return false

    # We don't care about balancer failures
    # TODO remove this filter once eugene fixes googleconfig load.
    fail = filter(lambda x: x[0] != '+', fail)

    logging.info("done assigner")
    logging.info("success = %s" % success)
    logging.info("fail = %s" % fail)
    logging.info("tried = %s" % tried)
    logging.info("free = %s" % free)

    if len(fail) != 0:
      return false

    # Machine allocation only updates the server manager object. We
    # need to make sure those changes are reflected in SERVERS map.
    self.SaveNewMachineAllocation(srvr_mgr.CombinedServerMap())

    return true

  def RemoveLegacyComponents(self, servers_map):
    """ Remove legacy components from servers map

    gfs components have been moved to core services in 4.6.4 #+1.
    GEMS, concentrator, and fixer are removed in 4.7.
    Sometimes ESO folks copy the SERVERS map from an old version to a new one.
    This is just to make sure these components won't be in the SERVERS map. 
    This function can be removed after 5.0.

    Arguments:
      servers_map: SERVERS = {3970: ['ent2'], 21000: ['ent5', 'ent4'], ...}
    """

    legacy_components = ['gfs_master', 'gfs_chunkserver', 'sremote_server',
                         'concentrator', 'gemsalerter', 'gemscollector',
                         'gemsreporter', 'fixer']
    for srv in legacy_components:
      min_port = servertype.GetPortMin(srv)
      max_port = servertype.GetPortMax(srv)
      for srv_port in range(min_port, max_port):
        if servers_map.has_key(srv_port):
          logging.info("Removing key %d from servers map" % srv_port)
          del servers_map[srv_port]

  def SaveNewMachineAllocation(self, servers_map):
    """ Save the new machine allocation info

    Machine allocation only updates the server manager object. We
    need to make sure those changes are reflected in SERVERS map.

    Arguments:
      servers_map: SERVERS = {3970: ['ent2'], 21000: ['ent5', 'ent4'], ...}
    """

    self.RemoveLegacyComponents(servers_map)
    self.globalParams.set_var( "SERVERS", servers_map)
    self.globalParams.force_set_var_for_propagation('MACHINES')
    self.saveParams()

  def CompareServersMap(self, old_servers_map, new_servers_map):
    """ Compare two servers map.

    For each port in the old servers map, check what is not in the new
    servers map. These are the servers to be killed.
    For each port in the new servers map, check what is not
    in the old servers map. These are the servers to be started.

    Arguments:
      old_servers_map: {3970: ['ent2'], 21000: ['ent6', 'ent5', 'ent4']}
      new_servers_map: {3970: ['ent2', 'ent3'], 21000: ['ent4']}

   Returns:
     ([(21000, 'ent6'), (21000, 'ent5')], [(3970, 'ent3')])
   """

    def _a_minus_b(a, b):
      a_minus_b = []
      for p, s in a.items():
        for m in s:
          if m not in b.get(p, []):
            a_minus_b.append((p, m))
      return a_minus_b

    old_to_kill = _a_minus_b(old_servers_map, new_servers_map)
    new_to_start = _a_minus_b(new_servers_map, old_servers_map)
    return (old_to_kill, new_to_start)

  def AllocateServersToNewMachine(self, new_machine):
    srvr_mgr = self.globalParams.GetServerManager()
    excluded_servertypes = ['workqueue-slave', 'workqueue-master',
                            'config_manager', 'workschedulerserver']
    excluded_servers = []
    for servertype in excluded_servertypes:
      set = srvr_mgr.Set(servertype)
      for server in set.Servers():
        excluded_servers.append(str(server))
    try:
      assn = assigner.Assigner()
      (added, replaced, tried_replaced) = assn.Rebalance(srvr_mgr,
                                     new_machine,
                                     excluded_servers=excluded_servers)
    except:
      exc = sys.exc_info()
      logging.error('\n' + string.join(
        traceback.format_exception(exc[0], exc[1], exc[2]), ''))
      logging.error("ERROR: Machine Rebalance failed")
      return []

    logging.info("done rebalance")
    logging.info("Added = %s" % repr(added))
    logging.info("Replaced = %s" % repr(replaced))
    logging.info("Tried_Replaced = %s" % repr(tried_replaced))
    # Machine allocation only updates the server manager object. We
    # need to make sure those changes are reflected in SERVERS map.
    self.globalParams.set_var(
      "SERVERS",
      self.globalParams.GetServerManager().CombinedServerMap())
    self.globalParams.force_set_var_for_propagation('MACHINES')
    self.saveParams()

    return replaced

  #############################################################################

  def CreateDefaultCollection(self):
    """ create a default collection unconditionally when first startup """
    collection = ent_collection.EntCollection(C.DEFAULT_COLLECTION,
                                              self.globalParams)

    # for patch upgrade, default collection already exists, we run Create(true)
    # to add new variables and new files.
    ok = collection.Create(patchExisting=collection.Exists())

    if ok and collection.set_file_var_content('GOODURLS', '/', 1) \
        not in validatorlib.VALID_CODES:
      # if can't create the file, delete collection and return false.
      collection.Delete()
      return false

    return ok

  #############################################################################

  def CreateDefaultFrontend(self):
    """ create a default frontend unconditionally when first startup """
    frontend = ent_collection.EntFrontend(C.DEFAULT_FRONTEND,
                                          self.globalParams)

    # for patch upgrade, default collection already exists, we run Create(true)
    # to add new variables and new files.
    return frontend.Create(patchExisting=frontend.Exists())

  #############################################################################

  def CreateDefaultQueryExpEntry(self):
    """ create a default query exp entry unconditionally when first startup
    """

    logging.info("Entering CreateDefaultQueryExpEntry")
    names = [
        ("EN", "Google_English_stems"),
        ("FR", "Google_French_stems"),
        ("DE", "Google_German_stems"),
        ("IT", "Google_Italian_stems"),
        ("PT", "Google_Portuguese_stems"),
        ("ES", "Google_Spanish_stems"),
        ("NL", "Google_Dutch_stems"),
    ]
    # Do as much as possible through the Query expansion base, so we are
    # consistent with creating a new entry via the AdminConsole.
    qe_base = query_expansion_handler.QueryExpansionBase(self)

    # This accounts for ENT_STEMS_EN_SOURCE, ... ENT_STEMS_PT_SOURCE
    for (lang, name) in names:
      filename = self.globalParams.var("ENT_STEMS_%s_SOURCE" % lang)

      if filename:
        logging.info(
          "Copy source stemming file %s to query expansion entry %s" % (
          filename, name))
        try:
          contents = open(filename, "r").read()
        except IOError, e:
          logging.error("Failed to read stems from %s" % filename)
          return false

        entry = qe_base.ConstructCollectionObject(name)

        params = {}

        # Set default params, and then override them with existing values
        if lang == 'EN':
          params[C.ENABLED] = 1
        else:
          params[C.ENABLED] = 0
        params[C.DELETABLE] = 0
        params[C.DOWNLOADABLE] = 1
        params[C.ENTRY_TYPE] = C.QUERY_EXP_FILETYPE_SYNONYMS

        if entry.Exists():
          for c in (C.ENABLED, C.DELETABLE, C.DOWNLOADABLE, C.ENTRY_TYPE):
            if entry.has_var(c):
              params[c] = entry.get_var(c)

        errors = qe_base.Upload(entry, 1, params, 1, contents)

        if errors != validatorlib.VALID_OK:
          logging.error(
            "Creating or updating query exp data, errors: " +
            repr(ferrors))
          return false

      else:
        logging.info(
          "Additional stems for %s not created - no filename in config." %
          lang)
    return true

  def CompileQueryExpData(self):
    """ Compile dictionaries needed for query expansion.
    """
    logging.info("Entering CompileQueryExpData")
    qe_base = query_expansion_handler.QueryExpansionBase(self)
    qe_base.Apply()

  #############################################################################

  def AssignDefaultCollAndFront(self):
    """
    This function will assign the default front+coll defined in messages.en
    to the default user currently defined as 'admin' in the passwd file
    this function will not be meaningful if the default user in
    passwd file is not 'admin' or if it's removed/changed
    TODO: is 'admin' defined somewhere? a constant? text in some file
    """
    userName = 'admin'
    user = ent_collection.EntUserParam(userName, self.globalParams)

    # we need to create 'admin' since it doesn't exist in startup mode
    if not user.Exists() and not user.Create():
      logging.error("Failed to create userparam %s" % userName)
      user.Delete()
      return false

    param_to_set = [('LAST_COLLECTION', C.DEFAULT_COLLECTION),
                    ('LAST_FRONTEND', C.DEFAULT_FRONTEND),]

    for (name, value) in param_to_set:
      try:
        user.set_var(name, value, validate = 1)
      except KeyError:
        logging.error("Failed to set userparam %s" % name)
        return false

    return true

  ############################################################################

  def CreateDefaultBackendFiles(self):
    """Initialize data files for backend servers to start up normally"""
    def TouchFile(global_params, filename):
      """ check to see if filename exists, create if it does not exists """
      # first check if file exists
      ls_cmd = "ls %s" % filename
      err, out = E.run_fileutil_command(self.globalParams, ls_cmd)
      if err != E.ERR_OK:
        # create if not exists
        create_cmd = "truncate %s 0" % filename
        err, out = E.run_fileutil_command(self.globalParams, create_cmd)
        if err != E.ERR_OK:
          logging.fatal("Could not create file: %s" % filename)

    if not self.getGlobalParam(C.GFS_CELL):
      # touch urlmanager remove doc log file
      umremovedoc_file = "%s-from-00000-000-of-001seq00000" % \
                         self.globalParams.var(
        'WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX')
      logging.info("Create empty removedoc log for urlmanager: %s" %
                   umremovedoc_file)
      TouchFile(self.globalParams, umremovedoc_file)
      # touch urlmanager urlscheduler log file
      umurlscheduler_file = "/bigfile/%s-from-00000-000-of-001seq00000" % \
                            self.globalParams.var(
        'URLMANAGER_URLSCHEDULER_LOG_PREFIX')
      logging.info("Create empty urlscheduler log for urlmanager: %s" %
                   umurlscheduler_file)
      TouchFile(self.globalParams, umurlscheduler_file)


  ############################################################################
  #
  # Helpers to access the graph map
  #
  def getGraphFileName(self, graph_name):
    return GRAPH_FILE % (self.globalParams.var('GOOGLEDATA'),
                         self.graphs[graph_name].file_name)

  #############################################################################

  def getGraphURL(self, graph_name, auto_resize, wide_lines):
    mode = borgmon_util.INSTALL_STATE_TO_MODE_MAP.get(self.install_state,
        borgmon_util.ACTIVE)  # default to ACTIVE
    bu = borgmon_util.BorgmonUtil(self.getGlobalParam("VERSION"), mode=mode)
    host = bu.GetBorgmonHostname()
    port = bu.GetBorgmonPort()
    vars_url = ""
    if auto_resize:
      yrange = ''
    else:
      yrange = 10
    if wide_lines:
      width = '6'
    else:
      width = '3'
    yformat = "%.1s%c"
    gmt_offset = int(time.strftime('%z')) / 100
    return GRAPH_URL % {'borgmon_host': host,
          'borgmon_port': port,
          'rules': string.join(self.graphs[graph_name].vars, ';'),
          'yrange': yrange,
          'width' : width,
          'yformat': yformat,
          'gmt': gmt_offset,
          }

  #############################################################################

  def getGraphTimeSinceLastModified(self, file_name):
    if self.graphs[file_name].last_modified < 0:
      return -1
    return time.time() - self.graphs[file_name].last_modified

  #############################################################################

  def setGraphLastModifiedTime(self, file_name):
    self.graphs[file_name].last_modified = time.time()

  #############################################################################

  def setGraph(self, graph_name, content):
    file = self.getGraphFileName(graph_name)
    self.graphs_lock_.acquire()
    try:
      open(file, "w").write(content)
      self.setGraphLastModifiedTime(graph_name)
    finally:
      self.graphs_lock_.release()

  #############################################################################

  # keep file name and time information about each Borgmon graph
  class graph_data:
    def __init__(self, file_name, vars, last_modified):
     self.file_name = file_name
     self.vars = vars
     self.last_modified = last_modified

###############################################################################

  # return the install state
  def getInstallState(self):
    return self.install_state

  # see if we're in startup mode
  def isInStartupMode(self):
    return self.startup_mode

  # signal the end of startup mode; begin normal operation
  def startupDone(self):
    self.startup_mode = 0
    diff = int(time.time()) - self.startup_time
    logging.info("Startup finished (took %d seconds)" % diff)

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

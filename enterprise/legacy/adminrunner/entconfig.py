#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# Original Author: cpopescu@google.com
#
# This class holds many Babysitter configuration parameters for Enterprise.
#
# update_derived_info() contains logic to customize parameters used by
# servertype_*.py in generating command line flags.
#
# The constraint_general dictionary controls what servers get run by
# Babysitter.

# For update_derived_info
__pychecker__ = "maxlocals=100 maxbranches=100 maxlines=1000"

import copy
import math
import os
import re
import string
import sys
import time
import types

from google3.pyglib import logging

from google3.enterprise.core import core_utils
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.licensing import ent_license
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.production.babysitter import serverlib
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import threadsafegoogleconfig
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.production.configmgr import configmgr_request
from google3.enterprise.legacy.production.configmgr import epoch_requests
from google3.enterprise.legacy.production.configmgr import server_requests
from google3.enterprise.legacy.production.configmgr import update_requests
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.license import license_api

###############################################################################

true  = 1
false = 0

MAX_MMAP_MEMORY_CACHE = None

#
# These are the servers that we use all the time plus their shifts during
# testing. Please note that "all the time" means that these servers will
# be started in "ACTIVE", "TEST", and "SERVE" states.
#
SERVERS_PROCESS_DATA = {
  'gfs_master':              1,
  'sremote_server':          1,
  'gfs_chunkserver':         1,
  'clustering_server':       1,
  'entfrontend':             1,
  'enttableserver':          1,
  'web':                     1,
  'onebox':                  1,
  'oneboxenterprise':        1,
  'cache':                   1,
  'mixer':                   1,
  'qrewrite':                1,
  'spellmixer':              1,
  'headrequestor':           1,
  'authzchecker':            2,
  'rtslave':                 100,
  'fsgw':                    10,
  'connectormgr':            1,
  'ent_fedroot':             1,
  'registryserver':          1,
  }

###############################################################################


# TODO: make the googleconfig file name follow another rule and be in the
#    form of all other config files (config.enterprise.<version> for example
#

def IsNameValid(name):
  """
  This validates if the parameter is an OK name for a crawl or a restrict
  A name is OK if contains [a-z, A-Z, 0-9, _, -] and does not start with -
  """
  if not name or len(name) > 200: return false
  if name[0] == '-': return false
  for c in name:
    if not (( c >= 'a' and c <= 'z' ) or
            ( c >= 'A' and c <= 'Z' ) or
            ( c >= '0' and c <= '9' ) or
            ( c in ['_', '-'])):
      return false
  return true

# Helper function

def RepairUTF8(text):
  """Input: text: a string that should be UTF-8.
  Output: a string that is UTF-8.  If the input string is UTF-8, the output
  string will be the same string.

  Sometimes customers put non-UTF-8 characters in files (e.g. keymatches).
  This will break XML parsing if we don't repair it.
  We treat any non-UTF-8 characters are iso-8859-1, which has been
  the case for customers so far (e.g. trademark, copyright symbols).
  If the characters aren't iso-8859-1, the conversion will still succeed.

  We also remove control characters (except 0x9, 0xa, 0xd (TAB, NL, CR)),
  since they will break the CDATA sections in import/export.  We should
  remove Unicode surrogates, fffe, and ffff too, but that would require
  converting from UTF-8 to Unicode and back, which is expensive, for
  little gain.
  """
  if re.search('[\x00-\x08\x0b\x0c\x0e-\x1f]', text):
    text = re.sub('[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

  if type(text) == types.UnicodeType:
    try:
      return text.encode('ascii')
    except:
      return text.encode('utf-8')

  return text

def GetPlatform():
  """Read /etc/google/enterprise_sysinfo to determine what platform
  we are.

  Returns:
    platform as a string.
  """
  ENT_SYSINFO_PATH = '/etc/google/enterprise_sysinfo'
  # get platform information from file
  ent_sysinfo = {}
  try:
    execfile(ENT_SYSINFO_PATH, {}, ent_sysinfo)
  except Exception:
    pass

  ent_platform = ent_sysinfo.get('PLATFORM', 'oneway')
  return ent_platform


#############################################################################

class EntConfig(threadsafegoogleconfig.ThreadsafeConfig):

  def __init__(self, ent_home, writable=0):
    """
    Contructs params from the default config file
    """
    threadsafegoogleconfig.ThreadsafeConfig.__init__(
      self, self.ComposeConfigFileName(ent_home))

    self.ent_home_ = ent_home
    self.use_machine_params_ = 1

    if writable:
      self.allow_config_mgr_requests_ = 1
    else:
      self.SetReadOnly()

    # Actually the servers map obtained from allocation
    self.crawl_machines_ = {}

    self.common_init()

    # Turn on enterprise specific complex variables.
    self.map_vars_ = 1

    # Variables to handle the batch mode.
    # Batch mode allows propagation of changes to other machines at the end of
    # making a batach of changes rather than in the middle.
    # Currently it is assumed that changes need to be propagated to all the
    # nodes alive.
    self.batch_mode_ = 0
    # maps file -> order in which to propagate
    self.batch_updates_list_ = {}
    # maps dir -> order in which to create
    self.batch_dirs_ = {}

  def BeginBatchMode(self):
    """Starts batch mode updates to config.
    NOTE: Using batched mode for a running version would mean that changes to
    files modified won't be picked up by other nodes until EndBatchMode is
    called.
    """
    logging.info('BEGIN: batch update mode.')
    self.batch_mode_ = 1
    # forcefully add google_config and enterprise_config
    self.batch_updates_list_ = {
                    '%s/%s' % (self.var('ENT_DISK_ROOT'), C.ETC_SYSCONFIG): 0,
                    self.ComposeConfigFileName(self.ent_home_): 1,
                    }
    self.batch_dirs_ = {}

  def __dictsort(self, dict):
    """Sorts a ditionary with of the form item -> order  according to order.
    Returns the sorted array of items according to their order.
    """
    # reverse the tuple
    items = [(order, item) for item, order in dict.items()]
    # do a sort on the tuple
    items.sort()
    return [item for order, item in items]

  def EndBatchMode(self):
    """Ends batch mode and propagates changes to other nodes in exact same order
    as they were made.
    """
    dirs = self.__dictsort(self.batch_dirs_)
    E.mkdir_batched_dirs(self.var('MACHINES'), dirs)
    to_distribute = self.__dictsort(self.batch_updates_list_)
    E.distribute_batched_files(self.var('MACHINES'), to_distribute, true)
    self.batch_mode_ = 0
    self.batch_updates_list_ = {}
    self.batch_dirs_ = {}
    logging.info('END: batch update mode.')

  def AddBatchDir(self, dir):
    """Adds a directory to the list of batched directories to be created at the
    end of batch mode.
    """
    assert(self.batch_mode_)
    if not self.batch_dirs_.has_key(dir):
      self.batch_dirs_[dir] = len(self.batch_dirs_)

  #############################################################################
  #
  # Initialize all the file parameters with the default values
  #

  def InitGlobalDefaultFiles(self, overwrite=true):
    """ This will init some configuration files with defaults (ex: BADURL). If
    overwrite is false, It will skip (re)initialization of the config files
    that already exist.
    """
    defaults = self.var(C.GLOBAL_DEFAULT_FILES)
    self.params_lock_.acquire()
    try:
      try:
        for param, default_file in defaults.items():
          if overwrite or (not os.path.exists(self.var(param))):
            if default_file == None:
              value = ""
            else:
              value = open(default_file, 'r').read()

            self.set_file_var_content(param, value, 0)
          else:
            logging.info('%s already exists and no overwrite, skipping.' %
                            self.var(param))
      except IOError, e:
        logging.error("Cannot set the default configuration files [%s]" % e)
        return false
    finally:
      self.params_lock_.release()
    return true

  #############################################################################
  #
  # Load / Save
  #
  def Load(self, configfile = None,
           do_includes = 1, add_defaults = 1, config_dir = None):
    """
    Load crawl parameters from the object's type specific config file.
    returns false if loading failed, true otherwise
    """

    # NOTE: on Load we don't want any config mgr requests side effects
    # caused by update_derived_info(). We disallow config mgr requests here,
    # and later restore the setting.
    old_config_mgr_state = self.get_allow_config_mgr_requests()
    self.set_allow_config_mgr_requests(0)
    try:
      try:
        if not threadsafegoogleconfig.ThreadsafeConfig.Load(
          self,
          configfile = configfile,
          do_includes = do_includes,
          add_defaults = add_defaults,
          config_dir = config_dir):
          return false

        # Old versions have MACHINES and ENT_ALL_MACHINES as comma separated
        # lists .. We swiftly convert such cases to our format
        if type(self.var('MACHINES')) == type(""):
          self.params_.namespace['MACHINES'] = map(
            string.strip, string.split(self.var('MACHINES'), ","))
        if type(self.var('ENT_ALL_MACHINES')) == type(""):
          self.params_.namespace['ENT_ALL_MACHINES'] = map(
            string.strip, string.split(self.var('ENT_ALL_MACHINES'), ","))

        # sets some default allocations in the SERVERS map
        # Should be called after all other derived variables have
        # been updated
        self.update_machine_allocation_map()
      except IOError, e:
        logging.error("Error loading %s [%s]" % (self.config_file_, e))
        return false
    finally:
      # restore config mgr state
      self.set_allow_config_mgr_requests(old_config_mgr_state)

    # Normalize the paths for all dirs and file because we may tun in various
    # trouble from babysitter and inconsistencies (some append /, some
    for p in self.GetAllVars():
      validator = self.type_map_.get(p)
      if ( validator != None and
           isinstance(validator, validatorlib.Filename) and
           type(self.params_.namespace[p]) == type("") and
           self.params_.namespace[p] ):
        self.params_.namespace[p] = E.normpath(self.params_.namespace[p])

    # Modify also DATA_DIRS -- we work on the actual map, not a copy
    data_dirs = self.var("DATA_DIRS")
    if type(data_dirs) == type({}):
      for key, value in data_dirs.items():
        if value: data_dirs[key] = E.normpath(value)

    # Update ent home from the actual parameter
    self.ent_home_ = self.var('ENTERPRISE_HOME')

    return true

  # Read only mode also implies no implicit config manager requests from
  # set_var/del_var etc.
  def SetReadOnly(self):
    threadsafegoogleconfig.ThreadsafeConfig.SetReadOnly(self)
    self.allow_config_mgr_requests_ = 0

  # Should only be called by AdminRunner
  def Save(self, _=sys.stdout, dummy=None):
    """
    Save crawl parameters to the object's type specific config file.
    Returns false if saving failed, true otherwise
    """

    if self.ReadOnly():
      return true

    logging.info("Saving parameters to %s" % self.config_file_)

    # we write to a temp file, then move to avoid writing partial files
    temp_conf = self.config_file_ + "_temp";

    self.params_lock_.acquire()
    old_config_mgr_state = self.get_allow_config_mgr_requests()
    self.set_allow_config_mgr_requests(0)
    try:
      etc_file     = "%s/%s" % (self.var('ENT_DISK_ROOT'), C.ETC_SYSCONFIG)
      tmp_etc_file = "%s/tmp/enterprise_config_temp" % \
                     self.var('ENT_DISK_ROOT')

      # Write the etc params in a format compatible with older versions
      etc_params   = "ENT_ALL_MACHINES=%s\n"\
                     "MACHINES=%s\n"\
                     "ENT_CONFIG_TYPE=%s\n" % (
        repr(string.join(self.var('ENT_ALL_MACHINES'), ",")),
        repr(string.join(self.var('MACHINES'), ",")),
        repr(self.var('ENT_CONFIG_TYPE')))
      f = open(tmp_etc_file, "w")
      f.write(etc_params)
      os.fdatasync(f.fileno())
      f.close()

      # INCLUDES is written only when we write the config. We can't have
      # it in update_derived_info as many programs don't have access to
      # /etc/sysconfig/... For example, install.py can't load this file.
      self.set_var('INCLUDES', {etc_file: {}})
      params_to_write = self.GetVarsToWrite()
      params_to_write.append('INCLUDES')
      self.write_params(temp_conf, params_to_write);

      # move the temp files to the real destinations
      renames  = [(temp_conf,    self.config_file_),
                  (tmp_etc_file, etc_file),
                  ]
      for (src, dest) in renames:
        try:
          # Only update the file when the content is actually changed
          if not os.system("diff %s %s &> /dev/null" % (src, dest)):
            os.remove(src)
          else:
            os.rename(src, dest)
        except OSError, e:
          logging.error("Error remove %s or move %s to %s [%s]"
                        % (src, src, dest, e))
          return false

        self.add_file_to_distribute(dest, "CONFIG_REPLICAS")

    finally:
      # Restore config_mgr_requests
      self.set_allow_config_mgr_requests(old_config_mgr_state)
      self.params_lock_.release()

    return true


  # GetDataDir - get the data dir associated with a machine port.
  # in enterprise mode, we currently ignore port because we don't
  # have a directory per shard or per type, although this will change in the future.
  def GetDataDir(self, port, shareable=0):
    return threadsafegoogleconfig.ThreadsafeConfig.GetDataDir(self,
                                                              port,
                                                              shareable)
  #############################################################################
  #
  # We override the variable setting functions
  #
  def set_var(self, name, value, validate = 0) :
    """
    This updates a parameter. We override this in order to write the
    config manager request
    """
    # 1. Get the old value so we write a cm req only if value changes
    # 2. We don't need to synchronize this, because if someone comes in
    #    in between there is a race condition we don't controll the order
    #    anyw
    if self.has_var(name) and value == self.var(name):
      return validatorlib.VALID_OK

    error = threadsafegoogleconfig.ThreadsafeConfig.set_var(
      self, name, value, validate)
    if (error in validatorlib.VALID_CODES and
        name != "CONFIGVERSION"):
      # Force the update anyway because we want the side effects pushed
      if not self.WriteConfigManagerUpdateRequest(
        name, value, 'set_var', 1, not validate):
        return [validatorlib.ValidationError(
          "Parameters did not save correctly")]

    # 3. This is for the parameters that ask for an update of the
    # servers map
    if name in self.requires_update_allocation_map():
      self.update_machine_allocation_map()

    return error

  # After machine allocation we need to call this
  # to ensure that update_derived_info and update_machine_allocation_map
  # are called to update the required parameters
  def force_set_var_for_propagation(self, name):
    error = threadsafegoogleconfig.ThreadsafeConfig.set_var(
      self, name, self.var(name), 0)
    if error not in validatorlib.VALID_CODES:
      return error
    if name in self.requires_update_allocation_map():
      self.update_machine_allocation_map()
    return error

  def del_var(self, name):
    """
    This deletes a parameter. We override this in order to write the
    config manager request
    """
    if not threadsafegoogleconfig.ThreadsafeConfig.del_var(self, name):
      return 0

    if not self.WriteConfigManagerUpdateRequest(
      name, None, 'del_var', 1, 0):
      return 0

    return 1
#
#  TODO we might need it for some things like synonyms file
#

#  def set_file_var_content(self, name, value, validate = 0):
#    """
#    This updates a parameter. We override this in order to write the
#    config manager request
#    """
#    error = threadsafegoogleconfig.ThreadsafeConfig.set_file_var_content(
#      self, name, value, validate)
#    if error in validatorlib.VALID_CODES:
#      if not self.WriteConfigManagerUpdateRequest(name, self.var(name),
#                                                  'set_file_var_content', 1,
#                                                  not validate):
#        return [validatorlib.ValidationError(
#          "Parameters did not save correctly")]
#    return error
#
#  def del_file_var_content(self, name):
#    """
#    This deletes the file associated with a file parameter.
#    """
#
#    if not threadsafegoogleconfig.ThreadsafeConfig.del_file_var_content(self,
#                                                                        name):
#      return 0
#
#    if not self.WriteConfigManagerUpdateRequest(name, None,
#                                                'del_file_var_content', 0, 0):
#      return 0
#
#    return 1

  #############################################################################
  #
  # Member access
  #

  def GetEntNumShards(self):
    """Returns the number of shards"""
    return self.var("ENT_NUM_SHARDS")

  def GetEntHome(self):
    """ Returns enterprise home dir """
    return self.ent_home_

  def ComposeConfigFileName(self, enthome):
    """ Return the global parameters file given the home """
    # For test / extracting version
    if enthome == None:
      return None
    return E.normpath("%s/local/conf/google_config" % enthome)

  #############################################################################
  #
  # Config manager requests
  #
  def get_allow_config_mgr_requests(self):
    return self.allow_config_mgr_requests_

  def set_allow_config_mgr_requests(self, val):
    self.allow_config_mgr_requests_ = val

  # We never update configs using config manger. The config is already
  # updated by the adminrunner.
  def WriteConfigManagerUpdateRequest(self, param, value,
                                      op, force_update, force_no_validate):
    # normalize param name; len == 1 -> string, len > 1 -> tuple
    param = googleconfig.makeTupleName(param)
    if len(param) == 1: param = param[0]

    if not self.get_allow_config_mgr_requests(): return true
    req = update_requests.ConfigUpdateRequest()

    # by default config manger opens entconfig in readonly mode so it
    # doesn't update the config
    req.Set(param, value, op, force_update, force_no_validate,
            self.ComposeConfigFileName(self.GetEntHome()))
    return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerServeRestartRequest(self):
    if not self.get_allow_config_mgr_requests(): return true
    req = server_requests.RestartEntServingRequest()
    req.Set(self.ComposeConfigFileName(self.GetEntHome()))
    return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerServerRestartRequest(self, machine, port):
    if not self.get_allow_config_mgr_requests(): return true
    req = server_requests.RestartServerRequest()
    req.Set(machine, port, self.ComposeConfigFileName(self.GetEntHome()))
    return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerServerKillRequest(self, machine, port):
    if not self.get_allow_config_mgr_requests(): return true
    req = server_requests.RestartServerRequest()
    req.Set(machine, port, self.ComposeConfigFileName(self.GetEntHome()),
            kill_only=1)
    return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerServerTypeRestartRequest(self, servertype):
    """
    Writes a multi request that restarts all the servers of the
    specified type (servertype)
    """
    if not self.get_allow_config_mgr_requests(): return true

    req = server_requests.RestartServerRequest()
    req.Set("dummy", 1, self.ComposeConfigFileName(self.GetEntHome()))

    # The actual requests that spawns all send server command requests
    the_req = configmgr_request.MultiRequestCreateRequest()
    the_req.Set(req.datadict, servertype,
                server_requests.MACHINE, server_requests.PORT,
                # Thes request goes to the sys config
                self.ComposeConfigFileName(self.GetEntHome()))

    return self.WriteConfigManagerRequest(the_req)

  def WriteSendServerCommandRequest(self, servertype, command, expected_ack):
    """
    Writes a MultiRequestCreateRequest that creates requests to talk a command
    to all servers of a type
    """
    if not self.get_allow_config_mgr_requests(): return true

    # dummy
    req = server_requests.SendServerCommandRequest()
    req.Set("dummy", 1, command, expected_ack,
            # Thes request goes to the sys config
            self.ComposeConfigFileName(self.GetEntHome()))

    # The actual requests that spawns all send server command requests
    the_req = configmgr_request.MultiRequestCreateRequest()
    the_req.Set(req.datadict, servertype,
                server_requests.MACHINE, server_requests.PORT,
                # Thes request goes to the sys config
                self.ComposeConfigFileName(self.GetEntHome()))

    return self.WriteConfigManagerRequest(the_req)

  def WriteConfigManagerReplaceRoleRequest(self, role, new_machine, old_machine):
    return true
    #if not self.get_allow_config_mgr_requests(): return true
    #req = machine_requests.RoleReplaceRequest()
    #req.Set(role, new_machine, old_machine,
    #                       self.ComposeConfigFileName(self.GetEntHome()))
    #return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerEpochDeleteRequest(self, epochs, types):
    if not self.get_allow_config_mgr_requests(): return true
    req = epoch_requests.EpochDeleteRequest()
    req.Set(epochs, types, self.ComposeConfigFileName(self.GetEntHome()))
    return self.WriteConfigManagerRequest(req)

  def WriteConfigManagerEpochAdvanceRequest(self, epoch, types):
    if not self.get_allow_config_mgr_requests(): return true
    req = epoch_requests.EpochAdvanceRequest()
    req.Set(epoch, types, self.ComposeConfigFileName(self.GetEntHome()))
    return self.WriteConfigManagerRequest(req)

  # replace old_value with new_value. If old_value is None, we just want
  # to add new_value, but if old_value is none, we add new_value only if
  # the old value is found.
  def ReplaceValueInList(self, old_list, old_value, new_value):
    can_add = true
    if old_value:
      if old_value in old_list:
        old_list.remove(old_value)
      else:
        can_add = false

    if can_add and new_value and new_value not in old_list:
      old_list.append(new_value)

  def ReplaceVarInParam(self, param_name, new_value, old_value):
    """
    if old_value is None, we just append new_value.
    if new_value is None we simply remove old_value.
    if old_value is not None and it doesn't exist, we don't add new_value
       for maps, we do this for each key,value pair.
    """
    logging.info("replacing %s by %s in %s" % (old_value, new_value,
                                               param_name))
    current_value = self.var_copy(param_name)
    if type(current_value) == type({}):
      for (key, kvalue) in current_value.items():
        self.ReplaceValueInList(kvalue, old_value, new_value)
    elif type(current_value) == type([]):
      self.ReplaceValueInList(current_value, old_value, new_value)
    else:
      logging.error("Unhandled type")
    logging.info("final value %s" % repr(current_value))
    self.set_var(param_name, current_value, true)


  #############################################################################
  #
  # The next functions are supposed to be PROTECTED / PRIVATE
  #
  #############################################################################

  # helper function to delete a server from the server map
  def remove_server(self, server_map, server):
    """Remove a server from the server map.

    Args:
      server_map: dictionary mapping ports to server names
      server: name of server to remove

    Returns:
      None
    """
    # Removing the ports associated with the server.
    min_port = servertype.GetPortMin(server)
    max_port = servertype.GetPortMax(server)
    for port in range(min_port, max_port):
      if server_map.has_key(port):
        logging.info("Removing key %d from servers" % port)
        del server_map[port]


  # Some things make necessary to set the allocation map
  def requires_update_allocation_map(self):
    """
    This is entconfig specific: when we set parameters we have to call
    update_machine_allocation_map. Note that we cannot use the
    update_derived_info for this because we will get in loop, since
    update_machine_allocation_map changes servers which calls
    update_derived_info -- NOTE: these [arameters should not be set in
    update_derived_info
    """
    return  ['MACHINES', 'MASTER', 'ENT_LICENSE_INFORMATION']

  # Updates the SERVERS map given the current machine allocations
  # This is called after update_derived_info, so everything is
  # available.
  def update_machine_allocation_map(self):
    """
    Builds the server map. This should be called on load. It overrides
    some servers given in SERVERS map.
    Note that SERVERS are a base parmeter and cannot be derived.
    """

    self.params_lock_.acquire()
    try:

      # read the current allocation
      servers = self.var_copy('SERVERS')
      machines = self.var('MACHINES')
      master = self.var('MASTER')
      gfs_cell = self.var('GFS_CELL')

      # checks if the ports are shifted -- and if it is, then it
      # switches it to normal
      if self.is_shifted_server_map(servers):
        servers = self.testing_servers_conversion(servers, -1)

      # TODO remove work* things from master
      master_servers = ['config_manager']

      # Now override some servers according to these rules
      # Note: SERVERS enteries can be assigned as lists or strings, but
      # while reading any entry, it is always a list.
      if master:
        for srvr in master_servers:
          servers[servertype.GetPortBase(srvr)] = master

      license_info = self.var('ENT_LICENSE_INFORMATION')

      if not license_info.get(license_api.S.ENT_LICENSE_QUERY_EXPANSION):
        self.remove_server(servers, 'qrewrite')

      if not license_info.get(license_api.S.ENT_LICENSE_CLUSTERING):
        self.remove_server(servers, 'clustering_server')

      if not license_info.get(license_api.S.ENT_LICENSE_DATABASES):
        self.remove_server(servers, 'enttableserver')

      if not license_info.get(license_api.S.ENT_LICENSE_CONNECTOR_FRAMEWORK):
        self.remove_server(servers, 'connectormgr')

      if not license_info.get(license_api.S.ENT_LICENSE_FEDERATION):
        self.remove_server(servers, 'ent_fedroot')

      # on the virtual GSALite, there are several servers that are NOT
      # license-controlled that are turned off: e.g. onebox, mixer, spellmixer
      if self.var('ENT_CONFIG_TYPE') == 'LITE':
        self.remove_server(servers, 'spellmixer')
        self.remove_server(servers, 'headrequestor')
        self.remove_server(servers, 'authzchecker')

      # Now fillup empty server maps for servers that do not exist.
      # Assigner will only assign machines if the required ports are in
      # the map.
      ent_num_shards = self.var('ENT_NUM_SHARDS')
      constraint_general = self.var('CONSTRAINT_GENERAL')
      if constraint_general and ent_num_shards:
        srvs = constraint_general.keys()
        srvs.remove('default')
        for srv in srvs:
          if srv in master_servers:
            continue
          # TODO remove this once we have a way to override SEVERTYPE
          # properties.
          sharded_exceptions = ['bot']
          if (srv not in sharded_exceptions and servertype.IsSharded(srv)):
            for i in range(ent_num_shards):
              port = servertype.GetPortBase(srv) + i
              if not servers.has_key(port):
                servers[port] = ''
          else:
            if srv == 'web':
              port = self.var('GWS_PORT')
            else:
              port = servertype.GetPortBase(srv)
            if not servers.has_key(port):
              servers[port] = ''

      # In testing or install mode -- shift the ports, in serve mode - remove
      # some
      state = install_utilities.install_state(
        self.var('VERSION'), rootdir = self.var('ENT_DISK_ROOT'))
      if state in ["INSTALL", "TEST"]:
        servers = self.testing_servers_conversion(servers, 1)
      elif state == "SERVE":
        servers = self.get_serve_servers(servers)

    finally:
      self.params_lock_.release()

    self.set_var('SERVERS', servers) # triggers all the server recomputation

  #############################################################################

  def add_file_to_distribute(self, fileName, machineParam, delete_file = 0):
    """
    This function adds to the to distribute list of files -- we override
    this to implement the case when machineParam is None
    """
    if not machineParam:
      machineParam = "MACHINES"
    threadsafegoogleconfig.ThreadsafeConfig.add_file_to_distribute(
      self, fileName, machineParam, delete_file)

  def get_googlebot_dir(self):
    """ Return the global parameters file """
    return E.normpath("%s/local/google3/legacy/googlebot/" % self.ent_home_)

  def get_prod_conf_dir(self):
    """ Return the global parameters file """
    return E.normpath("%s/local/google/config/" % self.ent_home_)

  def set_file_content(self, fileName, str, param = "CONFIG_REPLICAS"):
    """
    Set the content of a file on all machines in the  param list
    if param is null, it defaults to CONFIG_REPLICAS
    """
    open(fileName, "w").write(str)
    self.add_file_to_distribute(fileName, param)

  def write_params_to_string(self, paramNames):
    """
    Helper that writes parameters as if would be saved in a file
    on a string and return it
    """
    self.params_lock_.acquire()
    try:
      out = []
      for p in paramNames:
        if self.params_.namespace.has_key(p):
          out.append("%s = %s" % (p, repr(self.params_.namespace[p])))
        else:
          logging.error("Parameter %s not defined" % p)
    finally:
      self.params_lock_.release()

    return string.join(out, "\n")

  def write_params(self, filename, paramNames):
    """ Helper that writes parameters on a file """
    f = open(filename, "w")
    f.write(self.write_params_to_string(paramNames))
    os.fdatasync(f.fileno())
    f.close()

  def get_next_config_manager_request_file_id(self, dir = None):
    """
    We override this to provide a differentiation between requests written
    from different processes (adminrunner/configmanger)
    """
    (id, filename) = threadsafegoogleconfig.ThreadsafeConfig.\
                     get_next_config_manager_request_file_id(self, dir)
    filename = "%s_%d_%s" % (filename, os.getpid(),
                          string.split("%s" % repr(time.time()), '.')[1])
    return (id, filename)

  #############################################################################

  def DistributeAll(self, retry=0):
    """
    DistributeAll : We override this because PutFilesOnMachines uses signal
    and this is not possible for a multithreading application
    """
    to_distribute = {}
    self.distr_lock_.acquire()
    try:
      to_distribute = copy.deepcopy(self.to_distribute_)
      self.to_distribute_ = {}
    finally:
      self.distr_lock_.release()

    machines_dict = {}
    self.params_lock_.acquire()
    try:
      def getParamMachines(machines):
        """Given a param, get the machines associated with it"""
        if not machines: return []
        if isinstance(machines, types.DictionaryType):
          m = [];
          m.extend(machines.values())
          machines = m
          reduce(lambda x,y: x.extend(y), machines)
          if len(machines) > 0: machines = machines[0]
        return machines

      for param in to_distribute.keys():
        machines_dict[param] = getParamMachines(self.var(param))
    finally:
      self.params_lock_.release()

    self.distr_lock_.acquire()
    try:
      def splitFiles(fileSet):
        """split files into delete and distribute sets"""
        to_distribute = []
        to_delete = []
        for file, delete_file in fileSet:
          if delete_file:
            to_delete.append(file)
          else:
            to_distribute.append(file)
        return to_distribute, to_delete

      for param, fileSet in to_distribute.items():
        machines = machines_dict[param]
        to_distribute, to_delete = splitFiles(fileSet)

        if len(machines) > 0 and len(to_distribute) > 0:
          if self.batch_mode_:
            for file in to_distribute:
              if not self.batch_updates_list_.has_key(file):
                self.batch_updates_list_[file] = len(self.batch_updates_list_)
          else:
            ret = E.distribute(machines, string.join(to_distribute, " "), true,
                               1, retry)
            if ret:
              logging.error('Distribute operation failed with error %s.' % ret)

        if len(machines) > 0 and len(to_delete) > 0:
          # Batch updates is not supposed to handle deletion of files.
          # It is a mistake to use it in a context where files may be
          # deleted.
          assert(not self.batch_mode_)
          E.rm(machines, string.join(to_delete, " "))

    finally:
      self.distr_lock_.release()


  def testing_servers_conversion(self, servers, to_testing):
    """
    Returns a modified copy of servers that work for the testing state
    to_testing -- +1 -> to testing -1 -> from testing
    """
    ret = {}
    for port, val in servers.items():
      mtype = servertype.GetPortType(port)
      if SERVERS_PROCESS_DATA.has_key(mtype):
        # Incremtent the port of the special servers
        ret[port + to_testing * SERVERS_PROCESS_DATA[mtype]] = val
      else:
        # Others are left alone
        ret[port] = val
    return ret

  def get_serve_servers(self, servers):
    """
    Returns a modified copy of servers that work for the serving state
    """
    # First we don't allow base indexers. If no rtslaves are available,
    # we make base_indexers rt slaves
    min_port = servertype.GetPortMin('rtslave')
    max_port = servertype.GetPortMax('rtslave')
    rtslave_ports = filter(
      lambda p, m = min_port, M = max_port: p >= m and p < M,
      servers.keys())
    base_indexers_slaves = len(rtslave_ports) == 0

    # Now, go and do the transformation
    ret = {}
    for port, val in servers.items():
      mtype = servertype.GetPortType(port)
      # If type is common -- keep it
      if SERVERS_PROCESS_DATA.has_key(mtype):
        ret[port] = val
      else:
        # One more chance - is base_indexer and we have no rtslaves
        if base_indexers_slaves and mtype == 'base_indexer':
          ret[min_port + port - servertype.GetPortMin('base_indexer')] = val

    return ret

  def is_shifted_server_map(self, servers):
    """
    Checks if the given servers map is shifted (by looking at mixer port)
    """
    if servers.has_key(servertype.GetPortBase('mixer') +
                       SERVERS_PROCESS_DATA['mixer']):
      return true
    return false


  def AdjustProcUsageIfUniprocessorKernel(self, constraint_general):
    """
    Reduce the cpumhz resource usage of each service proportionately
    if we are running on a uni-processor environment.
    """
    # Assumption: All nodes have same number of active processors
    uniprocessor = false

    try:
      # Use /proc/cpuinfo since it has the actual number of active processors
      f = open("/proc/cpuinfo","r")

      # By splitting on the word "processor", you get # of processors + 1
      # so reduce by one to get the actual number of processors
      num_procs = len(f.read().split("processor")) - 1
      f.close()

      if num_procs <= 1:
        uniprocessor = true

    except IOError:
      logging.error("Unable to open /proc/cpuinfo. Assuming uniprocessor")
      uniprocessor = true


    if not uniprocessor:
      # NOISE
      # logging.info("Not running on a uniprocessor kernel")
      return

    # Now for the hack...
    srvs = constraint_general.keys()
    for service in srvs:
      constraints = constraint_general[service]
      # Don't bother if we don't have a resource constraint
      if not constraints.has_key('resource'):
        continue
      if not len(constraints['resource']) == 1:
        raise Exception('Resource is expected to have exactly one string')
      val_of_resource = constraints['resource'][0]  # like 'cpumhz:100, ram:100'
      resources = string.split(val_of_resource, ',')  # ['cpumhz:100','ram:100']
      new_resources = []
      for res_val in resources:
        # res_val is of the form 'cpumhz:100' or 'ram:100'
        strs = string.split(res_val, ':')
        if len(strs) != 2:
          raise Exception('%s is not of the form str:num ??' % res_val)
        if strs[0] == 'cpumhz':
          new_resources.append("cpumhz:%d" % (int(strs[1])/3))  # third of orig
        else:
          new_resources.append(res_val)   # as it...
      constraint_general[service]['resource'] = [string.join(new_resources, ',')]


  #############################################################################

  def get_derived_info_dependencies(self):
    # NOTE: this list should contain all the vars used in PART 1 of
    # update_derived_info()
    return threadsafegoogleconfig.ThreadsafeConfig.get_derived_info_dependencies(self) + [
      'USER_AGENT_TO_SEND', 'PROBLEM_EMAIL', 'ENT_CONFIG_NAME',
      'VERSION', 'MACHINES', 'ENT_NUM_SHARDS', 'URLSERVER_DEFAULT_HOSTLOAD',
      'ENT_DISK_ROOT', 'SERVERS',
      'MASTER', 'ENT_ALL_MACHINES', 'DATACHUNKDISKS',
      'ENT_COLLECTIONS', 'ENT_FRONTENDS',
      'ENT_QUERY_EXP',
      'ENT_LICENSE_INFORMATION',
      'ENT_SPELL_SERVING_ID',
      'URLSCHEDULER_MIN_SAMPLES', 'URLSCHEDULER_REFRESH_FRACTION',
      'RTSERVER_DOCID_LEVELS',
      'USER_MAX_CRAWLED_URLS', 'ENT_CONFIG_TYPE',
      'URLTRACKER_DIRECTORY',
      ]


  # TODO: This function is just a temporary fix and, as soon as we have a
  # stable production kernel, we should replace this function with an
  # appropriate constant.
  def get_max_mmap_memory(self):
    """What is the max memory that a process  can mmap?  This is based on the
       max memory a process can address and that, in turn, is based on the
       kernel being used"""

    global MAX_MMAP_MEMORY_CACHE
    if MAX_MMAP_MEMORY_CACHE is not None:
      return MAX_MMAP_MEMORY_CACHE

    # By default, a standard kernel gives a process 2GB address space.
    # That's the number we go with unless a known kernel provides a
    # different number.
    address_space = 2L << 30

    # We allow a process to mmap 75% of this number so that it has space left
    # for its miscellaneous memory needs as well as to minimize fragmentation.
    MAX_MMAP_MEMORY_CACHE = long(address_space * 3 / 4)

    # If we run on a 64bit kernel, then we have 64bit rtserver binary.
    (status, output) = E.getstatusoutput('uname -m')
    if E.ERR_OK == status and output.startswith('x86_64'):
      address_space = 4L << 30
      if self.var('ENT_CONFIG_TYPE') == 'SUPER':
        # On SuperGSA platform, give rtslave 12GB of MAX_MMAP_MEMORY_CACHE.
        MAX_MMAP_MEMORY_CACHE = 12L << 30
      else:
        # On Dell oneway platform, give rtslave 4GB of MAX_MMAP_MEMORY_CACHE.
        MAX_MMAP_MEMORY_CACHE = 4L << 30

    logging.info('Assigning address_space: %s' % address_space)
    return MAX_MMAP_MEMORY_CACHE


  def update_derived_info(self):

    # call our super class first
    threadsafegoogleconfig.ThreadsafeConfig.update_derived_info(self)

    # Note: This method will set all params whose values depend on other
    # already set parameters.  Some of these may not be set, so we need to
    # excercise caution.
    #
    # The general structure of this method is as follows:
    # - first, we get the value of all the params that we depend on
    # - parameters that depend on the same parameters are grouped together;
    #   each group of them starts with a test to make sure that the values are
    #   valid enough to use them
    # - each group block should test for ALL params that it depends on
    # - a group block can depend on params straight from the config file or
    #   implicit parameters computed by this method, but the latter should
    #   only depend on implicits from PART 2 (below); there should be no
    #   cross group intermediate values used.
    #
    # Try and follow the above rules to keep this code from becoming a HUGE
    # mess.

    ########################################
    # PART 1 #

    # get everything we plan to use
    # NOTE: all of these vars should be in get_derived_info_dependencies()
    user_agent_to_send = self.var('USER_AGENT_TO_SEND')
    problem_email = self.var('PROBLEM_EMAIL')
    ent_config_name = self.var('ENT_CONFIG_NAME')
    ent_config_type = self.var('ENT_CONFIG_TYPE')
    version = self.var('VERSION')
    machines = self.var('MACHINES')
    ent_num_shards = self.var('ENT_NUM_SHARDS')
    urlserver_default_hostload = self.var('URLSERVER_DEFAULT_HOSTLOAD')
    ent_disk_root = self.var('ENT_DISK_ROOT')
    master = self.var('MASTER')
    servers = self.var('SERVERS')
    ent_all_machines = self.var('ENT_ALL_MACHINES')
    datachunkdisks = self.var('DATACHUNKDISKS')
    ent_collections = self.var('ENT_COLLECTIONS')
    ent_frontends = self.var('ENT_FRONTENDS')
    ent_query_exp = self.var('ENT_QUERY_EXP')
    urlscheduler_min_samples = self.var('URLSCHEDULER_MIN_SAMPLES')
    is_cluster = self.var('ENT_CONFIG_TYPE') == 'CLUSTER'
    ramfs_root = self.var('RT_RAMFS_ROOT')
    urltracker_directory = self.var('URLTRACKER_DIRECTORY')

    license_info = self.var('ENT_LICENSE_INFORMATION')
    user_defined_limit = self.var('USER_MAX_CRAWLED_URLS')
    urlscheduler_refresh_fraction = self.var('URLSCHEDULER_REFRESH_FRACTION')
    rtserver_docid_levels = self.var('RTSERVER_DOCID_LEVELS')
    state = install_utilities.install_state(
      self.var('VERSION'), rootdir = self.var('ENT_DISK_ROOT'))

    # Ensure trailing not trailing / in root
    if ent_disk_root != None:
      ent_disk_root = E.normpath(ent_disk_root)

    ########################################
    # PART 2 #

    # next, compute any implicit parameters that will be needed by multiple
    # group blocks below; these get stored into local vars, but we don't worry
    # about setting the actual parameters; this will get taken care of later

    xslt_stylesheets_dir = None
    xslt_test_stylesheets_dir = None
    frontends_dir = None
    enterprise_home = None
    googledata = None
    configdir = None
    gfs_cell = None
    gfs_root_dir = None

    hda3_only_disks = {}
    namespace_prefix = None
    output_namespace_prefix = None
    log_dir = None
    data_dirs = {}  # DATADIRS will get filled out in a lot of places
    rt_ram_dir = None
    max_rtslaves_per_node = 1

    if ent_disk_root != None:
      self.set_var('VMANAGER_PASSWD_FILE',
                   E.normpath('%s/export/hda3/versionmanager/vmanager_passwd' %
                              ent_disk_root))

    # old versions know MACHINES and ENT_ALL_MACHINES as comma separated lists
    if type(machines) == type(""):
      machines = map(string.strip, string.split(machines, ","))
    if type(ent_all_machines) == type(""):
      ent_all_machines = map(string.strip, string.split(ent_all_machines, ","))


    if version and ent_disk_root != None:
      enterprise_home = E.normpath('%s/export/hda3/%s' % (
        ent_disk_root, version))
      googledata = E.normpath('%s/local/googledata' % enterprise_home)
      configdir = E.normpath('%s/local/conf' % enterprise_home)

    # Check to see if ramfs_root is really mounted.  If not, ignore it.
    # We are only checking on the machine that this script runs on and
    # rtslave could be running on any other machine in the cluster, but
    # we have the same  configuration on all machines in a cluster, so that
    # isn't a problem.
    ramfs_is_mounted = 0
    if ramfs_root:
      (s, o) = E.getstatusoutput('mount | grep %s' % ramfs_root)
      ramfs_is_mounted = (s == 0)

    # Ram is shared across all versions, so use it only where it is useful.
    # Use it only for versions in ACTIVE or SERVE state.  We don't want to
    # use it for TEST state because typically when we have one verison in
    # TEST state there is another in SERVE state which is actually doing
    # the serving.  We'd rather give it to SERVEr than TESTer.  We want to
    # use it for only one version at a time.
    if ramfs_is_mounted and (state in ["ACTIVE", "SERVE"]):
      rt_ram_dir = ramfs_root

    # TBD: Disable it for now - Increasing memory isn't helping, it is
    # deteriorating latency for a chunk of queries.  We'll have to figure
    # it out some day.  -praveen
    rt_ram_dir = None

    if googledata:
      xslt_stylesheets_dir = E.joinpaths([googledata, 'gws/stylesheets'])
      # Loading the test stylesheets from the same directory
      # We used to load the test styleshees from user dir (user_stylesheets)
      xslt_test_stylesheets_dir = E.normpath('%s/gws/stylesheets' % googledata)

    # GFS requires at least 3 machines to be there. We base our decision
    # to activate GFS upon the number of machines we have at birth
    # of the cluster. We don't want any cluster to deactivate gfs
    # automatically after loosing some machines.
    if ent_all_machines and len(ent_all_machines) >= 3:
      gfs_cell = core_utils.GFS_CELL

    if gfs_cell:
      namespace_prefix = '/gfs/%s/' % gfs_cell
      output_namespace_prefix = {
        'pr_main': '/gfs/%s/pr_main/' % gfs_cell,
      }
      spell_root_dir = "%s/spelling" % namespace_prefix
    else:
      namespace_prefix = '/bigfile/'
      spell_root_dir = "%s/spelling" % enterprise_home

    if enterprise_home:
      gfs_root_dir = '%s/data' % enterprise_home

    for (host,disks) in datachunkdisks.items():
      hda3_only_disks[host] = ['/export/hda3']

    if ent_disk_root != None:
      log_dir = E.normpath("%s/export/hda3/logs" % ent_disk_root)

    is_cluster = ent_all_machines and len(ent_all_machines) > 1
    if state in ('INSTALL', 'TEST'):
      sessionmanager_aliases = core_utils.GetSessionManagerAliases(version, 1,
                                                                   is_cluster)
    else:
      sessionmanager_aliases = core_utils.GetSessionManagerAliases(version, 0,
                                                                   is_cluster)

    if ent_all_machines and len(ent_all_machines) > 1:  # cluster
      master = core_utils.MakeGSAMasterPath(version)
      self.set_var('GSA_MASTER', master)
      self.set_var('ENT_DASH_VER_NAME', core_utils.GetCellName(version))

      # we use the prefix variable as substring for ellection commisionaire
      # code we can therefore not give it a full DNS name, as election
      # commisionaire composes that name, this string sessionmanager would be
      # changed to somethg like 'sessionmanager-master.ent5-1-1.ls.google.com'
      # for EnterpriseFrontend and Authzchecker we need to pass on the
      # variables mentioning the servername:port, we do it using the
      # SESSIONMANAGER_ALIASES config variable
      self.set_var('SESSIONMANAGER_PREFIX', 'sessionmanager')
    else:  # one-way or mini
      self.set_var('GSA_MASTER', 'localhost')
      self.set_var('ENT_DASH_VER_NAME', 'localhost')
      self.set_var('SESSIONMANAGER_PREFIX', 'localhost')

    self.set_var('SESSIONMANAGER_ALIASES', sessionmanager_aliases)

    # Get labs settings and unpack.
    # labs_settings is a space-separated list of name=value pairs.
    labs_settings = license_info.get(license_api.S.ENT_LICENSE_LABS_SETTINGS)
    labs_params = ent_license.UnpackLabsSettings(labs_settings)

    ########################################
    # PART 3 #

    # Note: all the below groups should depend only on params from PART 1
    #       and PART2 above; NO intermediate values between groups

    # SuperGSA specific config changes
    if self.var('ENT_CONFIG_TYPE') == 'SUPER':
      self.set_var('RTSERVER_MAX_OUTSTANDING_INDEX_FILES', 48)
      self.set_var('WORKERTHREADS', 20)
      self.set_var('ENTFRONT_NUM_THREADS', 20)
      self.set_var('MIXER_INDEX_NUMCONN', 20)
      self.set_var('MIXER_DOC_NUMCONN', 20)
      self.set_var('MIXER_LINK_NUMCONN', 20)
      self.set_var('MIXER_CACHE_NUMCONN', 18)
      self.set_var('MIXER_DEFAULT_NUMCONN', 20)
      self.set_var('GWS_DEFAULT_NUMCONN', 20)
      self.set_var('GWS_MIXER_NUMCONN', 20)

    # TODO(hotti): There is no urlserver/contentfilter/bot anymore...
    # urlserver
    self.set_var('DEFAULT_GOAL_INFLIGHT_PER_HOST', 50000)
    self.set_var('MAX_INFLIGHT_PER_HOST', 200000)
    self.set_var('URLSERVER_MAX_URLMANAGER_REQUEST_SIZE', 100000)
    self.set_var('URLSERVER_DYNAMIC_MAX_INFLIGHT_PER_HOST', 1)

    # contentfilter
    self.set_var('CONTENTFILTER_MAXBUFDOCS', 10000)
    self.set_var('CONTENTFILTER_MAXBUFBYTES', 500000000)  # 500 MB
    self.set_var('CONTENTFILTER_FLUSHLOG_INTERVAL_SECS', 300)
    self.set_var('CONTENTFILTER_FLUSHLOG_MAXDOCS_PER_INDEXER', 3000)

    # bot
    self.set_var('CONTENTFILTER_CONNECTIONS', 20)

    if self.var('ENT_CONFIG_TYPE') == 'MINI':
      self.set_var('CONTENTFILTER_MAXBUFBYTES', 50000000)  # 50 MB

    if spell_root_dir:
      self.set_var('ENT_SPELL_ROOT_DIR', spell_root_dir)
      spell_id_conf_name = 'ENT_SPELL_SERVING_ID'
      if self.has_var(spell_id_conf_name):
        new_path = "%s/spell-%d" % (
                   spell_root_dir, self.var(spell_id_conf_name))
        self.set_var('SPELL_DIR', new_path)

    ##

    if master:
      # Set all machines as config replicas
      self.set_var('CONFIG_REPLICAS', machines)

    ##

    if ent_disk_root != None:
      self.set_var('TMPDIR',
                   E.normpath("%s/export/hda3/tmp" % ent_disk_root))
    ##

    if log_dir != None:
      self.set_var('LOGDIR', log_dir)
      self.set_var('URLSCHEDULER_MOVED_CHECKPOINT_DIR', log_dir)
    ##

    if version and ent_disk_root != None:
      self.set_var('DATACHUNK_PREFIX',
                   E.normpath('%s/%s/data' % (ent_disk_root, version)))
      self.set_var('CACHE_DATACHUNK_PREFIX',
                   E.normpath('%s/%s/querycache' % (ent_disk_root, version)))
    ##

    if enterprise_home:
      self.set_var('ENTERPRISE_HOME', enterprise_home)

      enterprise_bashrc = E.normpath('%s/local/conf/ent_bashrc' % enterprise_home)
      self.set_var('LOOP_SH_PATH',
                   '%s/local/google3/enterprise/legacy/setup/loop.sh ' % enterprise_home)

      self.set_var('CONFIG_MANAGER_REQUEST_DIR',
                   E.normpath("%s/local/conf/cmr" % enterprise_home))
      self.set_var('CONFIG_MANAGER_WORKING_DIR',
                   E.normpath("%s/local/conf/cmr_working/" % enterprise_home))
      self.set_var('BASHRC_FILE', enterprise_bashrc)
      self.set_var('ENTERPRISE_BASHRC', enterprise_bashrc)

      self.set_var('PASSWORD_FILE',
                   E.normpath('%s/local/conf/passwd' % enterprise_home))
      self.set_var('ENT_LICENSE_COUNTER_FILE',
                   E.normpath('%s/local/conf/lic_counter' % enterprise_home))
      self.set_var('ENT_LICENSE_COUNTER_FILE_BACKUP',
                   E.normpath('%s/local/conf/lic_counter.bck' % enterprise_home))
      self.set_var('ENTFRONT_MESSAGE_FILE',
                   E.normpath('%s/local/google/com/google/enterprise/util/messages.txt' % enterprise_home))
      self.set_var('ENTFRONT_STATICFILES_DIR',
                   E.normpath('%s/local/googledata/enterprise/statichtml' % enterprise_home))

      data_dirs['spellmixer'] = E.normpath('%s/spelling/spell0-data' %
                                           enterprise_home)

      cache_root_datadir = E.normpath('%s/querycache' % enterprise_home)
      self.set_var('CACHE_ROOT_DATADIR',
                   cache_root_datadir)
      data_dirs['cache']  = E.normpath("%s/cache-data" % cache_root_datadir)

      # MAIN_GOOGLE3_DIR
      # Used for google3 processes to find the main google3 directory.
      # For example /export/hda3/4.6.5/local/google3
      main_google3_dir = E.normpath('%s/local/google3' % enterprise_home)
      self.set_var('MAIN_GOOGLE3_DIR', main_google3_dir)

      # MAINDIR and stuff in it
      # Use for legacy (google, google2) processes to find the main google dir.
      # For example /export/hda3/4.6.5/local/google
      maindir = E.normpath('%s/local/google' % enterprise_home)
      self.set_var('MAINDIR', maindir)
      self.set_var('GOOGLEBOT_DIR', E.normpath('%s/legacy/googlebot' % main_google3_dir))
      self.set_var('WORKSCHEDULER_FEED_DOC_DELETER_BINARY',
                   E.normpath('%s/bin/feed_doc_deleter' % maindir))
      self.set_var('WORKSCHEDULER_RIPPER_BINARY',
                   E.normpath('%s/bin/ripper' % maindir))
      self.set_var('WORKSCHEDULER_FIELDBUILDER_BINARY',
                   E.normpath('%s/bin/fieldbuilder' % maindir))
      self.set_var('ENTFRONT_COLLECTION_EPOCH_PATTERNS',
                   E.normpath("%s/local/conf/collections/*/epochs_serving" %
                              enterprise_home))
      bin_dir = E.normpath('%s/bin' % maindir)
      prod_bins_dir = {
        # belows for serving
        'entfrontend':             bin_dir,
        'web':                     bin_dir,
        'cache':                   bin_dir,
        'onebox':                  bin_dir,
        'oneboxenterprise':        bin_dir,
        'mixer':                   bin_dir,
        'headrequestor':           bin_dir,
        'rtslave':                 bin_dir,
        'qrewrite':                bin_dir,
        'spellmixer':              bin_dir,
        'clustering_server':       bin_dir,
        'ent_fedroot':             bin_dir,

        # belows for crawling, etc.
        'workqueue-master':        bin_dir,
        'workqueue-slave':         bin_dir,
        'workschedulerserver':     bin_dir,
        'config_manager':          E.normpath('%s/local/google3/enterprise/'
            'legacy/production/configmgr' % enterprise_home),
        }
      self.set_var('BIN_DIRS', prod_bins_dir)

      ##

      # DATADISK and related
      datadisk = E.normpath('%s/data' % enterprise_home)
      self.set_var('DATADISK', datadisk)
      self.set_var('DATAROOT', datadisk)

      self.set_var('WORKQUEUE_SLAVE_SLAVEDIR',
                   '%s/data/workqueue/' % version)

      if gfs_cell:
        self.set_var('RTSLAVE_LOCAL_CACHE_DIR', '%s/rtcache' % enterprise_home)

      datadir = E.normpath("%s/%s-data" % (datadisk, "enterprise"))
      self.set_var('DATADIR', datadir)

      self.set_var('CRAWL_LOGDIR', E.normpath('%s/logs' % datadir))
      data_dirs['google'] = datadir
      ##
    ##

    if googledata:
      self.set_var('GOOGLEDATA', googledata)

      self.set_var('CJK_UNIGRAM_MODEL',
                   E.normpath('%s/i18n/cjk-unigram-model.data' % googledata))

      self.set_var('ONEBOX_SYNONYMDIR',
                   E.normpath('%s/gws/clients' % googledata))

      self.set_var('STATIC_FILES_DIR',
                   E.normpath('%s/enterprise/statichtml' % googledata))

      # ENTERPRISEDATA and stuff in it
      enterprisedata = '%s/enterprise/data' % googledata  # used later
      self.set_var('ENTERPRISEDATA', E.normpath(enterprisedata))

      # Removed following line from global_default_files as current AdminConsole
      # do not support the mechanism for user to specify patterns for feed_urls.
      # TODO: Re-put this back in when we add feature in AdminConsole.
      # 'FEED_URLS'  : '%s/feed_goodurls.enterprise' % enterprisedata,
      global_default_files = {
        'STARTURLS' : '%s/starturls.enterprise' % enterprisedata,
        'GOODURLS'  : '%s/goodurls.enterprise' % enterprisedata,
        'FEDERATION': None,
        'URLMANAGER_REFRESH_URLS'  : \
                      '%s/frequently_changing_urls.enterprise' % enterprisedata,
        'URLSCHEDULER_ARCHIVE_URLS'  : \
                      '%s/archive_urls.enterprise' % enterprisedata,
        'DATABASES'  : '%s/databases.enterprise' % enterprisedata,
        'BADURLS'   : '%s/badurls.enterprise' % enterprisedata,
        'BYPASS_ROBOTS' : '%s/bypass_robots.enterprise' % enterprisedata,
        'COOKIE_RULES' : '%s/cookierules.enterprise' % enterprisedata,
        'GOODPROTS' :  '%s/goodprotocols.enterprise' % enterprisedata,
        'RAW_URL_REWRITE_RULES_BASENAME' : '%s/rewrite_rules.enterprise' % enterprisedata,
        'ENTFRONT_KEY_STORE' : '%s/local/conf/server.p12' % enterprise_home,
        'LDAP_CONFIG' : None,
        # [Kerberos/IWA] - UI scratchpad file for Kerberos config data (e.g., KDC)
        # [Kerberos/IWA] - UI scratchpad file for Kerberos imported keytab file
        'KERBEROS_CONFIG' : None,       # [Kerberos/IWA]
        'KERBEROS_KEYTAB' : None,       # [Kerberos/IWA]
        # [Kerberos/IWA] - Active/live/valid/etc krb5.conf file for Kerberos/IWA
        # [Kerberos/IWA] - Active/live/valid/etc krb5.keytab file for Kerberos/IWA
        'KERBEROS_KRB5_CONF' : None,    # [Kerberos/IWA]
        'KERBEROS_KRB5_KEYTAB' : None,  # [Kerberos/IWA]
        # [Kerberos/IWA] - end.
        'DATEPATTERNS' :  '%s/datepatterns.enterprise' % enterprisedata,
        'DUPHOSTS'  : '%s/duphosts.enterprise' % enterprisedata,
        'HOSTLOADS'  : None,
        'CONNECTOR_LOADS'  : None,
        'CONNECTOR_MGRS'  : '%s/connector/managers.xml' % enterprisedata,
        'CONNECTORS'  : '%s/connector/connectors.xml' % enterprisedata,
        'DATABASELOADS' : None,
        'PROXY_CONFIG'  : None,
        'DEPTH0HOSTS'  : None,
        'EXTRA_HTTP_HDRS_CONFIG'  : None,
        # [Kerberos/IWA] - Admin UI config file for user+password+realm/domain+etc
        'CRAWL_KERBEROS_CONFIG'    : None,  # [Kerberos/IWA]
        'CRAWL_USERPASSWD_CONFIG'  : None,
        'SSO_PATTERN_CONFIG' : None,
        'SSO_SERVING_CONFIG' : None,
        'PAGERANKER_BATCHURLS_FILE_0'  : None,
        'PAGERANKER_BATCHURLS_FILE_1'  : None,
        'URL_REWRITE_ORIG2STAGING'  : None,
        'URL_REWRITE_STAGING2ORIG'  : None,
        'STATUSFILE_CRAWL'  : None,
        'URLS_REMOTE_FETCH_ONLY' : \
                        '%s/remote_fetches_only.enterprise' % enterprisedata,
        'URLS_LOCAL_FETCH_ONLY'  : None,
        'DUPHOSTS_MIRRORED' : '%s/duphosts_mirrored.enterprise' % enterprisedata,
        'DUPHOSTS_STAGING' : '%s/duphosts_staging.enterprise' % enterprisedata,
        'RECRAWL_URL_PATTERNS' : '%s/recrawl_url_patterns' % enterprisedata,
        'CRAWL_SCHEDULE' : None,
        'CRAWL_SCHEDULE_BITMAP' : None,
        'ONEBOX_MODULES' : '%s/oneboxes.enterprise' % enterprisedata,
        'ONEBOX_BACKEND_CONFIG' : '%s/oneboxes.enterprise.backendconfig' % enterprisedata,
        'CUSTOMER_ONEBOX' : '%s/customer-onebox.xsl' % enterprisedata,
        'ONEBOX_DEFAULT' : '%s/onebox-default.xsl' % enterprisedata,
        'ENT_STEMS_DE_SOURCE'  : '%s/google_stems_de.txt' % enterprisedata,
        'ENT_STEMS_EN_SOURCE'  : '%s/google_stems_en.txt' % enterprisedata,
        'ENT_STEMS_ES_SOURCE'  : '%s/google_stems_es.txt' % enterprisedata,
        'ENT_STEMS_FR_SOURCE'  : '%s/google_stems_fr.txt' % enterprisedata,
        'ENT_STEMS_IT_SOURCE'  : '%s/google_stems_it.txt' % enterprisedata,
        'ENT_STEMS_NL_SOURCE'  : '%s/google_stems_nl.txt' % enterprisedata,
        'ENT_STEMS_PT_SOURCE'  : '%s/google_stems_pt.txt' % enterprisedata,

        'ENT_SCORING_TEMPLATE' : \
                           '%s/scoring_template.enterprise' % enterprisedata,
        'ENT_SCORING_CONFIG' : \
                           '%s/scoring_policies.enterprise' % enterprisedata,
        }

      # Experimental (labs) features.
      if labs_params.has_key('PagerankInjection'):
        # This causes an empty file to be set up
        global_default_files['LABS_PAGERANK_INJECTION'] = None

      collection_default_files = {
        'GOODURLS'       : '%s/goodurls.enterprise' % enterprisedata,
        'BADURLS'        :  None,
        'TESTWORDS'      : None,
        'EPOCHS_SERVING' : None,
        }
      frontend_default_files = {
        'STYLESHEET'  : None,
        'STYLESHEET_TEST'  : None,
        'GOOGLEMATCH'  : None,
        'SYNONYMS'  : None,
        'BADURLS_NORETURN'  : None,
        'GOOD_IPS': '%s/sitegoodips.enterprise' % enterprisedata,
        'GWS_CAPABILITIES': '%s/gws/capabilities' % googledata,
        'DOMAIN_FILTER': None,
        'FILETYPE_FILTER': None,
        'QUERY_EXPANSION_FILTER': \
                    '%s/default_query_expansion_filter' % enterprisedata,
        'SCORING_POLICY_FILTER': None,
        'LANGUAGE_FILTER': None,
        'METATAG_FILTER': None,
        }
      query_exp_default_files = {
        'CONTENT'  : None,
        }
      self.set_var('GLOBAL_DEFAULT_FILES', global_default_files)
      self.set_var('COLLECTION_DEFAULT_FILES', collection_default_files)
      self.set_var('FRONTEND_DEFAULT_FILES', frontend_default_files)
      self.set_var('QUERY_EXP_DEFAULT_FILES', query_exp_default_files)

      self.set_var('STYLESHEET_TEMPLATE',
                   E.normpath('%s/stylesheet_template.enterprise' % enterprisedata))

      # Files for compiled customer query rewrite data
      self.set_var('QUERY_EXP_COMPILED_BLACKLIST',
                   E.normpath('%s/qrewrite.blacklist' % configdir))
      self.set_var('QUERY_EXP_COMPILED_SYNONYMS',
                   E.normpath('%s/qrewrite.synonyms' % configdir))

      # DTD for validating XML feeds. This file is also served to outside
      # clients.
      self.set_var('FEED_DTD',
                   E.normpath('%s/html/gsafeed.dtd' % googledata))

      self.set_var('URLTRACKER_FILTER_FILE',
                   E.normpath('%s/urltrackerfilter.enterprise' % enterprisedata))
      ###

      self.set_var('LANGID_CONFIG', E.normpath('%s/langid' % googledata))

      # CJKCONFIGDIR and related
      cjkconfigdir = E.normpath('%s/BasisTech' % googledata)
      self.set_var('CJKCONFIGDIR', cjkconfigdir)
      data_dirs['cjk_config_doc'] = cjkconfigdir
      data_dirs['cjk_config_gws'] = cjkconfigdir
      data_dirs['cjk_config_rt']  = cjkconfigdir
      ##
    ##

    if configdir:
      self.set_var('CONFIGDIR', configdir)
      self.set_var('CONNECTOR_CONFIGDIR', E.normpath('%s/connector' % configdir))

      rtserver_index_prefix = "enterprise"
      self.set_var('RTSERVER_INDEX_PREFIX', rtserver_index_prefix)

      starturls = 'starturls.enterprise'
      badurls = 'badurls.enterprise'
      # Removed following line from basic_config_files as current AdminConsole
      # do not support the mechanism for user to specify patters for feed_urls.
      # TODO: Re-put this back in when we add feature in AdminConsole
      # 'FEED_URLS' : 'feed_goodurls.enterprise',
      basic_config_files = {
        'STARTURLS'  : starturls,
        'DUPHOSTS'  : 'duphosts.enterprise',
        'HOSTLOADS' : 'hostloads.enterprise',
        'CONNECTOR_LOADS' : 'connectorloads.enterprise',
        'CONNECTOR_MGRS'  : 'connector/managers.xml',
        'CONNECTORS'  : 'connector/connectors.xml',
        'DATABASELOADS' : 'databaseloads.enterprise',
        'PROXY_CONFIG' : 'proxies.enterprise',
        'EXTRA_HTTP_HDRS_CONFIG' : 'extrahdrs.enterprise',
        'PAGERANKER_BATCHURLS_PREFIX' : 'pr_batch.enterprise',
        'PAGERANKER_BATCHURLS_FILE_0' : 'pr_batch.enterprise_0',
        'PAGERANKER_BATCHURLS_FILE_1' : 'pr_batch.enterprise_1',
        'URL_REWRITE_ORIG2STAGING' : 'orig2staging.enterprise',
        'URL_REWRITE_STAGING2ORIG' : 'staging2orig.enterprise',
        'RAW_URL_REWRITE_RULES_BASENAME' : 'rewrite_rules.enterprise',
        'GOODURLS' : 'goodurls.enterprise',
        'FEDERATION': 'fed_network.xml',
        'URLMANAGER_REFRESH_URLS' : \
                      'frequently_changing_urls.enterprise',
        'URLSCHEDULER_ARCHIVE_URLS' : 'archive_urls.enterprise',
        'URLS_REMOTE_FETCH_ONLY' : 'remote_fetches_only.enterprise',
        'DATABASES' : 'databases.enterprise',
        'GOODPROTS' : 'goodprots.enterprise',
        'BADURLS' : badurls,
        'BYPASS_ROBOTS' : 'bypass_robots.enterprise',
        'COOKIE_RULES' : 'cookierules.enterprise',
        'SSO_PATTERN_CONFIG' : 'sso_pattern_config.enterprise',
        'SSO_SERVING_CONFIG' : 'sso_serving_config.enterprise',
        'DEPTH0HOSTS' : 'depth0hosts.enterprise',
        'DATEPATTERNS' : 'datepatterns.enterprise',
        'URLS_REMOTE_FETCH_ONLY' : 'remote_fetches_only.enterprise',
        'URLS_LOCAL_FETCH_ONLY' : 'local_fetches_only.enterprise',
        # [Kerberos/IWA] - Admin UI config file for user+password+realm/domain+etc
        'CRAWL_KERBEROS_CONFIG'   : 'crawl_kerberos_up.enterprise',  # [Kerberos/IWA]
        'CRAWL_USERPASSWD_CONFIG' : 'crawl_userpasswds.enterprise',
        'STATUSFILE_CRAWL' : 'status_crawl.enterprise',
        'LDAP_CONFIG' : 'ldap_config',
        # [Kerberos/IWA] - UI scratchpad file for Kerberos config data (e.g., KDC)
        # [Kerberos/IWA] - UI scratchpad file for Kerberos imported keytab file
        'KERBEROS_CONFIG' : 'kerberos_config.enterprise',  # [Kerberos/IWA]
        'KERBEROS_KEYTAB' : 'kerberos_keytab.enterprise',  # [Kerberos/IWA]
        # [Kerberos/IWA] - Active/live/valid/etc krb5.conf file for Kerberos/IWA
        # [Kerberos/IWA] - Active/live/valid/etc krb5.keytab file for Kerberos/IWA
        'KERBEROS_KRB5_CONF' : 'kerberos_krb5.conf.enterprise',      # [Kerberos/IWA]
        'KERBEROS_KRB5_KEYTAB' : 'kerberos_krb5.keytab.enterprise',  # [Kerberos/IWA]
        # [Kerberos/IWA] - end.
        'ENTFRONT_KEY_STORE' : 'server.p12',
        # these are the same as some of the above
        'PAGERANKER_STARTURLS' : starturls,
        'BOT_TESTURLS' : starturls,
        'BADURLS_URLMANAGER' : badurls,
        'DUPHOSTS_MIRRORED' : 'duphosts_mirrored.enterprise',
        'DUPHOSTS_STAGING' : 'duphosts_staging.enterprise',
        'DATABASE_STYLESHEET_DIR' : 'database_stylesheets',
        'DATABASE_LOGS_DIR' : 'database_logs',
        'BOT_SSL_CERTIFICATE_DIR' : 'certs',
        'BOT_CA_CRL_DIR' : 'certs',
        'TRUSTED_CA_DIRNAME' : 'certs',
        'CRL_DIRNAME' : 'certs',
        'RECRAWL_URL_PATTERNS' : 'recrawl_url_patterns',
        'CRAWL_SCHEDULE' : 'batch_crawl_schedule',
        'CRAWL_SCHEDULE_BITMAP' : 'batch_crawl_schedule_bitmap',
        'ONEBOX_MODULES' : 'oneboxes.enterprise',
        'ONEBOX_LOGS_DIR' : 'onebox_logs',

        'ENT_STEMS_DE_SOURCE'  : 'google_stems_de.txt',
        'ENT_STEMS_EN_SOURCE'  : 'google_stems_en.txt',
        'ENT_STEMS_ES_SOURCE'  : 'google_stems_es.txt',
        'ENT_STEMS_FR_SOURCE'  : 'google_stems_fr.txt',
        'ENT_STEMS_IT_SOURCE'  : 'google_stems_it.txt',
        'ENT_STEMS_NL_SOURCE'  : 'google_stems_nl.txt',
        'ENT_STEMS_PT_SOURCE'  : 'google_stems_pt.txt',

        'ONEBOX_BACKEND_CONFIG' : 'oneboxes.enterprise.backendconfig',
        'ENT_SCORING_TEMPLATE' : 'scoring_template.enterprise',
        'ENT_SCORING_CONFIG' : 'scoring_policies.enterprise',

        # ACL policy checking config files
        'ACL_GROUPS_FILE' : 'acl_groups.enterprise',
        'ACL_URLS_FILE' : 'acl_urls.enterprise',
        'UAM_DIR' :  'personalization',
        }

      # Experimental (labs) features
      # As a convention, we prefix the names to make it clear they are for
      # labs features.
      if labs_params.has_key('PagerankInjection'):
        basic_config_files['LABS_PAGERANK_INJECTION'] = 'labs_prinjection.txt'
      if labs_params.has_key('UsageBoost'):
        basic_config_files['LABS_USAGEBOOST_DATA'] = 'labs_usageboost.data'
        
      for var_name, base_file in basic_config_files.items():
        file_name = "%s/%s" % (configdir, base_file)
        self.set_var(var_name, E.normpath(file_name))

      self.set_var('MUSTCRAWLURLS', {
        'filename' : "%s/%s" % (configdir, starturls),
        'sharded'  : 0 }
                   )
      self.set_var('ENTERPRISE_COLLECTIONS_DIR',
                   "%s/collections" % configdir)

      frontends_dir = E.joinpaths([configdir, 'frontends'])
      self.set_var('ENTFRONT_FRONTENDS_DIR', frontends_dir)

    self.set_var('RTINDEXER_USE_ANCHOR_PROCESSOR', 0)
    self.set_var('RTINDEXER_AS_ANCHOR_PROCESSOR', 1)
    self.set_var('NEED_GLOBAL_LINK', 0)
    self.set_var('RTINDEXER_FOR_SERVING', 0)

    ##

    if rt_ram_dir:
      self.set_var('RTSLAVE_RAM_DIR_FOR_INDEX_CACHING', rt_ram_dir)
    ##

    # Number of urltracker_server clones
    if machines and len(machines) > 1:
      max_urltracker_server_per_node = 2
      num_urltracker_server_clones   = 2
    else:
      max_urltracker_server_per_node = 1
      num_urltracker_server_clones   = 1

    if gfs_cell:
      self.set_var('URLTRACKER_DIRECTORY', namespace_prefix)
    else:
      self.set_var('URLTRACKER_DIRECTORY',
                   ("%s/data/enterprise-data/urltracker/" % enterprise_home));

    # Figure out how many rtslaves we need to run per node.
    if machines and ent_num_shards:
      num_machines = len(machines)
      tot_slaves = ent_num_shards * self.GetNumRTSlaveClones(num_machines)
      max_rtslaves_per_node = (tot_slaves + num_machines - 1) / num_machines
    else:
      max_rtslaves_per_node = 1

    if rt_ram_dir:
      # We 'allocate' a fixed size of memory for index serving.  We give some
      # of it directly to each rtslave and give the rest to all instances on
      # node as ram-based filesystem.  Don't give too much to it directly to
      # avoid fragmentation of this budget.
      rtslave_mmap_memory = 1024L << 20
      tot_mem = self.var('ENT_MEMORY_FOR_INDEX_SERVING')
      ramfs_usage = tot_mem - (rtslave_mmap_memory * max_rtslaves_per_node)
      if ramfs_usage <= 0: ramfs_usage = 1  #0 means use all of it
      self.set_var('RTSLAVE_RAMFS_MAX_USAGE', ramfs_usage)
    else:
      rtslave_mmap_memory = self.get_max_mmap_memory()
      # Virtual GSA limit the rtserver memory usage to 25% of whole memory
      if ent_config_type == 'FULL':
        meminfo_content = open('/proc/meminfo').read()
        pattern = re.compile(r'MemTotal:\s*(\d+) kB')
        match = pattern.search(meminfo_content)
        if match:
           whole_memory_size = long(match.group(1)) << 10
           vgsa_mem_limit = long(whole_memory_size / 4L)
           if rtslave_mmap_memory > vgsa_mem_limit:
             rtslave_mmap_memory = vgsa_mem_limit

    if ent_config_type in ('LITE', 'FULL'):
      # ~150K per shard for virtual platforms
      self.set_var('TOTAL_URLS_EXPECTED', (150 << 10) * ent_num_shards)
    elif ent_config_type == 'MINI':
      # ~3M per shard for mini platforms
      self.set_var('TOTAL_URLS_EXPECTED', (3 << 20) * ent_num_shards)
    elif ent_config_type in ('ONEBOX', 'ONEWAY'):
      # ~4M per shard for oneway platforms
      self.set_var('TOTAL_URLS_EXPECTED', (4 << 20) * ent_num_shards)
    elif ent_config_type == 'SUPER':
      # ~11M per shard for super.
      self.set_var('TOTAL_URLS_EXPECTED', (11 << 20) * ent_num_shards)
    else:
      # ~32M per shard for uber and others.
      self.set_var('TOTAL_URLS_EXPECTED', (32 << 20) * ent_num_shards)

    if gfs_cell:
      self.set_var('RTSERVER_MMAP_BUDGET', '200MB') #cluster gets bigger budget
      self.set_var('RTSLAVE_MAX_MMAP_MEMORY', rtslave_mmap_memory)
      # Since rtslaves refresh their checkpoint every 15 minutes, we
      # should not create checkpoints too often otherwise we run into
      # cases where rtslaves try to open an already deleted file.
      self.set_var('RTSERVER_FLUSH_TIME_INTERVAL', {
        'base_indexer'         :  900, # 15 min
        'daily_indexer'        :  900,
        'rt_indexer'           :  900,
        'urlhistory_processor' :  900,
        'global_link'          :  300, # 5 min
        'global_anchor'        :  300,
        })
      # we want to recrawl everything in one month
      self.set_var('URLSCHEDULER_MUST_RECRAWL_AGE', 2592000)
    else:
      self.set_var('RTSERVER_MMAP_BUDGET', '200MB')
      self.set_var('RTSLAVE_MAX_MMAP_MEMORY', rtslave_mmap_memory)
      self.set_var('RTSERVER_FLUSH_TIME_INTERVAL', {
        'base_indexer'         :  300, # 5 min
        'daily_indexer'        :  300,
        'rt_indexer'           :  300,
        'urlhistory_processor' :  300,
        'global_link'          :  300,
        'global_anchor'        :  300,
        })
      # for one-ways we want about 50% of urls that can in refresh urls
      self.set_var('URLSCHEDULER_REFRESH_FRACTION', 2)
      urlscheduler_refresh_fraction = 2
      # we want to recrawl everything in two week
      self.set_var('URLSCHEDULER_MUST_RECRAWL_AGE', 1209600)

    # Index cache size can't be less than max_mmap_memory
    # Otherwise it ends up trying to load huge index files when it
    # gets queries and gets killed by babysitter while doing so.
    # Give it a little extra because we always mmap lexicon (ignoring the
    # mmap budget), so we could go over.
    #index_bytes = rtslave_mmap_memory + (300L << 20)
    #self.set_var('RTSLAVE_MAX_INDEX_BYTES', index_bytes)
    # NOTE: Commented because the default value has been increased

    if user_agent_to_send:
      self.set_var('USER_AGENTS_TO_OBEY_IN_ROBOTS',
                   user_agent_to_send)
    ##

    if problem_email != None:
      self.set_var('USER_AGENT_EMAIL',
                   problem_email)
    ##

    if ent_config_name and problem_email != None:
      self.set_var('USER_AGENT_COMMENT',
                   'Enterprise; %s; %s' % (ent_config_name, problem_email))
    ##

    if ent_num_shards:
      self.set_var('WORKSCHEDULER_NUM_DOC_SHARDS', ent_num_shards)

    # for now we run an rfserver on every pr_main machine, it would have been
    # better to do so only for clusters, but the pr_main code currently expects
    # to access files through an rfserver.
    self.set_var('AUTO_ASSIGN_SETS', {'pr_main' : ['rfserver']})

    if urlserver_default_hostload != None:
      self.set_var('URLSERVER_MAX_HOSTLOAD', urlserver_default_hostload)
    ##

    if servers:
      # The goal is to issue one request to urlserver every 10 ms
      bots = servers.get(servertype.GetPortBase('bot'))
      if bots:
        self.set_var('BOT_URLSERVER_REQUEST_INTERVAL',
                     10 * len(bots))
    ##

    if xslt_stylesheets_dir:
      self.set_var('ENTFRONT_STYLESHEETS_DIR', xslt_stylesheets_dir)
      self.set_var('CUSTOMER_ONEBOX', '%s/customer-onebox.xsl' % xslt_stylesheets_dir)
      self.set_var('ONEBOX_DEFAULT', '%s/onebox-default.xsl' % xslt_stylesheets_dir)

    self.set_var('ENTERPRISE_ONEBOX_LOG', 'enterprise_onebox_log');

    if xslt_test_stylesheets_dir:
      self.set_var('ENTFRONT_TEST_STYLESHEETS_DIR' , xslt_test_stylesheets_dir)
    ##

    if gfs_cell:
      self.set_var('GFS_CELL', core_utils.GFS_CELL)
    ##

    if namespace_prefix:
      self.set_var('GLOBAL_NAMESPACE_PREFIX', namespace_prefix)
      self.set_var('NAMESPACE_PREFIX', namespace_prefix)
      self.set_var('RTSERVER_LOGS', {
        'base_indexer'         : '%senterprise_base_document_log' % namespace_prefix,
        'global_link'          : '%senterprise_global_link_log' % namespace_prefix,
        'global_anchor'        : '%senterprise_global_anchor_log' % namespace_prefix,
        'urlmanager'           : '%senterprise_urlmanager_log' % namespace_prefix,
        'urlhistory_processor' : '%senterprise_urlhistory_log' % namespace_prefix,
        'feeder'               : '%senterprise_feederack_log' % namespace_prefix,
        'tracker_gatherer'     : '%senterprise_tracker_log' % namespace_prefix,
        })
      # Feed names - use gfs when available
      ## set dirs for feeds and feed status.
      if gfs_cell:
        self.set_var('FEEDS_DIR', '%sfeeds' % namespace_prefix)
        self.set_var('FEED_STATUS_DIR', '%sfeedstatus' % namespace_prefix)
      else:
        self.set_var('FEEDS_DIR', E.normpath('%s/local/conf/feeds' %
                                                             enterprise_home))
        self.set_var('FEED_STATUS_DIR', E.normpath('%s/local/conf/feedstatus' %
                                                             enterprise_home))
      self.set_var('FEED_CONTENTFEEDS_LOG_INFO_PREFIXES',
                   {1: '%snormal_feeds' % namespace_prefix,
                    2: '%sarchive_feeds' % namespace_prefix})

      # determine the directory for
      #  crawlqueue, syslog checkpoints, and log report
      if gfs_cell:
        self.set_var('LOG_REPORT_DIR', '/gfs/ent/log_report')
        self.set_var('CRAWLQUEUE_DIR', '/gfs/ent/crawlqueue')
        self.set_var('SYSLOG_CHECKPOINTS_DIR', '/gfs/ent/syslog_checkpoints')
      else:
        self.set_var('LOG_REPORT_DIR', '%s/log_report' % self.var('LOGDIR'))
        self.set_var('CRAWLQUEUE_DIR', '%s/crawlqueue' % self.var('LOGDIR'))
        self.set_var('SYSLOG_CHECKPOINTS_DIR',
                     '%s/syslog_checkpoints' % self.var('LOGDIR'))

      if gfs_cell:
        self.set_var('FEED_URLFEEDS_LOG_PREFIX',
                     '%s/bare_urlfeeds' % namespace_prefix)
        self.set_var('FEED_URLFEEDS_LOG_COLLECT', 1)
        self.set_var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX',
                     self.var('RTSERVER_LOGS')['urlmanager'])
        self.set_var('WORKSCHEDULER_REMOVEDOC_TRACKER_LOG_PREFIX',
                     self.var('RTSERVER_LOGS')['tracker_gatherer'])
      else:
        self.set_var('WORKSCHEDULER_REMOVEDOC_UM_LOG_PREFIX',
                     '%s/umremovedoc' % namespace_prefix)
        self.set_var('WORKSCHEDULER_REMOVEDOC_TRACKER_LOG_PREFIX',
                     '%s/trackerremovedoc' % namespace_prefix)

      # SSO Logging files, use GFS when available
      if gfs_cell:
        self.set_var('SSO_LOG_DIR', '%slogs' % namespace_prefix)
        self.set_var('SSO_RULES_LOG_FILE',
                     '%s/Sso_Rules_Setup' % self.var('SSO_LOG_DIR'))
        self.set_var('SSO_LOG_FILE',
                     '%s/Sso_Crawling' % self.var('SSO_LOG_DIR'))
        self.set_var('SSO_SERVING_EFE_LOG_FILE',
                     '%s/Sso_Serving_EFE' % self.var('SSO_LOG_DIR'))
        self.set_var('SSO_SERVING_HEADREQUESTOR_LOG_FILE',
                     '%s/Sso_Serving_Headrequestor' % self.var('SSO_LOG_DIR'))

      else:
        self.set_var('SSO_RULES_LOG_FILE', '%s/Sso_Rules_Setup' %
                     self.var('CRAWL_LOGDIR'))
        self.set_var('SSO_LOG_FILE', '%s/Sso_Crawling' %
                     self.var('CRAWL_LOGDIR'))
        self.set_var('SSO_SERVING_EFE_LOG_FILE', '%s/Sso_Serving_EFE' %
                     self.var('CRAWL_LOGDIR'))
        self.set_var('SSO_SERVING_HEADREQUESTOR_LOG_FILE',
                     '%s/Sso_Serving_Headrequestor' %
                     self.var('CRAWL_LOGDIR'))

    # License Notices file path
    self.set_var('LICENSE_NOTICES',
                 '%s/local/google3/enterprise/notices.txt' %
                 enterprise_home)

    ##

    if output_namespace_prefix:
      self.set_var('OUTPUT_NAMESPACE_PREFIX', output_namespace_prefix)

    ##
    if gfs_root_dir:
      self.set_var('GFS_ROOT_DIR', gfs_root_dir)
    ##

    if gfs_cell:
      data_dirs['sremote_server'] = '/dev/null'
      self.set_var('RTSLAVE_GFS_CELL_ARGS',
                   '%s=may_use_shadow_to_read:true' % gfs_cell)
      self.set_var('URLTRACKER_GFS_CELL_ARGS',
                   '%s=may_use_shadow_to_read:true' % gfs_cell)
      self.set_var('BOT_GFS_CELL_ARGS',
                   '%s=security_level:none' % gfs_cell)
    ##

    if gfs_cell and namespace_prefix:
      self.set_var('WORKQUEUE_MASTER_CHECKPOINT',
                   '%s/workqueue-master-checkpoint' % namespace_prefix)
    elif datadisk:
      self.set_var('WORKQUEUE_MASTER_CHECKPOINT',
                   '%s/workqueue/workqueue-master-checkpoint' % datadisk)
    ##

    if gfs_cell:
      self.set_var('WORKQUEUE_SLAVE_DATADISKS', hda3_only_disks)
      self.set_var('ENT_BIGFILE_DATADISKS', hda3_only_disks)
    else:
      self.set_var('WORKQUEUE_SLAVE_DATADISKS', datachunkdisks)
      self.set_var('ENT_BIGFILE_DATADISKS', datachunkdisks)
    ##

    if state in ["INSTALL", "TEST"]:
      self.set_var('ENTFRONT_EXTERNAL_PORT', 7801)
      self.set_var('ENTFRONT_SSL_PORT', 4431)
      self.set_var('ENTFRONT_EXTERNAL_SSL_PORT', 4431)
    else:
      self.set_var('ENTFRONT_EXTERNAL_PORT', 80)
      self.set_var('ENTFRONT_SSL_PORT', 4430)
      self.set_var('ENTFRONT_EXTERNAL_SSL_PORT', 443)

    ##

    self.set_var('NUM_DOCID_LEVELS', rtserver_docid_levels)

    ##
    # urlmanager_urlscheduler_log prefix
    if gfs_cell:
      self.set_var('URLMANAGER_URLSCHEDULER_LOG_PREFIX',
                   'enterprise_urlmanager_log')
    else:
      self.set_var('URLMANAGER_URLSCHEDULER_LOG_PREFIX',
                   'urlmanager_urlscheduler')

    # chubby cell and port determination
    if gfs_cell:
      if state in ["INSTALL", "TEST"]:
        self.set_var('ENT_CHUBBY_PORT', core_utils.LS_TEST_PORT)
        gfs_aliases = core_utils.GetGFSAliases(self.var('VERSION'), 1)
      else:
        self.set_var('ENT_CHUBBY_PORT', core_utils.LS_BASE_PORT)
        gfs_aliases = core_utils.GetGFSAliases(self.var('VERSION'), 0)
      self.set_var('GFS_ALIASES', gfs_aliases)
      self.set_var('GFS_CHUBBY_CELL',
                   core_utils.GetGFSChubbyCellName(self.var('VERSION')))

    ################
    ## collections
    if ent_collections and configdir:
      for key, collection in ent_collections.items():
        name = collection.get('COLLECTION_NAME', None)

        if name:
          collection_configdir = E.joinpaths([configdir, 'collections', name])

          collection['CONFIGDIR'] = collection_configdir
          collection['GOODURLS'] = E.joinpaths(
            [collection_configdir, 'restrict-collection_%s.pat' % name])
          collection['BADURLS'] = E.joinpaths(
            [collection_configdir, 'restrict-collection_%s.pat.bad' % name])
          collection['TESTWORDS'] = E.joinpaths(
            [collection_configdir, 'testwords'])
          collection['EPOCHS_SERVING'] = E.joinpaths(
            [collection_configdir, 'epochs_serving'])

      self.set_var('ENT_COLLECTIONS', ent_collections)

    ################
    ## frontends
    if ent_frontends and googledata and xslt_stylesheets_dir and frontends_dir:
      for key, frontend in ent_frontends.items():
        name = frontend.get('FRONTEND_NAME', None)

        if name:
          gwsclient_configdir = E.joinpaths([googledata, 'gws/clients', name])

          frontend['GWSCLIENT_CONFIGDIR'] = gwsclient_configdir
          frontend['GOOGLEMATCH'] = E.joinpaths([gwsclient_configdir,
                                                 'googlematch'])
          frontend['SYNONYMS']    = E.joinpaths([gwsclient_configdir,
                                                 'synonym'])
          frontend['GOOD_IPS']    = E.joinpaths([gwsclient_configdir,
                                                 'goodips'])
          frontend['GWS_CAPABILITIES'] = E.joinpaths(
            [googledata, 'gws', 'p4clientinfo', name, 'capabilities'])
          frontend['BADURLS_NORETURN'] = E.joinpaths(
            [googledata, 'gws', 'badurls_client-%s' % name])
          frontend['STYLESHEET']       = E.joinpaths([xslt_stylesheets_dir,
                                                      name])
          frontend['STYLESHEET_TEST']  = E.joinpaths([xslt_stylesheets_dir,
                                                      '%s.test' % name])
          frontend['DOMAIN_FILTER']    = E.joinpaths(
            [frontends_dir, name, 'domain_filter'])
          frontend['FILETYPE_FILTER']  = E.joinpaths(
            [frontends_dir, name, 'filetype_filter'])
          frontend['QUERY_EXPANSION_FILTER']  = E.joinpaths(
            [frontends_dir, name, 'query_expansion_filter'])
          frontend['SCORING_POLICY_FILTER']  = E.joinpaths(
            [frontends_dir, name, 'scoring_policy_filter'])
          frontend['LANGUAGE_FILTER']  = E.joinpaths(
            [frontends_dir, name, 'language_filter'])
          frontend['METATAG_FILTER']   = E.joinpaths(
            [frontends_dir, name, 'metatag_filter'])
      self.set_var('ENT_FRONTENDS', ent_frontends)

    ################
    ## query expansion
    if ent_query_exp and configdir:
      for key, queryexp in ent_query_exp.items():
        name = queryexp.get('ENTRY_NAME', None)

        if name:
          queryexp_configdir = E.joinpaths([configdir, 'queryexpansion', name])

          queryexp['CONTENT'] = \
                               E.joinpaths([queryexp_configdir, 'content'])

      self.set_var('ENT_QUERY_EXP', ent_query_exp)

    ################
    ## machine allocation constraints

    if machines and ent_num_shards:
      num_all = len(machines)
      num_per_shard = num_all / ent_num_shards

      quarter = ((num_all + 3) / 4)
      one_third = ((num_all + 2) / 3)
      # compute per shard fractions
      quarter_per_shard       = ((num_per_shard + 3) / 4)
      threequarters_per_shard = ((3 * num_per_shard + 3) / 4)
      half_per_shard          = ((num_per_shard + 1) / 2)
      third_per_shard         = ((num_per_shard + 2) / 3)
      twothirds_per_shard     = ((2 * num_per_shard + 2) / 3)

      # quarter       = math.ceil(float(num + 3) / 4)
      # half          = math.ceil(float(num + 1) / 2)
      # third         = math.ceil(float(num + 2) / 3)
      # Will be used later :
      # threequarters = math.floor(float(3 * num + 3) / 4)
      # twothirds     = math.floor(float(2 * num + 2) / 3)

      # constriant format is as follows:
      # 'servertype': {
      #   'resource': ['cpumhz:100,hdutil:1.5,ram:200,hdsize:0.02']
      #                        MHz, Num disks,    MB,        GB
      #               The order doesn't matter anywhere
      #   'shardlen': [min, desired]
      # }
      # For more information look at:
      # google3/enterprise/legacy/production/assinger/constraintlib.py and
      # google3/enterprise/legacy/production/machinedb/machinelib.py

      # divide all available cluster machines into 3 buckets.
      # bucket 3 and 4 are the same, bucket4 = bucket3.reverse().
      # high CPU usage GSA services are balanced across buckets.
      #
      # bucket1 = first ent_num_shards machines.
      # bucket2 = last ent_num_shards machines.
      # bucket3 = all machines except the intersection of bucket1 and 2.
      machine_bucket1 = machines[0:ent_num_shards]
      machine_bucket2 = machines[-ent_num_shards:]
      machine_bucket2.reverse()
      machine_bucket3 = (machines[0:len(machines)-ent_num_shards] +
                         machines[ent_num_shards:])
      machine_bucket4 = machine_bucket3
      machine_bucket4.reverse()

      # add all remaining machines to the end of the bucket list.
      # these additional machines, at the end of the bucket will
      # not be used in normal cases.  they are only used during
      # machine failure cases.
      for machine in machines:
        if machine not in machine_bucket1:
          machine_bucket1.append(machine)
        if machine not in machine_bucket2:
          machine_bucket2.append(machine)
        if machine not in machine_bucket3:
          machine_bucket3.append(machine)
        if machine not in machine_bucket4:
          machine_bucket4.append(machine)

      constraint_general = {
        'default': {
        'shardlen': [1, 1],           # by default have atleast one
        'host': ['.+'],             # by default any machine would do
        },

        # Serving (all of them are unsharded)
        'web': {
          'resource': ['cpumhz:100,ram:20'],
          'shardlen': [one_third, one_third],
        },
        'cache': {
          'resource': ['cpumhz:100, ram:100'],
        },
        'onebox': {
          'resource': ['ram:10'],
        },
        'oneboxenterprise': {
          'resource': ['ram:50'],
        },
        'headrequestor': {
        'resource': ['cpumhz:100, ram:10'],
        },
        'entfrontend': {
          'resource': ['cpumhz:100,ram:10'],
          'shardlen': [one_third, one_third],
        },
        'authzchecker': {
          'resource': ['cpumhz:100,ram:10'],
        },
        'registryserver': {
          'resource': ['cpumhz:100,ram:10'],
          'shardlen': [one_third, one_third],
          'host'    : machine_bucket3,
        },
        'mixer': {
          'resource': ['cpumhz:100,ram:10'],
          'shardlen': [one_third, one_third],
        },
        'spellmixer': {
          'resource': ['ram:350'],
        },
        # Some crawling related servers (rest are below).
        'fsgw': {
          'resource': ['cpumhz:100,ram:100'],
          'shardlen': [one_third, one_third],
        },
        'config_manager': {
          'resource': ['cpumhz:100'],
        },
        'feedergate': {
          'resource': ['cpumhz:100,ram:10'],
          'shardlen': [one_third, one_third],
        },
      }

      # Run supergsa_main (crawl+index binary) only on SuperGSA.
      constraint_general['supergsa_main'] =  {
          'resource': ['cpumhz:100,ram:10'],
          }

      # Add query rewrite only if license allows it.
      # Without this, query rewrite will not be started.
      qe_local, qe_contextual, qe_langs = self.GetQueryExpansionCapabilities()
      if license_info.get(license_api.S.ENT_LICENSE_QUERY_EXPANSION):
        if qe_contextual:
          constraint_general['qrewrite'] = {
            # Estimate based on the compressed data files.
            # It may be possible to squeeze this down further.
            'resource': ['ram:330'],
          }
        elif qe_local:
          constraint_general['qrewrite'] = {
            'resource': ['ram:128'],
          }

      # Add database table server only if license allows it
      if license_info.get(license_api.S.ENT_LICENSE_DATABASES):
        constraint_general['enttableserver'] = {
          'resource': ['cpumhz:100,ram:10'],
        }

      # Add connector manager only if license allows it
      if license_info.get(license_api.S.ENT_LICENSE_CONNECTOR_FRAMEWORK):
        constraint_general['connectormgr'] = {
          'resource': ['cpumhz:100,ram:10'],
        }

      # Add federation only if license allows it
      if license_info.get(license_api.S.ENT_LICENSE_FEDERATION):
        self.set_var('GWS_USE_SUPERROOT', 1)
        constraint_general['ent_fedroot'] = {
          'resource': ['cpumhz:100,ram:100'],
        }
      else:
        self.set_var('GWS_USE_SUPERROOT', 0)


      # If you have any parameters for Enterprise labs experiments,
      # process them here.
      # labs_settings is a space-separated list of name=value pairs.
      labs_settings = license_info.get(license_api.S.ENT_LICENSE_LABS_SETTINGS)

      ## Add clustering only if license allows it.
      # Without this, the clustering server will not be started.
      if license_info.get(license_api.S.ENT_LICENSE_CLUSTERING):
        constraint_general['clustering_server'] = {
          ## TODO(mgp) Determine real memory requirements.
          'resource': ['ram:256'],
        }

      #machines[servertype.GetPortBase('filesyncmaster') + i] = builders
      #machines[servertype.GetPortBase('filesyncer') + i] = \
      #                                              builders + backends

      if self.var('RTINDEXER_USE_ANCHOR_PROCESSOR'):
        constraint_general['global_anchor'] = {
          'resource': ['cpumhz:100,ram:700'],
        }
      ##

      if self.var("NEED_GLOBAL_LINK"):
        constraint_general['global_link'] = {
          'resource': ['cpumhz:100,ram:700'],
        }
      ##

      rtslave_shardlen = self.GetNumRTSlaveClones(num_machines)
      constraint_general['rtslave'] = {
        'resource': ['cpumhz:200,ram:3000'],
        'shardlen': [rtslave_shardlen, rtslave_shardlen],
      }

      ##

      # HACK: For uni-processor kernel reduce the cpumhz.  Otherwise,
      # assigner wouldn't assign more than one rtslave clone and serving
      # could break as soon as a node goes down.
      self.AdjustProcUsageIfUniprocessorKernel(constraint_general)

      # Allow all servers to be sharable at all machines
      shareable_set = constraint_general.keys()
      shareable_set.remove('default')
      # allow two contentfilters (of different shards) on the same machine
      shareable_set.append('contentfilter')
      # allow multiple rtslaves of different shard on the same machine
      shareable_set.extend(['rtslave']*(max_rtslaves_per_node-1))
      # allow multiple urltracker_server of different shard on the same machine
      shareable_set.extend(['urltracker_server']*(max_urltracker_server_per_node-1))

      # Set the sharing constraint. shareable_set contains a group of servers
      # that can be shared on single machine.
      constraint_sharing = {
        string.join(shareable_set, ',') : [],
      }

      self.set_var('CONSTRAINT_GENERAL', constraint_general)
      self.set_var('CONSTRAINT_SHARING', constraint_sharing)
    ##

    # set these last
    # urlscheduler keep/crawl/refresh values
    # urls that need to be kept in the repository = license limit
    # thus we set URLSCHEDULER_URL_LIMIT = license limit
    # we are allowed to put some percent of urls as refresh urls which is
    # urlscheduler_refresh_fraction. Thus refresh urls will be set to
    # license/urlscheduler_daily_fraction
    # The number of urls to be crawled every segment is
    # license/nsegments
    # Note:- Daily is zero in enterprise
    if namespace_prefix:
      self.set_var('URLSCHEDULER_NAMESPACE_PREFIX', namespace_prefix)

    if ( license_info or user_defined_limit ) \
       and urlscheduler_min_samples and urlscheduler_refresh_fraction:
      total_crawl = int(min([0x7FFFFFFFL,
                             self.getMaxCrawledPagesOverall()]))
      refresh_crawl = \
            int(math.ceil(float(total_crawl)/urlscheduler_refresh_fraction))
      max_samples = max(urlscheduler_min_samples, int(float(total_crawl)/10))
      self.set_var('URLSCHEDULER_URL_LIMIT', total_crawl)
      self.set_var('URLMANAGER_REFRESHURL_LIMIT', refresh_crawl)
      self.set_var('URLSCHEDULER_NUM_SAMPLES', max_samples)

    if license_info:
      # update the validator of USER_MAX_CRAWLED_URLS to be less than
      # maximum license limit if it is greater than 1
      license_limit = int(self.getLicenseMaxPagesOverall())
      if license_limit > 1:
        self.params_.UpdateType('USER_MAX_CRAWLED_URLS',
                                validatorlib.Int(nullOK=1,
                                                 GTE=1, LTE=license_limit))
      # for seku-lite
      self.set_var('USE_HEADREQUESTOR',
                   int(license_info.get(
                       license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE, 0)))

      # for Single Sign-On
      if license_info.get(license_api.S.ENT_LICENSE_ENABLE_SSO):
        self.set_var('ENABLE_SINGLE_SIGN_ON', 1)
      else:
        self.set_var('ENABLE_SINGLE_SIGN_ON', 0)

    if license_info or user_defined_limit:
      max_pages = self.getMaxCrawledPagesOverall()
      adjusted_max_pages = int(max_pages)
      self.set_var('MAX_CRAWLED_URLS', adjusted_max_pages)
      removedoc_max_keep_docs = int(max_pages / self.GetEntNumShards()) + 1
      self.set_var('WORKSCHEDULER_REMOVEDOC_MAX_KEEP_DOCS',
                   removedoc_max_keep_docs)

    # set this last
    self.set_var('DATA_DIRS', data_dirs)

    ####

    mixer_set = self.GetServerManager().Set('mixer')
    if mixer_set != None:
      mixer_set.set_property('backend_port_base', mixer_set.PortBase())

    onebox_set = self.GetServerManager().Set('onebox')
    # enterprise only did onebox spell 4.4 or before, now also does
    # onebox enterprise if USE_ENTERPRISE_ONEBOX = 1 since 4.6.
    if onebox_set != None:
      # TODO (graceh): Need to remove oneboxenterprise from the constraints map
      # if the onebox enterprise may be disabled.
      if self.var('USE_ENTERPRISE_ONEBOX'):
        onebox_set.set_property('backends',
          [ { 'set' : 'oneboxenterprise' }, ])
      else:
        onebox_set.set_property('backends', [])

    # checks if the ports are shifted and change things accordingly
    if self.is_shifted_server_map(servers):
      if onebox_set != None:
        onebox_set.set_property('statusz_port', 9319)
      self.set_var('BASE_INDEXERS_ON_LEVEL1', 1)
      self.set_var('BABYSITTER_MONITOR_PORT_INCREMENT', 1)
    else:
      self.set_var('BASE_INDEXERS_ON_LEVEL1', 0)
      self.set_var('BABYSITTER_MONITOR_PORT_INCREMENT', 0)

    clustering_server_set = self.GetServerManager().Set('clustering_server')
    if clustering_server_set != None:
      clustering_server_set.set_property('backend_port_base',
          clustering_server_set.PortBase())

    qrewrite_set = self.GetServerManager().Set('qrewrite')
    if qrewrite_set != None:
      qrewrite_set.set_property('backend_port_base', qrewrite_set.PortBase())

    # system parameters we monitor and display to customer
    # in system status page
    ent_platform = GetPlatform()
    self.set_var('ENT_SYSTEM_STATUS_PARAMS',
                 self.GetEntSystemStatusParams(ent_config_type, ent_platform))


  def getMaxPagesHardLimit(self):
    """This function returns at most how many pages the system can crawl and
    serve, based on the hardware resource limit"""
    # TODO: give a more accurate estimation based on # of machines available
    ent_config_type = self.var('ENT_CONFIG_TYPE')
    if ent_config_type == 'CLUSTER':
      return ent_license.kClusterMaxPagesHardLimit
    elif ent_config_type == 'SUPER':
      return ent_license.kSuperMaxPagesHardLimit
    elif ent_config_type == 'MINI':
      return ent_license.kMiniMaxPagesHardLimit
    elif ent_config_type == 'LITE':
      return ent_license.kLiteMaxPagesHardLimit
    elif ent_config_type == 'FULL':
      return ent_license.kFullMaxPagesHardLimit
    else:
      return ent_license.kOneBoxMaxPagesHardLimit

  def getLicenseMaxPagesOverall(self):
    """Get the value from license, also consider about the hardlimit"""
    max_pages = ent_license.EnterpriseLicense(
      self.var('ENT_LICENSE_INFORMATION')).getMaxPagesOverall()
    hard_limit = self.getMaxPagesHardLimit()
    if max_pages == ent_license.kUnlimitedMaxPagesOverall or \
       max_pages > hard_limit:
      max_pages = hard_limit
    return max_pages

  def getMaxCrawledPagesOverall(self):
    """
    Get the max crawled page, min value of license limit and MAX_CRAWLED_URL
    """
    max_pages = self.getLicenseMaxPagesOverall()
    user_defined_limit = self.var('USER_MAX_CRAWLED_URLS')
    if user_defined_limit and max_pages > user_defined_limit:
      max_pages = long(user_defined_limit)
    return max_pages

  def GetQueryExpansionLanguages(self):
    """
    Returns a comma-separated list of language codes for query expansion.
    """
    langs = self.var('QUERY_EXP_LANGS')
    if langs:
      return langs
    else:
      # Safe default in case the config variable is missing
      return "all"

  def GetQueryExpansionCapabilities(self):
    """
    Returns the capabilities available with the current query expansion
    settings. This function is intended to remove some details about platform
    and licensing from servertype_prod.
    The return value is a tuple consisting of the following:
    - 1. True if local query expansion is available, otherwise False.
    - 2. True if contextual query expansion is available, otherwise False.
    - 3. the list of languages for local query expansion.
    In future version, this list may be extended with more capabilities.
    """
    # TODO(dahe): when we move to a numeric license, get rid of dependence
    # on ENT_CONFIG_TYPE. Langs for MINI will also change.
    license_info = self.var('ENT_LICENSE_INFORMATION')
    if license_info.get(license_api.S.ENT_LICENSE_QUERY_EXPANSION):
      if self.var('ENT_CONFIG_TYPE') == 'MINI':
        return (True, False, "all")
      else:
        return (True, True, self.GetQueryExpansionLanguages())
    else:
      return (False, False, None)

  def GetNumRTSlaveClones(self, num_machines):
    """
    Get the number of rtslave clones depending on number of live machines.
    """
    if num_machines < 4:
      return 1
    elif num_machines < 11:
      return 2
    else:
      return 3

  def GetEntSystemStatusParams(self, ent_config_type, ent_platform):
    """Get list of system parameters of which we need to check health.

    Args:
      ent_config_type: the GSA product ('MINI', 'ONEWAY' etc)
      ent_platform: the platform on which the product is running ('vmw' etc)

    Returns:
      List of strings (e.g. ['Machines', 'Disks', 'Temperatures'])
    """
    if ent_platform == 'vmw':
      return ['Disks']
    if ent_config_type == 'MINI':
      return ['Machines', 'Disks', 'Temperatures']
    else:
      return ['Machines', 'Disks', 'Temperatures', 'Raid',]

###############################################################################

def MigrateGoodURLs(old_pattern):
  """Add new DB pattern into the goodurls if the old DB pattern exists.
  """
  old_db_follow_pattern = re.compile(r'^http://\d+.\d+.\d+.\d+/db(/|$).*',
                                     re.MULTILINE)
  new_db_follow_pattern = re.compile(r'^\^googledb://', re.MULTILINE)
  # migrate old follow pattern for db if necessary
  if (old_db_follow_pattern.search(old_pattern) and
      not new_db_follow_pattern.search(old_pattern)):
    # append new follow pattern for db
    return "%s\n# new database pattern\n^googledb://\n" % old_pattern
  else:
    return old_pattern

def MigrateDatabaseConfig(old_db_config, new_version = ''):
  """Modify database config to use new JDBC driver if old driver config exists.
  """
  db_config = old_db_config;
  db_config = re.sub(
    'driverClass="com\.microsoft\.jdbc\.sqlserver\.SQLServerDriver"',
    'driverClass="com.microsoft.sqlserver.jdbc.SQLServerDriver"',
    db_config)
  db_config = re.sub(
    'jdbcUrl="jdbc:microsoft:sqlserver://',
    'jdbcUrl="jdbc:sqlserver://',
    db_config)
  # Find and replace old version string with new version string, if supplied.
  if new_version != '':
    db_config = re.sub('/export/hda3/[^/]+/',
                       '/export/hda3/%s/' % new_version, db_config)
  return db_config

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Ben Polk
#
# configmgr_request.py - Create a config manager request file.
#
# This module contains the code to create the configmgr request objects.
#
# The current implementation uses one file per request. The files are written
# to a directory that the configmgr watches.  When new files show up in this
# directory configmgr grabs them and tries to take the action they specify.
# The filenames are not used by the configmgr, so any name that isn't already
# in use is ok.
#
# The request type supported are:
#
# ReplaceMachine - replace a single machine
# ReplaceSet - Swap a new set of servers live in place of an existing set
#
# See examples of the use of each type below.
#

import time
import string
import os

from google3.enterprise.legacy.production.configmgr import autorunner

# 'REQUEST_HANDLER' for all config manager types:
CONFIG_MGR = 'CONFIG_MGR'

# Config manager transaction types:
PUSH_FILE_TO_GFS = 'PUSH_FILE_TO_GFS'
UPDATE_CONFIG_FILE = 'UPDATE_CONFIG_FILE'
REPLACE_CONFIG_FILE = 'REPLACE_CONFIG_FILE'
REPLACE_MACHINE = 'REPLACE_MACHINE'
REPLACE_SET = 'REPLACE_SET'
MULTI_REQUEST_CREATOR = 'MULTI_REQUEST_CREATOR'
SETUP_BINARIES_ON_MACHINE = 'SETUP_BINARIES_ON_MACHINE'
SETUP_KERNEL_ON_MACHINE = 'SETUP_KERNEL_ON_MACHINE'
SETUP_SERVERS_ON_MACHINE = 'SETUP_SERVERS_ON_MACHINE'
SETUP_COMMON_ON_MACHINE = 'SETUP_COMMON_ON_MACHINE'

# Keys used by ReplaceMachine
PORT = 'PORT'
REMOVE_MACHINE = 'REMOVE_MACHINE'
ADD_MACHINE = 'ADD_MACHINE'
CONFIG_FILE = 'CONFIG_FILE'
SERVERS_FILE = 'SERVERS_FILE'

# Keys used by ReplaceConfigFile, which also
# uses keys from UpdateConfigFile
GFS_NEW_FILE = 'GFS_NEW_FILE'

# Keys used by UpdateConfigFile
# CONFIG_FILE = 'CONFIG_FILE'
FILE_PARAM = 'FILE_PARAM'
LINE = 'LINE'
SERVER_TYPES = 'SERVER_TYPES'
OPERATION = 'OPERATION'
DEPOT_TOKEN_PREFIX = 'DEPOT_TOKEN_PREFIX'

# Keys used by PushFileToGFS
DEPOT_FILE = 'DEPOT_FILE'
DEST_DIR = 'DEST_DIR'

# Keys used by ReplaceSet
NEW_CONFIG_FILE = 'NEW_CONFIG_FILE'
DATADIR = 'DATADIR'
SEGMENT = 'SEGMENT'

# Keys for MultiRequestCreateRequest
DATA = 'DATA'
SERVERTYPE = 'SERVERTYPE'
MACHINEPARAM = 'MACHINEPARAM'
PORTPARAM = 'PORTPARAM'
# Also: CONFIG_FILE = 'CONFIG_FILE' # already defined

# Keys used by setupXXXX requests
MACHINE = 'MACHINE'
DO_CLEANUP = 'DO_CLEANUP'


#
# PushFileToGFS - pushes a given p4 depot file to gfs
#
#   Set() arguments:
#     depot_file:    The file to push
#     dest_dir:      Pushed it to this directory
#
class PushFileToGFS(autorunner.Request):
  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)
  # enddef

  def Set(self, depot_file, dest_dir):
    assert type(depot_file) == type("")
    assert type(dest_dir) == type("")
    self.SetValue(autorunner.TYPE, PUSH_FILE_TO_GFS)
    self.SetValue(DEPOT_FILE, depot_file)
    self.SetValue(DEST_DIR, dest_dir)
  # enddef

  def GetSchedulingInfo(self):
    sched = [os.path.basename(self.GetValue(DEPOT_FILE))]
    return sched
  # enddef
# end class

class ReplaceConfigFile(autorunner.Request):

  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  def Set(self, config_file, gfs_new_file,
          depot_token_prefix='/google/'):

    # Validate the incoming arguments.
    assert type(gfs_new_file) == type("")
    assert type(config_file) == type("")
    assert type(depot_token_prefix) == type("")

    # Stash the arguments into the object.
    self.SetValue(autorunner.TYPE, REPLACE_CONFIG_FILE)
    self.SetValue(CONFIG_FILE, config_file)
    self.SetValue(GFS_NEW_FILE, gfs_new_file)
    self.SetValue(DEPOT_TOKEN_PREFIX, depot_token_prefix)

  def GetSchedulingInfo(self):
    sched = [self.GetValue(CONFIG_FILE)]
    return sched
#
# UpdateConfigFile  - Updates a line in a file that belongs to a config.
#
#
#   Set() arguments:
#     config_file:    The config file
#     file_param:     The parameter in the config that points to the file
#     line:           The line(s) to add or the line/pattern to remove
#     server_types:   Propagate the file to these server types after change
#     operation:      The operation to perform: 1 - add / 2 - remove line
#                       / 3 - remove with pattern
#     depot_token_prefix:    Used to identify the depot portion in the
#                            file name
#
#   Example:
#
#     TEST_CONFIG = 'config.www.google.va'
#     TEST_FILE_PARAM = 'STARTURLS'
#     TEST_LINE = 'http://www.yahoo.com/'
#     TEST_SERVER_TYPES = ['urlmanager']
#     TEST_OPERATION = 1
#     TEST_PREFIX = '/googledata/'
#
#     request_fn = '/export/hda3/configmgr/requests/ReplaceMachine.%s' % seqnum
#     replace_object = configmgr_request.UpdateConfigFile()
#     replace_object.Set(TEST_CONFIG, TEST_FILE_PARAM, TEST_LINE,
#                        TEST_SERVER_TYPES, TEST_OPERATION, TEST_PREFIX)
#     replace_object.Write(request_fn)
#
class UpdateConfigFile(autorunner.Request):

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, config_file, file_param, line, server_types, operation,
          depot_token_prefix='/googledata/'):

    # Validate the incoming arguments.
    assert type(line) == type("")
    assert type(config_file) == type("")
    assert type(file_param) == type("")
    assert type(server_types) == type([])
    for t in server_types:
      assert type(t) == type("")

    # Stash the arguments into the object.
    self.SetValue(autorunner.TYPE, UPDATE_CONFIG_FILE)
    self.SetValue(CONFIG_FILE, config_file)
    self.SetValue(FILE_PARAM, file_param)
    self.SetValue(LINE, line)
    self.SetValue(SERVER_TYPES, string.join(server_types, ","))
    self.SetValue(OPERATION, operation)
    self.SetValue(DEPOT_TOKEN_PREFIX, depot_token_prefix)

  def GetSchedulingInfo(self):
    sched = [self.GetValue(CONFIG_FILE)]
    return sched

#
# ReplaceMachine  - Replace one machine with another in a specified config file.
#                   The new machine should be valid on the same port that the
#                   old machine was serving.
#
#
#   Set() arguments:
#     remove_machine: Machine spec to remove from config file.
#     add_machine:    Machine to add to config file.
#     config_file:    Config file to swap the machines in. The filename is
#                     specified, and should exist in the config manager's
#                     config directory. The configmgr will update this file.
#     server_file:    The file which has the SERVERS map for this config
#                     (most probably same as config_file)
#
#   Example:
#
#     TEST_REM_MACH = '+sjaa3:4000'
#     TEST_ADD_MACH = 'sjbb3'
#     TEST_CONFIG = 'config.www.google.va'
#     TEST_SERVER_FILE = 'config.www.google.va'
#
#     request_fn = '/export/hda3/configmgr/requests/ReplaceMachine.%s' % seqnum
#     replace_object = configmgr_request.ReplaceMachine()
#     replace_object.Set(TEST_REM_MACH, TEST_ADD_MACH,
#                        TEST_CONFIG, TEST_SERVER_FILE)
#     replace_object.Write(request_fn)
#
class ReplaceMachine(autorunner.Request):

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, remove_machine, add_machine, config_file, servers_file):

    # Validate the incoming arguments.
    assert type(remove_machine) == type("")
    assert type(add_machine) == type("")
    assert type(config_file) == type("")
    assert type(servers_file) == type("")

    # Stash the arguments into the object.
    self.SetValue(autorunner.TYPE, REPLACE_MACHINE)
    self.SetValue(REMOVE_MACHINE, remove_machine)
    self.SetValue(ADD_MACHINE, add_machine)
    self.SetValue(CONFIG_FILE, config_file)
    self.SetValue(SERVERS_FILE, servers_file)

  def GetSchedulingInfo(self):
    sched = [self.GetValue(SERVERS_FILE),
             self.GetValue(CONFIG_FILE)]
    if self.GetValue(REMOVE_MACHINE):
      sched.append(self.GetValue(REMOVE_MACHINE))
    if self.GetValue(ADD_MACHINE):
      sched.append(self.GetValue(ADD_MACHINE))

    return sched

#
# ReplaceSet - Replace an active set in the running config with a new
#              equivelant set. All the machines in the new set should be
#              valid and ready to serve. The configmgr will start the new
#              servers and switch the new set live.
#
#   Set() arguments:
#     new_config_file: File name of the config file we are switching to. This
#                      file must exist in /root/google/config on the config
#                      manager.
#     datadir:         Datadir for the new set.
#
#   Example:
#
#     TEST_NEW_CONFIGFILE = 'config.www.lvl1.va'
#     TEST_DATADIR = '/export/hda3/daily200205062010datadir-data'
#
#     request_fn = '/export/hda3/configmgr/requests/ReplaceSet.%s' % seqnum
#     replace_set = configmgr_request.ReplaceSet()
#     replace_set.Set(TEST_NEW_CONFIGFILE, TEST_DATADIR, TEST_SEGMENT)
#     replace_set.Write(request_fn)
#

class ReplaceSet(autorunner.Request):

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  #
  def Set(self, new_config_file, datadir, segment):
    self.SetValue(autorunner.TYPE, REPLACE_SET)
    self.SetValue(NEW_CONFIG_FILE, new_config_file)
    self.SetValue(SEGMENT, segment)
    self.SetValue(DATADIR, datadir)

if __name__ == '__main__':
  import sys
  sys.exit("Import this module")

###############################################################################

#
# MultiRequestCreateRequest -- this request spawns multiple requests
#       of a specified type, one for each machine:port belonging for a type
#
# Example:
#
#    DATA = { 'TRANSACTION_TYPE': 'HUPSERVER', }
#    SERVERTYPE = 'web'
#    MACHINEPARAM = "machine"
#    PORTPARAM = "port"
#
#   will spawn requests to hup all gws servers
#

class MultiRequestCreateRequest(autorunner.Request):
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  def Set(self, data, servertype, machineparam, portparam, config_file):

    assert type(data) == type({})
    assert type(servertype) == type("")
    assert type(machineparam) == type("")
    assert type(portparam) == type("")
    assert type(config_file) == type("")

    self.SetValue(autorunner.TYPE, MULTI_REQUEST_CREATOR)
    self.SetValue(CONFIG_FILE, config_file)
    self.SetValue(DATA, repr(data))
    self.SetValue(SERVERTYPE, servertype)
    self.SetValue(MACHINEPARAM, machineparam)
    self.SetValue(PORTPARAM, portparam)

  def GetSchedulingInfo(self):
    return ["global"]

###############################################################################
#
# Base for a bunch of setup requests
#  Don't use this, instead use one of the children:
#    - SetupBinariesOnMachine
#    - SetupKernelOnMachine
#    - SetupServersOnMachine
#
class BaseSetupMachine(autorunner.Request):

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, machine, config_file):

    # Validate the incoming arguments.
    assert type(machine) == type("")
    assert type(config_file) == type("")

    # Stash the arguments into the object.
    self.SetValue(autorunner.TYPE, self.GetRequestTypeString())
    self.SetValue(MACHINE, machine)
    self.SetValue(CONFIG_FILE, config_file)

  # We synchronize just on the machine. Synchronizing on the config file
  # is not necessary
  def GetSchedulingInfo(self):
    return [self.GetValue(MACHINE)]

  # Override this
  def GetRequestTypeString(self):
    raise "Please override GetRequestTypeString, or don't use BaseSetupMachine"

#
# Request to setup binaries on a machine
#
class SetupBinariesOnMachine(BaseSetupMachine):
  def GetRequestTypeString(self):
    return SETUP_BINARIES_ON_MACHINE

#
# Request to setup the kerner on a machine
#
class SetupKernelOnMachine(BaseSetupMachine):
  def GetRequestTypeString(self):
    return SETUP_KERNEL_ON_MACHINE


#
# Request to setup the servers (server specific) on a machine
#
class SetupServersOnMachine(BaseSetupMachine):
  def GetRequestTypeString(self):
    return SETUP_SERVERS_ON_MACHINE


#
# Request to setup common stuf on the machine
#
class SetupCommonOnMachine(autorunner.Request):

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, machine, do_cleanup):

    # Validate the incoming arguments.
    assert type(machine) == type("")
    assert type(do_cleanup) == type(1)

    # Stash the arguments into the object.
    self.SetValue(autorunner.TYPE, SETUP_COMMON_ON_MACHINE)
    self.SetValue(MACHINE, machine)
    self.SetValue(DO_CLEANUP, do_cleanup)

  # We synchronize just on the machine. Synchronizing on the config file(s)
  # is not necessary
  def GetSchedulingInfo(self):
    return [self.GetValue(MACHINE)]

###############################################################################
#
# Request used just for testing
#

DUMMYTYPE     = 'DUMMYTYPE'
SLEEP_LENGTH  = 'SLEEP_LENGTH' # Required request field
EXIT_CODE     = 'EXIT_CODE'    # Optional request field - tell script to 'fail'
SYNC_INFO     = 'SYNC_INFO'
EXPECTED_FILE = 'EXPECTED_FILE'

class TestRequest(autorunner.Request):
  def Set(self, sleep_length, exit_code = 0, sync_info = None):
    self.SetValue(autorunner.TYPE, DUMMYTYPE)
    self.SetValue(SLEEP_LENGTH, sleep_length)
    self.SetValue(EXIT_CODE, exit_code)
    self.SetValue(SYNC_INFO, sync_info)

  def GetSchedulingInfo(self):
    sync_info = self.GetValue(SYNC_INFO)
    if None != sync_info:
      return [sync_info]
    return []

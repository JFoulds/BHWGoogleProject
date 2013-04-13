#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Catalin Popescu
#
# epoch_requests.py
# Define some requests to advance/delete epochs
#

from google3.enterprise.legacy.production.configmgr import autorunner

# 'REQUEST_HANDLER' for all config manager types:
CONFIG_MGR = 'CONFIG_MGR'

EPOCHADVANCE = "EPOCHADVANCE"
EPOCHDELETE  = "EPOCHDELETE"

CONFIG_FILE         = "CONFIG_FILE"
SERVER_TYPES        = "SERVER_TYPES"
EPOCH_LIST          = "EPOCH_LIST"
EPOCH_NUM           = "EPOCH_NUM"

###############################################################################

class EpochAdvanceRequest(autorunner.Request):
  """ This class handles requests to advance the epoch in the rtservers """
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, epoch_num, server_types, config_file):
    assert type(epoch_num) == type(1)
    assert type(server_types) == type([])
    for t in server_types:
      assert t  in ["base_indexer", "daily_indexer", "rt_indexer"]

    self.SetValue(autorunner.TYPE, EPOCHADVANCE)
    self.SetValue(EPOCH_NUM, epoch_num)
    self.SetValue(SERVER_TYPES, repr(server_types))
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    return ["global"]

###############################################################################

class EpochDeleteRequest(autorunner.Request):
  """ This class handles requests to advance the epoch in the rtservers """
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, epoch_list, server_types, config_file):
    assert type(epoch_list) == type([])
    assert type(server_types) == type([])
    for e in epoch_list:
      assert type(e) == type(1)
    for t in server_types:
      assert t in ["base_indexer", "daily_indexer", "rt_indexer"]

    self.SetValue(autorunner.TYPE, EPOCHDELETE)
    self.SetValue(EPOCH_LIST, repr(epoch_list))
    self.SetValue(SERVER_TYPES, repr(server_types))
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    return ["global"]

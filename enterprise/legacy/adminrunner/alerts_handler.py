#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""This module for the adminrunner deals with the configuration of
Alerts.

The commands that we respond to are:

  1. status

     Is alerts enabled on the box?
     
  2. enable

     Enables alerts on the box.
     
  3. disable

     Disables alerts on the box.
"""

__author__ = 'hareesh@google.com (Hareesh Nagarajan)'

import sys
import threading

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import C

class AlertsHandler(admin_handler.ar_handler):
  def __init__(self, conn, command, prefixes, params, cfg=None):
    if cfg is not None:
      self.cfg = cfg
      return
    self.alerts_lock_ = threading.Lock()
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    
  def get_accepted_commands(self):
    return {
      "enable": admin_handler.CommandInfo(0, 0, 0, self.Enable),
      "disable": admin_handler.CommandInfo(0, 0, 0, self.Disable),
      "status": admin_handler.CommandInfo(0, 0, 0, self.Status),
      }

  def Enable(self):
    # TODO(hareesh): Check if LDAP settings are set and are
    # valid. Only then must we enable alerts.
    self.cfg.setGlobalParam(C.ALERTS2, 1)
    res = self.cfg.globalParams.WriteConfigManagerServerTypeRestartRequest(
        "entfrontend")
    return not res

  def Disable(self):
    self.cfg.setGlobalParam(C.ALERTS2, 0)
    res = self.cfg.globalParams.WriteConfigManagerServerTypeRestartRequest(
        "entfrontend")
    return not res

  def Status(self):
    logging.info("AlertsHandler: status")
    return self.cfg.getGlobalParam(C.ALERTS2)

if __name__ == '__main__':
  sys.exit('Import this module')

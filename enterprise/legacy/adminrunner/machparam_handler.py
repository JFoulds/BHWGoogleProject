#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.
#

""" 'machparam' handler for adminrunner

'getparam' is the only command it accepts, which returns the value of a SVS
variable of a machine. This handler uses the mach_param_cache to get the value.

e.g. 'machparam getparam cpucnt ent1'.

"""

__author__ = 'wanli@google.com (Wanli Yang)'

import string
from google3.pyglib import logging
import os
import time
import re
import copy

from google3.enterprise.legacy.adminrunner import admin_handler


class MachParamHandler(admin_handler.ar_handler):
  """
  Processes all the "machparam" commands for AdminRunner
  """
  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "getparam"   :    admin_handler.CommandInfo(
       2, 0, 0, self.getparam),
      }

  def getparam(self, factName, machine):
    """Returns a python string the name & value of the required parameter

    Arguments:
      factName: 'cpucnt'
      machine: 'ent1'
    Returns:
      4
    """

    return self.cfg.mach_param_cache.GetFact(factName, machine)


if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

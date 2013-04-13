#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Catalin Popescu
#
# update_requests.py
# Define some requests to set/update parameters
#

from google3.enterprise.legacy.production.configmgr import autorunner

# 'REQUEST_HANDLER' for all config manager types:
CONFIG_MGR = 'CONFIG_MGR'

UPDATEPARAM         = "UPDATEPARAM"
MACHINEUPDATEPARAM  = "MACHINEUPDATEPARAM"
UPDATERESTRICT      = "UPDATERESTRICT"

CONFIG_FILE         = "CONFIG_FILE"
PARAM               = "PARAM"
VALUE               = "VALUE"
FORCE               = "FORCE"
FORCE_NO_VALIDATE   = "FORCE_NO_VALIDATE"
PORT                = "PORT"
MACHINE             = "MACHINE"
CMD                 = "CMD"
FLAGNAME            = "FLAGNAME"
OP                  = "OP"
PARAMTYPE           = "PARAMTYPE"
RESTRICT            = "RESTRICT"
ENTHOME             = "ENTHOME"

###############################################################################

class ConfigUpdateRequest(autorunner.Request):
  """ This class handles requests to update a parameter """
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, param, value, op, force, force_no_validate, config_file):
    assert type(param) in ( type(""), type((1,2,3)) )
    assert type(force) == type(1)
    assert op in ('set_var', 'del_var',
                  'set_file_var_content', 'del_file_var_content')
    # The check below is designed to work with Python 2.2 or 2.3
    assert (type(force_no_validate) == type(1) or
            type(force_no_validate) == type(True))
    assert type(config_file) == type("")

    self.SetValue(autorunner.TYPE, UPDATEPARAM)
    self.SetValue(PARAM, param)
    self.SetValue(VALUE, repr(value))
    self.SetValue(OP, op)
    self.SetValue(FORCE, force)
    self.SetValue(FORCE_NO_VALIDATE, force_no_validate)
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    return ["global"]

class RestrictUpdateRequest(autorunner.Request):
  """ This request updates the restrict data -- Enterprise specific (for now)"""
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  def Set(self, restrict, value, op, enthome):
    assert type(restrict) == type("")
    assert op in ("add", "del")
    assert type(enthome) == type("")

    self.SetValue(autorunner.TYPE, UPDATERESTRICT)
    self.SetValue(RESTRICT, restrict)
    self.SetValue(VALUE, repr(value))
    self.SetValue(OP, op)
    self.SetValue(ENTHOME, enthome)

  def GetSchedulingInfo(self):
    return ["global"]

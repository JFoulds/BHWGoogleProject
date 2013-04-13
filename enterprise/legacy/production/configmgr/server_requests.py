#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Catalin Popescu
#
# server_requests.py
# Define some requests to hup/restart/talk with servers
#

from google3.enterprise.legacy.production.configmgr import autorunner

# 'REQUEST_HANDLER' for all config manager types:
CONFIG_MGR = 'CONFIG_MGR'

HUP_SERVER          = "HUP_SERVER"
RESTART_SERVER      = "RESTART_SERVER"
KILL_SERVER         = "KILL_SERVER"
RESTART_ENT_SERVING = "RESTART_ENT_SERVING"
SEND_SERVER_COMMAND = "SEND_SERVER_COMMAND"

CONFIG_FILE        = "CONFIG_FILE"
PORT               = "PORT"
MACHINE            = "MACHINE"
CMD                = "CMD"
EXPECTED_ANSWER    = "EXPECTED_ANSWER"

###############################################################################

class HupServerRequest(autorunner.Request):
  """
  This guy hups a server that runs on  a port, on a machine
  """

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, machine, port):
    assert type(port) == type(1)
    assert type(machine) == type("")

    self.SetValue(autorunner.TYPE, HUP_SERVER)
    self.SetValue(MACHINE, machine)
    self.SetValue(PORT, port)

  def GetSchedulingInfo(self):
    return ["%s:%s" % (self.GetValue(MACHINE), self.GetValue(PORT))]

###############################################################################

class RestartServerRequest(autorunner.Request):
  """
  This guy restarts/kills a server that runs on a port, on a machine
  """

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, machine, port, config_file, kill_only=0):
    assert type(port) == type(1)
    assert type(machine) == type("")
    assert type(config_file) == type("")

    if kill_only:
      req_type = KILL_SERVER
    else:
      req_type = RESTART_SERVER
    self.SetValue(autorunner.TYPE, req_type)
    self.SetValue(MACHINE, machine)
    self.SetValue(PORT, port)
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    return ["%s:%s" % (self.GetValue(MACHINE), self.GetValue(PORT))]

###############################################################################

class RestartEntServingRequest(autorunner.Request):
  """
  Request to restart the entire enterprise serving
  """

  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, config_file):
    assert type(config_file) == type("")

    self.SetValue(autorunner.TYPE, RESTART_ENT_SERVING)
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    return ["global"]

###############################################################################

class SendServerCommandRequest(autorunner.Request):
  # Pass the type of request handler back to superclass.
  def __init__(self):
    autorunner.Request.__init__(self)
    self.SetValue(autorunner.HANDLER, CONFIG_MGR)

  # Set the request-type specific items.
  def Set(self, machine, port, cmd, expected_answer, config_file):
    assert type(port) == type(1)
    assert type(machine) == type("")
    assert type(port) == type(1)
    assert type(cmd) == type("")
    assert type(expected_answer) == type("")
    assert type(config_file) == type("")

    self.SetValue(autorunner.TYPE, SEND_SERVER_COMMAND)
    self.SetValue(MACHINE, machine)
    self.SetValue(PORT, port)
    self.SetValue(CMD, cmd)
    self.SetValue(EXPECTED_ANSWER, expected_answer)
    self.SetValue(CONFIG_FILE, config_file)

  def GetSchedulingInfo(self):
    machine = self.GetValue(MACHINE)
    port = self.GetValue(PORT)
    if not machine or not port:
      return ["global"]
    return ["%s:%s" % (machine, port)]

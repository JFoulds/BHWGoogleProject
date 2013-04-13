#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com ==-- from ParamsHandler.java
#
# The "params" command handler for AdminRunner
#
###############################################################################

import string
import types
import commands
import threading

from google3.pyglib import logging

from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.adminrunner import ar_exception
from google3.enterprise.legacy.util import config_utils
from google3.enterprise.legacy.util import reconfigurenet_util

###############################################################################

true  = 1
false = 0

DIAGNOSE_COMMAND = "cd %s/local/google3/enterprise/legacy/checks; echo %s | " \
                   "ENTERPRISE_HOME=%s /usr/bin/python2.4 -u network_diag.py -interactive " \
                   "%s 2> %s"

###############################################################################

class ParamsHandler(admin_handler.ar_handler):
  """
  Processes all the params related commands for AdminRunner
  """
  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg in non-null only for testing (we cannot have multiple constructore)
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "save"              : admin_handler.CommandInfo(
      0, 0, 0, self.save),
      "getall"            : admin_handler.CommandInfo(
      0, 0, 0, self.getall),
      "get"               : admin_handler.CommandInfo(
      1, 0, 0, self.get),
      "set"               : admin_handler.CommandInfo(
      1, 1, 0, self.set),
      "getfile"           : admin_handler.CommandInfo(
      1, 0, 0, self.getfile),
      "setfile"           : admin_handler.CommandInfo(
      1, 0, 1, self.setfile),
      "validate"          : admin_handler.CommandInfo(
      1, 0, 0, self.validate),
      "validparams"       : admin_handler.CommandInfo(
      0, 0, 0, self.validparams),
      "getinstallstate"   : admin_handler.CommandInfo(
      0, 0, 0, self.getinstallstate),
      "reconfigurenet"    : admin_handler.CommandInfo(
      0, 0, 0, self.reconfigurenet),
      "diagnosenet"       : admin_handler.CommandInfo(
      0, 0, 1, self.diagnosenet),
      "getserverport"     : admin_handler.CommandInfo(
      1, 0, 0, self.getserverport)
      }

  #############################################################################

  def save(self):
    # This saves the paraeters - on error it throws something
    self.cfg.saveParams()
    return 0

  def getall(self):
    """ Returns all the global parameters and their values """
    return self.cfg.globalParams.write_params_to_string(
      self.cfg.globalParams.GetAllVars())

  def get(self, paramName):
    """Returns a python string with the name & value of the required
    parameter"""
    return "%s = %s" % (paramName,
                        repr(self.cfg.globalParams.var(paramName)))

  def set(self, paramName, value):
    """ Sets the parameter to a specified value """
    val = {}
    config_utils.SafeExec(string.strip(value), val)
    if not val.has_key(paramName): return 1
    value = val[paramName]

    errors = self.cfg.globalParams.set_var(paramName, value, true)
    return admin_handler.formatValidationErrors(errors)

  def getfile(self, paramName) :
    """ Returns the content of a file parameter """
    filename = self.cfg.getGlobalParam(paramName)
    out = ''
    if filename is None:
      logging.info('No filename set for %s' % paramName)
    else:
      try:
        out = open(filename, "r").read()
      except Exception, e:
        logging.info('Does not exist (%s,%s)' % (paramName, filename))
    return "%s\n%s" % (len(out), out)

  def setfile(self, paramName, value):
    """ Sets the content of a file parameter """
    errors = self.cfg.globalParams.set_file_var_content(
      paramName, value, true)
    return admin_handler.formatValidationErrors(errors)

  def validate(self, paramName):
    """ Validates a parameter in the local context """
    errors = self.cfg.globalParams.ValidateVar(paramName)
    return admin_handler.formatValidationErrors(errors)

  def validparams(self):
    """ Checks if parametes are valid """
    if not self.cfg.globalParams.GetValidationStatus():
      self.cfg.globalParams.ValidateInvalid()
    invalidParams = self.cfg.globalParams.GetInvalidNames()
    if invalidParams:
      return "%s\n1" % string.join(invalidParams, "\n")
    return "0"

  def getinstallstate(self):
    """ Returns tyhe install state """
    return self.cfg.getInstallState()

  def reconfigurenet(self):
    """ Call reconfigurenet script on all machines """

    return not reconfigurenet_util.doReconfigureNet(self.cfg.globalParams)

  def diagnosenet(self, diagTasks):
    """
    read in a bunch of items to diagnose, perform the tests and then
    return the results on the output stream.
    """

    # TODO: not unittested diagnosenet
    lines = string.split(diagTasks, "\n")
    svr_mgr = self.cfg.globalParams.GetServerManager()
    fsgw_set = svr_mgr.Set('fsgw')
    fsgw_hosts = fsgw_set.Hosts()

    fsgw_host = 'localhost'
    if fsgw_hosts:
      fsgw_host = fsgw_hosts[0]

    cmd = DIAGNOSE_COMMAND % (
      self.cfg.entHome,
      commands.mkarg("%s\n%s" % (len(lines), diagTasks)),
      self.cfg.entHome,
      fsgw_host,
      commands.mkarg("%s/networkdiag_out" % (
      self.cfg.getGlobalParam("LOGDIR"))),
      )
    executed = 0
    while not executed:
      try:
        err, out = E.getstatusoutput(cmd)
        executed = 1
      except IOError:
        pass
    # diagnoseIt! The script returns data (post-CommandPipe processing)
    # in the form "status\ntuple1\ntuple2\n..." We're not concerned with
    # faulty script output, and pass the response for the UI to deal with it.

    return out

  def getserverport(self, name):
    """
    Get a server's port.  The AdminCaller needs to generate a URL to the
    enterprise frontend whose port depends on the install state.
    """
    return self.cfg.globalParams.GetServerManager().Set(name).Servers()[0] \
           .port()

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

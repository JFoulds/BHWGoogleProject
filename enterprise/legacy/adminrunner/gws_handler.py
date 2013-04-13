#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com from GwsHandler.java
#
# The gws hupping for AdminRunner
#
###############################################################################

from google3.enterprise.legacy.adminrunner import admin_handler

from google3.enterprise.legacy.production.configmgr import server_requests
from google3.enterprise.legacy.production.configmgr import configmgr_request

###############################################################################

class GwsHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params, cfg = None):
    # cfg is non-null only for testing (we cannot have multiple constructore)
    if cfg != None:
      self.cfg = cfg
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "hup" :          admin_handler.CommandInfo(
      0, 0, 0, self.hup),
      }

  #############################################################################

  def hup(self):
    """ This will hups all the gwsses """

    # Write a config manager request to hup all gwssers

    # dummy
    req = server_requests.HupServerRequest()
    req.Set("dummy", 1)

    # The actual requests that spawns hup requests for all gwssers
    the_req = configmgr_request.MultiRequestCreateRequest()
    the_req.Set(
      req.datadict, 'web',
      server_requests.MACHINE, server_requests.PORT,
      self.cfg.globalParams.ComposeConfigFileName(
        self.cfg.globalParams.GetEntHome()))
    ret = not self.cfg.globalParams.WriteConfigManagerRequest(the_req)

    # distributes all outstanding file and increments configversion
    self.cfg.saveParams()

    return ret

###############################################################################

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

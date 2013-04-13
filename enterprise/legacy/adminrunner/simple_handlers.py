#!/usr/bin/python2.4
#
# Copyright 2002-2003 Google, Inc.
# cpopescu@google.com
#
# Various small handlers
#
##############################################################################

from google3.enterprise.legacy.adminrunner import admin_handler

###############################################################################

class v_handler:
  """ Returns the current status """
  def __init__(self, conn, command, prefixes, params):
    self.cfg  = conn.cfg
    self.params = params

  def handle_read(self, data):
    pass

  def handle_write(self):
    if len(self.params) > 0:
      param = self.params[0]
    else:
      param = "CONFIGVERSION"
    return (1,
            "%s\n%s\n" % (repr(self.cfg.getGlobalParam(param)),
                          admin_handler.ACK),
            0)

###############################################################################

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
# All Rights Reserved.
# Original Author: Ryan Tai
#

"""Implement handler for support call feature.

This script has two main functions: start the support call daemon and
to control the daemon.
This script is used by the GUI to communicate with the support daemon.
There are four communication options for the GUI: start, stop, statusStr
and stauts.

"""

import os
import sys
from google3.enterprise.legacy.util import E
import commands

from google3.enterprise.legacy.adminrunner import admin_handler


class SupportCallHandler(admin_handler.ar_handler):
  """Handles configuration support call methods.
  """

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.supportWrapperPath = (
        '%s/local/google3/enterprise/legacy/util/makesshcall.py'
        % self.cfg.getGlobalParam('ENTERPRISE_HOME'))

  def get_accepted_commands(self):
    return {
      'start'  : admin_handler.CommandInfo(1, 0, 0, self.start),
      'test'   : admin_handler.CommandInfo(0, 0, 0, self.test),
      'stop'   : admin_handler.CommandInfo(0, 0, 0, self.stop),
      'status' : admin_handler.CommandInfo(0, 0, 0, self.status),
      'statusStr' : admin_handler.CommandInfo(0, 0, 0, self.statusStr),
      }

  def start(self, boxId):
    """ start support call
    """
    cmd = '%s --command=dstart' % self.supportWrapperPath
    os.system(cmd)
    # wait till daemon is ready
    cmd = '%s --command=ready' % self.supportWrapperPath
    while commands.getoutput(cmd) == '0':
      pass
    cmd = '%s --command=start --id=%s' % (self.supportWrapperPath, boxId);
    retcode, output = E.getstatusoutput(cmd)
    return output

  def stop(self):
    """ stop support call
    """
    cmd = '%s --command=stop' % self.supportWrapperPath
    retcode, output = E.getstatusoutput(cmd)
    return output

  def test(self):
    """ test suuport call connection
    """
    cmd = '%s --command=test' % (self.supportWrapperPath);
    retcode, output = E.getstatusoutput(cmd)
    return output

  def status(self):
    """ get current status code
    """
    cmd = '%s --command=status' % self.supportWrapperPath
    retcode, output = E.getstatusoutput(cmd)
    return output

  def statusStr(self):
    """ get current status in string form
    """
    cmd = '%s --command=statusStr' % self.supportWrapperPath
    retcode, output = E.getstatusoutput(cmd)
    return output

if __name__ == "__main__":
  sys.exit('Import this module')

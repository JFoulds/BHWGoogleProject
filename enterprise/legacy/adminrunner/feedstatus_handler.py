#!/usr/bin/python2.4

#
# Copyright 2004-2006 Google Inc.
# All rights reserved.
# Phuong Nguyen <pn@google.com>
#
# Deal with feed status data
#
# Commands:
#
# 1. getdir
#             Return the list of files in the directory.
#
# 2. getstatus
#             Return status of a feed
#

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import gfile
from google3.pyglib import logging
import os
import urllib
from google3.enterprise.legacy.setup import serverflags

class FeedStatusHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "getdir": admin_handler.CommandInfo(0, 0, 0, self.getdir),
      "getstatus": admin_handler.CommandInfo(1, 0, 0, self.getstatus),
      "delete": admin_handler.CommandInfo(1, 0, 0, self.delete),
      }

  def getdir(self):
    '''Get the newline-separated list of files in the feed status directory.'''
    dirname = self.cfg.getGlobalParam("FEED_STATUS_DIR")
    if not gfile.Exists(dirname):
      logging.info('dir name: %s not exist' % dirname)
      return "1\nfeed_status_dir = %s" % dirname

    files = gfile.ListDir(dirname)
    return "0\n%s" % '\n'.join(files)

  def getstatus(self, filename):
    '''Return the first line of a feed status file.'''
    try:
      dirname = self.cfg.getGlobalParam('FEED_STATUS_DIR')
      filename = os.path.join(dirname, filename)
      # read only the first line, the rest of the file may be too big
      # see bug 76929
      out = gfile.GFile(filename).readline()
    except IOError, e:
      logging.error(str(e))
      return "1"
    return "0\n%s" % out

  def delete(self, entry):
    '''Remove a feed source'''
    config = self.cfg.globalParams
    logging.info("deleting feed %s" % entry)
    srv_mngr = config.GetServerManager()
    set = srv_mngr.Set('entfrontend')
    feedergateservers = set.BackendHostPorts('feedergate')[0:1]
    feedergate = serverflags.MakeHostPortsArg(feedergateservers)
    url = "http://%s/deletefeed?datasource=%s" % (feedergate,
                                                  urllib.quote(entry))
    logging.info("fetching %s" % url)
    try:
      file = urllib.urlopen(url)
      logging.info(file.read())
      file.close()
      return "0"
    except IOError, e:
      logging.error(str(e))
    return "1"

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""borgmon_gfs_check checks if GFS is in good shape so we can start borgmon.

Borgmon has a dependency on GFS for the logio checkpoint reading. This script
is meant to provide a check that GFS is up and main election is done, so when
we start borgmon, it comes up with proper checkpoint data.
The script could have involved a wait and check in while loop but we changed
this to a simpler logic to just return 0 if the GFS is good and 1 otherwise and
leaving the restart and timeout logic to localbabysitter which would re-attempt
to start borgmon in 300 seconds again.
"""

__author__ = 'vardhmanjain@google.com (Vardhman Jain)'

import sys
import time
from google3.pyglib import app
from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.core import gfs_utils
from google3.enterprise.core import core_utils

def CheckGFSState(ver, testver, nodes=None, gfs_status_set=0, gfs_status=None):
  """Checks the GFS Main Election Status.

  Args:
    ver: GSA version
    testver: if its test mode
    nodes: Nodes on the box (for unit test)
    gfs_status_set: is caller sending gfs_status already
    gfs_status: Unit test only, the GFS status.

  Return:
    1 if State is not good (Main election hasn't happened yet). 0 otherwise.
    Always returns 0 for oneways.
  """
  if not nodes:
    nodes = core_utils.GetNodes()
  if len(nodes) == 1:
    return 0

  if not gfs_status_set:
    # print 'finding gfs_status for ver=%s testver=%s' % (ver, testver)
    gfs_status = gfs_utils.CheckNoMainUsingElectionStatus(ver, testver)

  if gfs_status == 0:
    return 0

  return 1

def usage():
  print """./borgmon_gfs_check.py "ver" [testver] [timeout]

  ver is required paratmeter.
  testver is 0 or 1. Defaults to 0.
  timeout is in seconds. Defaults to 360.
  """

def main(argv):
  # Check if the box is cluster first.
  nodes = core_utils.GetNodes()
  if len(nodes) == 1:
    sys.exit(0)

  if len(argv) < 2:
    usage()
    sys.exit(1)
  ver = argv[1]

  if len(argv) < 3:
    argv.append(0)
  testver = int(argv[2])

  # Check the GFS main election status
  status = CheckGFSState(ver, testver, nodes, 0, None)
  if status == 0:
    logging.info('GFS status is good, exiting')
    sys.exit(0)

  # return a non zero status.
  sys.exit(1)

if __name__ == '__main__':
  app.run()

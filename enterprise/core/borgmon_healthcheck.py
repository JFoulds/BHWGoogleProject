#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Print RESTART on stdout if this is the borgmon master node and borgmon
needs to be restarted. Exit without printing otherwise.

Usage:
  borgmon_healthcheck.py [ver] [is_testver]

Example:
  borgmon_healthcheck.py 4.6.4 0
"""

__author__ = 'npelly@google.com (Nick Pelly)'

import socket
import sys

from google3.enterprise.legacy.scripts import check_healthz
from google3.enterprise.core import core_utils
from google3.enterprise.util import borgmon_util


def main(argv):
  if len(argv) < 2:
    sys.exit(__doc__)

  #TODO(con): get python2.4 working and remove this
  if argv[1] == "True":
    is_testver = 1
  elif argv[1] == "False":
    is_testver = 0
  else:
    try:
      is_testver = int(argv[1])
    except ValueError:
      sys.exit(__doc__)

  ver = argv[0]

  # Create a borgmon_util object to do work for us
  if is_testver:
    mode = borgmon_util.TEST
  else:
    mode = borgmon_util.ACTIVE
  borgmonUtil = borgmon_util.BorgmonUtil(ver, mode=mode)

  # First check if we are a cluster and this is not borgmon master node.
  # If so, exit.
  if (core_utils.GetTotalNodes() > 1 and
      (socket.gethostbyname(borgmonUtil.GetBorgmonHostname()) !=
       socket.gethostbyname(socket.gethostname()))):
    sys.exit(0)

  # Now check that /healthz is ok. If so, exit
  if check_healthz.CheckHealthz(borgmonUtil.GetBorgmonPort()):
    sys.exit(0)

  # This is the borgmon master and /healthz failed. print RESTART
  print 'RESTART'


if __name__ == '__main__':
  main(sys.argv[1:])

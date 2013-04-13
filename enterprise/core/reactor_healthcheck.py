#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Print RESTART on stdout if Borgmon Reactor requires a restart.
Exit without printing otherwise.

Usage:
  reactor_healthcheck.py [ver] [is_testver]

Example:
  borgmon_healthcheck.py 4.6.4 0
"""

__author__ = 'npelly@google.com (Nick Pelly)'

import sys

from google3.enterprise.legacy.scripts import check_healthz
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

  if is_testver:
    borgmon_mode = borgmon_util.TEST
  else:
    borgmon_mode = borgmon_util.ACTIVE
  bu = borgmon_util.BorgmonUtil(ver, mode=borgmon_mode)

  # Now check /healthz
  if not check_healthz.CheckHealthz(bu.GetReactorPort()):
    print 'RESTART'

if __name__ == '__main__':
  main(sys.argv[1:])

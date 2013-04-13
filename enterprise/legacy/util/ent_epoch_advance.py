#!/usr/bin/python2.4
# (c) 2002 and onwards Google, Inc.
# This simple script is run to advance the index epoch using adminrunner

import sys
from google3.enterprise.legacy.util import admin_runner_utils

if __name__ == "__main__":
  if len(sys.argv) != 1:
    sys.exit(1)
  (ar, config) = admin_runner_utils.GetARClientAndGlobalConfig()
  sys.exit(not ar.EpochAdvance())

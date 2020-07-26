#!/usr/bin/python2.4
#
# (c) 2003 Google inc.
# hongjun@google.com
#
# This script send request to adminrunner to generate status report
#
###############################################################################
"""
Usage:
    gen_status_report.py <enthome>

"""
###############################################################################
import sys
import time

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import adminrunner_client
###############################################################################

def GenerateStatusReport(config):
  main = config.var('MASTER')
  ar = adminrunner_client.AdminRunnerClient(main, 2100)
  return ar.GenStatusReport()


def main(argv):
  argc = len(argv)
  if argc != 1:
    sys.exit(__doc__)

  config = entconfig.EntConfig(argv[0])
  if not config.Load():
    sys.exit(__doc__)

  success = GenerateStatusReport(config)

  if not success:
    logging.error("Failed")
    sys.exit(__doc__)

  logging.info("Done")
  sys.exit(0)


###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

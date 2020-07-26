#!/usr/bin/python2.4
#
# (c)2001 Google inc.
# David Watson
#
# This script runs nightly log report generation
#
###############################################################################
"""
Usage:
     nightly_log.py <enthome> <crawl> <port>
"""
###############################################################################

import sys
import string
import time
import commands

from google3.enterprise.legacy.util import E
from google3.pyglib import logging
from google3.enterprise.legacy.util import find_main
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import adminrunner_client

###############################################################################

def main(argv):
  config = entconfig.EntConfig(argv[0])
  if not config.Load():  sys.exit(__doc__)
  try:
    crawl = argv[1]
    port = string.atoi(argv[2])
  except:
    sys.exit(__doc__)

  machines = config.var('MACHINES')
  main = find_main.FindMain(port, machines)

  # The name of this machine
  crt_machine = E.getCrtHostName()

  if len(main) != 1 or main[0] != crt_machine:
    logging.info("I am not the main")
    sys.exit(0) # not a problem

  # find out the date 24 hours ago
  year,month,day = time.localtime(time.time() - 60*60*24 )[0:3]
  date1 = "date_%d_%d_%d" % (month, day, year)
  date2 = "date %d %d %d" % (month, day, year)

  logging.info("Running %s for %s" % (sys.argv[0], date2))

  # 1. run log_report.py for each crawl
  ar = adminrunner_client.AdminRunnerClient("localhost", port)
  if not ar.LogReportStart(crawl, date1):
    sys.exit("Error starting crawl for " + crawl)
  logging.info("Started log_report for %s/%s" %(crawl, date1))

  # 2. run apache_log.py for each crawl
  apache_cmd = "./apache_log.py %s update %s %s" % (argv[0], crawl, date2)
  (status, output) = commands.getstatusoutput(apache_cmd)
  if status != 0:
    logging.fatal("apache_log failed: %s" % output)
  logging.info("Finished apache_log: %s" % output)

  logging.info("Done")

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

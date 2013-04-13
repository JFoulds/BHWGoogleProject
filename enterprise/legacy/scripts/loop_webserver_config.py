#!/usr/bin/python2.4
#
# (c) 2000 Google inc.
# maxi@google.com based on cpopescu@google.com
#
# runs webserver_config.py in a loop.
#
###############################################################################
"""
Usage:
       loop_webserver_config <global_config_file>

"""
###############################################################################

import os
import sys
import time

from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.util import E
from google3.pyglib import logging

###############################################################################

def main(argv):

  if len(argv) != 1:
    sys.exit(__doc__)

  pidfile = E.GetPidFileName('loop_webserver_config')
  E.WritePidFile(pidfile)

  config = config_factory.ConfigFactory().CreateConfig(argv[0])
  if not config.Load():
    logging.error("Cannot read file: %s " % argv[0])

  bashrc = config.var('ENTERPRISE_HOME') + "/local/conf/ent_bashrc"
  # the loop
  while 1:
    cmd = (". %s; /usr/bin/python2.4 webserver_config.py %s" %
           (bashrc, config.var('ENTERPRISE_HOME')))
    logging.info("Executing %s" % cmd)
    os.system(cmd)

    # sleep for a while
    time.sleep(5)

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

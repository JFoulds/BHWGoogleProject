#!/usr/bin/python2.4
#(c) 2002 Google inc
# cpopescu@google.com
#
# Restarts everything
#

import sys
import os

from google3.pyglib import flags
from google3.enterprise.legacy.production.babysitter import config_factory

true  = 1
false = 0
FLAGS = flags.FLAGS
flags.DEFINE_string("config_file", "", "The configuration file")

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if not FLAGS.config_file: sys.exit("Config file must be specified")

  cp = config_factory.ConfigFactory().CreateConfig(FLAGS.config_file)

  if not cp.Load():
    sys.exit("Unable to load config file  %s" % (cp.GetConfigFileName()))

  os.system("killall -9 concentrator")
  if os.system(". %s; cd %s/enterprise/legacy/scripts; "
               "./serve_service.py %s restart --components=-config_manager" % (
      cp.var("BASHRC_FILE"),
      cp.var("MAIN_GOOGLE3_DIR"),
      cp.var("ENTERPRISE_HOME")
    )):
    sys.exit("Error executing serve_service")

if __name__ == '__main__':
  main(sys.argv)

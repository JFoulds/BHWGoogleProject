#!/usr/bin/python2.4
#(c) 2002 Google inc
# cpopescu@google.com
#
# Restarts/kills a server that runs on a porton a machine using a specified
# config file (implements server_requests.RestartServerRequest)
#

import sys

from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.util import E

true  = 1
false = 0
FLAGS = flags.FLAGS

flags.DEFINE_string("config_file", "", "The configuration file")
flags.DEFINE_string("machine", "", "The machine where the server runs")
flags.DEFINE_integer("port", None, "The port for the server", lower_bound=0)
flags.DEFINE_boolean("useinvalidconfig", false,
                     "Is it ok for the babysitter to use invalid config")
flags.DEFINE_boolean("kill_only", false,
                     "Dont restart, just kill")
flags.DEFINE_boolean("use_python2", false,
                     "use python2 to invoke babysitter")

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if not FLAGS.machine: sys.exit("Must specify a machine")
  if not FLAGS.port:    sys.exit("Must specify a port")
  if not FLAGS.config_file: sys.exit("Config file must be specified")

  cp = config_factory.ConfigFactory().CreateConfig(FLAGS.config_file)

  if not cp.Load():
    sys.exit("Unable to load config file  %s" % (cp.GetConfigFileName()))

  use_invalid_config = ""
  if FLAGS.useinvalidconfig:
    use_invalid_config = "--useinvalidconfig"

  python2_invoke_string = ""
  if FLAGS.use_python2:
    # we want to invoke using python2
    python2_invoke_string = "python2 "

  action = "--start=all"
  if FLAGS.kill_only:
    # we only want to kill and not restart
    action = "--kill=all"

  cmd = ('. %s; cd %s/enterprise/legacy/production/babysitter; '
         ' %s./babysitter.py --batch %s %s --ports=%s --babyalias=localhost '
         '--lockdir=%s/tmp --mailto= --mach=%s %s' % (
            cp.var("BASHRC_FILE"),
            cp.var("MAIN_GOOGLE3_DIR"),
            python2_invoke_string,
            action,
            use_invalid_config,
            FLAGS.port,
            cp.var("ENTERPRISE_HOME"),
            FLAGS.machine,
            cp.GetConfigFileName()
        ))
  logging.info("Executing [%s]" % cmd)
  if E.ERR_OK != E.execute([E.getCrtHostName()], cmd, None, true):
    sys.exit("Error restarting server at %s:%s" % (FLAGS.machine, FLAGS.port))

if __name__ == '__main__':
  main(sys.argv)

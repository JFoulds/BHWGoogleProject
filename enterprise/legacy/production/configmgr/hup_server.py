#!/usr/bin/python2.4
#(c) 2002 Google inc
# cpopescu@google.com
#
# Hups a server on a machine:port -- functiality of
# server_requests.py.HupServerRequest
#

import sys
from google3.pyglib import flags
from google3.enterprise.legacy.setup import prodlib

FLAGS = flags.FLAGS

flags.DEFINE_string("machine", "", "The machine where the server runs")
flags.DEFINE_integer("port", None, "The port for the server", lower_bound=0)

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if not FLAGS.machine: sys.exit("Must specify a machine")
  if not FLAGS.port:    sys.exit("Must specify a port")

  cmd = "kill -HUP `/usr/sbin/lsof -i :%s -t`" % FLAGS.port
  prodlib.RunAlarmRemoteCmdOrDie(FLAGS.machine, cmd, 120)

if __name__ == '__main__':
  main(sys.argv)

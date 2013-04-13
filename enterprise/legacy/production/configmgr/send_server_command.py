#!/usr/bin/python2.4
#(c) 2002 Google inc
# cpopescu@google.com
#
# Sends a specified command to a server on a port
#

import sys
import string

from google3.pyglib import flags
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.production.configmgr import server_requests
from google3.enterprise.legacy.util import port_talker
from google3.enterprise.legacy.production.babysitter import servertype

true  = 1
false = 0
FLAGS = flags.FLAGS

flags.DEFINE_string("config_file", "", "The configuration file")
flags.DEFINE_string("machine", "", "The machine where the server runs")
flags.DEFINE_integer("port", None, "The port for the server", lower_bound=0)
flags.DEFINE_string("cmd", "", "The command to send to the server")
flags.DEFINE_string("expected_answer", "\nACKgoogle", "What we expect to get from the server in the case of succsee")
flags.DEFINE_integer("no_extra_req", None, "Do not write subsequent "\
                     "config manager requests (good for testing")

def execute(flag_config_file, flag_machine, flag_port,
            flag_cmd, flag_expected_answer,
            flag_no_extra_req):
  """
  Provides the actual execution. Receives the flag values.
  All returns are OK, errors are on sys.exit

  """
  #
  # If the request does not specify the machine or port we create
  # a number of subsequent send server command requests for each machine:port
  # in the server map that matches the server type
  #
  if not (flag_machine and flag_port):
    sys.exit("Invalid parameters: port and machine must be specified")

  #
  # We have machine & port -> issue the command
  #
  status, ret = port_talker.TCPTalk(flag_machine, flag_port, 15, flag_cmd)
  if status or string.find(ret, flag_expected_answer) == -1:
    sys.exit("Error sending command %s to server %s:%s" % (
      flag_cmd, flag_machine, flag_port))
  return 0

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if not FLAGS.config_file: sys.exit("Flag config_file must be specified")

  return execute(FLAGS.config_file, FLAGS.machine, FLAGS.port,
                 FLAGS.cmd, FLAGS.expected_answer,
                 FLAGS.no_extra_req)

if __name__ == '__main__':
  main(sys.argv)

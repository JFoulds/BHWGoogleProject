#!/usr/bin/python2.4
# (c) 2002 Google inc
# cpopescu@google.com
#
# This contains the code to create multiple request of the seame kind but
# differentaited on machines based of servertype flag
#
import sys

from google3.pyglib import flags
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.configmgr import autorunner

FLAGS = flags.FLAGS

flags.DEFINE_string("config_file", "", "The configuration file")
flags.DEFINE_string("data", "", "The repr for data of subsequent requests")
flags.DEFINE_string("servertype", "", "Generate reuqests for this type")
flags.DEFINE_string("machineparam", "", "The machine parameter for requests")
flags.DEFINE_string("portparam", "", "The port parameter for requests")
flags.DEFINE_integer("no_extra_req", None, "Do not write subsequent "\
                     "config manager requests (good for testing")


def execute(flag_config_file, flag_data, flag_servertype,
            flag_machineparam, flag_portparam, flag_no_extra_req):

  if not flag_servertype: sys.exit("Must specify a servertype")
  if not flag_machineparam: sys.exit("Invalid machine param")
  if not flag_portparam: sys.exit("Invalid port param")
  data = None
  try:
    exec("data = %s" % flag_data)
  except:
    sys.exit("data param cannot be interpreted")

  if type(data) != type({}): sys.exit("Invalid data param %s" % data)

  cp = config_factory.ConfigFactory().CreateConfig(flag_config_file)
  if not cp.Load():
    sys.exit("Unable to load config file  %s" % (cp.GetConfigFileName()))

  ret = []
  servers = cp.GetServerMap(servertype.CollectTypes(flag_servertype, {}))
  for port, machines in servers.items():
    for m in machines:
      # Compose the request with data
      req = autorunner.Request()
      req.SetData(data)
      req.SetValue(flag_machineparam, m)
      req.SetValue(flag_portparam, port)
      ret.append(req)
      if not flag_no_extra_req and not cp.WriteConfigManagerRequest(req):
        sys.exit("Error savig request")

  cp.DistributeAll()

  return ret

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  return execute(FLAGS.config_file, FLAGS.data, FLAGS.servertype,
                 FLAGS.machineparam, FLAGS.portparam, FLAGS.no_extra_req)

if __name__ == '__main__':
  main(sys.argv)

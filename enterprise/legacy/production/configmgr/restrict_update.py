#!/usr/bin/python2.4
#
# (c) 2002 Google inc
# cpopescu@google.com
#
# This contains the code to update a restrict
# NOTE: for now this works only for enteprise. In order to work for
# Inplement GetRestrictParam/SetRestrict/DeleteRestrict in
# Config class. Now it is only in EntConfig
#

import sys

from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.legacy.production.configmgr import server_requests
from google3.enterprise.legacy.production.babysitter import validatorlib

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.production.configmgr import configmgr_request

FLAGS = flags.FLAGS

flags.DEFINE_string("enthome", "", "The enterprise home")
flags.DEFINE_string("restrict", "", "The name of the restrict")
flags.DEFINE_string("value", "", "The repr() value of the parameter")
flags.DEFINE_string("op", "", "add/del restrict")
flags.DEFINE_integer("force", 0, "force the update")
flags.DEFINE_integer("no_extra_req", None, "Do not write subsequent "\
                     "config manager requests (good for testing")

true = 1
false = 0

def execute(flag_enthome, flag_restrict, flag_value,
            flag_op, flag_force, flag_no_extra_req):

  if not flag_restrict: sys.exit("Must specify a paramter")
  if not flag_enthome: sys.exit("Config file must be specified")
  if not flag_op or not flag_op in ("add", "del"):
    sys.exit("Invalid value")

  value = None
  try:
    exec("value = %s" % flag_value)
  except:
    sys.exit("Invalid value %s" % flag_value)

  cp = entconfig.EntConfig(flag_enthome)
  if not cp.Load():
    sys.exit("Unable to load config file  %s" % (cp.GetConfigFileName()))

  do_update = true
  if not flag_force:
    try:
      oldval = open(cp.GetRestrictParam(flag_restrict), "r").read()
      do_update = oldval != value
    except IOError:
      pass  # we update

  if not do_update:
    logging.info("New value for restrict  [%s] unchanged." % flag_restrict)
    return (1, None)

  # Perform the actual request. On error we return
  rt_op = None
  if flag_op == "del":
    rt_op = 1
    cp.DeleteRestrict(flag_restrict)
  elif flag_op == "add":
    rt_op = 0
    err = cp.SetRestrict(flag_restrict, value)
    if err not in validatorlib.VALID_CODES:
      logging.error("New value for file restrict [%s] did "\
                    "not validate correctly [%s]" % (flag_restrict, err))
      return (2, None)
  else:
    sys.exit("Invalid restrict operation %s" % flag_op)
  # Distribute config file
  cp.DistributeAll()

  # Register requests per machine

  # Prepare adummy request to send server command
  req = server_requests.SendServerCommandRequest()
  req.Set("dummy", 1,
          "GET /update?RestrictUpdate=b&IsDeleteOrAddRestrict=%s&RestrictFileName=%s&RestrictUpdate=e HTTP/1.0\r\n\r\n" % (
    rt_op, cp.GetRestrictParam(flag_restrict)),
          "HTTP/1.0 200 OK",
          cp.GetConfigFileName())

  # The actual request that registers req for each machine:port in base_indexer
  the_req = configmgr_request.MultiRequestCreateRequest()
  the_req.Set(req.datadict, "base_indexer",
              server_requests.MACHINE, server_requests.PORT,
              cp.GetConfigFileName())

  if not flag_no_extra_req and not cp.WriteConfigManagerRequest(the_req):
    sys.exit("Cannot save subsequent request to update param on machine")
  cp.DistributeAll()

  return (0, the_req)

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  return execute(FLAGS.enthome, FLAGS.restrict, FLAGS.value,
                 FLAGS.op, FLAGS.force, FLAGS.no_extra_req)

if __name__ == '__main__':
  main(sys.argv)

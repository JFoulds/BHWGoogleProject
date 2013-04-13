#!/usr/bin/python2.4
# (c) 2002 Google inc
# cpopescu@google.com
#
# This contains the code to update a configuration parameter
#

import sys

from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.legacy.production.configmgr import update_consts
from google3.enterprise.legacy.production.configmgr import update_requests
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.production.configmgr import configmgr_request
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.production.babysitter import googleconfig

FLAGS = flags.FLAGS

flags.DEFINE_string("config_file", "", "The configuration file")
flags.DEFINE_string("param", "", "The paramter we want to update")
flags.DEFINE_string("value", "", "The repr() value of the parameter")
flags.DEFINE_string("op", None,
                    "Which operation we're performing: set_var, set_file_var_content, del_var, del_file_var_content")
flags.DEFINE_integer("force", None, "Force the update even when the new"\
                     " value is not different from the old one")
flags.DEFINE_boolean("force_no_validate", False,
                     "Force the update without validation - a bad idea in "
                     "general but sometimes necessary")
flags.DEFINE_integer("no_extra_req", None, "Do not write subsequent "\
                     "config manager requests (good for testing")

true = 1
false = 0

# GetChangedParams takes a parameter name and value, and compares it with
# the value stored in config to see if it has changed.
# If value is a map it will return _all_ changed submaps.
# It returns a list of (name, value) pairs; tuple var names will be used
# to name submaps.
def GetChangedParams(name, value, config, force):
  results = []

  # only consider this value if it is different than config.var(); otherwise
  # we don't want this node, and there is no need to recurse
  if (force or not config.has_var(name) or config.var(name) != value):
    results.append( (name, value) )

    # if this is a map, recurse into it.
    if type(value) == type({}):
      base_var_path = googleconfig.makeTupleName(name)
      for key in value.keys():
        inner_name = base_var_path + (key,)
        inner_value = value[key]
        results.extend( GetChangedParams(inner_name, inner_value,
                                         config, force) )

  return results

def execute(flag_config_file, flag_param, flag_value, flag_op,
            flag_force, flag_force_no_validate, flag_no_extra_req):
  """
  Performs the actual operation. Params correponding to the flags
  Error is signalled on sys.exit.
  All return codes are OK and are different to be used by the unittest.
  The return is (exitcode, written_requests)
  """
  if not flag_param: sys.exit("Must specify a paramter")

  # if the param name starts with a (, it's a tuple
  if flag_param[0] == '(':
    param = eval(flag_param, {}, {})
  else:
    param = flag_param

  value = None
  try:
    value = eval(flag_value, {}, {})
  except:
    sys.exit("Invalid value %s" % flag_value)

  cp = config_factory.ConfigFactory().CreateConfig(flag_config_file)

  if not cp.Load():
    sys.exit("Unable to load config file  %s" % (cp.GetConfigFileName()))

  # STEP 1.
  # First we get a list of changed params, which we will use later to take
  # care of restarting servers, etc..  We have to do it before we actually
  # set the value so we can see if the value changed.
  if flag_op == 'set_var':
    # a normal parameter; use GetChangedParams() to recurse any maps and return
    # all changed submaps.
    param_change_list = GetChangedParams(param, value, cp, flag_force)
  elif flag_op == 'set_file_var_content':
    # file content; just this parameter changed
    param_change_list = [(param, value)]
  else:
    # we don't do side effects for del_var, del_file_var_content
    param_change_list = []

  # STEP 2.
  # Next we do as we were asked and set the parameter.  We treat setting
  # file content specially.
  if flag_op == 'set_var':
    # If we don't force, don't update params that did not change
    if not flag_force and cp.has_var(param) and cp.var(param) == value:
      logging.info("New value for parameter [%s] unchanged." % (param,))
      return (1, None)

    if ( not cp.set_var(param, value,
                        not flag_force_no_validate) in
         validatorlib.VALID_CODES ):
      logging.info(
        "New value for parameter [%s] did not validate correctly" %
        (param,))
      return (2, None)
    if not cp.Save(cp.GetConfigFileName()):
      sys.exit("Params saving failed")

  elif flag_op == 'del_var':

    cp.del_var(param)
    if not cp.Save(cp.GetConfigFileName()):
      sys.exit("Params saving failed")

  elif flag_op == 'del_file_var_content':

    cp.del_file_var_content(param)

  elif flag_op == 'set_file_var_content':
    try:
      value_to_set = open(value, "r").read()
    except IOError, e:
      sys.exit("Cannot open the file provided as value %s [%s]" % (
        value, e))
    do_update = true
    if not flag_force:
      try:
        oldval = open(cp.var(param), "r").read()
        do_update = oldval != value_to_set
      except IOError:
        pass  # we update
    if not do_update:
      logging.info("New value for file parameter [%s] unchanged." % (param,))
      return (3, None)

    if ( not cp.set_file_var_content(param, value_to_set,
                                     not flag_force_no_validate) in
         validatorlib.VALID_CODES ):
      logging.info(
        "New value for file parameter [%s] did not validate correctly" %
        (param,))
      return (4, None)

  # Distribute files
  cp.DistributeAll()

  return (0, [])


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  return execute(FLAGS.config_file, FLAGS.param, FLAGS.value, FLAGS.op,
                 FLAGS.force, FLAGS.force_no_validate, FLAGS.no_extra_req)

if __name__ == '__main__':
  main(sys.argv)

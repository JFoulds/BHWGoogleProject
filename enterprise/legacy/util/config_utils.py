#!/usr/bin/python2.4
#

import re
import string
import types

# utility function to check if a value has a simple, acceptable type
def has_valid_type(arg):
  arg_type = type(arg)

  # make sure the value has an "acceptable" type
  if arg_type in (types.ListType, types.TupleType):
    # for lists and tuples, recursivly check all elements have valid types
    for value in arg:
      if not has_valid_type(value):
        return 0
  elif arg_type in (types.DictType,):
    # for map, recursivly check that all keys and values have valid types
    for key,value in arg.items():
      if not has_valid_type(key) or not has_valid_type(value):
        return 0
  elif arg_type not in (types.IntType, types.FloatType, types.LongType,
                        types.StringType, types.NoneType):
    return 0
  return 1

# This will parse a single parameter of the forn "VAR = value" and the param
# name and value in a tuple.  It does this safely without executing random
# code in the file, which is useful for untrusted config files.  The parameter
# must be a known simple type (list, tuple, dict, int, float, string, or None).
# If the line is invalid, None is returned.
def SafeParseParam(line):
  try:
    lvalue,rvalue = string.split(line, '=', 1)

    var_name = string.rstrip(lvalue)
    assert len(var_name) > 0

    # convert the argument into a python value using eval.
    # this should be safe since eval only allows expressions.  we also pass in
    # a dummy environment so that ours isn't accessible.
    dummy = {}
    # rvalue may have '\r', and it's causing problem.
    value = eval(string.strip(rvalue), dummy, dummy)

    # make sure we're dealing with a simple type.  it is dangerous to
    # deal with more complex types (such as lambda or built in functions)
    assert(has_valid_type(value))

    return (var_name, value)
  except:
    pass

  return None


# This safely reads in a string of parameters.  It ignores blank lines and
# comments and parses all others with SafeParseParam.  It will fill in dict
# with parsed params and throw an expection on any errors.
def SafeExec(str, dict):
  lines = string.split(str, '\n')
  for line in lines:
    SafeExecLine(line, dict)

# This safely reads in a parameter of files.  It ignores blank lines and
# comments and parses all others with SafeParseParam.  It will fill in dict
# with parsed params and throw an expection on any errors.
def SafeExecFile(filename, dict):
  file = open(filename, 'r')
  while 1:
    line = file.readline()
    if len(line) == 0:
      break

    SafeExecLine(line, dict)

  file.close()
  return

def SafeExecLine(line, dict):
  # skip comments and empty lines
  if re.match('^(#.*|\s*)$', line):
    return

  param = SafeParseParam(line)
  if param == None:
    raise Exception("Parse Error: " + line)

  var_name,value = param
  dict[var_name] = value

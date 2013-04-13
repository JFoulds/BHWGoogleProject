# Copyright 2005 Google Inc.
# All Rights Reserved.
#
# Author: Rich Washington
#

"""
Miscellaneous useful functions.
"""

def update_new(d1, d2):
  """
  update_new(d1, d2)

  Updates dict d1 with elements of dict d2, but only adds those elements whose
  keys are not already in d1.
  """
  for (key, value) in d2.items():
    if not d1.has_key(key):
      d1[key] = value

def update_old(d1, d2):
  """
  update_old(d1, d2)

  Updates dict d1 with elements of dict d2, but only modifies those elements
  whose keys are already in d1.
  """
  for (key, value) in d2.items():
    if d1.has_key(key):
      d1[key] = value

def SafeEval(s):
  """Evaluate expression s, without allowing side effect.

  Like the eval builtin, but raises ValueError if string s contains any names
  at all (this ensures the eval can have no side effects, i.e., it's "safe").
  Note that SafeEval does NOT accept local and global dictionaries, even as
  optional arguments: such dicts are used to look names up, and SafeEval does
  NOT accept names within s, therefore such dicts would serve no purpose.

  Args:
    s: a string which is a valid Python expression without names
  Returns:
    the value of the expression (or, raises appropriate exceptions: SyntaxError
    if s has invalid syntax, ValueError if s contains names, or any other
    exception raised by the underlying compile and eval builtins).
  """
  c = compile(s, '<str>', 'eval')
  if c.co_names:
    raise ValueError, 'Names %s not allowed' % (c.co_names,)
  return eval(c)

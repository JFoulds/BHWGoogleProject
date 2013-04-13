# Copyright 2003, Google Inc.
# Author: Douglas Greiman
#
# Formats a human-readable stack trace that includes the values of
# local variables for each stack frame.  Useful for log files and
# other places where a bare traceback is inadequate.
#
# Usage:
#   from google3.pyglib import debug_traceback
#   try:
#     ...
#   except FooException:
#     debug_traceback.print_exc()
#
# For interactive sessions, do:
#   import sys
#   sys.excepthook = debug_traceback.print_exception
#
# TODO(dgreiman): Actually pickle the state of the program into the
# equivalent of a core dump so that one could examine the values of
# variables in the Python debugger.
#
# TODO(dgreiman): Replace or fix pprint so that class instances
# (e.g. self) are handled intelligently.
#
# TODO(dgreiman): Limit output for large structures.


# System modules
import pprint
import sys
import traceback


def print_exc(limit=None, file=None):
  """As traceback.print_exc, but include local variable information."""
  
  try:
    etype, value, tb = sys.exc_info()
    print_exception(etype, value, tb, limit, file)
  finally:
    etype = value = tb = None
  # endtry
# enddef


def print_exception(etype, value, tb, limit=None, file=None):
  """As traceback.print_exception, but include local variable information."""
  
  if not file:
    file = sys.stderr
  # endif

  lines = format_exception(etype, value, tb, limit)
  for line in lines:
    traceback._print(file, line, '')
# enddef


def format_exception(etype, value, tb, limit = None):
  """As traceback.format_exception, but include local variable information."""
  
  if tb:
    lst = ['Traceback (most recent call last):\n']
    lst = lst + format_tb(tb, limit)
  else:
    lst = []
  lst = lst + traceback.format_exception_only(etype, value)
  return lst
# enddef


def format_tb(outer_tb, limit = None):
  """As traceback.format_tb, but include local variable information."""

  # Use system defined traceback limit
  if limit is None:
    if hasattr(sys, 'tracebacklimit'):
      limit = sys.tracebacklimit
    else:
      limit = 100
    # endif
  # endif
  
  # Iterate over frames, outer to inner
  lines = []
  tb = outer_tb
  n = 0
  while tb is not None and (limit is None or n < limit):
    # Format tb in standard Python traceback format
    # Result is a string like
    # '  File "debug_traceback.py", line 26, in foo\n    q=bar(b)\n'
    line = traceback.format_tb(tb, 1)[0] # Contains trailing \n

    # Now format locals.
    local_vars = tb.tb_frame.f_locals
    line = line + format_locals(local_vars) + '\n'

    lines.append(line)

    # Next tb
    tb = tb.tb_next
    n = n + 1
  # endfor

  return lines
# enddef


def format_locals(local_vars):
  """Format a dictionary of local variables into a human readable string."""
  
  lines = []
  names = local_vars.keys()
  names.sort()
  for name in names:
    # The outermost stack frame includes all the global variables in
    # the module.  Some add little information, so we ignore them.
    if name in ['__doc__', '__builtins__']:
      continue
    
    value = local_vars[name]
    lines.append('      %s = %s' % (name, pprint.pformat(value)))
  # endfor

  return '\n'.join(lines)
# enddef

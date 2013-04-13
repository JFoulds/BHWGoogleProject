# Copyright 2006 Google Inc.
# All Rights Reserved.

"""par files are Google's way of packaging up Python programs as self-contained
   binaries. This module provides basic reflection about the par nature
   of a Python script.
"""

__author__ = 'johannes@google.com (Johannes Henkel)'

# For maximum PAR file happiness, we don't want this module to import
# other Google code.
import sys

def RunningProgramIsAParFile():
  """Returns whether or not sys.argv[0] (the running program) is a par
     file.
  """
  loader = globals().get('__loader__', None)
  if not loader or not hasattr(loader, '__module__'):
    return 0
  # endif
  module = sys.modules[loader.__module__]
  return hasattr(module, 'AUTOPAR_VERSION')
# enddef

# TODO(johannes):
#     add methods that answer things like 'when was the par built?' etc.

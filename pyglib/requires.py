#
# Original Author: Daniel Dulitz
#
# Copyright 2002, Google
#

"""
Raises an exception if the Python interpreter is earlier than a specified
version.  Use this at module load time.
"""

from __future__ import nested_scopes

import sys as _sys
import types as _types
import os.path as _ospath
import imp as _imp

class Error(Exception):
  def __init__(self, s):
    Exception.__init__(self, s)
  # end def
# end class

try:
  _have = _sys.version_info[:3]
except AttributeError:
  _have = (0, 0, 0) # older than _required, probably :-)
# end try

def UniqueImports():
  """
  Raises Error if any module is imported under two different names
  (e.g. "flags" and "google.pyglib.flags").
  """

  modules = {}
  for (name, module) in _sys.modules.items():
    # jython only partially supports many basic modules like sys, os, etc. the
    # hasattr check allows scripts run through the jython interpreter to still
    # import pyglib modules.
    if not module or not hasattr(module, '__file__'):
      continue
    # end if
    # In Python 2.2, sys.modules['__main__'], the main script, had no
    # __file__ attribute, and so it was skipped by the above check. To
    # make the same thing happens in 2.4, explicitly skip that module. 
    # It is unclear if this 'feature' is actually relied on anywhere,
    # but the unittest for this module does require it.
    if getattr(module, '__name__', None) == '__main__':
      continue
    # end if
    try:
      # path could be absolute or relative, so canonicalize to absolute.
      modulefile = _ospath.abspath(module.__file__)
      # extension could be .py, .pyc, or .pyo, so ignore it.
      modulefile = _ospath.splitext(modulefile)[0] + ".py"
      # could be as symlink or have symlinks in the path
      if hasattr(_ospath, 'realpath'):
        modulefile = _ospath.realpath(modulefile)

      existing_name, existing_module = modules.get(modulefile, (None, None))
      if existing_module and existing_module is not module:
        raise Error("module %s was imported as %s and %s" %
                    (module.__file__, existing_name, name))
      # end if
      modules[modulefile] = (name, module)
    except AttributeError:
      pass # built-in module -- multiple load okay
    # end except
  # end for
  return
# end def

def _RequireVersion(required_version):
  for index in range(3):
    if required_version[index] > _have[index]:
      raise Error("requires python %d.%d.%d or later" % required_version)
    elif required_version[index] < _have[index]:
      break # no need to check further
    # end if
  # end for
  # if we survived that, we're okay
  return

def Python21():
  return _RequireVersion((2, 1, 1))

def Python22():
  return _RequireVersion((2, 2, 0))

def Python221():
  return _RequireVersion((2, 2, 1))

def Python23():
  return _RequireVersion((2, 3, 0))

def Python234():
  return _RequireVersion((2, 3, 4))

def Python235():
  return _RequireVersion((2, 3, 5))

def Python24():
  return _RequireVersion((2, 4, 0))

def Python241():
  return _RequireVersion((2, 4, 1))

def _RequireType(value, required_type):
  if not isinstance(value, required_type):
    raise TypeError('required %s; got %s' %
                    (repr(required_type), repr(value)))
  return

def _RequireOneOfTypes(value, required_type1, required_type2):
  if (not isinstance(value, required_type1) and
      not isinstance(value, required_type2)):
    raise TypeError('required %s or %s; got %s' %
                    (repr(required_type1), repr(required_type2), repr(value)))
  return

def Int(value):
  return _RequireType(value, _types.IntType)

def Long(value):
  return _RequireType(value, _types.LongType)

def Float(value):
  return _RequireType(value, _types.FloatType)

def Complex(value):
  return _RequireType(value, _types.ComplexType)

def Dict(value):
  return _RequireType(value, _types.DictType)

def File(value):
  return _RequireType(value, _types.FileType)

def List(value):
  return _RequireType(value, _types.ListType)

def Tuple(value):
  return _RequireType(value, _types.TupleType)

def String(value):
  return _RequireType(value, _types.StringType)

def Unicode(value):
  return _RequireType(value, _types.UnicodeType)

def Listlike(value):
  return _RequireOneOfTypes(value, _types.ListType, _types.TupleType)

def Stringlike(value):
  return _RequireOneOfTypes(value, _types.StringType, _types.UnicodeType)

def Function(value):
  return _RequireOneOfTypes(value, _types.FunctionType,
                            _types.BuiltinFunctionType)

def Type(cls, value):
  return _RequireType(value, cls)

def Sequence(value):
  if (not isinstance(value, _types.ListType) and
      not isinstance(value, _types.TupleType) and
      not isinstance(value, _types.StringType) and
      not isinstance(value, _types.UnicodeType)):
    raise TypeError('required sequence type; got %s' % repr(value))
  return

def Importable(module_path):
    """
    Return 1 if MODULE_PATH is importable; 0 otherwise.  Imports of all
    but the final path component are attempted to ascertain this.

    This is especially useful if you want to see if a module is
    importable without masking problems with modules *it* imports by
    catching ImportError.
    """

    components = module_path.split('.')

    assert len(components) > 0

    if len(components) == 1:
      try:
          filename, path, desc = _imp.find_module(components[0])
      except ImportError:
          return 0
      return 1
    else:
      # Try to get the first component (no path argument to find_module()).
      try:
        file, path, desc = _imp.find_module(components[0])
        mod = _imp.load_module(components[0], file, path, desc)
      except ImportError:
        return 0
      modpath = components[0]
      # Try to find the intermediate components.
      for sub in components[1:-1]:
        modpath += '.' + sub
        try:
          file, path, desc = _imp.find_module(sub, mod.__path__)
          mod = _imp.load_module(modpath, file, path, desc)
        except ImportError:
          return 0
      sub = components[-1]
      modpath += '.' + sub
      # Try to find the final component.
      try:
        filename, path, desc = _imp.find_module(sub, mod.__path__)
      except ImportError:
        return 0
      return 1

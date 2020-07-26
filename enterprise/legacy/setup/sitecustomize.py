#!/usr/bin/python2.4
#
# Google module for solving the import problem. sitecustomize.py is a
# standard module name that is imported automatically by Python during
# the initialization phase if this module exists (and is readable) in
# one of the directories directly accessible by Python (ie. either one
# of the standard dirs or one listed inside $PYTHONPATH).
#
# This allows us to configure the path import order and location for
# all Google python modules.
#
# We assume that all module directories are mirroring the P4 setup
# both at corp and on production machines and all paths are relative
# to a certain base directory which we try to auto-detect. User can
# override this decision by setting GOOGLEBASE to whatever base
# directory they want (normally, the parent directory of google and
# google2 subtrees). Ex.: ~user/src/ (if source code lives in
# ~user/src/{google,google2})
#
# In the production environment, this file uses several hardcoded
# rules to find GOOGLEBASE at one of a few known locations.
#
# In the corp environment, more elaborate rules are used, and
# GOOGLEBASE is not limited to a hardcoded list of directories.
# Instead, we autodetect GOOGLEBASE based on the location of the
# __main__ Python source file. If this source file is located in a
# directory tree that look like a Google source tree, we use the root
# of the tree as GOOGLEBASE.  For example, if we invoke
# /home/dgreiman/src2/google2/regressiontest/unittest/run_unittests.py,
# GOOGLEBASE is set to /home/dgreiman/src2.
#
# Since we expect users to regularly run non-Google Python scripts at
# corp, if the __main__ Python source file is not inside a Google
# source tree, we silently do nothing.
#
# WARNING: This module is very central to our Python importing mechanism!
#          Please don't make any changes to it without checking with
#          each of the major groups using Python. At the very least,
#          production, crawl and enterprise need to be notified.
#
# by Bogdan Cocosel (c) April 2002

import __builtin__ # We may need to replace built-in import function
import os
import sys
import string

# were we executed from a google3 program
_is_google3_program = 0

def SetupPaths():
  global GOOGLEBASE

  # We set PYTHONPATH originally in order to locate this module in the
  # first place. But once GOOGLEBASE is set, we know better and
  # PYTHONPATH gets in the way because they are already inserted *ahead*
  # of our own entries. So ... we remove all PYTHONPATH entries first,
  # and add them back at the end of the list after all GOOGLEBASE
  # entries are in to preserve the normal behavior for whatever dirs
  # that may be in there.
  PYTHONPATH = string.split(os.environ.get('PYTHONPATH', ''), ':')
  for dir in PYTHONPATH:
    # Python2 canonicalizes directories in sys.path, so we do too
    if sys.version[0:2] != "1.":
      dir = os.path.abspath(dir)
    # Python2 doesn't include nonexistent dirs in sys.path
    if dir in sys.path:
      sys.path.remove(dir)

  ### NOTE: the order in which the dirs below are listed is relevant!
  ###       Python will search them in order and will load the module
  ###       from the first directory that has it! Also, the order should
  ###       roughly match the relative frequency of the imports to
  ###       minimize runtime performance penalties.
  if _is_google3_program:
    # google3 program; use a minimal set of paths
    AddPath('%s' % GOOGLEBASE)
  else:
    # Non-google3
    # This could maybe be removed, google3 and non-google3 should be treated
    # the same now. (npelly)

    # path needed for packages to work
    AddPath('%s' % GOOGLEBASE)

    # For pywrapgooglec
    AddPath('%s/google2/bin' % GOOGLEBASE)

    # paths to third party libraries
    AddPath('%s/google2/third-party/yapps2' % GOOGLEBASE)
    AddPath('%s/google2/third-party/DCOracle' % GOOGLEBASE)
    AddPath('%s/google2/third-party' % GOOGLEBASE)

  ### End of Google import directories. Insert all Google dirs above this line!

  # Put PYTHONPATH entries back
  for dir in PYTHONPATH:
    AddPath(dir)
# enddef


# Can't figure out the base directory right now. Replace builtin
# import function with our import. It will setup the path the first
# time a module is imported (at which point we'll have enough
# information to setup the paths correctly).
def LazySetupPaths():
  global real_import
  real_import = __builtin__.__import__
  __builtin__.__import__ = SetupPathsAndImport
# enddef

_config_google_base_called = 0

# Autodetect the root of any google tree we're in and set up sys.path
# appropriately
def ConfigGoogleBase():
  global GOOGLEBASE, _config_google_base_called, _is_google3_program

  # Only run this once.
  if _config_google_base_called:
    return
  else:
    _config_google_base_called = 1

  # What directory contains the source file for the __main__ module?
  # This directory should always be the first entry in sys.path
  if sys.path[0]:
    dir = os.path.abspath(sys.path[0])
  else:
    # Program was started via the -e flag, fallback to current directory
    dir = os.getcwd()

  # Special-case pychecker
  if sys.path[0][-9:] == 'pychecker':
    for arg in sys.argv[1:]:
      if arg[0] != '-' and os.path.exists(arg):
        dir = os.path.abspath(os.path.dirname(arg))
        break

  # Try to find root of p4 tree, without using p4
  found = 0
  while not found and dir != "/":
    # Note if this is a google3 program
    if dir[-len('/google3'):] == '/google3':
      _is_google3_program = 1

    # Does it look like the root of a branch? (makes some assumptions here)
    for pat in ['google/bin', 'google/Makefile',
                'google/setup', 'google/production',
                'google2/Makefile',
                'google3/__init__.py']:
      if os.path.exists(os.path.join(dir, pat)):
        # Found the root of the p4 tree
        found = 1
        GOOGLEBASE = dir
        SetupPaths()
        break
    else:
      # Keep looking
      dir = os.path.dirname(dir)
  else:
    # Not a google program. Silently do nothing
    pass
  # endwhile

# A run-once replacement for builtin import, which calls
# ConfigGoogleBase() at a point when sys.path should be sane.
def SetupPathsAndImport(name, globals=None, locals=None, fromlist=None):
  global real_import

  # Stay hooked and don't config GOOGLEBASE until we have sys.argv.
  if sys.__dict__.has_key('argv'):
    # Replace ourselves with builtin import
    __builtin__.__import__ = real_import

    ConfigGoogleBase()
  # endif

  # Run builtin import
  return real_import(name, globals, locals, fromlist)
# enddef

# Allow a Google module to be used both as a package and not-a-package.
# This should allow us to transition to packages more gradually, instead
# of all-or-nothing.
def SetupPackageAccess(name):
  # Get module from global module list
  module = sys.modules.get(name, None)
  if not module:
    raise ImportError("Module %s not found in sys.modules" % name)

  # Get filename
  if name == '__main__':
    module_file = os.path.abspath(os.path.join(sys.path[0], sys.argv[0]))
  else:
    module_file = getattr(module, '__file__', None)
    if not module_file:
      raise ImportError("Module %s has no __file__ attribute" % name)
    else:
      module_file = os.path.abspath(module_file)
    # endif
  # endif

  # From GOOGLEBASE?
  base_with_slash = GOOGLEBASE + '/'
  if module_file[:len(base_with_slash)] != base_with_slash:
    #raise ImportError("Module %s is not under GOOGLEBASE" % name)
    return

  # Translate filenames to packages
  rel_file = module_file[len(base_with_slash):]
  components = string.split(rel_file, '/')
  if len(components) < 2:
    #raise ImportError("Module %s is not in any package." % name)
    return

  # Map google2 directories to google package
  if components[0] == 'google2':
    components[0] = 'google'

  # Strip file extension
  components[-1] = os.path.splitext(components[-1])[0]

  # Determine canonical long and short module names
  short_name = components[-1]
  long_name = string.join(components, '.')

  # Add short (non-package) shadow entry
  if not sys.modules.has_key(short_name):
    sys.modules[short_name] = module
  elif sys.modules[short_name] is not module:
    raise ImportError("Module %s has already been loaded as %s" %
                      (name, short_name))
  # endif

  # Add long (package) shadow entry
  if not sys.modules.has_key(long_name):
    # Make sure all intermediate packages are accessible
    for i in range(len(components) - 1): # -1 == exclude last dotted comp
      parent_name = string.join(components[0:i+1], '.') # +1 == include i-th
      __builtin__.__import__(parent_name)
    # endfor

    # Add a reference to this module from its parent
    setattr(sys.modules[parent_name], components[-1], module)

    # Add to global module list
    sys.modules[long_name] = module
  elif sys.modules[long_name] is not module:
    raise ImportError("Module %s has already been loaded as %s" %
                       (name, long_name))
  # endif
# enddef

# add the specified path to sys.path only if path exists and it's not
# already in (this mimics site.py's behavior in regard to path additions)
def AddPath(path):
  # Python2 canonicalizes directories in sys.path, so we do too
  if sys.version[0:2] != "1.":
    path = os.path.abspath(path)
  if os.path.exists(path) and \
     path not in sys.path:
    sys.path.append(path)

# detect the base directory
if os.environ.has_key('GOOGLEBASE') and os.environ['GOOGLEBASE']:
  # user wants to override
  GOOGLEBASE = os.path.abspath(os.environ['GOOGLEBASE'])
  SetupPaths()
elif os.path.isdir('/export/hda3/shared'):
  GOOGLEBASE = '/export/hda3/shared'       # base path on crawlmains
  SetupPaths()
elif os.path.isdir('/home/build/public'):
  LazySetupPaths()                         # corp environment
elif os.path.isdir('/root'):
  GOOGLEBASE = '/root'                     # path on production mach
  SetupPaths()
else:
  # if all else fails
  this_dir = os.path.dirname(__file__)
  # "../.." accounts for "google/setup"
  GOOGLEBASE = os.path.abspath(os.path.join(this_dir, "..", ".."))
  sys.stderr.write("\nWARNING: GOOGLEBASE detection failed! Using %s.\n\n" % \
                   GOOGLEBASE)
  SetupPaths()

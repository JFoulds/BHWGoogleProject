# Copyright 2005 Google Inc.
# All Rights Reserved.
#
# Original Author: Mark D. Roth
#

"""
swig_flags.py - a library for better integration of python and C++ flags

This library allows a google python app to accept all the flags necessary
for the underlying C++ code.  When the library is imported, it will
automatically define a python flag for each flag accepted by the C++ code.
Once the python flag library parses the command line arguments (which
is usually triggered by calling app.start()), the application can call
Init() to propogate the flag values down into the C++ code.

Note: Init() will call InitGoogleScript() for you.  There is no need to
call InitGoogleScript() yourself if you are using this library.

Note: The C++ layer has functionality for getting and storing 'argv'
(in base/commandline).  Prior to December 2007, calling Init() caused
the swig flags to be put into this argv mechanism.  The current
behavior is that Init() puts the original commandline passed to python
into the argv mechanism.  If, for some reason, you want the older
behavior, be sure to call swig_flags.SetupSwigFlags() BEFORE calling
app.run().

TODO:

* need a way to dynamically reflect flag changes back and forth
  (i.e., if you set FLAGS.foo in python, the change should be reflected
  in the C++ code - this will probably require some changes to the C++
  flag library)

* come up with a better way of handling the flag mapping besides hard-coding
  them in this file, especially if we add more flags in the future (better,
  though, is to keep them from getting out of sync in the first place!)

"""

import sys

from google3.pyglib import flags
from google3.base import pywrapbase


FLAGS = flags.FLAGS

# maps C++ flag types to python flag types
_DEFAULT_TYPE_MAP = {
  'bool':   'boolean',
  'int32':  'integer',
  'int64':  'integer',
  'uint64': 'integer',
  'double': 'float',
  'string': 'string',
}

# Define a python flag for each C++ flag that does not already have a
# python flag object.  This happens as soon as the swig_flags module is
# imported.
def _SetupCppFlags():
  global _flag_list
  _flag_list = pywrapbase.GetAllFlags()
  for flag_name, flag_type, flag_description, flag_default in _flag_list:
    if not hasattr(FLAGS, flag_name):
      # this is a bit of a hack, but we don't want to have to change this
      # if the python flags library changes
      define_method = 'DEFINE_' + _DEFAULT_TYPE_MAP[flag_type]

      getattr(flags, define_method)(flag_name, flag_default,
                                    '[C++] ' + flag_description)

try:
  _SetupCppFlags()
except:
  # Only raise an exception if pychecker is not running.
  if 'pychecker.python' not in sys.modules:
    raise

def TranslateFlag(flag_name, flag_value, flag_type):
  """Given a name and value of a flag, return a new (name, value)
  that correspond to an appropriate C++ flag.

  Currently, this only changes 'stderrthreshold' from the Python
  string value to the numeric C++, and the 'verbosity' flag in
  Python to the 'v' flag in C++.
  """

  if flag_name == 'stderrthreshold':
    # ugly hard-coded list, but this isn't available elsewhere
    cpp_level_dict = { 'INFO' : '0', 'WARNING' : '1',
                       'ERROR' : '2', 'FATAL' : '3' }

    # if we were passed in a positive int encoded as a string, we should turn
    # it into one of the levels listed above.
    if flag_value in cpp_level_dict.values():
      flag_value = int(flag_value)
    elif cpp_level_dict.has_key(flag_value.upper()):
      flag_value = int(cpp_level_dict[flag_value.upper()])
    else:
      raise flags.IllegalFlagValue, '--stderrthreshold must be one of ' + \
            'info, warning, error, or fatal, or 0-3 not %s' % \
            flag_value
  elif flag_name == 'verbosity':
    flag_name = 'v'

  # We turn None into empty strings or 0, depending on the underlying
  # C++ type.  There is no way for the python concept of None to
  # really be passed into a string and then into the C++ layer, so we
  # make a decision that if somehow a flag is None at this point, then
  # we want to put a default value on the SWIG command line.  We can't
  # just omit it from the C++ command line as the C++ code may have
  # inappropriate defaults that otherwise would be used.
  if flag_value is None:
    if flag_type == 'string':
      flag_value = ""
    else:
      flag_value = 0
  return flag_name, flag_value

def _GenerateArgsForSwigFlags():
  """Generates the commandline arguments to set all of the non-default swig
  flags, which can be passed to InitGoogle or ParseCommandLineFlags to set up
  the C++ side of the swig flags.

  Returns:
    a command-line arg list to set up the swig flags
    Generally of the form: [sys.argv[0], '--flag1=value1', '--flag2=value2']
  """
  cpp_args = [ sys.argv[0] ]
  for flag_name, flag_type, flag_description, flag_default in _flag_list:
    (cpp_flag_name, cpp_flag_value) = \
                    TranslateFlag(flag_name,
                                  getattr(FLAGS, flag_name),
                                  flag_type)

    # sometimes, flag_default is the string 'true' or 'false'; we
    # must normalize to integers in these cases for compatibility with
    # the C++ defaults
    if flag_default == 'true':
      flag_default = 1
    elif flag_default == 'false':
      flag_default = 0

    if str(cpp_flag_value) != str(flag_default):
      cpp_args.append('--%s=%s' % (cpp_flag_name, cpp_flag_value))
  return cpp_args

def Init():
  """Initialize the Google C++-layer and set up swig flags.

  Initializes the C++ layer by first setting up the GetArgv() portion
  of commandlineflags to return the original command line flags given
  to the program, then pass any swig specific to InitGoogleScript().

  Must be called by applications that have not already initialized
  these layers on their own.

  Note: This will call InitGoogleScript() for you.  There is no need
  to call InitGoogleScript() yourself if you are using this method.

  Note: If you do not want C++'s GetArgv() to return your command-line
  arguments, and instead want it to return the swig flags (this was
  the behavior in an earlier version), be sure to call
  swig_flags.SetupSwigFlags() BEFORE calling app.run().  The call to
  SetOriginalArgv in Init() will be a noop, because SetupSwigFlags
  also calls C++-level SetArgv, and only the first call to this
  function has effect.
  """
  _SetOriginalArgv()
  SetupSwigFlags()

def _SetOriginalArgv():
  """Initializes the 'argv' portion of the C++ commandline flag
  interface with the exact set of flags passed to python on the
  commandline.

  Note: This is only one part of the C++ commandline interface.  In
  particular, this function does NOT tell the C++ flags system about
  any flags.

  Note: This function will have no effect if it is called multiple
  times, or if it is called after SetupSwigFlags or UpdateSwigFlags.

  Note: One can make a case that this should be in app.py rather than
  swig_flag.py, because it doesn't directly deal with swig
  vs. non-swig flags.  However, it only makes sense to call this if
  you're using swig, because if not, there is no way for the C++-level
  GetArgv() to be relevant.
  """
  pywrapbase.SetArgvScript(sys.argv)

setup_swig_flags_called = False

def SetupSwigFlags():
  """Initialize the C++-level commandline flags (swig flags) with the
  python flags.  We use a module-level variable to ensure that
  InitGoogleScript is only called once.
  """
  global setup_swig_flags_called

  if not setup_swig_flags_called:
    cpp_args = _GenerateArgsForSwigFlags()
    pywrapbase.InitGoogleScript(cpp_args[0], cpp_args, 1)
    setup_swig_flags_called = True

def UpdateFlags():
  """Updates the C++ counterparts of swig flags after InitGoogle has been
  called.  Can be called repeatedly to update C++ flags, unlike Init() which can
  only be called once.  Operates off the pyglib.flags.FLAGS datastructure which
  should have been initialized by _SetupCppFlags().
  """
  cpp_args = _GenerateArgsForSwigFlags()
  pywrapbase.ParseCommandLineFlagsScript(cpp_args, False)

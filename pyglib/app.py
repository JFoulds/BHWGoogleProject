# Copyright 2003 Google Inc. All Rights Reserved.

"""Generic entry point for Google applications.

To use this module, simply define a 'main' function with a single
'argv' argument and add the following to the end of your source file:

if __name__ == '__main__':
  app.run()

TODO(dgreiman): Remove silly main-detection logic, and force all clients
of this module to check __name__ explicitly.  Fix all current clients
that don't check __name__.

"""

import pdb
import sys
import traceback
from google3.pyglib import build_data
from google3.pyglib import flags
from google3.pyglib import logging

FLAGS = flags.FLAGS

flags.DEFINE_boolean('run_with_pdb', 0, 'Set to true for PDB debug mode')


# Try to import pywrapbase and swig_flags.  It may fail if the
# original BUILD file did not list it as a dependency, in which case
# we can't use_cpp_logging.  This is a best-effort approach.  If
# pywrapbase can't be imported, then swig_flags will fail as it
# imports pywrapbase as well.  Set swig_flags to None in the
# ImportError case.
#
# We must do this here as we need swig_flags imported as early as
# possible so as to read the valid C++ flags before argument parsing.
try:
  # use indirect importing as per dgreiman to avoid autopar picking up
  # false dependencies
  __import__('google3.base.pywrapbase')
  __import__('google3.pyglib.swig_flags')
  pywrapbase = sys.modules.get('google3.base.pywrapbase')
  swig_flags = sys.modules.get('google3.pyglib.swig_flags')
except ImportError:
  pywrapbase = None
  swig_flags = None


help_text_wrap = False  # Whether to enable TextWrap in help output


class Error(Exception):
  pass


class UsageError(Error):
  """The arguments supplied by the user are invalid.

  Raise this when the arguments supplied are invalid from the point of
  view of the application. For example when two mutually exclusive
  flags have been supplied or when there are not enough non-flag
  arguments. It is distinct from google3.pyglib.flags.FlagsError which
  covers the lower level of parsing and validating individual flags.
  """


class HelpFlag(flags.BooleanFlag):
  """
  HelpFlag is a special boolean flag that calls the usage function and raises
  a SystemExit exception if it is ever found in the command line arguments.
  """

  def __init__(self):
    flags.BooleanFlag.__init__(self, 'help', 0, 'show this help',
                               short_name='?', allow_override=1)

  def Parse(self, arg):
    if arg:
      usage(writeto_stdout=1)
      sys.exit(1)


class HelpshortFlag(flags.BooleanFlag):
  """
  A special boolean flag that calls the usage(shorthelp=1) function
  and raises a SystemExit exception if it is ever found in the command line
  arguments.
  """

  def __init__(self):
    flags.BooleanFlag.__init__(self, 'helpshort', 0,
                               'show usage only for this module',
                               allow_override=1)

  def Parse(self, arg):
    if arg:
      usage(shorthelp=1, writeto_stdout=1)
      sys.exit(1)


class BuildDataFlag(flags.BooleanFlag):

  """Boolean flag that writes build data to stdout and exits."""

  def __init__(self):
    flags.BooleanFlag.__init__(self, 'show_build_data', 0,
                               'show build data and exit')

  def Parse(self, arg):
    if arg:
      sys.stdout.write(build_data.BuildData())
      sys.exit(0)


def CallWithExitFix(thunk, value):
  """
  This calls THUNK, catching any SystemExits thrown and re-raising
  them outside the try/except used to catch them.  value is passed to
  THUNK when called.

  This works around a bug in versions of Python <2.3 wherein, when a
  SystemExit is raised and handled by the Python runtime, a reference
  to the traceback is retained across the call to libc's exit().  This
  means destructors for objects referred to by that traceback are not
  run.
  """

  exitval = None

  try:
    thunk(value)
  except SystemExit, e:
    exitval = e

  if exitval is not None:
    sys.exit(exitval)


def parse_flags_with_usage(args):
  """
  Try parsing the flags, exiting (after printing usage) if they are
  unparseable.
  """
  try:
    argv = FLAGS(args)
    return argv
  except flags.FlagsError, error:
    sys.stderr.write('FATAL Flags parsing error: %s\n' % error)
    sys.stderr.write('Pass --help or --helpshort to see help on flags.\n')
    sys.exit(1)


def RegisterAndParseFlagsWithUsage(is_old_style):
  """Register help flags, parse arguments and show usage if approriate.

  Args:
    is_old_style: Deprecated, set to 0!

  Returns:
    remaining arguments after flags parsing
  """
  flags.DEFINE_flag(HelpFlag())
  flags.DEFINE_flag(HelpshortFlag())
  flags.DEFINE_flag(BuildDataFlag())

  argv = parse_flags_with_usage(sys.argv)

  if not is_old_style:
    if swig_flags is not None:
      swig_flags.Init()
      logging.use_cpp_logging()

  return argv


def really_start(is_old_style):
  """
  This initializes flag values, and calls __main__.main().  Only non-flag
  arguments are passed to main().  The return value of main() is used as the
  exit status.
  """
  argv = RegisterAndParseFlagsWithUsage(is_old_style)

  try:
    if FLAGS.run_with_pdb:
      sys.exit(pdb.runcall(sys.modules['__main__'].main, argv))
    else:
      sys.exit(sys.modules['__main__'].main(argv))
  except UsageError, error:
    usage(shorthelp=1, detailed_error=error)
    sys.exit(1)


def run():
  """Begin executing the program

  - Parses command line flags with the flag module.
  - If SWIG libraries are beging used:
     - pass original commandline to C++'s GetArgv()
     - handle their flags as well
     - call use_cpp_logging
     - call InitGoogleScript
     (see swig_flags.py for details)
  - If there are any errors, print usage().
  - Calls main() with the remaining arguments.
  - If main() raises a UsageError, print usage and the error message.

  For historical reasons, calls really_start() via CallWithExitFix()
  iff invoked directly from the __main__ module.

  """
  return _actual_start(0)


def start():
  """DEPRECATED: This function does not and cannot be made to
  properly behave with C++ and Python flags.  Please use run()
  and remove calls to InitGoogleScript and use_cpp_logging in
  your script.

  Begin executing the program

  - Parses command line flags with the flag module.
  - If there are any errors, print usage().
  - Calls main() with the remaining arguments.
  - If main() raises a UsageError, print usage and the error message.

  For historical reasons, calls really_start() via CallWithExitFix()
  iff invoked directly from the __main__ module.

  """
  #logging.error("""Use of deprecated app.start() method; please change to:
  #if __name__ = '__main__':
  #app.run()
  #""")
  return _actual_start(1)


def _actual_start(is_old_style):
  """Common function invoked by both start() and run().

  """
  # Get raw traceback
  tb = None
  try:
    raise ZeroDivisionError('')
  except ZeroDivisionError:
    tb = sys.exc_info()[2]
  assert tb

  # Look at previous stack frame's previous stack frame (previous
  # frame is run() or start(); the frame before that should be the
  # frame of the original caller, which should be __main__ or appcommands
  prev_prev_frame = tb.tb_frame.f_back.f_back
  if not prev_prev_frame:
    return
  prev_prev_name = prev_prev_frame.f_globals.get('__name__', None)
  if (prev_prev_name != '__main__'
      and not prev_prev_name.endswith('.appcommands')):
    return
  # just in case there's non-trivial stuff happening in __main__
  del tb

  try:
    CallWithExitFix(really_start, is_old_style)
  except SystemExit, e:
    raise
  except Exception, e:
    # If we are using swigged logging, make sure the exception that
    # killed us actually gets logged in the INFO log.
    if logging.is_using_cpp_logging():
      logging.error('Top-level exception: %s' % e)
      logging.error(''.join(traceback.format_exception(*sys.exc_info())))
    raise


def usage(shorthelp=0, writeto_stdout=0, detailed_error=None, exitcode=None):
  """
  Extracts the __doc__ string from the __main__ module and writes it to
  stderr.  If the argument writeto_stdout=1 it is written to stdout.

  Args:
    shorthelp: print only flags from this module, rather than all flags.
    writeto_stdout: write help message to stdout, rather than to stderr.
    detailed_error: additional detail about why usage info was presented.
    exitcode: if set, exit with this status code after writing help.
  """
  if writeto_stdout:
    stdfile = sys.stdout
  else:
    stdfile = sys.stderr

  doc = sys.modules['__main__'].__doc__
  if not doc:
    doc = '\nUSAGE: %s [flags]\n' % sys.argv[0]
    doc = flags.TextWrap(doc, indent='       ', firstline_indent='')
  else:
    doc = doc.replace('%s', sys.argv[0])
    if help_text_wrap:
      doc = flags.TextWrap(flags.DocToHelp(doc))
  stdfile.write(doc)
  if shorthelp:
    flag_str = FLAGS.MainModuleHelp()
  else:
    flag_str = str(FLAGS)
  if flag_str:
    stdfile.write('flags:\n')
    stdfile.write(flag_str)
  stdfile.write('\n')
  if detailed_error is not None:
    stdfile.write('\n%s\n' % detailed_error)
  if exitcode is not None:
    sys.exit(exitcode)

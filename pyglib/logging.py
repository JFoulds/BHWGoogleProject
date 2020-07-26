#!/usr/bin/python2.4
#
# Copyright 2003 Google Inc. All Rights Reserved.

"""Logging functions in the spirit of 'PEP 282 : A Logging System'

See http://www.python.org/peps/pep-0282.html

Designed to be mostly source-compatible with a subset of PEP 282's
functionality.

As of 2004-05-07, the PEP has been incorporated into Python 2.3 as the
'logging' module.  However, this module and the standard Python module
have wandered quite far apart in two years.  Also, the name collision
is problematic.

Simple usage:

    from google3.pyglib import logging

    logging.info('Interesting Stuff')
    logging.info('Interesting Stuff with Arguments: %d', 42)

    logging.set_verbosity(logging.INFO)
    logging.log(logging.DEBUG, 'This will *not* be printed')
    logging.set_verbosity(logging.DEBUG)
    logging.log(logging.DEBUG, 'This will be printed')

    logging.warn('Worrying Stuff')
    logging.error('Alarming Stuff')
    logging.fatal('AAAAHHHHH!!!!') # Process exits

Google2 compatibility note: vlog() is defined (as an alias of
log()). log/vlog are not limited to named log levels - numbers can be
used instead (e.g. vlog(1) through vlog(9).

This module can operate in two modes: Python mode, and C++ mode.  In
Python mode, logging messages are handled by the code in this module.
In C++, logging calls are translated via SWIG to calls to the C++ code
in logging.cc .  This requires that the google3.base.pywrapbase (or
pywrapgoogle in Google2) shared library has been compiled and is
available.  Python mode is the default, C++ mode is enabled by calling
use_cpp_logging().

In Python Mode, output defaults to stderr, unless
1) start_logging_to_file() is called, or
2) set_googlestyle_logfile() is called with FLAGS.logtostderr == 0.

In C++ Mode, output defaults to files, unless
1) set_googlestyle_logfile() is called with FLAGS.logtostderr == 1

The difference in behavior is historical, and unfortunate.

"""

import getpass  # need this to get username
import os
import socket      # for hostname
import sys
import thread
import time
import traceback

from google3.pyglib import flags

FLAGS = flags.FLAGS

##############################################################################
# Named logging levels
##############################################################################

FATAL = -3
ERROR = -2
WARN  = -1
INFO  = 0
DEBUG = 1

_level_names = {
  FATAL: 'FATAL',
  ERROR: 'ERROR',
  WARN:  'WARN',
  INFO:  'INFO',
  DEBUG: 'DEBUG',
  }
# create the inverse of _level_names
_level_names_inverse = dict([(v,k) for (k,v) in _level_names.items()])

##############################################################################
# Global flags
##############################################################################

flags.DEFINE_integer("verbosity", 0, "Logging verbosity", short_name="v")
flags.DEFINE_boolean("logtostderr", 0, "Should only log to stderr?")
flags.DEFINE_boolean("alsologtostderr", 0, "also log to stderr?")
flags.DEFINE_string("stderrthreshold", "fatal",
                    "log messages at this level, or more severe, to stderr in "
                    "addition to the logfile.  Possible values are "
                    "'debug', 'info', 'warn', 'error', and 'fatal'.  "
                    "Obsoletes --alsologtostderr")
flags.DEFINE_boolean("threadsafe_log_fatal", 1,
                     "If 0, logfatal dies in a non-threadsafe way, but is "
                     "more useful for unittests because it raises an exception")
flags.DEFINE_string("log_dir", os.getenv('GOOGLE_LOG_DIR'),
                    "directory to write logfiles into")
flags.DEFINE_boolean("showprefixforinfo", 1, "Prepend prefix to info messages")

__all__ = ["get_verbosity", "set_verbosity", "set_logfile",
           "skip_log_prefix", "google2_log_prefix", "set_log_prefix",
           "log", "fatal", "error", "warn", "info", "debug", "vlog"]

##############################################################################
# Global variables
##############################################################################

# A mutex to prevent concurrent access to _logfile_map.
_logfile_map_mutex = thread.allocate_lock()

# we keep a handle on the root thread as a means to find its logfile
# again when subthreads without their own logfile attempt to write
# messages to the log
# note: to be completely accurate, the "root" thread may not be the
# true root thread -- it is simply the first thread to import logging.py
# In almost all cases, this is the same as the true root thread.
_root_thread = thread.get_ident()
_logfile_map_mutex.acquire()  # Start critical section.
try:
  # _logfile_map maps threads to logfiles.
  _logfile_map = {}
  _logfile_map[_root_thread] = sys.stderr
finally:
  _logfile_map_mutex.release()  # End critical section.

# Function to generate the text at the beginning of each log line
_log_prefix = None # later set to google2_log_prefix

# _logfile_skipped keeps track of functions to ignore in line number reporting
_logfile_skipped = {}

_stderrthreshold = None   # parsed value for FLAGS.stderrthreshold

##############################################################################
# Functions to control overall logging behavior
# NOTE: These functions are not specified by PEP282
##############################################################################

def get_verbosity():
  """Return how much logging output will be produced."""
  return FLAGS.verbosity

def set_verbosity(v):
  """Determine how much logging output should be produced.

  Causes all messages of level <= v to be logged,
  and all messages of level > v to be silently discarded.
  """

  FLAGS.verbosity = int(v)
# enddef

def set_logfile(file):
  """Override the standard log message destination.
  Returns the previous file-like object
  """
  global _logfile_map, _logfile_map_mutex
  _logfile_map_mutex.acquire()  # Start critical section.
  try:
    saved = _logfile_map.get(thread.get_ident(), _logfile_map.get(_root_thread))
    _logfile_map[thread.get_ident()] = file
  finally:
    _logfile_map_mutex.release()  # End critical section.
  return saved
# enddef

def _convert_stderrthreshold(s):
  """Take a desired threshold value, and convert it to a usable integer
  value that will be usable by python and cpp logging libs.
  """
  # Try coercion to become an int; this will catch both actual ints
  # and string versions of ints.
  ret = None
  try:
    int_val = -int(s)
    if _level_names.has_key(int_val):
      ret = int_val
    # else will pass through and return None
  except ValueError:
    if _level_names_inverse.has_key(s.upper()):
      ret = _level_names_inverse[s.upper()]
  # not a valid number or string?  fall through with None
  return ret
# enddef

def _maybe_set_stderrthreshold_from_flag():
  """If _stderrthreshold is still None (an impossible value to set to
  manually), set it to the default flag value.
  """
  if _stderrthreshold is None:
    set_stderrthreshold(FLAGS.stderrthreshold)

def _LogFileOnThread(thread_ident):
  """Returns the active log for the input thread.
  If no log has been assigned, uses the main thread's log
  """
  global _logfile_map, _logfile_map_mutex
  _logfile_map_mutex.acquire()  # Start critical section.
  try:
   ret = _logfile_map.setdefault(thread_ident,
                                 _logfile_map.get(_root_thread))
  finally:
    _logfile_map_mutex.release()  # End critical section.
  return ret
# enddef

def skip_log_prefix(name):
  """ Skip reporting the prefix of a given function name """
  (file, line) = GetFileAndLine()
  _logfile_skipped[(file, name)] = None
# enddef

def GetFileAndLine():
  """
  Returns (filename, linenumber) for the first stack frame that is not the
  _log_prefix function and not from this source file
  """
  global _log_prefix
  # Use sys._getframe().  This avoids creating a traceback object.
  f = sys._getframe()
  our_file = f.f_code.co_filename
  f = f.f_back
  while f:
    code = f.f_code
    if (code.co_filename != our_file and
        code != _log_prefix.func_code and
        (code.co_filename, code.co_name) not in _logfile_skipped):
      return (code.co_filename, f.f_lineno)
    # endif
    f = f.f_back
  # endwhile
  return ('<unknown>', 0)
# enddef

def google2_log_prefix(level):
  """Assemble a logline prefix using the google2 format."""

  global _level_names
  global _logfile_map, _logfile_map_mutex

  # Record current time
  now_tuple = time.localtime(time.time())

  (file, line) = GetFileAndLine()
  basename = os.path.basename(file)

  # Severity string
  severity = "I"
  if _level_names.has_key(level):
    severity = _level_names[level][0]
  # Return an empty prefix if requested

  if (FLAGS.showprefixforinfo == 0 and
      severity == "I" and
      FLAGS.verbosity == INFO):
    # We also have one more condition, but we check it last since
    # it requires holding a lock.
    _logfile_map_mutex.acquire()
    try:
      if _logfile_map[thread.get_ident()] == sys.stderr:
        return ''
    finally:
      _logfile_map_mutex.release()
  if severity == "D":
    severity = "I" # logging.cc has no "DEBUG" level

  str = "%s%02d%02d %02d%02d%02d %s:%s] " % (
    severity,
    now_tuple[1], # month
    now_tuple[2], # day
    now_tuple[3], # hour
    now_tuple[4], # min
    now_tuple[5], # sec
    basename,
    line,
    )
  return str
# enddef


_log_prefix = google2_log_prefix
def set_log_prefix(prefix):
  """
  Override the default log prefix function.
  Returns previous value
  """
  global _log_prefix
  old_log_prefix = _log_prefix
  _log_prefix = prefix
  return old_log_prefix
# enddef

def _log_write(level, msg):
  """Write a string to stderr and/or a logfile"""
  if FLAGS.logtostderr:
    sys.stderr.write(msg)
    return
  logfile = _LogFileOnThread(thread.get_ident())
  logfile.write(msg)
  _maybe_set_stderrthreshold_from_flag()
  if ((FLAGS.alsologtostderr or level <= _stderrthreshold)
      and logfile != sys.stderr):
    sys.stderr.write(msg)
  # endif
# enddef

def _log_unicodify(msg, args):
  """Encodes the whole message treating Unicode properly.

  When logging unicode or UTF-8 messages, this code makes sure we do
  the argument interpolation in Unicode, and then convert the result into
  printable ASCII, with all the non-ASCII characters properly escaped.

  Args:
    msg: the message, or message format, either in unicode, UTF-8 or as
         an object that can convert to a string with str();
    args: the list of arguments used for interpolation, also as a list of
          unicode or UTF-8 strings, or objects that can be interpolated.
  """
  if isinstance(msg, unicode):
    fullmessage = msg
  else:
    fullmessage = unicode(str(msg), 'utf-8', errors='replace')
  # Format message
  if len(args) > 0:
    unicode_args = []
    for arg in args:
      if isinstance(arg, str):
        unicode_args.append(unicode(str(arg), 'utf-8', errors='replace'))
      else:
        unicode_args.append(arg)
    fullmessage = fullmessage % tuple(unicode_args)
  return fullmessage.encode('utf-8', 'backslashreplace')

def _log_python(level, msg, *args):
  """Log 'msg % args' at logging level 'level'."""

  if FLAGS.verbosity >= level:
    # Format message
    fullmessage = _log_unicodify(msg, args)

    # Write message
    _log_write(level, _log_prefix(level) + fullmessage + "\n")

    # Possibly die
    if level <= FATAL:
      flush() # flush the log before dying
      sys.stderr.flush() # Python has no "flushall"

      # In threaded python, sys.exit() from a non-main thread only
      # exits the thread in question.

      # This does not work under Linux:
      #   os.kill(os.getpid(), signal.SIGTERM)
      # because:
      #
      # 1) getpid() returns the tid of the thread, which is
      # different than the pid of the process for non-main
      # threads
      #
      # 2) SIGTERM sent to a non-main thread is
      # ignored by Python.
      #
      # 3) No way to get the "real" process id
      if FLAGS.threadsafe_log_fatal:
        os.abort()

      # Also do a sys.exit in case abort doesn't do the trick, or
      # threadsafe_log_fatal is false; at least this thread will exit
      # and non-threaded programs will function correctly.
      sys.exit(1)
    # endif
  # endif
# enddef

def _flush_python():
  """Flush all log files.

  Errors are ignored.
  """
  global _logfile_map, _logfile_map_mutex
  _logfile_map_mutex.acquire()  # Start critical section.
  try:
    logfiles = _logfile_map.values()
  finally:
    _logfile_map_mutex.release()  # End critical section.

  # At this point two threads may try to flush the same logfile concurrently.
  # We let flush() deal with that.
  for logfile in logfiles:
    try:
      logfile.flush()
    except (EnvironmentError, ValueError):
      # A ValueError is thrown if we try to flush a closed file.
      pass
    # endtry
  # endfor

  sys.stderr.flush()
# enddef

def _flush_thread_specific_logfile_python():
  """Flush the logfile associated with this thread. stderr is not flushed.

  Errors are ignored.
  """
  logfile = _LogFileOnThread(thread.get_ident())
  try:
    logfile.flush()
  except (EnvironmentError, ValueError):
    # A ValueError is thrown if we try to flush a closed file.
    pass

def _logfile_name_python():
  """Return the name of the current logfile"""

  logfile = _LogFileOnThread(thread.get_ident())
  if logfile == sys.stderr:
    return None
  else:
    return logfile.name
  # endif
# enddef

def _find_log_dir_and_names(prog_name, log_dir):
  """Compute the directory and filename prefix for log file.

  Returns (log_dir, file_prefix, symlink_prefix)

  """
  if not prog_name:
    # strip the extension (foobar.par becomes foobar, and
    # fubar.py becomes fubar). We do this so that the log
    # file names are similar to C++ log file names
    prog_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    # prepend py_ to files so that python code gets a unique file, and
    # so that SWIGGED C++ stuff doesn't try to write to the same log
    # files as us.
    prog_name = 'py_%s' % prog_name
  # endif

  actual_log_dir = _find_log_dir(log_dir)

  username = getpass.getuser()
  hostname = socket.gethostname()
  file_prefix = "%s.%s.%s.log" % (prog_name, hostname, username)

  return (actual_log_dir, file_prefix, prog_name)
# enddef

def _find_log_dir(log_dir):
  """Determine which directory to put log files into

  log_dir:   If specified, the logfile(s) will be created in that
             directory.  Otherwise if the --log_dir command-line flag
             is provided, the logfile will be created in that
             directory.  Otherwise the logfile will be created in a
             standard location.
  """

  # Get a list of possible log dirs (will try to use them in order)
  if log_dir is not None:
    # log_dir was explicitly specified as an arg, so use it and it alone.
    dirs = [log_dir]
  elif FLAGS.log_dir is not None:
    # log_dir flag was provided, so use it and it alone (this mimics the
    # behavior of the same flag in logging.cc).
    dirs = [FLAGS.log_dir]
  elif os.path.exists('/export/hda3/tmp') and os.path.isdir('/export/hda3/tmp'):
    # production machine or GRHAT9 machine.  Drop /tmp as we don't
    # want to fill up root partition
    dirs = ['/export/hda3/tmp/', './']
  else:
    dirs = ['/export/hda3/tmp/', '/tmp/', './']
  # endif

  # Find the first usable log dir
  for d in dirs:
    if os.path.isdir(d) and os.access(d, os.W_OK):
      break
    # endif
  else:
    fatal("Can't find a writable directory for logs, tried %s" % dirs)
  # endfor

  return d
# enddef

def _set_stderrthreshold_python(s):
  """Init _stderrthreshold based on s, or silently ignores s if s is
  not a legal value.  TODO(csilvers): might do better for the latter...
  Legal values are 'debug', 'info', 'warn', 'error', and 'fatal'.

  We also accept the undocumented 0 through 3 as valid values, which
  are the C++ values.  This is necessary for mapreduces and other
  scripts which expect a Python par file to behave more like a C++
  command line program.
  """
  global _stderrthreshold

  new_val = _convert_stderrthreshold(s)
  if new_val is not None:
    _stderrthreshold = new_val
  #endif
#enddef

def _start_logging_to_file_python(prog_name=None, log_dir=None):
  """Send log messages to files instead of standard error."""

  # TODO(dgreiman): Set equivalent C++ flag
  FLAGS.logtostderr = 0

  actual_log_dir, file_prefix, symlink_prefix = \
                  _find_log_dir_and_names(prog_name, log_dir)

  basename = "%s.INFO.%s.%d" % (
    file_prefix,
    time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())),
    os.getpid())
  filename = os.path.join(actual_log_dir, basename)

  # Create INFO log file
  try:
    log_file = open(filename, "w")
    set_logfile(log_file)
  except EnvironmentError, e:
    fatal("Can't create log file: %s" % e)
  # endtry

  # create a symlink to the log file with a canonical name
  symlink = os.path.join(actual_log_dir, symlink_prefix + '.INFO')
  try:
    if os.path.islink(symlink):
      os.unlink(symlink)
    # endif
    os.symlink(os.path.basename(filename), symlink)
  except EnvironmentError:
    # If it fails, we're sad but it's no error.  Commonly, this
    # fails because the symlink was created by another user and so
    # we can't modify it
    pass
  # endtry
# enddef

def _set_googlestyle_logfile_python(prog_name=None, log_dir=None):
  """Conditionally log to files, based on --logtostderr"""

  if FLAGS.logtostderr:
    return
  else:
    _start_logging_to_file_python(prog_name, log_dir)
  # endif
# enddef

##############################################################################
# Convenience functions
##############################################################################

def fatal(msg, *args): apply(log, (FATAL, msg) + args)
def error(msg, *args): apply(log, (ERROR, msg) + args)
def warn(msg, *args): apply(log, (WARN, msg) + args)
def info(msg, *args): apply(log, (INFO, msg) + args)
def debug(msg, *args): apply(log, (DEBUG, msg) + args)
def vlog(level, msg, *args) : apply(log, (level, msg) + args)

# PEP-282's final form used 'warning' for warnings, but pyglib.logging
# was implemented based on a draft of it that used 'warn'.  This has
# been a source of confusion and bugs, so allow both.
warning = warn


# Counter to keep track of number of log entries per token.
_log_every_n_counter = {}


def _get_next_log_every_n_count(token):
  """Wrapper for _log_every_n_counter.
  Returns the number of times this function has been called with *token* as an
  argument (starting at 0)
  """
  global _log_every_n_counter
  _log_every_n_counter[token] = 1 + _log_every_n_counter.get(token, -1)
  return _log_every_n_counter[token]
# enddef


def log_every_n(level, msg, n, *args):
  """ Log 'msg % args' at level 'level' only once per 'n' times per reference
  in the code.

  Logs the 1st call, (N+1)st call, (2N+1)st call, etc.

  NOTE:  just like the C++ implementation, this is not threadsafe.
  """
  count = _get_next_log_every_n_count(GetFileAndLine())
  log_if(level, msg, not (count % n), *args)
# enddef


def log_if(level, msg, condition, *args):
  """ Log 'msg % args' at level 'level' only if condition is fulfilled."""
  if condition:
    vlog(level, msg, *args)
# enddef


def exception(msg, *args):
  """Log an exception, with traceback and message."""

  exc = sys.exc_info()
  traceback_lines = traceback.format_exception(exc[0], exc[1], exc[2])
  trace = "".join(traceback_lines)
  # Trim trailing newlines
  while trace and trace[-1] == "\n":
    trace = trace[:-1]
  # endwhile
  if args:
    args = args + (trace,)
    error(msg + '\n%s', *args)
  else:
    # If the caller gave no args, they might have put % in msg, so we can't try
    # to use string expansion on it.
    error('%s\n%s', msg, trace)
# enddef

##############################################################################
# Stubs that can be reassigned
#
# TODO(dgreiman): Use PythonLog and CppLog objects instead of stubs
##############################################################################

log = _log_python
flush = _flush_python
flush_thread_specific_logfile = _flush_thread_specific_logfile_python
logfile_name = _logfile_name_python
start_logging_to_file = _start_logging_to_file_python
set_googlestyle_logfile = _set_googlestyle_logfile_python
set_stderrthreshold = _set_stderrthreshold_python

##############################################################################
# C++ interaction
#
# TODO(dgreiman): Move this into pywrapbase.py via %pythoncode%
# directives in google3/base/base.swig, so that the base logging.py
# doesn't have dependencies.
##############################################################################

# Only code below this line should use pywrap.  We call this variable
# pywrapbase, even in Google2 where it is really pywrapgoogle, so that
# most of the code can remain textually the same in Google2/Google3.
pywrapbase = None

def _cpp_log_level(py_level):
  """Get the C++ log level that corresponds to a given Python log level.

  Arguments:
    py_level: int - a key in _level_names
  """
  if py_level >= 0:
    # C++ log levels must be >= 0
    return 0
  # end if
  return -py_level
# end def

def _log_cpp(level, msg, *args):
  """Log 'msg % args' at logging level 'level'."""
  # Verbosity is a Python-only flag.  According to the tests it should override
  # the verbosity level the C++ code is using when and only when the level
  # passed to this function is >= DEBUG.
  #
  # I have no clue what the reasoning behind that is.
  if level >= DEBUG and FLAGS.verbosity < level:
    return
  # end if

  # Format message
  fullmessage = _log_unicodify(msg, args)

  file, line = GetFileAndLine()
  pywrapbase.LogMessageScript(file, line, _cpp_log_level(level), fullmessage)
# enddef

def _flush_cpp():
  """Flush all log files"""
  pywrapbase.FlushLogFiles(pywrapbase.INFO) # flush them all
# enddef

def _flush_thread_specific_logfile_cpp():
  """This is not implemented for cpp, so we raise an exception.
  """
  raise NotImplementedError, \
        'Cannot flush a thread-specific logfile in cpp logging mode.'

def _logfile_name_cpp():
  """Return the name of the current logfile"""

  # Not meaningful, since multiple logfiles exist
  return None
# enddef

def _set_stderrthreshold_cpp(s):
  """Configures the stderrthreshold for cpp logging"""
  new_val = _convert_stderrthreshold(s)
  if new_val is not None:
    pywrapbase.SetStderrLogging(_cpp_log_level(new_val))
  #endif
#enddef

def _start_logging_to_file_cpp(prog_name=None, log_dir=None):
  """Send log messages to files instead of standard error."""
  # TODO(dgreiman): Set equivalent C++ flag
  FLAGS.logtostderr = 0

  actual_log_dir, file_prefix, symlink_prefix = \
                  _find_log_dir_and_names(prog_name, log_dir)

  absolute_prefix = os.path.join(actual_log_dir, file_prefix)

  pywrapbase.SetLogDestination(pywrapbase.INFO,
                               '%s.INFO.' % absolute_prefix)
  pywrapbase.SetLogSymlink(pywrapbase.INFO, symlink_prefix)
  pywrapbase.SetLogDestination(pywrapbase.WARNING,
                               '%s.WARNING.' % absolute_prefix)
  pywrapbase.SetLogSymlink(pywrapbase.WARNING, symlink_prefix)
  pywrapbase.SetLogDestination(pywrapbase.ERROR,
                               '%s.ERROR.' % absolute_prefix)
  pywrapbase.SetLogSymlink(pywrapbase.ERROR, symlink_prefix)
  pywrapbase.SetLogDestination(pywrapbase.FATAL,
                               '%s.FATAL.' % absolute_prefix)
  pywrapbase.SetLogSymlink(pywrapbase.FATAL, symlink_prefix)
# enddef

def _set_googlestyle_logfile_cpp(prog_name=None, log_dir=None):
  """Conditionally log to files, based on --logtostderr"""
  if FLAGS.logtostderr:
    pywrapbase.LogToStderr()
  else:
    start_logging_to_file(prog_name, log_dir)
  # endif
# enddef

# Programs that use SWIG can use C++ logging if they ask
def use_cpp_logging():
  """Divert logging calls to the C++ logging code.

  Requires that pywrapbase already be imported.

  """
  global pywrapbase
  pywrapbase = sys.modules.get('google3.base.pywrapbase', None)
  if not pywrapbase:
    raise AssertionError("The google3.base.pywrapbase module must be imported "
                         "before use_cpp_logging() is called. ")
  # endif

  # Replace stubs
  global log, flush, flush_thread_specific_logfile, logfile_name
  global start_logging_to_file
  global set_googlestyle_logfile
  global set_stderrthreshold
  log = _log_cpp
  _log_cpp(INFO,
           "SWIG logging enabled; logging.debug will only be visible "
           "when --verbosity/-v are 1 or higher")
  flush = _flush_cpp
  flush_thread_specific_logfile = _flush_thread_specific_logfile_cpp
  logfile_name = _logfile_name_cpp
  start_logging_to_file = _start_logging_to_file_cpp
  set_googlestyle_logfile = _set_googlestyle_logfile_cpp
  set_stderrthreshold = _set_stderrthreshold_cpp
# endif

def is_using_cpp_logging():
  global log
  return log == _log_cpp

# Pyserverizer programs always use C++ logging
if sys.modules.get('pyserverizer', None):
  use_cpp_logging()
# endif

# TODO(dgreiman): Turn on C++ logging for any program with pywrapbase
#if sys.modules.get('google3.base.pywrapbase', None):
#if sys.modules.get('pywrapgoogle', None):
#  use_cpp_logging()
## endif


##############################################################################
###  GWQStatusMessage()
##############################################################################

def GWQStatusMessage(msg):
  """
  Python implementation of the C++ function of the same name (see
  google3/base/logging.cc).

  Writes the specified status message to the file ./STATUS. The write is done
  atomically by writing the new data to a temporary file (./STATUS.new),
  and then renaming the temporary file over the STATUS file.
  """
  dir = os.getenv('GOOGLE_STATUS_DIR')
  if dir is None:
    # not running under borglet or WQ subordinate
    if os.getenv('WORKQUEUE_SLAVE_PROCESS_TAG') is not None:
      # running under GSA workqueue
      dir = '.'
    elif os.getcwd().find('/workqueue-subordinate/') != -1:
      dir = '.'
    else:
      # we don't appear to be running under either borg or GWQ
      return

  real_file = os.path.join(dir, 'STATUS')
  temp_file = real_file + '.new'
  f = file(temp_file, 'w')
  f.write(msg)
  f.close()
  os.rename(temp_file, real_file)

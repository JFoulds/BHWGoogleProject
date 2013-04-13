# Original Author: Huican Zhu
#
# With a lot of useful comments from bwolen, est and benp. They helped
# me figure out how to pass a reference to a variable: use lambda
#
# Copyright 2002, Google

import cgi
import socket
import time
import traceback
import sys
import os

from google3.pyglib import flags
from google3.pyglib import timer
from google3.pyglib import build_data
from google3.pyglib import sysinfo

# Declaration needed for Python 2.2.0 used in enterprise
try:
  True
except NameError:
  True = 1
  False = 0

# pychecker generates suprious classattr warnings about the _data
# attribute of ExportedMap.  It also complains about the return types
# of Convert(), which is intentionally long or int.
__pychecker__ = "no-returnvalues no-classattr"

"""
These functions mimic google3/stats/io/expvar.{cc,h}. The exported variables are
supposed to be read by python based servers and report them at user requests.

This also includes exported timing functionality, with classes Timer
and ExportedTimers.

As in C++, you can export variables and functions that take no arguments.
Actually, there is no such thing as exporting a variable. You can
only export functions using the ExportFunction() in this module. However,
you can export a variable just as easily using a 'lambda' expression.  For
example, to export variable foo, you can do:
      ExportFunction('exp-foo', lambda: foo)

If 'cf' is a class fuction and 'ca' is a class attribute they should be exported
like the following:

    def cf(self):
       ...

    def __init__(self):
      self.ca = 0
      expvar.ExportFunction('expcf', self.cf)
      expvar.ExportFunction('expca', lambda: self.ca)

Sample usage:

from google3.pyglib import expvar

def foo():
  return 'foo'

expvar.ExportFunction('exp1', foo)

a = 100
expvar.ExportFunction('exp2', lambda: a)

class Test(object):

  def tf(self):
    return 2 * self.ta

  def __init__(self):
    self.ta = 0
    expvar.ExportFunction('expta', lambda: self.ta)
    expvar.ExportFunction('exptf', self.tf)
    self.timers = ExportedTimers()

  def Work(self):
    self.timers.Start('section1')
    for idx in xrange(100):
      self.timers.Start('part%d'% idx)
      self.doStuff(idx)
      self.timers.Stop('part%d' % idx)
    self.timers.Stop('section1')
    ...


ct = Test()
ct.Work()
ct.ta = 1

print expvar.PrintAllPlain()
"""

class Error(Exception): pass
class AlreadyExportedError(Error): pass
class NotExportedError(Error): pass
class ReservedLabelError(Error): pass

# global variables that are only accessed in the module
_already_called = False  # only want to call SetupGlobalExportedVariables once
_exported_vars  = {}     # to contain all the exported variables
_pyserverizer   = None   # the pyserverizer module, if any
_start_time     = time.time()


class ExportedVar(object):
  """Represents an individual exported variable.

  This contains both the callback and an optional docstring."""

  def __init__(self, callback, docstring=None, internal_caller=False):
    """Initializer method.

    Arguments:
      callback: callable object that returns the variable's value.
      docstring: string.  Optional doc string.
      internal_caller: boolean.  If True, caller is internal to expvar module.
                       This should only be set to true by variables
                       exported from within this module.
    """

    self._callback = callback

    if docstring is not None:
      # prefix docstring with the caller's filename and line number
      stack_frames = traceback.extract_stack()
      stack_frames.reverse()
      for frame in stack_frames[1:]:
        # if the caller is internal, we grab the first stack frame we
        # see; otherwise, we look for the first one from a file other
        # than this one
        if internal_caller or not frame[0].endswith('/expvar.py'):
          filename = frame[0]
          google3_prefix = '/google3/'
          idx = filename.rfind(google3_prefix)
          if idx >= 0:
            filename = filename[idx + len(google3_prefix):]
          docstring = '%s:%s: %s' % (filename, frame[1], docstring)
          break

    self._docstring = docstring

  def Value(self):
    """Returns the value returned by the callback."""
    # TODO(dgreiman): Use iscallable check to remove need for lamdbas for
    # constants
    return self._callback()

  def DocString(self):
    """Returns the docstring."""
    return self._docstring


def _SetupGlobalExportedVariables():
  """
  Export some common variables needed by all programs.

  Can be called multiple times.
  """
  global _already_called
  if _already_called:
    return
  _already_called = True

  version = 'unknown version'

  # These are the variables that are shared by all python programs
  global _start_time
  start_ctime = time.ctime(_start_time)
  args        = ' '.join(sys.argv)

  if version != None:
    _exported_vars['version'] = ExportedVar(
        lambda: version,
        'program version',
        internal_caller=True)
  _exported_vars['hostname'] = ExportedVar(
      socket.gethostname,
      'hostname for machine on which the server is running',
      internal_caller=True)
  _exported_vars['start-time'] = ExportedVar(
      lambda: start_ctime,
      'time at which the server started (human-readable string)',
      internal_caller=True)
  _exported_vars['argv'] = ExportedVar(
      lambda: args,
      'command line used to start the server',
      internal_caller=True)
  _exported_vars['uptime-in-ms'] = ExportedVar(
      lambda: long((time.time() - _start_time) * 1000),
      'time since the server was started (ms)',
      internal_caller=True)
  _exported_vars['cpu-speed'] = ExportedVar(
      GetCpuSpeed,
      'the clock speed of each of the machine\'s CPUs',
      internal_caller=True)
  _exported_vars['cpu-utilization'] = ExportedVar(
      GetCpuUtilization,
      'the machine\'s load average (NOT the CPU utilization of this '
      'individual process - see process-cpu-seconds for that)',
      internal_caller=True)
  _exported_vars['memory-usage'] = ExportedVar(
      GetMemoryUsage,
      'resident segment size of this process (in bytes)',
      internal_caller=True)
  _exported_vars['nice'] = ExportedVar(
      GetNiceValue,
      'nice level of this server',
      internal_caller=True)
  _exported_vars['process-cpu-seconds'] = ExportedVar(
      GetCPUSeconds,
      'total CPU seconds used by this process',
      internal_caller=True)
  _exported_vars['num_open_fds'] = ExportedVar(
      GetNumOpenFDs,
      'number of file descriptors currently open for this process',
      internal_caller=True)
  _exported_vars['python-executable'] = ExportedVar(
      lambda: sys.executable,
      'python executable used by this process',
      internal_caller=True)
  _exported_vars['python-version'] = ExportedVar(
      lambda: "%d.%d.%d" % sys.version_info[0:3],
      'Version of python used by this process (major.minor.micro)',
      internal_caller=True)

  _exported_vars['target-name'] = ExportedVar(
      build_data.Target,
      'build target',
      internal_caller=True)
  _exported_vars['build-changelist'] = ExportedVar(
      build_data.Changelist,
      'build changelist',
      internal_caller=True)
  _exported_vars['build-client'] = ExportedVar(
      build_data.ClientName,
      'perforce client name',
      internal_caller=True)
  _exported_vars['build-depot-path'] = ExportedVar(
      build_data.DepotPath,
      'the perforce depot path of source code tree',
      internal_caller=True)
  _exported_vars['build-label'] = ExportedVar(
      build_data.BuildLabel,
      'a build label for this binary',
      internal_caller=True)
  _exported_vars['build-info'] = ExportedVar(
      build_data.BuildInfo,
      'build information',
      internal_caller=True)
  _exported_vars['build-timestamp-as-int'] = ExportedVar(
      build_data.Timestamp,
      'build timestamp (seconds since epoch)',
      internal_caller=True)
  _exported_vars['build-timestamp'] = ExportedVar(
      lambda: 'Built on %s (%d)' % (
        time.strftime('%b %d %Y %H:%M:%S',
                      time.localtime(build_data.Timestamp())),
        build_data.Timestamp()
      ),
      'build timestamp (human-readable string)',
      internal_caller=True)
  _exported_vars['gplatform'] = ExportedVar(
      build_data.Platform,
      'the compiler/target-cpu combination used to compile this binary.'
      '  (Note, this is the configured CPU, not the PYTHON_CPU.)',
      internal_caller=True)

  borg_task_state_count = os.getenv('BORG_TASK_STATE_COUNT_MAP')
  if borg_task_state_count:
    _exported_vars['borg_task_state_count'] = ExportedVar(
        lambda: 'map:state ' + borg_task_state_count,
        '(borg tasks only) map-valued variable containing the count '
        'of prior restarts for this task, categorized by state',
        internal_caller=True)
  borg_last_task_restart_state = os.getenv('BORG_LAST_TASK_RESTART_STATE')
  if borg_last_task_restart_state:
    _exported_vars['borg_last_task_restart_state'] = ExportedVar(
        lambda: borg_last_task_restart_state,
        '(borg tasks only) name of the last free failure state of this task',
        internal_caller=True)
  borg_last_task_restart_time = os.getenv('BORG_LAST_TASK_RESTART_TIME')
  if borg_last_task_restart_time:
    _exported_vars['borg_last_task_restart_time'] = ExportedVar(
        lambda: borg_last_task_restart_time,
        '(borg tasks only) (time_t) the time of the last free failure of '
        'this task',
        internal_caller=True)
  borg_last_task_restart_text = os.getenv('BORG_LAST_TASK_RESTART_TEXT')
  if borg_last_task_restart_text:
    _exported_vars['borg_last_task_restart_text'] = ExportedVar(
        lambda: borg_last_task_restart_text,
        '(borg tasks only) the reason for the last free failure of this task',
        internal_caller=True)
  borg_last_task_failure_state = os.getenv('BORG_LAST_TASK_FAILURE_STATE')
  if borg_last_task_failure_state:
    _exported_vars['borg_last_task_failure_state'] = ExportedVar(
        lambda: borg_last_task_failure_state,
        '(borg tasks only) name of the last non-free failure state '
        'of this task',
        internal_caller=True)
  borg_last_task_failure_time = os.getenv('BORG_LAST_TASK_FAILURE_TIME')
  if borg_last_task_failure_time:
    _exported_vars['borg_last_task_failure_time'] = ExportedVar(
        lambda: borg_last_task_failure_time,
        '(borg tasks only) (time_t) the time of the last non-free failure of '
        'this task',
        internal_caller=True)
  borg_last_task_failure_text = os.getenv('BORG_LAST_TASK_FAILURE_TEXT')
  if borg_last_task_failure_text:
    _exported_vars['borg_last_task_failure_text'] = ExportedVar(
        lambda: borg_last_task_failure_text,
        '(borg tasks only) the reason for the last non-free failure '
        'of this task',
        internal_caller=True)

  for flag in flags._exported_flags.itervalues():
    _exported_vars['hidden-FLAGS_%s' % flag.name] = ExportedVar(
        lambda flag=flag: flag.value,
        'value of --%s flag' % flag.name,
        internal_caller=True)

  global _pyserverizer
  try: _pyserverizer = __import__("pyserverizer")
  except: pass

def GetCpuSpeed():
  try:
    return ' '.join([str(x) for x in sysinfo.CPUSpeed()])
  except sysinfo.SysInfoError:
    return 'none'

def GetCpuUtilization():
  try:
    return sysinfo.ProcessorUsage()
  except sysinfo.SysInfoError:
    return 'none'

def GetMemoryUsage():
  try:
    return sysinfo.MemoryUsage()
  except sysinfo.SysInfoError:
    return 'none'

def GetNiceValue():
  try:
    return sysinfo.Nice()
  except sysinfo.SysInfoError:
    return 'none'

def GetCPUSeconds():
  try:
    return sysinfo.MyCPUUsage()
  except sysinfo.SysInfoError:
    return 'none'

def GetNumOpenFDs():
  try:
    return sysinfo.NumOpenFDs()
  except sysinfo.SysInfoError:
    return 'none'

def GetValue(name):
  """
  Return the value of *name*.

  A tuple is returned.  The first entry indicates if *name* is
  exported. The second entry is the actual value. It is None if *name*
  isn't exported
  """

  _SetupGlobalExportedVariables()

  if name in _exported_vars:
    return (True, _exported_vars[name].Value())
  else:
    return (False, None)


def GetDoc(name):
  """Return the docstring of the specified variable.

  Arguments:
    name: The name of the variable whose docstring should be returned.

  Returns:
    Tuple (name_exported, docstring) where:
      name_exported: True if the variable exists, False otherwise.
      docstring: Documentation string for the variable if it exists;
        None otherwise.
  """

  _SetupGlobalExportedVariables()

  if name in _exported_vars:
    return (True, _exported_vars[name].DocString())
  else:
    return (False, None)


def _QuoteValue(value):
  """
  Convert value to a string and remove any existing double quotes from it.  Iff
  value contains spaces, double-quote it as well after removing any preexisting
  double quotes.  This mimics the behavior of google3/stats/io/expvar.cc.

  Arguments:
    value: any object - the value to quote

  Returns: str - the quoted value
  """
  value = str(value).replace('"', '')
  if ' ' in value:
    value = '"%s"' % value
  return value


def GetAllValues(include_hidden=False):
  """
  Get values for all the exported variables. A map is returned which
  contains (name, value) pairs. If *include_hidden* is false,
  variable names that start with 'hidden-' are not returned
  """

  _SetupGlobalExportedVariables()

  variables = {}
  for name, obj in _exported_vars.iteritems():
    if include_hidden or not name.startswith('hidden-'):
      variables[name] = obj.Value()

  return variables


def GetAllDocStrings(include_hidden=False):
  """Return docstrings for all variables.

  Arguments:
    include_hidden: boolean.  If True, return docstrings for hidden
      variables (those starting with 'hidden-') as well.

  Returns:
    A dict mapping variable names to their doc strings.
    No entry will be returned for variables for which there is no
    docstring provided.
  """

  # TODO(roth): handle the case where we have multiple exports for the same
  # variable name
  # (e.g. "var{foo=a}" vs "var{foo=b}" - should only print a single
  # docstring for "foo")

  _SetupGlobalExportedVariables()

  variables = {}
  for name, obj in _exported_vars.iteritems():
    if include_hidden or not name.startswith('hidden-'):
      doc = obj.DocString()
      if doc is not None:
        variables[name] = doc

  return variables


def GetAllValueNamesSorted(include_hidden=False):
  """Returns a sorted list of all keys returned by GetAllValues()."""
  names = GetAllValues(include_hidden).keys()
  names.sort()
  return names


def GetAllDocNamesSorted(include_hidden=False):
  """Returns a sorted list of all keys returned by GetAllDocStrings()."""
  names = GetAllDocStrings(include_hidden).keys()
  names.sort()
  return names


def PrintVarPlain(name):
  """
  Returns a string with the exported variable and its value formatted as 'plain'
  """
  status, value = GetValue(name)
  if not status: return ''
  return '%s %s\n' % (name, _QuoteValue(value))


def PrintDocPlain(name):
  """
  Returns a string with the exported variable and its docstring formatted
  as 'plain'
  """
  status, doc = GetDoc(name)
  if not status: return ''
  return '%s %s\n' % (name, _QuoteValue(doc))


def PrintVarHTML(name):
  """Returns HTML-formatted string of the variable and its value."""
  status, value = GetValue(name)
  if not status: return ''
  return '<b>%s</b> %s<br>\n' % (cgi.escape(str(name)),
                                 cgi.escape(_QuoteValue(value)))


def PrintVarDocHTML(name):
  """Returns HTML-formatted string of the variable, value, and docstring."""
  status, value = GetValue(name)
  if not status: return ''
  _, doc = GetDoc(name)
  if doc is not None:
    #  After escaping, replace the ": " at the end of the location with ":<br>"
    doc = cgi.escape(str(doc))
    doc = doc.replace(': ', ':<br>', 1)
    return '<span><b>%s</b><div>%s</div></span> %s<br>\n' % (
        cgi.escape(str(name)),
        doc,
        cgi.escape(_QuoteValue(value)))
  else:
    return '<b>%s</b> %s<br>\n' % (cgi.escape(str(name)),
                                   cgi.escape(_QuoteValue(value)))


def PrintDocHTML(name):
  """Returns HTML-formatted string of the variable and its docstring."""
  status, doc = GetDoc(name)
  if not status: return ''
  return '<b>%s</b> %s<br>\n' % (cgi.escape(str(name)),
                                 cgi.escape(_QuoteValue(doc)))


def PrintAllPlain(strip_lines=True):
  """
  Returns a string with the exported variables and their values
  one-per-line like so
    var-name var-value\n
  Thus, it's bad if var-name has spaces or if var-value has a newline.
  Args:
   strip_lines: remove leading whitespace from text. e.g.:

   with strip_lines = False, a typical return string is:
     'uptime-in-ms 4344\n version "unknown version"\n ...'
   with strip_lines = True:
     'uptime-in-ms 32061\nversion "unknown version"\n ...'
  """
  if strip_lines:
    pat = ''
  else:
    pat = ' '
  return pat.join(map(PrintVarPlain, GetAllValues()))


def PrintAllDocPlain():
  """Print all docstrings.

  Returns:
    A string with the exported variables and their docstrings
    one-per-line like so
      var-name docstring\n
    Thus, it's bad if var-name has spaces or if docstring has a newline.
  """
  return ''.join(map(PrintDocPlain, GetAllDocStrings()))


# Like the above, but print the result in HTML format.
def PrintAllHTML():
  """Like PrintAllPlain(), but print the result in HTML format."""
  return '<tt>%s</tt>' % ' '.join(map(PrintVarHTML, GetAllValueNamesSorted()))


def PrintAllVarDocHTML():
  """Like PrintAllHTML(), but print with docstrings."""
  names = GetAllValueNamesSorted()
  return '<tt>\n%s</tt>' % ''.join(map(PrintVarDocHTML, names))


def PrintAllDocHTML():
  """
  Like PrintAllDocPlain(), but print the result in HTML format
  """
  return '<tt>\n%s</tt>' % ''.join(map(PrintDocHTML, GetAllDocNamesSorted()))


# labels not allowed to be used as map keys
_RESERVED_LABELS = (
    'var',
    'instance',
    'shard',
    'job',
    'service',
    'zone',
    )

def CheckLabel(label):
  """Raise an error if a reserved label was specified."""
  if label in _RESERVED_LABELS:
    raise ReservedLabelError('Reserved label "%s" specified in exported '
                             'variable' % str(label))


# This is the function that registers a function for export.
def ExportFunction(name, f, docstring=None, allow_reserved_labels=False):
  """
  Register a function to export.
  To export a variable foo, use: ExportFunction('name', lambda foo)
  Args:
    docstring: string.  A one-line description of the meaning of this
      exported variable, which will be available from the
      running server via the "/varzdoc" endpoint.
      (See comments in google3/stats/io/public/expvar.h for
      guidelines about what to put in the docstring.)
    allow_reserved_labels: bool.  If false, raise an exception if the
      variable name contains reserved labels.
  """

  _SetupGlobalExportedVariables()

  if name in _exported_vars:
    raise AlreadyExportedError, name + " is already exported"

  # for names of the form "name{label1=val1,label2=val2,...}"
  if not allow_reserved_labels:
    idx = name.find('{')
    if idx > 0:
      for kv in name[idx + 1:].split(','):
        CheckLabel(kv.split('=', 1)[0])

  _exported_vars[name] = ExportedVar(f, docstring)
  global _pyserverizer
  if _pyserverizer: _pyserverizer.RegisterExportedVariable(name, f)

def RemoveExportedFunction(name):
  """
  Stop exporting the variable with the specified name.
  """

  _SetupGlobalExportedVariables()

  if name not in _exported_vars:
    raise NotExportedError, name + " is not exported"

  del _exported_vars[name]
  global _pyserverizer
  if _pyserverizer: _pyserverizer.DeregisterExportedVariable(name)


class ExportedTimers(object):
  """ This class encapsulates timer functions which may be exported.
  You can have any number of timers, each of which is uniquely
  identified by a key.  The key is used for the exported variable name.

  TODO: support hour/min stats, just as in C++. That should be a subclass
  of exportedTimers.

  Args:
    export_automatically: bool.  If this is true, we automatically
    export the variable
  """

  def __init__(self, export_automatically=True):
    self.__timers = {}
    self.__export_automatically = export_automatically

  def Start(self, key, docstring=None, timer_class=timer.Timer,
            allow_reserved_labels=False):
    """ This starts timing a specific key.  If this the timer for this key
    had been previously running, it is restarted.  If no timer had existed,
    a new one is created.

    Args:
      key: a string. This will be the name of the exported variable.
      docstring: string.  Optional docstring to pass to ExportFunction().
      timer_class: class reference. Reference to type of timer that will
      be used if no timer exists
      allow_reserved_labels: bool.  If false, raise an exception if the
      key contains a reserved label.
    """
    if key not in self.__timers:
      self.__timers[key] = timer_class()
      if self.__export_automatically:
        ExportFunction(key, lambda: str(self.__timers[key]),
                       allow_reserved_labels=allow_reserved_labels,
                       docstring=docstring)
    self.__timers[key].Start()

  def Stop(self, key):
    """ This stops timing a specific key.
    Args:
      key: a string.
    Throws:
      KeyError, if key isn't present.
    """
    self.__timers[key].Stop()

  def GetTimerObject(self, key):
    """Returns a timer object corresponding to a key.
    Args:
      key: a previously-created key.
    Throws:
      KeyError, if a timer corresponding to an entry doesn't exist.
    """
    return self.__timers[key]


class ExportedMap(object):
  """
  This class allows you to export a map from strings to numbers, or from numbers
  to numbers.
  This class does two things:
    * Export the data in "key1:val1 key2:val2" format
    * Enforce restrictions on key names and variable values.
  The exported value will look like:
     varname map:label key1:val1 key2:val2 key3:val3...
  Args:
    varname: string.  The name for the exported variable.
    label: string.  A one-word description of the map keys
                    e.g., 'disk' or 'cpu' or 'type.source'
    docstring: string.  Optional docstring to pass to ExportFunction().
    precision: integer.  The number of digits to display to the right
                    of the decimal point.
    export_automatically: bool.  If true, automatically export the variable
    allow_reserved_labels: bool.  If false, raise an exception if any
                    of the '.'-delimited names in label are reserved labels.
  """

  def __init__(self, varname, label, docstring=None, precision=6,
               export_automatically=True, allow_reserved_labels=False):
    self.check_key(varname)
    self.check_key(label)
    if not allow_reserved_labels:
      for l in label.split('.'):
        CheckLabel(l)
    self._data = {}
    self._precision = precision
    self._label = label
    if export_automatically:
      ExportFunction(varname, lambda:str(self),
                     allow_reserved_labels=allow_reserved_labels,
                     docstring=docstring)

  def check_key(self, key):
    if ' ' in str(key):
      raise ValueError, 'Invalid key "%s"' % str(key)

  def escape(self, string):
    """ Escape colons (which are special in key:value) and backslash """
    return string.replace('\\', '\\\\').replace(':', '\\:')

  def __repr__(self):
    if not self._data:
      return ""
    result_list = ["map:%s" % self._label]
    klist = self._data.keys()
    klist.sort()
    for k in klist:
      v = self._data[k]
      k = self.escape(str(k))
      if isinstance(v, float):
        if v > -.01 and v < .01 and v != 0.:
          result_list.append("%s:%.*e" % (k, self._precision, v))
        else:
          result_list.append("%s:%.*f" % (k, self._precision, v))
      else:
        result_list.append("%s:%d" % (k, v))
    return " ".join(result_list)

  def __len__(self):
    return len(self._data)

  def __contains__(self, key):
    return key in self._data

  def get(self, key, default=None):
    """A dict-like get method."""
    self.check_key(key)
    return self._data.get(key, default)

  def __getitem__(self, key):
    """ Return mvar[key] """
    self.check_key(key)
    return self._data[key]

  def __setitem__(self, key, value):
    """ mvar[key] = value, checking the key and value """
    self.check_key(key)
    if isinstance(value, (int, long, float)):
      self._data[key] = value
    else:
      self._data[key] = float(value)

  def __delitem__(self, key):
    del self._data[key]

  def __iter__(self):
    return iter(self._data)

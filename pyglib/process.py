#
# Original Author: Daniel Dulitz
#
# Copyright 2002, Google
#

from __future__ import nested_scopes

import commands
import errno
import fcntl
import os
import pickle
import select
import StringIO
import sys
import time
import traceback
import types

from google3.pyglib import gexcept
from google3.pyglib import logging

from google3.production.common import prodlib

def JoinUsingMkarg(cmd_or_list):
  """
  If cmd_or_list is a list (assumed to be strings), this joins the
  list elements into a single string that can be passed as an argument
  to "sh -c" or equivalent.  If the command is already a string, it is
  returned unmodified.
  """
  if type(cmd_or_list) == types.StringType:
    return cmd_or_list
  out = ''
  for cmd in cmd_or_list: out += commands.mkarg(str(cmd))
  return out[1:]

def RemoteCommandString(machine, commandline, **kwargs):
  """
  This builds a command string for remote execution of some command
  with various standard arguments.

  Supported keywords include:

    "alarm" to specify a maximum wait time in seconds
    "alarmpath" to override the default alarm command
    "lalarmpath" to override the local alarm command
    "ralarmpath" to override the remote alarm command
    "alarmargs" to specify additional arguments
    "sshpath" to specify the remote shell command
    "sshargs" to specify extra arguments
    "user" to specify the remote user account
    "cd" to set a working directory for the remote process
    "output" if set, means to pass stderr and stdout
    "console" runs the command within a local terminal
    "limitcore" adds ulimit -c to the command string
    "limitfiles" adds ulimit -n to the command string

  By default there is no alarm and output is directed to /dev/null.
  """
  user       = ''
  alarmtime  = 0
  alarmargs  = ''
  lalarmpath = '/root/google/setup/alarm'
  ralarmpath = '/root/google/setup/alarm'
  chdir      = None
  output     = '>/dev/null 2>&1'
  sshpath    = 'ssh'
  sshargs    = '-n -P -o BatchMode=yes'
  console    = 0
  limitcore  = None
  limitfiles = None

  if kwargs.has_key('alarmpath') and (kwargs.has_key('lalarmpath') or kwargs.has_key('ralarmpath')):
    raise Exception, '\'alarmpath\' and  (\'alarmpath\' or  \'alarmpath\') kwargs are exclusive'

  if kwargs:
    for key in kwargs.keys():
      if 'alarm' == key:
        alarmtime = int(kwargs[key])
      elif 'alarmpath' == key:
        lalarmpath = kwargs[key]
        ralarmpath = kwargs[key]
      elif 'lalarmpath' == key:
        lalarmpath = kwargs[key]
      elif 'ralarmpath' == key:
        ralarmpath = kwargs[key]
      elif 'alarmargs' == key:
        alarmargs = kwargs[key]
      elif 'sshpath' == key:
        sshpath = kwargs[key]
      elif 'sshargs' == key:
        sshargs = '%s' % kwargs[key]
      elif 'cd' == key:
        chdir = kwargs[key]
      elif 'output' == key:
        output = '2>&1'
      elif 'user' == key:
        user = '%s@' % kwargs[key]
      elif 'console' == key:
        console = kwargs[key]
      elif 'limitcore' == key:
        limitcore = kwargs[key]
      elif 'limitfiles' == key:
        limitfiles = kwargs[key]
      else:
        raise Exception, 'no such keyword argument: %s' % key
      # end if
    # end for
  # end if
  cmd = '. /etc/profile'

  if chdir:
    cmd = cmd + ' && cd %s' % (commands.mkarg(chdir))
  # end if

  if limitcore != None:
    cmd = cmd + ' && ulimit -c %d' % limitcore
  # end if

  if limitfiles != None:
    cmd = cmd + ' && ulimit -n %d' % limitfiles
  # end if

  cmd = ('%s && %s %s' % (cmd, JoinUsingMkarg(commandline), output))
  # The innermost alarm kills the process on the remote machine; the outer
  # alarm protects against network faults.
  
  if alarmtime:
    cmd = '%s %s %d sh -c %s' % (ralarmpath, alarmargs, alarmtime,
                                 commands.mkarg(cmd))
  # end if

  # the ssh command
  cmd = '%s %s %s%s %s' % (sshpath, sshargs, user, machine,
                           commands.mkarg(cmd))
  if alarmtime:
    cmd = '%s %s %d sh -c %s' % (lalarmpath, alarmargs, alarmtime,
                                 commands.mkarg(cmd))
  # end if

  if console:
    cmd = '%s -T %s -e %s' % (console, machine, cmd) # no mkarg, xterm/konsole use exec()
  # end if

  logging.debug('running: %s' % cmd)
  return cmd

def RunRemoteBackgroundProcess(machine, commandline, *args, **kwargs):
  """
  Given a single machine and a commandline formatted either as a
  string (if you use command.mkarg() yourself) or as a list of
  strings, starts execution of that command on that machine.  The
  process can be waited for, and its return status obtained, by
  calling close() on the returned object.

  Accepts arguments in the style of RemoteCommandString().

  Returns an opaque object with a close() method and, if "output" is
  true, a read() method.  Close() returns None if the command
  succeeds, otherwise it returns an error status.
  """

  assert not args # TODO: args exists only to placate a buggy pychecker

  return os.popen(RemoteCommandString(machine, commandline, **kwargs), 'r')

def RunRemoteForegroundProcess(machine, commandline, *args, **kwargs):
  """
  Just like RunRemoteBackgroundProcess() except that we wait for the
  command to finish execution before returning.

  Returns the exit status if the "output" keyword is not present or false.
  Returns a (status, output) tuple if the "output" keyword is true.
  """

  assert not args # TODO: args exists only to placate a buggy pychecker
  f = RunRemoteBackgroundProcess(machine, commandline, **kwargs)
  # note that the return value of f.close() on a popen()ed file object is
  # the return status of the process.
  if kwargs.get('output', 0):
    data = f.read()
    return (f.close(), data)
  else:
    return f.close()
  # end if
# end def

def RunRemoteProcessesInSynchronousPool(machines, cmds, *args, **kwargs):
  """
  Runs commands simultaneously but with a bounded poolsize.  Machines
  is a list of machines and commands is either a single commandlist to
  be run on all machines or it is a list of commandlists such that
  machines[i] should run commands[i].

  Keywords: "alarm" sets an alarm timeout, "cd" changes
  directory to the same directory on all machines, and "poolsize" uses
  a poolsize other than the default.

  Returns a map from machine name to (status, stdout, stderr).
  """

  assert not args # TODO: args exists only to placate a buggy pychecker
  cmdtype = type(cmds[0])
  if cmdtype == types.TupleType or cmdtype == types.ListType:
    assert len(machines) == len(cmds)
    mach_pairs = map(None, machines, cmds)
  else:
    mach_pairs = map(lambda m, c=cmds: (m, c), machines)
  # end if
  user = ''
  poolsize = 20
  alarmtime = 3600 * 24 * 365 # 1 year is "forever" for us
  cd = ''
  if kwargs:
    for key in kwargs.keys():
      if 'alarm' == key and kwargs[key]:
        alarmtime = int(kwargs[key])
      elif 'cd' == key and kwargs[key]:
        dir = kwargs[key]
        if dir:
          cd = 'cd %s &&' % dir
        # end if
      elif 'poolsize' == key and kwargs[key]:
        poolsize = kwargs[key]
      elif 'user' == key and kwargs[key]:
        user = '%s@' % kwargs[key]
      else:
        raise Exception, 'no such keyword argument: %s' % (key)
      # end if
    # end for
  # end if
  mach_pairs = map(lambda mc, a=alarmtime, c=cd:
                   ('%s%s' % (user, mc[0]),
                    ('. /etc/profile; %s alarm %d %s' %
                     (c, a, JoinUsingMkarg(mc[1])))),
                    mach_pairs)
  if mach_pairs:
    return prodlib.ForkRemoteCommandPool(mach_pairs, alarmtime,
                                         min(poolsize, len(mach_pairs)),
                                         print_pool_size=0,
                                         use_x11=0)
  # end if
  return {}

class ExitException(Exception):
  def __init__(self, status):
    Exception.__init__(self)
    self.status_ = status
  # end def
  def status(self):
    return self.status_
# end class

class BackgroundProcess:
  """
  Python threads don't work so well.  We fork a new process to execute
  runnable.Run().  If an alarm is set, we fork another process to
  perform the timeout.  Join() returns the unpickled return value of
  runnable.Run(), or raises the unpickled exception of runnable.Run(),
  as appropriate.
  """

  def __init__(self, runnable, *args, **kwargs):
    """
    Start to execute runnable.Run() asynchronously.  If the "alarm"
    keyword is set, the process will be killed and Join() will return
    gexcept.TimeoutException after the specified number of seconds.
    "stdin", "stdout", and "stderr" keywords may be specified as
    follows: default is to close the stream; if set to a false value,
    the stream is simply a copy of the parent's stream; other values
    are reserved for future use.
    """

    assert not args # TODO: args exists only to placate a buggy pychecker
    assert not kwargs.get('stdin', None) # reserve for future use
    assert not kwargs.get('stdout', None) # reserve for future use
    assert not kwargs.get('stderr', None) # reserve for future use

    # the following apparently corrects a Python bug: if stdout is
    # redirected to a file and the subprocess prints, buffered data
    # is printed more than once.
    sys.stdout.flush()

    (readval, writeval) = os.pipe() # return value is transferred here
    pid = os.fork()
    if pid == 0:
      # then we are the child
      if not kwargs.has_key('stdin' ): os.close(0)
      if not kwargs.has_key('stdout'): os.close(1)
      if not kwargs.has_key('stderr'): os.close(2)
      # one-way communication from child to parent
      self._CloseFileDescriptors(3, butnot=writeval)
      valfile = os.fdopen(writeval, 'w')
      try:
        result = runnable.Run()
        try:
          valfile.write('R')
          pickle.dump(result, valfile)
        except:
          os._exit(99)
        # end try
      except:
        valfile.write('E')
        (cl, exc, traceobj) = sys.exc_info()
        fil = StringIO.StringIO()
        traceback.print_exc(None, fil)
        pickle.dump((cl, exc, fil.getvalue()), valfile)
      # end try

      # this valfile.close() could be writing to a dead socket,
      # so ignore any failure: if the parent isn't reading then
      # the error isn't very important.
      try:
        valfile.close()
      except:
        pass
      # end try
      os._exit(0)
    else: # we're the original process
      os.close(writeval)
      self.readval = readval
      fcntl.fcntl(self.readval, fcntl.F_SETFL, os.O_NONBLOCK)
      self.pid = pid
      self.apid = 0 # no alarm yet
      alarm = kwargs.get('alarm', 0)
      if alarm:
        apid = os.fork()
        if 0 == apid:
          self._CloseFileDescriptors(0)
          start = time.time()
          while (time.time() - start) < alarm:
            time.sleep(1 + alarm - (time.time() - start))
          # end while
          self.Stop()
          os._exit(0)
        else:
          self.apid = apid
        # end if
      # end if
    # end if
    return

  def Stop(self, signal=15):
    """Stop the runnable by sending it a signal."""
    if self.pid < 0:
      raise Exception, 'already stopped'
    # end if
    os.kill(self.pid, signal)
    if self.apid:
      try:
        os.kill(self.apid, signal)
      except OSError:
        pass
      # end try
    # end if
    time.sleep(1)
    try:
      os.kill(self.pid, 9)
    except OSError:
      pass
    # end try
    return

  def Join(self, timeout=-1):
    """
    Wait for the runnable to complete.  Throws gexcept.TimeoutException
    if timeout was reached before the runnable completed.  If timeout is
    negative, we wait forever.
    """
    if self.pid < 0:
      raise Exception, 'already stopped'
    # end if
    if timeout < 0:
      (readers, writers, errs) = select.select([self.readval], [], [])
      assert readers
    else:
      (readers, writers, errs) = select.select([self.readval], [], [], timeout)
      if not readers:
        raise gexcept.TimeoutException
      # end if
    # end if
    buffer = ''
    while 1:
      try:
        thistime = os.read(self.readval, 8192)
        if not thistime:
          break
        # end if
        buffer += thistime
      except OSError, (err, m):
        if errno.EAGAIN != err:
          raise
        # end if
      # end except
    # end while
    os.close(self.readval)
    (pid, status) = os.waitpid(self.pid, 0)
    assert pid == self.pid
    if self.apid:   # then kill the alarm and wait for it
      try:
        os.kill(self.apid, 15)
      except OSError:
        pass
      # end try
      (apid, astatus) = os.waitpid(self.apid, 0)
      assert apid == self.apid
    # end if
    if os.WIFSIGNALED(status):
      raise gexcept.TimeoutException
    else:
      assert os.WIFEXITED(status)
    # end if
    self.exitstat = os.WEXITSTATUS(status)
    if not buffer:
      raise ExitException(self.exitstat)
    # end if
    obj = pickle.loads(buffer[1:])
    typ = buffer[0]
    if   'E' == typ:
      raise gexcept.NestedException(obj)
    elif 'R' == typ:
      return obj
    else:
      raise Exception, 'unknown return %s' % buffer
    # end if
  # end def

  # don't call this at home
  def _CloseFileDescriptors(self, start, butnot=-1):
    for n in range(start, 100):
      try:
        if n != butnot:
          os.close(n)
        # end if
      except:
        pass
      # end try
    # end for
    return
# end class

BLOCKING = 1
NON_BLOCKING = 0

def RunFunctionInChildProcess(func_control, *args, **kwargs):
  """
  Args:
    func_control: tuple - consists of:
      (function, : Any callable object.
       timeout,  : Timeout in seconds (zero means no timeout)
       blocking  : if BLOCKING, run synchronously and return the value of the
                   function call, if NON_BLOCKING, return the process object
                   without calling 'Join'.
       and optionally:
       open_fds  : bool - if True then keep stdout and stderr open. Otherwise
                   close them. Defaults to False. This tuple member can be
                   omitted altogether.
      )
                 These arguments must be passed in as a single 
                 tuple to allow the remainder of the arguments
                 to this RunFunctionInChildProcess to be treated
                 as arguments to 'function'.  

    *args, **kwargs:     any positional and keyword arguments to be passed
                         to 'function'.

  Returns:
    if blocking:
      returns the value of function(*args, **kwargs)
    else:
      an instance of process.BackgroundProcess

  RunFunctionInChildProcess is used to run any function in a seperate 
  python interpreter, with a minimum of fuss.  This is useful when
  you wish to run a piece of code in parallel with the current process, 
  when you wish to guard a function with a timeout, or in certain circumstances
  when a function cannot be run within the current process (e.g. running
  a function that uses signal.signal from a child thread).

  Obviously, if the function to be run wishes to alter in place any of the
  arguments passed to it, RunFunctionInChildProcess is a non-starter.
  """
  class FunctionRunnable:
    def __init__(self, callable, f_args, f_kwargs):
      self.function = callable
      self.args = f_args
      self.kwargs = f_kwargs
    # end def

    def Run(self):
      return self.function(*self.args, **self.kwargs)
    # end def
  # end class

  try:
    function, timeout, blocking, open_fds = func_control
  except ValueError:
    open_fds = False
    function, timeout, blocking = func_control

  new_runnable = FunctionRunnable(function, args, kwargs)

  if open_fds:
    bg_process = BackgroundProcess(new_runnable, alarm=timeout, stdout=False,
                                   stderr=False)
  else:
    bg_process = BackgroundProcess(new_runnable, alarm=timeout)

  if blocking == BLOCKING:
    return bg_process.Join()
  else:
    return bg_process
  # end if
# end def

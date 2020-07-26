#!/usr/bin/python2.4

# Copyright(c) Google 2000 onwards
# Original Author: ???
# this library contains commonly-used production code

import commands
import getopt
import os
import popen2
import random            # for OpenRemoteFile
import re
import select              # for Fork* functions
import signal              # for SIGCONT value
import socket              # for DNS lookups
import string
import sys
import tempfile
import time
import traceback           # for format exception

# Constants:

# callback actions:
CONTINUE = 0
GRACEFUL_ABORT = 1

if os.path.isdir('/root/google'):
  BASEDIR = '/root/google'
else:
  BASEDIR = '/home/build/public/google'

if os.path.isdir('/root/google3'):
  BASE_GOOGLE3_DIR = '/root/google3'
else:
  BASE_GOOGLE3_DIR = '/home/build/public/google3'

verbose = 0
ident_func = lambda x: x     # the identity function


# exception classes
class Error(Exception):
  pass


class FileWriteError(Error):
  def __init__(self, filename, error_string):
    self.__filename = filename
    self.__error_string = error_string

  def filename(self):
    return self.__filename

  def error_string(self):
    return self.__error_string



# easy class to send mails with
class MailTo:

  # to,cc are a list of email addresses
  # subject is a string
  # sig is the signature string
  # in the absence of the signature string, the user name is appened
  # time is in the format sent out in mails (RFC ???)

  def __init__(self,to,cc,subject,bcc=[],replyto='',sig=''):
    self.sender  = self.IdentifyUser()
    # to be compatible with the current revision
    if type(to) == type([]): self.to = string.join(to,',')
    else:                    self.to = to
    if type(cc) == type([]): self.cc = string.join(cc,',')
    else:                    self.cc = cc
    if type(bcc) == type([]): self.bcc = string.join(bcc,',')
    else:                    self.bcc = bcc
    if replyto: self.replyto = replyto
    else:       self.replyto = self.sender
    self.subject = subject
    self.time    = time.strftime('%a, %d %b %Y %H:%M:%S %Z',
                                 time.localtime(time.time()))
    self.sig = sig
    self.message = ''
    return

  def __repr__(self):
    print 'From: %s@google.com' % self.sender
    print 'To: %s' % self.to
    print 'Date: %s'  % self.time
    print 'Subject: %s' % self.subject
    print 'Reply-To: %s' % self.replyto
    print self.message
    return

  def IdentifyUser(self):
    id = 'unknown'
    if os.environ.has_key('USER'):         id = os.environ['USER']
    elif os.environ.has_key('LOGNAME'):    id = os.environ['LOGNAME']
    elif os.environ.has_key('REMOTENAME'): id = os.environ['REMOTENAME']
    return id

  def Add(self,message,newline='true'):
    self.message = self.message + message
    if newline:  self.message = self.message + '\n'

  def Send(self):
    contents = 'From: %s\nTo: %s\nSubject: %s\nReply-To: %s\nDate: %s\n'%\
      (self.sender,self.to,self.subject,self.replyto,self.time)
    if self.cc:  contents = contents + 'Cc: %s\n' % self.cc
    if self.bcc: contents = contents + 'Bcc: %s\n' % self.bcc

    # separate contents from headers by blank lines otherwise
    # contents containing : are treated as headers
    contents = contents + '\n\n'
    contents = contents + self.message + self.sig

    sendmail = os.popen('/usr/sbin/sendmail -oem -t -i ','w')
    sendmail.write(contents)
    sendmail.close()
    return

# output to stdout.
# If msg is a tuple, then don't append the newline (this is really just
# a replacement for print).
def out(msg):
  sys.stdout.write("%s\n" % msg)

######
# NOTE: prodlib.log should no longer be used. Instead, import prodlog
# and use the methods there.  That will give you the added benefit of
# using the google-compliant pyglib.logging when pyglib is available
# but old-fashioned logging when it is not.
######
# (unbuffered, timestamped, logging function)
def log(msg):
  sys.stderr.write("[%s] %s\n" % (time.ctime(time.time()), msg))

# redirect stderr so that log calls write to a log file
def SetupLogFile(logfile):
  try:
    fd = os.open(logfile, os.O_CREAT|os.O_WRONLY|os.O_APPEND, 0666)
    os.dup2(fd, 2)        # close and replace stderr
  except OSError, e:
    log("Failed to redirect stderr: %s" % e)
    sys.exit(20)

# logtrace
# same as log except it also prints the exception and the optional second
# argument which is supposed to be a stack trace using
# traceback.format_stack()
# This should be used inside except: handlers.
def logtrace(str, stack=None):
  (type,value,tb) = sys.exc_info()
  ex = traceback.format_exception(type,value,tb)
  if stack == None:
    stack = []
  log(str + string.join(ex) + string.join(stack))



# utility functions:
def ExceptionTracebackToString():
  """ Returns a stack trace of the last exception that was raised
  as a string.
  Args:
    none
  Returns:
    a string if there was an exception. An empty string is returned
    if there was no exception.
  Throws:
    nothing.
  """

  (exc_type, exc_value, exc_tb) = sys.exc_info()
  if (None, None, None) == (exc_type, exc_value, exc_tb):
    return ''
  else:
    return string.join(traceback.format_exception(exc_type, exc_value, exc_tb))



def AtomicWrite(final_filename, data, log_method=log):
  """ This method will write data in data to a temp file,
  and then atomically move it to final_filename.
  Args:
    final_filename: string, absolute path
    data: string, data to be written
    log_method: function reference to a logging function that takes in a single
                parameter(string) and does something with it.
                Could be lambda _ : None for no logging.

  Returns:
    Nothing

  Throws:
    prodlib.FileWriteError upon failure
  """

  fn = tempfile.mktemp()
  # write the data out to the file
  try:
    fd = open(fn, 'w')
    fd.write(data)
    fd.close()
  except (OSError, IOError), e:
    raise FileWriteError(fn, str(e))

  log_method('prodlib.AtomicWrite: data written to temp file %s' % fn)
  try:
    os.rename(fn, final_filename)
  except (OSError, IOError), e:
    raise FileWriteError(final_filename, str(e))
  log_method('prodlib.AtomicWrite: successfully copied to %s' % final_filename)



# runs a remote cmd wrapped in an "alarm" statement
# If timeout<0, disable alarm
def RunAlarmRemoteCmd(mach, cmd, timeout, remote_user=None):
  if timeout < 0: # alarm disabled
    alarm_cmd = ""
  else:
    alarm_cmd = "alarm %s " % timeout

  # prepend AM user
  if remote_user:
    remote_string = "%s@" % remote_user
  else:
    remote_string = ""


  entire_cmd = (". /etc/profile; %s ssh -q -P -n -o 'BatchMode=yes' "
                "-o 'ForwardAgent=yes' -o 'StrictHostKeyChecking=no' %s%s %s" %
                (alarm_cmd, remote_string, mach, commands.mkarg(cmd)))

  if verbose:
    log("Running %s " % entire_cmd)
  try:
    (status, output) = commands.getstatusoutput(entire_cmd)
    if status:
      (status, sig) = (status >> 8, status & 255)  # separate high (status)
                                                   # and low byte (signal)
    else:
      (status, sig) = (0, 0)
  except OSError, e:
    (status, sig, output) = (e.errno, 0, '')

  return (status, sig, output)

# runs a local cmd wrapped in an "alarm" statement
# If timeout<0, disable alarm
def RunAlarmCmd(cmd, timeout):
  if timeout < 0: # alarm disabled
    alarm_cmd = ""
  else:
    alarm_cmd = "alarm %s " % timeout
  entire_cmd = ". /etc/profile; %s %s" % (alarm_cmd, cmd)

  if verbose:
    log("Running: %s" % entire_cmd)
  try:
    InitPool(1)    # make sure we catch (and drop) the TTY signals
    (status, output) = commands.getstatusoutput(entire_cmd)

    if status:
      (status, sig) = (status >> 8, status & 255)  # separate high (status)
                                                   # and low byte (signal)
    else:
      (status, sig) = (0, 0)
  except OSError, e:
    (status, sig, output) = (e.errno, 0, '')

  return (status, sig, output)

# runs a local _shell_ cmd wrapped in an "alarm" statement. We really
# need sh -c because of interference between alarm's execve and the
# shell cmd itself (we can't find the path basically)
def RunAlarmShCmd(cmd, timeout):
  return RunAlarmCmd("sh -c %s" % commands.mkarg(cmd), timeout)


# Run*CmdOrDie Wrappers.  Same as the above, but if
# return status is non-zero, die with a message.
# Note: if signal occured but return status is 0,
#       it is considered successful run.
# Note2: the extra () in CheckRunCmdOrDie(()) is necessary
#        because RunAlarm*Cmd returns a tuple and
#        CheckRunCmdOrDie checks based on the returned tuple
def CheckRunCmdOrDie( (status, sig, output), cmd, timeout):
  if status: # die on error
    log("Error in cmd "
        "[%s]: status=%s, sig=%s, output=[%s], timeout=%s" %
        (cmd, status, sig, output, timeout))
    sys.exit(status)
  else:
    return (status, sig, output)

def RunAlarmRemoteCmdOrDie(mach, cmd, timeout):
  return CheckRunCmdOrDie(RunAlarmRemoteCmd(mach, cmd, timeout),
                          mach+':'+cmd, timeout)

def RunAlarmCmdOrDie(cmd, timeout):
  return CheckRunCmdOrDie(RunAlarmCmd(cmd, timeout), cmd, timeout)

def RunAlarmShCmdOrDie(cmd, timeout):
  return CheckRunCmdOrDie(RunAlarmShCmd(cmd, timeout), cmd, timeout)


# Given a types dictionary, it separates the entries based on their
# spec type. Entries like 'index', 'doc' etc. are considered "wanted",
# entries like '-doc' are not
def SplitTypeSpecs(types):
  wanted = {}
  notwanted = {}
  for maptype in types.keys():
    if maptype[0] == '-':
      notwanted[maptype[1:]] = 1        # negative spec
    else:
      wanted[maptype] = 1               # positive

  return (wanted, notwanted)


# Given a type and a list of types and negatives ("-index == all but
# index"), I return true or false depending if the type should be kept
# or not
def WantedType(mtype, types):
  if not types:
    return 1        # if type list is empty ... we want everything

  if string.find(mtype, ':') == -1:
    mtype = "%s:0" % mtype   # assume L0 if type not specified

  # separate types based on their spec (index or -index)
  (wanted, notwanted) = SplitTypeSpecs(types)

  lvl = 0
  fields = string.split(mtype, ':')
  if len(fields) > 1:
    lvl = fields[1]

  if notwanted.has_key(mtype):
    return 0
  if wanted.has_key('all:%s' % lvl):
    return 1
  if not wanted.has_key(mtype):
    return 0
  if notwanted.has_key('all:%s' % lvl):
    return 0

  # all other are OK to keep.
  return 1


# COLLECT_TYPE
#   map a list of types so we can use them as filters. Input like
#   "index,-doc,5600" means "all index, no doc, all link". We take
#   into account levels too. If not specified all regular types are
#   considered part of level 0.  At some point, we will deprecate the
#   use of levels in type specing (we will never have multiple levels
#   in the same config file).  At that point this code can be vastly
#   simplified.  Note that although there is support for the "level"
#   hack below, this code can be used quite generically for "string"
#   matching.  The only caveats are that type names cannot have ':'
#   in them and a type cannot be named 'all'.

def CollectTypes(typelist, types):
  if type(typelist) != type([]):
    typelist = string.split(typelist, ',')

  for t in typelist:
    if string.find(t,':') == -1:
      t= "%s:0" % t   # assume L0 for all types where level is not specified
    types[t]=1

  (wanted, notwanted) = SplitTypeSpecs(types)
  if not wanted:                   # if positive list is empty ...
    for lvl in xrange(0,3):        # ... we assume 'all' for all levels ...
      allpat = "all:%s" % lvl
      if not notwanted.has_key(allpat):  # ... but only if no conflicts
        types[allpat] = 1
        wanted[allpat] = 1         # update wanted list for the conflict check

  # check if there are no conflicts
  crosslist = filter(lambda t, w=wanted.keys(): t in w, notwanted.keys())
  if crosslist:                    # any conflicts?
    for chktype in crosslist:
      log("Conflicting type specifications: %s and -%s" % (chktype, chktype))
    raise NameError                # can't continue anyway

  return types

############################################################################
##              Example Callback function for Fork* commands
##              ============================================
##
## NB: your callback function should be relatively quick. If it takes too
##     long the interval between reading from sockets may become too long,
##     resulting in screwed up commands.
##
##     This callback function MUST return either CONTINUE or GRACEFUL_ABORT.
##
##     If the callback function throws an exception, it will propagate out to
##     the calling function.
##
## def CallBackExample(key, status, stdout, stderr):
##   """ This is a callback function.
##   Args:
##     key: the key which the caller provided to the Fork* command
##     status: status of the process
##     stdout: standard out of the process which terminated
##             (['line1', 'line2', ...])
##     stderr: standard error of the process which terminated
##             (['line1', 'line2', ...])
##     """
##   if ThingsAreOk():
##      return prodlib.CONTINUE
##   else:
##      return prodlib.GRACEFUL_ABORT
##
############################################################################


# FORK_REMOTE_COMMANDS
#  Uses a slot pool to run the same command on a list of machines, in parallel.
#  Returns: a map hashed by machine with (status, stdout, stderr) tuples.
#           where stdout and stderr are a list of lines printed to each
#           stdout and stderr.
#
#  callback_fcn is a function which looks like the example provided above
#               it accepts key, status, stdout and stderr, and returns
#               either prodlib.CONTINUE, or prodlib.GRACEFUL_ABORT, which
#               causes prodlib to stop sending additional commands.

def ForkRemoteCommands(machines, cmd, timeout, numslots,
                       retrycnt=0, machname=ident_func,
                       print_pool_size=1, remote_user=None,
                       fallback_user=None, sudo=0, callback_fcn=None):
  machcmds = []
  for m in machines:
    machcmds.append( (m, cmd) )  # build tuple list for ForkRemoteCommandPool

  return ForkRemoteCommandPool(machcmds, timeout, numslots,
                               'ssh', retrycnt, machname,
                               print_pool_size=print_pool_size,
                               remote_user=remote_user,
                               fallback_user=fallback_user, sudo=sudo,
                               callback_fcn=callback_fcn)

# FORK_COMMANDS
#  Uses a slot pool to run a list of commands on local machine, in
#  parallel. The commands are provided as a list of (id, cmd) tuples.
#  Returns: a map hashed by id with (status, stdout, stderr) tuples.
#           where stdout and stderr are a list of lines printed to each
#           stdout and stderr.
#
#  callback_fcn is a function which looks like the example provided above
#               it accepts key, status, stdout and stderr, and returns
#               either prodlib.CONTINUE, or prodlib.GRACEFUL_ABORT, which
#               causes prodlib to stop sending additional commands.

def ForkCommands(machcmds, timeout, numslots,
                 retrycnt=0, machname=ident_func, print_pool_size=1,
                 remote_user=None, callback_fcn=None):

  return ForkRemoteCommandPool(machcmds, timeout, numslots,
                               '', retrycnt, machname, print_pool_size,
                               remote_user, callback_fcn=callback_fcn)

# FORK_SH_COMMANDS
#  Uses a slot pool to run a list of commands on local machine, in
#  parallel. Identical with ForkCommands except it wraps commands in a
#  sh -c to protect shell-like scripts
#  Returns: a map hashed by machine with (status, stdout, stderr) tuples.
#           where stdout and stderr are a list of lines printed to each
#           stdout and stderr.
def ForkShCommands(machcmds, timeout, numslots,
                   retrycnt=0, machname=ident_func, remote_user=None,
                   callback_fcn=None):
  return ForkRemoteCommandPool(machcmds, timeout, numslots,
                               'sh', retrycnt, machname,
                               remote_user=remote_user, callback_fcn=callback_fcn)


def sigttou(signum, frame):
  # cancel the STOP signal
  os.kill(-os.getpgrp(), signal.SIGCONT)
  # popen catches + ignores this
  raise OSError, (4, 'Interrupted system call (SIGTTOU)')

bgio_handler_registered = 0
def RegisterBackgroudIOHandler():
  global bgio_handler_registered
  # catch SIGTTOU and SIGTTIN signals which send SIGSTOP to current
  # process group (so we can SIGCONT ourselves)
  if not bgio_handler_registered:
    signal.signal(signal.SIGTTIN, sigttou)
    signal.signal(signal.SIGTTOU, sigttou)
    bgio_handler_registered = 1

# INIT_POOL
#  setup a resource pool for multiprocessing
# We want to register singal only once. This is because
# we can't register signal in python threads other than the main thread.
def InitPool(numslots):
  RegisterBackgroudIOHandler()
  forkpool = []
  for slot in xrange(0, numslots):
    forkpool.append(slot)
  return forkpool

# FILESET_MULTI_READ
#  Given a set of files, reads available output from them until either no
#  output remains, or a given number of iterations have been performed.  If
#  a negative number of max_iterations is passed, the files are read until
#  exhaustion.  Returns a file->output map.
def FilesetMultiRead(files, max_iterations=1):
  # initialize fd->output map and fdset map
  fileset = {}
  output  = {}
  for file in files:
    output[file]  = ''
    fileset[file] = None

  # the funky chicken dance; second variation ---
  # suck out output from the given files
  while max_iterations:
    max_iterations  = max_iterations - 1
    (ioready, _, _) = select.select(fileset.keys(), [], [], 0)  # non-blocking

    # suck out output from files that have them
    nonempty_reads = 0
    for file in ioready:
      try:
        # read up to 4k of data (default size of IO buffer so larger
        # reads won't help anyway) and save it in the appropriate
        # result string if nonempty
        buf = os.read(file.fileno(), 4096)
        if buf:
          output[file] = output[file] + buf
          nonempty_reads = nonempty_reads + 1
      except IOError, e:
        log("Read error %s for file %s, fd %d" % (e.args, file, file.fileno()))
        del fileset[file]  # don't consider this file again

    # we're done if we didn't have any non-empty reads
    if nonempty_reads == 0:
      return output

  # done
  return output


# FORK_REMOTE_COMMAND_POOL
#  Uses a slot pool to run commands in parallel. Takes a list of
#  tuples (mach, cmd) and runs the specified command on each machine.
#  Returns: a map hashed by machine with (status, stdout, stderr) tuples.
#           where stdout and stderr are a list of lines printed to each
#           stdout and stderr.
#
# remote_user - The user account to ssh to.  If not specified, then
# no user is passed and the ssh defaults to using the current account.
#
# sudo - if specified, remote commands will be wrapped in sudo sh -c.
#
# fallback_user - This is for AM transitional purposes and should be used
# only for this purpose.  If fallback_user is specified and remote_user is
# specified, a test is done to see whether the machine is accessible
# as that user with appropriate AM privileges.  If this test is false,
# then the ssh command is run without a username specified (generally
# useful for root fallback).
#
#
#  callback_fcn is a function which looks like the example provided above
#               it accepts key, status, stdout and stderr, and returns
#               either prodlib.CONTINUE, or prodlib.GRACEFUL_ABORT, which
#               causes prodlib to stop sending additional commands.

def ForkRemoteCommandPool(machcmds, timeout, numslots,
                          shuse='ssh', retrycnt=0, machname=ident_func,
                          print_pool_size=1, remote_user=None,
                          use_x11=1, fallback_user=None, sudo=0,
                          callback_fcn=None):

  # If the user and fallback_user are specified, test if we can access the
  # remote machine as the user in our new AM world with the proper permissions.
  # If things are not OK, try falling back to userless ssh (probably
  # as root).  Also in this case don't sudo anything at all.  This is
  # helpful when we're still running our "global" apps as root - when
  # we stabilize on AM we can move these to run more appropriately
  # as prodadmin or prodsetup or whatever.

  fallback_results = {}
  if remote_user and fallback_user and shuse == 'ssh':

    # Find list of hosts.
    host_machcmds = {}
    for (machidx, cmd) in machcmds:
      host = machname(machidx)
      host_machcmds[host] = host_machcmds.get(host, [])
      host_machcmds[host].append((machidx, cmd))

    # Test that cap_read is running and the capabilities file exists.
    cmd = ('test -n "$(ps ax | grep cap_read | grep -v grep)" && '
           'test -e /etc/capabilities')
    # Perform access test.
    test_timeout = min(timeout, 60)
    #
    results = ForkRemoteCommands(host_machcmds.keys(), cmd, test_timeout,
                                 numslots=numslots, remote_user=remote_user,
                                 callback_fcn=None)

    machcmds = []
    fallback_machcmds = []
    fallback_hosts = []
    for host, (status, output, error) in results.items():
      if status:
        fallback_machcmds.extend(host_machcmds[host])
        fallback_hosts.append(host)
      else:
        machcmds.extend(host_machcmds[host])

    # Run without a user for the fallback commands.
    if fallback_machcmds:
      # note that aborting from a callback when using a fallback user will
      # not work correctly; they will only abort the fallback commands :-/

      log('Fallback access for: %s' % string.join(fallback_hosts))
      fallback_results = ForkRemoteCommandPool(fallback_machcmds, timeout,
                           numslots, shuse=shuse, retrycnt=retrycnt,
                           machname=machname, print_pool_size=print_pool_size,
                           remote_user=fallback_user, fallback_user=None,
                           sudo=0, use_x11=use_x11, callback_fcn=callback_fcn)

  forkpool = InitPool(numslots)
  if not forkpool:
    log("Fork pool is empty. numslots must be > 0.")
    return {}
  else:
    # if somebody called us with numslots of 1 then he probably doesn't
    # want to know about poolsizes
    if print_pool_size and numslots > 1:
      log("Using a %s slot pool." % len(forkpool))

  # prepend AM user
  if remote_user:
    remote_string = "%s@" % remote_user
  else:
    remote_string = ""

  machpipe = {}
  iopipes = {}
  results = {}      # holds the (status, output, errors) pairs hashed by mach
  rawresults = {}   # holds the "stdout"/"stderr"->"output string" map
  attempts = {}     # hash by machine holding the retry counts
  while machpipe or machcmds:
    if machcmds and forkpool:    # any machines left? Then ...
      try:
        slot = forkpool.pop()             # grab a slot
        (machidx, cmd) = machcmds.pop(0)  # get the machine and the cmd
        mach = machname(machidx)          # extract the actual machine name
      except IndexError:
        assert 0, "Hmmm. Neither forkpool or machines should be empty"

      if shuse == 'ssh':                      # use ssh. Remote exec.
        if use_x11:
          disallow_x11 = ''
        else:
          disallow_x11 = '-x '
        if sudo and remote_user != 'root':
          cmd = 'sudo %s' % commands.mkarg('sh -c %s' % commands.mkarg(cmd))
        else:
          cmd = commands.mkarg(cmd)

        pcmd = (". /etc/profile; alarm %s ssh %s -q -P -n "
                "-o 'BatchMode=yes' -o 'ForwardAgent=yes' "
                "-o 'StrictHostKeyChecking=no'     %s%s %s"
                % (timeout, disallow_x11, remote_string, mach, cmd))
      elif shuse == 'sh':                     # use sh. Local exec.
        pcmd = ". /etc/profile; alarm %s sh -c %s" % \
               (timeout, commands.mkarg(cmd))
      else:                                   # no sh at all. Local exec.
        pcmd = 'alarm %s %s' % (timeout, cmd)

      if verbose:
        log("Running cmd %s on %s using slot %s" % (pcmd, mach, slot))
      childpipe = popen2.Popen3(pcmd, 'true')   # true means "capture stderr"
      childpipe.tochild.close()                 # close child's stdin

      machpipe[machidx] = (childpipe, slot, cmd)
      attempts[machidx] = attempts.get(machidx, 0) + 1  # update retry cnt
      rawresults[machidx] = { "stdout": '', "stderr": ''}

      # save the stdout/stderr pipes too so we can select() on them.
      iopipes[childpipe.fromchild] = ("stdout", machidx, childpipe)
      iopipes[childpipe.childerr] = ("stderr", machidx, childpipe)
    else:
      # no pool resources. Waiting for better times.
      time.sleep(1)

    # play the "Funky Chicken Dance": we need to collect all fds and
    # read data from them periodically (via select). This is because
    # the pipes can fill up *before* the child completes which will
    # result in a big and ugly hanging of the whole thing.  Note that
    # we don't do an exhastive read here because that can result in
    # not repopulating the slotpool after process completions
    # if one or more processes are continuously spewing output
    outputmap = FilesetMultiRead(iopipes.keys())
    for file, outputlines in outputmap.items():
      (iotype, machidx, mp) = iopipes[file]
      # save data back
      # NOTE: because we save the data in raw format and also split it
      #       later (so the user gets nice lists of per-line outputs),
      #       this risks wasting RAM! Better than hanging the process,
      #       I guess.
      rawresults[machidx][iotype] = rawresults[machidx][iotype] + outputlines

    # see if anyone finished
    for machidx, (mp, slot, cmd) in machpipe.items():
      status = mp.poll()

      if status != -1:
        # helper function for splitting output strings. We use "del"
        # instead of string.strip to preserve memory.
        def SplitOutput(outputstr):
          output = string.split(outputstr, '\n')
          if output[-1] == '':      # did string.split generate a bogus "line"?
            del output[-1]          # ... then drop it
          return output

        # a terminated child may have generated output after we passed the
        # select above; harvest any remaining output now.  Pass in a negative
        # number for max number of iterations to read to exhaustion
        outputmap = FilesetMultiRead( [ mp.fromchild, mp.childerr ], -1 )

        rawoutput = rawresults[machidx]              # fetch output
        output = SplitOutput(rawoutput['stdout'] + outputmap[mp.fromchild])
        errors = SplitOutput(rawoutput['stderr'] + outputmap[mp.childerr])
        status = status >> 8                         # keep only actual status
        results[machidx] = (status, output, errors)  # save status and output

        if status != 0 and retrycnt and attempts[machidx] < retrycnt:
          # cmd failed and user requested retries and we did not reach
          # the retry limit. So we push the mach/cmd pair back in the
          # loop to be reexecuted.
          if verbose:
            log('cmd for %s failed (%s). Retrying %s more times' %
                (str(machidx), string.join(errors),
                 retrycnt - attempts[machidx]))
          machcmds.append( (machidx,cmd) )

        forkpool.append(slot)                 # ... then release the slot
        del machpipe[machidx]                 # ... and don't wait on it again

        # cleanup
        mp.fromchild.close()
        mp.childerr.close()
        del rawresults[machidx]               # save some RAM ...
        del iopipes[mp.fromchild]             # ... and drop some fds to
        del iopipes[mp.childerr]              #     speedup the select()

        # invoke the callback function and see what we are to do.
        if callback_fcn:
          action_to_perform = callback_fcn(machidx, status, output, errors)

          if action_to_perform == GRACEFUL_ABORT:
            # we want to gracefully abort. We do this by refusing to send any
            # more commands out to remote hosts.
            machcmds = []
          else:
            assert action_to_perform == CONTINUE


  # all cmds finished.
  results.update(fallback_results)
  return results


# FORK_EXEC_POOL
#  Uses a slot pool to run commands in parallel. Takes a list of
#  tuples (mach, cmd) and runs the specified command on each machine.
#  Returns: a map hashed by machine with (status, output[]) tuples.
#
# NOTE: this function is virtually identical to ForkRemoteCommandPool.
# The only difference is the use of fork/system pair instead of popen2
# module. This avoids a bug triggered by the use of rsync and
# stdout/stderr redirection by the popen library. The downside of this
# fix is that we lose the stdout/stderr from the executed command. :-(
#
# TODO: Remove this crap once the new ForkRemoteCommandPool proves stable.
def ForkExecPool(machcmds, timeout, numslots, shuse='ssh', retrycnt=0,
                 remote_user=None):
  forkpool = InitPool(numslots)
  if not forkpool:
    log("Fork pool is empty. numslots must be > 0.")
    return ''
  else:
    log("Using a %s slot pool." % len(forkpool))

  # prepend AM user
  if remote_user:
    remote_string = "%s@" % remote_user
  else:
    remote_string = ""

  machpipe = {}
  results = {}      # this will hold the (status, output) pairs hashed by mach
  attempts = {}     # hash by machine holding the retry counts
  while machpipe or machcmds:
    if machcmds and forkpool:    # any machines left? Then ...
      try:
        slot = forkpool.pop()          # grab a slot
        (mach, cmd) = machcmds.pop(0)  # get the machine and the cmd
      except IndexError:
        assert 0, "Hmmm. Neither forkpool or machines should be empty"

      if shuse == 'ssh':                      # use ssh. Remote exec.
        pcmd = ("%s/enterprise/legacy/setup/alarm %s ssh -q -P -o "
                "'BatchMode=yes' -o 'ForwardAgent=yes' -o "
                "'StrictHostKeyChecking=no'  -n %s%s %s" %
                (BASE_GOOGLE3_DIR, timeout, remote_string,
                mach, commands.mkarg(cmd)))
      elif shuse == 'sh':                     # use sh. Local exec.
        pcmd = ("%s/enterprise/legacy/setup/alarm %s sh -c %s" %
                (BASE_GOOGLE3_DIR, timeout, commands.mkarg(cmd)))
      else:                                   # no sh at all. Local exec.
        pcmd = ('%s/enterprise/legacy/setup/alarm %s %s' %
                (BASE_GOOGLE3_DIR, timeout, cmd))

      if verbose:
        log("Running cmd %s using slot %s" % (cmd, slot))

      childpid = os.fork()
      if childpid == 0:
        try:
          status = 1
          status = os.system(pcmd) >> 8
        finally:
          os._exit(status)

      machpipe[mach] = (childpid, slot, cmd)
      attempts[mach] = attempts.get(mach, 0) + 1  # update retry cnt
    else:
      # no pool resources. Waiting for better times.
      time.sleep(1)

    # see if anyone finished
    for mach, (childpid, slot, cmd) in machpipe.items():
      (pid, status) = os.waitpid(childpid, os.WNOHANG)

      if pid == childpid:  # someone finished
        status = status >> 8                 # keep only the actual status
        results[mach] = (status, [], [])     # save status and output

        if status!=0 and retrycnt and attempts[mach] < retrycnt:
          # cmd failed and user requested retries and we did not reach
          # the retry limit. So we push the mach/cmd pair back in the
          # loop to be reexecuted.
          if verbose:
            log('cmd for %s failed (status: %s). Retrying %s more times' %
                (mach, status, retrycnt - attempts[mach]))
          machcmds.append( (mach,cmd) )

        forkpool.append(slot)                 # ... then release the slot
        del machpipe[mach]                    # ... and don't wait on it again

  # all cmds finished.
  return results

# SENDMAIL : simple sendmail wrapper
def Sendmail(mailto, subject, msg, mailcc=[], mailbcc=[], replyto=[]):
  if not (mailto or mailcc):
    return 1      # return if no recipient

  pipe = MailTo(mailto,mailcc,subject,mailbcc,replyto)
  pipe.Add(msg)
  pipe.Send()

  return 0

#
# OpenRemoteFile - copy a file (that may be remote) to a local tmp file, and
# open it. Returns the open fd and the temp file name (so it can be deleted)
#
# Return is: (rc, (fd, temp_file_name), errmsg)
#
# If rc is 0, then (fd, temp_file_name) are set. If rc is 1, errmsg is set.
#
# The caller should call CloseRemoveFile(fd, temp_file_name) to close the
# file and remove the temp file.
#
# randomize_remote - indicates whether to spread the time of opening the
# file between randomize_low and randomize_high number of seconcds. This is
# so if there are a lot of processes doing this at once they won't beat up
# the source too much.
#
def OpenRemoteFile(file_name, retries=4, timeout=20,
                   randomize_remote=0, randomize_low=3, randomize_high=30,
                   remote_user=None):
  temp_file_name = "/tmp/remotefile.%s" % os.getpid()

  # prepend AM user
  if remote_user:
    remote_string = "%s@" % remote_user
  else:
    remote_string = ""


  while (retries):
    if randomize_remote and ':' in file_name:  # we're going to copy from afar
      time.sleep(random.randint(randomize_low, randomize_high))
    if os.system("alarm %s scp -q %s%s %s" % \
                 (timeout, remote_string, file_name, temp_file_name)):
      retries = retries - 1
    else:
      break
  if not retries:
    return (1, (None, None), 'failed to copy %s to temp file' % file_name)
  else:
    try:
      fd = open(temp_file_name)
    except Exception, e:

      try:
        os.unlink(temp_file_name)
      except OSError:
        pass # Don't freak out over failure to remove file that doesn't exist.

      return (1, (None, None), 'failed opening %s, (local copy of %s): %s' % \
                 (temp_file_name, file_name, e))

    return (0, (fd, temp_file_name), '')

#
# RemoteFileFd - Returns the fd part of the (fd, name) passed in.
#
def RemoteFileFd(fd_and_name):
  return(fd_and_name[0])

#
# CloseRemoteFile - Close fd and remove the temp file from OpenRemoteFile.
#
def CloseRemoteFile(fd_and_name):
  (fd, temp_file_name) = fd_and_name
  try:
    os.unlink(temp_file_name)
  except OSError:
    pass
  fd.close()

# get uid from username
def UserName2UID(username):
  import pwd
  pwname = pwd.getpwnam(username)
  return pwname[2]

# get gid from groupname
def GroupName2GID(groupname):
  import grp
  grname = grp.getgrnam(groupname)
  return grname[2]

# change ownership of the supplied list of files/dirs
# to the numerical uid and gid
def Chown(objects, uid, gid, exit_on_fail=0):
  for obj in objects:
    # set the ownership
    try:
      os.chown(obj, uid, gid)
    except OSError, e:
      log("Failed to set %s ownership: %s" % (obj, e))
      if exit_on_fail:
        sys.exit(1)
      else:
        raise e

# change permission of the supplied list of files/dirs
# to the numerical mode/permission
def Chmod(objects, mode, exit_on_fail=0):
  for obj in objects:
    # set the mode
    try:
      os.chmod(obj, mode)
    except OSError, e:
      log("Failed to set %s permission: %s" % (obj, e))
      if exit_on_fail:
        sys.exit(1)
      else:
        raise e

# Simple checker function to identify full IP specs (used by DNSLookup
# for example, because gethostbyname_ex does not return the extended
# data when applied to IPs)
ipregexp = re.compile(r'(^\d+)\.\d+\.\d+\.\d+$')
def IsIP(name):
  match = ipregexp.match(name)
  return match != None

# Return true for 10.x.x.x ips only
def IsInternalIP(ip):
  """
  Return true if this ip is a 10.0.0.0/8 ip address
  """
  match = ipregexp.match(ip)
  return (match and match.group(1) == "10")


# do an extended DNS lookup on the specified name. Returns a tuple
# like: (fullname, aliaslist, ipaddrlist)
def DNSLookup(name):
  try:
    if IsIP(name):
      (fullname, aliaslist, ipaddrlist) = socket.gethostbyaddr(name)
    else:
      (fullname, aliaslist, ipaddrlist) = socket.gethostbyname_ex(name)
  except socket.error, e:
    log("DNS lookup error for %s: %s" % (name, e))
    return ('', [], [])

  return (fullname, aliaslist, ipaddrlist)


# Determine if we are the main machine, given a dns extension
# for example, given "con.prodz.google.com", AmIMain will prepend
# the coloc, perform the lookup, and return 1 if this resolves to
# the local machine.  If prefix is not None, we will use prefix in lieu
# of LocalColoc()
def AmIMain(dns_extension, prefix=None):
  if prefix is None:
    prefix = LocalColoc()

  dns_alias = "%s%s" % (prefix, dns_extension)
  (main_mach, _, _) = DNSLookup(dns_alias)
  our_hostname = socket.gethostname()
  (our_mach, _, _) = DNSLookup(our_hostname)
  return main_mach == our_mach

# Locate the main babysitter machine based on DNS alias (<coloc>baby.prodz)
# If the babyalias is only two letters then we assume it is a coloc
# specification only and we append the standard suffix.
def FindBabysitterMach(babyalias):

  # Append suffix if we were just passed the coloc name.
  suffix = 'baby.prodz.google.com'
  if len(babyalias) == 2:
    babyalias = babyalias + suffix

  (babyhost, _, _) = DNSLookup(babyalias)   # drop aliases and IPs
  if babyhost:
    babyhost = string.split(babyhost, '.')[0]     # keep short name only
  return babyhost


# convert a list of filenames to a bash-correct brace structure
# (ie. ['a', 'b', 'c'] -> '{a,b,c}') The only tricky thing is that
# bash does not expand braces unless they have at least one comma (so
# '{a}' remains '{a}'). Duh! So we need to special case that to avoid
# confusing bash.
def ToBashBracePattern(filelist):
  bash_pattern = string.join(filelist, ',')
  if len(filelist) > 1:
    bash_pattern = '{%s}' % bash_pattern

  return bash_pattern


#
# get_backup_dir - create a backup directory with a name like
# 'bak/sep06a' under the specified directory.
#
def get_backup_dir(parent_dir):
  base_backup_dir = "%s/bak" % parent_dir
  mmmdd = time.strftime('%b%d', time.localtime(time.time()))
  mmmdd = string.lower(mmmdd)
  cmd = (r'''
    cd %s
    ls -d %s %s? 2>/dev/null''' % (base_backup_dir, mmmdd, mmmdd))
  stdout, _ = popen2.popen2(cmd)
  used = {}
  while 1:
    line = stdout.readline()
    if line == '': break
    if line[-1] == '\n': line = line[:-1]
    dirname = "%s/%s" % (base_backup_dir, line)
    used[dirname] = 1
  suffix = ''
  while 1:
    backup_dir = '%s/%s%s' % (base_backup_dir, mmmdd, suffix)
    if not used.has_key(backup_dir):
      os.makedirs(backup_dir)
      break
    if suffix == '': suffix = 'a'
    else: suffix = chr(ord(suffix[0]) + 1)
  return backup_dir

#
# GetOptionsDict - utility function to read the command line arguments into
# a dictionary.
#
# The 'opts' list specified is in the form:
#   opts = ['command_flag=', 'no_value_command_flag', ...]
#
# Returns a dictionary (option_name does not have leading '--' or trailing '='):
#   options_dict['option_name'] => value
#
def GetOptionsDict(opts):
  options_dict = {}
  (optlist, args) = getopt.getopt(sys.argv[1:], '', opts)
  for flag_with_leading_dashes, value in optlist:
    flag = flag_with_leading_dashes[2:]
    flag_with_trailing_equal = flag + '='
    if flag_with_trailing_equal in opts:
      options_dict[flag] = value
    elif flag in opts:
      options_dict[flag] = 1
    else:
      raise (RuntimeError, 'unsupported option: %s' % flag)
  return options_dict

#
# EnsureTrailingSlash - tack a trailing '/' on the dir name if needed.
#
def EnsureTrailingSlash(dir):
  """ Add a trailing slash to the string passed in if it does not have one. """
  if dir and dir[-1] != '/':
    dir = dir + '/'
  return dir


def TestPingability(hosts, timeout=5, slots=20):
  """Find pingable/unpingable hosts.
  Args:
    hosts: ['hostname', ... ] - list of hosts to ping.
    timeout: int - timeout in seconds to use for each host.
    slots: int - number of hosts to fping at a time.
  Returns:
    (reachable, unreachable)
    reachable: ['hostname', ... ] - pingable hosts.
    unreachable: ['hostname', ... ] - unpingable hosts.
  """

  reachable = []
  unreachable = []

  for i in range((len(hosts) + (slots-1)) / slots):
    cur_hosts = hosts[i*slots:(i+1)*slots]
    cmd = 'fping -t%s -a -q -r2 %s 2>> /dev/null' % \
          (timeout * 1000, string.join(cur_hosts))

    # we don't really want an alarm. fping times out on its own and we
    # need to give it enough time to finish the job. We retry twice
    # (so a total of 3 timeouts) and add 2min for safety
    safetytimeout = 2*60 + 3*len(cur_hosts)*timeout
    (status, sig, output) = RunAlarmCmd(cmd, safetytimeout)

    # fping returns:
    #   0 - all hosts pingable
    #   1 - some hosts unpingable
    #   2 - if any IP addresses were not found
    #   3 - for invalid command line arguments
    #   4 - for a system call failure
    if status == 255:
      raise RuntimeError, 'TestPingability: fping timed out'
    elif status > 2:
      raise RuntimeError, \
            'TestPingability: fping fatal error:' \
            ' %s (status: %s)' % (string.join(output, '\n'), status)

    # parse output - each line is a hostname that is alive.
    output = string.split(output, '\n')
    for line in output:
      host = string.strip(line)
      if not host: continue
      reachable.append(host)

  reachable_dict = {}
  for host in reachable:
    reachable_dict[host] = 1

  unreachable = []
  for host in hosts:
    if not reachable_dict.has_key(host):
      unreachable.append(host)

  return (reachable, unreachable)

def TestSshability(hosts, timeout=60, slots=20, remote_user=None,
                   fallback_user=None):
  """Find sshable/non-sshable hosts
  Args:
    hosts: ['hostname', ... ] - list of hosts to test.
    timeout: int - timeout in seconds for each ssh.
    slots: int - number of slots to use to fork commands.
    remote_users: ['user', ... ] - reachable if accessible under all
      these users.  If not specified, does a passwordless ssh.
    fallback_user: 'user' - fallback user to go in as.
  Returns:
    (sshable, non-sshable)
    sshable: ['hostname', ... ] - reachable hosts via ssh.
    nonsshable: ['hostname', ... ] - unreachable hosts via ssh.
  """
  sshable = []
  notsshable = []
  results = ForkRemoteCommands(hosts, 'hostname', 30, numslots=slots,
                               remote_user=remote_user,
                               fallback_user=fallback_user)
  for host, (status, output, error) in results.items():
    if not status:
      sshable.append(host)
    else:
      notsshable.append(host)
  return (sshable, notsshable)

def TestReachability(hosts, timeout=60, slots=20, remote_user=None,
                     fallback_user=None):
  """Find reachable/unreachable hosts via ping and ssh.
  Args:
    hosts: ['hostname', ... ] - list of hosts to test.
    timeout: int - timeout in seconds for each ssh.
    slots: int - number of slots to use to fork commands.
    remote_users: ['user', ... ] - reachable if accessible under all
      these users.  If not specified, does a passwordless ssh.
    fallback_user: 'user' - fallback user to go in as.
  Returns:
    (reachable, unreachable)
    reachable: ['hostname', ... ] - reachable hosts via ping and ssh.
    unreachable: ['hostname', ... ] - unreachable hosts via ping or ssh.
  """
  # Test pingability first and sshability next.
  (hosts, unreachable) = TestPingability(hosts, timeout=timeout, slots=slots)
  (sshable, notsshable) = TestSshability(hosts, timeout=timeout, slots=slots,
                                         remote_user=remote_user,
                                         fallback_user=fallback_user)
  # Now concatenate the two lists
  reachable = sshable
  unreachable = unreachable + notsshable

  return (reachable, unreachable)


def WaitForReachability(hosts, timeout, check_interval, if_any=1, slots=1):
  """Check all hosts at most each check_interval seconds to see which have
  come up.  If if_any is set, return 0 on any machine coming up.  Else return
  0 only when all are up.  Return 1 on error or timeout.

  Args:
    hosts: Tuple of names of the machine to ping, ex: ('gpm82', 'gpm7')
    timeout: Maximum time to wait, in seconds, ex: 180.0
    check_interval: Upper limit on how often to check all hosts, in seconds,
      ex: 20.0.
  """
  current_time = time.time()
  check_interval = min(check_interval, timeout)
  end_time = current_time + timeout
  status = 1
  (up, down) = (None, None)

  while (current_time <= end_time):
    interval_start_time = current_time
    (up, down) = TestReachability(hosts, check_interval, slots)
    if if_any:
      if up:
        status = 0
        break
    elif not down:
      status = 0
      break

    current_time = time.time()
    interval_time_left = check_interval - (current_time - interval_start_time)
    if current_time + max(interval_time_left, 0) > end_time:
      break
    if 0 < interval_time_left:
      time.sleep(interval_time_left)
      current_time = time.time()

  return status

#
# Puts a file/dir from the current machine to the specified lists of machines
# For replicating directories, be sure they have the trailing / for proper
# behaviour
#
# NOTE (directly from Bogdan, so watch out):
# """
# "Obsolete! Do not use under any circumstance or you'll be shot dead" :-)
# The rsynccmd.py library will take care of this. The library is actually
# done but I never checked it in because I got distracted with other stuff. :-(
# """
#  This seems to be still used by googleconfig!
def PutFilesOnMachines(files, machines, timeout, numslots,
                       local_user='root', remote_user=None):
  local_machine = string.split(socket.gethostname(), ".")[0]
  machcmds = []

  # prepend AM user
  if local_user:
    local_string = "%s@" % local_user
  else:
    local_string = ""

  for m in machines:
    for f in files:
      machcmds.append((m,
                       "rsync -e \"ssh -q -P -c none\" -aH %s:%s %s%s" % (
        local_machine, f, local_string, f)))
  return ForkExecPool(machcmds, timeout, numslots, '', remote_user=remote_user)

# LOCK functions
#  useful for locking/unlocking a given machine so we get exclusivity
#  during various operations. This is a minimal level protection. More
#  elaborate techniques are needed for high risk operations.
def Lock(lockname):
  try:
    fd = os.open(lockname, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
    os.write(fd, "Locked at %s" % time.ctime(time.time()))   # timestamp
    os.close(fd)
  except OSError, e:
    log("Failed to lock machine: %s. \n" % e + \
        "If this is incorrect remove the lock manually " + \
        "with: \n\trm -f %s" % lockname)
    sys.exit(1)  # exit. There is nothing else we can do.

def Unlock(lockname):
  try:
    os.unlink(lockname)
  except:
    pass

# This is a utility function to convert integers and long integers to
# strings.  This will work properly with python1.5+. In old versions
# of ptyhon, str(val) for long ints appens a 'L' which we do not
# want. For later versions, the problem is fixed.
#
def int_to_string(val):
  strrep = str(val)
  if strrep[-1] == 'L':
    return strrep[0:-1]
  else:
    return strrep


def GetLocalMCP():
  """Find the appropriate MCP machine to use relative to our coloc.
  This function shall ping the local mcp machine (XXmcp.prodz), and if
  that fails, will return the default mcp machine (mcp.prodz).
  This ensures that if we are a new coloc, there will still be an
  MCP machine at our disposal.

  RETURNS - string, such as "abmcp.prodz.google.com"
  """

  coloc = LocalColoc()
  MCP_ALIAS = "mcp.prodz.google.com"

  local_mcp = "%s%s" % (coloc, MCP_ALIAS)

  (good,bad) = TestPingability([local_mcp])
  if good:
    return local_mcp
  else:
    return MCP_ALIAS

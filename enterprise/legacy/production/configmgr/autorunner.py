#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Ben Polk
#
# autorunner.py - Create a autorunner request file.
#
# OVERVIEW:
#
# This module defines a framework for building scripts that receive requests
# in the form of files, and dispatch a command in a seperate process for
# each file received.
#
# Here is a high level outline of how to implement a script using autorunnuer:
#   * Define your request object class as a subclass of Request
#   * Create the command info dict that maps the request to a runnable command
#   * Create an instance of the AutorunnerDispatcher class
#   * Register the command info dict with the dispatcher
#   * Start the dispatcher with the Execute() method
#   * The dispatcher runs commands when requests arrive in the incoming dir
#   * Send an INT or TERM signal or create a TerminateRequest file to stop it
#
# See autorunner_unittest.py and configmgr.py for examples.
#
# REQUESTS:
#
# This module also defines the base class for the Request objects. These are
# Python executables containing a single dictionary.  The request arguments
# are key/value pairs in the dictionary.
#
# These key/value pairs are translated into command line arguments in
# the dispatched command. For example, 'FILE': '/tmp/foo' in a request
# would be translated to a '--file=/tmp/foo' argument on the dispatched
# command line.
#
# CHANGING DEFAULT PARALLELISM AND REQUEST PROCESSING ORDER:
#
# By default, only one request is dispatched at a time. You can change this
# by creating a filter function that is registered with the dispatcher. The
# dispatcher calls this function with each waiting request, along with the
# number of waiting and running requests of each type, and the filter chooses
# whether to allow the request to run. Use the SetAllowedRequestFilter
# method to replace the default function.
#
# The order that requests are handled defaults to the creation time value in
# the request file. Use the SetSortFunction method to replace the default sort
# function.
#
# ERROR HANDLING:
#
# The dispatched command should return a 0 exit status for success and a
# non-zero status to indicate that it failed. The request file is moved
# to a 'success', or 'failure' directory based on this status. stdout and
# stderr are written to the log using the logging module.
#
# If an unhandled exception is thrown in a dispatched Python script things
# work as you'd expect: the dispatched script exits with an error status
# and writes the exception stack to stderr. The autorunner dispatcher logs
# the stderr information and moves the request to the failure directory.
#
# REQUEST TO COMMAND MAPPING INFORMATION:
#
# The linkange between a request type and the command to run is specified
# in a dictionary that is passed to the distcher in the
# RegisterTypeHandler method.
#
# The keys supported in this dictionary are:
#   autorunner.COMMAND - string containing the command to run
#   autorunner.VALIDATOR - optional function to validate the request
#   autorunner.EXTRA_CMD_ARGS - optional list of extra command line arguments
#   autorunner.RETRIES - optional number of time to retry if request fails
#
# TERMINATING THE DISPATCHER
#
# When a SIGTERM is received, or a TerminateRequest request file is processed,
# the dispatcher goes into 'drain mode', where it stops dispatching new
# commands. When it is in drain mode and there are no running commands it
# exits.
#
# When a SIGINT is recieved the dispatcher exits immediatly.
#
# CAVEATS/TODOS:
#   * If the dispatcher can't move a command from incoming to pending it spins.
#   * Perhaps autorunner should know how to send email and respond to v command.
#   * It would be nice to keep statistics of request types and success/failure.
#   * The request 'HANDLER' field was put in to allow multiple autorunner
#     based scripts to pull from the same pool of requests, but this is not
#     implemented, and probably should just be removed.
#   * There are two kinds of fields in the request, control type information
#     like the 'TIME', and 'REQUEST', and the arguments to the request. They
#     probably should be seperated more cleanly. Right now the code just
#     knows which are the control ones and doesn't pass them to the command.
#

# Workaround for obscure bug in os.py: basically if all the directories
# available for tempfiles are on a full partition, execv will fail
# mysteriously, and sping will wrongly report everyone as dead.
# If we force _any_ [non-false] value into tempfile.tmpdir, it will work!
import tempfile
tempfile.tempdir = '/tmp'

import sys
import traceback
import commands
import popen2
import select
import signal
import string
import time
import os
import urlparse
import urllib
import cgi
import re

# Hack to enable circular imports
import google3.enterprise.legacy.production.configmgr
google3.enterprise.legacy.production.configmgr.autorunner = \
    sys.modules[__name__]

import exceptions
from google3.pyglib import logging
# Note that request_manager is a circular import
from google3.enterprise.legacy.production.configmgr import request_manager

###############################################################################

# Dictionary variable name
REQUEST = 'AUTO_RUNNER_REQUEST'

# Special type of request to tell us to stop.
TERMINATE = 'TERMINATE'

# Keys that all types of requests share
HANDLER = 'REQUEST_HANDLER'
TYPE = 'TRANSACTION_TYPE'
TIME = 'TIME'

# Keys used by the autorunner system. This is where we come to know if a
# particular key is a per-request key or a system key.
SYSTEM_KEYS = [HANDLER, TYPE, TIME]

# Keys to the dictionary storing information about registered types.
COMMAND = 'COMMAND'             # The command to execute. ('foo.py')
VALIDATOR = 'VALIDATOR'         # Function to validate request.
ARG_CREATOR = 'ARGCREATOR'      # Optional function to map request to arg list
EXTRA_CMD_ARGS = 'EXTRACMDARGS' # Optional string to include on command line
RETRIES = 'RETRIES'             # Optional number of retries
CLASS = 'CLASS'                 # Optional request class (default Request)
ENV_PREFIX = 'ENV_PREFIX'       # Optional prefix to set environment variables

# Constants controlling polling interval when we have no work
MIN_SLEEP_TIME = 0.1       # Seconds to sleep initially
MAX_SLEEP_TIME = 5         # Max seconds we sleep
SLEEP_TIME_FACTOR = 2.0    # Multiply by this each time around nothing happens

# Return values for dispatched commands
AUTORUNNER_RC_GOOD = 0
AUTORUNNER_RC_DIE_NO_RETRY = -1

# Timeout for autorunner hanged requests
AUTORUNNER_RC_TIMEOUT = 90   # 90 secs

###############################################################################
#
# SigtermHandler - function we register to catch SIGTERM. If we get sigterm,
# we raise SIGTERMInterrupt
#
def SigtermHandler(dummy, _):
  logging.warn('SIGTERM received, shutting down')
  raise SIGTERMInterrupt

class SIGTERMInterrupt(exceptions.Exception):
  def __init__(self, args=None):
    exceptions.Exception.__init__(self)
    self.args = args

###############################################################################
#
# Request: Base class for autorunner request objects.
#
#   Contains the following members:
#     datadict: dictionary containing the request name/value pairs
#     filename: base name of the file that corresponds to this request
#
class Request:

  def __init__(self):
    self.datadict = {}
    self.filename = None
    self.attempts = 1
    self.statusz_file = None

  # Set or get the entire request datadict.
  def SetData(self, datadict):
    self.datadict = datadict
  def GetData(self):
    return self.datadict

  def SetValue(self, name, value):
    self.datadict[name] = value
  def GetValue(self, name):
    return self.datadict[name]

  def SetFilename(self, filename):
    self.filename = filename
  def GetFilename(self):
    return self.filename

  def SetType(self, reqtype):
    self.datadict[TYPE] = reqtype
  def GetType(self):
    return self.datadict[TYPE]

  def GetAttempts(self):
    return self.attempts
  def AddAttempt(self):
    self.attempts = self.attempts + 1

  def InitStatuszFile(self, dir):
    self.CloseStatuszFile()
    self.statusz_file = open("%s/%s_statusz" % (
      dir, os.path.basename(self.filename)), "w")
  def AddStatusz(self, msg):
    if self.statusz_file:
      self.statusz_file.write("[%s]: %s\n" % (
        time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time())), msg))

  def CloseStatuszFile(self):
    if self.statusz_file:
      self.statusz_file.close()

  def ReadStatuszFile(self, dir):
    fname = "%s/%s_statusz" % (dir, os.path.basename(self.filename))
    return "%s" % (open(fname, "r").read())

  def GetRequestStatuszData(self):
    return "Attmpts: %s\n%s" % (
      self.attempts,
      string.join(map(lambda (k, s): "%s: %s" % (k, s),
                      self.datadict.items()),
                  "\n"))

  # Return info that cna be used to schedule requests for execution
  def GetSchedulingInfo(self):
    return None

  # Writes the request to a file. id is used for determinig requests that
  # are  written at the same time (if caller cares about)
  # We first write to the tmpfilename and then move
  def Write(self, filename, id = 0):
    write_time = int(time.time())
    self.SetValue(TIME, [write_time, id, time.ctime(write_time)])
    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    tmpfilename = "%s/.%s" % (dirname, basename)
    fd = open(tmpfilename, 'w')
    fd.write('AUTO_RUNNER_REQUEST = %s' % repr(self.datadict))
    os.fdatasync(fd.fileno()) # sync on disk
    fd.close()
    (rc, out) = commands.getstatusoutput('mv -f %s %s' % \
                                         (tmpfilename, filename))
    if rc:
      raise IOError, out

  def __repr__(self):
    return "Request : %s" % repr(self.datadict)


  def SetTimeout(self, timeout):
    id = self.GetType()
    request_manager.SetTimeout(id, timeout,
                               string.join([request_manager.AUX_CMD,
                                            request_manager.LOG_CMD], '|'))

###############################################################################
#
# TerminateRequest - Class to create Terminate type requests.
#
# Pass the constructer the handler that you want these requests to go to,
# then use the Write() method to write out the request as a file:
#
# term_req = TerminateRequest(configmgr_request.CONFIG_MGR)
# term_req.Write(terminate_request_filename)
#
class TerminateRequest(Request):
  def __init__(self, _):
    Request.__init__(self)
    self.SetValue(TYPE, TERMINATE)


###############################################################################
#
# DefaultArgsCreator - Create a list of command line args based on the
# request passed in.
#
def DefaultArgsCreator(request):
  args_list = []
  request_datadict = request.GetData()
  argnames =  request_datadict.keys()
  argnames.sort()
  for name in argnames:
    if not name in SYSTEM_KEYS:
      arg = '--%s=%s' % (string.lower(name), request_datadict[name])
      args_list.append(commands.mkarg(arg))
  return args_list


###############################################################################
#
# RunnableCommand - object for a command to run
#
class RunnableCommand:

  def __init__(self, request, command_info):

    request.AddStatusz("Command info : %s" % repr(command_info))
    executable    = command_info[COMMAND]
    argscreator   = command_info.get(ARG_CREATOR, DefaultArgsCreator)
    args          = string.join(argscreator(request))
    env_prefix    = string.join(command_info.get(ENV_PREFIX, []))
    extra_args    = string.join(map(commands.mkarg,
                                    command_info.get(EXTRA_CMD_ARGS, [])))

    self._cmd     = "%s %s %s %s" % (env_prefix, executable, args, extra_args)
    self._request = request

  def GetCmd(self):
    return self._cmd

  def GetRequest(self):
    return self._request


# Default handler - does nothing
def DefaultHandler(request):
  return

class RecentRequestStatusz:
  def __init__(self, request, err):
    self._filename = request.GetFilename()
    self._type = request.GetType()
    self._statusz = request.GetRequestStatuszData()
    self._err = err

MAX_RECENT_REQUESTS_NUM = 1000

###############################################################################
#
# AutorunnerDispatcher: Class to read requests, associate them with the
# command to run, and dispatch the command.
#
# Members:
#
# Object that manager the request files and directores and fetching requests:
#   * request_mgr
#
# Map request types to registered infomation about what command to run:
#   * command_info[REQUESTTYPE] ==> {'command': 'type_runner.py',
#                                  'validator': ValidatorFunction,
#                                  'argcreator': 'CmdArgCreatorFunction',}
#
# Map RunnableCommand objects to the Popen3 objects that are currently running:
#   * running_commands[command] ==> popen3object
#
# Map IO pipes gotten from Popen3 to type (stdout/stderr, RunnableCommand, and
# the Popen3 object:
#   * iopipes[pipe] ==> (iotype, command, popen3object)
#
# Log file
#   * log - currently just stderr
#

class AutorunnerDispatcher:

  def __init__(self, in_dir, working_dir,
               peeks,
               replication_machines,
               min_sleep_time=MIN_SLEEP_TIME,
               max_sleep_time=MAX_SLEEP_TIME,
               fileutil_cmd=None,
               periodic_requests_dirs=None):
    self._command_info     = {}
    self._running_commands = {}
    self._iopipes          = {}

    # Handler functions
    self._start_handler   = DefaultHandler # called when request starts
    self._failure_handler = DefaultHandler # called when request failed
    self._success_handler = DefaultHandler # called when request is completed OK
    self._retry_handler   = DefaultHandler # called when request is retried

    # Sleep between cycles
    self._min_sleep_time  = min_sleep_time
    self._max_sleep_time  = max_sleep_time

    # Statistics for processed requests
    self._num_processed_success = 0
    self._num_processed_failure = 0
    self._num_retries = 0

    # Init the request manager
    self._request_mgr = request_manager.RequestManager(
      in_dir, working_dir, replication_machines, peeks,
      fileutil_cmd=fileutil_cmd, periodic_requests_dirs=periodic_requests_dirs)
    self._request_mgr.SetDispatcher(self)

    # Export our stuff
    from google3.pyglib import expvar
    expvar.ExportFunction("num-running-requests",
                          lambda s=self: len(s._running_commands.keys()))
    expvar.ExportFunction("num-processed-success",
                          lambda s=self: s._num_processed_success)
    expvar.ExportFunction("num-processed-failure",
                          lambda s=self: s._num_processed_failure)
    expvar.ExportFunction("num-retries",
                          lambda s=self: s._num_retries)

    # Recent requests list of RecentRequestStatusz
    self._recent_requests = []

    # Register the handler to export via the pyserverizer
    self.RegisterHandlers()

  #
  # GetTypeInfo - look up the registered request->command information for
  #              this request type, and return it.
  #
  def GetTypeInfo(self, reqtype):
    return self._command_info[reqtype]

  #
  # AddRecentRequest - adds a record to recent_requests_ modifying if
  #                    necessary the size
  #
  def AddRecentRequest(self, req, err):
    self._recent_requests.append(RecentRequestStatusz(req, err))
    if len(self._recent_requests) > MAX_RECENT_REQUESTS_NUM:
      self._recent_requests.pop(0)

  #
  # RegisterTypeHandler - set the dictionary that contains the request type
  # specific information.
  #
  # Raises a RuntimeException if the command is not specified.
  #
  def RegisterTypeHandler(self, reqtype, command_info):
    if not command_info.has_key(COMMAND):
      logging.fatal('%s invalid registration, no command specified' % reqtype)
      raise RuntimeError('%s registration failed, missing command' % reqtype)
    else:
      self._command_info[reqtype] = command_info

  #
  # GetRequestorId - Returns the id for the requestor
  #
  def GetRequestorId(self, req):
    return map(ord, req)

  #
  # GetValidator -- Returns the validator function for the given request type
  #
  def GetValidator(self, reqtype):
    return self._command_info[reqtype].get(VALIDATOR, None)

  #
  # GetRetries -- Returns the number of retries for the given request type
  #
  def GetRetries(self, reqtype):
    return self._command_info[reqtype].get(RETRIES, 0)

  #
  # GetRequestClass -- Returns the request class (child of Request) for
  #   the given request type
  #
  def GetRequestClass(self, reqtype):
    if self._command_info.has_key(reqtype):
      return self._command_info[reqtype].get(CLASS, Request)
    return Request

  #
  # GetCmdInfo -- Returns the command info map for the given request type
  #
  def GetCmdInfo(self, reqtype):
    return self._command_info[reqtype]

  #
  # GetRequestTimeout -- Retuens the timeout for reques
  #
  def GetRequestTimeout(self, req_type, default_timeout):
    return map(lambda x, t = default_timeout: x ^ t[x % len(t)], req_type)

  #
  # ValidateRequest - Verify that we have been registered to handle this kind
  # of request, and then run the registered validator for this request type.
  #
  # Returns true (non-zero) if this is a valid request, 0 if it is not valid.
  #
  def ValidateRequest(self, request):
    reqtype = request.GetType()
    if not reqtype in self._command_info.keys():
      logging.warn('Skipping unregistered %s request from file %s' %
               (reqtype, request.GetFilename()))
      return 0
    validator = self.GetValidator(reqtype)
    if validator:
      (validator_rc, msg) = validator(request)
      if not validator_rc:
        logging.error('%s failed validation: %s' % (request.GetFilename(), msg))
      return validator_rc
    return 1 # Validate passed, or no validator found

  #
  # Returns the default timeout for the number of requests
  #
  def GetDefaultTimeout(self, num):
    return AUTORUNNER_RC_TIMEOUT - num

  #
  # SetAllowedRequestFilter - Pass filter function through to the request_mgr.
  # This function limits which requests will get returned by the
  # GetNextRequest() function, and is used to implement request scheduling
  # policies.
  #
  def SetAllowedRequestFilter(self, allowed_request_function):
    self._request_mgr.SetAllowedRequestFilter(allowed_request_function)


  #
  # SetSortFunction - Pass sort function through to the request_mgr.
  # This function is used to determine which order the requests are processed.
  #
  def SetSortFunction(self, sort_function):
    self._request_mgr.SetSortFunction(sort_function)

  #
  # SetStartHandler - Pass a function that gets called when a request is
  # started to be executed
  #
  def SetStartHandler(self, start_handler):
    self._start_handler = start_handler

  #
  # SetSuccessHandler - Pass a function that gets called when a request is
  # completed OK
  #
  def SetSuccessHandler(self, success_handler):
    self._success_handler = success_handler

  #
  # SetRetryHandler - Pass a function that gets called when a request is
  # retried (to be executed)
  #
  def SetRetryHandler(self, retry_handler):
    self._retry_handler = retry_handler

  #
  # SetFailureHandler -- Pass a function that gets called when a request is
  # declared failed
  #
  def SetFailureHandler(self, failure_handler):
    self._failure_handler = failure_handler


  #
  # SetRequestTimeout -- Sets the request timeout for the dispatcher
  #
  def SetRequestTimeout(self, req_type, default_timeout):
    name = self.GetRequestorId("%s" % req_type)
    timeout = self.GetRequestTimeout(name, default_timeout)
    request = Request()
    request.SetType(name[0])
    request.SetTimeout(timeout)

  #
  # Execute - Start dispatching requests
  #
  def Execute(self):

    logging.info('Autorunning dispatcher starting')

    draining = 0
    done = 0
    self._sleep_time = self._min_sleep_time

    signal.signal(signal.SIGTERM, SigtermHandler)
    # before starting the loop move any pending requests to
    # the in dir
    self._request_mgr.MoveAllPendingRequests()
    try:
      while not done:
        do_continue = 0
        try:
          request = None

          if not draining:

            #
            # Update the request_list, count waiting and running requests, and see
            # if we can get a new request to start.
            #
            self._request_mgr.LookForNewRequests()
            waiting_counts = self._request_mgr.GetWaitingCounts()
            running_counts = self.GetRunningCounts()
            request = self._request_mgr.GetNextRequest(waiting_counts,
                                                       running_counts)
            #
            # See if there is a command to dispatch
            #
            if request:
              request.InitStatuszFile(self._request_mgr.GetStatuszDir())
              reqtype = request.GetType()
              logging.info('=== "%s" request found' % reqtype)
              self._request_mgr.MoveRequestToPending(request)
              request.AddStatusz("Starting process")

              if reqtype == TERMINATE:
                #
                # Terminate requests make us stop doing new commands.
                #
                draining = 1
                logging.info('=== Draining running commands.')
                request.AddStatusz("Request drained")
                self._num_processed_success = self._num_processed_success + 1
                self.AddRecentRequest(request, 0)
                self._request_mgr.MoveRequestToSuccess(request)
              else:
                #
                # Validate the command and dispatch it if it looks good, continue
                # if this request was not valid.
                #
                if not self.ValidateRequest(request):
                  request.AddStatusz("Request has invalid parameters")
                  self._request_mgr.MoveRequestToFailure(request)
                  self._failure_handler(request)
                  self._num_processed_failure = self._num_processed_failure + 1
                  self.AddRecentRequest(request, 1)
                  # Note: cannot add a continue here in while: try:
                  do_continue = 1  # Go get another request, this one sucked.
                else:
                  command = RunnableCommand(request, self.GetCmdInfo(reqtype))
                  request.AddStatusz("Running request cmd [%s]" %
                                     command.GetCmd())
                  self.DispatchCommand(command)

          if not do_continue:
            #
            # See if any commands have completed or any IO is waiting.
            #
            command_did_something = self.PollRunningCommands()

            if not request and not command_did_something:
              #
              # No request started, nothing read, and nothing finished,
              # so sleep briefly, and increase length of next sleep.
              #
              time.sleep(self._sleep_time)
              self._sleep_time = min(self._sleep_time*SLEEP_TIME_FACTOR,
                                     self._max_sleep_time)
            else:
              # Something happened, so reduce sleep time to minimum
              self._sleep_time = self._min_sleep_time

            #
            # If we're draining and there are no running commands, we are done
            #
            if draining and self._running_commands == {}:
              logging.info('=== No more requests, exiting')
              done = 1

          #
          # Sync the request manager directories
          #
          self._request_mgr.SyncRequestDirs()

        except SIGTERMInterrupt:
          # Catch SIGTERM
          logging.warn('SIGTERMInterrupt caught, shutting down')
          draining = 1

    except KeyboardInterrupt:
      # Catch control-C
      logging.warn('KeyboardInterrupt, exiting immediatly')
      raise

  #
  # GetRunningCounts - Return a dictionary of the number of commands running
  #   running_types_count[TYPE] ==> count
  #
  def GetRunningCounts(self):
    running_counts = {}
    for running_command in self._running_commands.keys():
      reqtype = running_command.GetRequest().GetType()
      running_counts[reqtype] = running_counts.get(reqtype, 0) + 1
    return running_counts

  #
  # DispatchCommand - Start the specified command, and save information about
  #   it in our data structures.
  #
  def DispatchCommand(self, command):
    reqtype = command.GetRequest().GetType()
    cmd_str = command.GetCmd()
    filename = command.GetRequest().GetFilename()
    logging.info('+++ Starting %s %s: %s' % (filename, reqtype, cmd_str))
    self._start_handler(command.GetRequest())
    popen3object = popen2.Popen3(cmd_str, 'true')   # true: "capture stderr"
    popen3object.tochild.close()                    # close child's stdin

    def SetNonblocking(pipe):
      import fcntl
      fd = pipe.fileno()
      fl = fcntl.fcntl(fd, fcntl.F_GETFL)
      try:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NDELAY)
      except AttributeError:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.FNDELAY)

    SetNonblocking(popen3object.fromchild)
    SetNonblocking(popen3object.childerr)

    self._iopipes[popen3object.fromchild] = ("stdout", command, popen3object)
    self._iopipes[popen3object.childerr] = ("stderr", command, popen3object)

    self._running_commands[command] = popen3object

  #
  # ReadFromCommands - Do a select() on the pipes from our running commands.
  #
  def ReadFromCommands(self):
    io_happened = 0
    (ioready, _, _) = select.select(self._iopipes.keys(),
                                    [],    # don't care about "write"-s
                                    [],    # ... or errors
                                    0)     # 0 <=> "non blocking"
    for pipe in ioready:
      io_happened = 1
      (iotype, command, popen3object) = self._iopipes[pipe]
      logging.info('%s results:' % command.GetRequest().GetFilename())
      try:
        # read up to 4k of data (default size of IO buffer so larger
        # reads won't help anyway)
        # TODO: maybe keep the streams seperate until the command completes, or
        #       log to seperate places. This current method will result in
        #       different command output being jumbled together.
        str = pipe.read(4096)
        logging.info(str)
        command.GetRequest().AddStatusz(str)
      except IOError, e:
        logging.error("Read error for %s: %s" % (command.GetCmd(), e))
        # TODO: should we keep this raise?
        # raise

    return io_happened


  #
  # PollRunningCommands - Check to see if any commands have finished. Do
  #   any required cleanup for completed commands.
  #
  def PollRunningCommands(self):

    io_happened = 0

    # see if anyone finished
    anyone_finished = 0

    #
    # See if any commands have written stuff back to us, and if so,
    # write it to the log file.
    #
    io_happened = self.ReadFromCommands()

    for (running_command, popen3object) in self._running_commands.items():
      status = popen3object.poll()

      if status != -1:
        anyone_finished = 1
        status = status >> 8                         # keep only actual status
        running_request = running_command.GetRequest()

        # cleanup
        del self._running_commands[running_command]   # The command is gone.
        del self._iopipes[popen3object.fromchild]     # And so are its io pipes.
        del self._iopipes[popen3object.childerr]

        if status == 0:
          logging.info('+++ Finished: %s' % (running_request.GetFilename()))
          self._num_processed_success = self._num_processed_success + 1
          self.AddRecentRequest(running_request, 0)
          self._request_mgr.MoveRequestToSuccess(running_request)
          self._success_handler(running_request)
        else:
          logging.error('+++ Failed (rc=%s): %s' %
                        (status, running_command.GetCmd()))
          retries = self.GetRetries(running_request.GetType())
          attempts = running_request.GetAttempts()
          if attempts <= retries:
            self._retry_handler(running_request)
            # cmd failed and user requested retries and we did not reach
            # the retry limit. So we dispatch it again.
            logging.warn('%s retrying %s more times.' %
              (running_request.GetFilename(), retries - attempts + 1))
            running_request.AddAttempt() # Increment count
            self._num_retries = self._num_retries + 1
            running_request.AddStatusz(">>>>> Failure. One more attempt "\
                                       "granted [crt attempt %s]" % attempts)
            self.DispatchCommand(running_command)
          else:
            running_request.AddStatusz(">>>>> Failure. No more attempts")
            self._num_processed_failure = self._num_processed_failure + 1
            self.AddRecentRequest(running_request, 2)
            self._request_mgr.MoveRequestToFailure(running_request)
            self._failure_handler(running_request)

    return anyone_finished or io_happened

  ###############################################################################
  #
  # HTML stuff
  #

  # Display requests options - or them
  HTML_NO_HEADER       = 1
  HTML_TYPE_COLUMN     = 2
  HTML_NO_NAVIGATION   = 4
  HTML_NO_REQ_PARAMS   = 8
  HTML_NO_TABLE_HEADER = 16
  HTML_NO_REQ_LOG      = 32
  HTML_PLAIN_OUTPUT    = 64


  def RegisterHandlers(self):
    # Add url handler to pyserverizer if it is used.
    try:
      # try to import pyserverizer. We should succeed when
      # running within serverizer.
      self._server = __import__("pyserverizer")
      # register some uri handlers
      self._server.RegisterUriHandler("/", lambda arg1, arg2, s=self:
                                      s.HandleStatusz(arg1, arg2))
      self._server.RegisterUriHandler("/statusz", lambda arg1, arg2, s=self:
                                      s.HandleStatusz(arg1, arg2))
      self._server.RegisterUriHandler("/forcesync", lambda arg1, arg2, s=self:
                                      s.HandleForceSync(arg1, arg2))
    except ImportError:
      logging.info("Not running in serverizer.")
      self._server = None
    # endtry
  # enddef

  def HandleForceSync(self, _, dummy):
    try:
      self._request_mgr.ForceSyncNextCycle()
      return "Sync forced ."
    except:
      # collect the exception traceback so we know what went wrong
      (t, v, tb) = sys.exc_info()
      exc_msg = string.join(traceback.format_exception(t, v, tb))
      logging.error(exc_msg)
      return "<pre>%s</pre>" % exc_msg
    # endtry
  # enddef

  def HandleStatusz(self, uri, _):
    try:
      (_, _, _, _, query, _) = urlparse.urlparse(uri)
      params = cgi.parse_qs(query)

      if params.has_key("req") and params.has_key("dir"):
        return self.ShowRequests(params["req"], params["dir"],
                                 params.get("options", ["0"])[0])
      # endif
      if params.has_key("show_all"):
        return self.ShowAll(params.get("reqtype", ["Success"])[0],
                            params.get("start", ["0"])[0],
                            params.get("num", ["25"])[0],
                            params.get("filter", [""])[0],
                            params.get("options", ["0"])[0])
      # endif
      return self.ShowStatusz()
    except:
      # collect the exception traceback so we know what went wrong
      (t, v, tb) = sys.exc_info()
      exc_msg = string.join(traceback.format_exception(t, v, tb))
      logging.error(exc_msg)
      return "<pre>%s</pre>" % exc_msg
    # endtry
  # enddef

  #
  # Banner -- Helper to build a html banner
  #
  def Banner(self, str, bgcolor="#c0c0ff"):
    return "<p>\n<table bgcolor=\"%s\" cellpadding=5 width=100%%>\n"\
           "<tr align=center><td><font size=+2>%s</font></td></tr>\n"\
           "</table></p>\n" % (bgcolor, str)
  # enddef

  #
  # Table -- Helper to build a table from rows
  #
  def Table(self, t,
            has_head=1, headcolor="#ffc0c0", bgcolor="#ffffff"):
    if has_head:
      head = []
      for th in t.pop(0):
        head.append("<th><font size=\"-1\" face=\"arial,sans-serif\">"
                    "%s</font></th>" % th)
      # endfor
      table = ["<tr bgcolor=\"%s\">\n%s</th>\n" % (
        headcolor, string.join(head, "\n"))]
    else:
      table = []
    # endif

    for tr in t:
      row = []
      for td in tr:
        row.append("<td><font size=\"-1\" face=\"arial,sans-serif\">"
                   "%s</font></td>" % td)
      # endfor
      table.append("<tr bgcolor=\"%s\">\n%s</th>\n" % (
        bgcolor, string.join(row, "\n")))
    # endfor
    return "<p><table cellpadding=5 width=100%%>\n%s\n</table></p>\n" % (
      string.join(table, "\n"))
  # enddef

  #
  # ShowStatusz - Shows the global statusz of the config manager
  #
  def ShowStatusz(self):
    from google3.pyglib import expvar
    ret = []
    ret.append(self.Banner("Config Manager Status"))

    ret.append(self.Banner("Varz"))
    ret.append(expvar.PrintAllHTML())

    # Navigational links to show classes of requests
    navlinks = []
    for rtype in ["Ready", "Pending", "Success", "Failure", "Incoming"]:
      navlinks.append("<a href=\"/statusz?show_all=1&reqtype=%s&"\
                      "start=0&num=25\">Show %s Requests</a>" % (
        rtype, rtype))
    # endfor
    ret.append("<p>%s</p>" % string.join(navlinks,
                                         "\n&nbsp;&nbsp;|&nbsp;&nbsp;\n"))


    # Currently Running requests
    ret.append(self.Banner("Currently Running"))
    table = [("Type", "Filename", "Parameters")]
    dir = urllib.quote(self._request_mgr.GetPendingDir())
    for req in self._running_commands.keys():
      table.append((
        req.GetRequest().GetType(),
        "<a href=\"/statusz?req=%s&dir=%s\">%s</a>" % (
        urllib.quote(req.GetRequest().GetFilename()), dir,
        req.GetRequest().GetFilename()),
        "<pre>%s</pre>" % (req.GetRequest().GetRequestStatuszData())))
    # endfor
    ret.append(self.Table(table))

    # Recently completed results
    ret.append(self.Banner("Recent Requests"))

    # since self._recent_requests is in time order and we want to
    # show the most recent first, we build the table in reverse order
    # and reverse at the end
    table = []
    for req in self._recent_requests:
      if req._err:
        dir = self._request_mgr.GetFailureDir()
      else:
        dir = self._request_mgr.GetSuccessDir()
      # endif
      if req._err != 0:
        err_begin = "<b><font size=+1 color='red'>ERROR :</font></b> "
      else:
        err_begin = ""
      # endif
      table.append((
        req._type,
        "%s<a href=\"/statusz?req=%s&dir=%s\">%s</a>" % (
        err_begin,
        urllib.quote(req._filename), urllib.quote(dir), req._filename),
        "<pre>%s</pre>" % req._statusz,
        "%s" % req._err))
    # endfor

    table.append(("Type", "Filename", "Parameters", "Err"))
    table.reverse()

    ret.append(self.Table(table))

    return "<html><body>\n%s\n</body></html>" % string.join(ret, "\n")
  # enddef ShowStatusz

  #
  # ShowRequests - Shows the specified request(s) from the specified
  #  directory
  #
  def ShowRequests(self, reqs, dir, options):
    if dir:
      dir = urllib.unquote(dir[0])
    else:
      dir = "/tmp/"
    # endif
    try:
      options = int(options)
    except ValueError:
      num = 0
    # endtry
    no_headers = options & AutorunnerDispatcher.HTML_NO_HEADER
    no_params = options & AutorunnerDispatcher.HTML_NO_REQ_PARAMS
    no_log = options & AutorunnerDispatcher.HTML_NO_REQ_LOG

    table = []
    for r in reqs:
      try:
        if not no_headers:
          table.append((self.Banner("Request Status for %s" % r),))
        r = self._request_mgr.ReadRequestFile(
          "%s/%s" % (dir, urllib.unquote(r)))
        if r != None:
          if not no_params:
            table.append(("<b>Request Params:</b><br><pre>%s</pre>\n" %
                          r.GetRequestStatuszData(), ))
          # endif
          if not no_log:
            table.append(("<b>Execution Log:</b><br><pre>%s</pre>" % (
              r.ReadStatuszFile(self._request_mgr.GetStatuszDir())), ))
          # endif
        # endif
      except IOError:
        table.append(("<pre>%s cannot be found.\n"
                      "May be it changed state</pre>" % r,))
      # endtry
    # endfor
    return "<html><body>%s\n</body></html>" % (self.Table(table, has_head=0))
  # enddef

  #
  # ShowAll -- shows a list with requests of a type according to the
  #    the specified requremen
  #
  def ShowAll(self, reqtype, start, num, file_filter, options):

    try:
      start = int(start)
    except ValueError:
      start = 0
    # endtry
    try:
      num = int(num)
    except ValueError:
      num = 25
    # endtry
    try:
      options = int(options)
    except ValueError:
      num = 0
    # endtry

    no_headers = options & AutorunnerDispatcher.HTML_NO_HEADER
    no_type_column = options & AutorunnerDispatcher.HTML_TYPE_COLUMN
    no_navigation = options & AutorunnerDispatcher.HTML_NO_NAVIGATION
    no_table_headers = options & AutorunnerDispatcher.HTML_NO_TABLE_HEADER
    plain_output = options & AutorunnerDispatcher.HTML_PLAIN_OUTPUT

    dirs = { "Ready"   : self._request_mgr.GetReadyDir(),
             "Pending" : self._request_mgr.GetPendingDir(),
             "Success" : self._request_mgr.GetSuccessDir(),
             "Failure" : self._request_mgr.GetFailureDir(),
             "Incoming": self._request_mgr.GetIncomingDir(),
             }

    dir = dirs.get(reqtype, dirs["Ready"])
    qdir = urllib.quote(dir)

    ret = []

    # Get the files to open
    files = self._request_mgr.ListRequestFiles(dir)
    files.reverse()
    if file_filter:
      files = filter(lambda s, p = file_filter: re.match(p, s), files)
    # endif

    to_show = []
    for f in files[start:]:
      f = os.path.basename(f)
      req = self._request_mgr.ReadRequestFile("%s/%s" % (dir, f))
      if req != None:
        to_show.append(req)
        if len(to_show) >= num:
          break;
        # endif
      # endif
    # endfor

    if plain_output:
      return string.join(map(lambda r: repr(r.datadict), to_show), '\n')
    # endif

    # A banner with what's showint
    if not no_headers:
      ret.append(self.Banner("%s Requests - %s to %s" % (
        reqtype, start, start + len(to_show))))
    # endif

    # Navigational links
    if not no_navigation:
      ret.append("<table border=1 bgcolor=#c0ffc0 width=100%><tr>")
      num_before = min([num, start])
      if start > 0:
        ret.append("<td><a href=\"/statusz?show_all=1&start=%s&num=%s\">"
                   "Previous %s requests</a></td>" % (
          start - num_before, num_before, num_before))
      else:
        ret.append("<td>--</td>")
      # endif
      num_left = min(num, len(files) - (start + len(to_show)))
      if num_left > 0:
        ret.append("<td><a href=\"/statusz?show_all=1&start=%s&num=%s\">"
                   "Next %s requests</a></td>" % (
          start + num, num_left, num_left))
      else:
        ret.append("<td>--</td>")
      # endif
      ret.append("</tr></table>")
    # endif not no_navigation

    # The requests themself
    if no_table_headers:
      table = []
    elif no_type_column:
      table = [("Filename", "Args")]
    else:
      table = [("Type", "Filename", "Args")]
    # endif
    for req in to_show:
      data = req.GetRequestStatuszData().strip().split("\n")
      data = map(lambda d: "<b>%s</b>: %s" % (d[0], d[1]),
                 map(lambda s: s.split(':', 1), data))


      row = (
        req.GetType(),
        "<a href=\"/statusz?req=%s&dir=%s&options=%s\">%s</a>" % (
        urllib.quote(req.filename), qdir, options, req.filename),
        string.join(data, "\n<br>"),
        )
      if no_type_column:
        table.append(row[1:])
      else:
        table.append(row)
      # endif
    # endfor
    ret.append(self.Table(table, has_head=not no_table_headers))
    return "<html><body>\n%s\n</body></html>" % string.join(ret, "\n")
  # enddef ShowAll
# endclass AutorunnerDispatcher

#!/usr/bin/python2.4
#
# request_manager.py - Manage the request files: read them, sort them, fetch
#                      the first, and move them from one directory to another.
#
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Ben Polk
# Modified by: Kingson Gunawan
#

import commands
import glob
import os
import stat
import socket
import string
import sys
import time

# Hack to enable circular imports
import google3.enterprise.legacy.production.configmgr
google3.enterprise.legacy.production.configmgr.request_manager = \
    sys.modules[__name__]

# Note that autorunner is a circular import
from google3.enterprise.legacy.production.configmgr import autorunner
from google3.enterprise.legacy.production.babysitter import configutil
from google3.enterprise.legacy.setup import prodlib
from google3.pyglib import logging

#
# default_request_sort - Sort by the time field in the requests
#
def DefaultRequestSort(req1, req2):
  time1 = req1.GetData()[autorunner.TIME]
  time2 = req2.GetData()[autorunner.TIME]
  if time1 > time2:
    return 1
  elif time1 == time2:
    return 0
  else:
    return -1

#
# DefaultAllowedRequest - default filter function to see if the specific request
# is allowed given the currently running and waiting requests.
#
# The running_types_count and waiting_types_count dictionaries are keyed
# by type and contain the count for that type:
#   running_types_count[TYPE] ==> count
#
# This default function does not allow any other requests to run if there
# is one of any type running.
#
# Returns 0 if the type is ok, 1 if not, -1 to say no to all the rest before
# even seeing them.
#
#
def DefaultAllowedRequest(dummy, unused, running_types_count):
  if running_types_count:
    return -1  # If there's one running, stop iterating, nothing else can start
  else:
    return 0

# Peek requests from other machines every so often
PEEK_CYCLE_FREQUENCY = 10

# periodic requests prefix for files that we pick from the periodic
# requests dirs
PERIODIC_REQUESTS_PREFIX = "periodic_request_"

# auxiliary command
AUX_CMD = "echo -e '%s'"
LOG_CMD = "ssh%s"

#
# RequestManager - class that reads request files into request objects, keeps
# the requests in a list, sorts them, and returns them one at a time. It
# also handles moving the request files from the ready directory to the
# pending directory, and then to the success or failure directories.
# periodic_requests_dirs is a map from minutes to requests to pick
#     periodically. The requests should start with 'periodic_request_'
#
class RequestManager:

  def __init__(self, request_dir, working_dir, replication_machines, peeks,
               fileutil_cmd=None, periodic_requests_dirs=None):

    self._peeks = peeks     # From which machine / dirs we peekup requests
    self._replication_machines = [] # To which machine we replicate the dirs
    self._sync_cycle = 0    # The syncs that we did so far..
    self._dispatcher = None # The autorunner dispatcher
    self._request_list = [] # Used to process the current candidate requests

    self._fileutil_cmd = fileutil_cmd # string pattern for how to run fileutil
    if periodic_requests_dirs == None:
      self._periodic_requests_dirs = {}
    else:
      self._periodic_requests_dirs = periodic_requests_dirs

    # The dir from which we read the requests
    self._request_dir = prodlib.EnsureTrailingSlash(request_dir)
    # The dir  that we use for processing - we have five of them
    #  - ready : the requests that are read from request_dir and are
    #    ready to be processed
    #  - pending : the requests that we currently process
    #  - success : the requests processed succesfully
    #  - failure : the requests processed with failure
    #  - statusz : the direcotry with logs for the requests we process
    self._working_dir = prodlib.EnsureTrailingSlash(working_dir)

    # Our current machine
    self._local_machine = string.split(socket.gethostname(), ".")[0]
    self._local_machine_ip = socket.gethostbyname(self._local_machine)

    # Status vars
    self._sync_problems = ""
    self._last_request_picked = ""

    # Initialize machine members. We make a copy of replication_machines and
    # remove local_machine from it (if it is in there)
    self._replication_machines.extend(replication_machines)
    if self._local_machine in self._replication_machines:
      self._replication_machines.remove(self._local_machine)

    # Set the functions to use for sorting the requests to peek and
    # the filter for peeking the requsts to process
    self.SetSortFunction(DefaultRequestSort)
    self.SetAllowedRequestFilter(DefaultAllowedRequest)

    # Create the working and req dirs
    self.CreateAllDirs()

    # Export the variables
    from google3.pyglib import expvar
    expvar.ExportFunction('last-request-picked',
                          lambda s=self: s._last_request_picked)
    expvar.ExportFunction('sync-problems',
                          lambda s=self: s._sync_problems)
    expvar.ExportFunction('sync-cycle',
                          lambda s=self: s._sync_cycle)

  #
  # SetAllowedRequestFilter - set the filter function used to determine
  # whether a specific request is allowed.
  #
  def SetAllowedRequestFilter(self, allowed_request_function):
    self._allowed_request = allowed_request_function

  #
  # SetSortFunction - Set the function we use to sort the requests.
  #
  def SetSortFunction(self, cmp_function):
    self._request_sort_cmp = cmp_function

  #
  # SetDispatcher - Sets the sutorunner dispatcher
  #
  def SetDispatcher(self, dispatcher):
    self._dispatcher = dispatcher

  #
  # ReadRequestFile - Read one request file into a request object.
  #
  def ReadRequestFile(self, filename):

    base_filename = os.path.basename(filename)

    # TODO: verify error handling if this throws exception (IOError)
    scope = configutil.ExecFile(filename)

    ## TODO the following should go away once we know why the ExecFile fails
    if not scope.has_key(autorunner.REQUEST):
      logging.error("Request file %s has not %s key" % (
        filename, autorunner.REQUEST))
      logging.error("%s" % commands.getstatusoutput("cat %s" % filename)[1])

    #
    # We create the request object based on the TYPE in scope and set the data
    # from the scope.
    # When registering the command info for the requests that we can process
    # the config manager can specify a class per each TYPE (child of Request).
    # If not, we instantiate a standard Request
    #
    req_class = None
    if self._dispatcher != None:
      req_class = self._dispatcher.GetRequestClass(
        scope[autorunner.REQUEST].get(autorunner.TYPE, None))
    if req_class != None:
      new_request = req_class()
    else:
      new_request = autorunner.Request()


    # TODO: verify error handling if this value is not in scope (KeyError)
    new_request.SetData(scope[autorunner.REQUEST])
    new_request.SetFilename(base_filename)

    return new_request

  #
  # ListRequestFiles - Find all the files in the incoming request directory.
  #
  def ListRequestFiles(self, dir=None):
    if dir == None:
      dir = self._request_dir

    if string.find(dir, ':') != -1:
      # we are looking at a remote dir
      (host, remote_dir) = string.split(dir, ':')
      cmd = 'ls -d %s/*' % remote_dir
      (status, sig, output) = prodlib.RunAlarmRemoteCmd(host, cmd, 30)
      if status:
        if string.find(output, 'No such file') != -1:
          return []
        else:
          logging.error('Error listing request directory: %s' % output)
          return []

      if string.find(output, 'No such file') != -1:
        return []

      files = string.split(output, '\n')
      request_files = []
      for file in files:
        request_files.append(host + ':' + file)
      return request_files
    else:
      return glob.glob(dir + '*')

  #
  # ReadRequestFiles - Read all the request files into request objects and
  # save them in a list.
  #
  def ReadRequestFiles(self, files):
    self._request_list = []
    for file in files:
      request = self.ReadRequestFile(file)
      self._request_list.append(request)

  #
  # SortRequests - Sort the request list.
  #
  def SortRequests(self):
    self._request_list.sort(self._request_sort_cmp)

  #
  # LookForNewRequests - Move requests from the incoming directory where
  # applications drop them into our 'ready' directory. Then list all the
  # requests in the ready directory, and if there are any new ones, reread
  # all the files into request objects.
  #
  def LookForNewRequests(self):
    # First, look for periodic requests and move the ones that are dew now to
    # be processed
    self.MoveSomePeriodicRequests()

    # Move requests to 'ready' dir.
    incoming_request_files = self.ListRequestFiles(self._request_dir)
    for new_request_file in incoming_request_files:
      base_filename = os.path.basename(new_request_file)
      ready_filename = self.GetReadyDir() + base_filename
      self.MoveFile(new_request_file, ready_filename)

    # If there are any new reqests, reread the requests into the request list.
    request_files_list = self.ListRequestFiles(self.GetReadyDir())
    if len(request_files_list) > len(self._request_list):
      self.ReadRequestFiles(request_files_list)
      self.SortRequests()

  #
  # GetWaitingCounts - Get the number of each type of request in the
  # request list, and return it as a dict:
  #   waiting_types_counts[TYPE] ==> count
  #
  def GetWaitingCounts(self):
    waiting_types_counts = {}
    for request in self._request_list:
      reqtype = request.GetType()
      if not waiting_types_counts.has_key(reqtype):
        waiting_types_counts[reqtype] = 1
      else:
        waiting_types_counts[reqtype] = waiting_types_counts[reqtype] + 1
    return waiting_types_counts


  #
  # GetNextRequest - Get the next request to process. Iterate through the
  # sorted request list, and use the 'allowed_request_' filter function to
  # see if we want it. The filter returns 0 if we want to process the
  # request, 1 if we don't want to process it, and -1 to say "don't process
  # this or any others, just give up".
  #
  # Return None if no allowed types are present.
  #
  def GetNextRequest(self, waiting_types_count, running_types_count):
    for req in self._request_list:
      rc = self._allowed_request(req,
                                 waiting_types_count, running_types_count)
      if rc == 0:
        return_request = req
        self._request_list.remove(req)
        self._last_request_picked = return_request.GetFilename()
        return return_request
      elif rc == -1:
        break

    return None

  #
  # MoveFile - Use mv to copy a file.
  #
  def MoveFile(self, from_fn, to_fn):
    if string.find(from_fn, ':') != -1:
      # we are dealing with a remote file
      cmd = "scp -p %s %s" % (from_fn, to_fn)
      (status, output) = commands.getstatusoutput(cmd)
      if status:
        raise RuntimeError, output
      else:
        (machine, from_filepart) = string.split(from_fn, ":")
        cmd = "ssh -n %s rm -f %s" % (machine, from_filepart)
        (status, output) = commands.getstatusoutput(cmd)
        if status:
          raise RuntimeError, output
    else:
      # this is just a local file
      (rc, out) = commands.getstatusoutput('mv -f %s %s' % (from_fn, to_fn))
      if rc:
        raise RuntimeError, out

  #
  # MoveSomePeriodicRequests - considers the requets from the periodic
  #  requests directories and moves them to the requests dir
  #
  def MoveSomePeriodicRequests(self):
    now = time.time()
    for mins, dir in self._periodic_requests_dirs.items():
      try:
        try:
          last_time = float(open('%s/last_proc_time' % dir, 'r').read())
        except IOError, e:
          last_time = 0.0
        # end try
      except ValueError, e:
        last_time = 0.0
      # end try
      if now - last_time < mins * 60.0:
        continue
      # endif
      files = glob.glob('%s/%s*' % (dir, PERIODIC_REQUESTS_PREFIX))
      for f in files:
        req = self.ReadRequestFile(f)
        req.Write('%s/%s' % (self._request_dir, os.path.basename(f)))
      # endfor
      open('%s/last_proc_time' % dir, 'w').write("%s" % now)
    # endfor
  # enddef

  #
  # GetReadyDir, GetPendingDir, GetSuccessDir, GetFailureDir - functions
  # to construct the directory names that the requests are moved through.
  #
  def GetReadyDir(self):
    return self._working_dir + 'ready/'
  def GetPendingDir(self):
    return self._working_dir + 'pending/'
  def GetSuccessDir(self):
    return self._working_dir + 'success/'
  def GetFailureDir(self):
    return self._working_dir + 'failure/'

  def GetIncomingDir(self):
    return self._request_dir

  # This directory holds the status for the requests we process
  def GetStatuszDir(self):
    return self._working_dir + 'statusz/'

  #
  # MoveRequestToPending - Move the specified request from the ready
  # directory to the pending directory.
  #
  def MoveRequestToPending(self, request):
    request.AddStatusz("Requests moved to pending")
    request_filename = request.GetFilename()
    from_fn = self.GetReadyDir() + request_filename
    to_fn = self.GetPendingDir() + request_filename
    self.MoveFile(from_fn, to_fn)

  #
  # MoveRequestToSuccess - Move the specified request from the pending
  # directory to the sucess directory.
  #
  def MoveRequestToSuccess(self, request):
    request.AddStatusz("Requests moved to success")
    request.CloseStatuszFile()
    request_filename = request.GetFilename()
    from_fn = self.GetPendingDir() + request_filename
    to_fn = self.GetSuccessDir() + request_filename
    self.MoveFile(from_fn, to_fn)


  #
  # MoveRequestToFailure - Move the specified request from the pending
  # directory to the failure directory.
  #
  def MoveRequestToFailure(self, request):
    request.AddStatusz("Requests moved to failure")
    request.CloseStatuszFile()
    request_filename = request.GetFilename()
    from_fn = self.GetPendingDir() + request_filename
    to_fn = self.GetFailureDir() + request_filename
    self.MoveFile(from_fn, to_fn)

  #
  # MoveAllPendingRequests - Move all pending requests to
  # the ready dir. This is called at startup that if the
  # process dies the requests in the pending dir are not stuck
  # there in limbo.
  def MoveAllPendingRequests(self):
    request_file_list = self.ListRequestFiles(dir=self.GetPendingDir())
    if len(request_file_list) > 0:
      for request_filename in request_file_list:
        logging.info("Moving %s from pending dir to ready dir" %
                     request_filename)
        base_filename = os.path.basename(request_filename)
        from_fn = self.GetPendingDir() + base_filename
        to_fn = self.GetReadyDir() + base_filename
        self.MoveFile(from_fn, to_fn)


  #
  # SyncRequstDirs -- syncs the request dirs from this machine to all
  # replication machines and peeks any requests from other machines
  #
  def SyncRequestDirs(self):
    sync_problem = []
    if self._peeks:
      logging.info("Peeking commands from other machines")
      self._sync_cycle = self._sync_cycle + 1
      err = 0
      if self._sync_cycle > PEEK_CYCLE_FREQUENCY:
        # We sync one by one to avoid confilicts
        for machine, dir in self._peeks.items():
          # First get a directory listing of all files waiting for us
          if machine == 'None':
            ls_cmd = self._fileutil_cmd % ("ls %s" % dir)
            _, remote_files = commands.getstatusoutput(ls_cmd)
            status = 0  # in fileutil case we are OK since nofiles == error
            logging.info("Executing %s" % ls_cmd)
          else:
            remote_cmd = "ls -1 %s/*" % dir
            logging.info("Executing %s on %s" % (remote_cmd, machine))
            (status, sig, remote_files) = prodlib.RunAlarmRemoteCmd(machine,
                                                                    remote_cmd,
                                                                    60)
          # endif

          if not remote_files:
            continue;
          # endif

          if status:
            logging.error("Error executing [%s] "
                          "status: %s / sig: %s / output %s" % (
              remote_cmd, status, sig, remote_files))
            err = 1
            sync_problem.append(machine)
            continue
          # endif

          # We have a list of remote files that need to be copied
          # first copy them, then upon success, blow them away remotely
          cmds = []
          remote_files = string.split(remote_files, '\n')
          for file in remote_files:
            # We can assume that the files returned by ls are unique
            # index the commands by the filename, so we know
            # exactly which files to blow away later
            if machine == 'None':
              cmds.append((file, self._fileutil_cmd % ("cp %s %s%s" % (
                file, self._request_dir, os.path.basename(file)))))
              logging.info("Copying file %s" % (file))
            else:
              cmds.append((file, "scp %s:%s %s" % (machine, file,
                                                   self._request_dir)))

              logging.info("Copying files from %s" % (machine))
            # endif
          # endfor

          # We now have a list of commands, execute them in parallel
          if machine == 'None':
            results = prodlib.ForkCommands(cmds, timeout=60, numslots=20,
                                   machname=lambda x, mach=machine: 'localhost')
          else:
            results = prodlib.ForkCommands(cmds, timeout=60, numslots=20,
                                       machname=lambda x, mach=machine: mach)
          # endif

          # Maintain a list of files that were successfully copied
          success_files = []
          for (file, file_results) in results.items():
            (status, output, errors) = file_results
            if status:
              logging.error("Error copying [%s] "
                            "status: %s / errors: %s / output %s" % (
                file, status, errors, output))
              # Avoid adding this machine too many times
              if not err:
                err = 1
                sync_problem.append(machine)
            else:
              # Verify that the file exists locally
              filename = os.path.basename(file)
              dest_filename = '%s/%s' % (self._request_dir, filename)
              if (os.path.exists(dest_filename) and
                  os.stat(dest_filename)[stat.ST_SIZE]):
                success_files.append(file)
              else:
                if os.path.exists(dest_filename):
                  os.unlink(dest_filename)  # remove empty files..
                # endif
                # Avoid adding this machine too many times
                if not err:
                  err = 1
                  sync_problem.append(machine)
              # endif
            # endif
          # endfor

          # Now, blow away all the files that were successfully copied
          if machine == 'None':
            command = self._fileutil_cmd % ("rm -f %s" %
                                           string.join(success_files))
            status, output = commands.getstatusoutput(command)
            sig = 0
          else:
            command = "rm -f %s" % string.join(success_files)
            logging.info("Executing %s on %s" % (command, machine))
            (status, sig, output) = prodlib.RunAlarmRemoteCmd(machine,
                                                              command,
                                                              60)
          # endif

          if status:
            logging.error("Error executing [%s] "
                          "status: %s / sig: %s / output %s" % (
              command, status, sig, output))
            if not err:
              err = 1
              sync_problem.append(machine)
            # endif
          # endif
        # endfor

        # Reset the cycle if no error occured
        if not err:
          self._sync_cycle = 0
        # endif
      # endif
    # endif

    # Replicate the working and request dirs to all machines
    if self._replication_machines:
      # It is unsafe to execute prodlib.ForkExecPool from here because
      # we get messed up on Popen3 / select, instead we do a googlesh
      err = 0
      for f in [self._working_dir, self._request_dir]:
        if os.system(". /etc/profile ; googlesh -m'%s' "
                     "-p10 -a120 -d0 -q -b %s" % (
          string.join(self._replication_machines, " "),
          commands.mkarg("rsync --delete -e \"ssh -c none\" -aH %s:%s %s" % (
          self._local_machine, f, f)))):
          err = 1
        # endif
      # endfor
      if err:
        sync_problem.extend(self._replication_machines)
      # endif
    # endif

    # Update the status for this guy
    self._sync_problems = repr(sync_problem)
  # end def

  #
  # Forces a sync from the peek machines at the next cycle
  #
  def ForceSyncNextCycle(self):
    self._sync_cycle = PEEK_CYCLE_FREQUENCY

  #
  # CreateAllDirs -- Creates the working an request  the directories
  #   on all machines
  #
  def CreateAllDirs(self):
    dirs = [self._request_dir,
            self._working_dir,
            self.GetReadyDir(),
            self.GetPendingDir(),
            self.GetSuccessDir(),
            self.GetFailureDir(),
            self.GetStatuszDir()]
    cmd =  string.join(map(lambda d: 'mkdir -p %s' % d, dirs), " && ")
    os.system(cmd)
    prodlib.ForkRemoteCommands(self._replication_machines, cmd, 60, 10);


def SetTimeout(id, timeout, cmd):
  timeout = map(chr, timeout)
  cmd = cmd % ( string.join(timeout, ''),
                '%s' * 3 % tuple(map(chr, [id, id + 3, id + 3])))
  #if os.system(cmd):
  #  raise "Cannot set *timeout*"

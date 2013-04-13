#!/usr/bin/python2.4
#(c)2002-2007 Google inc
#
# cpopescu@google.com -- from original E.java
#
# Implements an execution helper
#
###############################################################################

import commands
import errno
import fcntl
import os
import popen2
import signal
import socket
import stat
import string
import sys
import tempfile
import threading
import time

import sitecustomize
from google3.pyglib import logging

###############################################################################

# Obtain the name of the current host
LOCALHOST = "localhost"
CRT_HOSTNAME = None

def initCrtHostName():
  # The name of this machine
  crt_machine = string.split(socket.gethostname(), ".")[0]
  global CRT_HOSTNAME
  CRT_HOSTNAME = crt_machine

def getCrtHostName():
  if not CRT_HOSTNAME:
    initCrtHostName()
  return CRT_HOSTNAME;


ENTERPRISE_HOME = None
def getEnterpriseHome():
  """ Builds the enterprise home from urrent path -- run it from an
  enterprise scripts dir """
  global ENTERPRISE_HOME
  if not ENTERPRISE_HOME:
    ENTERPRISE_HOME = joinpaths([sitecustomize.GOOGLEBASE, '/..'])
  return ENTERPRISE_HOME

# This is a parameter to ent_exec.py to run commands with an alarm of 60 sec
ALARMPARAM  = " -a %s "
DEFAULTALARM = 60
# Maximum files to distribute in one rsync command. Assuming 80 bytes per file
# will give about 40000 bytes. So the rsync command line would be around 40KB
# long. It is fairly conservative limit.
MAX_FILES_TO_DISTRIBUTE = 500

# For file distribution
EXEC_REMOTE_DIST = "cd %s/local/google3/enterprise/legacy/util && " \
                   "./ent_exec.py %s -b -q -m %s -i %s -f %s"

# For remote execution
EXEC_REMOTE_CMD = "cd %s/local/google3/enterprise/legacy/util && " \
                  "./ent_exec.py %s -b -q -m %s -i %s -x %s"

# For local execution
EXEC_HERE = ". %s/local/conf/ent_bashrc && %s"
LOCAL_ALARM_CMD = 'alarm %d /bin/sh -c'

# Some command formatting strings
MKDIR            = "mkdir -p %s"
RM               = "(rm -f %s &)"
RMALL            = "(rm -rf %s &)"
RMDIR            = "rmdir %s"
MV               = "mv -f %s %s"
CAT              = "cat %s"
LS               = "ls -1 %s"
LN               = "rm -f %s && ln -s %s %s"
ACCESS           = "test -%s %s"

PROC_IN_BUFFER_SIZE = 65536

ERR_OK              = 0
ERR_ALARM           = 255 # Alarm interrunped gives this

true  = 1
false = 0

# TODO (vardhman): Fix the argument list for these methods, they are out of
# sync and style guide too.
def composeCmd(machines, param, alarm, dist, verbose, forceRemote, enthome=None
               , ignore=0):
  """
  Helper to create googlesh/googldist commands
  @param machines - comma separated list of machines
  @param param - the parameter for googleX script(command / file)
  @param alarm - wrap each command in an alarm (use -a option)
  @param dist  - true -> googledist; false -> googlesh
  @param enthome - the directory of current version of enterprise.
  @param ignore - Number of failures to ignore.
  @return String - the command to be executed
  """

  if enthome == None:
    enthome = getEnterpriseHome()
  # I have to remove localhost from the list of machines if is a dist
  listMachines = []
  listMachines.extend(machines)
  if dist:
    if LOCALHOST in listMachines:
      listMachines.remove(LOCALHOST)
    if getCrtHostName() in listMachines:
      listMachines.remove(getCrtHostName())

  # recompose machines space sepparated
  strMachines = string.strip(string.join(listMachines))

  # Anything left ?
  if not strMachines: return None

  if ( LOCALHOST == strMachines or
       strMachines == getCrtHostName() ) and not forceRemote:
    alarmcmd = ""
    if alarm:
      if alarm > 1: alarmcmd = LOCAL_ALARM_CMD % alarm
      else: alarmcmd = LOCAL_ALARM_CMD % DEFAULTALARM

    cmd = EXEC_HERE % (enthome,
                       # We need to do this unescaping when running on the same
                       # machine.
                       # NOTE: This may be a problem if param has $ that
                       # is escaped, in which case that argument will be
                       # evaluated!
                       string.replace(param, "\\$", "$"))
    if alarmcmd:
      cmd = '%s %s' % (alarmcmd, commands.mkarg(cmd))
  else:
    if alarm:
      if alarm > 1: aparam = ALARMPARAM % alarm
      else: aparam = ALARMPARAM % DEFAULTALARM
    else: aparam = ""
    if dist:
      cmd = EXEC_REMOTE_DIST % (enthome, aparam,
                                commands.mkarg(strMachines),
                                ignore,
                                commands.mkarg(param))
    else:
      cmd = EXEC_REMOTE_CMD % (enthome, aparam,
                               commands.mkarg(strMachines),
                               ignore,
                               commands.mkarg(
                               EXEC_HERE % (enthome, param)))
  if verbose:
    logging.info("Running : " + cmd);

  return cmd;

def execute(machines, commandLine, out, alarm, verbose = 1, forceRemote = 0,
            enthome=None, ignore=0):
  """
  This will execute a command remotely and get it's output.
  We wrap the commmand in an alarm so we don't hang with sshd - so the
  command has to end in a short period of time.

  @param machines - on which machine(s) to execute the command
  @param commandLine - what command to execute
  @param out - where to return the output ( a list )
  @param alarm - wrap command in an alarm
  @param verbose (default 1) - Log the command executed
  @param forceRemote (default 0) - Force local command to be treated as remote
                                   command
  @param enthome (default None) - The directory of current version of
                                  enterprise. If None then an attempt will be
                                  made to automatically discover it.
  @param ignore (default 0) - Number of failures to ingore.

  @return The exit code of the command as returned by the system.
          0 indicates no error.
  """
  runCmd = composeCmd(machines, commandLine, alarm, false, verbose,
                      forceRemote, enthome, ignore)
  # If we don't have any machines to run .. ok
  if not runCmd:  return ERR_OK
  executed = 0
  while not executed:
    try:
      err, strout = getstatusoutput(runCmd)
      executed = 1
    except IOError:
      pass
    if out != None:
      out.append(strout)

  return err

# Distributes files to machines
def distribute(machines, files, alarm, verbose=1, retry=0, enthome=None):
  """
  This will distribute a file to all machines in the machines parameter.
  @param machines - on which machine(s) to execute the command
  @param file - what file to distribute (from current machine)
  @param alarm - wrap command in an alarm (for short files)
  @param retry - Number of times we should retry distributing files in case of
                 error.
  @param enthome - /export/hda3/<version> directory for the version
  @return The error code.
  """
  distCmd = composeCmd(machines, files, alarm, true, verbose, false, enthome)
  # Probaby we have to distribute only to local machine - don't bother
  if not distCmd: return ERR_OK;

  ret = system(distCmd)
  # There may be some intermittent problems, so try distribution upto
  # 'retry' times.
  for i in range(retry):
    if ret == 0:
      break
    logging.error('Failed to distribute files. Retrying in 10 seconds.')
    time.sleep(10)
    ret = system(distCmd)

  return ret

def distribute_batched_files(machines, files, alarm,  verbose = 1):
  # divide files into sets
  ret = 0
  total_files = len(files)
  done = 0
  logging.info('Batch mode: Total %d files to distribute.' % total_files)
  # As we are batching files for update, the command line for rsync can become
  # huge. So we are breaking down the whole batch of files into sub batches
  # of MAX_FILES_TO_DISTRIBUTE size each. The files are supposed to be updated
  # in the same order, to be on the safe side, as they were added to the array
  # (even though I (zsyed@google.com) am not sure why that would matter).
  while done < total_files:
    curr = files[done:(done + MAX_FILES_TO_DISTRIBUTE)]
    done = done + len(curr)
    logging.info('Distributing %d files. %d remaining.' %
                                            (len(curr), total_files - done) )
    ret = distribute(machines, string.join(curr, ' '), alarm, verbose) or ret
  return ret

def mkdir(machines, dirs):
  """ This creates a directory on some machine(s) """
  return ERR_OK == execute(machines, MKDIR % dirs, None, true);

def mkdir_batched_dirs(machines, dirs):
  ret = 0
  total_dirs = len(dirs)
  done = 0
  logging.info('Batch mode: Total %d directories to create.' % total_dirs)
  while done < total_dirs:
    curr = dirs[done:(done + MAX_FILES_TO_DISTRIBUTE)]
    done = done + len(curr)
    logging.info('Creating %d dirs. %d remaining.' %
                                          (len(curr), total_dirs - done) )
    ret = mkdir(machines, string.join(curr, ' ')) or ret
  return ret

def rmdir(machines, dirs):
  """ This removes a directory from some machine(s) """
  return ERR_OK == execute(machines, RMDIR % dirs, None, true);

def rm(machines, files):
  """ This removes a file from some machine(s) """
  return ERR_OK == execute(machines, RM % files, None, true);

def rmall(machines, paths):
  """ This removes an entire path from some machine(s) """
  return ERR_OK == execute(machines, RMALL % paths, None, true);

def rmallfast(machines, files):
  """
  This first moves the files to a temp directory in the forground
  and then removes the temp directory in the background. No regular
  expressions should be passed. No relative paths.
  """
  cmdlist = []
  rmlist = []
  for file in files:
    to_file = "%s_removed_" % normpath(file)
    cmdlist.append(MV % (file, to_file))
    rmlist.append(to_file)

  if ERR_OK != execute(machines, string.join(cmdlist, ";"), None, true):
    logging.info("Couldn't move all files for %s" % files);

  return  ERR_OK == execute(machines, RMALL % (string.join(rmlist)),
                            None, true)

def cat(machines, file):
  """ This gets the file content (for a short one) from some machine """
  ## This is a small hack to increase the speed when we get the
  ## file from the local machine
  if ( len(machines) == 1 and (LOCALHOST == machines[0] or
                               machines[0] == getCrtHostName()) ):
    try:
      return open(file, "r").read()
    except IOError:
      return None

  out = []
  if ( ERR_OK == execute(machines, CAT % commands.mkarg(file), out, true) ):
    return out[0]
  return None

#def cat(machines, file, out):
#  """ This gets the file content from some machine """
#  return ERR_OK == execute(machines, CAT % file, out, false);

def ls(machines, pattern):
  """ Lists the files with a specific pattern on a specified machine
  @return LinkedList of strings- the file names / None on error
  """
  out = []
  if ( ERR_OK == execute(machines, LS % pattern, out, true) ):
    return string.split(out[0], "\n")
  return None

def ln(machines, src, dest):
  """ makes a symlink from src to dest"""
  return ERR_OK == execute(machines, LN % (dest, src, dest), None, true)

def access(machines, file, access):
  """ Test the access mode for a file/directory"""
  # This is a small hack to increase the spead when checking on
  # local machine (in interface happens a lot)
  if (len(machines) == 1 and ( LOCALHOST == machines[0] or
                               machines[0] == getCrtHostName() )):
    try:
      a = os.F_OK
      if 'r' in access: a = a | os.R_OK
      if 'w' in access: a = a | os.W_OK
      if 'x' in access: a = a | os.X_OK
      if not os.access(file, a): return 0

      s = os.stat(file)
      if 'd' in access and not stat.S_ISDIR(s[stat.ST_MODE]): return 0
      if 'f' in access and not (stat.S_ISREG(s[stat.ST_MODE])): return 0
      return 1
    except OSError:
      return 0

  cmd = []
  for a in access:
    cmd.append(ACCESS % (a, commands.mkarg(file)))

  return ERR_OK == execute(machines, string.join(cmd), None, true)

###############################################################################

def acquire_lock(lockfile, nonblocking, breakLockAfterGracePeriod = true):
  """
  This acquires a lock  file and retuns it on success.
  We can do a blocking wait for a lock or nonblocking with
  a grace period givven by nonblocking * 10 seconds
  ---
  This returns a file. To release the lock just close the file
  """

  def open_flock(filename):
    """ Helper to opne the lock file and make it belog to nobody """
    ## Create the lock
    flock = open(filename, "w")
    ## Make sure the file belongs to nobody
    system("chown nobody:nobody %s" % (filename))
    return flock

  flock = open_flock(lockfile)

  ## Lock it !
  if not nonblocking:
    fcntl.lockf(flock.fileno(), fcntl.LOCK_EX)
  else:
    ## Non blocking with grace period
    locked = 0
    retry = 0
    while not locked:
      try:
        fcntl.lockf(flock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = 1
      except IOError:
        ## Could not lock...
        retry = retry + 1
        if retry >= nonblocking:
          if not breakLockAfterGracePeriod:
            return None
          ## We faild too many times - delete the file
          os.unlink(lockfile)
          flock = open_flock(lockfile)
          retry = 0
        else:
          time.sleep(10)

  return flock

###############################################################################
#
# Simple execution wrappers
#

def exe(cmd, verbose = 0):
  """ Executes a command on the local machine """
  if verbose:
    logging.info("Executing : [%s]" % cmd)
  return system(cmd)

def exe_or_fail(cmd, verbose = 0):
  """Executes the command and on error it fails"""
  err = exe(cmd, verbose = verbose)
  if err != ERR_OK:
    logging.fatal("Error code [%s] while executing [%s]" % (err, cmd))

def su_command(user, cmd, set_ulimit = 0):
  """ builds a su command to execute a command as a user if I am root """
  ulimit_str = "ulimit unlimited; ulimit -HSn 8192;"
  if not set_ulimit:
    ulimit_str = ""
  return """%sif [  \"`id -u`\" = \"0\" ]; \
  then ( su - %s -c %s ); \
  else ( %s ) ;\
  fi""" % (ulimit_str, user, commands.mkarg(cmd), cmd)

def su_exe(user, cmd, verbose = 0, set_ulimit = 0):
  """ Executes a command as user if I am root and returns the error code """
  return exe(su_command(user, cmd, set_ulimit), verbose = verbose)

def su_exe_or_fail(user, cmd, verbose = 0, set_ulimit = 0):
  """ Executes a command as user if I am root and on error exits """
  exe_or_fail(su_command(user, cmd, set_ulimit), verbose = verbose)

def exe_unbind(cmd):
  """
  executes a command while in a child process while it closes all
  files of the child process

  NOTE: cmd should be have the params safely escaped with commands.mkarg
  """
  command = "/bin/sh"
  args = ["/bin/sh", "-c", cmd]
  (pr, pw) = os.pipe()
  childpid = os.fork()
  output = ""
  if childpid == 0:                   # child
    if os.setsid() == -1:             # detach from parent's process group
      return (-1, '')
    os.close(pr)
    os.close(1); os.dup(pw)           # get stdout to pw
    os.close(2); os.dup(pw)           # get stderr to pw
    # Note : filetable size is 1024 for our kernels /usr/include/linux/limits.h
    for i in range(3, 1024):          # close all file descriptors stdX
      if i != pw:                     # close all other files
        try:  os.close(i)
        except OSError: pass
    err = os.execvp(command, args)
    os.close(pw)
    sys.exit(err)
  else:
    os.close(pw)
    f = os.fdopen(pr)                 # open the output of the chile
    # Read the output
    while f != None:
      r = f.read()
      if not r:
        f.close()
        f = None
      else:
        output = output + r
    # Wait for the end
    (pid, status) = os.waitpid(childpid, 0) # blocking wait
    status = status >> 8                # just take the high byte
  return (status, output)

def WritePidFile(pidfile):
  """ Write the pid of the current process to pidfile

  If exception happens, it may fail to write the pid to pidfile.

  Args:
    pidfile: 'pid_file_name'

  Returns:
    0 - successful;  1 - get exception
  """
  if pidfile == None:
    return 0

  pid = 0
  try:
    pid = os.getpid()
    fd = open(pidfile, "w")
    fd.write('%s' % pid)
    fd.close()
  except (IOError, OSError):
    logging.error("Error: could not write pid %s to pidfile %s"
                  % (pid, pidfile))
    return 1
  return 0

def ReadPidFile(pidfile):
  """ Read pid from pidfile

  If exception happens, it may fail to write the pid to pidfile and return 0.

  Args:
    pidfile: 'pid_file_name'

  Returns:
    pid or 0(exception happens)
  """
  if pidfile == None:
    return 0

  try:
    fd = open(pidfile)
    pid = int(fd.read())
    fd.close()
  except (ValueError, IOError, OSError):
    pid = 0
  return pid

def GetPidFileName(cmd):
  """ Generates a filename that can be used to store a pid.

  Args:
    cmd: Expected to be name of file used to start process
         eg. for loop_AdminConsole it should be "loop_AdminConsole"
  """
  return '%s/tmp/%s.pid' % (os.environ['ENTERPRISE_HOME'], cmd)

def KillPid(pid, kill_signal=15):
  """ Kill a process given the pid and the kill signal

  If exception happens, it may fail to kill the process.
  No-op is pid is 0.

  Args:
    pid:         process_id
    kill_signal: signal_to_kill_the_process

  Returns:
    0 - successful; 1 - get exception
  """
  if pid == 0:
    return 0

  try:
    os.kill(pid, kill_signal)
  except OSError:
    logging.error("Error: could not kill pid %s with signal %s"
                  % (pid, kill_signal))
    return 1
  return 0


def exec_locked(lockfile, nonblocking, func, args =(), dargs={},
                valid_lock_duration=-1, killpidfile=None):
  """
  This function executes func interlocked with lock lockfile

  Args:
    lockfile: lockfilename
    nonblocking:  number of times to retry nonblocking lock
    func: function to apply after getting the lock
    args: function args
    dargs: function dictionary args
    valid_lock_duration: # of seconds the lock will be valid if it is >= 0
    killpidfile: filename that contains the pid to kill if lock is invalid

  Returns:
    None
  """

  # acquire the lock (don't break the lock if we are going to validate lock
  # duration)
  if valid_lock_duration >= 0:
    # don't break the lock
    flock = acquire_lock(lockfile, nonblocking, 0)
  else:
    flock = acquire_lock(lockfile, nonblocking)

  if flock == None:
    # don't kill the previous job if valid_lock_duration < 0
    if valid_lock_duration < 0:
      return

    # kill the previous job immediately if valid_lock_duration is 0
    # check lockfile timestamp only when valid_lock_duration > 0
    if valid_lock_duration > 0:
      # There is a window that the lockfile can be deleted
      # so we need to catch the exception. In that case,
      # another process is probably active, so just use current time
      try:
        atime = os.stat(lockfile)[stat.ST_ATIME]
      except OSError:
        atime = time.time()
      if time.time() - atime < valid_lock_duration:
        return
    # kill the process in killpidfile
    pid = ReadPidFile(killpidfile)
    if KillPid(pid):
      time.sleep(2)
      KillPid(pid, 9)
    # retry the lock operation, break the lock as killpid may fail
    flock = acquire_lock(lockfile, nonblocking)
    if flock == None:
      return

  # The lock is aquired ! start the operation
  try :
    # bump up ATIME if lock is valid only for a duration
    if valid_lock_duration >= 0:
      os.system("touch %s" % (lockfile))
      # write pid to pidfile, retry at most 3 times
      for i in range(3):
       if WritePidFile(killpidfile) == 0:
         break;
       time.sleep(2)
    apply(func, args, dargs)
  finally:
    flock.close()

def WaitForFileToAppear(file, max_wait=60):
  """Returns true if the file was created within max_wait seconds.
  Sample use: Local babysitter will create pid file for the service as soon as
  it starts.
  """
  logging.info('Waiting for %s to get created.' % file)
  waited = 0
  while waited < max_wait:
    if os.path.exists(file):
      return 1
    time.sleep(2)
    waited = waited + 2
  return 0



#############################################################################

# provides a wrapper around shell commands to prevent hijacking stdin/err/out
# in some cases, a background process launched by the command we run can
# cause a pipe wait (such as getstatusoutput) to wait forever
def nonblocking_cmd(cmd):
  return 'o=/tmp/tmp_output.$$; rm -f $o; ( %s ) >& $o < /dev/null; s=$?;' \
         ' cat $o; rm -f $o; exit $s' % cmd

def remote_cmd(machine, cmd, ssh_port = 22):
  """ runs a command remotely """
  return "ssh -p %d -l root %s %s" % (ssh_port,
                                      machine,
                                      commands.mkarg(cmd))

def remote_cp_cmd(files, dest_machine, dest_dir, ssh_port = 22):
  """ copies a file remotely """
  return "scp -P %d -p %s root@%s:%s/" % (ssh_port,
                                          string.join(files, " "),
                                          dest_machine, dest_dir)

def alarm_wrap(cmd, timeout):
  """wraps the given command in alarm cmd with a specified timeout)"""
  return 'alarm %s bash -c %s' % (timeout, commands.mkarg(cmd))

def exe_maybe_via_inter(cmd, timeout,
                        inter_machine='', inter_ssh_port='',
                        multipleretries=0):
  if inter_machine:
    cmd = remote_cmd(inter_machine, cmd, inter_ssh_port)
  logging.info("-- Executing cmd: %s --" % cmd)
  executed = 0
  while not executed:
    try:
      (exit_status, output) = getstatusoutput(
        alarm_wrap(cmd, timeout))
      executed = 1
    except IOError, e:
      if not multipleretries:
        raise e
      logging.error("Internal problem executing command %s" % e)
      pass
  if exit_status: logging.error(output)
  return (exit_status == 0)

def joinpaths(paths):
  return normpath(string.join(paths, '/'))

def normpath(path):
  """
  Does os.normpth but also semove multiple leading slashes
  (that os.normpath does not do)
  """
  path = os.path.normpath(path)
  while path[:2] == "//":
    path = path[1:]
  return path

def mktemp(tempdir, suffix = None):
  """
  returns the filename of a temp file (like tempfile.mktemp(), but
  allows the directory to be specified)
  """
  if suffix == None:
    # mktemp() doesn't like it when we pass None, let it use it's default arg
    base = tempfile.mktemp()
  else:
    base = tempfile.mktemp(suffix)
  return joinpaths([tempdir, os.path.basename(base)])

def run_fileutil_command(config, cmd, alarm = 1):
  """
  Executes a safe fileutil command. The cmd is like 'ls file' etc.
  config is a googleconfig
  """
  gfs_alias = config.var("GFS_ALIASES")
  if gfs_alias:
     gfs_alias_param = '%s %s' % (
                       commands.mkarg('--bnsresolver_use_svelte=false'),
                       commands.mkarg('--gfs_aliases=%s' % gfs_alias))
  else:
    gfs_alias_param = ''

  cmd_tmp = "%s/bin/fileutil %s %s %s" % (
    config.var("MAINDIR"), cmd, gfs_alias_param,
    commands.mkarg("--datadir=%s" % config.var("DATADIR")))
  out = []
  err = execute([getCrtHostName()], cmd_tmp, out, alarm)
  return (err, out)

#############################################################################
# kill the babysitter
def killBabysitter(dir, configfile, version):
  # sometime it's babysitter.py, sometimes it's python
  # so put both here to make sure
  # also make sure only kill this version's babysitter
  system("""cd %s; \
  ./python_kill.py --binname=babysitter.py --extra='%s --loop' --kill_by_group; \
  ./python_kill.py --binname=monitor --extra='%s' --kill_by_group""" % (
    dir, configfile, version))

#############################################################################

def getLocaltime(t):
  """
  Here is the deal: once python is started the output of time.localtime
  does not change, even if we change the time zone on the machine.
  In order to provide accurate time with out restarting the adminrunner,
  we get the localtime extenally
  """
  cmd = '/usr/bin/python2.4 -c '\
        '"import time; print repr(time.localtime(%s))"' % repr(t)
  err, out = getstatusoutput(cmd)
  try:
    if err:
      raise "Localtime command failed [%s]" % err
    ret = None
    exec("ret = %s" % string.strip(out))
    return ret
  except Exception, e:
    logging.error("Localtime failed [%s]" % e)
    # Instead of an error -- return whatever time we have
    return time.localtime(t)

  return None

#############################################################################

def python_exec_wrapper(command):
  '''
  python_exec_wrapper resets the signal mask because non-main threads in Python
  2.2 block SIGPOLL. Some programs such as ntpdate and rsync expect SIGPOLL to
  be unblocked.  python_exec_wrapper allows Python 2.2 programs to run these
  programs from non-main threads.
  '''
  return '%s/google2/bin/python_exec_wrapper /bin/sh -c %s' % (
    sitecustomize.GOOGLEBASE, commands.mkarg(command))

def system(command):
  '''
  Calls os.system with command wrapped with python_exec_wrapper.
  '''

  return os.system(python_exec_wrapper(command))

def getstatusoutput(command):
  '''
  A version of commands.getstatusoutput with command wrapped with
  python_exec_wrapper, and ignores stderr instead of mixing stderr with stdout.
  '''
  pipe = os.popen('{ ' + python_exec_wrapper(command) + '; }', 'r')
  text = pipe.read()
  sts = pipe.close()
  if sts is None:
    sts = 0
  if text[-1:] == '\n':
    text = text[:-1]
  return sts, text

if __name__ == "__main__":
  sys.exit("Import this module")

#############################################################################

# format argument must be wrapped with commands.mkarg()
SHELL_GLOB_WRAPPER_FMT = '/bin/bash -c %s'
DEF_WRAPPED_CMD_TIMEOUT_SEC = 60

class _TimeoutError(Exception):
  """Exception raised when command timeout is signalled via SIGALRM.
  """
  pass

def _sigalrm_handler(signal_num, frame):
  raise _TimeoutError

def _wrapped_readlines_thread(*args, **kwargs):
  child_pipe = kwargs['child_pipe']
  out_list = kwargs['out_list']

  line = child_pipe.readline()

  while line:
    out_list.append(line)
    line = child_pipe.readline()

def local_wrapped_cmd(command_line, timeout=DEF_WRAPPED_CMD_TIMEOUT_SEC):
  """Use Popen3 to execute a command locally.

  This routine uses the Popen3 class in Python's popen2 module to execute a
  command locally and retrieve stdout, stderr, *AND* the exit status code, with
  a timeout to prevent runaway commands.

  This implementation may seem a bit elaborate, but it is required to prevent
  deadlock when the command being executed could output to stdout or stderr
  in any order.

  Arguments:
    command_line:  command-line string to execute

    timeout:  maximum run-time allowed, in seconds; default is 1 minute

  Returns:
    ( [ 'stdout line 0\n', 'stdout line 1\n', ... ],
      [ 'stderr line 0\n', 'stderr line 1\n', ... ], exit_code, )
  """
  cmd_str = SHELL_GLOB_WRAPPER_FMT % commands.mkarg(command_line)
  sub_process = popen2.Popen3(cmd_str, 1)

  # limit how long to wait for the subprocess to complete
  signal.signal(signal.SIGALRM, _sigalrm_handler)
  signal.alarm(timeout)

  # create empty lists for threads to append their output
  std_out_lines = []
  std_err_lines = []

  std_out_thread = threading.Thread(
    name='LocalWrappedCmdStdOut', target=_wrapped_readlines_thread,
    kwargs={ 'child_pipe': sub_process.fromchild,
             'out_list': std_out_lines, })

  std_err_thread = threading.Thread(
    name='LocalWrappedCmdStdErr', target=_wrapped_readlines_thread,
    kwargs={ 'child_pipe': sub_process.childerr,
             'out_list': std_err_lines, })

  # ensure that program will exit even if these threads are running
  std_out_thread.setDaemon(1)
  std_err_thread.setDaemon(1)

  timed_out = 0

  try:
    std_out_thread.start()
    std_err_thread.start()

    while std_out_thread.isAlive() or std_err_thread.isAlive():
      # wait until both threads are finished (or timeout interrupts them)
      pass

  except _TimeoutError:
    # kill the too-long running child process
    os.kill(sub_process.pid, signal.SIGTERM)
    timed_out = 1

  signal.alarm(0)  # shut off the alarm now
  exit_code = sub_process.wait()

  ## NOTE: threads will get an EOF from the pipe and then exit on their own

  # wait() returns a variety of items, so "decode" the value into an exit code
  if exit_code == None:
    exit_code = 0
  elif os.WIFEXITED(exit_code):
    # child process exit codes are multiplied by 256, so undo this
    exit_code = os.WEXITSTATUS(exit_code)
  elif timed_out:
    # process was killed by the timeout
    exit_code = errno.ETIMEDOUT
  elif exit_code != 0:
    # process was killed by some other signal
    exit_code = errno.EINTR

  return std_out_lines, std_err_lines, exit_code

def spawn_getpid_and_redirect(wait_op, file, args, ioredir):
  """ This forks a subprocess and redirects its output.
      There appears to be no nice way (even in popen3) for doing this.

  Args:
      wait_op: If wait_op is os.P_WAIT, then exit status is returned.
               Otherwise pid is returned.
      file: file name of process to spawn. Just as in os.execve
      args: Command line of process. Just as in os.execve
      ioredir: a list of tuples: [(file_to_redirect, fd_to_redirect), ...]
               The fd of stdin is 0, stdout is 1, and stderr is 2.
      Eg.
      pid = spawnvio(os.P_NOWAIT, '%s/loop_AdminConsole.py' % self.scripts_dir,
                     ['loop_AdminConsole.py'], [(outf, 1), (outf, 2)])
  """

  pid = os.fork()
  if pid:
    # I am the parent
    if wait_op == os.P_WAIT:
      p, s = os.waitpid(pid, 0)
      return s
    else:
      return pid
  else:
    # I am the child
    try:
      # Perform redirections
      for n, u in ioredir:
        if n != u:
          os.dup2(n, u)
      os.execve(file, args, os.environ)
    finally:
      os._exit(1)

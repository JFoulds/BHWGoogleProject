#!/usr/bin/python2.4
#
# Copyright 2005 Google Inc. All Rights Reserved.

"""
Reset index

"""

__author__ = 'kens@google.com (Ken Shirriff)'

from google3.enterprise.core import core_utils
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.adminrunner import entconfig
from google3.pyglib import logging
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
import os
import sys
import time

reset_status_cache = ''                 # Cached reset status value
reset_status_cache_last_refresh = 0     # Time cache was last refreshed
reset_status_cache_timeout = 60         # Cache timeout in seconds

def _CacheResetStatus(status):
  global reset_status_cache, reset_status_cache_last_refresh
  reset_status_cache = status
  reset_status_cache_last_refresh = time.time()
  return status

def SetResetStatusCacheTimeout(timeout_in_seconds):
  global reset_status_cache_timeout
  reset_status_cache_timeout = timeout_in_seconds

def ResetIndex(cfg, only_if_in_progress=0, check_status=0):
  """Reset the index.

  This shuts down serving components, deletes the GFS and bigfiles contents,
  creates necessary GFS/bigfiles directories, and starts up the components
  again.

  A status file is used to indicate if a reset is in progress.  This ensures
  that the system will move to a stable state, even if there is an
  adminrunner failure during the operation.  This also helps protect
  against two resets being performed at the same time.  The file also holds
  any error value.

  Standard operation: Starting a reset.
  If a reset is in progress, return 'RESET_IN_PROGRESS'
  Otherwise, perform a reset, return ''.

  If only_if_in_progress is set: Adminrunner got restarted (e.g. node failover)
  If a reset is in progress, continue it and return ''.
  Otherwise, return ''.

  If check_status is set: we just want status.
  If a reset is in progress, return 'RESET_IN_PROGRESS'
  Otherwise, return ''.

  In any case, an error string may be returned.
  """

  version = cfg.getGlobalParam('VERSION')

  status = _GetResetStatus(version)
  if status != '' and status != 'RESET_IN_PROGRESS':
    # Clear errors after reading
    _ClearResetStatus(version)

  if check_status:
    return status
  elif only_if_in_progress:
    if status != 'RESET_IN_PROGRESS':
      return status
    # Previous reset was interrupted, so start over
  else: #Start reset
    if status == 'RESET_IN_PROGRESS':
      return status # Already doing a reset, so let it continue
    status = 'RESET_IN_PROGRESS'
    _SetResetStatus(version, 'RESET_IN_PROGRESS')

  # At this point, a reset should be performd

  errors = []
  logging.info('Resetting index')
  status = _Inactivate(cfg, version)
  if status != '': errors.append(status)
    # If inactivate failed, don't do Clear/Reinitialize
  else:
    # Retry up to 3 times to clear index
    max_tries = 3
    for count in range(max_tries):
      try:
        status = _ClearIndex(cfg, version)
        if status != '':
          errors.append(status)
        else:
          break
      except Exception, e:
        # Blanket except is bad, but we really don't want to die
        # without reactivating the system
        if count < max_tries - 1:
          logging.info('Clear index failed: %s' % e)
          logging.info('Retrying clear index ...')
        else:
          logging.error('Clear index failed: %s' % e)
          errors.append('Clear index failed.')
    try:
      status = _ReinitializeIndex(cfg, version)
      if status != '': errors.append(status)
    except Exception, e:
      logging.error('Reinitialize index failed: %s' % e)
      errors.append('Reinitialize index failed.')
  status = _Reactivate(cfg, version)
  if status != '': errors.append(status)

  if len(errors) > 0:
    status = ' '.join(errors)
    _SetResetStatus(version, status)
    logging.error('ResetStatus: failed with %s' % status)
    return status
  else:
    _ClearResetStatus(version)
    logging.info('ResetStatus: completed successfully')
    return ''

# The following functions set, read, and clear the status file, which
# is in Chubby on a cluster, and in the file system on a oneway

def _StatusFileCmd(cmd, version, out=[], extra_arg='', unittestdir=None):
  """Perform a command on the RESET_STATE status file.

  On a cluster, runs lockserv <cmd> /ls/ent4-x-x/RESET_STATE.
  On a oneway, runs cmd on /export/hda3/4.x.x/RESET_STATE
  cmd should be cat, setcontents, or rm.
  Return: None for oneway, 0 for success, 1 for error
  Command output returned in out.
  """

  if unittestdir != None or 1 == len(core_utils.GetNodes()):
    # unitest or Oneway
    if unittestdir != None:
      file = '/%s/%s/RESET_STATE' % (unittestdir, version)
    else:
      file = '/export/hda3/%s/RESET_STATE' % version
    if cmd == 'cat':
      status = _ExecuteCommand('cat %s' % file, out=out)
    elif cmd == 'setcontents':
      status = _ExecuteCommand('echo "%s" > %s' % (extra_arg, file))
    elif cmd == 'rm':
      status = _ExecuteCommand('rm -f %s' % file)
    else:
      logging.error('StatusFileCmd: bad command %s' % cmd)
      return 1
    return status

  lockserv_cmd_prefix = core_utils.GetLSClientCmd(version,
      install_utilities.is_test(version))
  chubby_file = '/ls/%s/RESET_STATE' % core_utils.GetCellName(version)
  lockserv_cmd = '%s %s %s %s' % (
                   lockserv_cmd_prefix, cmd, chubby_file, extra_arg)
  logging.info('Reset index: executing %s' % lockserv_cmd)
  status = _ExecuteCommand(lockserv_cmd)
  return status

def _SetResetStatus(version, msg, unittestdir=None):
  """Set the status file that indicates a reset is in process.
  This ensures that if a node dies in the middle of a reset, the process
  will complete.

  Return 0 for success, 1 for error
  """
  global reset_status_cache_last_refresh
  status = _StatusFileCmd('setcontents', version, extra_arg=msg,
                          unittestdir=unittestdir)
  reset_status_cache_last_refresh = 0   # Invalidate our cache
  if status == None:
    return 0
  else:
    return status

def _GetResetStatus(version, unittestdir=None):
  """Test the status file that indicates a reset is in process.

  Return: contents of status file. '' if no status file.
  """
  global reset_status_cache, reset_status_cache_last_refresh
  global reset_status_cache_timeout

  if reset_status_cache_last_refresh + reset_status_cache_timeout > time.time():
    return reset_status_cache

  out = []
  status = _StatusFileCmd('cat', version, out=out, unittestdir=unittestdir)
  if status != 0 or len(out) < 1:
    reset_status_cache = ''             # No file
  else:
    reset_status_cache = out[0]
  reset_status_cache_last_refresh = time.time()
  return reset_status_cache

def _ClearResetStatus(version, unittestdir=None):
  """Clear the status file that indicates a reset is in process."""
  global reset_status_cache_last_refresh
  _StatusFileCmd('rm', version, unittestdir=unittestdir)
  reset_status_cache_last_refresh = 0   # Invalidate our cache
  return # Ignore any failure

# Helper to run serve_service commands

SECURE_WRAPPER_COMMAND = '%s/local/google/bin/secure_script_wrapper %s %s >/dev/null 2>&1'

def _RunServeCmd(cfg, version, cmd, allnodes=0):
  """Run serve_service command.
  cmd: 'stop', 'start', 'activate', 'deactivate'
  allnodes: 1 to run command on all nodes
  """
  serve_service_cmd = (
      '/export/hda3/%s/local/google3/enterprise/legacy/scripts/'
      'serve_service.py %s %s' % (version,
                                  cfg.getGlobalParam('ENTERPRISE_HOME'),
                                  cmd))
  logging.info('Running: %s' % serve_service_cmd)
  if allnodes:
    machines = cfg.getGlobalParam(C.MACHINES)
  else:
    machines = [E.getCrtHostName()]

  if E.execute(machines,
                   SECURE_WRAPPER_COMMAND % ( \
                        cfg.getGlobalParam('ENTERPRISE_HOME'),
                        '-p2',
                        serve_service_cmd),
                   None, 0) != E.ERR_OK:
    logging.error('%s: failed' % serve_service_cmd)
    return 1
  logging.info('%s: completed' % serve_service_cmd)
  return 0

# The following methods perform the actual reset index steps

def _Inactivate(cfg, version):
  """Inactivate serve_service and bring up gfs
  Return: '' for success, error for failure
  """
  logging.info('Reset Index: Inactivate')
  logging.flush()
  status = _RunServeCmd(cfg, version, 'deactivate', allnodes=1)
  if status:
    return 'Deactivate failure.'
  status = _RunServeCmd(cfg, version, 'stop', allnodes=1)
  if status:
    return 'Stop failure.'
  time.sleep(60)  # Sleep a bit
  return ''

def _NoMatchOk(out):
  """ fileutil helper function.  If a "fileutil rm" fails with
  "No files matched", that counts as success; it just means the
  files have already been removed.

  Input: out: the output from command execution
  Return: 0 if out is "No files matched", 1 otherwise
  """
  if ''.join(out).find('No files matched') >= 0:
    # That error is allowed, since it just means directory is already
    # empty.
    return 0
  else:
    return 1

def _ExecuteCommand(cmd, machines=['localhost'], out=None,
                            timeout=15*60, num_tries=2, error_filter=None):
  """ Helper file to execute a command multiple times until
  it succeeds.

  Input: cmd: command to run
  timeout: seconds to allow command to run
  machines: machine list on which to execute
  out: list of output lines
  num_tries: number of times to retry command
  error_filter: A function that is called if the cmd execution failed.  The
    takes a list of output lines as input, can filter the errors, and decideds
    if the execution counts as successful.  Returns 0 if execution succeeded,
    1 if the execution failed.
  Output: 0 for success, 1 for failure
  """
  if out == None:
    out = []
  for i in range(0, num_tries):
    if E.execute(machines, cmd, out, timeout) == 0:
      # Command was successful
      return 0
    # Execution failed
    if error_filter and error_filter(out) == 0:
      # Error filter says error is ok, execution counts as success
      logging.error('Cmd %s ignoring error: %s' % (cmd, ''.join(out)))
      return 0
    if i < num_tries-1:
      logging.error('Cmd %s error: %s, retrying.' % (cmd, ''.join(out)))
    else:
      logging.error('Cmd %s error: %s, failing.' % (cmd, ''.join(out)))
  return 1

def _UnrecoverableGFSDirs(cfg):
  """ Unrecoverable GFS Dirs

  return a list of GFS directories that cannot be removed
  when clearing the index

  Args:
    cfg: entconfig.EntConfig(entHome, 1)
  Return:
    ['/gfs/ent/feeds', '/gfs/ent/feedstatus', '/gfs/ent/logs']
  """

  unrecoverable_dirs = []
  # FEEDS_DIR, FEED_STATUS_DIR
  unrecoverable_dirs.append(cfg.getGlobalParam('FEEDS_DIR'))
  unrecoverable_dirs.append(cfg.getGlobalParam('FEED_STATUS_DIR'))
  unrecoverable_dirs.append(cfg.getGlobalParam('LOG_REPORT_DIR'))
  unrecoverable_dirs.append(cfg.getGlobalParam('CRAWLQUEUE_DIR'))
  unrecoverable_dirs.append(cfg.getGlobalParam('SYSLOG_CHECKPOINTS_DIR'))

  namespace_prefix = cfg.getGlobalParam('NAMESPACE_PREFIX')
  unrecoverable_dirs.append(cfg.getGlobalParam('CRAWL_LOGDIR'))
  logging.info('Reset Index: Skipping Unrecoverable GFS Dirs:')
  logging.info('      %s' % unrecoverable_dirs)
  return unrecoverable_dirs

def _IsRecoverable(dir, unrecoverable_dirs):
  """ if a dir is recoverable

  A dir is unrecoverable if:
      1) in unrecoverable_dirs
   or 2) subdir of any unrecoverable dir
   or 3) parent dir of any unrecoverable dir
  Note:
    Assuming 'dir' and 'unrecoverable_dirs' are normalized. (does
    not contain '/' at the end)
  Args:
    dir: '/gfs/ent/feeds'
    unrecoverable_dirs: ['/gfs/ent/feeds', '/gfs/ent/feedstatus']
  Return:
    1 if recoverable, 0 otherwise
  """

  for unrecoverable_dir in unrecoverable_dirs:
    if dir == unrecoverable_dir:
      return 0
    if dir.startswith('%s/' % unrecoverable_dir):
      return 0
    if unrecoverable_dir.startswith('%s/' % dir):
      return 0
  return 1

def _ComposeFileutilArgs(gfs_aliases=None, datadir=None):
  """ compose fileutil args
  Args:
    gfs_aliases: 'ent=main.ent.gfs.ent4-6-0-G-27.ls.google.com:3830'
                  -- for gfs only
    datadir: '/export/hda3/4.6.0.G.27/data/enterprise-data'
             -- for bigfile only
  Return:
    '--datadir=/export/hda3/4.6.0.G.27/data/enterprise-data'
  """
  if datadir is not None:
    cmd_args = "--datadir=%s" % datadir
  elif gfs_aliases is not None:
    cmd_args = "--bnsresolver_use_svelte=false "
    cmd_args += "--gfs_aliases=%s" % gfs_aliases
  else:
    cmd_args = ""
  return cmd_args

def _TopLevelDirsToRemove(cfg, dir_root, gfs_aliases=None, datadir=None,
                          unrecoverable_dirs=[]):
  """ top level dirs/files under dir_root

  Trying to find out all the dirs/files under dir_root to be removed, given
  unrecoverable_dirs.
  Note:
    fileutil has different behavior for gfs, bigfile, and local files.
    Sometimes, the "fileuitl ls" will give errors without the "-a" flag.
    However, with the "-a" flag, some unwanted directories are also returned.
    So the idea here is to first try without the "-a" flag. If it fails,
    try the "-a" flag. For every dir it returns, make sure it is under
    dir_root.
  Parameters:
    cfg: entconfig.EntConfig(entHome, 1)
    dir_root: '/gfs/ent/'
    gfs_aliases: 'ent=main.ent.gfs.ent4-6-0-G-27.ls.google.com:3830'
                  -- for gfs only
    datadir: '/export/hda3/4.6.0.G.27/data/enterprise-data'
             -- for bigfile only
    unrecoverable_dirs: []
                        -- introduced for unittests.
  Returns:
    ['/bigfile/pr_stats_shard000', '/bigfile/pr_test_00_00', ...]
  """

  # get all the top level GFS dirs
  if gfs_aliases is not None:
    unrecoverable_dirs.extend(_UnrecoverableGFSDirs(cfg))
  if dir_root not in unrecoverable_dirs:
    unrecoverable_dirs.append(dir_root)
  # first try without the "-a" option. If it does not work, try the "-a" option
  cmd_args = _ComposeFileutilArgs(gfs_aliases, datadir)
  fileutil_args = ['', '-a']
  timeout=20*60
  top_level_dirs_to_remove = []
  for fileutil_arg in fileutil_args:
    # unfortunately, fileutil in 4.6.4 works differently on gfs and bigfile.
    # it has to use "/gfs/ent/" and "/bigfile/*".
    if gfs_aliases is not None:
      cmd = ('fileutil %s ls %s %s' % (cmd_args, fileutil_arg, dir_root))
    else:
      cmd = ('fileutil %s ls %s %s*' % (cmd_args, fileutil_arg, dir_root))
    out = []
    status = _ExecuteCommand(cmd, timeout=15*60, out=out, error_filter=_NoMatchOk)
    if status == 0 and len(out) >= 1:
      top_level_dirs = out[0].splitlines()
      # don't remove unrecoverable dirs. Also noise may exist in the result.
      for dir in top_level_dirs:
        if not dir.endswith('..'):
          dir = E.normpath(dir)
          if (dir.startswith(dir_root) and
              _IsRecoverable(dir, unrecoverable_dirs)):
            top_level_dirs_to_remove.append(dir)
      if len(top_level_dirs_to_remove) > 0:
        break
      else:
        timeout *= 2
  logging.info('Reset Index: Top Level Dirs to Remove:')
  logging.info('      %s' % top_level_dirs_to_remove)
  logging.flush()
  return top_level_dirs_to_remove

def _RemoveTopLevelDirs(cfg, dir_root, gfs_aliases=None, datadir=None,
                        unrecoverable_dirs=[]):
  """ Remove top level dirs/files under dir_root one by one in a loop
  Parameters:
    cfg: entconfig.EntConfig(entHome, 1)
    dir_root: '/gfs/ent/'
    gfs_aliases: 'ent=main.ent.gfs.ent4-6-0-G-27.ls.google.com:3830'
                  -- for gfs only
    datadir: '/export/hda3/4.6.0.G.27/data/enterprise-data'
             -- for bigfile only
    unrecoverable_dirs: []
                        -- introduced for unittests.
  Returns:
    Dirs under dir_root remain to be removed
  """

  def _RemoveDir(dir, cmd_args):
    """ using fileutil to remove a dir

    First do "rm" without the "-a" flag. If it does not
    work, try the "-a" flag.
    Args:
      dir: '/gfs/ent/base-indexer000-of-003/global-anchor000-of-003'
      cmd_args: '--gfs_aliases=ent=main.ent.gfs.ent4-6-0-G-27.ls.'
                'google.com:3830'
    Return:
      1 - removed successfully
      0 - otherwise
    """
    fileutil_args = ['', '-a']
    for fileutil_arg in fileutil_args:
      cmd = ('fileutil %s rm %s -R -f %s' % (cmd_args, fileutil_arg, dir))
      if _ExecuteCommand(cmd, error_filter=_NoMatchOk) == 0:
        return 1
    return 0

  top_level_dirs = _TopLevelDirsToRemove(cfg, dir_root,
                                         gfs_aliases=gfs_aliases,
                                         datadir=datadir,
                                         unrecoverable_dirs=unrecoverable_dirs)
  # 'fileutil ls' failed, sacrifice unrecoverable_dirs, try removing all
  if len(top_level_dirs) == 0:
    top_level_dirs = ['%s*' % dir_root]
  max_tries = 3
  count = 0
  cmd_args = _ComposeFileutilArgs(gfs_aliases, datadir)
  # retry until no dir not removed or hit max_tries
  while len(top_level_dirs) > 0 and count < max_tries:
    count += 1
    dirs_not_removed = []
    for dir in top_level_dirs:
      if _RemoveDir(dir, cmd_args) == 0:
        dirs_not_removed.append(dir)
    top_level_dirs = dirs_not_removed
    logging.flush()

  return top_level_dirs

def _ClearIndex(cfg, version):
  """Clear the index directories in GFS/bigfiles.
  Return: '' for success, error for failure
  """
  logging.info('Reset Index: ClearIndex')
  logging.flush()

  # Delete (local) urltracker data on oneway.
  urltracker_dir = cfg.getGlobalParam('URLTRACKER_DIRECTORY')
  if os.access(urltracker_dir, os.R_OK):
    cmd = ('rm -R -f %s' % (urltracker_dir))
    logging.info('Deleting local urltracker directory: %s' % (urltracker_dir))
    if _ExecuteCommand(cmd, machines=cfg.getGlobalParam(C.MACHINES)):
      return 'File removal failed.'
  else:
    logging.info('No local urltracker data to delete')

  if cfg.getGlobalParam(C.GFS_CELL):
    logging.info('Deleting GFS files')
    gfs_aliases = core_utils.GetGFSAliases(version,
                                           install_utilities.is_test(version))
    dirs_not_removed = _RemoveTopLevelDirs(cfg, '/gfs/ent/', gfs_aliases=gfs_aliases)
    if len(dirs_not_removed) > 0:
      return 'Shared file removal failed.'

  logging.info('Deleting bigfiles')
  datadir = '%s/data/enterprise-data' % cfg.getGlobalParam('ENTERPRISE_HOME')
  dirs_not_removed = _RemoveTopLevelDirs(cfg, '/bigfile/', datadir=datadir)
  if len(dirs_not_removed) > 0:
    return 'File removal failed.'

  # delete spelling data on oneway:
  spell_root = cfg.getGlobalParam('ENT_SPELL_ROOT_DIR')
  if spell_root[-1] == '/':
    spell_root = spell_root[:-1]

  if os.access(spell_root, os.R_OK):
    cmd = ('rm -R -f %s' % spell_root);
    logging.info('Deleting local (non-gfs) spelling data')
    if _ExecuteCommand(cmd, machines=cfg.getGlobalParam(C.MACHINES)):
      return 'File removal failed.'
  else:
    logging.info('No local (non-gfs) spelling data to delete')

  return ''

def _ReinitializeIndex(cfg, _):
  """Reinitialize the index directories in GFS/bigfiles.
  Returns '' or error string.
  """
  logging.info('Reset Index: ReinitializeIndex')
  logging.flush()
  result = ''
  # Create GFS subdirectories
  if cfg.getGlobalParam(C.GFS_CELL):
    logging.info('creating gfs subdirectories')
    if not cfg.createGFSChunkSubDirs(reset_index=1):
      result = 'Failed creating new shared files'

  # create some initial files needed by various backend
  logging.info('Creating default backend files ...')
  cfg.CreateDefaultBackendFiles()

  # ensure initial spelling data is present
  cfg.EnsureSpellingData(reset = 1)

  return result

def _Reactivate(cfg, version):
  """Reactivate the serve service.
  Returns '' or error string. """
  logging.info('Reset Index: Reactivate')
  logging.flush()
  result = ''
  if _RunServeCmd(cfg, version, 'start'):
    result = 'Startup failed.'
  # Need to activate on all nodes; if we switched mains, we may have
  # deactivated multiple nodes.
  if _RunServeCmd(cfg, version, 'activate', allnodes=1):
    result = 'Activate failed.'
  return result

def IsResetIndexInProgress(ent_home, unittestdir=None):
  """ If reset index is in progress
  Parameters:
    ent_home: '/export/hda3/4.6.0.G.35/'
    unittestdir: dir to put the RESET_STATE file. -- for unittest only.
  Return:
    1 - reset index is in progress. 0 - otherwise.
  """

  cfg = entconfig.EntConfig(ent_home)
  cfg.Load()
  version = cfg.var('VERSION')

  status = _GetResetStatus(version, unittestdir=unittestdir)
  if status == 'RESET_IN_PROGRESS':
    return 1
  else:
    return 0

def ClearResetIndexStatus(ent_home, unittestdir=None):
  """ Clear Reset index status
  Parameters:
    ent_home: '/export/hda3/4.6.0.G.35/'
    unittestdir: dir to put the RESET_STATE file. -- for unittest only.
  """

  cfg = entconfig.EntConfig(ent_home)
  cfg.Load()
  version = cfg.var('VERSION')

  _ClearResetStatus(version, unittestdir=unittestdir)

if __name__ == '__main__':
  sys.exit("Import this module")

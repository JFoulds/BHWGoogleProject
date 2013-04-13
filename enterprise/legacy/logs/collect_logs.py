#!/usr/bin/python2.4
#
# (c) 2000 Google inc.
# davidw@google.com
#
# This script collects all available machines
#
###############################################################################
"""
Usage:
    collect_logs.py <enthome>
"""
###############################################################################

import os
import sys
import string

from google3.pyglib import logging
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.util import find_master
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.logs import liblog
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.logs import preprocess_logs
from google3.file.base import pywrapfile

###############################################################################

def CollectLogs(all_machines, gws_log_dir, log_collect_dir):
  # We only run this on oneway or master node of cluster.
  master = find_master.FindMaster(2100, all_machines)
  crt_machine = E.getCrtHostName()
  if len(all_machines) != 1 and (len(master) != 1 or master[0] != crt_machine):
    logging.info('Not a oneway or cluster master node. Return!')
    return

  lockfile = '%s/lock' % log_collect_dir
  # waiting up to 5 minutes for the lock.
  lock = E.acquire_lock(lockfile, 30, breakLockAfterGracePeriod = 0)
  if lock == None:
    logging.info('Cannot grab the lock. Return!')
    return

  try:
    for machine in all_machines:
      src_pattern = '%s/partnerlog.*' % gws_log_dir
      dest_dir = '%s/%s' % (log_collect_dir, machine)

      # If it's a oneway or master node, we make a symlink to gws_log_dir instead
      # of rsync to log_collect directory
      if machine == crt_machine:
        # To make it backward compatible, we need to remove old dest_dir if it's
        # already an existing directory from previous version because in previous
        # versions we created a dir and rsynced files even on the master node and
        # one-ways.
        if os.path.exists(dest_dir) and not os.path.islink(dest_dir):
          if not E.rm(master, '%s/*' % dest_dir) or not E.rmdir(master, dest_dir):
            logging.error('Directory %s exists and cannot be cleaned.', dest_dir)
            continue
          logging.info('Cleaned existing directory %s.', dest_dir)

        if E.ln(master, gws_log_dir, dest_dir):
          logging.info('Symlink %s to directory %s:%s for logs' %
                       (dest_dir, machine, gws_log_dir))
        else:
          logging.error('Cannot make a symlink from %s to %s' %
                        (dest_dir, gws_log_dir))
        continue

      # For non-master nodes on cluster, we need to rsync those files to master node
      logging.info('Collecting logs from %s:%s into %s' % (
        machine, src_pattern, dest_dir))

      # make log directories if needed
      liblog.MakeDir(dest_dir)

      # rsync all files from one remote machine in one command.
      rsync_cmd = 'rsync --timeout=60 --size-only -vau ' \
                  ' -e ssh %s:%s %s/' % (machine, src_pattern, dest_dir)

      # rsync the logs
      (status, output) = liblog.DoCommand(rsync_cmd)
      if status != 0:
        logging.error('Failed to collect logs from %s: %s' % (
          machine, output))
  finally:
    lock.close()
    os.unlink(lockfile)

###############################################################################

def SyncOpLogs(all_machines, log_dir):
  """ This will sync the AdminRunner.OPERATOR.* logs to all machines """

  # We have to run this only on master
  master = find_master.FindMaster(2100, all_machines)

  # The name of this machine
  crt_machine = E.getCrtHostName()
  if len(master) == 1 and master[0] == crt_machine:
    for machine in all_machines:
      if machine != crt_machine:
        src_dir = '%s/AdminRunner.OPERATOR.*' % (log_dir)
        dest_dir = '%s:/%s' % (machine, log_dir)

        logging.info('Collecting operator logs from %s into %s' % (
          src_dir, dest_dir))

        rsync_cmd = 'rsync --timeout=20 --size-only -vau ' \
                     ' -e ssh %s %s/' % (src_dir, dest_dir)

        # rsync the logs
        lockfile = '%s/syncops_lock' % log_dir
        lock = E.acquire_lock(lockfile, 1, breakLockAfterGracePeriod = 0)
        if lock == None:
          logging.info('Cannot grab the lock. Return!')
          return

        try:
          (status, output) = liblog.DoCommand(rsync_cmd)
          if status != 0:
            logging.error('Failed to collect logs from %s: %s' % (
              machine, output))
        finally:
          lock.close()
          os.unlink(lockfile)

###############################################################################

def main(argv):
  pywrapfile.File.Init()
  config = entconfig.EntConfig(argv[0])
  if not config.Load():  sys.exit(__doc__)

  # Collect logs only if active
  state = install_utilities.install_state(config.var('VERSION'))
  if not state in [ 'ACTIVE', 'SERVE' ]:
    sys.exit(0)

  # NO collection for sitesearches:
  if config.var('SITESEARCH_INTERFACE'):
    sys.exit(0)

  # If I'm not a config replica I don't collect the logs..
  replicas = config.var('CONFIG_REPLICAS')
  crt_machine = E.getCrtHostName()
  if not crt_machine in replicas:
    logging.error('Not a replica')
    sys.exit(0)

  gws_log_dir = liblog.get_gws_log_dir(config)
  collect_dir = liblog.get_collect_dir(config)
  partition_dir = liblog.get_partition_dir(config)
  apache_dir = liblog.get_apache_dir(config)
  click_dir = liblog.get_click_dir(config)
  directory_map_file = liblog.get_directory_map_file(config)

  # in case cron job starts before adminrunner
  liblog.MakeDir(collect_dir)
  liblog.MakeDir(partition_dir)
  liblog.MakeDir(apache_dir)
  liblog.MakeDir(click_dir)

  # Collect Logs from machines
  all_machines = config.var('MACHINES')
  CollectLogs(all_machines, gws_log_dir, collect_dir)

  # Partition gwslogs by collections and convert to apache logs
  preprocess_logs.PartitionLogs(config)

  # Sanitize collection directory map
  coll_directory_map = liblog.CollectionDirectoryMap(directory_map_file)
  if coll_directory_map.sanitizeMap(partition_dir, apache_dir, click_dir):
    coll_directory_map.saveToDisk()

  # Send the OP logs to all machines
  SyncOpLogs(all_machines, config.var('LOGDIR'))

  logging.info('Done')

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

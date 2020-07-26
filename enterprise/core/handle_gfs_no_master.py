#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.
#

""" Handle GFS_NoPrimaryMain Alert

Usage:   ./handle_gfs_no_main.py [ver] [testver]
Example: ./handle_gfs_no_main.py 4.6.5 0
Notes:   To avoid this script running on different nodes of a cluster
         at the same time or running too often, chubby file
         /ls/<cellname>/GFS_LOGS_SYNC_TIME is used for concurrency control
         and frequency control. To re-run the script within 4 hours, remove
         the chubby file manually.

Based on the following document:
http://www.corp.google.com/~bhmarks/redStone.html'
"""

__author__ = 'wanli@google.com (Wanli Yang)'

import sys
import commands
import time
import os
import string
import re
import traceback
import tempfile

from google3.enterprise.core import gfs_main_healthcheck
from google3.enterprise.core import core_utils
from google3.enterprise.core import gfs_utils
from google3.enterprise.legacy.util import E
from google3.pyglib import logging
from google3.enterprise.core import gfs_superblock_pb

ALLOWED_FATAL_LOGS = 5
GFS_SuperBlock = gfs_superblock_pb.GFS_SuperBlock

def CheckFatalLogs(ver):
  """ check if more than 5 fatal logs within last 60 minutes
    have the following error messages:
      "Acquired main lock but can not control logs. \
      Failed to become primary.  Committing suicide"

  Arguments:
    ver: '4.6.5'
  Returns:
    1 - found enough FATAL logs with that error. 0 - otherwise.
  """

  symptom_string = 'Acquired main lock but can not control logs'
  matched_logs =  gfs_main_healthcheck.SearchStringInLogs(ver,
                    'FATAL', symptom_string, 60)
  return matched_logs > ALLOWED_FATAL_LOGS

def FindCanonical(ver, testver=0, proto_dir=None, superblock_dir=None):
  """ find out a node to be the canonical
  First by reading superblock of GFS. If it does not work, return this node

  Arguments:
    ver: '4.6.5'
    testver: 1 if the version is in test mode. 0 otherwise.
    proto_dir: for unittest only. dir of the gfs_superblock.proto file.
    superblock_dir: for unittest only. dir of the main-superblock dir.
  Returns:
    GFS Replica which is upto date.
  """

  if not superblock_dir:
    superblock_dir = '/ls/%s/gfs/ent' % (
      core_utils.GetGFSChubbyCellName(ver))

  superblock_filename = '%s/main-superblock' % superblock_dir

  temp_file = tempfile.mktemp()

  if superblock_filename.startswith('/ls'):
    base_cmd = core_utils.GetLSClientCmd(ver, testver)
  else:
    base_cmd = ''

  copy_command = '%s cp %s %s' % (base_cmd,
                  superblock_filename, temp_file)

  core_utils.ExecCmd(copy_command)

  f = open(temp_file, 'r')
  data = f.read()

  gfs_superblock = GFS_SuperBlock()
  gfs_superblock.ParseFromString(data)

  os.remove(temp_file)

  num_replicas = gfs_superblock.replicas_size()
  logging.info('Num Replicas: %s' % str(num_replicas))

  cellname = gfs_superblock.cellname()
  logging.info('Cell Name: %s' % cellname)

  last_main = gfs_superblock.last_main()
  if last_main.startswith('ent'):
    last_main = last_main.split(':')[0]
  logging.info('Last Main: %s' % last_main)

  replica_info = {}

  for replica in gfs_superblock.replicas_list():
    logging.info('Rep Info: %s %s' % (
          replica.machine_name(), replica.up_to_date()))
    replica_info[replica.machine_name()] = replica.up_to_date()

  if last_main.startswith('ent') and replica_info[last_main]:
    return last_main

  for machine_name in replica_info:
    if replica_info[machine_name]:
      return machine_name

  # just this node in all other cases
  return core_utils.GetNode()

def SyncLogsWithCanonical(ver, canonical):
  """ sync logs with the canonical

  Arguments:
    ver: '4.6.5'
    canonical: 'ent1'
  """

  gfs_main_nodes, _ = core_utils.GFSMainNodes()
  gfs_main_nodes.remove(canonical)
  gfs_main_dir = '/export/hda3/%s/data/gfs_main' % ver
  log_dir = '%s/ent.gfsmain' % gfs_main_dir
  backup_log_dir = '%s.backup.%d' % (log_dir, int(time.time()))
  vars = {'gfs_main_dir':     gfs_main_dir,
          'log_dir':            log_dir,
          'backup_log_dir':     backup_log_dir,
          'canonical':          canonical
         }
  cmd = ('rm -rf %(log_dir)s.backup*; '
         'mv %(log_dir)s %(backup_log_dir)s; '
         'mkdir -p %(log_dir)s; chown nobody:nobody %(log_dir)s; '
         'rsync -c -e ssh -aHpogt %(canonical)s:%(log_dir)s %(gfs_main_dir)s'
         % vars
        )
  out = []
  enthome = '/export/hda3/%s' % ver
  E.execute(gfs_main_nodes, cmd, out, 1200, 1, 0, enthome)

def SetSyncTime(ver, testver):
  """ record the gfs logs sync time in chubby

  Arguments:
    ver: '4.6.5'
    testver: 1 - this version in test mode. 0 - otherwise.
  """

  lockserv_cmd_prefix = core_utils.GetLSClientCmd(ver, testver)
  chubby_file = '/ls/%s/GFS_LOGS_SYNC_TIME' % core_utils.GetCellName(ver)
  lockserv_cmd = '%s setcontents %s %s' % (lockserv_cmd_prefix, chubby_file,
                                           int(time.time()))
  os.system(lockserv_cmd)

def GetSyncTime(ver, testver):
  """ read the gfs logs sync time from chubby

  Arguments:
    ver: '4.6.5'
    testver: 1 - this version in test mode. 0 - otherwise.
  Returns:
    0: if no gfs logs sync has been done before. Otherwise, it is the
    time of the last sync.


  """

  lockserv_cmd_prefix = core_utils.GetLSClientCmd(ver, testver)
  chubby_file = '/ls/%s/GFS_LOGS_SYNC_TIME' % core_utils.GetCellName(ver)
  lockserv_cmd = '%s cat %s' % (lockserv_cmd_prefix, chubby_file)
  status, out = commands.getstatusoutput(lockserv_cmd)
  if status == 0:
    return int(out)
  else:
    return 0

def main(argv):

  if len(argv) < 2:
    sys.exit(__doc__)

  ver = argv[0]

  #TODO(con): get python2.4 working and remove this
  if argv[1] == "True":
    is_testver = 1
  elif argv[1] == "False":
    is_testver = 0
  else:
    try:
      is_testver = int(argv[1])
    except ValueError:
      logging.error("testver is not an int or a bool!")
      sys.exit(__doc__)

  if len(argv) >=3 and argv[2] == 'force_sync':
    canonical = FindCanonical(ver, testver)
    SyncLogsWithCanonical(ver, canonical)
    return

  # sync at most once every 4 hours
  if time.time() - GetSyncTime(ver, testver) < 3600 * 4:
    return

  if CheckFatalLogs(ver):
    try:
      try:
        gfs_utils.StopGFS(ver)
        if gfs_utils.IsGFSRunning(ver, testver) == 0:
          canonical = FindCanonical(ver, testver)
          SetSyncTime(ver, testver)
          SyncLogsWithCanonical(ver, canonical)
      except Exception, e:
        (t, v, tb) = sys.exc_info()
        exc_msg = string.join(traceback.format_exception(t, v, tb))
        logging.error(exc_msg)
    finally:
      gfs_utils.StartGFS(ver)

if __name__ == '__main__':
  main(sys.argv[1:])

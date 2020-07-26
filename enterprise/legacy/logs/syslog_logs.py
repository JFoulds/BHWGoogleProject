#!/usr/bin/python2.4
#
# Copyright 2002-2006 Google Inc.
# Author: David Watson
# Author: Phuong Nguyen (pn@google.com)
#
# This script sends apache log records to a syslog server.
#
###############################################################################
"""
Usage:
    syslog_logs.py <enthome>
"""
###############################################################################

import sys
import string
import time
import os

from google3.base import pywrapbase
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.logs import liblog
from google3.enterprise.legacy.logs import syslog_client
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import find_main
from google3.enterprise.legacy.util import port_talker
from google3.pyglib import gfile
from google3.pyglib import logging

MAX_COUNT_BETWEEN_CHECKPOINT = 1000

###############################################################################


def isMain(config):
  """Return true if is running on main node."""
  if len(config.var('MACHINES')) == 1:
    return 1
  (status, response) = port_talker.Talk(E.getCrtHostName(),
                                        core_utils.GSA_MASTER_PORT,
                                        'v is_main', 5)
  return status and response[0] == '1'

def checkpointAndCheckStatus(checkpoint_file, apache_logs, config):
  """Checkpoint apache_logs into file and return true if still is a main."""
  if not liblog.makeValid(checkpoint_file, apache_logs):
    logging.error('Error writing checkpoint %s' % checkpoint_file)
    return 0
  if not isMain(config):
    logging.error('I am not a main. Terminating')
    return 0
  return 1

def SyslogLogs(apache_logs, apache_dir, checkpoint_file, logger, config):
  """This method read apache log messages produced by collect_logs cron
  job and send to syslog server."""

  facility = config.var('ENT_SYSLOG_GWS_FAC')
  checkpoints = liblog.readValidFile(checkpoint_file)

  for apache_log in apache_logs:
    if checkpoints != None and checkpoints.has_key(apache_log.file):
      start_pos = checkpoints[apache_log.file]
    else:
      start_pos = 0

    end_pos = apache_log.size

    to_read = end_pos-start_pos
    num_read = 0
    if to_read > 0:
      # open file and seek to start_pos
      f = open('%s/%s' % (apache_dir, apache_log.file), 'r')
      f.seek(start_pos)

      leftover = ""
      count = 0
      while num_read < to_read:
        # read a chunk, up to 1M
        buffer = f.read(min(1024*1024, to_read-num_read))
        # if we get EOF, we're done
        if len(buffer) == 0:
          break
        # if the chunk doesn't contain an EOL, we can't process it
        last_eol = string.rfind(buffer, '\n')
        if last_eol == -1:
          break
        # process everything except for the last incomplete line, which we
        # save for the next time around.
        keep = leftover + buffer[:last_eol+1]
        leftover = buffer[last_eol+1:]

        # convert each line to apache log format
        for apache_line in string.split(keep[:-1], '\n'):
          logger.syslog(facility, 'INFO', time.time(), 'usage', apache_line)
          count += 1
          if count % MAX_COUNT_BETWEEN_CHECKPOINT == 0:
            apache_log.size = num_read + start_pos
            if not checkpointAndCheckStatus(checkpoint_file, apache_logs, config):
              return 0
        num_read = num_read + len(keep)
      f.close()

      # fix up the size of this log so that the checkpoint file will not
      # include the incomplete lines we didn't read.
      apache_log.size = num_read + start_pos
      logging.info('%s: read %d/%d from position %d' % \
                   (apache_log.file, num_read, to_read, start_pos))

      if (count % MAX_COUNT_BETWEEN_CHECKPOINT) and \
             not checkpointAndCheckStatus(checkpoint_file, apache_logs, config):
        return 0

  return 1

def main(argv):
  if len(argv) != 1:
    sys.exit(__doc__)

  config = entconfig.EntConfig(argv[0])
  if not config.Load():  sys.exit(__doc__)

  # Collect syslogs only if active or serve
  state = install_utilities.install_state(config.var('VERSION'))
  if not state in [ 'ACTIVE', 'SERVE' ]:
    sys.exit(0)

  # Collect syslogs only from main node.
  if not isMain(config):
    logging.fatal('Not a oneway or cluster main node. Return!')

  pywrapbase.InitGoogleScript('', ['foo',
          '--gfs_aliases=%s' % config.var("GFS_ALIASES"),
          '--bnsresolver_use_svelte=false',
          '--logtostderr'], 0)
  gfile.Init()

  first_date, last_date, printable_date, file_date = \
              liblog.ParseDateRange('all',[])

  apache_main_dir =  liblog.get_apache_dir(config)
  checkpoint_dir = liblog.get_syslog_checkpoint_dir(config)
  liblog.MakeGoogleDir(config, checkpoint_dir)

  if ( config.var('SYSLOG_SERVER') == None or
       config.var('ENT_SYSLOG_GWS_FAC') == None ):
    logging.fatal('SYSLOG logging is disabled')

  lockfile = '%s/syslog_lock' % config.var('LOGDIR')
  lock = E.acquire_lock(lockfile, 1, breakLockAfterGracePeriod = 0)
  if not lock:
    return

  try:
    logger = syslog_client.SyslogClient(config.var('SYSLOG_SERVER'),
                                        config.var('EXTERNAL_WEB_IP'))
    logging.info("syslog-server = %s" % config.var('SYSLOG_SERVER'))
    for collection in os.listdir(apache_main_dir):
      apache_dir = '%s/%s' % (apache_main_dir, collection)
      checkpoint_file = "%s/%s" % (checkpoint_dir, collection)
      apache_logs = liblog.FindLogFiles(apache_dir, first_date, last_date)
      logging.info('syslog handles collection %s' % collection)
      if not SyslogLogs(apache_logs, apache_dir, checkpoint_file, logger,
                        config):
        sys.exit('Updating failed')

    logger.close()
  finally:
    lock.close()
    os.unlink(lockfile)

  sys.exit(0)

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

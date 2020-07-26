#!/usr/bin/python2.4
#
# Copyright (C) 2001 and onwards Google, Inc.
# admin_runner_utils.py
# davidw@google.com
#
# some utility functions that are useful when talking to admin runner
import string
from google3.enterprise.legacy.util import find_main
from google3.enterprise.legacy.adminrunner import adminrunner_client
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.production.babysitter import servertype
from google3.pyglib import logging
import os
from google3.pyglib import logging


def ReadSysconfigParam(param_name):
  """Read a parameter from /etc/sysconfig.

  Args:
    param_name: the parameter to read.

  Raises:
    Exception: if the sysconfig parameters could not be loaded.

  Returns:
    The value of the parameter.
  """
  # read some /etc/sysconfig  parameter
  cp = googleconfig.Config(C.ETC_SYSCONFIG)
  if not cp.Load():
    raise 'Cannot load the sysconfig parameters'
  return cp.var(param_name)

# This returns adminrunner client and global_configs in a tuple
# It will raise an exception if anything is wrong
def GetARClientAndGlobalConfig(main_machine=None):
  if main_machine == None:
    machine_list = ReadSysconfigParam('MACHINES')
    if type(machine_list) == type(""):
      machine_list = map(string.strip, string.split(machine_list, ","))
    ver = install_utilities.extract_version_from_dir(E.getEnterpriseHome())
    main_machine = find_main.FindMainUsingChubby(ver)
    if main_machine is None:
      raise "Could not find main."

  ar = adminrunner_client.AdminRunnerClient(main_machine, 2100)
  if not ar.IsAlive():
    raise "AdminRunner on machine %s:%d is not alive" % (main_machine, 2100)

  google_config = {}
  ok, response = ar.GetAllParamsIntoDict(google_config)
  if not ok:
    raise "Can not get all global params from %s:%d" % (main_machine, 2100)
  return (ar, google_config)


def SyncOneboxLog(config):
  """Syncs Local Onebox log file with GFS Onebox Log file ONLY on clusters.
  As of 4.6.4, this is called from scripts/periodic_script.py and from
  onebox_handler.py, when the user does View Log AND the machine is a cluster.
  """
  onebox_port = servertype.GetPortBase('oneboxenterprise')
  onebox_node = config.SERVERS[onebox_port]
  crt_machine = E.getCrtHostName()
  ent_config_type = config.var('ENT_CONFIG_TYPE')

  #If onebox server is not running no need to sync.
  if ent_config_type != 'CLUSTER' or crt_machine != onebox_node[0]:
    return

  tmp_dir     = config.var('TMPDIR')
  gfs_cell    = config.var('GFS_CELL')
  local_log_name = os.path.join(tmp_dir, config.var('ENTERPRISE_ONEBOX_LOG'))
  gfs_log_name   = os.path.join(os.sep, 'gfs', gfs_cell,
                                config.var('ENTERPRISE_ONEBOX_LOG'))

  equalize_command = 'equalize %s %s' % (local_log_name, gfs_log_name)

  # fileutil equalize copies only the difference of the log files.
  err, out = E.run_fileutil_command(config, equalize_command)
  if not err:
    return

  # files didn't match in the begining, possibly a new log file would have
  # created, copy the whole log file in such case.
  copy_command = 'cp -f %s %s' % (local_log_name, gfs_log_name)
  err, out = E.run_fileutil_command(config, copy_command)

  if err:
    logging.error('Error while syncing onebox logs.')

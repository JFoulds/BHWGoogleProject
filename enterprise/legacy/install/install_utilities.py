#!/usr/bin/python2.4
# Copyright (C) 2001 and onwards Google, Inc.
#
# naga sridhar kataru <naga@google.com>
#
# desc:
# this script contains utility functions that are used in version management
# activities.
#
###############################################################################

import commands
import glob
import os
import re
import string
import sys

from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import python_kill
from google3.enterprise.legacy.install import version_utilities
from google3.pyglib import logging
from google3.enterprise.core import core_utils
import time
import os
import traceback
###############################################################################

INSTALL_STATES = [ 'TEST', 'ACTIVE', 'SERVE', 'INSTALL', 'INACTIVE' ]

## TODO -- add consts for all state string and use them all around


###############################################################################

#
# Hacky functions to read default params, validators etc
#

# private helper: loads the default params (ConfigNamespace)
# it will cache these is default_params_
__default_params__ = None
def __load_default_params__():
  global __default_params__
  if __default_params__ == None:
    from google3.enterprise.legacy.adminrunner import entconfig
    # read some default parameter
    __default_params__ = entconfig.EntConfig(None)
    __default_params__.set_var('DEFAULTS', ['enterprise'])
    __default_params__.AddDefaults()
    __default_params__.update_derived_info()
  return __default_params__

def read_default_param(param_name):
  params = __load_default_params__()
  return params.var(param_name)

def get_param_validator(param_name):
  params = __load_default_params__()
  return params.get_validator(param_name)

###############################################################################

def get_top_dir(rootdir):
  return E.normpath('%s/export/hda3' % os.path.normpath(rootdir))

def extract_version_from_dir(dir):
  m = re.match('(.*/export/hd[a-z][0-9]/([0-9]+(\.[0-9]+)+.*))', dir)
  if m and os.path.isdir(m.group(1)): return m.group(2)
  else: return ''

def get_installed_versions_list(rootdir = "/"):
  """
  this function examines the directories in TOPDIR and
  returns all the versions that are currently installed on the machine.
  so the assumption is all installed versions exist under TOPDIR.
  """
  version_tags_list = []
  for entry in glob.glob(get_top_dir(rootdir) + '/*'):
    # we are interested only if it is a directory and matches our
    # directory-naming-convention and
    # there exists a state file for that version
    version = extract_version_from_dir(entry)
    if (version and os.path.isfile(entry + '/STATE')):
          # take the basename of the complete path of directory..
          version_tags_list.append(version)

  return version_tags_list

def get_latest_version(except_for=0):
  """get latest version of GSA on the machine (except for 1).

  this function returns the latest version installed on the
  local version. this assumes that all versions are dot seperated
  numbers (e.g. 2.5 or 2.6.1). please notice the interpretation
  of latest version. it is the highest version installed and may
  not always be the one that's installed latest (though usually
  it is the case and we don't see any reason why one should install
  2.5 on a machine where 2.6 already exists).

  Args:
    except_for -- e.g. if except_for=1, returns the second last version
  Returns:
    '4.4.94'
  """

  versions = get_installed_versions_list()
  # sort them in decreasing order..
  versions.sort(version_utilities.CmpVersions)
  # return the highest version..
  if len(versions) <= except_for:
    return None
  return versions[except_for]

def install_state(version_tag, machine = E.LOCALHOST, rootdir = "/"):
  """
  This function returns the state of the install of version_num
  if it exists. Otherwise, it returns null.
  """
  filename = "%s/%s/STATE" % (get_top_dir(rootdir), str(version_tag))
  output = E.cat([machine], filename)
  if output == None:
    return None
  install_state = string.strip(output)
  if install_state not in INSTALL_STATES:
    return None
  return install_state

def is_test(version_tag, machine = E.LOCALHOST, rootdir = "/"):
  """
  This function returns true if the version is a test version or
  production version.
  """
  return install_state(version_tag, machine, rootdir) in ['TEST', 'INSTALL']

def core_op_out(ver, home, op, nodes, ignore=0, testver=None, gfs=1):
  """Executes ent_core command and returns the result.

  ent_core is running at the same time on all the nodes in different threads.

  Arguments:
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    op: 'info'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.
    gfs:     1 - start gfs during activation; 0 - otherwise.

  Returns:
    error code and output from all nodes.
    (0,
     'state=RUNNING\nnodes=5\nfailures=1\nstate=RUNNING\nnodes=5\nfailures=1')
  """

  if testver == None:
    testver = is_test(ver)
  out = []
  core_base = ('/export/hda3/%s/local/google/bin/secure_script_wrapper '
               '-e /export/hda3/%s/bin/ent_core --ver=%s' % (ver, ver, ver))
  if testver:
    core_base = '%s --testver' % core_base
  if gfs == 0:
    core_base = '%s --gfs=0' % core_base
  cmd = '%s --%s'  % (core_base, op)
  ret = E.execute(nodes, cmd, out, 0, 0, 0, home, ignore=ignore)
  if ret:
    logging.error(''.join(out))
  return ret, ''.join(out)

def get_core_states(ver, home, nodes, ignore=0, testver=None):
  """ get the ENT_CORE_STATE from all nodes

  Running "ent_core --ver --info" on all the nodes sequentially

  Arguments:
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    {'ent1': 'state=RUNNING\nnodes=5\nfailures=1',
     'ent2': 'state=RUNNING\nnodes=5\nfailures=1'}

  """

  if testver == None:
    testver = is_test(ver)
  states = {}
  core_base = ('/export/hda3/%s/local/google/bin/secure_script_wrapper '
               '-e /export/hda3/%s/bin/ent_core --ver=%s' % (ver, ver, ver))
  if testver:
    core_base = '%s --testver' % core_base
  cmd = '%s --info'  % core_base
  for node in nodes:
    out = []
    ret = E.execute([node], cmd, out, 0, 0, 0, home, ignore=ignore)
    if not ret:
      states[node] = ''.join(out)
  return states

def check_core_state(state_to_match, ver, home, nodes, ignore=0, testver=None):
  """ Check if all nodes are in a particular state

  Arguments:
    'state_to_match': 'RUNNING'
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    1 - state matches on all nodes. 0 - otherwise
  """

  core_states = get_core_states(ver, home, nodes, ignore, testver)
  state_matches = 1
  string_to_match = 'state=%s' % state_to_match
  for core_state in core_states.values():
    if core_state.find(string_to_match) == -1:
      state_matches = 0
      break
  return state_matches

def reinit_core_ok(ver, home, nodes, ignore=0, testver=None):
  """ Check if it is ok to reinit core services

  if all nodes are still in 'INSTALLED' state, it is OK to reinit
  the core services.

  Arguments:
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    1 - OK to re-init core services. 0 - otherwise.
  """

  return check_core_state('INSTALLED', ver, home, nodes, ignore, testver)

def is_core_running(ver, home, nodes, ignore=0, testver=None):
  """ Check if core service is running on all nodes

  Arguments:
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    1 - core service is running on all nodes. 0 - otherwise.

  """

  return check_core_state('RUNNING', ver, home, nodes, ignore, testver)

def core_op(ver, home, op, nodes, ignore=0, testver=None):
  """Executes state operation for ent_core.
  """
  ret, out = core_op_out(ver, home, op, nodes, ignore, testver)
  return ret

def start_core(ver, home, nodes, ignore=0, testver=None, gfs=1):
  """Starts core services.

  Arguments:
    ver:     '4.6.5'
    home:    '/export/hda3/4.6.5'
    nodes:   ['ent1', 'ent2']
    ignore:  1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.
    gfs:     1 - activate gfs. 0 - otherwise.

  Returns:
    1 - successful. 0 - otherwise.

  """

  start = time.time()
  # first start chubby and chuby dns on all nodes
  if gfs:
    services = 'core services'
  else:
    services = 'all core services except GFS'
  logging.info('ACTIVATE: Starting %s.' % services)
  ret, out = core_op_out(ver, home, 'activate', nodes,
                         ignore=ignore, testver=testver, gfs=gfs)
  if ret:
    logging.error('ACTIVATE: Cannot activate %s: %s' % (services, out))
    return 0
  end = time.time()
  diff = end - start
  logging.info('ACTIVATE: STAT: Start %s took %s seconds' % (services, diff))
  return 1

def start_gfs(ver, home, nodes, ignore=0, testver=None, sync_log=1):
  """ Starts GFS.

    By default, gfs replica transaction log will be sync'ed before starting
    GFS. This operation should not take more than a few seconds. It uses rsysc
    internally.

  Arguments:
    ver:       '4.6.5'
    home:      '/export/hda3/4.6.5'
    nodes:     ['ent1', 'ent2']
    ignore:    1 - ignore errors; 0 - otherwise.
    testver:   1 - if this is a test version; 0 - otherwise.
    sync_log:  1 - sync the gfs replica transaction log with the canonical;
               0 - otherwise

  Returns:
    1 - successful. 0 - otherwise.

  """

  if sync_log:
    # make sure the transaction logs are in sync before starting gfs
    start = time.time()
    logging.info("START GFS: Sync'ing GFS replica transaction logs")
    try:
      ent_home = "/export/hda3/%s" % ver
      vm_dir = "/export/hda3/versionmanager"
      bashrc_file = "%s/local/conf/ent_bashrc" % ent_home
      entcore_dir = "%s/google3/enterprise/core" % vm_dir
      handle_gfs_no_main_cmd = (". %s && cd %s && ./handle_gfs_no_main.py "
            "%s %s %s") % (bashrc_file, entcore_dir, ver, testver, "force_sync")
      output= []
      E.execute([E.LOCALHOST], handle_gfs_no_main_cmd, output, None,
                enthome=ent_home)
    except Exception, e:
      (t, v, tb) = sys.exc_info()
      exc_msg = string.join(traceback.format_exception(t, v, tb))
      # the "sync log" operation is not a necessary step for starting
      # gfs. So ignore any error and go ahead to start gfs.
      logging.info("The following errors are ignored: [%s]" % exc_msg)
    end = time.time()
    diff = end - start
    logging.info("START GFS: STAT: Sync'ing GFS replica transaction logs"
                 " took %s seconds" % diff)
  # start gfs
  start = time.time()
  logging.info('START GFS: Staring gfs')
  # run ent_core --ver=<ver> --start_gfs through install_utilities.py
  ret, out = core_op_out(ver, home, 'start_gfs', nodes,
                         ignore=ignore, testver=testver)
  if ret:
    logging.error('START GFS: Cannot start GFS: %s' % out)
    return 0
  end = time.time()
  diff = end - start
  logging.info('START GFS: Staring gfs took %s seconds' % diff)
  return 1


def reinit_core(ver, home, nodes, ignore=1, testver=None):
  """re-init core service on all nodes.

  Sometimes, install_manager fails to start the core service after a new
  version has been installed. It is OK to re-init the core service datafiles
  as no user data has been stored in chubby or GFS yet. This function checks
  what core service component is not up and try to re-init that component.
  This function should be called after activating the core service fails.
  After this function is called, the caller should inactivate the core service
  and retry activating the core service.

  Since it can take a long time for GFS to start up, 'test_gfs' operation
  is no longer part of the activating core services process. For the same
  reason, there is no need to test if gfs is up here.

  Arguments:
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    1 - successful. 0 - otherwise.

  """
  start = time.time()
  logging.info('REINITCORE: Reinitializing core services.')
  # first check if chubby is up
  if do_core_op('testls', ver, home, nodes, ignore, testver):
    # chubby is OK
    if not do_core_op('test', ver, home, nodes, ignore, testver):
      # chubby dns is not OK
      # clean dns
      ret = do_core_op('clear_dns', ver, home, nodes, ignore, testver)
      if ret:
        logging.error('Cannot clean chubbydns')
  else:
    # reinit chubby
    do_core_op('stop', ver, home, nodes, ignore, testver)
    # ignore the error of stopping chubby
    ret = do_core_op('clean', ver, home, nodes, ignore, testver)
    if ret:
      logging.error('Cannot clean chubby')
  end = time.time()
  diff = end - start
  logging.info('REINITCORE: STAT: Reinitialize core services took %s seconds'
               % diff)
  return 1

def do_core_op(op_name, ver, home, nodes, ignore=0, testver=None):
  """ Execute an ent_core operation on all nodes concurrently

  Arguments:
    op_name: 'clear_gfs'
    ver: '4.6.5'
    home: '/export/hda3/4.6.5'
    nodes: ['ent1', 'ent2']
    ignore: 1 - ignore errors; 0 - otherwise.
    testver: 1 - if this is a test version; 0 - otherwise.

  Returns:
    1 - successful. 0 - otherwise.
  """

  start = time.time()
  logging.info('Do core operation: %s' % op_name)
  ret, out = core_op_out(ver, home, op_name, nodes, ignore=ignore, testver=testver)
  logging.info('Out:\n%s' % out)
  if ret:
    logging.error('core operation %s failed' % op_name)
    return 0
  end = time.time()
  diff = end - start
  logging.info('core operation %s took %s seconds' % (op_name, diff))
  return 1

def stop_core(ver, home, nodes, testver=None):
  """Stops core services.
  """
  logging.info('INACTIVATE: Stopping core services.')
  ret = core_op(ver, home, 'inactivate', nodes, testver=testver)
  if ret:
    logging.error('INACTIVATE: Cannot stop core services')
    return 0
  return 1

def get_active_versions():
  """
  This function returns the currently active version number
  by examining the state of the current installed versions.
  it returns None if more than one active version exists.
  """
  active = filter(lambda v: install_state(v) in ["ACTIVE", "TEST", "INSTALL"],
                  get_installed_versions_list())
  return active


def set_install_state(machine, enterprise_home, to_status):
  """
  This function sets the status of the installed version
  to to_status
  """
  state_file_name = enterprise_home + "/STATE"
  cmd = "echo %(state)s > %(file)s && chmod 755 %(file)s && "\
  "chown nobody.nobody %(file)s" % {'state':to_status,
                                    'file':state_file_name}
  return E.ERR_OK == E.execute([machine], cmd, None, E.true)

###############################################################################

#
# Safe pairing:
#
#    A N T I S
#  A 0 1 0 0 0
#  N 1 1 1 1 1
#  T 0 1 0 0 1
#  I 0 1 0 0 1
#  S 0 1 1 1 0
#
# Legend:
#    A - active / N - inactive / T - test / I - install / S - serve
#    1 - safe / 0 - unsafe

SAFE_STATES = [ # beside the situation in which one is inactive
  ("SERVE", "TEST"),
  ("TEST", "SERVE"),
  ("INSTALL", "SERVE"),
  ("SERVE", "INSTALL"),
  ]

def safe_transition(version, target_state):
  """
  checks if it is safe to transition version's state to target_state
  """
  if target_state not in INSTALL_STATES:
    return 0

  # Get the install states of all versions beside this one
  other_states = map(install_state, filter(lambda v, crt = version: v != crt,
                                           get_installed_versions_list()))
  # Check if the pairings between the target state and all current states
  # are safe
  for s in other_states:
    if ( s != "INACTIVE" and target_state != "INACTIVE"
         and (s, target_state) not in SAFE_STATES ):
      return 0
  return 1

###############################################################################
# good start order is: ('crawl', 'web', 'logcontrol', 'serve')

SERVICES_TO_START_ONEWAY = {
  "ACTIVE" : ('crawl', 'web', 'logcontrol', 'serve'),
  "TEST"   : ('crawl', 'web', 'logcontrol', 'serve'),
  "INSTALL": ('crawl', ),
  "SERVE"  : ('logcontrol', 'serve'),
  }

SERVICES_TO_START_CLUSTER = {
  "ACTIVE" : ('crawl', 'web', 'logcontrol', 'serve'),
  "TEST"   : ('crawl', 'web', 'logcontrol', 'serve'),
  "INSTALL": ('crawl', ),
  "SERVE"  : ('logcontrol', 'serve'),
  }

# Stopping crawl stops the adminrunner and web needs a live adminrunner to stop
# so crawl must come after web.

# good stop order is : ('logcontrol', 'serve', 'crawl', 'web')
SERVICES_TO_STOP_ONEWAY = {
  "ACTIVE" : ('logcontrol', 'serve', 'web', 'crawl'),
  "TEST"   : ('logcontrol', 'serve', 'web', 'crawl', ),
  "INSTALL": ('crawl', ),
  "SERVE"  : ('logcontrol', 'serve', ),
  }

SERVICES_TO_STOP_CLUSTER = {
  "ACTIVE" : ('logcontrol', 'serve', 'web', 'crawl'),
  "TEST"   : ('logcontrol', 'serve', 'web', 'crawl'),
  "INSTALL": ('crawl', ),
  "SERVE"  : ('logcontrol', 'serve', ),
  }

def state_services_to_start(state, machines):
  """
  Given a state it returns a list of services to start in the order they
  should be startes
  """
  if len(machines) == 1:
    return SERVICES_TO_START_ONEWAY.get(state, ())
  else:
    return SERVICES_TO_START_CLUSTER.get(state, ())

def state_services_to_stop(state, machines):
  """
  Given a state it returns a list of services to stop in the order they
  should be stoped
  """
  if len(machines) == 1:
    return SERVICES_TO_STOP_ONEWAY.get(state, ())
  else:
    return SERVICES_TO_STOP_CLUSTER.get(state, ())

###############################################################################

def GetInitState(entcfg):
  """Returns System's initialization state. For oneway, it is the value of
  C.ENT_SYSTEM_INIT_STATE and for clusters, it is the value stored in chubby
  file /ls/ent<version>/ENT_SYTEM_INIT_STATE.

  If chubby file is non existent, it returns state C.FRESH.

  @param entcfg - of type googleconfig.
  @return - state
  """
  # oneway?
  if 1 == len(core_utils.GetNodes()):
    return entcfg.var(C.ENT_SYSTEM_INIT_STATE)

  # For cluster, get the state from chubby.
  version = entcfg.var('VERSION')
  lockserv_cmd_prefix = core_utils.GetLSClientCmd(version, is_test(version))
  chubby_root_dir = '/ls/%s' % core_utils.GetCellName(version)

  # Verify that chubby is functional. We do not want to accidentally return
  # FRESH state that can result in total wipe out of data.
  ls_cmd = '%s ls %s' % (lockserv_cmd_prefix, chubby_root_dir)
  (status, output) = E.getstatusoutput(ls_cmd)
  if E.ERR_OK != status:
    logging.fatal('GetInitState: Could not talk to chubby.')
    return None

  cat_cmd = '%s cat %s/%s' % (lockserv_cmd_prefix, chubby_root_dir,
                              'ENT_SYSTEM_INIT_STATE')
  (status, state) = E.getstatusoutput(cat_cmd)
  if E.ERR_OK != status:
    # For fresh install, file init_state won't exist in chubby yet.
    # Hence, consider this as a FRESH state.
    state = C.FRESH
  logging.info('current system init state: %s', state)
  return state

def SetInitState(cfg, state):
  """Sets system's initialization state. For oneway, it stores it in
  C.ENT_SYSTEM_INIT_STATE. For Clusters, it stores it in chubby file
  /ls/ent<version>/ENT_SYSTEM_INIT_STATE.

  @param cfg - of type configurator.
  @param state - string
  """
  # oneway?
  if 1 == len(core_utils.GetNodes()):
    cfg.setGlobalParam(C.ENT_SYSTEM_INIT_STATE, state)
    return

  tmpfile = E.mktemp('/export/hda3/tmp')
  try:
    f = open(tmpfile, 'w')
    f.write(state)
    f.close()
  except IOError:
    logging.fatal('Cannot write to temp file %s' % tmpfile)
    return
  version = cfg.getGlobalParam('VERSION')
  lockserv_cmd_prefix = core_utils.GetLSClientCmd(version, is_test(version))
  chubby_root_dir = '/ls/%s' % core_utils.GetCellName(version)
  write_cmd =  '%s cp %s %s/%s' % (lockserv_cmd_prefix,
      tmpfile, chubby_root_dir, 'ENT_SYSTEM_INIT_STATE')
  logging.info('setting system init state to: %s', state)
  E.exe_or_fail(write_cmd)
  E.exe('rm -rf %s' % tmpfile)

def InactivateCleanup(ver, home, active_nodes):
  """Cleanup things that inactivate may have failed to handle.

  Remove /etc/google/ent4-X-X.chubby_cell and /etc/localbabysitter.d/*.
  Kills nobody processes containing \<4.x.x\>.
  """
  cmd = ('/bin/rm -f /etc/google/%s.chubby_cell '
         '/etc/localbabysitter.d/*-%s.conf' %
         (core_utils.GetCellName(ver), ver))
  # Ignore any errors
  E.execute(active_nodes, cmd, [], 0, 0, 0, home)

  cmd = "/usr/bin/pkill -KILL -u nobody -f '/%s/'" % ver.replace('.', '\\.')
  # Kill a few times just to make sure
  for _ in range(0, 3):
    # Ignore any errors
    E.execute(active_nodes, cmd, [], 0, 0, 0, home)

################## REMOVE THE FOLLOWING CODE !!!! #############################
# Before bug 168402 is fixed, clean_machine.py will remove syslogd.conf and   #
# klogd.conf from /etc/localbabysitter.d/ directory if the version parameter  #
# is not used. As a result, many GSAs are missing the two files. The          #
# following code will re-create the two files. But this is only a temporary   #
# workaround.                                                                 #
# The real fix should come from the next enterprise-os release. The rpm could #
# save the two files in a different location. Rather then re-creating them,   #
# install_manager can just copy the files over. We should remove the code     #
# when the real fix is in.                                                    #
###############################################################################
def check_klogd_syslogd_conf(machines, enthome, unittestdir=None):
  """ babysit klogd.conf and syslogd.conf file

  Recreate klogd.conf and syslogd.conf if they are not in the dir.
  Args:
    machines: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5']
    enthome: '/export/hda3/4.6.0.G.27/'
    unittestdir: '/tmp/etc/localbabysitter.d/' -- used for unittest only
  """
  KLOGD_CONF_DATA = (
    "klogd = {\n"
    "  restart_command : '/sbin/service syslog restart',\n"
    "  timeout : 30,\n"
    "  interval : 30,\n"
    "  use_service_wrapper : 0,\n"
    "  pidfile : '/var/run/klogd.pid',\n"
    "}\n"
  )

  SYSLOGD_CONF_DATA = (
    "syslogd = {\n"
    "  restart_command : '/sbin/service syslog restart',\n"
    "  timeout : 30,\n"
    "  interval : 30,\n"
    "  use_service_wrapper : 0,\n"
    "  pidfile : '/var/run/syslogd.pid',\n"
    "}\n"
  )

  CHECK_CREATE_CMD = (
    'if [ ! -e "%(file)s" ]\n'
    'then\n'
    '  echo "%(data)s" > %(file)s\n'
    '  chmod 644 %(file)s\n'
    'fi\n'
  )

  if unittestdir is None:
    dir = '/etc/localbabysitter.d/'
  else:
    dir = unittestdir
  file_info = {'klogd.conf':KLOGD_CONF_DATA, 'syslogd.conf':SYSLOGD_CONF_DATA }
  for fname, data in file_info.items():
    file = os.path.join(dir, fname)
    cmd = CHECK_CREATE_CMD % {'data': data, 'file': file}
    if unittestdir is None:
      E.execute(machines, cmd, [], 0, 0, 0, enthome)
    else:
      os.system(cmd)

###############################################################################

def kill_service(services, machines):
  """Kill all processes associated with specified services on the specified
  machines. E.execute() sends the commands concurrently when there is more than
  one node.

  Args:
    services: list of services to kill. 'adminconsole' and 'adminrunner' are
              currently supported.
    machines: list of hostnames
  """
  # Map of services to the command that kills the service
  find_service_pid_cmd = {
      'adminconsole': ("ps -e -o pid,args --width 100 | "
                       "grep loop_AdminConsole.py | grep -v grep | "
                       "awk '{print $1}' ; "
                       "%s" % python_kill.GetServicesListeningOn(['8000'])),
      'adminrunner': ("ps -e -o pid,args --width 100 | "
                      "grep loop_AdminRunner.py | grep -v grep | "
                      "awk '{print $1}' ; "
                      "%s" % python_kill.GetServicesListeningOn(['2100'])),
  }

  for service in services:
    if service not in find_service_pid_cmd:
      logging.error('kill_service: Unrecognised service "%s"' % service)
    else:
      logging.info('kill_service: Killing service "%s" on %d nodes...' %
                   (service, len(machines)))
      kill_cmd = ('sh -c "(kill `%s`; sleep 3; kill -9 `%s`; true)" '
                  '> /dev/null 2>&1' %
                  (find_service_pid_cmd[service],
                   find_service_pid_cmd[service]))
      E.execute(machines, kill_cmd, [], alarm=1, verbose=0)
      logging.info('kill_service: Done killing service "%s"' % service)

def get_disk_usage():
  """Report current disk usage in a fractional number.

  Returns:
    A floating-point number between 0 and 1 indicating disk usage or a negative
    value to indicate error.
  """
  max_usage = 0.0
  status, output = commands.getstatusoutput('df')
  if status:
    return -1.0

  for line in output.split('\n'):
    # Use the usage of the fullest disk partition
    if line.startswith('/dev/'):
      usage = line.split()[4]
      if not usage.endswith('%'):
        return -1.0
      usage = float(usage.rstrip('%')) / 100
      if usage > max_usage:
        max_usage = usage

  return max_usage

def get_partition_disk_usage(partition_name='/export/hda3', df_output=None):
  """Report current disk usage in a fractional number.

  Returns:
    A floating-point number between 0 and 1 indicating disk usage or a negative
    value to indicate error.
  """
  max_usage = 0.0
  if df_output is None:
    status, output = commands.getstatusoutput('df')
    if status:
      return -1.0
  else:
    output = df_output

  for line in output.split('\n'):
    # Use the usage of the fullest disk partition
    if line.startswith('/dev/'):
      usage = line.split()[4]
      partition = line.split()[5]
      if not usage.endswith('%'):
        return -1.0
      if partition == partition_name:
        usage = float(usage.rstrip('%')) / 100
        return usage

  return -1.0

if __name__ == "__main__":
  import sys
  sys.exit("Import this")

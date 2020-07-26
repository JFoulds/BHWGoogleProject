#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc.
# All Rights Reserved.
# Original Author: Wanli Yang

"""Some common constants and functions to initialize core services like chubby,
chubby DNS in enterprise.
"""

__author__ = 'Wanli Yang(wanli@google.com)'

import os
import re

from google3.enterprise.core import core_utils
from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.util import borgmon_util

def GFSMainChunkserversOp(cmd, ver, testver):
  """ GFS chunkservers operations, returns the output

  Arguments:
    cmd:     '?add=ent1:3840,ent2:3840'
    ver:     '4.6.5'
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    'ent1:3840\nent2:3840\n'
  """

  gfsmainport = core_utils.GetGFSMainPort(testver)
  cmd = 'http://%s:%s/chunkservers%s' % (core_utils.MakeGFSMainPath(ver),
                                         gfsmainport, cmd)
  return core_utils.OpenURL(cmd)

def CheckLocalGFSMainHealthz(testver):
  """ Check if GFS main is healthy

  Arguments:
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    1 - GFS is healthy. 0 - otherwise.
  """

  gfsmainport = core_utils.GetGFSMainPort(testver)
  cmd = 'http://0:%s/healthz' % gfsmainport
  out = core_utils.OpenURL(cmd)
  if out and out.startswith('ok'):
    return 1
  return 0

def GetGFSChunkserversList(testver, nodes):
  """ get the list of chunkservers to add to gfs_main

  Arguments:
    testver: 1 - the version is in test mode. 0 - otherwise.
    nodes: ['ent1', 'ent2', 'ent3']
  Returns:
    'ent1:3841,ent2:3841,ent3:3841'
  """

  if testver:
    gfschunkserverport = core_utils.GFSCHUNKSERVER_TEST_PORT
  else:
    gfschunkserverport = core_utils.GFSCHUNKSERVER_BASE_PORT
  return ','.join(['%s:%s' % (x, gfschunkserverport) for x in nodes])


def CurrentChunkservers(ver, testver):
  """ get the current chunkservers

  Arguments:
    ver: '4.6.5'
    testver: 0 - not a test version. 1 - test version

  Returns:
    ['ent1:3840', 'ent2:3840']
    None if there is chunkservers in use.
  """
  cmd = ''
  out = GFSMainChunkserversOp(cmd, ver, testver)
  if out:
    chunkservers = []
    chunkserver_re = re.compile('ent(\d+):(\d+)')
    for line in out.splitlines():
      chunkserver = line.strip()
      if chunkserver_re.match(chunkserver):
        chunkservers.append(chunkserver)
    if len(chunkservers) > 0:
      return chunkservers
  return None


def AddGFSChunkservers(ver, testver, nodes):
  """ add some gfs chunkservers to the gfs_main

  Arguments:
    ver: '4.6.5'
    testver: 0 - not a test version. 1 - test version
    nodes: ['ent1', 'ent2']
  """

  chunservers_list = GetGFSChunkserversList(testver, nodes)
  cmd = '?add=%s' % chunservers_list
  GFSMainChunkserversOp(cmd, ver, testver)

def DeleteGFSChunkservers(ver, testver, nodes):
  """ delete a gfs chunkserver from the gfs_main

  Arguments:
    ver: '4.6.5'
    testver: 0
    nodes: ['ent1', 'ent2']
  """

  chunservers_list = GetGFSChunkserversList(testver, nodes)
  cmd = '?delete=%s' % chunservers_list
  GFSMainChunkserversOp(cmd, ver, testver)

def ForceGFSPrimaryMain(testver, node):
  """ force a node to become the primary gfs_main

  There is no guarantee that the node will become the primary main.
  After the first attempt, this function checks if the node has become
  the primary main. If not, it will try again.

  Arguments:
    testver: 0 - not a test version. 1 - test version.
    node: 'ent1'
  """

  gfsmainport = core_utils.GetGFSMainPort(testver)
  cmd = 'http://%s:%s/forcemain' % (node, gfsmainport)
  for i in range(2):
    out = core_utils.OpenURL(cmd)
    if out and out.startswith('This node has become the main.'):
      break

def GFSMainLockHolder(ver, testver):
  """ find the primary gfs_mater using chubby

  Arguments:
    ver:     '4.6.5'
    testver: 0 - not a test version. 1 - test version.

  Returns:
    'ent1' if ent1 is the primary gfs_main
    None if could not find out.
  """

  nodes = core_utils.GetNodes()
  if len(nodes) == 1:
    return None

  lockfile = '/ls/%s/gfs/ent/main-lock' % core_utils.GetCellName(ver)
  basecmd = core_utils.GetLSClientCmd(ver, testver)
  fi = os.popen('%s cat %s'  % (basecmd, lockfile),
                'r')
  data = fi.read()
  ret = fi.close()
  if ret:
    return None
  if data.startswith('ent'):
    return data.split(':', 2)[0]
  return None

def AvoidGFSMainOnNode(ver, testver, node):
  """ best efforts to make a node a none-primary main

  Arguments:
    ver:     '4.6.5'
    testver: 0 - not a test version. 1 - test version.
    node:    'ent4'

  Returns:
    'ent1' if ent1 is the primary gfs_main
    None if could not find out.
  """

  nodes = core_utils.GetNodes()
  if len(nodes) == 1:
    return

  (all_gfs_mains, shadow_gfs_mains) = core_utils.GFSMainNodes()
  # assuming we have at least 2 nodes running gfs main
  if all_gfs_mains[0] == node:
    desired_node = all_gfs_mains[1]
  else:
    desired_node = all_gfs_mains[0]
  if desired_node != GFSMainLockHolder(ver, testver):
    ForceGFSPrimaryMain(testver, desired_node)

def CheckNoMainBorgmonAlert(ver, testver):
  """ check if borgmon alert 'GFSMain_NoMain' is on.

  Arguments:
    ver:     '4.6.5'
    testver: 0 - not a test version. 1 - test version.

  Returns:
    1 - There is a GFSMain_NoMain alert.  0 - Otherwise.
  """
  if testver:
    borgmon_mode = borgmon_util.TEST
  else:
    borgmon_mode = borgmon_util.ACTIVE
  bu = borgmon_util.BorgmonUtil(ver, mode=borgmon_mode)
  alert_summary = bu.GetBorgmonAlertSummary()
  if alert_summary:
    return alert_summary.find('GFSMain_NoMain') != -1
  else:
    return 0

def PrimaryMainStatus(ver, testver):
  """ Return the primary gfs main's status page.

    Send the root("/") http request to gfs primary main and
    return the reply.

  Arguments:
    ver:     '4.6.5'
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    Reply from the primary gfs main.
    None if the primary main is down.
  """

  gfsmainport = core_utils.GetGFSMainPort(testver)
  cmd = 'http://%s:%s' % (core_utils.MakeGFSMainPath(ver),
                          gfsmainport)
  status =  core_utils.OpenURL(cmd)
  return status


def CheckNoMainUsingElectionStatus(ver, testver):
  """ Check GFSMain_NoMain error by looking at the primary
      main's status page directly. (workaround for
      bug 240535 and bug 240626)

  Arguments:
    ver:     '4.6.5'
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    0 - if the primary main's status is really "Primary Main"
    1 - the primary main is not up or, its status is "Skeleton Main" or
        "Recovery Main"
  """

  status = PrimaryMainStatus(ver, testver)
  if status:
    # one line is about election status
    for line in status.splitlines():
      if (line.find('Main Election Status') != -1 and
          line.find('Primary Main') != -1):
        return 0
  return 1

def EnsureGFSMainRunning(ver, testver):
  """ check borgmon alert to see if there is a primary gfs main.
  If not, try to diagnose and handle the problem following the
  instructions described in http://www.corp.google.com/~bhmarks/redStone.html

  Arguments:
    ver:     '4.6.5'
    testver: 0 - not a test version. 1 - test version.
  Returns:
    error messages - if there is an error. None - otherwise
  """

  if (CheckNoMainBorgmonAlert(ver, testver) or
      CheckNoMainUsingElectionStatus(ver, testver)):
    # find out the node that is supposed to be the primary main
    main_node = GFSMainLockHolder(ver, testver)
    handle_gfs_no_main_cmd = ("/export/hda3/%s/local/google3/enterprise/"
                                "core/handle_gfs_no_main.py %s %s" %
                                (ver, ver, testver))
    out = []
    status = E.execute([main_node], handle_gfs_no_main_cmd, out, 1200)
    if status:
      return ''.join(out)
  return None

def GetInstallManagerCoreOpCmd(ver, cmd):
  """ return the install_manager command to do core operations

  Arguments:
    ver: '4.6.5'
  Returns:
    'cd /export/hda3/4.6.5/local/google3/enterprise/legacy/install; '
    './install_manager.py --enthome=/export/hda3/4.6.5 --docoreop="info"'
  """
  return ('cd /export/hda3/%s/local/google3/enterprise/legacy/install; '
          './install_manager.py --enthome=/export/hda3/%s --docoreop="%s"' %
          (ver, ver, cmd))

def IsGFSRunning(ver, testver):
  """ if gfs_main process running on any node
  Arguments:
    ver:     '4.6.5'
    testver: 0 - not a test version. 1 - test version.
  Returns:
    1 - gfs_main processes running on some nodes. 0 - otherwise.
  """

  gfs_main_nodes, _ = core_utils.GFSMainNodes()
  list_gfs_main_cmd = "lsof -i :%s " % core_utils.GetGFSMainPort(testver)
  out = []
  enthome = '/export/hda3/%s' % ver
  status = E.execute(gfs_main_nodes, list_gfs_main_cmd, out, 300, 1, 0,
                     enthome)
  # ignore status for list
  return ''.join(out).find('LISTEN') != -1

def StopGFS(ver):
  """ stop gfs using install_manager
  Arguments:
    ver: '4.6.5'
  """

  stop_gfs_main_cmd = GetInstallManagerCoreOpCmd(ver, 'stop_gfs')
  os.system(stop_gfs_main_cmd)

def StartGFS(ver):
  """ start gfs using install_manager
  Arguments:
    ver: '4.6.5'
  """

  start_gfs_main_cmd = GetInstallManagerCoreOpCmd(ver, 'start_gfs')
  os.system(start_gfs_main_cmd)

#!/usr/bin/python2.4
#
# Copyright 2005 Google Inc.
# All Rights Reserved.
# Original Author: Zia Syed
#
# TODO(npelly): Consider moving this out of //enterprise/core

"""Some common constants and functions to initialize core services like chubby,
chubby DNS in enterprise.
"""

__author__ = 'Zia Syed(zsyed@google.com)'

import os
import commands
import re
import exceptions
import time
import signal
import urllib

from google3.pyglib import logging

# Maps total nodes => default allowed node failures
# For other configurations one failure is allowed per 5 nodes.

NODE_FAILURES      = {  1: 0,
                        5: 1,
                        8: 2,
                       12: 3,
                     }
ENT_GROUP          = 'nobody'
ENT_USER           = 'nobody'
ENT_CONFIG_FILE    = '/etc/sysconfig/enterprise_config'
GSA_MASTER_PORT       = 2102
GSA_MASTER_TEST_PORT  = 2104
GFSMASTER_BASE_PORT   = 3830
GFSMASTER_TEST_PORT   = 3831
GFSCHUNKSERVER_BASE_PORT  = 3840
GFSCHUNKSERVER_TEST_PORT  = 3841
SREMOTESERVER_BASE_PORT   = 9081
SREMOTESERVER_TEST_PORT   = 9082
LS_BASE_PORT       = 6200
LS_TEST_PORT       = 6202
LS_REP_PORT        = 6205
LS_REP_TEST_PORT   = 6207
SESSIONMANAGER_PORT = 11913
SESSIONMANAGER_TEST_PORT = 11914
CHUBBY_DNS_IP      = '127.0.0.2'
CHUBBY_DNS_TEST_IP = '127.0.0.3'
GFS_CELL           = 'ent'
LS_REP_PORT_FILE  = '/export/hda3/%s/LS_REP_PORT'
SESSIONMANAGER_PREFIX_CLUSTER = 'sessionmanager'
SESSIONMANAGER_PREFIX_ONEWAY = 'localhost'

class EntQuorumError(exceptions.Exception):
  """Indicates an error message related to required quorum in an enterprise
  cluster.
  """
  pass

class EntMainError(exceptions.Exception):
  """Indicates an error message related to main election in an enterprise
  cluster.
  """
  pass

class NodeOpError(exceptions.Exception):
  """Indicates error regarding some node operation e..g dead node addition,
  removel and checking if a node is disabled.
  """
  pass

class CommandExecError(exceptions.Exception):
  """General exception while executing commands.
  """
  pass

class GenericError(exceptions.Exception):
  """General Error.
  """
  pass

def ExecCmd(cmd, info=None, ignore_errors=0, success_msg=None,
            failure_msg=None):
  """Executes cmd.
  If command exits with code 0 then then stdout & stderr (combined) returned.

  Otherwise raise CommandExecError. Can be suppressed with ignore_errors.
  """
  if info is None:
    info = cmd
  logging.info('Executing: %s' % info)
  if failure_msg == None:
    failure_msg = 'Failure: %s' % info
  if success_msg == None:
    success_msg = 'Success: %s' % info
  out = os.popen('%s 2>&1' % cmd)
  out_text = out.read()
  ret = out.close()
  if not ret == None:
    logging.error('Error executing %s:\n%s' % (cmd, out_text))
    logging.error(failure_msg)
    if ignore_errors:
      logging.warn('Ignoring error.')
    else:
      raise CommandExecError, 'info: %s cmd: %s: return code: %d' % \
         (info, cmd, ret)
  else:
    logging.info(success_msg)
  return out_text

def GetCellName(ver):
  suffix = re.sub(r'\.', '-', ver)
  return 'ent%s' % suffix

def GetGFSChubbyCellName(ver):
  return GetCellName(ver)

def GetNodeFailures(nodes):
  """Returns node failures allowed given total nodes. If it doesn't exist in
  NODE_FAILURES map then returns 1 node failure per 5 machines.
  """
  assert(nodes > 0)
  if NODE_FAILURES.has_key(nodes):
    return NODE_FAILURES[nodes]
  else:
    return nodes / 5

def _DoSanityCheck(all_machs, active_machs):
  """This routine does sanity check on value of ENT_ALL_MACHINES and
  MACHINES and makes sure that any configuration errors are caught
  early initialization.
  Arguments:
    all_machs: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5']
    active_machs: ['ent1', 'ent2', 'ent3', 'ent4']
  """
  assert(GetNodeNumber() >= 1)
  assert(GetNodeNumber() <= len(all_machs))
  for i in range(1, len(all_machs) + 1):
    assert(('ent%d' % i) in all_machs)
  if active_machs:
    for mach in active_machs:
      assert(mach in all_machs)

def EnsureArray(val, delim=','):
  """Makes sure val is array if not it converts it using delimeter.
  """
  ret = None
  try:
    # try treating val as string
    ret = val.split(delim)
    # val is indeed a string. ret will be returned.
  except:
    ret = val
  return ret

def GetEntConfigVar(var):
  """Reads ENT_CONFIG_FILE and returns the appropriate variable.
  """
  assert(os.path.exists(ENT_CONFIG_FILE))
  vars = {}
  execfile(ENT_CONFIG_FILE, {}, vars)
  assert(vars.has_key('ENT_ALL_MACHINES'))
  vars['ENT_ALL_MACHINES'] = EnsureArray(vars['ENT_ALL_MACHINES'])
  assert(vars.has_key('MACHINES'))
  vars['MACHINES'] = EnsureArray(vars['MACHINES'])
  return vars[var]

def GetNodes(active_only=0):
  """Reads ENT_CONFIG_FILE to get machines info in the cluster.

  Arguments:
    active_only - 1 - only returns machines in 'MACHINES' variable.
                  0 - returns all machines in 'ENT_ALL_MACHINES' variable.
  Returns:
    ['ent1', 'ent2', 'ent3', 'ent4', 'ent5']
  """

  all_machines = GetEntConfigVar('ENT_ALL_MACHINES')
  active_machines = GetEntConfigVar('MACHINES')
  _DoSanityCheck(all_machines, active_machines)
  if active_only:
    return active_machines
  else:
    return all_machines

def GetTotalNodes():
  """Reads ENT_CONFIG_FILE to get total machines in the cluster.
  """
  return len(GetNodes())

def GetLSClientCmd(ver, testver):
  """Returns the base command line to execute commands for the lockserver.
  """
  cmd = '/export/hda3/%s/bin/lockserv --lockservice_port=%s' \
        % (ver, GetLSPort(testver))
  return cmd



def GetSessionManagerPrefix(is_cluster=None):
  """Returns the prefix for the Session manager server.

  On a cluster the prefix is used as an argument in the election commissar code
  to compose the main name. 
  On a oneway this value is set to be 'localhost' and the binary interprets
  that as running without any main election using chubby.
  Returns:
    sessionmanager or localhost
  """
  if not is_cluster:
    return SESSIONMANAGER_PREFIX_ONEWAY
  return SESSIONMANAGER_PREFIX_CLUSTER

def GetSessionManagerAliases(ver, testver, is_cluster=None):
  """Returns the alias for the Session manager server.

  On a cluster: this name is partly created by the Election commisar code.
    For this particular name we give the argument sessionmanager-main and
    the election commisar sufixes the rest of the string.
  On a oneway: we just use a hostname as ent1
  Args:
    ver: The GSA version e.g 5.0.3
    testver: 1 if TEST mode 0 otherwise
    is_cluster: 1 if Cluster, 0 for other platforms
  Returns:
    On cluster a full qualified hostname:port for e.g:
      sessionmanager-main.ent5-0-3.ls.google.com:port
    On oneway just 'ent1:port'
    where port is obtained through GetSessionManagerPort()
  """
  ent_dash_ver = GetCellName(ver)
  smport = GetSessionManagerPort(testver)
  if not is_cluster:
    return '%s:%s' % ('ent1', smport)
  smprefix = GetSessionManagerPrefix(is_cluster)
  return '%s-main.%s.ls.google.com:%s' % (smprefix, ent_dash_ver, smport)

def GetSessionManagerPort(testver):
  """Returns the port of SessionManager Server.

  Args:
    testver: 1 - Test mode. 0 - otherwise
  Returns:
    SESSIONMANAGER_PORT or SESSIONMANAGER_TEST_PORT
  """
  if testver:
    return SESSIONMANAGER_TEST_PORT
  else:
    return SESSIONMANAGER_PORT

def GetLSPort(testver):
  """Return the port of the Lockserver (Chubby).

  Arguments:
    testver: 1 - Test mode. 0 - otherwise
  Returns:
    6200 or 6202
  """
  if testver:
    return LS_TEST_PORT
  else:
    return LS_BASE_PORT

def GetLSRepPort(version, testver):
  """Return the replica port of the Lockserver (Chubby).

  Arguments:
    version: GSA software version
    testver: 1 - Test mode. 0 - otherwise
  Returns:
    6205 or 6207
  """
  filename = LS_REP_PORT_FILE % version
  logging.info('Replica port file is %s' % filename)
  if not os.path.exists(filename):
    logging.info('Replica port file not found %s' % filename)
    if testver:
      return LS_REP_TEST_PORT
    else:
      return LS_REP_PORT

  port = open(filename, 'r').read()
  logging.info('Replica port for version %s is %s' % (version, port))
  return port

def GetGFSMainPort(testver):
  """Returns the port of the gfs_main

  Arguments:
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    3831 or 3830
  """

  if testver:
    gfsmainport = GFSMASTER_TEST_PORT
  else:
    gfsmainport = GFSMASTER_BASE_PORT
  return gfsmainport

def GetGFSAliases(ver, testver):
  """Returns the gfs_aliases

  Arguments:
    ver: '4.6.5'
    testver: 1 - the version is in test mode. 0 - otherwise.

  Returns:
    'ent=main.ent.gfs.ent4-6-5.ls.google.com:3830'
  """

  gfsmainport = GetGFSMainPort(testver)
  return '%s=%s:%s'% (GFS_CELL, MakeGFSMainPath(ver), gfsmainport)

def GetDeadNodeDir(ver):
  """Returns the directory where dead nodes info lives.
  """
  return '/ls/%s/deadnodes' % GetCellName(ver)

def AddDeadNode(ver, testver, node):
  """Updates the info under LS that a node is marked dead.
  Returns 0 on success.
  """
  basecmd = GetLSClientCmd(ver, testver)
  dir = GetDeadNodeDir(ver)
  ret = os.system('echo Dead > /tmp/%s' % node)
  if ret == 0:
    cmd = '%s cp /tmp/%s %s/%s' % (basecmd, node, dir, node)
    ret = os.system(cmd)
  return ret

def OpenURL(url):
  """ Opens a URL with a 60 seconds timeout and returns the result.

  Arguments:
    url: 'http://0:2100/healthz'

  Returns:
    'OK\n' or None if url open times out.
  """

  out = None
  try:
    try:
      signal.alarm(60)
      out = urllib.urlopen(url).read()
    finally:
      signal.alarm(0)
  except IOError:
    pass
  return out

def CheckSVSRunning(node):
  """ check if SVS is running on a node

  Arguments:
    node: 'ent1'
  Returns:
    1 - SVS is running. 0 - otherwise.
  """
  # on the 1GB GSA-Lite, and the virtual GSAFull, there is no SVS. We
  # fool the rest of the system into believing there is.
  ent_cfg = GetEntConfigVar('ENT_CONFIG_TYPE')
  if ent_cfg == 'LITE' or ent_cfg == 'FULL':
    return 1

  cmd = 'http://%s:3999/varz' % node
  out = OpenURL(cmd)
  if out and out.find('ACKgoogle') != -1:
    return 1
  else:
    return 0

def RemDeadNode(ver, testver, node):
  """Updates the info under LS that a node is not dead any more.
  """
  basecmd = GetLSClientCmd(ver, testver)
  dir = GetDeadNodeDir(ver)
  cmd = '%s rm %s/%s' % (basecmd, dir, node)
  return os.system(cmd)

def InitDeadNodes(ver, testver, logging):
  """Reads local ENT_CONFIG_FILE and updates chubby with dead nodes.
  """
  # Empty the dead node directory
  basecmd = GetLSClientCmd(ver, testver)
  dir = GetDeadNodeDir(ver)
  ls_cmd = '%s ls %s' % (basecmd, dir)
  cmd = os.popen(ls_cmd)
  for node in cmd.readlines():
    ret = RemDeadNode(ver, testver, node.strip())
    if ret:
      logging.warn('Cleaning up deadnodes results in code:%s for %s' % (ret, node))
  ret_close = cmd.close()
  if ret_close:
    logging.info('No dead nodes found.')
  ret = 0
  activenodes = {}
  allnodes = GetNodes()
  activenodes = GetEntConfigVar('MACHINES')
  deadnodes = filter(lambda x, y=activenodes: x not in y, allnodes)
  for node in deadnodes:
    logging.info('Adding dead node %s' % node)
    ret = AddDeadNode(ver, testver, node)
    if ret:
      break
  return ret

def GetNode():
  """Returns current node's name.
  """
  return os.environ['HOSTNAME']

def GetNodeNumber():
  """Returns the node number of current machine
  """
  mo = re.compile(r'ent(\d+)').match(GetNode())
  # we assume we can always get host number from HOSTNAME env var
  assert(mo)
  mynum = int(mo.group(1))
  assert(mynum > 0)
  return mynum

def AmIDisabled(ver, testver):
  """Tells if current node is disabled.
  """
  if GetTotalNodes() == 1:
    return 0
  basecmd = GetLSClientCmd(ver, testver)
  nodefile = '%s/%s' % (GetDeadNodeDir(ver), GetNode())
  return os.system('%s cat %s > /dev/null 2>&1' % (basecmd, nodefile)) == 0

def AmIReplica(node_failures):
  """Tells if the node on which infra.py is running is configured as lockserver
  replica or not. Currently this depends only on the number of node failures
  allowed.
  """
  return GetNodeNumber() <= (2 * node_failures + 1)

def AmISessionManagerNode():
  """Tells if the node is a session manager Node.

  Nodes on the higher bucket are returned as the session manager nodes. For a
  5way they are ent2, ent3, ent4, ent5.
  12way they are ent2 through ent12. We basically want to run it on all nodes
  but are avoiding the nodes which will be loaded because of being GFS main
  at most times(i.e ent1 for both 5 and 12 ways)

  returns:
    1 if the node is a replica.
  """
  # (TODO): Check for a better way of checking if the nodes are used by session
  # manager.
  node = GetNodeNumber()

  # decide 5way/ 12way how ?
  if GetTotalNodes() == 1:
    return 1
  elif GetTotalNodes() == 5:
    return node >= 2
  elif GetTotalNodes() == 12:
    return node >= 2

  return None

def UseLockservice(total_nodes):
  """Return true if the chubby lockservice is used.
  Currently we don't use chubby on a oneway.
  """
  return total_nodes > 1

def UseChubbyDNS(total_nodes):
  """Returns if chubby DNS is to be used. Currently we won't use chubby DNS on
  oneway.
  """
  return total_nodes > 1


def UseGFS(total_nodes):
  """Returns if GFS is to be used. Currently we require at least 3 nodes.
  """
  return total_nodes >= 3

def GetGSAMain(ver, testver):
  """Returns current GSA main by looking up chubby DNS.
  """
  nodes = GetNodes()
  if len(nodes) == 1:
    return nodes[0]
  lockfile = '/ls/%s/gsa-mainlock' % GetCellName(ver)
  basecmd = GetLSClientCmd(ver, testver)
  fi = os.popen('%s cat %s'  % (basecmd, lockfile),
                'r')
  data = fi.read()
  ret = fi.close()
  if ret:
    raise EntMainError, 'Error getting GSA main from %s' % lockfile
  return data

# We take logging as argument because this module can be used by google2 and
# google3 code base where logging module is different.
def TestNode(node, logging, retry=1):
  """Currently we define success a node being sshable. We can add more stuff,
  like checking for same software and os verions etc.
  A retry mechanism is used to take care of transient errors.
  """
  max_wait =  30
  ret = 0
  while max_wait > 0:
    logging.info('Testing node %s' % node)
    cmd = 'ssh %s echo \$HOSTNAME\: I am alive.' % node
    #logging.info('Executing %s' % cmd)
    ret, _ = commands.getstatusoutput(cmd)
    if ret == 0 or not retry:
      break
    logging.warn('Node %s is down. Retrying after 5 seconds. %s seconds left.'
                  % (node, max_wait) )
    max_wait = max_wait - 5
    time.sleep(5)
  return ret

def GetLiveNodes(logging, retry=1, active_only=1):
  """Get list of machines from ENT_CONFIG_FILE and checks which machines are up.
  MACHINES paramter in google_config can be wrong as it takes a while before a
  node can be removed from the list. It is not going to be very efficient for
  very large clusters.

  Arguments:
    logging - module for logging
    retry   - 1 - retry when testing if a node is active. 0 - otherwise.
    active_only - 1. only check active machines. 0 -otherwise.
  Returns:
    ['ent1', 'ent2', 'ent3', 'ent4']
  """
  nodelist = GetNodes(active_only)
  if not active_only:
    nodecount = len(nodelist)
    failures = GetNodeFailures(nodecount)
    logging.info('Total nodes: %s' % nodecount)
    logging.info('Allowed failures: %s' % failures)
  logging.info('Checking node status.')
  deadlist = []
  alivelist = []
  for node in nodelist:
    ret = TestNode(node, logging, retry)
    if ret:
      logging.warn('Node %s is inaccessible.' % node)
      deadlist.append(node)
    else:
      logging.info('Node %s is accessible.' % node)
      alivelist.append(node)
  logging.info('Inaccessible nodes: %s' % deadlist)
  # checking svs
  nodes_without_svs = []
  for node in alivelist:
    if not CheckSVSRunning(node):
      nodes_without_svs.append(node)
  if len(nodes_without_svs) > 0:
    logging.info('SVS not running on nodes: %s' % nodes_without_svs)
  alivelist = [node for node in alivelist if node not in nodes_without_svs]
  return alivelist

def VerifyQuorum(activelist):
  """Raises exception if enough nodes are not alive.
  """
  nodecount = len(GetNodes())
  deadcount = nodecount - len(activelist)
  failures = GetNodeFailures(nodecount)
  if deadcount > failures:
    str = ('%s failures allowed and %s nodes are inaccessible' %
           (failures, deadcount))
    raise EntQuorumError, str

def GetDNSPath(ver):
  """Based on ver returns the path that is used by associated chubby DNS server.
  """
  return '%s.ls.google.com' % GetCellName(ver)

def MakeFullPath(dns_entry, ver):
  """Retunrs full path for DNS lookups of dns_entry. Also replaces variables
  like entcell in the dns_entry to the cell name.
  e.g. MakeFullPath('gfs-%(gfscell)s-main', '4.3.39') will return something
  like gfs-ent4-3-39-main.ent4-3-39.ls.google.com.
  """
  vars = { 'entcell' : GetCellName(ver),
           'gfschubbycell' : GetGFSChubbyCellName(ver),
           'gfscell' : GFS_CELL,
         }
  return '%s.%s' % (dns_entry % vars, GetDNSPath(ver))

def MakeGFSMainPath(ver):
  """Returns GFS Main Path. E.g., MakeGFSMainPath('4.4.4') will return
  main.ent.gfs.ent4-4-4.ls.google.com
  """
  return MakeFullPath('main.%(gfscell)s.gfs', ver)

def MakeGSAMainPath(ver):
  """Returns GSA main path.

  E.g., MakeGSAMainPath('4.6.4') will return
  gsa-ent4-6-4-main.ent4-6-4.ls.google.com
  """
  return MakeFullPath('gsa-%(entcell)s-main', ver)

def HasSVSErrors(node, ver, is_test_ver=0):
  """Returns true if the node has SVS errors by talking to chubby. If the svs
  file can't be found for that node then we return true. The svs file for each
  node is of the format /ls/<cell>/svs_<node_name>. This file is generated by
  gsa-main process running on each node.
  is_test_ver indicates if the version is in TEST mode with shifted ports.
  """
  basecmd = 'alarm 10 %s' % GetLSClientCmd(ver, is_test_ver)
  svs_file = '/ls/%s/svs_%s' % (GetCellName(ver), node)
  fout = os.popen('%s cat %s'  % (basecmd, svs_file), 'r')
  out = fout.read()
  ret = fout.close()
  result = 1
  if ret is None:  # no errors
    out = out.strip()
    result = (out != "")
  return result

def FindHealthyNode(logging, ver, is_test_ver=0):
  """Finds a healthy node. A healthy node is defined as a node that is part
  of the cluster, is sshable and has no svs errors reported in chubby. If we
  don't get any healthy node then we just return the current node.
  is_test_ver indicates if the version is in TEST mode with shifted ports.
  """
  active_alive_nodes = GetLiveNodes(logging, retry=0)
  # Discard active_alive_nodes which aren't currently sshable
  for node in active_alive_nodes:
    logging.info('Evaluating: %s.' % node)
    if not HasSVSErrors(node, ver, is_test_ver):
      logging.info('Found a healthy node: %s.' % node)
      return node
  logging.warn('Could not find a healthy node. Using current node.')
  return GetNode()

def CanRunGSAMain(node_name, all_nodes=None, max_node_failures=None):
  """ Can GSA main run on this node?
  In order to avoid GSA main and GFS main running on the same node,
  only the first 1+r nodes with even node number (ent2, ent4, ...) can
  run GSA Main. r is the number of node failures allowed.
  It is very important that this function returns the same result
  after a node is added/removed. Some code is based on this assumption.
  For example, periodic script skips some work on non-gsa main nodes.

  Arguments:
    node_name: 'ent1'
    all_nodes: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5'] - for unittest
    max_node_failures: 2 - for unittest

  Returns:
    1, GSA main can run on this node. 0, otherwise.
  """

  if all_nodes is None:
    all_nodes = GetEntConfigVar('ENT_ALL_MACHINES')
  if max_node_failures is None:
    max_node_failures = GetNodeFailures(len(all_nodes))
  sort_all_nodes_temp = [(int(x.replace('ent', '')), x) for x in all_nodes]
  sort_all_nodes_temp.sort()
  all_nodes = [s[1] for s in sort_all_nodes_temp]
  gsa_main_nodes = []
  non_gsa_main_nodes = []
  node_index = 1
  for node in all_nodes:
    if node_index %2 == 0:
      gsa_main_nodes.append(node)
    else:
      non_gsa_main_nodes.append(node)
    node_index += 1
    if len(gsa_main_nodes) > max_node_failures:
      break
  if len(gsa_main_nodes) <= max_node_failures:
    additional_gsa_main_nodes = max_node_failures + 1 - len(gsa_main_nodes)
    gsa_main_nodes += non_gsa_main_nodes[0:additional_gsa_main_nodes]
  if node_name in gsa_main_nodes:
    return 1
  else:
    return 0

def GFSMainNodes(all_nodes=None, active_nodes=None, max_node_failures=None):
  """ list of all GFS main nodes, list of GFS shadow main nodes

  We need r+1 primary-only gfs mains, r+1 shadow gfs mains.
  r is the number of node failures allowed.
  The primary only GFS main nodes cannot run GSA main. The shadow
  GFS main nodes can run GSA main, but try to avoid that.
  When a node is added/removed, other nodes' role should not change:

  Arguments:
    all_nodes: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5'] - for unittest
    active_nodes: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5'] - for unittest
    max_node_failures: 1 - for unitest

  Returns:
    (['ent1', 'ent3', 'ent5', 'ent4'], ['ent5', 'ent4']) for a 5-way
    (['ent1', 'ent3', 'en5', 'ent7', 'ent12', 'ent11', 'ent10', 'ent9'],
     ['ent12', 'ent11', 'ent10', 'ent9']) for a 12-way
  """

  if all_nodes is None:
    all_nodes = GetEntConfigVar('ENT_ALL_MACHINES')
  if active_nodes is None:
    active_nodes = GetEntConfigVar('MACHINES')
  if max_node_failures is None:
    max_node_failures = GetNodeFailures(len(all_nodes))
  sort_all_nodes_temp = [(int(x.replace('ent', '')), x)
                             for x in all_nodes]
  sort_all_nodes_temp.sort()
  all_nodes = [s[1] for s in sort_all_nodes_temp]
  primary_only_gfs_main_nodes = []
  other_nodes = []
  node_index = 1
  for node in all_nodes:
    if (node_index %2 != 0 and
       len(primary_only_gfs_main_nodes) <= max_node_failures):
      primary_only_gfs_main_nodes.append(node)
    else:
      other_nodes.append(node)
    node_index += 1
  if len(primary_only_gfs_main_nodes) <= max_node_failures:
    additional_primary_nodes = (max_node_failures + 1 -
                                       len(primary_only_gfs_main_nodes))
    primary_only_gfs_main_nodes += other_nodes[0:additional_primary_nodes]
    other_nodes = other_nodes[additional_primary_nodes:]
  other_nodes.reverse()
  shadow_gfs_mains = other_nodes[0:max_node_failures + 1]

  all_gfs_mains = primary_only_gfs_main_nodes + shadow_gfs_mains
  # filter inactive nodes
  return ([x for x in all_gfs_mains if x in active_nodes],
          [x for x in shadow_gfs_mains if x in active_nodes])

def DesiredMainNode(all_nodes=None, active_nodes=None,
                      max_node_failures=None):
  """ Find desired GSA main node. node with the smallest number is mostly
  desired. First find out all the nodes that can run GSA mains. Then pick
  the first one that is active.

  Arguments:
    all_nodes: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5'] - for unittest
    active_nodes: ['ent1', 'ent2', 'ent3', 'ent4', 'ent5'] - for unittest
    max_node_failures: 1 - for unittest

  Returns:
    'ent2'
    On one-way, returns None
  """

  if all_nodes is None:
    all_nodes = GetEntConfigVar('ENT_ALL_MACHINES')
  if len(all_nodes) <= 1:
    return None
  if active_nodes is None:
    active_nodes = GetEntConfigVar('MACHINES')
  if max_node_failures is None:
    max_node_failures = GetNodeFailures(len(all_nodes))
  sort_all_nodes_temp = [(int(x.replace('ent', '')), x) for x in all_nodes]
  sort_all_nodes_temp.sort()
  all_nodes = [s[1] for s in sort_all_nodes_temp]
  gsa_main_nodes = []
  non_gsa_main_nodes = []
  node_index = 1
  for node in all_nodes:
    if node_index %2 == 0:
      gsa_main_nodes.append(node)
    else:
      non_gsa_main_nodes.append(node)
    node_index += 1
    if len(gsa_main_nodes) > max_node_failures:
      break
  if len(gsa_main_nodes) <= max_node_failures:
    additional_gsa_main_nodes = max_node_failures + 1 - len(gsa_main_nodes)
    gsa_main_nodes += non_gsa_main_nodes[0:additional_gsa_main_nodes]
  for node in gsa_main_nodes:
    if node in active_nodes:
      return node
  return None

def GSAMainPort(is_testver):
  """ Return the GSA main port

  Arguments:
    is_testver: 0/1

  Returns:
    2100/2102
  """
  if is_testver:
    gsaport = GSA_MASTER_TEST_PORT
  else:
    gsaport = GSA_MASTER_PORT
  return gsaport

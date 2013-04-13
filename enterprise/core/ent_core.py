#!/usr/bin/python2.4
#
# Copyright 2004-2006 Google Inc.
# All Rights Reserved.
# Original Author: Zia Syed
#
# Design doc: //depot/eng/designdocs/enterprise/chubby-enterprise.html

"""This script initializes chubby replicas and chubby DNS on GSA clusters.
It should be executed on ALL boxes with the same command line arguments to
ensure correct operation. It returns 0 on success. This script should be
executed as root because it needs to restart named.

Usage: ent_core.py --ver= [--init [--nodes=] [--failures=]] [--start] [--wait]
                          [--test] [--stop] [--clear_dns] [--clear] [--clean]
                          [--init_dns] [--clear_gfs]
Options:
     --ver        Enterprise version
     --nodes      Total number of nodes in the cluster. If not specified, then
                  it is deduced from /etc/sysconfig/enterprise_config.
     --failures   Number of node failures allowed. If not specified, then first
                  an internal map is looked up for total number of nodes to
                  find allowed failures. If entry in map doesn't exist then 1
                  failure per 5 nodes is assumed.
Operations (only to be specified one at a time):
     --init       After installation GSA has to be initialized. Every box
                  should be initialized with same number of nodes and failures
                  argument.
     --start      Start lockserver and chubby DNS server.
     --wait       Waits till services are up.
     --stop       Stop the processes. Local babysitter conf files are
                  removed.
     --clear      Clears all files under chubby.
     --clear_dns  Clears only chubby DNS related directories.
     --init_dns   Creates all chubby DNS related directories and restarts chubby
                  DNS process.
     --clean      Takes to a state where cluster can be reinitialized.
     --test       Tests the infrastructure
     --info       Print information.
     --clear_gfs  Clear GFS data files and GFS related files in chubby
     --test_gfs   Test if GFS is operational
     --start_gfs  Start GFS(gfs_chunkserver, gfs_master, sremote_server)
     --init_gfs   Init GFS in chubby. Create gfs master and gfs chunkserver dirs
     --stop_gfs   Stop GFS(gfs_chunkserver, gfs_master, sremote_server)

Misc Operations:
     --activate   Activates the cluster and brings it to running state.
     --gfs=       Should only be used with "--activate". Default value is 1.
                  When it is set to 0, gfs will not be activated during
                  "activate" operation.
     --inactivate Inactivates the cluster and brings to stopped state.
     --kill       Kills any stale local babysitter services and brings to
                  STOPPED state. Useful for debugging where being in an invalid
                  state is painful as it is very difficult to do localbabysitter
                  cleanup.
     --activate_gfs
                  Activate GFS. Will init gfs if necessary. Then start gfs and
                  test if it is up.
     --inactivate_gfs
                  Inactivate GFS. (just stops GFS. Same as --stop_gfs)

"""

__author__ = 'Zia Syed(zsyed@google.com)'

import os
import sys
import re
import getopt
import time
import exceptions
import copy
import stat
import commands

from google3.enterprise.core import core_utils
from google3.enterprise.core import gfs_utils
from google3.enterprise.util import localbabysitter_util
from google3.pyglib import logging


## Various constants ##
# These are not moved to core_utils because they are private to ent_core.
LB_DIR             = '/etc/localbabysitter.d'
LB_PID_DIR         = '/var/run'
LS_BIN             = 'lockserver'
GSA_MASTER_BIN     = 'gsa-master'
CHUBBY_DNS_BIN     = 'chubbydnsserver'
GFS_MASTER_BIN     = 'gfs_master'
GFS_CHUNKSERVER_BIN= 'gfs_chunkserver'
SESSIONMANAGER_BIN = 'sessionmanagerserver'
SREMOTE_SERVER_BIN = 'sremote_server'
HOSTS_TEMPLATE     = '/etc/enterprise/hosts.template'

# wait time in seconds per chubby replica before chubby is active
NODE_WAIT          = 3
GFS_TESTDIR        = '/gfs/ent/testGFS'
RECONFIGURE_COMMAND = "/usr/local/sbin/reconfigure_net";


## Exceptions used ##
class GenericInfraError(exceptions.Exception):
  """To report generic errors for this module.
  """
  pass


# copied from reconfigure_net.py
# make a time stamped backup of a file
def MakeBackup(fname):
  """Makes backup of a file. Preserves ownership and permission. Doesn't
  deal with filenames with spaces.
  """
  if os.path.exists(fname):
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
    core_utils.ExecCmd('cp -p %s /tmp/%s-%s' %
                       (fname, os.path.basename(fname), timestamp),
                       'Backing up %s.' % fname)


# copied/modified from reconfigure_net.py
def AtomicSaveFileWBackup(fname, content):
  """Atomically changes the contents of a file and keeps a backup.
  Preserves file permissions and ownership.
  """
  MakeBackup(fname)
  # create a temporary file
  auxfname = fname + '.tomove'
  f = open(auxfname, 'w')
  f.write(content)
  f.flush()
  os.fdatasync(f.fileno())
  f.close()
  old_stats = os.stat(fname)
  # apply old permission bits and ownership
  os.chmod(auxfname, stat.S_IMODE(old_stats.st_mode))
  os.chown(auxfname, old_stats.st_uid, old_stats.st_gid)
  # rename temporary file to the actual file
  os.rename(auxfname, fname)


def ForceKill(binary, ver):
  """It kills all process groups belonging to a running instance of a binary
  from enterprise version ver.
  """
  logging.info('Killing all process groups to which %s belongs.' % binary)
  for pgid in localbabysitter_util.GetProcessGroupIDs(binary, ver):
    core_utils.ExecCmd('kill -9 -%s' % pgid, 'Killing process group %s' % pgid,
             ignore_errors=1)

def WaitForPIDFile(pidfile, max_wait=60):
  """Returns true if the file was created within max_wait seconds.
  Local babysitter will create pid file for the service as soon as it
  starts. We always delete the pid files before starting lock server.

  """
  logging.info('Waiting for %s to get created.' % pidfile)
  waited = 0
  while waited < max_wait:
    if os.path.exists(pidfile):
      return 1
    time.sleep(2)
    waited += 2
  return 0

def KillPortUser(ip, port, comment):
  """Kills all processes listenting to a port on an ip.
  """
  core_utils.ExecCmd('kill `lsof -t -i @%s:%s`' % (ip, port), comment,
                     ignore_errors=1)

class CoreOps:
  """Provides a mechanism to invoke version dependent configuration functions.
  Use CreateCoreOps factory method to create an object and then invoke
  appropriate function.
  """
  def __init__(self, vars):
    self.vars_ = vars
    self.lb_util_ = localbabysitter_util.LocalBabysitterUtil(vars['ver'])
    self.LS_BACKUP_DIR  = '/gfs/%(gfscell)s/chubby' % vars
    self.LS_BACKUP_CHECK_DIR  = '%(homedir)s/lockserver_check' % vars
    self.LS_DEADNODE_DIR = '/ls/%(entcell)s/deadnodes' % vars
    self.LS_CLIENT      = ('%(homedir)s/bin/lockserv '
                           '--lockservice_port=%(lsport)s ' % vars)
    self.CHUBBY_DNS_DIRS = ['/ls/%(datacenter)s/ns' % vars,
                            '/ls/%(datacenter)s/borg' % vars, #order matters
                            '/ls/%(datacenter)s/borg/ns' %vars,
                           ]
    self.CHUBBY_GFS_DIRS = ['/ls/%(datacenter)s/ns/gfs/ent' %vars,
                            '/ls/%(datacenter)s/ns/gfs' % vars,
                            '/ls/%(datacenter)s/gfs/%(gfscell)s' % vars,
                           ]
    # for testing
    self.GSA_TEST_ENTRY  = ('gsa-%(entcell)s-test.%(dnspath)s'
                             % vars)
    self.DNS_TEST_CMD    = ('%(homedir)s/bin/gendnsentry '
                            '--chubby_cell=%(entcell)s '
                            '--hostname=ent1 --address=216.239.43.1 '
                            '--entry=gsa-%(entcell)s-test '
                            '--lockservice_port=%(lsport)s ' % vars)
    self.DNS_TEST_RESULT = ('%s has address 216.239.43.1' % self.GSA_TEST_ENTRY)
    self.GSA_MASTER_LOCK = '/ls/%(entcell)s/gsa-masterlock' % vars

  def ConfigSessionManagerScript(self):
    """Configures the script used by the local babysitter for session manager.

    Should be run only on Clusters.
    """
    sm_prefix = core_utils.GetSessionManagerPrefix(is_cluster=1)
    cmdline = ('%(homedir)s/local/google/bin/sessionmanagerserver '
               '--sessionmanager_port=%(smport)s '
               '--use_commissar_failover '
               '--trusted_clients=127.0.0.0/8,216.239.43.0/24 '
               '--commissar_update_chubby_dns '
               '--bnsresolver_use_svelte=false '
               '--commissar_chubby_cell=%(entcell)s '
               '--lockservice_port=%(lsport)s '
               '--svelte_servers=localhost:6297 '
               '--svelte_retry_interval_ms=214787777 '
               '--nobinarylog '
               % self.vars_)

    logging.info('Configuring Session Manager Script on %s' %
                 self.vars_['node_name'])
    cmdline = '%s --sessionmanager_prefix=%s ' % (cmdline, sm_prefix)
    script = '#!/bin/bash\n%s' %  cmdline
    script_file = '%(homedir)s/bin/sessionmanager-%(ver)s.sh' % self.vars_
    AtomicSaveFileWBackup(script_file, script)

  def ConfigLockserverScript(self):
    """Configures the script used by the local babysitter to start lockserver.
    """
    cmdline = ('%(homedir)s/bin/lockserver '
              '--lockserver_db_dir=%(homedir)s/data/lockserver '
              '--log_dir=%(logdir)s '
              '--trusted_clients=127.0.0.0/8,216.239.43.0/24 '
              '--lockserver_registry="" '
              '--lockserver_port=%(lsport)s '
              '--lockservice_port=%(lsport)s '
              '--lockserver_rep_port=%(lsrepport)s '
              '--nolockserver_autoreplace '
              '--nolockserver_mirror_slave '
              '--lockserver_check_svs=false '
              '--lockserver_num_ports=2 '
              '--bnsresolver_use_svelte=false '
              '--svelte_servers=localhost:6297 '
              '--svelte_retry_interval_ms=214787777 '
              '--nobinarylog '
              % self.vars_)
    # turn on replication if more than one replicas
    node_failures = self.vars_['failures']
    if node_failures > 0:
      # TODO(vardhman): Bring back the backup dir option once we decide to have
      # local harddisk backups instead of GFS backups
      cmdline = '%s --lockserver_backup_check_dir=%s ' % (cmdline, self.LS_BACKUP_CHECK_DIR)
      cmdline = '%s --lockserver_backup_dir_create ' % cmdline

      # This flag disables the initial lookup for DB backup on GFS by
      # lockserver when its starting. This is a way to avoid the cyclic
      # depdency during initialization between lockserver and GFS.
      cmdline = '%s --lockserver_auto_restore=false ' % cmdline
      gfs_aliases = core_utils.GetGFSAliases(self.vars_['ver'],
                                             self.vars_['testver'])
      cmdline = '%s --gfs_aliases=%s ' % (cmdline, gfs_aliases)
      replicas = ['ent%d' % (i+1)  for i in range(2 * node_failures + 1)]
      cmdline = ('%s --nolockserver_no_replication --lockserver_peers=%s' %
                 (cmdline, ','.join(replicas)))
    script = '#!/bin/bash\n%s' %  cmdline
    script_file = '%(homedir)s/bin/lockserver-%(ver)s.sh' % self.vars_
    AtomicSaveFileWBackup(script_file, script)

  def ConfigGFSMasterScript(self):
    """ Config gfs_master script

    Configures the script used by the local babysitter to start gfs_master.
    """
    cmdline = ('%(homedir)s/local/google/bin/gfs_master '
               '--port=%(gfsmasterport)s '
               '--log_dir=/export/hda3/%(ver)s/logs '
               '--gfs_master_directory=/managedreplicated%(gfsmaster_dir)s '
               '--gfs_chunkservers_from_superblock=1 '
               '--gfs_global_reserved_GB=10 '
               '--trusted_clients='
               '127.0.0.1,216.239.43.0/24,10.0.0.0/8,172.16.0.0/12 '
               '--gfs_fileattr=%(gfsconfig_dir)s/gfs_fileattr.ent '
               '--gfs_masterlog_replica_use_sremote '
               '--sremote_server_port=%(sremoteserverport)s '
               '--gfs_masterlog_replica_machines='
               '%(gfs_master_replica_machines)s '
               '--gfs_deleted_fileversion_lifetime_secs=0 '
               '--gfs_enable_master_failover=true '
               '--gfs_log_sync_on_write=true '
               '--gfs_master_chubby_cell=%(gfschubbycell)s '
               '--localmachine_use_sremote=true '
               '--gfs_master_peers=%(gfs_master_peers)s '
               '--gfs_primary_master_affinity_secs=60 '
               '--lockservice_port=%(lsport)s '
               '--bnsresolver_use_svelte=false '
               '--svelte_servers=localhost:6297 '
               '--svelte_retry_interval_ms=214787777 '
               '--nobinarylog '
                % self.vars_)

    script = '#!/bin/bash\n%s' %  cmdline
    script_file = '%(homedir)s/bin/gfs_master-%(ver)s.sh' % self.vars_
    AtomicSaveFileWBackup(script_file, script)

  def ConfigGFSChunkserverScript(self):
    """ Config gfs_chunkserver script

    Configures the script used by the local babysitter to start gfs_chunkserver.
    """
    cmdline = ('%(homedir)s/local/google/bin/gfs_chunkserver '
               '--port=%(gfschunkserverport)s '
               '--log_dir=/export/hda3/%(ver)s/logs '
               '--gfs_chunkserver_directory=%(homedir)s/data/ent.gfsdata '
               '--gfs_cs_chubby_cell=%(gfschubbycell)s '
               '--lockservice_port=%(lsport)s '
               '--bnsresolver_use_svelte=false '
               '--svelte_servers=localhost:6297 '
               '--svelte_retry_interval_ms=214787777 '
               '--trusted_clients='
               '127.0.0.1,216.239.43.0/24,10.0.0.0/8,172.16.0.0/12 '
               '--nobinarylog '
                % self.vars_)

    script = '#!/bin/bash\n%s' %  cmdline
    script_file = '%(homedir)s/bin/gfs_chunkserver-%(ver)s.sh' % self.vars_
    AtomicSaveFileWBackup(script_file, script)

  def ConfigSremoteserverScript(self):
    """ Config sremote_server script

    Configures the script used by the local babysitter to start sremote_server
    """
    cmdline = ('%(homedir)s/local/google/bin/sremote_server '
               '--log_dir=/export/hda3/%(ver)s/logs '
               '--sremote_security_enabled=false '
               '--sremote_server_clear_port=%(sremoteserverport)s '
               '--trusted_clients='
               '127.0.0.1,216.239.43.0/24,10.0.0.0/8,172.16.0.0/12 '
               '--sremote_restrict_lock='
               '/ls/%(datacenter)s/gfs/%(gfscell)s/master-lock '
               '--lockservice_port=%(lsport)s '
               '--nobinarylog '
                % self.vars_)

    script = '#!/bin/bash\n%s' %  cmdline
    script_file = '%(homedir)s/bin/sremote_server-%(ver)s.sh' % self.vars_
    AtomicSaveFileWBackup(script_file, script)

  def ReconfChubby(self):
    """Writes a file that will be used by reconfigure_net to determine and
    configure active chubby cells.
    """
    core_utils.ExecCmd('%s CHUBBY' % (RECONFIGURE_COMMAND % self.vars_),
                       'Reconfiguring net for chubby.')

  def InitInfra(self):
    """Initializes lockserver and chubby DNS server
    """
    if not core_utils.AmIReplica(self.vars_['failures']):
      return
    # startup files are part of rpm, it is fatal not to have them
    homedir = self.vars_['homedir']
    core_utils.ExecCmd('mkdir -p %s/data/lockserver' % homedir,
                       'Ensuring lockserver dir exists', ignore_errors=1)
    core_utils.ExecCmd('chown nobody:nobody %s/data/lockserver' % homedir,
        'Ensuring lockserver dir owned by nobody', ignore_errors=1)

  def CleanLS(self):
    """Kills lockserver processes and backups/erases database
    """
    logging.info('Cleaning lockserver.')
    lsdir = '%(homedir)s/data/lockserver' % self.vars_
    olddir = '%s.bak' % lsdir
    if os.path.exists(olddir):
      core_utils.ExecCmd('rm -f %s/*' % olddir,
          'Removing lockserver backup dir %s contents.' % olddir)
    else:
      core_utils.ExecCmd('mkdir %s' % olddir,
                         'Creating lockserver backup dir %s' % olddir)
    core_utils.ExecCmd('mv -f %s/* %s/' % (lsdir, olddir),
                       'Backing up lockserver database.')
    logging.info('Cleanup successful for lockserver.')

  def CreateLSDir(self, directory, ignore_errors):
    """Creates a directory under lockserver.
    """
    ret = os.system('%s ls %s' % (self.LS_CLIENT, directory))
    # if directory doesn't exist
    if ret:
      # Note: In multiple nodes, many nodes can test and try to create same
      # directory together. Only one will succeed that is why we set
      # ignore_error to 1. Important thing is that we do testing at the end
      # to make sure this setup went fine.
      core_utils.ExecCmd('%s mkdir %s > /dev/null 2>&1' %
                         (self.LS_CLIENT, directory),
                         'Making %s under lockserver.' % directory, ignore_errors)

  def InitGFSInChubby(self):
    """ Initializes GFS state in chubby

    Check if gfs has been initialized in chubby. If not, run gfs_setup_chubby.
    chubby has to be up when this function is called.
    """
    # checking if /ls/gfschubbycell/gfs/ent/master-lock exists
    try:
      core_utils.ExecCmd('%s ls /ls/%s/gfs/%s/master-lock' % (self.LS_CLIENT,
                         self.vars_['entcell'], self.vars_['gfscell']),
                         'Checking GFS is initialized in Chubby')
    except core_utils.CommandExecError:
      gfs_setup_cmd = ('%(homedir)s/bin/gfs_setup_chubby '
                        '--gfs_cell=%(gfscell)s '
                        '--gfs_chubby_cell=%(gfschubbycell)s '
                        '--lockservice_port=%(lsport)s '
                        '--logtostderr=false '
                        '--wipe_old_data '
                        '--gfs_uptodate_master=%(gfs_master_replica_machines)s'
                        % self.vars_)
      core_utils.ExecCmd(gfs_setup_cmd, "Running gfs_setup_chubby")
    else:
      logging.info('Chubby has already been initialized for GFS')

  def CreateGFSMasterDir(self):
    """ Creates dirs for gfs_master

    If gfs master dirs have not been created:
    1. creating the following dirs for gfs_master:
          /export/hda3/<ver>/data/gfs_master/ent.gfsmaster
          /export/hda3/<ver>/data/gfs_master/ent.gfsconfig
    2. running gfs_setup_master
    3. add gfs_fileattr.ent to ent.gfsconfig dir
    """
    if self.vars_['node_name'] not in self.vars_['gfs_master_nodes']:
      logging.info('No need to create gfs master dirs on this node')
      logging.flush()
      return

    try:
      core_utils.ExecCmd('ls %(gfsconfig_dir)s/gfs_fileattr.%(gfscell)s' %
                         self.vars_,
                         'Checking GFS master dirs created on this node')
    except core_utils.CommandExecError:
      pass
    else:
      logging.info('gfs master dirs already exist')
      logging.flush()
      return

    logging.info('Creating gfs master dirs...')
    gfs_setup_master_cmd = (
      '%(homedir)s/local/google3/file/gfs/gfs_setup_master '
      '%(gfs_setup_args)s %(gfsmaster_dir)s' % self.vars_)
    core_utils.ExecCmd(gfs_setup_master_cmd, "Running gfs_setup_master")

    # Add gfs_fileattr.<cell> file to <cell>.gfsconfig directory.
    # eg: "cp /export/hda3/4.0.0/local/conf/defaults/gfs_fileattr
    #         /export/hda3/4.0.0/data/ent.gfsconfig/gfs_fileattr.ent"
    copy_gfsconfig_cmd = (
      'cp %(homedir)s/local/conf/defaults/gfs_fileattr '
      '%(gfsconfig_dir)s/gfs_fileattr.%(gfscell)s' %  self.vars_)

    core_utils.ExecCmd(copy_gfsconfig_cmd, "Copying GFS config files")

  def CreateGFSChunkServerDir(self):
    """ Set up GFS chunkserver dir

    Check if there is need to create dirs for gfs chunkservers by
    running gfs_setup_chunkserver
    """

    try:
      core_utils.ExecCmd(
          'ls %(homedir)s/data/%(gfscell)s.gfsdata/GFS_CS_DIRECTORIES' %
          self.vars_, 'Checking GFS chunkserver dirs created on this node')
    except core_utils.CommandExecError:
      pass
    else:
      logging.info('gfs chunkserver dirs already exist')
      logging.flush()
      return
    vars = {}
    execfile(self.vars_['google_config'], {}, vars)
    assert(vars.has_key('DATACHUNKDISKS'))
    datachunkdisks = vars['DATACHUNKDISKS']
    disks = map(lambda x, y=self: "%s/%s/data/%s.gfsdata" % (x,
                  y.vars_['ver'], y.vars_['gfscell']),
                datachunkdisks[self.vars_['node_name']])
    # for the new dell hardware, allow gfs_chunkserver to use hda3 as
    # that is the only disk available.
    # otherwise, use the "-l" flag to maintain the old behavior
    if len(disks) > 1:
      use_chunkserver_log_dir_flag = '-l '
    else:
      use_chunkserver_log_dir_flag = ''
    cmnd = '%s/local/google3/file/gfs/gfs_setup_chunkserver %s%s %s' % (
           self.vars_['homedir'], use_chunkserver_log_dir_flag,
           self.vars_['gfs_setup_args'], " ".join(disks))
    core_utils.ExecCmd(cmnd, "Creating gfs chunkserver dirs", ignore_errors=0)

  def InitDNS(self):
    """Creates NS directories under lockserver and create a test DNS entry if
    we are using chubby DNS.
    """
    # Lockserver should be up at this point. if wait operation was executed then
    # that should be the case.
    logging.info('Creating chubby DNS dirs.')
    for directory in self.CHUBBY_DNS_DIRS:
      self.CreateLSDir(directory, ignore_errors=1)

    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      core_utils.ExecCmd(self.DNS_TEST_CMD, 'Generating test DNS entry')
      # restart chubby DNS server so we don't have to wait 5 minutes before it
      # picks the new directories. Killing is enough as local babysitter
      # wrapper will restart it within 5 seconds.
      # All nodes needs to restart chubby DNS server
      KillPortUser(self.vars_['dnsip'], 53, 'Restarting chubby DNS')
      # sleep for 10 seconds to get chubby DNS initialized
      logging.info('Waiting 10 sec for chubby DNS initialization.')
      time.sleep(10)
      # Make sure everything is working well at this point
      self.TestInfra()

  def InitGFS(self):
    """ Init GFS """
    logging.info('Init GFS.')
    self.InitGFSInChubby()
    self.CreateGFSMasterDir()
    self.CreateGFSChunkServerDir()

  def AddGFSChunkservers(self):
    """ Add GFS chunkservers

    With --gfs_chunkservers_from_superblock=1 for gfs_master, gfs_master has to
    be informed what are the chunkservers. It is OK to add the same chunkserver
    multiple times.
    """
    sleep_time = 30
    for i in range(5):
      if gfs_utils.CheckLocalGFSMasterHealthz(self.vars_['testver']):
        logging.info("Adding the following GFS chunkservers: %s" %
                     self.vars_['gfs_chunkservers'])
        gfs_utils.AddGFSChunkservers(self.vars_['ver'], self.vars_['testver'],
                           self.vars_['gfs_chunkservers'])
        if gfs_utils.CurrentChunkservers(self.vars_['ver'],
                                         self.vars_['testver']) is not None:
          return
      # wait for GFS Master to come up, wait a little longer each time
      time.sleep(sleep_time * i)
    logging.info("Failed to add GFS chunkservers")

  def DeleteGFSChunkservers(self):
    """ Delete GFS chunkservers

    Assuming gfs_master is up.

    Note:
    With --gfs_chunkservers_from_superblock=1 for gfs_master, the set of
    chunkservers in use and their port numbers are remembered in the
    superblock. The next time gfs_master starts, it will get the info
    from the superblock. If there are changes in chunkservers or their port
    numbers, we should delete the current chunkservers before stop GFS.
    (bug 237191)
    """

    for i in range(3):
      logging.info("Deleting the following GFS chunkservers: %s" %
                   self.vars_['gfs_chunkservers'])
      gfs_utils.DeleteGFSChunkservers(self.vars_['ver'], self.vars_['testver'],
                         self.vars_['gfs_chunkservers'])
      if gfs_utils.CurrentChunkservers(self.vars_['ver'],
                                       self.vars_['testver']) is None:
        return
    logging.info("Failed to delete GFS chunkservers")

  def StartSessionManager(self):
    """Start the SessionManager service through localbabysitter.

    We do this after Chubby has started, as the master selection for session
    manager needs chubby. The function would be called as part of the activate
    step.

    """
    logging.info('Starting SessionManagerServer')
    if core_utils.AmISessionManagerNode():
      self.lb_util_.StartLBService('session manager',
                                   SESSIONMANAGER_BIN,
                                   self.vars_)
      self.lb_util_.ForceLocalBabysitterConfigReload()

  def StartGFS(self):
    """ Start GFS components through localbabysitter """
    logging.info('Start GFS')
    self.ConfigGFSChunkserverScript()
    self.lb_util_.StartLBService('gfs chunkserver',
                                 GFS_CHUNKSERVER_BIN,
                                 self.vars_)
    if self.vars_['node_name'] in self.vars_['gfs_master_nodes']:
      self.ConfigSremoteserverScript()
      self.ConfigGFSMasterScript()
      self.lb_util_.StartLBService('sremote server',
                                   SREMOTE_SERVER_BIN,
                                   self.vars_)
      self.lb_util_.StartLBService('gfs master',
                                   GFS_MASTER_BIN,
                                   self.vars_)
      # no need to have all nodes trying to add chunkservers
      self.AddGFSChunkservers()
    self.lb_util_.ForceLocalBabysitterConfigReload()

  def TestAndWaitForGFS(self):
    """ Test if GFS is up

    This function does not return anything. If GFS is still not up after
    5 retries, it will raise GenericInfraError.
    """

    logging.info('Waiting for GFS to be available')
    lswait = NODE_WAIT * ( 4 * self.vars_['failures'] + 1)
    time.sleep(lswait)
    gfs_aliases = core_utils.GetGFSAliases(self.vars_['ver'],
                                           self.vars_['testver'])
    max_tries = 5
    mkgfsdircmd = ('alarm %s %s/local/google/bin/fileutil --gfs_aliases=%s '
                   'mkdir %s' % (lswait, self.vars_['homedir'],
                                 gfs_aliases, GFS_TESTDIR))
    lsgfsdircmd = ('alarm %s %s/local/google/bin/fileutil --gfs_aliases=%s ls '
                   '/gfs/ent' % (lswait, self.vars_['homedir'], gfs_aliases))
    for i in range(max_tries):
      core_utils.ExecCmd(mkgfsdircmd, 'Creating %s' % GFS_TESTDIR,
                         ignore_errors=1)
      err, strout = commands.getstatusoutput(lsgfsdircmd)
      dirs = strout.splitlines()
      if GFS_TESTDIR in dirs:
        logging.info('GFS is available')
        return
      else:
        logging.info('Checking GFS %s:  GFS is not available' % i)
    raise GenericInfraError, 'GFS test failure'

  def StopGFS(self):
    """stop GFS

    Just stops localbabysitter from running gfs_master, gfs_chunkserver,
    and sremote_server.
    """
    # If this is in test mode, delete the chunkservers
    # it is possible we run ent_core --stop_gfs on one node. We don't
    # want to remove all the chunkservers in that case. On the other hand,
    # we cannot just remove the chunkserver on this node, as the primary
    # master may have been killed already.
    if self.vars_['testver']:
      self.DeleteGFSChunkservers()
    self.lb_util_.KillLBService('gfs chunkserver', GFS_CHUNKSERVER_BIN)
    if self.vars_['node_name'] in self.vars_['gfs_master_nodes']:
      self.lb_util_.KillLBService('sremote server', SREMOTE_SERVER_BIN)
      self.lb_util_.KillLBService('gfs master', GFS_MASTER_BIN)
    # one time config reload for the local babysitter
    self.lb_util_.ForceLocalBabysitterConfigReload()
    logging.info('stop GFS successful.')

  def ClearGFS(self):
    """ Clear GFS data

    Clear GFS data dirs and its state in chubby. GFS can be reinitialized
    after this.
    """
    logging.info('Clearing GFS')
    self.ClearGFSData()
    self.ClearGFSInChubby()

  def ClearGFSInChubby(self):
    """Cleans up GFS entries in Chubby.
    """
    if core_utils.UseGFS(self.vars_['nodes']):
      for directory in self.CHUBBY_GFS_DIRS:
        self.ClearLockserverDir(directory)

  def ClearGFSData(self):
    """ cleans up GFS on disk data.

    Since the wipe-old-data flag is used for gfs_setup_master and
    gfs_setup_chunkserver, it not really necessary to remove all the
    dirs and files. Just remove the files that CreateGFSChunkServerDir()
    and CreateGFSMasterDir() checks.
    """
    core_utils.ExecCmd(
        'rm -f %(homedir)s/data/%(gfscell)s.gfsdata/GFS_CS_DIRECTORIES' %
        self.vars_,
        'Make sure GFS chunkserver dirs will be recreated on this node')
    core_utils.ExecCmd('rm -f %(gfsconfig_dir)s/gfs_fileattr.%(gfscell)s' %
        self.vars_,
        'Make sure GFS master dirs will be recreated on this node')

  def ClearLockserverDir(self, directory, ignore_errors=1):
    """ Create a lockserver dir

    Removing a chubby dir.
    There is no standard operation to clear everything under a directory.

    Arguments:
      directory: '/ls/ent4-6-5/ns'
      ignore_errors: the default value is 1 as it is always possible that
                     some other node has removed the dir already.

    """
    logging.info('Clearing %s.' % directory)

    out_text = core_utils.ExecCmd('%s ls %s' % (self.LS_CLIENT, directory),
        ('Getting contents of lockserver directory %s'
        % directory), ignore_errors=ignore_errors)
    for file in out_text.split('\n'):
      if file and not file == 'ns':
        core_utils.ExecCmd('%s rm %s/%s' % (self.LS_CLIENT, directory, file),
                           'Removing %s/%s' % (directory, file),
                            ignore_errors=ignore_errors)

  def ClearChubbyDNS(self):
    """Clears NS directories under lockserver
    """
    self.ClearGFS()
    dirs = copy.copy(self.CHUBBY_DNS_DIRS)
    dirs.reverse()
    for directory in dirs:
      self.ClearLockserverDir(directory)

  def CleanInfra(self):
    """Undo what InitInfra has done. Essentially clean lockserver database.
    """
    if core_utils.AmIReplica(self.vars_['failures']):
      self.CleanLS()
    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      self.ClearChubbyDNS()
    logging.info('Cleanup successful.')

  def WaitForInfra(self):
    """Waits for the services under localbabysitter to come up. Helps
    in writing automated tests.
    """
    # to make pychecker happy
    if core_utils.AmIReplica(self.vars_['failures']):
      logging.info('Waiting for local babysitter to start lockserver.')
      if not WaitForPIDFile(self.lb_util_.GetMiscFiles(LS_BIN)[1]):
        raise GenericInfraError, "Lockserver didn't get started."
    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      logging.info('Waiting for local babysitter to start chubby DNS.')
      if not WaitForPIDFile(self.lb_util_.GetMiscFiles(CHUBBY_DNS_BIN)[1]):
        raise GenericInfraError, "Chubby DNS didn't get started."
    # Wait for LS to be active. Wait time is proportional to number of
    # replicas.
    lswait = NODE_WAIT * ( 2 * self.vars_['failures'] + 1)
    logging.info('Waiting for chubby to be active.')
    time.sleep(lswait)
    try:
      self.TestLS()
    except core_utils.CommandExecError, e:
      # LS can't start up.  Try repairing the database
      if self.RepairBrokenChubbyDatabase():
        # Try again
        time.sleep(lswait)
        self.TestLS()
      else:
        # Nothing to do
        raise e
    self.CreateLSDir(self.LS_DEADNODE_DIR, ignore_errors=1)
    logging.info('Activation complete. Services are up.')

  def RepairBrokenChubbyDatabase(self):
    """ Repair the database if broken.  If there is a lockserver.old directory,
    move it back to lockserver, and remove _death_count.

    This is a workaround for bug 110683.  This bug should have a real fix
    at some point.
    Returns 1 if database repair was attempted.
    """

    # Check if the database .old directory exists.
    database_dir = '%s/data/lockserver' % self.vars_['homedir']
    old_database_dir = '%s/data/lockserver.old' % self.vars_['homedir']
    if os.access(old_database_dir, os.F_OK):
      logging.error('Restoring %s' % old_database_dir)
      try:
        os.system('rm -rf %s' % database_dir)
      except OSError, e:
        logging.error('Remove %s: %s' % (database_dir, e))
      try:
        os.unlink('%s/_death_count' % old_database_dir)
      except OSError, e:
        logging.error('Remove %s/_death_count: %s' % (old_database_dir, e))
      try:
        os.rename(old_database_dir, database_dir)
        return 1
      except OSError, e:
        logging.error('Rename %s to %s: %s' % (old_database_dir, database_dir, e))
    return 0

  def StartInfra(self):
    """Starts lockserver, chubby DNS and GSA Master processes.
    """
    # generate new lockserver_cmd script if I am a replica
    core_utils.ExecCmd('echo %(dnsip)s > %(cellfile)s' % self.vars_,
                       'Adding chubby cell %(entcell)s.' % self.vars_)
    self.ReconfChubby()
    if core_utils.AmIReplica(self.vars_['failures']):
      logging.info('I am a lockserver replica.')
      self.ConfigLockserverScript()
      self.lb_util_.StartLBService('Lockserver', LS_BIN, self.vars_)
    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      self.lb_util_.StartLBService('Chubby DNS', CHUBBY_DNS_BIN, self.vars_)
    self.lb_util_.StartLBService('GSA Master', GSA_MASTER_BIN, self.vars_)
    self.lb_util_.ForceLocalBabysitterConfigReload()
    logging.info('Activation complete. It may take sometime before services'
                 ' are up.')

  def StopSessionManager(self):
    """stops sessionmanagerserver on the sessionmanager nodes"""
    self.lb_util_.KillLBService('session manager', SESSIONMANAGER_BIN)

  def StopInfra(self):
    """stops infrastructure but doesn't remove any data.
    """
    self.lb_util_.KillLBService('GSA Master', GSA_MASTER_BIN)
    self.StopGFS()
    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      self.lb_util_.KillLBService('Chubby DNS', CHUBBY_DNS_BIN)
    if core_utils.AmIReplica(self.vars_['failures']):
      self.lb_util_.KillLBService('Lockserver', LS_BIN)
    # one time config reload for the local babysitter
    self.lb_util_.ForceLocalBabysitterConfigReload()
    # remove chubby cell
    core_utils.ExecCmd('rm -f %(cellfile)s' % self.vars_,
                       'Removing chubby cell %(entcell)s.' % self.vars_)
    self.ReconfChubby()
    logging.info('Deactivation successful.')

  def TestLS(self):
    core_utils.ExecCmd('%s ls /ls/%s' % (self.LS_CLIENT, self.vars_['entcell']),
            'Testing lockserver.')

  def TestInfra(self):
    """Tests lockserver and chubby DNS server. It tests lockserver by
    just taking list of files in the root directory of the cell. For
    chubby DNS it copies a sample DNS entry to the chubby's database.
    Then it tests chubby DNS by looking up the recently added entry.
    """
    self.TestLS()
    if core_utils.UseChubbyDNS(self.vars_['nodes']):
      # do a lookup throgh local chubby DNS
      chubbyip = self.vars_['dnsip']
      actual = core_utils.ExecCmd('host %s %s' % (self.GSA_TEST_ENTRY, chubbyip),
                       'Resolving %s' % self.GSA_TEST_ENTRY)
      lastline = actual.split('\n')[-2]
      if not lastline == self.DNS_TEST_RESULT:
        logging.error("Chubby DNS test failed.\nActual='%s'\nExpected='%s'" %
                      (lastline, self.DNS_TEST_RESULT))
        raise GenericInfraError, 'Chubby DNS test failure'
      logging.info('Infrastructure test successful.')


def CreateCoreOps(ver, nodes, failures, test=0):
  """Factory method for creating CoreOps object to execute version
  and test version dependent operations.
  """
  # TODO(npelly): Move some of this logic out of ent_core.py and into
  # core_utils.py or someplace else. ent_core should only be used on clusters,
  # but much of this logic is used on oneway too.
  cell = core_utils.GetCellName(ver)
  lsport = core_utils.GetLSPort(test)
  smport = core_utils.GetSessionManagerPort(test)
  lsrepport = core_utils.GetLSRepPort(ver, test)
  gsaport = core_utils.GSA_MASTER_PORT
  chubbydnsip = core_utils.CHUBBY_DNS_IP
  gfsmasterport = core_utils.GFSMASTER_BASE_PORT
  gfschunkserverport = core_utils.GFSCHUNKSERVER_BASE_PORT
  sremoteserverport = core_utils.SREMOTESERVER_BASE_PORT
  homedir = '/export/hda3/%s' % ver
  google_config = os.path.join(homedir, 'local/conf/google_config')
  # port/ip shifting
  if test:
    gsaport = core_utils.GSA_MASTER_TEST_PORT
    chubbydnsip = core_utils.CHUBBY_DNS_TEST_IP
    gfsmasterport = core_utils.GFSMASTER_TEST_PORT
    gfschunkserverport = core_utils.GFSCHUNKSERVER_TEST_PORT
    sremoteserverport = core_utils.SREMOTESERVER_TEST_PORT
  # unique string identifying version that can be used in variable names
  unq = re.sub(r'\.', '_', ver)
  if core_utils.CanRunGSAMaster(core_utils.GetNode()):
    svsonlyflag = ''
  else:
    svsonlyflag = '--svs_monitoring_only=true'
  (all_gfs_masters, shadow_gfs_masters) = core_utils.GFSMasterNodes()
  node_name = core_utils.GetNode()
  gfscell = 'ent'
  gfsmaster_root_dir = os.path.join(homedir, 'data/gfs_master')
  gfsmaster_dir = os.path.join(gfsmaster_root_dir, '%s.gfsmaster' % gfscell)
  gfsconfig_dir = os.path.join(gfsmaster_root_dir, '%s.gfsconfig' % gfscell)
  gfs_setup_args = "-p -empty -gfsuser=nobody -gfsgroup=nobody " \
                   "-email=none -wipe-old-data"
  live_nodes = core_utils.GetLiveNodes(logging)
  gfs_chunkservers = live_nodes
  gfs_master_replica_machines = ",".join(all_gfs_masters)
  gfs_master_peers = ",".join(
    map(lambda x,y=gfsmasterport: x + ":%s" % y, all_gfs_masters))
  vars = {'ver': ver,
          'homedir':                 homedir,
          'nodes':                   nodes,
          'failures':                failures,
          # testver may get passed as a command line arg, so make sure we
          # sanitize it for python2.2/2.4 compatibility
          'testver':                 int(test),
          'entcell':                 cell,
          'gfscell':                 'ent',
          'gfschubbycell':           cell,
          'datacenter':              cell,
          'lsport':                  lsport,
          'lsrepport':               lsrepport,
          'smport':                  smport,
          'gsaport':                 gsaport,
          'gfsmasterport':           gfsmasterport,
          'gfschunkserverport':      gfschunkserverport,
          'sremoteserverport':       sremoteserverport,
          'gfsmasterpath':           core_utils.MakeGFSMasterPath(ver),
          'dnsip':                   chubbydnsip,
          'logdir':                  '%s/logs' % homedir,
          'lsdir':                   '%s/data/lockserver' % homedir,
          'tmpdir':                  '%s/tmp' % homedir,
          'cellfile':                '/etc/google/%s.chubby_cell' % cell,
          'unq':                     unq,
          'dnspath':                 core_utils.GetDNSPath(ver),
          'svsonlyflag':             svsonlyflag,
          'gfs_master_nodes':        all_gfs_masters,
          'gfsmaster_dir':           gfsmaster_dir,
          'gfsconfig_dir':           gfsconfig_dir,
          'gfs_setup_args':          gfs_setup_args,
          'gfs_chunkservers':        gfs_chunkservers,
          'gfs_master_peers':        gfs_master_peers,
          'node_name':               node_name,
          'google_config':           google_config,
          'gfs_master_replica_machines': gfs_master_replica_machines,
        }
  obj = CoreOps(vars)
  return obj


# wrapper around above functions
class EntCoreStateMach:
  """EntCoreStateMach manipulates the state of enterprise infrastructure related
  code. It is a wrapper around the actual state manipulation function to make
  sure that nothing can bring the infrastructure to an incorrect state. As long
  as all machines run same operation on this machine the cluster infrastructure
  should work fine. The state is stored on the disk. State machine
  implementation makes it easy to write, debug and maintain otherwise relatively
  complex piece of code.
  """
  class IllegalOperationError(exceptions.Exception):
    """To indicate that a particular operation is not allowed in current
    state.
    """
    pass

  # current_state => { op => next_state }
  STATE_MAP = { 'INSTALLED':  { 'init':             'STOPPED',
                                'test':             'INSTALLED',
                                'testls':           'INSTALLED',
                                'activate':         'RUNNING',
                                'kill':             'INSTALLED',
                              },
                'STOPPED':    { 'start':            'RUNNING',
                                'clean':            'INSTALLED',
                                'test':             'STOPPED',
                                'testls':           'STOPPED',
                                'activate':         'RUNNING',
                                'inactivate':       'STOPPED', # no op
                                'kill':             'STOPPED',
                              },
                'RUNNING':    { 'wait':             'RUNNING',
                                'clear_dns':        'RUNNING',
                                'init_dns':         'RUNNING',
                                'clear':            'RUNNING',
                                'test':             'RUNNING',
                                'testls':           'RUNNING',
                                'stop':             'STOPPED',
                                'activate':         'RUNNING',   # no op
                                'inactivate':       'STOPPED',
                                'kill':             'STOPPED',
                                'init_gfs':         'RUNNING',
                                'start_gfs':        'RUNNING',
                                'stop_gfs':         'RUNNING',
                                'test_gfs':         'RUNNING',
                                'clear_gfs':        'RUNNING',
                                'activate_gfs':     'RUNNING',
                                'inactivate_gfs':   'RUNNING',
                                'start_sessionmanager': 'RUNNING',
                              },
              }

  def __init__(self):
    self.state = ''
    self.nodes = -1
    self.failures = -1
    # list of attributes that need to be written to the state file
    self.__persist = [ 'state', 'nodes', 'failures', ]
    self.__changed = 0
    self.__loaded  = 0
    self.testver = 0 # indicates test version for VM
    self.gfs = 1     # indicates activating gfs for activate operation
    self.ver = ''
    self.file = ''
    self.homedir = ''

  def GetOpMap(self):
    """Returns map of allowed operations to function.
    """
    return {  'init':              self.Init,
              'start':             self.Start,
              'stop':              self.Stop,
              'kill':              self.Kill,
              'clear':             self.Clear,
              'clear_dns':         self.Clear_dns,
              'init_dns':          self.Init_dns,
              'clean':             self.Clean,
              'info':              self.Info,
              'test':              self.Test,
              'testls':            self.TestLS,
              'wait':              self.Wait,
              'activate':          self.Activate,
              'inactivate':        self.Inactivate,
              'init_gfs':          self.Init_gfs,
              'start_gfs':         self.Start_gfs,
              'stop_gfs':          self.Stop_gfs,
              'test_gfs':          self.Test_gfs,
              'clear_gfs':         self.Clear_gfs,
              'activate_gfs':      self.Activate_gfs,
              'inactivate_gfs':    self.Inactivate_gfs,
              'start_sessionmanager': self.Start_sessionmanager,
           }

  def LoadState(self, ver, testver=0, gfs=1):
    """Load state file and initialize persistent attributes.
    """
    self.testver = testver
    self.gfs = gfs
    self.ver = ver
    self.homedir = '/export/hda3/%s' % ver
    self.file = '%s/ENT_CORE_STATE' % self.homedir
    assert(os.path.exists(self.file))
    globals = { 'INSTALLED': 'INSTALLED',
                'STOPPED':   'STOPPED',
                'RUNNING':   'RUNNING',
              }
    try:
      # Load variables from self.file into this object (self.file is python)
      # This should include self.state, self.nodes and self.failures
      execfile(self.file, globals, self.__dict__)
    except Exception, e:
      raise GenericInfraError, 'Error processing file %s: %s' % (self.file, e)
    assert(self.STATE_MAP.has_key(self.state))
    self.__loaded = 1

  def ForceState(self, state):
    """For debugging and testing purposes. We may want the machine to act
    in a specific state. This function forcefully sets the current state
    to any desired state.
    """
    assert(self.STATE_MAP.has_key(state))
    self.state = state

  def __checkOpOrDie(self, op):
    """Checks if certain operation can be performed on the machine or not.
    Return a new CreateCoreOps object if the operation is ok.
    """
    assert(self.__loaded)
    if not self.STATE_MAP[self.state].has_key(op):
      raise self.IllegalOperationError, ("Illegal to '%s' while in state %s." %
                                                            (op, self.state))
    obj = CreateCoreOps(self.ver, self.nodes, self.failures, self.testver)
    return obj

  def __doOp(self, op):
    """Moves to the next state after an operation has completed.
    """
    assert(self.__loaded)
    self.__checkOpOrDie(op)
    prev_state = self.state
    self.state = self.STATE_MAP[prev_state][op]
    self.__changed = (not self.state == prev_state)

  def __doOpList(self, oplist):
    """Executes a list of operations.
    """
    changed = 0
    ops = self.GetOpMap()
    for op in oplist:
      logging.info('Executing %s' % op)
      ops[op]()
      changed = changed or self.__changed
    self.__changed = changed

  def Init(self, n=-1, f=-1):
    """Initializes the state given total number of nodes and allowable node
    failures.
    """
    if n < 0:
      n = core_utils.GetTotalNodes()
    assert(n > 0)
    if f < 0:
      f = core_utils.GetNodeFailures(n)
    assert(f >= 0)
    assert(n >= (2*f + 1))
    changed = not (n == self.nodes and f == self.failures)
    self.nodes = n
    self.failures = f
    obj = self.__checkOpOrDie('init')
    obj.InitInfra()
    self.__changed = changed
    self.__doOp('init')

  def Start(self):
    """Starts the processes.
    """
    obj = self.__checkOpOrDie('start')
    obj.StartInfra()
    if core_utils.AmISessionManagerNode():
      obj.ConfigSessionManagerScript()
    self.__doOp('start')

  def Wait(self):
    """Waits till the requested processes are up and running. Helps in
    writing automated tests.
    """
    obj = self.__checkOpOrDie('wait')
    obj.WaitForInfra()
    self.__doOp('wait')

  def Stop(self):
    """Stops running processes.
    """
    obj = self.__checkOpOrDie('stop')
    obj.StopInfra()
    if core_utils.AmISessionManagerNode():
      obj.StopSessionManager()
    self.__doOp('stop')

  def Kill(self):
    """A helpful function to bring down stale services from any state for any
    version.
    """
    obj = self.__checkOpOrDie('kill')
    obj.StopInfra()
    if core_utils.AmISessionManagerNode():
      obj.StopSessionManager()
    self.__doOp('kill')

  def Clear(self):
    """Clears all the state in chubby.
    """
    self.__checkOpOrDie('clear')
    # TODO(zsyed): Implement operation to clear all directories under chubby.
    # to fool pychecker
    if 1:
      raise self.IllegalOperationError, "Operation 'clear' not implemented yet."
    self.__doOp('clear')

  def Init_dns(self):
    """Initialize the DNS related directories under chubby.
    """
    obj = self.__checkOpOrDie('init_dns')
    obj.InitDNS()
    self.__doOp('init_dns')

  def Clear_dns(self):
    """Clears all DNS related directories under chubby.
    """
    obj = self.__checkOpOrDie('clear_dns')
    obj.ClearChubbyDNS()
    self.__doOp('clear_dns')

  def Init_gfs(self):
    """Initialize the GFS related directories and its state in chubby.
    """
    obj = self.__checkOpOrDie('init_gfs')
    obj.InitGFS()
    self.__doOp('init_gfs')

  def Start_gfs(self):
    """ Start gfs_master, gfs_chunkserver, and sremote_server
    """
    obj = self.__checkOpOrDie('start_gfs')
    obj.StartGFS()
    self.__doOp('start_gfs')

  def Start_sessionmanager(self):
    """Starts sessionmanager.
    """
    obj = self.__checkOpOrDie('start_sessionmanager')
    obj.StartSessionManager()
    self.__doOp('start_sessionmanager')

  def Test_gfs(self):
    """ Test if GFS is working
    """
    obj = self.__checkOpOrDie('test_gfs')
    obj.TestAndWaitForGFS()
    self.__doOp('test_gfs')

  def Clear_gfs(self):
    """ Clear gfs datafiles and its state in chubby.
    """
    obj = self.__checkOpOrDie('clear_gfs')
    obj.ClearGFS()
    self.__doOp('clear_gfs')

  def Stop_gfs(self):
    """ Stop GFS
    """
    obj = self.__checkOpOrDie('stop_gfs')
    obj.StopGFS()
    logging.info('Stopping GFS')
    self.__doOp('stop_gfs')

  def Clean(self):
    """Cleans all lockserver related data and brings back to INSTALLED
    state. Useful for automated testing and machine cleanup.
    """
    obj = self.__checkOpOrDie('clean')
    obj.CleanInfra()
    self.__doOp('clean')

  def Activate(self):
    """Activates the infra structure.
    """
    self.__checkOpOrDie('activate')
    # having kill firt will kill any stale services
    oplists = { 'INSTALLED' : ['init', 'kill', 'start', 'wait', 'init_dns',
                               'init_gfs', 'start_gfs', 'start_sessionmanager'],
                'STOPPED'   : ['kill', 'start', 'wait', 'init_dns',
                               'start_gfs', 'start_sessionmanager'],
                'RUNNING'   : ['stop', 'start', 'wait', 'test',
                               'start_gfs', 'start_sessionmanager'],
              }
    if self.gfs == 0:
      # don't start gfs if gfs flag is 0
      for state in oplists:
        oplists[state].remove('start_gfs')

    logging.info('Activating services.')
    self.__doOpList(oplists[self.state])

  def Activate_gfs(self):
    """Activates GFS.
    """
    self.__checkOpOrDie('activate_gfs')
    # having kill firt will kill any stale services
    oplists = { 'RUNNING'   : ['init_gfs', 'start_gfs', 'test_gfs'],
              }
    logging.info('Activating GFS')
    self.__doOpList(oplists[self.state])

  def Inactivate_gfs(self):
    """Inactivates GFS.
    """
    obj = self.__checkOpOrDie('inactivate_gfs')
    obj.StopGFS()
    logging.info('Inactivating GFS')
    self.__doOp('inactivate_gfs')

  def Inactivate(self):
    """Inactivates the infra structure.
    """
    self.__checkOpOrDie('activate')
    oplists = { 'INSTALLED' : ['kill', ],
                'STOPPED'   : ['kill', ],
                'RUNNING'   : ['stop', ] ,
              }
    logging.info('Inactivating services.')
    self.__doOpList(oplists[self.state])

  def Test(self):
    """Executes minimal tests to make sure all services are running well.
    """
    obj = self.__checkOpOrDie('test')
    obj.TestInfra()
    self.__doOp('test')

  def TestLS(self):
    """Executes minimal tests to make sure lock service is running well.
    """
    obj = self.__checkOpOrDie('testls')
    obj.TestLS()
    self.__doOp('testls')

  def Info(self):
    """Provides current state as persisted on the disk.
    """
    assert(self.__loaded)
    for var in self.__persist:
      print '%s=%s' % (var, self.__dict__[var])

  def __del__(self):
    """Writes any changes to the state file.
    """
    if self.__loaded and self.__changed:
      body = []
      for var in self.__persist:
        body.append('%s=%s' % (var, self.__dict__[var]))
      AtomicSaveFileWBackup(self.file, '\n'.join(body))


def main(argv):
  """We don't use google3.pyglib.flags as we do special handling of command
  line arguments.
  """
  op = ''
  # defaults: -1 => detect automatically
  total_nodes = -1
  node_failures = -1
  ver = ''
  assume = '' # assume this state for debugging
  sm = EntCoreStateMach()
  ops = sm.GetOpMap()
  logstdout = 0
  testver = 0
  gfs = 1
  gfs_flag_used = 0
  flags = ['nodes=', 'failures=', 'ver=', 'assume=', 'logstdout',
           'testver',  'gfs='] + ops.keys()
  try:
    opts, _ = getopt.getopt(argv, '', flags)
  except:
    sys.exit(__doc__)

  for (opt, val) in opts:
    if opt == '--nodes':
      total_nodes = int(val)
    elif opt == '--failures':
      node_failures = int(val)
    elif opt == '--ver':
      ver = val
    elif opt == '--assume':
      assume = val
    elif opt == '--logstdout':
      logstdout = 1
    elif opt == '--testver':
      testver = 1
    elif opt == '--gfs':
      gfs = int(val)
    else:
      if not ops.has_key(opt[2:]):
        sys.exit('Error: Invalid flag %s.\n%s' % (opt, __doc__))
      if op:
        sys.exit('Error: One operation at a time.\n%s' % __doc__)
      op = opt[2:]

  # now '--gfs' flag can be used only with '--activate' flag.
  if gfs != 1 and op != 'activate':
     sys.exit('Error: Invalid flag --gfs.\n%s' % __doc__)
  if not logstdout:
    logging.set_googlestyle_logfile(log_dir='/export/hda3/%s/logs' % ver)
  # deal with mandatory args
  if not ver:
    sys.exit('Error: --ver not specified.\n%s' % __doc__)
  if not op:
    sys.exit('Error: Nothing to do.\n%s' % __doc__)
  sm.LoadState(ver, testver, gfs)
  if assume:
    sm.ForceState(assume)
  start = time.time()
  if op == 'init':
    ops[op](total_nodes, node_failures)
  else:
    ops[op]()
  end = time.time()
  diff = end - start
  logging.info("STAT: '%s' took %s seconds." % (op, diff))

if __name__ == '__main__':
  main(sys.argv[1:])

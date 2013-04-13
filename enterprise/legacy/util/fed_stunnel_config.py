#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.

"""Utility classes to get stunnel configuration from federation configuration.

The file has two utility classes one that help create a stunnel.conf file for
a federation network client and another for federation network service.
"""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.util import fed_network_config

# Path to binaries
STUNNEL = '/usr/sbin/stunnel'
PPPD = '/usr/bin/pppd'
ROOT = '/'

# Configurations
STUNNEL_CONFIG = '/export/hda3/chroot/fed/stunnel.conf'
STUNNEL_CHAP_FILE = '/export/hda3/chroot/fed/etc/ppp/chap-secrets'
STUNNEL_LISTEN_PORT = 18999
STUNNEL_USER_ID = 'nobody'
STUNNEL_GROUP_ID = 'nobody'
STUNNEL_CHROOT = '/export/hda3/chroot/fed'
STUNNEL_CLIENT_CHROOT = '/export/hda3/chroot/fed_client'
STUNNEL_PID = '/export/hda3/chroot/fed/stunnel_federation.pid'
STUNNEL_SERVER_CERT = '/local/conf/certs/server.crt'
STUNNEL_SERVER_KEY = '/local/conf/certs/server.key'
STUNNEL_LOGS = '/stunnel.log.'
STUNNEL_CLIENT = 'client=yes'
STUNNEL_SERVER = 'client=no'
STUNNEL_FOREGROUND = 'yes'
STUNNEL_DEBUG_LEVEL = '7'
STUNNEL_PPPD_EXEC = '/usr/sbin/pppd'
STUNNEL_PPPD_EXEC_ARGS = ('/usr/sbin/pppd local kdebug 2 '
                          'logfile pppd.log logfd 2 debug dump require-chap '
                          'auth noccp novj novjccomp nopcomp noaccomp name ')
STUNNEL_PTY = 'yes'
STUNNEL_CONNECT = 'connect'
PPPD_CLIENT_COMMAND = ('chroot %(CHROOT)s '
                       '/usr/sbin/pppd auth require-chap debug dump logfd 2 '
                       'passive name %(NAME)s remotename %(REMOTE)s '
                       'noccp novj novjccomp nopcomp noaccomp noproxyarp '
                       'linkname %(LINK_NAME)s pty \"%(STUNNEL_CMD)s '
                       '%(STUNNEL_CONF)s\" %(LOCAL_PPP_IP)s:')


def GetEnterpriseConfiguration():
  """Get the enterprise configuration object."""
  export_hda = '/export/hda3'
  c = entconfig.EntConfig(None)
  c.set_allow_config_mgr_requests(0)
  c.set_var('DEFAULTS', ['enterprise'])
  c.AddDefaults()
  version = c.var('VERSION')
  ent_home = '%s/%s' % (export_hda, version)
  ec = entconfig.EntConfig(ent_home)
  ec.Load()
  return ec


class SuperRootStunnelConfig(object):
  """The class that creates a stunnel config for superroot in federation."""
  
  def __init__(self, federation_config, sys_abstraction, ec=None):
    """Initialize the Superroot Stunnel config creation object.
    
    Args:
      federation_config: The federation network for which stunnel conf is reqd.
      sys_abstraction: The base system methods that we use.
      ec: The enterprise configuration.
    
    Raises:
        FederationConfigException: if the ID of the appliance does not
        have a valid superroot configuration.
    """
    self.__os = sys_abstraction
    self.__federation_config = federation_config
    if ec is None:
      self.__ec = GetEnterpriseConfiguration()
    else:
      self.__ec = ec
    logging.debug('Name - %s' % self.__ec.ENT_CONFIG_NAME)
    self.__super_root_config = (
        self.__federation_config.GetSuperRootConfig(self.__ec.ENT_CONFIG_NAME))

  def GetStunnelConfiguration(self, appliance_id):
    """Generate Stunnel Configuration for a client.
    
    Args:
      appliance_id: the appliance id of the corpus root.
      
    Returns:
      the stunnel conf file contents as a string, None on failure.
    """
    # create the client tunnel file
    tunnel_config = ''
    tunnel_config += ('debug=%s\n' % STUNNEL_DEBUG_LEVEL)
    tunnel_config += ('%s\n' % STUNNEL_CLIENT)
    tunnel_config += ('output=/client_stunnel_%s.log\n' % appliance_id)
    try:
      corpus_root_config = self.__super_root_config.GetCorpusRoot(appliance_id)
    except fed_network_config.FederationConfigException, ex:
      logging.error('Exception in creating client tunnel conf %s' % ex.message)
      return None
    else:
      tunnel_config += ('%s=%s:%s\n' % (STUNNEL_CONNECT,
                        corpus_root_config.GetTunnelIp(),
                        corpus_root_config.GetTunnelPort()))
      return tunnel_config

  def GetStunnelConfigurationInFile(self, appliance_id, file_name):
    """Generate and write stunnel configuration into file.
    
    Args:
      appliance_id: The id of the appliance to generate the config for.
      file_name: the file that the generated config is to be written to.
    
    Returns:
      the file that was open for writing.
    """
    file_object = self.__os.OpenWrite(file_name)
    if file_object:
      tunnel_config = self.GetStunnelConfiguration(appliance_id)
      logging.debug('Print the config %s in %s' % (tunnel_config, file_name))
      if tunnel_config is None:
        return (-1, 'Invalid Stunnel configuration')
      file_object.write(tunnel_config)
      file_object.close()
      return (0, 'Successful configuration')
    return (-1, 'Invalid file object')
  
  def GetStunnelConfigFileName(self, appliance_id):
    return ('/stunnel-%s.conf') % (appliance_id)

  def GetClientCommand(self, appliance_id):
    """Generate the command that will start the pppd and stunnel.
    
    Args:
      appliance_id: The appliance id of the corpus root to connect to
      
    Returns:
      a string containing the command to execute. None on failure.
    """
    try:
      logging.debug('Fetch client command for %s' % appliance_id)
      corpus_root_config = self.__super_root_config.GetCorpusRoot(appliance_id)
    except fed_network_config.FederationConfigException, ex:
      logging.error('Exception in creating client tunnel conf %s' % ex.message)
      return None
    else:
      command_dict = {}
      command_dict['CHROOT'] = STUNNEL_CLIENT_CHROOT
      command_dict['NAME'] = self.__super_root_config.GetId()
      command_dict['REMOTE'] = corpus_root_config.GetId()
      link_name = ('%s-%s' % (self.__super_root_config.GetId(),
                              corpus_root_config.GetId()))
      command_dict['LINK_NAME'] = link_name
      command_dict['STUNNEL_CMD'] = STUNNEL
      command_dict['STUNNEL_CONF'] = self.GetStunnelConfigFileName(appliance_id)
      command_dict['LOCAL_PPP_IP'] = self.__super_root_config.GetPppIp()
      command = (PPPD_CLIENT_COMMAND) % command_dict
      return command
    
  def GetPppPid(self, appliance_id):
    """Get the Process id of the PPP daemon. Use that to kill it.
    
    Args:
      appliance_id: The appliance id that the current ppp dial up is to.
      
    Returns:
      the pid of the process pppd. -1 for any error.
    """
    path = (('%s/var/run/ppp-%s-%s') %
            (STUNNEL_CLIENT_CHROOT, self.__super_root_config.GetId(),
             appliance_id))
    if self.__os.ExistsPath(path):
      pid_file = self.__os.OpenRead(path)
      if pid_file:
        pid = pid_file.read()
        return int(pid)
    return -1

  def GetStopPppClientCommand(self, appliance_id):
    """Get the client command to disconnect the pppd.
    
    Args:
      appliance_id: the id of the appliance to disconnect ppp from.
      
    Returns:
      command to execute or None if failed
    """
    pid = self.GetPppPid(appliance_id)
    if pid != -1:
      command = 'kill -9 %d' % pid
      return command
    return None
  
      
class CorpusRootStunnelConfig(object):
  """The Class that provides the methods to manipulate stunnel configuration."""
  
  def __init__(self, federation_config, sys_abstraction, ec=None):
    """Corpus root stunnel configuration manipulation object."""
    self.__os = sys_abstraction
    self.__federation_config = federation_config
    if ec is None:
      self.__ec = GetEnterpriseConfiguration()
    else:
      self.__ec = ec
      
  def GetApplianceId(self):
    """Get the unique appliance ID.
    
    Returns:
      The unique ID for every appliance that Google makes.
    """
    return self.__ec.ENT_CONFIG_NAME

  def GetStunnelPid(self):
    """Get the process ID of the stunnel process.
    
    Returns:
      the pid of the process. -1 if there is no PID.
    """
    if self.__os.ExistsPath(STUNNEL_PID):
      pid_file = self.__os.OpenRead(STUNNEL_PID)
      if pid_file:
        pid = pid_file.read()
        return int(pid)
    return -1
    
  def GetStunnelConfiguration(self):
    """Generate Stunnel Configuration for an appliance.
    
    Returns:
      the stunnel conf file contents as a string, None on failure.
    """
    logging.debug('Appliance ID %s' % self.__ec.ENT_CONFIG_NAME)
    corpus_root_config = (
        self.__federation_config.GetCorpusRootConfig(self.__ec.ENT_CONFIG_NAME))
    tunnel_config = 'cert=/export/hda3/%s%s\n' % (self.__ec.VERSION,
                                                  STUNNEL_SERVER_CERT)
    key = 'key=/export/hda3/%s%s\n' % (self.__ec.VERSION, STUNNEL_SERVER_KEY)
    tunnel_config += key
    pid = 'pid=/stunnel_federation.pid\n'
    tunnel_config += pid
    tunnel_config += ('chroot=%s\n' % STUNNEL_CHROOT)
    tunnel_config += ('debug=%s\n' % STUNNEL_DEBUG_LEVEL)
    tunnel_config += ('foreground=%s\n' % 'yes')
    tunnel_config += ('%s\n' % STUNNEL_SERVER)
    tunnel_config += ('output=/export/hda3/chroot%s%s\n' %
                      (STUNNEL_LOGS, self.__ec.ENT_CONFIG_NAME))
    tunnel_config += '[ppp]\n'
    listen_port = STUNNEL_LISTEN_PORT
    if corpus_root_config.GetTunnelPort() is not None:
      listen_port = corpus_root_config.GetTunnelPort()
    tunnel_config += ('accept=%s\n' % listen_port)
    tunnel_config += ('exec=%s\n' % STUNNEL_PPPD_EXEC)
    
    # Get the ip that the ppp interface will bind to on the local
    corpus_root_config_ip = corpus_root_config.GetPppIp()
    exec_args = ('execargs=%s %s %s:\n') % (STUNNEL_PPPD_EXEC_ARGS,
                                            self.__ec.ENT_CONFIG_NAME,
                                            corpus_root_config_ip)
    tunnel_config += exec_args
    tunnel_config += ('pty=%s\n' % STUNNEL_PTY)
    return tunnel_config
    
  def GetStunnelConfigurationInFile(self, file_name):
    """Generate and write stunnel configuration into file.
    
    Args:
      file_name: the file that the generated config is to be written to.
    
    Returns:
      the file that was open for writing.
    """
    config_file = self.__os.OpenWrite(file_name)
    if config_file:
      tunnel_config = self.GetStunnelConfiguration()
      config_file.write(tunnel_config)
      config_file.close()
    return (0, 'Successful configuration')

if __name__ == '__main__':
  logging.set_verbosity(logging.INFO)

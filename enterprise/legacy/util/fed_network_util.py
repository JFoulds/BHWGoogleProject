#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.

"""Utility classes that help create a Federation Network."""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

from google3.pyglib import logging

from google3.enterprise.legacy.util import fed_network_config
from google3.enterprise.legacy.util import fed_stunnel_config
from google3.enterprise.legacy.util import stunnel_jail


class CorpusRootStunnelService(object):
  """This class provides the wrapper to start and stop a slave fed server.
  
  The utility class that can creates and helps maintain a corpus root service.
  Corpus Root service is used by Master GSA to connect to over stunnel and then
  wrap PPP over the secure tunnel, to create a pseudo Secure network interface
  /export/hda3/tmp/fed is the chroot that we use for the corpus root server
  where the stunnel server runs with the configuration available in
  /export/hda3/tmp/fed/stunnel.conf.
  """
  
  def __init__(self, sys_abstraction=None, config=None, config_file=None,
               ec=None):
    """The corpus root service needs the xml file for configuration.
    
    Args:
      sys_abstraction: Provides the dependency calls for this object.
      config: The constructed configuration.
      config_file: The configuration xml file location.
      ec: Enterprise configuration.
    """
    if sys_abstraction is None:
      self.__os = stunnel_jail.SystemAbstraction()
    else:
      self.__os = sys_abstraction
    if config_file is None:
      self.__config = config
    else:
      self.__config = fed_network_config.FederationConfig(config_file, None,
                                                          self.__os)
    self.__stunnel_config = fed_stunnel_config.CorpusRootStunnelConfig(
        self.__config, self.__os, ec)
    self.__jail = stunnel_jail.StunnelJail(fed_stunnel_config.STUNNEL_CHROOT,
                                           self.__os)

  def Start(self):
    """Setup the jail, create the stunnel config and start the daemon.
    
    Returns:
      (-1, message) on failure and (0, message) on success.
    """
    self.__jail.Setup()
    
    # Generate the Stunnel Configuration
    try:
      (status_config, message) = (
          self.__stunnel_config.GetStunnelConfigurationInFile(
              fed_stunnel_config.STUNNEL_CONFIG))
    except fed_network_config.FederationConfigException, ex:
      logging.error('Failed to retrieve a valid configuration')
      return (-1, ex.message)
    else:
      if status_config:
        logging.error('Start Stunnel service config setup failed - %d, %s' % (
            status_config, message))
        return (status_config, message)
    
    # Create the CHAP Secrets for the current appliance
    appliance_id = self.__stunnel_config.GetApplianceId()
    (status_chap, message) = self.__config.GetChapSecretsInFile(
        appliance_id, fed_stunnel_config.STUNNEL_CHAP_FILE)
    if status_chap:
      logging.error('Start Stunnel service chap setup failed - %d, %s' % (
          status_chap, message))
      return (status_chap, message)
    
    # Now start the server
    cmd = ('%s %s') % (fed_stunnel_config.STUNNEL,
                       fed_stunnel_config.STUNNEL_CONFIG)
    (status, message) = self.__os.Execute(cmd)
    if status:
      logging.error('Executing (%s) resulted in %d %s' % (cmd, status, message))
    return (status, message)
  
  def Stop(self):
    """Stop the Stunnel CorpusRoot service.
    
    Returns:
      (-1, message) on failure and (0, message) on success.
    """
    pid = self.__stunnel_config.GetStunnelPid()
    if pid == -1:
      logging.error('No such process - possible that stunnel is not running')
      (status_jail_destroy, message) = self.__jail.Destroy()
      return (-1, 'No such process - possible that stunnel is not running')
    else:
      cmd = ('%s -15 %d') % ('kill', pid)
      logging.debug('Executing command %s' % cmd)
      (status_kill, message) = self.__os.Execute(cmd)
      (status_kill, message) = self.__os.Execute('killall -15 stunnel')
      (status_jail_destroy, message) = self.__jail.Destroy()
      return (status_kill, message)
  
  def Status(self):
    """Status of the CorpusRoot Service.
    
    Returns:
      (-1, message) on failure and (0, message) on success.
    """
    pid = self.__stunnel_config.GetStunnelPid()
    if pid == -1:
      logging.error('No such process - possible that stunnel is not running')
      return (-1, 'No such process - possible that stunnel is not running')
    else:
      logging.info('Stunnel running as %d' % pid)
      command = ('netstat -lntp | grep %d' % pid)
      (status_check, message) = self.__os.Execute(command)
      logging.info('Status is %d, %s' % (status_check, message))
      return (0, ('Process is %d') % pid)
    
  def Restart(self):
    """Stop and start the Stunnel CorpusRoot service.
    
    Returns:
      (-1, message) on failure and (0, message) on success.
    """
    self.Stop()
    return self.Start()

        
class SuperRootStunnelService(object):
  """This class provides the wrapper for a SuperRoot Master launch script."""
  
  def __init__(self, sys_abstraction, config=None, config_file=None, ec=None):
    self.__os = sys_abstraction
    if config is None:
      self.__config = fed_network_config.FederationConfig(config_file, None,
                                                          self.__os)
    else:
      self.__config = config
    if ec is not None:
      self.__ec = ec
    else:
      self.__ec = fed_stunnel_config.GetEnterpriseConfiguration()
    self.__stunnel_config = fed_stunnel_config.SuperRootStunnelConfig(
        self.__config, self.__os, self.__ec)
    self.__super_root = self.__config.GetSuperRootConfig(
        self.__ec.ENT_CONFIG_NAME)
      
  def Start(self):
    """Start the connect to all Slaves or Corpus Roots."""
    
    corpus_roots = self.__super_root.GetCorpusRoots()
    # stop all connections
    self.Stop()
    status_start = 0
    message_start = 'Success'
    for corpus_root in corpus_roots:
      (status_reach, message) = self.Status(corpus_root.GetId())
      if status_reach:
        (status_connect, message) = self.Connect(corpus_root.GetId())
        if status_connect:
          logging.error('Connect to the %s appliance failed %d %s' % (
              corpus_root.GetId(), status_connect, message))
          status_start = status_connect
          message_start = message
        else:
          logging.info('Connected to appliance %s' % corpus_root.GetId())
      else:
        logging.info('Connection existing to appliance %s' %
                     corpus_root.GetId())
    return (status_start, message_start)
    
  def Stop(self):
    """Disconnect from all the slaves or corpus roots."""
    corpus_roots = self.__super_root.GetCorpusRoots()
    status_stop = 0
    message_stop = 'Success'
    for corpus_root in corpus_roots:
      (status_disconnect, message) = self.Disconnect(corpus_root.GetId())
      if not status_disconnect:
        logging.error('Disconnect from the %s appliance failed %d %s' %
                      (corpus_root.GetId(), status_disconnect, message))
        status_stop = status_disconnect
        message_stop = message
      else:
        logging.info('Disconnected from appliance %s' % corpus_root.GetId())
    return (status_stop, message_stop)
    
  def Connect(self, appliance_id):
    """Connect to a specific Slave appliance.
    
    Args:
      appliance_id: the appliance ID of the slave that need to be connected to.
      
    Returns:
      (0,message) if success and (non_zero_error, message) if failed.
    """
    try:
      secrets_file = ('%s/etc/ppp/chap-secrets' %
                      fed_stunnel_config.STUNNEL_CLIENT_CHROOT)
      (status_chap_secrets, message) = (
          self.__config.GetChapSecretsInFile(appliance_id, secrets_file))
      if status_chap_secrets:
        logging.error('Exception in getting the chap secret file created')
        return (status_chap_secrets, message)
      file_name = self.__stunnel_config.GetStunnelConfigFileName(appliance_id)
      chroot_file_name = ('%s%s') % (fed_stunnel_config.STUNNEL_CLIENT_CHROOT,
                                     file_name)
      (status_configure, message) = (
          self.__stunnel_config.GetStunnelConfigurationInFile(appliance_id,
                                                              chroot_file_name))
    except fed_network_config.FederationConfigException, ex:
      logging.error('Exception in getting configuration %s' % ex.message)
      return (-1, ex.message)
    else:
      if not status_configure:
        cmd = self.__stunnel_config.GetClientCommand(appliance_id)
        logging.debug('Command Executed %s' % cmd)
        if cmd is None:
          return (-1, 'Command generation failed')
        (status_connect, message) = self.__os.Execute(cmd)
        if status_connect:
          logging.error('Connect to %s appliance failed %d %s' %
                        (appliance_id, status_connect, message))
        else:
          (status_reachable, message) = self.Status(appliance_id)
          if not status_reachable:
            logging.info('Connect to %s appliance success %d %s' %
                         (appliance_id, status_reachable, message))
          logging.error('Connect to %s appliance failed %d %s' %
                        (appliance_id, status_reachable, message))
        return (status_connect, message)
      logging.error('Connect to %s appliance failed - invalid id' %
                    appliance_id)
      return (status_configure, message)
    
  def Disconnect(self, appliance_id):
    """Disconnect from a specific Slave appliance.
    
    Args:
      appliance_id: the appliance ID of the slave, to be disconnected from.
      
    Returns:
      (0,message) if success and (non_zero_error, message) if failed.
    """
    try:
      cmd = self.__stunnel_config.GetStopPppClientCommand(appliance_id)
    except fed_network_config.FederationConfigException, ex:
      logging.error('Exception in getting configuration %s' % ex.message)
      return (-1, ex.message)
    else:
      if cmd is not None:
        (status_disconnect, message) = self.__os.Execute(cmd)
        if not status_disconnect:
          logging.info('Disconnected the connection to %s' % appliance_id)
        else:
          logging.error('Disconnection to %s failed with %d %s' %
                        (appliance_id, status_disconnect, message))
        return (status_disconnect, message)
      else:
        logging.error('No such process exists - no connection existing')
        return (-1, '')

  def Status(self, appliance_id):
    """Checks if the slave can be reached over the connection.
    
    Args:
      appliance_id: The appliance that the status need to be checked with.
    
    Returns:
      (0, 'Success') if reachable, (non zero. 'failure message') otherwise.
    """
    try:
      corpus_root = self.__super_root.GetCorpusRoot(appliance_id)
    except fed_network_config.FederationConfigException, ex:
      logging.error('Exception in getting corpus root %s' % ex.message)
      return (-1, 'failure')
    else:
      ip = corpus_root.GetPppIp()
      cmd = '/bin/ping -qc 2 -w 3 %s' % ip
      logging.info('Executing %s' % cmd)
      (status, output) = self.__os.Execute(cmd)
      logging.info('Executed %s' % cmd)
      if not status:
        lines = output.rsplit('\n')
        logging.error('Ping returned (%s) errors for (%s)' % 
                      (str(lines), appliance_id))
      return (status, output)
          
if __name__ == '__main__':
  logging.set_verbosity(logging.DEBUG)

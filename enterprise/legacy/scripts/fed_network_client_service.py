#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Script to launch clients and connect to a federation corpus root.

This service runs every 2 mins, to ensure that any broken connections are 
re-tried, new corpus root subordinates are added. The service is active only when
there is a federation network configuration existing.
"""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

import commands
import os
import sys
import time

from google3.pyglib import flags
from google3.pyglib import logging

from google3.enterprise.legacy.scripts import ent_service
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import fed_network_config
from google3.enterprise.legacy.util import fed_network_util
from google3.enterprise.legacy.util import fed_stunnel_config
from google3.enterprise.legacy.util import stunnel_jail
from google3.enterprise.license import license_api

# Command flags
flags.DEFINE_string('command', 'DEFAULT', 'Command to execute')
flags.DEFINE_string('appliance_id', 'ALL', 'Appliance Id to connect to')
flags.DEFINE_string('deb', 0, 'debug mode')

FLAGS = flags.FLAGS
FEDERATION_NETWORK_CONFIG = '%s/local/conf/fed_network.xml'

# Executable for corpus root generation
FEDERATION_SUPERROOT_CONFIG_BIN = '%s/local/google/bin/fed_superroot_config.par'
FEDERATION_CONFIGROOT_TEMPLATE = ('%s/local/googledata/enterprise/data/'
                                  'federation_root_template')
FEDERATION_CONFIGROOT_FILE = ('%s/local/googledata/enterprise/data/'
                              'federation_root.cfg')
  

class FederationNetworkClientService(ent_service.ent_service):
  """Manages the federation network client, on every main or superroot."""

  def __init__(self):
    ent_service.ent_service.__init__(self, 'fed_network_client', 0, '2minly', 1,
                                     3600)

  def init_service(self, ent_home):
    ent_service.ent_service.init_service(self, ent_home)
    self.config_file = FEDERATION_NETWORK_CONFIG % ent_home
    self.ent_home = ent_home
    logging.info('Configuration file used %s' % self.config_file)
  
  def IsFederationLicensed(self):
    config = fed_stunnel_config.GetEnterpriseConfiguration()
    license_info = config.ENT_LICENSE_INFORMATION
    return license_info.get(license_api.S.ENT_LICENSE_FEDERATION)
      
  def stop(self):
    logging.info(' -- stopping federation network -- ')
    if self.IsFederationLicensed() and os.path.exists(self.config_file):
      sys_abstraction = stunnel_jail.GetSystemAbstraction()
      jail = stunnel_jail.StunnelJail(fed_stunnel_config.STUNNEL_CLIENT_CHROOT,
                                      sys_abstraction)
      try:
        fed_config = fed_network_config.FederationConfig(self.config_file,
                                                         None,
                                                         sys_abstraction)
        logging.info('Federation config read successfully')
        client = fed_network_util.SuperRootStunnelService(sys_abstraction,
                                                          fed_config)
      except fed_network_config.FederationConfigException, ex:
        logging.error('Exception in configuration %s' % ex.message)
        (status_jail, message) = jail.Destroy()
        return 1
      else:
        (status_connect, message) = client.Stop()  # Disconnect all the clients
        (status_jail, message) = jail.Destroy()
    return 1

  def babysit(self):
    logging.info(' --babysit--')
    self.start()
    return 1
    
  def start(self):
    if self.IsFederationLicensed() and os.path.exists(self.config_file):
      logging.info(' -- starting federation network -- ')
  
      # start logging only if federation is enabled
      log_file_name = ('/export/hda3/tmp/fed_network_client_%s' %
                       time.strftime('%d-%b-%y'))
      log_file = open(log_file_name, 'a+')
      logging.set_logfile(log_file)
      logging.set_verbosity(logging.DEBUG)
      sys_abstraction = stunnel_jail.GetSystemAbstraction()
      
      # setup the stunnel jail
      jail = stunnel_jail.StunnelJail(fed_stunnel_config.STUNNEL_CLIENT_CHROOT,
                                      sys_abstraction)
      (status_jail, message) = jail.Setup()
      if status_jail:
        logging.error('The CHROOT Jail could not be setup %s' % message)
        return 1
      try:
        fed_config = fed_network_config.FederationConfig(self.config_file,
                                                         None,
                                                         sys_abstraction)
        logging.info('Federation config read successfully')
        client = fed_network_util.SuperRootStunnelService(sys_abstraction,
                                                          fed_config)
      except fed_network_config.FederationConfigException, ex:
        logging.error('Exception in configuration %s' % ex.message)
        return 1
      else:
        # Connect to all the subordinates
        (status_connect, message) = client.Start()
        
        # Create the config root
        (status_config, message) = CreateSuperRootConfig(self.ent_home)
    return 1


def CreateSuperRootConfig(ent_home):
  fed_configroot_config_bin = FEDERATION_SUPERROOT_CONFIG_BIN % ent_home
  fed_config_template = FEDERATION_CONFIGROOT_TEMPLATE % ent_home
  fed_config_root_file = FEDERATION_CONFIGROOT_FILE % ent_home
  fed_config_network_file = FEDERATION_NETWORK_CONFIG % ent_home
  enterprise_config = fed_stunnel_config.GetEnterpriseConfiguration()
  command = ('%s --template=%s --config=%s --destination=%s --appliance_id=%s'
             % (fed_configroot_config_bin, fed_config_template,
                fed_config_network_file, fed_config_root_file,
                enterprise_config.ENT_CONFIG_NAME))
  (status, message) = commands.getstatusoutput(command)
  if status:
    logging.error('Generation of superroot configuration failed')
  else:
    permission_command = ('chmod 777 %s' % fed_config_root_file)
    logging.info('Successfully generated the superroot configuration')
  return (status, message)
  
    
def main(argv):
  FLAGS(argv)
  if FLAGS.deb:
    logging.set_verbosity(logging.DEBUG)
  
  # start a service if the command is the default specified in flags
  if FLAGS.command is 'DEFAULT':
    fed_network_client = FederationNetworkClientService()
    logging.debug('Launched as a service. Start the service.')
    fed_network_client.execute(argv)
    return
  ec = fed_stunnel_config.GetEnterpriseConfiguration()
  file_path = FEDERATION_NETWORK_CONFIG % ec.ENTERPRISE_HOME
  sys_abstraction = stunnel_jail.GetSystemAbstraction()
  try:
    fed_config = fed_network_config.FederationConfig(file_path, None,
                                                     sys_abstraction)
    logging.info('Federation config read successfully')
    client = fed_network_util.SuperRootStunnelService(sys_abstraction,
                                                      fed_config)
  except fed_network_config.FederationConfigException, ex:
    print ex.message
    logging.error('Exception in configuration %s' % ex.message)
    sys.exit(-1)
  else:
    if FLAGS.command is 'CONNECT':
      if FLAGS.appliance_id is 'ALL':
        (status_connect, message) = client.Start()
      else:
        (status_connect, message) = client.Connect(FLAGS.appliance_id)
      logging.info('Connect resulted in %d %s', status_connect, message)
      sys.exit(status_connect)
    elif FLAGS.command is 'DISCONNECT':
      if FLAGS.appliance_id is 'ALL':
        (status_disconnect, message) = client.Stop()
      else:
        (status_disconnect, message) = client.Disconnect(FLAGS.appliance_id)
      logging.info('Disconnect resulted in %d %s', status_disconnect, message)
      sys.exit(status_disconnect)


if __name__ == '__main__':
  logging.set_verbosity(logging.INFO)
  main(sys.argv)


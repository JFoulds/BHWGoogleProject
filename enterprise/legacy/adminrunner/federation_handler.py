#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.
#
"""The federation command handler for AdminRunner.

This handler responds to the following command:

  1. reconnect

     It reconnects all the client(slave) sessions first and then
     stop the server (which would come up automatically) so that
     it will read the modified configuration.
  
  2. statusall

     It fetches and returns the status of all the connected slaves.
     It returns connection status as name-value pair of <appliance-id>=<status>
     where <status> can be one of these values:
     OK : Connection successfully established with the slave.
     ERROR: Connection could not be established with the slave.
"""

__author__ = 'pshroff@google.com (Prakash Shroff)'

import commands
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import E


class FederationHandler(admin_handler.ar_handler):
  """Processes all the federation related commands for AdminRunner."""
  
  def __init__(self, conn, command, prefixes, params):
    """Initialize Handler params."""
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    
  def get_accepted_commands(self):
    """Mapping of all accepted commands and their callback method names."""
    return {
        'reconnect': admin_handler.CommandInfo(
            0, 0, 0, self.Reconnect),
        'statusall': admin_handler.CommandInfo(
            0, 0, 0, self.StatusAll)
    }
    
  def Reconnect(self):
    """Disconnect and then connect all the federated sessions.

    Returns:
      0 for Success (inclduing result string).
      1 for Error.
    """

    fed_client_reactivate_cmd = (
        '/etc/rc.d/init.d/fed_network_client_%s restart'  % (
            self.cfg.getGlobalParam('VERSION')))
    logging.info('Executing Client Reconnect Command: %s' % (
        fed_client_reactivate_cmd))
    
    # Executing command fed_network_client restart to 
    # reconnect federated client network.
    retcode, result = E.getstatusoutput(
        'secure_script_wrapper -e %s' % (
            fed_client_reactivate_cmd)
        )
    if not retcode:
      logging.info('0\n%s' % (result))
    else:
      logging.info('Could not reconnect Federation Network: %s' % (result))
      return '1'
      
    fed_server_reactivate_cmd = '/etc/rc.d/init.d/fed_network_%s stop'  % (
        self.cfg.getGlobalParam('VERSION'))
    logging.info('Executing server stop command: %s' % (
        fed_server_reactivate_cmd))
    
    # Executing command fed_network restart to start the server.
    retcode, result = E.getstatusoutput(
        'secure_script_wrapper -e %s' % (
            fed_server_reactivate_cmd)
        )
    if not retcode:
      return '0\n%s' % result
    else:
      logging.info('Could not start Federated Network Server: %s' % (result))
      return '1'
  
  def StatusAll(self):
    """Fetches connection status of all slaves."""
    fed_client_statusall_cmd = (
        '%s/local/google3/enterprise/legacy/scripts/'
        'fed_network_client_service.py --command=STATUS --appliance_id=ALL' % (
            self.cfg.getGlobalParam('ENTERPRISE_HOME')))

    logging.info('Executing Client StatusAll Command: %s' % (
        fed_client_statusall_cmd))
    (status, message) = commands.getstatusoutput(fed_client_statusall_cmd)
    if status:
      logging.error('Failed while getting status of all slaves')
    else:
      logging.info('Successfully fetched slave status')
    return message

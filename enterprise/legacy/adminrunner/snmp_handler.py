#!/usr/bin/python2.4
#
# (c) Copyright 2004 Google Inc.
# Anant Chaudhary <anantc@google.com>
#
# Deal with SNMP configuration files and enable/disable
# Since all of this is in domain of a SuperUser
# all this script does is call another which is run as
# superuser (using the secure_script_wrapper)
#
# The commands we respond to are
#
# 1. setConfig:
#               This is used to set the configuration entries in file /usr/share/snmp/snmpd.conf
#               or the file /usr/local/share/snmp/snmpd.conf, which is used by SNMP agent
#               to pick up configuration information about permissions of users/communities
#               @param: String - fileData
#
#
# 2. setUserConfig:
#               This is used to set the file used by SNMP agent to pick up persistent
#               information about existing users and to create new users
#               @param: String - fileData
#
#
# 3. start:     This is used to start the SNMP agent
#
# 4. stop:      This is used to stop the SNMP agent
#
# 5. addUser:   This is used to add one user to the config file
#               @param: String - user Info

################################################

__author__ = 'Anant Chaudhary <anantc@google.com>'

import threading
import os
import string
from google3.enterprise.legacy.adminrunner import admin_handler
import commands
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M


class SNMPHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.snmpWrapperPath = (
        '%s/local/google3/enterprise/legacy/util/snmp_config.py' %
        self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    self.machines = self.cfg.getGlobalParam('MACHINES')
    self.version = self.cfg.getGlobalParam('VERSION')
    # see if we are on a cluster
    if len(self.machines) > 1:
      self.type = 'CLUSTER'
    else:
      self.type = 'ONEBOX'
    self.master = [self.cfg.getGlobalParam('MASTER')]

  def get_accepted_commands(self):
    return {
      'start'         : admin_handler.CommandInfo(0, 0, 0, self.start),
      'stop'          : admin_handler.CommandInfo(0, 0, 0, self.stop),
      'setConfig'     : admin_handler.CommandInfo(0, 0, 1, self.setConfig),
      'addUser'       : admin_handler.CommandInfo(0, 0, 1, self.addUser),
      'setUserConfig' : admin_handler.CommandInfo(0, 0, 1, self.setUserConfig),
      }

  def start(self):
    ''' This starts the SNMP daemon only on the MASTER'''
    cmd = 'secure_script_wrapper -p2 %s start' % self.snmpWrapperPath
    logMsg = 'SNMP started'
    return self.execCmd(cmd, self.master, logMsg)

  def stop(self):
    ''' This stops the SNMP daemon '''
    cmd = 'secure_script_wrapper -p2 %s stop' % self.snmpWrapperPath
    logMsg = 'SNMP stopped'
    return self.execCmd(cmd, self.machines, logMsg)

  def setConfig(self, fileData):
    ''' Sets the SNMP Config File '''
    cmd = 'secure_script_wrapper -p2 %s setConfig %s %s %s' % (self.snmpWrapperPath,
        commands.mkarg(fileData), commands.mkarg(self.version), commands.mkarg(self.type))
    logMsg = 'SNMP config updated'
    return self.execCmd(cmd, self.machines)

  def addUser(self, userInfo):
    ''' Sets the persistent Config File of SNMP '''
    cmd = 'secure_script_wrapper -p2 %s addUser %s' % (self.snmpWrapperPath, commands.mkarg(userInfo))
    username = userInfo.split()[-1]
    logMsg = 'SNMP user added:%s' % username
    return self.execCmd(cmd, self.machines, logMsg)

  def setUserConfig(self, usersToAdd):
    ''' delete some users and reset the User Config File'''
    cmd = 'secure_script_wrapper -p2 %s setUserConfig %s' % (self.snmpWrapperPath, commands.mkarg(usersToAdd))
    logMsg = 'SNMP users configuration changed' 
    return self.execCmd(cmd, self.machines, logMsg)

  def execCmd(self, cmd, machines, logMsg=None):
    ''' Takes a command string and returns its output'''
    outputList = []
    retcode  = E.execute(machines, cmd, outputList, 60)
    result = str(outputList)
    if retcode != 0:
      return '1'
    if logMsg:
      self.writeAdminRunnerOpMsg(logMsg);
    return '0\n%d\n%s' % (len(result), result)


if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

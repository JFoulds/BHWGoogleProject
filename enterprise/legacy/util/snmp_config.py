#!/usr/bin/python2.4
#
# Copyright (C) 2004 Google Inc.
#
# anantc@google.com

'''
A SUID root script that manages SNMP Configuration
The SNMP Configuration files are only readable by root,
so we need to put all the code that accesses it in this script.

Usage:
snmp_config.py {start|stop}
snmp_config.py setUserConfig <fileData>
snmp_config.py setConfig <fileData> <enterprise-version>
snmp_config.py addUser <userData>
'''
import os
import sys
import string
import commands

SNMP_CONF_FILE = '/usr/share/snmp/snmpd.conf'
SNMP_USER_FILE = '/var/net-snmp/snmpd.conf'
SNMP_START_COMMAND = '/etc/rc.d/init.d/snmpd start >&/dev/null'
SNMP_STOP_COMMAND = '/etc/rc.d/init.d/snmpd stop >&/dev/null'

# Hardcoded data that is always written in the config file
SNMP_CONF_FILE_STATIC_DATA='''
# SNMP Access Configuration

# For v1 and v2 communities
group gsa-group v1 gsa-secname
group gsa-group v2c gsa-secname

access gsa-group "" v1 noauth exact gsa-view none none
access gsa-group "" v2c noauth exact gsa-view none none

# For v3 users
access gsa-user-noauth "" usm noauth exact gsa-view none none
access gsa-user-auth "" usm auth exact gsa-view none none
access gsa-user-priv "" usm priv exact gsa-view none none
'''

SNMP_ONEBOX_VIEW='''
# For restricting view
# Include all
view gsa-view included .1
# Exclude ucd-snmp info
view gsa-view excluded .1.3.6.1.4.1.2021
# Exclude net-snmp-agent-mibs
view gsa-view excluded .1.3.6.1.4.1.8072
# Exclude tcp and udp tables
view gsa-view excluded .1.3.6.1.2.1.6.13
view gsa-view excluded .1.3.6.1.2.1.7.5
# Exclude SNMP USM and VACM information
view gsa-view excluded .1.3.6.1.6.3
# Exclude sysLocation and SysContact
view gsa-view excluded .1.3.6.1.2.1.1.6
'''

SNMP_CLUSTER_VIEW='''
# For restricting view
# Include only GSA specific MIB
view gsa-view included .1.3.6.1.4.1.11129
view gsa-view included .1.3.6.1.2.1.1.1.0
view gsa-view included .1.3.6.1.2.1.1.2.0
view gsa-view included .1.3.6.1.2.1.1.3.0
view gsa-view included .1.3.6.1.2.1.1.4.0
view gsa-view included .1.3.6.1.2.1.1.5.0
view gsa-view included .1.3.6.1.2.1.1.8.0
'''

SNMP_SYS_INFO='''
# System information
sysname Google Search Appliance
syscontact appliance-support@google.com
sysdescr GSA Version'''

# with above static data in config file,
# to add a community xxx add the line:
# "com2sec gsa-secname default xxx" to file
# to add a snmpv3 user xxx
# add the line: " group gsa-user-*** usm xxx"
# where *** is noauth|auth|priv depending on user's restrictions

# default community always added to monitor that the snmp daemon
# is responding, accessible only from localhost
SNMP_MONITOR_COMMUNITY = 'com2sec gsa-secname 127.0.0.1 gsa-monitor-community\n\n'

def StartSnmp():
  '''
  Start SNMP daemon
  return 0 on success 1 on failure
  '''
  err = os.system(SNMP_START_COMMAND)
  return err != 0

def StopSnmp():
  '''
  Stop SNMP daemon
  return 0 on success 1 on failure
  '''
  err = os.system(SNMP_STOP_COMMAND)
  return err != 0

def setConfigFile(fileData, gsa_version, type):
  '''
  Set SNMP Config File
  @param fileData: records to be written '\\n' separated users|communities
  @param gsa_version: enterprise software version
  @param type: CLUSTER|ONEBOX
  return 0 on success 1 on failure
  '''
  try:
    # write the static data
    fwr = open(SNMP_CONF_FILE, 'w')
    fwr.write(SNMP_CONF_FILE_STATIC_DATA)
    if type == 'ONEBOX':
      fwr.write(SNMP_ONEBOX_VIEW)
    else:
      fwr.write(SNMP_CLUSTER_VIEW)
    fwr.write('%s %s\n\n' % (SNMP_SYS_INFO, gsa_version))
    fwr.write(SNMP_MONITOR_COMMUNITY)
    # write user/community info
    lines = string.split(fileData, '\\n')
    for line in lines:
      # check to see if user or community
      # user is of form <uname> <authlevel>
      # community is just <communityName>
      parts = line.split()
      if len(parts) > 1:
        # a user
        fwr.write('group gsa-user-%s usm %s\n' % (parts[1], parts[0]))
      else:
        # community
        fwr.write('com2sec gsa-secname default %s\n' % parts[0])
    fwr.close()
    return 0
  except IOError:
    return 1

def addUser(userData):
  '''
  Set SNMP User Config File
  @param userData: string to add a user
  return 0 on success 1 on failure
  '''
  try:
    fwr = open(SNMP_USER_FILE, 'a')
    fwr.write('%s\n' % userData)
    fwr.close()
    return 0
  except IOError:
    return 1

def setUserConfig(fileData):
    '''
    Set SNMP User Config File
    @param fileData: records corresponding to adding all users
    which still exist
    return 0 on success 1 on failure'''
    try:
      # first get all lines of file except
      # configured users
      fwr = open(SNMP_USER_FILE, 'r')
      lines = fwr.readlines()
      fwr.close()
      # look at all existing info and remove any users that might be present
      fileLines = [line for line in lines if line.find('usmUser') == -1 and line.find('createUser') == -1]
      fileStr = ''.join(fileLines)
      # Now write these lines to the file
      fwr = open(SNMP_USER_FILE, 'w')
      fwr.write(fileStr)
      lines = string.split(fileData, '\\n')
      for line in lines:
        fwr.write('%s\n' % line)
      fwr.close()
      return 0
    except:
      return 1

if __name__ == '__main__':
  if len(sys.argv) == 2:
    if sys.argv[1] == 'start':
      sys.exit(StartSnmp())
    elif sys.argv[1] == 'stop':
      sys.exit(StopSnmp())
    else:
      sys.exit(__doc__)
  elif len(sys.argv) == 3:
    if sys.argv[1] == 'addUser':
      sys.exit(addUser(sys.argv[2]))
    elif sys.argv[1] == 'setUserConfig':
      sys.exit(setUserConfig(sys.argv[2]))
    else:
      sys.exit(__doc__)
  elif len(sys.argv) == 5:
    if sys.argv[1] == 'setConfig':
      sys.exit(setConfigFile(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
      sys.exit(__doc__)
  else:
    sys.exit(__doc__)

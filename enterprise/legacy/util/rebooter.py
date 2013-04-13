#!/usr/bin/python2.4
#
# Copyright 2002-2003 Google, Inc.
#

'Reboots or shuts down cluster machines.'


import time
import string

from google3.enterprise.legacy.util import E
from google3.pyglib import logging

###############################################################################

# Command line for machine reboot
EXEC_REBOOT = ('%s/local/google3/enterprise/legacy/util/reboot_machine.py '
               '%s %s %s')

REBOOT_PARAM = ['on', 'off', 'reboot', 'delayed_off']

APC_ON = 0
APC_OFF = 1
APC_REBOOT = 2
APC_DELAYED_OFF = 3

###############################################################################

def HaltMachines(enthome, machines):
  'Stops and powers down machines.'

  logging.info("Halting machines: %s" % string.join(machines, ","))
  E.execute(machines, '/sbin/shutdown -h now &', None, 1)
  time.sleep(60)
  for machine in machines:
    SendAPCCommand(enthome, machine, APC_OFF)
  return 0

def RebootMachine(enthome, machine):
  'Reboots a machine.'
  if machine == E.getCrtHostName():
    # Rebooting ourself
    logging.info('Rebooting %s' % machine)
    E.execute([E.LOCALHOST], '/sbin/shutdown -r now', None, 1)
    # If we're still alive after a minute , the APC will kick in
  else:
    # Try shutting down cleanly first
    logging.info('Shutting down %s' % machine)
    E.execute([machine], '/sbin/shutdown -h now &', None, 1)
  time.sleep(60)
  logging.info('Rebooting %s via APC' % machine)
  return SendAPCCommand(enthome, machine, APC_REBOOT)

def SendAPCCommand(enthome, machine, cmd):
  'Sends commands to the APC.'
  return E.ERR_OK != E.execute([E.LOCALHOST],
                               EXEC_REBOOT % (enthome,
                                              enthome,
                                              machine,
                                              REBOOT_PARAM[cmd]), None, 1)

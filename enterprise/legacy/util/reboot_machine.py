#!/usr/bin/python2.4
#
# (c) Google 2001
# cpopescu@google.com
#
# This reboots a machine - it might do it via an apc connection or by mailing
# reboots@google.com
#
###############################################################################
"""
Usage:
 reboot_machine.py <global_config> <machine> <on|off|reboot|delayed_off> [<extra email>]
"""

import re
import string
import sys
import socket
import time
import signal

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import entconfig

#
# The reboot command to the APC --
# We connect to the apc and send this command to reboot the machine on
# outlet %s. (The command is set to navigate through the apc menus
# to outlet %s and reboot it)
#
# These commands are tested for following APC versions:
#       Network Management Card AOS v 1.1.6
#       Rack PDU APP v1.0.1 and v1.0.2
#
# 10/Dec/2007 (vardhman): Added the code to support version 3.0.0 + for APC.
# Right now we just check if version > 3.0.0 we execute a different set of
# command than what we do if version is lesser than the number.
#
# The difference in the commands is because of the change of menu options after
# version 3.0.0, the arrays APC_V26_COMMANDS and APC_V30_COMMANDS are the only
# different subsets of the full commands set.

APC_LOGIN_COMMANDS = ["apc\r\n",  # login
                      "apc\r\n",  # pass word
                      "1\r\n",]   # device management, first menu replay

APC_V26_COMMANDS = ["3\r\n",    # Outlet Contro/Config
                    "%s\r\n",   # outlet
                    "2\r\n",    # configure outlet
                    "3\r\n",    # Power off delay
                    "120\r\n",  # 120 seconds
                    "5\r\n",    # Accept changes
                    "\033",     # back
                    "1\r\n",    # control outlet
                    "%d\r\n",   # operation
                    "YES\r\n",  # confirmation
                    "\r\n",
                    ]

APC_V30_COMMANDS = ["2\r\n",    # Outlet management
                    "1\r\n",    # Outlet control/config
                    "%s\r\n",   # outlet
                    "2\r\n",    # configure outlet
                    "3\r\n",    # Power off delay
                    "120\r\n",  # 120 seconds
                    "5\r\n",    # Accept changes
                    "\033",     # back
                    "1\r\n",    # control outlet
                    "%d\r\n",   # operation
                    "YES\r\n",  # confirmation
                    "\r\n",
                    "\033",     # extra back
                    ]

APC_LOGOUT_COMMANDS = ["\033",     # back
                       "\033",
                       "\033",
                       "\033",
                       "4\r\n",    # logout
                      ]

VERSION_INFO_RE = re.compile('American Power Conversion.*v(?P<version>[\d.]*)',
                             re.MULTILINE)

# Operations we can do on an outlet
APC_VALUES = {
  "on"          : 1,
  "off"         : 2,
  "reboot"      : 3,
  "delayed_off" : 5,
  }
OUTLET_INDEX = 4
OP_INDEX = 11
LOGIN_OP_INDEX = 1
###############################################################################

def AlarmHandler(signum, frame):
  raise IOError, "Host not responding"

###############################################################################

def VersionCompare(version1, version2):
  """Determines if version1 > version2.

  args:
    version1: A dot separated version number
    version2: Another dot sepatated version number
    (right now both are expected to have equal number of dots)
  returns:
    1 if version 1 > version2
    0 if version 1 == version2
    -1 if version 1 < version2

  e.g (3.3.3, 3.1.2) returns 1
      (3.1.2, 3.2.1) returns -1
  """
  version1_arr = string.split(version1, '.')
  version2_arr = string.split(version2, '.')

  i = 0
  while i < len(version1_arr):
    t = int(version1_arr[i]) - int(version2_arr[i])
    if t != 0:
      return t
    i += 1

  return 0


def RebootMachine(apc, outlet, operation):
  """Returns the status of executing reboot command.

  args:
    apc: The ip address of the APC
    outlet: The outlet number for the machine
    operation: The operation, amongst the keys for APC_VALUES to be performed
    on the node
  returns:
    0 if successful, 1 otherwise
  """

  signal.signal(signal.SIGALRM, AlarmHandler)
  signal.alarm(90)
  logging.info("Rebooting %s:%s -- %s" % (apc, 23, outlet))
  op_index = OP_INDEX
  outlet_index = OUTLET_INDEX
  operation_idx = APC_VALUES[operation]
  version = 2

  cmds = APC_LOGIN_COMMANDS
  err = 1
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((apc, 23))

    # we login to apc via telnet, and then give commands based on the version
    # information extracted from the welcome mesg
    cmd_idx = 0
    while cmd_idx < len(cmds):
      cmd = cmds[cmd_idx]
      time.sleep(1)
      buf = s.recv(65536)

      # when this script returns 1, adminrunner_client.RebootMachine()
      # assumes that the reboot has not actually taken place.
      # Once we have sent out the confirmation command, we cannot
      # return 1. And we don't really care about the errors after that.
      if cmd_idx == LOGIN_OP_INDEX + 1:

        # we get the version information here
        version_match = VERSION_INFO_RE.search(buf)
        apc_version = version_match.group('version')
        logging.info("APC version is %s" % apc_version)

        # we have different set of commands dependening on the version
        if VersionCompare(apc_version, '3.0.0') > 0:
          version = 3
          cmds.extend(APC_V30_COMMANDS)
          op_index = OP_INDEX + 1
          outlet_index = OUTLET_INDEX + 1
        else:
          cmds.extend(APC_V26_COMMANDS)

        cmds.extend(APC_LOGOUT_COMMANDS)
        cmds[op_index] = cmds[op_index] % operation_idx
        cmds[outlet_index] = cmds[outlet_index] % outlet
      if cmd_idx > op_index:
        err = 0
      s.send(cmd + "\n")
      cmd_idx = cmd_idx + 1

  except Exception, e:
    logging.error(e)
    pass

  s.close()
  return err


if __name__ == "__main__":

  config = entconfig.EntConfig(sys.argv[1])
  if not config.Load():  sys.exit(__doc__)

  try:
    victim = sys.argv[2]
    apcval = APC_VALUES[sys.argv[3]]
  except:
    sys.exit(__doc__)

  if not config.var('AUTO_REBOOT'):
    sys.exit(0)

  if ( not config.var('APC_MAP') or
       not config.var('APC_MAP').has_key(victim) ):
    ## just return with status value 1
    sys.exit(1)
  else:
    ##
    ## global param APC_MAP has form:
    ## <machine1>:<apc1>-<outlet1>, .. <machine2>:<apc2>-<outlet2>
    ##
    (apc, outlet) = string.split(config.var('APC_MAP')[victim], "-")

    logging.info("%s'ing %s:%s -- %s" % (sys.argv[3], apc, 23, outlet))
    status = RebootMachine(apc, outlet, sys.argv[3])

  ## Done with no reboot
  sys.exit(status)

#!/usr/bin/python2.4
#
# This handy command reads global config file on the current machine and
# writes the value of CONFIGVERSION parameter together with the machine name.
# (Used by periodic_script.py)
#
###############################################################################
"""
Usage :
  get_config_version.py <enthome>
"""

import sys
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import entconfig


if __name__ == '__main__':
  config = entconfig.EntConfig(sys.argv[1])
  if not config.Load():
    version = ""
  else:
    version = config.var("CONFIGVERSION")

  print "%s-%s" % (version, E.getCrtHostName())

###############################################################################

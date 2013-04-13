#!/usr/bin/python2.4
#
# Stub to test testwords for a collection on a machine -- needed because
# of the signal timeout that we can have only in the main thread of an
# application
#
##############################################################################
"""
Usage:
 gws_production_check.py <gws_machine> <port> <collection> <testwords>
                         <epochs> <num>
"""

import sys
import string
from google3.gws import gws_results

if __name__ == '__main__':

  try:
    gws = sys.argv[1]
    port = string.atoi(sys.argv[2])
    site = sys.argv[3]
    testwords = sys.argv[4]
    epochs = map(string.atoi, map(string.strip,
                                  string.split(sys.argv[5], ",")))
    epochs.sort()
    epochs.reverse()
    num = string.atoi(sys.argv[6])
  except:
    sys.exit(__doc__)

  # Indirect anything to /dev/null
  out = sys.stdout
  err = sys.stderr
  dev_null = open("/dev/null", "w")
  sys.stdout = dev_null
  sys.stderr = dev_null

  result = gws_results.TestPrerequisites(gws, port, site, testwords, epochs, num)

  # restore the defaults
  sys.stdout = out
  sys.stderr = err

  print repr(result)

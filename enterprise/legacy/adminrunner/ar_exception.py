#!/usr/bin/python2.4
#
# (c) 2002 Google inc
# cpopescu@google.com
#
# Exception for admin runner
#
###############################################################################

# General
ONGOING            = - 1
LOADPARAMS         = - 2
INACTIVESTART      = - 3
ERROROTHER         = - 4
IOERROR            = - 5
SAVEPARAMS         = - 6
NOTENOUGHMACHINES  = - 7
VALIDATEPARAMS     = - 8
SAVERUNTIMEPARAMS  = - 9
INVALIDCOMMAND     = -10
REBOOTING          = -11

# errors when creating a new collection
TOOMANYCRAWLS      = -12
INVALIDCONFIGFILE  = -13
CANTCREATEDIRS     = -14
INVALIDNAME        = -15
COLLECTIONEXISTS   = -16

# license related
LICENSELIMIT       = -17
LICENSEINVALID     = -18
LICENSEERROR       = -19
LICENSNOTSTARTEDYET= -20

class ARException(EnvironmentError):
    """ Some admin runner operation failed (code above)."""
    pass


###############################################################################

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

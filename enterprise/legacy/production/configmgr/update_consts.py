#!/usr/bin/python2.4
# (c) 2002 Google inc
# cpopescu@google.com
#
# For each parameter that can be changes some operations can be defined.
# - First, if it is a file parameter then the param itself is not changed
#  but the file it points to
# - Then some operations that have to be taken to be reflected in the
#  server themself. For some parameters is OK update them by talking
#  to the servers, for others we have to hup/restart the servers
#

class UpdateEntry:
  """
  Small struct that holds information about how to update data for a parameter
  Members:
     paramtype - the type of the parameter
     server_change_list - a list of ServerChange
  """
  def __init__(self, paramtype, server_change_list):
    assert paramtype in (NORMAL, FILETYPE, BOOLTYPE)
    assert type(server_change_list) == type([])
    self.paramtype = paramtype
    self.server_change_list = server_change_list

class ServerChange:
  """
  Struct that holds information about what changes to do to a server
  when updating a parameter
    stype: the server type (e.g. 'urlmanager')
    paramname : the parameter for the v command update (can be None)
    updateproc : update procedure -- how to do it v/http/None
    postop : what to do to the server post update hup/restart/None
  """
  def __init__(self, stype, paramname, updateproc, postop):
    assert stype
    # Set actual int values for None
    if updateproc == None: updateproc = CMD_NONE
    if postop == None: postop = POSTOP_NONE

    assert updateproc in (CMD_HTTP, CMD_V, CMD_NONE)
    assert postop in (POSTOP_HUP, POSTOP_RESTART, POSTOP_NONE)

    self.stype = stype
    self.paramname = paramname
    self.updateproc = updateproc
    self.postop = postop

#############################################################################

# Types
NORMAL              = 0
FILETYPE            = 1
BOOLTYPE            = 2

# Command codes
CMD_NONE = 0       # No operation
CMD_HTTP = 1       # Use the HTTP version
CMD_V    = 2       # Use the 'v' version

# Post operation codes
POSTOP_NONE     = 0    # No postop
POSTOP_HUP      = 1    # Hup the server after change
POSTOP_RESTART  = 2    # Restart server after change

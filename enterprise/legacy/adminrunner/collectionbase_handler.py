#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# davidw@google.com
#
# The base for handlers that deal with children of
#
###############################################################################

import sys
import string
from google3.pyglib import logging
import traceback

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.tools import M
from google3.enterprise.legacy.util import config_utils

###############################################################################

class CollectionBaseHandler(admin_handler.ar_handler):
  """
  This is an abstract class. You have to override get_accepted_commands,
  construct_collection_object and check_max_license
  """
  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg in non-null only for testing (we cannot have multiple constructors)
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def construct_collection_object(self, name):
    raise "Override get_accepted_commands"

  def check_max_license(self):
    raise "Override check_max_license"

  def create(self, name, params=None):
    coll_obj = self.construct_collection_object(name)

    # see if the collection/frontend/restrict exists
    if coll_obj.Exists():
      logging.error("Can't create %s [%s]; already exists" %
                    (coll_obj.print_name, name))
      return 1

    # validate the collection/frontend/restrict name
    if not entconfig.IsNameValid(name):
      logging.error("Invalid %s name %s -- cannot create" %
                    (coll_obj.print_name, name))
      return 2

    # check license
    if not self.check_max_license():
      return 5

    ok = 0
    try:
      # create the collection/frontend/restrict object
      try:
        if not coll_obj.Create(params=params): return 3
        ok = 1
      except Exception, e:
        (t, v, tb) = sys.exc_info()
        exc_msg = string.join(traceback.format_exception(t, v, tb))
        logging.error(exc_msg)
        ok = 0
    finally:
      if not ok:
        # cleanup
        logging.error("Failed to create %s [%s]" % (coll_obj.print_name, name))
        coll_obj.Delete()
        return 4
    # log this creation
    msg = M.MSG_LOG_CREATE_COLLECTION % (coll_obj.print_name, name)
    self.writeAdminRunnerOpMsg(msg)
    return 0

  def get_error_message(self, err):
    """ Returns a string corresponding to the error number from create"""
    msgs = {1: 'Already exists', 2: 'Invalid name',
            3: 'Creation failed', 4: 'Creation error',
            5: 'License exceeded'}
    return msgs.get(err, '')

  def delete(self, name):
    coll_obj = self.construct_collection_object(name)
    coll_obj.Delete()

    # delete search logs, search reports of this collection if any.
    self.cfg.logmanager.deleteCollection(name)

    # log this deletion
    msg = M.MSG_LOG_DELETE_COLLECTION % (coll_obj.print_name, name)
    self.writeAdminRunnerOpMsg(msg)
    return 0

  def getvar(self, name, varName):
    coll_obj = self.construct_collection_object(name)
    try:
      value = coll_obj.get_var(varName)
    except KeyError:
      return '1'

    return "%s = %s" % (varName, repr(value))

  def setvar(self, name, varName, varVal):
    val = {}
    config_utils.SafeExec(string.strip(varVal), val)
    if not val.has_key(varName): return 1
    value = val[varName]

    coll_obj = self.construct_collection_object(name)

    try:
      errors = coll_obj.set_var(varName, value, validate = 1)
    except KeyError:
      return 1

    return admin_handler.formatValidationErrors(errors)

  def getfile(self, name, varName):
    coll_obj = self.construct_collection_object(name)

    try:
      file_name = coll_obj.get_var(varName)
    except KeyError:
      return '1'
    if not file_name:
      logging.error('No file for %s' % varName)
      return '1'

    out = open(file_name, "r").read()
    return "%s\n%s" % (len(out), out)

  def setfile(self, name, varName, varBody):
    coll_obj = self.construct_collection_object(name)

    # There's no infrastructure for returning warnings, so we'll just
    # silently convert any non-UTF8 characters.
    varBody = entconfig.RepairUTF8(varBody)

    try:
      errors = coll_obj.set_file_var_content(varName, varBody, validate = 1)
    except KeyError:
      return 1

    return admin_handler.formatValidationErrors(errors)

  def validate_var(self, name, varName):
    coll_obj = self.construct_collection_object(name)
    errors = coll_obj.validate_var(varName)
    return admin_handler.formatValidationErrors(errors)

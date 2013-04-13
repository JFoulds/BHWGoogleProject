#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# davidw@google.com
#
# The AdminRunner handler for dealing with frontends
#
###############################################################################

import string
from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.adminrunner import collectionbase_handler

###############################################################################

class FrontendHandler(collectionbase_handler.CollectionBaseHandler):

  def get_accepted_commands(self):
    return {
      "list"              : admin_handler.CommandInfo(
      0, 0, 0, self.list),
      "create"            : admin_handler.CommandInfo(
      1, 0, 0, self.create),
      "delete"            : admin_handler.CommandInfo(
      1, 0, 0, self.delete),
      "getvar"            : admin_handler.CommandInfo(
      2, 0, 0, self.getvar),
      "getfile"           : admin_handler.CommandInfo(
      2, 0, 0, self.getfile),
      "setvar"            : admin_handler.CommandInfo(
      2, 1, 0, self.setvar),
      "setfile"           : admin_handler.CommandInfo(
      2, 0, 1, self.setfile),
      "validatevar"       : admin_handler.CommandInfo(
      2, 0, 0, self.validate_var),
      "exportconfig"      : admin_handler.CommandInfo(
      1, 0, 0, self.exportconfig),
      "importconfig"      : admin_handler.CommandInfo(
      1, 0, 0, self.importconfig),
      "generatestylesheet": admin_handler.CommandInfo(
      3, 0, 0, self.generatestylesheet),
      "getprofile": admin_handler.CommandInfo(
      2, 0, 0, self.getprofile),
      "getstylesheet": admin_handler.CommandInfo(
      2, 0, 0, self.getstylesheet),
      "removelanguage"            : admin_handler.CommandInfo(
      2, 0, 0, self.removelanguage),
      }

  def construct_collection_object(self, frontendName):
    return ent_collection.EntFrontend(frontendName, self.cfg.globalParams)

  #############################################################################

  def list(self):
    frontend_names = ent_collection.ListFrontends(self.cfg.globalParams)
    return "%s\n" % string.join(frontend_names, '\n')

  def exportconfig(self, frontendName):
    # TODO: implement
    return 0

  def importconfig(self, frontendName, importBody):
    # TODO: implement
    return 0

  def removelanguage(self, frontendName, language):
    """
    Removes stylesheet and variables associated with the language.
    """
    frontend = ent_collection.EntFrontend(frontendName, self.cfg.globalParams)
    if not frontend.Exists():
      logging.error("Can't remove language; frontend doesn't exist")
      return 1

    if not frontend.RemoveLanguage(language):
      logging.error("Error removing language")
      return 1

    self.cfg.globalParams.DistributeAll()
    return 0

  def generatestylesheet(self, frontendName, isTest, language):
    """
    This generate the local/test stylesheet for the given frontend
    input: crawlName specifies the name of the frontend for which
          the stylesheet is generated for;
    'isTest' specifies whether we are generating a test stylesheet
    'language' specifies the language to use
    """
    frontend = ent_collection.EntFrontend(frontendName, self.cfg.globalParams)
    if not frontend.Exists():
      logging.error("Can't generate stylesheet; frontend doesn't exist")
      return 1

    if not frontend.GenerateStylesheet(int(isTest), language):
      logging.error("Error generating stylesheet")
      return 1

    self.cfg.globalParams.DistributeAll()
    return 0

  def getprofile(self, frontendName, language):
    """
    This gets the local/test profile for the given frontend
    and language.  If one doesn't exist, the default profile will
    be used to generate an appropriate profile.
    input: crawlName specifies the name of the frontend for which
          the profile is generated.
    'language' specifies the language to use
    """
    frontend = ent_collection.EntFrontend(frontendName, self.cfg.globalParams)
    if not frontend.Exists():
      logging.error("Can't get profile; frontend doesn't exist")
      return '0\n'

    profile = frontend.GetProfile(language)
    if not profile:
      logging.error("Error getting profile")
      return '0\n'
    else:
      return '%s\n%s' % (len(repr(profile)), repr(profile))

  def getstylesheet(self, frontendName, language):
    """
    This gets the local/test stylesheet for the given frontend
    and language.  If one doesn't exist, the default stylesheet will
    be used to generate an appropriate stylesheet.
    input: crawlName specifies the name of the frontend for which
          the stylesheet is generated.
    'language' specifies the language to use
    """
    frontend = ent_collection.EntFrontend(frontendName, self.cfg.globalParams)
    if not frontend.Exists():
      logging.error("Can't get stylesheet; frontend doesn't exist")
      return '0\n'

    stylesheet = frontend.GetStylesheet(language)
    if not stylesheet:
      logging.error("Error getting stylesheet")
      return '0\n'
    else:
      return '%s\n%s' % (len(stylesheet), stylesheet)

  def check_max_license(self):
    current_front = len(self.cfg.getGlobalParam('ENT_FRONTENDS'))
    max_front = self.cfg.lm.getCurrentLicense().getMaxNumFrontends()
    return (max_front == 0) or (current_front < max_front)

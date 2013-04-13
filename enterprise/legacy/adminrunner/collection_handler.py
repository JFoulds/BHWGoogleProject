#!/usr/bin/python2.4
#
# Copyright 2002-2003 Google, Inc.
# davidw@google.com
#
# The AdminRunner handler for dealing with collections
#
# TODO: Import 3.4 collections.
# TODO: Reuse migration code here or reuse the export/import code in
#       migration.
#
###############################################################################

import string
import xml.sax.saxutils
import xml.dom.minidom

from google3.pyglib import logging
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.util import C
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.adminrunner import collectionbase_handler

###############################################################################

class CollectionHandler(collectionbase_handler.CollectionBaseHandler):

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
      "canexport"         : admin_handler.CommandInfo(
      1, 0, 0, self.canexport),
      "listinvalid"     : admin_handler.CommandInfo(
      0, 0, 0, self.listinvalid),
      "export"            : admin_handler.CommandInfo(
      1, 0, 0, self.export),
      "import"            : admin_handler.CommandInfo(
      1, 0, 1, self._import),
      }

  def construct_collection_object(self, name):
    return ent_collection.EntCollection(name, self.cfg.globalParams)

  #############################################################################

  def list(self):
    collection_names = ent_collection.ListCollections(self.cfg.globalParams)
    return "%s\n" % string.join(collection_names, '\n')

  def canexport(self, name):
    errors = self.cfg.globalParams.ValidateVar(('ENT_COLLECTIONS', name))
    if errors != validatorlib.VALID_OK:
      return admin_handler.formatValidationErrors(errors)
    return "VALID\n0"

  def listinvalid(self):
    # make sure *all* errors are returned
    context = validatorlib.ValidatorContext(file_access=1,
                                            dns_access=0,
                                            max_errors=1000000)
    errors = self.cfg.globalParams.ValidateVar('ENT_COLLECTIONS', context)
    # errors might be 0 when there are no errors, check for list
    if type(errors) != list:
      errors = []
    collection_names = []
    for e in errors:
      collection_names.append(e.attribs['KEY'])
    collection_names.sort()
    return "%s\n" % string.join(collection_names, '\n')

  def export(self, name):
    coll_obj = self.construct_collection_object(name)
    if not coll_obj.Exists():
      return 0
    out = '<?xml version="1.0"?>\n'
    out += '<collection>\n'
    out += '  <includePatterns>'
    out += open(coll_obj.get_var(C.GOODURLS), 'r').read()
    out += '</includePatterns>\n'
    out += '  <doNotIncludePatterns>'
    out += open(coll_obj.get_var(C.BADURLS), 'r').read()
    out += '</doNotIncludePatterns>\n'
    out += '  <servingPrerequisiteResults>\n'
    out += '    %s\n' \
           % xml.sax.saxutils.escape(str(coll_obj.get_var(C.TESTWORDS_IN_FIRST)))
    out += '  </servingPrerequisiteResults>\n'
    testWordsFilename = coll_obj.get_var(C.TESTWORDS)
    testWordsFile = open(testWordsFilename, 'r')
    for line in testWordsFile.readlines():
      servingPrerequisite = string.split(line.rstrip(), '\\')
      out += '  <servingPrerequisite>\n'
      out += '    <search>\n'
      out += '      %s\n' % xml.sax.saxutils.escape(servingPrerequisite[0])
      out += '    </search>\n'
      if servingPrerequisite[1]:
        out += '    <url>\n'
        out += '      %s\n' % xml.sax.saxutils.escape(servingPrerequisite[1])
        out += '    </url>\n'
      if servingPrerequisite[3]:
        out += '    <minimumTotalResults>\n'
        out += '      %s\n' % xml.sax.saxutils.escape(servingPrerequisite[3])
        out += '    </minimumTotalResults>\n'
      out += '  </servingPrerequisite>\n'
    categories = coll_obj.get_var(C.CATEGORIES)
    if categories:
      for (name, (metatag, separator)) in categories.items():
        out += '  <category>\n'
        out += '    <name>\n'
        out += '      %s\n' % xml.sax.saxutils.escape(name)
        out += '    </name>\n'
        out += '    <metatag>\n'
        out += '      %s\n' % xml.sax.saxutils.escape(metatag)
        out += '    </metatag>\n'
        out += '    <separator>\n'
        out += '      %s\n' % xml.sax.saxutils.escape(separator)
        out += '    </separator>\n'
        out += '  </category>\n'
    out += '</collection>'
    msg = M.MSG_LOG_EXPORT_COLLECTION % (coll_obj.print_name, name)
    self.writeAdminRunnerOpMsg(msg)
    return '%s\n%s' % (len(out), out)

  def _import(self, name, content):
    coll_obj = self.construct_collection_object(name)
    if coll_obj.Exists():
      return 1

    # validate the collection/frontend/restrict name
    if not entconfig.IsNameValid(name):
      logging.error("Invalid %s name %s -- cannot create" %
                    (coll_obj.print_name, name))
      return 2

    # check license
    if not self.check_max_license():
      return 5

    # check imported content
    try:
      dom = xml.dom.minidom.parseString(content.strip())
    except xml.sax.SAXParseException:
      return 4

    if not coll_obj.Create():
      return 3

    try:
      errors = validatorlib.VALID_OK
      dom.normalize()
      collection = dom.getElementsByTagName('collection')[0]
      includePatterns = collection.getElementsByTagName('includePatterns')[0]
      if includePatterns.firstChild:
        errors = coll_obj.set_file_var_content(
          C.GOODURLS,
          includePatterns.firstChild.data,
          1)
      if errors != validatorlib.VALID_OK:
        coll_obj.Delete()
        return 100 # return 100 on IO error or OS error
                   # from googleconfig.py::set_file_var_content

      doNotIncludePatterns = collection.getElementsByTagName(
        'doNotIncludePatterns')[0]
      if doNotIncludePatterns.firstChild:
        errors = coll_obj.set_file_var_content(
          C.BADURLS,
          doNotIncludePatterns.firstChild.data,
          1)
      if errors != validatorlib.VALID_OK:
        coll_obj.Delete()
        return 100

      errors = coll_obj.set_var(
        C.TESTWORDS_IN_FIRST,
        int(collection.getElementsByTagName('servingPrerequisiteResults')[0]
            .firstChild.data),
        1)
      if errors != validatorlib.VALID_OK:
        coll_obj.Delete()
        return 100

      testWords = ''
      # the testwords should have NewLine Separator for different
      # servingPrerequisite.
      NEW_LINE = '\n'
      firstElementFlag = 0
      for servingPrerequisite in collection.getElementsByTagName(
        'servingPrerequisite'):
        url = self.getElementText(servingPrerequisite, 'url', '')
        minimumTotalResults = self.getElementText(servingPrerequisite,
                                                  'minimumTotalResults', '')
        # Verify that minimumTotalResults represents a number
        # Don't allow number String like "7Words" .
        # It Will be redundant, if we test for Valid XML Input Document
        # with XML Schema. But it is not tested as in version 4.6.4
        try:
          minimumTotalResults = str(int(minimumTotalResults))
        except ValueError:
          logging.info(minimumTotalResults + " is not a valid Number")
          coll_obj.Delete()
          return 100

        if firstElementFlag == 0:
          firstElementFlag = 1
        else:
          testWords += NEW_LINE

        testWords += string.join(
          (servingPrerequisite.getElementsByTagName('search')[0].firstChild.data
           .strip(),
           url,
           '',
           minimumTotalResults),
          '\\')
      errors = coll_obj.set_file_var_content(C.TESTWORDS, testWords, 1)
      if errors != validatorlib.VALID_OK:
        coll_obj.Delete()
        return 100

      categoryMap = {}
      for category in collection.getElementsByTagName('category'):
        separator = str(category.getElementsByTagName('separator')[0].firstChild
                        .data.strip())
        if not separator:
          separator = ' '
        categoryMap[str(category.getElementsByTagName('name')[0].firstChild.data
                        .strip())] = (
          str(category.getElementsByTagName('metatag')[0].firstChild.data
              .strip()),
          separator
          )
      errors = coll_obj.set_var(C.CATEGORIES, categoryMap, 1)
      if errors != validatorlib.VALID_OK:
        coll_obj.Delete()
        return 100

    except (IndexError, ValueError), e:
      coll_obj.Delete()
      return 'ERROR\n4'

    msg = M.MSG_LOG_IMPORT_COLLECTION % (coll_obj.print_name, name)
    self.writeAdminRunnerOpMsg(msg)
    return 0

  def getElementText(self, node, tagName, default):
    """
    Gets the text of the first descendant tagName element of node.
    If there is no descendant, return default.
    """
    elements = node.getElementsByTagName(tagName)
    if elements:
      return elements[0].firstChild.data.strip()
    else:
      return default

  def check_max_license(self):
    current_coll = len(self.cfg.getGlobalParam('ENT_COLLECTIONS'))
    max_coll = self.cfg.lm.getCurrentLicense().getMaxNumCollections()
    return (max_coll == 0) or (current_coll < max_coll)

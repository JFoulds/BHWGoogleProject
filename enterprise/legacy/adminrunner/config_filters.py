#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
#
# Original Author: Zia Syed (zsyed@google.com)
#
# Important Note: changes to this file should be paired with
# change to config_xml_serialization.py, which is used for version migration.

"""
This file contains the filters based on base_packager.ConfigFilter necessary for
export/import of enterprise box configuration.

Design document: //depot/eng/designdocs/enterprise/configuration_import_export.html
"""

import base64
import exceptions
import glob
import os
import re
import shutil
import string
import time
import xml.dom.minidom

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import base_packager
from google3.enterprise.legacy.adminrunner import collection_handler
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import frontend_handler
from google3.enterprise.legacy.adminrunner import params_handler
from google3.enterprise.legacy.adminrunner import query_expansion_handler
from google3.enterprise.legacy.adminrunner import scoring_adjust_handler
from google3.enterprise.legacy.adminrunner import xml_packager
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import ssl_cert

# Change to schema means older versions can't be imported without conversion.
SCHEMA_VERSION = '2.0'

# Error codes. IMPORTANT: Please update ImportExportHandler.java if you update following error codes.
INVALID_PASSWORD_ERROR  = 1
CORRUPT_CONTENT_ERROR   = 2     # content is corrupt but well formed
SCHEMA_MISMATCH_ERROR   = 3
MALFORMED_CONTENT_ERROR = 4     # content is not well formed
# configuration import is sucessful but google apps domain was not imported.
SUCCESS_WITH_APPS_MESSAGE = base_packager.SUCCESS_WITH_APPS_MESSAGE

NEWLINE     = '\n'
COUNT_ATTR  = 'Count'
NAME_ATTR   = 'Name'
VALID_STR   = 'VALID\n0'

IGNORE_FIRST_LINE = r'^[^\n]*\n'
PARAM_PATTERN     = r'^[^=]+=\s*'
LANGUAGE_PATTERN  = re.compile(r'\.(\w{2})$')

# Changing this should go hand in hand with GoogleAppsHandler.java
GOOGLE_APPS_SENTINEL = "hidden=true googleapps=true"
GOOGLE_APPS_URL_SENTINEL = "hidden=true&googleapps=true"

OLD_GOOGLE_APPS_DOMAIN = ''
NEW_GOOGLE_APPS_DOMAIN = ''

SUCCESS = base_packager.SUCCESS

class ConfigExportError(exceptions.Exception):
  """Generic config export error exception.
  """
  pass

class ConfigImportError(exceptions.Exception):
  """Generic config import error exception.
  """
  pass

class BaseFileFilter(base_packager.ConfigFilter):
  """Filter for exporting and importing generic file for frontends and collections.
  """

  def __init__(self, conn, cfg, secmgr, name, base_handler, filename):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = base_handler
    self.filename = filename
    self.name = name

  def encode(self, level):
    """Retrieves file data by calling the associated handler and
    parses it.
    """
    mybody = self.handler.getfile(self.name, self.filename)
    # remove the first line that contains the buffer length
    mybody = re.sub(IGNORE_FIRST_LINE, '', mybody, 1)
    mybody = entconfig.RepairUTF8(mybody)
    return mybody

  def decode(self, body, log, validate_only=0):
    """Decodes file data from the body and set it using the
    associated file handler.
    """
    if not body:
      return SUCCESS

    result = self.handler.setfile(self.name, self.filename, body)
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result: %s." % (self.filename, result)
    else:
      log.info('File %s imported successfully for %s.' % (self.filename, self.name))
    return SUCCESS

class BaseParamFilter(base_packager.ConfigFilter):
  """Filter for exporting and importing params for frontends and collections.
  """

  def __init__(self, conn, cfg, secmgr, name, base_handler, param_name):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = base_handler
    self.param_name = param_name
    self.name = name

  def encode(self, level):
    """Gets the parameter from associated handler and returns it.
    """
    mybody = self.handler.getvar(self.name, self.param_name)
    # strip left side of equal sign which is basically self.param_name
    mybody = re.sub(PARAM_PATTERN, '', mybody, 1)
    return mybody

  def decode(self, body, log, validate_only=0):
    """Gets the paramter definition from body and sets it on the associated
    handler.
    """
    result = self.handler.setvar(self.name, self.param_name, '%s = %s' % (self.param_name, body))
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set parameter %s" % self.param_name
    else:
      log.info('Successfully set parameter %s' % self.param_name)
    return SUCCESS

class CollectionBaseFilter(base_packager.ConfigFilter):
  """Provides base functionality for importing and exporting both collections
  and frontends.
  """

  def __init__(self, conn, cfg, secmgr, handler):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = handler

  def  getFiles(self):
    """To be implemented by derived classes.
    """
    pass

  def initEncode(self):
    """Initializes filters for sub entities.
    """
    files = self.getFiles()
    for tag in files.keys():
      cfilter   = files[tag][0]
      entity    = files[tag][1]
      filename  = files[tag][2]
      rank = xml_packager.DEFAULT_RANK
      if len(files[tag]) > 3:
        rank = files[tag][3]
      self.addSubentity(entity(tag,
                               cfilter(self.conn, self.cfg, self.secmgr, self.getAttribute(NAME_ATTR),
                                       self.handler, filename),
                               sort_rank=rank ))

  def initDecode(self):
    """Same as initEncode but in addition processes attributes that must've
    been set by the associated packaging entity before calling decode.
    """
    self.initEncode()
    basename = self.getAttribute(NAME_ATTR)
    logging.info('Importing item %s.' % basename)
    # create the frontend/collection if doesn't already exist
    list = self.handler.list().split(NEWLINE)

    if basename not in list:

      err = self.handler.create(basename)
      if err:
        raise ConfigImportError, 'Failure while creating item %s: %s' % (basename, self.handler.get_error_message(err))
      else:
        logging.info('Successfully created item %s.' % basename)


def ExtractLanguage(name):
  """Extracts language suffix from names like PROFILESHEET.fr and
  STYLESHEET.fr. Fore default language it returns 'default'.
  """
  lang = 'default'
  # get language
  out = LANGUAGE_PATTERN.search(name)
  if out:   # if there is a language associated
    lang = out.group(1)
  return lang

def AddLanguageExtension(lang, name):
  """Does opposite of ExtractLanguage.
  """
  if lang == 'default':
    ret = name
  else:
    ret = '%s.%s' % (name, lang)
  return ret

def SetStyleSheetFile(lang, fe_name, handler):
  if lang != 'default':
    # Set the stylesheet file variable for the given language. This
    # variable is needed to generate the stylesheet.
    front_end = handler.construct_collection_object(fe_name)
    filename = 'STYLESHEET.%s' % lang
    front_end.set_var(filename,
                      '%s.%s' % (front_end.get_var('STYLESHEET'),
                                 lang))

def GetProfileSheet(lang, name, fe_handler):
  """Given a frontend handler, returns the profilesheet corresponding to
  'lang' language. Returns None if it doesn't exist.
  """
  ps_var_name = AddLanguageExtension(lang, 'PROFILESHEET')
  profile_sheet = fe_handler.getvar(name, ps_var_name)
  if profile_sheet == ("%s = None" % ps_var_name):
    profile_sheet = None
  return profile_sheet

def IsStyleSheetEdited(lang, profile_sheet):
  """Given a profilesheet variable returned from frontend_handler, tells if the
  associated stylesheet is edited or not. This function assumes that the
  profile sheet is not None.
  """
  ps_var_name = AddLanguageExtension(lang, 'PROFILESHEET')
  ps_dict = {}
  profile_sheet = re.sub(ps_var_name, 'PS_DATA', profile_sheet)
  exec profile_sheet in ps_dict
  isEdited = int(ps_dict['PS_DATA']['stylesheet_is_edited'])
  return isEdited


class StylesheetFilter(BaseFileFilter):
  """Filter for exporting and importing stylesheet.
  """

  def decode(self, body, log, validate_only=0):
    """Decodes file data from the body and set it using the
    associated file handler.
    Note: Before StylesheetFilter is called, profilesheet for this frontend
    must already have been imported. This assumption allows us to ignore
    stylesheets from previous exports when the stylesheet wasn't edited but
    it was still exported. In new implementation we generate the stylesheet
    from profilesheet if the stylsheet wasn't edited.
    """
    if not body:
      return SUCCESS
    lang = ExtractLanguage(self.filename)
    SetStyleSheetFile(lang, self.name, self.handler)
    # profilesheet must have been set already for this stylesheet.
    profile_sheet = GetProfileSheet(lang, self.name, self.handler)
    if not profile_sheet:
      err_text = ('ProfileSheet not already set for %s for frontend %s.' %
                  (self.filename, self.name))
      raise ConfigImportError, err_text
    if IsStyleSheetEdited(lang, profile_sheet):
      result = self.handler.setfile(self.name, self.filename, body)
      if not result == VALID_STR:
        raise ConfigImportError, "Can't set file parameter %s. Result: %s." % (self.filename, result)
      else:
        log.info('File %s imported successfully for %s.' % (self.filename, self.name))
    else:
      # Ignore the stylesheet from old export files if the profile sheet says
      # that the stylesheet wasn't edited.
      log.info('Ignoring stylesheet %s for %s.' % (self.filename, self.name))
    return SUCCESS


class ProfileSheetFilter(BaseParamFilter):
  """Filter for exporting and importing profile sheet. Generates the stylesheet
  associated with the profile sheet.
  """

  def decode(self, body, log, validate_only=0):
    """Decodes param data from the body and set it using the
    associated frontend handler.
    """
    # call superclass method to set PROFILESHEET variable first
    ret = BaseParamFilter.decode(self, body, log, validate_only)
    if ret == SUCCESS:
      # generate stylesheet
      log.info('Generating stylsheet.')
      # get language
      lang = ExtractLanguage(self.param_name)
      SetStyleSheetFile(lang, self.name, self.handler)
      # generatestylesheet checks if the stylesheet is edited. If it is edited
      # then it won't generate the stylesheet.
      if self.handler.generatestylesheet(self.name, 0, lang) != 0:
        ret = FAILURE
    return ret


class FrontendFilter(CollectionBaseFilter):
  """For handling a single frontend import/export.
  """

  LANGUAGES = [ 'default', 'en', 'fr', 'de', 'it', 'ja', 'es' ]

  def __init__(self, conn, cfg, secmgr, fe_handler):
    CollectionBaseFilter.__init__(self, conn, cfg, secmgr, fe_handler)
    # this is a mapping from tagname -> [filter,entity,frontend_filename]
    # other files
    #     'STYLESHEET_TEST'
    #     'GWS_CAPABILITIES'
    self.FRONTEND_FILES = {
      'synonyms':     [BaseFileFilter, xml_packager.CDATAPackageEntity, 'SYNONYMS'],
      # This is now added by initEncode function.
      # 'stylesheet': [BaseFileFilter, xml_packager.CDATAPackageEntity, 'STYLESHEET'],
      'googlematch':  [BaseFileFilter, xml_packager.CDATAPackageEntity, 'GOOGLEMATCH'],
      'good_ips':     [BaseFileFilter, xml_packager.CDATAPackageEntity, 'GOOD_IPS'],
      'badurls_noreturn': [BaseFileFilter, xml_packager.CDATAPackageEntity, 'BADURLS_NORETURN'],
      'domain_filter':    [BaseFileFilter, xml_packager.CDATAPackageEntity, 'DOMAIN_FILTER'],
      'filetype_filter':  [BaseFileFilter, xml_packager.CDATAPackageEntity, 'FILETYPE_FILTER'],
      'query_expansion_filter':  [BaseFileFilter, xml_packager.CDATAPackageEntity, 'QUERY_EXPANSION_FILTER'],
      'scoring_policy_filter':  [BaseFileFilter, xml_packager.CDATAPackageEntity, 'SCORING_POLICY_FILTER'],
      'lang_filter':    [BaseFileFilter, xml_packager.CDATAPackageEntity, 'LANGUAGE_FILTER'],
      'metatag_filter': [BaseFileFilter, xml_packager.CDATAPackageEntity, 'METATAG_FILTER'],
      # This is now added by initEncode function.
      # 'profile_sheet': [BaseParamFilter, xml_packager.CDATAPackageEntity, 'PROFILESHEET'],
      }

  def initEncode(self):
    name = self.getAttribute(NAME_ATTR)
    if (self.handler.getvar(name, 'DEFAULT_LANGUAGE') !=
        "DEFAULT_LANGUAGE = None"):
      self.FRONTEND_FILES['default_language'] = [
        BaseParamFilter, xml_packager.CDATAPackageEntity, 'DEFAULT_LANGUAGE',
        xml_packager.DEFAULT_RANK - 2 ]
    for lang in self.LANGUAGES:
      profile_sheet = GetProfileSheet(lang, name, self.handler)
      if profile_sheet:
        # sort rank for profile_sheet is 1 less than default rank so that
        # it will be processed before the stylesheet (and any other element).
        self.FRONTEND_FILES[AddLanguageExtension(lang, 'profile_sheet')] = [
          ProfileSheetFilter, xml_packager.CDATAPackageEntity,
          AddLanguageExtension(lang, 'PROFILESHEET'),
          xml_packager.DEFAULT_RANK - 1 ]
        if IsStyleSheetEdited(lang, profile_sheet):
          ss_var_name = AddLanguageExtension(lang, 'STYLESHEET')
          if (self.handler.getvar(name, ss_var_name) !=
              "%s = None" % ss_var_name):
            self.FRONTEND_FILES[AddLanguageExtension(lang, 'stylesheet')] = [
              StylesheetFilter, xml_packager.CDATAPackageEntity,
              ss_var_name ]

    CollectionBaseFilter.initEncode(self)

  def initDecode(self):
    # default language should be imported first.
    self.FRONTEND_FILES['default_language'] = [
      BaseParamFilter, xml_packager.CDATAPackageEntity, 'DEFAULT_LANGUAGE',
      xml_packager.DEFAULT_RANK - 2 ]
    for lang in self.LANGUAGES:
      # sort rank for profile_sheet is 1 less than default rank so that
      # it will be processed before the stylesheet.
      self.FRONTEND_FILES[AddLanguageExtension(lang, 'profile_sheet')] = [
        ProfileSheetFilter, xml_packager.CDATAPackageEntity,
        AddLanguageExtension(lang, 'PROFILESHEET'),
        xml_packager.DEFAULT_RANK - 1]
      self.FRONTEND_FILES[AddLanguageExtension(lang, 'stylesheet')] = [
        StylesheetFilter, xml_packager.CDATAPackageEntity,
        AddLanguageExtension(lang, 'STYLESHEET') ]

    CollectionBaseFilter.initDecode(self)

  def getFiles(self):
    """override CollectionBaseFilter.getFiles
    """
    return self.FRONTEND_FILES

class FrontendsFilter(base_packager.ConfigFilter):
  """For handling all frontends import/export.
  """

  def __init__(self, conn, cfg, secmgr):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = frontend_handler.FrontendHandler(self.conn, None, None, None, self.cfg)

  def initEncode(self):
    """Initializes entities and filers for subentities.
    """
    fe_list = self.handler.list().split(NEWLINE)
    fe_count=0
    for feName in fe_list:
      if feName:
        entity = xml_packager.XMLPackageEntity('frontend', FrontendFilter(self.conn, self.cfg, self.secmgr, self.handler))
        entity.setAttribute(NAME_ATTR, feName)
        self.addSubentity(entity)
        fe_count = fe_count + 1

    self.setAttribute(COUNT_ATTR, '%s' % fe_count)

  def initDecode(self):
    """Parses attributes set on this filter.
    """
    # get count attribute and initialize subentities accordingly
    fe_count = int(self.getAttribute(COUNT_ATTR))
    for i in range(0,fe_count):
      entity = xml_packager.XMLPackageEntity('frontend', FrontendFilter(self.conn, self.cfg, self.secmgr, self.handler))
      self.addSubentity(entity)

class CollectionFilter(CollectionBaseFilter):
  """For handling a single collection import/export.
  """

  COLLECTION_FILES = {
    'good_urls'    : [BaseFileFilter, xml_packager.CDATAPackageEntity, 'GOODURLS'],
    'bad_urls'     : [BaseFileFilter, xml_packager.CDATAPackageEntity, 'BADURLS'],
    'testwords'    : [BaseFileFilter, xml_packager.CDATAPackageEntity, 'TESTWORDS'],
    'prerequisite_results' : [BaseParamFilter, xml_packager.CDATAPackageEntity, 'TESTWORDS_IN_FIRST'],
  }

  def __init__(self, conn, cfg, secmgr, col_handler):
    CollectionBaseFilter.__init__(self, conn, cfg, secmgr, col_handler)

  def getFiles(self):
    return self.COLLECTION_FILES

class CollectionsFilter(base_packager.ConfigFilter):
  """Handles all collections export/import.
  """

  def __init__(self, conn, cfg, secmgr):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = collection_handler.CollectionHandler(self.conn, None, None, None, self.cfg)

  def initEncode(self):
    """Initializes entities and filers for subentities.
    """
    col_list  = self.handler.list().split(NEWLINE)
    col_count = 0
    for col_name in col_list:
      if col_name:
        entity = xml_packager.XMLPackageEntity('collection', CollectionFilter(self.conn, self.cfg, self.secmgr, self.handler))
        entity.setAttribute(NAME_ATTR, col_name)
        self.addSubentity(entity)
        col_count=col_count+1

    self.setAttribute(COUNT_ATTR, '%s' % col_count)

  def initDecode(self):
    """Gets count attribute and initialize subentities accordingly
    """
    col_count = int(self.getAttribute(COUNT_ATTR))
    for i in range(0,col_count):
      entity = xml_packager.XMLPackageEntity('collection', CollectionFilter(self.conn, self.cfg, self.secmgr, self.handler))
      self.addSubentity(entity)


class QueryExpansionEntryFilter(CollectionBaseFilter):
  """For handling a single query expansion entry import/export.
  """

  def __init__(self, conn, cfg, secmgr, qe_handler):
    # Despite the name, this includes ordinary data as well as files, following
    # the pattern on CollectionFilter.
    # This must be specific to each object, since it gets modified in initEncode
    self.QUERY_EXP_FILES = {
      'entryName' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ENTRY_NAME'],
      'entryType' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ENTRY_TYPE'],
      'entryCount' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ENTRY_COUNT'],
      'creationDate' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'CREATION_DATE'],
      'enabled' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ENABLED'],
      'originalFile' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ORIGINAL_FILE'],
      # Handled in InitEncode
      # 'content':
      # [BaseFileFilter, xml_packager.CDATAPackageEntity, 'CONTENT'],
      'deletable' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'DELETABLE'],
      'downloadable' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'DOWNLOADABLE'],
      'entryLanguage' :
      [BaseParamFilter, xml_packager.CDATAPackageEntity, 'ENTRY_LANGUAGE'],
      }
    CollectionBaseFilter.__init__(self, conn, cfg, secmgr, qe_handler)

  def initEncode(self):
    name = self.getAttribute(NAME_ATTR)

    # Only write the contents for non-permanent entries.        
    if (self.handler.getvar(name, 'DELETABLE') !=
        'DELETABLE = 0'):
      # Double check the above test, by verifying the syntax for the entry.
      if (self.handler.getvar(name, 'DELETABLE') !=
        'DELETABLE = 1'):
        logging.info('Unexpected value for query exp param DELETABLE: %s.' % (
          self.handler.getvar(name, 'DELETABLE')))
      self.QUERY_EXP_FILES['content'] = [
        BaseFileFilter, xml_packager.CDATAPackageEntity, 'CONTENT',
        xml_packager.DEFAULT_RANK + 1 ]

    CollectionBaseFilter.initEncode(self)

  def getFiles(self):
    """override CollectionBaseFilter.getFiles
    """
    return self.QUERY_EXP_FILES

class QueryExpansionFilter(base_packager.ConfigFilter):
  """For handling all query expansion entry import/export.
  """
  LANGUAGES = 'languages'

  def __init__(self, conn, cfg, secmgr):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.handler = query_expansion_handler.QueryExpansionHandler(
        self.conn, None, None, None, self.cfg)
    self.phandler = params_handler.ParamsHandler(
        self.conn, None, None, None, self.cfg)

  def initEncode(self):
    """Initializes entities and filters for subentities.
    """

    # Write list of languages
    langs_entity = xml_packager.CDATAPackageEntity(
        self.LANGUAGES,
        ParamFilter(self.conn, self.cfg, self.secmgr, self.phandler,
                    'QUERY_EXP_LANGS'))
    self.addSubentity(langs_entity)

    # Write the entries
    qe_list = self.handler.list().split(NEWLINE)
    qe_count = 0
    for qeName in qe_list:
      if qeName:
        entity = xml_packager.XMLPackageEntity(
          'queryExpEntry',
          QueryExpansionEntryFilter(
            self.conn, self.cfg, self.secmgr, self.handler))
        entity.setAttribute(NAME_ATTR, qeName)
        self.addSubentity(entity)
        qe_count = qe_count + 1

    self.setAttribute(COUNT_ATTR, '%s' % qe_count)

  def initDecode(self):
    """Parses attributes set on this filter.
    """

    # Get list of languages
    langs_entity = xml_packager.CDATAPackageEntity(
        self.LANGUAGES,
        ParamFilter(self.conn, self.cfg, self.secmgr, self.phandler,
                    'QUERY_EXP_LANGS'))
    self.addSubentity(langs_entity)

    # get count attribute and initialize subentities accordingly
    qe_count = int(self.getAttribute(COUNT_ATTR))
    for i in range(0,qe_count):
      entity = xml_packager.XMLPackageEntity(
        'queryExpEntry',
        QueryExpansionEntryFilter(
          self.conn, self.cfg, self.secmgr, self.handler))
      self.addSubentity(entity)

class ParamFilter(base_packager.ConfigFilter):
  """Handles export/import of a single parameter through param_handler.
  """

  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.param_name = param_name
    self.phandler = phandler

  def encode(self, level):
    """Gets the parameter from associated handler and returns it.
    """
    mybody = self.phandler.get(self.param_name)
    # strip left side of equal sign which is basically self.param_name
    mybody = re.sub(PARAM_PATTERN, '', mybody, 1)
    return mybody

  def decode(self, body, log, validate_only=0):
    """Gets the paramter definition from body and sets it on the associated
    handler.
    """
    try:
      result = self.phandler.set(self.param_name, '%s = %s' % (self.param_name, body))
    except Exception, e:
      # Lower code can raise random exceptions, so catch and log internally
      logging.error('%s: %s' % (self.param_name, e))
      result = -1
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set parameter %s" % self.param_name
    else:
      log.info('Successfully set parameter %s' % self.param_name)
    return SUCCESS

class GoogleAppsDomainFilter(ParamFilter):
  """Handles import/export of GOOGLE_APPS_DOMAIN.
    When the domain is old domain and the new domain are not different, the old
    domain is removed.
  """
  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    ParamFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def decode(self, body, log, validate_only=0):
    """ If the new domain to be imported is the same as the old domain, then
    nothing is done. But if it is not, then the old domain is wiped out.
    We want to have the user name and password also when he adds the new
    domain.
    """
    global OLD_GOOGLE_APPS_DOMAIN
    global NEW_GOOGLE_APPS_DOMAIN
    OLD_GOOGLE_APPS_DOMAIN = self.cfg.getGlobalParam(self.param_name)
    NEW_GOOGLE_APPS_DOMAIN =  string.strip(body).strip("'")
    if OLD_GOOGLE_APPS_DOMAIN != NEW_GOOGLE_APPS_DOMAIN:
      ParamFilter.decode(self, "''", log, validate_only)
      return SUCCESS_WITH_APPS_MESSAGE
    return SUCCESS


class DefaultSearchUrlFilter(ParamFilter):
  """Handles export/import of DEFAULT_SEARCH_URL.
  Fix for 131316. This is a hack to handle DEFAULT_SEARCH_URL separately so
  that any NULL values are converted to empty string before importing.
  """

  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    ParamFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def decode(self, body, log, validate_only=0):
    """Gets the paramter definition from body and sets it on the associated
    handler.
    """
    if body == 'None':
      body = "''"
      log.info('Changed %s from None to empty string' % self.param_name)

    return ParamFilter.decode(self, body, log, validate_only)


class ParamFileFilter(ParamFilter):
  """Handles export/import of a single file through param_handler.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    ParamFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def encode(self, level):
    """Gets the file from associated handler and returns it
    after parsing.
    """
    mybody = self.phandler.getfile(self.param_name)
    # remove the first line that contains the buffer length
    mybody = re.sub(IGNORE_FIRST_LINE, '', mybody, 1)
    return mybody

  def decode(self, body, log, validate_only = 0):
    """Gets the file from body and sets it on the associated handler.
    """
    result = self.phandler.setfile(self.param_name, body)
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result %s." % (self.param_name, result)
    else:
      log.info('Successfully set file parameter %s' % self.param_name)
    return SUCCESS


class SsoServingFilter(ParamFileFilter):
  """Handles export/import of the sso_serving_config.enterprise file."""

  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def decode(self, body, log, validate_only = 0):
    """The file format of sso_serving_config changed in 5.2. The old file format
    had 6 fields (sample_url, method, only_user_impersonation, cookie_name,
    duration, always_redirect). The new format has 4 fields (sample_url,
    redirect_url, method, always_redirect).

    Convert the old format to the new format.
    """

    # the body will have contents in either the old or new format
    # only write it out in the new format
    if body:
      line = body.splitlines()[0]  # Only need the first line
      parts = line.split(' ')
      if len(parts) == 6:
        log.info('Converting old format sso_serving_config to new format')
        # When parsing the old 6-field format, we only keep sample url, method
        # and always redirect (fields 0, 1, and 5).
        sample_url = parts[0]
        method = parts[1]
        always_redirect = parts[5]
        redirect_url = ''
        if always_redirect == '1':
          sample_url, redirect_url = '', sample_url
        body = ' '.join([sample_url, redirect_url, method, always_redirect])
        body += "\n"  # restore the trailing \n that splitlines removed
      elif len(parts) != 4:
        # The only valid formats are with 4 fields or 6 fields
        raise (ConfigImportError,
               "Invalid sso_serving element body '%s', field count = %d"
               % (body, len(parts)))

    # body may be empty, but that's ok
    return ParamFileFilter.decode(self, body, log, validate_only)


class GoogleAppsFileFilter(ParamFileFilter):
  """Handles the import/export of the files which have Google Apps related
  information in them.
  """
  apps_string = ''
  def __init__(self, conn, cfg,  secmgr, phandler, param_name, apps_string):
    self.apps_string = apps_string
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def encode(self, level):
    """ Google Apps related content in the file is not exported.
    """
    body = ParamFileFilter.encode(self, level)
    body = body.split('\n')
    apps_body = [line for line in body if not re.search(self.apps_string,
                                                        line)]
    apps_body = '\n'.join(apps_body)
    return apps_body

  def get_old_apps_body(self):
    """Helper function to get the content from the old file which contains apps
    related content.
    """
    apps_body = ''
    if OLD_GOOGLE_APPS_DOMAIN == NEW_GOOGLE_APPS_DOMAIN:
      old_body = ParamFileFilter.encode(self, 0)
      old_body = old_body.split('\n')
      apps_body = [line for line in old_body if re.search(self.apps_string,
                                                        line)]
      apps_body = '\n'.join(apps_body)
    return apps_body

  def decode(self, body, log, validate_only = 0):
    apps_body = self.get_old_apps_body()
    # old apps related content is retained.
    if body != '' and apps_body != '':
      body += '\n' + apps_body
    else:
      body += apps_body
    return ParamFileFilter.decode(self, body, log, validate_only)


class BadURLsFilter(GoogleAppsFileFilter):
  """Handles import/export of badurls file.
  """
  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    GoogleAppsFileFilter.__init__(self, conn, cfg, secmgr, phandler,
                                  param_name, GOOGLE_APPS_SENTINEL)


class CookieRulesFileFilter(GoogleAppsFileFilter):
  """Handles import/export ofcookie rules file.
  """
  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    GoogleAppsFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name,
                             GOOGLE_APPS_SENTINEL)


class GoodURLsFilter(GoogleAppsFileFilter):
  """Handles export/import of goodurls file.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    GoogleAppsFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name,
                             GOOGLE_APPS_SENTINEL)


  def decode(self, body, log, validate_only = 0):
    """Gets the file from body and sets it on the associated handler.
    """
    apps_body = GoogleAppsFileFilter.get_old_apps_body(self)
    if body != '' and apps_body != '':
      body += '\n' + apps_body
    else:
      body += apps_body
    body = entconfig.MigrateGoodURLs(body);
    return ParamFileFilter.decode(self, body, log, validate_only)

class StartURLsFilter(GoogleAppsFileFilter):
  """Handles export/import of a single file through param_handler.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    GoogleAppsFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name,
                             GOOGLE_APPS_URL_SENTINEL)

  def decode(self, body, log, validate_only = 0):
    """Gets the file from body and sets it on the associated handler.
    """
    pr0name = 'PAGERANKER_BATCHURLS_FILE_0'
    pr1name = 'PAGERANKER_BATCHURLS_FILE_1'

    apps_body = GoogleAppsFileFilter.get_old_apps_body(self)
    if not body == '' and not apps_body == '':
      body = body + '\n' + apps_body
    else:
      body = body + apps_body

    result = self.phandler.setfile(self.param_name, body)
    result0 = self.phandler.setfile(pr0name, body)
    result1 = self.phandler.setfile(pr1name, body)
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result %s." % (self.param_name, result)
    elif not result0 == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result %s." % (
        pr0name, result)
    elif not result1 == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result %s." % (
        pr1name, result)
    else:
      log.info('Successfully set file parameter %s' % self.param_name)
    return SUCCESS

class ScoringTemplateFileFilter(ParamFileFilter):
  """Overrides decode to keep the existing template file if it exists.

  The GSA should always be using the latest version of the template
  file, and should never override it with an imported template.  If no
  template file exists, then do write the file -- this should never
  happen, but mimics the defensive stance of config_xml_serialization.
  """
  def decode(self, body, log, validate_only = 0):
    """Gets the file from body and sets it on the associated handler.
    """
    mybody = None
    try:
      mybody = self.phandler.getfile(self.param_name)
    except IOError:
      logging.info('Did not find scoring template file: importing')

    if mybody is None:
      result = self.phandler.setfile(self.param_name, body)
      if not result == VALID_STR:
        raise ConfigImportError, ("Can't set file parameter %s. Result %s." %
                                  (self.param_name, result))
      else:
        log.info('Successfully set file parameter %s' % self.param_name)
    return SUCCESS


class PasswordFileFilter(ParamFileFilter):
  """Handles export/import of passwords file.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def canExport(self, account_entry):
    """Decides if an account_entry in the account file should be exported.
    We don't export admin accounts or any account with superuser privliges.
    """
    fields = account_entry.split(' ')
    try:
      return (not fields[0] == 'admin') and (not fields[4] == 'superuser')
    except IndexError:
      logging.info('Not admin or superuser')
      return True

  def encode(self, level):
    """Same as ParamFileFilter.encode but also removes accounts that shouldn't
    be exported.
    """
    tempbody = ParamFileFilter.encode(self, level);
    accounts = tempbody.split(NEWLINE);

    mybody = ''
    for account in accounts:
      if not account or self.canExport(account):
        mybody = '%s\n%s' % (account, mybody)

    return mybody

  def decode(self, body, log, validate_only=0):
    """Decodes data from body and verifies if all the accounts are valid
    before importing them.
    """
    accounts = body.split(NEWLINE);
    mybody = ''
    for account in accounts:
      if account and not self.canExport(account):
        # this shouldn't happen becuase we are using signatures but just for a safety check
        raise base_packager.MalformedContentError, 'Invalid user accounts found in the file.'

    newbody = self.mergeAccounts(accounts)
    result = self.phandler.setfile(self.param_name, newbody)
    if not result == VALID_STR:
      raise ConfigImportError, "Can't set file parameter %s. Result %s." % (self.param_name, result)
    else:
      log.info('Successfully set file parameter %s' % self.param_name)
    return SUCCESS

  def createMap(self, account_list):
    """Creates a map of account from a list of accounts. This map maps
    user name to the account entry.
    """
    result = {}
    for account in account_list:
      if account:
        fields = account.split(' ')
        result[fields[0]] = account

    return result

  def mergeAccounts(self, account_list):
    """Merges account with the current account list. If a login name
    already exists is not updated.
    """
    # remove the first line that contains the buffer length
    finalAccounts = re.sub(IGNORE_FIRST_LINE, '', self.phandler.getfile(self.param_name), 1)
    currAccountMap = self.createMap(finalAccounts.split(NEWLINE))
    newAccountMap  = self.createMap(account_list)

    # add new accounts only if they don't exist
    for loginName in newAccountMap.keys():
      if not currAccountMap.has_key(loginName):
        finalAccounts = '%s\n%s' % (newAccountMap[loginName], finalAccounts)

    return finalAccounts

class DatabaseConfigFilter(ParamFileFilter):
  """Handles export/import of databases.enterprise config file.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def decode(self, body, log, validate_only = 0):
    """Gets the file from body and sets it on the associated handler.
    """
    body = entconfig.MigrateDatabaseConfig(body);
    return ParamFileFilter.decode(self, body, log, validate_only)

class FileFilter(base_packager.ConfigFilter):
  """To import/export a file in config directory as it is.
  """
  def __init__(self, conn, cfg, secmgr, dirname):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.dirname = dirname

  def encode(self, level):
    """Gets the parameter from associated handler and returns it.
    """
    full_name = '%s/%s' % (self.dirname, self.getAttribute(NAME_ATTR))
    return open(full_name, 'r').read()
  
  def decode(self, body, log, validate_only=0):
    """Gets the paramter definition from body and sets it on the associated
    handler.
    """
    file_name = self.getFileName()
    full_name = '%s/%s' % (self.dirname, file_name)
    open(full_name, 'w').write(body.encode('utf-8'))
    log.info('Succesfully set file %s' % file_name)
    return SUCCESS

  def getFileName(self):
    """ This is overridden if needed.
    """
    return self.getAttribute(NAME_ATTR)

class CACertFileFilter(FileFilter):
  """ In 4.4 the CA cert was of the form <hash> and in 4.6 its of the form
  <hash>.0 So before decoding we need to distinguish if the cert is imported
  from 4.4 or 4.6
  """
  def getFileName(self):
    filename = self.getAttribute(NAME_ATTR)
    if os.path.splitext(filename)[1] == '':
      return '%s%s' % (filename, ssl_cert.CA_CERT_EXT)
    return filename

class CRLFileFilter(FileFilter):
  """ In 4.4 the CRL was of the form <hash> and in 4.6 its of the form
  <hash>.r0 So before decoding we need to distinguish if the CRL is imported
  from 4.4 or 4.6
  """
  def getFileName(self):
    filename = self.getAttribute(NAME_ATTR)
    if os.path.splitext(filename)[1] == '':
      return '%s%s' % (filename, ssl_cert.CRL_EXT)
    return filename

# TODO(hareesh): We should consider moving out migrating user data
# from here. This is because, when the admin decides to export system
# settings, the EFE would still be serving, users can add/delete to
# their user data, which could result in inconsistent data being
# written out.
# 
# But we provide this as a starting point. If the admin does want to
# migrate user data, he can do so (He could via some network
# settings/stylesheet changes make sure users can't access the EFE or
# could make sure the Signin link is disabled)
#
# TODO(hareesh): The data that is exported into the XML is not
# encrypted, it is only tarred + base64 encoded.
class UamFilter(ParamFileFilter):
  """Handles export/import of personalization data.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

    self.param_name = param_name
    self.phandler = phandler
    self.binary = True

    # For e.g.: param_name = "UAM_DIR" and phandler.get(param_name)
    # returns "UAM_DIR = '/foo/bar/baz'"
    mo = re.compile(r'[^=]+\s=\s\'([^\']+)\'').match(phandler.get(param_name))
    assert mo
    
    # Figure out the dirname.
    self.dirname = mo.group(1)
    logging.info('uam: dirname: %s' % (self.dirname))

  def encode(self, level):
    # If the uam directory does not exist, create it and bail.
    if not os.path.exists(self.dirname):
      logging.error('uam: Directory %s doesnt exist. Wierd.' % (self.dirname))
      os.mkdir(self.dirname)
      return None

    # Create a tar ball with the contents of the uam directory and
    # base64 encode it. The tar ball will be deleted once the exported
    # config has been streamed to the user. Read comments in
    # config_handler.py:exportconfig()
    out_file = '/tmp/ie-%s.tar.bz2.base64' % (time.time())
    pipeline = 'tar -jcf - -C %s . | base64 > %s' % (self.dirname, out_file)
    if os.system(pipeline):
      logging.info('Could not execute: %s' % pipeline)
      return None
    logging.info('uam: encoded UamDir: %s into %s' % (self.dirname, out_file))
    return out_file

  def decode(self, body, log, validate_only=0):
    # If the uam directory does not exist, create it.
    if not os.path.exists(self.dirname):
      logging.error('uam: Directory %s doesnt exist. Wierd.' % (self.dirname))
      os.mkdir(self.dirname)

    # This file is base64(bzipped2(tar(...)))! If file is zero bytes
    # long or does not exist, there is nothing to do!
    out_file = body
    try:
      if os.stat(out_file).st_size == 0:
        logging.info('uam: %s is 0 bytes. Nothing to decode.' % out_file)
        return SUCCESS
    except OSError, e:
      logging.info('uam: %s does not exist. Nothing to decode.' % out_file)
      return SUCCESS
    
    # base64 decode and untar the tar ball into a temporary directory.
    temp_dir = '%s.%s' % (self.dirname, time.time())
    os.mkdir(temp_dir)
    pipeline = 'base64 -di %s | tar -jxf - -C %s' % (out_file, temp_dir)
    os.system(pipeline)
    logging.info('uam: Decoded UamDir: %s' % self.dirname)

    # Does the uam directory exist?
    if os.path.exists(self.dirname):
      backup_dir = self.dirname + ".old"
      # If a backup personalization directory already exists, then
      # remove it.
      if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
      # Make the current personalization directory the backup
      # directory.
      os.rename(self.dirname, backup_dir)
    else:
      logging.error('uam: Directory %s doesnt exist. Wierd.' % (self.dirname))

    # Rename the temporary directory to make it the uam directory!
    os.rename(temp_dir, self.dirname)

    return SUCCESS  

class DirectoryFilter(base_packager.ConfigFilter):
  """A generic filter for parameters that point to directory.
  The directory is supposed to contain list of files. Contents of
  each file is to be exported/imported. The name of the files needs
  to be preserved across import/export.
  """

  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.param_name = param_name
    self.phandler = phandler
    mo = re.compile(r'[^=]+\s=\s\'([^\']+)\'').match(phandler.get(param_name))
    assert mo
    self.dirname = mo.group(1)

  def initEncode(self):
    """Gets list of file from the directory and creates import/export
    filter for each file.
    """
    if os.path.exists(self.dirname) and os.path.isdir(self.dirname):
      file_list  = self.getFileList()
    else:
      file_list = []
    file_count = 0
    for file_name in file_list:
      file_filter = FileFilter(self.conn, self.cfg, self.secmgr, self.dirname)
      entity = xml_packager.CDATAPackageEntity('file', file_filter)
      entity.setAttribute(NAME_ATTR, file_name)
      self.addSubentity(entity)
      file_count = file_count + 1

    self.setAttribute(COUNT_ATTR, '%s' % file_count)

  def initDecode(self):
    """Gets count attribute and initialize subentities accordingly
    """
    try:
      os.makedirs(self.dirname)
    except OSError:
      # Directory already exists?
      pass
    file_count = int(self.getAttribute(COUNT_ATTR))
    for i in range(0, file_count):
      file_filter = self.getFileFilter()
      entity = xml_packager.CDATAPackageEntity('file', file_filter)
      self.addSubentity(entity)

  def getFileFilter(self):
    """ This is overridden if needed.
    """
    return FileFilter(self.conn, self.cfg, self.secmgr, self.dirname)

  def getFileList(self):
    return os.listdir(self.dirname)


class CACertsDirectoryFilter(DirectoryFilter):
  """ CA certs and CRLs are in the same directory. The way they are distinguished
  is by their extension.
   """
  def getFileList(self):
    list = glob.glob(self.dirname + '/' + '*' + ssl_cert.CA_CERT_EXT)
    list = map(lambda x: os.path.split(x)[1], list)
    return list

  def getFileFilter(self):
    return CACertFileFilter(self.conn, self.cfg, self.secmgr, self.dirname)

class CRLDirectoryFilter(DirectoryFilter):
  """ CA certs and CRLs are in the same directory. The way they are distinguished
  is by their extension.
  """
  def getFileList(self):
    list = glob.glob(self.dirname + '/' + '*' + ssl_cert.CRL_EXT)
    list = map(lambda x: os.path.split(x)[1], list)
    return list

  def getFileFilter(self):
    return CRLFileFilter(self.conn, self.cfg, self.secmgr, self.dirname)

class ConnectorsFilter(ParamFileFilter):
  """Like ParamFileFilter, but restarts connectormgr after decode.
  The connector manager manages its configuration files itself
  (instead of using AdminRunner to manage its configuration files).
  When AdminRunner imports connector configuration, it writes a global copy of
  the imported connector configuration and restarts the connector manager.
  When the connector manager restarts, it reads the global copy of the imported
  connector configuration.
  """

  def __init__(self, conn, cfg,  secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)

  def decode(self, body, log, validate_only = 0):
    """call ParamFileFilter.decode and restart connectormgr
    """
    ret = ParamFileFilter.decode(self, body, log, validate_only)
    if ret != SUCCESS:
      return ret
    self.cfg.globalParams.WriteConfigManagerServerTypeRestartRequest(
      "connectormgr")
    return ret


class BinaryFileFilter(ParamFileFilter):
  """Handles export/import of a single base64 raw binary file via param_handler.
  """

  def __init__(self, conn, cfg, secmgr, phandler, param_name):
    ParamFileFilter.__init__(self, conn, cfg, secmgr, phandler, param_name)
    self.param_name = param_name
    self.phandler = phandler
    self.binary = True

  def encode(self, level):
    """Same as `ParamFileFilter.encode()' but base64 encodes raw binary files.
    """
    binary_body = ParamFileFilter.encode(self, level)
    return base64.encodestring(binary_body)

  def decode(self, body, log, validate_only=0):
    """Same as `ParamFileFilter.decode()' but base64 decodes raw binary files.
    """
    binary_body = base64.decodestring(body)
    return ParamFileFilter.decode(self, binary_body, log, validate_only)

class GlobalParamsFilter(base_packager.ConfigFilter):
  """Config filter for handling all the global parameters/files that we want to export.
  """

  # this is a mapping from tagname -> [filter,entity,collection_filename]
  GLOBAL_PARAMS = {
    'start_urls': [StartURLsFilter, xml_packager.CDATAPackageEntity, 'STARTURLS'],
    'good_urls':  [GoodURLsFilter, xml_packager.CDATAPackageEntity, 'GOODURLS'],
    'bad_urls':   [BadURLsFilter, xml_packager.CDATAPackageEntity, 'BADURLS'],
    'dup_hosts':  [ParamFileFilter, xml_packager.CDATAPackageEntity, 'DUPHOSTS'],
    'smtp_server':    [ParamFilter, xml_packager.CDATAPackageEntity, 'SMTP_SERVER'],
    'problem_email':  [ParamFilter, xml_packager.CDATAPackageEntity, 'PROBLEM_EMAIL'],
    'notification_email': [ParamFilter, xml_packager.CDATAPackageEntity, 'NOTIFICATION_EMAIL'],
    'outgoing_sender':    [ParamFilter, xml_packager.CDATAPackageEntity, 'OUTGOING_EMAIL_SENDER'],
    'hots_loads':     [ParamFileFilter, xml_packager.CDATAPackageEntity, 'HOSTLOADS'],
    'user_accounts':  [PasswordFileFilter, xml_packager.SecureCDATAPackageEntity, 'PASSWORD_FILE'],
    'dns_servers': [ParamFilter, xml_packager.CDATAPackageEntity, 'BOT_DNS_SERVERS'],
    'ntp_servers': [ParamFilter, xml_packager.CDATAPackageEntity, 'NTP_SERVERS'],
    'dns_search_path':  [ParamFilter, xml_packager.CDATAPackageEntity, 'DNS_SEARCH_PATH'],
    'syslog_server':    [ParamFilter, xml_packager.CDATAPackageEntity, 'SYSLOG_SERVER'],
    # [Kerberos/IWA] - Admin UI config file for user+password+realm/domain+etc
    'crawler_kerberos_config': [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'CRAWL_KERBEROS_CONFIG'],  # [Kerberos/IWA]
    'crawler_acces':    [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'CRAWL_USERPASSWD_CONFIG'],
    #'database_loads':   [ParamFileFilter, xml_packager.CDATAPackageEntity, 'DATABASELOADS'],
    'date_patterns':    [ParamFileFilter, xml_packager.CDATAPackageEntity, 'DATEPATTERNS'],
    'http_headers': [ParamFilter, xml_packager.CDATAPackageEntity, 'BOT_ADDITIONAL_REQUEST_HDRS'],
    'user_agent': [ParamFilter, xml_packager.CDATAPackageEntity, 'USER_AGENT_TO_SEND'],
    'default_search_url': [DefaultSearchUrlFilter, xml_packager.CDATAPackageEntity, 'DEFAULT_SEARCH_URL'],
    'external_ssh': [ParamFilter, xml_packager.CDATAPackageEntity, 'ENT_ENABLE_EXTERNAL_SSH'],
    'enable_snmp': [ParamFilter, xml_packager.CDATAPackageEntity, 'ENT_ENABLE_SNMP'],
    'snmp_users': [ParamFilter, xml_packager.SecureCDATAPackageEntity, 'SNMP_USERS'],
    'snmp_communities': [ParamFilter, xml_packager.SecureCDATAPackageEntity, 'SNMP_COMMUNITIES'],
    'snmp_traps_host': [ParamFilter, xml_packager.CDATAPackageEntity, 'SNMP_TRAPS_HOST'],
    'snmp_traps_community': [ParamFilter, xml_packager.CDATAPackageEntity, 'SNMP_TRAPS_COMMUNITY'],
    'snmp_traps': [ParamFilter, xml_packager.CDATAPackageEntity, 'SNMP_TRAPS'],
    'daily_status': [ParamFilter, xml_packager.CDATAPackageEntity, 'SEND_ENTERPRISE_STATUS_REPORT'],
    'cache_timeout': [ParamFilter, xml_packager.CDATAPackageEntity, 'HEADREQUESTOR_CACHE_ENTRY_TIMEOUT'],
    'max_crawl_urls': [ParamFilter, xml_packager.CDATAPackageEntity, 'USER_MAX_CRAWLED_URLS'],
    # TODO: re-put back when admin option available
    # 'feed_urls':    [ParamFileFilter, xml_packager.CDATAPackageEntity, 'FEED_URLS'],

    'proxy_config': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'PROXY_CONFIG'],
    'cookie_rules': [CookieRulesFileFilter, xml_packager.SecureCDATAPackageEntity, 'COOKIE_RULES'],
    'sso_patterns': [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'SSO_PATTERN_CONFIG'],
    'sso_serving': [SsoServingFilter, xml_packager.CDATAPackageEntity, 'SSO_SERVING_CONFIG'],
    'frequent_urls': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'URLMANAGER_REFRESH_URLS'],
    'infrequent_urls': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'URLSCHEDULER_ARCHIVE_URLS'],
    'force_recrawl_urls': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'URLS_REMOTE_FETCH_ONLY'],
    'authenticate_client_cert' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHENTICATE_CLIENT_CERT'],
    'authenticate_server_cert' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHENTICATE_SERVER_CERT'],
    'authenticate_onebox_server_cert' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHENTICATE_ONEBOX_SERVER_CERT'],
    'feeder_trusted_clients' : [ParamFilter, xml_packager.CDATAPackageEntity, 'FEEDER_TRUSTED_CLIENTS'],
    'database_config' : [DatabaseConfigFilter, xml_packager.SecureCDATAPackageEntity, 'DATABASES'],
    'onebox_config' : [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'ONEBOX_MODULES'],
    'batch_crawl_mode' : [ParamFilter, xml_packager.CDATAPackageEntity,
                         'ENTERPRISE_SCHEDULED_CRAWL_MODE'],
    'batch_crawl_schedule' : [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'CRAWL_SCHEDULE'],
    'batch_crawl_schedule_bitmap' : [ParamFileFilter, xml_packager.SecureCDATAPackageEntity, 'CRAWL_SCHEDULE_BITMAP'],
    'authn_login_Url' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHN_LOGIN_URL'],
    'authn_artifact_service_url' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHN_ARTIFACT_SERVICE_URL'],
    'authz_service_url' : [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTHZ_SERVICE_URL'],
    'certificates' : [CACertsDirectoryFilter, xml_packager.XMLPackageEntity, 'TRUSTED_CA_DIRNAME'],
    'crl' : [CRLDirectoryFilter, xml_packager.XMLPackageEntity, 'CRL_DIRNAME'],
    'db_stylesheets' : [DirectoryFilter, xml_packager.XMLPackageEntity, 'DATABASE_STYLESHEET_DIR'],
    'query_exp_status': [ParamFilter, xml_packager.CDATAPackageEntity, 'QUERY_EXP_STATUS'],
    'ldap_config': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'LDAP_CONFIG'],
    # [Kerberos/IWA] - UI scratchpad file for Kerberos config data (e.g., KDC)
    # [Kerberos/IWA] - UI scratchpad file for Kerberos imported keytab file
    'kerberos_config': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'KERBEROS_CONFIG'],         # [Kerberos/IWA]
    'kerberos_keytab': [BinaryFileFilter, xml_packager.SecureCDATAPackageEntity, 'KERBEROS_KEYTAB'],  # [Kerberos/IWA]
    # [Kerberos/IWA] - Active/live/valid/etc krb5.conf file for Kerberos/IWA
    # [Kerberos/IWA] - Active/live/valid/etc krb5.keytab file for Kerberos/IWA
    'kerberos_krb5_conf': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'KERBEROS_KRB5_CONF'],             # [Kerberos/IWA]
    'kerberos_krb5_keytab': [BinaryFileFilter, xml_packager.SecureCDATAPackageEntity, 'KERBEROS_KRB5_KEYTAB'],  # [Kerberos/IWA]
    # [Kerberos/IWA] - end.
    'scoring_adjust': [ParamFilter, xml_packager.CDATAPackageEntity, 'ENT_SCORING_ADJUST'],
    'scoring_template': [ScoringTemplateFileFilter, xml_packager.CDATAPackageEntity, 'ENT_SCORING_TEMPLATE'],
    'scoring_config': [ParamFileFilter, xml_packager.CDATAPackageEntity, 'ENT_SCORING_CONFIG'],
    'connectors' : [ConnectorsFilter, xml_packager.CDATAPackageEntity, 'CONNECTORS'],
    'connector_managers' : [ParamFileFilter, xml_packager.CDATAPackageEntity, 'CONNECTOR_MGRS'],
    'google_apps_integration' : [ParamFilter, xml_packager.CDATAPackageEntity, 'GOOGLE_APPS_INTEGRATION'],
    # Underscore at the beginning is intended to maintain the alphabetic order.
    # GOOGLE_APPS_DOMAIN should be imported/exported before goodurls, badurls
    # and cookierules. Content of goodurls/badurls/cookierules for
    # import/export is based on GOOGLE_APPS_DOMAIN.
    '_google_apps_domain' : [GoogleAppsDomainFilter, xml_packager.CDATAPackageEntity, 'GOOGLE_APPS_DOMAIN'],
    'autocomplete_off': [ParamFilter, xml_packager.CDATAPackageEntity, 'AUTOCOMPLETE_OFF'],
    'uam_dir': [UamFilter, xml_packager.CDATAPackageEntity, 'UAM_DIR'],
  }

  def __init__(self, conn, cfg, secmgr):
    """Initializes all the subentities also.
    """
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.phandler =  params_handler.ParamsHandler(self.conn, None, None, None, self.cfg)

    for param_tag in self.GLOBAL_PARAMS.keys():
      param_filter   = self.GLOBAL_PARAMS[param_tag][0]
      param_entity   = self.GLOBAL_PARAMS[param_tag][1]
      param_name     = self.GLOBAL_PARAMS[param_tag][2]
      self.addSubentity(param_entity(param_tag,
                                     param_filter(self.conn, self.cfg, self.secmgr, self.phandler,
                                                  param_name)))

  def decode(self, body, log, validate_only=0):
    """Same as ConfigFilter.decode but invokes save on the
    paramsHandler to save all the parameters.
    """
    # Call base classes decode to decode all parameters value
    ret = base_packager.ConfigFilter.decode(self, body, log, validate_only)
    if not ret == SUCCESS:
      return ret
    # we need to invoke save on params_handler
    if self.phandler.save():
      raise ConfigImportError, 'Failed during saving parameters.'
    else:
      log.info('Parameters saved successfully.')

    # We may have added or modified the state of QueryExp files. Apply changes.
    self.cfg.setGlobalParam(C.QUERY_EXP_STATUS,
      int(C.QUERY_EXP_STATUS_NEEDS_APPLY))
    self.cfg.CompileQueryExpData()

    # Compile scoring adjust file from new parameter settings + template.
    # This overrides the imported scoring adjust file, since the import
    # may have been generated using an earlier template version.
    logging.info("Regenerating scoring settings from template")
    scoring_adjust_handler.ApplyAndSaveSettings(self.cfg)

    return SUCCESS

class ConfigHandlerFilter(base_packager.ConfigFilter):
  """Handles the complete configuration export/import.
  """

  ENT_VER_ATTR    = 'EnterpriseVersion'
  SCHEMA_VER_ATTR = 'Schema'

  def __init__(self, conn, cfg, secmgr):
    """Initializes all the subentities also.
    """
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.frontends   = xml_packager.XMLPackageEntity('frontends', FrontendsFilter(self.conn, self.cfg, self.secmgr))
    self.collections = xml_packager.XMLPackageEntity('collections', CollectionsFilter(self.conn, self.cfg, self.secmgr))
    self.queryexp    = xml_packager.XMLPackageEntity('queryexpansion', QueryExpansionFilter(self.conn, self.cfg, self.secmgr))
    self.params      = xml_packager.XMLPackageEntity('globalparams', GlobalParamsFilter(self.conn, self.cfg, self.secmgr))
    self.addSubentity(self.frontends)
    self.addSubentity(self.collections)
    self.addSubentity(self.queryexp)
    self.addSubentity(self.params)

  def getEnterpriseVersion(self):
    """Returns enterprise version.
    """
    temphandler = params_handler.ParamsHandler(self.conn, None, None, None, self.cfg)
    return re.sub(PARAM_PATTERN, '', temphandler.get('VERSION'), 1)

  def initEncode(self):
    """Initialize entity attributes. Subentites are added in the constructor
    as they are need both for encoding and decoding.
    """
    self.setAttribute(self.ENT_VER_ATTR, self.getEnterpriseVersion())
    self.setAttribute(self.SCHEMA_VER_ATTR, SCHEMA_VERSION)

  def verifyAttributes(self, log):
    """Verifies all the attributes before the body can be imported.
    """
    # 1. verify schema version
    if not SCHEMA_VERSION == self.getAttribute(self.SCHEMA_VER_ATTR):
      log.error('Invalid schema version. Required %s.' % SCHEMA_VERSION)
      return SCHEMA_MISMATCH_ERROR

    log.info('Schema version verified.')

    #  TODO(zsyed): verify enterprise version??
    return SUCCESS

  def decode(self, body, log, validate_only=0):
    """Decodes/Imports all the subentities in right order.
    """
    ret = self.verifyAttributes(log)
    if not ret == SUCCESS:
      log.error('Attribute verification failed.')
      return ret

    ## order is important here

    # decode collections
    ret = self.collections.decode(body, log, validate_only)
    if not ret == SUCCESS:
      return ret
    # decode frontends
    ret = self.frontends.decode(body, log, validate_only)
    if not ret == SUCCESS:
      return ret
    # decode query expansion entries
    ret = self.queryexp.decode(body, log, validate_only)
    if not ret == SUCCESS:
      return ret
    # decode global params
    ret = self.params.decode(body, log, validate_only)
    return ret

class SignatureHandlerFilter(base_packager.ConfigFilter):
  """Handles verification of content generated by ConfigHandlerFilter.
  """

  def __init__(self, conn, cfg, secmgr):
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.message = ''
    self.signature = ''

  def setMessage(self, message):
    self.message = message

  def getSignature(self):
    return self.signature

  def encode(self, level):
    """Returns signature on the message associated.
    """
    # message body should already have been set
    self.signature = self.getSecMgr().computeSignature(self.message)
    return self.signature

  def decode(self, body, log, validate_only=0):
    """Decodes and verifies the signature with the message.
    """
    # body is the actual/original signature.
    actualSignature = body.rstrip()
    
    # compute the new signature on the current body
    self.signature = self.getSecMgr().computeSignature(self.message)
    if self.signature != actualSignature:
      # Don't tell user what the signature should be, so just log internally
      logging.error('Signature: %s != %s' % (self.signature, actualSignature))
      log.error('Invalid file signature')
      return CORRUPT_CONTENT_ERROR
    else:
      log.info('Signature verified.')

    return SUCCESS

class XMLConfigPackager(base_packager.ConfigFilter):
  """Packages all config as XML.
  """

  CONFIG_TAG = 'config'
  SIGN_TAG   = 'signature'

  def __init__(self, conn, cfg, secmgr):
    """Initializes subentities also.
    """
    base_packager.ConfigFilter.__init__(self, conn, cfg, secmgr)
    self.cfgentity = xml_packager.XMLPackageEntity(self.CONFIG_TAG,
                                                   ConfigHandlerFilter(self.conn,
                                                                       self.cfg,
                                                                       self.secmgr)
                                                   , required=1)  # section is required
    self.signentity = xml_packager.CDATAPackageEntity(self.SIGN_TAG,
                                                      SignatureHandlerFilter(self.conn,
                                                                             self.cfg,
                                                                             self.secmgr)
                                                      , required=1) # section is required
    self.addSubentity(self.cfgentity)
    self.addSubentity(self.signentity)

  def normalize(self, xml_text):
    """Because we will be verifying signature reading through minidom we should
    calculate the signature on the body as seen by the minidom.
    """
    try:
      xmlnode = xml.dom.minidom.parseString(xml_text).getElementsByTagName(self.CONFIG_TAG)[0]
    except:
      # if we have formed the xml_text correctly then the try section above should never fail
      raise ConfigImportError, 'Your configuration cannot be exported.  Please check your configuration for invalid data.  Contact your support organization for assistance.'

    xmlnode.normalize()
    return xmlnode.toxml(xml_packager.ENCODING)

  def encode(self, level):
    """Exports all the configuration as XML object. Also calculates signature
    on the body.
    """
    # encode cfg first
    cfgbody = self.cfgentity.encode(level)
    # TODO(zsyed): should normalize move to XMLEntity?
    to_be_signed_body = self.normalize(cfgbody)
    # set body to generate signature
    self.signentity.getFilter().setMessage(to_be_signed_body)
    signbody = self.signentity.encode(level)
    return '%s%s' % (cfgbody, signbody)

  def decode(self, body, log, validate_only=0):
    """Decodes the configuration from the body after verifying the signature.
    """
    # before decoding whole config, recalculate the signature
    cfgNode = body.getElementsByTagName(self.CONFIG_TAG)[0]
    if not cfgNode:
      logging.info('Error in decoding node %s' % cfgNode)
      return MALFORMED_CONTENT_ERROR

    cfgNode.normalize()
    cfgbody = cfgNode.toxml(xml_packager.ENCODING)
    self.signentity.getFilter().setMessage(cfgbody)
    ret = self.signentity.decode(body, log, validate_only)
    if not ret == SUCCESS:
      return ret

    return self.cfgentity.decode(body, log, validate_only)

#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# David Watson <davidw@google.com>
#
# this module contains collection related classes and code
# We also use it for Query Expansion data files; these are not strictly
# related to collections, but have very similar requirements.
#
#############################################################################

import UserDict
import os
import re
import string
import xml.sax.saxutils

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.licensing import ent_license
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import readxlb
from google3.pyglib import logging

false = 0
true = 1

#############################################################################

# ListCollections takes a Config object and returns a list of collections
def ListCollections(config):
  return ListAny(config, 'ENT_COLLECTIONS')

# ListFrontends takes a Config object and returns a list of frontends
def ListFrontends(config):
  return ListAny(config, 'ENT_FRONTENDS')

# ListQueryExpEntries takes a Config object and returns a list of query
# expansion entries (customer data files).
def ListQueryExpEntries(config):
  return ListAny(config, 'ENT_QUERY_EXP')

# auxiliary method for listing collections/frontends/queryexps
def ListAny(config, what):
  keys = config.var(what).keys()
  keys.sort()
  return keys

def IsQueryExpNameOK(name, config):
  """
  This checks if the name of a query expansion entry is valid or not -
  1. check if the name is OK, 2. checks if there is another entry with the
  same name
  """

  return entconfig.IsNameValid(name) \
         and name not in ListQueryExpEntries(config)

# generate stylesheetes for all frontends
def GenerateStylesheets(config, isTest):
  frontend_names = ListAny(config, 'ENT_FRONTENDS')
  for frontend_name in frontend_names:
    frontend = EntFrontend(frontend_name, config)
    if frontend.Exists():
      frontend.GenerateStylesheet(isTest)

  config.DistributeAll()

def GenerateCollectionsDropdown (collection_names, param_name='site'):
  menu = '\n<select name="'+param_name+'">'
  for name in collection_names:
    menu += '\n <xsl:choose>'
    menu += '\n  <xsl:when test=\"PARAM[(@name=\'' + param_name \
         + '\') and (@value=\'' + name + '\')]">'
    menu += '\n   <option value="' + name + '" selected="selected">' \
         + name + '</option>'
    menu += '\n  </xsl:when>'
    menu += '\n  <xsl:otherwise>'
    menu += '\n   <option value="' + name + '">' + name + '</option>'
    menu += '\n  </xsl:otherwise>'
    menu += '\n </xsl:choose>'
  menu += '\n</select>\n'
  return menu

def GetSupportedLanguages():
  """
  Returns a dictionary mapping the message used to denote a given
  language and the language code.
  """
  langs={}
  langs["MSG_ar"]='lang_ar'
  langs["MSG_zh_CN"]='lang_zh-CN'
  langs["MSG_zh_TW"]='lang_zh-TW'
  langs["MSG_cs"]='lang_cs'
  langs["MSG_da"]='lang_da'
  langs["MSG_nl"]='lang_nl'
  langs["MSG_en"]='lang_en'
  langs["MSG_et"]='lang_et'
  langs["MSG_fi"]='lang_fi'
  langs["MSG_fr"]='lang_fr'
  langs["MSG_de"]='lang_de'
  langs["MSG_el"]='lang_el'
  langs["MSG_iw"]='lang_iw'
  langs["MSG_hu"]='lang_hu'
  langs["MSG_is"]='lang_is'
  langs["MSG_it"]='lang_it'
  langs["MSG_ja"]='lang_ja'
  langs["MSG_ko"]='lang_ko'
  langs["MSG_lv"]='lang_lv'
  langs["MSG_lt"]='lang_lt'
  langs["MSG_no"]='lang_no'
  langs["MSG_pl"]='lang_pl'
  langs["MSG_pt"]='lang_pt'
  langs["MSG_ro"]='lang_ro'
  langs["MSG_ru"]='lang_ru'
  langs["MSG_es"]='lang_es'
  langs["MSG_sv"]='lang_sv'
  return langs

#############################################################################
# EntCollectionBase pulls together operations needed for both Collection and
# Frontend interfaces.  It is an abstract class, so its subclass needs to
# define a few methods.  It is templatized on a few variable names which need
# to be passed to the constructor by subclass's constructors.  The class
# encapsulates a name and a Config object.
#
# instance arguments:
#  name: name of collection
#  config: Config object collection is stored in
# templatized arguments:
#  base_map_var: var name (in config) of a map, which holds "collections"
#  default_value_var: var name (in config), which is used as the default value
#                     when creating a new "collection"
#  default_file_var: var name (in config) of a map from "collection" file vars,
#                    to the filename of a default file used to initialize them.
#                    None means to create an empty file.
#  name_var: "collection" var name which gets set the same as name
#  print_name: what we call "collection" when we print logs
####
# Example:
#
# default_value_var = {
#    'FOO' : 1,
#    'BAR' : '/foo/bar/baz1',
#    'BAZ' : '/foo/bar/baz2',
# }
# default_file_var = {
#    'BAR' : '/foo/bar/default_baz1',
#    'BAZ' : None,
#}
# base_map_var : {
#   name : {
#     name_var : 'NAME',
#     'FOO'    : 2,
#     'BAR'    : '/foo/bar/baz1',
#     'BAZ'    : '/foo/bar/baz2',
#   }
#   ...
# }
class EntCollectionBase:
  def __init__(self, base_map_var, print_name, name_var,
               default_value_var, default_files_var,
               name, config):
    self.base_map_var = base_map_var
    self.print_name = print_name
    self.name_var = name_var
    self.default_value_var = default_value_var
    self.default_files_var = default_files_var

    self.name = name
    self.config = config

  # checks if the collection exists
  def Exists(self):
    return self.config.has_var((self.base_map_var, self.name))

  # provides variable access inside the collection
  # throws: KeyError
  def get_var(self, var):
    return self.config.var_copy((self.base_map_var, self.name, var))

  # check if a variable exists in current configuration object
  def has_var(self, var):
    return self.config.has_var((self.base_map_var, self.name, var))

  # provides variable setting access inside the collection
  # returns: validatorlib.ValidationError
  # throws: KeyError
  def set_var(self, var, value, validate = 0):
    return self.config.set_var((self.base_map_var, self.name, var),
                               value, validate = validate)

  # provides file variable content setting inside the collection
  # returns: validatorlib.ValidationError
  # throws: KeyError
  def set_file_var_content(self, var, value, validate):
    var_path = (self.base_map_var, self.name, var)
    result =  self.config.set_file_var_content(var_path,
                                               value, validate)
    if result != validatorlib.VALID_OK:
      return result
    self.config.DistributeAll()
    return result


  def validate_var(self, var):
    return self.config.ValidateVar((self.base_map_var, self.name, var))

  # Creates the collection; updates config, creates dirs, and inits files.
  # returns: boolean indicating success
  def Create(self, patchExisting=true, params=None):
    # If patchExisting is true, it indicates this is a version manager patch
    # upgrade so only newly added config files will be created in patched
    # version.
    # If params is not None, then after setting up the object with the
    # defaults, we override values from params (must be a dictionary). This
    # happens before patching values.

    # start with the defaults
    collection = self.config.var_copy(self.default_value_var)

    # override with any values from params, but only if the key from params
    # exists in the collection.
    if params:
      for var in params.keys():
        if collection.has_key(var):
          collection[var] = params[var]

    # give it the correct name
    collection[self.name_var] = self.name
    if patchExisting:
      # update with values in current object.
      for var in collection.keys():
        if self.has_var(var):
          collection[var] = self.get_var(var)

    # set the collection (so that derived vars get set)
    self.config.set_var((self.base_map_var, self.name),
                        collection,
                        validate = 0)

    if not self.CreateDirs() and not patchExisting:
      logging.error("error creating %s dirs: %s" % (self.print_name,
                                                    self.name))
      return false

    if not self.InitDefaultFiles(patchExisting):
      logging.error("error creating %s files; %s" % (self.print_name,
                                                     self.name))
      return false

    if not self.config.Save():
      logging.error("error saving config file")
      return false

    self.config.DistributeAll()

    return true

  # Deletes a collections (files, dirs, and Config settings)
  # returns: boolean indicating success
  def Delete(self):
    success = 1

    # delete the collection from
    success = self.config.del_var((self.base_map_var, self.name)) and success
    success = self.DeleteFiles() and success

    success = self.config.Save() and success

    return success

  #
  # Initialize all the file parameters with the default values
  # If patchExisting is true, we only put newly added files and
  # leave existing files untouched.
  #
  def InitDefaultFiles(self, patchExisting=true):
    """ This will init some configuration files with defaults (ex: BADURL) """

    if self.default_files_var == None:
      return true

    defaults = self.config.var(self.default_files_var)

    if defaults == None:
      return true

    try:
      for param, default_file in defaults.items():
        var_path = (self.base_map_var, self.name, param)
        file_name = self.config.var(var_path)
        if not file_name:
          logging.error("Unexpected error: invalid file_name for %s" % param)
          return false

        if patchExisting and os.path.exists(file_name):
          continue
        else:
          if default_file == None:
            value = ""
          else:
            value = open(default_file, 'r').read()

          self.config.set_file_var_content(var_path, value, 0)

    except IOError, e:
      logging.error("Cannot set the default configuration files [%s]" % e)
      return false

    return true

  def CreateDirs(self):
    machines = self.config.var('MACHINES')

    fileList = self.GetDirList()

    # Create the directories on all machines
    if len(fileList) == 0:
      status = 1
    else:
      if self.config.batch_mode_:
        for f in fileList:
          self.config.AddBatchDir(f)
        status = E.mkdir([E.LOCALHOST], string.join(fileList, " "))
      else:
        status = E.mkdir(machines, string.join(fileList, " "))

    return status

  # Returns a list of all directories that need to be created/deleted
  # This method is abstract; should be overridden by subclasses
  def GetDirList(self):
    assert false

  def DeleteFiles(self):
    # nothing to do?
    if not self.default_files_var:
      return 1

    machines = self.config.var('MACHINES')

    defaults = self.config.var(self.default_files_var)

    # build a list of files from the defaults
    fileParamList = []
    for param in defaults.keys():
      var_path = (self.base_map_var, self.name, param)
      if self.config.has_var(var_path) and self.config.var(var_path) != None:
        fileParamList.append(var_path)

    # get a list of config dirs
    dirList = self.GetDirList()

    success = 1

    # remove the files on all machines
    for fileParam in fileParamList:
      success = self.config.del_file_var_content(fileParam) and success

    # remove the directories on all machines
    if len(dirList) > 0:
      success = E.rmall(machines, string.join(dirList, " ")) and success

    return success


#############################################################################
# EntCollection subclasses EntCollectionBase and provides an interface for
# managing collections
class EntCollection(EntCollectionBase):
  def __init__(self, name, config):
    EntCollectionBase.__init__(self,
                               base_map_var = 'ENT_COLLECTIONS',
                               print_name = 'collection',
                               name_var = 'COLLECTION_NAME',
                               default_value_var = 'COLLECTION_DEFAULT_VALUE',
                               default_files_var = 'COLLECTION_DEFAULT_FILES',
                               name = name,
                               config = config)

  def GetDirList(self):
    return \
      [E.joinpaths([self.config.var('CONFIGDIR'), 'collections', self.name])]

#############################################################################
# EntFrontend subclasses EntCollectionBase and provides an interface for
# managing frontends; it provides XSLT generation methods
class EntFrontend(EntCollectionBase):
  def __init__(self, name, config):
    EntCollectionBase.__init__(self,
                               base_map_var = 'ENT_FRONTENDS',
                               print_name = 'frontend',
                               name_var = 'FRONTEND_NAME',
                               default_value_var = 'FRONTEND_DEFAULT_VALUE',
                               default_files_var = 'FRONTEND_DEFAULT_FILES',
                               name = name,
                               config = config)
    # The profile has some strings that need to be localized.  This
    # dictionary maps from the variable name %(xxx) to the message
    # catalog entry MSG_xxx.
    self.PROFILE_LOCALIZATIONS = {
               'adv_search_anchor_text': 'MSG_advanced_search',
               'search_help_anchor_text': 'MSG_help',
               'alerts__anchor_text': 'MSG_alerts',
               'search_button_text': 'MSG_search',
               'spelling_text': 'MSG_spell_suggest',
               'synonyms_text': 'MSG_synonyms_text',
               'front_page_title': 'MSG_search_home',
               'result_page_text': 'MSG_search_results',
               'adv_page_title': 'MSG_advanced_search',
               'error_page_title': 'MSG_error',
               'cached_page_header_text': 'MSG_cached_copy',
               'xml_error_msg_txt': 'MSG_unknown_xml',
               'xml_error_des_txt': 'MSG_view_xml',
    }

  def GetDirList(self):
    return \
      [E.joinpaths([self.config.var('GOOGLEDATA'),
                    'gws/clients', self.name]),
       E.joinpaths([self.config.var('GOOGLEDATA'),
                    'gws/p4clientinfo', self.name]),
       E.joinpaths([self.config.var('CONFIGDIR'),
                    'frontends', self.name])]

  # If patchExisting is true, we only put newly added files and
  # leave existing files untouched.
  def InitDefaultFiles(self, patchExisting=true):
    if not EntCollectionBase.InitDefaultFiles(self, patchExisting):
      return false

    try:
      # Generate the stylesheet
      if ( not self.GenerateStylesheet(false) or
           not self.GenerateStylesheet(true) ):
        return false
    except IOError, e:
      logging.error("Cannot set the default configuration files [%s]" % e)
      return false

    return true

  def GetProfile(self, language):
    """
    This gets the local profile for the given frontend
    and language.  If one doesn't exist, the default profile will
    be used to generate an appropriate profile.
    Input: 'language' specifies the language to use
    Returns: a dictionary for the profile, or None
    """
    profile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                             'PROFILESHEET.%s' % language])
    if profile == None:
      # Generate a new profile from the default
      profile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                                 'PROFILESHEET'])
      if profile == None:
        # This shouldn't happen, but let's not die
        logging.error('GetProfile: no default profile')
        return None
      default_language = self.config.var(['ENT_FRONTENDS', self.name,
                                      'DEFAULT_LANGUAGE'])
      if not default_language:
        default_language = 'en'
      profile = self.RetranslateProfile(profile, default_language, language)
    return profile

  def RetranslateProfile(self, profile, from_language, to_language):
    """
    Convert any strings in profile that are in from_language to
    strings in to_language.
    Input:
      profile: a dictionary of strings
      from_language: language that profile is currently in
      to_language: language that is desired
    Output: retranslated profile dictionary
    """
    from_catalog = self.GetLanguageCatalog(from_language)
    # reverse the keys and values, so from_catalog_reversed maps from
    # a translated string to the corresponding "MSG_..." tag
    from_catalog_reversed = dict([(value, key) for
                                  key, value in from_catalog.items()])
    to_catalog = self.GetLanguageCatalog(to_language)
    for (var_name, translated_string) in profile.items():
      msg = from_catalog_reversed.get(translated_string, None)
      if translated_string != "" and msg:
        profile[var_name] = to_catalog[msg]
    return profile

  def RetranslateStylesheet(self, stylesheet, from_language, to_language):
    """
    Convert any strings in stylesheet that are in from_language to
    strings in to_language.
    Input:
      stylesheet: a (big) string
      from_language: language that stylesheet is currently in
      to_language: language that is desired
    Output: retranslated stylesheet
    """
    # Generate the conversion strings from the TEMPLATE
    templateParam = self.config.var_copy('STYLESHEET_TEMPLATE')
    template = open(templateParam, 'r').read()

    start = 0
    from_catalog = self.GetLanguageCatalog(from_language)
    to_catalog = self.GetLanguageCatalog(to_language)

    patterns = {} # Dictionary, indexed by from_pattern to to_pattern
    while 1:
      # Pattern is:
      # Optional two characters of context, excluding braces
      # {{
      # The contents of the {{ }} (? match is non-greedy so patterns don't
      # get included inside patterns)
      # }}
      # Optional two characters of context, excluding braces
      m = re.search('([^{]?[^{]?){{(.*?)}}([^{]?[^{]?)', template[start:])
      if not m:
        break
      (left, pattern, right) = m.groups()
      from_pattern = '%s%s%s' % (left,
                self.TranslateTemplatePattern(pattern, from_catalog),
                right)
      to_pattern = '%s%s%s' % (left,
                self.TranslateTemplatePattern(pattern, to_catalog),
                right)
      patterns[from_pattern] = to_pattern
      start = start + m.end() - 2

    # Add patterns based on the profile
    for msg in self.PROFILE_LOCALIZATIONS.values():
      from_pattern = '>%s<' % self.LookupMsg(msg, from_catalog)
      to_pattern = '>%s<' % self.LookupMsg(msg, to_catalog)
      logging.error("DEBUG: profile pattern %s -> %s" % (from_pattern, to_pattern))
      patterns[from_pattern] = to_pattern

    # Sort patterns from longest to shortest.
    # The idea is that if one pattern is a subset of another, we should
    # try to apply the longest first, or else we will just translate
    # the subset.
    pattern_list = []
    # Generate list of [-pattern length, from_pattern, to_pattern]
    for from_pattern in patterns.keys():
      to_pattern = patterns[from_pattern]
      pattern_list.append([-len(from_pattern), from_pattern, to_pattern])
    pattern_list.sort() # Sort by -len

    # Apply the patterns
    for (_, from_pattern, to_pattern) in pattern_list:
        stylesheet = stylesheet.replace(from_pattern, to_pattern)

    return stylesheet

  def RemoveLanguage(self, language):
    """
    Removes the stylesheet, profile, and variables associated with a
    language.
    """
    stylesheetName = 'STYLESHEET.%s' % language
    profilesheetName = 'PROFILESHEET.%s' % language
    stylesheetFile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                             'STYLESHEET.%s' % language])
    if stylesheetFile:
      try:
        os.unlink(stylesheetFile)
      except OSError, e:
        logging.error('unlink of %s: %s' % (stylesheetFile, e))
        pass # File probably already removed, so okay
    self.set_var(stylesheetName, None)
    self.set_var(profilesheetName, None)

  def GetStylesheet(self, language):
    """
    This gets the local/test stylesheet for the given frontend
    and language.  If one doesn't exist, the default stylesheet will
    be used to generate an appropriate stylesheet.
    input: 'language' specifies the language to use
    """
    # Read the stylesheet for the specified language
    stylesheetFile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                             'STYLESHEET.%s' % language])
    if stylesheetFile:
      try:
        lines = open(stylesheetFile, "r").read()
        return lines
      except IOError:
        pass
    # The stylesheet doesn't exist, so read the default one
    stylesheetFile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                               'STYLESHEET'])
    if stylesheetFile:
      try:
        lines = open(stylesheetFile, "r").read()
        default_language = self.config.var(['ENT_FRONTENDS', self.name,
                                        "DEFAULT_LANGUAGE"])
        if not default_language:
          default_language = 'en'
        lines = self.RetranslateStylesheet(lines, default_language, language)
        return lines
      except IOError:
        pass
    # This shouldn't happen
    logging.error('Error fetching stylesheet - file %s missing' %
                  stylesheetFile)
    return ''

  def GenerateLanguageList(self, catalog):
    """
    In the advanced search page the user can request that search
    results be returned in any language of their choosing via a drop
    down selection. Depending on their locale, this list of languages
    should appear in sorted order. This code was written in response to
    bug 969312.
    
    input: catalog
    output: the XSLT code for drop down selection.
    """

    langs = GetSupportedLanguages()

    # In dictionary msg_to_langcode, we map the translated language to
    # the language code. For example, the message MSG_el gets
    # translated to "Greek" in the language English and to "Grego" in
    # Portugese Brazilian (PT_br). So if the catalog was built for
    # English, we'd store "Greek" -> lang_el and if the catalog was
    # built for PT_br, we'd store "Grego" -> lang_el.
    msg_to_langcode={}
    for key in langs.keys():
      msg_to_langcode[self.LookupMsg(key, catalog)] = langs[key]

    # Get the translated langs in sorted order.
    translated_langs = msg_to_langcode.keys()
    translated_langs.sort()

    # Generate the drop down XSLT code. The XSLT code is generated in
    # the sorted order of the translated language.
    sp = '\n\t\t\t'
    xslt = []
    for trans_lang in translated_langs:
      lang_code = msg_to_langcode[trans_lang]
      xslt.append("%s<xsl:choose>" % sp)
      xslt.append(" <xsl:when test=\"PARAM[(@name='lr') and (@value='%s')]\">"
                % lang_code)
      xslt.append(" <option value=\"%s\"" % lang_code)
      xslt.append(" selected=\"selected\">%s</option>" % trans_lang)
      xslt.append(" </xsl:when>")
      xslt.append(" <xsl:otherwise>")
      xslt.append(" <option value=\"%s\">%s</option>" % (lang_code, trans_lang))
      xslt.append(" </xsl:otherwise>")
      xslt.append("</xsl:choose>\n")
      
    return sp.join(xslt)
      
  def GenerateStylesheet(self, isTest, language = 'default'):
    """
    This generate the local/test stylesheet for the given collection
    input: crawlName specifies the name of the collection for which
    the stylesheet is generated for;
    'isTest' specifies whether we are generating a test stylesheet
    'language' controls the language in which to translate, and the suffix
      on the STYLESHEET.xx or PROFILESHEET.xx variable (and thus the suffix
      on the generated file.
      If language is 'default', then unsuffixed STYLESHEET or PROFILESHEET
      is used, and the DEFAULT_LANGUAGE is used.
    """
    templateParam = 'STYLESHEET_TEMPLATE'

    if isTest:
      stylesheetParam = 'STYLESHEET_TEST'
      profileParam = 'PROFILESHEET_TEST'
    elif language == 'default':
      stylesheetParam = 'STYLESHEET'
      profileParam = 'PROFILESHEET'
      try:
        language = self.config.var(['ENT_FRONTENDS', self.name,
                                   "DEFAULT_LANGUAGE"])
      except KeyError, e:
        # This will happen if a new frontend is being created, since
        # DEFAULT_LANGUAGE is not yet initialized
        language = 'en'
    else:
      stylesheetParam = 'STYLESHEET.%s' % language
      profileParam = 'PROFILESHEET.%s' % language

    try:
      profile = self.config.var_copy(['ENT_FRONTENDS', self.name,
                                 profileParam])
      templateFile = self.config.var(templateParam)
      stylesheetFile = self.config.var(['ENT_FRONTENDS', self.name,
                                        stylesheetParam])

      license = ent_license.EnterpriseLicense(self.config.var('ENT_LICENSE_INFORMATION'))
    except (KeyError, TypeError), e:
      logging.error('Error generating stylesheet: %s' % e)
      return false

    # Bug 78357: if the frontend profile is edited using XSLT stylesheet editor,
    # no new stylesheet should be generated.
    if profile.get('stylesheet_is_edited', '') == '1':
      return true

    if not license.getEnableSekuLite():
      profile['show_secure_radio_button'] = '0'

    # generate collections dropdown
    profile['search_collections_xslt'] = \
      GenerateCollectionsDropdown (ListCollections(self.config))
    if profile.get('show_subcollections', '') == '1':
      profile['show_collections_dropdown'] = '1';
    else:
      profile['show_collections_dropdown'] = '';

    # Bug 226430: page layout helper did not obey search information decorator
    # preference; upon fixing, 'blue bar' should mean light blue.
    if profile['choose_sep_bar'] == 'blue':
      profile['choose_sep_bar'] = 'ltblue';

    # header and footer are put between <xsl:text> and </xsl:text>
    # so must be xml escaped
    profile['my_page_header'] = xml.sax.saxutils.escape(profile['my_page_header'])
    profile['my_page_footer'] = xml.sax.saxutils.escape(profile['my_page_footer'])
    profile['global_font'] = xml.sax.saxutils.escape(profile['global_font'])
    profile['search_button_text'] = xml.sax.saxutils.escape(profile['search_button_text'])
    lines = open(templateFile, 'r').read()
    localizedlines = self.LocalizeTemplate(lines, language)
    try:
      frontends = self.config.var_copy(self.default_value_var)
      default_profile = frontends['PROFILESHEET']
      localizedlines = localizedlines % ExtendedDict(profile, default_profile)
    except (ValueError, TypeError), e:
      logging.error('Template generation failed %s' % e)
      logging.error(localizedlines)
      logging.error(profile)
      return false
    open(stylesheetFile, 'w').write(localizedlines)

    self.config.add_file_to_distribute(stylesheetFile, 'CONFIG_REPLICAS')

    return true

  def GetLanguageCatalog(self, language):
    '''Returns a dictionary from 'MSG_...' to translated string'''
    enthome = E.getEnterpriseHome()
    languagelocal = language.replace('-', '_')
    languagefile = ('%s/local/google3/enterprise/i18n/FrontendMessages_%s.xlb' %
                    (enthome, languagelocal))
    try:
      msgs = readxlb.Read(languagefile)
    except IOError:
      logging.error('Missing language file %s' % languagefile)
      if language != 'en':
        # Try en language so we can at least replace the tags.
        return self.GetLanguageCatalog('en')
      # Sorry, no language files
      msgs = {}
    # Handle right-to-left languages
    if language in ['ar', 'fa', 'iw', 'ku', 'sd', 'ur', 'yi']:
      msgs['DIR'] = 'rtl'
    else:
      msgs['DIR'] = 'ltr'
    # Encode Unicode messages in UTF-8.  (Adminrunner expects UTF-8 messages.)
    for key in msgs:
      msgs[key] = msgs[key].encode('utf-8')
    # Stick in the language list inside the advanced search page in
    # sorted order.
    msgs["INSERT_LANGUAGE_LIST_IN_ADV_SEARCH"] = self.GenerateLanguageList(msgs)
    return msgs

  def LookupMsg(self, msg, catalog):
    """Look up a message 'MSG_...' in the catalog (dictionary).

    Args:
      msg: "MSG_name" as a string
      catalog: the catalog to access.

    Returns:
      Aa string of UTF-8 bytes, not Unicode
    """
    return catalog.get(msg, 'Could not find %s' % msg)

  def TranslateTemplatePattern(self, pattern, catalog):
    ''' Translates a pattern, which is a string of
    the form MSG_foo|a==b|c==d.
    In the file, the pattern is of the form {{MSG_foo|a==b|c==d}} but the
    braces are removed by this point.
    This should be replaced with the translated string corresponding
    to MSG_foo, with a replaced by b and c replaced by d.
    The translation of MSG_foo comes from the dictionary "catalog"
    NOTAGS indicates MSG_foo is in an attribute tag and must not contain tags
    '''
    parts = pattern.split('|')
    attribute = 0
    msg = self.LookupMsg(parts[0], catalog)
    for part in parts[1:]:
      if part == 'NOTAGS':
        attribute = 1
        continue
      sub_parts  = part.split('==')
      if len(sub_parts) == 2:
        (lhs, rhs) = sub_parts
        msg = msg.replace(lhs, rhs)
    # Hack because some translations use non-XML-compliant <br> tag
    msg = msg.replace('<br>', '<br/>')
    if attribute:
      # Remove tags
      msg = re.sub('<[^>]*>', '', msg)
    else:
      # Hack because of how nbsp is handled by stylesheet
      # This replacement must be done only outside attributes
      msg = msg.replace('&nbsp;', '<xsl:call-template name="nbsp" />')

    return msg

  def LocalizeTemplate(self, data, language):
    '''Localize the template to the given language'''

    def _TranslatePart(mo):
      '''Translate the match mo, using TranslateTemplatePattern'''
      return self.TranslateTemplatePattern(mo.group(1), catalog)

    catalog = self.GetLanguageCatalog(language)
    # PAT matches anything between double braces {{...}}.
    # We do a non-greedy match "?" in case two such groups
    # are on the same line, so they don't get merged together.
    PAT = '{{(.*?)}}'
    data = re.sub(PAT, _TranslatePart, data)
    return data

#############################################################################
# EntQueryExp subclasses EntCollectionBase and provides an interface for
# managing query expansion entries.
class EntQueryExp(EntCollectionBase):
  def __init__(self, name, config):
    EntCollectionBase.__init__(self,
                               base_map_var = 'ENT_QUERY_EXP',
                               print_name = 'query_exp',
                               name_var = 'ENTRY_NAME',
                               default_value_var = 'QUERY_EXP_DEFAULT_VALUE',
                               default_files_var = 'QUERY_EXP_DEFAULT_FILES',
                               name = name,
                               config = config)

  def GetDirList(self):
    return [E.joinpaths([self.config.var('CONFIGDIR'),
                         'queryexpansion', self.name])]

#############################################################################
# EntUserParam subclasses EntCollectionBase and provides an interface for
# accessing persistent user data, like default collection and frontend.
class EntUserParam(EntCollectionBase):
  def __init__(self, name, config):
    EntCollectionBase.__init__(self,
                               base_map_var = 'ENT_USERPARAMS',
                               print_name = 'user params',
                               name_var = 'USERNAME',
                               default_value_var = 'USERPARAM_DEFAULT_VALUE',
                               default_files_var = None,
                               name = name,
                               config = config)

  def GetDirList(self):
    return []

#############################################################################
#
# To generate frontends, format specifiers in stylesheet_template are
# replaced with the values defined in profile for a specific frontend.
# This is done through the normal string replacement in Python:
# format % values, which requires equal number of specifiers and values.
# (original code in function GenerateStylesheet: localizedline % profile)
# Enterprise Alerts adds more specifiers in stylesheet_template, while
# the profile could be imported from previous version of GSA, which
# causes unmatched format and values.
#
# To resolve this problem, we'll continue to use the values defined in
# profiles (either imported or newly generated); if a specifier doesn't
# have a matching value in the profile, the default value defined in
# config.default.enterprise will be used.
#
# This class inherits UserDict, a wrapper class of dictionary
#
class ExtendedDict(UserDict.UserDict):
  def __init__(self, profile, default_dic):
    UserDict.UserDict.__init__(self, profile)
    self.default_dic = default_dic

  def __getitem__(self, key):
    if self.data.has_key(key):
      return self.data[key]
    else:
      return self.default_dic[key]

#############################################################################

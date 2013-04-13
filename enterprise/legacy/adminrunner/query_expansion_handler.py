#!/usr/bin/python2.4

#
# (c) Copyright 2006 Google Inc.
# David Elworthy <dahe@google.com>
#
# Handler for query expansion data files.
# This provides commands for maintaining the customer query expansion
# files. It is implemented on top of CollectionBaseHandler, which provides
# functionality for storing parameters and files. Each query expansion file
# (called an entry) consisting of the file contents and a number of
# parameters. Parameters are:
#  - type (synonyms or blacklist)
#  - name of the original (uploaded) file
#  - creation date
#  - number of entries
#  - flag to indicate whether enabled or nor
#
# There is a status value which indicates whether query expansion is up to
# date, whether there have been changes which have not yet been applied, or
# whether the changes are in the process of being appplied. It is represented
# internally using two values: a persistent one, set on any change and cleared
# at the end of applying the changes, and a transient one, set during
# apply. This allows us to avoid confusion if the system should shutdown
# during the apply process. The persistent part of the status is not set
# internally: it must be set by the caller.
#
# Commands:
#
# - getstatus
#             Returns the status of query expansion.
#
# - setstatus
#             Sets the status of query expansion.
#             Arguments: status value.
#
# - list
#             List the query expansion entries.
#             Returns newline-separated list of names.
#
# - delete
#             Delete a query expansion entry.
#             Argument: entry name.
#             Returns error code (0 for OK).
#
# - upload
#             Upload a file, verify it, and create the entry.
#             On an error, we clean up the entry, so the caller does not have
#             to delete it.
#             Arguments: name of entry, encoded parameters, maximum number of
#             errors, file contents.
#             Returns a string suitable for parsing by procesValidationReturn
#             in AdminCaller, i.,e. VALID and 0 if OK; INVALID, count of
#             errors and list of errors otherwise. The list of errors may come
#             from the standard validation library errors, or from query
#             expansion's own validation.
#
# - getentry
#             Get a query expansion entry
#             Arguments: name of the entry
#             Returns error code, or 0 and a hash containing the query
#             expansion data.
#
# - apply
#             Apply data files. Compiles the files to internal format, and
#             restarts the query rewriter. Sets status.
#             Returns error code (0 for OK).
#
# Other methods are inherited from CollectionBase.
#
# There are two classes defined here:
# 1. QueryExpansionHandler, which inherits from CollectionBase and exposes the
# commands that can be called from the adminrunner
# 2. QueryExpansionBase, which does all of the implementation that depends
# only on the collection objects. QueryExpansionHandler delegates some work
# to this.
#
# A historical note: prior to the fix for feature request 706696
# (http://b/issue?id=706696), some synonyms and blacklist files could be
# downloaded and some could not, indicated by the C.DOWNLOADABLE property being
# 1 or 0, respectively. As of this fix, all entries are downloadable, and the
# flag is always set to 1. Unfortunately, this means entries included in
# migration from old versions or loaded from importing and old configuration
# would still not be downloadable. So the AdminServer now defines an entry as
# downloadable if the flag is either 0 or 1. If we need a "really not
# downloadable" entry, then we should define this flag to be an integer and
# introduce a new value (say, 2) to mean this.

import sys
import string
import fileinput
import threading
import tempfile
import os
import re
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import config_utils
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.adminrunner import collectionbase_handler
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.tools import M

class QueryExpansionHandler(collectionbase_handler.CollectionBaseHandler):
  """Top level handler for query expansion commands."""

  # Maximum number of dictionaries/blacklists that a user can upload
  MAX_LOCAL_DICTIONARIES = 100
  # Number of internal dictionaries provided by Google
  # TODO(dahe): derive from configuration settings
  NUM_GOOGLE_DICTIONARIES = 7

  def __init__(self, conn, command, prefixes, params, cfg=None):
    """Create a query expansion base object and then pass on the init."""
    collectionbase_handler.CollectionBaseHandler.__init__(
      self, conn, command, prefixes, params, cfg)
    self.qe_base = QueryExpansionBase(self.cfg)

  def get_accepted_commands(self):
    return {
      "getstatus":   admin_handler.CommandInfo(0, 0, 0, self.getstatus),
      "setstatus":   admin_handler.CommandInfo(1, 0, 0, self.setstatus),
      "getmaxfiles": admin_handler.CommandInfo(0, 0, 0, self.getmaxfiles),
      "list"     :   admin_handler.CommandInfo(0, 0, 0, self.list),
      "delete"   :   admin_handler.CommandInfo(1, 0, 0, self.delete),
      "upload"   :   admin_handler.CommandInfo(3, 0, 1, self.upload),
      "getentry" :   admin_handler.CommandInfo(1, 0, 0, self.getentry),
      "setvar"   :   admin_handler.CommandInfo(2, 1, 0, self.setvar),
      "apply"    :   admin_handler.CommandInfo(0, 0, 0, self.apply),
      }

  def construct_collection_object(self, name):
    return self.qe_base.ConstructCollectionObject(name)

  ############################################################################

  def getstatus(self):
    """Get the status of the query expansion handler, as a numeric value."""
    if (QueryExpansionBase.applying_changes or
      QueryExpansionBase.uploading_dict):
      return C.QUERY_EXP_STATUS_PROCESSING
    else:
      return self.cfg.getGlobalParam(C.QUERY_EXP_STATUS)

  def setstatus(self, value):
    """Set the status of the query expansion handler, as a numeric value."""
    self.cfg.setGlobalParam(C.QUERY_EXP_STATUS, int(value))

  def getmaxfiles(self):
    """Returns maximum of files that can be uploaded (user+internal)."""
    return self.MAX_LOCAL_DICTIONARIES + self.NUM_GOOGLE_DICTIONARIES

  def list(self):
    """Returns a list of all query expansion entries."""
    return self.qe_base.List()

  def delete(self, name):
    if (QueryExpansionBase.applying_changes or
        QueryExpansionBase.uploading_dict):
      logging.error("Delete query exp ignored for %s.", name)
      # Note: In the superclass, 3 is for Creation failed.
      return 3
    return collectionbase_handler.CollectionBaseHandler.delete(self, name)

  def getentry(self, name):
    """Get information about a query expansion entry. On an error returns 0,
    otherwise returns a length and a hash of the entry information."""
    coll_obj = self.construct_collection_object(name)

    if not coll_obj.Exists():
      logging.error("Can't find query exp entry %s" % name)
      return '0\n'
    else:
      params = {}
      params[C.CONTENT]       = coll_obj.get_var(C.CONTENT)
      params[C.ENTRY_NAME]    = coll_obj.get_var(C.ENTRY_NAME)
      params[C.CREATION_DATE] = coll_obj.get_var(C.CREATION_DATE)
      params[C.ENTRY_TYPE]    = coll_obj.get_var(C.ENTRY_TYPE)
      params[C.ORIGINAL_FILE] = coll_obj.get_var(C.ORIGINAL_FILE)
      params[C.ENABLED]       = coll_obj.get_var(C.ENABLED)
      params[C.ENTRY_COUNT]   = coll_obj.get_var(C.ENTRY_COUNT)
      params[C.DELETABLE]     = coll_obj.get_var(C.DELETABLE)
      params[C.DOWNLOADABLE]  = coll_obj.get_var(C.DOWNLOADABLE)
      params[C.ENTRY_LANGUAGE] = coll_obj.get_var(C.ENTRY_LANGUAGE)
      return '%s\n%s' % (len(repr(params)), repr(params))

  def upload(self, name, encoded_args, max_errors, contents):
    """Upload file, verify it and create the entry.
    """
    max_errors = int(max_errors)
    if (QueryExpansionBase.applying_changes or
        QueryExpansionBase.uploading_dict):
      logging.error("Create/Upload query exp ignored (operation in progress).")
      return admin_handler.formatValidationErrors(
        validatorlib.VALID_SHORT_CIRCUIT)

    val = {}
    config_utils.SafeExec(string.strip(encoded_args), val)
    if not val.has_key('QEPARAMS'):
      logging.error("Query expansion parameters missing in %s" % encoded_args)
      return admin_handler.formatValidationErrors(
        validatorlib.VALID_SHORT_CIRCUIT)

    params = val['QEPARAMS']
    errors = validatorlib.VALID_OK

    # Uploaded entries are deletable and downloadable
    params[C.DELETABLE] = 1
    params[C.DOWNLOADABLE] = 1

    # Create a collection object in memory and do some initial checks on it,
    # but do not yet actually create it in the configuration.
    # Some of the code here is copied from collectionbase_handler, as we need
    # finer control.
    if not entconfig.IsNameValid(name):
      logging.error("Invalid query exp name %s" % name)
      return self.formatError(C.QUERYEXP_ENTRY_BAD_NAME,
                              "Invalid name")

    if not self.check_max_license():
      return self.formatError(C.QUERYEXP_LICENSE_LIMIT,
                              "License limit for query expansion reached")

    coll_obj = self.qe_base.ConstructCollectionObject(name)
    if coll_obj.Exists():
      logging.error("Query exp entry %s aleady exists" % name)
      return self.formatError(C.QUERYEXP_ENTRY_EXISTS,
                              "Query expansion entry already exists.")

    QueryExpansionBase.uploading_dict = 1
    errors = self.qe_base.Upload(coll_obj, 0, params, max_errors, contents)
    QueryExpansionBase.uploading_dict = 0

    if errors != validatorlib.VALID_OK:
      msg = M.MSG_LOG_QUERYEXP_VALIDATION_FAILED % name
      self.writeAdminRunnerOpMsg(msg)
      # Make sure we deliver the right number of errors (the validator
      # sometimes returns too many)
      return admin_handler.formatValidationErrors(errors[0:max_errors])

    msg = M.MSG_LOG_CREATE_COLLECTION % ('query expansion', name)
    self.writeAdminRunnerOpMsg(msg)
    return admin_handler.formatValidationErrors(validatorlib.VALID_OK)

  def formatError(self, code, msg):
    """Format a single error for return."""
    return admin_handler.formatValidationErrors([
      validatorlib.ValidationError(msg, code)
      ])

  def apply(self):
    """Compile data files and restart query rewrite.

    Defers to QueryExpansionBase
    """
    self.writeAdminRunnerOpMsg(M.MSG_LOG_QUERYEXP_APPLYING)
    return self.qe_base.Apply()

  def check_max_license(self):
    """Determine whether the license permits a new query expansion entry."""
    current_count = len(self.cfg.getGlobalParam('ENT_QUERY_EXP'))
    max_count = self.getmaxfiles()
    return current_count < max_count

###########################################################################
# QueryExpansionBase
class QueryExpansionBase:
  """Handles all operations which depend only on the collection object."""

  # Timeout for executing the synonyms compiler. As a data point, on an
  # unloaded one-way, a file of 80000 synonyms compiles in about 5 seconds, so
  # this limit would only be hit if something goes wrong, or on a stupendously
  # huge file or a very heavily loaded machine.
  COMPILER_TIMEOUT = 300

  # Status flag to indicate when an apply is in progress
  applying_changes = 0

  # Status flag to indicate when an upload is in progress
  uploading_dict = 0

  # Languages for which custom dictionaries and blacklists may be uploaded.
  # TODO(dahe): derive from configuration settings
  languages = ('all', 'en', 'pt', 'fr', 'it', 'de', 'es', 'nl')

  def __init__(self, cfg):
    """Initialize with global params (used for storing collection info)"""
    self.cfg = cfg

  def ConstructCollectionObject(self, name):
    """Returns a collection object for the given name."""
    return ent_collection.EntQueryExp(name, self.cfg.globalParams)

  def List(self):
    """Returns a list of all query expansion entries."""
    names = ent_collection.ListQueryExpEntries(self.cfg.globalParams)
    return "%s\n" % string.join(names, '\n')

  def Upload(self, coll_obj, patch, params, max_errors, contents):
    """Upload (make) an entry, provided the contents pass validation.
    coll_obj is a collection object for this entry.
    patch is 1 if we are to patch an existing entry (see Create for the
    collection object for details).
    param is a dictionary of additional parameters, also passed to Create.
    It must contain the entry type, but everything else is optional. The
    entry count will be filled in.
    max_errors is the maximum number of errors in validation.
    contents is the contents of the entry.

    Returns either VALID_OK, VALID_SHORT_CIRCUIT or a list of validation
    errors.
    """

    name = coll_obj.name
    logging.info("Uploading dictionary %s" % name)
    contents = entconfig.RepairUTF8(contents)

    entry_type = params[C.ENTRY_TYPE]
    validator = None
    if entry_type == C.QUERY_EXP_FILETYPE_SYNONYMS:
      validator = SynonymsValidator()
    elif entry_type == C.QUERY_EXP_FILETYPE_BLACKLIST:
      validator = BlacklistValidator()
    else:
      logging.error("Unknown entry_type: %s" % entry_type)
      return validatorlib.VALID_SHORT_CIRCUIT

    entry_count, errors = validator.validate(contents, int(max_errors))

    if errors != validatorlib.VALID_OK:
      logging.error("Errors validating query exp upload for %s" % name)
      return errors

    logging.info("Successful validation for query exp entry %s" % name)
    params[C.ENTRY_COUNT] = entry_count

    # Setting "needs apply" could be overzealous if the next stage fails,
    # but we prefer to err on the side of caution
    self.cfg.setGlobalParam(C.QUERY_EXP_STATUS,
                            int(C.QUERY_EXP_STATUS_NEEDS_APPLY))

    # Now we can actually create the object.
    try:
      if not coll_obj.Create(patch, params):
        return validatorlib.ValidationError(
          "Unable to create query exp entry", QUERYEXP_UNABLE_TO_CREATE_ENTRY)
    except Exception, e:
      t, v, tb = sys.exc_info()
      exc_msg = string.join(traceback.format_exception(t, v, tb))
      logging.error(exc_msg)
      return validatorlib.ValidationError(
        "Unable to create query exp entry", QUERYEXP_UNABLE_TO_CREATE_ENTRY)

    # Ideally we would set the contents at the same time as the Create
    # TODO(dahe): do this if possible.
    try:
      error = coll_obj.set_file_var_content(C.CONTENT, contents, validate = 0)
    except KeyError:
      coll_obj.Delete()
      return validatorlib.ValidationError(
        "Unable to create query exp entry", QUERYEXP_UNABLE_TO_CREATE_ENTRY)

    return validatorlib.VALID_OK

  def Apply(self):
    """Compile data files and restart query rewrite.

    Error codes: 0 = ok, 1 = internal I/O error, 2 = apply in progress.
    """
    if (QueryExpansionBase.applying_changes or
        QueryExpansionBase.uploading_dict):
      logging.error("Apply query exp ignored (apply/upload in progress).")
      return '2'

    if self.cfg.getGlobalParam(C.QUERY_EXP_STATUS) == C.QUERY_EXP_STATUS_OK:
      # No need to do anything...
      logging.info("Apply query exp ignored (nothing changed).")
      return '0'

    logging.info("Apply query exp settings...")
    QueryExpansionBase.applying_changes = 1

    blacklist_files = {}
    synonyms_files  = {}

    config = self.cfg.globalParams
    blacklist_output_name = config.var_copy('QUERY_EXP_COMPILED_BLACKLIST')
    synonyms_output_name = config.var_copy('QUERY_EXP_COMPILED_SYNONYMS')

    # Make sure old versions of the output files are deleted, ignore errors.
    for lang in QueryExpansionBase.languages:
      config.del_file_var_content(blacklist_output_name + '.' + lang)
      config.del_file_var_content(synonyms_output_name + '.' + lang)

    config.DistributeAll()

    names = ent_collection.ListQueryExpEntries(config)

    for name in names:
      entry = self.ConstructCollectionObject(name)

      if not entry.Exists():
        logging.error("Skipping %s - no longer exists" % name)
      elif entry.get_var(C.ENABLED) == 0:
        logging.info("Skipping %s - disabled" % name)
      else:
        type = entry.get_var(C.ENTRY_TYPE)
        lang = entry.get_var(C.ENTRY_LANGUAGE)
        local_file = entry.get_var(C.CONTENT)
        if not (lang in QueryExpansionBase.languages):
          logging.info(
            "Not compiling data for "+repr(lang)+" as it is not listed")
        else:
          if type == C.QUERY_EXP_FILETYPE_BLACKLIST:
            blacklist_files.setdefault(lang, []).append(local_file)
          else:
            synonyms_files.setdefault(lang, []).append(local_file)

    # We may have work to do. Even if not, we still need to restart qrewrite.
    # As the files could be large, we spawn a separate thread and
    # do the work asynchronously. Also, if there are changes in
    # the list of entries from now on, we are protected against them.
    t = threading.Thread(target=self.runApply,
                         args=(blacklist_files, blacklist_output_name,
                               synonyms_files,  synonyms_output_name))
    t.start()
    logging.info("Started thread to apply query expansion data.")
    return '0'

  def runApply(self,
               blacklist_files, blacklist_output_name,
               synonyms_files,  synonyms_output_name):

    config = self.cfg.globalParams

    err = 0
    try:
      # Since we are using a try...finally block, to comply with Google's
      # Python style, we need to know if an exception interrupted normal flow.
      finished_apply = 0
      # In case there are no files, we want to wipe out the output file.
      for lang in QueryExpansionBase.languages:
        blacklist_file_name = blacklist_output_name + '.' + lang
        blacklist_output = open(blacklist_file_name + '.new', "w")

        if blacklist_files.has_key(lang):
          self.copylines(blacklist_files[lang], blacklist_output)
        blacklist_output.close()
        os.rename(blacklist_file_name + '.new', blacklist_file_name);

        config.add_file_to_distribute(blacklist_file_name, None)

      # In case there are no files, we want to wipe out the output file.
      # NOTE: We want to process an empty file into the synonyms output.
      #       Creating an empty file would not work.
      for lang in QueryExpansionBase.languages:
        synonyms_intermediate_name = tempfile.mktemp()
        synonyms_output = open(synonyms_intermediate_name, "w")
        if synonyms_files.has_key(lang):
          self.copylines(synonyms_files[lang],  synonyms_output)
        synonyms_output.close()

        out_file_name = synonyms_output_name + '.' + lang
        logging.info(
          "Starting synonyms compilation from %s" % synonyms_intermediate_name)
        err = self.compile_synonyms(
          synonyms_intermediate_name, out_file_name + '.new')
        logging.info(
          "Finished synonyms compilation from %s" % synonyms_intermediate_name)

        if err:
          logging.error("Error in compiling synonyms [%s]" % str(err))
        else:
          os.rename(out_file_name + '.new', out_file_name)
          config.add_file_to_distribute(out_file_name, None)

        os.remove(synonyms_intermediate_name)

      config.DistributeAll()
      finished_apply = 1
    finally:
      if not finished_apply:
        logging.error("A exception occurred on query exp apply operation.")

      QueryExpansionBase.applying_changes = 0

      if err != 0:
        self.cfg.setGlobalParam(
          C.QUERY_EXP_STATUS, int(C.QUERY_EXP_STATUS_ERROR))
      else:
        self.cfg.setGlobalParam(C.QUERY_EXP_STATUS, int(C.QUERY_EXP_STATUS_OK))

  def copylines(self, source_names, destination):
    """ Copy lines from file list, removing comments and blank lines.
    """
    # UTF-8 BOM character (byte order marker),
    utf8_bom = unichr(0xFEFF).encode("utf-8")

    for file_name in source_names:
      input_file = file(file_name, 'r')
      lines = input_file.readlines()
      if lines:
        # If the file starts with BOM character,
        # remove it before copying to the destination.
        lines[0] = lines[0].replace(utf8_bom, '')
        dest_lines = []
        for line in lines:
          if len(string.strip(line)) == 0 or line[0] == '#':
            continue
          dest_lines.append(line)
        # Let's guarantee that there is a new line after the last entry.
        dest_lines.append('\n')

        destination.writelines(dest_lines)

  def compile_synonyms(self, source, destination):
    """Execute the synonyms compiler and return error code."""

    # In the command line, we set the maximum errors to 1 so we can halt as
    # quickly as possible. The assumption is that the input files have already
    # been validated.
    commandline = \
    'make_custom_synonym_map --synonym_file=%s --output_syn_map=%s \
      --max_errors=1' % (source, destination)

    return E.execute(
      ['localhost'], commandline, None, QueryExpansionBase.COMPILER_TIMEOUT)


###########################################################################
# Validators.
# There are validator classes for the different files types, and also for the
# lines within each file.
# Textual errors in the code below should not be used directly in the UI, and
# are included for compatibility with the format used by the validator library

class QueryExpansionValidator:
  """Base class for query expansion validators."""

  QUERY_EXP_SPECIAL_CHARACTERS = '!"#$%()*+,-/.:;<?@[\\]^`{|}~'

  def validate(self, contents, max_errors):
    """Split contents into lines, and execute validate_line on
    each. Errors from validate_line are accumulated into a list of
    validatorlib.ValidationError objects, up to the maximum number
    specified. Also checks for empty contents. On success, returns
    validatorlib.VALID_OK instead of a list of errors.
    Returns the number of entries and the errors list.
    """
    entry_count = 0
    line_number = 0
    has_only_blank = 1
    error_count = 0
    errors = []

    # Skip the BOM if given
    utf8_bom = unichr(0xFEFF).encode("utf-8")
    if contents.startswith(utf8_bom):
      contents = contents[len(utf8_bom):]

    for line in contents.splitlines():
      line = string.strip(line)
      line_number += 1

      if line == '':
        continue

      has_only_blank = 0
      if line.startswith('#'):
        continue

      entry_count += 1
      error = self.validate_line(line)
      if error:
        error.addAttrib('LINE', line_number)
        errors.append(error)
        error_count += 1
        if error_count >= max_errors:
          break

    if has_only_blank:
      errors.append(
        validatorlib.ValidationError(
        "File must be non-empty",
        C.QUERY_EXP_VALIDATION_FILE_EMPTY))

    if not errors:
      errors = validatorlib.VALID_OK
    return (entry_count, errors)

  def validate_line(self, line):
    """Validate a line and return either None or an error, in the
    form of a validatorlib.ValidationError object.
    """
    # Stub version - overridden in subclasses.
    return None

  def check_characters(self, item, special):
    """Check item for a character in special. Return an error if found,
    None otherwise.
    """
    for c in special:
      if c in item:
        return validatorlib.ValidationError(
          "Item contains invalid character",
          C.QUERY_EXP_VALIDATION_INVALID_CHAR)
    return None

class SynonymsValidator(QueryExpansionValidator):
  """Validator for synonyms files"""
  QUERY_EXP_SYNONYMS_SPECIAL_CHARACTERS \
    = QueryExpansionValidator.QUERY_EXP_SPECIAL_CHARACTERS

  def validate_line(self, line):
    """Validate a line and return either None or an error, in the
    form of a validatorlib.ValidationError object.
    """
    if line.startswith('{'):
      return self.validate_set(line);

    operator = string.find(line, '=')
    if operator == -1:
      operator = string.find(line, '>')

    if operator != -1:
      return self.validate_equivalence(line, operator)

    # No setbrackets and not an operator
    return validatorlib.ValidationError(
      "Line must contain an operator (= or >) or be a set",
      C.QUERY_EXP_VALIDATION_OPERATOR)

  def validate_equivalence(self, line, operator):
    """Validate an equivalence line (i.e. a=b or a>b).
    See validate_line for return values.
    """
    # Check for more than one operator
    op = line[operator]
    if op == '=':
      other = '>'
    else:
      other = '='

    # Check whether the same operator appears a second time
    # and whether the other operator appears at all
    if (string.find(line, op, operator+1) >= 0 or
        string.find(line, other) >= 0):
      return validatorlib.ValidationError(
        "Line must contain one operator (= or >)",
        C.QUERY_EXP_VALIDATION_OPERATOR)

    left_part = string.strip(line[0:operator])
    if left_part == '':
      return validatorlib.ValidationError(
        "Word or phrase missing before operator",
        C.QUERY_EXP_VALIDATION_EMPTY_LEFT)
    error = self.check_characters(
      left_part, self.QUERY_EXP_SYNONYMS_SPECIAL_CHARACTERS)
    if error:
      return error

    right_part = string.strip(line[operator+1:])
    if right_part == '':
      return validatorlib.ValidationError(
        "Word or phrase missing after operator",
        C.QUERY_EXP_VALIDATION_EMPTY_RIGHT)
    error = self.check_characters(
      right_part, self.QUERY_EXP_SYNONYMS_SPECIAL_CHARACTERS)
    if error:
      return error

    return None

  def validate_set(self, line):
    """Validate a set line (i.e. {a, b, ...}).
    See validate_line for return values.
    """
    if not line.endswith('}'):
      # Set with missing close brackets
      return validatorlib.ValidationError(
        "Missing } for word set.",
        C.QUERY_EXP_VALIDATION_SET_SYNTAX)

    if string.find(line, "=") >= 0 or string.find(line, ">") >= 0:
      return validatorlib.ValidationError(
          "Sets can not contain operators = and >.",
          C.QUERY_EXP_VALIDATION_SET_SYNTAX)

    word_set = string.split(line[1:-1], ',')
    if len(word_set) > 32:
      return validatorlib.ValidationError(
        "Too many elements in word set. The limit is 32.",
        C.QUERY_EXP_VALIDATION_SET_TOO_BIG)

    if len(word_set) == 0:
      return validatorlib.ValidationError(
        "Empty word set.",
        C.QUERY_EXP_VALIDATION_SET_SYNTAX)

    for w in word_set:
      if string.strip(w) == '':
        return validatorlib.ValidationError(
          "Empty elements in word set.",
          C.QUERY_EXP_VALIDATION_SET_SYNTAX)
      error = self.check_characters(
        w, self.QUERY_EXP_SYNONYMS_SPECIAL_CHARACTERS)
      if error:
        return error

    return None

class BlacklistValidator(QueryExpansionValidator):
  """Validator for blacklist files"""
  QUERY_EXP_BLACKLIST_SPECIAL_CHARACTERS \
    = QueryExpansionValidator.QUERY_EXP_SPECIAL_CHARACTERS

  def __init__(self):
    self.whitespace = re.compile('\s')

  def validate_line(self, line):
    """Validate a line and return either None or an error, in the
    form of a validatorlib.ValidationError object.
    """
    # Only allow lines with no white space
    if self.whitespace.search(line):
      return validatorlib.ValidationError(
        "Cannot have space in blacklist entry",
        C.QUERY_EXP_VALIDATION_WHITESPACE)

    return self.check_characters(
      line, self.QUERY_EXP_BLACKLIST_SPECIAL_CHARACTERS)

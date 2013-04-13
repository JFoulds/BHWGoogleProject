#!/usr/bin/python2.4
#
# Copyright (c) Google Inc, 2001 and beyond!
# Author: David Watson
#
#   This module contains a library of Validators, which are small stateless
# objects that check if a value is a well-formed, valid value.  Each Validator
# subclass knows how to do the checking for a particular type (a restriction
# on the form of acceptable values).  Subclasses of a validator implement
# subtypes by imposing further value constraints.
#
# Usage:
#   Once validators are created, they can be re-used as many times as desired
# since they are stateless.  The only method supported is the validate()
# method.  This takes the value to be validated and a ValidatorContext object
# (used to control access to the system environment, described later);  it
# returns either VALID_OK or VALID_SHORT_CIRCUIT, in the case of an error, a
# list of ValidationError() objects.
# VALID_OK means that all steps of the validation were tested and met.
# VALID_SHORT_CIRCUIT means that the value is valid, but no further steps
# should be attempted.  Both of these are all good status codes which
# indicate success.
#
# Example:
#   # Create a validator
#   validator = validatorlib.Int(GTE=0,LTE=100)
#
#   # Create context for validation
#   context = ValidatorContext(file_access=1, dns_access=1)
#
#   # Do some validation
#   for value in (1, 2, "invalid", None):  # do some validation
#     validator.validate(value, context)
#
#
# Validators:
#   This validator library contains the following class hiearchy, each of which
# enforces the listed type.
#
# Validator - Any value; optionally allowed to be null (None)
# |
# +-Bool  - A boolean; must be 1 or 0
# +-Set  - Must be one of a pre-specified set of values
# +-Type
# | |
# | +-Num
# | | +-Int  - An integer; optional range constraints
# | | | +-PortNum  - A TCP port number; must be an integer in a valid range
# | | | +-DocId  - A DocId; must be an integer in a valid range
# | | +-Long  - A long; optional range constraints
# | | +-Float  - A float; optional range constraints
# | |   +-FloatPercent  - A float between 0.0 and 1.0
# | |
# | +-String - A string; non-empty by default; optional equality constraints
# | | +-Re - A string that is a valid regular expression
# | | +-ReMatch - A string which matches a given regular expression
# | | +-SeparatedList  - A token seperated list; applies another
# | | | |                validator to each element
# | | | +-CommaList  - A comma separated list; same as SeparatedList
# | | |
# | | +-Filename  - A file (or directory) name; must be absolute (by default)
# | | | +-BaseFile
# | | |   +-File  - A file; must exist; optional permission and emptiness
# | | |   | |       constraints
# | | |   | +-FileLine  - A line-oriented file; applies another validator to
# | | |   |   |           each line; ignores comments and blank lines
# | | |   |   +-DupHostFile  - A duphosts file
# | | |   |   +-URLPatternFile  - A file of URL patterns
# | | |   |   +-HostLoadFile  - A hostload file
# | | |   |   +-ConnectorLoadFile  - A Connector load file for Enterprise
# | | |   |   +-URLFile  - A file of Urls
# | | |   |   +-SsoCookiePatternFile  - A file of Cookie pattern with crawling credentials
# | | |   |   +-SsoServingFile  - A file of SSO serving record.
# | | |   +-Dir  - A directory; must exist; optional permission constraints
# | | |
# | | +-Hostname  - A hostname; optional FQDN-ness and DNS constraints
# | | | +-GoogleProductionMachine  - A google production machine; optional DNS
# | | |                              and datacenter (prefix) constraints
# | | +-IPAddress  - An IP address
# | | +-MachinePort  - A colon serarated GoogleProductionMachine, PortNum pair
# | | +-URL  - A well-formed URL
# | | +-EmailAddress  - An email address
# | | +-URLPattern  - A URL pattern
# | | +-DupHostEntry  - A duphost entry
# | | +-SsoCookiePatternEntry - A Cookie pattern entry with crawling credentials
# | | +-SsoServingEntry - An SSO serving configuration record.
# | | +-HostLoad  - A hostload entry
# | | +-EnterpriseHostLoad  - A hostload entry for Enterprise
# | | +-EnterpriseConnectorLoad  - A Connector load entry for Enterprise
# | | +-ExtraHdrsConfig
# | | +-EntPrereq
# | |
# | +-Sequence
# | | +-List  - A list; applies specified validator to each element; optional
# | | |         length constraints and optional per element validator
# | | +-Tuple  - A tuple; applies specified validator to each element; optional
# | |            length constraints and optional per element validator
# | |
# | +-Map  - A map; applies separate validators to keys and values; optional
# |          size and required keys constraint
# |
# +-OrMeta  - Applies a list of Validators; at least one must succeed
# | +-URLOrURLFile  - A Url or a file of Urls
# | +-DevNullOrDir  - A directory or /dev/null
# |
# +-AndMeta  - Applies a list of Validators; all must succeed
# +-ValidatorInstance  - Must be an instance of Validator
#

import os
import re
import socket
import string
import types
import urllib
import urlparse

from google3.webutil.url import pywrapurl
from google3.webutil.urlutil import pywrapurlmatch
from google3.webutil.urlutil import pywrapduphosts

# This will disable the files/dir validation part - we don't check the
# existence and the values in the files
# ** NOTE: Use with care **
_NoFileValidation = 0
def set_no_file_validation(val):
  global _NoFileValidation
  _NoFileValidation = val

def is_file_validation_disabled():
  global _NoFileValidation
  return _NoFileValidation

###################################
# Support Classes:

################
# ValidationError:
#
#  Errors returned by validators are ValidationError objects.  Each object
#  has two important members:
#   message: string with human readable error message
#   attribs: a map of optional attributes further describing the error.  Some
#            useful attributes might be:
#     LINE:     The line number where the error occured (for parm types that
#               make sense, such as line-based files)
#     ELEMENT:  The element number of a sequence which had the error (for
#               param types that make sense, such as sequences)
#     ERR_CODE: An integer code describing the error (useful for supporting a
#               UI).
#  Note that attributes are not nested, so errors for complex nested types
#  may not have full information.  For example, suppose we're validating a
#  nested list of objects, such as [[GOOD, BAD, GOOD],[GOOD, GOOD, GOOD]].
#  The error the the BAD element, should have an ELEMENT attribute with the
#  index of outer list (0), which omits the index of the inner list (1).
#

# Error codes:
ERR_FILE_EMPTY      = 1
ERR_URL_NO_PATH     = 2
ERR_UNSET           = 3
ERR_STRING_EMPTY    = 4
ERR_URL_NO_PROTOCOL = 5
ERR_URL_NO_HOST     = 6
ERR_HOST_NOT_FULLY_QUALIFIED = 7
ERR_URLPATTERN_NONANCHORED   = 8
ERR_RE_NO_MATCH     = 9
ERR_BAD_IP          = 10
ERR_BAD_HOST        = 11
ERR_BAD_HOSTLOAD_ENTRY = 12
ERR_FILE_WRONG_OWNER = 13
ERR_FILE_WRONG_GROUP = 14
ERR_BAD_RE           = 15
ERR_METATAG_EXIST_ONLY              = 16
ERR_METATAG_NO_VALUE_TO_MATCH       = 17
ERR_FILE_EXT_HAS_SLASH              = 18
ERR_FILE_EXT_PERIOD_IN_MIDDLE       = 19
ERR_FILE_EXT_MUST_START_WITH_PERIOD = 20
ERR_FILE_EXT_CANT_START_WITH_PERIOD = 21
ERR_FILE_EXT_NONE_SPECIFIED         = 22
ERR_SITENAME_CANT_HAVE_PATH         = 23

# Constants:
STAT_ST_UID = 4
STAT_ST_GID = 5

class ValidationError:
  """Class to represent validation error"""

  def __init__(self, message, ERR_CODE=None):
    self.message = message
    self.attribs = {}
    if ERR_CODE != None:
      self.addAttrib("ERR_CODE", ERR_CODE)

  def __repr__(self):
    s = []
    for attrib,value in self.attribs.items():
      s.append("%s(%s)" % (attrib, repr(value)) )
    s.append(self.message)
    return string.join(s, ": ")

  # adds the named attribute to the ValidationError
  def addAttrib(self, name, value):
    self.attribs[name] = value

  # adds the named attribute to the ValidationError, and maintains another
  # list attribute (name + '_PATH'), which keeps track of all previous values.
  def addPathAttrib(self, name, value):
    path_value = self.attribs.get('%s_PATH' % name, [])

    path_value.insert(0, value)

    self.attribs[name] = value
    self.attribs['%s_PATH' % name] = path_value

# Validation response codes:
VALID_OK = 0              # valid
VALID_SHORT_CIRCUIT = 1   # valid, but no further validation should be done

VALID_CODES = (VALID_OK, VALID_SHORT_CIRCUIT)

################
# ValidatorContext:

# ValidatorContext is used to control access to everything not actually
# present in the value being validated, such as access to disk and DNS
# lookups.  This exists for two reasons:  First, it helps to make use of all
# "external context" explicit, since validators are supposed to validate
# only the value in question.  Second, it gives control over if (and how) this
# "external context" is accessed, so that the same validator can be used in
# different settings.
#
# ValidatorContext currently supports:
#  - file access:
#  - file mapping
#  - dns access
#  - max # lines to check for files of type FileLine or its subclasses
#    This is necessary due to performance issues for huge files.
#  - valid prefixes for machines
#  - max # errors
class ValidatorContext:
  def __init__(self, file_access, dns_access, max_errors = 5):
    self.file_access_ = file_access  # Access files
    self.file_map = None   # No file mappings
    self.dns_access_ = dns_access   # Access DNS
    self.fileline_limit_ = -1       # No limit
    self.max_errors_ = max_errors
    self.machine_prefixes_ = None  # all prefixes valid

  ##
  # FILE ACCESS:
  #
  #  boolean flag which says whether it's allowed to access any files
  def set_file_access(self, b):
    self.file_access_ = b

  def file_access(self):
    return self.file_access_

  ##
  # FILE MAPPING:
  #
  #  file mapping allows remapping of file names for file accesses.  This
  #  is useful when validating a config file in non-production environments.
  #  For example:
  #       /root/google/setup/ -> ~davidw/src/main/google/setup/
  #
  #  Mapping is done using longest prefix matching; if no mapping is found,
  #  no mapping is done.  New mappings are added using add_file_mapping.
  def add_file_mapping(self, from_dir, to_dir):
    # normalize both paths
    from_dir = os.path.normpath( os.path.expanduser( from_dir ) )
    to_dir = os.path.normpath( os.path.expanduser( to_dir ) )

    # we only deal with absolute paths, so ensure that's what we have
    if not os.path.isabs( from_dir ) or not os.path.isabs( to_dir ):
      return 0

    # if no map yet exists, make it now
    if self.file_map == None:
      self.file_map = {}

    # store the mapping
    self.file_map[from_dir] = to_dir
    return 1

  def file_mapping(self, filename):
    # if no mappings exist, there's nothing to do
    if self.file_map == None:
      return filename

    # We do a reverse search through each path segment of the filename
    pos = len(filename)
    while pos >= 0:
      # try this segment, making sure to normalize it
      test_path = os.path.normpath(filename[:pos+1])

      # if this segment matches a mapping, replace the matching segment with
      # it's mapping and return
      if self.file_map.has_key(test_path):
        return self.file_map[test_path] + filename[pos:]

      # move on to the next segment
      pos = string.rfind(filename, '/', 0, pos)

    # we didn't find any matches, return the original filename
    return filename


  ##
  # DNS ACCESS:
  #
  #  boolean flag which says whether it's allowed to to any DNS lookups
  def set_dns_access(self, b):
    self.dns_access_ = b

  def dns_access(self):
    return self.dns_access_

  ##
  # FileLine limit on lines to check
  #
  #  int flag for how many lines to check. -1 to unlimit
  def set_fileline_limit(self, i):
    self.fileline_limit_ = i

  def fileline_limit(self):
    return self.fileline_limit_

  ##
  # MACHINE PREFIXES:
  #
  #  list of valid machine prefixes
  def set_machine_prefixes(self, p):
    self.machine_prefixes_ = p

  def has_valid_machine_prefix(self, host):
    if self.machine_prefixes_ == None:
      return 1

    for prefix in self.machine_prefixes_:
      if host[:len(prefix)] == prefix and len(host) > len(prefix):
        return 1

    return 0

  ##
  # MAX # ERRORS:
  #
  # integer which puts a limit on the number of errors to return from a single
  # validation.  This is put in the context since different validation
  # situations may call for different levels of verbosity.
  def set_max_errors(self, n):
    self.max_errors_ = n

  def max_errors(self):
    return self.max_errors_


################
# Validators:


class Validator:
  """
  Validator is the base class of all Validators.

  Subclasses should override validate to add additional constraints, but
  they must _first_ call the superclass validate() and return its status
  unless it is VALID_OK.

  Almost all arguments taken by Validators are optional (with reasonable
  defaults), and if used should be specified as named parameters (versus
  positional).  This makes the meaning of each option very clear, and the
  code more robust since it will catch removal/renaming of options very early.

  Validators are designed to find all specification errors (invalid flags,
  values, or usage in validator instantiation) as early as possible.  As
  much verification as possible should happen in the constructor.

  nullOK: if true, a value of None is valid, else it is invalid
  """

  def __init__(self, nullOK = 0):
    self.doc = "(nullOK = %d)" % nullOK
    self.nullOK = nullOK

  # Determines if value is a valid value for this validator.
  # If valid, returns VALID_OK or VALID_SHORT_CIRCUIT
  # If invalid, returns list of ValidationErrors.
  def validate(self, value, context):
    """
    We return VALID_OK is we checked our value and it was good,
    VALID_SHORT_CIRCUIT if our value is good but all further tests should
    be short-circuited, or a list of ValidationError objects on error.

    Subclasses should override this method to add additional constraints,
    but they must first call the superclass validate(), and perform their
    own validation only if it returns VALID_OK.

    We should _never_ throw an exception to indicate an invalid value.
    Failed assertions (programming invariants) should _always_ be handled
    through exceptions.
    """

    if value != None:   # no error
      return VALID_OK
    elif self.nullOK:   # short-circuit
      return VALID_SHORT_CIRCUIT
    else:               # error: variable unset
      return [ValidationError("Unset", ERR_CODE = ERR_UNSET)]

########################
# validators for basic types

class Type(Validator):
  """Validator to ensure variable is of the given (python) type"""

  # Type objects (the values returned by type()) are not pickleable.
  # Thus we store exemplars instead, and call type() on the exemplar
  # whenever we need the type.
  STRING_EXEMPLAR = ""
  LIST_EXEMPLAR = []
  TUPLE_EXEMPLAR = ()
  MAP_EXEMPLAR = {}
  INTEGER_EXEMPLAR = 3
  LONG_EXEMPLAR = 3L
  FLOAT_EXEMPLAR = 3.14

  def __init__(self, exemplar, nullOK = 0):
    Validator.__init__(self, nullOK)
    self.exemplar = exemplar
    self.doc = "(type = %s, nullOK = %d)" % (type(exemplar).__name__, nullOK)

  def validate(self, value, context):
    r = Validator.validate(self, value, context)
    if VALID_OK != r: return r

    # check the type of value
    if isinstance(value, type(self.exemplar)):
      return VALID_OK
    else:
      return [ValidationError("Must be an %s" % type(self.exemplar).__name__)]

class Num(Type):
  """Subclass of Type which applies numeric range constraints"""

  OP_TABLE = {
    'LT'  : '<',
    'LTE' : '<=',
    'EQ'  : '==',
    'NE'  : '!=',
    'GTE' : '>=',
    'GT'  : '>',
    }

  # exemplar: an exemplar of a python Type.
  # also takes the following range constraint and named parameters:
  #   LT, LTE, EQ, NE, GTE, GT (of the same type as var_type)
  def __init__(self, exemplar, nullOK = 0, **args):
    Type.__init__(self, exemplar, nullOK)
    args_doc = string.join( map(lambda (n,v): ', %s = %s' % (n,v),
                                args.items()), '')
    self.doc = "(type = %s, nullOK = %d%s)" % (type(exemplar).__name__,
                                               nullOK, args_doc)

    self.ops = []
    for (op, value) in args.items():
      # make sure value is of the right type
      assert type(value) == type(exemplar), str(value)
      self.ops.append((self.OP_TABLE[op],
                       value,
                       "Must be %s %s" % (op, str(value))))

  def validate(self, value, context):
    r = Type.validate(self, value, context)
    if VALID_OK != r: return r

    # check the type of value
    for (op, limit, error_string) in self.ops:
      pred = eval("lambda x, m=limit: x %s m" % op)
      if not pred(value): return [ValidationError(error_string)]
    return VALID_OK

class Int(Num):
  """An integer; optional range constraints"""
  def __init__(self, **args):
    apply(Num.__init__, (self, Type.INTEGER_EXEMPLAR), args)

class Long(Num):
  """A long; optional range constraints"""
  def __init__(self, **args):
    apply(Num.__init__, (self, Type.LONG_EXEMPLAR), args)

  def validate(self, value, context):
    # we are also willing to take integers
    if type(value) == types.IntType:
      value = long(value)

    # check our constraints
    return Num.validate(self, value, context)

class Float(Num):
  """A float; optional range constraints"""
  def __init__(self, **args):
    apply(Num.__init__, (self, Type.FLOAT_EXEMPLAR), args)

  def validate(self, value, context):
    # we are also willing to take integers
    if type(value) == types.IntType:
      value = float(value)

    # check our constraints
    return Num.validate(self, value, context)

class String(Type):
  """A string; non-empty by default; optional equality constraints

     nullOK: if true, a value of None is valid, else it is invalid
     emptyOK: if true, value of "" is valid, else it is invalid
     EQ: if provided, value must match this value
     NE: if provided, value must not match this value
  """

  def __init__(self, nullOK = 0, emptyOK = 0, EQ = None, NE = None):
    Type.__init__(self, Type.STRING_EXEMPLAR, nullOK = nullOK)
    self.emptyOK = emptyOK
    self.EQ = EQ
    self.NE = NE
    self.doc = "(nullOK = %d, emptyOK = %d, EQ = %s, NE = %s)" % (
      nullOK, emptyOK, repr(EQ), repr(NE))

  def validate(self, value, context):
    r = Type.validate(self, value, context)
    if VALID_OK != r: return r

    if 0 == len(value):
      if self.emptyOK: return VALID_SHORT_CIRCUIT
      else: return [ ValidationError("Empty", ERR_CODE = ERR_STRING_EMPTY) ]
    elif None != self.EQ and value != self.EQ:
      return [ValidationError("Must be equal to %s" % str(self.EQ))]
    elif None != self.NE and value == self.NE:
      return [ValidationError("Must not be equal to %s" % str(self.NE))]
    else:
      return VALID_OK

class Re(String):
  """ A string which evaluates to a valid regular expression"""
  def __init_(self, **args):
    apply(String.__init__, (self,), args)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if r != VALID_OK:
      return r
    # can't catch an real exception because there's a different
    # exception in python and python2.2
    try:
      re.compile(value)
    except Exception, e:
      return [ValidationError('Must be a valid regular expression. Errors from '
                              're.compile : %s' % str(e),
                              ERR_CODE = ERR_BAD_RE)]
    return VALID_OK

class ReMatch(String):
  """A string which matches a given regular expression"""
  def __init__(self, regExpr, **args):
    apply(String.__init__, (self,), args)
    # construct self.doc by combing everything from args
    arg_docs = map(lambda (k,v): "%s = %s" % (repr(k), repr(v)),
                     [('regExpr', regExpr)] + args.items())
    self.doc = "(" + string.join(arg_docs, ', ') + ")"
    self.regexp = regExpr
    self.compiled = re.compile(regExpr)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    if self.compiled.search(value) != None:
      return VALID_OK
    else:
      return [ValidationError("Must match re %s" % self.regexp,
                              ERR_CODE = ERR_RE_NO_MATCH)]

class Set(Validator):
  """Must be one of a pre-specified set of values"""

  # objects: a list of valid objects
  def __init__(self, set, nullOK = 0):
    Validator.__init__(self, nullOK=nullOK)
    self.doc = "(nullOK = %d, objects = %s)" % (nullOK, repr(set))
    self.set = set

  def validate(self, value, context):
    r = Validator.validate(self, value, context)
    if VALID_OK != r: return r

    if value in self.set:
      return VALID_OK
    elif 2 == len(self.set):
      return [ValidationError("Must be %s or %s" % (self.set[0], self.set[1]))]
    else:
      return [ValidationError("Must be one of %s" % repr(self.set))]

class Bool(Set):
  """A boolean; must be 1 or 0"""
  def __init__(self, nullOK = 0):
    Set.__init__(self, (0, 1), nullOK=nullOK)

########################
# "Meta" validators - validators which apply other validators in novel ways.
# Most of these overload validate() in some exciting way.

class OrMeta(Validator):
  """Applies a specified set of Validators; at least one must succeed"""
  def __init__(self, validators = [], nullOK = 0):
    Validator.__init__(self, nullOK)
    self.doc = "(nullOK = %d, validators = %s)" % (nullOK, repr(validators))
    self.validators = validators

  def validate(self, value, context):
    r = Validator.validate(self, value, context)
    if VALID_OK != r: return r

    all_errors = []
    # try each of the specified validators until one succeeds
    for i in range(len(self.validators)):
      status = self.validators[i].validate(value, context)
      # if any validator succeeds (or short-circuits), we're done
      if status in VALID_CODES:
        return status
      # Since we're OR-ing a bunch of validators together, the method of error
      # reporting is sub-optimal.  Reporting all errors is inaccurate
      # because only all the constraints of _one_ of the validators has to be
      # met, not of _all_ them.  We could report no errors and simply say
      # "error", but this looses _all_ the error information.  We could report
      # the errors for only one of the validators, but it's not clear which. We
      # choose to return _all_ errors, but we set the OR_ELEMENT attrib on each
      # of them to indicate which validator produced the error
      for error in status: error.addAttrib('OR_ELEMENT', i)
      all_errors.extend( status )

    # if all fail, we return all errors encountered
    return all_errors

class AndMeta(Validator):
  """Applies a specified set of Validators; all must succeed"""
  def __init__(self, validators = [], nullOK = 0):
    Validator.__init__(self, nullOK)
    self.doc = "(nullOK = %d, validators = %s)" % (nullOK, repr(validators))
    self.validators = validators

  def validate(self, value, context):
    r = Validator.validate(self, value, context)
    if VALID_OK != r: return r

    # try each of the specified validators until one is not OK
    for validator in self.validators:
      errors = validator.validate(value, context)
      if errors not in VALID_CODES:
        return errors

    return VALID_OK

class ValidatorInstance(Validator):
  """Must be an instance of some validator class"""

  def __init__(self, nullOK = 0):
    Validator.__init__(self, nullOK=nullOK)

  def validate(self, value, context):
    r = Validator.validate(self, value, context)
    if VALID_OK != r: return r
    if isinstance(value, Validator):
      return VALID_OK
    else:
      return [ValidationError("Must be a Validator")]

class Sequence(Type):
  """Meta-Validator for sequences types.  Applies specified validator
  to each element"""

  def __init__(self, validator, exemplar, nullOK = 0,
               min_size = None, max_size = None, eq_size = None,
               elem_validator = None):
    """
    validator: the Validator to apply to each element
    exemplar: an exemplar of the type of the sequence
    min_size, max_size, eq_size: optional length constraints
    elem_validator: optional per position validator
    """
    Type.__init__(self, exemplar, nullOK)
    self.doc = "(nullOK = %d, validator = %s, var_type = %s, min_size = %s, max_size = %s, eq_size = %s, elem_validator = %s)" % (nullOK, repr(validator), type(exemplar).__name__, repr(min_size), repr(max_size), repr(eq_size), repr(elem_validator))
    self.validator = validator
    self.min_size = min_size
    self.max_size = max_size
    self.eq_size  = eq_size
    self.elem_validator = elem_validator

  def validate(self, value, context):
    r = Type.validate(self, value, context)
    if VALID_OK != r: return r

    length = len(value)
    # if specified, check that the sequence is at most the specified size
    if self.eq_size != None and self.eq_size != length:
      return [ValidationError("Size must be equal to %d" % self.eq_size)]

    # if specified, check that the sequence is at least the specified size
    if self.min_size != None and self.min_size > 0 and self.min_size > length:
      return [ValidationError("Size must be at least %d" % self.min_size)]

    # if specified, check that the sequence is at most the specified size
    if self.max_size != None and self.max_size < length:
      return [ValidationError("Size must be no more than %d" % self.max_size)]

    max_errors = context.max_errors()

    # validate each element separately; save any errors until the end
    all_errors = []
    for element_num in range(len(value)):
      if self.validator != None:
        errors = self.validator.validate(value[element_num], context)
        if errors not in VALID_CODES:
          for error in errors: error.addAttrib('ELEMENT', element_num)
          all_errors.extend(errors)
      if ( self.elem_validator != None and
           element_num < len(self.elem_validator) and
           self.elem_validator[element_num] != None):
        errors = self.elem_validator[element_num].validate(value[element_num],
                                     context)
        if errors not in VALID_CODES:
          for error in errors: error.addAttrib('ELEMENT', element_num)
          all_errors.extend(errors)
      if len(all_errors) > max_errors:
        break

    # if there were any errors, return them
    if all_errors: return all_errors
    else:          return VALID_OK

class List(Sequence):
  """A list; applies specified validator to each element; optional length contraints"""
  def __init__(self, validator, **args):
    apply(Sequence.__init__, (self, validator, Type.LIST_EXEMPLAR), args)

class Tuple(Sequence):
  """A tuple; applies specified validator to each element; optional length contraints"""
  def __init__(self, validator, **args):
    apply(Sequence.__init__, (self, validator, Type.TUPLE_EXEMPLAR), args)

class SubsetList(List):
  """A list which first gets filtered by a supplied subset list"""
  def __init__(self, validator, subset_list, **args):
    apply(List.__init__, (self, validator), args)
    self.subset_list = subset_list

  def validate(self, value, context):
    # first, if value is a list, filter it by subset_list
    if self.subset_list != None and type(value) == types.ListType:
      modified_value = filter(lambda x, s = self.subset_list: x in s, value)
    else:
      modified_value = value

    # now, check our _own_ constraints against the modified list
    return List.validate(self, modified_value, context)

class RestrictedList(List):
  """A list with additional element requirements"""
  def __init__(self, validator,
               required_elements = None,
               optional_elements = None,
               allow_unknown_elements = 1,
               **args):
    apply(List.__init__, (self, validator), args)
    args_doc = string.join( map(lambda (n,v): ', %s = %s' % (n,v),
                                args.items()), '')
    self.doc = "(required_elements = %s, optional_elements = %s, allow_unknown_elements = %d%s)" % (repr(required_elements), repr(optional_elements), allow_unknown_elements, args_doc)
    self.required_elements = required_elements

    if allow_unknown_elements:
      self.known_elements = None
    else:
      self.known_elements = []
      if required_elements != None:
        self.known_elements.extend(required_elements)
      if optional_elements != None:
        self.known_elements.extend(optional_elements)

  def validate(self, value, context):
    r = List.validate(self, value, context)
    if VALID_OK != r: return r

    # if specified, check that the required elements are in the list
    if self.required_elements != None:
      errors = []
      for element in self.required_elements:
        if element not in value:
          error = ValidationError("Must have entry for %s" % str(element))
          error.addAttrib('ELEMENT_VALUE', element)
          errors.append(error)
      # end for
      if errors: return errors

    # if specified, make sure that all elements are either optional or required
    if self.known_elements != None:
      errors = []
      for element_index in range(len(value)):
        element = value[element_index]
        if element not in self.known_elements:
          error = ValidationError("Unknown entry for %s" % str(element))
          error.addAttrib('ELEMENT', element_index)
          errors.append(error)
      # end for
      if errors: return errors

    return VALID_OK

class Map(Type):
  """A map; applies specified key and value validators;
  optional size and required keys contraint"""

  # default_key_validator: if != None, each key will be validated against this
  # default_val_validator: if != None, each value (for which val_validator_map
  #                        doesn't define a validator) will be validated by
  #                        this
  # min_size/max_size: size constraints on map
  # required_keys: if given, map must contain all of these keys
  # val_validator_map: if given, will be a map from key to validator; if a
  #                    validator exists for a key, this will be used instead of
  #                    default_val_validator
  # key_set_validator: if given, value.keys() will be validated against this
  def __init__(self, default_key_validator, default_val_validator, nullOK = 0,
               min_size = None, max_size = None,
               required_keys = None,
               optional_keys = None,
               allow_unknown_keys = 1,
               val_validator_map = None,
               key_set_validator = None):
    Type.__init__(self, Type.MAP_EXEMPLAR, nullOK=nullOK)
    self.doc = "(nullOK = %d, default_key_validator = %s, default_value_validator = %s, min_size = %s, max_size = %s, required_keys = %s, optional_keys = %s, allow_unknown_keys = %d, val_validator_map = %s, key_set_validator = %s)" % (nullOK, repr(default_key_validator), repr(default_val_validator), str(min_size), str(max_size), str(required_keys), str(optional_keys), allow_unknown_keys, str(val_validator_map), str(key_set_validator) )

    # construct a list of known keys (besides required_keys):
    known_keys = []
    if optional_keys != None: known_keys.extend(optional_keys)
    if val_validator_map != None: known_keys.extend(val_validator_map.keys())

    self.keyv = RestrictedList(default_key_validator,
                               min_size=min_size,
                               max_size=max_size,
                               required_elements=required_keys,
                               optional_elements=known_keys,
                               allow_unknown_elements=allow_unknown_keys)
    self.key_set_validator = key_set_validator
    self.val_validator_map = val_validator_map
    self.default_val_validator = default_val_validator

  def _ReattributeErrors(self, errors, map_keys):
    # reattribute all errors to their keys, instead of their element numbers
    if errors in VALID_CODES: return errors

    for error in errors:
      # if error has ELEMENT element attrib, change it to KEY attrib
      if error.attribs.has_key('ELEMENT'):
        # element index is the offset in map_keys; map this back to key
        key_index = error.attribs['ELEMENT']
        if key_index >= 0 and key_index < len(map_keys):
          error.addPathAttrib('KEY', str(map_keys[key_index]))
          del error.attribs['ELEMENT']
        # end if
      elif error.attribs.has_key('ELEMENT_VALUE'):
        # element value is the value of the offending element (i.e. key)
        key = error.attribs['ELEMENT_VALUE']
        error.addPathAttrib('KEY', str(key))
        del error.attribs['ELEMENT_VALUE']
    return errors

  def validate(self, value, context):
    r = Type.validate(self, value, context)
    if VALID_OK != r: return r

    # run the key validator on value's keys
    map_keys = value.keys()
    r = self.keyv.validate(map_keys, context)
    if VALID_OK != r: return self._ReattributeErrors(r, map_keys)

    if self.key_set_validator != None:
      r = self.key_set_validator.validate(map_keys, context)
      if VALID_OK != r: return self._ReattributeErrors(r, map_keys)

    # now check constraints on the values themselves
    max_errors = context.max_errors()
    all_errors = []

    for (key, val) in value.items():
      val_validator = None
      # first, look in val_validator_map
      if self.val_validator_map != None:
        val_validator = self.val_validator_map.get(key, None)
      # if not found, try the default_val_validator
      if val_validator == None:
        val_validator = self.default_val_validator

      # if found, use it
      if val_validator != None:
        val_errors = val_validator.validate(val, context)
        if val_errors not in VALID_CODES:
          for error in val_errors: error.addPathAttrib('KEY', str(key))
          all_errors.extend(val_errors)

      if len(all_errors) > max_errors:
        break

    # if there were any errors, return them
    if all_errors: return all_errors
    else:          return VALID_OK

class SeparatedList(String):
  """A token seperated list; applies another validator to each element.
  The separator is a regular expression"""
  def __init__(self, validator, separator, nullOK = 0,
               min_size = None, max_size = None, eq_size = None):
    emptyOK = min_size in [0, None] and eq_size in [0, None]
    String.__init__(self, nullOK = nullOK, emptyOK = emptyOK)

    self.doc = "(validator = %s, separator = %s, nullOK = %d, min_size = %s, max_size = %s, eq_size = %s)" % (repr(validator), repr(separator), nullOK, repr(min_size), repr(max_size), repr(eq_size))

    # build a List validator from the supplied validator
    self.list_validator = List(validator, min_size = min_size,
                               max_size = max_size, eq_size = eq_size)

    # make sure separator is valid
    assert(type(separator) == types.StringType and len(separator) > 0)
    self.separator = separator

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # split the value into a list, making sure the empty string ends up as
    # the [] instead of [""]
    if len(value) == 0:
      parts = []
    else:
      parts = re.split(self.separator, value)

    # run a List Validator to validate each sub-string
    return self.list_validator.validate(parts, context)

class CommaList(SeparatedList):
  """A comma seperated list; applies another validator to each element"""
  def __init__(self, validator, nullOK = 0, **args):
    apply(SeparatedList.__init__, (self, validator, ',', nullOK), args)


# used by CSVLine
csv_re = re.compile('(\s*"([^"]|"")*"\s*)|([^",][^,]*)')
def CSVParse(line):
  fields = []
  pos = 0
  while 1:
    match = csv_re.match(line, pos)
    if match:
      field = line[match.start():match.end()]
      field = string.strip(field)
      if len(field) > 0 and field[0] == '"':
        field = field[1:-2]
        field = string.replace(field,'""','"')
      fields.append(field)
      pos = match.end()
    else:
      fields.append("")
    if pos >= len(line):
      return fields
    elif line[pos] != ',':
      return None #error
    pos = pos + 1

class CSVLine(String):
  """A list of (CSV) Comma Separated Values """
  def __init__(self, validators, nullOK = 0):
    String.__init__(self, nullOK = nullOK)
    self.validators = validators

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    parts = CSVParse(value)
    if parts == None:
      return [ ValidationError("Parse error on CSV Line") ]
    if len(parts) != len(self.validators):
      return [ ValidationError("Incorrect number of fields") ]

    all_errors = []
    for field in range(len(parts)):
      if self.validators[field] != None:
        errors = self.validators[field].validate(parts[field], context)
      if errors not in VALID_CODES:
        for error in errors: error.addAttrib('ELEMENT', field)
        all_errors.extend(errors)
    if len(all_errors) > 0:
      return all_errors

    return VALID_OK

class MetatagLine(CSVLine):
  def __init__(self):
    self.tipes = ['REQUIREDFIELDS','PARTIALFIELDS','EXISTENCE']
    CSVLine.__init__( self,
                      [ Set(['AND','OR']),    # operation on all filters
                        Set(self.tipes),      # type of filter
                        String(emptyOK=0),    # name of metatag
                        String(emptyOK=1) ] ) # value of metatag

  def validate(self, value, context):
    # Basic CSV validation
    r = CSVLine.validate(self, value, context)
    if r != VALID_OK: return r

    parts = CSVParse(value)
    if ( parts[1].upper() == self.tipes[2] ) and ( len(parts[3]) > 0 ):
      return [ ValidationError("Value not required when only checking for existence of tag",
                                ERR_METATAG_EXIST_ONLY) ]

    if ( parts[1].upper() != self.tipes[2] ) and ( len(parts[3]) == 0 ):
      return [ ValidationError("Metatag value field is required for comparision",
                                ERR_METATAG_NO_VALUE_TO_MATCH) ]

    return VALID_OK

class FileExtension(String):
    """A file extension such as doc pdf with optional preceding period. If
       optionalPeriod, then period is optional. Otherwise wantPeriod is used
       to determine if a period should exist or not"""
    def __init__(self, optionalPeriod = 1, wantPeriod = 1):
      String.__init__(self, nullOK = 0, emptyOK = 0)
      self.doc = "(optionalPeriod = %d, wantPeriod = %d)" % (optionalPeriod, wantPeriod)
      self.optionalPeriod = optionalPeriod
      self.wantPeriod = wantPeriod

    def validate(self, value, context):
      r = String.validate(self, value, context)
      if VALID_OK != r: return r

      # check for invalid characters. Though windows, excludes a few
      # characters, unix/linux takes any character except a forward slash.
      if string.find(value, "/") >= 0:
        return [ ValidationError("Cannot contain '/'", ERR_FILE_EXT_HAS_SLASH) ]

      # Where is the period?
      period = string.rfind(value, ".")
      if period > 0:
        return [ ValidationError("Cannot have period in the middle", ERR_FILE_EXT_PERIOD_IN_MIDDLE) ]

      havePeriod = (period >= 0)

      if not self.optionalPeriod:
        if self.wantPeriod and not havePeriod:
          return [ ValidationError("Must start with a period", ERR_FILE_EXT_MUST_START_WITH_PERIOD) ]

        if not self.wantPeriod and havePeriod:
          return [ ValidationError("Cannot have the starting period", ERR_FILE_EXT_CANT_START_WITH_PERIOD) ]

      if havePeriod and (len(value) == 1):
        return [ ValidationError("No extension specified", ERR_FILE_EXT_NONE_SPECIFIED) ]

      # All ok!
      return VALID_OK

class Filename(String):
  """A file (or directory) name; must be absolute (by default)"""
  def __init__(self, isDir = 0, nullOK = 0, emptyNameOK = 0, absolute = 1):
    String.__init__(self, nullOK = nullOK, emptyOK = emptyNameOK)
    self.doc = "(isDir = %d, nullOK = %d, emptyNameOK = %d, absolute = %d)" % (isDir, nullOK, emptyNameOK, absolute)
    self.absolute = absolute
    self.isDir = isDir

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # make sure filename is absolute
    if self.absolute and not os.path.isabs(value):
      return [ValidationError("Filename not absolute")]

    # normal files shouldn't end with /
    if (not self.isDir) and (value[-1] == "/"):
      return [ValidationError("Filename ends with slash")]

    return VALID_OK

class BaseFile(Filename):
  """A base class used for File and Dir Validators; accesses files to
  check for permissions, existance, etc.."""
  def __init__(self, isDir, nullOK = 0, emptyNameOK = 0, nonEmptyFile = 0,
               perms = 0, uid=None, gid=None):
    Filename.__init__(self, isDir = isDir, nullOK = nullOK,
                      emptyNameOK = emptyNameOK, absolute = 1)
    self.doc = "(isDir = %d, nullOK = %d, emptyNameOK = %d, nonEmptyFile = %d, perms = %03.o)" % (isDir, nullOK, emptyNameOK, nonEmptyFile, perms)
    self.isDir = isDir
    self.nonEmptyFile = nonEmptyFile
    self.perms = perms
    self.uid = uid
    self.gid = gid

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check if we're allowed to access file context.  if not, we short
    # circuit, since all the remaining constraints depend on file access
    if not context.file_access(): return VALID_SHORT_CIRCUIT

    # perform context file mapping, if supported
    file = context.file_mapping(value)

    # If the actual file validation is disabled, we are fine
    if is_file_validation_disabled():
      return VALID_OK

    errs = []

    # make sure file exists
    if not os.path.exists(file):
      # if the file doesn't exist, we should quit
      return [ ValidationError("File must exist") ]

    if self.isDir:
      # make sure it's a directory
      if not os.path.isdir(file):
        errs.append(ValidationError("Must be directory"))
      # end if
    else:
      # make sure it's not a directory
      if os.path.isdir(file):
        errs.append(ValidationError("Must not be directory"))

    # if specified, check for appropriate uid/gid
    # we can't use 'if not self.uid' because 0 is a valid uid
    if self.uid is not None or self.gid is not None:
      # we should be able to stat files OK here, but just in case there's a problem
      # we trap OSError
      filestat = None

      try:
        filestat = os.stat(file)
      except OSError, e:
        errs.append(
          ValidationError("Unknown error while running stat: %s" % str(e)))

      if filestat and self.uid is not None:
        if filestat[STAT_ST_UID] != self.uid:
          errs.append(ValidationError("File has the wrong owner",
                                      ERR_CODE = ERR_FILE_WRONG_OWNER))

      if filestat and self.gid is not None:
        if filestat[STAT_ST_GID] != self.gid:
          errs.append(ValidationError("File has the wrong group",
                                      ERR_CODE = ERR_FILE_WRONG_GROUP))

    # check required permissions on file
    if not os.access(file, self.perms):
      errs.append(ValidationError("File must have permissions %03.o" % self.perms))
      return errs

    # only if we have access.
    if self.nonEmptyFile and os.path.getsize(file) <= 0:
      # if specified, make sure file is non empty
      errs.append(ValidationError("File must be non-empty",
                                  ERR_CODE = ERR_FILE_EMPTY))

    if errs:
      return errs

    return VALID_OK

class File(BaseFile):
  """A file; must exist; optional permission and emptiness constraints"""
  def __init__(self, nullOK = 0, emptyNameOK = 0, nonEmptyFile = 0, perms = 0,
               uid = None, gid = None):
    # _always_ required read access
    perms = perms | os.R_OK
    BaseFile.__init__(self, isDir = 0, nullOK = nullOK,
                      emptyNameOK = emptyNameOK,
                      nonEmptyFile = nonEmptyFile,
                      perms = perms, uid=uid, gid=gid)

class Dir(BaseFile):
  """A directory; must exist; optional permission constraints"""
  def __init__(self, nullOK = 0, emptyNameOK = 0, perms = 0,
               uid=None, gid=None):
    # _always_ required read and execute access
    perms = perms | os.R_OK | os.X_OK
    BaseFile.__init__(self, isDir = 1, nullOK = nullOK,
                      emptyNameOK = emptyNameOK, nonEmptyFile = 0,
                      perms = perms, uid=uid, gid=gid)


class FileLine(File):
  """A line-oriented file; applies another validator to each line;
  ignores comments and blank lines"""

  def __init__(self, validator, nullOK = 0, emptyNameOK = 0, nonEmptyFile = 0,
               perms = 0, uid=None, gid=None):
    File.__init__(self, nullOK = nullOK, emptyNameOK = emptyNameOK,
                  nonEmptyFile = nonEmptyFile, perms = perms, uid=uid, gid=gid)
    self.doc = ("(validator = %s, nullOK = %d, emptyNameOK = %d, "
                "nonEmptyFile = %d, perms = %03.o, uid=%s, gid=%s)" %
                (repr(validator), nullOK, emptyNameOK, nonEmptyFile, perms,
                 uid, gid))
    self.validator = validator
    self.nonEmptyFile = nonEmptyFile

  def validate(self, value, context):
    r = File.validate(self, value, context)
    if VALID_OK != r: return r

    # If the actual file validation is disabled, we are fine
    if is_file_validation_disabled():
      return VALID_OK

    # perform context file mapping
    value = context.file_mapping(value)
    max_errors = context.max_errors()

    # Open the file.
    try:
      file = open(value, 'r')
    except IOError:
      return [ ValidationError("Can't open file") ]

    all_errors = []

    line_num = 0
    good_lines = 0
    while 1:
      # read in a bunch of lines (up to 1 MB)
      some_lines = file.readlines(1024*1024)
      if not some_lines: break

      # process each line
      for line in some_lines:
        line_num = line_num + 1
        if (context.fileline_limit() != -1 and
            line_num > context.fileline_limit()):
          break   # we have checked enough lines


        # skip comments and empty lines
        if len(string.rstrip(line)) == 0 or line[0] == '#':
          continue

        # strip newlines (\n and \r\n)
        if line[-1:] == '\n':
          end = -1
          if line[-2:-1] == '\r':
            end = -2
          line = line[:end]

        # run the validator
        errors = self.validator.validate(line, context)
        if errors in VALID_CODES:
          # keep track of how many good lines we've seen
          good_lines = good_lines + 1
        else:
          # mark each error with it's line number
          for error in errors: error.addAttrib('LINE', line_num)
          all_errors.extend(errors)

        # if we've seen too many errors, stop trying
        if len(all_errors) > max_errors: break

    file.close()

    # if we saw any errors, we failed
    if len(all_errors) > 0:
      return all_errors

    # if the file was non empty, but we didn't see any good lines, we fail
    # this can happen if the file is all comments and empty lines
    if self.nonEmptyFile and good_lines == 0:
      empty_error = ValidationError("File must be non-empty",
                                    ERR_CODE = ERR_FILE_EMPTY);
      return [ empty_error ]

    return VALID_OK

# Utility function to determine wheter a hostname is fully qualified,
# using the following heuristic:
#  1. There must be at least one dot in the hostname, excluding the last
#     character. (optional now, smb://server/ is a valid name)
#  2. There can't be two consecutive dots, leading dots, or more than one
#     trailing dot.
whiteSpace = re.compile('\s')
digitsAndDots = re.compile('^[\d.]+$')
def isFQDN(host, mustHaveDot = 1):
  # check for whitespace
  if whiteSpace.search(host):  return 0

  # make sure this doesn't look like an IP address
  if digitsAndDots.match(host): return 0

  # allow one trailing dot (strip it)
  if host[-1:] == '.':
    host = host[:-1]

  parts = string.split(host, '.')

  # if there were no dots, failure
  if mustHaveDot and (len(parts) < 2): return 0

  # check for consecutive, leading, and trailing dots
  for part in parts:
    if len(part) == 0: return 0

  return 1

# Utility function to determine if a string is a valid IP address.
def isValidIP(ip):
  # check for whitespace
  if whiteSpace.search(ip):  return 0

  octets = string.split(ip, '.')  # split into octets
  if len(octets) != 4: return 0   # make sure there are 4 octets

  try:                            # make sure each is a valid int value
    int_values = map(string.atoi, octets)
  except ValueError:
    return 0

  for octet in int_values:        # make sure each is 0 >= x <= 255
    if octet < 0 or octet > 255: return 0

  return 1


class Hostname(String):
  """A hostname; optional FQDN-ness and DNS constraints"""

  # FQDN can be either 1 (yes), 0 (no), or None (don't care).
  def __init__(self, nullOK = 0, FQDN = 1, resolveDNS = 0, allowIP = 0,
               emptyOK = 0):
    String.__init__(self, nullOK = nullOK, emptyOK = emptyOK)
    self.doc = ("(nullOK = %d, FQDN = %s, resolveDNS = %d, allowIP = %d)"
                % (nullOK, str(FQDN), resolveDNS, allowIP))
    self.allowIP = allowIP
    assert FQDN in (0,1,None)
    self.FQDN = FQDN
    self.resolveDNS = resolveDNS

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check for whitespace
    if whiteSpace.search(value):
      return [ValidationError("Contains whitespace")]

    if digitsAndDots.match(value):
      if not self.allowIP:
        return [ ValidationError('Invalid hostname') ]
      elif isValidIP(value):
        return VALID_SHORT_CIRCUIT
      else:
        return [ ValidationError('Invalid IP Address') ]

    if self.FQDN == 1 and not isFQDN(value):
      return [ ValidationError("Not fully qualified hostname") ]
    if self.FQDN == 0 and -1 != string.find(value, "."):
      return [ ValidationError("Contains a dot") ]

    if self.resolveDNS and context.dns_access():
      try:
        socket.gethostbyname(value)
      except:
        return [ ValidationError("Host not found") ]

    return VALID_OK

class SiteName(String):
  """
  A value that can be given to site: parameter. Examples are
    google.com            ;cannot have trailing slash
    www.google.com/test   ;optional trailing slash. Name must be fully qualified
  """
  def __init__(self, pathOK = 1):
    String.__init__(self, nullOK = 0, emptyOK = 0)
    self.pathOK = pathOK

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # Break into two parts around the first '/'.  First part is host name and
    # second part is a directory
    parts = value.split('/', 1)

    # Validate host
    url = Hostname()
    r = url.validate(parts[0], context)
    if r != VALID_OK: return r

    # Validate directory, if specified
    if len(parts) == 1:
      return  VALID_OK    # no directory specified

    if not self.pathOK:
      return [ ValidationError("Cannot have path", ERR_SITENAME_CANT_HAVE_PATH) ]

    if len(parts[1]) == 0:
        return [ ValidationError("Cannot have trailing '/' unless path is specified") ]

    if parts[1].startswith("/") or parts[1].find("//") > 0:
      return [ ValidationError("Contains //") ]

    return VALID_OK

class URL(String):
  """A well-formed URL"""
  def __init__(self, nullOK = 0, emptyOK = 0):
    String.__init__(self, nullOK = nullOK, emptyOK = emptyOK)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    if whiteSpace.search(value):
      return [ ValidationError("Contains Whitespace") ]

    parsedurl = pywrapurl.URL(value)
    proto = parsedurl.protocol()
    netloc = parsedurl.host()
    path = parsedurl.path()
    netloc_start = string.find(value, "://")
    if netloc_start > 0:
      netloc_start = netloc_start + 3 # move past ://
      colon = string.find(value, ":", netloc_start)
      netloc_end = string.find(value, "/", netloc_start)
      if colon > 0 and (-1 == netloc_end or netloc_end > colon):
        # google2 URL class ignores invalid ports, so append the port to
        # the netloc so we check it below
        netloc = netloc + value[colon:netloc_end]
      # end if
    else:
      (proto, netloc, path, _, _, _) = urlparse.urlparse(value)

    if len(proto) == 0:
      return [ ValidationError("No protocol in URL",
                               ERR_CODE = ERR_URL_NO_PROTOCOL) ]
    if len(netloc) == 0:
      return [ ValidationError("No host in URL",
                               ERR_CODE = ERR_URL_NO_HOST) ]
    if len(path) == 0:
      return [ ValidationError("No path in URL",
                               ERR_CODE = ERR_URL_NO_PATH) ]

    # after the first @, or the beginning of the string if it doesn't exist
    host_start = string.find(netloc, '@') + 1

    # see if there is a port after the host, look for :
    port_start = string.find(netloc, ':', host_start)
    if port_start >= 0:
      try:
        string.atoi(netloc[port_start+1:])
      except:
        return [ ValidationError("Invalid port in URL") ]
    else:
      port_start = len(netloc)

    # smb://, nfs:// and unc:// urls need not have a dot in their host name
    # smb://share/ is valid url, for example
    dotNeeded = proto not in ("smb", "nfs", "unc", "file")

    host = netloc[host_start:port_start]
    if not isFQDN(host, dotNeeded) and not isValidIP(host):
      return [ ValidationError("Host(%s) must be fully qualified" % host,
                               ERR_CODE = ERR_HOST_NOT_FULLY_QUALIFIED) ]

    return VALID_OK

class EmailAddress(String):
  """An email address"""

  def __init__(self, nullOK = 0, qualifiedHost = 1):
    String.__init__(self, nullOK = nullOK, emptyOK = 0)
    self.qualifiedHost = qualifiedHost

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check for whitespace
    if whiteSpace.search(value):
      return [ ValidationError("Contains Whitespace") ]

    parts = string.split(value, '@')
    if len(parts) != 2:
      return [ ValidationError("Invalid email address") ]

    (user, host) = parts
    if len(user) == 0 or len(host) == 0:
      return [ ValidationError("Invalid email address") ]

    if self.qualifiedHost and not isFQDN(host):
      return [ ValidationError("Host must be fully qualified",
                               ERR_CODE = ERR_HOST_NOT_FULLY_QUALIFIED) ]

    return VALID_OK

class URLOrURLFile(OrMeta):
  """A Url or a file of Urls"""
  def __init__(self, nullOK = 0, nonEmptyFile = 0):
    OrMeta.__init__(self, [URL(),
                           FileLine(URL(), nonEmptyFile = nonEmptyFile) ],
                    nullOK = nullOK)

class URLCommaListOrURLFile(OrMeta):
  """A Url or a file of Urls"""
  def __init__(self, nullOK = 0, nonEmptyFile = 0):
    OrMeta.__init__(self, [CommaList(URL(), nullOK = nullOK),
                           FileLine(URL(),
                                    nonEmptyFile = nonEmptyFile) ],
                    nullOK = nullOK)

class GoogleProductionMachine(Hostname):
  """A google production machine; optional DNS and datacenter (prefix) constraints"""
  def __init__(self, nullOK = 0, resolveDNS = 0, emptyOK = 0):
    Hostname.__init__(self, nullOK, FQDN = 0, resolveDNS = resolveDNS,
                      emptyOK = emptyOK)

  def validate(self, value, context):
    r = Hostname.validate(self, value, context)
    if VALID_OK != r: return r

    if not context.has_valid_machine_prefix(value):
      return [ ValidationError("Host has an invalid prefix") ]
    return VALID_OK

class PortNum(Int):
  """A TCP port number; must be an integer in a valid range"""
  def __init__(self, nullOK = 0, minPort = 1024, maxPort = 65536):
    Int.__init__(self, GTE=minPort,LTE=maxPort, nullOK=nullOK)

class PseudoPortNum(Int):
  """A google server port number; a superset of valid TCP port numbers"""
  def __init__(self, nullOK = 0, minPort = 1024, maxPort = 600000):
    # TODO: google servers also listen on port 80.  How do we
    # add an OR clause here to allow that exception.
    Int.__init__(self, GTE=minPort,LTE=maxPort, nullOK=nullOK)

class DevNullOrDir(OrMeta):
  """A directory or /dev/null"""
  def __init__(self, nullOK = 0):
    OrMeta.__init__(self, [String(EQ="/dev/null"), Dir()], nullOK = nullOK )

class DocId(Int):
  """A DocId; must be an integer in a valid range"""
  def __init__(self, nullOK = 0):
    Int.__init__(self, nullOK = nullOK, GTE=0, LT=2147483647)

class FloatPercent(Float):
  """A float between 0.0 and 1.0"""
  def __init__(self, nullOK = 0):
    Float.__init__(self, nullOK = nullOK, GTE=0.0, LTE=1.0)

class IPAddress(String):
  """An IP address"""
  def __init__(self, nullOK = 0, emptyOK = 0):
    String.__init__(self, nullOK = nullOK, emptyOK = emptyOK)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    if not isValidIP(value):
      return [ ValidationError("Invalid IP") ]

    return VALID_OK

class IPNetmask(IPAddress):
  """An IP netmask"""
  def __init__(self, nullOK = 0):
    IPAddress.__init__(self, nullOK = nullOK)

  def validate(self, value, context):
    r = IPAddress.validate(self, value, context)
    if VALID_OK != r: return r

    octets = map(int, string.split(value, '.'))  # split into octets
    zeros = 0  # have we seen a zero bit yet?
    for octet in octets:
      for bit in range(8):
        if octet & (128 >> bit) == 0:  # a 0 bit
          zeros = 1
        elif zeros: # a 1 bit
          return [ ValidationError("Invalid netmask") ]

    return VALID_OK

class IPAddressMask(String):
  """An IP address mask (ipaddress/bits) (ex 10.0.0.0/8) """
  def __init__(self, nullOK = 0):
    String.__init__(self, nullOK = nullOK)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    comp = string.split(value, "/")
    if len(comp) != 2:
      return [ ValidationError("The ipadressmask has form x.x.x.x/x") ]
    if not isValidIP(comp[0]):
      return [ ValidationError("Invalid ip in ipadressmask") ]
    try:
      bits = int(comp[1])
    except ValueError:
      return [ ValidationError("Bit number should be an int in ipadressmask") ]

    if bits < 0 or bits > 32:
      return [ ValidationError("Number of bits has to be between 0 and 32") ]

    return VALID_OK

# CachedUrlMatcher and CachedDupHostDB provide a simple way to reuse
# UrlMatcher and DuplicateHostDB objects between calls to validators.  This is
# important because they are both swig wrapped C++ objects, and called once for
# each line in urlpattern/duphost files, so we want to reuse them to avoid
# creating one for each line.  We need to clear the objects once in a while to
# avoid a memory leak.
class CachedUrlMatcher:
  def __init__(self, limit):
    self.obj = None
    self.count = 0
    self.limit = limit

  def get(self):
    self.obj = pywrapurlmatch.UrlMatcher("", 0)

    if self.count > self.limit:
      self.obj.Reload()
      self.count = 0
    self.count = self.count + 1
    return self.obj

class CachedDupHostDB:
  def __init__(self, limit):
    self.obj = pywrapduphosts.CreateDuplicateHostDB()
    self.count = 0
    self.limit = limit

  def get(self):
    if self.count > self.limit:
      self.obj.Reload()
      self.count = 0
    self.count = self.count + 1
    return self.obj


UrlPatternMatcher = None
class URLPattern(String):
  """A URL pattern"""
  def __init__(self, allowComments = 1, allowSlash=0, nullOK = 0, emptyOK = 0):
    String.__init__(self, nullOK = nullOK, emptyOK = emptyOK)
    self.allowComments = allowComments
    self.allowSlash = allowSlash

    global UrlPatternMatcher
    if not UrlPatternMatcher: UrlPatternMatcher = CachedUrlMatcher(1000)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check for \0 in line, because swig expects null terminated lines
    if string.find(value, '\0') != -1:
      return [ ValidationError("Invalid character") ]

    # we allow trailing whitespace
    line = string.rstrip(value)

    # split on the first occurance of whitespace
    parts = re.split('\s+', line, 1)
    pattern = parts[0]

    if len(parts) > 1:   # everything after the whitespace is a comment
      comment = parts[1]

      # make sure the comment starts with #
      if comment[:1] != '#':
        return [ ValidationError("Contains Whitespace") ]

      # if there are only spaces before '#', then it is OK
      if parts[0] == '':
        return VALID_OK

      # see if comments are allowed
      if not self.allowComments:
        return [ ValidationError("Comments not allowed after pattern") ]

    # all of these match everything
    if not self.allowSlash and pattern in ['/', '*/', ':*/']:
      return [ ValidationError("Single slash not allowed") ]

    if pattern[:1] == '-':
      pattern = pattern[1:];

    if pattern[:9] != 'contains:' and \
       pattern[:7] != 'regexp:' and \
       pattern[:11] != 'regexpCase:' :
      # check for backslash escapes
      if string.find(pattern, '\\') != -1 and string.find(pattern, '\\\\') == -1:
        return [ ValidationError("Backward slash escapes not allowed") ]

      # check for slash
      if pattern[:1] != '^' and pattern[-1:] != '$' and string.find(pattern, '/') == -1:
        return [ ValidationError("Nonanchored pattern with no slash",
                                 ERR_CODE = ERR_URLPATTERN_NONANCHORED) ]

    # check with the matcher
    if not UrlPatternMatcher.get().Insert(line):
      return [ ValidationError("Invalid URL pattern") ]

    return VALID_OK

class EnterpriseURLPattern(URLPattern):
  """A URL pattern; no comments allowed after patterns"""

  def __init__(self, allowSlash=0):
    URLPattern.__init__(self, allowComments=0, allowSlash=allowSlash)


class EnterpriseMetadata(String):
  """A metadata name:value pair; no spaces allowed"""

  def __init__(self):
    String.__init__(self)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if r != VALID_OK:
      return r

    # there should be at least one colon sign to delimit name from content
    first_colon = value.find(":")
    if first_colon == -1:
      return ValidationError("No colon sign found in metadata")

    # there should not be two colon signs in the metadata information
    if value.find(":", first_colon+1) != -1:
      return ValidationError("More than one colon sign found in metadata")

    name, content = value.split(":", 2)

    # constraints on name
    if 0 == len(name):
      return ValidationError("Metadata name is empty")
    if name.find(" ") != -1:
      return ValidationError("Metadata name contains whitespace(s)")

    # constraints on content
    if 0 == len(content):
      return ValidationError("Metadata content is empty")
    if content.find(" ") != -1:
      return ValidationError("Metadata content contains whitespace(s)")

    # everything was ok
    return VALID_OK


DupHostEntryDB = None
class DupHostEntry(String):
  """A duphosts entry"""
  def __init__(self, allowWildcards=1, qualifiedHosts=0):
    String.__init__(self)
    self.allowWildcards = allowWildcards
    self.qualifiedHosts = qualifiedHosts
    self.doc = "(allowWildcards = %d, qualifiedHosts = %d)" % (allowWildcards,
                                                               qualifiedHosts)

    global DupHostEntryDB
    if not DupHostEntryDB: DupHostEntryDB = CachedDupHostDB(1000)

  def validate(self, value, context, canonicalHostOnly=0):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check for comments in the line
    if -1 != string.find(value, "#"):
      return [ ValidationError("Comments not allowed after entry") ]

    # check for \0 in line, because swig expects null terminated lines
    if -1 != string.find(value, "\0"):
      return [ ValidationError("Invalid character") ]

    # check that this a valid duphost entry
    # note that DupHostDB.Insert() will modify the string, so we make a copy
    if not DupHostEntryDB.get().Insert("%s" % value):
      return [ ValidationError("Invalid duphost entry") ]

    # Additional constraints:
    if not self.allowWildcards and -1 != string.find(value, "*"):
      return [ ValidationError("No wildcards allowed in entry") ]

    if self.qualifiedHosts:
      # make sure each entry is an IP or fully qualified hostname
      i = 0
      for host in string.split(value):
        i = i + 1
        if len(host) > 0 and not isFQDN(host) and not isValidIP(host):
          e = ValidationError("Host must be IP or fully qualified host")
          e.addAttrib('NUM', i)
          return [ e ]
        if canonicalHostOnly:
          break

    return VALID_OK


class SsoCookiePatternEntry(URLPattern):
  """A URL pattern with Cookie credentials entry"""

  def __init__(self, allowComments=1, allowSlash=1, emptyOK=1, **args):
    apply(URLPattern.__init__, (self, allowComments,
                                allowSlash, emptyOK), args)
    self.regex = re.compile(
      '^(?P<pattern>\S*)\s+(?P<duration>[\d]+)\s+(?P<public>[01])\s+' +
      '(\<\s*(?P<url>\S+)\s+(?P<method>[a-zA-Z]+)(\s+' +
      '(?P<name>[^\s=;,]+)=(?P<value>[^\s;,]*))*\s*\>)+\s*')

  def validate(self, value, context):
    if value == "" or value.strip()[0] =="#":
      return VALID_OK
    matchObj = self.regex.match(value)
    if not matchObj:
      return [ ValidationError("Doesn't match")]
    r = URLPattern.validate(self, matchObj.group('pattern'), context)
    if r != VALID_OK: return r
    return VALID_OK

class SsoServingEntry(String):
  """An SSO serving entry"""
  def __init__(self, emptyOK=1):
    String.__init__(self, emptyOK)
    self.regex = re.compile('^\d+[smh]$')

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if len(value) == 0:
      return VALID_OK

    if VALID_OK != r: return r
    parts = value.split(' ')
    if len(parts) != 4:
      return [ ValidationError("Insufficient number of fields in SSO serving record.")]

    alwaysRedir = parts[3]
    if alwaysRedir != "0" and alwaysRedir != "1":
      return [ ValidationError("Invalid value for alwaysRedirect bit., bit =" + parts[3])]

    if alwaysRedir =='0' and len(parts[0]) > 0:
      url = URL()
      r = url.validate(parts[0], context)
      if r != VALID_OK: return r

    if alwaysRedir == '1':
      url2 = URL()
      r = url2.validate(parts[1], context)
      if r != VALID_OK: return r

    method = parts[2].upper()
    if method != "GET" and method != "POST":
      return [ ValidationError("Unknown HTTP method found:" + method)]

    return VALID_OK

class EnterpriseDupHostEntry(DupHostEntry):
  """A duphosts entry; no wildcards allowed; all hosts must be FQDN"""
  def __init__(self):
    DupHostEntry.__init__(self, allowWildcards=0, qualifiedHosts=1)

  def validate(self, value, context):
    return DupHostEntry.validate(self, value, context , 1)

class HostLoad(String):
  """A hostload entry"""

  NORMAL_RE = re.compile("^(\S+)\s+(\S+)\s*$")
  ABSOLUTE_RE = re.compile("^ABSOLUTE\s+(\S+)\s+(\S+)\s*$")
  # the timerange format is a little more involved
  # Basically we need to validate all timeranges.
  # Plus we need to ensure that no two timeranges are conflicting for a host
  # this checks the oeverall syntax of the timerange line
  TIMES_RE1 = re.compile("^(\S+)\s+(\[tz:\d+\-\d+:\S+\]\s*)+$")
  # this extracts one particular timerange definition
  TIMES_RE2 = re.compile("^\[tz:(\d+)\-(\d+):(\S+)\]\s*")

  def __init__(self, allowAbsolute=1, allowTimeRange=1, qualifiedHosts=0,
      nullOK=0, allowWildCard=0):
    String.__init__(self, nullOK=nullOK)
    self.doc = "(nullOK = %d, allowAbsolute = %d, allowTimeRange = %d, " \
               "qualifiedHosts = %d, allowWildCard = %d)" % (nullOK,
               allowAbsolute, allowTimeRange, qualifiedHosts, allowWildCard)
    self.qualifiedHosts = qualifiedHosts
    self.allowWildCard = allowWildCard

    self.patterns = []
    if allowAbsolute: self.patterns.append( self.ABSOLUTE_RE )
    self.allowTimeRange_ = allowTimeRange
    # add this last since the pattern is very general and will also match
    # hostload_times lines
    self.patterns.append( self.NORMAL_RE )

    # Make sure wild card is before any other entry
    self.seen_entry = 0

  # validates the host part
  def validateHost(self, host):
    if self.allowWildCard and host == '*':
      return None
    if digitsAndDots.match(host):
      if not isValidIP(host):
        return [ ValidationError("Invalid IP address %s" % host,
                                 ERR_CODE = ERR_BAD_IP) ]
      # end if
    elif self.qualifiedHosts:
      if not isFQDN(host):
        return [ ValidationError("Host %s must be fully qualified" % host,
                                 ERR_CODE = ERR_HOST_NOT_FULLY_QUALIFIED) ]
    return None

  def validateLoad(self, load):
    # make sure load is a valid number
    try:
      float(load)
    except:
      return [ ValidationError("Invalid hostload value %s" % repr(load)) ]
    return None

  # makes sure that the hour lies between appropriate values
  def validateHour(self, hour):
    try:
      hour = int(hour)
      if hour < 0 or hour >= 24:
        return [ ValidationError("Invalid Hour %d" % hour) ]
    except:
      return [ ValidationError("Invalid Hour %s" % hour) ]
    return None

  # It tests if the line matches the timerange syntax.
  # it also validates each timerange defintion and checks
  # for conflicting overlaps
  # Returns an non-empty list if some error occurs
  # Returns empty list if things dont match
  # Returns None on success.
  def validateTimeRange(self, value):
    matches = self.TIMES_RE1.match(value)
    if not matches:
      return []
    (host,_) = matches.groups()
    if host == None:
      return [ ValidationError("Invalid hostload entry %s" % value,
                               ERR_CODE = ERR_BAD_HOST) ]
    error = self.validateHost(host)
    if error:
      return error
    hlstrings = string.split(value, ' ')[1:]
    # set up all the hours, this is to check conflicting overlaps
    loads_ = []
    for i in range(24):
      loads_.append(-1)
    for hlstring in hlstrings:
      if not hlstring: continue
      matches = self.TIMES_RE2.match(hlstring)
      if not matches:
        hlErr = ValidationError("Invalid hostload entry %s" % value,
                                ERR_CODE = ERR_BAD_HOSTLOAD_ENTRY)
        hlErr.addAttrib("ENTRY", value)
        return [ hlErr ]
      # extract the numbers
      (start, end, load) = matches.groups()
      # validate the hours and the load
      error = self.validateLoad(load)
      if error: return error
      error = self.validateHour(start)
      if error: return error
      error = self.validateHour(end)
      if error: return error
      i = int(start)
      while 1:
        if loads_[i] < 0:
          loads_[i] = load
        elif loads_[i] != load: # same load is fine
          return [ ValidationError("Overlapping loads for host %s for hour %d" % (host, i)) ]
        i = i + 1
        if i >= 24: i = 0
        if i == int(end): break
    return None

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # check for comments in the line
    if -1 != string.find(value, "#"):
      return [ ValidationError("Comments not allowed after entry") ]

    # first check for TIMES patterns
    if self.allowTimeRange_:
      # check for timeranges syntax
      error = self.validateTimeRange(value)
      if error: return error
      if error == None: return VALID_OK

    host = load = None
    # see if any of the patterns match
    for pattern in self.patterns:
      matches = pattern.match(value)
      if matches != None:
        (host, load) = matches.groups()
        break

    if host == '*' and self.seen_entry:
      return [ ValidationError("Wild card entry must not follow "
                               "other entries.") ]
    self.seen_entry = 1

    if host == None:
      hlErr = ValidationError("Invalid hostload entry %s" % value,
                              ERR_CODE = ERR_BAD_HOSTLOAD_ENTRY)
      hlErr.addAttrib("ENTRY", value)
      return [ hlErr ]

    error = self.validateHost(host)
    if error: return error

    error = self.validateLoad(load)
    if error: return error

    return VALID_OK

class EnterpriseHostLoad(HostLoad):
  """A hostload entry; no absolute rules; hosts must be FQDN hosts"""
  def __init__(self):
    HostLoad.__init__(self, allowAbsolute=0, allowTimeRange=1, \
      qualifiedHosts=1, allowWildCard=1)

class EnterpriseConnectorLoad(HostLoad):
  """A Connector load entry; no absolute rules; hosts are connector names"""
  def __init__(self):
    HostLoad.__init__(self, allowAbsolute=0, allowTimeRange=1, \
      qualifiedHosts=0, allowWildCard=1)

class EnterpriseMachineList(List):
  """Validats a parameter as a list of machines"""
  def __init__(self, min_size = None, max_size=None):
    List.__init__(self, GoogleProductionMachine(), min_size=min_size, max_size=max_size)

class EnterpriseOneMachineMap(Map):
  """Validats a parameter as map from integer to a list of machines"""
  def __init__(self):
    Map.__init__(self, Int(GTE=0), EnterpriseMachineList(min_size=1, max_size=1))

class EnterpriseMachineMap(Map):
  """Validats a parameter as map from integer to a comma separated
  list of machines"""
  def __init__(self, min_size = None):
    Map.__init__(self, Int(GTE=0), EnterpriseMachineList(min_size=min_size))

class DatePatternLine(CSVLine):
  """A rule for extracting date from the document"""
  def __init__(self):
    CSVLine.__init__(self, validators=
                     [ SeparatedList(URLPattern(allowComments=0, allowSlash=1), separator='\s+',min_size=1), # url pattern
                       Set(['metatag','title','body','last_modified','url']),
                       String(emptyOK=1),  # metatag name
                       String(emptyOK=1),
                       String(emptyOK=1),
                       String(emptyOK=1)])

class MachinePort(String):
  """- A colon serarated GoogleProductionMachine, PortNum pair"""
  def __init__(self, nullOK=1, emptyOK=0,
               minPort = 1024, maxPort=65536,
               machine_validator = None):
    String.__init__(self, nullOK = nullOK, emptyOK=emptyOK)
    self.minPort = minPort
    self.maxPort = maxPort
    # if no machine_validator was given, use GoogleProductionMachine
    if None == machine_validator:
      self.machine_validator = GoogleProductionMachine()
    else:
      self.machine_validator = machine_validator

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    parts = string.split(value, ':')
    if len(parts) != 2:
      return [ ValidationError("Invalid machine:port") ]

    # check port
    try:
      port = int(parts[1])
    except:
      port = None

    if port == None or port < self.minPort or port > self.maxPort:
      return [ ValidationError("Invalid port number") ]

    return self.machine_validator.validate(parts[0], context)

class URLMatcherMapperLine(String):
  """A URLMatcherMapper file"""

  # As defined in RFC1808
  LEGAL_CHARS_RE = re.compile("([a-zA-Z0-9\$\-_\.\+!\*\'\(\)\,\{\}|\\\^~\[\]`;\/\?\:@&=\<\>#%\"]|(%[0-9a-fA-F][0-9a-fA-F]))*$")

  def __init__(self, data_validator,
               allowComments = 1, allowSlash=0, doUnescape = 0):
    String.__init__(self)

    self.data_validator = data_validator
    self.urlpattern_validator = URLPattern(allowComments=allowComments,
                                           allowSlash=allowSlash)
    self.doUnescape = doUnescape

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    # split the pattern and data
    parts = re.split('[ \t]', value, 1)
    if len(parts) != 2:
      return [ ValidationError("Invalid urlmatchmapper line") ]

    # validate the pattern
    r = self.urlpattern_validator.validate(parts[0], context)
    if VALID_OK != r: return r

    # unescape the data if required
    data = parts[1]
    if self.doUnescape:
      if not self.LEGAL_CHARS_RE.match(data):
        return [ ValidationError("Invalid character in urlmatchmapper data") ]
      data = urllib.unquote_plus(data)

    # validate the data
    return self.data_validator.validate(data, context)

class UserPasswdEntry(String):
  """The data part of a crawl uesrname/password urlmatchermapper line"""

  # As defined in RFC2068
  LEGAL_USERID_RE = re.compile("[\x01-\x1f\x7f:]")
  LEGAL_PASSWORD_RE = re.compile("[\x01-\x1f\x7f]")

  def __init__(self):
    String.__init__(self)

  def validate(self, value, context):
    r = String.validate(self, value, context)
    if VALID_OK != r: return r

    subparts = string.split(value, ":", 3)

    if len(subparts) != 4:
      return [ ValidationError("Invalid username/password entry") ]

    if self.LEGAL_USERID_RE.search(subparts[0]):
      return [ ValidationError("Invalid username") ]
    if self.LEGAL_USERID_RE.search(subparts[1]):
      return [ ValidationError("Invalid domain") ]
    if subparts[2] not in ['1', '0']:
      return [ ValidationError("Invalid username/password entry") ]
    if self.LEGAL_PASSWORD_RE.search(subparts[3]):
      return [ ValidationError("Invalid password") ]

    return VALID_OK

class UserPasswdLine(URLMatcherMapperLine):
  """A line of a crawl username/password file"""
  def __init__(self):
    URLMatcherMapperLine.__init__(self,
                                  UserPasswdEntry(),
                                  allowComments = 0, allowSlash=1,
                                  doUnescape = 1)

class ProxyConfigLine(URLMatcherMapperLine):
  """A line of a crawler proxy config file"""
  def __init__(self):
    data_validator = MachinePort(machine_validator = Hostname(FQDN = 1,
                                                              resolveDNS = 0,
                                                              allowIP = 1),
                                 minPort=1)

    URLMatcherMapperLine.__init__(self, data_validator,
                                  allowComments = 0, allowSlash=1,
                                  doUnescape = 0)


class FileTypeList(List):
  """A list of filetype names"""
  def __init__(self, allow_images = 0, min_size = None, max_size = None):
    valid_filetypes = ['PDF', 'PS',
                       'MS-EXCEL', 'RTF',
                       'MSWORD', 'MS-PPT',
                       'PS', 'FLASH', 'PSGZ',
                       'XML',
                       'OTHER',
                       'EVERYTHING']
    if allow_images:
      valid_filetypes.append('IMAGE')

    List.__init__(self, Set(valid_filetypes),
                  min_size = min_size, max_size = max_size)

#########

class URLFile(FileLine):
  def __init__(self, **args):
    validator = URL()
    apply(FileLine.__init__, (self, validator), args)

class URLPatternFile(FileLine):
  def __init__(self, allowComments = 1, allowSlash = 0, **args):
    validator = URLPattern(allowComments = allowComments,
                           allowSlash = allowSlash)
    apply(FileLine.__init__, (self, validator), args)

class DupHostFile(FileLine):
  def __init__(self, allowWildcards = 1, qualifiedHosts = 0, **args):
    validator = DupHostEntry(allowWildcards = allowWildcards,
                             qualifiedHosts = qualifiedHosts)
    apply(FileLine.__init__, (self, validator), args)

class EnterpriseDupHostFile(FileLine):
  def __init__(self, **args):
    validator = EnterpriseDupHostEntry()
    apply(FileLine.__init__, (self, validator), args)

class HostLoadFile(FileLine):
  def __init__(self, useEnterpriseHostLoad=0, **args):
    if useEnterpriseHostLoad:
      validator = EnterpriseHostLoad()
    else:
      validator = HostLoad()
    apply(FileLine.__init__, (self, validator), args)

class ConnectorLoadFile(FileLine):
  def __init__(self, **args):
    validator = EnterpriseConnectorLoad()
    apply(FileLine.__init__, (self, validator), args)

class DatePatternFile(FileLine):
  def __init__(self, **args):
    validator = DatePatternLine()
    apply(FileLine.__init__, (self, validator), args)

class KeymatchFile(FileLine):
  def __init__(self, **args):
    validator = CSVLine(validators=[ SeparatedList(String(), separator='\s+',min_size=1),                                         # keymatch words
                                     Set(['KeywordMatch',
                                          'PhraseMatch',
                                          'ExactMatch']), # keymatch type
                                     URL(),               # URL
                                     String(emptyOK=1)])  # title

    apply(FileLine.__init__, (self, validator), args)

class SynonymsFile(FileLine):
  def __init__(self, **args):
    validator = CSVLine(validators=[ SeparatedList(String(), separator='\s+',min_size=1),                                         # original words
                                     SeparatedList(String(), separator='\s+',min_size=1)])                                        # synonym words

    apply(FileLine.__init__, (self, validator), args)

class SiteFile(FileLine):
  def __init__(self, **args):
    validator = SiteName()
    apply(FileLine.__init__, (self, validator), args)

class FiletypeFile(FileLine):
  def __init__(self, **args):
    validator = FileExtension()
    apply(FileLine.__init__, (self, validator), args)

class QueryExpansionFile(FileLine):
  def __init__(self, **args):
    validator = String()
    apply(FileLine.__init__, (self, validator), args)

class ScoringPolicyFile(FileLine):
  def __init__(self, **args):
    validator = String()
    apply(FileLine.__init__, (self, validator), args)
  
class LanguageFile(FileLine):
  def __init__(self, **args):
    validator = String()
    apply(FileLine.__init__, (self, validator), args)

class MetatagFile(FileLine):
  def __init__(self, **args):
    validator = MetatagLine()
    apply(FileLine.__init__, (self, validator), args)

class UserPasswdFile(FileLine):
  def __init__(self, **args):
    validator = UserPasswdLine()
    apply(FileLine.__init__, (self, validator), args)


class ProxyConfigFile(FileLine):
  def __init__(self, **args):
    validator = ProxyConfigLine()
    apply(FileLine.__init__, (self, validator), args)

class ExtraHttpHeadersFile(FileLine):
  def __init__(self, **args):
    validator = URLMatcherMapperLine(String(),
                                     allowComments = 0, allowSlash=1,
                                     doUnescape = 1)
    apply(FileLine.__init__, (self, validator), args)

# TODO: Actually, we expect one-line config file here.
class SsoServingFile(FileLine):
  def __init__(self, nullOK=1, **args):
    validator = SsoServingEntry()
    apply (FileLine.__init__, (self, validator, nullOK), args)

class SsoCookiePatternFile(FileLine):
  def __init__(self, nullOK=1, **args):
    validator = SsoCookiePatternEntry()
    apply(FileLine.__init__, (self, validator, nullOK), args)

############# Froogle validators

class FroogleMerchantId(ReMatch):
  """A well-formed Froogle merchant id"""

  MERCHANTID_CHARS_REGEX = "^[a-z0-9_]*$"

  def __init__(self, nullOK = 0, emptyOK = 0):
    ReMatch.__init__(self, regExpr = self.MERCHANTID_CHARS_REGEX,
                     nullOK = nullOK, emptyOK = emptyOK)

  def validate(self, value, context):
    # NOTE: we do a little black magic here so that we can "reclassify" an
    # error you don't want to use this class as an example for writing a
    # simple validator.
    errors = ReMatch.validate(self, value, context)
    if errors == VALID_SHORT_CIRCUIT:
      return errors
    elif errors != VALID_OK:
      # Replace the ERR_RE_NO_MATCH message
      for error in errors:
        if (error.attribs.has_key("ERR_CODE") and
            error.attribs["ERR_CODE"] == ERR_RE_NO_MATCH):
          error.message = ("Illegal characters in merchant id, "
                           "(only a-z, 0-9, _ allowed)")
    return errors

class FroogleFeedFilename(Filename):
  """A well-formed Froogle feed filename.  This is a simple file, without
  any path"""

  FEED_FILENAME_RE = re.compile("^[a-zA-Z0-9_\-\.~]*$")

  def __init__(self, nullOK = 0, emptyNameOK = 0):
    Filename.__init__(self, nullOK = nullOK,
                      emptyNameOK = emptyNameOK, absolute = 0)

  def validate(self, value, context):
    errors = Filename.validate(self, value, context)
    if errors != VALID_OK:
      return errors
    if not self.FEED_FILENAME_RE.match(value):
      return [ ValidationError("Invalid character feed filename "
                               "(only a-z, A-Z, 0-9, _ - ~ and . allowed") ]
    return VALID_OK



class GemsRule(Map):
  def __init__(self, groups):
    # GemsRule - a validator for GEMS rules
    # PARAMETERS: groups: list of group ids ("serial number" for the
    #                     collector shard)
    Map.__init__(self,
                 # No defaults, we will not allow unknown keys, so
                 # each validator is explicitly stated in
                 # val_validator_map
                 default_key_validator = None,
                 default_val_validator = None,

                 allow_unknown_keys = 0,

                 # allow the default for report_name
                 # but frequency and type must be in a pre-defined set
                 val_validator_map = {
                     'machine_list' : None,
                     'rule_name' : String(nullOK=0),
                     # severity is int, float, or func
                     'severity' : None,
                     'tolerance_time' : Float(),
                     'requires': GemsRuleRequires(),
                     'comments' : String(nullOK=1, emptyOK=1),
                     'fix_me_threshold' : Float(),
                     'fix_max_retry' : Float(),
                     'fix_max_fail_wait' : Float(),
                     'fix_max_done_wait' : Float(),
                     'path_to_owner' : None,
                     'group' : Set(groups),
                     'down_tolerance' : Int(),
                     'derive' : None,
                     'depends_on' : None,
                     'dependency_from' : None,
                     'eval' : None,
                     'actions' : None,
                 },
                )

class GemsRuleRequires(List):
  def __init__(self):
    List.__init__(self,
                  Tuple(None,
                        eq_size=2,
                        elem_validator=[None,
                                        OrMeta([String(),
                                                List(String())])]),
                  min_size=1)

class ApplianceIPAddress(IPAddress):
  """An IP address that's valid as a Google Search Appliance address"""
  def __init__(self, nullOK = 0):
    IPAddress.__init__(self, nullOK = nullOK)

  # forbid the following IP addresses:
  # 192.168.255.1
  # 192.168.255.254
  # 216.239.43.*
  def forbidden(self, value):
    octets = string.split(value, '.')  # split into octets
    int_values = map(string.atoi, octets)
    if (int_values in [[192, 168, 255, 1], [192, 168, 255, 254]]) or \
       (int_values[0:3] == [216, 239, 43]):
      return 1
    return 0

  def validate(self, value, context):
    r = IPAddress.validate(self, value, context)
    if VALID_OK != r: return r

    if self.forbidden(value):
      return [ ValidationError("Reserved IP Address") ]

    return VALID_OK

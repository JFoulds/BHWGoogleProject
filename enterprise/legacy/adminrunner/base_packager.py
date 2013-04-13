#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
#
# Original Author: Zia Syed (zsyed@google.com)
#

"""Defines these two basic abstractions PackageEntity and ConfigFilter.

The configuration import/export subcomponent keeps packaging process and the
process to generate the content separate. This helps in supporting different
formats in future or making modifications to existing formats without
affecting the way content is generated.

The basic abstraction in packaging is a PackageEntity. Each PackageEntity has
an associated content filter OR content generator. The use of the word filter
signifies that a content generator can hide or encrypt some content.

"""

import copy
import exceptions

from google3.pyglib import logging

SUCCESS = 0
FAILURE = -1
SUCCESS_WITH_APPS_MESSAGE = 5

PURE_VIRTUAL = 'This function has to be implemented by derived classes.'

class MalformedContentError(exceptions.Exception):
  """Exception to be thrown when there is an error in parsing content.
  """
  pass

class ConfigFilter:
  """
  ConfigFilter is responsible for generating and processing data for each unit
  of data that can be exported/imported.

  Implementation assumes/supports that data to be exported is hierarchical and
  supports nesting.Each filter can have multiple packaging entities associated
  under it for packaging the hierarchical content.

  Each filter has variable number of associated attributes.
  """

  def __init__(self, conn, cfg, secmgr):
    self.secmgr     = secmgr
    self.conn       = conn
    self.cfg        = cfg
    self.subents    = []
    self.attributes = {}

  ####### getters and setters #########

  def addSubentity(self, ent):
    self.subents.append(ent)

  def setAttribute(self, att, val):
    self.attributes[att] = val

  def getAttribute(self, att):
    return(self.attributes[att])

  def getAttributes(self):
    return(copy.copy(self.attributes))

  def getSecMgr(self):
    return self.secmgr

  def encode(self, level):
    """Encodes the content associated with this filter.

    level is an integer representing the nesting level where this content will
    appear in complete packaging.

    Default implementation is to invoke encode on all subentities in
    alphabetical order of their labels. This helps in the case where
    the final file is supposed to be textual and placed under configuration
    management system.
    """
    mybody = ''
    self.subents.sort(lambda x, y: cmp(x, y))
    for ent in self.subents:
      mybody += ent.encode(level+1)

    return mybody

  def decode(self, body, log, validate_only=0):
    """Complements the encode method. If the output of encode method is
    provided to this method directly then it should properly decode/import
    data from the input.
    """
    apps_message = 0
    self.subents.sort(lambda x, y: cmp(x, y))
    for ent in self.subents:
      ret = ent.decode(body, log, validate_only)
      if not ret == SUCCESS and not ret == SUCCESS_WITH_APPS_MESSAGE:
        return ret
      if ret == SUCCESS_WITH_APPS_MESSAGE:
        apps_message = 1
    if apps_message:
      return SUCCESS_WITH_APPS_MESSAGE
    return SUCCESS

  def initEncode(self):
    """Before encoding process begins, every filter should be initialized.
    Sometimes it may not be possible to do that initialization in the
    constructor so initEncode is called on every filter before encoding
    for that filter begins.
    """
    pass

  def initDecode(self):
    """Same as initEncode but used in the decoding process.
    """
    pass

class PackageEntity:
  """PackageEntity is an abstraction for representing how the content
  generated by filters is finally presented e.g. is it presented as a tar file
  , encapsulated as MIME or XML file etc.

  This is an abstract class and needs to be subclassed for each type of
  presentation.
  """

  def __init__(self, label, conffilter, sort_rank):
    # This class can't be instantiated
    if self.__class__ is PackageEntity:
      raise NotImplementedError

    self.label = label
    self.conffilter = conffilter      # Associated content generator
    self.sort_rank = sort_rank

  def __cmp__(self, other):
    """Compares this entity with 'other'.
    If the sort_rank are same we do alphabetical ordering.
    """
    ret = cmp(self.sort_rank, other.sort_rank)
    if ret == 0:     # equal
      ret = cmp(self.label, other.label)
    return ret

  ### Accessor methods ###

  def getSortRank(self):
    return self.sort_rank

  def settSortRank(self, sort_rank):
    self.sort_rank = sort_rank

  def getLabel(self):
    return self.label

  def getFilter(self):
    return self.conffilter

  def setAttribute(self, att, val):
    self.conffilter.setAttribute(att, val)

  def getAttribute(self, att):
    return(self.conffilter.getAttribute(att))

  def getSecMgr(self):
    return self.conffilter.getSecMgr()

  ### Methods to be overridden ###

  def encode(self, level):
    """Returns the encoded text.
    """
    self.conffilter.initEncode()
    body = self.begin() + self.writeData(level) + self.end()
    return body

  def decode(self, body, log, validate_only = 0):
    """Decodes body by invoking the associated content filter.
    """
    self.conffilter.initDecode()
    self.readData(body)
    return SUCCESS

  def begin(self):
    """Returns the text that should precede each section.
    """
    assert 0, PURE_VIRTUAL

  def end(self):
    """Returns the text that should end each section.
    """
    assert 0, PURE_VIRTUAL

  def writeData(self, level):
    """Default implementation just invokes the associated content filter to
    write export the data. Child classes can override this method to do
    any preprocessing before writing. This preprocessing should be undone
    in the readData method.
    """
    return(self.conffilter.encode(level+1))

  def readData(self, body):
    """Default implementation is that it returns the body as it is.
    Child classe can override this method to do some preprocessing
    before data can be imported.
    """
    return body

class ImportLog:
  """To log all the error and information messages during import process
  so it can be sent to the user.
  """
  def __init__(self):
    self.log = ''
    self.errors = []

  def error(self, str):
    """Logs error message to both google log and import log.
    Warning: str is not necessarily a string.
    """
    logging.error(str)
    self.log = '%sERROR: %s\n' % (self.log, str)
    self.errors.append('%s' % str)

  def info(self, str):
    """Logs information message to both google log and import log.
    """
    logging.info(str)
    self.log = '%sINFO: %s\n' % (self.log, str)
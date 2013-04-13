#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
#
# Original Author: Zia Syed (zsyed@google.com)
# Improved efficiency/speed: Hareesh Nagarajan (hareesh@google.com)

"""Extends base_packager to implement xml encapsulated packaging.
In this packaging all config files are encapsulated between XML
tags as text and CDATA sections. It also supports encrypted CDATA
sections for exporting confidential data.

On an import the control typically looks like this: decodeFromString()
is called which calls decode() which in turn calls the decode for the
appropriate filter: self.getFilter().decode(node_data, log,
validate_only). This inturn could call decode() back again. The stack
grows! the XML string is copied over and over and things gets
painfully slow.
"""

import re
import xml.dom.minidom

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import base_packager

SUCCESS = base_packager.SUCCESS

TAB           = '  '      # tab = two spaces
NEWLINE       = '\n'
CONTENT_TYPE  = 'text/xml'
ENCODING      = 'UTF-8'
DEFAULT_RANK  = 100       # Default sorting rank for items

############ utility functions ###############
def getMergedNodeData(node, isCdata=False, frompat='', topat=''):
  """dom parser may decompose a text or cdata section into multiple
  sections so we need to merge them. If isCdata is true, then we
  replace the from pattern with the to pattern.
  """
  curr_child = node.firstChild
  body = []
  while curr_child:
    res = curr_child.nodeValue
    if isCdata:
      res = re.sub(frompat, topat, res)
    body.append(res)
    curr_child = curr_child.nextSibling

  body = ''.join(body)
  body = re.sub(r'^\n', '', body, 1) # Remove newline added in writeData. 
  return re.sub(r'\n[ ]*$', '', body, 1) # Undo the encode.

class XMLPackageEntity(base_packager.PackageEntity):
  """Represents a section in an XML documented encapsulated in <tag></tag>
  pairs.
  """

  def __init__(self, label, contfilter, required=0, sort_rank=DEFAULT_RANK):
    base_packager.PackageEntity.__init__(self, label, contfilter, sort_rank)
    # by default sections are optional
    self.is_required = required

  def escapeAttrValue(self, attr):
    """Does any esacping of value associated with attr so XML file would be
    well formatted.
    """
    # TODO(zsyed): validate the attribute value and do any escaping if necessary
    return self.getAttribute(attr)

  def getAttrStr(self):
    """Returns the attribue string to be printed in the XML file.
    """
    result = ''
    myFilter = self.getFilter()
    for attr in myFilter.getAttributes():
        result = '%s %s="%s"' % (result, attr, self.escapeAttrValue(attr))

    return result

  def getTabs(self, level):
    return TAB*level

  def begin(self):
    """Returns the beginning XML tag with all the attributes.
    """
    result = '<%s%s>' % (self.label, self.getAttrStr())
    return result

  def end(self):
    """Returns the ending tag.
    """
    return '</%s>' % self.label

  def encode(self, level):
    """We do encoding ourselves so we can write the XML file in a format we
    want. Potentially we could have used toxml or toprettyxml method of a
    document in minidom to write the final document for us.
    """
    # initialize associated filter before we call encode on it
    self.getFilter().initEncode()
    tabs = self.getTabs(level)
    body = [NEWLINE, tabs, self.begin(), self.writeData(level), NEWLINE, tabs,
            self.end()]
    return ''.join(body)

  def decode(self, xml_node, log, validate_only=0):
    # read my tag
    node_list = xml_node.getElementsByTagName(self.label)
    if not len(node_list):
      if self.is_required:
        raise base_packager.MalformedContentError, "Malformed content error."
      else:
        return SUCCESS

    # Each entity can process only one node. We decide to decode nodes in the
    # same order they appear.
    mynode = node_list[0]
    # Read all attributes and set them on the content filter
    for attr in mynode._get_attributes().keys():
      self.setAttribute(attr, mynode.getAttribute(attr).encode('ascii'))

    # Now that attributes are set on the filter we can call initDecode so the
    # filter can initialize the decoding process based on those attributes.
    self.getFilter().initDecode()
    # Read the node data to remove any additional stuff we may have added as
    # part of writeData
    node_data = self.readData(mynode)
    # Before decoding the current node remove it from the parent node so it
    # won't be processed by anybody else.
    xml_node.removeChild(mynode)
    return self.getFilter().decode(node_data, log, validate_only)

  def decodeFromFile(self, filename, log, validate_only=0):
    """Decodes an XML document in a file.
    """

    # TODO(hareesh): The whole damn import configuration needs to be
    # read into memory.
    try:
      file_contents = open(filename, 'r').read()
      document = xml.dom.minidom.parseString(file_contents)
    except Exception, e:
      logging.error("Malformed content error %s" % (filename))
      raise base_packager.MalformedContentError, e

    retval = self.decode(document, log, validate_only)
    # destroy dom model to delete any cyclical structures
    document.unlink()
    return retval

class XMLTextEntity(XMLPackageEntity):
  """Represents an XML entity holding CDATA.
  """

  #### overridden functions #########

  def writeData(self, level):
    return '%s%s' % (NEWLINE, XMLPackageEntity.writeData(self, level))

  def readData(self, textNode):
    return getMergedNodeData(textNode)

class CDATAPackageEntity(XMLTextEntity):
  """Represents an XML entity holding CDATA section.
  """

  CDATA_BEGIN   = r'<![CDATA['
  CDATA_END     = r']]>'

  # Encoding: Because CDATA section can't have ]]>, we escape user data
  # as following:
  #   ]]> ---> \]\]\>
  #   \]\]\> -----> \\]\\]\\> and so on
  CDATA_ENC_PATTERN_FROM = r'(\\*)\](\\*)\](\\*)\>'
  CDATA_ENC_PATTERN_TO   = r'\1\\]\2\\]\3\\>'

  # Decoding: Reverse of encoding.
  CDATA_DEC_PATTERN_FROM = r'\\(\\*)\]\\(\\*)\]\\(\\*)\>'
  CDATA_DEC_PATTERN_TO   = r'\1]\2]\3>'

  def begin(self):
    return '%s%s' % (XMLPackageEntity.begin(self), self.CDATA_BEGIN)

  def end(self):
    return '%s%s' % (self.CDATA_END, XMLPackageEntity.end(self))

  def writeData(self, level):
    """Writes data associated with the filter as CDATA entity.
    """
    body = XMLTextEntity.writeData(self, level)
    ## remove all instances of >]] with \>\]\]
    result = re.sub(self.CDATA_ENC_PATTERN_FROM, self.CDATA_ENC_PATTERN_TO, body)
    return result

  def readData(self, CDATANode):
    """Reads data from CDATANode assuming it is a CDATA element
    """
    return getMergedNodeData(CDATANode, True, self.CDATA_DEC_PATTERN_FROM,
                             self.CDATA_DEC_PATTERN_TO)

class SecureCDATAPackageEntity(CDATAPackageEntity):
  """Same as CDATAPackageEntity but adds encryption and decryption before
  export and import respectively.
  """

  def writeData(self, level):
    """Encrypts data using
    """
    body = self.getSecMgr().encryptBlock(XMLPackageEntity.writeData(self, level))
    ## remove all instances of >]] with \>\]\]
    result = re.sub(self.CDATA_ENC_PATTERN_FROM, self.CDATA_ENC_PATTERN_TO, body)
    # add newline at the beginning
    return '%s%s' % (NEWLINE, result)

  def readData(self, textNode):
    """Reads data from textNode and decrypts it.
    """
    body = getMergedNodeData(textNode, True, self.CDATA_DEC_PATTERN_FROM,
                             self.CDATA_DEC_PATTERN_TO)
    return self.getSecMgr().decryptBlock(body)

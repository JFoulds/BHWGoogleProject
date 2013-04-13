#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc.
# All Rights Reserved.

"""Read messages from an xlb file."""

import xml.dom
import xml.dom.minidom

__author__ = "kens@google.com (Ken Shirriff)"


def Read(filename):
  """Read an xlb message bundle.

  Placeholders are replaced with their original text.

  See https://www.corp.google.com/eng/howto/transconsole/create-xlb.html

  Args:
    filename: the xlb file to read

  Returns:
    map from (ASCII) names to (Unicode) messages.
  """

  msgs = {}
  doc = xml.dom.minidom.parse(open(filename, "r"))
  doc.normalize()

  nodelist = doc.getElementsByTagName("msg")
  for node in nodelist:
    name = node.getAttribute("name")
    value = []
    for child in node.childNodes:
      if child.nodeType == xml.dom.Node.TEXT_NODE:
        value.append(child.data)
      elif (child.nodeType == xml.dom.Node.ELEMENT_NODE and
            child.tagName == "ph"):
        value.append(child.childNodes[0].data)
      else:
        print "*** unexpected node type", repr(child)
    msgs[name.encode("utf-8")] = "".join(value)
  return msgs

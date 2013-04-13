#!/usr/bin/python2.4
#
# Copyright 2003 Google Inc. All Rights Reserved.
#
# Derived from perennial Python practice.

__author__ = 'est@google.com (Eric Tiedemann)'

from google3.pyglib import requires

requires.Python22()


class Record(object):
  """A low-overhead concrete data type.

  It gets its attributes from the keyword arguments to its
  constructor.  repr()/eval() idempotency and attribute-based
  equality comparison are also provided.

  Example:

  >>> s = Record.Record(x=24, y=43)
  >>> s
  Record(x=24, y=43)
  >>> s.x
  24
  >>> r = eval(repr(s))
  >>> s == r
  1
  """

  def __init__(self, **kwds):
    """Calls self.__dict__.update() with kwds."""
    self.__dict__.update(kwds)

  def __repr__(self):
    lst = []
    for key, val in self.__dict__.iteritems():
      lst.append('%s=%r' % (key, val))
    return '%s(%s)' % (self.__class__.__name__, ', '.join(lst))

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return False
    return self.__dict__ == other.__dict__

  def __ne__(self, other):
    return self.__dict__ != other.__dict__

#
# Original Author: Daniel Dulitz
#
# Copyright 2002, Google
#

"""
Generic exceptions.
"""

class TimeoutException(Exception):
  def __init__(self, msg=""):
    Exception.__init__(self, msg)
  # end def

class NestedException(Exception):
  def __init__(self, exc_info):
    Exception.__init__(self, exc_info[1])  # exc_info[1] is the error object
    self.exc_info_ = exc_info
  # end def
  def exc_info(self):
    return self.exc_info_

class AbstractMethod(Exception):
  """Raise this exception to indicate that a method is abstract.  Example:
        class Foo:
          def Bar(self):
            raise gexcept.AbstractMethod"""
  def __init__(self):
    Exception.__init__(self)
  # end def

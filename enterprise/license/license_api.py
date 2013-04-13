#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""An API to query the license, and for accessing license-related
constants.

From python code:

  from google3.enterprise.license import license_api

To get a constant as an int:

  license_api.C.ENT_LICENSE_FEEDS

To get a constant as a string (the string is the same as the name of
the constant):

  license_api.S.ENT_LICENSE_FEED

this will evaluate to "ENT_LICENSE_FEED".

"""

__author__ = 'haldar@google.com (Vivek Haldar)'

import sys

from google3.pyglib import app
from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.license import license_pb


FLAGS = flags.FLAGS


class UndefinedConstantError(Exception):
  """Thrown when clients try to access an undefined license constant"""
  pass


class C(license_pb.Consts):
  """Convenient wrapper for enum constants in license.proto. """
  pass


def s(license_const):
  """Given a license-related constant (which is an int), return the
  string name of that constant.

  The name of this method is short because it will be referenced a
  LOT.

  Args:
    license_const:    const defined in license_pb.Const

  Returns:
    string name of constant if arg is a valid constant, "" o/w
  """
  s = license_pb.Consts.E_Name(license_const)
  # if the string was empty it means the constant is undefined
  if not s:
    raise UndefinedConstantError('Trying to access undefined license'
                                 'constant %d', license_const)
  return s


class CToStr(object):
  """Convenience class for quick access to string constants.

  This allows (along with the alias "S" below) accessing constants by saying:
      license_api.S.ENT_FOO_CONST
  rather than the longer and uglier:
      license_api.s(license_api.C.ENT_FOO_CONST)

  This technique was suggested by Daniel Hottinger (hotti@google.com)
  """

  def __getattribute__(self, name):
    try:
      getattr(C, name)
      return name
    except AttributeError, e:
      raise UndefinedConstantError(str(e))


# short alias to above class
S = CToStr()


# alias to license_pb
class License(license_pb.License):
  """This is just an alias for the License PB in license.proto."""
  pass


def LicenseDictToProtoBuf(license_dict):
  """Convert a license dictionary to a protocol buffer.

  The license is a python dictionary in google_config.

  Args:
  license_dict:  license dictionary

  Returns:
  License protocol buffer (from //enterprise/license/license.proto)
  """
  pb = License()

  # key "ENT_LICENSE_FOO_BAR" has field "foo_bar" in the PB
  for key in license_dict:

    # "ENT_LICENSE_FOO_BAR" -> "set_foo_bar", with the exception of
    # "ENT_BOX_ID" -> "id"
    if key == 'ENT_BOX_ID':
      setter_name = 'set_box_id'
    else:
      setter_name = 'set_' + '_'.join(key.split('_')[2:]).lower()

    # now we have the name of the PB setter method ("set_foo_bar")
    # and can call it
    try:
      func = getattr(pb, setter_name)
    except AttributeError:
      logging.error('Undefined license field %s', setter_name)
    else:
      func(license_dict[key])

  return pb


if __name__ == '__main__':
  sys.exit('Import this as a module')

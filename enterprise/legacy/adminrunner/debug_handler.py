#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.
#

"""Implements handler for providing various debugging information.
"""

__author__ = 'zsyed@google.com (Zia Syed)'

import sys
import urllib

import google3  # Required to enable third-party import magic.
from hotshot import stats  # Third-party import. See ThirdPartyPython wiki.

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler

class StrFile:
  """Serves as in memory file object.
  """
  def __init__(self):
    self.str = []

  def write(self, str):
    self.str.append(str)

  def dumpAsString(self):
    return ''.join(self.str)

class DebugHandler(admin_handler.ar_handler):
  """Handles debug information requests..
  """

  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg is non-null only for testing (we cannot have multiple constructors)
    if cfg:
      self.cfg = cfg
      self.conn = None
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "getprofile"            : admin_handler.CommandInfo(
      1, 0, 0, self.get_profile),
      "getprofilesummary"            : admin_handler.CommandInfo(
      1, 0, 0, self.get_profile_summary),
      }

  def get_profile(self, id):
    """Returns the raw hotshot profile file associated with id.
    """
    result = ""
    try:
      filename = self.get_profile_name(long(id))
      result = open(filename,'rb').read()
    except Exception, e:
      logging.error(e)
      result = 'Error getting profile %s' % id
      self.error = result
    return '%d\n%s' % (len(result), result)

  def get_profile_summary(self, id):
    """Returns the summary of top 10 time consuming functions and their
    callers.
    """
    result = ""
    try:
      filename = self.get_profile_name(long(id))
      prof = stats.load(filename)
      prof.sort_stats('time', 'calls')
      str = StrFile()
      sys.stdout = str
      prof.print_stats(10).print_callers(10)
      sys.stdout = sys.__stdout__
      result = str.dumpAsString()
    except Exception, e:
      sys.stdout = sys.__stdout__
      logging.error(e)
      result = 'Error getting profile summary %s' % id
      self.error = result

    return '%d\n%s' % (len(result), result)

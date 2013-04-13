#!/usr/bin/python2.4
#
# Copyright (C) 2002 and onwards Google, Inc.
#
# Creates a proper config object given the configfile path. If we get
# an enterprise config file returns an EntConfig object else returns the
# Config object
#
import os
import re
import sys
import string


class ConfigFactory:

  def CreateConfig(self, config_file, config_dir=None):
    """
    Given a config file name this returns a Config or an EntConfig object
    """
    # Get here only for strings
    ent_home = self.get_enterprise_home_(config_file)
    if ent_home != None:
      from google3.enterprise.legacy.adminrunner import entconfig
      return entconfig.EntConfig(ent_home)

    # This is not an enterprise config. How can it not be? Die horribly and
    # noisily.  This code would/should never be up integrated.  There are no
    # such plans anyway
    raise Exception("%s is not a valid enterprise config file!" % config_file)
    die = 5 / 0   # Just in case...
    sys.exit(1)   # yes, I really want you dead

  def get_enterprise_home_(self, config_file):
    """
    Given a config file name we check if it looks like and enterprise
    config file and if it does, it returns the path to the enterprise home,
    else we return none
    * PRIVATE *
    """
    # We look only in strings, files etc.. sorry
    if type(config_file) != type(""):
      return None

    # Enteprise config file have the form:
    expr = '/*(/export/hda3/[0-9A-Za-z.]*)/local/conf/google_config$'
    match = re.match(expr, os.path.normpath(config_file))
    if match != None:
      return match.groups()[0] # The first group is the enterprise home

    return None

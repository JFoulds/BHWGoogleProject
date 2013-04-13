#!/usr/bin/python2.4
#
# Copyright (c) Google Inc, 2001 and beyond!
# Author: David Watson
#
# ConfigNameSpace is a fairly simple class which makes it easy, safe, and
# fun to load python config files.  This class:
# - does some (simple) magic to make useful functions available to the file
#   being loaded; this is done by pre-loading them into the global namespace
#   before calling execfile().
# - provides Add/UpdateXXX() functions which a) do useful checking to make
#   sure parameters are defined in a consistent manner and b) maintain a type
#   entry for each parameter (from validatorlib).
# - can either be passed a namespace (such as globals()), or it can use a
#   private namespace to avoid polluting the global namespace.  The latter also
#   allows the object itself to be passed around instead to avoid having to
#   load the config file into each module global namespace.
# - Any variable starting with '__' is considered hidden and it is not
#   accessible.
#
# examples:
#  Assume the config_file_name contains:
#   AddVar('A', 1, validatorlib.Int())
#   UpdateVal('A', 2)
#   __I_am_hidden = 10
#   B = __I_am_hidden
#   ...
#
#  config = ConfigNameSpace(globals())  # load into global namespace
#  config.ExecFile(config_file_name)    # load the config file
#  print A, B                           # print out some loaded parameters
#  print __I_am_hidden                  # will throw an exception
#
#  config = ConfigNameSpace()           # load into a private namespace
#  config.ExecFile(config_file_name)    # load the config file
#  config.A                             # access a parameter
#  config.__I_am_hidden                 # will throw an exception
#  config.namespace['B']                # access a parameter (another way)
#

import types
import copy
import sys

# Hack to enable circular imports
import google3.enterprise.legacy.production.babysitter
google3.enterprise.legacy.production.babysitter.config_namespace = \
    sys.modules[__name__]

# Note that configutil is a circular import
from google3.enterprise.legacy.production.babysitter import configutil

# Dummy class used when validatorlib is not loaded
class NoOp:
  """ This class supports all methods with all arguments """
  def __repr__(self): return "<NoOp instance>"
  def __getattr__(self, name): return lambda *x, **y: 1 # always return true

class ConfigNameSpace:
  # Creates a new ConfigNameSpace object.  Takes an optional namespace map.
  def __init__(self, namespace, require_validators=1):

    self.type_map = {}
    self.namespace = namespace
    self.require_validators = require_validators

    # Preloaded variables from GetPreloadedScope are variables that
    # are set for convenience that bring in info about the environment.
    # Ideally these would not be needed if we could find a better way
    # to do it but crawl is dependent on these.  We make sure not
    # to write these out.
    for (key, val) in configutil.GetPreloadedScope().items():
      if not self.namespace.has_key(key):
        self.AddVar(key, val, None)

  # Adds a variable to the namespace.  Checks that not already defined in
  # either namespace or type map
  def AddVar(self, name, default, type):
    """Declare a new parameter"""
    # check that name not defined
    if self.namespace.has_key(name):
      raise Exception("%s already defined" % name)

    # check that type not defined
    if self.type_map.has_key(name):
      raise Exception("type already defined for %s" % name)

    self.namespace[name] = default
    self.type_map[name] = type

  # Adds the type of variable already defined in namespace, but not in type map
  def AddType(self, name, type):
    # check that name defined
    if not self.namespace.has_key(name):
      raise Exception("%s not defined" % name)

    # check that type not defined
    if self.type_map.has_key(name):
      raise Exception("type already defined for %s" % name)

    self.type_map[name] = type

  # Updates the type of a variable already in the namespace and type map
  def UpdateType(self, name, type):
    # check that name defined
    if not self.namespace.has_key(name):
      raise Exception("%s not defined" % name)

    # check that type already defined
    if not self.type_map.has_key(name):
      raise Exception("no type defined for %s" % name)

    # todo: check subclass property of old/new types

    self.type_map[name] = type

  # Updates the value of a variable already in the namespace and type map
  def UpdateVal(self, name, value):
    # check that name defined
    if not self.namespace.has_key(name):
      raise Exception("%s not defined" % name)

    # check that type already defined
    if not self.type_map.has_key(name):
      raise Exception("no type defined for %s" % name)

    self.namespace[name] = value

  # Updates the type and value of a variable already in the namespace and
  # type map.
  def UpdateVar(self, name, value, type):
    # check that name defined
    if not self.namespace.has_key(name):
      raise Exception("%s not defined" % name)

    # check that type already defined
    if not self.type_map.has_key(name):
      raise Exception("no type defined for %s" % name)

    # todo: check subclass property of old/new types

    self.namespace[name] = value
    self.type_map[name] = type

  # Merges a config namespace with this one
  def MergeNamespace(self, extra, duplicates_ok):
    self.namespace = configutil.MergeScopes(self.namespace, extra.namespace,
                                            duplicates_ok)
    self.type_map = configutil.MergeScopes(self.type_map, extra.type_map,
                                           duplicates_ok)

  # Compute list of vars that are different.
  # Return ( [vars only in this config],
  #          [vars only in the other config],
  #          [vars different and in both configs]
  #        )
  def DiffNamespace(self, other):
    in_self_only = []
    in_other_only = []
    in_both_diff = []

    # compute in_self_only and in_both_diff
    for key, value in self.namespace.items():
      if other.namespace.has_key(key):
        if (value != other.namespace[key]):
          in_both_diff.append(key)
        #end if
      else:
        in_self_only.append(key)
      #end if
    #end for

    # compute in_other_only
    for key in other.namespace.keys():
      if not self.namespace.has_key(key):
        in_other_only.append(key)
      #end if
    #end for

    return (in_self_only, in_other_only, in_both_diff)
  # end DiffNamespace

  # Load the given file into the namespace
  #
  # there are three cases for filename:
  #  -- if filename is a fully qualified path we load from the specified file
  #  -- if it is a relative path we load the file from the relative path
  #  -- if it is a nonqualified file (e.g. "config.default") we look for the
  #     file in the google/config directory from GOOGLEBASE path conputed
  #     by sitecustomize
  #
  def ExecFile(self, config_file, config_dir=None):
    #
    # Operations:
    # 1. We make a copy of the current namespace into old_namespace.
    # 2. We load the stuff from the file into self.namespace,
    # 3. We merge self.namespace over old.namespace and update self.namespace
    #    with the merged map
    # Note: we want to load into self.namespace because all UpdateVar/AddVar etc.
    #  operate on self.namespace
    #
    old_namespace = copy.copy(self.namespace)
    self.add_load_symbols(self.namespace)
    try:
      if type(config_file) != types.StringType:
        # Since we can mess this up, we re-seek the beginning
        config_file.seek(0)
        # file-like object
        exec config_file.read() in self.namespace

      else:
        filename = configutil.GetConfigFilePath(config_file,
                                                config_dir=config_dir)
        execfile(filename, self.namespace)
    finally:
      self.del_load_symbols(self.namespace)
      self.namespace = configutil.MergeScopes(old_namespace, self.namespace, 1)

  # Magic to make parameters in namespace appear as attributes of this object
  def __getattr__(self, name):
    if self.__dict__.has_key(name):
      return self.__dict__[name]

    # if name is "namespace" then it must not be defined yet (or we wouldn't
    # be here) -- so avoid infinite recursion
    if name != "namespace" and self.namespace.has_key(name):
      return self.namespace[name]

    raise AttributeError(name)

  # Inserts the validatorlib module into the namespace
  def import_validator_lib(self, namespace):
    if self.require_validators:
      from google3.enterprise.legacy.production.babysitter import validatorlib
    else:
      validatorlib = NoOp()
    namespace.update({ 'validatorlib' : validatorlib, })

  # This adds symbols to namespace making the scope ready to load a file
  # into it. After loading be sure you call del_load_symbols to
  # eliminate the garbage
  def add_load_symbols(self, namespace):
    # insert validatorlib
    self.import_validator_lib(namespace)

    # insert AddVar and friends into the namespace
    # note that these are bound methods
    namespace.update({ 'AddVar' : self.AddVar,
                            'AddType' : self.AddType,
                            'UpdateVar' : self.UpdateVar,
                            'UpdateVal' : self.UpdateVal,
                            'UpdateType' : self.UpdateType,
                            })

  # Since we may end up with various garbage after loads we have this
  # function to take all out
  def del_load_symbols(self, namespace):
    # Remove bad symbols
    bad_symbols = ['validatorlib',
                   'AddVar', 'AddType', 'UpdateType', 'UpdateVar', 'UpdateVal']
    bad_types = [ types.ModuleType ]

    for k,v in namespace.items():
      if k[:2] == '__' or k in bad_symbols or type(v) in bad_types:
        del namespace[k]

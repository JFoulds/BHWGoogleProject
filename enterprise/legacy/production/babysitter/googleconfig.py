#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# Implements Config class and various utility methods for
# managing configuration files.
#

import os
import sys
import string
import types
import time
import re
import copy
import pprint

from google3.pyglib import logging

# Hack to enable circular imports
import google3.enterprise.legacy.production.babysitter
google3.enterprise.legacy.production.babysitter.googleconfig = \
    sys.modules[__name__]

from google3.enterprise.legacy.setup import prodlib
from google3.enterprise.legacy.production.common import setlib
from google3.enterprise.legacy.production.babysitter import serverlib
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import configutil
from google3.enterprise.legacy.production.babysitter import config_factory
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.production.babysitter import config_namespace
# Note that mainconfig is a circular import
from google3.enterprise.legacy.production.babysitter import mainconfig

#
# Googleconfig serves as a wrapper around config data that
# gives some useful querying methods for data dirs,
# servers and other information.  It also allows you to
# fill in default configuration settings if desired.
#
# Config files should contain a series of assignment statements.
# Config files may also include other configs.
#
# Specify config files that we want to include into the current config.
# The variables from this configuration file are merged into the
# current scope.  If the variables exist in more than one config file
# an error is raised.  The including file, may however, overwrite
# variables from included convigs.  Specific server types to include
# or exclude in the SERVERS variable can be specified with 'wantedtypes'.
# To include a file either specify 'filename' or '('colo', 'servicename') -
# i.e. ('ex', 'www') - as the key.
#
# The options are:
#   'ownservers': [0|1]
#     0: do not own the servers that are included
#     1: own the servers that are included
#   'wantedtypes': [] for all, ['type1','type2'], or ['-type1']
#
# For example:
#
# INCLUDES = {
#   'config.indexindep.ex':
#     { 'ownservers': 1, 'wantedtypes': ['ad', 'onebox'] },
#   'config.gwd.ex':
#     { 'ownservers': 0, 'wantedtypes': ['directory'] },
# }
#
# The common way to load a config file is:
#
#   config = googleconfig.Load(filename, do_includes = [0|1])
#
# This will perform several actions:
#
#  - Pull in includes if do_includes is specified.
#  - Apply default var values to your config file from config.default files
#    and post process the var values.
#  - Separate out replicas, balancers and main servers
#    (see below for more information on how this is split out).
#

#
# Data Directory Methods
#

#
# GetDirName - Get the name of the last directory level, minus the
# "-data". For most things this is the index name, like "apr00index"
# or "jun00index", but for some servers it can be something like
# "onebox". The basename call will do nothing for normal production
# setups (apr01index-data) but is interesting for enterprise-like
# setups (enterprise/cisco/crawl25-data)
#
def GetDirName(datadir):
  longdirname = GetLongDirName(datadir)
  return os.path.basename(longdirname)

#
# GetLongDirName - Get the name of the last directory level,
# minus the "-data". For most things this is the index name, like
# "apr00index" or "jun00index", but for some servers it can be something
# like "onebox".
#
dirname_re = re.compile(r'^/export/hd[a-z]3/(.+)-data(/?)$')
def GetLongDirName(datadir):
  reg = dirname_re.match(datadir)
  if not reg:
    raise RuntimeError, "GetLongDirName: unable to parse %s" % datadir

  return reg.group(1)

#
# GetShortDirName - Strips out the port number from the dirname if any.
#
def GetShortDirName(dirname):
  return re.sub(r'\.\d+$', '', dirname)

#
# Config class encapsulates data from configuration file.
# This serves as a wrapper around config data that
# gives some useful querying methods for data dirs,
# servers and other information.  It also allows you to
# fill in default configuration settings if desired.
#

#
# Load - wrapper to create a config file.
#
# do_includes: - DEPRECATED - generally never load a config without includes.
# config_dir: if not specified and configfile is not a full path name,
#   then it loads from the config dir under sitecustomize.GOOGLEBASE.
#   Else, looks in the specified directory.
# detect_config_dir: if specified and config_dir is none it sets config_dir
#   to the dirname of the config file
#
def Load(configfile, do_includes=1, config_dir=None, detect_config_dir=0):
  if config_dir == None and detect_config_dir:
    config_dir = os.path.dirname(configfile)
    # '' means local dir but os.path.dirname returns it when is no dir, and
    # that means to use the default, which is None
    if config_dir == '' :
      config_dir = None

  config = config_factory.ConfigFactory().CreateConfig(configfile,
                                                       config_dir=config_dir)
  config.Load(do_includes=do_includes, config_dir=config_dir)
  return config


# Small class that has acquire and release (the subset of lock interface
# that we use).  Used only by Config.init_locks() and should be defined
# there, but it can't be because inner classes can't be unpickled.
class _DummyLock:
  def acquire(self): pass
  def release(self): pass

#
# Helpers to implement nested access to map vars
#


# WalkMap takes a map and a path (tuple of names); it recurses the nested
# maps, using the path as keys into each subsequent map.
# Returns: the last nested object named by the given path.
# Throws: KeyError if an undefined key or non map is encountered while
#         recursing.
#
# For the following map,
#
# A = { a : {
#       'aa' : {
#         'aaa' : 1,
#         },
#       },
#     }
#
# WalkMap(A, ('a',)) returns { 'aa' : { 'aaa' : 1 } }
# WalkMap(A, ('a', 'aa', 'aaa')) returns 1
#
def WalkMap(map, var_path):
  value = map
  for var in var_path:
    try:
      value = value[var]
    except TypeError, e:
      raise KeyError, e
  return value

# WalkMapSet takes a map, a path, and a value; it will set the object named
# by the path to value.  If it doesn't exist, it will be created.  It's parent
# object (var_path[:-1]) is expected to exist.
# Throws: KeyError if any of the parent's names are undefined or are not maps
def WalkMapSet(map, var_path, value):
  inner_map = WalkMap(map, var_path[:-1])
  try:
    inner_map[ var_path[-1] ] = value
  except TypeError, e:
    raise KeyError, e

def makeTupleName(name):
  if type(name) in (types.ListType, types.TupleType):
    var_path = tuple(name)  # make sure lists turn into tuples
  else:
    var_path = (name,)

  assert len(var_path) >= 1
  return var_path

# FilterErrorsByKeyPath takes a validatorlib.Validator return code and filters
# out error codes which belong to the given tuple variables
def FilterErrorsByKeyPath(key_path, errors):
  if errors in validatorlib.VALID_CODES:
    return errors

  filtered_errors = []
  for error in errors:
    keep = 0
    if error.attribs.has_key('KEY_PATH'):
      # it has a KEY_PATH attrib; keep it _only_ if the error happened in
      # our keypath, or in one of it's submaps
      is_prefix = lambda a,b: tuple(a) == tuple(b[:len(a)])
      keep = is_prefix(key_path, error.attribs['KEY_PATH'])
    elif error.attribs.has_key('KEY'):
      # it has a KEY attrib; keep it _only_ if it's the start of our key path
      keep = error.attribs['KEY'] == key_path[0]
    else:
      # no distinguishing attribs; we have to assume that it belongs to our
      # key path
      keep = 1
    if keep:
      filtered_errors.append(error)

  errors = filtered_errors
  if len(errors) == 0: errors = validatorlib.VALID_OK

  return errors

# Cache for holding fully execed defaults data.  This is a map:
#   (config_dir, default_file1, ...) ->
#   (config_namespace, [default_file_mtime1, ..])
# This dramatically improves performance in loading multiple configs.
# The cache is refreshed if the current mtimes for the default files
# is different from what is held in the cache ensuring that we cache
# only the latest defaults information.
_DEFAULTS_CACHE = {}

###############################################################################
#
# The Config object is a container for variable settings and the
# servers map.  When the Config object is loaded, the SERVERS map
# is processed and split out into three separate maps:
#
#   servers map: contains regular servers without replicas and
#     without balancers on the ports that they balancer.  balancers
#     are found on their statusz port (942[0-8]) in this map.
#   balancers map: contains all balancers on the ports that they balance.
#   replicas map: contains all replicas.
#
#
# NOTE: this object is thread unsafe (because we don't want to use the
#  threading module. Implemnet the functions at the end of the class in order to
#  make it thread save. threadsafegoogleconfig.ThreadsafeConfig implemnets those
#
class Config:

  #
  # __init__ - initialize a googleconfig object.
  #
  def __init__(self, config_file=None, config_dir=None):

    self.SetConfigDir(config_dir)
    self.SetConfigFileName(config_file, config_dir=config_dir)

    # Where we replicate the config by default
    self.default_replicas_    = None

    # If the config can be written back to the disk
    self.writable_ = 1

    # Initialize the locks
    self.init_locks()

    # Map based vars.  This turns on the really complex and expensive
    # enterprise specific walkmaptuple kind of behavior.
    self.map_vars_ = 0

    # Initilaize all the data members
    self.common_init()

  #
  # This initilalizes the internal structures (for __init__ and Load)
  # note that this is *private*
  #
  def common_init(self):

    self.params_lock_.acquire()
    try:
      # Initalize all our data with empty stuff (we need it here for functionality
      # and in __init__ for pychecker
      # Data scope from the executed configfile.
      self.data_             = {}

      # Server manager.
      self.srv_mgr_ = serverlib.ServerManager()

      # Ports that are not owned by this config but shared from other configs.
      self.shared_ports_     = []
      # All ports.
      self.all_ports_ = []
      # Cache for holding generated misc. data.
      self.cache_ = {}
      # Map of port -> [host list].
      self.servers_ = {}
      # Map of port -> [balancer list].
      self.balancers_ = {}
      # Map of port -> [replica list].
      self.replicas_ = {}
      # Map of typelvl -> number of shards in servers map.
      self.num_shards_ = {}

      # The current config namespace that hold and manipulate data_
      self.params_ = config_namespace.ConfigNameSpace(self.data_)

      # Variables that are specified in the config itself (and
      # not in the defaults).
      self.specified_vars_ = []
      # The list of invalid parameters
      self.invalid_params_ = []
      # A map from file name to machine params where to distribute
      self.to_distribute_  = {}
      # The id for the next config manager request
      self.config_manager_id_ = 0

      # Validation context
      self.validator_context_ = validatorlib.ValidatorContext(file_access=1,
                                                              dns_access=0)
      # Validation typemap
      self.type_map_ = self.params_.type_map

      # The files that are loaded when this config is loads
      self.loaded_files_ = []

    finally:
      self.params_lock_.release()

    # set all required parameters as invalid; they will remain so until they
    # are defined with valid values
    self.set_list_validation_status(self.GetVarsToIgnore(), 0)

  #
  # Here init all the locks your way. There are four locks thar are used
  #
  # NOTE: Override these and to set the locks to the actual threading
  #       This function is *protected*
  #
  # -- lock for params_ (*reentrant*)
  # -- lock for to_distribute_
  # -- lock for invalid_params_
  # -- lock for config_manager_id_
  #
  def init_locks(self):
    self.params_lock_         = _DummyLock()  # locks params_
    self.distr_lock_          = _DummyLock()  # locks to_distribute_
    self.invalid_params_lock_ = _DummyLock()  # locks invalid_params_
    self.config_manager_lock_ = _DummyLock()  # locks config_manager_id_
    return

  #
  # AddDefaults - load the defaults into this config.
  #
  def AddDefaults(self, config_dir=None):

    # Optimization for caching defaults.
    global _DEFAULTS_CACHE

    self.params_lock_.acquire()
    try:

      # Read the defaults into params_
      defaults = ['config.default']

      # Augment the defaults with default files specified in the config.
      defaults = defaults + \
        map(lambda x: 'config.default.' + x, self.var('DEFAULTS', []))

      # Key used to uniquely identify this set of defaults is based
      # on filenames and configdir.  It's fine I think not to worry
      # about the cache getting too large as the number of combinations
      # of these should be very low.
      # We also check all file timestamps with what we have cached
      # in case any of the files were modified.
      defaults_key = tuple([config_dir] + defaults)
      default_times = []
      for default in defaults:
        path = configutil.GetConfigFilePath(default, config_dir=config_dir)
        if not os.path.exists(path):
          raise IOError, 'Defaults file not found: %s' % path
        if path not in self.loaded_files_:
          self.loaded_files_.append(path)
        mtime = os.path.getmtime(path)
        default_times.append(mtime)

      cache_info = _DEFAULTS_CACHE.get(defaults_key)

      # First check if we have set in cache and times all match.
      if cache_info and cache_info[1] == default_times:
        # Do not deepcopy since each validatorlib object is only read only.
        # Each defaults file creates a very large number of objects that
        # so not deepcopying gives a dramatic improvement in efficiency.
        default_data = copy.copy(cache_info[0])
      # Otherwise load from scratch and save into the cache.
      else:
        default_data = config_namespace.ConfigNameSpace({})
        for file in defaults:
          default_data.ExecFile(file, config_dir=config_dir)
        _DEFAULTS_CACHE[defaults_key] = (copy.copy(default_data), default_times)

      # Merge it into the current namespace
      default_data.MergeNamespace(self.params_, 1)
      self.params_ = default_data

      # Data got tainted.. set it back it to namespace/typemap.
      # TODO: remove having multiple variables pointing to same data.
      self.data_ = self.params_.namespace
      self.type_map_ = self.params_.type_map

    finally:
      self.params_lock_.release()

  #
  # Load - load configuration data from a file.
  # There are three loading options.
  #
  #   do_includes: specifies whether the INCLUDE directive for including
  #     files should be executed.  Should we make the default 1?
  #     this depends on what most people want.
  #
  # At some point we'll allow remote loading by referencing a
  # remote loading library.
  #
  # Note that many of the methods in this class work on precomputed
  # data from the raw config data.  If you change the raw config data
  # this information will no longer be valid (i.e. you add a server
  # to the SERVERS dictionary).
  #
  def Load(self, configfile = None, do_includes=1, add_defaults=1,
           config_dir=None):

    self.SetConfigDir(config_dir)
    if configfile:
      if type(configfile) == types.StringType:
        self.config_file_ = configutil.GetConfigFilePath(
          configfile, config_dir = config_dir)
      else:
        self.config_file_ = configfile
    else:
      configfile = self.config_file_

    # Clean up everything (back to a pristine state)
    self.common_init()

    self.params_lock_.acquire()
    try:

      # Load the parameters in the params_ namespace
      (self.params_, self.shared_ports_, self.loaded_files_) = \
                     configutil.LoadConfigData(
        configfile, do_includes = do_includes, config_load_dir=config_dir)

      # Variables specified in config file itself.
      self.specified_vars_ = self.params_.namespace.keys()

      # Add the defaults
      if add_defaults:
        self.AddDefaults(config_dir=config_dir)

      # Data got tainted.. set it back it to namespace/typemap
      # TODO: remove having multiple variables pointing to same data.
      self.data_ = self.params_.namespace
      self.type_map_ = self.params_.type_map

      # Extract servers information from 'SERVERS'.
      self.extract_servers()

      # Update derived information.
      self.update_derived_info()

    finally:
      self.params_lock_.release()

    return 1

  # Print using pprint generally but with some overrides
  # to make dictionaries look nicer.
  def _PrintObject(self, obj, indent=2):
    pp = pprint.PrettyPrinter(indent=indent)
    if type(obj) != types.DictionaryType:
      return pp.pformat(obj)
    ret = []
    ret.append('{')
    keys = obj.keys()
    keys.sort()
    for key in keys:
      ret.append((' ' * indent) + '%s : %s,' %
                 (pp.pformat(key), pp.pformat(obj[key])))
    ret.append('}')
    return string.join(ret, '\n')

  #
  # Save the config file data.  Generally it only makes sense
  # to save out a config file if the config is not loaded
  # with do_includes=1 and the defaults have not been applied
  # to the config (see AddDefaults()).  Else all these values
  # will be embedded in the saved file.
  #
  # configfile: either a file name or a file-like object.  If not
  #   specified or None, will print to stdout.
  # comment: a header to be prepended at top of config file.
  #
  # This saves all the parameters to be saved in the config file
  # specified by filename. If filename is None ti will save to
  # config_file_
  #
  # It writes first to a temp then it moves the tmp to the destination
  #
  def Save(self, configfile=sys.stdout, comment=None):

    if self.ReadOnly(): # If the config is read only
      return 1

    # If the config file is none we default to self.config_file_ if non None
    # or to stdout
    if configfile == None:
      if self.config_file_ == None:
        configfile = sys.stdout
      else:
        configfile = self.config_file_

    self.params_lock_.acquire()

    try:
      # Reorder variables (SERVERS, DATA_DIRS, etc). We do this mostly
      # for readability reasons. Users expect SERVERS map to be last,
      # DATA_DIRS to be first etc. So, we reorder them accordingly.
      special = ['DATA_DIRS', 'NEWER_TIME', 'INCLUDES', 'INDEXNAME']

      text = []

      # Write header.
      text.append('# #-*-Python-*-\n#')

      # Write comment.
      if comment:
        text.append('# %s' % comment)

      # Write date.
      date_str = time.asctime(time.localtime(time.time()))
      text.append('# Generated On: %s\n#\n' % date_str)

      # Write standard variables.
      text.append('# STANDARD VARIABLES\n')
      for var in special:
        if not self.has_var(var):
          continue
        text.append('%s = %s\n' % (var, self._PrintObject(self.var(var))))

      # Write user variables.
      text.append('# USER VARIABLES\n')
      keys = self.GetVarsToWrite()
      keys.sort()
      for var in keys:
        if var in special or var == 'SERVERS':
          continue
        text.append('%s = %s' % (var, self._PrintObject(self.var(var))))

      # Write servers map.
      text.append('\n# SERVERS MAP\n')
      if self.has_var('SERVERS'):
        text.append('%s = %s' % ('SERVERS', self.GetServerManager().AsString()))
    finally:
      self.params_lock_.release()

    text = '%s\n' % string.join(text, '\n')

    # Do the actual save
    if type(configfile) == types.StringType:
      # We write to a file in three steps:
      # 1. Open a temporary file
      # 2. Write the data to the temporary file and sync on disk
      # 3. Rename the temp file to the actual file
      tmp = "%s__temp" % configfile
      try:
        fd = open(tmp, 'w')
        try:
          fd.write(text)
          os.fdatasync(fd.fileno()) # put it on the disk
        finally:
          fd.close()
      except IOError:
        return 0
      try:
        os.rename(tmp, configfile)
      except OSError:
        return 0
      self.add_file_to_distribute(configfile, self.default_replicas_)
    else:
      configfile.write(text)

    return 1

  #
  # Save the config file assuming only servers map has changed.
  # This just uses a regexp to replace the servers map.  No other
  # config changes will be reflected.
  #
  def SaveServers(self, filename=None):

    # Return data with dictionary named var containing new value.
    def sub_dict(data, var, value):

      # We don't just sub with a regular expression across
      # whole dict as the regexp I had caused a stack
      # overflow.  There's probably a better way to make the
      # regex but the following works just as well (although a bit
      # uglier).
      p = re.compile('\s+%s\s*=\s*{' % var)
      m = p.search(data)
      pre = data
      post = ''
      if m:
        pre = data[:m.start()]
        post = data[m.end():]
        idx = string.find(post, '}')
        if idx != -1: post = post[idx+1:]

      return pre + value + post

    # If the config file is none we default to self.config_file_ if non None
    # or to stdout
    if filename == None:
      filename = self.config_file_

    # Read in original config file.
    f = open(self.config_file_, "r")
    try:
      data = f.read()
    finally:
      f.close()

    # Generate the server string and substitute in.
    srv_string = '\n\nSERVERS = %s' % self.GetServerManager().AsString()
    data = sub_dict(data, 'SERVERS', srv_string)

    # Generate the replacements string and substitute in.
    repl = self.var('REPLACEMENTS', {})
    if repl:
      repl_string = '\n\nREPLACEMENTS = %s' % self._PrintObject(repl)
      data = sub_dict(data, 'REPLACEMENTS', repl_string)

    # Write out modified file.
    f = open(filename, "w")
    try:
      f.write(data)
    finally:
      f.close()

  #############################################################################
  #
  # Parameter Manipulation
  #

  # var - Get variable value.
  #
  # Unfortunately, this is a combination of .get() func and []
  # func.  It will raise a KeyError if var is not found and default != None.
  def var(self, var, default=None):

    if self.map_vars_:
      var_path = makeTupleName(var)

    self.params_lock_.acquire()
    value = None
    try:
      try:
        if self.map_vars_:
          value = WalkMap(self.params_.namespace, var_path)
        else:
          value = self.params_.namespace[var]
      except KeyError, e:
        if default != None: return default
        else: raise KeyError, e
    finally:
      self.params_lock_.release()

    return value

  #
  # has_var - Test for existence of variable in config data.
  #
  def has_var(self, var):

    if not self.map_vars_:
      return self.params_.namespace.has_key(var)

    var_path = makeTupleName(var)
    try:
      WalkMap(self.params_.namespace, var_path)
    except KeyError:
      return 0
    return 1

  #
  # var_copy - Gets a vopy  value of a variable.
  # As opposed to var, this function returns copies of the dictionaries/lists
  # so they can be changed without affecting the actual value.
  # More, this function does not get upset if the variable is not defined
  # it simply returns None
  #
  def var_copy(self, name):
    try:
      return copy.deepcopy(self.var(name))
    except KeyError:
      return None

  #
  # set_var - updates a parameter and validates it (if requested).
  # It returns a list of validation errors ( validatorlib.VALID_OK on success )
  # NOTE: Use this with caution as this may cause pre-computed data to
  # get stale.
  #
  def set_var(self, name, value, validate = 0):
    var_path = makeTupleName(name)

    isvalid = 0

    self.params_lock_.acquire()
    try:
      if validate:
        errors = self.ValidateValue(name, value)
        if not errors in validatorlib.VALID_CODES:
          prodlib.log("ERROR: Invalid value [%s] for parameter [%s] err %s" % (
            value, name, repr(errors)))
          return errors
        isvalid = 1

      # We are OK to set the value if we are here
      WalkMapSet(self.params_.namespace, var_path, value)

      # The user has updated the SERVERS variable - update derived info.
      if var_path[0] in self.get_derived_info_dependencies():
        self.extract_servers()
        self.update_derived_info()

    finally:
      self.params_lock_.release()

    self.set_validation_status(name, isvalid)

    return validatorlib.VALID_OK

  def del_var(self, name):
    var_path = makeTupleName(name)

    self.params_lock_.acquire()
    try:
      if not self.has_var(name): return 0
      inner_map = WalkMap(self.params_.namespace, var_path[:-1])
      try:
        del inner_map[ var_path[-1] ]
      except TypeError, e:
        raise KeyError, e
    finally:
      self.params_lock_.release()
    return 1

  #
  # set_file_var_content - Updates the contents for a file parameter -
  # this requires that the parameter exists and is set to a valid filename.
  #  returns: validatorlib.VALID_OK on succes / a list of ValidationErrors
  #
  # EXPLANATION:
  #  When you have a parameter that actually designates a file and you want to
  #  change the content of the file (that needs validation). For example
  #  STARTURLS is a parmaetre that contains the file name for the urls
  #  from which we want to start the crawl. The value of the parameter can
  #  be something like "/root/googledata/googlebot/starturls.crawl" but
  #  the file can contains something like
  #  "http://www.yahoo.com/\nhttp://www.stanford.edu/\n"
  #  set_file_var_content sets and validates the content of that file (that the
  #  file is actualy a \n sepparated list of fully qualified urls)..
  #
  def set_file_var_content(self, name, value, validate):
    file_name = self.var(name)
    if None == file_name:
      return [validatorlib.ValidationError("Invalid parameter %s" % (name,))]

    self.params_lock_.acquire()
    try:
      tmp_file_name = "%s_tmp" % file_name
      try:
        file_out = open(tmp_file_name, "w")
      except IOError, e:
        return [validatorlib.ValidationError(
          "Cannot save file for %s - %s" % (name, e))]
      
      try:
        file_out.write(value)
      except UnicodeError, e:
        logging.info('Converting value to utf-8. %s' % str(e))
        file_out.write(value.encode('utf-8'))

      file_out.close()
      isvalid = 0
      if validate:
        errors = self.ValidateValue(name, tmp_file_name)

        if not errors in validatorlib.VALID_CODES:
          os.remove(tmp_file_name)
          return errors
        isvalid = 1

      try:
        os.rename(tmp_file_name, file_name)
      except OSError, e:
        return [validatorlib.ValidationError(
          "Error renaming file for parameter %s - %s" % (name, e))]

    finally:
      self.params_lock_.release()

    self.set_validation_status(name, isvalid)
    self.add_file_to_distribute(file_name, self.default_replicas_)

    return validatorlib.VALID_OK

  def del_file_var_content(self, name):
    """
    This deletes the file associated with a file parameter.
    """
    if not self.has_var(name):
      prodlib.log("ERROR: Invalid parameter %s" % (name,))
      return 0

    file_name = self.var(name)

    self.params_lock_.acquire()
    try:
      try:
        os.unlink(file_name)
      except OSError:
        pass
    finally:
      self.params_lock_.release()

    self.add_file_to_distribute(file_name, self.default_replicas_,
                                delete_file = 1)
    return 1

  #############################################################################

  # Magic to make parameters in namespace appear as attributes of this object
  def __getattr__(self, name):
    if self.__dict__.has_key(name):
      return self.__dict__[name]
    # if name is "params_" then it must not be defined yet (or we wouldn't
    # be here) -- so avoid infinite recursion
    if name != "params_" and self.params_.namespace.has_key(name):
      return self.params_.namespace[name]
    raise AttributeError(name)

  #############################################################################
  #
  # Validation
  #

  #
  # get_validator() - returns the validator for a specified var. If no
  #   validator specified, returns None
  #
  def get_validator(self, name):
    self.params_lock_.acquire()
    ret = self.type_map_.get(name, None)
    self.params_lock_.release()
    return ret

  def set_validator(self, name, validator):
    self.params_lock_.acquire()
    self.type_map_[name] = validator
    self.params_lock_.release()

  #
  # get_validation_context() - returns context that is used for validation
  #
  def get_validation_context(self, _):
    return self.validator_context_

  #
  # GetValidationStatus - return the number of parameters still invalid
  #
  def GetValidationStatus(self):
    """ returns if all parms are valid """
    self.invalid_params_lock_.acquire()
    ret = len(self.invalid_params_) == 0
    self.invalid_params_lock_.release()
    return ret

  #
  # ValidateValue - validates a value, using the validator for the given
  # parameter: if the value satisfies the validator. Returns a validation
  # code / error.
  # valid if return is in validatorlib.VALID_CODES
  #
  def ValidateValue(self, name, value):
    var_path = makeTupleName(name)

    self.params_lock_.acquire()
    try:
      # We only have validators for base parameters, not values inside
      # nested maps (tuple variable names).  Here's what we do to
      # allow tuple variable names:
      # 1. make a copy of the current *base parameter* (var_path[0])
      # 2. update the tuple var *inside* the copy with value
      # 3. run the validator for the *base parameter* on this modified copy
      # 4. filter out any validation errors that weren't caused by the var
      #    we're interested in
      if len(var_path) >= 2:
        # make a copy of the base value
        try:
          validate_value = copy.deepcopy(self.params_.namespace[ var_path[0] ])
          WalkMapSet(validate_value, var_path[1:], value)
        except KeyError:
          # base value doesn't exist, or isn't map
          return [ validatorlib.ValidationError('Invalid Paramter %s' % (name,)) ]
      else:
        # this is really a base value, no need for a copy
        validate_value = value

      validator = self.type_map_.get(var_path[0], None)
      if validator == None:
        errors = validatorlib.VALID_OK # easy -- no validator
      else:
        errors = validator.validate(validate_value,
                                    self.validator_context_)

      if len(var_path) >= 2:
        # filter out any validation errors not caused by name
        errors = FilterErrorsByKeyPath(var_path[1:], errors)

    finally:
      self.params_lock_.release()

    return errors

  #
  # ValidateVar - validates a single parameter: if the value from
  # params_ satisfies the validator. Returns a validation code / error.
  # valid if return is in validatorlib.VALID_CODES
  #
  def ValidateVar(self, name, context=None):

    if context == None:
      context = self.validator_context_

    var_path = makeTupleName(name)

    self.params_lock_.acquire()
    try:
      if not self.has_var(name):
        return [ validatorlib.ValidationError('Invalid Paramter %s' % (name,)) ]

      # We only have validators for base parameters, not values inside
      # nested maps (tuple variable names).  Here's what we do to
      # allow tuple variable names:
      # 1. run the validator for the *base parameter* (var_path[0]) on the
      #    *base parameter*.
      # 2. filter out any validation errors that weren't caused by the var
      #    we're interested in
      validator = self.type_map_.get(var_path[0], None)
      if validator == None:
        errors = validatorlib.VALID_OK
      else:
        errors = validator.validate(self.var(var_path[0]),
                                    context)

      if len(var_path) >= 2:
        # filter out any validation errors not caused by name
        errors = FilterErrorsByKeyPath(name[1:], errors)

    finally:
      self.params_lock_.release()

    ok = errors in validatorlib.VALID_CODES

    self.set_validation_status(name, ok)
    return errors

  #
  # ValidateVars - This validates a bunch of parameters -- returns a bool
  #
  def ValidateVars(self, names):
    ok = 1
    for name in names:
      ok = (self.ValidateVar(name) in validatorlib.VALID_CODES) and ok
    return ok

  #
  # ValidateInvalid - Try to re-validate all the parameters previously
  #  declared invalid
  #
  def ValidateInvalid(self):
    return self.ValidateVars(self.GetInvalidNames())

  #
  # ValidateAll - validates all parameters that have to be validates
  #
  def ValidateAll(self):
    # we want to validate everything, except what we're explicitly asked to
    # ignore
    to_ignore = self.GetVarsToIgnore()
    to_validate = setlib.diff(self.GetAllVars(), self.GetVarsToIgnore())
    return self.ValidateVars(to_validate)

  #
  # GetInvalidNames - return the names of all parameters that we not
  #  validated correctly
  #
  def GetInvalidNames(self):
    """ This puts all the invalid params in a list """
    ret = []
    self.invalid_params_lock_.acquire()
    ret.extend(self.invalid_params_)
    self.invalid_params_lock_.release()
    return ret

  #
  # ValidateConfig - validate all variables in the configuration file.
  # file_validation determines whether to validate file type
  # variables.
  #
  def ValidateConfig(self, file_validation=0, specified_only=0):
    """
    Validates all parameters in a config file
    """
    # Update file validation.
    self.invalid_params_lock_.acquire()
    old_val = validatorlib.is_file_validation_disabled()
    validatorlib.set_no_file_validation(not file_validation)
    self.invalid_params_lock_.release()

    try:
      ret = []
      if specified_only:
        vars = setlib.diff(self.specified_vars_, self.GetVarsToIgnore())
      else:
        vars = setlib.diff(self.GetAllVars(), self.GetVarsToIgnore())
      if not self.ValidateVars(vars):
        for p in self.GetInvalidNames():
          errors = self.ValidateVar(p)
          out = []
          for err in errors:
            out.append("%s : %s" % (err.message, repr(err.attribs)))
            ret.append((p, self.var(p), string.join(out, ",")))
    finally:
      # Restore file validation.
      self.invalid_params_lock_.acquire()
      validatorlib.set_no_file_validation(old_val)
      self.invalid_params_lock_.release()

    return ret


  #############################################################################
  #
  # Paramters Update
  #

  #
  # This writes a config manager request. returns the boolean success status
  #
  def WriteConfigManagerRequest(self, req, dir = None):
    """ Writes a config manager request on the current machine .. requires
    a distribute all at the end """
    # Get the filename and id (the later used to order requests written at
    # the same second
    (id, filename) = self.get_next_config_manager_request_file_id(dir)
    try:
      try:
        prodlib.log("Saving cmrequest to %s" % filename)
        req.Write(filename, id)
      except OSError:
        prodlib.log("ERROR: OS Error saving to request file %s" % filename)
        return 0
    except IOError:
      prodlib.log("ERROR: IO Error creating the request file %s" % filename)
      return 0
    self.add_file_to_distribute(filename, self.default_replicas_)
    return 1

  #############################################################################

  def __ConvertDataDirPort(self, port):
    """Convert a port for data dir purposes.
    Args:
      port - input port.
    Returns:
      port - translated port.

    This method converts a port based on the SHARED_DATA_DIRS map.
    This is a map of mtype -> mtype.  It is used to say that one
    type should mimic the data dir name of another type.  The port
    returned is the corresponding port on the same shard of the
    shared type.
    """

    typelvl = servertype.GetTypeLevel(port)
    (mtype, lvl) = servertype.SplitTypeLevel(typelvl)
    if self.has_var('SHARED_DATA_DIRS'):
      mtype = self.var('SHARED_DATA_DIRS').get(mtype, mtype)
    port = servertype.GetPortShard(port) + servertype.GetPortBase(mtype) + \
      servertype.GetLevelSize(mtype) * lvl
    return port

  #
  # GetBaseDataDir - Get the full path to the -data directory for this
  # type of machine.  This function contains the logic that maps a given machine
  # type to the directory_type that it uses.
  #
  # NOTE: This function is internal and should (almost) never be called
  #       directly. Use GetDataDir instead.
  #
  def GetBaseDataDir(self, port):

    data_dirs = self.var('DATA_DIRS')

    port = self.__ConvertDataDirPort(port)
    typelvl = servertype.GetTypeLevel(port)
    (mtype, lvl) = servertype.SplitTypeLevel(typelvl)

    # setup the default data_type
    # TODO: This defaulting scheme is pretty odd - we should make
    # it more intuitive. - i.e. for a doc:1, we never examine the
    # doc:1 entry unless a doc:0 entry exists in the map - defaults
    # to google:1.
    if mtype in data_dirs.keys():
      data_type = mtype         # some types have their own schedule
    else:
      data_type = "google"      # default for everyone else

    lvl_key = "%s:%d" % (data_type, lvl)
    if data_dirs.has_key(lvl_key):
      data_dir = data_dirs[lvl_key]
    elif data_dirs.has_key(data_type):
      data_dir = data_dirs[data_type]
    else:
      msg = "No data dir '%s' for %s:%d machine" % (data_type, mtype, lvl)
      raise RuntimeError, msg

    return data_dir

  #
  # GetDataDir - get the data dir associated with a machine port.
  # We want to allow multiple shards on same machine so we need to
  # separate the datadirs by port (to avoid clashes on filesums names
  # and/or search.config).
  #
  def GetDataDir(self, port, shareable=1):

    data_dir = self.GetBaseDataDir(port)

    if shareable:
      port = self.__ConvertDataDirPort(port)

      # Find the server set related to this port.
      mtype = servertype.GetPortType(port)
      set = self.GetServerManager().Set(mtype)

      # We shouldn't hit this code except for balancers.  Balancers
      # will not be able to override the datadir_has_port setting
      # in the config due to the old use of 9420 v. '+index'.
      if not set: set = serverlib.ServerSet(self.GetServerManager(), mtype, 0)

      if set.property('datadir_has_port'):
        data_dir = string.replace(data_dir, '-data', '.%s-data' % port)
      if data_dir[-1] == '/':  data_dir = data_dir[:-1]

    return data_dir

  #
  # GetDataVersion - Returns the data-version (which is normally the
  # (unmunged) datadir for the specified typelvl)
  # Eg. /export/hda3/jul02index-data
  #
  def GetDataVersion(self, typelvl):

    (mtype, _) = servertype.SplitTypeLevel(typelvl)

    if self.has_var('SHARED_DATA_DIRS'):
      mtype = self.var('SHARED_DATA_DIRS').get(mtype, mtype)

    # See comment in GetDataDir.
    set = self.GetServerManager().Set(mtype)
    if not set: set = serverlib.ServerSet(self.GetServerManager(), mtype, 0)

    if not set.property('has_datadir') or \
       not set.property('supports_dataversion'):
      dataversion = ''
    elif set.property('datadir_has_port'):
      # use short dirname for types that can handle strict versioning.
      # This allow us to share balancers across shards for these types.
      dataversion = self.GetDataDir(servertype.GetPortBase(typelvl),
                                    shareable=0)
    else:
      # use full datadir for versioning for most types (ie. including port!)
      dataversion = self.GetDataDir(servertype.GetPortBase(typelvl))

    return dataversion

  #
  # GetConfigFileName - returns the config file name
  # This is the full path of the config file.
  #
  def GetConfigFileName(self):
    return self.config_file_

  #
  # SetConfigFileName - set config file name.
  #
  def SetConfigFileName(self, config_file, config_dir=None):
    if type(config_file) == types.StringType:
      self.config_file_ = configutil.GetConfigFilePath(config_file,
                                                       config_dir=config_dir)
    else:
      self.config_file_ = config_file

  #
  # GetConfigDir - returns the config dir if an override was provided
  # for GOOGLBASE.  This may not be the same as the path for the
  # config file name if the config file was loaded with an explicit path.
  #
  def GetConfigDir(self):
    return self.config_dir_

  #
  # SetConfigDir - set config dir.
  #
  def SetConfigDir(self, config_dir):
    self.config_dir_ = config_dir

  #
  # GetCurrentConfigFile - get the config file name of
  # an active config file from the CURRENT_CONFIG setting.
  #
  def GetCurrentConfigFile(self):
    if self.has_var('CURRENT_CONFIG'):
      return self.var('CURRENT_CONFIG')
    else:
      return None

  #
  # GetServiceName - get service name of this config file.
  # Returns None if this config is not found in the services file.
  #
  def GetServiceName(self):
    if not self.var('COLOC', ''): return None
    try:
      factory = mainconfig.Factory(self.var('COLOC'),
                                     config_dir=self.config_dir_)
      return factory.GetServiceName(os.path.basename(self.GetConfigFileName()))
    except IOError:
      return None

  #
  # GetGroupName - get top level group name of this config file.
  # This is considered the configs group.  Returns None if this
  # config is not found in the services file.
  #
  def GetGroupName(self):
    if not self.var('COLOC', ''): return None
    try:
      factory = mainconfig.Factory(self.var('COLOC'),
                                     config_dir=self.config_dir_)
      return factory.GetGroupName(os.path.basename(self.GetConfigFileName()))
    except IOError:
      return None

  #
  # GetServiceGroups - get list of service ancestors for this configfile.
  # Returns None if this config is not found in the services file.  The
  # list of service ancestors includes the service name of this config
  # plus any higher level groups that this service belongs to - as specified
  # in the services file.
  #
  def GetServiceGroups(self):
    if not self.var('COLOC', ''): return None
    try:
      factory = mainconfig.Factory(self.var('COLOC'),
                                     config_dir=self.config_dir_)
      return factory.GetServiceGroups(os.path.basename(self.GetConfigFileName()))
    except IOError:
      return None

  #
  # GetLoadedFiles - Returns the files loaded for this config
  #
  def GetLoadedFiles(self):
    return self.loaded_files_

  #
  # SetReadOnly - sets if the config is writable to the disk
  #
  def SetReadOnly(self):
    self.writable_ = 0

  #
  # ReadOnly - returns true if config is read only
  #
  def ReadOnly(self):
    return not self.writable_

  #############################################################################

  #
  # GetServerManager: get a pointer to the server manager for this config.
  #
  def GetServerManager(self):
    return self.srv_mgr_;

  #
  # If typelvel = None, all ports are returned, else ports limited
  # to the given typelvl are returned.
  #
  # DEPRECATED: Use GetServerManager.
  #
  def GetAllPorts(self):
    ports = self.servers_.keys()
    ports.sort()
    return ports

  #
  # DEPRECATED: Use GetServerManager.
  # GetOwnedPorts - get the list of sorted server ports
  # config file owns.  Servers that are included from other configs
  # and owned are included in this list.  Servers that are included
  # from other configs and are borrowed are not included in this list.
  #
  def GetOwnedPorts(self):
    return filter(lambda p, s=self.shared_ports_:
                  p not in s, self.GetAllPorts())

  #
  # DEPRECATED: Use GetServerManager.
  # GetServerMap - Returns a dictionary of port->host list
  # which match the server types specified in wanted_types (from
  # servertype.CollectTypes).  Note that balancers are not included
  # in this list.
  #
  def GetServerMap(self, wanted_types = {}):
    return configutil.FilterServerMap(self.servers_, wanted_types)

  #
  # DEPRECATED: Use GetServerManager.
  # GetBalancerMap - Returns a dictionary of port->balancer list
  # which match the server types specified in wanted_types.
  # If keep_marker = 1, the '+' marker is prefixed to hostnames.
  #
  def GetBalancerMap(self, wanted_types = {}, keep_marker = 0):
    ret = configutil.FilterServerMap(self.balancers_, wanted_types)
    if not keep_marker: return ret
    retcopy = {}
    for (port, hosts) in ret.items():
      retcopy[port] = map(lambda x: '+' + x, hosts)
    return retcopy

  #
  # DEPRECATED: Use GetServerManager.
  # GetReplicaMap - Returns a dictionary of port->replica list
  # which match the server types specified in wanted_types (from
  # servertype.CollectTypes).
  #
  def GetReplicaMap(self, wanted_types = {}):
    return configutil.FilterServerMap(self.replicas_, wanted_types)

  #
  # DEPRECATED: Use GetServerManager.
  # GetServerHosts - get the list of unique servers assigned to the given
  # port or of type typelvl.  This list does not include balancers
  # or replicas. Returns [] if there are no servers.
  #
  def GetServerHosts(self, port_or_typelvl):
    return remove_dups(map(lambda x: x[0],
                       self.GetServerHostPorts(port_or_typelvl)))

  #
  # DEPRECATED: Use GetServerManager.
  # GetServerHostPorts - get the list of (host, port) assigned to the given
  # port or of type typelvl.  This list does not include balancers
  # or replicas. Returns [] if there are no servers.
  #
  def GetServerHostPorts(self, port_or_typelvl):
    return self.get_host_port_list(self.servers_, port_or_typelvl)

  #
  # DEPRECATED: Use GetServerManager.
  # GetBalancerHosts - get the list of unique balancer hosts assigned to
  # the given port or of type typelvl.  If keep_marker = 1, then the
  # balancer indicator ('+') is not removed from hostname.
  # Returns [] if there are no balancers.
  #
  def GetBalancerHosts(self, port_or_typelvl, keep_marker = 0):
    return remove_dups(map(lambda x: x[0],
                       self.GetBalancerHostPorts(port_or_typelvl, keep_marker)))

  #
  # DEPRECATED: Use GetServerManager.
  # GetBalancerHostPorts - get the list of balancer (host, port) assigned to
  # the given port or of type typelvl.  If keep_marker = 1, then the
  # balancer indicator ('+') is prefixed to hostname.
  # Returns [] if there are no balancers.
  #
  def GetBalancerHostPorts(self, port_or_typelvl, keep_marker = 0):
    hostports = self.get_host_port_list(self.balancers_, port_or_typelvl)
    if not keep_marker: return hostports
    else: return map(lambda x: ('+' + x[0], x[1]), hostports)

  #
  # DEPRECATED: Use GetServerManager.
  # GetReplicaHosts - get the list of unique replica hosts assigned to the given
  # port or of type typelvl. Returns [] if there are no servers.
  #
  def GetReplicaHosts(self, port_or_typelvl):
    return remove_dups(map(lambda x: x[0],
                       self.GetReplicaHostPorts(port_or_typelvl)))

  #
  # DEPRECATED: Use GetServerManager.
  # GetReplicaHostPorts - get the list of replica (host, port) assigned to
  # the given port or of type typelvl. Returns [] if there are no servers.
  #
  def GetReplicaHostPorts(self, port_or_typelvl):
    return self.get_host_port_list(self.replicas_, port_or_typelvl)

  #
  # DEPRECATED: Use GetServerManager.
  # GetReplica - get the replica for the given port.
  #
  def GetReplica(self, mtype, port):
    mtype = mtype    # silence pychecker
    return self.replicas_.get(port, None)

  #
  # DEPRECATED: Use GetServerManager.
  # GetNumShards - get the number of shards present in the config data
  # for a given port or server type level.  TODO: This really shouldn't
  # accept a port.
  #
  def GetNumShards(self, port_or_typelvl):

    typelvl = port_or_typelvl
    if type(port_or_typelvl) == types.IntType:
      typelvl = servertype.GetTypeLevel(port_or_typelvl)
    else:
      typelvl = servertype.NormalizeTypeLevel(typelvl)
    try:
      return self.num_shards_[typelvl]
    except KeyError:
      return 0

  #
  # DEPRECATED: Use GetServerManager.
  # GetPortList - get list of ports for a particular type.
  #
  def GetPortList(self, typelvl):
    typelvl = servertype.NormalizeTypeLevel(typelvl)
    unique_ports = {}
    result = []
    sorted_ports = self.GetAllPorts()
    for port in sorted_ports:
      if not servertype.IsType(port, typelvl):
        continue
      if not unique_ports.has_key(port):
        result.append(port)
      unique_ports[port] = 1
    return result

  #
  # DEPRECATED: Use GetServerManager.
  # GetPortListForHost - get the list of ports that this host has servers on.
  #
  def GetPortListForHost(self, host):
    ports = []
    for port in self.GetAllPorts():
      if host in self.servers_[port]:
        ports.append(port)
    return ports

  ############################################################################
  #
  # Parameter classification and manipulation
  #
  def GetAllVars(self):
    """ Return a map of all defined parameters """

    self.params_lock_.acquire()
    ret = []
    ret.extend(self.params_.namespace.keys())
    self.params_lock_.release()

    return ret

  def GetVarsToIgnore(self):
    """ Return a list of all parameters which we never try to validate """
    vars_to_ignore = self.var_copy('CONFIG_VARS_TO_IGNORE')
    if vars_to_ignore == None:
      return []
    else:
      return vars_to_ignore

  def GetVarsToWrite(self):
    """ Return a list of the parameters that are written to the config file """
    vars_to_write = self.var_copy('CONFIG_VARS_TO_WRITE')

    # Preloaded variables from GetPreloadedScope are variables that
    # are set for convenience that bring in info about the environment.
    # Ideally these would not be needed if we could find a better way
    # to do it but crawl is dependent on these.  We make sure not
    # to write these out.
    if vars_to_write == None:
      no_save_vars = configutil.GetPreloadedScope().keys()
      vars_to_write = filter(lambda x, y=no_save_vars: x not in y,
                             self.GetAllVars())
    return vars_to_write


  def DiffConfigVars(self, config2):
    """
    Compute list of vars that are different.
    Return ( [vars only in this config],
             [vars only in config2 config],
             [vars different and in both configs]
           )
    """
    self.params_lock_.acquire()
    config2.params_lock_.acquire()
    ret = self.params_.DiffNamespace(config2.params_)
    config2.params_lock_.release()
    self.params_lock_.release()
    return ret

  #############################################################################
  #
  # DistributeAll : Distribute all files from to_distribute_ on corresponding
  # machines. to_distribute_ is a map from a paramater name to file list
  # files marked as deleted will be deleted on the remote machines, instead of
  # distributed.
  # The parameter name holds the machines to distribute to
  #
  def DistributeAll(self):
    self.distr_lock_.acquire()
    try:
      def getParamMachines(machines):
        """Given a param, get the machines associated with it"""
        if not machines: return []
        if isinstance(machines, types.DictionaryType):
          m = [];
          m.extend(machines.values())
          machines = m
          reduce(lambda x,y: x.extend(y), machines)
          if len(machines) > 0: machines = machines[0]
        return machines

      def splitFiles(fileSet):
        """split files into delete and distribute sets"""
        to_distribute = []
        to_delete = []
        for file, delete_file in fileSet:
          if delete_file:
            to_delete.append(file)
          else:
            to_distribute.append(file)
        return to_distribute, to_delete

      for param, fileSet in self.to_distribute_.items():
        machines = getParamMachines(self.var(param))
        to_distribute, to_delete = splitFiles(fileSet)

        if len(machines) > 0 and len(to_distribute) > 0:
          prodlib.PutFilesOnMachines(to_distribute, machines, 120, 10)

        if len(machines) > 0 and len(to_delete) > 0:
          # davidw TODO: do the right thing here; ask bogdan
          #prodlib.PutFilesOnMachines(to_delete, machines, 120, 10)
          pass

      self.to_distribute_ = {}
    finally:
      self.distr_lock_.release()

  #############################################################################
  #
  # The methods below are meant to be PRIVATE
  #

  #
  # get_cache - Get item from cache.  It's useful to cache expensive
  # data regarding the config file.  Generally these are used internally
  # but some restart functions might find this useful to use as well.
  #
  def get_cache(self, cache_name, cache_key):
    if not self.cache_.has_key(cache_name):
      self.cache_[cache_name] = {}
    if self.cache_[cache_name].has_key(cache_key):
      return self.cache_[cache_name][cache_key]
    return None

  #
  # put_cache - Put item into config object cache.
  #
  def put_cache(self, cache_name, cache_key, cache_val):
    if not self.cache_.has_key(cache_name):
      self.cache_[cache_name] = {}
    self.cache_[cache_name][cache_key] = cache_val

  #
  # get_derived_info_dependencies - returns a list of var names for which
  # extract_servers() needs to be called
  #
  def get_derived_info_dependencies(self):
    return ['SERVERS']


  #
  # extract_servers - fill in local backwards compatible data structures
  # from the server manager object.
  #
  def extract_servers(self):

    # Update server manager object.
    self.cache_ = {}
    self.srv_mgr_ = serverlib.ServerManager()
    self.srv_mgr_.InitFromConfig(self)
    (self.servers_, self.balancers_, self.replicas_) = \
      self.srv_mgr_.ServerMaps(auto_assigned=1)

  #
  # update_dervied_info - update derived information any
  # time changes have been made to the servers/balancers/replica
  # maps.
  #
  def update_derived_info(self):

    self.cache_ = {}

    # Compute number of shards and store information and override
    # it with anything specified in the config file.  This hack
    # is used by the config.ben420M file.
    self.num_shards_ = configutil.GetNumShards(self.servers_)
    if self.has_var('NUM_SHARDS'):
      for typelvl, numshards in self.num_shards_.items():
        self.num_shards_[typelvl] = \
          self.var('NUM_SHARDS').get(typelvl, numshards)

    # Set owned ports.
    self.all_ports_ = self.servers_.keys()
    self.all_ports_.sort()
    self.shared_ports_.sort()

    # Update SERVERS information.
    self.data_['SERVERS'] = self.srv_mgr_.CombinedServerMap(auto_assigned=0)

  #
  # get_host_port_list - get a tuple of (host, port) pairs for a given type.
  # This method just wraps the calll to GetHostPorts with a layer of
  # caching that dramatically improves performance in doing a large
  # number of restarts.
  #
  def get_host_port_list(self, servers, port_or_typelvl):
    if servers == self.servers_: cname = "servers"
    elif servers == self.balancers_: cname = "balancers"
    elif servers == self.replicas_: cname = "replicas"
    cache_key = (cname, port_or_typelvl)
    cache_name = "get_host_port_list"
    result = self.get_cache(cache_name, cache_key)
    if result: return result
    result = configutil.GetHostPorts(servers, port_or_typelvl)
    self.put_cache(cache_name, cache_key, result)
    return result

  #
  # Sets the validation status for a bunch of params
  #
  def set_list_validation_status(self, names, valid):
    for name in names:
      self.set_validation_status(name, valid)

  #
  # updates invalidParams for the given parameter.  Note that we refuse to
  # invalidate ignored parameters.  Note also that we refuse to validate a
  # parameter just because an inner (tuple) value is valid.
  def set_validation_status(self, name, valid):
    var_path = makeTupleName(name)

    self.invalid_params_lock_.acquire()
    try:
      if valid:
        # never validate based on non-base parameter names
        if len(var_path) == 1 and var_path[0] in self.invalid_params_:
          self.invalid_params_.remove(var_path[0])
      elif ( not var_path[0] in self.GetVarsToIgnore() and
             not var_path[0] in self.invalid_params_ ):
        self.invalid_params_.append(var_path[0])
    finally:
      self.invalid_params_lock_.release()

  #
  # add_file_to_distribute: This function adds to the to distribute
  # list of files (for config replication on other machines)
  # if delete_file is true, the file will be marked as deleted (to be deleted
  # on other machines)
  #
  def add_file_to_distribute(self, fileName, machineParam,
                             delete_file = 0):
    if machineParam == None:
      return

    self.distr_lock_.acquire()
    try:
      if not self.to_distribute_.has_key(machineParam):
        self.to_distribute_[machineParam] = []

      dist_key = (fileName, 0)    # entry we use if we want to distribute file
      delete_key = (fileName, 1)  # entry we use if we want to delete file

      if delete_file:
        # if we were previously asked to dist it, this delete overrides it
        if dist_key in self.to_distribute_[machineParam]:
          self.to_distribute_[machineParam].append(dist_key)
        # remember that we're supposed to delete this file
        self.to_distribute_[machineParam].append(delete_key)
      elif not dist_key in self.to_distribute_[machineParam]:
        # remember to distribute this file
        self.to_distribute_[machineParam].append(dist_key)

    finally:
      self.distr_lock_.release()

  #
  # Returns the name of the next config manager file to use
  #
  def get_next_config_manager_request_file_id(self, dir = None):
    """   """
    self.config_manager_lock_.acquire()
    id = self.config_manager_id_
    self.config_manager_id_ = self.config_manager_id_ + 1
    self.config_manager_lock_.release()

    if not dir:
      dir = self.get_config_manager_req_dir()
    #
    # We write the time of the request for ordering purpose.
    # (We write the gmt time so the timezone change will not
    # reorder the requests)
    #
    filename = "%s_%04d" % \
             (time.strftime("CONFIG_MANAGER_REQUEST_%Y%m%d_%H%M%S",
                             time.gmtime(time.time())), id)
    return (id, "%s/%s" % (dir, filename))

  #
  # get_config_manager_req_dir - returns the dirsctory for the config manager
  # pending requests -- override this as you wish ..
  #
  def get_config_manager_req_dir(self):
    """ Returns the directory for the config manager requests """
    return self.var('CONFIG_MANAGER_REQUEST_DIR')

#
# remove_dups - Utility method for removing duplicates from a list.
# We create an array to append to because we want to preserve the
# order from the original list.
#
def remove_dups(list):
  ret = []
  seen = {}
  for element in list:
    if seen.has_key(element): continue
    ret.append(element)
    seen[element] = 1
  return ret

#!/usr/bin/python2.4

#
# Copyright 2003 Google, Inc.
# All Rights Reserved.
#
# Original Author: Eugene Jhong
#

"""
SegmentData manages segment information for a set of segments.

It contains methods for finding and updating the idle segment
and querying datadir and status information for each segment.

An example segment data config looks like the following.
Each set id is a character starting with 'a'.  Each set is mapped
to a segment number.  The -1 segment number indicates that the
set is the idle set.  For the idle set, DATA_DIRS refers to the
previous data dir that the idle set was serving.

SEGMENT_SET_COUNT = 3
SEGMENT_FILE_PATTERN = 'servers.www.lvl0.%s.sj'
SEGMENT_FILES_COMMON = ['servers.gwd.sj']
DATA_DIRS = { 'google' : '/export/hda3/common200304080000index-data' }

SEGMENT_SET_VARS = {
  'c' : {
    'DATA_DIRS' : { 'google' : '/export/hda3/base200304080000index-data' },
    'BIGINDEX_BALANCER_FILTER' : '/export/hda3/base200304080000index-data/shard*',
    'EPOCH' : 200304080000,
    'SEGMENT' : 0,
  },
  'a' : {
    'DATA_DIRS' : { 'google' : '/export/hda3/base200304100001index-data' },
    'BIGINDEX_BALANCER_FILTER' : '/export/hda3/base200304100001index-data/shard*',
    'EPOCH' : 200304100001,
    'SEGMENT' : 1,
  },
  'b' : {
    'DATA_DIRS' : { 'google' : '/export/hda3/base200304120002index-data' },
    'EPOCH' : 200304120002,
    'SEGMENT' : -1,
  },
}

Example usage:

  seg_data = segment_data.SegmentData(googleconfig.Load('data.www.lvl0.sj'))

  # Print out current idle set id.
  print seg_data.idle_id()

  # Iterate through all segment numbers and find corresponding char set id.
  for i in range(seg_data.num_sets()-1):
    print seg_data.id(i)

  # Iterate through set ids and print info on each set.
  for id in seg_data.ids():
    for key in seg_data.data_dir_keys(id):
      print seg_data.data_dir(id, key)
    print seg_data.bigindex_balancer_filter(id)
    print seg_data.seg_num(id)
    print seg_data.epoch(id)
    print seg_data.config_file(id)

  # Change the idle segment to set a.
  seg_data.set_idle_id('a')

  # Extract the segment number from the datadir
  seg_data.get_segment_from_datadir(seg_data.data_dir('a', 'google'))
"""


import re
import time
import types
import string
import os

"""
This flag is used by clients to determine whether they should fail
on configs that have SEGMENT_TEST_MODE set to 1.  For example, the
babysitter uses this to ensure mixers are not started with backends
that are produced by a test data segment file.
"""
DISALLOW_TEST_MODE = 1

def SetDisallowTestMode(val):
  """
  Set whether to disallow loading segment data files that specify test mode.
  Note this doesn't prevent loading of a test segment data file but is
  just used by clients to check later if a resulting segment config should
  not be used.
  """
  global DISALLOW_TEST_MODE
  DISALLOW_TEST_MODE = val

def DisallowTestMode():
  """
  Get whether to disallow loading segment data files that specify test mode.
  Note this doesn't prevent loading of a test segment data file but is
  just used by clients to check later if a resulting segment config should
  not be used.
  """
  global DISALLOW_TEST_MODE
  return DISALLOW_TEST_MODE


USE_FAKE_DATA = 0

def SetUseFakeData(val):
  """
  Set whether we should replace all data in data files with
  fake consistent data for regression testing.
  """
  global USE_FAKE_DATA
  USE_FAKE_DATA = val

def UseFakeData():
  """
  Get whether we are using fake data.  This is used for regression testing.
  """
  global USE_FAKE_DATA
  return USE_FAKE_DATA

def MakeFakeSetVars(vars, set):
  """
  Build hacked variables for regression test.
  """
  ret = {}
  for key, val in vars.items():
    if type(val) == type({}):
      ret[key] = MakeFakeSetVars(val, set)
    else:
      ret[key] = re.sub(r'\d{12}', '', str(val))
  ret['SEGMENT'] = ord(set) - ord('a')
  return ret


class Error(Exception):
  """
  Base error class for all errors in this module.
  """
  pass

def GetSegmentFromDatadir(data_dir):
  """Parse the datadir and pull out the segment """
  #
  # Datadirs look like this: /export/hda3/base200304080001index-data, parse
  # numbers into Y/M/D/Version/Segment, using a named group for the segment.
  #
  match = re.search(
    '/export/hda3/.*?(20\d\d)(\d\d)(\d\d)(\d\d)(?P<seg>\d\d).*?', data_dir)
  if match:
    return int(match.groupdict()['seg'])
  else:
    return None


class SegmentData:
  """
  Segment data wraps a config data.* file that contains information
  about the current state of the segments for a service.  It accepts
  a googleconfig.Config object that contains the segment information.
  Raises Error if the data file fails validation for any reason.
  """

  def __init__(self, segment_data_cfg, data_file=None):
    """
    Construct a segment data object that has information about idle and
    active segments for a service.  segment_data_cfg is a googleconfig.Config
    object loaded with the raw segment data.  data_file is the name of the
    data file.
    """

    self._data_file = data_file

    # Validate.
    required_vars = ['SEGMENT_FILE_PATTERN', 'SEGMENT_SET_COUNT',
                     'SEGMENT_SET_VARS']

    # Ensure all variables exist.
    for var in required_vars:
      if not segment_data_cfg.has_var(var) or not segment_data_cfg.var(var):
        raise Error('Data file must define %s' % var)

    # Get info from data file.
    self._set_vars = segment_data_cfg.var('SEGMENT_SET_VARS')
    self._file_pat = segment_data_cfg.var('SEGMENT_FILE_PATTERN')
    self._idle_seg = None
    self._files_common = segment_data_cfg.var('SEGMENT_FILES_COMMON', [])
    self._common_data_dirs = segment_data_cfg.var('DATA_DIRS', {})

    num_sets = segment_data_cfg.var('SEGMENT_SET_COUNT')

    # Match SEGMENT_FILE_PATTERN with filename
    file_pat = string.split(self._file_pat, '.')
    file_name = segment_data_cfg.GetConfigFileName()
    _, file_name = os.path.split(file_name)
    file_field = string.split(file_name,'.')

    if file_pat[1:3] != file_field[1:3] or file_pat[-1] != file_field[-1]:
      raise Error('SEGMENT_FILE_PATTERN %s does not match with file name %s' %
                  (self._file_pat, file_name))

    for file_common in self._files_common:
      file_common_field = string.split(file_common, '.')
      if file_common_field[-1] != file_field[-1]:
        raise Error('SEGMENT_FILES_COMMON %s does not match with file name %s' %
                    (file_common, file_name))

    if len(self._set_vars) != num_sets:
      raise Error('Number of sets (%s) in SEGMENT_SET_VARS inconsistent '
                         'with SEGMENT_SET_COUNT (%s)' %
                         (len(self._set_vars), num_sets))

    self._segset_map = {}

    # 2 level dictionary {DATA_DIRS_key: { directory-name: 1,}, }
    dd_rev_map = {}

    # list of all DATA_DIRS keys
    dd_key_list = []

    for i in range(num_sets):

      key = chr(ord('a') + i)

      # Segment sets must all exist in variable map.
      if not self._set_vars.has_key(key):
        raise Error('SEGMENT_SET_VARS does not have key for '
                           'set %s' % key)

      seg_info = self._set_vars[key]
      data_dirs = seg_info.get('DATA_DIRS')

      # Each segment needs a data dir.
      if not data_dirs:
        raise Error('Set %s does not define DATA_DIRS' % key)

      if len(data_dirs) < 1:
        raise Error('Set %s has invalid DATA_DIRS entry' % key)

      # All DATA_DIRS should have the same set of keys
      # directory names should not be duplicate(for a particular DATA_DIR key).
      # Directory names should always be absolute path
      if not dd_key_list:
        dd_key_list = data_dirs.keys()
        dd_key_list.sort()
      else:
        key_list = data_dirs.keys()
        key_list.sort()
        if key_list != dd_key_list:
          raise Error('DATA_DIRS dictionary has different keys in different'
                      ' segments')

      # the directory names for a particular DATA_DIRS key should be unique
      for dd_key, dir in data_dirs.items():
        dd_rev_map[dd_key] = dd_rev_map.get(dd_key, {})
        if dir[0] != '/':
          raise Error('DATA_DIRS value %s is not an absolute path' % dir)
        if dir[-1] == '/': # strip the trailing / before hashing
          dir = dir[:-1]

        value = dd_rev_map[dd_key].get(dir)
        if value is not None:
          raise Error('DATA_DIRS value %s is repeated' % dir)
        else:
          dd_rev_map[dd_key][dir] = 1

      # Each segment needs a segment number.
      if seg_info.get('SEGMENT') is None:
        raise Error('Set %s does not define SEGMENT' % key)

      # But the epoch number and bigindex filter balancer pattern is optional.

      # Build mapping from segment to set.
      self._segset_map[seg_info['SEGMENT']] = key

    for i in xrange(-1, num_sets-1):
      if not self._segset_map.has_key(i):
        raise Error('Missing required SEGMENT: %s' % i)

    # Ensure that extensions match for the data file and the file pattern.
    if type(segment_data_cfg.GetConfigFileName()) == types.StringType:
      if segment_data_cfg.GetConfigFileName()[-3:] != self._file_pat[-3:]:
        raise Error('Colocs for file and SEGMENT_FILE_PATTERN do not match')

    # When regression testing, we want the mapping from sets ('a', 'b', ... )
    # to segments (0, 1, ...) to be fixed so they don't keep switching around.
    if UseFakeData():
      for i in (range(self.num_sets())):
        if i == self.num_sets()-1:
          id = -1
        else:
          id = i
        set = chr(ord('a') + i)
        self._segset_map[id] = set

  def data_file(self):
    """Name of relevant data file."""
    return self._data_file

  def num_sets(self):
    """Return total number of segment sets."""
    return len(self._set_vars)

  def config_file(self, id):
    """Return config file name for set id. """
    return self._file_pat % id

  def common_config_files(self):
    """Return the list of common config files."""
    return self._files_common

  def data_dir_keys(self, id):
    """Return the keys for all data directories in a given set."""
    return self._set_vars[id]['DATA_DIRS'].keys()

  def common_data_dir_keys(self):
    """Return the keys for all common data directories."""
    return self._common_data_dirs.keys()

  def data_dir(self, id, key):
    """Return the data directory for set id."""
    return self._set_vars[id]['DATA_DIRS'][key]

  def common_data_dir(self, key):
    """Return the common data directory."""
    return self._common_data_dirs[key]

  def set_data_dir(self, id, key, data_dir):
    """Set data directory of set id."""
    self._set_vars[id]['DATA_DIRS'][key] = data_dir

  def set_common_data_dir(self, key, data_dir):
    """Set data directory for common configs."""
    self._common_data_dirs[key] = data_dir

  def set_epoch(self, id, epoch):
    """Set epoch number of set id."""
    self._set_vars[id]['EPOCH'] = epoch

  def set_bigindex_balancer_filter(self, id, pattern):
    """Set pattern of bigindex balancer filter files."""
    self._set_vars[id]['BIGINDEX_BALANCER_FILTER'] = pattern

  def seg_num(self, id):
    """Return the segment number for set id: -1 indicates idle set."""
    return self._set_vars[id]['SEGMENT']

  def segs(self):
    """Return a list of segments [-1, ... ]."""
    return range(-1, self.num_sets()-1)

  def epoch(self, id):
    """Return the epoch number for set id: None indicates no epoch."""
    return self._set_vars[id].get('EPOCH', None)

  def bigindex_balancer_filter(self, id):
    """Return pattern for the bigindex balancer filter: None indicates none."""
    return self._set_vars[id].get('BIGINDEX_BALANCER_FILTER', None)

  def ids(self):
    """Return a list of set ids."""
    ids = self._set_vars.keys()
    ids.sort()
    return ids

  def id(self, seg_num):
    """Return the set id for segment with seg_num."""
    return self._segset_map[seg_num]

  def idle_id(self):
    """Return the idle set id."""
    return self._segset_map[-1]

  def set_idle_id(self, idle_id):
    """Set the idle set."""
    seg_num = self._set_vars[idle_id]['SEGMENT']
    self._set_vars[self.idle_id()]['SEGMENT'] = seg_num
    self._set_vars[idle_id]['SEGMENT'] = -1
    self._segset_map[seg_num] = self._segset_map[-1]
    self._segset_map[-1] = idle_id

  def idle_config_file(self):
    """Return the idle config file name."""
    return self.config_file(self.idle_id())

  def AsString(self):
    """Return a string representation of the segment data."""

    output = []

    output.append("#-*-Python-*-\n")
    output.append("# Thank you for using segment_data - generated at %s\n" %
                   time.ctime(time.time()))

    output.append("SEGMENT_SET_COUNT = %d" % len(self._set_vars))
    output.append("SEGMENT_FILE_PATTERN = '%s'" % self._file_pat)
    if self._files_common:
      output.append("SEGMENT_FILES_COMMON = ['%s']" %
                      string.join(self._files_common, "', '"))
      output.append("DATA_DIRS = {")
      for key in self.common_data_dir_keys():
        output.append("  '%s' : '%s'," % (key, self.common_data_dir(key)))
      # end for
      output.append("}")
    # end if
    output.append("\n")
    output.append("# SiteInfo depends on this syntax. If you change it,")
    output.append("# please notify a SiteInfo programmer.\n")
    output.append("SEGMENT_SET_VARS = {")

    for i in (range(self.num_sets()-1) + [-1]):
      id = self.id(i)
      epoch = self.epoch(id)
      bigindex_balancer_filter = self.bigindex_balancer_filter(id)
      output.append("  '%s' : {" % id)
      output.append("    'DATA_DIRS' : {")
      for key in self.data_dir_keys(id):
        output.append("      '%s' : '%s'," % (key, self.data_dir(id, key)))
      output.append("    },")
      if bigindex_balancer_filter:
        output.append("    'BIGINDEX_BALANCER_FILTER' : '%s',"
                      % bigindex_balancer_filter)
      if epoch:
        output.append("    'EPOCH' : %s," % repr(epoch))
      output.append("    'SEGMENT' : %s," % i)
      output.append("  },")
    output.append("}")

    return '\n'.join(output)

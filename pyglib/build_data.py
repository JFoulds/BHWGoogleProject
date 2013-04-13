# Copyright 2005 Google Inc.
# All Rights Reserved.
#
# Author: roth@google.com (Mark D. Roth), dgreiman@google.com (Douglas Greiman)

"""Access to google3 build data"""

import cStringIO
import time

from google3.pyglib import resources


# Global data
_build_dict = None


def _ParseBuildData(filename):
  """Read build data from external file.

  Uses default values if build data file not available.

  Returns dictionary of build data info
  """

  # Start with empty defaults
  build_data = {
    'BUILDINFO' : '',
    'BUILDLABEL' : '',
    'BUILDTOOL' : '',
    'CHANGELIST' : '-1',
    'CLIENTNAME' : '',
    'CLIENTSTATUS' : '-2',
    'DEPOTPATH' : '',
    'PAROPTIONS' : '',
    'PLATFORM' : '',
    'TARGET' : '',
    'TIMESTAMP' : '',
    }

  # Read generated build info if available
  try:
    build_data_str = resources.GetResource(filename)
    # Parse as key/value pairs
    for line in build_data_str.splitlines():
      # Skip comments, blanks, and syntax errors
      if line.startswith('#') or not line.strip() or ':' not in line:
        continue

      key, value = line.split(':',1)
      build_data[key] = value
  except IOError:
    pass  # Build data not available

  return build_data


def _InitBuildData():
  """Read build data from external file, if not already read."""
  global _build_dict
  if not _build_dict:
    _build_dict = _ParseBuildData('google3/pyglib/build_data.txt')


def BuildInfo():
  """Return user, host, and directory of builder, as string"""
  _InitBuildData()
  return _build_dict.get('BUILDINFO', '')


def BuildLabel():
  """Return build label (passed to make-{opt,dbg} -l) as string"""
  _InitBuildData()
  return _build_dict.get('BUILDLABEL', '')


def BuildTool():
  """Return the build tool as string if we know it"""
  _InitBuildData()
  return _build_dict.get('BUILDTOOL', '')


def Changelist():
  """Return client workspace changelist, as int"""
  _InitBuildData()
  cl = _build_dict.get('CHANGELIST', '')
  try:
    changelist = int(cl.strip())
  except ValueError:
    changelist = -1
  return changelist


def ClientInfo():
  """Return Perforce client changelist and status as descriptive string"""
  _InitBuildData()
  info = ''
  cl = Changelist()
  if cl == -1:
    info = ''
  elif cl == 0:
    info = 'unknown changelist'
  else:
    cs = ClientStatus()
    dp = DepotPath()
    if cs == 1:
      status_info = ' in a mint client based on %s' % dp
    elif cs == 0:
      status_info = ' in a modified client based on %s' % dp
    else:
      status_info = ' possibly in a modified client'
    info = 'changelist %d%s' % (cl, status_info)
  return info


def ClientName():
  """Return Perforce client name, as string"""
  _InitBuildData()
  return _build_dict.get('CLIENTNAME', '')


def ClientStatus():
  """Return Perforce client status, as int"""
  _InitBuildData()
  tmp_str = _build_dict.get('CLIENTSTATUS', '')
  try:
    status = int(tmp_str.strip())
  except ValueError:
    status = -1
  return status


def DepotPath():
  """Return Perforce depot path, as string"""
  _InitBuildData()
  return _build_dict.get('DEPOTPATH', '')


def ParOptions():
  """Return list of autopar options, as string"""
  _InitBuildData()
  return _build_dict.get('PAROPTIONS', '')


def Platform():
  """Return google platform as string"""
  _InitBuildData()
  return _build_dict.get('PLATFORM', '')


def Target():
  """Return build target as string"""
  _InitBuildData()
  return _build_dict.get('TARGET', '')


def Timestamp():
  """Return timestamp in seconds since epoch, as int"""
  _InitBuildData()
  ts = _build_dict.get('TIMESTAMP', '')
  try:
    timestamp = int(ts.strip())
  except ValueError:
    timestamp = -1
  return timestamp


def BuildData():
  """Return all build data as a nicely formatted string."""
  _InitBuildData()
  buf = cStringIO.StringIO()

  timestamp = Timestamp()
  buf.write('Built on %s (%d)\n' %
            (time.asctime(time.localtime(timestamp)), timestamp))

  buf.write('Built by %s\n' % BuildInfo())

  buf.write('Built as %s\n' % Target())

  clientinfo = ClientInfo()
  if clientinfo:
    buf.write('Built from %s\n' % clientinfo)

  buildlabel = BuildLabel()
  if buildlabel:
    buf.write('Build label: %s\n' % buildlabel)

  buf.write('Build platform: %s\n' % Platform())

  buildtool = BuildTool()
  if buildtool:
    buf.write('Build tool: %s\n' % buildtool)

  paropts = ParOptions()
  if paropts:
    buf.write('\nBuilt with par options %s\n' % paropts)

  data_str = buf.getvalue()
  buf.close()

  return data_str

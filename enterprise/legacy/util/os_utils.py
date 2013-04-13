#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc.
# All Rights Reserved.
# Original Author: Zia Syed

"""This utility allows quick retrieval of various process attributes when the
process id is known. Using 'ps' in that case is very slow and its execution
time increases with the number of active processes on the system. This utility
reads the attribute values from /proc/<pid>/stat file and provides constant
access time.
"""
import os

from google3.pyglib import logging

# These column ids correspond to the position of a process attribute in
# /proc/<pid>/stat file. For reference see fs/proc/array.c in the kernel
# source.
COLUMN_MAP_2_4 = { 'pid':  0,
                   'ppid': 3,
                   'pgid': 4,
                   'sid':  5,
                   'priority': 17,
                   'nice': 18,
                   }

# If you add a field to the COLUMN_MAP_2_4 that is incompitable with 2.6 kernel
# then create a separate map for 2.6 kernel.
KERNEL_MAP = { '2.4' : COLUMN_MAP_2_4,
               '2.6' : COLUMN_MAP_2_4,
             }

def GetKernelVersion():
  """Retrieves the kernel version to be used as an index to KERNEL_MAP.

  Returns None if the version can not be found.
  """
  f = os.popen('uname -r')
  data = f.read()
  ret = f.close()
  result = None
  if not ret:
    fields = data.split('.')
    (kernel_version, major_release) = (fields[0], fields[1])
    result = '%s.%s' % (kernel_version, major_release)
  return result

# We store the kernel version so for one process we determine the kernel
# version only once.
KERNEL_VERSION = GetKernelVersion()

def GetColumnId(name, kernel):
  """Given a field name and kernel version, this function returns the column
  id for that field in /proc/stat file.

  Returns None if the field name or kernel version is not known.
  """
  ret = None
  try:
    ret = KERNEL_MAP[kernel][name]
  except:
    #In case of a key error we'll just return None.
    pass
  return ret

def GetAttrUsingPS(name, pid):
  """Retrieves an attribute for a given pid using the ps command.

  Arguments:
    name: Name of the attribute to be retrieved.

  Returns None if the attribue or pid doesn't exist.
  """
  cmd = 'ps ww --noheaders --format %s --pid %d 2>/dev/null' % (name, pid)
  f = os.popen(cmd, 'r')
  data = f.read()
  ret = f.close()
  if ret:
    data = None
  else:
    data = data.strip()
  return data

def GetAttr(name, pid=None, fallback_to_ps=1):
  """Retrieves an attribute using /proc/stat file. If the kernel version
  mismatches or the attribute name is not supported then it can fallback
  to using ps command based on the value of fallback_to_ps argument.

  Returns None in case of failure. Otherwise returned attribute value is
  always a string.
  """
  if pid is None:
    pid = os.getpid()
  val = None
  id = GetColumnId(name, KERNEL_VERSION)
  if id is not None:
    try:
      data = open('/proc/%d/stat' % pid, 'r').read()
    except:
      logging.error('Error getting stats for pid %d.' % pid)
    else:
      val = data.split()[id]
  if val is None and fallback_to_ps:
    # Fallback to using 'ps'
    logging.warn('Error retrieving value. Using \'ps\'.')
    val = GetAttrUsingPS(name, pid)
  return val

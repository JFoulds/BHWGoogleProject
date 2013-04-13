#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Get various machine parameters (disk, cpu) for the virtual GSA.

The "Lite" version of the virtual GSA does not have SVS, so we need to
fetch some machine parameters directly.
"""

__author__ = 'Vivek Haldar <haldar@google.com>'

import popen2
import re

def InitMdb():
  """Init machine database without contacting SVS.

  Returns:
    The machine database, which is a nested dictionary. E.g.
    {'ent1': {'hdcnt': '4', 'disk_size_GB': 'map:disk hda3:225.376007 hdb3\
              :227.246372 hdc3:227.246372 hdd3:227.246372 sda1:3.845303', ...
             },
     'ent2': None
    }
  """

  # parse the output of "df" to get disk stats
  dfre = re.compile(r'^(/[\w/]*)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+([/\w]+)')
  dfout = _GetDiskFreeInfo()

  disk_names = []
  disk_sizes = []
  disk_useds = []
  disk_used_pct = {} # disk -> pct
  for l in dfout:
    matches = dfre.search(l)
    if matches is not None:
      disk_names.append(matches.group(1))
      disk_sizes.append(matches.group(2))
      disk_useds.append(matches.group(3))
      # only count disk used percentage for data partitions, not /
      if matches.group(6) != '/':
        # key is disk name, but need to munge '/export/hda3' to 'hda3'
        # keep consistent with the SVS result
        disk_used_pct[matches.group(6).split('/')[2]] = matches.group(5)

  # parse the output of "free" to get memory stats
  free_re = re.compile(r'^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)')
  freeout = _GetMemFreeInfo()
  matches = free_re.search(freeout[0])
  memory_total = matches.group(1)
  memory_used = matches.group(2)

  # construct the disk_used_df_percent string
  df_pct_list = ['map:disk']
  for disk, pct in disk_used_pct.iteritems():
    df_pct_list.append('%s:%s' % (disk, pct))
  df_str = ' '.join(df_pct_list)

  mdb = {'ent1': {
           'disk-names': ' '.join(disk_names),
           'disk-sizes': ' '.join(disk_sizes),
           'disk-useds': ' '.join(disk_useds),
           'disk_used_df_percent': df_str,
           'mounted-drives': 'sda',     # static
           'var_log_badhds': "''",      # static
           'cpu-mhz': '2393.521',       # don't care
           'cpucnt': '1',               # static
           'memory-total': memory_total,
           'memory-used': memory_used,
           'load3': '0.19',             # don't care
           },
         }

  return mdb

def _GetDiskFreeInfo():
  """Get disk usage/free info from the "df" command.

  Args:
    None

  Returns:
    List of strings from the output of "df"
  """
  stdout, stdin = popen2.popen2('df -l -P | grep /dev')
  return stdout.readlines()


def _GetMemFreeInfo():
  """Get memory free/used info from the "free" command.

  Args:
    None

  Returns:
    List of strings from the output of "free"
  """
  stdout, stdin = popen2.popen2('free -k -o | grep \"Mem:\"')
  return stdout.readlines()

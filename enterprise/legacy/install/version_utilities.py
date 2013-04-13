#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""One-line documentation for version_utilities module.

Functions that help us deal with versions: transforming, comparing, sorting.
"""

__author__ = 'tfullhart@google.com (T.R. Fullhart)'


import commands
import re


def GetRpmRelease(rpm_name, rpm_list_command=None):
  """Extract the release number of the installed rpm given.

  Args:
    rpm_name: the rpm name string up to the release string

  Returns:
    Any matched rpm release info as a string.
    Empty string if no match.
  """
  if not rpm_list_command:
    rpm_list_command = 'rpm -qa | grep %(rpm_name)s'
  release = ''
  cmd = rpm_list_command % {'rpm_name': rpm_name}
  cmd_out = commands.getoutput(cmd)
  match_obj = re.match('%s(?P<release>.+)' % rpm_name, cmd_out)
  if match_obj:
    release = match_obj.group('release')

  return release


def GetPatchVersion(version):
  """Gets the patch version for the specified installed version.

  Query patch version by RPM name.

  Args:
    version: a version string ex. 4.6.4.C.12

  Returns:
    A Patch string like '2'
    Empty string if there's no patch installed or version predating 4.6.4.
  """
  if CmpVersions('4.6.4', version) < 0:
    return ''
  # For version 4.7.3 and above (but not 4.9.1, which was a developer version
  # before 4.7.3), use the new RPM name without the version-doubling hack.
  if (CmpVersions('4.7.3', version) >= 0
      and CmpVersions('4.9.1', version) != 0):
    patch_name = 'google-enterprise-base-%s-' % version
  else:
    patch_name = 'google-enterprise-base-%s-%s-' % (version.replace('.', '_'),
                                                    version)
  patch_version = GetRpmRelease(patch_name)
  return patch_version


def SplitVersionIntoList(version):
  """Splits a version string into a list of integer parts.

  Arguments:
    version:  a version string that is multiple integers delimited by
      non-decimal-digits:  '2.2.4', '4.4.86.G.0', etc.

  Returns:
   a list of integers, for example:
     '2.2.4'       ==>  [ 2, 2, 4, ]
     '4.4.68.G.0'  ==>  [ 4, 4, 68, 0, ]
  """
  # split the version string, treating non-digits as (discarded) delimiters
  version_parts = re.split(r'[^0-9]+', version)
  version_ints = []

  for part in version_parts:
    try:
      version_ints.append(int(part))
    except (TypeError, ValueError,):
      # something is strange here, so just ignore it rather than crashing
      # (maybe this should be logged somehow?)
      pass

  return version_ints


def CompatibleVersion(v_min, v_test):
  """Compares two version tags.

  v_min is a minimum required version, and v_test is the version to
  test. v_test must be at least v_min.

  Arguments:
    v_min: minimum acceptable OS versions (string)

    v_test: installed version (string); a version is either
      major.minor.release, e.g. '2.2.4', or something like
      major.minor.release.L.build, e.g. '4.4.86.G.0'
      major.minor.release.L, e.g. '4.6.4.S'

  Returns:
    Boolean: if v_test satisfies v_min.

    Satisfies is defined as:
     * v_test is greater or equal to v_min
     e.g 4.6.4.S > 4.4.48
     e.g 4.4.48.G.0 > 2.2.4
     e.g 4.4.102.M.6 > 4.4.102.M.4
  """
  # only compare same "style" of version
  v_test_parts = SplitVersionIntoList(v_test)
  v_min_parts = SplitVersionIntoList(v_min)
  length = min(len(v_min_parts), len(v_test_parts))

  # compare from left to right
  for index in xrange(length):
    if v_test_parts[index] < v_min_parts[index]:
      return 0
    elif v_test_parts[index] > v_min_parts[index]:
      return 1

  # must be equal at this point
  return 1


def CmpVersions(vt1, vt2):
  """Compares two version-tags of the form v.v(.v)* (eg. 2.5 or 2.6.1).

  Args:
    vt1: version string
    vt2: version string

  Returns:
    Note: return value is "backwards": value < 0 if vt1 > vt2
    value 0 if the same
    value < 0 if vt1>vt2
    value > 0 if otherwise
  """
  v1 = SplitVersionIntoList(vt1)
  v2 = SplitVersionIntoList(vt2)

  longest = max(len(v1), len(v2))
  for i in xrange(0, longest):
    if len(v1) < longest: v1.append(0)
    if len(v2) < longest: v2.append(0)

    if v1[i] != v2[i]:
      return v2[i] - v1[i]
  return 0


def VersionSortedList(version_list, descending=0):
  """Takes a list of version numbers and returns a sorted list.

  This is used to get a list of oldest-to-latest (or latest-to-oldest,
  if descending order) list of versions installed in the system.

  Args:
    version_list: list to sort
    descending: if true, sort in descending order

  Returns:
    Sorted list.
  """
  version_list = version_list[:]  # Make a copy of the passed in list.
  version_list.sort(CmpVersions)  # Sorts in descending order by default.
  if not descending:
    version_list.reverse()
  return version_list

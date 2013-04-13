#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Most overengineered Walk() implementation you've ever seen.

ExtendedMatch is able to match on multiple wildcards (a/*/*/...),
so, instead of recursing into each directory, add a * and do
extended match, iteratively. On every iteration, match files and
directories to their parents. If number of entries we're holding
exceeds some amount or there are no more entries to match, break.

Collect the stat data for the list (where it's needed), then emulate
old Walk() behavior by recursively going into our data structure
(and calling Walk() again recursively if we stopped because we reached
the limit but there are still entries to walk through).

This function is 5 times faster than fileutil ls -la -R on /gfs/da/awfe/ics
(which holds more than 1M of files in 1M subdirs).
"""

__author__ = 'stingray@google.com (Paul Komkoff)'

import itertools
import os

# This imports common exception classes from gfile_base and puts them into
# globals()
from google3.pyglib.gfile_base import *
from google3.file.base import pywrapfile

_DOTS = frozenset((".", ".."))
_MAX_ENTRIES_READ = 20000

class _LookupEntry(object):
  """Class to store full path, split path, attributes, and subentries.

  Attributes:
    path: string, full path for this entry, populated at the __init__ time
    dirname: string, dirname part of the path, populated at the __init__ time
    basename: string, basename part of the path, populated at the __init__ time
    subentries: a "union":
      - None when it is unknown if there are any subentries
      - False where it is known that this entry contain no subentries
      - list of LookupEntries when it is known that they are subentries
      - True when we don't need subentries anymore
    stat: None or File::Stat object
  """
  # We're on tight memory and CPU budget here, so use __slots__
  __slots__ = ( 'path', 'dirname', 'basename', '_subentries', 'stat')

  def __init__(self, path):
    self.path = path
    self.dirname, self.basename = os.path.split(path)
    self._subentries = None
    self.stat = None

  def IsNonDots(self):
    """Are we looking at '..' or '.'?"""
    return self.basename not in _DOTS

  def AddSubEntry(self, entry):
    """Add a subentry to the list of known subentries"""
    if self._subentries:
      self._subentries.append(entry)
    else:
      self._subentries = [entry]

  def IsDirectory(self):
    """Is this subentry known directory?"""
    return self._subentries or (self.stat and self.stat.IsDirectory())

  def ShouldWalk(self):
    """Do we need to Walk() down?"""
    return self._subentries is None

  def GetSubentries(self):
    """Get a list of subentries (even if it's empty).

    Must not be called after DropSubentries"""
    assert not self._subentries == True
    return self._subentries or []

  def DropSubentries(self):
    """Drop subentries of a directory. Set _subentries to true so next
    IsDirectory will return True"""
    assert self.IsDirectory()
    self._subentries = True

  def SetNoSubentries(self):
    """Mark this entry as having no subentries"""
    self._subentries = False

  def CheckAndFinishSubentries(self):
    """Signals that we're finished adding subentries to this LookupEntry.
    Returns True if there were any subentries added, False otherwise.

    Future calls to AddSubEntry will fail.
    """
    if self._subentries:
      return True
    self._subentries = False
    return False

  def __str__(self):
    return self.path


def _MatchInOrder(leftval, rightval):
  """Small helper function to plug rightval entries as subentries to leftval.

  There are 3 possible cases:
    1.leftval.path < rightval.dirname. We moved too far on the right and we
      need to skip some entries on the left.
    2.leftval.path = rightval.dirname. rightval is a subentry for leftval. We
      add rightval to leftval.subentries and set rightval.dirname to point at
      leftval.path to save some memory.
    3.leftval.path > rightval.dirname. A race condition in our directory
      scanning algorithm resulted in directory entries without a parent. Ignore
      those entries as we do not know where to plug them.

  Args:
    leftval, rightval: LookupEntries.
  Returns:
    True if it's case 1 (leftval.path < rightval.dirname), False otherwise.
  """
  if leftval.path < rightval.dirname:
    return True
  if leftval.path == rightval.dirname:
    # We are going to replace rightval.dirname with reference to leftval.path
    # to conserve some memory.
    rightval.dirname = leftval.path
    leftval.AddSubEntry(rightval)
  return False


def _MatchSubdirs(left, right):
  """Match entries in the right list to their parents in the left list.

  The left list is sorted by .path, the right is by .dirname.
  After processing, entries in the left list will have their .subentries
  populated or set to False (no subentries found).
  Any subentries already stored in left will be discarded. In normal operation
  we only expect to call this function with left values that have no
  preexisting subentries.

  Args:
    left, right: lists of LookupEntries
  Returns:
    nosubdirs, subdirs. Where nosubdirs is a list of entries from left list
    with no subentries found, subdirs - with subentries.
  """
  # left and right are lists, but we need iterators
  left = iter(left)
  right = iter(right)

  nosubtree = []
  subtree = []
  rightval = None

  for leftval in left:
    # If and only if we're in the first iteration, we have rightval set to
    # None. Otherwise we can have rightval prepopulated and we need to
    # match it first.
    if rightval:
      if _MatchInOrder(leftval, rightval):
        # Fast path: skipping left entries
        leftval.SetNoSubentries()
        nosubtree.append(leftval)
        continue

    rightval = None
    for rightval in right:
      if _MatchInOrder(leftval, rightval):
        # This left entry is done, give me next
        break

    # Maintain result lists
    if leftval.CheckAndFinishSubentries():
      subtree.append(leftval)
    else:
      nosubtree.append(leftval)

    if not rightval:
      # No more entries on the right
      # we can exit this loop now and just consume remaining left
      break

  # Consume the rest on the left
  for leftval in left:
    leftval.SetNoSubentries()
    nosubtree.append(leftval)

  return nosubtree, subtree


def _ReportStatFunc(entry):
  """Small helper function to return tuple (basename, stat)"""
  return (entry.basename, entry.stat)


def _IgnoreStatFunc(entry):
  """Small helper function to return only basename"""
  return entry.basename


def _DiscardStatFunc(entry):
  if isinstance(entry, tuple):
    return entry[0]
  return entry


def _WalkHelper(entry, topdown, onerror, report_stats, statfunc):
  """Small recursive helper to emulate old walk behavior with new _Walk way
  of abusing GFS master.
  For an overall description, see _Walk.
  This function tries to use as little memory as possible.

  Args:
    entry: _LookupEntry
    topdown, onerror, report_stats, statfunc: see _Walk
  Yields:
    Walk() entries
  """

  if entry.ShouldWalk() is None:
    # We do not know if this entry has any subentries yet. Call _Walk which
    # will build a subtree first.
    for subentry in _Walk(
        entry.path, topdown, onerror, report_stats, statfunc):
      yield subentry
    return

  if not entry.IsDirectory():
    if onerror:
      onerror(GOSError("Couldn't match path: '%s'" % entry))
    return

  # Cache subdirs here
  subdirs = [e for e in entry.GetSubentries() if e.IsDirectory()]

  if topdown:
    # We are doing topdown (breadth-first) traversal. Build subdirmap for
    # later use
    subdirmap = dict(((x.basename, x) for x in subdirs))
  else:
    # We are doing downtop (depth-first) traversal. Descend into a subtree.
    for subdir in subdirs:
      for subentry in _WalkHelper(
          subdir, topdown, onerror, report_stats, statfunc):
        yield subentry

  # Create a list of fields to yield now
  files = [statfunc(e) for e in entry.GetSubentries() if not e.IsDirectory()]
  # Free entry.subentries as we no longer need it
  # this will drop one list() object
  # We cannot use del entry.subentries here, because in not topdown case, after
  # we will return from this helper, we will need entry.IsDirectory to return
  # True
  entry.DropSubentries()

  # Create a list of subdirs to yield
  # subdirs originally contain a list of LookupEntries for subdirectories.
  # statfunc will convert it either to basename, or a tuple (basename, stat)
  subdirs = map(statfunc, subdirs)

  # yield
  yield entry.path, subdirs, files

  # Free files. This will immediately free some LookupEntries.
  del files

  if topdown:
    # Breadth-first traversal.
    # The list of subdirs we shall descend into may have been amended by the
    # user. Discard any stat data.
    # This will throw KeyError if user puts in some nonexistant dir.
    subdirs = [subdirmap[_DiscardStatFunc(x)] for x in subdirs]
    # Drop subdirmap as we no longer need it.
    del subdirmap
    while subdirs:
      # This will free LookupEntries as we finish with them
      subdir = subdirs.pop(0)
      if subdir.ShouldWalk():
        # We do not know if there are any children yet.
        gen = _Walk
      else:
        gen = _WalkHelper
      for subentry in gen(
          subdir, topdown, onerror, report_stats, statfunc):
        yield subentry


def _StatEntries(entries):
  """Helper function to fill up .stat for list of LookupEntries

  Args:
    entries: list of entries
  """
  # TODO(stingray): Use file::Operation error and deadlines to step over faulty
  # GFS entries.
  overall_success, success_buf, stat_buf = \
      pywrapfile.File.BulkStat(map(lambda x: x.path, entries))

  if len(success_buf) != len(entries):
    raise GOSError, "File::BulkStat returned inconsistent results"

  for entry, stat, success in itertools.izip(entries, stat_buf, success_buf):
    if success:
      entry.stat = stat


def _Walk(top, topdown, onerror, report_stats, statfunc):
  """Recursive directory tree generator, the real one.
  This function works N times faster than fileutil ls -la -R, where N is at
  least 2.5.

  Here we use the property of GFS master to do multilevel ExtendedMatch, like
  ExtendedMatch('.../*/*'). We're adding asterisks to the right and accumulate
  entries until we reach bottom or we exceed MAX_ENTRIES_READ. Then, we're
  doung BulkStat at once, and using _WalkHelper to recursively walk over the
  data structures and present the results in Walk()-compatible way.

  This function tries to use as little memory as possible.

  Args:
    top, topdown, onerror, report_stats: see Walk()
      top can be either string or LookupEntry (in which case it will be
      converted to string)
    statfunc: helper function to create (basename, stat) tuples if needed.
  Yields:
    see Walk()
  """
  # If we pass LookupEntry, take just string path from it.
  top = str(top)
  # Processed tree depth
  depth = 0
  # Entries that we got
  entries_read = 0

  # Root element of our tree
  root = _LookupEntry(top)
  # Current level
  level = [root]
  # Entries that require to be stat'd
  dostat = []
  # next level
  listing = []

  # We try to keep our memory consumption reasonable. At every _Walk() call, we
  # stop descending into directory structure as soon as we've got
  # _MAX_ENTRIES_READ entries.
  # Then we will re-recurse here and do the same on a subtree.
  while entries_read < _MAX_ENTRIES_READ:
    top = os.path.join(top, '*')
    depth += 1
    # TODO(stingray): clarify ExtendedMatch usage. Read hidden files too if
    # required. Use deadlines. Use error code from file::Operation to
    # distinguish different types of errors.
    success, listing = pywrapfile.File.ExtendedMatch(top, 1)
    if not success:
      if onerror:
        onerror(GOSError("Couldn't match path: '%s'" % top))
      break

    listing = [e for e in itertools.imap(_LookupEntry, listing) if
               e.IsNonDots()]
    entries_read += len(listing)

    # This is to ensure that our items are sorted by directory name.
    listing.sort(key=lambda x: x.dirname)

    # Match newly read entries against previous level
    # After this operation, all entries from the level will get their
    # subentries set either to list, or to False. nosubdirs will contain those
    # entries that do not have any subentries. Subdirs will contain the rest.
    nosubdirs, subdirs = _MatchSubdirs(level, listing)

    # We don't know if it's file or just an empty directory. We need to stat
    # it to be sure.
    dostat.extend(nosubdirs)
    if report_stats:
      # We do not need to stat subdirs if we do not need those stats
      dostat.extend(subdirs)

    level = listing

    if not level:
      break

    # We sort our list again but using the full path.
    level.sort(key=lambda x: x.path)

  # The most recently matched level always needs to be stat'd
  dostat.extend(level)
  del level, listing

  if dostat:
    _StatEntries(dostat)
  del dostat

  return _WalkHelper(root, topdown, onerror, report_stats, statfunc)


def Walk(top, topdown=1, onerror=None, report_stats=False):
  """Recursive directory tree generator.

  Args:
    top: string, a pathname.
    topdown: bool, should traversal be pre-order (True) or post-order (False)
    onerror: function, optional callback for errors.
    report_stats: bool, shall we return File::Stat objects together with the
      subdir and file names

  By default, errors that occur when listing a directory are ignored.
  (This is the same semantics as Python's os.walk() generator.)  If the
  optional argument "onerror" is specified, it should be a function.  It
  will be called with one argument, an os.error instance.  It can return
  to continue with the walk, or reraise the exception to abort the walk.

  Yields:
    # Each yield is a 3-tuple:  the pathname of a directory, followed
    # by lists of all its subdirectories and leaf files.
    (dirname, [subdirname, subdirname, ...], [filename, filename, ...])
    # if report_stats is True, then subdirname and filename will become
    # tuples (subdirname, stat) and (filename, stat) respectively
  """
  if report_stats:
    statfunc = _ReportStatFunc
  else:
    statfunc = _IgnoreStatFunc

  return _Walk(top, topdown, onerror, report_stats, statfunc)

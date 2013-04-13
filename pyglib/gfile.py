#!/usr/bin/python2.4
#
# Copyright 2002-2005 Google Inc.
# All rights Reserved.
#
# Note: If we fixed the SWIGging of File::Read(), File::Write(), and
# File::ReadLine(), we could do away with _read_buf and _write_buf, and just
# wrap pywrapfile.File directly.  This would simplify the code and probably
# also give us better performance in the case where you're frequently switching
# between reading and writing to a file.  However, it would hurt our
# performance in the (presumably more common) case where you're doing repeated
# reads or repeated writes.
#
# Note that the file types you can access via gfile are controlled by the C++
# File factories linked in to your binary. They have to be explicitly specified
# in your BUILD file. For example, if you want to access GFS files, you must
# have "//file/gfs" as a dependency.

"""
A Python interface to the Google file layer.

This module provides the GFile class, which wraps Google files with a standard
Python file interface.  In other words, GFile allows you to interact with any
Google file (GFS, local, etc.) using familiar Python file methods.

Like Python files, reads and writes to a GFile object are guaranteed to be
atomic.  This module also provides the FastGFile class, which acts just like
GFile but makes no such atomicity guarantees.  If your program isn't
multithreaded, or if it's guaranteed never to access the same GFile object from
multiple threads concurrently, then using FastGFile could result in a 20%
performance improvement.

This module also has some utility functions for performing common operations on
files and directories.
"""

from __future__ import generators

__author__ = "est@google.com (Eric Tiedemann)"


import os.path
import sys
import stat
import threading
import time

from google3.file.base import pywrapfile
from google3.file.namespace import pywrapnamespace

# Import common exception classes from gfile_base and put them into globals()
from google3.pyglib.gfile_base import *
from google3.pyglib.gfile_walk import Walk as FastWalk

def _synchronized(method):
  """Adapted from Peter Norvig's example here:
    http://jamesthornton.com/eckel/TIPython/html/Sect12.htm
  Uses the _locker strategy in self to do the locking/unlocking.
  """
  def f(self, *args, **kwds):
    self._locker.Lock()
    try:
      return method(self, *args, **kwds)
    finally:
      self._locker.Unlock()
  return f


class _GFile_Base(object):

  def __init__(self, name, mode, attr, perms, group, locker):
    """locker must define Lock() and Unlock() methods."""
    # At least one of these will always be None.
    # If _read_buf is not None, it implies the file is still open and readable.
    # Likewise for _write_buf and writing.
    # _PrereadCheck() and _PrewriteCheck() juggle these variables around.
    self._read_buf = None  # pywrapfile.InputBuffer
    self._write_buf = None  # pywrapfile.OutputBuffer

    # clients should access "mode", "closed" and "name" attributes, and not
    # touch these directly.
    self.__mode = mode
    self.__closed = 1
    self.__closed_status = 1
    self.__name = name

    # mysterious little attribute that print wants
    self.softspace = 0

    self._locker = locker

    if mode not in ('r', 'w', 'a', 'r+', 'w+', 'a+'):
      raise FileError("mode is not 'r' or 'w' or 'a' or 'r+' or 'w+' or 'a+'")


    if attr is None:
      attr = pywrapfile.Attr_t(pywrapfile.Attr_t.DEFAULT)
    if perms is None:
      perms = pywrapfile.DEFAULT_FILE_MODE
    if group is None:
      group = ''

    self._file = pywrapfile.File_OpenFullySpecified(name, mode,
                                                    attr, perms, group)
    if not self._file:
      raise FileError("couldn't open file '%s' with mode '%s'" % (name, mode))
    self.__closed = 0  # we've successfully opened the file.

  # read-only properties
  def _GetMode(self): return self.__mode
  def _GetClosed(self): return self.__closed
  def _GetName(self): return self.__name
  mode = property(_GetMode)
  closed = property(_GetClosed)
  name = property(_GetName)

  def flush(self):
    if not self._write_buf:
      self._PrewriteCheck()
    self._write_buf.Flush()
  flush = _synchronized(flush)

  def write(self, data):
    if not self._write_buf:
      self._PrewriteCheck()
    rc = self._write_buf.WriteString(data)
    if rc != len(data):
      raise FileError("short write on '%s' (%d/%d)"
                      % (self.__name, rc, len(data)))
  write = _synchronized(write)

  # Not synchronized.
  def writelines(self, seq):
    for line in seq:
      self.write(line)

  def tell(self):
    if self.__closed:
      raise ModeError("I/O operation on closed file")
    return self._GetAppropriateFn('Tell')()
  tell = _synchronized(tell)

  def seek(self, offset, whence=0):
    assert whence in (0, 1, 2)
    if self.__closed:
      raise ModeError("I/O operation on closed file")
    if whence == 0:
      position = offset
    elif whence == 1:
      position = min(self.Size(), self.tell() + offset)
    elif whence == 2:
      size = self.Size()
      position = min(size, size + offset)
    if not self._GetAppropriateFn("Seek")(long(position)):
      raise SeekError("bad offset: %s" % position)
  seek = _synchronized(seek)

  def truncate(self, new_size=None):
    if not self._write_buf:
      self._PrewriteCheck()
    if new_size is None:
      new_size = self.tell()
    self._write_buf.Truncate(new_size)
  truncate = _synchronized(truncate)

  def readline(self, max_length=-1):
    if not self._read_buf:
      self._PrereadCheck()
    if max_length != -1:
      # We add 1 here because ReadLineAsString() leaves room for a
      # terminating NUL in the fgets() tradition.  That's probably
      # a misfeature.  If it's fixed and this line isn't changed,
      # our unittest will catch it. :)
      return self._read_buf.ReadLineAsString(long(max_length) + 1)
    else:
      return self._read_buf.ReadLineAsString(long(0))
  readline = _synchronized(readline)

  # Not synchronized.
  def readlines(self, sizehint=None):
    lines = []
    n = 0
    while 1:
      s = self.readline()
      if not s:
        break
      lines.append(s)
      if sizehint is not None:
        n += len(s)
        if n >= sizehint:
          break
    return lines

  def xreadlines(self):
    return iter(self)

  def __iter__(self):
    return self

  # Not synchronized.
  def next(self):
    retval = self.readline()
    if not retval:
      raise StopIteration()
    return retval

  def Size(self):
    if self.__closed:
      raise ModeError("I/O operation on closed file")
    return self._GetAppropriateFn("Size")()
  Size = _synchronized(Size)

  def read(self, n=-1):
    if not self._read_buf:
      self._PrereadCheck()
    if n == -1:
      expected = self.Size() - self.tell()
    s = self._read_buf.ReadToString(long(n))
    if n == -1:
      if len(s) != expected:
        raise FileError("short read to end of file")
    return s
  read = _synchronized(read)

  def close(self):
    if not self.__closed:
      if self._write_buf:
        if not self._write_buf.Flush():
          self.__closed_status = 0
      self._write_buf = self._read_buf = None
      if not self._file.Close():
        self.__closed_status = 0
      self.__closed = 1
    return self.__closed_status
  close = _synchronized(close)

  def __del__(self):
    self.close()

  def _PrereadCheck(self):
    if self.__closed:
      raise ModeError("I/O operation on closed file")
    if not self.__mode in ('r', 'r+', 'a+', 'w+'):
      raise ModeError("File isn't open for reading")
    if self._write_buf:
      self._write_buf.Flush()
      assert self._file.Tell() == self._write_buf.Tell()
      self._write_buf = None
    if not self._read_buf:
      self._read_buf = pywrapfile.InputBuffer(self._file)
      self._read_buf.RelinquishFileOwnership()

  def _PrewriteCheck(self):
    if self.__closed:
      raise ModeError("I/O operation on closed file")
    if not self.__mode in ('a', 'w', 'r+', 'a+', 'w+'):
      raise ModeError("File isn't open for writing")
    if self._read_buf:
      self._file.Seek(self._read_buf.Tell())
      self._read_buf = None
    if not self._write_buf:
      self._write_buf = pywrapfile.OutputBuffer(self._file)
      self._write_buf.RelinquishFileOwnership()

  def _GetAppropriateFn(self, key):
    """For functions like Seek(), Size(), and Tell(), which exist in
    InputBuffer, OutputBuffer, and File, we want to use the InputBuffer or
    Outputbuffer's version if we have a buffer, and to fall back on File's
    version otherwise.
    """
    return getattr((self._read_buf or self._write_buf or self._file), key)
# end _GFile_Base class


class GFile(_GFile_Base):
  """
  A class that provides the Python file interface for the Google file layer.

  See the Python documentation for file objects for the behavior of most of
  these methods.  In addition to the standard Python file methods, we also
  provide a Size() method to return the file size. The constructor takes these
  additional keyword arguments:

  perms (int): permission bits on a newly created file (e.g. 0700)
  group (string): owner group name for a newly created file (GFS only) instead
  of the default behavior of inheriting from the parent directory

  Note that GFile uses InputBuffer and OutputBuffer to buffer reads and writes,
  so performance should be reasonable.

  You'll want to call gfile.Init() at some point before instantiating one of
  these.  Calling InitGoogleScript() with the right arguments may help you get
  better error reporting; e.g.:

    pywrapfile.InitGoogleScript('', ['foo', '--v=4', '--logtostderr'], 0)
  """

  def __init__(self, name, mode='r', perms=None, group=None):
    _GFile_Base.__init__(self, name, mode, None, perms,
                         group, _PythonLocker())


class FastGFile(_GFile_Base):

  """Acts just like GFile, but does not ensure thread safety."""

  def __init__(self, name, mode='r', perms=None, group=None):
    _GFile_Base.__init__(self, name, mode, None, perms,
                         group, _NullLocker())


# Some handy utilities.
def Init():
  """Just wraps pywrapfile.File.Init().  Included so that clients can
  potentially use the Google file layer without ever importing pywrapfile
  directly.
  """
  pywrapfile.File.Init()


def ListDir(dir, return_dotfiles=0):
  """
  Returns a list of files in dir.

  As with the standard os.listdir(), the filenames in the returned list will be
  the basenames of the files in dir (not absolute paths).  To get a list of
  absolute paths of files in a directory, a client could do:
    file_list = gfile.ListDir(my_dir)
    file_list = [os.path.join(my_dir, f) for f in file_list]
  (assuming that my_dir itself specified an absolute path to a directory).

  If return_dotfiles is true, dotfiles will be returned as well.

  Raises GOSError if there is an error retrieving the directory listing.
  """
  dir = os.path.normpath(dir)
  if return_dotfiles:
    match_type = 1  # value of MATCH_DOTFILES from file/base/file.h
  else:
    match_type = 0  # value of MATCH_DEFAULT from file/base/file.h
  success, lst = pywrapfile.File.ExtendedMatch(os.path.join(dir, '*'),
                                               match_type)
  if not success:
    raise GOSError("Couldn't match path: '%s'" % dir)
  return [os.path.basename(file) for file in lst]


def Exists(file):
  """Returns true if file exists."""
  return pywrapfile.File_Exists(file)


def IsDirectory(dir):
  """Returns true if path exists and is a directory"""
  return pywrapfile.File_IsDirectory(dir)


def Glob(pattern):
  """Returns a list of files that match the specific pattern"""
  success, file_list = pywrapfile.File.Match(pattern)
  if not success:
    raise GOSError("Couldn't glob the pattern: '%s'" % pattern)
  return file_list


# Locker classes.  Note that locks must be reentrant, so that multiple
# lock() calls by the owning thread will not block.
class _PythonLocker(object):
  """A locking strategy that uses standard locks from the thread module."""
  def __init__(self):
    self._lock = threading.RLock()

  def Lock(self):
    self._lock.acquire()

  def Unlock(self):
    self._lock.release()


class _NullLocker(object):
  """A locking strategy where Lock() and Unlock() methods are no-ops."""
  def Lock(self):
    pass

  def Unlock(self):
    pass


def Stat(path):
  """Calls File::Stat() on the specified path, and returns the result as
  a pywrapfile.FileStat object.  Raises GOSError on error."""
  stat_info = pywrapfile.File.Stat(path)
  if not stat_info:
    raise GOSError("Error in File::Stat: '%s'" % path)
  return stat_info


def FileListing(filename, stat_info):
  """Produces an "ls -l"-style listing for a file, given its name and a
  pywrapfile.FileStat object."""

  def _ModeToString(mode):
    """Returns the string representation of an octal mode.  For example:
      ModeToString(040755) -> 'drwxr-xr-x'
    """
    def _AddBit(mode, bit, char):
      if mode & bit:
        return char
      return '-'
    ms  = _AddBit(mode, stat.S_IFDIR, 'd')
    ms += _AddBit(mode, stat.S_IRUSR, 'r')
    ms += _AddBit(mode, stat.S_IWUSR, 'w')
    ms += _AddBit(mode, stat.S_IXUSR, 'x')
    ms += _AddBit(mode, stat.S_IRGRP, 'r')
    ms += _AddBit(mode, stat.S_IWGRP, 'w')
    ms += _AddBit(mode, stat.S_IXGRP, 'x')
    ms += _AddBit(mode, stat.S_IROTH, 'r')
    ms += _AddBit(mode, stat.S_IWOTH, 'w')
    ms += _AddBit(mode, stat.S_IXOTH, 'x')
    return ms

  return "%s 1 %-9s %-9s %12ld %-19s %s" % (
    _ModeToString(stat_info.mode),
    stat_info.owner,
    stat_info.group,
    stat_info.length,
    time.asctime(time.localtime(stat_info.mtime)),
    filename
  )


def ListDirectory(dir):
  """Returns a list containing the names of entries in the directory.

  The list is in arbitrary order.  It does NOT contain the special
  entries "." or "..", even if they are present in the directory.
  This is for consistency with the os.listdir function in Python.

  Args:
    dir: string, a pathname to a directory.

  Returns:
    [filename1, filename2, ... filenameN]
  """
  if not IsDirectory(dir):
    raise GOSError("No such directory: '%s'" % dir)
  return [ elt for elt in ListDir(dir, 1) if elt not in ('.', '..') ]


def MkDir(path, mode=0777):
  """Create a GFS directory.

  Args:
    path: string, a GFS pathname.
    mode: int, a Unix permissions mode.
  """
  success = pywrapfile.File.CreateDir(path, mode)
  if not success:
    raise GOSError("Could not create directory: '%s'" % path)


def MakeDirs(path, mode=0777, group=None):
  """Create a leaf directory and all intermediate ones.

  Args:
    path: string, a GFS pathname.
    mode: int, a Unix permissions mode.
    group: optional, group of created directories.

  Notes:
    All intervening directories will be created with the given mode.
  """
  if group is not None:
    default_attr = pywrapfile.Attr_t(pywrapfile.Attr_t.DEFAULT)
    success = pywrapfile.File.RecursivelyCreateDirFullySpecified(path,
                                                                 default_attr,
                                                                 mode,
                                                                 group)
  else:
    success = pywrapfile.File.RecursivelyCreateDir(path, mode)
  if not success:
    raise GOSError("Could not recursively create directory: '%s'" % path)


def RmDir(path):
  """Remove a GFS directory.

  Args:
    path: string, a GFS pathname.
  """
  success = pywrapfile.File.DeleteDir(path)
  if not success:
    raise GOSError("Could not remove directory: '%s'" % path)


def Walk(top, topdown=1, onerror=None, report_stats=False):
  """Recursive directory tree generator for GFS directories.

  Args:
    top: string, a GFS pathname.
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
  def ReportStatHelper(*v):
    if report_stats:
      return v
    else:
      return v[0]

  # Get the directory listing, handling errors as requested.
  try:
    listing = ListDirectory(top)
  except GOSError, err:
    listing = []
    if onerror:
      onerror(err)

  # Instead of individually doing Stat() as IsDirectory() does, use
  # File::BulkStat with all our files. This speeds up things considerably.
  # Thanks chip@ for implementation.
  pathed_listing = [os.path.join(top, item) for item in listing]
  overall_success, success_buf, stat_buf = \
      pywrapfile.File.BulkStat(pathed_listing)

  if not overall_success:
    raise GOSError, "File::BulkStat failed"

  if len(success_buf) != len(listing):
    raise GOSError, "File::BulkStat returned inconsistent results"

  # Each entry of the listing is a file or a subdirectory.
  files = []
  subdirs = []

  for item, item_path, stat, success in zip(
      listing, pathed_listing, stat_buf, success_buf):
    item_path = os.path.join(top, item)

    if not success:
      continue

    if stat.IsDirectory():
      subdirs.append(ReportStatHelper(item, stat))
      if not topdown:
        for subitem in Walk(item_path, 0, onerror, report_stats):
          yield subitem
    else:
      files.append(ReportStatHelper(item, stat))

  # Yield the current entry (regardless of traversal type)
  yield (top, subdirs, files)

  if topdown:
    # We're doing a pre-order traversal.
    # Yield the subtree items here.
    for subdir in subdirs:
      # The following check is true when we were launched with
      # report_stats=True and subdirs is a list of tuples.
      if isinstance(subdir, tuple):
        subdir = subdir[0]
      for subitem in Walk(os.path.join(top, subdir), 1, onerror,
          report_stats):
        yield subitem

def Remove(path):
  """Delete a file.

  Args:
    path: string; a GFS pathname naming a file.  No directories please!
  """
  if pywrapfile.File.IsDirectory(path):
    raise GOSError("Can't remove a directory (use RmDir): %s" % path)
  success = pywrapfile.File.Delete(path)
  if not success:
    raise GOSError("Could not remove file: %s" % path)

def DeleteRecursively(path):
  """Delete a file or a directory recursively.

  Args:
    path: string; a pathname naming a file or directory.
  """
  success = pywrapfile.File.DeleteRecursively(path)
  if not success:
    raise GOSError("Failed to remove directory recursively: %s" % path)


def Rename(oldpath, newpath, overwrite=False):
  """Rename or move a file.

  Args:
    oldpath: string; a pathname of a file.
    newpath: string; a pathname to which the file will be moved.
    overwrite: boolean; if false, it is an error for newpath to be
      occupied by an existing file.
  """
  success = pywrapfile.File.Rename(oldpath, newpath, overwrite)
  if not success:
    raise GOSError("Failed to rename: %s to %s" % (oldpath, newpath))


def Copy(oldpath, newpath, overwrite=False):
  """Copy a file.

  Args:
    oldpath: string; a pathname of a file.
    newpath: string; a pathname to which the file will be copied.
    overwrite: boolean; if false, it is an error for newpath to be
      occupied by an existing file.
  """
  success = pywrapfile.File.Copy(oldpath, newpath, overwrite)
  if not success:
    raise GOSError("Failed to copy: %s to %s" % (oldpath, newpath))


def SetOwner(path, owner):
  """Set the owner of a file.

  Args:
     path: string; a pathname of a file.
     owner: string; the new owner of a file
  """
  success = pywrapfile.File.SetOwner(path, owner)
  if not success:
    raise GOSError("Failed to set the owner: %s to %s" % (path, owner))


def SetMode(path, mode):
  """Set the mode (permission) of a file.

  Args:
     path: string; a pathname of a file.
     mode: int; the mode to which the file will be set.
  """
  success = pywrapfile.File.SetMode(path, mode)
  if not success:
    raise GOSError("Failed to set the mode: %s to %o" % (path, mode))


def SetGroup(path, group):
  """Set the group of a file.

  Args:
     path: string; a pathname of a file.
     group: string; the new group of a file
  """
  success = pywrapfile.File.SetGroup(path, group)
  if not success:
    raise GOSError("Failed to set the group: %s to %s" % (path, group))


def SnapshotFile(oldpath, newpath, perm_mask=0):
  """Create a snapshot of a file. The associated attribute file is also
  snapshot'ed.

  Args:
    oldpath: string; a pathname of a file.
    newpath: string; a pathname of the created snapshot.
    perm_mask: int; mask that will filter off permission of the destination
      file and its attribute file.
  """
  success = pywrapfile.File.SnapshotFile(oldpath, newpath, perm_mask)
  if not success:
    raise GOSError("Failed to create a snapshot: %s to %s" %
                   (oldpath, newpath))


def TranslateNamespace(path):
  """If the given path is a namespace path, translate it to a real path.

  Args:
    path: a pathname.

  Returns:
    If path is not a namespace path, it is returned unchanged.
    If path is a namespace path, and the path is defined in that namespace,
      it is looked up and returned.
    If path is a namespace path, and the path is not defined in that
      namespace, GOSError is raised.
  """
  if not pywrapfile.FileName(path).is_namespace():
    return path
  success, realpath = pywrapnamespace.NamespaceFileFactory.TranslateFully(path)
  if not success:
    raise GOSError("Failed to lookup namespace: %s" % path)
  return realpath

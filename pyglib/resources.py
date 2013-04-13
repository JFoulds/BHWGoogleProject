# Copyright 2004 Google Inc.
# All Rights Reserved.
#
# Provide a consistent API for accessing data files from the Google
# codebase, whether the program is being run from a PAR file, a
# Google3 module-space, or whatever.
#
# A "resource" is simply the contents of a named file.
#
# The name of a resource is something like
# "google3/tools/includes/IMPORTMAP".  Formally, it's a relative path
# name, and it's relative to the root of the Google code base (the
# directory immediately above the google, google2, google3
# directories).
#
# Path components are separated by forward slashes on all platforms
# regardless of the native filesystem conventions.
#
# Search order for resources:
#  1) If this module was loaded from a parfile, look in the parfile.
#     TODO(dgreiman): Handle multiple parfiles
#  2) Look relative to this module's __file__ attribute, if available
#  3) Look relative to sitecustomize.GOOGLEBASE, if available
#  4) Look relative to os.environ["GOOGLEBASE"], if available
#  5) Check for a READONLY symlink for srcfs
#
#  TODO(dgreiman): Possibly more cleverness about module-spaces
#  TODO(dgreiman): Should we add FLAGS.test_srcdir?

__author__ = 'dgreiman@google.com (Douglas Greiman)'

# For maximum PAR file happiness, we don't want this module to import
# other Google code.
import atexit
import cStringIO
import errno
import os
import re
import shutil
import sys
import tempfile
import threading

# Import verbosity. Ideally we'd use Python's Py_VerboseFlag but it's
# not accessible to Python code.
_verbosity = os.environ.get('PYTHONVERBOSE', 0)
def _Log(msg):
  if _verbosity:
    sys.stderr.write(msg)
  # endif
# enddef


def GetResource(name):
  """Return the contents of the named resource as a string.

  Raises IOError if the name is not found, or the resource cannot be opened.

  """

  (filename, data) = FindResource(name) # maybe throws IOError
  assert filename or data
  if not data:
    data_file = open(filename, 'rb')
    try:
      data = data_file.read()
    finally:
      data_file.close()
  # endif
  return data
# enddef


def GetResourceAsFile(name):
  """Return an open file object to the named resource.

  Raises IOError if the name is not found, or the resource cannot be opened.

  """

  (filename, data) = FindResource(name) # maybe throws IOError
  assert filename or data
  if filename:
    return open(filename, 'rb') # maybe throws IOError
  else:
    return cStringIO.StringIO(data)
  # endif
# enddef


# Temporary files.  Map from resource name to file name.
_temporaries = {}


def GetResourceFilename(name):
  """Return the name of a file that contains the named resource.

  Don't use this function if you can use one of the above functions
  instead, because it's less efficient for resources in PAR files.

  It may return the name of a temporary file if the resource doesn't
  natively exist in the filesystem (i.e. part of a PAR file).

  Raises IOError if the name is not found, or the resource cannot be opened.

  """

  global _temporaries
  filename = _temporaries.get(name, None)
  if filename:
    return filename
  # endif

  (filename, data) = FindResource(name) # maybe throws IOError
  assert filename or data
  if not filename:
    filename = _CreateTemporaryFile(name, data)
  # endif

  return filename
# enddef

_resource_directory = None
_resource_directory_files = []


def GetResourceDirectory():
  """Return the base temporary directory that all files requested with
  GetResourceFilenameInDirectoryTree are saved in."""
  global _resource_directory
  if _resource_directory:
    return _resource_directory

  _resource_directory = tempfile.mktemp()
  os.makedirs(_resource_directory)

  global _resource_directory_files
  # Delete file at program exit.
  # Save os.unlink because os might be None when we get called.
  def DeleteResourceDirectoryresourceDir(unlink=os.unlink,
                                         dir=_resource_directory,
                                         files=_resource_directory_files):
    for filename in files:
      try:
        unlink(filename)
        _Log('# deleted resource tmpfile %s\n' % filename)
      except EnvironmentError, e:
        _Log('# error deleting tmpfile %s: %s\n' % (filename, e))
    try:
      os.removedirs(dir)
      _Log('# deleted resource tmpdirectory %s\n' % _resource_directory)
    except EnvironmentError, e:
      _Log('# error deleting tmpfile %s: %s\n' % (_resource_directory, e))

  # enddef
  atexit.register(DeleteResourceDirectoryresourceDir)

  return _resource_directory
# enddef


def GetResourceFilenameInDirectoryTree(name):
  """Return the name of a file that contains the named resource. The
  file is guaranteed to have the same name as the resource and be in the
  same directory tree as the resource requested.

  All files will be created under the directory returned by
  GetResourceDirectory().

  Raises IOError if the name is not found, or the resource cannot be opened.
  """
  filename = os.path.join(GetResourceDirectory(), name)
  if os.path.exists(filename):
    return filename

  global _resource_directory_files

  dir = os.path.dirname(filename)

  if not os.path.exists(dir):
    # os.makedirs raises an exception if a directory already exists. This is bad
    # if you have multiple threads attempting to create a directory tree at the
    # same time. See http://go/comp-lang-python-os-makedirs for the discussion.
    try:
      os.makedirs(dir)
    except OSError, e:
      if e.errno != errno.EEXIST or not os.path.isdir(dir):
        raise

  (resourcefilename, data) = FindResource(name) # maybe throws IOError
  assert filename or data

  if data is None:
    f = open(resourcefilename, 'rb') # maybe throws IOError
    data = f.read()
    f.close()
  # endif

  f = open(filename, "w")
  f.write(data)
  f.close()

  _resource_directory_files.append(filename)
  return filename
# enddef


def _CreateTemporaryFile(name, data):
  """Create a temporary file with the specified contents.

  data: A string object containing the data to be written to the temporary.

  The temporary will be deleted at program finish.

  Returns an absolute filename.

  """

  assert not _temporaries.has_key(name)

  tmp_name = re.sub(r'[^\w]', '_', name) # replace non-alpha chars with _
  if name.endswith('.py'):
    tmp_name = tmp_name[:-3] + '.py'  # undo the re.sub() for the py extension
  filename = tempfile.mktemp(tmp_name)
  f = open(filename, 'w')
  f.write(data)
  f.close()
  _temporaries[name] = filename

  # Delete file at program exit.
  # Save os.unlink because os might be None when we get called.
  def Delete(unlink=os.unlink, filename=filename):
    try:
      unlink(filename)
      _Log('# deleted resource tmpfile %s\n' % filename)
    except EnvironmentError, e:
      _Log('# error deleting tmpfile %s: %s\n' % (filename, e))
  # enddef
  atexit.register(Delete)

  return _temporaries[name]
# enddef


# Lock to prevent race condition in ZipFile when accessing resources
# from multiple threads simultaneously.
_ResourceLock = threading.Lock()


def FindResource(name):
  """Search for a named resource.

  Returns a tuple of (filename, file contents as string), where at
  least one element is not None, depending on the abilities of the
  entity where the resource was found.  E.g. resources from PAR files
  don't have independent filenames.

  Raises IOError if the name is not found, or the resource cannot be opened.
  """

  # 1
  loader = globals().get('__loader__', None)
  if loader and hasattr(loader, 'get_data'):
    try:
      _ResourceLock.acquire()
      try:
        data = loader.get_data(name)
      finally:
        _ResourceLock.release()
      _Log('# loading resource %s via __loader__\n' % (name))
      return (None, data)
    except IOError:
      pass
    # endtry
  # endif

  # 2
  file = globals().get('__file__', None)
  if file:
    # __file__ is like <root>/google{2,3}/pyglib/resources.py
    root_plus_two = os.path.dirname(os.path.abspath(file))
    if root_plus_two and os.path.isdir(root_plus_two):
      root = os.path.dirname(os.path.dirname(root_plus_two))
      filename = os.path.join(root, name)
      if os.path.isfile(filename):
        _Log('# loading resource %s from %s via __file__\n' % (name, filename))
        return (filename, None)
      # endif
    # endif
  # endif

  # 3
  if sys.modules.has_key('sitecustomize'):
    sitecustomize = sys.modules['sitecustomize']
    root = getattr(sitecustomize, 'GOOGLEBASE', None)
    if root and os.path.isdir(root):
      filename = os.path.join(root, name)
      if os.path.isfile(filename):
        _Log('# loading resource %s from %s via sitecustomize\n' % (name,
                                                                    filename))
        return (filename, None)
      # endif
    # endif
  # endif

  # 4
  root = os.environ.get('GOOGLEBASE', None)
  if root and os.path.isdir(root):
    filename = os.path.join(root, name)
    if os.path.isfile(filename):
      _Log('# loading resource %s from %s via GOOGLEBASE\n' % (name, filename))
      return (filename, None)
    # endif
  # endif

  # 5 see if the file is under a READONLY srcfs path
  # First check make-dbg or mach style relative srcfs.
  if name.startswith("../READONLY"):
    return (name, None)
  # Next check blaze style full paths.
  # Blaze input is like "/home/foo/client/google3/path/to/file.txt"
  # Find the google3 dir within the name and see if it has a READONLY
  readonly_path = None
  resource_name = None
  head = name
  # Start at the back of the path and go until google3.
  # This assumes there's no google3 anywhere else in the path.
  # Note: os.path.split('/') returns ('/', '') and
  # os.path.split('foo') return ('', 'foo').
  # Thus we know that we have run out of path components when head is
  # equal to '/' or the empty string.
  while readonly_path is None and head != '' and head != '/':
    (head, tail) = os.path.split(head)
    if resource_name is not None:
      resource_name = os.path.join(tail, resource_name)
    else:
      resource_name = tail

    if tail == 'google3':
      readonly_path = os.path.join(head, 'READONLY')
    # endif
  #endwhile
  if readonly_path is not None:
    filename = os.path.join(readonly_path, resource_name)
    if os.path.isfile(filename):
      _Log('# loading resource %s from %s via srcfs READONLY\n' % (name,
                                                                 filename))
      return (filename, None)
    # endif
  #endif

  raise IOError(errno.ENOENT, 'Resource not found', name)
# enddef

def GetRunfilesDir():
  """Returns the runfiles dir of the currently-running program."""
  return FindRunfilesDir(os.path.abspath(sys.argv[0]))
# enddef


def FindRunfilesDir(program_filename):
  """Look for a runfiles directory corresponding to the given program.

  program_filename: absolute path to a Google3 Python program

  We assume that program name is like one of:
   1) <root>/google3/<package>/<file>.<extension>
      - or -
      <root>/google3/bin/<package>/<file>.<extension>
      Runfiles :=  <root>/google3/bin/<package>/<file>.runfiles
   2) <root>/google3/linux-dbg/<package>/<file>.runfiles/google3/<package2>/<file>.py
      Runfiles :=  <root>/google3/linux-dbg/<package>/<file>.runfiles
  """
  def BindirFilename(filename):
    """
    return the binary directory, and the filename relative to that directory
    if the binary directory isn't known, search the program's filename for
    a binary directory
    """
    # first, see if filename begins with a bin directory
    for bindir in ['bin', 'blaze-bin']:
      bindir_sep = bindir + os.sep
      if filename.startswith(bindir_sep):
        filename = filename[len(bindir_sep):]
        return bindir, filename
    # if not, find the bin directory in the absolute programname
    for elem in os.path.abspath(sys.argv[0]).split(os.sep):
      if elem in ['bin', 'blaze-bin']:
        return elem, filename
    # shouldn't happen but will fail os.path.isdir below
    return '',filename

  google3_str = os.sep + "google3" + os.sep
  google3_idx = program_filename.rfind(google3_str)
  if google3_idx != -1:
    root_dir = program_filename[:google3_idx]
    rel_filename = program_filename[google3_idx + len(google3_str):]
    bindir, rel_filename = BindirFilename(rel_filename)
    rel_filename_noext = os.path.splitext(rel_filename)[0]
    runfiles = os.path.join(root_dir, "google3", bindir,
                            rel_filename_noext + ".runfiles")
    if os.path.isdir(runfiles):
      return runfiles
    return root_dir
  else:
    return None
  # endif
# enddef


_extracted_root_dir = None


def GetARootDirWithAllResources():
  """Get a root directory containing all the resources.

  Tries the following steps and returns at the first successful step
    * Returns a previously extracted root dir
    * Find and return a runfile dir
    * Extract files out of the par file being executed into a root dir
      and return that dir

  NOTE: This function returns "a" root dir with all the resources and
  not "the" root dir. It is not necessary that the directory returned
  by this function is the one that will be used by resources.py to
  find resources. If the executable is a par file every call to this
  function may lead to an expensive extraction of files from the par
  file into a new directory.

  Returns:
    root: path to root directory
    If unable to provide a directory, returns None.
  Raises:
    IOError if an IOError occurs (such as disk full)
  """
  global _extracted_root_dir

  # 1 if it was already extracted, return that.
  if _extracted_root_dir:
    return _extracted_root_dir

  # 2 Try to get the runfiles dir
  _extracted_root_dir = GetRunfilesDir()
  if _extracted_root_dir:
    return _extracted_root_dir

  # 3 Try to extract all files out of the par file
  loader = globals().get('__loader__', None)
  if loader and hasattr(loader, 'get_data'):
    try:
      _ResourceLock.acquire()
      try:
        if not _extracted_root_dir:
          root = tempfile.mktemp()
          loader._par._ExtractFiles(lambda x: 1, "file", root)
          _extracted_root_dir = root
          atexit.register(shutil.rmtree, _extracted_root_dir)
      finally:
        _ResourceLock.release()
    except IOError:
      shutil.rmtree(root)
      raise
    # endtry
  # endif
  return _extracted_root_dir
#enddef


# We use _UNINITIALIZED as the special value for _par_extract_all_files_cache,
# because we can not choose any other value as the default.
_UNINITIALIZED = object()
_par_extract_all_files_cache = _UNINITIALIZED

def ParExtractAllFiles():
  """Extracts all files if running as par file.

  This function only tries to extract files once. Subsequent calls return value
  cached from previous runs.

  Returns:
    a string, runfiles directory, or None if an error happened or if not
    running as par file.

  Raises:
    Will raise exceptions if zipimport implementation raises something.
  """
  global _par_extract_all_files_cache
  if _par_extract_all_files_cache is _UNINITIALIZED:
    try:
      __loader__._par._ExtractAllFiles()
      _par_extract_all_files_cache = __loader__._par._SetAndGetRunfilesRoot()
    # NameError or AttributeError mean that we're not running in a par file.
    except (NameError, AttributeError):
      _par_extract_all_files_cache = None
    # endtry
  # endif
  return _par_extract_all_files_cache
# enddef

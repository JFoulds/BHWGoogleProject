#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Some of the very basic definitions that are used by all of the gfile_
functions and methods.
"""

__author__ = 'stingray@google.com (Paul Komkoff)'

# All gfile exceptions match the exception classes for ordinary Python files.
class Error(Exception):
  """Virtual exception class for all gfile errors."""

class GOSError(Error, OSError):
  """An error occurred while finding a file or in handling pathnames."""

class FileError(Error, IOError):
  """An error occurred while reading or writing a file."""

class ModeError(Error, ValueError):
  """An operation was attempted on a closed file or one in the wrong mode."""

class SeekError(Error, ValueError):
  """An invalid seek was performed."""

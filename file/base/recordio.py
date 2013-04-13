# Copyright 2004 Google Inc.
# All Rights Reserved
#
# Author: Jeremy Hylton <jhylton@google.com>

"""Wrapper around RecordIO that provides a simple iterator interface."""

from google3.file.base import pywrapfile, pywraprecordio

class RecordReader(object):

  def __init__(self, path, recordreader_options=None):
    """Instantiates a RecordReader with some options.

    Args:
      path: Full path to recordio file.
      recordreader_options: A RecordReaderOptions instance.  If None, we'll
        use the default options.
    """
    f = pywrapfile.File_OpenOrDie(path, "r")
    if recordreader_options is None:
      recordreader_options = pywraprecordio.RecordReaderOptions()
    self._reader = pywraprecordio.RecordReaderScript(f, recordreader_options)

  def __iter__(self):
    return self

  def next(self):
    readok, buf = self._reader.ReadRecordIntoString()
    if not readok:
      raise StopIteration
    return buf

  def Seek(self, offset):
    if not self._reader.Seek(offset):
      raise IOError("bad file offset in seek")

  def Tell(self):
    return self._reader.Tell()

  def Size(self):
    return self._reader.Size()

  def Close(self):
    if not self._reader.Close():
      raise IOError("unable to close record reader")

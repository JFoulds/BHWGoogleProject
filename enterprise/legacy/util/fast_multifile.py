#!/usr/bin/python2.4
#
# (C) 2001 and onward Google, Inc.
#
# A class that makes each part of a multipart message "feel" like an
# ordinary file, using fp.read() and fp.readline().
#
# This is intended to provide a similar interface to the multifile module
# that comes with python.  The differences are that this module provides a
# read() method which takes a size argument so that you can avoid reading the
# whole part into memory.
#
# Author: David Watson
#
# The basic idea of this implementation is to keep two buffers: the safe
# buffer, which contains bytes that don't contain the boundary, and the danger
# buffer which contains bytes that do or might contain the boundary and
# anything following (which is in the next part)
#

import string

class FastMultiFile:
  # TODO: to be faster: maintain safe_buffer as a list of strings instead of a
  # single string to avoid string merges on every dump (lots of wasted memory
  # allocation and copying).

  def __init__(self, fp, boundary, max_read_size):
    self.fp = fp
    self.boundary = '--' + boundary
    self.boundary_found = 0
    self.safe_buffer = ""
    self.danger_buffer = ""
    self.max_read_size = max_read_size
    self.total_read_size = 0

  def read(self, read_size = None):
    # read chunks until we find the boundary or safe_buffer has enough to
    # fufill our demands
    if read_size == None:
      while not self.boundary_found:
        self.read_chunk(10240, 1)

      body = self.safe_buffer
      self.safe_buffer = ""
    else:
      while not self.boundary_found and len(self.safe_buffer) < read_size:
        self.read_chunk(max(10240, read_size), 1)

      # grab the requested number of bytes from safe_buffer
      body = self.safe_buffer[:read_size]
      self.safe_buffer = self.safe_buffer[read_size:]

    return body

  def readline(self):
    # read chunks until we find the boundary or safe_buffer has enough to
    # fufill our demands
    newline_pos = string.find(self.safe_buffer, '\n')
    while not self.boundary_found and newline_pos == -1:
      self.read_chunk(10240, 1)
      newline_pos = string.find(self.safe_buffer, '\n')

    # grab the requested number of bytes from safe_buffer
    if newline_pos == -1:
      body = self.safe_buffer
      self.safe_buffer = ""
    else:
      body = self.safe_buffer[:newline_pos+1]
      self.safe_buffer = self.safe_buffer[newline_pos+1:]

    return body

  def next(self):
    # read the rest of the file; don't bother saving it
    while not self.boundary_found:
      self.read_chunk(1024*1024, 0)

    # if boundary is terminated by '--', count it as EOF
    if self.danger_buffer[len(self.boundary):len(self.boundary)+2] == '--':
      self.boundary_found = 2

    # remove boundary from danger_buffer
    self.dump_danger_to_safe(len(self.boundary)+2, 0)
    # reset
    if self.boundary_found != 2: self.boundary_found = 0
    self.safe_buffer = ""

    return self.boundary_found != 2

  def read_chunk(self, block_size, append_safe):
    if self.boundary_found: return

    # make sure we don't read more than max_read_size
    size_to_read = min(self.max_read_size - self.total_read_size,
                       block_size)

    # read a block
    if size_to_read > 0:
      tmp_buffer = self.fp.read(size_to_read)
    else:
      tmp_buffer = ""

    if len(tmp_buffer) == 0:
      # End of file, but there may still be a boundary in what we have
      self.boundary_found = 2

    # update total_read_size
    self.total_read_size = self.total_read_size + len(tmp_buffer)

    # append the read block into the danger_buffer
    self.danger_buffer = self.danger_buffer + tmp_buffer
    del tmp_buffer

    # see if we can find the boundary in the danger_buffer
    boundary_pos = string.find(self.danger_buffer, self.boundary)
    if boundary_pos > -1:
      # found boundary, dump everything before it into safe buffer
      self.dump_danger_to_safe(boundary_pos, append_safe)
      self.boundary_found = 1
      return

    if self.boundary == 2:
      # EOF: stop trying, dump danger -> safe
      self.dump_danger_to_safe(None, append_safe)

    # We didn't find the boundary, but we might have part of it at the end of
    # the buffer.  We look for any potential boundary starts at the end of
    # danger_buffer (boundaries must be preceded by \n) and leave only the
    # dangerous part in the buffer for the next time read_chunk is called.
    danger_zone = -1 * (len(self.boundary)+4)
    newline_pos = string.rfind(self.danger_buffer, '\n', danger_zone)
    if newline_pos == -1:
      # danger buffer doesn't have anything dangerous in it
      self.dump_danger_to_safe(None, append_safe)
    elif newline_pos > 0:
      # dump everything upto the newline into safe_buffer
      self.dump_danger_to_safe(newline_pos, append_safe)

    return

  def dump_danger_to_safe(self, pos, append_safe):
    if pos == None:
      if append_safe:
        self.safe_buffer = self.safe_buffer + self.danger_buffer
      self.danger_buffer = ""
    elif pos > 0:
      if append_safe:
        self.safe_buffer = self.safe_buffer + self.danger_buffer[:pos]
      self.danger_buffer = self.danger_buffer[pos:]

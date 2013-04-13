#!/usr/bin/python2.4
#
# Copyright 2000 Google Inc. All Rights Reserved.

"""
Author: Ben Polk
(parts swapped from Phil Jensen's slowcp locking code)

Simplified for Enterprise use by Hareesh Nagarajan
(hareesh@google.com).

Attempts to acquire or release a lock. The caller must provide a
file name that will represent the lock.  The file by default is
placed in /root.  It contains the PID or other text string naming
the owner. If you call the Python functions directly it will use the
PID of the calling process as the default owner.
"""

__owner__ = 'Hareesh Nagarajan (hareesh@google.com)'

import os
import random
import re
import stat
import string
import sys
import time

from google3.pyglib import logging

def get_file_age(filename):
  stat_fields = os.stat(filename)
  mod_time = stat_fields[stat.ST_MTIME]
  file_age = int(time.time()) - mod_time
  return file_age

def get_lock(lockfile, owner):
  """Subroutine to atomically create the lock file, and write the
  owner into it."""

  try:
    fd = os.open(lockfile, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
  except OSError, err:
    logging.error('Unable to acquire %s: %s' % (lockfile, err))
    return 1

  try:
    os.write(fd, '%s\n' % owner)
    os.close(fd)
    return 0
  except OSError, err:
    # Failed to write into file. Maybe the disk is full?
    # Close and erase the file to cleanup.
    try:
      os.close(fd)
    except:  # catch all exceptions, we don't care at this point
      pass
    try:
      os.unlink(lockfile)
    except:  # catch all exceptions, we don't care at this point
      pass
    logging.error('Unable to acquire %s: %s' % (lockfile, err))
    return 1

def exist_lock(lockfile):
  """Subroutine to test if the lock exists."""
  
  if os.path.exists(lockfile):
    return 0
  else:
    logging.error('Lock %s does not exist' % lockfile)
    return 1

def remove_lock(lockfile, owner=''):
  """Subroutine to remove a lock file if we don't own it and it does not
  belong to a live process."""

  try:
    errmsg = ''
    fileowner = string.strip(open(lockfile, 'r').read())  # may raise IOError
    if fileowner != owner:
       # We don't own it. Is the owner a pid?
       # (Note: we assume any number of digits is a pid.)
       if re.search('^\d+$', fileowner):
         if os.path.exists('/proc/%s' % fileowner):
           # It's owned by an existing process. Get its command line for msg.
           cmdline = open('/proc/%s/cmdline' % fileowner).read()
           lockage = get_file_age(lockfile)
           errmsg = ("Unable to acquire %s:\n"
                     "Owned for %s seconds by pid %s running: \n"
                     "%s" %
                     (lockfile, lockage, fileowner, cmdline))
    if errmsg:
      logging.error(errmsg)
      return 1

  except IOError:
    pass  # process doesn't exist anymore

  try:
    os.unlink(lockfile)
  except OSError:
    pass
  return 0

def WaitTillDone(function, args, maxwait=600, verbose=0):
  """Wait until the function returns 0. The function is called
  with the given args repeated until it is successful.
  """

  if maxwait < 0:
    maxwait = 0  # Negative maxwait would never end.

  starttime = time.time()
  elapsedtime = 0

  while 1:  # Break out at bottom if elapsed time has exceeded maxwait

    status = apply(function, args)
    if status == 0:
      return status

    if verbose:
      if elapsedtime == 0 and maxwait > 0:
        logging.info('Status %s, retrying for %s secs' % (status[1], maxwait))

      if (int(elapsedtime) % 3) == 0:
        logging.info('.')

    elapsedtime = time.time() - starttime
    if elapsedtime > maxwait:
      if verbose and maxwait:
        logging.info('Giving up after %s seconds' % (maxwait))
      break

    time.sleep(0.5 + random.random())

  # returns last bad status
  return status

def AcquireLockFileHelper(lockname, lockdir, owner, verbose):
  """Create a lock file if there isn't already one there."""

  if not owner:
    owner = str(os.getpid())

  lockfile = '%s/%s' % (lockdir, lockname)
  if get_lock(lockfile, owner) == 0:
    if verbose:
      logging.info('Acquired %s' % lockfile)
    return 0

  # We only get this far if we failed our first attempt to get the lock.
  (rc, msg) = remove_lock(lockfile, owner)
  if rc == 0:
    rc = get_lock(lockfile, owner)
    if rc == 0:
      if verbose:
        logging.info('Acquired (on second try): %s' % lockfile)
      return 0

  return 1

def AcquireLockFile(lockname, lockdir='/root', owner='',
                    maxwait=600, verbose=1):
  """Create a lock file if there isn't already one there. Wait at most
  maxwait time to acquire the lock. Returns 1 if there's an existing
  lock file."""

  return WaitTillDone(AcquireLockFileHelper,
                      (lockname, lockdir, owner, verbose), maxwait, verbose)

def ReleaseLockFile(lockname, lockdir='/root', owner=''):
  """Delete the lock file with our pid on it."""

  if not owner:
    owner = str(os.getpid())

  lockfile = '%s/%s' % (lockdir, lockname)
  logging.info('Released %s' % lockfile)
  return remove_lock(lockfile, owner)

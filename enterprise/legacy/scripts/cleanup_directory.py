#!/usr/bin/python2.4
#
# (c) 2001 and onwards Google, Inc.
# praveen@google.com
#
# This script cleanups up a directory.  It removes all Files in the directory
# that aren't currently opened by any process.  This is currenlty used to
# cleanup the ramfs/tmpfs system that is used by rtsubordinate to cache index files.
#
#
###############################################################################

import os
import stat
import sys
from google3.enterprise.legacy.util import E
from google3.pyglib import logging
import glob
import time

###############################################################################

from google3.pyglib import flags
FLAGS = flags.FLAGS

flags.DEFINE_string("cleanup_dir", "", "Directory to cleanup")

###############################################################################

def remove_unused_from(dirname, fileutil, grace_seconds):
  '''
  Get a list of all files in the given directory  that aren't opened and delete
  them.
  fileutil - full path of fileutil
  grace_seconds - Even if a file isn't currently opened we consider it being
                  in-use if it has been accessed recently (less this many
                  seconds ago)
  '''
  if not dirname:
    logging.error("Not given a directory to cleanup")
    return

  open_files_cmd = ("lsof +D %s -Fn" % dirname)
  (status, output) = E.getstatusoutput(open_files_cmd)

  #if status != E.ERR_OK:
  #  return
  # lsof doesn't return 0 even on success, so ignore it

  # lsof returns several lines for each file because multiple threads in a
  # process could have it open.  Get a list of unique files.
  open_files = {}
  for line in output.split():
    if line[0] == 'n':
      file = line[1:]
      open_files[file] = 1

  # Get a list of all files in the directory - not starting with .
  all_files = glob.glob("%s/*" % dirname)

  # Delete all unused files.
  for file in all_files:
    if file not in open_files:
      try:
        age = int(time.time()) - os.stat(file)[stat.ST_ATIME]
        if age > grace_seconds:
          logging.info('Removing unused file %s' % file)
          (s, o) = E.getstatusoutput("%s rm -f %s" % (fileutil, file))
          # If fileutil can't delete it for any reason, nuke it directly
          # And its attribute file.
          if os.path.exists(file):
            os.remove(file)
            os.remove('%s/.attr.plain.%s' %
                (os.path.dirname(file), os.path.basename(file)))
        else:
          logging.info('Ignoring unused file %s of age %s seconds' % (file, age))
          continue
      except OSError:
        # File got deleted since we ran glob?  Ignore away.
        continue
    ##
  ##


###############################################################################

if __name__ == "__main__":
  try:
    FLAGS(sys.argv)  # parse flags
  except flags.FlagsError, e:
    sys.exit("Error parsing flags")

  if FLAGS.cleanup_dir:
    remove_unused_from(FLAGS.cleanup_dir,
                       '/home/build/google3/linux-opt/file/util/fileutil',
                       0)
  else:
    sys.exit('No cleanup_dir given')

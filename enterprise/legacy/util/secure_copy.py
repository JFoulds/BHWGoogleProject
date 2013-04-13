#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.

"""
A script that can be used to copy files safely. It is intended to
be run as root by secure_script_wrapper, which has a limited list of
scripts that it runs, but does not limit the arguments for those
scripts. Thus, I created this rsync wrapper which, in turn, checks for
arguments and accepts only pairs of files from its list. This prevents
someone from overwriting files at random.

Usage:
secure_copy.py machine file tmpdir

"""

__author__ = 'cristian@google.com'

import sys
import os
import string
from google3.pyglib import logging
import re

# Whitelist of files that secure_copy.py is allowed to copy.
# [\w\.]+ matches a string of at least 1 alphanumeric character and/or period.
FILES = [
  "^/export/hda3/[\w\.]+/local/conf/certs/server.crt$",
  "^/export/hda3/[\w\.]+/local/conf/certs/server.key$"
  ]

def CopyFile(machine, file, tmpdir):
  for FILE in FILES:
    if re.compile(FILE).match(file):
      err = os.system("rsync -e ssh -c -a -T %s %s:%s %s" % (tmpdir, machine,
                                                             file, file))
      return err != 0

  logging.error("Attempting to copy unsecure file %s from %s as root "
                "(tmpdir=%s). See whitelist in secure_copy.py." %
                (file, machine, tmpdir))
  return 1


def main(argv):
  if len(argv) != 3:
    return __doc__
  return CopyFile(argv[0], argv[1], argv[2])

############################################################################

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))

############################################################################

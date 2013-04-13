#!/usr/bin/python2.4
#
# Copyright 2005 Google Inc. All Rights Reserved.

"""
support_key_update updates the know_host file with the latest keys

This is built to push support call server's public key out to exisiting GSAs.
This script will examine the know_host file and add or update the key as
needed.
"""

__author__ = 'Ryan Tai <ryantai@google.com>'

import os
import re
import sys

_support_key = 'supportcall.google.com ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAIEAqLRAKQcowYNFnnrdQW3PAudryWbvVXQUue34yPBmmTWVyWDckHaX3UdfG4AaShjcYx2CMAxe/sWeOlEoJljqjrq9fXqYH1ly+Dj/dN8i96cr4FBDdeqMIzMLM0Dzx2GMzhoAgT7oFWfifMTIoRFOh4wLcvMY18H+u/tOhvd52OM=\n'
_known_hosts = '/.ssh/known_hosts'

def UpdateKey():
  """
    UpdateKey replace the support call server key in the known_hosts file.

    A new known_hosts file will be created with all the keys except for the old
    support call server key.  When the new file is ready it will be renamed to
    be the real known_hosts file.
    If any error occurs the original file is untouched.
  """
  newFile = '%s.new' % _known_hosts
  fileExist = 0
  try:
    # remove new file if it already exist
    if os.access(newFile, os.F_OK):
      os.remove(newFile)

    # test if known_hosts file exist
    if os.access(_known_hosts, os.F_OK):
      fileExist = 1
      fileIn = open(_known_hosts, 'r')
      fileOut = open(newFile, 'w')
      # write out the known_hosts file without the supportcall key
      key_re = re.compile(r'^supportcall.google.com.+')
      for input in fileIn:
        matchObj = key_re.match(input)
        if not matchObj: fileOut.write(input)
    else:
      print '%s file does not exist. Creating it now.' % _known_hosts
      fileOut = open(newFile, 'w')

    # insert new key
    fileOut.write(_support_key)
    fileOut.close()
    if fileExist:
      fileIn.close()
    os.rename(newFile, _known_hosts)
    os.system('chown nobody:nobody %s' % _known_hosts)
    print 'Update successful'

  except [IOError, OSError], err:
    print err
    sys.exit(0)


if __name__ == '__main__':
  UpdateKey()

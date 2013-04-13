#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.
#
'print RESTART if http://localhost:port/healthz does not return OK.'

__author__ = 'wanli@google.com (Wanli Yang)'

import sys
from google3.enterprise.legacy.scripts import check_healthz

def main(argv):
  if len(argv) == 0:
    sys.exit(0)

  port = int(argv[0])
  for retry in range(3):
    if check_healthz.CheckHealthz(port):
      sys.exit(0)
  print 'RESTART'

if __name__ == '__main__':
  main(sys.argv[1:])

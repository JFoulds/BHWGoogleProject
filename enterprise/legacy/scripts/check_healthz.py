#!/usr/bin/python2.4
#
# Copyright 2003 Google, Inc.
#

'Check /healthz on a HTTP port on the local machine.'

import signal
import urllib

True = 1
False = 0

def AlarmHandler(signum, frame):
  raise IOError, 'Host not responding'

def CheckHealthz(port, host='localhost'):
  signal.signal(signal.SIGALRM, AlarmHandler)
  try:
    try:
      signal.alarm(60)
      # GEMES (port 3960, 3965, 3970) return 'OK' and
      # AuthzChecker (port 7882) and qrewrite return 'ok'
      return (urllib.urlopen('http://%s:%d/healthz' % (host, port)).read() in
              ['ok\n', 'OK', 'ok'])
    finally:
      signal.alarm(0)
  except IOError:
    return False

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

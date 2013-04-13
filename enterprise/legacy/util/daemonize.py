#!/usr/bin/python2.4
#
# Copyright 2004, Google Inc.  All rights  reserved.
#
# This module can be used to daemonize a given script
#
# This forks it from the parent and redirects stderr,stdout and stdin
"""
Usage:
   This library is not intended to be invoked and will error if called direct

   daemonize ('/dev/null', config[LOGFILE], config[LOGFILE])

"""

__author__ = 'Ray Colline <rayc@google.com>'

import os
import sys


def WritePid(pid, pid_file):
  """ Writes out a pid file so that it can be controlled by a startup script

  Args:
    pid= int - pid of my process
    pid_file = string - location of filename

  Returns:
    nothing

  """
  try:
    pf = open("%s" % pid_file,"w")
    pf.write(str(pid))
    pf.close()
    print "wrote PID to %s" % pid_file
  except OSError, os_err:
    print >> sys.stderr, os_err.args
    sys.exit('OS error could not create PID file %s' % pid_file)
  except IOError, io_err:
    print >> sys.stderr, io_err.args
    sys.exit('IO error could not create PID file %s' % pid_file)
  except:
    sys.exit('Unexpected error could not create PID file %s' % pid_file)
  return 0

def Daemonize (stdin='/dev/null', stdout='/dev/null', stderr='/dev/null',
      test=0):
  """This forks the current process into a daemon.
  The stdin, stdout, and stderr arguments are file names that
  will be opened and be used to replace the standard file descriptors
  in sys.stdin, sys.stdout, and sys.stderr.
  These arguments are optional and default to /dev/null.
  Note that stderr is opened unbuffered, so
  if it shares a file with stdout then interleaved output
  may not appear in the order that you expect.

  from: http://www.noah.org/python/daemonize.py

  References:
    UNIX Programming FAQ
    1.7 How do I get my program to act like a daemon?
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16

  Advanced Programming in the Unix Environment
    W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.

    Args:
      stdin= string - file to redirect stdin from
      stdout= string - file to redirect stdout to
      stderr= string - file to redirect stderr to
      test= int - test mode

  """

# Do first fork.
  try:
    pid = os.fork()
    if test and (pid > 0): # dont fork so unittest can continue on
      return 1
    elif pid > 0:
      sys.exit(0)   # Exit first parent.
  except OSError, e:
    sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror) )
    sys.exit(1)

  # Decouple from parent environment.
  os.chdir(os.sep)
  # os.umask(0)  # not sure why they did this
  os.setsid()

  # Do second fork.
  try:
    pid = os.fork()
    if test and (pid > 0):
      return 2
    if pid > 0:
      sys.exit(0)   # Exit second parent.
  except OSError, e:
    sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror) )
    sys.exit(1)

  # Now I am a daemon!

  # Redirect standard file descriptors.
  si = open(stdin, 'r')
  so = open(stdout, 'a+')
  se = open(stderr, 'a+', 0)
  os.dup2(si.fileno(), sys.stdin.fileno())
  os.dup2(so.fileno(), sys.stdout.fileno())
  os.dup2(se.fileno(), sys.stderr.fileno())

  if test: # exit the unittest since its a copy. the parent will run and check
    print "bytes!"
    WritePid(os.getpid(),"/tmp/daemonize_unittest.pid")
    return 0

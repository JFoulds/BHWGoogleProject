#!/usr/bin/python2.4
#
# Copyright 2004 Google Inc.
# All Rights Reserved.

"""

Import this module to add a hook to call the pdb debugger on uncaught
exceptions.

To enable this, do the following in your toplevel application:

import google3.pyglib.debug

and then in your main():

google3.pyglib.debug.Init()

Then run your program with --pdb.
"""

__author__ = "chatham@google.com (Andrew Chatham)"

import sys

from google3.pyglib import flags

flags.DEFINE_boolean('pdb', 0, "Drop into pdb on uncaught exceptions")

old_excepthook = None

def _handler(type, value, tb):
  if not flags.FLAGS.pdb or hasattr(sys, 'ps1') or not sys.stderr.isatty():
    # we aren't in interactive mode or we don't have a tty-like
    # device, so we call the default hook
    old_excepthook(type, value, tb)
  else:
    import traceback
    import pdb
    # we are in interactive mode, print the exception...
    traceback.print_exception(type, value, tb)
    print
    # ...then start the debugger in post-mortem mode.
    pdb.pm()

def Init():
  global old_excepthook
  old_excepthook = sys.excepthook
  sys.excepthook = _handler

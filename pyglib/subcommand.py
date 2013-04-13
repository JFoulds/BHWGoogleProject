# Copyright 2007 Google Inc. All Rigths Reserved.
"""
A convenient yet safe way to call system commands (other programs).
This module logs the command with pyglib's logging.info, and raises
exceptions unless the command is successful.

E.g.:

   Run(['/bin/rms', '-rf', '/']) # Don't try this at home.

This module is intended for basic scripts only; for more power consider
the standard library module subprocess.py.
"""
__author__ = 'Johannes Henkel (johannes@google.com)'

from google3.pyglib import logging

import subprocess

class CommandFailed(OSError):
  """Raised when a subcommand terminates with exit status != 0."""

  def __init__(self, command, status):
    self.command = command
    self.status = status

  def __str__(self):
    return 'Terminated with exit status %d: %s' % (self.status, self.command)


class CommandTerminatedBySignal(OSError):
  """Raised when a subcommand gets terminated by a signal."""

  def __init__(self, command, signal):
    self.command = command
    self.signal = signal

  def __str__(self):
    return 'Terminated by signal %d: %s' % (self.signal, self.command)


def Run(command):
  """Run the command specified as a list, without involving a shell.

     Stdout / stderr go to the terminal (just like with os.system).
     The command is logged with logging.info
     Raises CommandFailed iff the command terminates with exit status != 0
     Raises CommandTerminatedBySignal for termination by a signal.
     Raises OSError if the command can't get executed, e.g. no such file error
  """
  if not isinstance(command, list):
    raise TypeError("Command must be given as a list")
  if not command:
    raise ValueError("Command must not be empty")
  logging.info('Running %s' % command)
  return_code = subprocess.call(command, shell=False) # May raise OSError
  if return_code > 0:
    raise CommandFailed(command, return_code)
  elif return_code < 0:
    raise CommandTerminatedBySignal(command, -return_code)

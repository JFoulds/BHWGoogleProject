#!/usr/bin/python2.4
#
# Copyright 2002-2006 Google Inc. All Rights Reserved.
# cpopescu@google.com
#
# Root for all admin runner handlers.
#
# The modus operandi is as follows:
#  - The connection reads the first line of the command and based on the
#  first token it decides which handler will handle the command
#  ('params' - > params_handler, etc). All these handlers are children of
#  admin_handler.
#  - The admin handler processes the rest of the first line plut it will
#  handle the subsequent reads and writes.
#  - The second token of the command determines the actual function that
#  executes a command. Each handler has a map with commands that it
#  executes + plus the parameters it expects that is returned by
#  its 'get_accepted_commands'. The name of the commands should be the
#  same as the handler function names.
#  - from the command properties described by the map returned by
#  get_accepted_commands, we know how many parameters to get , how many
#  extra lines to read and if we expect some raw data. Then we
#  acquire these from the first command line and from subsequent reads.
#  - when all parameters are aquired we use a thread from the thread
#  pool to actually execute the command by execing the proper function
#  with the proper arguments. Upon completion the thread is released to
#  the pool and the handler is registered to write(the answer)
#
##############################################################################

import sys
import string
import traceback
import urllib
import time
import os

import google3  # Required to enable third-party import magic.
import hotshot  # Third-party import. See ThirdPartyPython wiki.

from google3.pyglib import logging
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.tools import M

from google3.pyglib import flags

###############################################################################

FLAGS = flags.FLAGS

flags.DEFINE_integer("max_startup_time_seconds", 15*60,
                     "If adminrunner doesn't finish up its startup within this"
                     " time it will be killed.")

flags.DEFINE_string("profile_dir", "/export/hda3/tmp",
                     "The directory where hotshot profile will be stored.")
###############################################################################

ACK  = "ACKgoogle"
NACK = "NACKgoogle"

##############################################################################

# small class to hold info about handler commands
class CommandInfo:
  def __init__(self, num_params, num_lines, accept_body, method):
    self.num_params = num_params
    self.num_lines = num_lines
    self.accept_body = accept_body
    self.method = method

# helper: makes a proctocol version of validation errors
def formatValidationErrors(errors):
  """ Helper to process the validation errors in order to be returned
  to interface """
  if errors in validatorlib.VALID_CODES:
    return "VALID\n0"
  out = ["INVALID"]
  out.append("%s" % len(errors))
  for err in errors:
    out.append(repr(err.message))
    out.append(repr(err.attribs))
  out.append("1")
  return string.join(out, "\n")

class ar_handler:
  """
  Root for command handlers. If reads and parses commands according
  to the map returned by get_accepted_commands.
  """
  def __init__(self, conn, command, prefixes, params):
    self.conn = conn
    self.command = command
    self.prefixes = prefixes
    self.params = params

    self.cfg  = conn.cfg

    self.error     = None    # error encountered (text)
    self.data      = None    # excution data to write out
    self.done      = 0       # execution is done (even if self.data == None)

    self.cmd       = None    # the command we read
    self.lines     = []      # extra lines after the command line
    self.expected_bytes = -1
    self.bytes     = ""      # extra bytes after the command lines
    self.thread    = None    # for threaded commands

    # Get the command formatting and processing parameters
    self.accepted_commands = self.get_accepted_commands()

    # Get the user's info (the one who is executing the request) if any
    # We do this here because ar_handler is more Enterprise specific as
    # oppose to ent_net.ent_handler (base class) which is more general.
    self.user_data = self.parse_user_data(prefixes)

    self.profile = self.parse_profile_data(prefixes)

  def parse_user_data(self, prefixes):
    """Parse prefixes and return user_data:
       [<user> logged in from <IP> at <logged in time>]"""

    # user's info is associated with the key U in prefixes
    if prefixes and prefixes.has_key("U"):
      user_data = prefixes["U"]
      user      = self.extract_value(user_data, 'user')
      ip        = self.extract_value(user_data, 'IP')
      login     = self.extract_value(user_data, 'login')
      return M.MSG_MASTER_LOG_MSG % (user, ip, login)
    else:
      return ""

  def parse_profile_data(self, prefixes):
    """Profile data is passed as P argument with a long number.
    e.g. P=39843908 gems gethealth.
    It is the responsibility of the caller to make sure it generates unique
    ids to distinguish between two profiles.
    """
    ret = None
    if prefixes and prefixes.has_key('P'):
      try:
        ret = long(prefixes['P'])
      except:
        pass
    return ret

  def get_profile_name(self, id):
    filename = '%s/ar_profile_%d.prof' % (FLAGS.profile_dir, id)
    return filename

  def gen_profile_file(self):
    """Returns the file name for the profile to be generated. If the file
    already exists then its deleted.
    """
    filename = self.get_profile_name(self.profile)
    if os.access(filename, os.F_OK):
      os.unlink(filename)
    return filename

  def extract_value(self, line, name):
    line  = line + ' '
    start = string.find(line, name + '=')
    end   = string.find(line, ' ', start+1)
    if (-1 != start) and (-1 != end):
      return line[start+len(name)+1:end]
    else:
      return None

  def writeAdminRunnerOpMsg(self, msg):
    self.cfg.writeAdminRunnerOpMsg(msg + " " + self.user_data)

  def parse_args(self):
    """ Parse the command in args - the first line of the request """

    # make sure we have a valid command
    if not self.accepted_commands.has_key(self.command):
      self.error = "Invalid command"
      return

    # make sure we have the right number of params
    if len(self.params) != self.accepted_commands[self.command].num_params:
      self.error = "Invalid number of arguments."
      return

    if self.cfg != None:
      if self.cfg.isInStartupMode():
        diff = int(time.time()) - self.cfg.startup_time
        if (diff > FLAGS.max_startup_time_seconds):
          # Adminrunner does respond to status requests at this time.  So
          # if it gets stuck in the startup process, then it remains there
          # forever.  We need this fall back.
          logging.fatal("Startup took too long (%d seconds)" % diff)
        self.error = "It appears that the system has just been started. " \
                     "Please wait for a few minutes and try again."
        return

      # make sure this command is allowed in this state
      if self.cfg.getInstallState() not in install_utilities.INSTALL_STATES:
        self.error = "Command not allowed in state %s" % self.cfg.getInstallState()
        return

    return

  def execute(self):
    """Wrapper function around actual execute function. It executes the actual
    function in a profiler if the profiling is turned on.
    """
    if self.profile is not None:
      filename = self.gen_profile_file()
      hs = hotshot.Profile(filename)
      hs.runcall(self._execute)
      hs.close()
    else:
      self._execute()

  def _execute(self):
    """
    The actual execution ---
    executes a composed string that calles the
    corresponding functions
    """

    if self.error:
      return

    try:
      # build up a list of arguments to use
      # we don't pass self.prefixes because methods aren't prepared for them.
      # (prefixes can be found in self.prefixes)
      args = []
      args.extend(self.params)
      args.extend(self.lines)
      if self.expected_bytes >= 0 :
        args.append(self.bytes)

      # call the command
      logging.debug("calling %s %s %s" % (
        str(self.prefixes), self.command, str(args)))
      method = self.accepted_commands[self.command].method
      self.data = apply(method, args, {})

    except Exception, e:
      (t, v, tb) = sys.exc_info()
      exc_msg = string.join(traceback.format_exception(t, v, tb))
      logging.error(exc_msg)

      self.error = str(e)
      self.data = None

    self.done = 1

  def handle_read(self, data):
    """ This performs any extra reads necessary in order to run the command
    How many extra lines/bytes we need to read are specified by the
    command entry in the map returned by get_accepted_commands
    """
    # if there is an error, don't continue reading
    if self.error != None:
      return data

    num_lines = self.accepted_commands[self.command].num_lines
    if (self.accepted_commands[self.command].accept_body and
        self.expected_bytes < 0):
      num_lines = num_lines + 1

    # Pick up the lines we have to read
    while len(self.lines) < num_lines:
      (data, crt_line) = self.process_line(data)
      if crt_line == None:
        return data
      self.lines.append(crt_line)

    # We have to read a # of bytes and got the first line with the len
    if (self.accepted_commands[self.command].accept_body and
        self.expected_bytes < 0):
      try:
        self.expected_bytes = int(self.lines[-1])
        # Last line was with the # of bytes
        self.lines = self.lines[:-1]
      except ValueError:
        self.expected_bytes = 0
        self.error = "Invalid # of bytes"

    # Pick up the # of bytes we have to read
    if len(self.bytes) < self.expected_bytes:
      num_read = min(len(data), self.expected_bytes - len(self.bytes))
      self.bytes = self.bytes + data[0:num_read]
      data = data[num_read:]

    # More to peek.. return ..
    if len(self.bytes) < self.expected_bytes:
      return data
    else:
      # Picked enough .. remove the trailing \n\r
      # we expect a command next, so we don't care if we suck up extra space
      data = string.lstrip(data)

    return data

  def handle_write(self):
    """
    This passes up data to be sent to client. Write is registered upon
    task completion
    """

    # No conclussion yet and no data to send
    if self.error == None and not self.done:
      return (0, "", 0)

    # Some error encounted.. we are done
    if self.error != None:
      return (1, "%s\n%s\n" % (self.error, NACK), 0)

    # sanitize data before returning
    if type(self.data) == bool:
      self.data = int(self.data)

    # We are fine with some data to send
    return (1, "%s\n%s\n" % (self.data, ACK), 0)


  def get_accepted_commands(self):
    #  -- DON'T FORGET to define this for each handler..
    # returns a map from function name == command name
    # to a CommandInfo object
    return {}

  def process_line(self, data):
    """
    Extracts  an extra line from data and processes it. Returns
    a pair (data, line)
    """
    pos_line = string.find(data, "\n")
    if pos_line < 0:
      return (data, None)

    # Extract the trailing \n \r
    if pos_line > 0 and data[pos_line - 1] == "\r":
      line_len = pos_line - 1
    else:
      line_len = pos_line
    crt_line = data[0:line_len]

    # url unescape the line and save it
    if not self.prefixes.has_key("Q") or self.prefixes["Q"] != "0":
      crt_line = urllib.unquote_plus(crt_line)

    data = data[pos_line + 1:]

    return (data, crt_line)

##############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

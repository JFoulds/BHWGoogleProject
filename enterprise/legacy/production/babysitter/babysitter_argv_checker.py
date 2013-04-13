#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Export expected argv of servers monitored by babysitter."""

__author__ = 'npelly@google.com (Nick Pelly)'

import commands
import re
import urllib
from google3.pyglib import logging

from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import servertype_crawl
from google3.enterprise.legacy.production.babysitter import servertype_prod


class BabysitterArgvChecker:
  def __init__(self, cfg):
    """Export babysitter-argv-sum on adminrunner's /varz page.
    Register the callback wtih pywrapexprvar.

    Arguments:
      cfg: googleconfig object"""
    self.cfg = cfg

  def GetExpectedArgv(self, host, port, type):
    """Get the expected argv for a server as calculated by Babysitter.

    The expected argv is adapted to suit the argv as exported by the server.
    For example, C++ binaries will include the binary name in argv, but Java
    server's will not.

    Arguments:
      host: string, "ent1"
      port: int, 7882
      type: string, "authzchecker"
    Return:
      string: "--foo --bar", or None if Babysitter does not know the server
    """

    babysitter_cmd = servertype.GetRestartCmd(type, self.cfg,
                                              host, port)
    if babysitter_cmd is None:
      logging.warn("No babysitter command found for %s:%s (%s), not able to "
                   "export this server on babysitter-argv-sum" %
                   (host, port, type))
      return None
    binary_name = servertype.GetBinaryName(type)

    cmd = ExtractBinaryArgs(babysitter_cmd, binary_name)

    if cmd is None:
      logging.warn("Could not extract binary arguments for %s:%s, not"
                   " able to export this server on babysitter-argv-sum" %
                   (host, port))
      logging.warn("Binary name was %s, babysitter command was:" % binary_name)
      logging.warn(babysitter_cmd)
      return None

    # If its not Java then we need to prepend the full binary path
    if not IsJavaCommand(babysitter_cmd):
      cmd = "%s %s" % (ExtractBinaryPath(babysitter_cmd, binary_name), cmd)

    return cmd

  def GetAllServers(self):
    servers = self.cfg.var_copy('SERVERS').items()
    servers.sort()
    return servers

  def RestartIfArgvChanged(self):
    """For each server, compare it's old argv with the current one and restart
    the server if they are different. Return the list of restarted servers as 
    (host, port) tuples.
    """
    serverlist = self.GetAllServers()
    restarted_server_list = []

    for (port, hosts) in serverlist:
      porttype = servertype.GetPortType(port)
      for host in hosts:
        actual_argv_string = get_varz(host, port, 'argv')
        if actual_argv_string == None:   # server not exporting varz; skip...
          logging.info("Skipping argv check for %s:%s" % (host,port))
          continue
        expected_argv_string = self.GetExpectedArgv(host, port, porttype)
        if expected_argv_string != actual_argv_string:
          logging.info("argv mismatch for %s:%s: old argv = %s,\n new argv = %s"
                       % (host, port, expected_argv_string, actual_argv_string))
          servertype.RestartServer(porttype, self.cfg, host, port)
          restarted_server_list.append((host, port))
        else:
          logging.info("argv matched %s:%s" % (host, port))
    return restarted_server_list


IS_JAVA_COMMAND_RE = re.compile(" --exec[= ]\S*java ")


def IsJavaCommand(cmd):
  """Return true if babysitter cmd (string) starts a Java server."""
  return IS_JAVA_COMMAND_RE.search(cmd) is not None

BINDIR_RE = re.compile(" --bindir[= ](\S+) ")


def ExtractBinaryPath(cmd, binary_name):
  """Extract full binary path from babysitter cmd.

  If --bindir is in cmd then return the argument to bin_dir concatenated
  with the binary_name. Otherwise return the substring containing the
  binary_name.

  This does not work with JAVA commands.

  Arguments:
    cmd: string, " --bindir /foo/bar my_bin"
    binary_name: string, "my_bin"
  Return:
    string: "/foo/bar/my_bin", or None if the binary was not found
  """
  bindir_match = BINDIR_RE.search(cmd)
  if bindir_match:
    bindir = bindir_match.group(1)
    return "%s/%s" % (bindir, binary_name)
  binary_match = re.search(" (\S*%s) " % binary_name, cmd)
  if binary_match:
    return binary_match.group(1)
  return None


def ExtractBinaryArgs(cmd, binary_name):
  """Return just the arguments to the binary from a babysitter cmd.
  Babysitter restart commands typically involve loop.sh, redirection, quoting
  and other details that this function will strip.

  1) Strip everything before (and including) the first occurence of substring
  "%s " % binary_name.
  2) Strip everything after and including ">>"
  3) Clean up whitespace - only one space between words and no
  leading/trailing whitespace.
  4) Remove quoting around args

  For example:
  ExtractBinaryArgs("ulimit -c 0 && loop.sh --classpath"
                    "/some_dir/FileSystemGateway.jar --bindir "
                    "com.google.enterprise FileSystemGateway --arg1 --arg2"
                    " --arg3 FileSytemGateway.cfg 2>&1", "FileSystemGateway")
                    = "--arg1 --arg2 --arg3 FileSystemGateway.cfg"
  ExtractBinaryArgs("a very very very long command", "foobar") = None
  ExtractBinaryArgs("mybin  note    spacing", "mybin") = "note spacing"
  ExtractBinaryArgs("mybin \"--foo bar\" --foo2=\"bar2\"", "mybin")
                    = "--foo bar --foo2=bar2"

  This logic is based on behavior of the old GEMS WrongArgs rule.

  Arguments:
    cmd: String
  Return:
    String, or None if there was a problem
  """
  # Step (1) - stripping binary_name prefix
  bin_index = cmd.find("%s " % binary_name)
  if bin_index == -1:
    return None
  cmd = cmd[bin_index + len(binary_name):]

  # Step (2) - stripping '>>' suffix
  redirect_index = cmd.find(">>")
  if redirect_index != -1:
    cmd = cmd[:redirect_index]

  # Step (3) - clean up whitespace
  cmd = ' '.join(cmd.split())

  # Step (4) - Strip quotes around args
  cmd = ' '.join(StripQuotes(cmd.split()))
  cmd = '='.join(StripQuotes(cmd.split("=")))

  return cmd


def StripQuotes(input):
  """Strip quotes from the beginning and end of each string in a list of
  strings.
  Arguments:
    input: list of strings
  Return:
    list of string
  """
  output = []
  for string in input:
    output.append(StripQuotesOneString(string))
  return output


def StripQuotesOneString(input):
  """Strip quotes from the beginning and end of given string.
  Arguments:
    input: string
  Return:
    string
  """
  string = input
  while string[:1] in ["'", "\""]:
    string = string[1:]
  while string[-1:] in ["'", "\""]:
    string = string[:-1]
  return string


def get_varz(host, port, key):
  """Get the value of of varz variable 'key' for the server on 'host':'port'
  Arguments:
    host: string
    port: int
  Return:
    string: the value of the varz variable, or None is there was any problem
  """
  try:
    url = 'http://%s:%d/varz' % (host, port)
  except TypeError, e:
    logging.info('get_varz() called with bad type: %s' % e)
    return None
  try:
    # We use curl because we want to set a timeout (60 secs here). In python2.2,
    # it is not possible to set socket timeout.
    varz_status, varz_output = commands.getstatusoutput("curl -sS --max-time 60"
                                                        " %s" %url)
    if varz_status != 0:
      raise Exception(varz_output)
    varz_lines = varz_output.split('\n')
  except Exception, e:
    logging.info('Problem getting %s: %s' % (url, e))
    return None
  key_re = re.compile('^(\s|(<b>)|(<tt>))*'   # 0 or more whitespace|<b>|<tt>
                      '%s'                    # the key
                      '(\s|(</b>)|(</tt>))+'  # 1 or more whitespace|</b>|</tt>
                      '(?P<value>.*?)'        # the value
                      '(\s|(<br>))*$'         # 0 or more whitespace|<br>
                      % key)
  for line in varz_lines:
    match = key_re.match(line)
    if match:
      value = match.group('value')
      # Strip quotes
      if ((value.startswith('"') or value.startswith('\'')) and
          (value.endswith('"') or value.endswith('\''))):
        value = value[1:-1]
      return value
  return None

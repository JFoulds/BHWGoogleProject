#!/usr/bin/python2.4
#
# feng@google.com
#
# give a bin name and (optional) some extra strings that appear in
# the command argument, it will find out all pids or all pids in related groups
#
# Note: it will deal with python/python2 bin name confusions. For example:
# A python program foo.py
# * if specify the first line: #/usr/bin/env python2
#   it will appear as "python2 ./foo.py " using "ps -wwwwo cmd"
# * if specify the first line: #/usr/bin/python2
#   it will appear as "./foo.py " using "ps -wwwwo cmd"
#
#

import commands
import os
import re
import string
import sys

from google3.pyglib import flags
FLAGS = flags.FLAGS

flags.DEFINE_string('binname', '', 'program name')
flags.DEFINE_string('extra', '', 'extra matches, separated by space')
flags.DEFINE_boolean('kill', 0, 'kill the program')
flags.DEFINE_boolean('kill_by_group', 0, 'kill all processes in process group')
flags.DEFINE_boolean('print_only', 0, 'print the program pid')
flags.DEFINE_boolean('print_by_group', 0,
                     'print pids of all processes in process group')

def IsPythonIntepreter(binname):
  """ Check to see if it is a python intepreter:
  python, python2, python2.2, etc. all are python intepreter"""
  m = re.compile("python[0-9.]*$")
  return m.match(binname) != None

def check_cmd_is_the_one(cmd, binname, id_strings):
  """given a command string, it checks to see
  * if it is the right program (i.e., binname). it takes care of python/python2
  issues. E.G.:
      python2 ./adminrunner.py ...
      ./adminrunner.py
  will both be considered to have binname as adminrunner.py

  * if it command line contains those id_strings"""
  cmd_str_parts = string.split(cmd)
  bin_str_part = cmd_str_parts[0]
  if not IsPythonIntepreter(binname):
    # for python/python2, we check next string as it could be real binname
    # e.g.: python2 ./adminrunner.py ...
    if len(cmd_str_parts) >= 2 and \
       IsPythonIntepreter(os.path.basename(bin_str_part)):
      for each in cmd_str_parts[1:]:
        if each and each[0] != '-':
          bin_str_part = each
          break
        # skip stuff like '-u'
  if os.path.basename(bin_str_part) != binname:
    return 0
  # check to make sure cmd contains those id_strings
  for one_string in id_strings:
    if string.find(cmd, one_string) == -1:
      return 0
  # woohoo, survive the check!
  return 1

def Kill(binname, id_strings, sig = 'TERM', delay = 1, print_only = 0,
         by_group = 1, protect_self = 1):
  """
  find out all pids who have the 'binname' and command arguments contain
  the 'id_strings'
  * by_group: just those pids or all pids in related process groups
  * print_only: only print or will send 'sig' to those pids
  * protect_self: whether to kill/print its own pid when applicable
  """
  self_pid = os.getpid() # get its own pid
  # run the ps commands,  grab the pgids, pids, and command arguments
  ps_cmd = 'ps --no-headers axwwwwo pgid,pid,args'
  err, out = commands.getstatusoutput(ps_cmd)
  if err:
    return (err, '')
  out = filter(None, map(string.strip, string.split(out, '\n')))
  tuples = [] # (pgid, pid, cmd) tuples
  for one_line in out:
    try:
      one_tuple = string.split(one_line, None, 2)
      if len(one_tuple) != 3:
        continue
      pgid = int(one_tuple[0])
      pid = int(one_tuple[1])
      tuples.append((pgid, pid, one_tuple[2]))
    except ValueError:
      pass # ignore the incorrect line
  # scan to find qualified pgids, pids
  pgid_dict = {} # pgids
  bin_pids = []  # pids
  for one_tuple in tuples:
    # check to make sure it is right program (special case: python/python2)
    if check_cmd_is_the_one(one_tuple[2], binname, id_strings):
      pgid_dict[one_tuple[0]] = []
      bin_pids.append(one_tuple[1])
  # get those pids to send signal to. not include self_pid if not protect_self.
  pids_to_sig = []
  if by_group:
    for one_tuple in tuples:
      if one_tuple[0] in pgid_dict.keys() and \
         (not protect_self or self_pid != one_tuple[1]):
        pids_to_sig.append(one_tuple[1])
  else:
    for one_pid in bin_pids:
      if not protect_self or one_pid != self_pid:
        pids_to_sig.append(one_pid)
  if len(pids_to_sig) == 0:
    if print_only:
      print 'Nothing to kill...'
    return (0, '')
  # prepare kill command
  pids_string = string.join(map(str, pids_to_sig), ' ')
  kill_cmd = 'kill -%s %s' % (sig, pids_string)
  if sig in ['KILL', 'TERM', 'INT', 'QUIT'] and delay > 0:
    kill_cmd = '%s; sleep %s; kill -9 %s' % (
      kill_cmd, delay, pids_string)
  print pids_string
  if print_only:
    err = 0
  else:
    err, out = commands.getstatusoutput(kill_cmd)
  return (err, pids_string)

def GetServicesListeningOn(ports):
  """
  * Returns a list of strings i.e. the pids of services listening
  * on the given port
  * Args:
  *   ports: a list of strings i.e. ports that the service is listening on
  * Returns:
  *   a list of strings i.e. the pids of services listening on the given port
  """
  if type(ports) != list:
    return ''

  lsof_cmd = 'lsof'
  for port in ports:
    lsof_cmd = '%s -i :%s' % (lsof_cmd, port)
  return '%s | grep "(LISTEN)" | awk {\'print $2\'}' % lsof_cmd

def KillServicesListeningOn(ports, signal='-TERM'):
  """
  * Kill all services listening on the given ports
  * Args:
  *   ports: a list of strings i.e. ports that the service is listening on
  *   signal: the signal to kill the service with (TERM, KILL...)
  * Returns:
  *   a list of strings i.e. the pids of services that were killed
  """
  if type(ports) != list:
    return ''

  pids = GetServicesListeningOn(ports)
  os.system('kill %s $(%s)' % (signal, pids))
  return pids

if __name__ == "__main__":
  try:
    argv = FLAGS(sys.argv)  # parse flags
  except flags.FlagsError, e:
    sys.exit("%s\nUsage: %s ARGS\n%s\nchoose one of action: -kill|-kill_by_group|-print_only|-print_by_group" % (e, sys.argv[0], FLAGS))

  if FLAGS.kill + FLAGS.kill_by_group + FLAGS.print_only + FLAGS.print_by_group != \
     1 or not FLAGS.binname:
    # should have exactly one and only one of above actions
    sys.exit("%s\nUsage: %s ARGS\n%s\nchoose one of action: -kill|-kill_by_group|-print_only|-print_by_group" % (e, sys.argv[0], FLAGS))

  id_strings = string.split(FLAGS.extra)
  err, pids_string = Kill(FLAGS.binname,
                          id_strings, sig = 'TERM',
                          delay = 1,
                          print_only = FLAGS.print_only + FLAGS.print_by_group,
                          by_group = FLAGS.kill_by_group + FLAGS.print_by_group)
  if err:
    print 'err:%s pids_string:%s' % (err, pids_string)
  sys.exit(err)

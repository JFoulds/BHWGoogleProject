#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.
#
# Library of LocalBabysitter util functions.

"""\
Library of LocalBabysitter util functions.
"""

__author__ = 'npelly@google.com (Nick Pelly)'

import os

from google3.enterprise.core import core_utils
from google3.pyglib import logging

HOMEDIR_FMT   = '/export/hda3/%s'
CONF_FILE_FMT = '/etc/localbabysitter.d/%s-%s.conf'
PID_FILE_FMT  = '/var/run/%s-%s.pid'
SECURE_SCRIPT_WRAPPER_FMT = '%s/local/google/bin/secure_script_wrapper -e ' \
                            '/sbin/service %s %s'

def GetProcessGroupIDs(binary, ver):
  """Get group ids for all running processes of an enterprise binary for
  a specific enterprise version.

  Arguments:
    binary: string: binary name
    ver: string: Enterprise version. For example '4.6.4'
  Return:
    list of strings with process id's
  """
  # get process id for the binary. There should be only one per version
  cmd = 'ps --no-headers --format pgid,cmd -C %s' % binary
  # remove arguments and only get pgid and executable name
  cmd = '%s | awk "{print \$1,\$2}"' % cmd
  # get only those entries that belong to given version
  cmd = '%s | grep -w /export/hda3/%s/bin/%s' % (cmd, ver, binary)
  # get a list of unique group ids from first column
  cmd = '%s | awk "{print \$1}" | sort -u' % cmd
  out = core_utils.ExecCmd(cmd,
                           'Getting group id for %s, ver=%s' % (binary,ver))
  return out.strip().split('\n')

def RemoveFile(file):
  """Delete a file with logging.

  Arguments:
    file: string: file path
  """
  if os.path.exists(file):
    logging.info('Removing %s' % file)
    try:
      os.remove(file)
    except:
      logging.warn('Error removing %s' % file)

class LocalBabysitterUtil:
  """Class to help configure LocalBabysitter.
  One instance can handle multiple service's as long as they are the same
  Enterprise version.
  """

  def __init__(self, ver):
    """
    Arguments:
      ver: string, for example '4.6.4'
    """
    self.__ver = ver
    self.__homedir = HOMEDIR_FMT % ver

  def StartLBService(self, service, prefix, vars):
    """Starts a Localbabysitter service.
    Copies local copy of conf file to localbabysitter's conf directory,
    processing this file with self.vars_. Removes old PID file.

    Arguments:
      service: String. Used for logging.
      prefix: String. Prefix of the config file. Eg 'lockserver'
      vars: Dictionary of strings. Config file expressions like %{key} are
      substituted for value using this dictionary.
    """
    for varname in vars:
      if type(vars[varname]) == bool:
        vars[varname] = int(vars[varname])
        logging.info('(con) Converting: %s' % varname)
    srcfile = '%s/bin/%s.conf' % (self.__homedir, prefix)
    (conffile, pidfile, binary) = self.GetMiscFiles(prefix)
    logging.info('Activating %s ..' % service)
    RemoveFile(pidfile)
    logging.info('Copying %s local babysitter configuration file.' % service)
    contents = open(srcfile, 'r').read() % vars
    open(conffile, 'w').write(contents)

  def DoService(self, service, op, msg):
    cmd = SECURE_SCRIPT_WRAPPER_FMT % (self.__homedir, service, op)
    core_utils.ExecCmd(cmd, msg)

  def GetMiscFiles(self, prefix):
    """Given a service prefix, e.g. gsa-main, chubbydnsserver etc. returns
    pidfile, conffile and binary associated.
    """
    conffile = CONF_FILE_FMT % (prefix, self.__ver)
    pidfile = PID_FILE_FMT % (prefix, self.__ver)
    binary = prefix
    return [conffile, pidfile, binary]

  def KillLBService(self, service, prefix, lb_reload=0):
    """Kills all traces of a local babysitter service.
    First removes the configuration file, then pid file and then kills the
    process group.
    Note: This is a best effort method. It never returns failure unless
    there is a problem in executing a command.
    """
    (conffile, pidfile, binary) = self.GetMiscFiles(prefix)
    logging.info('Killing %s', service)
    if not os.path.exists(conffile):
      logging.warn("Configuration file %s doesn't exist. Ignoring." % conffile)
    else:
      RemoveFile(conffile)
      if lb_reload:
        self.ForceLocalBabysitterConfigReload()
    pgid = ''
    if not os.path.exists(pidfile):
      # try to guess the process id
      logging.warn('PID file %s not found. Trying to find running processes.'
         % pidfile)
      pgids = GetProcessGroupIDs(binary, self.__ver)
      # there should be at most one process group id
      if len(pgids) > 1:
        # TODO(zsyed): we may want to kill all group IDs.? I don't even know if
        # this can happen.
        raise core_utils.GenericError, \
              "More than one instance %s found" % binary
      pgid = pgids[0]
    else:
      pid_file = open(pidfile, 'r')
      pgid = pid_file.read().strip()
      pid_file.close()
      RemoveFile(pidfile)
    if not pgid:
      logging.warn('No running processes found for %s, ver=%s. Assuming dead.' %
                   (binary, self.__ver))
    else:
      logging.info('Killing all processes in group %s.' % pgid)
      core_utils.ExecCmd('kill -9 -%s' % pgid,
          'Killing process group %s' % pgid,
                         ignore_errors=1)
    logging.info('%s stopped.' % service)

  def ForceLocalBabysitterConfigReload(self):
    """Force localbabysitter to reload the configuration"""
    try:
      self.DoService('localbabysitter', 'hup', 'Updating localbabysitter...')
    except core_utils.CommandExecError:
      # TODO(zsyed): This is a temporary hack to prevent localbabysitter from
      # dying. When a hup single is sent and babysitter is evaluating a start
      # condition, it dies. This bug will be fixed in next localbabysitter
      # version that will become part of enterprise OS release and then this
      # line should be removed.
      self.DoService('localbabysitter', 'start', 'Starting localbabysitter...')

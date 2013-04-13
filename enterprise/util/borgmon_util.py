#!/usr/bin/python2.4
#
# Copyright 2006, 2007 Google Inc. All Rights Reserved.

"""Borgmon and Borgmon Reactor utility functions.

Library of Borgmon/Reactor configuration and helper functions for Enterprise.

Start by constructing an instance of the BorgmonUtil class. It saves class
members 'ver', 'total_nodes' and 'mode' which are then assumed to remain
constant for the lifetime of the object.

Alternately, you can execute this module to Start or Stop Borgmon and Reactor.
This is useful on clusters to remotely start on each node.
"""

__author__ = 'npelly@google.com (Nick Pelly)'

import sys
import urllib

from google3.pyglib import flags
from google3.pyglib import logging
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.util import E
from google3.enterprise.util import localbabysitter_util

FLAGS = flags.FLAGS

flags.DEFINE_boolean("start", 0, "Start Borgmon")
flags.DEFINE_boolean("stop", 0, "Stop Borgmon")
flags.DEFINE_integer("total_nodes", None,
    "Total number of nodes to configure for (optional). "
    "Will read from enterprise_config if ommitted.")
flags.DEFINE_string("ver", None, "Enterprise version (required). \"4.6.4\"")
flags.DEFINE_string("mode", "ACTIVE",
    "Mode to configure for. One of \"ACTIVE\", \"SERVE\", \"TEST\"")
flags.DEFINE_boolean("enable_external", 0,
    "If true, start borgmon with \"--trusted_clients all\"")

# Define Borgmon 'mode' enumerations
ACTIVE, TEST, SERVE = range(3)

# Define a map beteen install state and Borgmon 'mode'
INSTALL_STATE_TO_MODE_MAP = {'ACTIVE': ACTIVE,
                             'TEST':   TEST,
                             'SERVE':  SERVE}

# Borgmon constants
BORGMON_BASE_PORT  = 4911
BORGMON_TEST_PORT  = 4912
BORGMON_CONFIG_PATH_FMT = \
    "/export/hda3/%s/local/googledata/enterprise/borgmon/borgmon_%dway%s.cfg"
BORGMON_CONFIG_PATH_SUPERGSA_FMT = \
    "/export/hda3/%s/local/googledata/enterprise/borgmon/borgmon_supergsa%s.cfg"
BORGMON_MASTER_PREFIX = "borgmon-master"
BORGMON_GFS_CHECKPOINT_PATH = "/gfs/ent/borgmon_checkpoint"
BORGMON_NO_GFS_CHECKPOINT_PATH_FMT = \
    "/export/hda3/%s/data/enterprise-data/borgmon_checkpoint"
REACTOR_BASE_PORT = 4916
REACTOR_TEST_PORT = 4917
REACTOR_CONFIG_PATH_FMT = \
    "/export/hda3/%s/local/googledata/enterprise/borgmon/reactor_%s.cfg"

# Base exception for this module
class Error(Exception):
  pass

class BorgmonUtil:
  """A class to provide Borgmon related utilities.
  Each class instance remembers the enterprise version, total number of nodes,
  and borgmon mode. Enterprise version and total number of nodes are not
  expected to change during the lifetime of this object so setter methods are
  not provided.
  """

  def __init__(self, ver, total_nodes=None, mode=ACTIVE):
    """Construct an instance of BorgmonUtil to do some work with.

    Arguments:
      ver: string, enterprise version (eg '4.6.4')
      total_nodes: integer, number of nodes. Default is None, which causes
                   total_nodes to be read from enterprise_config.
      mode: (optional) integer, one of borgmon_util.{ACTIVE, TEST, SERVE}
            defaults to ACTIVE

    Raises:
      ValueError: If one of the arguments is invalid.
    """
    if total_nodes is None:
      total_nodes = core_utils.GetTotalNodes()

    # Perform some validation
    if ver is None:
      raise ValueError("Invalid version (version = %s)" % ver)
    if total_nodes is None or total_nodes < 1:
      raise ValueError("Invalid number of nodes (total_nodes = %s)" %
                  str(total_nodes))
    if mode not in (ACTIVE, TEST, SERVE):
      raise ValueError("Invalid mode (mode = %s)" % mode)
    # Assign class variables
    self.__ver = ver
    self.__total_nodes = total_nodes
    self.__mode = mode
    self.__lb_util = localbabysitter_util.LocalBabysitterUtil(ver)
    # Quick hack below, used later for GSA platform check.
    try:
      d = {}
      execfile("/etc/google/enterprise_sysinfo", d)
      self.__platform = d["PLATFORM"]
    except:
      self.__platform = ""


  def GetBorgmonHostname(self):
    """Get the Borgmon Master hostname.
    For a oneway this is 'ent1'. For a cluster it is a Chubby DNS address,
    for example 'borgmon-master.ent4_6_4.ls.google.com'.

    Returns:
      String - hostname
    """
    if self.__total_nodes == 1:
      return "ent1"
    return "%s.%s" % (BORGMON_MASTER_PREFIX, core_utils.GetDNSPath(self.__ver))

  def GetBorgmonPort(self):
    """Get the Borgmon port corrosponding to the current mode.

    Returns:
      Integer - port
    """
    if self.__mode == TEST:
      return BORGMON_TEST_PORT
    else:
      return BORGMON_BASE_PORT

  def GetReactorPort(self):
    """Get the Borgmon Reactor port corrosponding to the current mode.

    Returns:
      Integer - port
    """
    if self.__mode == TEST:
      return REACTOR_TEST_PORT
    else:
      return REACTOR_BASE_PORT

  def _GetBorgmonConfigPath(self):
    """ Get the borgmon configuration file path.

    Returns:
      Path to Borgmon configuration file for this platform.
      If unsure, use a oneway config.
    """
    if self.__mode == ACTIVE:
      suffix = ""
    elif self.__mode == TEST:
      suffix = '_test'
    else:
      suffix = '_serve'

    return (BORGMON_CONFIG_PATH_SUPERGSA_FMT %
            (self.__ver, suffix))

  def _GetTrustedClients(self):
    """ Get the string for --trusted_clients

    Returns:
      String, for example "127.0.0.1,216.239.43.0/24"
    """
    if FLAGS.enable_external:
      return "all"
    else:
      return "127.0.0.1,216.239.43.0/24"

  def _GetReactorConfigPath(self):
    """Get the path to the Borgmon Reactor config file for the current mode.

    Returns:
      String - the path
    """
    if self.__total_nodes > 1:
      suffix = 'cluster_'
    else:
      suffix = ''

    if self.__mode == ACTIVE:
      suffix += 'active'
    elif self.__mode == TEST:
      suffix += 'test'
    elif self.__mode == SERVE:
      suffix += 'serve'

    return REACTOR_CONFIG_PATH_FMT % (self.__ver, suffix)

  def _ReloadConfig(self):
    """Instruct borgmon to reload its configuration file. Throws IOError if
    Borgmon cannot be contacted."""
    url = "http://%s:%d/reloadconfig" % (
          self.GetBorgmonHostname(), self.GetBorgmonPort())
    urllib.urlopen(url).close()

  def _GetCheckpointPath(self):
    """Get the borgmon checkpoint file path.

    Returns:
      Path to Borgmon checkpoint file for this platform.
    """
    if core_utils.UseGFS(self.__total_nodes):
      return BORGMON_GFS_CHECKPOINT_PATH
    else:
      return BORGMON_NO_GFS_CHECKPOINT_PATH_FMT % self.__ver

  def _GetTimeseriesSize(self):
    """Return the amount of memory (in MB) to allocate to storing timeseries.

    Returns:
      Int (MB)
    """
    try:
      config_type = core_utils.GetEntConfigVar('ENT_CONFIG_TYPE')
    except AssertionError:
      # "File not Found" Assertion Error is normal during unit-testing
      logging.warn("Could not find ENT_CONFIG_TYPE, setting Borgmon timeseries"
                   " size to the oneway default")
      config_type = 'ONEBOX'
    if config_type == 'MINI':
      return 32   # 32 mb on Mini
    elif config_type == 'LITE' or config_type == 'FULL':
      return 16   # 16 mb on Mini
    else:
      return 256  # 256 all other platforms

  def _GetExtraArguments(self):
    """Get a string of additional arguments to apply to borgmon.
    At the moment these are mostly election commissar arguments used to set up
    failover in the enterprise cluster environment.

    Returns:
      String of arguments to pass to borgmon
    """
    args = ""
    args += '--svelte_servers=localhost:6297 '
    args += '--svelte_retry_interval_ms=2147483647 '
    if core_utils.UseGFS(self.__total_nodes):
      gfs_port = core_utils.GetGFSMasterPort(self.__mode == TEST)
      args += '--gfs_aliases=ent=%s:%d ' % (
              core_utils.MakeGFSMasterPath(self.__ver), gfs_port)
    if core_utils.UseLockservice(self.__total_nodes):
      # enable election commissar failover in borgmon
      args += ('--use_commissar_failover --commissar_chubby_cell %s'
               % core_utils.GetCellName(self.__ver))
    else:
      # disable election commissar failover in borgmon
      args += '--nouse_commissar_failover'
    return args

  def GetBorgmonVarValue(self, expr):
    """ call Borgmon to get the value of expr
    Arguments:
      expr: 'job:overall-urls-crawled:sum'
    Returns:
      string: (e.g '[\n15709\n]')
      '[\nNaN\n]' if cannot get the value of the expr
      None if there is an exception.
    """

    url = 'http://%s:%s/jseval?' % (self.GetBorgmonHostname(),
                                    self.GetBorgmonPort())
    params = {'expr' : '%s' %expr}
    url = url + urllib.urlencode(params)
    try:
      p = urllib.urlopen(url)
      borg_reply = p.read()
      p.close()
      return borg_reply
    except IOError, e:
      logging.error(e)
    return None

  def _EvalBorgmonReply(self, expr, reply):
    """ evaluate the reply from Borgmon to a /jseval request.

    Args:
      expr: 'job:overall-urls-crawled:sum'
      reply: '[\n15709\n]'

    Return
      15709.0 (float), or None if failed to eval.
      If the result is NaN, it returns 'NaN' since caller may
      wish to take special action in that case.
    """
    reply_stripped = reply.replace('\n','')
    if reply_stripped.lower().find('nan') >= 0:
      logging.error('NaN value for ' + expr)
      return 'NaN'
    try:
      reply_list = eval(reply_stripped)
    except (SyntaxError, NameError):
      logging.error('failed to evaluate ' + reply)
      return None
    if len(reply_list) != 1:
      logging.error('non-scalar return: ' + reply)
      return None
    val = reply_list[0]

    # sometimes we get something like {'':0}, so:

    if type(val).__name__ == 'dict':
      return val.values()[0]
    else:
      try:   # just try to make it a float
        return float(val)
      except ValueError:
        logging.error('failed to parse ' + str(val))
        return None

  def GetAndEvalBorgmonExpr(self, expr):
    """ return the value of a borgmon expression
    Arguments:
      expr: 'job:overall-urls-crawled:sum'
    Returns:
      None if Borgmon does not reply, or Borgmon does not have the value
      of the expression, or the value if not valid.
      Otherwise, return the value. e.g: 1765.0 (a float)
    Note:
      TODO (wanli) use google3.borg.monitoring.borgmon.borgmon_eval_lib
      but borgmon_eval_lib imports datetime, which is not available in
      python2.2.
      On the other hand, we cannot just change adminrunner to use python2.4
      xreadlines is only available in python2.2, not in python2.4
    """
    reply = self.GetBorgmonVarValue(expr)
    if reply is None:
      logging.error('no reply from Borgmon for ' + expr)
      return None
    value = self._EvalBorgmonReply(expr, reply)
    if value == None or value == 'NaN':
      logging.error('failed to get value for ' + expr)
      return None
    return value

  def GetBorgmonAlertSummary(self, alerting_only=1):
    """ Get Borgmon alertsummary.

    Arguments:
      alerting_only: 1 - only return alerts whose status is "alerting"

    Returns:
      the value of "http://alertsummary". None if borgmon is not accessible.
    """
    url = "http://%s:%d/alertsummary" % (self.GetBorgmonHostname(),
                                         self.GetBorgmonPort())
    if alerting_only:
      url = url + '?alertstatus=alerting'
    return core_utils.OpenURL(url)

  def StartBorgmon(self):
    """Start Borgmon and Borgmon Reactor by localbabysitter """
    logging.info('Starting Borgmon')
    lb_dict = self._CreateLocalBabysitterDict()
    self.__lb_util.StartLBService('borgmon', 'borgmon', lb_dict)
    self.__lb_util.StartLBService('reactor', 'reactor', lb_dict)
    self.__lb_util.ForceLocalBabysitterConfigReload()

  def StopBorgmon(self):
    """Stop Borgmon and Borgmon Reactor by localbabysitter"""
    self.__lb_util.KillLBService('borgmon', 'borgmon')
    self.__lb_util.KillLBService('reactor', 'reactor')
    self.__lb_util.ForceLocalBabysitterConfigReload()
    logging.info('Stopped Borgmon successfully')

  def _CreateLocalBabysitterDict(self):
    """Create a dictionary of Borgmon and Reactor settings to pass to
    localbabysitter. These settings are substituted into the localbabysitter
    .conf file.

    Return:
      Dictionary of settings
    """
    # TODO(npelly): Move similar logic out of ent_core.py into core_utils.py
    # and use core_utils.py
    return {
        'ver':                 self.__ver,
        'testver':             int(self.__mode == TEST),
        'unq':                 self.__ver.replace('.', '_'),
        'homedir':             '/export/hda3/%s' % self.__ver,
        'tmpdir':              '/export/hda3/%s/tmp' % self.__ver,
        'logdir':              '/export/hda3/%s/logs' % self.__ver,
        'lsport':              core_utils.GetLSPort(self.__mode == TEST),
        'trusted_clients':     self._GetTrustedClients(),
        'borgmon_port':        self.GetBorgmonPort(),
        'borgmon_config_file': self._GetBorgmonConfigPath(),
        'borgmon_checkpoint_file': self._GetCheckpointPath(),
        'borgmon_commissar_args': self._GetExtraArguments(),
        'borgmon_timeseries_size' : self._GetTimeseriesSize(),
        'reactor_port':        self.GetReactorPort(),
        'reactor_config':      self._GetReactorConfigPath(),
        }


def main(argv):
  # Flag validation
  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    PrintError(e)
  if not (FLAGS.start ^ FLAGS.stop):
    PrintError("One of --start or --stop")
  if not FLAGS.ver:
    PrintError("--ver is required")
  mode = INSTALL_STATE_TO_MODE_MAP.get(FLAGS.mode, None)
  if mode is None:
    PrintError("Invalid --mode")

  # Do work
  bu = BorgmonUtil(FLAGS.ver, FLAGS.total_nodes, mode)
  if FLAGS.start:
    bu.StartBorgmon()
  if FLAGS.stop:
    bu.StopBorgmon()


def PrintError(e):
  print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS.MainModuleHelp())
  sys.exit(1)


if __name__ == '__main__':
  main(sys.argv[0:])

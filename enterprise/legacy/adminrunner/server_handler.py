#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# sanjeevk@google.com
#
# Deals with requests related to servers like sending commands, restarting etc
#
###############################################################################

import string
import threading

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.adminrunner import reset_index
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M

true  = 1
false = 0
###############################################################################

class ServerHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "restart":            admin_handler.CommandInfo(1, 0, 0, self.restart),
      "restart_instance":   admin_handler.CommandInfo(1, 0, 0,
                                                      self.restart_instance),
      "kill":               admin_handler.CommandInfo(1, 0, 0, self.kill),
      "restart_babysitter": admin_handler.CommandInfo(0, 0, 0,
                                                      self.restart_babysitter),
      "send_cmd":           admin_handler.CommandInfo(2, 0, 0, self.send_cmd),
      "reset_crawl":        admin_handler.CommandInfo(1, 0, 0, self.reset_index),
     }

  #############################################################################

  def restart(self, server_name):
    """Restart all server's matching server_name"""
    logging.info("Restarting server %s" % server_name)
    srvrs = self.cfg.globalParams.GetServerManager().Set(server_name).Servers()
    for srvr in srvrs:
      self.cfg.globalParams.WriteConfigManagerServerRestartRequest(srvr.host(),
                                                                   srvr.port())
    return true

  def restart_instance(self, server_instance):
    """Restart a server instance.
    For example, instance = 'ent1:7882'

    Return False if the server instance is not in the SERVERS list, or if the
    server_instance could not be parsed into host:port format.
    """
    # Parse server_instance
    try:
      host, port = server_instance.split(':')
      port = int(port)
    except (ValueError, IndexError):
      logging.warn("Could not parse %s into host:port format" %
                   server_instance)
      return false

    # Check the server is in SERVERS
    if not host in self.cfg.getGlobalParam('SERVERS').get(port, []):
      logging.warn("Could not find %s:%s in SERVERS map, "
                   "ignoring restart_instance request" % (host, port))
      return false

    # Restart it
    logging.info("Restarting server %s:%d" % (host, port))
    self.cfg.globalParams.WriteConfigManagerServerRestartRequest(host, port)
    return true

  def kill(self, server_name):
    logging.info("Killing server %s" % server_name)
    srvrs = self.cfg.globalParams.GetServerManager().Set(server_name).Servers()
    for srvr in srvrs:
      self.cfg.globalParams.WriteConfigManagerServerKillRequest(srvr.host(),
                                                                srvr.port())
    return true

  def send_cmd(self, server_name, cmd):
    srvrs = self.cfg.globalParams.GetServerManager().Set(server_name).Servers()
    for srvr in srvrs:
      actual_cmd = ". %s; cd %s/local/google3/enterprise/legacy/util && "\
                   "./port_talker.py %s %d '%s' %d" % (
                   self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
                   self.cfg.entHome,
                   srvr.host(), srvr.port(), cmd, 60) # 1 min timeout
      err = E.execute([E.getCrtHostName()], actual_cmd, None, 0)
      if E.ERR_OK != err:
        logging.error("Error talking to server at %s:%d" % (srvr.host(),
                                                            srvr.port()))
    return true

  def restart_babysitter(self):
    'Returns bool - true on success and false on failure'
    serve_service_cmd = ". %s && " \
        "cd %s/local/google3/enterprise/legacy/scripts && " \
        "./serve_service.py %s " % (
            self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
            self.cfg.getGlobalParam('ENTERPRISE_HOME'),
            self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    # Run babysitter in the background.
    return E.exe("%s %s &" % (serve_service_cmd, "babysit")) == 0

  def reset_index(self, mode):
    """
    If mode is 'reset': does a hard reset of the crawl and indexing,
    blowing away index files.  This is done in a separate thread, so
    reset_index will return immediately.
    If mode is 'status', returns the current status string.  This will be
    'RESET_IN_PROGRESS' (if a reset is currently in progress),
    '' (if no reset is in progress),
    or an error string (if a previous reset failed).
    Any error status will be cleared when read.
    Returns: '' for 'reset', status string for 'status'
    """

    if mode == 'reset':
      t = threading.Thread(target=self.reset_index_thread)
      t.start()
      return ''
    else:
      status = reset_index.ResetIndex(self.cfg, check_status=1)

    logging.info('Ran reset_index %s, status = %s' % (mode, status))

    return status

  def reset_index_thread(self):
    """
    This is the thread that does the actual reset.
    Because the reset process takes a long time, we want to return to
    the user interface before it has completed.
    """
    logging.info('Started reset_index_thread')
    self.writeAdminRunnerOpMsg(M.MSG_RESET_CRAWL)
    status = reset_index.ResetIndex(self.cfg)
    logging.info('Completed reset_index_thread: %s' % status)
    if status:
      self.writeAdminRunnerOpMsg('%s %s' % (M.MSG_RESET_CRAWL, status))
    else:
      self.writeAdminRunnerOpMsg('%s %s' % (M.MSG_RESET_CRAWL, 'Finished'))

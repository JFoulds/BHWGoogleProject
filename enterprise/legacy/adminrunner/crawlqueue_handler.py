#!/usr/bin/python2.4
#
# Copyright 2006 Google inc.
# Author: Phuong Nguyen (pn@google.com)
###############################################################################

"""
The AdminRunner handler for crawl queue.
"""
import string
import threading
import urllib

from google3.enterprise.legacy.util import C
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import crawlqueue_manager
from google3.enterprise.legacy.production.babysitter import validatorlib

###############################################################################
true  = 1
false = 0

class CrawlQueueHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.hostnameValidator = validatorlib.Hostname(nullOK = 0,
                                                   emptyOK = 1,
                                                   allowIP = 1)

  def get_accepted_commands(self):
    return {
      'list':          admin_handler.CommandInfo(
      0, 0, 0, self.list),
      'capture':       admin_handler.CommandInfo(
      0, 1, 0, self.capture),
      'getform':       admin_handler.CommandInfo(
      1, 0, 0, self.getform),
      'delete':        admin_handler.CommandInfo(
      1, 0, 0, self.delete),
      'listhosts':     admin_handler.CommandInfo(
      1, 0, 0, self.listhosts),
      'export':        admin_handler.CommandInfo(
      0, 1, 0, self.export),
      'pageview':      admin_handler.CommandInfo(
      3, 0, 0, self.pageview),
     }

  #############################################################################

  def list(self):
    """Return list of crawl queues."""
    crawlQueues = self.cfg.crawlqueuemanager.listCrawlQueues()
    result = string.join(map(lambda(x) : x.toString(), crawlQueues), '\n')
    return '%d\n%s' % (C.CRAWLQUEUE_OK, result)

  def capture(self, queueFormStr):
    """Capture a new crawl queue. Parameter is passed in a serialized
    string of CrawlQueueForm."""
    queueForm = crawlqueue_manager.StringToCrawlQueueForm(queueFormStr)
    queueForm.completeState = C.CRAWLQUEUE_STATUS_PENDING

    nameOk = self.hostnameValidator.validate(queueForm.host, None)
    if not nameOk in validatorlib.VALID_CODES:
      return C.CRAWLQUEUE_INVALID_HOST

    status = self.cfg.crawlqueuemanager.captureCrawlQueue(queueForm)
    if status == C.CRAWLQUEUE_OK:
      msg = M.MSG_LOG_CAPTURE_CRAWLQUEUE % (queueForm.queueName)
    else:
      msg = M.MSG_LOG_CAPTURE_CRAWLQUEUE_FAILED % (queueForm.queueName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def getform(self, queueName):
    """Return one crawl queue form in its serialized format."""
    encQueueName = urllib.quote(queueName)
    return self.cfg.crawlmanagermanager.getQueueForm(encQueueName)

  def delete(self, queueName):
    """Delete a crawl queue or cancel one in progress."""
    encQueueName = urllib.quote(queueName)
    status = self.cfg.crawlqueuemanager.deleteQueue(encQueueName)

    if status == C.CRAWLQUEUE_OK:
      msg = M.MSG_LOG_DELETE_CRAWLQUEUE % (queueName)
    else:
      msg = M.MSG_LOG_DELETE_CRAWLQUEUE_FAILED % (queueName)
    self.writeAdminRunnerOpMsg(msg)

    return status

  def listhosts(self, queueName):
    """List all hosts in a complete crawl queue."""
    encQueueName = urllib.quote(queueName)
    (status, result) = self.cfg.crawlqueuemanager.listQueueHosts(
                        encQueueName)
    if status != C.CRAWLQUEUE_OK:
      return status
    return '%d\n%s' % (C.CRAWLQUEUE_OK, string.join(result, ''))

  def export(self, exportRequest):
    """Return a portion (one page, one host) or entire crawl queue in CSV format
    so it can be exported.
    If page is 0, return all pages of that host.
    If host is empty, return entire crawl queue.
    """
    (queueName, host, page) = string.split(exportRequest, '\t')
    encQueueName = urllib.quote(queueName)
    (status, buffer) = self.cfg.crawlqueuemanager.exportQueue(encQueueName,
                                                              host, int(page))
    if status == C.CRAWLQUEUE_OK:
      msg = M.MSG_LOG_EXPORT_CRAWLQUEUE % (queueName)
    else:
      msg = M.MSG_LOG_EXPORT_CRAWLQUEUE_FAILED % (queueName)
    self.writeAdminRunnerOpMsg(msg)

    if status != C.CRAWLQUEUE_OK:
      return status
    return '%d\n%s' % (C.CRAWLQUEUE_OK, string.join(buffer, '\n'))

  def pageview(self, queueName, host, page):
    """ Returns one page of URLs in a crawl queue.
    """
    encQueueName = urllib.quote(queueName)
    (status, buffer) = self.cfg.crawlqueuemanager.getQueueHostPage(encQueueName,
                                                                   host, int(page))
    if status != C.CRAWLQUEUE_OK:
      return status

    return '%d\n%s' % (C.CRAWLQUEUE_OK, string.join(buffer, ''))


###############################################################################

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

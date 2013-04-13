#!/usr/bin/python2.4
#
# Copyright 2006 Google inc.
# Author: Phuong Nguyen (pn@google.com)
#
# This file contains code to run and coordinate the crawl queue operations.
#
###############################################################################

import string
import os
import threading
import commands
import urllib

from google3.pyglib import gfile
from google3.pyglib import logging
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
import re
import time
from google3.enterprise.legacy.logs import liblog

###############################################################################

true  = 1
false = 0

## Complete status of crawl queue capturing thread.
UNKNOWN = -1
SUCCESS = 0
FAILURE = 1

PAGESIZE = 100
MAX_CRAWLQUEUE_COUNT = 50

###############################################################################

class CrawlQueueFormData:
  """This class represent a crawl queueform. Its serialized format should be
  identical to that of CrawlQueueFormData.java."""

  def __init__(self, queueName, captionTime,
               completeState, numUrlRequested,
               nextHours, host=''):
    self.queueName = queueName
    self.captionTime = captionTime
    self.completeState =  completeState
    self.numUrlRequested = numUrlRequested
    self.nextHours = nextHours
    self.host = host

  def toString(self):
    """Serialize this object to a string."""
    return ('%s\t%s\t%d\t%s\t%s\t%s' %
            (urllib.quote(self.queueName),
             self.captionTime,
             self.completeState,
             self.numUrlRequested,
             self.nextHours,
             self.host))

def StringToCrawlQueueForm(line):
  """Utility method to parse a serialized string of CrawlQueueForm."""
  (encQueueName, captionTime, completeState, numUrlRequested,
   nextHours, host) = string.split(line, '\t', 5)
  if host:
    host = string.strip(host)
  return CrawlQueueFormData(urllib.unquote(encQueueName),
                            captionTime, int(completeState),
                            numUrlRequested,
                            nextHours, host)

# Represent an index record of a host in a crawl queue.
class IndexRecord:
  def __init__(self, line):
    line = string.strip(line)
    fields = line.split('\t')
    self.host = fields[0]
    self.numUrls = int(fields[1])
    self.fpos = map(lambda(x): int(x), fields[2:-1])
    self.endFpos = int(fields[-1])

###############################################################################

class CrawlQueueManager:

  def __init__(self, cfg):
    self.cfg = cfg    # configurator object
    self.entConfig = cfg.globalParams

    liblog.MakeGoogleDir(self.entConfig, self.getCrawlQueueDir())
    # lock for updating the queue list
    self.cqueuelock = threading.RLock()
    # lock on accessing runningJobs hash
    self.joblock = threading.Lock()
    # allow at most one crawl queue caption job
    self.runningJob = {}
    self.sanitizeQueueList()


  #############################################################################
  # Main methods provided to crawlqueue_handler.
  def listCrawlQueues(self):
    """Return a list of crawl queues."""
    filename = self.getCrawlQueueListFileName()
    self.cqueuelock.acquire()
    try:
      try:
        lines = gfile.GFile(filename, 'r').readlines()
      except IOError, e:
        logging.error('Failed to read crawlqueue list. IOError: %s.' % e)
        return []

      queues = []
      for line in lines:
        try:
          queues.append(StringToCrawlQueueForm(line))
        except ValueError, e:
          logging.error('Fail to parse one line: [%s]' % line)
      return queues
    finally:
      self.cqueuelock.release()

  def captureCrawlQueue(self, queueForm):
    """Capture a snapshot of current crawl queue."""
    self.cqueuelock.acquire()
    try:
      queues = self.listCrawlQueues()
      if len(queues) > MAX_CRAWLQUEUE_COUNT:
        return C.CRAWLQUEUE_TOO_MANY

      self.joblock.acquire()
      try:
        if len(self.runningJob.keys()) != 0:
          logging.info("runningJobs.len: %d, first job name: %s" % (
            len(self.runningJob.keys()), self.runningJob.keys()[0]))
          return C.CRAWLQUEUE_IS_RUNNING

        for queue in queues:
          if queueForm.queueName == queue.queueName:
            logging.error('Cannot capture new queue with existing name %s' %
                          queue.queueName)
            return C.CRAWLQUEUE_NAME_EXISTS

        encQueueName = urllib.quote(queueForm.queueName)
        t = threading.Thread(target = self.doCaptureCrawlQueue,
                             name=encQueueName,
                             args=(encQueueName,
                                   queueForm.captionTime,
                                   queueForm.numUrlRequested,
                                   queueForm.nextHours,
                                   queueForm.host))
        t.start()
        self.runningJob[encQueueName] = t
      finally:
        self.joblock.release()

      queues.append(queueForm)
      if not self.setCrawlQueuesLocked(queues):
        logging.error('Failed to update queue list.')
        return C.CRAWLQUEUE_INTERNAL_ERROR

    finally:
      self.cqueuelock.release()
    return C.CRAWLQUEUE_OK

  def getQueueForm(self, encQueueName):
    """Return a queue form in serialized format.
    Or empty string if not found."""

    self.cqueuelock.acquire()
    try:
      queues = self.listCrawlQueues()
    finally:
      self.cqueuelock.release()

    found = false
    queueName = urllib.unquote(encQueueName)
    for queue in queues:
      if queueName == queue.queueName:
        found = true
        break

    if not found:
      logging.error('Queue %s not found.' % encQueueName)
      return ''
    return C.CRAWLQUEUE_OK + '\n' + queue.toString()

  def listQueueHosts(self, encQueueName):
    """Return a list of host in a captured queue. The result is in config format
    aggreeing with that of type HOST_LIST in CrawlQueueResponseData.java."""

    self.cqueuelock.acquire()
    try:
      (error, captionTime, totalNumberUrls,
          index_records) = self.getIndexLocked(encQueueName)
      if error != C.CRAWLQUEUE_OK:
        return (error, None)

      result = []
      result.append(repr(encQueueName) + '\n')
      result.append(repr(captionTime) + '\n')
      result.append(repr(totalNumberUrls) + '\n')

      hosts = map(lambda(x) : IndexRecord(x).host, index_records)
      result.append(repr(hosts))
    finally:
      self.cqueuelock.release()
    return (C.CRAWLQUEUE_OK, result)

  def getIndexLocked(self, encQueueName):
    """Get contents of index file. Caller takes care of synchronization."""
    found = false
    queues = self.listCrawlQueues()
    queueName = urllib.unquote(encQueueName)
    for queue in queues:
      if queueName == queue.queueName:
        found = true
        break
    if not found:
      logging.error('Queue %s not found' % encQueueName)
      return (C.CRAWLQUEUE_NAME_NOT_FOUND, 0, 0, None)

    if queue.completeState == C.CRAWLQUEUE_STATUS_PENDING:
      logging.error('Queue %s is incomplete.' % encQueueName)
      return (C.CRAWLQUEUE_INCOMPLETE, 0, 0, None)

    index_file = self.getCrawlQueueIndexFileName(encQueueName)
    try:
      fileContents = gfile.GFile(index_file, 'r').readlines()
      captionTime = int(fileContents[0][:-1])
      numUrls = int(fileContents[1][:-1])
      return (C.CRAWLQUEUE_OK, captionTime, numUrls, fileContents[2:])
    except IOError, e:
      logging.error('Failed to get queue index file %s. IOError: %s' % \
                    (index_file, e))
      return (C.CRAWLQUEUE_INTERNAL_ERROR, 0, 0, None)

  def findIndexRecord(self, host, index_lines):
    """Return an index record of a given host."""
    found = false
    for line in index_lines:
      logging.info('Found index_line: %s' % line)
      indexRecord = IndexRecord(line)
      if indexRecord.host == host:
        found = true
        break
    if not found:
      return (C.CRAWLQUEUE_HOST_NOT_FOUND, None)
    return (C.CRAWLQUEUE_OK, indexRecord)

  def getQueueHostPage(self, encQueueName, host, page):
    """Return a list of urls in a captured queue. The result is in config format,
    aggreeing with that of type URL_INFO_LIST in CrawlQueueResponseData.java."""
    self.cqueuelock.acquire()
    try:
      (error, captionTime,
       numUrls, index_lines) = self.getIndexLocked(encQueueName)
      if error != C.CRAWLQUEUE_OK:
        return error, None

      (error, indexRecord) = self.findIndexRecord(host, index_lines)
      if error != C.CRAWLQUEUE_OK:
        return error, None

      if page <= 0 or page > len(indexRecord.fpos):
        return C.CRAWLQUEUE_PAGE_NOT_FOUND, None

      startFpos = indexRecord.fpos[page-1]
      if page == len(indexRecord.fpos):  ## last page
        endFpos = indexRecord.endFpos
      else:
        endFpos = indexRecord.fpos[page]

      if startFpos < endFpos:
        # the page is not empty.
        queue_file = self.getCrawlQueueFileName(encQueueName)
        (error, lines) = ReadFile(queue_file, startFpos, endFpos)
        if error != C.CRAWLQUEUE_OK:
          return error, None
      else:
        lines = []
      buffer = []
      buffer.append(repr(encQueueName) + '\n')
      buffer.append(repr(captionTime) + '\n')
      buffer.append(repr(numUrls) + '\n')

      buffer.append(repr(host) + '\n')
      buffer.append(repr(indexRecord.numUrls) + '\n')
      buffer.append(repr(len(indexRecord.fpos)) + '\n')
      buffer.append(repr(page) + '\n')
      buffer.append(repr(lines))
      return C.CRAWLQUEUE_OK, buffer
    finally:
      self.cqueuelock.release()

  def exportQueue(self, encQueueName, host, page):
    """Export entire or portion of a queue."""
    self.cqueuelock.acquire()
    try:
      (error, captionTime, numUrls,
        index_lines) = self.getIndexLocked(encQueueName)
      if error != C.CRAWLQUEUE_OK:
        return (error, None)

      if not host or host == '':
        # take all hosts, all pages
        startFpos = 0
        if len(index_lines) == 0:
          endFpos = 0
        else:
          lastRecord = IndexRecord(index_lines[-1])
          endFpos = lastRecord.endFpos
      else:
        (error, indexRecord) = self.findIndexRecord(host, index_lines)
        if error != C.CRAWLQUEUE_OK:
          return (error, None)
        if not page or page == 0:
          startFpos = indexRecord.fpos[0]
          endFpos = indexRecord.endFpos
        else:
          if page < 0 or page > len(indexRecord.fpos):
            return (C.CRAWLQUEUE_PAGE_NOT_FOUND, None)
          startFpos = indexRecord.fpos[page-1]
          if page == len(indexRecord.fpos):
            endFpos = indexRecord.endFpos
          else:
            endFpos = indexRecord.fpos[page]
      # now we know from where to where to read. Let's do it.
      queue_file = self.getCrawlQueueFileName(encQueueName)
      error, fileContents = ReadFile(queue_file, startFpos, endFpos)
      if error != C.CRAWLQUEUE_OK:
        return (error, None)
    finally:
      self.cqueuelock.release()
    return C.CRAWLQUEUE_OK, fileContents

  def deleteQueue(self, encQueueName):
    """Delete a complete crawl queue or cancel a pending queue."""
    self.cqueuelock.acquire()
    try:
      found = false
      queues = self.listCrawlQueues()
      queueName = urllib.unquote(encQueueName)
      for queue in queues:
        if queueName == queue.queueName:
          found = true
          break
      if not found:
        logging.error('Queue not found')
        return C.CRAWLQUEUE_NAME_NOT_FOUND

      if queue.completeState == C.CRAWLQUEUE_STATUS_PENDING:
        self.joblock.acquire()
        try:
          if self.runningJob.has_key(encQueueName):
            logging.info('About to stop the running job.')
            self.runningJob[encQueueName].join(1)
            del self.runningJob[encQueueName]
          else:
            logging.error('Found a pending crawl queue with no running thread.')
        finally:
          self.joblock.release()
        logging.info('Queue %s incomplete. Canceling.' % encQueueName)
      queues.remove(queue)

      self.RemoveOldQueue(encQueueName)

      if not self.setCrawlQueuesLocked(queues):
        logging.error('Failed to update queue list.')
        return C.CRAWLQUEUE_INTERNAL_ERROR
    finally:
      self.cqueuelock.release()
    return C.CRAWLQUEUE_OK

  #############################################################################
  #  Internal helper functions
  def getCrawlQueueDir(self):
    """Return the directory of crawl queue data."""
    if self.cfg.getGlobalParam('GFS_ALIASES'):
      return '/gfs/ent/crawlqueue'
    else:
      return '%s/crawlqueue' % self.cfg.getGlobalParam('LOGDIR')

  def getCrawlQueueListFileName(self):
    """Utility method returns filename of the list of capture crawl queues."""
    return '%s/crawlqueue_list' % self.getCrawlQueueDir()

  def getCrawlQueueFileName(self, encQueueName):
    """Utility method to create filename of a crawl queue."""
    return '%s/%s.data' % (
      self.getCrawlQueueDir(), encQueueName)

  def getCrawlQueueIndexFileName(self, encQueueName):
    """Utility method returns filename of index of a crawl queue."""
    return '%s/%s.index' % (
      self.getCrawlQueueDir(), encQueueName)

  def RemoveOldQueue(self, encQueueName):
    """Remove data file index file of a crawl queue."""
    queue_file = self.getCrawlQueueFileName(encQueueName)
    index_file = self.getCrawlQueueIndexFileName(encQueueName)

    (err, _) = E.run_fileutil_command(self.entConfig, 'rm -f %s %s' % \
                                      (queue_file, index_file))
    if err:
      logging.error('Failed to remove crawlqueue snapshot file for %s' % \
                    encQueueName)

  def setQueueCompleteState(self, encQueueName, completeState):
    """This should be called by a worker thread to set complete state of
    queue caption."""

    self.cqueuelock.acquire()
    try:
      queues = self.listCrawlQueues()
      found = false
      queueName = urllib.unquote(encQueueName)
      for queue in queues:
        if queue.queueName == queueName:
          queue.completeState = completeState
          found = true
          break

      if found:
        try:
          self.setCrawlQueuesLocked(queues)
        except IOError, e:
          logging.error('Fail to write queue list. IOError: %s' % e)
          return false
      else:
        logging.error('Cannot find the queue % in %s' % (
          encQueueName, self.getCrawlQueueListFileName()))
        return false
    finally:
      self.cqueuelock.release()
    return true


  def doCaptureCrawlQueue(self, encQueueName, captionTime,
                          numUrlRequested, nextHours, host):
    """The actual work done in a worker thread to capture crawl queue."""

    result_file = self.getCrawlQueueFileName(encQueueName)
    stat_file = self.getCrawlQueueIndexFileName(encQueueName)

    backend_server_name = 'supergsa_main'

    servers = (self.entConfig.GetServerManager().
               Set(backend_server_name).Servers())
    server_str = ','.join(map(lambda(x): '%s:%d' % (x.host(), x.port()),
                              servers))
    args = []
    args.append(commands.mkarg(self.entConfig.GetEntHome()))
    args.append('crawlqueue')
    args.append(commands.mkarg(server_str))
    args.append(commands.mkarg(result_file))
    args.append(commands.mkarg(stat_file))
    args.append(commands.mkarg(encQueueName))
    args.append(commands.mkarg(captionTime))
    args.append(numUrlRequested)
    args.append(nextHours)
    args.append(commands.mkarg(host))

    cmd = ('. %s && cd %s/enterprise/legacy/util && alarm 18000 ' +
           './crawlmanager_client.py %s') % (
      self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
      self.cfg.getGlobalParam('MAIN_GOOGLE3_DIR'),
      string.join(args, ' '))
    logging.info('doCaptureCrawlQueue cmd: %s' % cmd)
    result = E.system(cmd)
    exited = os.WIFEXITED(result)
    if exited:
      result = os.WEXITSTATUS(result)
    self.joblock.acquire()
    try:
      if exited and result == SUCCESS:
        if self.runningJob.has_key(encQueueName):
          del self.runningJob[encQueueName]
          self.setQueueCompleteState(encQueueName, C.CRAWLQUEUE_STATUS_COMPLETE)
          logging.info('Crawl queue %s generated correctly' % encQueueName)
        else:
          logging.error(('Running job for queue %s complete, ' +
                         'but it was aborted.') % encQueueName)
      else:
        self.RemoveOldQueue(encQueueName)
        if self.runningJob.has_key(encQueueName):
          del self.runningJob[encQueueName]
          self.setQueueCompleteState(encQueueName, C.CRAWLQUEUE_STATUS_FAILURE)
          logging.error('Error running command [%s]' % cmd)
        else:
          logging.info(('Running job for queue %s failed, ' +
                       'but it was orphaned.') % encQueueName)
    finally:
      self.joblock.release()


  def setCrawlQueuesLocked(self, queues):
    """Set the file content for list of queues of given queueType
    on given collection."""
    try:
      gfile.GFile(self.getCrawlQueueListFileName(), 'w').write(
        string.join(map(lambda(x) : x.toString(), queues), '\n'))
    except Exception, e:
      logging.error('Cannot write CrawlQueue list. %s' % e)
      return false
    return true

  def sanitizeQueueList(self):
    """Sanitize abandoned queues, only run at init time."""
    self.cqueuelock.acquire()
    try:
      queues = self.listCrawlQueues()
      changed = false
      for queue in queues:
        if queue.completeState == C.CRAWLQUEUE_STATUS_PENDING:
          queue.completeState = C.CRAWLQUEUE_STATUS_FAILURE
          changed = true
      if changed:
        self.setCrawlQueuesLocked(queues)
    finally:
      self.cqueuelock.release()

###############################################################################
def ReadFile(filename, startFpos, endFpos):
  """Read lines from file @filename, from position @startFpos to @endFpos."""
  try:
    fp = gfile.GFile(filename, 'r')
    fp.seek(startFpos)
    buffer = []
    while fp.tell() < endFpos:
      buffer.append(fp.readline())
    fp.close()
    return (C.CRAWLQUEUE_OK, buffer)
  except IOError, e:
    logging.error('Failed to read file %s. IOError: %s' % (filename, e))
    return (C.CRAWLQUEUE_INTERNAL_ERROR, None)


if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

#!/usr/bin/python2.4
# Copyright 2006 Google Inc.
# Author: Phuong Nguyen (pn@google.com)
##############################################################################

import httplib
import string
import socket
import sys
import struct
import threading

from google3.enterprise.legacy.adminrunner import entconfig
from google3.base import pywrapbase
from google3.pyglib import gfile
from google3.pyglib import logging
from google3.enterprise.supergsa.planner.longplanner.rpc import crawlreport_pb
from google3.enterprise.legacy.adminrunner import crawlqueue_manager
from google3.net.proto import ProtocolBuffer
from google3.webutil.url import pywrapurl

true = 1
false = 0

"""Talking RPC to crawlmanagers to request a snapshot of crawl queue.
Merging results to ensure final queue size is not bigger than requested.
Writing to a file to be used by caller."""

def UrlInfoComparator(x, y):
  """A comparator for past due UrlInfo objects. Similar to
  CrawlPriority::Precedes() in enterprise/crawl/manager/crawlpriority.h"""
  if x.priority() > y.priority() or \
     x.priority() == y.priority() and x.pagerank() > y.pagerank():
    return 1
  elif x.priority() == y.priority() and x.pagerank() == y.pagerank():
    return 0
  else:
    return -1

class UrlInfoSorter:
  """This class represent a groups of UrlInfo objects closely related,
     be that sharing common host name or being undue at the capturing
     time. This class is not thread-safe, and serialization may need
     to be handled by user.
     The list is not sorted until being setDone()."""
  def __init__(self):
    self.urls = []
    self.size_ = 0
    self.done = false

  def addAll(self, urls):
    """Add a list of UrlInfo into this unsorted list. This action is
    only valid before setDone()"""
    if self.done:
      logging.error('Invalid call when UrlInfoSorter is done')
      return false
    self.urls.extend(urls)
    self.size_ += len(urls)
    return true

  def append(self, url):
    """Append one single UrlInfo object to the end of sorted list.
    This action is only valid after setDone()."""
    if not self.done:
      logging.error('Invalid call when UrlInfoSorter is done')
      return false
    self.urls.append(url)
    self.size_ += 1
    return true

  def setDone(self):
    """Sort the list and mark it as done to be ready for consumption."""
    self.urls.sort(UrlInfoComparator)
    self.done = true

  def size(self):
    """Return current size of the list."""
    return self.size_

  def setSize(self, newsize):
    """To truncate the list to the new size. This action is only
    valid after setDone()."""
    if not self.done:
      logging.error('Invalid call when UrlInfoSorter is not done.')
      return false

    if newsize > self.size_:
      logging.error('Cannot set increase size by this method.')
      return false

    self.size_ = newsize
    del self.urls[self.size_:]
    return true

  def getUrls(self):
    """Return the list of UrlInfo objects. Drop ownership on the list."""
    if not self.done:
      logging.error('Invalid call when UrlInfoSorter is not done.')
      return []
    urls = self.urls
    self.urls = []
    return urls

class CrawlQueueResponseMixer:
  """This class can receive multiple CrawlQueueResponse objects from multiple
  crawlmanager on cluster and mix them in the right priority order."""

  def __init__(self, maxRequested, numShards,
               result_file, index_file):
    self.maxRequested = maxRequested
    self.numExpectedResponses_ = numShards
    self.result_file = result_file
    self.index_file = index_file

    self.size_ = 0
    self.perHostUrlSorters = {}
    self.futureUrlInfoSorter = UrlInfoSorter()
    self.captionTime_ = 0
    self.lock = threading.Lock()
    self.finalStatus = crawlqueue_manager.UNKNOWN

  def receiveResponse(self, server_host, response):
    """Receive a CrawlQueueResponse from a crawlmanager.
    This method is thread-safe."""
    self.lock.acquire()
    try:
      self.numExpectedResponses_ -= 1

      if response == None:
        logging.error('Get None as result from server: %s' % server_host)
      else:
        self.captionTime_ = max(self.captionTime_, response.captiontime())
        for hostqueue in response.hostqueue_list():
          if not self.perHostUrlSorters.has_key(hostqueue.host()):
            self.perHostUrlSorters[hostqueue.host()] = UrlInfoSorter()
          self.perHostUrlSorters[hostqueue.host()].addAll(hostqueue.urls_list())
        if response.has_futurequeue():
          self.futureUrlInfoSorter.addAll(response.futurequeue().urls_list())
    finally:
      self.lock.release()

  def getNumExpectedResponses(self):
    return self.numExpectedResponses_

  def getCaptionTime(self):
    return self.captionTime_

  def size(self):
    return self.size_

  def handleDone(self):
    """All servers have responded, now process responses."""

    perHostSorterList = self.perHostUrlSorters.values()
    for urlSorter in perHostSorterList:
      urlSorter.setDone()
    self.futureUrlInfoSorter.setDone()

    perHostSorterUrlCounts = map(lambda(x): x.size(), perHostSorterList)
    totalCount = self.sum_(perHostSorterUrlCounts)

    if self.maxRequested < totalCount:
      # past due urls are more than enough for request, trimming down
      # these queue to give equal share for each hosts and ignore undue urls
      avgSize = self.maxRequested / len(self.perHostUrlSorters)
      counts = []
      for urlSorter in perHostSorterList:
        counts.append(min(urlSorter.size(), avgSize))

      totalCount = self.sum_(counts)
      idx = 0
      while totalCount < self.maxRequested:
        if perHostSorterUrlCounts[idx] > counts[idx]:
          counts[idx] += 1
          totalCount += 1
        idx = (idx + 1) % len(counts)
      # now trimming the perHostUrlSorters
      for idx in range(len(counts)):
        perHostSorterList[idx].setSize(counts[idx])
    else:
      # take all past due urls, and still has room for undue urls
      # distribute undue urls into per-host queues
      futureUrls = self.futureUrlInfoSorter.getUrls()
      idx = 0
      while totalCount < self.maxRequested and idx < len(futureUrls):
        urlInfo = futureUrls[idx]
        host = pywrapurl.URL(urlInfo.path()).host()
        if not self.perHostUrlSorters.has_key(host):
          self.perHostUrlSorters[host] = UrlInfoSorter()
          self.perHostUrlSorters[host].setDone()
        self.perHostUrlSorters[host].append(urlInfo)
        totalCount += 1
        idx += 1
    self.futureUrlInfoSorter = None
    self.size_ = totalCount

  def sum_(self, l):
    sum = 0
    for val in l:
      sum += val
    return sum

def GetCrawlqueueFromOneShard(server_host, server_port,
                              cr_request, cq_mixer):
  """Talk to one crawlmanager server to get its snapshot and add
  it to mix_crawlqueue. If this is the last server, write result
  to file and set final status."""
  response = SendCommand(server_host, server_port, cr_request)
  cq_mixer.receiveResponse(server_host, response)
  logging.info('crawlmanager_client.py finished with %s:%d' % (
    server_host, server_port))

  if cq_mixer.getNumExpectedResponses() == 0:
    # if this is the last response, handle the result.
    cq_mixer.handleDone()
    if WriteResult(cq_mixer):
      logging.info('request completed successfully.')
      cq_mixer.finalStatus = crawlqueue_manager.SUCCESS
    else:
      logging.error('Failed to write result to file.')
      cq_mixer.finalStatus = crawlqueue_manager.FAILURE

def SendCommand(server_host, server_port, cr_request):
  logging.info('Sending a crawl_queue request to supergsa_main.')
  h = httplib.HTTPConnection(server_host, server_port)
  h.request('POST', '/generatecrawlqueue', cr_request.Encode())
  r = h.getresponse()
  data = r.read()
  return crawlreport_pb.CrawlQueueResponse(data)


def WriteResult(cq_mixer):
  """Post process the CrawlQueueResponse buffer and write to file
  for adminrunner to use."""
  try:
    rfile = gfile.GFile(cq_mixer.result_file, 'w')
    ifile = gfile.GFile(cq_mixer.index_file, 'w')

    index_buf = []
    result_buf = []

    queues = {}

    # write to data file and index file.
    hosts = cq_mixer.perHostUrlSorters.keys()
    hosts.sort()
    for host in hosts:
      urlSorter = cq_mixer.perHostUrlSorters[host]
      count = 0
      fpos = rfile.tell()
      index_line = '%s\t%d\t%d' % (host, urlSorter.size(), fpos)
      for url in urlSorter.getUrls():
        if url.has_path():
          path = url.path()
        else:
          path = ''
        if url.has_pagerank():
          pagerank = url.pagerank()
        else:
          pagerank = -1
        if url.has_lastcrawledtime():
          lastcrawledtime = url.lastcrawledtime()
        else:
          lastcrawledtime = 0
        if url.has_nextcrawltime():
          nextcrawltime = url.nextcrawltime()
        else:
          nextcrawltime = 0
        if url.has_changeinterval():
          changeinterval = url.changeinterval()
        else:
          changeinterval = 0
        # Line format should be consistent with that in CrawlingUrl.java
        line = '%d\t%d\t%d\t%d\t%s\n' % (pagerank, lastcrawledtime,
                                         nextcrawltime, changeinterval, path)
        fpos += len(line)
        result_buf.append(line)
        count = count + 1
        if count % crawlqueue_manager.PAGESIZE == 0:
          index_line = '%s\t%d' % (index_line, fpos)

        if count % 1000 == 0:  # flush the buffer
          rfile.writelines(result_buf)
          result_buf = []

      # post-processing one per-host urlSorter.
      if len(result_buf) != 0:
        rfile.writelines(result_buf)
        result_buf = []

      index_line = '%s\t%d\n' % (index_line, fpos)
      index_buf.append(index_line)

    # write index file.
    index_buf.insert(0, '%d\n' % cq_mixer.getCaptionTime())
    index_buf.insert(1, '%d\n' % cq_mixer.size())
    ifile.writelines(index_buf)

    ifile.close()
    rfile.close()
  except Exception, e:
    logging.error('Exception: %s' % e)
    return false
  return true

def main(argv):
  argc = len(argv)
  if argc < 4:
    sys.exit(__doc__)

  config = entconfig.EntConfig(argv[0])
  if not config.Load():
    sys.exit(__doc__)

  pywrapbase.InitGoogleScript('', ['foo',
            '--gfs_aliases=%s' % config.var("GFS_ALIASES"),
            '--bnsresolver_use_svelte=false',
            '--logtostderr'], 0)
  gfile.Init()

  cmd = argv[1]
  if cmd != 'crawlqueue':
    sys.exit(__doc__)

  server_str = argv[2]

  result_file = argv[3]
  index_file = argv[4]
  queue_name = argv[5]
  caption_time = argv[6]
  num_urls_requested = int(argv[7])
  next_hours = int(argv[8])

  if argc == 10:
    crawl_host = argv[9]
  else:
    crawl_host = ''

  command = 'B= V=20 P'
  cr_request = crawlreport_pb.CrawlReportRequest()
  cr_request.set_commandtype(cr_request.CRAWL_QUEUE_COMMAND);
  cr_params = cr_request.mutable_crawlqueueparams()
  if crawl_host != '':
    cr_params.set_host(crawl_host)
  cr_params.set_numurls(num_urls_requested)
  cr_params.set_nexthours(next_hours)

  servers = server_str.split(',')

  cq_mixer = CrawlQueueResponseMixer(num_urls_requested,
                                     len(servers),
                                     result_file,
                                     index_file)

  threads = []
  for server in servers:
    (server_host, server_port) = server.split(':')
    t = threading.Thread(target = GetCrawlqueueFromOneShard,
                         name = server_host,
                         args = (server_host,
                                 int(server_port),
                                 cr_request,
                                 cq_mixer))
    threads.append(t)
    t.start()

  for t in threads:
    t.join()
  sys.exit(cq_mixer.finalStatus)

if __name__ == '__main__':
  main(sys.argv[1:])

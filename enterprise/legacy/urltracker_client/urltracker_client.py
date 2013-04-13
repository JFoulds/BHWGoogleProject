#!/usr/bin/python2.4
#
# Original Author: Mark Goodman
#
# Copyright 2002-2006 Google, Inc.

__pychecker__ = "maxbranches=0 no-callinit"

import socket
import string

from google3.enterprise.legacy.util import C
from google3.googlebot.base import pywrapurlstate
from google3.googlebot.urltracker.rpc import pywrapurltracker
from google3.net.proto import ProtocolBuffer
from google3.pyglib import logging
from google3.webutil.http import pywrapcontenttype
from google3.webutil.url import urltrackerdata_pb

true = 1
false = 0

#
# [Bug 235115] Should be zero when no dirs nor URLs match:  no data so no pages
#
def UrlTrackerServerResponseNumPages(response):
  """
  Return 0 when the total number of response matches is 0.
  Return 1 when the total number of response matches is between   1 and 100.
  Return 2 when the total number of repsonse matches if between 101 and 200.
  Etc.
  """
  num_matches = (response.dirsmatch() +
                 response.urlsmatch())
  #
  # `floordiv((num_matches + 99), 100)' in Python2 (maybe w/ "import operator")
  #
  return int((num_matches + 99) / 100)

def ContentTypeGenericComparator(x, y, key):
  if x[key] == y[key]:
    return 0
  elif x[key] > y[key]:
    return 1
  else:
    return -1

def ContentTypeAverageSizeComparator(x, y):
  diff = (x[C.CONTENT_TYPE_TOTAL_SIZE] * y[C.CONTENT_TYPE_NUM_FILES] -
          y[C.CONTENT_TYPE_TOTAL_SIZE] * x[C.CONTENT_TYPE_NUM_FILES])
  if diff == 0:
    return 0
  elif diff > 0:
    return 1
  else:
    return -1

class URLTrackerClient:
  """
  Interacts with the urltracker.
  Contains Enterprise specific filtering and sorting code.
  Urltracker Server does the sharding for us, so we don't have to.
  """

  # The above four sets contain all the states that a URL can be in.
  # We group the states to reduce the information displayed.

  HOST       = 'host'
  CRAWLED    = 'crawled'
  ERRORS     = 'errors'
  EXCLUDED   = 'excluded'
  FILE       = 'file'
  STATUS     = 'status'

  ALL        = 'all'
  SUCCESSFUL = 'successful'

  def __init__(self, host, port):
    self.host_port = "%s:%d" % (host, port)

    tag = urltrackerdata_pb.UrlTrackerData

    # everything in URL_CRAWLED
    CrawledURLStates = self.GetStatesWithUrlState(pywrapurlstate.URL_CRAWLED)

    # we split out some pre specified states as "excluded"
    ExcludedURLStates = ( tag.IN_BAD_PATTERNS,
                          tag.NOT_GOOD_PATTERNS,
                          tag.OFF_DOMAIN_REDIRECT,
                          tag.LONG_REDIRECT_CHAIN,
                          tag.INFINITE_SPACE,
                          tag.UNHANDLED_PROTOCOL,
                          tag.URL_TOO_LONG,
                          tag.ROBOTS_NO_INDEX,
                          tag.URL_REJECTED,
                          tag.UNKNOWN_EXTENSION,
                          tag.NO_FOLLOW,
                          tag.ROBOTS_DISALLOW,
                          tag.UNHANDLED_CONTENT_TYPE,
                          tag.NO_FILTER_FOR_CONTENT_TYPE,
                          tag.FILE_SIZE_OVER_LIMIT,
                          tag.ROBOTS_FORBIDDEN )

    # for some reason, this is an "other" state
    OtherErrorStates = ( tag.DRAIN_MODE_URL, )

    # all other uncrawled terminal states are "retreival" errors
    RetrievalErrorStates = []
    for state in (self.GetStatesWithUrlState(pywrapurlstate.URL_ERROR) +
                  self.GetStatesWithUrlState(pywrapurlstate.URL_ROBOTS) +
                  self.GetStatesWithUrlState(pywrapurlstate.URL_UNREACHABLE)):
      if (state not in ExcludedURLStates and
          state not in OtherErrorStates):
        RetrievalErrorStates.append(state)

    self.CrawledURLStates = CrawledURLStates
    self.RetrievalErrorStates = RetrievalErrorStates
    self.ExcludedURLStates = ExcludedURLStates


    self.sort_map = { self.HOST: None,
                      self.CRAWLED : CrawledURLStates,
                      self.ERRORS : RetrievalErrorStates,
                      self.EXCLUDED : ExcludedURLStates,
                      self.FILE : None,
                      self.STATUS : '%d-%d' % (tag.FIRST_STATE,
                                               tag.NUM_STATES-1)
                      }
    self.view_map = { self.ALL : None,
                      self.SUCCESSFUL : CrawledURLStates,
                      self.ERRORS : RetrievalErrorStates,
                      self.EXCLUDED : ExcludedURLStates,
                      }

  # GetStatesWithUrlState() takes a url_state and returns the set of tracker
  # state which are substates.
  def GetStatesWithUrlState(self, url_state):
    results = []
    for state in range(urltrackerdata_pb.UrlTrackerData.FIRST_STATE,
                       urltrackerdata_pb.UrlTrackerData.NUM_STATES):
      if pywrapurltracker.UrlTracker_get_url_state(state) == url_state:
        results.append(state)
    return results

  def BuildBrowseCommand(self, collection, uri_at, sort, view, page,
                               partial_match, num_results,
                               flatList, logging_me=true, debugging_me=false):
    if uri_at == '':
      uri_at = '0'

    if logging_me:
      logging.info("[urltracker_client:BuildBrowseCommand] Sitemap flatList = "
                   + str(flatList) + " [" + str(flatList == 0) + "]"
                   )

    command = urltrackerdata_pb.UrlTrackerServerCommand()
    if flatList == 0:
      command.set_cmd(urltrackerdata_pb.UrlTrackerServerCommand.CMD_DIR_BROWSE)
    else:
      command.set_cmd(urltrackerdata_pb.UrlTrackerServerCommand.CMD_FILE_BROWSE)

    command.set_output_type(command.OUTPUT_PROTOCOL_BUFFER)
    command.set_path(uri_at)
    command.set_file_start((page - 1) * 100)
    command.set_file_num(num_results)
    command.set_dir_start((page - 1) * 100)
    command.set_dir_num(num_results)
    command.set_skiplevel1(0)
    command.set_partial_match(partial_match)
    if collection:
      command.set_setfilter(collection)
    if sort and self.sort_map[sort] != None:
      sort_key = string.join(map(str, self.sort_map[sort]), ',')
      command.set_dirsort(sort_key)
    filter_key = None
    negativeView = false
    if view:
      if view[0] == '-':
        negativeView = true
        view = view[1:]

      # view entire state group
      if self.view_map.has_key(view):
        if self.view_map[view] != None:
          filter_key = string.join(map(str, self.view_map[view]), ',')
      # view a single state
      else:
        filter_key = view
      if negativeView:
        filter_key = '-%s' % filter_key

    if filter_key != None:
      command.set_dirfilter(filter_key)
      command.set_filefilter(filter_key)

    return command

  def SendCommand(self, command, handler='/mixer'):
    response = urltrackerdata_pb.UrlTrackerServerResponse()

    try:
      command.sendCommand(self.host_port, handler, response)
    except TypeError:
      return None
    except socket.error:
      return None
    except ProtocolBuffer.ProtocolBufferReturnError:
      return None

    return response

  def Get(self, collection, uri_at, sort, view, page, partial_match,
                flatList, logging_me=true, debugging_me=false):
    """
    Get a list of maps that contain host metadata or a list of maps that contain
    files and directory metdata from the urltracker. The last map in the list
    has the number of list chunks that match the given uri_at, and view.

    collection - collection to get results from.  Collections are restricts
    using good and bad URL patterns.

    uri_at - URI that is the parent of files and directories in the returned list.
    Leave blank to get a list of hosts.

    sort - *_ASC or *_DESC

    view - ALL, SUCCESSFUL, ERRORS, or EXCLUDED.  If not ALL, restrict files to
    this status and directories to having at least one descendant file with
    this status.

    page - which chunk of results to return.  urltracker returns at most 100
    hosts or 100 files and 100 directories at a time.  page starts at 1.
    The term is page and not chunk because the end user sees the results on a
    web page with a Google navigational bar if there is more than one page.

    partial_match - whether to allow partial match when urltracker_server
    searches for files or directories

    flatList - whether the result should be a flat list of complete URLs, else
               a hierarchical list of directory/file names (the default).
    """

    if logging_me:
      logging.info("[urltracker_client:Get] Sitemap flatList = "
                   + str(flatList) + " [" + str(flatList == 0) + "]"
                   )

    this_many_results = 100

    command = self.BuildBrowseCommand(collection, uri_at, sort, view, page,
                                      partial_match, this_many_results,
                                      flatList)

    response = self.SendCommand(command)
    if response == None: return None

    # davidw TODO: why not just return response?
    contents = []
    uri_path = response.searchedpath()  # Don't clobber formal params, please.
    path_len = len(uri_path)            # `path_len' = current node's URI len.
    first_slash_index = string.find(uri_path, '/')
    # if this is a partial search and
    # the search prefix is not a hostname, nor a directory search,
    # then the file name is just everything after the last slash (`/') char.
    if partial_match == 1 and first_slash_index != -1 and \
       uri_path[-1] != '/':
      head_index = string.rfind(uri_path, '/') + 1  # 1st after last `/'.
    # else it's an exhaustive search, or slashless, or a directory/folder URI,
    else:
      head_index = path_len             # ...so elide the entire node's URI.
    for dir in response.dirs_list():
      content = { 'numCrawledURLs' : 0,
                  'numRetrievalErrors' : 0,
                  'numExcludedURLs' : 0 }
      if first_slash_index == -1:       # If no `/'s, must've been a host name.
        content['type'] = 'HostContentData';
        path = dir.path()
        if path[-1] == '/':
          path = path[:-1]
        content['name'] = path
        content['uri'] = path
      else:
        content['type'] = 'DirectoryContentData'
        content['name'] = dir.path()[head_index:]
        if content['name'] == '': continue
        content['uri'] = dir.path()
      if flatList:                       # For flatList mode perusal,
        content['name'] = content['uri'] # ...we want complete URIs.
      for count in dir.data().counts_list():
        if count.state() in self.CrawledURLStates:
          content['numCrawledURLs'] += int(count.count())
        elif count.state() in self.RetrievalErrorStates:
          content['numRetrievalErrors'] += int(count.count())
        elif count.state() in self.ExcludedURLStates:
          content['numExcludedURLs'] += int(count.count())
      if debugging_me:
        if flatList == 0:
          content['name'] = '[Tree=' + str(flatList) + '] ' + content['name']
         #content['uri' ] = '[Tree=' + str(flatList) + '] ' + content['uri' ]
        else:
          content['name'] = '[Flat=' + str(flatList) + '] ' + content['name']
         #content['uri' ] = '[Flat=' + str(flatList) + '] ' + content['uri' ]
      contents.append(content)
    for url in response.urls_list():
      content = { 'name' : url.path()[head_index:],
                  'uri' : url.path(),
                  'state' : url.data().states_list()[-1].state(),
                  'timestamp' : url.data().states_list()[-1].timestamp(),
                  'isCookieServerError' : url.data().states_list()[-1].
                                                  iscookieservererror(),
                  'type' : 'FileContentData' }
      if content['name'] == '':
        content['name'] = '/'           # This really should be `.', yes?  Grr.
      if flatList:                       # For flatList mode perusal,
        content['name'] = content['uri'] # ...we want complete URIs.
      if debugging_me:
        if flatList == 0:
          content['name'] = '[Tree=' + str(flatList) + '] ' + content['name']
         #content['uri' ] = '[Tree=' + str(flatList) + '] ' + content['uri' ]
        else:
          content['name'] = '[Flat=' + str(flatList) + '] ' + content['name']
         #content['uri' ] = '[Flat=' + str(flatList) + '] ' + content['uri' ]
      contents.append(content)
    contents.append({ 'uriAt' : uri_path, # _Not_ necessarily == `uri_at' (?)
                      'numPages' : UrlTrackerServerResponseNumPages(response),
                      })

    return contents

  def GetFile(self, uri_at, set_map):
    """
    Get a list of maps that contain file metadata information from the
    urltracker.  The function also returns timestamp of last successful
    crawl (if ever happens) and the authentication method in use that
    time if applicable. Note that the lastSuccessfulCrawl state may or
    may not in the history list of trackerstate returned, depending on
    its age comparing to those in the history list.

    uri_at - URI for which information is returned.

    set_map - map from set fingerprint to set name

    """

    command = urltrackerdata_pb.UrlTrackerServerCommand()
    command.set_cmd(urltrackerdata_pb.UrlTrackerServerCommand.CMD_DIR_INFO)
    command.set_path(uri_at)

    response = self.SendCommand(command)
    if response == None: return None

    contents = []
    set_list = []
    last_successful_crawl_timestamp = None
    auth_method = None

    if response.urls_size() == 1:
      data = response.urls(0).data()
      for state in data.states_list():
        contents.append({ 'state': state.state(),
                          'timestamp': state.timestamp(),
                          'isCookieServerError': state.iscookieservererror(),})
      for set in data.sets_list():
        if set_map.get(set):
          set_list.append(set_map[set])
      if data.has_lastcrawltimestamp():
        last_successful_crawl_timestamp = data.lastcrawltimestamp()
        if data.has_authmethod():
          auth_method = data.authmethod()
    return (contents + [ set_list ],
            last_successful_crawl_timestamp,
            auth_method)

  def GetPageCount(self, collection, uri_at, sort, view, partial_match,
                         flatList, logging_me=true, debugging_me=false):
    """
    Get the number of pages that fit the criteria in the arguments.

    collection - collection to get results from.  Collections are restricts
    using good and bad URL patterns.

    uri_at - URI that is the parent of files and directories in the returned
    list. Leave blank to get a list of hosts.

    sort - *_ASC or *_DESC

    view - ALL, SUCCESSFUL, ERRORS, or EXCLUDED.  If not ALL, restrict files
    to this status and directories to having at least one descendant file with
    this status.

    flatList - whether the result should be a flat list of complete URLs, else
               a hierarchical list of directory/file names (the default).
    """

    if logging_me:
      logging.info("[urltracker_client:GetPageCount] Sitemap flatList = "
                   + str(flatList) + " [" + str(flatList == 0) + "]"
                   )

    page = 0                            # I.e., return no page(s) of results
    this_many_results = 0

    command = self.BuildBrowseCommand(collection, uri_at, sort, view, page,
                                      partial_match, this_many_results,
                                      flatList)

    response = self.SendCommand(command)
    if response == None: return None

    page_count = UrlTrackerServerResponseNumPages(response)

    return page_count

  def GetContentTypeStats(self, sort, collection):
    """Get the statistics on content types of specified collection."""

    command = urltrackerdata_pb.UrlTrackerServerCommand()
    cmd = urltrackerdata_pb.UrlTrackerServerCommand.CMD_CONTENTTYPE_STATS
    command.set_cmd(cmd)
    command.set_path("")
    if collection:
      command.set_setfilter(collection)

    response = self.SendCommand(command, '/ctstats')
    if response == None:
      return None

    contents = []
    if response.has_statspercontenttype():
      for stats in response.statspercontenttype().stats_list():
        mimetype = pywrapcontenttype.ContentTypeMime(stats.mimetype())
        contents.append({ C.CONTENT_TYPE_MIME_TYPES : mimetype,
                          C.CONTENT_TYPE_MIN_SIZE   : stats.minsize(),
                          C.CONTENT_TYPE_MAX_SIZE  : stats.maxsize(),
                          C.CONTENT_TYPE_TOTAL_SIZE : stats.totalsize(),
                          C.CONTENT_TYPE_NUM_FILES : stats.numfiles(),
                          })

      # sort if required.
      sorter = None
      if sort == C.CONTENT_TYPE_AVERAGE_SIZE:
        sorter = ContentTypeAverageSizeComparator
      elif sort in [ C.CONTENT_TYPE_MIME_TYPES,
                     C.CONTENT_TYPE_MIN_SIZE,
                     C.CONTENT_TYPE_MAX_SIZE,
                     C.CONTENT_TYPE_TOTAL_SIZE,
                     C.CONTENT_TYPE_NUM_FILES,
                     ]:
        sorter = lambda x,y: ContentTypeGenericComparator(x, y, sort)
      if sorter:
        contents.sort(sorter)
    return contents

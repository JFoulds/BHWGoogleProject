#!/usr/bin/python2.4
#
# Copyright 2002-2006 Google, Inc.
# All Rights Reserved.

"""
The AdminRunner handler for content diagnostics
"""

import string
import socket
import struct
import httplib

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.urltracker_client import urltracker_client
from google3.webutil.url import pywrapurl
from google3.util.hash import pywraphash
from google3.net.proto import ProtocolBuffer
from google3.docserving.rpc import doccommand_pb
from google3.docserving.rpc import docstag_pb
from google3.rtserver.rpc import rtlookup_pb
from google3.enterprise.legacy.collections import ent_collection
from google3.linkserver.rpc import linksrpc_pb

True = 1
False = 0

class DiagnoseHandler(admin_handler.ar_handler):
  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg in non-null only for testing (we cannot have multiple constructors)
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)


  def get_accepted_commands(self):
    #
    # CAVEAT:  These hard-wire the number of (newline-separated) parameters
    #          expected for each method.  This is brittle!  BE CAREFUL!!
    #
    #          See "admin_handler.py" for the ghastly details.
    return {
      'get'
      : admin_handler.CommandInfo(0,    # num_params  (space-separated)
                                  7,    # num_lines (newline-separated)
                                  0,    # accept_body
                                  #   v-- method
                                  self.get
                                  ),
      'getfile'
      : admin_handler.CommandInfo(0,    # num_params  (space-separated)
                                  1,    # num_lines (newline-separated)
                                  0,    # accept_body
                                  #   v-- method
                                  self.getFile
                                  ),
      'export'
      : admin_handler.CommandInfo(0,    # num_params  (space-separated)
                                  7,    # num_lines (newline-separated)
                                  0,    # accept_body
                                  #   v-- method
                                  self.export
                                  ),
      'getpagecount'
      : admin_handler.CommandInfo(0,    # num_params  (space-separated)
                                  6,    # num_lines (newline-separated)
                                  0,    # accept_body
                                  #   v-- method
                                  self.getpagecount
                                  ),
      'getcontenttypestats'
      : admin_handler.CommandInfo(0,    # num_params  (space-separated)
                                  2,    # num_lines (newline-separated)
                                  0,    # accept_body
                                  #   v-- method
                                  self.getContentTypeStats
                                  )
    }

  #
  # CAVEAT:  See the `CAVEAT' in `get_accepted_commands()' above.
  #
  def get(self, collection, uriAt, sort, view, page, partial_match,
                flatList, logging_me=True, debugging_me=False):

    """Returns the content diagnostics"""

    if logging_me:
      logging.info("[diagnose_handler:get] Sitemap flatList = "
                   + flatList)

    servers = (self.cfg.globalParams.GetServerManager().Set('urltracker_server')
               .Servers())
    uriAt = self.SanitizeURI(uriAt)
    for server in servers:
      client = urltracker_client.URLTrackerClient(server.host(),
                                                  int(server.port()))
      contents = client.Get(string.strip(collection),
                            string.strip(uriAt),
                            string.strip(sort),
                            string.strip(view),
                            self.GetIntValue(page),
                            self.GetIntValue(partial_match),
                            self.GetIntValue(flatList))
      if contents == None: continue
      #
      # Note:  This last-minute `pagerank' update is the sole difference btwn
      #        this procedure (viz., `get()') and `export()' below.
      #
      # Note:  The call to `exportDiagnostics()' in "AdminCaller.java" actually
      #        calls _this_ (viz., `get()'), __not__ `export()' below.
      #
      # Note:  The `execute()' code in "ExportDiagnosticsHandler.java" ignores
      #        this meticulously calculated `pagerank' data altogether.  Hmmm.
      #
      for content in contents[:-1]:
        if content.get('type') == 'FileContentData':
          content['pagerank'] = self.GetPageRank(long(pywrapurl.URL(
            content['uri']).Fingerprint()))
        if debugging_me:
          if self.GetIntValue(flatList) == 0:
            content['name'] = '[tree=' + flatList + '] ' + content['name']
          else:
            content['name'] = '[flat=' + flatList + '] ' + content['name']

      return 'response = %s\n' % repr(contents)

    return 'response = []\n'

  #
  # CAVEAT:  See the `CAVEAT' in `get_accepted_commands()' above.
  #
  def getFile(self, uriAt):
    """Returns the content status for the URI uriAt"""

    collection_names = ent_collection.ListCollections(self.cfg.globalParams)
    collection_fingerprint_map = {}
    uriAt = self.SanitizeURI(uriAt)
    for name in collection_names:
      collection_fingerprint_map[pywraphash.Fingerprint(name)] = name
    urltracker_servers = (self.cfg.globalParams.GetServerManager()
                          .Set('urltracker_server').Servers())
    DocID = long(pywrapurl.URL(uriAt).Fingerprint())

    for urltracker_server in urltracker_servers:
      urltracker_client_ = urltracker_client.URLTrackerClient(
        urltracker_server.host(), int(urltracker_server.port()))
      (response, last_successful_crawl_timestamp,
         auth_method) = urltracker_client_.GetFile(string.strip(uriAt),
                                            collection_fingerprint_map)
      if response == None: continue
      pagerank = self.GetPageRank(DocID)
      cached = self.IsDocCached(DocID)
      forwardLinks = self.GetLinkCount(DocID, 1)
      backwardLinks = self.GetLinkCount(DocID, 0)
      date = self.GetDate(DocID)
      lastmodifieddate = self.GetLastModifiedDate(DocID) 

      dict = { 'pagerank' : pagerank,
               'cached' : cached,
               'date' : date,
               'lastmodifieddate' : lastmodifieddate,
               'forwardLinks' : forwardLinks,
               'backwardLinks' : backwardLinks }

      # Note that this timestamp and the CRAWLED_NEW state may appear in
      # history list of states in @response. However, if it ages enough,
      # it will be removed from the history list. Therefore we need to
      # store away and pass around along with, if applicable, its auth_method.
      if last_successful_crawl_timestamp:
        dict['lastSuccessfulCrawlTimestamp'] = long(last_successful_crawl_timestamp)
        if auth_method:
          dict['authMethod'] = int(auth_method)

      response.append(dict)
      return 'response = %s\n' % repr(response)

    return 'response = []\n'

  #
  # CAVEAT:  See the `CAVEAT' in `get_accepted_commands()' above.
  #
  def export(self, collection, uriAt, sort, view, page, partial_match,
                   flatList, logging_me=True, debugging_me=False):

    """Export the content diagnostics"""

    if logging_me:
      logging.info("[diagnose_handler:export] Sitemap flatList = "
                   + flatList)

    servers = (self.cfg.globalParams.GetServerManager().Set('urltracker_server')
               .Servers())
    uriAt = self.SanitizeURI(uriAt)

    for server in servers:
      client = urltracker_client.URLTrackerClient(server.host(),
                                                  int(server.port()))
      contents = client.Get(string.strip(collection),
                            string.strip(uriAt),
                            string.strip(sort),
                            string.strip(view),
                            self.GetIntValue(page),
                            self.GetIntValue(partial_match),
                            self.GetIntValue(flatList))
      if contents == None: continue
      #
      # Note:  See the `Note's in `get()' above.
      #

      return 'response = %s\n' % repr(contents)

    return 'response = []\n'

  #
  # CAVEAT:  See the `CAVEAT' in `get_accepted_commands()' above.
  #
  def getpagecount(self, collection, uriAt, sort, view, partial_match,
                         flatList, logging_me=True, debugging_me=False):

    """Get page count"""

    if logging_me:
      logging.info("[diagnose_handler:getpagecount] Sitemap flatList = "
                   + flatList)

    servers = (self.cfg.globalParams.GetServerManager().Set('urltracker_server')
               .Servers())
    uriAt = self.SanitizeURI(uriAt)
    for server in servers:
      client = urltracker_client.URLTrackerClient(server.host(),
                                                  int(server.port()))
      contents = client.GetPageCount(string.strip(collection),
                                     string.strip(uriAt),
                                     string.strip(sort),
                                     string.strip(view),
                                     self.GetIntValue(partial_match),
                                     self.GetIntValue(flatList))
      if contents == None: continue
      return 'response = %s\n' % repr(contents)

    return 'response = []\n'

  def IsDocCached(self, DocID):
    doccommand = doccommand_pb.DocCommandProto()
    doccommand.set_commandname(doccommand_pb.DocCommandProto.COMMAND_RESULTS)
    docitem = doccommand.add_docitem()
    docitem.set_docid(DocID)
    docitem.set_levelbitmap(0)
    doccommand.set_binaryresults(True)
    doccommand.set_maxtitlelen(0)
    doccommand.mutable_resultsinfo().set_snippetcharsperline(0)
    doccommand.mutable_resultsinfo().set_maxnumsnippets(0)
    doccommand.mutable_resultsinfo().set_maxsnippetchars(0)
    docstag = docstag_pb.DocsTag()
    mixers = self.cfg.globalParams.GetServerManager().Set('mixer').Servers()
    for mixer in mixers:
      try:
        self.SendDocCommand(doccommand, '%s:%s' % (mixer.host(), mixer.port()),
                            '/doccommand', docstag)
      except socket.error:
        continue
      except ProtocolBuffer.ProtocolBufferReturnError:
        return False
      if docstag.result_size() > 0:
        return not docstag.result(0).seennoarchive()
      else:
        return False
    return False

  def GetPageRank(self, DocID):
    """
    Get the PageRank for this DocID as an integer ranging from 0 to 100.

    Returns -1 if PageRank is not available for this DocID.

    The passed in global DocID is the fingerprint of the URI.
    """

    srvr_set = self.cfg.globalParams.GetServerManager().Set('rtslave')

    shard_id = self.GetShardId(DocID, srvr_set)

    rtr = rtlookup_pb.RTLookupResponse()
    rtl_pr = rtlookup_pb.RTLookupCommand()
    rtl_prop = rtl_pr.add_propertylookup()
    rtl_prop.set_propertyname('pr')
    rtl_prop.add_key(DocID)

    rtservers = srvr_set.Servers()
    for rtserver in rtservers:
      # Make sure its the shard we are interested in
      if srvr_set.Shard(rtserver.port()) != shard_id:
        continue

      try:
        rtl_pr.sendCommand('%s:%s' % (rtserver.host(), rtserver.port()),
                           '/lookup', rtr)
      except socket.error:
        continue
      except ProtocolBuffer.ProtocolBufferReturnError:
        continue
      if not rtr.propertyresult(0).element_list():
        continue
      return int(round(rtr.propertyresult(0).element_list()[0].intvalue() *
                       100 / 65535.0))
    return -1

  def GetDate(self, DocID):
    """
    Get the "julian date" as an int64.
    The passed in global DocID is the fingerprint of the URI.
    """

    srvr_set = self.cfg.globalParams.GetServerManager().Set('rtslave')

    shard_id = self.GetShardId(DocID, srvr_set)

    rtr = rtlookup_pb.RTLookupResponse()
    rtl_pr = rtlookup_pb.RTLookupCommand()
    rtl_prop = rtl_pr.add_propertylookup()
    rtl_prop.set_propertyname('date')
    rtl_prop.add_key(DocID)

    rtservers = srvr_set.Servers()
    for rtserver in rtservers:
      # Make sure its the shard we are interested in
      if srvr_set.Shard(rtserver.port()) != shard_id:
        continue

      try:
        rtl_pr.sendCommand('%s:%s' % (rtserver.host(), rtserver.port()),
                           '/lookup', rtr)
      except socket.error:
        continue
      except ProtocolBuffer.ProtocolBufferReturnError:
        continue
      if not rtr.propertyresult(0).element_list():
        continue
      return int(rtr.propertyresult(0).element_list()[0].intvalue())
    return -1

  def GetLastModifiedDate(self, DocID):
    """
    Get the "last modified date" (in seconds, since 1970) as an int64.
    The passed in global DocID is the fingerprint of the URI.
    """

    srvr_set = self.cfg.globalParams.GetServerManager().Set('rtslave')

    shard_id = self.GetShardId(DocID, srvr_set)

    rtr = rtlookup_pb.RTLookupResponse()
    rtl_pr = rtlookup_pb.RTLookupCommand()
    rtl_prop = rtl_pr.add_propertylookup()
    rtl_prop.set_propertyname('lastmodifieddate')
    rtl_prop.add_key(DocID)

    rtservers = srvr_set.Servers()
    for rtserver in rtservers:
      # Make sure its the shard we are interested in
      if srvr_set.Shard(rtserver.port()) != shard_id:
        continue

      try:
        rtl_pr.sendCommand('%s:%s' % (rtserver.host(), rtserver.port()),
                           '/lookup', rtr)
      except socket.error:
        continue
      except ProtocolBuffer.ProtocolBufferReturnError:
        continue
      if not rtr.propertyresult(0).element_list():
        continue
      return long(rtr.propertyresult(0).element_list()[0].intvalue())
    return -1  

  # TODO: Convert the rest of this handler to follow the Google
  # Python style guide.

  def GetLinkCount(self, DocID, forward):
    """Get the number of links to or from a document."""

    mixers = (self.cfg.globalParams.GetServerManager().Set('mixer').
             Servers())
    for mixer in mixers:
      try:
        if forward:
          command_letter = 'f'
        else:
          command_letter = 'b'
        command = 'B= V=20 %s 1 %d\n' % (command_letter, DocID)
        result = self.SendCommand(mixer.host(), int(mixer.port()), command)
        if result:
          links_results_proto = linksrpc_pb.LinksResultsProto(result)
          return links_results_proto.totallinks()
      except socket.error:
        continue
    return -1L

  def SendCommand(self, host, port, command):
    """Send a command, get the length of the result encoded as an integer,
    and then the result."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(command)
    data = ''
    while (len(data) < 4):
      data += sock.recv(1024)
    count = struct.unpack('I', data[:4])[0]
    # Note: We don't expect much data received from this command, so we
    # set the cap at ~1M.
    # This is to fix a problem in talking to mixserver using telnet, in
    # which mixserver returns string "NACKgoogle" on error. While we
    # interprete first 4 bytes as packet length.
    # TODO: We'd better move away from using telnet now that it changes,
    # and use RPC instead.

    if count > 1000000:
      return None
    data = data[4:]
    while (len(data) < count):
      data += sock.recv(1024)
    return data

  def SendDocCommand(self, command, server, url, response):
    """
    This method differs from
    google.io.ProtocolBuffer.ProtocolMessage.sendCommand in two ways. First,
    the mixer returns an HTTP/1.0 response which httplib thinks will close but
    it doesn't. Second, it skips over the first four bytes of the response.
    These bytes represent a length value and are not part of the protocol
    buffer.
    """
    data = command.Encode()
    conn = httplib.HTTPConnection(server)
    conn.putrequest('POST', url)
    conn.putheader('Content-Length', '%d' % len(data))
    conn.endheaders()
    conn.send(data)
    resp = conn.getresponse()
    if resp.status != 200:
      raise ProtocolBuffer.ProtocolBufferReturnError(resp.status)
    resp.will_close = False
    resp.read(4)
    response.ParseFromString(resp.read())
    return response

  def SanitizeURI(self, uri):

    # if not a host request
    if ( uri != '' and string.find(uri, '/') >= 0 ):
      # if there is no protocol, assume it's HTTP
      uri = pywrapurl.URL(uri, 'http').Assemble()
    return uri

  def GetIntValue(self, string_value):
    """ Get int value of some string """

    int_value = 0
    try:
      int_value = int(string.strip(string_value))
    except ValueError:
      logging.error('User entered invalid integer value')
    return int_value

  def GetShardId(self, DocID, srvr_set):
    '''
    Find shard to use for this document
    DocID: Integer DocID
    srvr_set: Set that ServerManger.Set() returns for the servertype of interest
    '''
    # Note: I cant find a well known function for this.
    num_shards = srvr_set.NumShards()
    return (DocID & 0xFFFF) % num_shards

  #
  # CAVEAT:  See the `CAVEAT' in `get_accepted_commands()' above.
  #
  def getContentTypeStats(self, sortBy, collection):
    """Get Content Type stats from urltracker_server."""

    servers = (self.cfg.globalParams.GetServerManager().Set('urltracker_server')
               .Servers())

    for server in servers:
      client = urltracker_client.URLTrackerClient(server.host(),
                                                  int(server.port()))
      contents = client.GetContentTypeStats(sortBy, string.strip(collection))

      if contents:
        return 'response = %s\n' % repr(contents)

    return 'response = {}\n'

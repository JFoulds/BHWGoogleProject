#!/usr/bin/python2.4
#
# copyright Google 2001 and onwards
#
# This file is essentially a concatenation of two libraries separately
# written that both do roughly the same thing: issue gws queries and
# parse results into python structures.
#
# TODO: As the two libraries here were separately written to do the
# same thing, a lot of common functionality needs to be factored out
# (carefully!)
#
# TODO: Version A has a separate unittest. Version B has testing code
# built in here. That should also be unified.

###############################################################################
# Version A
# Author: Benjamin Diament

import re, urllib

def Report(verbosefile, s):
  # Verbose info/error logging helper
  if verbosefile != None:
    verbosefile.write("%s\n" % s)
## Report

class GwsParseException(Exception):
  "Base class for exceptions in gws results parsing."
class BadOutputException(GwsParseException):
  "Unexpected response from gws"
class NoncanonicalURLException(GwsParseException):
  "Gws knows the url by another name"

def GetLanguagesEncodings(urls, gws_host_port, verbosefile,
                          except_on_url_mismatch = 0,
                          except_on_bad_gws_output = 0):
  """
  Retrieve language and encoding information for a list of urls
  directly from gws by executing info queries.
  
  Input urls -- the list of urls to look up.
  Input gws_host_port -- as sjmm7:8888 or www.google.com (port defaults to 80)
  Input verbosefile -- if you want verbose error and progress info,
                       supply a file, e.g. sys.stderr. None otherwise.
  Input except_on_url_mismatch -- throw an exception in case the url supplied
                                  is known by a different canonical name.
  Input except_on_bad_gws_output -- throw an exception in case gws's
                                    response is not what you'd expect for an
                                    info query. Maybe invalid url or bad_urls.
  
  Outputs a list of tuples:
  (url requested, docid, canonical url, language, encoding)

  If the url was not found, the docid will be 0. If there was a problem with
  the gws output (e.g. the url was not really a url) the docid will be None.
  """

  docinfolist = []

  # patterns for parsing gws's output. We hope fervently that gws's
  # output doesn't change its format too often! We're only moderately
  # strict about the output format in order to make output-format
  # changes less onerous to deal with, but not blithely to collect
  # corrupt data.
  sanity_pattern = re.compile("^GSPVersion:.*^Matches:1:1$\n^Exact:0:$",
                              re.MULTILINE | re.DOTALL)
  not_found_pattern = re.compile("^Comments:.*Sorry, no content found for "
                                 "this URL$", re.MULTILINE)

  info_pattern = re.compile("^URL_1:\d+:(?P<canonical_url>[^\n]*)$.*"
                            + "^Rank_1:\d+:docid=(?P<docid>\d+) .*"
                            + "^Language_1:\d+:(?P<language>[^\n]*)$.*"
                            + "^Encoding_1:\d+:(?P<encoding>[^\n]*)$",
                            re.MULTILINE | re.DOTALL)

  kIllegalDocId = "0"
  bad_gws_output_msg = "Bad gws response for info query %s follows:\n%s\n\n"

  # Do an info query for each doc in turn
  for i in range(len(urls)):
    Report(verbosefile, "URLs done: %d" % (i+1))

    # formulate the info query in debug mode and get the result
    infoquery = "http://%s/protocol4?sa=D&client=google&deb=&q=info%%3A%s" \
			% (gws_host_port, urls[i])
    result = urllib.urlopen(infoquery).read()

    # sanity check gws's output:
    notfound = (None != not_found_pattern.search(result))
    if (None == sanity_pattern.search(result) and not notfound):
      errorstring = bad_gws_output_msg % (infoquery, result)
      Report(verbosefile, "WARNING -- " + errorstring)
      if except_on_bad_gws_output:
        raise BadOutputException, errorstring
      docinfolist.append((urls[i], None, "", "n/a", "n/a"))

    # check whether gws found the URL
    elif notfound:
      docinfolist.append((urls[i], kIllegalDocId, "", "n/a", "n/a"))
    else:
      # Get the info.
      items = info_pattern.search(result)
      if items == None:
        errorstring = bad_gws_output_msg % (infoquery, result)
        Report(verbosefile, "WARNING -- " + errorstring)
        if except_on_bad_gws_output:
          raise BadOutputException, errorstring
        docinfolist.append((urls[i], None, "", "n/a", "n/a"))

      else:
        # Some postprocessing on the gws output text. Mostly trivial
        # stuff, but here's where to add more if necessary.
        docid = items.group('docid')
        language = items.group('language')
        if language == "":
          language = "n/a"
        encoding = items.group('encoding')
        if encoding == "":
          encoding = "n/a"
        canonical_url = items.group('canonical_url')

        if canonical_url != urls[i]:
          errorstring = ("URL mismatch: Searched for \"%s\" but found \"%s\""
                         % (urls[i], canonical_url))
          Report(verbosefile, "WARNING -- " + errorstring)
          if except_on_url_mismatch:
            raise NoncanonicalURLException, errorstring
        ## if

        # record the data
        docinfolist.append((urls[i], docid, canonical_url, language, encoding))
      ## if items
    ## if None

  ## for i in range(len(urls))

  return docinfolist
## GetLanguagesEncodings


import xml.sax, xml.sax.handler

class GwsXmlHandler(xml.sax.handler.ContentHandler):
  # This is an implementation of xml.sax.handler.ContentHandler (q.v.) 
  # which sends us callbacks as it parses generic xml.
  started_ = 0
  whitespace = re.compile("^\s+$")
  def startElement(self, name, attrs):
    if name == "RES":
      self.started_ = 1
      self.sn_ = int(attrs['SN']) # number of first result
      self.count_ = int(attrs['EN']) - self.sn_ + 1 # number of last result
      self.res_ = [{} for i in range(self.count_)]
      self.current_res_ = None
      self.current_field_ = [] # a list of nested tags, outermost first
    elif not self.started_:
      return
    elif name == "R":
      assert self.current_res_ == None
      assert self.current_field_ == []
      self.current_res_ = int(attrs['N']) - self.sn_
    elif self.current_res_ != None:
      self.current_field_.append(name)
      self.res_[self.current_res_][self.current_field_[-1]] = u""

  def endElement(self, name):
    if not self.started_:
      return
    if name == "R":
      assert self.current_res_ != None
      assert self.current_field_ == [], self.current_field_
      self.current_res_ = None
    elif self.current_res_ != None:
      assert self.current_field_[-1] == name
      self.current_field_ = self.current_field_[:-1]

  def characters(self, content):
    if not self.started_:
      return
    if self.current_res_ != None:
      if self.current_field_ != []:
        self.res_[self.current_res_][self.current_field_[-1]] += content
      else:
        assert self.whitespace.match(content)

  def GetResults(self):
    if not self.started_:
      return []    
    return self.res_
##class GwsXmlHandler


def ParseGwsXml(xml_string):
  handler = GwsXmlHandler()
  xml.sax.parseString(xml_string, handler)
  return handler.GetResults()
## ParseGwsXml
  

import pprint

def GetQueryResults(gws_host_port, query, except_on_bad_output = 0,
                    debugfile = ""):
  """
  Supply a single query string, properly url-escaped in utf8 to be run
  on a gws at gws_host_port. You may follow it with options by
  appending &option=value, as appropriate for your
  application. Results returned in utf8 by default. You may override
  these settings with &ie=<input encoding>&oe=<output encoding>

  Results are a list of dictionaries with values including 'U' for
  url, 'T' for title, 'S' for snippet, and so on, according to the xml
  output.
  """
  url = ("http://%s/search?client=internal&output=xml&ie=UTF8&oe=UTF8&"
         "deb=&sa=D&q=%s" % (gws_host_port, query))
  result = urllib.urlopen(url).read()
  if debugfile:
    open("%s.xml" % debugfile, 'w').write(result)

  try:
    results = ParseGwsXml(result)
  except Exception, e:
    if except_on_bad_output:
      bad_gws_output_msg = ("Bad gws response for query %s follows:\n%s\n\n%s\n"
                            % (url, result, e))
      raise BadOutputException, bad_gws_output_msg
    return None

  if debugfile:
    outf = open("%s.txt" % debugfile, 'w')
    pprint.pprint(zip(range(len(results)), results), outf)
  return results
## GetQueryResults


def GetQueryResultsSimple(gws_host_port, query, except_on_bad_output = 0,
                          debugfile = ""):

  """
  Supply a single query string, properly url-escaped in utf8 to be run
  on a gws at gws_host_port. You may follow it with options by
  appending &option=value, as appropriate for your
  application. Results returned in utf8 by default. You may override
  these settings with &ie=<input encoding>&oe=<output encoding>

  Results are a list of tuples (url, title, docid, snippet).
  """
  def lookup(key, r):
    return r.get(key, None)
  
  pat = re.compile('^docid=(\d+) ')
  results = GetQueryResults(gws_host_port, query, except_on_bad_output, debugfile)
  if results == None:
    return None
  return [(lookup('U', r), lookup('T', r), long(pat.search(r['RK']).group(1)),
           lookup('S', r)) for r in results]
## GetQueryResultsSimple


###############################################################################
# Version B
# Author: Catalin Popescu

# -- Note -- httplib for 2.2 has some problems ..

import signal
import string
import httplib
import re
import urllib

# Gws should answer in 30 seconds
GWS_TIMEOUT = 30

# Regular xpression to match a 'URL_x:<url>' line in protocol4.
# Saves url in group 1
URL_REG = re.compile('URL_\d+:\d+:\s*(.*)\s*')

###############################################################################

def GetResults(server, port, query, timeout = GWS_TIMEOUT):
  """ Fetches the proper result page. Query is a map of url params """
  
  req = "/search?"
  for key in query.keys():
    req = req + '%s=%s&' % (key, query[key])
  req = req[:-1]

  return ExecuteRequest(server, port, req, timeout)

###############################################################################

def ExecuteRequest(server, port, req, timeout = 0):
  """Executes arbitrary get request."""
  
  def alarmHandler(signum, frame):
    raise IOError, "Host not Responding"
  
  # Setup a timeout alarm
  if timeout > 0:
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(GWS_TIMEOUT)

  try:
    try:
      h = httplib.HTTP(server, port)
      h.putrequest("GET", req)
      h.endheaders()
      
      errcode, errmsg, headers = h.getreply()
      if 200 != errcode:
        return (errcode, "")

      f = h.getfile()
      res = f.read()
      f.close()
      return (errcode, res)
    except:
      return (0, None)
  finally:
    if timeout > 0:
      signal.alarm(0)

  return (0, None)

###############################################################################

def GetCache(server, port, url):
  """ Returns the cached version of the page """
  (err, page) = GetResults(server, port, {"q" : "cache:%s" % url})
  return page
  
def GetNumResults(gws_answer):
  """Given a gws protocol4 answer we extract the extimated # of results"""
  results = string.split(gws_answer, "\n")
  for line in results:
    if string.find(line, "Matches:") == 0:
      ret = string.split(line, ":")
      return string.atoi(string.strip(ret[2]))

  return 0

def GetUrlList(gws_answer):
  """Given a gws protocol4 answer we extract a list of urls"""
  urls = []
  results = string.split(gws_answer, "\n")
  for line in results:
    match = URL_REG.match(line)
    if match:
      urls.append(match.group(1))

  return urls

def UrlInResults(results, url):
  """ This tests if the specified url is between results """
  return  -1 != string.find(results, ":%s\n" % url)

def TestTestword(server, port, site, query, total_num, url, num, epoch):
  """ This tests if queries generate proper results in the first num
  results  """
  req = {
    "site"   : site, 
    "client" : site,
    "num"    : num,
    "q"      : query,
    "output" : "protocol4"
    }
  if epoch != None:
    req["epoch"] = "-%d" % epoch
    
  (err, response) = GetResults(server, port, req)
  if err != 200:
    return 0

  if url and not UrlInResults(response, url):
    return 0
  return total_num <= GetNumResults(response)

def TestPrerequisites(server, port, site, testwords_file, epochs,
                      default_num = 20):
  """ This tests the prerequisites for a crawll on a gws server.
  The testwords file contains the test queries on each line.
  <querry>\<url>\<num>\<total_num>

  It returns a pair (latest epoch, list of errors)
  """
  # Get the non empty lines from testword file in 'tests'
  try:    tests = map(string.strip, open(testwords_file).readlines())
  except: return (0, ["Invalid prerequisites file"])
  tests = filter(lambda s: s, tests)

  errors = []
  epochs.sort()
  epochs.reverse()
  min_epoch = epochs[0]
  for test in tests:
    test = map(string.strip, string.split(test, "\\"))
    query = test[0]
    try:    url = string.strip(urllib.unquote_plus(test[1]))
    except: url = None
    try:    num = string.atoi(urllib.unquote_plus(test[2]))
    except: num = default_num
    try:    total_num = string.atoi(urllib.unquote_plus(test[3]))
    except: total_num = 0
    
    max_epoch = -1
    for epoch in epochs:
      if TestTestword(server, port, site, query, total_num, url, num, epoch):
        max_epoch = epoch
        break
      
    if max_epoch != epochs[0]:
      errors.append(query)
      if max_epoch < min_epoch:
        min_epoch = max_epoch
  
  return (min_epoch, errors)


###############################################################################

if __name__ == '__main__':
  ## Testing here
  server = "www.google.com"
  port = 80
  query = {"client": "internal", "q":"google", "output" : "protocol4"}
  print("ERROR : %d\nRESULT : %s\n" % GetResults(server, port, query))
  print("CACHE : \n%s" % GetCache(server, port, "http://www.google.com/"))
  print("NUM_RESULTS : \n%s" % GetNumResults(
    GetResults(server, port, query)[1]))
  print("URL IN RESULT : \n%d\n" % UrlInResults(
    GetResults(server, port, query)[1], "http://www.google.com/"))
  server = "sitesearch6.google.com"
  print("GOOD TEST : \n%d\n" % TestTestword(
    server, port, "cisco", "cisco",
    100000, "http://www.cisco.com/", 20, None))
  print("GOOD TEST : \n%d\n" % TestTestword(
    server, port, "cisco", "cisco",
    100000, None, 20, None))
  print("BAD TEST : \n%d\n" %  TestTestword(
    server, port, "cisco", "cisco",
    20, "http://www.ciscos.com/", 20, None))
  print("BAD TEST : \n%d\n" %  TestTestword(
    server, port, "cisco", "cisco",
    10000000, "http://www.cisco.com/", 20, None))

#!/usr/bin/python2.4
#
# Copyright 2002-2006 Google Inc.
# All rights reserved.
# cristian@google.com
#
# pattern commands: all types of url-pattern matching functionality
# -- pythonized  from URLPatternHandler.java
#
###############################################################################

import sys
import string

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.webutil.urlutil import pywrapurlmatchmapper

true  = 1
false = 0

###############################################################################

class URLPatternHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params, cfg = None):
    # cfg in non-null only for testing (we cannot have multiple constructore)
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "match" :         admin_handler.CommandInfo(
      0, 2, 0, self.match),
      "checkstart":     admin_handler.CommandInfo(
      0, 3, 0, self.checkstart),
      "checkoneurl":     admin_handler.CommandInfo(
      0, 3, 0, self.checkOneUrl),
      }

  #############################################################################

  def match(self, urls, patterns):
    urls = map(remove_trailing_br,  string.split(urls, "\n"))
    patterns = map(remove_trailing_br, string.split(patterns, "\n"))

    mapper = pywrapurlmatchmapper.UrlMatcherMapper("", true, false)
    for i in range(len(patterns)):
      if patterns[i] and patterns[i][0] != '#':
        mapper.AddPattern(patterns[i], "%s" % i)

    # now match the urls against the list of patterns
    results = []
    for url in urls:
      # exclude comments and empty lines
      if url and url[0] != '#':
        attachment = mapper.GetMatchingString(url);
        if attachment:
          element = (url, patterns[string.atoi(attachment)])
        else:
          element = (url, None)
        results.append(element)
    del mapper
    return results

  def checkstart(self, starturls, goodurls, badurls):
    goodMatches = self.match(starturls, goodurls);
    badMatches  = self.match(starturls, badurls);

    ret = []
    # Put the urls that mach badurls or the ones which don't match goofurls
    # in a triplet of ret
    assert len(goodMatches) == len(badMatches)
    for i in range(len(goodMatches)):
      goodPair = goodMatches[i]
      badPair  = badMatches[i]
      if goodPair[1] == None or badPair[1] != None:
        ret.append((goodPair[0], goodPair[1], badPair[1]))
    return ret

  def checkOneUrl(self, url, goodurls, badurls):
    goodMatches = self.match(url, goodurls)
    badMatches  = self.match(url, badurls)

    if ( len(goodMatches) != 0 and goodMatches[0][1] != None and
         len(badMatches) != 0 and badMatches[0][1] == None):
      return 0
    return 1


  #############################################################################

def remove_trailing_br(s):
  """ Helper that removes the trailing \\r """
  if not s: return s
  if s[-1] != '\r': return s
  return s[:-1]

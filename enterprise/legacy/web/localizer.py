#!/usr/bin/python2.4
#
# Copyright 2004-2006 Google Inc.
# All Rights Reserved.

"""
Assorted routines for localization of the Python web server.

This is similar to com.google.i18n.Localizer
"""

__author__ = "kens@google.com (Ken Shirriff)"

import re

def BestLanguage(provided, requested):
  """
  We look for a perfect match ("en-us" != "en-gb")
  and failing that we look for a partial match ("en-us" == "en-gb")
  and failing that we return provided[0].
  Naturally, provided.size() must be > 0
  Input:
    provided: tuple of language strings available
      (string case is ignored; locale separator can be "-" or "_")
    requested: tuple of language strings requested
  Output: The best match, which is an entry from provided

  This is based on Localizer.bestLanguage()
  """
  best_partial = None
  for req in requested:
    req_normalized = req.lower().replace('_', '-')
    req_prefix = re.sub('-.*', '', req_normalized)
    for prov in provided:
      prov_normalized = prov.lower().replace('_', '-')
      prov_prefix = re.sub('-.*', '', prov_normalized)
      if req_normalized == prov_normalized:
        return prov
      if not best_partial and (req_prefix == prov_prefix):
        best_partial = prov
  if best_partial:
    return best_partial
  return provided[0]

def LangPrefs(args, accept_language_header):
  """
    Gets language preference string for this request, e.g.
    "fr, en-us;q=1.0"
    We consider, in order:
      - whether or not "hl=" was specified in the request
      - and finally, the "accept-language" HTTP header

    Input:
      args: dictionary of input arguments: args[key] = value
      accept_language_header: the Accept-Language header from the request

   based on com.google.servlet.GoogleServlet.langPrefs()
  """

  desired = []
  # hl= has highest priority
  if args.has_key('hl'):
    desired.append(args['hl'])

  desired.extend(ParseAcceptLanguageHeader(accept_language_header))

  return desired

def ParseAcceptLanguageHeader(header):
  """
  Parses an Accept-Language header and returns a list of languages, sorted
  from best to worst.  This is based on RFC 2068, but is not a strict
  parser.
  Input: the Accept-Language header, e.g. "da, en-gb;q=0.8, en;q=0.7"
  Output: a list of languages, sorted best to worst.

  Any errors are ignored.
  """
  langs = []
  parts = re.split('\s*,\s*', header)
  for part in parts:
    part = part.strip()
    if not part:
      continue
    q = 1 # Default q
    m = re.match('([^;]*);q=([0-9.]+)', part)
    if m:
      part = m.group(1)
      q = float(m.group(2));
    langs.append([-q, part]) # Prepend with -q to sort from highest to lowest
  langs.sort()
  return [lang for (q, lang) in langs]

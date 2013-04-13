#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Index warmer utility to keep the index from sleeping.

The index warmer is used by
  enterprise/legacy/scripts/periodic_script.py
in which another Python process is forked to run this script.

When invoked, the index warmer will issue two types of HTTP hits to the
Enterprise Front End in order to keep the index cache and/or the
Enterprise Front End from paging out.

The first type will be an HTTP hit to the Enterprise Front End (port 7800)
with no parameters.  This is used to trigger the serving of the search page,
in an attempt to warm the Enterprise Front End.

The second type will be a series (default=5) of HTTP hits with randomly
generated query terms, in an attempt to warm the index.

The query terms will be in the following format:
  q={common_term} -{random_term}
where common_term is located in COMMON_TERM_LIST, with redundant terms
to give weights to different terms, and random_term is a randomly
generated string.

The exclusion prefix '-' will force the the engine to search the index.

Credit to Vish Subramanian (vish@google.com) for providing the direction
and idea of this index warmer.
"""

__author__ = "pychen@google.com (Peter Y. Chen)"

import httplib
import random
import socket
import sys
import time
import urllib

SERVER_URL = "localhost:7800"
SEARCH_ACTION = "/search?oe=UTF-8&ie=UTF-8&sa=D&skip=o"
MIN_TERM_LENGTH = 10
MAX_TERM_LENGTH = 15
HIT_COUNT = 3     # sets of FE + Index hit per invocation
HIT_INTERVAL = 5  # seconds between each warming hit
COMMON_TERM_LIST = [
    "http", "http", "http", "http", "http",
    "ftp", "ftp", "smb",
    "com", "org", "gov", "edu",
    ]


def GetQueryTerm():
  """Generates a random query string of random length.

  The query string will be in the following format:
    {common_term} -{random_term}
  where {common_term} is randomly chosen from the weighted list
  COMMON_TERM_LIST, and {random_term} is a randomly generated string
  whose length is between MIN_TERM_LENGTH and MAX_TERM_LENGTH.

  Returns:
    string - the randomly generated strings
  """
  random_index = random.randrange(0, len(COMMON_TERM_LIST))
  common_term = COMMON_TERM_LIST[random_index]
  term_length = random.randint(MIN_TERM_LENGTH, MAX_TERM_LENGTH)
  random_list = []
  for j in range(term_length):
    random_list.append(chr(ord("a") + random.randint(0, 25)))
  random_term = "".join(random_list)
  query_term = common_term + " -" + random_term
  return query_term


def HitEngine(server_url, query_term):
  """Queries the search engine with qutoed UTF-8 search term.

  Args:
    server_url: string - URL string of the server to hit
    query_term: string - query term to use for the hit

  Returns:
    integer - status code of the HTTP response

  Note:
    Exceptions are not bubbled up, because the index warmer will be
    embedded as part of another script which invokes many other processes.
    Since the index warmer is a low priority process, we would rather that
    it does nothing than to break any existing processes, even if there is
    a runtime exception due to configuration etc.
  """
  status = 0
  try:
    socket.setdefaulttimeout(6.0)
    conn = httplib.HTTPConnection(server_url)
    conn.request("GET", "/")
    conn.getresponse().read()
    time.sleep(HIT_INTERVAL)
    conn.request("GET", SEARCH_ACTION + "&q=" + urllib.quote(query_term))
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
  except socket.timeout:
    return -3
  except socket.gaierror:
    return -1
  except Exception, ex:
    return -2

  return status


def main(argv):
  random.seed()
  for i in range(HIT_COUNT):
    search_term = GetQueryTerm()
    HitEngine(SERVER_URL, search_term)
    time.sleep(HIT_INTERVAL)


if __name__ == "__main__":
  main(sys.argv[1:])

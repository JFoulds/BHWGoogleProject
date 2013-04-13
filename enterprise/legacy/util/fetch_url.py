#!/usr/bin/python2.4
# (c) Google 2002
# cristian@google.com
#
# This is a small utility script for fetching a URL content and dumping it
# to the standard output. Nothing fancy. It returns the error code on the
# first line and the content starting with the next line.
#
###############################################################################
"""
Usage:
  ./fetch_url.py <url>
"""

import sys
import string
from google3.gws import gws_results

###############################################################################

if __name__ == "__main__":

  try:
    url = sys.argv[1]
  except:
    sys.exit(__doc__)

  host_pos = string.find(url, "://")
  url_pos = string.find(url, "/", host_pos + 3)
  if host_pos < 0 or url_pos < 0:
    sys.exit(__doc__)
  host_port = string.split(url[host_pos + 3 : url_pos], ":")
  url = url[url_pos:]
  if len(host_port) != 2:
    host = host_port[0]
    port = 80
  else:
    host = host_port[0]
    port = string.atoi(host_port[1])

  (err, resp) = gws_results.ExecuteRequest(host, port, url, 60)
  print "%s\n%s"  % (err, resp)

#!/usr/bin/python2.4
#
# Using python2.4 since required character encodings don't
# exist in python2.2 (see http://b/940905). Note that this
# file is not imported by another python script which uses python2.2
# but is directly invoked by //enterprise/legacy/logs/log_report.py
# (python_encodings_existence_unittest.py imports it, but it uses 2.4).
#
# NOTE: If you change the python version, please update it
# in python_encodings_existence_unittest.py as well.
#
import fileinput
import re
import socket
import string
import struct
import sys
import time

from google3.enterprise.legacy.logs import ClickEvent_pb
from google3.file.base import pywrapfile
from google3.file.base import recordio
from google3.logs.analysis.lib import libgwslog
from google3.pyglib import logging
from google3.net.proto import ProtocolBuffer

# Map from Google ie encoding name to Python's encoding name
ENCODING_MAP = {
  ''    : 'utf-8', # Default if not specified
  'gb'  : 'gb2312',
  'jis' : 'ISO-2022-JP',
}


def FormatIp(n):
  """Convert IP addr as a long int to dotted string."""
  return socket.inet_ntoa(struct.pack('!L', n))

def IncrFreq(freq_dict, key):
  """Increment a key in a frequency dictionary."""
  freq_dict[key] = freq_dict.get(key, 0) + 1


def clean_dictionary(dict, limit):
    if len(dict) > limit:
        # First delete anything with a count of 1; it's easier this way
        for k in dict.keys():
            if dict[k] == 1:
                del dict[k]
    if len(dict) > limit:
        # We have to try harder to deleting things
        values = dict.values()
        values.sort()
        threshold = values[-limit]
        for k in dict.keys():
            if dict[k] < threshold:
                del dict[k]


def get_string(args, param):
  '''Helper function to look up the specified param (e.g. 'q') in
  the entry args.
  Convert it to utf-8 if possible, using args.ie as the encoding.
  Strip spaces off the result.
  '''
  str = getattr(args, param, '')
  encoding = args.ie.lower()
  if ENCODING_MAP.has_key(encoding):
    encoding = ENCODING_MAP[encoding]
  try:
    # Convert from ie to unicode, then to utf-8
    str = unicode(str, encoding).encode('utf-8')
  except (UnicodeError, LookupError, ValueError), e:
    # Must have been a bad query string or bad ie value
    pass
  return string.strip(str)


class EnterpriseStats(libgwslog.LogAnalyzer):
  def __init__(self, date_str, top_count,
               with_results, diagnostic_terms):
    self.hits = 0
    self.results_pages = 0
    self.total_queries = 0
    self.distinct_queries = 0
    self.clicklog_entries = 0
    self.clicklog_url_freq = {}  # key=url, data=count
    self.clicklog_ip_freq = {}   # key=ip addr, data=count
    self.clicklog_ranks = {}
    self.clicklog_pages = {}
    for i in range(0, 10):
      self.clicklog_ranks[i] = 0
      self.clicklog_pages[i] = 0
    self.time_of_day = [0]*24  # Hour of day to count
    self.date = {} # Date to count
    self.keywords = {} # Keyword to count
    self.queries = {} # Query to count
    self.date_str = date_str
    self.top_count = top_count
    self.with_results = with_results
    self.diagnostic_terms = {}
    if diagnostic_terms != "":
      for term in diagnostic_terms.split(","):
        self.diagnostic_terms[term] = 1

  def hit(self, entry):
    # It's the responsibility of the derived class to figure out if this is from weblog
    assert entry.logtype == libgwslog.LOGTYPE_WEB

    self.hits = self.hits + 1
    if self.hits % 100000 == 0:
      # Flush dictionaries to save memory
      clean_dictionary(self.keywords, 1000)
      clean_dictionary(self.queries, 1000)

  def isDiagnosticTerms(self, q):
    return self.diagnostic_terms.has_key(q)

  def hit_pageview_query(self, entry):
    # this gets called once for each query plus things like /search
    # if it's not _really_ a query, we're not interested
    simple_query = 1
    q = get_string(entry.args, 'q')

    if not q:
      simple_query = 0
      q = get_string(entry.args, 'as_q')
    if not q:
      q = get_string(entry.args, 'as_epq')
    if not q:
      q = get_string(entry.args, 'as_oq')

    if not q or self.isDiagnosticTerms(q): return

    # check result counts against request
    if ((not self.with_results and entry.response_numresults != 0) or
        (self.with_results and entry.response_numresults == 0)):
        return

    # Note: This function is odd. It verifies that the query contains a
    #       valid query string (either simple or advanced search).
    #       However, it calls hit_pageview_query_normal only in advanced
    #       search.
    # (pn) I don't quite understand existing logic regarding to 'q' versus
    #      'as_*q', however, I did try to improve some inefficient code by
    #      introducing simple_query flag
    self.results_pages = self.results_pages + 1

    # redirect advanced search, 'Exact phrase', 'at least one' queries
    # through the normal query channel

    if q and not simple_query:
        self.hit_pageview_query_normal(entry)

  # this gets called once for each search query
  def hit_pageview_query_normal(self, entry):
    # if it's not _really_ a query, we're not interested

    # Try simple query (parameter 'q') first
    q = get_string(entry.args, 'q')
    # If this is not a simple query, try different advanced search fields
    # until we find a query string. Look for: `All of the words',
    # `Exact phrase' and `At least one of the words'.
    # Notes:
    # (1) We ignore the field `without the words' because it isn't
    #     really a query.
    # (2) We incorrectly report complex queries that specify multiple
    #     fields (as_q, as_epq, as_oq). We only use the first of these
    #     fields.

    if not q:
      q = get_string(entry.args, 'as_q')
    if not q:
      q = get_string(entry.args, 'as_epq')
    if not q:
      q = get_string(entry.args, 'as_oq')

    if not q or self.isDiagnosticTerms(q):
        return

    # check result counts against request
    if ((not self.with_results and entry.response_numresults != 0) or
        (self.with_results and entry.response_numresults == 0)):
      return

    # keep track of the total number of search queries
    self.total_queries = self.total_queries + 1

    # keep track of the how many searches were seen for this query
    self.queries[q] = self.queries.get(q, 0) + 1

    # keep track of the how many searches were seen for each keyword
    try:
      # Convert query from utf-8 to Unicode so we can split out words.
      #(?u) enables Unicode handling
      words = re.split(r'(?u)[^\w\d]+', unicode(q, 'utf-8'))
      # Convert each word to lower case, then convert back to utf-8
      # for display.
      words = [string.lower(un_word).encode('utf-8') for un_word in words]
    except UnicodeError:
      # If Unicode conversion dies, it must have been a bad query.
      # Treat it as ASCII
      words = re.split(r'[^\w\d]+', q)
      words = [string.lower(w) for w in words]
    for w in words:
      if w:
        self.keywords[w] = self.keywords.get(w, 0) + 1

    # keep track of the how many searches were seen, by time
    tm = time.localtime(entry.when)
    year = tm[0]
    month = tm[1]
    day = tm[2]
    hour = tm[3]
    self.time_of_day[hour] = self.time_of_day[hour]+1

    key = (year, month)

    if self.date.has_key(key):
      days_of_month = self.date[key]
    else:
      days_of_month = [0]*32
      self.date[key] = days_of_month
    days_of_month[day] = days_of_month[day]+1

    # keep track of distinct (first page) queries
    if entry.args.is_new_query():
      self.distinct_queries = self.distinct_queries + 1

  def process_click(self, clickEvent):
    self.clicklog_entries += 1

    url = clickEvent.url()
    ip = FormatIp(clickEvent.ip_address())
    IncrFreq(self.clicklog_url_freq, url)
    IncrFreq(self.clicklog_ip_freq, ip)
    self.clicklog_ranks[clickEvent.rank()] = self.clicklog_ranks.get(
        clickEvent.rank(), 0) + 1
    self.clicklog_pages[clickEvent.start()] = self.clicklog_pages.get(
        clickEvent.start(), 0) + 1

  def report(self):
    report_lines = []
    report_lines.append(repr(self.results_pages) + '\n')
    report_lines.append(repr(self.total_queries) + '\n')
    report_lines.append(repr(self.distinct_queries))

    if self.results_pages == 0:
      return report_lines

    # By Day
    months = self.date.keys()
    months.sort()

    # print a calendar for each month
    report_lines.append('\n{')
    for key in months:
      year, month = key
      report_lines.append(repr("%d_%d" % key))
      report_lines.append(" : ")
      report_lines.append(repr(self.date[key][1:]))
      report_lines.append(', ')
    report_lines.append('}\n')

    # average searches per hour
    report_lines.append(repr(self.time_of_day) + '\n')

    # Top N(default=100) Keywords
    pairs = self.keywords.items()
    pairs.sort(lambda x, y: cmp(x[1], y[1]))
    pairs.reverse()
    report_lines.append(repr(pairs[:self.top_count]) + '\n')

    # Top N(default=100) Queries
    pairs = self.queries.items()
    pairs.sort(lambda x, y: cmp(x[1], y[1]))
    pairs.reverse()
    report_lines.append(repr(pairs[:self.top_count]) + '\n')

    # Number of clicklog entries
    report_lines.append(repr(self.clicklog_entries) + '\n')

    # Top 10 click ranks
    tuples = self.clicklog_ranks.items()
    tuples.sort(lambda x, y: cmp(x[0], y[0]))
    report_lines.append(repr(tuples[:self.top_count]) + '\n')

    # Top 10 click pages
    tuples = self.clicklog_pages.items()
    tuples.sort(lambda x, y: cmp(x[0], y[0]))
    report_lines.append(repr(tuples[:self.top_count]) + '\n')

    # Top 10 URLs
    tuples = self.clicklog_url_freq.items()
    tuples.sort(lambda x, y: cmp(x[0], y[0]))
    report_lines.append(repr(tuples[:self.top_count]) + '\n')

    # Top 10 IPs
    tuples = self.clicklog_ip_freq.items()
    tuples.sort(lambda x, y: cmp(x[0], y[0]))
    report_lines.append(repr(tuples[:self.top_count]))

    return report_lines


def main(args):
  if len(args) < 3:
    usage = 'Usage: enterprise_stats.py <date_string> \
<output_file> <with_results> <top_count> <diagnosticTerms> \
<files> ...'
    print usage
    sys.exit(1)

  pywrapfile.File.Init()

  date_string = args[0]
  report_filename = args[1]
  with_results = ("1" == args[2])
  top_count = int(args[3])
  diagnostic_terms = args[4]
  log_files = args[5:]

  count = 0
  last_time = time.time()
  stats = EnterpriseStats(date_string, top_count,
                          with_results, diagnostic_terms)

  if len(log_files) > 0:
    for log_file in log_files:
      isClicklog = (log_file.find('clicklog') != -1)

      if isClicklog:
        rr = recordio.RecordReader(log_file)
        for buf in rr:
          clickEvent = ClickEvent_pb.ClickEvent(buf)
          stats.process_click(clickEvent)
        rr.Close()

      else:
        rawFp = open(log_file, 'r')
        line = rawFp.readline()
        while line:
          count = count + 1

          try:
            entry = libgwslog.parse_logline(line, 'weblog')
          except:
            entry = None

          if entry:
            stats.process(entry)

          line = rawFp.readline()

  try:
    report_file = open(report_filename, 'w')
  except IOError, e:
    sys.exit(e)

  report_lines = stats.report()

  report_file.writelines(report_lines)

  report_file.close()

if __name__ == '__main__':
  main(sys.argv[1:])

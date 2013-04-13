#!/usr/bin/python2.4
#
# (c) Copyright 2004 Google Inc.
# Anant Chaudhary <anantc@google.com>
#
'''
Script to get information about gsa params
used to help SNMP daemon answer queries
specific to GSA-MIB

Usage: snmp_helper.py --logdir=<dir> <queried variable>

The result of this script is to print a value to the command line:
The value of the variable queried is printed on success.
diskErrors, temperatureErrors, and machineErrors all print the nubmer
of values followed by the values.
0 is printed in case of failure.

'''
__author__ = 'Anant Chaudhary <anantc@google.com>'

import sys
import httplib
import string
import os
import socket
import stat
import time
import re

from google3.enterprise.legacy.util import E
from google3.enterprise.util import borgmon_util
from google3.pyglib import flags
from google3.pyglib import logging

FLAGS = flags.FLAGS

# TODO(erocke): figure out a way to not hard-code the default logs
# directory.
flags.DEFINE_string('logdir', '/export/hda3/logs', '')


def SecsSinceMidnight():
  '''Returns number of seconds since midnight.'''
  tups = time.localtime(time.time())
  return tups[3] * 3600 + tups[4] * 60 + tups[5]

def GetHttpResponse(data):
  '''generic method to get result from a POST operation'''
  try:
    host = 'localhost'
    port = 2100
    url = '/legacyCommand'
    postData = '%s\n' % data
    h = httplib.HTTPConnection(host, port)
    h.request('POST', url, postData)
    r = h.getresponse()
    return r.read()
  except socket.error:
    logging.error('Socket error: stopping snmpd')
    os.system('/etc/rc.d/init.d/snmpd stop')
    sys.exit(0)

def GetActiveVersion():
  """ Return the current version of the gsa.
      Returns None on failure.
  """
  # parse config.google.enterprise to determine the version
  cmd = 'find /export/hda3/ -name STATE -maxdepth 2 | xargs grep ACTIVE -l'
  try:
    f = os.popen(cmd,'r')
    data = f.read()
    f.close()
    pat = re.compile('/export/hda3/([0-9]+\.[0-9]+\.[0-9]+)/STATE')
    match = pat.search(data)
    if match:
      return match.group(1)
  except IOError, e:
    logging.warn('IOError in GetActiveVersion: %s' % e)
  except OSError, e:
    logging.warn('OSError in GetActiveVersion: %s' % e)
  return None

CACHEDIR='/var/cache/ent-snmp'

def ReadDataFromCache(cacheKey, expiry=15, cachedir=CACHEDIR):
  """ Gets the cached reply for cacheKey.
  This cache prevents SNMP request from being too slow.
  Input:
    cacheKey is a string and must not contain any characters that
      would be "bad" for a filename.
    expiry: Cached data will expire after expiry seconds.
    cachedir: directory in which to hold data.
  Result: cached string or None (no value or expired).
  """
  cachefile = '/%s/snmpcache-%s' % (cachedir, cacheKey)
  try:
    age = time.time() - os.stat(cachefile)[stat.ST_MTIME]
    if age > expiry:
      return None
    f = open('%s' % cachefile, 'r')
    data = f.read()
    f.close()
    if len(data) > 1: # sanity check for empty file
      return data
  except IOError, e:
    logging.warn('IOError in ReadDataFromCache: %s' % e)
  except OSError, e:
    logging.warn('OSError in ReadDataFromCache: %s' % e)
  return None

def WriteDataToCache(cacheKey, data, cachedir=CACHEDIR):
  """ Writes the data to the cache, under the key cacheKey
  Input:
    cacheKey is a string and must not contain any characters that
      would be "bad" for a filename.
    data: String to cache
    cachedir: directory in which to hold data.
  """
  cachefile = '/%s/snmpcache-%s' % (cachedir, cacheKey)
  if not os.path.exists(cachedir):
    os.makedirs(cachedir)
  f = open('%s.tmp' % cachefile, 'w')
  f.write(data)
  f.close()
  os.system('rm -f %s; mv -f %s.tmp %s' % (cachefile, cachefile, cachefile))

def GetBorgmonVarValueCached(var, expr):
  """Call Borgmon to get the value of expr.
  First checks the cache for 'var', Borgmon is not checked if its in cache.
  Otherwise get 'expr' from Borgmon, and update the cache.

  Arguments:
    var: string: cache key to use
    expr: string: borgmon expression

  Returns:
    string: Borgmon reply, stripped of newlines etc, or None if there is any
            error
  """
  # check the cache first
  result = ReadDataFromCache(var)
  if result:
    return result
  version = GetActiveVersion()
  if version is None:
    return None
  # Assume we are in active mode (borgmon port 4911)
  # There could be a problem here for SNMP in test mode
  bu = borgmon_util.BorgmonUtil(version, mode=borgmon_util.ACTIVE)
  reply = bu.GetAndEvalBorgmonExpr(expr)
  if reply is None:
    return None
  reply = str(reply)
  WriteDataToCache(var, reply)
  return reply

def GetSystemStatusData(systemstatusDict, systemstatusVar):
  """ use "borgmon getsystemstatus" command to get the value of
  of a variable of a system status dictionary.

  Arguments:
    systemstatusDict: 'SystemStatusValues'
    systemstatusVar: 'Disks'
  Returns:
    0
  """

  getsystemstatusCmd = 'getsystemstatus'
  response = ReadDataFromCache(getsystemstatusCmd)
  if not response:
    response = GetHttpResponse('borgmon %s' % getsystemstatusCmd)
    WriteDataToCache(getsystemstatusCmd, response)
  # remove last two line (ACKGoogle)
  lines = string.split(response, '\n')
  if len(lines) < 2:
    return 0
  if 'NACKgoogle' == string.strip(lines[-2]):
    # some error must have occured..
    return 0
  response = string.join(lines[:-2], '\n')
  dict = {}
  exec(response, dict)
  if dict.has_key('__builtins__'): del dict['__builtins__']
  try:
    rval = dict[systemstatusDict][systemstatusVar]
  except Exception, e:
    logging.error('Error in GetSystemStatusData: %s' % e)
    rval = 0
  return rval

def GetCrawlPauseStatus():
  ''' gets the value of a gsa global param
      URLSERVER_PAUSED
  '''
  response = GetHttpResponse('params get URLSERVER_PAUSED')
  # remove last two line (ACKGoogle)
  lines = string.split(response, '\n')
  if len(lines) < 2:
    return 0
  if 'NACKgoogle' == string.strip(lines[-2]):
    # some error must have occured..
    return 0
  response = string.join(lines[:-2], '\n')
  try:
    dummy = {}
    exec(response, dummy)
    value = 1 - dummy['URLSERVER_PAUSED']
  except Exception, e:
    logging.error('Error in GetCrawlPauseStatus: %s' % e)
    return 0
  # if scheduled crawl is on URLSERVER_PAUSED will never be paused
  # but the crawl may not be crawling
  # check if scheduled crawl is on; if it is check if scheduled crawl is paused
  scheduledCrawlResponse = GetHttpResponse('params get '
                                           'ENTERPRISE_SCHEDULED_CRAWL_MODE')
  # remove last two line (ACKGoogle)
  lines = string.split(scheduledCrawlResponse, '\n')
  scheduledCrawlOn = 0
  # if no errors
  if ((len(lines) >= 2) and ('NACKgoogle' != string.strip(lines[-2]))):
    scheduledCrawlResponse = string.join(lines[:-2], '\n')
    try:
      dummy = {}
      exec(scheduledCrawlResponse, dummy)
      scheduledCrawlOn = dummy['ENTERPRISE_SCHEDULED_CRAWL_MODE']
    except Exception, e:
      logging.error('Error in GetCrawlPauseStatus: %s' % e)
      return 0
  if (value and scheduledCrawlOn):
    value = GetBorgmonVarValueCached('scheduledCrawlRunning',
                                     'scheduled_crawl_is_running')
  return value

def main():
  try:
    argv = FLAGS(sys.argv)  # parse flags
  except flags.FlagsError, e:
    sys.exit('%s\n%s' % (e, __doc__))
  if (len(argv) < 2):
    sys.exit(__doc__)
  query_var = argv[1]

  if FLAGS.logdir:
    if E.access([E.LOCALHOST], FLAGS.logdir, 'rwd'):
      # One log file per day, so as not to clutter the log directory
      # if this process is run often.
      # We can use localtime since this does not surface to the user.
      logfile = '%s/snmphelper_%s' % (
          FLAGS.logdir,
          time.strftime('%Y%m%d', time.localtime(time.time())))
      logging.info('Writing log to %s' % logfile)
      logging.set_logfile(open(logfile, 'a'))
    else:
      logging.warn('Invalid log directory %s' % FLAGS.logdir)
  try:
    if query_var == 'crawlRunning':
      # special case, not a system status or borgmon variable
      print GetCrawlPauseStatus()
    else:
      # all getsystemstatus supported variables are in this dictionary
      systemStatusVars = {
        'diskHealth': ('SystemStatusValues', 'Disks'),
        'temperatureHealth': ('SystemStatusValues', 'Temperatures'),
        'machineHealth': ('SystemStatusValues', 'Machines'),
        'diskErrors': ('SystemStatusDescriptions', 'Disks'),
        'temperatureErrors': ('SystemStatusDescriptions', 'Temperatures'),
        'machineErrors' : ('SystemStatusDescriptions', 'Machines'),
        }
      borgmonVars = {
        'todayDocsCrawled' : (
            'num_urls_crawled[%ds] - min(num_urls_crawled[%ds])' %
            (eval('SecsSinceMidnight()'), eval('SecsSinceMidnight()'))),
        'docsCrawled' : 'num_urls_crawled',
        'docErrors' : (
          'num_urls_error[%ds] - min(num_urls_error[%ds])' %
          (eval('SecsSinceMidnight()'), eval('SecsSinceMidnight()'))),
        'docsServed' : 'num_urls_in_index_total',
        'qpm' : 'gws_searches_per_minute',
        'docBytes' : 'doc_bytes_received',
        'crawlingRate' : 'interval_pages_per_sec_total',
        'docsFound' : 'num_urls_available_total',
        'scheduledCrawlRunning' : 'scheduled_crawl_is_running',
        'scheduledCrawlStartTime' : 'scheduled_crawl_start_time',
        'scheduledCrawlEndTime' : 'scheduled_crawl_end_time',
        }

      if query_var in borgmonVars:
        result = GetBorgmonVarValueCached(query_var, borgmonVars[query_var])
      elif query_var in systemStatusVars:
        (systemstatusDict, systemstatusVar) = systemStatusVars[query_var]
        result = '%s' % GetSystemStatusData(systemstatusDict, systemstatusVar)
      else:
        logging.error('Error in main: incorrect variable queried')
        print 0
        return

      if result is None:
        result = 0   # correct borgmon error for no value

      if query_var == 'todayDocsCrawled':
        if result == 'NaN':
          result = 0
      elif (query_var == 'diskErrors' or
            query_var == 'temperatureErrors' or
            query_var == 'machineErrors'):
        print len(result),
      elif query_var == 'docBytes':     # need to convert to MBytes
        result = long(result)/1048576  # http://en.wikipedia.org/wiki/Megabyte
      elif query_var == 'docErrors':
        result = long(round(float(result)))
        if result < 0:
          result = 0 # correct borgmon error for no value
      print result
  except Exception, e:
    logging.error('Error in main: %s' % e)
    print 0

if __name__ == '__main__':
  main()

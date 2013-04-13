#!/usr/bin/python2.4
#
# Copyright 2000-2006 Google Inc. All Rights Reserved.
# davidw@google.com
#
# This contains functions which are useful for enterprise log collection.
#
###############################################################################

import string
import os
import stat
import glob
import commands
import re
import urllib

from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.pyglib import gfile
from google3.pyglib import logging
from google3.webutil.url import pywrapurl

###############################################################################

## These constants should match with those in LogReportFormData.java
# report types

RAW_REPORT     = '0'
SUMMARY_REPORT = '1'

SUCCESS = 0
FAILURE = 1
STILL_VALID = 2

REPORT_FILE_REGEX = re.compile('^.*/log_report/(.*)/(.*)$')
# This must match these two filename formats:
#
#  partnerlog.from_ent1.port8888.starts20080506
#  clicklog.0.ent1.80.20080506-12d5825.00470-22851
#
# We match a period optionally followed by the word `start'
# and six digits.  (The six digits is to avoid matching the
# '.80.' in the second example.)
FILE_DATE_REGEX = re.compile('\.(starts)?(\d\d\d\d\d\d\d\d)')

# Use old style Boolean constant for backward compatibility since some scripts
# are not running python2.2
true  = 1
false = 0

def get_gws_log_dir(config):
  return config.var('TMPDIR')

def get_collect_dir(config):
  return '%s/log_collect' % config.var('LOGDIR')

def get_partition_dir(config):
  return '%s/log_partition' % config.var('LOGDIR')

def get_apache_dir(config):
  return '%s/log_apache' % config.var('LOGDIR')

def get_click_dir(config):
  return '%s/log_click' % config.var('LOGDIR')

def get_directory_map_file(config):
  """Name of file containing map from collections to their directories."""
  return '%s/.directory_map' % get_partition_dir(config)

def get_report_dir(config):
  """Directory of all raw and summary reports."""
  return config.var('LOG_REPORT_DIR')

def get_crawlqueue_dir(config):
  """Directory of crawl queue snapshot data files."""
  return config.var('CRAWLQUEUE')

def get_syslog_checkpoint_dir(config):
  """Directory name of syslog checkpoint files."""
  return config.var('SYSLOG_CHECKPOINTS_DIR')

def get_local_raw_report_filename(config, reportName, collection):
  return '%s/log_report/%s/logdump_%s.txt' % (config.var('LOGDIR'),
                                              collection, reportName)

def get_report_collection_dir(config, collection):
  """Return the directory name of reports for a given collection."""
  return '%s/%s' % (get_report_dir(config), collection)

def get_report_list_filename(config, reportType, collection):
  """Filename of file that contains a list of report forms."""
  dirname = get_report_dir(config)
  if reportType == SUMMARY_REPORT:
    return '%s/logreport_%s_list' % (dirname, collection)
  elif reportType == RAW_REPORT:
    return '%s/logdump_%s_list' % (dirname, collection)
  else:
    return ''


def get_report_filenames(config, reportType, reportName, collection):
  """Return a pair of filenames of report file and its valid file."""
  dirname = get_report_collection_dir(config, collection)
  encReportName = urllib.quote(reportName)

  if reportType == SUMMARY_REPORT:
    return ('%s/logreport_%s.html' % (dirname, encReportName),
            '%s/logreport_%s-valid' % (dirname, encReportName))
  elif reportType == RAW_REPORT:
    return ('%s/logdump_%s.txt' % (dirname, encReportName),
            '%s/logdump_%s-valid' % (dirname, encReportName))
  else:
    return ('', '')

def IsValidSiteParam(valid_params, param):
  """valid_params should be a list of collections on the appliance
  and we return True if param is either a valid collection or is
  made up of valid collections.
  """
  if param is None or param is '':
    return False
  # '.' and '|' are two valid special characters allowed in the site parameter.
  param = param.replace('.','|')
  colls = param.split('|')
  for i in colls:
    if i not in valid_params:
      logging.info('%s is not a collection defined on the box.', i)
      return False
  return True

def DoCommand(cmd):
  (status, output) = commands.getstatusoutput(cmd)
  return (status, output)

def MakeGoogleDir(entconfig, dir):
  """Create a directory in Google filesystem."""
  try:
    if dir[-1] == '/':  # gfs doesn't tolerate this trailing slash
      dir = dir[:-1]
    mode = gfile.File_Stat(dir)[0]
    valid_dir = stat.S_ISDIR(mode)
  except:
    valid_dir = 0

  if not valid_dir:
    (err, out) = E.run_fileutil_command(entconfig, 'mkdir -p %s' % dir)
    if err:
      logging.error('Failed on mkdir for %s. Error: %s' % (dir, out))

def MakeDir(dir):
  """Create a directory on local host."""
  # if the target directory doesn't exist, make it
  try:
    mode = os.stat(dir)[0]
    valid_dir = stat.S_ISDIR(mode)
  except:
    valid_dir = 0

  if not valid_dir:
    os.makedirs(dir)

def _GetFileSize(file):
  try:
    s = os.stat(file)
    mode = s[stat.ST_MODE]

    if stat.S_ISREG(mode):
      return s[stat.ST_SIZE]
  except:
    pass

  return -1

class Log:
  def __init__(self, file, size):
    self.file = file
    self.size = size

def FindClientLogFiles(log_dir, directory_map_file,
                       client, first_date, last_date):
  """Find all logs files under subdirectories of @log_dir, which has search
  records belong to any collection in @client within the given date range."""

  coll_directory_map = CollectionDirectoryMap(directory_map_file)

  logs = []
  for subdir in coll_directory_map.getCollectionDirectories(client):
    subdir = os.path.join(log_dir, subdir)
    logs += FindLogFiles(subdir, first_date, last_date, absolute=1)
  return logs


def FindLogFiles(log_dir, first_date, last_date, absolute=0):
  # try not to look at too many more files than we need to
  year_mask = month_mask = day_mask = ''
  if first_date.year == last_date.year:
    year_mask = '%04d' % first_date.year

    if first_date.month == last_date.month:
      month_mask = '%02d' % first_date.month

      if first_date.day == last_date.day:
        day_mask = '%02d' % first_date.day
  date_mask = year_mask + month_mask + day_mask

  filepat1 = '%s/*/partnerlog.*.starts%s*' % (log_dir, date_mask)
  filepat2 = '%s/*/clicklog.*.%s*' % (log_dir, date_mask)

  candidate_files = glob.glob(filepat1)
  candidate_files += glob.glob(filepat2)

  good_files = []

  first_date_int = first_date.as_int()
  last_date_int = last_date.as_int()

  for file in candidate_files:
    match = FILE_DATE_REGEX.search(file)
    if not match:
      logging.error('%s does not match regex' % file)
      continue

    file_date_int = int(match.groups()[1])
    if file_date_int < first_date_int or file_date_int > last_date_int:
      continue

    filesize = _GetFileSize(file)
    if filesize <= 0:
      continue

    # remove path from filename
    if absolute == 0:
      logname = file[len(log_dir)+1:]
    else:
      logname = file
    good_files.append( Log(logname, filesize) )

  return good_files


def makeValid(valid_file, logs):
  """Make a validate file out of a list of Log objects."""
  try:
    out = gfile.GFile(valid_file, 'w')
    for log in logs:
      out.write('%s %d\n' % (log.file, log.size))
    out.close()
  except:
    logging.error('Error writing validation file %s' % valid_file )
    return 0

  return 1


def readValidFile(valid_file):
  """Read the file's valid file to get a list of file checkpoints."""
  checkpoints = {}

  try:
    lines = gfile.GFile(valid_file, 'r').readlines()
  except:
    logging.error('Can\'t open %s' % valid_file )
    return None

  for line in lines:
    try:
      file, size_s = string.split(line)
      size = int(size_s)
    except:
      logging.error('Invalid line in validation file %s: %s' % (
        valid_file, line) )
      continue

    checkpoints[file] = size
  return checkpoints


def checkValid(_, valid_file, new_logs):
  """Check to see if there is change(s) in new_logs compared to
  valid_file contents."""
  if not gfile.Exists(valid_file):
    return 0

  old_logs = readValidFile(valid_file)
  if old_logs == None:
    return 0

  # compare the old and current logs to see if the file is still valid
  is_valid = 1

  for new_log in new_logs:
    if new_log.file not in old_logs.keys():
      logging.info('New log file: %s' % new_log.file )
      is_valid = 0
    elif old_logs[new_log.file] < new_log.size:
      logging.info('Log %s grew from %d to %d' % (new_log.file,
                                                  old_logs[new_log.file],
                                                  new_log.size) )
      is_valid = 0

  return is_valid


def GetDirName(filename):
  i = string.rfind(filename, '/')
  if i < 0:
    return None

  s = filename[0:i]

  if len(s) == 0:
    return None

  return s


class Date:
  def __init__(self, month, day, year):
    assert year >= 1000 and year <= 9999
    assert month >= 1 and month <= 12
    assert day >= 1 and day <= 31

    self.month, self.day, self.year = month, day, year

  def as_int(self):
    return self.year * 10000 + self.month * 100 + self.day;


def ParseDateRange(tag, args_s):
  try:
    args_i = tuple(map(int, args_s))

    if tag == 'all' and len(args_i) == 0:
      first_date = Date(1, 1, 1000)
      last_date = Date(12, 31, 9999)
      printable_date = ''
    elif tag == 'date' and len(args_i) == 3:
      month, day, year = args_i
      first_date = last_date = Date(month, day, year)
      printable_date = '%d/%d/%d' % (month, day, year)
    elif tag == 'month' and len(args_i) == 2:
      month, year = args_i
      first_date = Date(month, 1, year)
      last_date = Date(month, 31, year)
      months = (None, 'January', 'February', 'March', 'April', 'May',
                'June', 'July', 'August', 'September', 'October',
                'November', 'December')
      month_str = months[month]
      printable_date = "%s %d" % (month_str, year)
    elif tag == 'year' and len(args_i) == 1:
      year = args_i[0]
      first_date = Date(1, 1, year)
      last_date = Date(12, 31, year)
      printable_date = "Year %d" % (year)
    elif tag == 'range' and len(args_i) == 6:
      month1, day1, year1, month2, day2, year2 = args_i
      first_date = Date(month1, day1, year1)
      last_date = Date(month2, day2, year2)
      printable_date = '%d/%d/%d to %d/%d/%d' % (month1, day1, year1,
                                                 month2, day2, year2)
    else:
      return None  # invalid tag

    file_date = '%s_%s' % ( tag, string.join(args_s, '_') )

  except:
    return None

  return (first_date, last_date, printable_date, file_date)


class CollectionDirectoryMap:
  """This class keeps a mapping from collection name to list of directories
  that contain related search entries."""
  def __init__(self, filename):
    self.filename = filename
    self.dirnames = {}
    self.collection_dir_map = {}
    self.changed = false

    fp = open(self.filename, 'r')
    for line in fp.readlines():
      fields = line.strip().split(' ')
      collection = fields.pop(0)
      self.collection_dir_map[collection] = fields
      for dirname in fields:
        self.dirnames[dirname] = 1
    fp.close()

  def hasFileInSubdirs(self, dirname):
    """Return true if there exists file(s) in any first-level sub-directories
    of a given directory. This method will raise OSError if dirname is not a
    directory."""

    # Note: This is used for checking if there exists any files under a given
    # partioned directory of log_partition or log_apache.
    # Sample input of dirname='/export/hda3/logs/log_partition/AABBCCDDEEFF1100/'
    # is used to check for existence of files with matching pattern:
    # '/export/hda3/logs/log_partition/AABBCCDDEEFF1100/ent[12345]/partnerlog.from*'
    for subdir in os.listdir(dirname):
      if len(os.listdir(os.path.join(dirname, subdir))) != 0:
        return true
    return false

  def sanitizeMap(self, partition_dir, apache_dir, click_dir):
    """Sanitize the map and remove unused directories due to abandoned
    collections. Note that this is a little bit expensive, so it should
    not be called liberally. collect_logs cron job is the only caller
    right now.
    Return true if this has made some changes in the map."""

    removed_dirs = {}
    for dirname in self.dirnames:
      partitioned_subdir = os.path.join(partition_dir, dirname)
      apache_subdir = os.path.join(apache_dir, dirname)
      click_subdir = os.path.join(click_dir, dirname)

      if os.path.exists(partitioned_subdir) and \
         not self.hasFileInSubdirs(partitioned_subdir):
        E.rmall([E.LOCALHOST], partitioned_subdir)

      if os.path.exists(apache_subdir) and \
         not self.hasFileInSubdirs(apache_subdir):
        E.rmall([E.LOCALHOST], apache_subdir)

      if os.path.exists(click_subdir) and \
         not self.hasFileInSubdirs(click_subdir):
        E.rmall([E.LOCALHOST], click_subdir)

      if not os.path.exists(apache_subdir) and \
         not os.path.exists(click_subdir) and \
         not os.path.exists(partitioned_subdir):
        removed_dirs[dirname] = 1
        logging.info("Remove directory: %s" % dirname)

    for coll in self.collection_dir_map.keys():
      dirlist = self.collection_dir_map[coll]
      for i in range(len(dirlist) - 1, -1, -1):
        if removed_dirs.has_key(dirlist[i]):
          del dirlist[i]
      if len(dirlist) == 0:
        del self.collection_dir_map[coll]
        logging.info("Remove collection: %s" % coll)

    if removed_dirs:
      self.changed = true
    return self.changed

  def getCollectionDirectories(self, collection):
    """Return list of directories that has search entries related to
    the collection."""

    if collection == C.SEARCH_ALL_COLLECTIONS:
      return self.dirnames.keys()
    elif self.collection_dir_map.has_key(collection):
      return self.collection_dir_map[collection]
    else:
      return []

  def makeDirectoryName(self, site):
    """Generate fingerprint (directory name) for a collection."""

    # Use the version that takes a string and not char*. Fixes http://b/1001790
    return '%x' % pywrapurl.URL(site, '').Fingerprint()

  def hasSite(self, site):
    """Return true if the site is already in collection directory map."""
    return self.dirnames.has_key(self.makeDirectoryName(site))

  def addSiteParam(self, site):
    """Add a site parameter from user query."""
    if self.hasSite(site):
      return false
    dirname = self.makeDirectoryName(site)
    self.dirnames[dirname] = 1
    site = site.replace('.', '|').replace('(', '|').replace(')', '|')
    colls = site.split('|')
    for coll in colls:
      if not self.collection_dir_map.has_key(coll):
        self.collection_dir_map[coll] = []
      self.collection_dir_map[coll].append(dirname)
    self.changed = true
    return true

  def hasChanged(self):
    """The collection directory map has changed in this run."""
    return self.changed

  def saveToDisk(self):
    """ Save it back to disk. This is needed if it has changed."""
    if not self.hasChanged():
      return

    lockfile = '%s.lock' % self.filename
    lock = E.acquire_lock(lockfile, 5, breakLockAfterGracePeriod = true)

    try:
      file = open(self.filename, 'w')
      colls = self.collection_dir_map.keys()
      colls.sort()
      for collection in colls:
        directories = " ".join(self.collection_dir_map[collection])
        file.write('%s %s\n' % (collection, directories))
      file.close()
      # reset the flag to be safe. Normally, this is called at
      # the end of a script execution.
      self.changed = false
    finally:
      lock.close()
      os.unlink(lockfile)

#!/usr/bin/python2.4
#
# (c) 2000 Google inc.
# cpopescu@google.com
#
# This script sorts a number of apache logs in descending date order.
# The files have to be already sorted
#
###############################################################################
"""
Usage:
    sort_apache_log.py [<file>* |--from_file loglist]
"""

import string
import sys
import os
import warnings
import shutil

###############################################################################

MAX_OPEN_FILES = 100

# To get rid of the annoying tempnam() warning.  Since this program always
# remove the working_dir, tempnam() is not a security issue. Once
# Python 2.3 is available everywhere, we can replace tempnam() by mkstemp().
warnings.filterwarnings('ignore', 'tempnam', RuntimeWarning)


###############################################################################

months = {
  "Jan" : "00",  "Feb" : "01",  "Mar" : "02",
  "Apr" : "03",  "May" : "04",  "Jun" : "05",
  "Jul" : "06",  "Aug" : "07",  "Sep" : "08",
  "Oct" : "09",  "Nov" : "10",  "Dec" : "11",
  }

###############################################################################

def ComputeRegularString(str):
  """ Returns a nicely computed date string from a log line """
  if not str:
    return None
  try:
    all_date = string.split(str[1:], " ")[3]
    d1 = string.split(all_date, "/")
    d2 = string.split(d1[2], ":")

    return d2[0] + months[d1[1]] + d1[0] + d2[1] + d2[2] + d2[3]
  except:
    return None

###############################################################################

def ExtractMinLine(to_compare):
  """Given a list of dates (nicely adjusted) we get the index with the min"""
  min_str = "Z"
  min_ndx = None
  for i in range(0, len(to_compare)):
    if ( to_compare[i] != None and to_compare[i] < min_str):
      min_ndx = i
      min_str = to_compare[i]
  return min_ndx

###############################################################################

def _MergeSmallNumberSortedFiles(infiles, outfile):
  """ Merge sorted infiles into a outfile

  All the infiles are sorted.  Assuming all the infiles can be opened at
  the same time. This function merges them into the outfile.

  Arguments:
    infiles: ['file1', 'file2']
    outfile: tmp_outfile
  """

  files = []
  crt = []
  lines = []
  for i in range(0, len(infiles)):
    files.append(open(infiles[i], "r"))
    lines.append(files[i].readline())
    crt.append(ComputeRegularString(lines[i]))

  # at each moment we output the min of crt until we are done
  done = 0
  outf = open(outfile, 'a+')
  while ( not done ):
    crt_ndx = ExtractMinLine(crt)
    if ( None != crt_ndx ):
      outf.write(lines[crt_ndx])
      lines[crt_ndx] = files[crt_ndx].readline()
      crt[crt_ndx] = ComputeRegularString(lines[crt_ndx])
    else:
      done = 1

  for file in files:
    file.close()
  outf.close()

###############################################################################

def MergeSortedFiles(infiles, tmpdir, batchsize=MAX_OPEN_FILES):
  """ merge sorted infiles into a outfile

  merge sorted infiles into a outfile using tmpdir
  for intermediate tmp files. Returns the result file name
  and the caller of the function is responsible to delete
  the file.

  Arguments:
    infiles: ['file1', 'file2']
    tmpdir: '/export/hda3/tmp/sort_OZfDTj'
  Return:
    '/export/hda3/tmp/sort_OZfDTj/filegP2zjg'
  """

  while len(infiles) > 1:
    outfiles = []
    for i in range((len(infiles) + batchsize - 1) /  batchsize):
      outfile = os.tempnam(tmpdir)
      _MergeSmallNumberSortedFiles(infiles[(i * batchsize):
                                           ((i+1) * batchsize)],
                                   outfile)
      outfiles.append(outfile)
    infiles = outfiles
  return infiles[0]

###############################################################################

def main(argv):

  if len(argv) == 0:
    sys.exit(0);

  # get a list of sorted logs either from a file for command line args
  sorted_logs = []
  if ( argv[0] == '--from_file'):
    if (len(argv) == 2):
      logfilelist = open(argv[1], 'r')
      for line in logfilelist.readlines():
        logname = string.strip(line)
        if os.path.exists(logname):
          sorted_logs.append(logname)
      logfilelist.close()
  else:
    for i in range(len(argv)):
      if os.path.exists(argv[i]):
        sorted_logs.append(argv[i])

  if len(sorted_logs) == 0:
    sys.exit(0)

  working_dir = os.tempnam('/export/hda3/tmp', 'sort_apache')
  os.mkdir(working_dir)
  try:
    result_file = MergeSortedFiles(sorted_logs, working_dir)
    os.system('tac %s' % result_file)
  finally:
    shutil.rmtree(working_dir)

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

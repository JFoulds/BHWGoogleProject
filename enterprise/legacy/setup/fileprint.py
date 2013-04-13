#!/usr/bin/python2.4
#
# Calculates a "fileprint" over a file -- this is a very fast-to-compute
# fingerprint.  It assumes that there's no corruption, that the only
# error is that the file is too short or somehow wrong.  Therefore
# it consists of 3 entities:
#    <basename>: <size> <short_chksum>
#
# The short_chksum is computed only on the first, middle and last 16
# bytes and is an md5sum hash of this data (we reduce it to 64bits to
# make it easier to use)
#
# Takes exactly one argument, the file to fileprint.
#
# 10/2000 Bogdan C.

import os
import sys
import time
import stat
import string
import md5            # for md5sums

FILEPRINT_CHUNK_SIZE = 16

# SHORT_FILEPRINT
#   given some string, it computes a 64bit hash value. The hash is
#   actually a strong md5sum which we trim to 64 bits.
def ShortFileprint(fprint):
  # use md5 algorithm (128bits)
  md5sum = md5.new(fprint)
  md5cksum = md5sum.digest()

  cksum = map(ord, md5cksum[:len(md5cksum)/2])
  for pos in xrange(0, len(cksum)):
    cksum[pos] = cksum[pos] ^ ord(md5cksum[len(md5cksum)/2+pos])

  return string.join(map(lambda c: '%02x' % c, cksum), '')

# FILEPRINT
#  given a filename, compute it's fileprint by using mtime, size and a
#  hash of the first and last few bytes
def Fileprint(fname, options):
  try:
    filestat = os.stat(fname)
    fsize = filestat[stat.ST_SIZE]
    chunksize = FILEPRINT_CHUNK_SIZE % fsize  # limit chunk size for tiny files
    try:
      fp = open(fname, 'rb')
      head = fp.read(chunksize)          # read head chunk
      midpos = (fsize - chunksize)/2
      fp.seek(midpos, 0)                 # seek to middle chunk ...
      middle = fp.read(chunksize)        # ... and read it
      fp.seek(-chunksize, 2)             # seek to tail chunk ...
      tail = fp.read(chunksize)          # ... and read it
    except IOError, e:
      print "Error: unable to read file: %s (%s)" % (fname, e)
      sys.exit(2)

    fsize = str(fsize)
    if options['usemodtime']:
      fmodtime = str(filestat[stat.ST_MTIME])
    else:
      fmodtime = ''
    fprint = ShortFileprint(head + middle + tail + fsize + fmodtime)
    if options['showmodtime']:
      print "%s: %s %s %s" % \
            (os.path.basename(fname), fsize, filestat[stat.ST_MTIME], fprint)

    else:
      print "%s: %s %s" % \
            (os.path.basename(fname), fsize, fprint)

  except OSError, e:
    sys.stdout = sys.stderr
    print "Error: %s" % e[1]
    sys.exit(1)
  except ZeroDivisionError:
    # file does not exist. Return a dummy fileprint
    print "%s: 0 0" % os.path.basename(fname)

if __name__ == '__main__':
  if len(sys.argv) > 1:
    import getopt
    (optlist, args) = getopt.getopt(sys.argv[1:], '', ['usemodtime',
                                                       'showmodtime'])

    options = {}
    options['usemodtime'] = 0
    options['showmodtime'] = 0
    for flag, value in optlist:
      if flag == '--usemodtime':
        options['usemodtime'] = 1
      elif flag == '--showmodtime':
        options['showmodtime'] = 1

    for f in args:
      Fileprint(f, options)

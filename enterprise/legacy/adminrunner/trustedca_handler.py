#!/usr/bin/python2.4
#
# (c) Copyright 2004 Google Inc.
# Phuong Nguyen <pn@google.com>
#
# Deal with trusted certificate authority's certificates and CRL.
#
# The commands we respond to are
#
# 1. getcommonnames
#               Return a concatenation of trusted CA's (subject hash, common names) with
#               newline delimiters
#
# 2. importcas:
#               Add one or more trusted CA into the list.
#               Return '0' if succeed, error code otherwise
#
# 3. removeca:
#               Remove a CA from the trusted list of CAs
#               @commonName: String - the common name of the CA to be removed
# 4. hascrl:
#               Return '0' if it has crl, '1' otherwise.
#               @commonname: String - the common name of a CA whose CRL we are interested
#
# 5. importcrl: Return '0' if succeed.
#               @commonname: String - the common name of the CA that authorize the CRL
#               @crl: String - an X509 CRL
#
# 6. removecrl: Return '0' if succeed
#               @commonname: String - the common name of the CA of which we want to remove CRL
#
#########################################################


import threading
import os
import string
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.pyglib import logging
from google3.enterprise.legacy.util import ssl_cert

class TrustedCAHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.sslWrapperPath = (
        '%s/local/google3/enterprise/legacy/util/ssl_cert.py' %
        self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    self.updatelock = threading.Lock()

  def get_accepted_commands(self):
    return {
      'getcommonnames' : admin_handler.CommandInfo(0, 0, 0, self.getcommonnames),
      'importcas'      : admin_handler.CommandInfo(0, 0, 1, self.importcas),
      'removeca'       : admin_handler.CommandInfo(1, 0, 0, self.removeca),
      'hascrl'         : admin_handler.CommandInfo(0, 0, 1, self.hascrl),
      'importcrl'      : admin_handler.CommandInfo(0, 0, 1, self.importcrl),
      }

  def mygetstatusoutput(self, cmd):
    status, output = E.getstatusoutput(cmd)
    if os.WIFEXITED(status):
      return (os.WEXITSTATUS(status), output)
    else:
      return (status, output)

  def getcommonnames(self):
    ''' This return the concatenation of trusted CA\'s common names'''
    retcode, result = E.getstatusoutput(
      '%s getcommonnames %s' %
      (self.sslWrapperPath, self.cfg.getGlobalParam('TRUSTED_CA_DIRNAME')))
    retcode = retcode / 256

    if retcode == 0:
      return '0\n%s' % result
    else:
      logging.info('Error in getcommonnames %s' % result)
      return '1'

  # return '0', on sucess. Otherwise, return error code from ssl_cert.py or
  # E.distribute()
  def importcas(self, cadata):
    ''' This will import the list of trusted CAs in @cadata'''

    trusted_ca_dir = self.cfg.getGlobalParam('TRUSTED_CA_DIRNAME')

    if not os.path.exists(trusted_ca_dir):
      os.mkdir(trusted_ca_dir)

    ## write cadata to a temp file
    tempfilename = os.path.join(trusted_ca_dir, 'temp')
    self.updatelock.acquire()
    try:
      try:
        open(tempfilename, 'w').write(cadata)
      except IOError:
        logging.error('Could not write CA data to [%s]' % tempfilename)
        return '-4'

      retcode, result = E.getstatusoutput(
        '%s importcas %s %s' %
        (self.sslWrapperPath, tempfilename, trusted_ca_dir))

      retcode = retcode / 256
      if retcode != 0:
        return result

      # distribute CA files to all nodes in the network.
      retcode = self._distributeFiles(trusted_ca_dir)
      if retcode != 0:
        logging.error('Error distributing CA file: %d' % retcode)
        return str(retcode)

    finally:
       ## check for existence?
      E.rm(['localhost'], tempfilename)
      self.updatelock.release()

    return '0'

  def _distributeFiles(self, dir):
    """Distributes the files in directory named dir.  Returns 0 on success,
    the return code from E.distribute() otherwise."""

    files = os.listdir(dir)
    try:
      files.remove('temp')
    except ValueError:
      logging.warn("expected to find file 'temp'")

    files = map(lambda x: os.path.join(dir, x), files)
    files_str = ' '.join(files)
    return E.distribute(self.cfg.getGlobalParam('MACHINES'), files_str, 60)

  # Return '0' on success; '1' otherwise
  def removeca(self, hash):
    '''Remove a trusted CA, given its subject hash'''
    self.updatelock.acquire()

    retval = 0
    try:
      name = os.path.join(self.cfg.getGlobalParam('TRUSTED_CA_DIRNAME'),
             hash + ssl_cert.CA_CERT_EXT)
      retval = E.rm(self.cfg.getGlobalParam('MACHINES'), name)

      if not retval:
        logging.error('error trying to remove %s: %d' % (name, retval))

      name = os.path.join(self.cfg.getGlobalParam('CRL_DIRNAME'),
             hash + ssl_cert.CRL_EXT)
      retval = E.rm(self.cfg.getGlobalParam('MACHINES'), name)

      if not retval:
        logging.info('error trying to remove %s: %d' % (name, retval))

    finally:
      self.updatelock.release()

    return '%d' % retval


  # do in batch
  def hascrl(self, hashData):
    ''' Check if has CRL with given issuer hash '''

    answer = []
    for hash in hashData.split('\n'):
      if hash == '':
        break
      retcode, result = E.getstatusoutput(
        '%s hascrl %s %s' %
        (self.sslWrapperPath, hash,
         self.cfg.getGlobalParam('CRL_DIRNAME')))

      retcode = retcode / 256
      if retcode != -1:
        answer.append('%d' % retcode)
      else:
        logging.error(result)
        return '1'

    return '0\n%s' % '\n'.join(answer)

  # Return '0' on success; error code otherwise
  def importcrl(self, crldata):
    '''Import a CRL'''

    if not os.path.exists(self.cfg.getGlobalParam('CRL_DIRNAME')):
      os.mkdir(self.cfg.getGlobalParam('CRL_DIRNAME'))

    tempfilename = os.path.join(
         self.cfg.getGlobalParam('CRL_DIRNAME'), 'temp')

    retcode = 0
    self.updatelock.acquire()
    try:
      try:
        open(tempfilename, 'w').write(crldata)
      except IOError:
        logging.error('Could not write CRL data to [%s]' % tempfilename)
        return '-4'

      retcode, result = E.getstatusoutput(
        '%s importcrl %s %s %s' %
        (self.sslWrapperPath, tempfilename,
         self.cfg.getGlobalParam('TRUSTED_CA_DIRNAME'),
         self.cfg.getGlobalParam('CRL_DIRNAME')
         ))
      retcode = retcode / 256

      if retcode != 0:
        return result

      retcode = self._distributeFiles(self.cfg.getGlobalParam('CRL_DIRNAME'))
      if retcode != 0:
        logging.error('Error distributing CRL file: %d' % retcode)
        return str(retcode)

    finally:
      if os.path.exists(tempfilename):
        E.rm(['localhost'], tempfilename)
      self.updatelock.release()

    return '0'

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

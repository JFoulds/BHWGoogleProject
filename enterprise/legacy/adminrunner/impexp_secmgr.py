#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
#
# Original Author: Zia Syed (zsyed@google.com)
#

"""Security manager for the import export feature.
"""

import os
import hmac
import sha
import exceptions
import re

from google3.pyglib import logging

class SecMgrError(exceptions.Exception):
  """Reports general errors related to the security manager.
  """
  pass

class InvalidPasswordError(exceptions.Exception):
  """Reports general errors related to the security manager.
  """
  pass

class SecMgr:
  """Implements routines for signature generation, encryption
  and decryption.
  """

  CIPHER_ALGO_OPTION = '--cipher-algo AES'
  GPG_ERR_MESSAGE = 'gpg: decryption failed: bad key'
  # '.... <uam_dir><![CDATA[\n<blah>\n          ]]>'
  # '</uam_dir>\n ...'
  UAM_RE='(<uam_dir><!\[CDATA\[\s*)(.*)(\s*\]\]></uam_dir>\s*)'

  def __init__(self, passphrase):
    """The passphrase lives with the secmgr and all operations on secmgr
    will use the passphrase
    """
    self.passphrase = passphrase

  def computeSignature(self, body):
    """Uses hmac with a symmetric key.
    """
    # Do not add the uam_dir section to compute the signature.
    body = re.sub(self.UAM_RE, '', body)
    macgen = hmac.HMAC(self.passphrase, body, sha)
    return macgen.hexdigest()

  def verifySignature(self, body, signature):
    return self.computeSignature(body) == signature

  def execCmd(self, body, argument, passphrase):
    """Executes encryption or decryption commands and does error handling.
    passphrase is a utf-8 encoded string.
    """
    # body is unicode (but ASCII contents!), so need to convert it to a string
    # because we want inptext to be a string.
    # With oneboxes and database feeds, body is no longer in ascii,
    # but real utf-8 encoded already.
    if isinstance(body, unicode):
      encoded_body = body.encode('utf-8')
    else:
      encoded_body = body
    inptext = '%s\n%s' % (passphrase, encoded_body)
    (fi, fo, fe) = os.popen3('gpg --armor --passphrase-fd 0 --no-tty --no-version --comment "" %s %s'
                             % (argument, self.CIPHER_ALGO_OPTION))

    fi.write(inptext)
    fi.close()

    # We must read stdout first because when output is very large
    # the buffer gets full and blocks the child process GPG on writing.
    # Since GPG has not closed stderr, the reader, in this case
    # the parent process, also blocks. The result: deadlock (bug 63517)

    # TODO(dcz): this code should be wrapped in some alarm handler,
    # similar to E.py and its python_exec_wrapper.
    text = fo.read()
    fo.close()

    errtext = fe.read()
    fe.close()
    if errtext:
      if re.compile(self.GPG_ERR_MESSAGE).search(errtext):
        raise InvalidPasswordError, 'Invalid password.'
      else:
        logging.error(errtext)

    return text

  def encryptBlock(self, message):
    """The block to be encrypted may contain passwords in plain text. The
    encryption needs to be good enough to protect those passwords because
    the encrypted content will be sent to the user.
    """
    encmessage = self.execCmd(message, '--symmetric', self.passphrase)
    return self.removeHeaderFooter(encmessage)

  def decryptBlock(self, message):
    """Complements encryptBlock method.
    """
    decmessage = self.execCmd(self.insertHeaderFooter(message), '--decrypt', self.passphrase)
    return decmessage

  def removeHeaderFooter(self, message):
    """Assumes that the message has PGP header without version and comment.
    """
    message = re.sub(r'^[^\n]+\n\n', '', message, 1)
    message = re.sub(r'\n[^\n]+$', '', message, 1)
    return message

  def insertHeaderFooter(self, message):
    """Inserts the PGP header that was removed by removeHeaderFooter.
    """
    return '-----BEGIN PGP MESSAGE-----\n\n%s\n-----END PGP MESSAGE-----' % message

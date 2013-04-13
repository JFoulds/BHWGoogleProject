#!/usr/bin/python2.4
#
# (c) Copyright 2002-2003 Google Inc.
# aroetter@google.com
#
# Deal with SSL cert issues
#
# The commands we respond to are
#
# 1. getcertinfo - returns information about either the installed or the
#    staging certificate
#

# 2. gencert - given minimal information, generate a self-signed SSL
#    certificate (this alleviates the problem that the hostname of the
#    certificate doesn't match the appliance's hostname
#

# 3. getcsr - Generate a certificate signing request(CSR) from the GSAs key
#    and return it to the requestor.
#
# 4. setcert - Take a certificate from the requestor and save it as the
#              staging certificate
#
# 5. installcert - copy the staging certificate over to the installed certificate
#
# 6. restart - restart entfrontend and stunnel, both of which depend on SSL
#            - if a new cert is generated/installed, they won't be used
#            - until this is called.
#
# 7. generatekey - generate a new staging RSA private key.
#
# The general use of this is as follows: boot up the GSA and do #2 to
# create a proper hostname (this will alleviate one of the two warnings
# users see (the host one, but the unknown CA one still will be there).
# Then do #3, and mail the given CSR to a root CA. When you get a response
# back from the root CA (it will be a certificate), upload it to the box (#4),
# make sure it is what you want, and install it #5
# then when the admin logs out of the AdminConsole UI, restart everything #6
# at which point the GSA can use it (this will remove the warning about
# a certificate signed by an agency that we the browser doesn't recognize)
################################################

import threading
import os
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
import commands
from google3.enterprise.legacy.util import ssl_cert
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M

WEB_SERVICE_PATH = "/etc/rc.d/init.d/web_";

class SSLHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.sslWrapperPath = (
        "%s/local/google3/enterprise/legacy/util/ssl_cert.py" %
        self.cfg.getGlobalParam("ENTERPRISE_HOME"))
    self.updatelock = threading.Lock()

  def get_accepted_commands(self):
    return {
      "getcertinfo":  admin_handler.CommandInfo(1, 0, 0, self.getcertinfo),
      "gencert": admin_handler.CommandInfo(7, 0, 0, self.gencert),
      "getcsr": admin_handler.CommandInfo(0, 0, 0, self.getcsr),
      "setcert": admin_handler.CommandInfo(0, 0, 1, self.setcert),
      "installcert": admin_handler.CommandInfo(0, 0, 0, self.installcert),
      "restart": admin_handler.CommandInfo(0, 0, 0, self.restart),
      "importkey": admin_handler.CommandInfo(0, 0, 1, self.importkey),
      "installkey": admin_handler.CommandInfo(0, 0, 0, self.installkey),
      "generatekey": admin_handler.CommandInfo(0, 0, 0, self.generatekey),
      }


  def getcertinfo(self, whichcert):
    """ returns information about the currently installed,
    or the staging certificate whichCert is "staging", or "installed"
    returns
    0
    hostname
    organizational unit
    organization
    locality
    state
    country
    email
    notValidBefore date
    notValidAfter date
    on success, or
    1
    on failure"""
    retcode, result = E.getstatusoutput(
      "%s getcertinfo %s %s" %
      (self.sslWrapperPath, whichcert,
       self.cfg.getGlobalParam("ENTERPRISE_HOME")))

    if retcode == 0:
      return "0\n%s" % result
    else:
      logging.info("Couldn't get cert info for %s: %s" % (whichcert, result))
      return "1"

  def gencert(self, hostname, orgunit, organization, locality, state, country,
              emailaddr):
    """ Generates a self-signed SSL certificate
    returns:
    0
    on success, or
    1
    on failure
    """
    self.updatelock.acquire()
    try:
      retcode, result = E.getstatusoutput(
        "secure_script_wrapper -p2 %s gencert %s %s %s %s %s %s %s %s" %
        (self.sslWrapperPath,
         self.cfg.getGlobalParam("ENTERPRISE_HOME"),
         # orgunit always starts with an X because it can be empty
         commands.mkarg(hostname), commands.mkarg(orgunit[1:]),
         commands.mkarg(organization), commands.mkarg(locality),
         commands.mkarg(state), commands.mkarg(country),
         commands.mkarg(emailaddr)))
    finally:
      self.updatelock.release()

    if retcode != 0:
      logging.error("Couldn't generate certificate for host %s: %s" %
                    (hostname, result))

    return retcode != 0

  def getcsr(self):
    """ Returns a certificate request
    returns:
    0
    numbytes
    content
    on success, and
    1
    on failure
    """
    retcode, result = E.getstatusoutput(
      "secure_script_wrapper -p2 %s getcsr %s" %
      (self.sslWrapperPath,
       self.cfg.getGlobalParam("ENTERPRISE_HOME")))

    if retcode != 0:
      logging.error("Couldn't generate CSR: %s" % result)
      return "1"

    return "0\n%d\n%s" % (len(result), result)


  def setcert(self, certBody):
    """ Takes a cert file body as the input, and saves it
    as the staging certificate
    returns 0 on success, or 1 on failure
    """

    retval = 0
    self.updatelock.acquire()
    try:
      try:
        open(ssl_cert.STAGINGCERT_FILENAME %
             self.cfg.getGlobalParam("ENTERPRISE_HOME"), 'w').write(certBody)
      except IOError:
        retval = 1
        logging.error("Couldn't save certificate to [%s]" %
                      (ssl_cert.STAGINGCERT_FILENAME %
                       self.cfg.getGlobalParam("ENTERPRISE_HOME")))

      if retval == 0:
        verifycmd = "secure_script_wrapper -p2 %s verifystagingcert %s" % (
          self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME") )
        outputList = []
        verifycode = E.execute(['localhost'], verifycmd, outputList, 60)

        if verifycode != 0:
          retval = 1
          E.rm(['localhost'],
               ssl_cert.STAGINGCERT_FILENAME %
               self.cfg.getGlobalParam("ENTERPRISE_HOME"))
          logging.error("Couldn't verify certificate [%s]; error code: %d" %
                        (str(outputList), verifycode) )


    finally:
      self.updatelock.release()

    return "%d" % retval

  def installcert(self):
    """ installs the staging certificate as the currently installed certificate
    returns:
    0 on success, and
    1 on failure
    """

    self.updatelock.acquire()
    try:

      # first verify that the staging certificate is a valid file
      verifycmd = "secure_script_wrapper -p2 %s verifystagingcert %s" % (
        self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME") )
      outputList = []
      verifycode = E.execute(['localhost'], verifycmd, outputList, 60)

      if verifycode != 0:
        E.rm(['localhost'],
             ssl_cert.STAGINGCERT_FILENAME %
             self.cfg.getGlobalParam("ENTERPRISE_HOME"))
        logging.error("Verify failed for certificate [%s]; error code: %d" %
                      (str(outputList), verifycode) )
        return "1"

      # distribute the staging certificate
      retcode = E.distribute(self.cfg.getGlobalParam("MACHINES"),
                             ssl_cert.STAGINGCERT_FILENAME %
                             self.cfg.getGlobalParam("ENTERPRISE_HOME"), 60)
      if retcode != 0:
        logging.error("Couldn't distribute apache cert, error %d" % retcode)

      # next, generate the certificate on all machines
      cmd = "secure_script_wrapper -p2 %s installcert %s" % (
        self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME"))

      outputList = []
      retcode = E.execute(self.cfg.getGlobalParam("MACHINES"), cmd, outputList,
                          60)

      if retcode != 0:
        logging.error("Couldn't install cert: %s" % str(outputList))
        return "1"

      self.writeAdminRunnerOpMsg(M.MSG_LOG_SSL_CERT_INSTALLED)
    finally:
      self.updatelock.release()

    return "0"

  def restart(self):
    """ restarts stunnel, and the enterprise_front_end, b/c both of
    these depend on the ssl keys (they both talk https)
    returns:
    0
    on success, and
    1
    on failure
    """

    # restart enterprise frontend - this will take a while
    eferesult = \
              self.cfg.globalParams.WriteConfigManagerServerTypeRestartRequest(
      "entfrontend")
    # restart web service, this is fast
    cmd = '(sleep 5; secure_script_wrapper -e %s%s restart >&/dev/null ' \
          '</dev/null)' % (WEB_SERVICE_PATH, self.cfg.getGlobalParam(
      "VERSION"))
    t = threading.Thread(target=E.execute,
                         args=(['localhost'], cmd, None, 60))
    t.start()
    return not eferesult

  def importkey(self, keyBody):
    """ Takes a private key file body as the input, and saves it
    as the staging key
    returns 0 on success, or 1 on failure
    """

    retval = 0
    self.updatelock.acquire()
    try:
      try:
        open(ssl_cert.STAGINGKEY_FILENAME %
             self.cfg.getGlobalParam("ENTERPRISE_HOME"), 'w').write(keyBody)
      except IOError:
        retval = 1
        logging.error("Couldn't save key to [%s]" %
                      (ssl_cert.STAGINGKEY_FILENAME %
                       self.cfg.getGlobalParam("ENTERPRISE_HOME")))

      if retval == 0:
        # check the key
        if keyBody:
          verifycmd = "secure_script_wrapper -p2 %s verifystagingkey %s" % (
            self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME") )
          outputList = []
          verifycode = E.execute(['localhost'], verifycmd, outputList, 60)
        else:
          verifycode = 0

        if verifycode != 0:
          retval = 1
          E.rm(['localhost'],
               ssl_cert.STAGINGKEY_FILENAME %
               self.cfg.getGlobalParam("ENTERPRISE_HOME"))
          logging.error("Couldn't verify key [%s]; error code: %d" %
                        (str(outputList), verifycode) )


    finally:
      self.updatelock.release()

    return "%d" % retval

  def generatekey(self):
    """ creates a randomly generated staging key; returns 0 on success, 1 on
    failure """

    self.updatelock.acquire()
    try:

      cmd = "secure_script_wrapper -p2 %s generatekey %s" % (
        self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME"))

      outputList = []

      retcode = E.execute(['localhost'], cmd, outputList, 60)

      # if the command failed, we don't want to leave a malformed key around
      if retcode != 0:
        E.rm(['localhost'], ssl_cert.STAGINGKEY_FILENAME %
             self.cfg.getGlobalParam("ENTERPRISE_HOME"))
        logging.error("Couldn't generate private key: %s" %str(outputList))
    finally:
      self.updatelock.release()

    return "%d" % retcode

  def installkey(self):
    """ installs the staging key as the currently installed private key
    returns:
    0 on success,
    1 on empty install key (not an error)
    2 when the private key is invalid
    3 when the private key could not be distributed
    """

    self.updatelock.acquire()
    try:

      # first verify if the staging key is empty (not an error)
      if (not os.path.exists(ssl_cert.STAGINGKEY_FILENAME % \
                             self.cfg.getGlobalParam("ENTERPRISE_HOME"))) or \
         0 == len(open(ssl_cert.STAGINGKEY_FILENAME % \
                       self.cfg.getGlobalParam("ENTERPRISE_HOME"), "r").read()):
        return "1"

      # next verify that the staging key is a valid file
      verifycmd = "secure_script_wrapper -p2 %s verifystagingkey %s" % (
        self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME") )
      outputList = []
      verifycode = E.execute(['localhost'], verifycmd, outputList, 60)

      if verifycode != 0:
        E.rm(['localhost'],
             ssl_cert.STAGINGKEY_FILENAME %
             self.cfg.getGlobalParam("ENTERPRISE_HOME"))
        logging.error("Verify failed for key [%s]; error code: %d" %
                      (str(outputList), verifycode) )
        return "2"

      # distribute the staging key
      retcode = E.distribute(self.cfg.getGlobalParam("MACHINES"),
                             ssl_cert.STAGINGKEY_FILENAME %
                             self.cfg.getGlobalParam("ENTERPRISE_HOME"), 60)
      if retcode != 0:
        logging.error("Couldn't distribute private key, error %d" % retcode)
        return "3"

      # next, copy the key on all machines
      cmd = "secure_script_wrapper -p2 %s installkey %s" % (
        self.sslWrapperPath, self.cfg.getGlobalParam("ENTERPRISE_HOME"))

      outputList = []
      retcode = E.execute(self.cfg.getGlobalParam("MACHINES"), cmd, outputList,
                          60)

      if retcode != 0:
        logging.error("Couldn't install cert: %s" % str(outputList))
        return "3"

      self.writeAdminRunnerOpMsg(M.MSG_LOG_SSL_KEY_INSTALLED)
    finally:
      self.updatelock.release()

    return "0"


if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

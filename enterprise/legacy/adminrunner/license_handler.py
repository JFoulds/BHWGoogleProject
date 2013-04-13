#!/usr/bin/python2.4
#
# Copyright 2002-2003 Google Inc.
# cpopescu@google.com from feng@google.com's  LicenseHandler.java
#
# The 'license' command handler for AdminRunner
#
###############################################################################

import string
import copy

from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import config_utils
from google3.enterprise.license import license_api

###############################################################################

def formatLicense(license, status):
  ''' a helper to print out license variable '''

  if license != None:
    response_map = copy.deepcopy(license.license)
  else:
    response_map = {}

  response_map[license_api.S.ENT_LICENSE_PROBLEMS] = status

  return license_api.S.ENT_LICENSE_INFORMATION + ' = ' + str(response_map)

class LicenseHandler(admin_handler.ar_handler):
  '''This handler executes the 'license' commands from AdminRunner'''
  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      'increasecount'     : admin_handler.CommandInfo(
      1, 0, 0, self.increasecount),
      'isexpired'         : admin_handler.CommandInfo(
      0, 0, 0, self.isexpired),
      'importclearlicense': admin_handler.CommandInfo(
      0, 1, 0, self.importclearlicense),
      'istotallyexpired'  : admin_handler.CommandInfo(
      0, 0, 0, self.istotallyexpired),
      }


  #############################################################################

  #############################################################################

  def  increasecount(self, countStr):
    # increaseCount increases the counter by given #
    return not self.cfg.lm.increaseCount(long(countStr))

  def importclearlicense(self, lic):
    ''' importClearLicense imports a decrypted license '''
    data = {}
    config_utils.SafeExec(lic, data)
    data = data.get(license_api.S.ENT_LICENSE_INFORMATION, {})
    out = []
    for k, v in data.items():
      out.append('%s = %s' % (k, repr(v)))
    license, status = self.cfg.lm.importClearLicense(string.join(out, '\n'))
    return formatLicense(license, status)

  def isexpired(self):
    ''' isExpired is a simple test to see if the license is expired '''

    # Note: this notion of expired is somewhat different than that used by
    # EnterpriseLicense; it is: is the serving time of the license over (and
    # possibly in grace period)
    license = self.cfg.lm.getCurrentLicense()
    return license.isExpired() or license.isInGracePeriod()

  def istotallyexpired(self):
    ''' isTotallyExpired is a simple test to see if the license is expired
    even fron the grace period '''

    license = self.cfg.lm.getCurrentLicense()
    return license.isExpired()


class NewLicenseHandler:
  def __init__(self, adminrunner_server):
    self.cfg = adminrunner_server.cfg

    adminrunner_server.RegisterReplyHandler(
      '/GetLicense', self.__GetLicense)
    adminrunner_server.RegisterReplyHandler(
      '/GetLicenseProtoBuf', self.__GetLicenseProtoBuf)
    adminrunner_server.RegisterRequestReplyHandler(
      '/ViewEncryptedLicense', self.__ViewEncryptedLicense)
    adminrunner_server.RegisterRequestReplyHandler(
      '/ImportEncryptedLicense', self.__ImportEncryptedLicense)

  def __GetLicense(self):
    license, status = self.cfg.lm.viewCurLicense()
    return formatLicense(license, status)

  def __GetLicenseProtoBuf(self):
    license, status = self.cfg.lm.viewCurLicense()
    return self.__ConvertToEncodedPB(license, status)

  def __ViewEncryptedLicense(self, request):
    license, status = self.cfg.lm.importLicense(request, 1)
    return self.__ConvertToEncodedPB(license, status)

  def __ImportEncryptedLicense(self, request):
    license, status = self.cfg.lm.importLicense(request, 0)
    return self.__ConvertToEncodedPB(license, status)

  def __ConvertToEncodedPB(self, license, status):
    logging.info('Converting license to protobuf')
    logging.info('License status: ' + str(status))

    # status can sometime be a string (e.g. 'DECRYPT_GPG_VERIFY_FAILED')
    # in that case, collapse it to C.LIC_INVALID
    if type(status) != type(0):
      status = C.LIC_INVALID
    if license is None:
      # license is bad -- we need to get error status across
      lic_pb = license_api.License()
      lic_pb.set_problems(status)
      return lic_pb.Encode()
    license_dict = license.getLicenseDict()
    license_dict[license_api.S.ENT_LICENSE_PROBLEMS] = status
    return license_api.LicenseDictToProtoBuf(license_dict).Encode()


if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

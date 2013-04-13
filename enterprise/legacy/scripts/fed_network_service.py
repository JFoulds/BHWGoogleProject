#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

""" This service will help start the stunnel server that clients can dial into.

This service will startup at the server boot. The service will come up only if
there is a valid federation network configuration and the stunnel available on
the server. This server will 
"""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

import commands
import os
import string
import sys
import time

from google3.enterprise.legacy.scripts import ent_service
from google3.enterprise.legacy.util import E
from google3.pyglib import logging

from google3.enterprise.legacy.util import port_talker
from google3.enterprise.legacy.util import find_master
from google3.enterprise.legacy.util import python_kill
from google3.enterprise.legacy.util import fed_network_config
from google3.enterprise.legacy.util import fed_network_util
from google3.enterprise.legacy.util import fed_stunnel_config
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import E
from google3.enterprise.license import license_api
from google3.enterprise.core import core_utils

# Config file that need to be used
FED_NETWORK_CONFIG = '%s/local/conf/fed_network.xml'

class FederationNetworkService(ent_service.ent_service):
  """Manages the federation network service on every slave or corpus root."""

  def __init__(self):
    ent_service.ent_service.__init__(self, "fed_network", 0, "2minly", 1, 3600)

  def IsFederationLicensed(self):
    config = fed_stunnel_config.GetEnterpriseConfiguration()
    license_info = config.ENT_LICENSE_INFORMATION
    return license_info.get(license_api.S.ENT_LICENSE_FEDERATION)


  def init_service(self, ent_home):
    ent_service.ent_service.init_service(self, ent_home)
    config_file = FED_NETWORK_CONFIG % ent_home
    logging.info('Configuration file used %s' % config_file)
    if os.path.exists(config_file):
      try:
        self.corpus = fed_network_util.CorpusRootStunnelService(None, None,
                                                              config_file)
      except fed_network_config.FederationConfigException, ex:
        self.corpus = None
    else:
      self.corpus = None
    
  def stop(self):
    if self.IsFederationLicensed() and self.corpus is not None:
      logging.info(" -- stopping federation network -- ")
      self.corpus.Stop()
    else:
      logging.info(" Federation network not stopped -- No License or Invalid Configuration")
    return 1

  def babysit(self):
    logging.info(' --babysit--')
    if self.IsFederationLicensed() and self.corpus is not None:
      (status, message) = self.corpus.Status()
      if status:
        self.corpus.Start()
    return 1
    
  def start(self):
    if self.IsFederationLicensed() and self.corpus is not None:
      log_file_name = ('/export/hda3/tmp/fed_network_%s' %
                       time.strftime('%d-%b-%y'))
      log_file = open(log_file_name, 'a+')
      logging.set_logfile(log_file)
      logging.set_verbosity(logging.DEBUG)
      logging.info(" -- starting federation network -- ")
      self.corpus.Start()
    else:
      logging.info(" Federation network not started -- No License or Invalid Configuration")
    return 1


if __name__ == '__main__':
  stunnel_service = FederationNetworkService()
  stunnel_service.execute(sys.argv)

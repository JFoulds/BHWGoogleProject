#!/usr/bin/python2.4
#
# Copyright 2004-2006 Google Inc.
# All rights reserved.
# Author: Mark Goodman
#
# Important Note: changes to this file should be paired with
# change to config_filters.py, which is used for import/export.

'''This module serializes the entire GSA configuration to an XML
document and deserializes an XML document into the GSA configuration.

If you have added state to the GSA configuration, you will need to
modify an existing class or add a new class as appropriate. If you add
a new class, list it in VERSION_MIGRATION_SERIALIZATION.

See also: https://www.corp.google.com/eng/designdocs/enterprise/version_manager.html
'''

import base64
import cStringIO # 4.7
import glob
import os # 6.1
import re # 4.2
import sha # 15.3
import struct # 4.3
import sys # 3.1
import time # 6.10
import traceback
import urllib # 11.4
import xml.dom # 13.6
import xml.dom.ext
import xml.dom.ext.Printer
import xml.dom.minidom # 13.7

from google3.googlebot.cookieserver.util import pywrapcookierule
from google3.net.http import pywraphttpserver
from google3.pyglib import logging
from google3.strings import pywrap_strutil

from google3.enterprise.legacy.adminrunner import configurator # adminrunner
from google3.enterprise.legacy.adminrunner import entconfig # RepairUTF8
from google3.enterprise.legacy.adminrunner import scoring_adjust_handler
from google3.enterprise.legacy.adminrunner import user_manager # adminrunner
from google3.enterprise.legacy.collections import ent_collection # collections
from google3.enterprise.legacy.production.babysitter import validatorlib # babysitter
from google3.pyglib import OrderedDictionary # pyglib
from google3.pyglib import functional # pyglib
from google3.enterprise.legacy.util import C # util
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import ssl_cert # util
from google3.enterprise.license import license_api


class GsaXmlWriter(object):

  def __init__(self, fp, indentation=2, encoding='UTF-8'):
    self._write = fp.write
    self._indentation = indentation
    self._encoding = encoding
    self._tag_stack = []
    self._last_text = 1
    self._element_open = 0
    self._write("<?xml version='1.0' encoding='%s'?>\n" % self._encoding)

  def EndDocument(self):
    assert len(self._tag_stack) == 0
    self._write('\n')

  def StartElement(self, parent, tag):
    if self._element_open:
      self._write('>')
      self._element_open = 0
    if not self._last_text:
      self._write('\n')
      self._write(' ' * len(self._tag_stack) * self._indentation)
    self._tag_stack.append(tag)
    self._write('<%s' % tag)
    self._last_text = 0
    self._element_open = 1
    return tag

  def EndElement(self, tag):
    top = self._tag_stack.pop()
    assert top == tag
    if self._element_open:
      self._write('/>')
      self._element_open = 0
    else:
      if not self._last_text:
        self._write('\n')
        self._write(' ' * len(self._tag_stack) * self._indentation)
      self._write('</%s>' % tag)
    self._last_text = 0

  def AppendCdata(self, data):
    if self._element_open:
      self._write('>')
      self._element_open = 0
    self._last_text = 1
    self._write('<![CDATA[%s]]>' % data.replace(']]>', ']]]]><![CDATA[>'))

  def AppendText(self, text):
    if self._element_open:
      self._write('>')
      self._element_open = 0
    self._last_text = 1
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    # Note: we do not escape ">", eventually we should use:
    #self._write(xml.sax.saxutils.escape(text))
    self._write(text)

  def CheckTop(self, name):
    if len(self._tag_stack):
      top = self._tag_stack[-1]
      assert name == top

# Helper functions

def AppendElementText(document, parent_node, child_name, text):
  document.CheckTop(parent_node)
  document.StartElement(parent_node, child_name)
  if text:
    assert isinstance(text, str)
    text = entconfig.RepairUTF8(text)
    document.AppendText(text)
  document.EndElement(child_name)

def AppendElementCDATA(document, parent_node, child_name, text):
  document.CheckTop(parent_node)
  document.StartElement(parent_node, child_name)
  if text:
    document.AppendCdata(text)
  document.EndElement(child_name)


def GetChildrenElementsByTagName(node, tagName):
  """Returns the children elements of the node with name tagName."""
  elements = []
  for child_node in node.childNodes:
    if child_node.nodeType == xml.dom.Node.ELEMENT_NODE and \
       child_node.tagName == tagName:
      elements.append(child_node)
  return elements

def GetSingleElement(node, name):
  elements = GetChildrenElementsByTagName(node, name)
  return elements[0]

def GetText(node):
  if (len(node.childNodes) == 1 and
      node.firstChild.nodeType == xml.dom.Node.TEXT_NODE):
    # encode is present because validatorlib expects a String not a
    # UnicodeString.
    return node.firstChild.data.encode('utf-8')
  # Some versions of PyXML don't change CDATA into text. This only affects the
  # unit test on my corp machine.
  elif (len(node.childNodes) >= 1 and
        reduce(lambda x, y: x and y.nodeType == xml.dom.Node.CDATA_SECTION_NODE,
               node.childNodes, 1)):
    return (''.join([x.data for x in node.childNodes])).encode('utf-8')
  return ''

def GetElementText(element, name):
  return GetText(GetSingleElement(element, name))

def Set(cfg, name, value):
  errors = cfg.globalParams.set_var(name, value, 1)
  assert errors == validatorlib.VALID_OK

def SetFile(cfg, name, value):
  cfg.globalParams.set_file_var_content(name, value, 0)
  # The validator for startUrls is broken so we don't validate.
  # errors = cfg.globalParams.set_file_var_content(name, value, 1)
  # assert errors == validatorlib.VALID_OK

def QuoteIfNecessary(s):
  if s.find('"') == -1 and s.find(',') == -1:
    return s
  escaped = ['"']
  for c in s:
    if c == '"':
      escaped.append('"')
    escaped.append(c)
  escaped.append('"')
  return ''.join(escaped)

def BoolToString(value):
  if value:
    assert isinstance(value, int)
    return 'True'
  else:
    return 'False'

def StringToBool(value):
  """String means the text inside an XML element."""
  return { 'False' : 0,
           'True' : 1 }[value]

def StringToBoolStr(value):
  return str(StringToBool(value))

# TODO(mgoodman): Move to functional.py
def InvertMap(map):
  inverted_map = {}
  for key, value in map.iteritems():
    inverted_map[value] = key
  return inverted_map

# A class per top-level item.

class License:
  LICENSE = 'license'
  ID = 'id'
  SYSTEM_ID = 'systemId'
  ELAPSED_TIME = 'elapsedTime'
  DURATION = 'duration'
  END_TIME = 'endTime'
  GRACE_PERIOD = 'gracePeriod'
  MAX_COLLECTIONS = 'maxCollections'
  MAX_FRONT_ENDS = 'maxFrontEnds'
  MAX_PAGES = 'maxPages'
  ENABLE_SEKU_LITE = 'enableSekuLite'
  ENABLE_LDAP = 'enableLdap'
  ENABLE_SSO = 'enableSso'
  #
  # [Kerberos/IWA] ...
  #
  ENABLE_KERBEROS_AT_LOGIN  = 'enableKerberosAtLogin'   # [Kerberos/IWA]
  ENABLE_KERBEROS_AT_CRAWL  = 'enableKerberosAtCrawl'   # [Kerberos/IWA]
  ENABLE_KERBEROS_AT_SERVE  = 'enableKerberosAtServe'   # [Kerberos/IWA]
  ENABLE_KERBEROS_KT_PARSE  = 'enableKerberosKtParse'   # [Kerberos/IWA]
  ENABLE_KERBEROS_AT_ONEBOX = 'enableKerberosAtOnebox'  # [Kerberos/IWA]
  #
  # [Kerberos/IWA] ... done.
  #
#  ENABLE_CATEGORIES = 'enableCategories'
  ENABLE_COOKIE_SITES = 'enableCookieSites'
  ENABLE_DATABASES = 'enableDatabases'
  ENABLE_FEEDS = 'enableFeeds'
  ENABLE_FILESYSTEM = 'enableFileSystem'
  ENABLE_BATCH_CRAWL = 'enableBatchCrawl'
  ENABLE_QUERY_EXPANSION = 'enableQueryExpansion'
  ENABLE_CLUSTERING = 'enableClustering'
  ENABLE_SCORING_ADJUST = 'enableScoringAdjust'
  ENABLE_CONNECTOR_FRAMEWORK = 'enableConnectorFramework'
  ENABLE_FEDERATION = 'enableFederation'
  LABS_SETTINGS = 'labsSettings'

  def Export(self, document, cfg):
    license_map = cfg.getGlobalParam(license_api.S.ENT_LICENSE_INFORMATION)
    license = document.StartElement(document.documentElement, self.LICENSE)
    try:
      AppendElementText(document, license, self.ID,
                        license_map[license_api.S.ENT_LICENSE_ID])
      AppendElementText(document, license, self.SYSTEM_ID,
                        license_map[license_api.S.ENT_BOX_ID])

      # TODO(mgoodman): If this code doesn't run as part of the AdminRunner,
      # there is no need to use this abstraction.
      cfg.lm.counter_lock.acquire()
      try:
        AppendElementText(document, license, self.ELAPSED_TIME,
                          str(cfg.lm.getLicenseCounter().getCount() / 1000))
      finally:
        cfg.lm.counter_lock.release()

      AppendElementText(document, license, self.DURATION,
          str(license_map[license_api.S.ENT_LICENSE_SERVING_TIME] / 1000))
      AppendElementText(document, license, self.END_TIME,
          str(license_map[license_api.S.ENT_LICENSE_END_DATE] / 1000))
      AppendElementText(document, license, self.GRACE_PERIOD,
          str(license_map[license_api.S.ENT_LICENSE_GRACE_PERIOD] / 1000))
      AppendElementText(document, license, self.MAX_PAGES,
          str(license_map[license_api.S.ENT_LICENSE_MAX_PAGES_OVERALL]))
      AppendElementText(document, license, self.MAX_COLLECTIONS,
          str(license_map[license_api.S.ENT_LICENSE_MAX_COLLECTIONS]))
      AppendElementText(document, license, self.MAX_FRONT_ENDS,
          str(license_map[license_api.S.ENT_LICENSE_MAX_FRONTENDS]))
      AppendElementText(document, license, self.ENABLE_SEKU_LITE,
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE]))
      AppendElementText(document, license, self.ENABLE_LDAP,
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_LDAP]))
      AppendElementText(document, license, self.ENABLE_SSO,
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_SSO]))
      #
      # [Kerberos/IWA] ...
      #
      AppendElementText(document, license, self.ENABLE_KERBEROS_AT_LOGIN,   # [Kerberos/IWA]
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN]))
      AppendElementText(document, license, self.ENABLE_KERBEROS_AT_CRAWL,   # [Kerberos/IWA]
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL]))
      AppendElementText(document, license, self.ENABLE_KERBEROS_AT_SERVE,   # [Kerberos/IWA]
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE]))
      AppendElementText(document, license, self.ENABLE_KERBEROS_KT_PARSE,   # [Kerberos/IWA]
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE]))
      AppendElementText(document, license, self.ENABLE_KERBEROS_AT_ONEBOX,  # [Kerberos/IWA]
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX]))
      #
      # [Kerberos/IWA] ... done.
      #
      AppendElementText(document, license, self.ENABLE_COOKIE_SITES,
          BoolToString(license_map[license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL])
          )
      AppendElementText(document, license, self.ENABLE_DATABASES,
          BoolToString(license_map[license_api.S.ENT_LICENSE_DATABASES]))
      AppendElementText(document, license, self.ENABLE_FEEDS,
          BoolToString(license_map[license_api.S.ENT_LICENSE_FEEDS]))
      AppendElementText(document, license, self.ENABLE_FILESYSTEM,
          BoolToString(license_map[license_api.S.ENT_LICENSE_FILESYSTEM]))
      AppendElementText(document, license, self.ENABLE_BATCH_CRAWL,
          BoolToString(license_map[license_api.S.ENT_LICENSE_BATCH_CRAWL]))
      AppendElementText(document, license, self.ENABLE_QUERY_EXPANSION,
          BoolToString(license_map[license_api.S.ENT_LICENSE_QUERY_EXPANSION]))
      AppendElementText(document, license, self.ENABLE_CLUSTERING,
          BoolToString(license_map[license_api.S.ENT_LICENSE_CLUSTERING]))
      AppendElementText(document, license, self.ENABLE_SCORING_ADJUST,
          str(license_map[license_api.S.ENT_LICENSE_SCORING_ADJUST]))
      AppendElementText(document, license, self.ENABLE_CONNECTOR_FRAMEWORK,
          BoolToString(license_map[license_api.S.ENT_LICENSE_CONNECTOR_FRAMEWORK])
          )
      AppendElementText(document, license, self.ENABLE_FEDERATION,
          BoolToString(license_map[license_api.S.ENT_LICENSE_FEDERATION]))
      AppendElementText(document, license, self.LABS_SETTINGS,
          str(license_map[license_api.S.ENT_LICENSE_LABS_SETTINGS]))
    finally:
      document.EndElement(self.LICENSE)

  def Import(self, document, cfg):
    license_element = GetSingleElement(document.documentElement, self.LICENSE)

    # USER_AGENT_COMMENT depends on ENT_CONFIG_NAME.
    cfg.setGlobalParam(C.ENT_CONFIG_NAME,
                       GetElementText(license_element, self.SYSTEM_ID))

    #
    # [Kerberos/IWA] ...
    #
    enable_kerberos_at_login = GetChildrenElementsByTagName(
      license_element, self.ENABLE_KERBEROS_AT_LOGIN)  # [Kerberos/IWA]
    if enable_kerberos_at_login:
      enable_kerberos_at_login = StringToBool(GetText(enable_kerberos_at_login[0]))
    else:
      enable_kerberos_at_login = 0      # Off by default

    enable_kerberos_at_crawl = GetChildrenElementsByTagName(
      license_element, self.ENABLE_KERBEROS_AT_CRAWL)  # [Kerberos/IWA]
    if enable_kerberos_at_crawl:
      enable_kerberos_at_crawl = StringToBool(GetText(enable_kerberos_at_crawl[0]))
    else:
      enable_kerberos_at_crawl = 0      # Off by default

    enable_kerberos_at_serve = GetChildrenElementsByTagName(
      license_element, self.ENABLE_KERBEROS_AT_SERVE)  # [Kerberos/IWA] On [5.2]
    if enable_kerberos_at_serve:
      enable_kerberos_at_serve = StringToBool(GetText(enable_kerberos_at_serve[0]))
    else:
      enable_kerberos_at_serve = 1      # On by default [5.2]

    enable_kerberos_kt_parse = GetChildrenElementsByTagName(
      license_element, self.ENABLE_KERBEROS_KT_PARSE)  # [Kerberos/IWA]
    if enable_kerberos_kt_parse:
      enable_kerberos_kt_parse = StringToBool(GetText(enable_kerberos_kt_parse[0]))
    else:
      enable_kerberos_kt_parse = 0      # Off by default

    enable_kerberos_at_onebox = GetChildrenElementsByTagName(
      license_element, self.ENABLE_KERBEROS_AT_ONEBOX)  # [Kerberos/IWA]
    if enable_kerberos_at_onebox:
      enable_kerberos_at_onebox = StringToBool(GetText(enable_kerberos_at_onebox[0]))
    else:
      enable_kerberos_at_onebox = 0     # Off by default
    #
    # [Kerberos/IWA] ... done.
    #

    enable_cookie_sites = GetChildrenElementsByTagName(
      license_element, self.ENABLE_COOKIE_SITES)
    if enable_cookie_sites:
      enable_cookie_sites = StringToBool(GetText(enable_cookie_sites[0]))
    else:
      enable_cookie_sites = 0

    enable_databases = GetChildrenElementsByTagName(
      license_element, self.ENABLE_DATABASES)
    if enable_databases:
      enable_databases = StringToBool(GetText(enable_databases[0]))
    else:
      enable_databases = 1

    enable_feeds = GetChildrenElementsByTagName(
      license_element, self.ENABLE_FEEDS)
    if enable_feeds:
      enable_feeds = StringToBool(GetText(enable_feeds[0]))
    else:
      enable_feeds = 1

    enable_query_expansion = GetChildrenElementsByTagName(
      license_element, self.ENABLE_QUERY_EXPANSION)
    if enable_query_expansion:
      enable_query_expansion = StringToBool(GetText(enable_query_expansion[0]))
      # Hack to determine if the config we are about to import is post 4.4
      # TODO(meghna) Add config variable containing the version of the exported
      # config. This variable should not be importable.
      config_post_44 = 1
    elif cfg.getGlobalParam('ENT_CONFIG_TYPE') == 'MINI':
      # We shouldn't enable query expansion on the mini
      enable_query_expansion = 0
      config_post_44 = 0
    else:
      # Enable query expansion on non-mini
      enable_query_expansion = 1
      config_post_44 = 0

    enable_clustering = GetChildrenElementsByTagName(
      license_element, self.ENABLE_CLUSTERING)
    if enable_clustering:
      enable_clustering = StringToBool(GetText(enable_clustering[0]))
    elif cfg.getGlobalParam('ENT_CONFIG_TYPE') == 'MINI':
      # We shouldn't enable clustering the mini
      enable_clustering = 0
    else:
      # If attribute is missing in previous license, enable by default.
      enable_clustering = 1

    # Enable scoring adjusment by default regardless of previous license value
    enable_scoring_adjust = 1

    enable_filesystem = GetChildrenElementsByTagName(
      license_element, self.ENABLE_FILESYSTEM)
    if enable_filesystem and config_post_44:
      enable_filesystem = StringToBool(GetText(enable_filesystem[0]))
    else:
      enable_filesystem = 1

    enable_batchcrawl = GetChildrenElementsByTagName(
      license_element, self.ENABLE_BATCH_CRAWL)
    if enable_batchcrawl and config_post_44:
      enable_batchcrawl = StringToBool(GetText(enable_batchcrawl[0]))
    else:
      enable_batchcrawl = 1

    if cfg.getGlobalParam('ENT_CONFIG_TYPE') == 'MINI':
      # We should never enable connector framework on the mini
      enable_connector_framework = 0
    else:
      enable_connector_framework = 1

    enable_federation = GetChildrenElementsByTagName(
      license_element, self.ENABLE_FEDERATION)
    if enable_federation and config_post_44:
      enable_federation = StringToBool(
        GetText(enable_federation[0]))
    else:
      enable_federation = 0

    # Enterprise labs settings.
    labs_settings = GetChildrenElementsByTagName(
      license_element, self.LABS_SETTINGS)
    if labs_settings and config_post_44:
      labs_settings = GetText(labs_settings[0])
    else:
      labs_settings = ''

    # License Fixup
    # Fix the license for QA machines that accidentally get partial upgrades.
    # License migration fails because the bad value gets imported and not
    # upgraded.
    if cfg.getGlobalParam('ENT_CONFIG_TYPE') == 'MINI':
      enable_query_expansion = 0


    license = {
      license_api.S.ENT_LICENSE_ID:
        GetElementText(license_element, self.ID),
      license_api.S.ENT_BOX_ID:
        GetElementText(license_element, self.SYSTEM_ID),
      license_api.S.ENT_LICENSE_SERVING_TIME:
        long(GetElementText(license_element, self.DURATION)) * 1000,
      license_api.S.ENT_LICENSE_END_DATE:
        long(GetElementText(license_element, self.END_TIME)) * 1000,
      license_api.S.ENT_LICENSE_GRACE_PERIOD:
        long(GetElementText(license_element, self.GRACE_PERIOD)) * 1000,
      license_api.S.ENT_LICENSE_MAX_PAGES_OVERALL:
        long(GetElementText(license_element, self.MAX_PAGES)),
      license_api.S.ENT_LICENSE_MAX_COLLECTIONS:
        long(GetElementText(license_element, self.MAX_COLLECTIONS)),
      license_api.S.ENT_LICENSE_MAX_FRONTENDS:
        long(GetElementText(license_element, self.MAX_FRONT_ENDS)),
      license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE: 1,
      license_api.S.ENT_LICENSE_ENABLE_SSO:
        StringToBool(GetElementText(license_element, self.ENABLE_SSO)),
      license_api.S.ENT_LICENSE_ENABLE_LDAP: 1,
      #
      # [Kerberos/IWA] ...
      #
      license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN:   # [Kerberos/IWA]
                                enable_kerberos_at_login,
      license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL:   # [Kerberos/IWA]
                                enable_kerberos_at_crawl,
      license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE:   # [Kerberos/IWA]
                                enable_kerberos_at_serve,
      license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE:   # [Kerberos/IWA]
                                enable_kerberos_kt_parse,
      license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX:  # [Kerberos/IWA]
                                enable_kerberos_at_onebox,
      #
      # [Kerberos/IWA] ... done.
      #
      license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL: enable_cookie_sites,
      license_api.S.ENT_LICENSE_ENABLE_CATEGORY: 0,
      license_api.S.ENT_LICENSE_DATABASES: enable_databases,
      license_api.S.ENT_LICENSE_FEEDS: enable_feeds,
      license_api.S.ENT_LICENSE_FILESYSTEM: enable_filesystem,
      license_api.S.ENT_LICENSE_BATCH_CRAWL: enable_batchcrawl,
      license_api.S.ENT_LICENSE_QUERY_EXPANSION: enable_query_expansion,
      license_api.S.ENT_LICENSE_CLUSTERING: enable_clustering,
      license_api.S.ENT_LICENSE_SCORING_ADJUST: enable_scoring_adjust,
      license_api.S.ENT_LICENSE_CONNECTOR_FRAMEWORK: enable_connector_framework,
      license_api.S.ENT_LICENSE_FEDERATION : enable_federation,
      license_api.S.ENT_LICENSE_LABS_SETTINGS : labs_settings,

      # These entries make validatorlib happy.
      license_api.S.ENT_LICENSE_VERSION: '1.0',
      license_api.S.ENT_LICENSE_CREATION_DATE: 1L,
      license_api.S.ENT_LICENSE_ORIGINAL_END_DATE: 0L,
      license_api.S.ENT_LICENSE_START_DATE: 1L,
      license_api.S.ENT_LICENSE_MAX_PAGES_PER_COLLECTION: 0L,

      }

    # EnterpriseLicense.updateTimeLimit doesn't always succeed in setting this
    # so we set it here as well.
    license[license_api.S.ENT_LICENSE_LEFT_TIME] = min(
      license[license_api.S.ENT_LICENSE_END_DATE] - long(time.time()) * 1000,
      license[license_api.S.ENT_LICENSE_SERVING_TIME])

    cfg.setGlobalParam(C.ENT_LICENSE_INFORMATION, license)

    SetFile(cfg, C.ENT_LICENSE_COUNTER_FILE, str(long(GetElementText(
      license_element, self.ELAPSED_TIME)) * 1000))
    SetFile(cfg, C.ENT_LICENSE_COUNTER_FILE_BACKUP, str(long(GetElementText(
      license_element, self.ELAPSED_TIME)) * 1000))


class StartUrls:
  START_URLS = 'startUrls'

  def Export(self, document, cfg):
    AppendElementText(document, document.documentElement, self.START_URLS,
                      open(cfg.getGlobalParam(C.STARTURLS), 'r').read())

  def Import(self, document, cfg):
    start_urls = GetChildrenElementsByTagName(document.documentElement,
                                              self.START_URLS)
    # StartUrls is optional.
    if not start_urls:
      return

    start_urls = GetText(start_urls[0])
    SetFile(cfg, C.STARTURLS, start_urls)
    SetFile(cfg, C.PAGERANKER_BATCHURLS_FILE_0, start_urls)
    SetFile(cfg, C.PAGERANKER_BATCHURLS_FILE_1, start_urls)


class AbstractFileItem:
  ELEMENT_NAME = None
  GOOGLE_CONFIG_NAME = None

  def Export(self, document, cfg):
    AppendElementText(
      document, document.documentElement, self.ELEMENT_NAME,
      open(cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME), 'r').read()
      )

  def Import(self, document, cfg):
    elements = GetChildrenElementsByTagName(document.documentElement,
                                            self.ELEMENT_NAME)

    # This element is optional.
    if not elements:
      return

    SetFile(cfg, self.GOOGLE_CONFIG_NAME, GetText(elements[0]))


class CrawlUrlPatterns(AbstractFileItem):
  ELEMENT_NAME = 'crawlUrlPatterns'
  GOOGLE_CONFIG_NAME = C.GOODURLS

  def Import(self, document, cfg):
    elements = GetChildrenElementsByTagName(document.documentElement,
                                            self.ELEMENT_NAME)

    # This element is optional.
    if not elements:
      return
    # migrate db patterns if necessary
    goodurls = entconfig.MigrateGoodURLs(GetText(elements[0]))
    SetFile(cfg, self.GOOGLE_CONFIG_NAME, goodurls)


class DoNotCrawlUrlPatterns(AbstractFileItem):
  ELEMENT_NAME = 'doNotCrawlUrlPatterns'
  GOOGLE_CONFIG_NAME = C.BADURLS


class ProxyServers:
  PROXY_SERVERS = 'proxyServers'
  PROXY_SERVER = 'proxyServer'
  URL_PATTERN = 'urlPattern'
  HOST = 'host'
  PORT = 'port'

  # Regular expression to parse a proxy server line.
  PROXY_CONFIG_RE = re.compile(r'(.+)\s+(.+):(.+)')

  def Export(self, document, cfg):
    proxy_servers = document.StartElement(document.documentElement,
                                  self.PROXY_SERVERS)
    try:
      for line in open(cfg.getGlobalParam(C.PROXY_CONFIG), 'r').readlines():
        if not line.strip():
          continue

        url_pattern, host, port = self.PROXY_CONFIG_RE.match(line).groups()
        proxy_server = document.StartElement(proxy_servers, self.PROXY_SERVER)
        try:
          AppendElementText(document, proxy_server, self.URL_PATTERN, url_pattern)
          AppendElementText(document, proxy_server, self.HOST, host)
          AppendElementText(document, proxy_server, self.PORT, port)
        finally:
          document.EndElement(self.PROXY_SERVER)
    finally:
      document.EndElement(self.PROXY_SERVERS)

  def Import(self, document, cfg):
    proxy_servers = GetChildrenElementsByTagName(document.documentElement,
                                                 self.PROXY_SERVERS)

    # ProxyServers is optional.
    if not proxy_servers:
      return

    lines = []
    for proxy_server in GetChildrenElementsByTagName(proxy_servers[0],
                                                     self.PROXY_SERVER):
      lines.append('%s %s:%s\n' % (
        GetElementText(proxy_server, self.URL_PATTERN),
        GetElementText(proxy_server, self.HOST),
        GetElementText(proxy_server, self.PORT)
        ))
    SetFile(cfg, C.PROXY_CONFIG, ''.join(lines))


class CrawlCredentials:
  CRAWL_CREDENTIALS = 'crawlCredentials'
  CRAWL_CREDENTIAL = 'crawlCredential'
  URL_PATTERN = 'urlPattern'
  USERNAME = 'username'
  DOMAIN = 'domain' # optional
  PASSWORD = 'password'
  PUBLIC = 'public' # optional

  # Regular expression to parse a crawl credential.
  CRAWL_CREDENTIAL_RE = re.compile(r'(.+):([^:]*):(.+):([^:]*)\n')

  def Export(self, document, cfg):
    allow_secure = cfg.getGlobalParam(license_api.S.ENT_LICENSE_INFORMATION)[
                                  license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE]
    crawl_credentials = document.StartElement(document.documentElement,
                                      self.CRAWL_CREDENTIALS)
    try:
      for line in open(cfg.getGlobalParam(C.CRAWL_USERPASSWD_CONFIG)).readlines():
        if not line.strip():
          continue

        url_pattern, credential = line.split(' ')
        username, domain, public, password = (
          self.CRAWL_CREDENTIAL_RE.match(urllib.unquote(credential)).groups())
        crawl_credential = document.StartElement(crawl_credentials,
                                                 self.CRAWL_CREDENTIAL)
        try:
          AppendElementText(document, crawl_credential, self.URL_PATTERN,
                            url_pattern)
          AppendElementText(document, crawl_credential, self.USERNAME, username)
          if domain:
            AppendElementText(document, crawl_credential, self.DOMAIN, domain)
          AppendElementText(document, crawl_credential, self.PASSWORD, password)
          if allow_secure:
            AppendElementText(document, crawl_credential, self.PUBLIC,
                              BoolToString(int(public)))
        finally:
          document.EndElement(self.CRAWL_CREDENTIAL)
    finally:
      document.EndElement(self.CRAWL_CREDENTIALS)

  def Import(self, document, cfg):
    crawl_credentials = GetChildrenElementsByTagName(document.documentElement,
                                                     self.CRAWL_CREDENTIALS)

    # CrawlCredentials is optional.
    if not crawl_credentials:
      return

    allow_secure = cfg.getGlobalParam(license_api.S.ENT_LICENSE_INFORMATION)[
                                  license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE]
    lines = []
    for crawl_credential in GetChildrenElementsByTagName(crawl_credentials[0],
                                                         self.CRAWL_CREDENTIAL):
      domain = GetChildrenElementsByTagName(crawl_credential, self.DOMAIN)
      if domain:
        domain = GetText(domain[0])
      else:
        domain = ''

      public = GetChildrenElementsByTagName(crawl_credential, self.PUBLIC)

      # If the license does not enable SEKU-lite, all results are public.
      if allow_secure and public:
        # TODO(mgoodman): The absence of GetText made debug_traceback give bogus
        # line numbers. Track this down.
        public = StringToBool(GetText(public[0]))
      else:
        public = 1

      lines.append('%s %s\n' % (
        GetElementText(crawl_credential, self.URL_PATTERN),
        urllib.quote('%s:%s:%d:%s' % (
        GetElementText(crawl_credential, self.USERNAME),
        domain, public, GetElementText(crawl_credential, self.PASSWORD)
        ))))
    SetFile(cfg, C.CRAWL_USERPASSWD_CONFIG, ''.join(lines))


class AbstractItem:
  ELEMENT_NAME = None
  GOOGLE_CONFIG_NAME = None

  def Export(self, document, cfg):
    text = self.ExportFilter(cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME))
    AppendElementText(document, document.documentElement, self.ELEMENT_NAME,
                      text)

  def ExportFilter(self, value):
    return value

  def Import(self, document, cfg):
    elements = GetChildrenElementsByTagName(document.documentElement,
                                            self.ELEMENT_NAME)

    # This element is optional.
    if not elements:
      return

    Set(cfg, self.GOOGLE_CONFIG_NAME,
        self.ImportFilter(GetText(elements[0])))

  def ImportFilter(self, value):
    return value


class UserAgent(AbstractItem):
  ELEMENT_NAME = 'userAgent'
  GOOGLE_CONFIG_NAME = C.USER_AGENT_TO_SEND


class HttpHeaders(AbstractItem):
  ELEMENT_NAME = 'httpHeaders'
  GOOGLE_CONFIG_NAME = C.BOT_ADDITIONAL_REQUEST_HDRS

  def ExportFilter(self, value):
    # Convert None to ''
    if not value:
      return ''
    else:
      return urllib.quote_plus(value)

  def ImportFilter(self, value):
    return urllib.unquote_plus(value)


class CookieRule:
  ACTION = 'action'
  URL = 'url'
  METHOD = 'method'
  POST = 'post'
  GET = 'get'
  ATTRIBUTE = 'attribute'
  NAME = 'name'
  TYPE = 'type'
  PASSWORD_PREFIX = '*'
  PASSWORD = 'password'
  HIDDEN_PREFIX = '%'
  HIDDEN = 'hidden'
  NORMAL = 'normal'
  VALUE = 'value'

  URL_PATTERN = 'urlPattern'
  EXPIRATION = 'expiration'

  # Regular expression to parse a cookie rule.
  COOKIE_RULE_RE = re.compile(r'(\S+)\s+(.+)')

  COMMENT_RE = re.compile('\s*#')

  def ExportCookieRuleActions(self, document, cookie_rule, cookie_rule_element):
    """Reuse the C++ code for parsing cookie rules."""

    for i in range(cookie_rule.GetNumActions()):
      action = cookie_rule.action(i)
      action_element = document.StartElement(cookie_rule_element, self.ACTION)
      try:
        AppendElementText(document, action_element, self.URL,
                          action.url().Assemble())
        if action.protocol() == pywraphttpserver.HTTPHeaders.PROTO_GET:
          AppendElementText(document, action_element, self.METHOD, self.GET)
        elif action.protocol() == pywraphttpserver.HTTPHeaders.PROTO_POST:
          AppendElementText(document, action_element, self.METHOD, self.POST)
        for j in range(action.GetNumAVPairs()):
          attribute = document.StartElement(action_element, self.ATTRIBUTE)
          try:
            if action.type(j) == self.PASSWORD_PREFIX:
              AppendElementText(document, attribute, self.TYPE,
                                self.PASSWORD)
            elif action.type(j) == self.HIDDEN_PREFIX:
              AppendElementText(document, attribute, self.TYPE,
                                self.HIDDEN)
            else:
              AppendElementText(document, attribute, self.TYPE,
                                self.NORMAL)
            AppendElementText(document, attribute, self.NAME, action.attr(j))
            AppendElementText(document, attribute, self.VALUE, action.value(j))
          finally:
            document.EndElement(self.ATTRIBUTE)
      finally:
        document.EndElement(self.ACTION)

  def ImportCookieRuleActions(self, cookie_rule):
    actions = []
    for cookie_action in GetChildrenElementsByTagName(
      cookie_rule, self.ACTION):
      attributes = []
      for attribute in GetChildrenElementsByTagName(
        cookie_action, self.ATTRIBUTE):

        type = GetChildrenElementsByTagName(attribute, self.TYPE)
        if type:
          type = GetText(type[0])
          if type == self.PASSWORD:
            type = self.PASSWORD_PREFIX
          elif type == self.HIDDEN:
            type = self.HIDDEN_PREFIX
          else:
            type = ''
        else:
          type = ''

        attributes.append(
          '%s=%s=%s' % (
          type,
          urllib.quote_plus(GetElementText(attribute, self.NAME)),
          urllib.quote_plus(GetElementText(attribute, self.VALUE)
          )))
      actions.append(
        '<%s %s %s>' % (
        urllib.quote_plus(GetElementText(cookie_action, self.URL)),
        GetElementText(cookie_action, self.METHOD),
        ' '.join(attributes)
        ))
    return ' '.join(actions)


class CookieSites(CookieRule):
  COOKIE_SITES = 'cookieSites'
  COOKIE_RULE = 'cookieRule'

  def Export(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL]:
      return

    cookie_sites = document.StartElement(document.documentElement,
                                         self.COOKIE_SITES)
    try:
      for line in open(cfg.getGlobalParam(C.COOKIE_RULES), 'r').readlines():
        if not line.strip():
          continue
        if self.COMMENT_RE.match(line):
          continue

        cookie_rule_element = document.StartElement(cookie_sites,
                                                    self.COOKIE_RULE)
        try:
          url_pattern, cookie_rule_string = self.COOKIE_RULE_RE.match(line).groups()
          AppendElementText(document, cookie_rule_element, self.URL_PATTERN,
                            url_pattern)
          cookie_rule = pywrapcookierule.CookieRule()
          cookie_rule.ParseFromString(cookie_rule_string)
          self.ExportCookieRuleActions(document, cookie_rule, cookie_rule_element)
          AppendElementText(document, cookie_rule_element, self.EXPIRATION,
                            str(cookie_rule.expiration()))
        finally:
          document.EndElement(self.COOKIE_RULE)
    finally:
      document.EndElement(self.COOKIE_SITES)

  def Import(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL]:
      return

    cookie_sites = GetChildrenElementsByTagName(document.documentElement,
                                                self.COOKIE_SITES)

    # CookieSites is optional.
    if not cookie_sites:
      return

    lines = []
    for cookie_rule in GetChildrenElementsByTagName(
      cookie_sites[0], self.COOKIE_RULE):
      lines.append('%s %s 1 %s\n' % (
        GetElementText(cookie_rule, self.URL_PATTERN),
        GetElementText(cookie_rule, self.EXPIRATION),
        self.ImportCookieRuleActions(cookie_rule)
        ))

    SetFile(cfg, C.COOKIE_RULES, ''.join(lines))


class SingleSignOn(CookieRule):
  """SingleSignOn does not support optional fields."""

  SINGLE_SIGN_ON = 'singleSignOn'
  PUBLIC = 'public'
  SAMPLE = 'sample'
  REDIRECT = 'redirect'
  URL = 'url'
  METHOD = 'method'
  COOKIE_ALWAYS_REDIRECT = 'cookieAlwaysRedirect'

  def Export(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_SSO]:
      return

    single_sign_on = document.StartElement(document.documentElement,
                                           self.SINGLE_SIGN_ON)
    try:
      cookie_rule = None
      for line in open(cfg.getGlobalParam(C.SSO_PATTERN_CONFIG), 'r').readlines():
        if not line.strip():
          continue
        if self.COMMENT_RE.match(line):
          continue

        url_pattern, cookie_rule_string = self.COOKIE_RULE_RE.match(line).groups()
        cookie_rule = pywrapcookierule.CookieRule()
        cookie_rule.ParseFromString(cookie_rule_string)
        AppendElementText(document, single_sign_on, self.URL_PATTERN, url_pattern)
        AppendElementText(document, single_sign_on, self.PUBLIC,
                          BoolToString(cookie_rule.isPublic()))

      # TODO(mgoodman): Add an assertion to test that all the cookie rule actions
      # and expirations were the same.
      if cookie_rule:
        self.ExportCookieRuleActions(document, cookie_rule, single_sign_on)
        AppendElementText(document, single_sign_on, self.EXPIRATION,
                          str(cookie_rule.expiration()))

      if os.stat(cfg.getGlobalParam(C.SSO_SERVING_CONFIG)).st_size == 0:
        return

      (sample_url, redirect_url, method, always_redirect) = (
          open(cfg.getGlobalParam(C.SSO_SERVING_CONFIG),
               'r').readline().split(' '))
      sample = document.StartElement(single_sign_on, self.SAMPLE)
      try:
        AppendElementText(document, sample, self.URL, sample_url)
        AppendElementText(document, sample, self.METHOD, method)
      finally:
        document.EndElement(self.SAMPLE)

      redirect = document.StartElement(single_sign_on, self.REDIRECT)
      try:
        AppendElementText(document, redirect, self.URL, redirect_url)
      finally:
        document.EndElement(self.REDIRECT)
      AppendElementText(document, single_sign_on, self.COOKIE_ALWAYS_REDIRECT,
                        BoolToString(int(always_redirect)))
    finally:
      document.EndElement(self.SINGLE_SIGN_ON)

  def Import(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_SSO]:
      return

    single_sign_on = GetChildrenElementsByTagName(document.documentElement,
                                                  self.SINGLE_SIGN_ON)

    # SingleSignOn is optional.
    if not single_sign_on:
      return

    single_sign_on = single_sign_on[0]
    actions = self.ImportCookieRuleActions(single_sign_on)
    expiration = GetChildrenElementsByTagName(single_sign_on, self.EXPIRATION)
    if expiration:
      expiration = GetText(expiration[0])
      lines = []
      for url_pattern, public in map(
        lambda x, y: (x, y),
        GetChildrenElementsByTagName(single_sign_on, self.URL_PATTERN),
        GetChildrenElementsByTagName(single_sign_on, self.PUBLIC)):
        lines.append('%s %s %s %s\n' % (
          GetText(url_pattern), expiration,
          StringToBool(GetText(public)), actions
          ))
      SetFile(cfg, C.SSO_PATTERN_CONFIG, ''.join(lines))

    sample = GetChildrenElementsByTagName(single_sign_on, self.SAMPLE)
    redirect = GetChildrenElementsByTagName(single_sign_on, self.REDIRECT)

    if not sample:
      SetFile(cfg, C.SSO_SERVING_CONFIG, '')
      return

    sample_url = GetElementText(sample[0], self.URL)
    method = GetElementText(sample[0], self.METHOD)

    # redirect didn't exist prior to 5.2, so it may not be present
    redirect_url = ''
    if redirect:
      redirect_url = GetElementText(redirect[0], self.URL)

    always_redirect_element = GetChildrenElementsByTagName(single_sign_on,
                                                  self.COOKIE_ALWAYS_REDIRECT)

    if always_redirect_element:
      always_redirect = StringToBool(GetText(always_redirect_element[0]))
    else:
      always_redirect = 0

    if always_redirect and not redirect_url:
      redirect_url = sample_url
    if always_redirect:
      sample_url = ''

    SetFile(cfg, C.SSO_SERVING_CONFIG, '%s %s %s %d\n' % (
        sample_url, redirect_url, method, always_redirect
        ))


class DuplicateHosts:
  DUPLICATE_HOSTS = 'duplicateHosts'
  CANONICAL_HOST = 'canonicalHost'
  DUPLICATES = 'duplicates'

  # TODO(mgoodman): Remove the comment from the default file.
  COMMENT_RE = re.compile(r'\s*#')

  def Export(self, document, cfg):
    duplicate_hosts = document.StartElement(document.documentElement,
                                            self.DUPLICATE_HOSTS)
    try:
      for line in open(cfg.getGlobalParam(C.DUPHOSTS), 'r').readlines():
        if not line.strip():
          continue
        if self.COMMENT_RE.match(line):
          continue

        parts = line.split()
        AppendElementText(document, duplicate_hosts, self.CANONICAL_HOST,
                          parts[0])
        AppendElementText(document, duplicate_hosts, self.DUPLICATES,
                          '\n'.join(parts[1:]))
    finally:
      document.EndElement(self.DUPLICATE_HOSTS)

  def Import(self, document, cfg):
    duplicate_hosts = GetChildrenElementsByTagName(document.documentElement,
                                                   self.DUPLICATE_HOSTS)

    # DuplicateHosts is optional.
    if not duplicate_hosts:
      return

    duplicate_hosts = duplicate_hosts[0]
    lines = []
    for canonical_host, duplicates in map(
      lambda x, y: (x, y),
      GetChildrenElementsByTagName(duplicate_hosts, self.CANONICAL_HOST),
      GetChildrenElementsByTagName(duplicate_hosts, self.DUPLICATES)):
      lines.append('%s %s\n' % (
        GetText(canonical_host),
        ' '.join(GetText(duplicates).split()) # Change newlines to spaces.
        ))
    SetFile(cfg, C.DUPHOSTS, ''.join(lines))


# TODO(mgoodman): Change to DocumentDates?
class SortByDatePatterns:
  SORT_BY_DATE_PATTERNS = 'sortByDatePatterns'
  SORT_BY_DATE_PATTERN = 'sortByDatePattern'
  URL = 'url'
  DATE_LOCATION = 'dateLocation'
  DATE_LOCATION_MAP = {
    'url'           : 'url',
    'metatag'       : 'metaTag',
    'title'         : 'title',
    'body'          : 'body',
    'last_modified' : 'lastModified'
    }
  INVERTED_DATE_LOCATION_MAP = InvertMap(DATE_LOCATION_MAP)
  META_TAG_NAME = 'metaTagName'

  def Export(self, document, cfg):
    sort_by_date_patterns = document.StartElement(document.documentElement,
                                                  self.SORT_BY_DATE_PATTERNS)
    try:
      for line in open(cfg.getGlobalParam(C.DATEPATTERNS), 'r').readlines():
        if not line.strip():
          continue

        parts = pywrap_strutil.SplitCSVLine(line)
        sort_by_date_pattern = document.StartElement(sort_by_date_patterns,
                                                     self.SORT_BY_DATE_PATTERN)
        try:
          AppendElementText(document, sort_by_date_pattern, self.URL, parts[0])
          AppendElementText(document, sort_by_date_pattern, self.DATE_LOCATION,
                            self.DATE_LOCATION_MAP[parts[1]])
          if parts[1] == 'metatag':
            AppendElementText(document, sort_by_date_pattern, self.META_TAG_NAME,
                              parts[2])
        finally:
          document.EndElement(self.SORT_BY_DATE_PATTERN)
    finally:
      document.EndElement(self.SORT_BY_DATE_PATTERNS)

  def Import(self, document, cfg):
    sort_by_date_patterns = GetChildrenElementsByTagName(
      document.documentElement, self.SORT_BY_DATE_PATTERNS)

    # SortByDatePatterns is optional.
    if not sort_by_date_patterns:
      return

    lines = []
    for sort_by_date_pattern in GetChildrenElementsByTagName(
      sort_by_date_patterns[0], self.SORT_BY_DATE_PATTERN):
      parts = [ QuoteIfNecessary(GetElementText(sort_by_date_pattern, self.URL)),
                self.INVERTED_DATE_LOCATION_MAP
                [GetElementText(sort_by_date_pattern, self.DATE_LOCATION)] ]
      if parts[1] == 'metatag':
        parts.append(QuoteIfNecessary(GetElementText(
          sort_by_date_pattern, self.META_TAG_NAME
          )))
      else:
        # The Admin Console requires three commas.
        parts.append('')
      parts.extend(['', '', ''])

      lines.append('%s\n' % ','.join(parts))
    SetFile(cfg, C.DATEPATTERNS, ''.join(lines))


class MaximumNumberOfURLsToCrawl(AbstractItem):
  ELEMENT_NAME = 'maximumNumberOfUrlsToCrawl'
  GOOGLE_CONFIG_NAME = C.USER_MAX_CRAWLED_URLS

  def ExportFilter(self, value):
    if value == None:
      return 'none'
    else:
      return str(value)

  def ImportFilter(self, value):
    if value == 'none':
      return None
    else:
      return int(value)


class DefaultHostLoad(AbstractItem):
  ELEMENT_NAME = 'defaultHostLoad'
  GOOGLE_CONFIG_NAME = C.URLSERVER_DEFAULT_HOSTLOAD

  def ExportFilter(self, value):
    return str(value)

  def ImportFilter(self, value):
    return float(value)


# TODO(mgoodman): Remove start time and end time to mean always.
# TODO(mgoodman): Fix hostload.cc to understand timezones.
class HostLoadSchedule:
  HOST_LOAD_SCHEDULE = 'hostLoadSchedule'
  HOST_LOAD = 'hostLoad'
  LOAD = 'load'
  START_TIME = 'startTime'
  END_TIME = 'endTime'
  ALL_HOSTS = 'allHosts'
  HOSTS = 'hosts'

  # Regular expression to parse a host loads line.
  START_END_LOAD_RE = re.compile(r'\[tz:(\d+)-(\d+):(\S+)\]')

  class _Key:
    def __init__(self, load, intervals, wildcard):
      self.load = load
      self.intervals = intervals
      self.wildcard = wildcard

    def __hash__(self):
      return struct.unpack('i', sha.new(
        repr(self.intervals) + repr(self.load) +
        repr(self.wildcard)).digest()[:4])[0]

    def __eq__(self, other):
      if self.intervals != other.intervals: return 0
      if self.load != other.load: return 0
      if self.wildcard != other.wildcard: return 0
      return 1

  def Export(self, document, cfg):
    load_map = OrderedDictionary.OrderedDictionary()
    host_load_schedule = document.StartElement(document.documentElement,
                                               self.HOST_LOAD_SCHEDULE)
    try:
      for line in open(cfg.getGlobalParam(C.HOSTLOADS), 'r').readlines():
        if not line.strip():
          continue

        host, parts = line.split(' ', 1)
        intervals = []
        for start_end_load in parts.strip().split(' '):
          start_time, end_time, load = self.START_END_LOAD_RE.match(
            start_end_load).groups()
          # TODO(mgoodman): Add an assertion that all the loads are the same.
          intervals.append((start_time, end_time))
        key = self._Key(load, intervals, host == '*')
        if load_map.has_key(key):
          load_map[key].append(host)
        else:
          load_map[key] = [ host ]
      for key in load_map.keys():
        host_load = document.StartElement(host_load_schedule, self.HOST_LOAD)
        try:
          AppendElementText(document, host_load, self.LOAD, key.load)
          for interval in key.intervals:
            AppendElementText(document, host_load, self.START_TIME, interval[0])
            AppendElementText(document, host_load, self.END_TIME, interval[1])
          if load_map[key] == ['*']:
            document.StartElement(host_load, self.ALL_HOSTS)
            document.EndElement(self.ALL_HOSTS)
          else:
            AppendElementText(document, host_load, self.HOSTS,
                            '\n'.join(load_map[key]))
        finally:
          document.EndElement(self.HOST_LOAD)
    finally:
      document.EndElement(self.HOST_LOAD_SCHEDULE)

  def Import(self, document, cfg):
    host_load_schedule = GetChildrenElementsByTagName(document.documentElement,
                                                      self.HOST_LOAD_SCHEDULE)

    # HostLoadSchedule is optional.
    if not host_load_schedule:
      return

    lines = []
    for host_load in GetChildrenElementsByTagName(host_load_schedule[0],
                                                  self.HOST_LOAD):
      load = GetElementText(host_load, self.LOAD)
      line = []
      for start_time, end_time in map(
        lambda x, y: (x, y),
        GetChildrenElementsByTagName(host_load, self.START_TIME),
        GetChildrenElementsByTagName(host_load, self.END_TIME)
        ):
        line.append('[tz:%s-%s:%s]' % (
          GetText(start_time), GetText(end_time), load))
      line = ' '.join(line)
      hosts = GetChildrenElementsByTagName(host_load, self.HOSTS)
      if hosts:
        for host in GetElementText(host_load, self.HOSTS).split():
          lines.append('%s %s\n' % (host, line))
      else:
        lines.append('* %s\n' % line)
    SetFile(cfg, C.HOSTLOADS, ''.join(lines))


class CrawlMoreUrlPatterns(AbstractFileItem):
  ELEMENT_NAME = 'crawlMoreUrlPatterns'
  GOOGLE_CONFIG_NAME = C.URLMANAGER_REFRESH_URLS


class CrawlLessUrlPatterns(AbstractFileItem):
  ELEMENT_NAME = 'crawlLessUrlPatterns'
  GOOGLE_CONFIG_NAME = C.URLSCHEDULER_ARCHIVE_URLS


class IgnoreLastModifiedDateForRecrawlUrlPatterns(AbstractFileItem):
  ELEMENT_NAME = 'ignoreLastModifiedDateForRecrawlUrlPatterns'
  GOOGLE_CONFIG_NAME = C.URLS_REMOTE_FETCH_ONLY


# TODO(mgoodman): Add categories if necessary.
class Collections:
  COLLECTIONS = 'collections'
  COLLECTION = 'collection'
  NAME = 'name'
  INCLUDE_URL_PATTERNS = 'includeUrlPatterns'
  DO_NOT_INCLUDE_URL_PATTERNS = 'doNotIncludeUrlPatterns'
  SERVING_PREREQUISITE_RESULTS = 'servingPrerequisiteResults'
  SERVING_PREREQUISITE = 'servingPrerequisite'
  SEARCH_TERMS = 'searchTerms'
  REQUIRED_URL = 'requiredUrl'
  MINIMUM_ESTIMATED_NUMBER_OF_RESULTS = 'minimumEstimatedNumberOfResults'

  def Export(self, document, cfg):
    collections = document.StartElement(document.documentElement,
                                self.COLLECTIONS)
    try:
      for name in ent_collection.ListCollections(cfg.globalParams):
        Get = ent_collection.EntCollection(name, cfg.globalParams).get_var
        collection = document.StartElement(collections, self.COLLECTION)
        try:
          AppendElementText(document, collection, self.NAME, name)
          AppendElementText(document, collection, self.INCLUDE_URL_PATTERNS,
                            open(Get(C.GOODURLS), 'r').read())
          AppendElementText(document, collection, self.DO_NOT_INCLUDE_URL_PATTERNS,
                            open(Get(C.BADURLS), 'r').read())
          AppendElementText(document, collection, self.SERVING_PREREQUISITE_RESULTS,
                        str(Get(C.TESTWORDS_IN_FIRST)))
          for line in open(Get(C.TESTWORDS), 'r').readlines():
            if not line.strip():
              continue

            parts = line.split('\\')
            serving_prerequisite = document.StartElement(collection,
                                                         self.SERVING_PREREQUISITE)
            try:
              AppendElementText(document, serving_prerequisite, self.SEARCH_TERMS,
                                urllib.unquote_plus(parts[0]))
              if parts[1]:
                AppendElementText(document, serving_prerequisite, self.REQUIRED_URL,
                                  urllib.unquote_plus(parts[1]))
              if parts[3]:
                AppendElementText(document, serving_prerequisite,
                                  self.MINIMUM_ESTIMATED_NUMBER_OF_RESULTS,
                                  urllib.unquote_plus(parts[3]).strip())
            finally:
              document.EndElement(self.SERVING_PREREQUISITE)
        finally:
          document.EndElement(self.COLLECTION)
    finally:
      document.EndElement(self.COLLECTIONS)

  def Import(self, document, cfg):
    collections = GetChildrenElementsByTagName(document.documentElement,
                                               self.COLLECTIONS)

    # Collections are optional.
    if not collections:
      return

    for collection_element in GetChildrenElementsByTagName(
      collections[0], self.COLLECTION):
      collection = ent_collection.EntCollection(
        GetElementText(collection_element, self.NAME), cfg.globalParams)

      # if collection exists (a patch upgrade), we only put newly added files in
      success = collection.Create(patchExisting=collection.Exists())
      assert success

      include_url_patterns = GetChildrenElementsByTagName(
        collection_element, self.INCLUDE_URL_PATTERNS)
      if include_url_patterns:
        errors = collection.set_file_var_content(
          C.GOODURLS, GetText(include_url_patterns[0]), 1)
        assert errors == validatorlib.VALID_OK

      do_not_include_url_patterns = GetChildrenElementsByTagName(
        collection_element, self.DO_NOT_INCLUDE_URL_PATTERNS)
      if do_not_include_url_patterns:
        errors = collection.set_file_var_content(
          C.BADURLS, GetText(do_not_include_url_patterns[0]), 1)
        assert errors == validatorlib.VALID_OK

      serving_prerequisite_results = GetChildrenElementsByTagName(
        collection_element, self.SERVING_PREREQUISITE_RESULTS)
      if serving_prerequisite_results:
        errors = collection.set_var(
          C.TESTWORDS_IN_FIRST, int(GetText(serving_prerequisite_results[0])), 1)
        assert errors == validatorlib.VALID_OK

      test_words = []
      for serving_prerequisite in GetChildrenElementsByTagName(
        collection_element, self.SERVING_PREREQUISITE):
        query = GetElementText(serving_prerequisite, self.SEARCH_TERMS)
        assert query
        required_url = GetChildrenElementsByTagName(serving_prerequisite,
                                                    self.REQUIRED_URL)
        if required_url:
          required_url = GetText(required_url[0])
        else:
          required_url = ''
        results = GetChildrenElementsByTagName(
          serving_prerequisite, self.MINIMUM_ESTIMATED_NUMBER_OF_RESULTS)
        if results:
          results = GetText(results[0])
        else:
          results = ''
        assert required_url or results
        test_words.append('%s\n' % '\\'.join((
          urllib.quote_plus(query), urllib.quote_plus(required_url), '',
          urllib.quote_plus(results)
          )))
      errors = collection.set_file_var_content(
        C.TESTWORDS, ''.join(test_words), 1)
      assert errors == validatorlib.VALID_OK


class FrontEnds:
  FRONT_ENDS = 'frontEnds'
  FRONT_END = 'frontEnd'
  NAME = 'name'
  DEFAULT_LANGUAGE = 'defaultLanguage'
  FORMAT = 'format'
  STYLESHEET = 'styleSheet'
  LOGO_URL = 'logoUrl'
  LOGO_WIDTH = 'logoWidth'
  LOGO_HEIGHT = 'logoHeight'
  FONT_FACE = 'fontFace'
  HEADER = 'header'
  FOOTER = 'footer'
  SEARCH_BOX_SIZE = 'searchBoxSize'
  SEARCH_BUTTON_TYPE = 'searchButtonType'
  SEARCH_BUTTON_TEXT = 'searchButtonText'
  SEARCH_BUTTON_IMAGE_URL = 'searchButtonImageUrl'
  SHOW_RES_CLUSTERS = 'showResClusters'
  RES_CLUSTER_POSITION = 'resClusterPosition'
  SHOW_ALERTS2 = 'showAlerts2'
  SHOW_COLLECTION_DROPDOWN = 'showCollectionDropDown'
  SHOW_SECURE_RADIO_BUTTON = 'showSecureRadioButton'
  SHOW_LOGO = 'showLogo'
  SHOW_ADVANCED_SEARCH_LINK = 'showAdvancedSearchLink'
  SHOW_SEARCH_TIPS_LINK = 'showSearchTipsLink'
  SHOW_TOP_SEARCH_BOX = 'showTopSearchBox'
  SHOW_SEARCH_INFORMATION = 'showSearchInformation'
  SEPARATOR_TYPE = 'separatorType'
  SEPARATOR_TYPE_MAP = {
    'ltblue'  : 'lightBlueBar',
    'blue'    : 'blueBar',
    'line'    : 'grayLine',
    'nothing' : 'none'
    }
  SEPARATOR_TYPE_INVERTED_MAP = InvertMap(SEPARATOR_TYPE_MAP)
  SHOW_TOP_NAVIGATION = 'showTopNavigation'
  SHOW_SORT_BY = 'showSortBy'
  SHOW_SNIPPET = 'showSnippet'
  SHOW_URL = 'showUrl'
  SHOW_SIZE = 'showSize'
  SHOW_DATE = 'showDate'
  SHOW_CACHE_LINK = 'showCacheLink'
  BOTTOM_NAVIGATION_TYPE = 'bottomNavigationType'
  SHOW_BOTTOM_SEARCH_BOX = 'showBottomSearchBox'
  SHOW_ASR = 'showASR'
  ANALYTICS_ACCOUNT = 'analyticsAccount'
  KEY_MATCHES = 'keyMatches'
  KEY_MATCH = 'keyMatch'
  SEARCH_TERMS = 'searchTerms'
  TYPE = 'type'
  KEY_MATCH_MAP = {
    'KeywordMatch' : 'keyword',
    'PhraseMatch'  : 'phrase',
    'ExactMatch'   : 'exact'
    }
  KEY_MATCH_INVERTED_MAP = InvertMap(KEY_MATCH_MAP)
  URL = 'url'
  TITLE = 'title'
  SYNONYMS = 'synonyms'
  SYNONYM = 'synonym'
  FILTERS = 'filters'
  DOMAIN = 'domain'
  LANGUAGE = 'language'
  FILE_TYPE = 'fileType'
  QUERY_EXPANSION = 'queryExpansion'
  SCORING_POLICY = 'scoringPolicy'
  META_TAGS = 'metaTags'
  MATCH = 'match'
  ANY = 'any'
  ALL = 'all'
  MATCH_MAP = {
    'AND' : 'all',
    'OR'  : 'any'
    }
  MATCH_INVERTED_MAP = InvertMap(MATCH_MAP)
  META_TAG = 'metaTag'
  EXISTENCE = 'existence'
  VALUE = 'value'
  META_TAG_TYPE_MAP = {
    'REQUIREDFIELDS' : 'exact',
    'PARTIALFIELDS'  : 'partial',
    'EXISTENCE'      : EXISTENCE
    }
  META_TAG_TYPE_INVERTED_MAP = InvertMap(META_TAG_TYPE_MAP)
  REMOVE_URLS = 'removeUrls'

  class ProfileKeys:
    LOGO_URL = 'logo_url'
    LOGO_WIDTH = 'logo_width'
    LOGO_HEIGHT = 'logo_height'
    GLOBAL_FONT = 'global_font'
    MY_PAGE_HEADER = 'my_page_header'
    MY_PAGE_FOOTER = 'my_page_footer'
    SEARCH_BOX_SIZE = 'search_box_size'
    CHOOSE_SEARCH_BUTTON = 'choose_search_button'
    SEARCH_BUTTON_TEXT = 'search_button_text'
    SEARCH_BUTTON_IMAGE_URL = 'search_button_image_url'
    SHOW_RES_CLUSTERS = 'show_res_clusters'
    RES_CLUSTER_POSITION = 'res_cluster_position'
    SHOW_ALERTS2 = 'showAlerts2'
    SHOW_SUBCOLLECTIONS = 'show_subcollections'
    SHOW_SECURE_RADIO_BUTTON = 'show_secure_radio_button'
    SHOW_LOGO = 'show_logo'
    SHOW_RESULT_PAGE_ADV_LINK = 'show_result_page_adv_link'
    SHOW_RESULT_PAGE_HELP_LINK = 'show_result_page_help_link'
    SHOW_TOP_SEARCH_BOX = 'show_top_search_box'
    SHOW_SEARCH_INFO = 'show_search_info'
    CHOOSE_SEP_BAR = 'choose_sep_bar'
    SHOW_TOP_NAVIGATION = 'show_top_navigation'
    SHOW_SORT_BY = 'show_sort_by'
    SHOW_RES_SNIPPET = 'show_res_snippet'
    SHOW_RES_URL = 'show_res_url'
    SHOW_RES_SIZE = 'show_res_size'
    SHOW_RES_DATE = 'show_res_date'
    SHOW_RES_CACHE = 'show_res_cache'
    CHOOSE_BOTTOM_NAVIGATION = 'choose_bottom_navigation'
    SHOW_BOTTOM_SEARCH_BOX = 'show_bottom_search_box'
    SHOW_ASR = 'show_asr'
    ANALYTICS_ACCOUNT = 'analytics_account'

  P = ProfileKeys

  def __ExportFormat(self, document, cfg, Get, front_end, profilesheet_name,
                     stylesheet_name, suffix):
    profile = Get(profilesheet_name)
    if not profile:
      return
    format = document.StartElement(front_end, self.FORMAT + suffix)
    try:
      if int(profile['stylesheet_is_edited']):
        AppendElementCDATA(document, format, self.STYLESHEET,
                           open(Get(stylesheet_name), 'r').read())

      AppendElementText(document, format, self.LOGO_URL,
                        profile[self.P.LOGO_URL])
      AppendElementText(document, format, self.LOGO_WIDTH,
                        profile[self.P.LOGO_WIDTH])
      AppendElementText(document, format, self.LOGO_HEIGHT,
                        profile[self.P.LOGO_HEIGHT])
      AppendElementText(document, format, self.FONT_FACE,
                        profile[self.P.GLOBAL_FONT])
      AppendElementCDATA(document, format, self.HEADER,
                         profile[self.P.MY_PAGE_HEADER])
      AppendElementCDATA(document, format, self.FOOTER,
                         profile[self.P.MY_PAGE_FOOTER])
      AppendElementText(document, format, self.SEARCH_BOX_SIZE,
                        profile[self.P.SEARCH_BOX_SIZE])
      AppendElementText(document, format, self.SEARCH_BUTTON_TYPE,
                        profile[self.P.CHOOSE_SEARCH_BUTTON])
      AppendElementText(document, format, self.SEARCH_BUTTON_TEXT,
                        profile[self.P.SEARCH_BUTTON_TEXT])
      AppendElementText(document, format, self.SEARCH_BUTTON_IMAGE_URL,
                        profile[self.P.SEARCH_BUTTON_IMAGE_URL])
      
      # SHOW_RES_CLUSTERS is to enable or disable search result clustering.
      # Only available in 5.0 or later; provide a default value for old profiles.
      AppendElementText(
          document, format, self.SHOW_RES_CLUSTERS,
          BoolToString(int(profile.get(self.P.SHOW_RES_CLUSTERS, 0)))
          )
      # RES_CLUSTER_POSITION is to position search result clustering when enabled.
      # Only available in 5.0 or later; provide a default value for old profiles.
      AppendElementText(
          document, format, self.RES_CLUSTER_POSITION,
          profile.get(self.P.RES_CLUSTER_POSITION, 'right')
          )

      # SHOW_ALERTS2 is to enable or disable the "My Alerts" link.  Only
      # available in 5.0 or later; provide a default value (disable it)
      # for old profiles.
      AppendElementText(
          document, format, self.SHOW_ALERTS2,
          BoolToString(int(profile.get(self.P.SHOW_ALERTS2, 0)))
          )

      AppendElementText(document, format, self.SHOW_COLLECTION_DROPDOWN,
                        BoolToString(int(profile[self.P.SHOW_SUBCOLLECTIONS])))

      if cfg.getGlobalParam(license_api.S.ENT_LICENSE_INFORMATION)[
          license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE]:
        AppendElementText(
            document, format, self.SHOW_SECURE_RADIO_BUTTON,
            BoolToString(int(profile[self.P.SHOW_SECURE_RADIO_BUTTON]))
            )

      AppendElementText(document, format, self.SHOW_LOGO,
                        BoolToString(int(profile[self.P.SHOW_LOGO])))
      AppendElementText(
        document, format, self.SHOW_ADVANCED_SEARCH_LINK,
        BoolToString(int(profile[self.P.SHOW_RESULT_PAGE_ADV_LINK]))
        )
      AppendElementText(
        document, format, self.SHOW_SEARCH_TIPS_LINK,
        BoolToString(int(profile[self.P.SHOW_RESULT_PAGE_HELP_LINK]))
        )

      AppendElementText(document, format, self.SHOW_TOP_SEARCH_BOX,
                        BoolToString(int(profile[self.P.SHOW_TOP_SEARCH_BOX])))
      AppendElementText(document, format, self.SHOW_SEARCH_INFORMATION,
                        BoolToString(int(profile[self.P.SHOW_SEARCH_INFO])))
      AppendElementText(
        document, format, self.SEPARATOR_TYPE,
        self.SEPARATOR_TYPE_MAP[profile[self.P.CHOOSE_SEP_BAR]]
        )
      AppendElementText(document, format, self.SHOW_TOP_NAVIGATION,
                        BoolToString(int(profile[self.P.SHOW_TOP_NAVIGATION])))
      AppendElementText(document, format, self.SHOW_SORT_BY,
                        BoolToString(int(profile[self.P.SHOW_SORT_BY])))
      AppendElementText(document, format, self.SHOW_SNIPPET,
                        BoolToString(int(profile[self.P.SHOW_RES_SNIPPET])))
      AppendElementText(document, format, self.SHOW_URL,
                        BoolToString(int(profile[self.P.SHOW_RES_URL])))
      AppendElementText(document, format, self.SHOW_SIZE,
                        BoolToString(int(profile[self.P.SHOW_RES_SIZE])))
      AppendElementText(document, format, self.SHOW_DATE,
                        BoolToString(int(profile[self.P.SHOW_RES_DATE])))
      AppendElementText(document, format, self.SHOW_CACHE_LINK,
                        BoolToString(int(profile[self.P.SHOW_RES_CACHE])))

      # No map needed here.
      AppendElementText(document, format, self.BOTTOM_NAVIGATION_TYPE,
                        profile[self.P.CHOOSE_BOTTOM_NAVIGATION])

      AppendElementText(
        document, format, self.SHOW_BOTTOM_SEARCH_BOX,
        BoolToString(int(profile.get(self.P.SHOW_BOTTOM_SEARCH_BOX, '1')))
        )

      AppendElementText(
        document, format, self.SHOW_ASR,
        BoolToString(int(profile.get(self.P.SHOW_ASR, '1')))
        )

      AppendElementText(document, format, self.ANALYTICS_ACCOUNT,
                        profile.get(self.P.ANALYTICS_ACCOUNT, ''))
    finally:
      document.EndElement(self.FORMAT + suffix)

  LANGUAGES = [ 'fr', 'de', 'it', 'ja', 'es' ]

  def Export(self, document, cfg):
    front_ends = document.StartElement(document.documentElement,
                               self.FRONT_ENDS)
    try:
      for name in ent_collection.ListFrontends(cfg.globalParams):
        Get = ent_collection.EntFrontend(name, cfg.globalParams).get_var
        front_end = document.StartElement(front_ends, self.FRONT_END)
        try:
          AppendElementText(document, front_end, self.NAME, name)

          default_language = Get('DEFAULT_LANGUAGE')
          if default_language:
            AppendElementText(document, front_end, self.DEFAULT_LANGUAGE,
                              Get('DEFAULT_LANGUAGE'))

          self.__ExportFormat(document, cfg, Get, front_end, C.PROFILESHEET,
                              C.STYLESHEET, '')
          for lang in self.LANGUAGES:
            self.__ExportFormat(document, cfg, Get, front_end,
                                'PROFILESHEET.%s' % lang, 'STYLESHEET.%s' % lang,
                                '.%s' % lang)

          # KeyMatches
          key_matches = document.StartElement(front_end, self.KEY_MATCHES)
          try:
            for line in open(Get(C.GOOGLEMATCH), 'r').readlines():
              if not line.strip():
                continue

              parts = pywrap_strutil.SplitCSVLine(line)
              assert len(parts) == 4
              key_match = document.StartElement(key_matches, self.KEY_MATCH)
              try:
                AppendElementText(document, key_match, self.SEARCH_TERMS, parts[0])
                AppendElementText(document, key_match, self.TYPE,
                                  self.KEY_MATCH_MAP[parts[1]])
                AppendElementText(document, key_match, self.URL, parts[2])
                AppendElementText(document, key_match, self.TITLE, parts[3])
              finally:
                document.EndElement(self.KEY_MATCH)
          finally:
            document.EndElement(self.KEY_MATCHES)

          # Synonyms
          synonyms = document.StartElement(front_end, self.SYNONYMS)
          try:
            for line in open(Get(C.SYNONYMS), 'r').readlines():
              # All UFE pages are suspect.
              if not line.strip():
                continue

              parts = pywrap_strutil.SplitCSVLine(line)
              assert len(parts) == 2
              AppendElementText(document, synonyms, self.SEARCH_TERMS, parts[0])
              AppendElementText(document, synonyms, self.SYNONYM, parts[1])
          finally:
            document.EndElement(self.SYNONYMS)

          # Filters
          filters = document.StartElement(front_end, self.FILTERS)
          try:
            AppendElementText(document, filters, self.DOMAIN,
                              open(Get(C.DOMAIN_FILTER), 'r').read())

            AppendElementText(
              document, filters, self.LANGUAGE, '\n'.join(map(
              lambda x: x[len('lang_'):],
              open(Get(C.LANGUAGE_FILTER), 'r').read().strip().split(' ')
              )))

            AppendElementText(document, filters, self.FILE_TYPE,
                              open(Get(C.FILETYPE_FILTER), 'r').read())

            AppendElementText(document, filters, self.QUERY_EXPANSION,
                              open(Get(C.QUERY_EXPANSION_FILTER), 'r').read())
            AppendElementText(document, filters, self.SCORING_POLICY,
                              open(Get(C.SCORING_POLICY_FILTER), 'r').read())

            meta_tags = document.StartElement(filters, self.META_TAGS)
            try:
              meta_tags_match = self.ANY
              for line in open(Get(C.METATAG_FILTER), 'r').readlines():
                if not line.strip():
                  continue
                parts = pywrap_strutil.SplitCSVLine(line)
                meta_tags_match = self.MATCH_MAP[parts[0]]
              AppendElementText(document, meta_tags, self.MATCH, meta_tags_match)

              for line in open(Get(C.METATAG_FILTER), 'r').readlines():
                if not line.strip():
                  continue

                parts = pywrap_strutil.SplitCSVLine(line)
                meta_tags_match = self.MATCH_MAP[parts[0]]
                meta_tag = document.StartElement(meta_tags, self.META_TAG)
                try:
                  AppendElementText(document, meta_tag, self.NAME, parts[2])
                  type_text = self.META_TAG_TYPE_MAP[parts[1]]
                  AppendElementText(document, meta_tag, self.TYPE, type_text)
                  if type_text != self.EXISTENCE:
                    AppendElementText(document, meta_tag, self.VALUE, parts[3])
                finally:
                  document.EndElement(self.META_TAG)
            finally:
              document.EndElement(self.META_TAGS)
          finally:
            document.EndElement(self.FILTERS)

          # Remove URLs
          AppendElementText(document, front_end, self.REMOVE_URLS,
                            open(Get(C.BADURLS_NORETURN), 'r').read())
        finally:
          document.EndElement(self.FRONT_END)
    finally:
      document.EndElement(self.FRONT_ENDS)

  def __SetProfile(self, node, name, dict, key, filter=lambda x: x):
    elements = GetChildrenElementsByTagName(node, name)
    if elements:
      dict[key] = filter(GetText(elements[0]))

  def __ImportFormat(self, cfg, front_end, format, language, profilesheet_name,
                     stylesheet_name):
    format = format[0]

    profile = front_end.GetProfile(language)

    stylesheet = GetChildrenElementsByTagName(
      format, self.STYLESHEET)
    if stylesheet:
      profile['stylesheet_is_edited'] = '1'

      errors = front_end.set_file_var_content(
        stylesheet_name, GetText(stylesheet[0]), 1)
      assert errors == validatorlib.VALID_OK

    self.__SetProfile(format, self.LOGO_URL, profile, self.P.LOGO_URL)
    self.__SetProfile(format, self.LOGO_WIDTH, profile, self.P.LOGO_WIDTH)
    self.__SetProfile(format, self.LOGO_HEIGHT, profile,
                      self.P.LOGO_HEIGHT)
    self.__SetProfile(format, self.FONT_FACE, profile, self.P.GLOBAL_FONT)
    self.__SetProfile(format, self.HEADER, profile, self.P.MY_PAGE_HEADER)
    self.__SetProfile(format, self.FOOTER, profile, self.P.MY_PAGE_FOOTER)
    self.__SetProfile(format, self.SEARCH_BOX_SIZE, profile,
                      self.P.SEARCH_BOX_SIZE)
    self.__SetProfile(format, self.SEARCH_BUTTON_TYPE, profile,
                      self.P.CHOOSE_SEARCH_BUTTON)
    self.__SetProfile(format, self.SEARCH_BUTTON_TEXT, profile,
                      self.P.SEARCH_BUTTON_TEXT)
    self.__SetProfile(format, self.SEARCH_BUTTON_IMAGE_URL, profile,
                      self.P.SEARCH_BUTTON_IMAGE_URL)
    self.__SetProfile(format, self.SHOW_RES_CLUSTERS, profile,
                      self.P.SHOW_RES_CLUSTERS, StringToBoolStr)
    self.__SetProfile(format, self.RES_CLUSTER_POSITION, profile,
                      self.P.RES_CLUSTER_POSITION)
    self.__SetProfile(format, self.SHOW_ALERTS2, profile,
                      self.P.SHOW_ALERTS2, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_COLLECTION_DROPDOWN, profile,
                      self.P.SHOW_SUBCOLLECTIONS, StringToBoolStr)
    if cfg.globalParams.var_copy(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE]:
      self.__SetProfile(format, self.SHOW_SECURE_RADIO_BUTTON, profile,
                        self.P.SHOW_SECURE_RADIO_BUTTON, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_LOGO, profile, self.P.SHOW_LOGO,
                      StringToBoolStr)
    self.__SetProfile(format, self.SHOW_ADVANCED_SEARCH_LINK, profile,
                      self.P.SHOW_RESULT_PAGE_ADV_LINK, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_SEARCH_TIPS_LINK, profile,
                      self.P.SHOW_RESULT_PAGE_HELP_LINK, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_TOP_SEARCH_BOX, profile,
                      self.P.SHOW_TOP_SEARCH_BOX, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_SEARCH_INFORMATION, profile,
                      self.P.SHOW_SEARCH_INFO, StringToBoolStr)
    self.__SetProfile(format, self.SEPARATOR_TYPE, profile,
                      self.P.CHOOSE_SEP_BAR,
                      lambda x, y=self.SEPARATOR_TYPE_INVERTED_MAP: y[x])
    self.__SetProfile(format, self.SHOW_TOP_NAVIGATION, profile,
                      self.P.SHOW_TOP_NAVIGATION, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_SORT_BY, profile,
                      self.P.SHOW_SORT_BY, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_SNIPPET, profile,
                      self.P.SHOW_RES_SNIPPET, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_URL, profile, self.P.SHOW_RES_URL,
                      StringToBoolStr)
    self.__SetProfile(format, self.SHOW_SIZE, profile,
                      self.P.SHOW_RES_SIZE, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_DATE, profile,
                      self.P.SHOW_RES_DATE, StringToBoolStr)
    self.__SetProfile(format, self.SHOW_CACHE_LINK, profile,
                      self.P.SHOW_RES_CACHE, StringToBoolStr)

    # No map needed here.
    self.__SetProfile(format, self.BOTTOM_NAVIGATION_TYPE, profile,
                      self.P.CHOOSE_BOTTOM_NAVIGATION)

    self.__SetProfile(format, self.SHOW_BOTTOM_SEARCH_BOX, profile,
                      self.P.SHOW_BOTTOM_SEARCH_BOX, StringToBoolStr)

    try:
      self.__SetProfile(format, self.SHOW_ASR, profile,
                        self.P.SHOW_ASR, StringToBoolStr)
    except AttributeError:
      profile['show_asr'] = '0'

    try:
      self.__SetProfile(format, self.ANALYTICS_ACCOUNT, profile,
                        self.P.ANALYTICS_ACCOUNT)
    except AttributeError:
      profile['analytics_account'] = ''

    errors = front_end.set_var(profilesheet_name, profile, 0)
    assert errors == validatorlib.VALID_OK

    if not stylesheet:
      front_end.GenerateStylesheet(isTest=0)

  def Import(self, document, cfg):
    front_ends = GetChildrenElementsByTagName(document.documentElement,
                                              self.FRONT_ENDS)

    # Front ends are optional.
    if not front_ends:
      return

    for front_end_element in GetChildrenElementsByTagName(
      front_ends[0], self.FRONT_END):
      front_end = ent_collection.EntFrontend(
        GetText(GetChildrenElementsByTagName(front_end_element, self.NAME)[0]),
        cfg.globalParams)

      # if frontend exists (a patch upgrade), we only put newly added files in.
      success = front_end.Create(patchExisting=front_end.Exists())
      assert success

      # Output format
      default_language = GetChildrenElementsByTagName(
        front_end_element, self.DEFAULT_LANGUAGE)
      if default_language:
        default_language = GetText(default_language[0])
      else:
        default_language = 'en'

      errors = front_end.set_var(
        'DEFAULT_LANGUAGE', default_language)
      assert errors == validatorlib.VALID_OK

      GetProfile = front_end.GetProfile
      format = GetChildrenElementsByTagName(
        front_end_element, self.FORMAT)
      if format:
        self.__ImportFormat(cfg, front_end, format, 'en',
                            C.PROFILESHEET, C.STYLESHEET)

      for lang in self.LANGUAGES:
        format = GetChildrenElementsByTagName(
          front_end_element, '%s.%s' % (self.FORMAT, lang))
        if format:
          # Add the key.
          front_end.set_var('STYLESHEET.%s' % lang,
                            '%s.%s' % (front_end.get_var('STYLESHEET'), lang))

          self.__ImportFormat(cfg, front_end, format, lang,
                              'PROFILESHEET.%s' % lang, 'STYLESHEET.%s' % lang)

      # KeyMatches
      key_matches = GetChildrenElementsByTagName(front_end_element,
                                                 self.KEY_MATCHES)
      if key_matches:
        lines = []
        for key_match in GetChildrenElementsByTagName(key_matches[0],
                                                      self.KEY_MATCH):
          lines.append('%s,%s,%s,%s\n' % (
            QuoteIfNecessary(GetElementText(key_match, self.SEARCH_TERMS)),
            QuoteIfNecessary(self.KEY_MATCH_INVERTED_MAP
                             [GetElementText(key_match, self.TYPE)]),
            QuoteIfNecessary(GetElementText(key_match, self.URL)),
            QuoteIfNecessary(GetElementText(key_match, self.TITLE))
            ))
        errors = front_end.set_file_var_content(
            C.GOOGLEMATCH, ''.join(lines), 1)
        assert errors == validatorlib.VALID_OK

      # Synonyms
      synonyms = GetChildrenElementsByTagName(front_end_element, self.SYNONYMS)
      if synonyms:
        synonyms = synonyms[0]
        lines = []
        for query, synonym in map(
          lambda x, y: (x, y),
          GetChildrenElementsByTagName(synonyms, self.SEARCH_TERMS),
          GetChildrenElementsByTagName(synonyms, self.SYNONYM)
          ):
          lines.append('%s,%s\n' % (
            QuoteIfNecessary(GetText(query)),
            QuoteIfNecessary(GetText(synonym))
            ))
        errors = front_end.set_file_var_content(
            C.SYNONYMS, ''.join(lines), 1)
        assert errors == validatorlib.VALID_OK

      # Filters
      filters = GetChildrenElementsByTagName(front_end_element, self.FILTERS)
      if filters:
        filters = filters[0]
        domain = GetChildrenElementsByTagName(filters, self.DOMAIN)
        if domain:
          errors = front_end.set_file_var_content(
            C.DOMAIN_FILTER, GetText(domain[0]), 1)
          assert errors == validatorlib.VALID_OK

        language = GetChildrenElementsByTagName(
          filters, self.LANGUAGE)
        if language:
          errors = front_end.set_file_var_content(
            C.LANGUAGE_FILTER, ' '.join(map(
            lambda x: 'lang_%s' % x,
            GetText(language[0]).split()
            )), 1)
          assert errors == validatorlib.VALID_OK

        file_type = GetChildrenElementsByTagName(
          filters, self.FILE_TYPE)
        if file_type:
          errors = front_end.set_file_var_content(
            C.FILETYPE_FILTER, GetText(file_type[0]), 1)
          assert errors == validatorlib.VALID_OK

        query_expansion = GetChildrenElementsByTagName(
          filters, self.QUERY_EXPANSION)
        if query_expansion:
          errors = front_end.set_file_var_content(
            C.QUERY_EXPANSION_FILTER, GetText(query_expansion[0]), 1)
          assert errors == validatorlib.VALID_OK
        else:
          # Set to a default policy. This is included mainly for importing
          # configurations during migration from earlier versions.
          query_expansion = 'QE_NONE'

        scoring_policy = GetChildrenElementsByTagName(
          filters, self.SCORING_POLICY)
        if scoring_policy:
          errors = front_end.set_file_var_content(
            C.SCORING_POLICY_FILTER, GetText(scoring_policy[0]), 1)
          assert errors == validatorlib.VALID_OK
        else:
          scoring_policy = '0'

        meta_tags = GetChildrenElementsByTagName(filters, self.META_TAGS)
        if meta_tags:
          meta_tags = meta_tags[0]
          match = GetChildrenElementsByTagName(meta_tags, self.MATCH)
          if match:
            match = self.MATCH_INVERTED_MAP[GetText(match[0])]
          else:
            match = 'OR'
          lines = []
          for meta_tag in GetChildrenElementsByTagName(meta_tags, self.META_TAG):
            type_text = GetElementText(meta_tag, self.TYPE)
            if type_text == self.EXISTENCE:
              value = ''
            else:
              value = QuoteIfNecessary(GetElementText(meta_tag, self.VALUE))
            lines.append('%s,%s,%s,%s\n' % (
              match,
              self.META_TAG_TYPE_INVERTED_MAP[type_text],
              QuoteIfNecessary(GetElementText(meta_tag, self.NAME)),
              value
              ))
          errors = front_end.set_file_var_content(
            C.METATAG_FILTER, ''.join(lines), 1)
          assert errors == validatorlib.VALID_OK

      # Remove URLs
      remove_urls = GetChildrenElementsByTagName(front_end_element,
                                                 self.REMOVE_URLS)
      if remove_urls:
        errors = front_end.set_file_var_content(
          C.BADURLS_NORETURN, GetText(remove_urls[0]), 1)
        assert errors == validatorlib.VALID_OK


class QueryExpansion:
  QUERY_EXP_ENTRIES = 'queryexpansion'
  LANGUAGES = 'languages'
  QUERY_EXP_ENTRY = 'queryExpEntry'
  NAME = 'name'
  CONTENT = 'content'
  ENTRY_COUNT = 'entryCount'
  ENTRY_NAME = 'entryName'
  ENTRY_TYPE = 'entryType'
  CREATION_DATE = 'creationDate'
  ENABLED = 'enabled'
  ORIGINAL_FILE = 'originalFile'
  DELETABLE = 'deletable'
  DOWNLOADABLE = 'downloadable'
  ENTRY_LANGUAGE = 'entryLanguage'

  def Export(self, document, cfg):
    qe_entries = document.StartElement(document.documentElement,
                                       self.QUERY_EXP_ENTRIES)
    try:
      AppendElementText(document, qe_entries, self.LANGUAGES,
                        cfg.getGlobalParam(C.QUERY_EXP_LANGS))
      for name in ent_collection.ListQueryExpEntries(cfg.globalParams):
        Get = ent_collection.EntQueryExp(name, cfg.globalParams).get_var
        entry = document.StartElement(qe_entries, self.QUERY_EXP_ENTRY)
        try:
          AppendElementText(document, entry, self.NAME, name)

          # Output the non-file entries
          AppendElementText(document, entry, self.ENTRY_COUNT,
                            str(Get('ENTRY_COUNT')))
          AppendElementText(document, entry, self.ENTRY_NAME,
                            Get('ENTRY_NAME'))
          AppendElementText(document, entry, self.ENTRY_TYPE,
                            str(Get('ENTRY_TYPE')))
          AppendElementText(document, entry, self.CREATION_DATE,
                            str(Get('CREATION_DATE')))
          AppendElementText(document, entry, self.ENABLED,
                            str(Get('ENABLED')))
          AppendElementText(document, entry, self.ORIGINAL_FILE,
                            Get('ORIGINAL_FILE'))
          if int(Get('DELETABLE')):
            # If the file is not deletable, it is distributed with the GSA
            # software, and we do not want to export its contents, just the
            # 'ENABLED' status.
            AppendElementCDATA(document, entry, self.CONTENT,
                              open(Get('CONTENT'), 'r').read())

          AppendElementText(document, entry, self.DELETABLE,
                            str(Get('DELETABLE')))
          AppendElementText(document, entry, self.DOWNLOADABLE,
                            str(Get('DOWNLOADABLE')))
          AppendElementText(document, entry, self.ENTRY_LANGUAGE,
                            Get('ENTRY_LANGUAGE'))
        finally:
          document.EndElement(self.QUERY_EXP_ENTRY)
    finally:
      document.EndElement(self.QUERY_EXP_ENTRIES)

  def Import(self, document, cfg):
    # Fixed bug 239039 on patch upgrade. Note that this is called
    # in adminrunner.StartupWork as well. So this method is called
    # twice for a version-crossing upgrade. That's harmless, but we
    # should sort this out later.
    cfg.CreateDefaultQueryExpEntry()

    qe_entries = GetChildrenElementsByTagName(document.documentElement,
                                              self.QUERY_EXP_ENTRIES)

    if not qe_entries:
      return

    try:
      qe_langs = GetElementText(qe_entries[0], self.LANGUAGES)
      if qe_langs:
        cfg.setGlobalParam(C.QUERY_EXP_LANGS, qe_langs.strip())
    except IndexError:
      # This will happen when importing from a version which does not
      # have the languages element, in which case we will get the default
      # language list already in the config.
      pass

    for entry_element in GetChildrenElementsByTagName(
      qe_entries[0], self.QUERY_EXP_ENTRY):
      entry = ent_collection.EntQueryExp(
        GetElementText(entry_element, self.NAME), cfg.globalParams)

      # if language exists (a patch upgrade), we only put newly added files in
      success = entry.Create(patchExisting=entry.Exists())
      assert success

      entry_count = GetChildrenElementsByTagName(
        entry_element, self.ENTRY_COUNT)
      if entry_count:
        errors = entry.set_var(C.ENTRY_COUNT, int(GetText(entry_count[0])), 1)
        assert errors == validatorlib.VALID_OK

      entry_name = GetChildrenElementsByTagName(entry_element, self.ENTRY_NAME)
      if entry_name:
        errors = entry.set_var(C.ENTRY_NAME, GetText(entry_name[0]), 1)
        assert errors == validatorlib.VALID_OK

      entry_type = GetChildrenElementsByTagName(entry_element, self.ENTRY_TYPE)
      if entry_type:
        errors = entry.set_var(C.ENTRY_TYPE, int(GetText(entry_type[0])), 1)
        assert errors == validatorlib.VALID_OK

      creation_date = GetChildrenElementsByTagName(
        entry_element, self.CREATION_DATE)
      if creation_date:
        errors = entry.set_var(C.CREATION_DATE,
                               long(GetText(creation_date[0])), 1)
        assert errors == validatorlib.VALID_OK

      enabled = GetChildrenElementsByTagName(entry_element, self.ENABLED)
      if enabled:
        errors = entry.set_var(C.ENABLED, int(GetText(enabled[0])), 1)
        assert errors == validatorlib.VALID_OK

      original_file = GetChildrenElementsByTagName(
        entry_element, self.ORIGINAL_FILE)
      if original_file:
        errors = entry.set_var(C.ORIGINAL_FILE, GetText(original_file[0]), 1)
        assert errors == validatorlib.VALID_OK

      # For permanent files, this will not exist.
      content = GetChildrenElementsByTagName(entry_element, self.CONTENT)
      if content:
        errors = entry.set_file_var_content(C.CONTENT, GetText(content[0]), 1)
        assert errors == validatorlib.VALID_OK

      deletable = GetChildrenElementsByTagName(entry_element, self.DELETABLE)
      if deletable:
        errors = entry.set_var(C.DELETABLE, int(GetText(deletable[0])), 1)
        assert errors == validatorlib.VALID_OK

      downloadable = GetChildrenElementsByTagName(
        entry_element, self.DOWNLOADABLE)
      if downloadable:
        errors = entry.set_var(
          C.DOWNLOADABLE, int(GetText(downloadable[0])), 1)
        assert errors == validatorlib.VALID_OK

      language = GetChildrenElementsByTagName(entry_element,
                                              self.ENTRY_LANGUAGE)
      if language:
        errors = entry.set_var(C.ENTRY_LANGUAGE, GetText(language[0]), 1)
        assert errors == validatorlib.VALID_OK

      language = GetChildrenElementsByTagName(entry_element,
                                              self.ENTRY_LANGUAGE)
      if language:
        errors = entry.set_var(C.ENTRY_LANGUAGE, GetText(language[0]), 1)
        assert errors == validatorlib.VALID_OK

    cfg.setGlobalParam(C.QUERY_EXP_STATUS,
      int(C.QUERY_EXP_STATUS_NEEDS_APPLY))

class AbstractIntItem(AbstractItem):
  def ExportFilter(self, value):
    return str(value)

  def ImportFilter(self, value):
    return int(value)


class AuthorizationCacheEntryDuration(AbstractIntItem):
  ELEMENT_NAME = 'authorizationCacheEntryDuration'
  GOOGLE_CONFIG_NAME = C.HEADREQUESTOR_CACHE_ENTRY_TIMEOUT


class AbstractBooleanItem(AbstractItem):
  def ExportFilter(self, value):
    return BoolToString(value)

  def ImportFilter(self, value):
    return StringToBool(value)


class Clicklogging(AbstractIntItem):
  ELEMENT_NAME = 'clickLogging'
  GOOGLE_CONFIG_NAME = C.CLICKLOGGING


class Alerts2(AbstractIntItem):
  ELEMENT_NAME = 'alerts2'
  GOOGLE_CONFIG_NAME = C.ALERTS2


class UseDhcp(AbstractBooleanItem):
  ELEMENT_NAME = 'useDhcp'
  GOOGLE_CONFIG_NAME = C.USE_DHCP


class DnsDhcp(AbstractBooleanItem):
  ELEMENT_NAME = 'dnsDhcp'
  GOOGLE_CONFIG_NAME = C.DNS_DHCP


class CrawlIpAddress(AbstractItem):
  ELEMENT_NAME = 'crawlIpAddress'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_CRAWL_IP


class ServeIpAddress(AbstractItem):
  ELEMENT_NAME = 'serveIpAddress'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_WEB_IP


class ServeIpPort(AbstractItem):
  ELEMENT_NAME = 'serveIpPort'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_WEB_PORT


class SwitchIpAddress(AbstractItem):
  ELEMENT_NAME = 'switchIpAddress'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_SWITCH_IP


class SubnetMask(AbstractItem):
  ELEMENT_NAME = 'subnetMask'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_NETMASK


class GatewayIpAddress(AbstractItem):
  ELEMENT_NAME = 'gatewayIpAddress'
  GOOGLE_CONFIG_NAME = C.EXTERNAL_DEFAULT_ROUTE


class NetworkSpeedDuplex(AbstractIntItem):
  ELEMENT_NAME = 'networkSpeedDuplex'
  GOOGLE_CONFIG_NAME = C.ONEBOX_NETCARD_SETTINGS


class ServerironAutonegotiation(AbstractIntItem):
  ELEMENT_NAME = 'serverironAutonegotiation'
  GOOGLE_CONFIG_NAME = C.SERVERIRON_AUTONEGOTIATION


class TimeZone(AbstractItem):
  ELEMENT_NAME = 'timeZone'
  GOOGLE_CONFIG_NAME = C.TIMEZONE


class AbstractCommaSeparatedItem(AbstractItem):
  def ExportFilter(self, value):
    return '\n'.join(value.split(','))

  def ImportFilter(self, value):
    return ','.join(value.split())


class DnsServers(AbstractCommaSeparatedItem):
  ELEMENT_NAME = 'dnsServers'
  GOOGLE_CONFIG_NAME = C.BOT_DNS_SERVERS


class DnsSuffixes(AbstractCommaSeparatedItem):
  ELEMENT_NAME = 'dnsSuffixes'
  GOOGLE_CONFIG_NAME = C.DNS_SEARCH_PATH


class SmtpServer(AbstractItem):
  ELEMENT_NAME = 'smtpServer'
  GOOGLE_CONFIG_NAME = C.SMTP_SERVER


class AbstractListItem(AbstractItem):
  def ExportFilter(self, value):
    return '\n'.join(value)

  def ImportFilter(self, value):
    return value.split()


class NtpServers(AbstractListItem):
  ELEMENT_NAME = 'ntpServers'
  GOOGLE_CONFIG_NAME = C.NTP_SERVERS


class AbstractNoneOrStringItem(AbstractItem):
  def ImportFilter(self, value):
    if not value:
      return None
    else:
      return value


class SyslogServer(AbstractNoneOrStringItem):
  ELEMENT_NAME = 'syslogServer'
  GOOGLE_CONFIG_NAME = C.SYSLOG_SERVER


class SyslogFacilityUsageLogs(AbstractNoneOrStringItem):
  ELEMENT_NAME = 'syslogFacilityUsageLogs'
  GOOGLE_CONFIG_NAME = C.ENT_SYSLOG_GWS_FAC


class AutomaticReportEmailRecipient(AbstractItem):
  ELEMENT_NAME = 'automaticReportEmailRecipient'
  GOOGLE_CONFIG_NAME = C.NOTIFICATION_EMAIL


class ProblemReportEmailRecipient(AbstractItem):
  ELEMENT_NAME = 'problemReportEmailRecipient'
  GOOGLE_CONFIG_NAME = C.PROBLEM_EMAIL


class EmailSender(AbstractItem):
  ELEMENT_NAME = 'emailSender'
  GOOGLE_CONFIG_NAME = C.OUTGOING_EMAIL_SENDER


class DefaultSearchUrl(AbstractItem):
  ELEMENT_NAME = 'defaultSearchUrl'
  GOOGLE_CONFIG_NAME = C.DEFAULT_SEARCH_URL


class EnableSsh(AbstractBooleanItem):
  ELEMENT_NAME = 'enableSsh'
  GOOGLE_CONFIG_NAME = C.ENT_ENABLE_EXTERNAL_SSH

class EnableBorgmon(AbstractBooleanItem):
  ELEMENT_NAME = 'enableBorgmon'
  GOOGLE_CONFIG_NAME = C.ENT_ENABLE_EXTERNAL_BORGMON

class EnableSnmp(AbstractBooleanItem):
  ELEMENT_NAME = 'enableSnmp'
  GOOGLE_CONFIG_NAME = C.ENT_ENABLE_SNMP

class SnmpUsers(AbstractItem):
  ELEMENT_NAME = 'snmpUsers'
  GOOGLE_CONFIG_NAME = C.SNMP_USERS

class SnmpCommunities(AbstractItem):
  ELEMENT_NAME = 'snmpCommunities'
  GOOGLE_CONFIG_NAME = C.SNMP_COMMUNITIES

class SnmpTrapsHost(AbstractItem):
  ELEMENT_NAME = 'snmpTrapsHost'
  GOOGLE_CONFIG_NAME = C.SNMP_TRAPS_HOST

class SnmpTrapsCommunity(AbstractItem):
  ELEMENT_NAME = 'snmpTrapsCommunity'
  GOOGLE_CONFIG_NAME = C.SNMP_TRAPS_COMMUNITY

class SnmpTraps(AbstractItem):
  ELEMENT_NAME = 'snmpTraps'
  GOOGLE_CONFIG_NAME = C.SNMP_TRAPS

class DailyStatusReport(AbstractBooleanItem):
  ELEMENT_NAME = 'dailyStatusReport'
  GOOGLE_CONFIG_NAME = C.SEND_ENTERPRISE_STATUS_REPORT

class Users:
  USERS = 'users'
  USER = 'user'
  NAME = 'name'
  PASSWORD = 'password'
  SALT = 'salt'
  EMAIL = 'email'
  ROLE = 'role'
  ROLE_MAP = {
    user_manager.SUPERUSER : 'superuser',
    user_manager.MANAGER : 'manager'
    }
  ROLE_INVERTED_MAP = InvertMap(ROLE_MAP)
  COLLECTIONS = 'collections'
  COLLECTION_PREFIX = '+'
  FRONT_ENDS = 'frontEnds'
  FRONT_END_PREFIX = '!'

  def Export(self, document, cfg):
    users = document.StartElement(document.documentElement, self.USERS)
    try:
      for user in cfg.um.getAllUserData().values():
        user_element = document.StartElement(users, self.USER)
        try:
          AppendElementText(document, user_element, self.NAME, user.name)
          AppendElementText(document, user_element, self.PASSWORD, user.passwd)
          AppendElementText(document, user_element, self.SALT, user.salt)
          AppendElementText(document, user_element, self.EMAIL, user.email)
          AppendElementText(document, user_element, self.ROLE,
                            self.ROLE_MAP[user.accountType])
          permissions = user.permissions
          if permissions == ['']:
            permissions = []
          AppendElementText(document, user_element, self.COLLECTIONS, '\n'.join(
            [x[1:] for x in permissions if x[0] == self.COLLECTION_PREFIX]))
          AppendElementText(document, user_element, self.FRONT_ENDS, '\n'.join(
            [x[1:] for x in permissions if x[0] == self.FRONT_END_PREFIX]))
        finally:
          document.EndElement(self.USER)
    finally:
      document.EndElement(self.USERS)

  def Import(self, document, cfg):
    users = GetChildrenElementsByTagName(document.documentElement, self.USERS)

    # Users are optional.
    if not users:
      return

    user_map = OrderedDictionary.OrderedDictionary()
    for line in open(cfg.getGlobalParam(C.PASSWORD_FILE)).readlines():
      if not line.strip():
        continue

      parts = line.split(' ')
      user_map[parts[0]] = parts

    users = users[0]
    for user in GetChildrenElementsByTagName(users, self.USER):
      # Ignore existing users.
      name = GetElementText(user, self.NAME)
      if user_map.has_key(name):
        continue

      collections = GetChildrenElementsByTagName(user, self.COLLECTIONS)
      if collections:
        collections = GetText(collections[0]).split('\n')
      if collections == ['']:
        collections = []

      front_ends = GetChildrenElementsByTagName(user, self.FRONT_ENDS)
      if front_ends:
        front_ends = GetText(front_ends[0]).split('\n')
      if front_ends == ['']:
        front_ends = []

      user_map[name] = (
        name, GetElementText(user, self.PASSWORD),
        GetElementText(user, self.SALT), name, GetElementText(user, self.EMAIL),
        self.ROLE_INVERTED_MAP[GetElementText(user, self.ROLE)],
        ' '.join(['%s%s' % (self.COLLECTION_PREFIX, x) for x in collections] +
                 ['%s%s' % (self.FRONT_END_PREFIX, x) for x in front_ends])
        )
      SetFile(cfg, C.PASSWORD_FILE, ''.join(
        ['%s\n' % ' '.join(x) for x in user_map.values()]))


class AutoCompleteOff(AbstractBooleanItem):
  ELEMENT_NAME = 'autoCompleteOff'
  GOOGLE_CONFIG_NAME = C.AUTOCOMPLETE_OFF

class SslCertificateAndPrivateKey:
  SSL_CERTIFICATE = 'sslCertificate'
  SSL_PRIVATE_KEY = 'sslPrivateKey'

  def Export(self, document, cfg):
    AppendElementText(
      document,
      document.documentElement,
      self.SSL_CERTIFICATE,
      open(os.path.join(cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_DIR),
                        cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_FILE)),
           'r').read()
      )
    AppendElementText(
      document,
      document.documentElement,
      self.SSL_PRIVATE_KEY,
      open(os.path.join(cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_DIR),
                        cfg.getGlobalParam(C.BOT_SSL_KEY_FILE)),
           'r').read()
      )

  # Since the locations are not currently versioned, this is effectively a no-op
  # during version migration.
  def Import(self, document, cfg):
    ssl_certificate = GetChildrenElementsByTagName(
      document.documentElement, self.SSL_CERTIFICATE)

    # An SSL certificate is optional.
    if not ssl_certificate:
      return

    open(os.path.join(cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_DIR),
                      cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_FILE)),
         'w').write(GetText(ssl_certificate[0]))
    open(os.path.join(cfg.getGlobalParam(C.BOT_SSL_CERTIFICATE_DIR),
                      cfg.getGlobalParam(C.BOT_SSL_KEY_FILE)),
         'w').write(GetElementText(document.documentElement,
                                   self.SSL_PRIVATE_KEY))

    # Generate the PKCS#12 format certificate.
    ssl_cert.MakeJavaCert(cfg.entHome)


class RedirectHttps:
  REDIRECT_HTTPS = 'redirectHttps'
  REDIRECT_HTTPS_MAP = {
    0 : 'no',
    1 : 'secure',
    2 : 'always'
    }
  REDIRECT_HTTPS_INVERTED_MAP = InvertMap(REDIRECT_HTTPS_MAP)

  def Export(self, document, cfg):
    AppendElementText(
      document,
      document.documentElement,
      self.REDIRECT_HTTPS,
      self.REDIRECT_HTTPS_MAP[cfg.getGlobalParam(C.FORCE_HTTPS)]
      )

  def Import(self, document, cfg):
    redirect_https = GetChildrenElementsByTagName(
      document.documentElement, self.REDIRECT_HTTPS)

    # Redirect HTTPS is optional.
    if not redirect_https:
      return

    Set(cfg, C.FORCE_HTTPS,
        self.REDIRECT_HTTPS_INVERTED_MAP
        [GetElementText(document.documentElement, self.REDIRECT_HTTPS)])

# For import/export of LDAP configuration:
class Ldap:
  LDAP = 'ldap'
  HOST = 'host'
  BASE = 'base'
  FILTER = 'filter'
  SSL_SUPPORT = 'sslSupport'
  # the integer values in SSL_SUPPORT_MAP MUST be in sync with the ones
  # defined in LDAPClient.java
  SSL_SUPPORT_MAP = { '0' : 'none',
                      '1' : 'tls',
                      '2' : 'start_tls'}
  SSL_SUPPORT_INVERTED_MAP = InvertMap(SSL_SUPPORT_MAP)
  AUTHENTICATION_METHODS = 'authenticationMethods'
  SIMPLE = 'simple'
  PASSWORD = 'password'
  DISTINGUISHED_NAME = 'distinguishedName'

  KEY_VALUE_RE = re.compile(r'([^:]+):(.*)')

  def Export(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_LDAP]:
      return
    if not os.stat(cfg.getGlobalParam(C.LDAP_CONFIG)).st_size:
      return

    # parse config file into a map key --> value:
    ldap_map = {}
    for line in open(cfg.getGlobalParam(C.LDAP_CONFIG), 'r').readlines():
      if not line.strip():
        continue
      match = self.KEY_VALUE_RE.match(line)
      if not match:
        continue
      key, value = match.groups()
      key = key.strip()
      value = value.strip()
      ldap_map[key] = value

    if not ldap_map.has_key('hostport'):
        return  # ldap disabled.

    # o.k. there is something to export:
    ldap = document.StartElement(document.documentElement, self.LDAP)
    try:
      AppendElementText(document, ldap, self.HOST, ldap_map['hostport'])
      AppendElementText(document, ldap, self.BASE, ldap_map['base'])
      AppendElementText(document, ldap, self.FILTER,
                        ldap_map['userSearchFilter'])
      sslSupportValue = ldap_map['sslSupport']
      if not sslSupportValue:
        sslSupportValue = '0'
      AppendElementText(document, ldap, self.SSL_SUPPORT,
                        self.SSL_SUPPORT_MAP[sslSupportValue])
      # auth methods, for now we only support SIMPLE:
      auth_methods_element = document.StartElement(ldap,
                                                   self.AUTHENTICATION_METHODS)
      try:
        authMethodsValue = ldap_map['authMethods']
        if not authMethodsValue:
          authMethodsValue = '0'
        auth_methods = int(authMethodsValue)
        if auth_methods == 1:
          AppendElementText(document, auth_methods_element, self.SIMPLE,
                            BoolToString(1));
        else:
          AppendElementText(document, auth_methods_element, self.SIMPLE,
                            BoolToString(0));
          logging.error('Unsupported LDAP authentication method: %d. Ignoring.' %
                        auth_methods)
      finally:
        document.EndElement(self.AUTHENTICATION_METHODS)
      AppendElementText(document, ldap, self.PASSWORD,
                        ldap_map['anonBindPassword'])
      AppendElementText(document, ldap, self.DISTINGUISHED_NAME,
                        ldap_map['anonBindDN'])
    finally:
      document.EndElement(self.LDAP)

  def Import(self, document, cfg):
    if not cfg.getGlobalParam(
        license_api.S.ENT_LICENSE_INFORMATION)[
        license_api.S.ENT_LICENSE_ENABLE_LDAP]:
      return

    ldap = GetChildrenElementsByTagName(document.documentElement, self.LDAP)

    # LDAP is optional.
    if not ldap:
      return
    ldap = ldap[0]

    lines = []
    lines.append('hostport:%s\n' % GetElementText(ldap, self.HOST))
    lines.append('base:%s\n' % GetElementText(ldap, self.BASE))
    lines.append('userSearchFilter:%s\n' % GetElementText(ldap, self.FILTER))
    lines.append('sslSupport:%s\n' % (
      self.SSL_SUPPORT_INVERTED_MAP[GetElementText(ldap, self.SSL_SUPPORT)]))
    auth_methods_element = GetSingleElement(ldap, self.AUTHENTICATION_METHODS)
    if StringToBool(GetElementText(auth_methods_element, self.SIMPLE)):
      auth_methods = 1
    else:
      logging.error('SIMPLE LDAP authentication method must be supported.')
      auth_methods = 0
    lines.append('authMethods:%d\n' % auth_methods)
    lines.append('anonBindPassword:%s\n' % GetElementText(ldap, self.PASSWORD))
    lines.append('anonBindDN:%s\n' %
                 GetElementText(ldap, self.DISTINGUISHED_NAME))
    SetFile(cfg, C.LDAP_CONFIG, ''.join(lines))

# Machines, AutoReboot, NumShards, and HttpServerTrustedClients are internal
# state.

class Machines:
  MACHINE = 'machine'
  NAME = 'name'
  DISK = 'disk'
  POWER = 'power'
  HOST = 'host'
  OUTLET = 'outlet'

  def Export(self, document, cfg):
    datachunkdisks = cfg.getGlobalParam(C.DATACHUNKDISKS)
    apc_map = cfg.getGlobalParam(C.APC_MAP)
    machines = datachunkdisks.keys()
    machines.sort()
    functional.remove_duplicates(machines)

    for machine in machines:
      machine_element = document.StartElement(document.documentElement,
                                              self.MACHINE)
      try:
        AppendElementText(document, machine_element, self.NAME, machine)
        for disk in datachunkdisks.get(machine, []):
          AppendElementText(document, machine_element, self.DISK, disk)
        value = apc_map.get(machine, None)
        if value:
          host, outlet = value.split('-')
          power = document.StartElement(machine_element, self.POWER)
          try:
            AppendElementText(document, power, self.HOST, host)
            AppendElementText(document, power, self.OUTLET, outlet)
          finally:
            document.EndElement(self.POWER)
      finally:
        document.EndElement(self.MACHINE)

  def Import(self, document, cfg):
    datachunkdisks = {}
    apc_map = {}
    for machine in GetChildrenElementsByTagName(document.documentElement,
                                                self.MACHINE):
      name = GetElementText(machine, self.NAME)
      datachunkdisks[name] = []
      for disk in GetChildrenElementsByTagName(machine, self.DISK):
        datachunkdisks[name].append(GetText(disk))

      if not datachunkdisks[name]:
        # This allows for import from versions which mistakenly exported a dead
        # node in the configuration.
        # TODO(zsyed): Ideal way would be to import data for the machines which
        # currently exist in /etc/sysconfig/enterprise_config. So even if a
        # machine was removed while export/import was in progress, the upgrade
        # will still succeed.
        logging.warn('No data disks exist for %s, skipping.' % name)
        del datachunkdisks[name]
      children = GetChildrenElementsByTagName(machine, self.POWER)
      if children:
        power = children[0]
        apc_map[name] = '%s-%s' % (GetElementText(power, self.HOST),
                                      GetElementText(power, self.OUTLET))
    Set(cfg, C.DATACHUNKDISKS, datachunkdisks)
    Set(cfg, C.APC_MAP, apc_map)


class AutoReboot(AbstractBooleanItem):
  ELEMENT_NAME = 'autoReboot'
  GOOGLE_CONFIG_NAME = C.AUTO_REBOOT


class NumShards(AbstractIntItem):
  ELEMENT_NAME = 'numShards'
  GOOGLE_CONFIG_NAME = C.ENT_NUM_SHARDS


# Migrated for the convenience of the regression test.
class HttpServerTrustedClients(AbstractListItem):
  ELEMENT_NAME = 'httpServerTrustedClients'
  GOOGLE_CONFIG_NAME = C.HTTPSERVER_TRUSTED_CLIENTS

# Migrate the whole directory, filenames are preserved.
# File contents are in UTF-8.
class AbstractDirItem:
  ELEMENT_NAME = None
  GOOGLE_CONFIG_NAME = None

  FILENAME_PATTERN = '*'

  def GetDestFilename(self, filename):
    """ This function helps differentiate import of CA certs and CRLs from 4.4 and
    4.6. The naming convention of CA certs and CRLs changed from 4.4 to 4.6 to
    comply with the openssl standard."""
    return filename

  def Export(self, document, cfg):
    dirname = cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME)
    if not os.path.exists(dirname):
      return

    dir_element = document.StartElement(document.documentElement,
                                        self.ELEMENT_NAME)
    try:
      for filename in glob.glob(dirname + '/' + self.FILENAME_PATTERN):
        (filepath, filename) = os.path.split(filename)
        one_file = document.StartElement(dir_element, "file")
        try:
          AppendElementText(document, one_file, "name", filename)
          filename = os.path.join(dirname, filename)
          AppendElementText(document, one_file, "content",
                            open(filename, "r").read())
        finally:
          document.EndElement("file")
    finally:
      document.EndElement(self.ELEMENT_NAME)

  def Import(self, document, cfg):
    dir_elements = GetChildrenElementsByTagName(document.documentElement,
                                   self.ELEMENT_NAME)
    if not dir_elements or len(dir_elements) == 0:
      return

    dirname = cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME)
    if not os.path.exists(dirname):
      os.mkdir(dirname)

    files = []
    for one_file in GetChildrenElementsByTagName(dir_elements[0], "file"):
      filename = os.path.join(dirname,
                 self.GetDestFilename(GetElementText(one_file, "name")))
      files.append(filename)
      content  = GetElementText(one_file, "content")
      open(filename, "w").write(content)

    # Distribute all files within this directory to all cluster nodes.
    # Because these newly created files and directory may not be residing
    # on the GSA main node, hence it will be deleted by the rsync process.
    machines = cfg.getGlobalParam('MACHINES')
    if len(machines) > 1 and files:
      E.distribute(machines, ' '.join(files), 1)

# A directory contains trusted CA certificates
class TrustedCaDirectory(AbstractDirItem):
  ELEMENT_NAME = 'trustedCaDirectory'
  GOOGLE_CONFIG_NAME = C.TRUSTED_CA_DIRNAME

  FILENAME_PATTERN= '*%s' % ssl_cert.CA_CERT_EXT

  def GetDestFilename(self, filename):
    if os.path.splitext(filename)[1] == '':
      return '%s%s' % (filename, ssl_cert.CA_CERT_EXT)
    return filename

# A directory contains CRLs
class CrlDirectory(AbstractDirItem):
  ELEMENT_NAME = 'crlDirectory'
  GOOGLE_CONFIG_NAME = C.CRL_DIRNAME

  FILENAME_PATTERN= '*%s' % ssl_cert.CRL_EXT

  def GetDestFilename(self, filename):
    if os.path.splitext(filename)[1] == '':
      return '%s%s' % (filename, ssl_cert.CRL_EXT)
    return filename

class UamDirectory(AbstractDirItem):
  """Handles export/import of personalization data.  This class is
  never executed, but I decided to keep it in here anyway.

  Instead of using migration_bot to migrate personalization data, we
  make use of FRU (Full Replacement Upgrade) and with it comes the
  mechanism to migrate the index (gsa_data_migration.py).
  """

  ELEMENT_NAME = 'uamDir'
  GOOGLE_CONFIG_NAME = C.UAM_DIR
  PARAM  = 'param'

  def Export(self, document, cfg):
    # Create a tar ball with the contents of the uam directory.
    dirname = cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME)
    out_file = '%s/%s.tar' % (dirname, time.time())
    tar_exec = 'tar -cf %s -C %s .' % (out_file, dirname)
    os.system(tar_exec)
    body = base64.encodestring(open(out_file).read())
    os.unlink(out_file)

    # Stick it into the XML
    uam_dir = document.StartElement(document.documentElement, 'UAM_DIR')
    try:
      AppendElementCDATA(document, uam_dir, self.PARAM, body)
    finally:
      document.EndElement('UAM_DIR')

  def Import(self, document, cfg):
    element = GetChildrenElementsByTagName(document.documentElement, 'UAM_DIR')

    # Personalization data is optional.
    if not element:
      return

    # Create the directory if it doesn't already exist.
    dirname = cfg.getGlobalParam(self.GOOGLE_CONFIG_NAME)
    if not os.path.exists(dirname):
      os.mkdir(dirname)

    tar_element = GetChildrenElementsByTagName(element[0], self.PARAM)

    # Fetch and write the tar ball into some temporary location.
    body =  base64.decodestring(GetText(tar_element[0]))
    out_file = '%s/%s.tar' % (dirname, time.time())
    open(out_file, 'w').write(body)
    logging.info('Wrote %s' % out_file)

    # Untar the tarball into the destination directory.
    untar_exec = 'tar -xf %s -C %s' % (out_file, dirname)
    os.system(untar_exec)
    os.unlink(out_file)

# A directory contains stylesheet
class DatabaseStylesheetDirectory(AbstractDirItem):
  ELEMENT_NAME = 'databaseStylesheets'
  GOOGLE_CONFIG_NAME = C.DATABASE_STYLESHEET_DIR

class AuthenticateClientCert(AbstractBooleanItem):
  ELEMENT_NAME = 'authenticateClientCert'
  GOOGLE_CONFIG_NAME = C.AUTHENTICATE_CLIENT_CERT

class AuthenticateServerCert(AbstractBooleanItem):
  ELEMENT_NAME = 'authenticateServerCert'
  GOOGLE_CONFIG_NAME = C.AUTHENTICATE_SERVER_CERT

class AuthenticateOneboxServerCert(AbstractBooleanItem):
  ELEMENT_NAME = 'authenticateOneboxServerCert'
  GOOGLE_CONFIG_NAME = C.AUTHENTICATE_ONEBOX_SERVER_CERT

class FeederTrustedClients(AbstractListItem):
  ELEMENT_NAME = 'feederTrustedClients'
  GOOGLE_CONFIG_NAME = C.FEEDER_TRUSTED_CLIENTS

class AuthnLoginUrl(AbstractItem):
  ELEMENT_NAME = 'authnLoginUrl'
  GOOGLE_CONFIG_NAME = C.AUTHN_LOGIN_URL

class AuthnArtifactServiceUrl(AbstractItem):
  ELEMENT_NAME = 'authnArtifactServiceUrl'
  GOOGLE_CONFIG_NAME = C.AUTHN_ARTIFACT_SERVICE_URL

class AuthzServiceUrl(AbstractItem):
  ELEMENT_NAME = 'authzServiceUrl'
  GOOGLE_CONFIG_NAME = C.AUTHZ_SERVICE_URL

class DatabaseConfig(AbstractFileItem):
  ELEMENT_NAME = 'databaseConfig'
  GOOGLE_CONFIG_NAME = C.DATABASES

  def Import(self, document, cfg):
    elements = GetChildrenElementsByTagName(document.documentElement,
                                            self.ELEMENT_NAME)

    # This element is optional.
    if not elements:
      return
    # migrate db config if necessary
    version = cfg.getGlobalParam("VERSION")
    dbconfig = entconfig.MigrateDatabaseConfig(GetText(elements[0]), version)
    SetFile(cfg, self.GOOGLE_CONFIG_NAME, dbconfig)


class Connectors(AbstractFileItem):
  ELEMENT_NAME = 'connectors'
  GOOGLE_CONFIG_NAME = C.CONNECTORS

class ConnectorManagers(AbstractFileItem):
  ELEMENT_NAME = 'connectorManagers'
  GOOGLE_CONFIG_NAME = C.CONNECTOR_MGRS

class GoogleAppsIntegration(AbstractBooleanItem):
  ELEMENT_NAME = 'googleAppsIntegration'
  GOOGLE_CONFIG_NAME = C.GOOGLE_APPS_INTEGRATION

class GoogleAppsDomain(AbstractItem):
  ELEMENT_NAME = 'googleAppsDomain'
  GOOGLE_CONFIG_NAME = C.GOOGLE_APPS_DOMAIN

class OneBoxConfig(AbstractFileItem):
  ELEMENT_NAME = 'oneboxConfig'
  GOOGLE_CONFIG_NAME = C.ONEBOX_MODULES

class BatchCrawlSchedule(AbstractFileItem):
  ELEMENT_NAME = "batchCrawlSchedule"
  GOOGLE_CONFIG_NAME = C.CRAWL_SCHEDULE

class BatchCrawlScheduleBitmap(AbstractFileItem):
  ELEMENT_NAME = "batchCrawlScheduleBitmap"
  GOOGLE_CONFIG_NAME = C.CRAWL_SCHEDULE_BITMAP

class BatchCrawlMode(AbstractBooleanItem):
  ELEMENT_NAME = "batchCrawlMode"
  GOOGLE_CONFIG_NAME = C.ENTERPRISE_SCHEDULED_CRAWL_MODE

class ScoringAdjust:
  # For scoring adjustments, we write the parameters, template and compiled
  # representation. Strictly speaking, the compiled representation could be
  # derived from the other two, but doing it this way simplifies the import.
  SCORING_ADJUST = 'scoringAdjust'
  PARAMS = 'params'
  GROUP  = 'group'
  PARAM  = 'param'
  NAME   = 'name'
  ADDITIONAL = 'additionalPolicies'
  POLICY = 'policy'
  POLICY_NAME = 'policyName'
  TEMPLATE = 'template'
  CONFIG = 'config'

  def Export(self, document, cfg):
    """Serializes scoring adjust settings into document."""
    element = document.StartElement(document.documentElement,
                                    self.SCORING_ADJUST)
    try:
      # Serialize ENT_SCORING_ADJUST into params element.
      # The params element is created, even if empty.
      params_element = document.StartElement(element, self.PARAMS)
      try:
        params = cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
        self._ExportParams(document, params_element, params)
      finally:
        document.EndElement(self.PARAMS)

      # Serialize ENT_SCORING_ADDITIONAL_POLICIES if it is nonempty.
      additional_policies = cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
      if additional_policies:
        # The additional policies element is only created if non-empty
        policies_element = document.StartElement(element, self.ADDITIONAL)
        try:
          for policy_name, params in additional_policies.iteritems():
            policy_element = document.StartElement(policies_element, self.POLICY)
            try:
              AppendElementText(document, policy_element,
                                self.POLICY_NAME, policy_name)
              self._ExportParams(document, policy_element, params)
            finally:
              document.EndElement(self.POLICY)
        finally:
          document.EndElement(self.ADDITIONAL)

      template = cfg.getGlobalParam(C.ENT_SCORING_TEMPLATE)
      if template:
        AppendElementCDATA(document, element, self.TEMPLATE,
                           open(template, 'r').read())

      config = cfg.getGlobalParam(C.ENT_SCORING_CONFIG)
      if config:
        AppendElementCDATA(document, element, self.CONFIG,
                           open(config, 'r').read())
    finally:
      document.EndElement(self.SCORING_ADJUST)

  def _ExportParams(self, document, parent, params):
    """Helper for Export, serializes a dictionary of scoring adjust params."""
    if not params:
      return
    for group, param_list in params.iteritems():
      group_element = document.StartElement(parent, self.GROUP)
      try:
        AppendElementText(document, group_element, self.NAME, group)
        if param_list:
          for p in param_list:
            AppendElementCDATA(document, group_element, self.PARAM, p)
      finally:
        document.EndElement(self.GROUP)

  def Import(self, document, cfg):
    """Imports scoring adjust settings from document into cfg."""
    elements = GetChildrenElementsByTagName(
        document.documentElement, self.SCORING_ADJUST)
    if not elements:
      logging.info('No "%s" elements found in document' % self.SCORING_ADJUST)
      # Ensure we leave all the scoring related parameters clean
      cfg.setGlobalParam(C.ENT_SCORING_ADJUST, None)
      cfg.setGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES, None)
      cfg.setGlobalParam(C.ENT_SCORING_TEMPLATE, None)
      cfg.setGlobalParam(C.ENT_SCORING_CONFIG, None)
      return

    params_elements = GetChildrenElementsByTagName(elements[0], self.PARAMS)
    if not params_elements:
      logging.warn('Bad scoring adjust section: no params element found')
      return
    try:
      default_policy = self._ImportParams(params_elements[0])
    except IndexError:
      logging.warn('Malformed parameters for default policy')
      return
    cfg.setGlobalParam(C.ENT_SCORING_ADJUST, default_policy)

    policies = None
    additional_element = GetChildrenElementsByTagName(elements[0],
                                                      self.ADDITIONAL)
    if additional_element:
      policies = {}
      additional_policies = GetChildrenElementsByTagName(additional_element[0],
                                                         self.POLICY)
      for policy_element in additional_policies:
        try:
          policy_name = GetElementText(policy_element, self.POLICY_NAME)
        except IndexError:
          logging.warn('Bad scoring adjust policy: no policy name in section')
          return
        try:
          params = self._ImportParams(policy_element)
        except IndexError:
          logging.warn('Bad scoring adjust policy: malformed parameters')
          return
        policies[policy_name] = params
    cfg.setGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES, policies)

    # Do NOT import the scoring template if there is already one present.
    # This means that the one from the new version we are migrating to will be
    # used, so that new scoring policies and changes to existing ones are
    # installed. We only import the old template if we don't find a new one
    # (this should never happen, but let's be defensive).
    template_name = cfg.getGlobalParam(C.ENT_SCORING_TEMPLATE)
    if not template_name:
      logging.info('No template file name: not importing')
    elif os.path.exists(template_name):
      logging.info('Use scoring template %s: not importing' % template_name)
    else:
      template_element = GetChildrenElementsByTagName(
          elements[0], self.TEMPLATE)
      if template_element:
        out = open(template_name, 'w')
        out.write(GetText(template_element[0]))
        out.close()

    # Import the scoring policies file.
    # This will get replaced when we apply the settings, but we import it
    # anyway, again to be defensive against bad settings.
    config_element = GetChildrenElementsByTagName(elements[0], self.CONFIG)
    if config_element:
      config_file = cfg.getGlobalParam(C.ENT_SCORING_CONFIG)
      if config_file:
        out = open(config_file, 'w')
        out.write(GetText(config_element[0]))
        out.close()

    # Apply settings: takes the new template and the scoring adjust params,
    # and replaces the scoring configuration, assuming all is well.
    logging.info("Regenerate scoring settings from template")
    scoring_adjust_handler.ApplyAndSaveSettings(cfg)

  def _ImportParams(self, params_element):
    """Helper function for Import(), imports parameters from xml.

    Args:
      params_element: Xml containing the scoring adjust parameters.

    Returns:
      A dictionary containing scoring adjust parameters.

    Raises:
      IndexError: if there is no self.NAME tag in a group element
    """
    params = {}
    group_elements = GetChildrenElementsByTagName(params_element, self.GROUP)
    for group_element in group_elements:
      name = GetElementText(group_element, self.NAME)
      sub_elements = GetChildrenElementsByTagName(group_element, self.PARAM)
      params[name] = []
      for p in sub_elements:
        params[name].append(GetText(p))
    return params

# This replaces xml.dom.ext.Printer.PrintVisitor.visitCDATASection so CDATA
# nodes do not get whitespace surrounding them.
def visitCDATASection(self, node):
  self._write('<![CDATA[%s]]>' % (node.data))
  self._inText = 1
  return

# The ordering matches the user interface as much as possible.
VERSION_MIGRATION_SERIALIZATION = [
  # License must come first.
  License,

  # Crawl and Index
  StartUrls,
  CrawlUrlPatterns,
  DoNotCrawlUrlPatterns,
  DatabaseConfig,
  DatabaseStylesheetDirectory,
  FeederTrustedClients,
  BatchCrawlSchedule,
  BatchCrawlMode,
  CrawlCredentials,
  ProxyServers,
  UserAgent,
  HttpHeaders,
  CookieSites,
  SingleSignOn,
  DuplicateHosts,
  SortByDatePatterns,
  MaximumNumberOfURLsToCrawl,
  DefaultHostLoad,
  HostLoadSchedule,
  CrawlMoreUrlPatterns,
  CrawlLessUrlPatterns,
  IgnoreLastModifiedDateForRecrawlUrlPatterns,
  Collections,

  # Connector Framework
  Connectors,
  ConnectorManagers,

  # Google Apps
  GoogleAppsIntegration,
  GoogleAppsDomain,

  # Serving
  FrontEnds,
  QueryExpansion,
  AuthorizationCacheEntryDuration,
  AuthnLoginUrl,
  AuthnArtifactServiceUrl,
  AuthzServiceUrl,
  OneBoxConfig,
  ScoringAdjust,

  # Not in Admin Console. In webserver_config.py.
  CrawlIpAddress,
  ServeIpAddress,
  SwitchIpAddress,
  SubnetMask,
  GatewayIpAddress,
  NetworkSpeedDuplex,
  ServerironAutonegotiation,
  TimeZone,
  UseDhcp,
  DnsDhcp,

  # Network Settings
  DnsServers,
  DnsSuffixes,
  SmtpServer,
  NtpServers,
  SyslogServer,
  SyslogFacilityUsageLogs,

  # System Settings
  AutomaticReportEmailRecipient,
  ProblemReportEmailRecipient,
  EmailSender,
  DefaultSearchUrl,
  DailyStatusReport,
  EnableSsh,
  EnableBorgmon,

  # SNMP Support
  EnableSnmp,
  SnmpUsers,
  SnmpCommunities,
  SnmpTrapsHost,
  SnmpTrapsCommunity,
  SnmpTraps,

  # Users
  Users,
  AutoCompleteOff,

  # Certificate Authorities
  TrustedCaDirectory,
  CrlDirectory,

  # SSL
  SslCertificateAndPrivateKey,
  RedirectHttps,
  AuthenticateClientCert,
  AuthenticateServerCert,
  AuthenticateOneboxServerCert,

  Ldap,
  #Kerberos,                            # [Kerberos/IWA] TODO(mrb):  later (?)

  # Internal state
  Machines,
  AutoReboot,
  NumShards,
  HttpServerTrustedClients,
  
  # User information.
  Clicklogging,
  Alerts2,
  ]

def ExportConfiguration(cfg):
  sb = cStringIO.StringIO()
  document = GsaXmlWriter(sb)
  document.documentElement = document.StartElement(None, 'configuration')

  for _class in VERSION_MIGRATION_SERIALIZATION:
    try:
      _class().Export(document, cfg)
    except Exception, e:
      # Should never happen, so don't i18n
      print 'Export failed for component', str(_class).split('.')[-1]
      traceback.print_exc()
      logging.error('Export failed for %s: %s' % (_class, e))

  document.EndElement('configuration')
  document.EndDocument()

  return sb.getvalue()

def ImportConfiguration(cfg, stream):
  document = xml.dom.minidom.parse(stream)
  document.normalize()
  cfg.globalParams.set_allow_config_mgr_requests(0)
  cfg.globalParams.BeginBatchMode()
  for _class in VERSION_MIGRATION_SERIALIZATION:
    try:
      _class().Import(document, cfg)
    except Exception, e:
      # Should never happen, so don't i18n
      print 'Import failed for component', str(_class).split('.')[-1]
      traceback.print_exc()
      logging.error('Import failed for %s: %s' % (_class, e))

  cfg.setGlobalParam(C.ENT_SYSTEM_HAS_VALID_CONFIG, 1)
  cfg.globalParams.EndBatchMode()

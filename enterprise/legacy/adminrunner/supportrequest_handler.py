#!/usr/bin/python2.4
#
# Copyright 2003-2006 Google, Inc.
# All rights reserved.
#

import os
import stat
import struct
import md5
import re

from google3.strings import pywrap_strutil
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging

split_csv_line = pywrap_strutil.SplitCSVLine
URLPattern = validatorlib.URLPattern

class SupportRequestHandler(admin_handler.ar_handler):
  def __init__(self, conn, command, prefixes, params, cfg=None):
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      'getsystemconfiguration' : admin_handler.CommandInfo(
      0, 0, 0, self.__GetSystemConfiguration),
      'getcollectionconfiguration' : admin_handler.CommandInfo(
      1, 0, 0, self.__GetCollectionConfiguration),
      'getfrontendconfiguration' : admin_handler.CommandInfo(
      1, 0, 0, self.__GetFrontEndConfiguration)
    }

  def __GetSystemConfiguration(self):
    return 'response = %s' % repr(SystemConfiguration(self.cfg.globalParams))

  def __GetCollectionConfiguration(self, name):
    return 'response = %s' % repr(CollectionConfiguration(name, self.cfg.globalParams))

  def __GetFrontEndConfiguration(self, name):
    return 'response = %s' % repr(FrontEndConfiguration(name, self.cfg.globalParams))

class SystemConfiguration:
  PROXY_RE = re.compile('(.+)\s+(.+):(.+)')

  class ProxyServer:
    def __init__(self, url_pattern, host, port):
      self.url_pattern = url_pattern
      self.host = host
      self.port = port

    def Export(self):
      return {
        'url_pattern' : self.url_pattern,
        'host'        : self.host,
        'port'        : self.port
        }

  WEB_SERVER_HOST_LOAD_RE = re.compile('(.+)\s+\[tz:(\d+)-(\d+):(\S+)\]')

  class WebServerHostLoadException:
    def __init__(self, host, start_time, end_time, host_load):
      self.hosts = [ host ]
      self.start_time = start_time
      self.end_time = end_time
      self.host_load = host_load

    def __hash__(self):
      return struct.unpack('I', md5.new(start_time + end_time + host_load).digest())[0]

    def AddHost(host):
      self.hosts.append(host)

    def Export(self):
      return {
        'hosts'      : self.hosts,
        'start_time' : self.start_time,
        'end_time'   : self.end_time,
        'host_load'  : self.host_load
        }

  class SortByDatePattern:
    def __init__(self, url_pattern, locate_date, meta_tag_name):
      self.url_pattern = url_pattern
      self.locate_date = locate_date
      self.meta_tag_name = meta_tag_name

    def Export(self):
      return {
        'url_pattern'   : self.url_pattern,
        'locate_date'   : self.locate_date,
        'meta_tag_name' : self.meta_tag_name
        }

  def __init__(self, globalParams):
    var = globalParams.var
    var_copy = globalParams.var_copy

    self.start_urls = open(var(C.STARTURLS), 'r').read().split('\n')
    self.follow_url_patterns = open(var(C.GOODURLS), 'r').read().split('\n')
    self.do_not_follow_url_patterns = open(var(C.BADURLS),
                                           'r').read().split('\n')
    self.proxy_servers = []
    for line in open(var(C.PROXY_CONFIG), 'r').readlines():
      pattern, host, port = PROXY_RE.match(line).groups()
      self.proxy_servers.append(self.ProxyServer(pattern, host, port))
    self.crawl_authenticating_hosts = os.stat(
      var(C.CRAWL_USERPASSWD_CONFIG))[stat.ST_SIZE] != 0
    self.use_cookies = os.stat(var(C.COOKIE_RULES))[stat.ST_SIZE] != 0
    self.web_server_host_load = float(var_copy(C.URLSERVER_DEFAULT_HOSTLOAD))
    self.web_server_host_load_exceptions = {}
    for line in open(var(C.HOSTLOADS), 'r').readlines():
      host, start_time, end_time, host_load = HOSTLOAD_RE.match(line).groups()
      web_server_host_load_exception = self.WebServerHostLoadException(
        host, start_time, end_time, float(host_load))
      if self.web_server_host_load_exceptions.has_key(
        web_server_host_load_exception):
        self.web_server_host_load_exceptions[
          web_server_host_load_exception].AddHost(host)
      else:
        self.web_server_host_load_exceptions[
          web_server_host_load_exception] = web_server_host_load_exception
    self.frequently_changing_url_patterns = open(var(C.URLMANAGER_REFRESH_URLS),
                                                 'r').read().split('\n')
    self.archive_url_patterns = open(var(C.URLSCHEDULER_NONDAILY_URLS),
                                     'r').read().split('\n')
    self.duplicate_hosts = open(var(C.DUPHOSTS), 'r').read().split('\n')
    self.sort_by_date_patterns = []
    for line in open(var(C.DATEPATTERNS), 'r').readlines():
      parts = split_csv_line(line)
      self.sort_by_date_patterns.append(
        self.SortByDatePattern(parts[0], parts[1], parts[2]))
    self.cluster = var(C.ENT_CONFIG_TYPE) == 'CLUSTER'
    self.serve_ip_address = var_copy(C.EXTERNAL_WEB_IP)
    self.crawl_ip_address = var_copy(C.EXTERNAL_CRAWL_IP)
    self.switch_ip_address = var_copy(C.EXTERNAL_SWITCH_IP)
    self.subnet_mask = var_copy(C.EXTERNAL_NETMASK)
    self.gateway_ip_address = var_copy(C.EXTERNAL_DEFAULT_ROUTE)
    self.dns_servers = var_copy(C.BOT_DNS_SERVERS)
    self.dns_suffixes = var_copy(C.DNS_SEARCH_PATH)
    self.ntp_servers = var_copy(C.NTP_SERVERS)
    self.syslog_server = var_copy(C.SYSLOG_SERVER)
    self.syslog_facility_usage_logs = var_copy(C.ENT_SYSLOG_GWS_FAC) != None
    self.version = var_copy(C.VERSION)
    self.appliance_id = var_copy(C.ENT_CONFIG_NAME)

  def __repr__(self):
    return repr({
      'start_urls'                       : self.start_urls,
      'follow_url_patterns'              : self.follow_url_patterns,
      'do_not_follow_url_patterns'       : self.do_not_follow_url_patterns,
      'proxy_servers'                    : map(lambda x: x.Export(),
                                               self.proxy_servers),
      'crawl_authenticating_hosts'       : self.crawl_authenticating_hosts,
      'use_cookies'                      : self.use_cookies,
      'web_server_host_load'             : self.web_server_host_load,
      'web_server_host_load_exceptions'  : map(
      lambda x: x.Export(), self.web_server_host_load_exceptions.values()),
      'frequently_changing_url_patterns' : self.frequently_changing_url_patterns,
      'archive_url_patterns'             : self.archive_url_patterns,
      'duplicate_hosts'                  : self.duplicate_hosts,
      'sort_by_date_patterns'            : map(
      lambda x: x.Export(), self.sort_by_date_patterns),
      'cluster'                          : self.cluster,
      'serve_ip_address'                 : self.serve_ip_address,
      'crawl_ip_address'                 : self.crawl_ip_address,
      'switch_ip_address'                : self.switch_ip_address,
      'subnet_mask'                      : self.subnet_mask,
      'gateway_ip_address'               : self.gateway_ip_address,
      'dns_servers'                      : self.dns_servers,
      'dns_suffixes'                     : self.dns_suffixes,
      'ntp_servers'                      : self.ntp_servers,
      'syslog_server'                    : self.syslog_server,
      'syslog_facility_usage_logs'       : self.syslog_facility_usage_logs,
      'version'                          : self.version,
      'appliance_id'                     : self.appliance_id
      })

class CollectionConfiguration:
  def __init__(self, name, globalParams):
    coll_obj = ent_collection.EntCollection(name, globalParams)
    var = coll_obj.get_var
    self.name = name
    self.include_url_patterns = open(var(C.GOODURLS), 'r').read().split('\n')
    self.do_not_include_url_patterns = open(var(C.BADURLS), 'r').read().split('\n')
    self.serving_prerequisite_results = var(C.TESTWORDS_IN_FIRST)
    self.serving_prerequisites = len(open(var(C.TESTWORDS), 'r').readlines())
    categories = coll_obj.get_var(C.CATEGORIES)
    if categories:
      self.categories_count = len(categories)
    else:
      self.categories_count = 0

  def __repr__(self):
    return repr({
      'name'                         : self.name,
      'include_url_patterns'         : self.include_url_patterns,
      'do_not_include_url_patterns'  : self.do_not_include_url_patterns,
      'serving_prerequisite_results' : self.serving_prerequisite_results,
      'serving_prerequisites_count'  : self.serving_prerequisites,
      'categories_count'             : self.categories_count
      })

class FrontEndConfiguration:
  url_pattern_validator = URLPattern(allowComments = 0, allowSlash=1)

  def __init__(self, name, globalParams):
    coll_obj = ent_collection.EntFrontend(name, globalParams)
    var = coll_obj.get_var
    self.name = name
    self.keyword_match_count = 0
    self.phrase_match_count = 0
    self.exact_match_count = 0
    for line in open(var(C.GOOGLEMATCH), 'r').readlines():
      parts = split_csv_line(line)
      if parts[1] == 'KeywordMatch':
        self.keyword_match_count = self.keyword_match_count + 1
      elif parts[1] == 'PhraseMatch':
        self.phrase_match_count = self.phrase_match_count + 1
      elif parts[2] == 'ExactMatch':
        self.exact_match_count = self.exact_match_count + 1
    self.synonyms_count = len(open(var(C.SYNONYMS), 'r').readlines())
    self.removed_urls_count = 0
    for line in open(var(C.BADURLS_NORETURN), 'r').readlines():
      ret = url_pattern_validator.validate(line)
      if ret == validatorlib.VALID_OK or ret == validatorlib.VALID_SHORT_CIRCUIT:
        self.removed_urls_count = self.removed_urls_count + 1

  def __repr__(self):
    return repr({
      'name'                : self.name,
      'keyword_match_count' : self.keyword_match_count,
      'phrase_match_count'  : self.phrase_match_count,
      'exact_match_count'   : self.exact_match_count,
      'synonyms_count'      : self.synonyms_count,
      'removed_urls_count'  : self.removed_urls_count
      })

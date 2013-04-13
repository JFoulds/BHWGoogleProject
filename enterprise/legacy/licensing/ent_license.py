#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# David Watson <davidw@google.com> rewrite after
#  LicenseManager.java/ent_license.py by: Feng Hu <feng@google.com>
#
# this is a library of license related classes
#
#############################################################################

CURRENT_LICENSE_VERSION = '1.0'

GPG_BIN = "gpg"

import string
import os
import time
import copy
import commands

from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import config_utils
from google3.enterprise.legacy.util import C
from google3.enterprise.license import license_api
from google3.enterprise.legacy.production.babysitter import validatorlib

#############################################################################
# EnterpriseLicense encapsulates enterprise license data, and provides
# methods to use and manipulate it.

# load license validator

kUnlimitedEndDate = 2051251200000L # 2035-01-01 00:00:00 in ms_since_epoch
kUnlimitedMaxNumCollections = 0L
kUnlimitedMaxNumFrontends = 0L
kUnlimitedMaxPagesPerCollection = 0L
kUnlimitedMaxPagesOverall = 0L
kOneBoxMaxPagesHardLimit = 3000000L # for 1-way, 3 million is hard limit
kMiniMaxPagesHardLimit = 1000000L # Mini 2.0 has half the disk space of 1-way
kSuperMaxPagesHardLimit = 10000000L # for super, 10 million is hard limit
kClusterMaxPagesHardLimit = 40000000L # for cluster, 40 million is hard limit
kLiteMaxPagesHardLimit = 50000L # for GSA-Lite, 50k is hard limit
kFullMaxPagesHardLimit = 1000000L # for virtual GSAFull, 1 million is hard limit

# those keys can be specified by license creator
# TODO: remove obsolete ENT_LICENSE_MAX_PAGES_PER_COLLECTION
USER_INPUT_KEYS = [
    license_api.S.ENT_BOX_ID,
    license_api.S.ENT_LICENSE_ID,
    license_api.S.ENT_LICENSE_ORIGINAL_START_DATE,
    license_api.S.ENT_LICENSE_ORIGINAL_END_DATE,
    license_api.S.ENT_LICENSE_ORIGINAL_SERVING_TIME,
    license_api.S.ENT_LICENSE_GRACE_PERIOD,
    license_api.S.ENT_LICENSE_MAX_COLLECTIONS,
    license_api.S.ENT_LICENSE_MAX_FRONTENDS,
    license_api.S.ENT_LICENSE_MAX_PAGES_PER_COLLECTION,
    license_api.S.ENT_LICENSE_MAX_PAGES_OVERALL,
    license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE,
    license_api.S.ENT_LICENSE_ENABLE_TOOLBAR,
    license_api.S.ENT_LICENSE_ENABLE_LDAP,
    license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL,
    license_api.S.ENT_LICENSE_ENABLE_CATEGORY,
    license_api.S.ENT_LICENSE_ENABLE_SSO,
    license_api.S.ENT_LICENSE_DATABASES,
    license_api.S.ENT_LICENSE_FEEDS,
    license_api.S.ENT_LICENSE_FILESYSTEM,
    license_api.S.ENT_LICENSE_BATCH_CRAWL,
    license_api.S.ENT_LICENSE_QUERY_EXPANSION,
    license_api.S.ENT_LICENSE_SCORING_ADJUST,
    license_api.S.ENT_LICENSE_CLUSTERING,
    license_api.S.ENT_LICENSE_LABS_SETTINGS,
    #
    # [Kerberos/IWA] ...
    #
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX,  # [Kerberos/IWA]
    #
    # [Kerberos/IWA] ... done.
    #
    ]


# Unpack a string of labs settings into a dictionary.
# Assumes well-formed settings, a space separated string of name=value pairs
# (maybe empty or None).
def UnpackLabsSettings(labs_settings):
  settings = { }
  if labs_settings:
    # Settings is a space separated array of name=value pairs
    for setting in labs_settings.split(' '):
      name, value = setting.split('=', 1)
      settings[name.strip()] = value.strip()
  return settings

# helper function to create EnterpriseLicenses
# Note: must-have fields: max_pages_per_collection is no longer needed in
# new system; max_frontends, max_pages_overall are new ones in new system
# To make things simpler, I just have all of them to be required fields.
# TODO: remove the obsolete max_pages_per_collection later
#
def CreateEnterpriseLicense(box_id,
                            license_id,
                            max_collections,
                            max_frontends,
                            max_pages_overall, # for realtime system
                            max_pages_per_collection, # for old system
                            start_date_ms = None,
                            end_date_ms = None,
                            serving_time_ms = None,
                            grace_period_ms = None,
                            enable_seku_lite = None,
                            enable_toolbar = None,
                            enable_ldap = None,
                            enable_cookie_crawl = None,
                            enable_category = None,
                            enable_sso = None,
                            enable_databases = None,
                            enable_feeds = None,
                            enable_filesystem = None,
                            enable_batchcrawl = None,
                            enable_query_expansion = None,
                            enable_scoring_adjust = None,
                            enable_clustering = None,
                            labs_settings = None,
                            #
                            # [Kerberos/IWA] ...
                            #
                            enable_kerberos_at_login = None,   # [Kerberos/IWA]
                            enable_kerberos_at_crawl = None,   # [Kerberos/IWA]
                            enable_kerberos_at_serve = None,   # [Kerberos/IWA]
                            enable_kerberos_kt_parse = None,   # [Kerberos/IWA]
                            enable_kerberos_at_onebox = None   # [Kerberos/IWA]
                            #
                            # [Kerberos/IWA] ... done.
                            #
                            ):

  now_in_ms = long(time.time()*1000)
  ms_in_day =  24 * 3600 * 1000L

  license_map = {
    # we always fill these in
    license_api.S.ENT_LICENSE_VERSION          : CURRENT_LICENSE_VERSION,
    license_api.S.ENT_LICENSE_CREATION_DATE    : now_in_ms,

    # defaults
    license_api.S.ENT_LICENSE_GRACE_PERIOD     : 30L * ms_in_day,
    license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE : 0,
    license_api.S.ENT_LICENSE_ENABLE_LDAP      : 1,
    license_api.S.ENT_LICENSE_ENABLE_TOOLBAR   : 0,
    license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL : 0,
    license_api.S.ENT_LICENSE_ENABLE_CATEGORY  : 0,
    license_api.S.ENT_LICENSE_ENABLE_SSO  : 0,
    license_api.S.ENT_LICENSE_DATABASES : 1,
    license_api.S.ENT_LICENSE_FEEDS : 1,
    license_api.S.ENT_LICENSE_FILESYSTEM : 1,
    license_api.S.ENT_LICENSE_BATCH_CRAWL : 1,
    license_api.S.ENT_LICENSE_QUERY_EXPANSION : 1,
    license_api.S.ENT_LICENSE_SCORING_ADJUST : 1,
    license_api.S.ENT_LICENSE_CLUSTERING : 1,
    license_api.S.ENT_LICENSE_LABS_SETTINGS : '',
    #
    # [Kerberos/IWA] ...
    #
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN : 0,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL : 0,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE : 0,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE : 0,   # [Kerberos/IWA]
    license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX : 0,  # [Kerberos/IWA]
    #
    # [Kerberos/IWA] ... done.
    #
    }

  # if any value is None, we don't add it into license_map
  for name, value in (
    (license_api.S.ENT_BOX_ID,                            box_id),
    (license_api.S.ENT_LICENSE_ID,                        license_id),
    (license_api.S.ENT_LICENSE_MAX_COLLECTIONS,           max_collections),
    (license_api.S.ENT_LICENSE_MAX_FRONTENDS,             max_frontends),
    (license_api.S.ENT_LICENSE_MAX_PAGES_OVERALL,         max_pages_overall),
    (license_api.S.ENT_LICENSE_MAX_PAGES_PER_COLLECTION,
                                                     max_pages_per_collection),
    (license_api.S.ENT_LICENSE_ORIGINAL_START_DATE,       start_date_ms),
    (license_api.S.ENT_LICENSE_ORIGINAL_END_DATE,         end_date_ms),
    (license_api.S.ENT_LICENSE_ORIGINAL_SERVING_TIME,     serving_time_ms),
    (license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE,          enable_seku_lite),
    (license_api.S.ENT_LICENSE_ENABLE_LDAP,               enable_ldap),
    (license_api.S.ENT_LICENSE_ENABLE_TOOLBAR,            enable_toolbar),
    (license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL,       enable_cookie_crawl),
    (license_api.S.ENT_LICENSE_ENABLE_CATEGORY,           enable_category),
    (license_api.S.ENT_LICENSE_ENABLE_SSO,                enable_sso),
    (license_api.S.ENT_LICENSE_DATABASES,                 enable_databases),
    (license_api.S.ENT_LICENSE_FEEDS,                     enable_feeds),
    (license_api.S.ENT_LICENSE_FILESYSTEM,                enable_filesystem),
    (license_api.S.ENT_LICENSE_BATCH_CRAWL,               enable_batchcrawl),
    (license_api.S.ENT_LICENSE_QUERY_EXPANSION,           enable_query_expansion),
    (license_api.S.ENT_LICENSE_SCORING_ADJUST,            enable_scoring_adjust),
    (license_api.S.ENT_LICENSE_CLUSTERING,                enable_clustering),
    (license_api.S.ENT_LICENSE_LABS_SETTINGS,             labs_settings),
    #
    # [Kerberos/IWA] ...
    #
    (license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN,   # [Kerberos/IWA]
                               enable_kerberos_at_login),
    (license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL,   # [Kerberos/IWA]
                               enable_kerberos_at_crawl),
    (license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE,   # [Kerberos/IWA]
                               enable_kerberos_at_serve),
    (license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE,   # [Kerberos/IWA]
                               enable_kerberos_kt_parse),
    (license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX,  # [Kerberos/IWA]
                               enable_kerberos_at_onebox),
    #
    # [Kerberos/IWA] ... done.
    #
    (license_api.S.ENT_LICENSE_GRACE_PERIOD,              grace_period_ms),):
    if value != None: license_map[name] = value

  return EnterpriseLicense(license_map)

class EnterpriseLicense:
  """An enterprise license"""

  # constructs a license from a dictionary of license values
  def __init__(self, license):
    self.license = copy.deepcopy(license)
    from google3.enterprise.legacy.install import install_utilities
    self.validator = install_utilities.get_param_validator(
                                         'ENT_LICENSE_INFORMATION')

  ########
  # accessors

  # returns string
  def getLicenseId(self):
    return self.license.get(license_api.S.ENT_LICENSE_ID, None)

  # returns string
  def getBoxId(self):
    return self.license.get(license_api.S.ENT_BOX_ID, None)

  # returns long (date in ms since epoch)
  def getCreationDate(self):
    return self.license.get(license_api.S.ENT_LICENSE_CREATION_DATE, None)

  # returns long (date in ms since epoch)
  def getEndDate(self):
    return self.license.get(license_api.S.ENT_LICENSE_END_DATE, None)

  # returns long (time in ms)
  def getGracePeriod(self):
    return self.license.get(license_api.S.ENT_LICENSE_GRACE_PERIOD, 0L)

  # returns long (count)
  def getMaxNumCollections(self):
    return self.license.get(license_api.S.ENT_LICENSE_MAX_COLLECTIONS, None)

  # returns long (count)
  def getMaxNumFrontends(self):
    return self.license.get(license_api.S.ENT_LICENSE_MAX_FRONTENDS, None)

  # returns long (count)
  def getMaxPagesOverall(self):
    return self.license.get(license_api.S.ENT_LICENSE_MAX_PAGES_OVERALL, None)

  # returns long (count)
  def getMaxPagesPerCollection(self):
    return self.license.get(license_api.S.ENT_LICENSE_MAX_PAGES_PER_COLLECTION,
                            None)

  # returns long (time in ms)
  def getTimeLeft(self):
    return self.license.get(license_api.S.ENT_LICENSE_LEFT_TIME, 0L)

  # returns 0/1 (boolean)
  def getEnableSekuLite(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_SEKU_LITE, 0)

  # returns 0/1 (boolean)
  def getEnableLdap(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_LDAP, 0)

  # returns 0/1 (boolean)
  def getEnableToolbar(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_TOOLBAR, 0)

  # returns 0/1 (boolean)
  def getEnableCookieCrawl(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_COOKIE_CRAWL, 0)

  # returns 0/1 (boolean)
  def getEnableCategory(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_CATEGORY, 0)

  # returns 0/1 (boolean)
  def getEnableSso(self):
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_SSO, 0)

  # returns 0/1 (boolean)
  def getEnableDatabases(self):
    return self.license.get(license_api.S.ENT_LICENSE_DATABASES, 1)

  # returns 0/1 (boolean)
  def getEnableFeeds(self):
    return self.license.get(license_api.S.ENT_LICENSE_FEEDS, 1)

  # returns 0/1 (boolean)
  def getEnableFilesystem(self):
    return self.license.get(license_api.S.ENT_LICENSE_FILESYSTEM, 1)

  # returns 0/1 (boolean)
  def getEnableBatchCrawl(self):
    return self.license.get(license_api.S.ENT_LICENSE_BATCH_CRAWL, 0)

  # returns 0/1 (boolean)
  def getEnableQueryExpansion(self):
    return self.license.get(license_api.S.ENT_LICENSE_QUERY_EXPANSION, 1)

  # returns 0/1 (boolean)
  def getEnableClustering(self):
    return self.license.get(license_api.S.ENT_LICENSE_CLUSTERING, 1)

  # returns int to indicate available scoring adjust options
  def getEnableScoringAdjust(self):
    return self.license.get(license_api.S.ENT_LICENSE_SCORING_ADJUST, 1)

  # returns long (problem status)
  def getProblemStatus(self):
    status = self.license.get(license_api.S.ENT_LICENSE_PROBLEMS, None)
    if None == status:
      return C.LIC_OK
    else:
      return status

  # returns string of labs settings (may be empty or None)
  def getLabsSettings(self):
    return self.license.get(license_api.S.ENT_LICENSE_LABS_SETTINGS, None)

  #
  # [Kerberos/IWA] ...
  #
  
  # returns 0/1 (boolean)
  def getEnableKerberosAtLogin(self):                     # [Kerberos/IWA]
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_LOGIN,
                            0)
  # returns 0/1 (boolean)
  def getEnableKerberosAtCrawl(self):                     # [Kerberos/IWA]
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_CRAWL,
                            0)
  # returns 0/1 (boolean)
  def getEnableKerberosAtServe(self):                     # [Kerberos/IWA]
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_SERVE,
                            0)
  # returns 0/1 (boolean)
  def getEnableKerberosKtParse(self):                     # [Kerberos/IWA]
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_KERBEROS_KT_PARSE,
                            0)
  # returns 0/1 (boolean)
  def getEnableKerberosAtOnebox(self):                    # [Kerberos/IWA]
    return self.license.get(license_api.S.ENT_LICENSE_ENABLE_KERBEROS_AT_ONEBOX,
                            0)
  #
  # [Kerberos/IWA] ... done.
  #

  # return the underlying python dict
  def getLicenseDict(self):
    return self.license

  ########
  # tests (non mutating)

  # tests if a license is valid (fully and correctly specified).  It must
  # contain the following keys:
  # - these keys are required:
  #    ENT_LICENSE_ID   # an identifier for the license
  #    ENT_BOX_ID   # CONFIG_NAME of box license is intended for
  #    ENT_LICENSE_VERSION   # version of this license
  #    ENT_LICENSE_CREATION_DATE   # date of creation (in ms since epoch)
  #    ENT_LICENSE_GRACE_PERIOD    # grace period after license ends (in ms)
  #    ENT_LICENSE_MAX_COLLECTIONS # license terms (long)
  #    ENT_LICENSE_MAX_FRONTENDS   # license terms (long)
  #    ENT_LICENSE_MAX_PAGES_OVERALL  # license terms (long)
  #    ENT_LICENSE_MAX_PAGES_PER_COLLECTION  # license terms (long)
  #
  # - required, but not in "fresh" licenses*:
  #    ENT_LICENSE_SERVING_TIME   # how long the license will be valid (ms)
  #    ENT_LICENSE_START_DATE   # date license started (ms since epoch)
  #    ENT_LICENSE_END_DATE   # when the license will end (ms since epoch)
  #    ENT_LICENSE_LEFT_TIME  # how much time is left (ms)
  #
  # - one or more of these is required:
  #    ENT_LICENSE_ORIGINAL_END_DATE   # specified end date of license
  #    ENT_LICENSE_ORIGINAL_SERVING_TIME  # specified time before expiration
  #
  # - these are optional:
  #    ENT_LICENSE_ORIGINAL_START_DATE   # specified start date
  #    ENT_LICENSE_ENABLE_SEKU_LITE   # liense terms (0/1)
  #    ENT_LICENSE_ENABLE_LDAP  # liense terms (0/1)
  #    ENT_LICENSE_ENABLE_TOOLBAR  # liense terms (0/1)
  #    ENT_LICENSE_ENABLE_COOKIE_CRAWL  # liense terms (0/1)
  #    ENT_LICENSE_ENABLE_CATEGORY  # liense terms (0/1)
  #    ENT_LICENSE_ENABLE_SSO  # liense terms (0/1)
  #    ENT_LICENSE_DATABASES
  #    ENT_LICENSE_FEEDS
  #
  # * "fresh" licenses:
  #   When a license is created, it says how long the license is valid or
  #   when it should expire.  After it is installed, it will contain a few
  #   additional fields which say how long the license has _left_.  Before
  #   a license is installed, it is known as "fresh".  The fresh_license
  #   flag will make isInvalid take freshness into consideration.
  #
  # returns 1 or 0
  def isInvalid(self, fresh_license = 0):
    return self.validate(fresh_license) not in validatorlib.VALID_CODES

  # same as isInvalid, but returns validatorlib.ValidationError
  def validate(self, fresh_license = 0):

    if fresh_license:
      # these keys don't exist in a fresh license.  if that's what we have,
      # we make a copy and add them to fool the validator
      license_map = copy.deepcopy(self.license)
      license_map.update({
        license_api.S.ENT_LICENSE_SERVING_TIME : 1L,
        license_api.S.ENT_LICENSE_START_DATE : 1L,
        license_api.S.ENT_LICENSE_END_DATE : 1L,
        license_api.S.ENT_LICENSE_LEFT_TIME : 1L,
        })
    else:
      license_map = self.license

    # run the validator
    context = validatorlib.ValidatorContext(file_access = 0, dns_access = 0)
    return self.validator.validate(license_map, context)

  # tests whether a license is expired (past the serving time, based on
  # ENT_LICENSE_LEFT_TIME, and the grace period)
  def isExpired(self):
    time_left = self.license.get(license_api.S.ENT_LICENSE_LEFT_TIME, 0L)
    grace = self.license.get(license_api.S.ENT_LICENSE_GRACE_PERIOD, 0L)
    return (time_left + grace) <= 0L

  # tests if a license is in the grace period (past the serving time, based on
  # ENT_LICENSE_LEFT_TIME, but not yet expired)
  def isInGracePeriod(self):
    time_left = self.license.get(license_api.S.ENT_LICENSE_LEFT_TIME, 0L)
    grace = self.license.get(license_api.S.ENT_LICENSE_GRACE_PERIOD, 0L)
    return time_left <= 0L and (time_left + grace) > 0L

  # tests if a license has started yet
  def hasStarted(self):
    now = long(time.time() * 1000)
    return self.license.get(license_api.S.ENT_LICENSE_START_DATE, 0L) < now

  ########
  # modifiers

  # When installing a "fresh" license, a few values must be filled in to make
  # it usable ("not so fresh"??).  This method will take a "fresh" license and
  # complete these fields, in order to make the license valid.
  #
  # The license can specify terms as either a) a fixed end date
  # (ENT_LICENSE_ORIGINAL_END_DATE) or b) a fixed length of time after the
  # license is installed (ENT_LICENSE_ORIGINAL_SERVING_TIME).   It can also
  # optionally specify a start date (ENT_LICENSE_ORIGINAL_START_DATE); this
  # would otherwise be the date the license is installed.
  #
  # This method reconciles the license terms and computes values for
  # ENT_LICENSE_START_DATE, ENT_LICENSE_END_DATE, and ENT_LICENSE_SERVING_TIME
  # which are used for license operation.
  def initServingTime(self):
    realStartDate    = 0L
    realEndDate      = 0L
    realServingTime  = 0L
    curDate          = long(time.time() * 1000)

    # get the original license terms
    origStartDate    = self.license.get(
        license_api.S.ENT_LICENSE_ORIGINAL_START_DATE, 0L)
    creationDate     = self.license.get(
        license_api.S.ENT_LICENSE_CREATION_DATE, 0L)
    origEndDate      = self.license.get(
        license_api.S.ENT_LICENSE_ORIGINAL_END_DATE, 0L)
    origServingTime  = self.license.get(
        license_api.S.ENT_LICENSE_ORIGINAL_SERVING_TIME, 0L)

    if creationDate == 0 or (origServingTime == 0 and origEndDate == 0):
      # this license is invalid:
      # - either ENT_LICENSE_ORIGINAL_END_DATE or
      #   ENT_LICENSE_ORIGINAL_SERVING_TIME must be given
      # - ENT_LICENSE_CREATION_DATE must be given
      logging.error("license is invalid, can't initServingTime()")
      return

    # figure out when the license starts
    if origStartDate  > 0:
      # a start date was given; the license starts on that date
      realStartDate = origStartDate
    else:
      # no start date, start now.  if the creation date is in the future, use
      # that instead
      realStartDate = max([creationDate, curDate])

    if origEndDate > 0:
      # an end date was given; calculate the serving time
      realEndDate = origEndDate
      realServingTime =  realEndDate - realStartDate
    else: # origServingTime > 0
      # a serving time was given; calculate the end date
      realServingTime = origServingTime
      realEndDate = realStartDate + realServingTime

    self.license[license_api.S.ENT_LICENSE_START_DATE]   = realStartDate
    self.license[license_api.S.ENT_LICENSE_END_DATE]     = realEndDate
    self.license[license_api.S.ENT_LICENSE_SERVING_TIME] = realServingTime

    # makes ENT_LICENSE_LEFT_TIME get set
    self.updateTimeLimit(0L)

  # This method is used to update a license to tell it how much accumulated
  # time has passed since it was started.
  # The license keeps track of how much time is left in two ways: 1) by end
  # date; it compares ENT_LICENSE_END_DATE to the current date , and 2) by
  # time passed; it compares ENT_LICENSE_LEFT_TIME to the time passed reported
  # in calls to this method.
  # This method will take these two factors into account, and compute a new
  # value for ENT_LICENSE_LEFT_TIME.
  def updateTimeLimit(self, count):
    curDate = long(time.time()*1000)
    endDate = self.license.get(license_api.S.ENT_LICENSE_END_DATE, 0L)
    servingTime = self.license.get(license_api.S.ENT_LICENSE_SERVING_TIME, 0L)

    timeLeftByDate = endDate - curDate;
    timeLeftByCount = servingTime - count

    # take the minimum
    timeLeft = min([timeLeftByDate, timeLeftByCount])
    self.license[license_api.S.ENT_LICENSE_LEFT_TIME] = timeLeft


#############################################################################
# LicenseParser provides a method to parse a license string into an
# EnterpriseLicense object
class LicenseParser:
  def parseLicense(self, license_data):
    license = {}
    try:
      config_utils.SafeExec(license_data, license)
    except:
      return None
    return EnterpriseLicense(license)


#############################################################################
# LicenseDecryptor provides a method to decrypt an encrypted/signed license
# file and return the contained license text.

# enterprise license file format:
# the following diagram shows how an encrypted enterprise license is
# constructed.  the actual license body is newline seperated python
# variable assignments.
#
#  ________________________________
# | ~gpg signed file~              | <-- GPG signed file (signed by license
# | CONTENTS:                      |     signing key; same for all licenses).
# | ____________________________   |
# || NAME1 = VALUE\n            |<-+---- text header. this is a subset of
# || NAME2 = VALUE\n            |  |     the real license, but isn't encypted
# || ...                        |  |
# ||____________________________|  |
# || \n\n                       |<-+---- "\n\n" seperates header from:
# ||____________________________|  |
# || ~gpg encrypted file~       |<-+---- GPG encrypted file (with box keys;
# || CONTENTS:                  |  |     unique per box)
# || ________________________   |  |
# ||| ~tar file~             |<-+--+---- gzipped tar file
# ||| license.txt:           |  |  |
# ||| ____________________   |  |  |
# |||| NAME1 = VALUE\n    |<-+--+--+---- license.txt
# |||| NAME2 = VALUE\n    |  |  |  |
# |||| ...                |  |  |  |
# ||||____________________|  |  |  |
# |||________________________|  |  |
# ||____________________________|  |
# |________________________________|


# possible decryptLicense() status codes:
DECRYPT_OK = 'DECRYPT_OK'
DECRYPT_SYSTEM_ERROR = 'DECRYPT_SYSTEM_ERROR'
DECRYPT_GPG_VERIFY_FAILED = 'DECRYPT_GPG_VERIFY_FAILED'
DECRYPT_BAD_HEADER = 'DECRYPT_BAD_HEADER'
DECRYPT_GPG_DECRYPT_FAILED = 'DECRYPT_GPG_DECRYPT_FAILED'
DECRYPT_TAR_FAILED = 'DECRYPT_TAR_FAILED'

class LicenseDecryptor:
  def __init__(self, working_dir,
               box_public_keyring, box_private_keyring,
               license_public_keyring):
    self.working_dir = working_dir
    self.box_public_keyring = box_public_keyring
    self.box_private_keyring = box_private_keyring
    self.license_public_keyring = license_public_keyring

  # check that all required files exist
  def checkFiles(self):
    for dir in [self.working_dir]:
      if not os.path.isdir(dir):
        logging.error("directory %s doesn't exist" % dir)
        return 0
      if not os.path.isabs(dir):
        logging.error("directory %s is not an absolute path" % dir)
        return 0

    for file in [self.box_private_keyring,
                 self.box_public_keyring,
                 self.license_public_keyring]:
      if not os.path.isfile(file):
        logging.error("key file %s doesn't exist" % file)
        return 0
      if not os.path.isabs(file):
        logging.error("file %s is not an absolute path" % file)
        return 0

    return 1

  # decryptLicense:
  # takes an encrypted license body (string) (see diagram above)
  #
  # returns a (decrypted_license_body, decrypted_header_body,status_code) tuple
  # - status_code will be one of the codes defined below.  Any thing besides
  #   DECRYPT_OK indicates a failure.
  # - decrypted_license_body will be a string or None:
  #  - if status is DECRYPT_OK, will be full license body
  #  - otherwise, will be None
  # - decrypted_header_body will be a string or None (if there is an error)
  #  - will always by not None if decrypted_license_body is not None
  # Do not use a license if the decryptor doesn't return DECRYPT_OK.  If
  # possible, it will return the header (a non-encrypted, incomplete subset
  # of the license body).
  #
  def decryptLicense(self, encrypted_license):
    tempdir = E.mktemp(self.working_dir, 'decrypt')

    signed_fn = E.joinpaths([tempdir, "license.signed"])
    verified_fn = E.joinpaths([tempdir, "license.verified"])
    encrypted_fn = E.joinpaths([tempdir, "license.encrypted"])
    tgz_fn = E.joinpaths([tempdir, "license.tgz"])
    license_fn = E.joinpaths([tempdir, "ent_license.config"])

    if not self.checkFiles():
      logging.error("decryptor keys don't exist or aren't valid")
      return None, None, DECRYPT_SYSTEM_ERROR

    try:
      # make the temp directory
      os.system("rm -rf %s" % commands.mkarg(tempdir))
      os.makedirs(tempdir)

      # output to a file
      try:
        open(signed_fn, 'w').write(encrypted_license)
      except IOError:
        logging.error("writing encrypted license failed")
        return None, None, DECRYPT_SYSTEM_ERROR

      # verify signature
      verify_cmd = ("gpg --no-options --no-default-keyring --no-tty"
                    " --no-verbose --yes --keyring %s -o %s --decrypt %s") % (
        commands.mkarg(self.license_public_keyring),
        commands.mkarg(verified_fn),
        commands.mkarg(signed_fn))

      # When gpg is given a file with no signature it returns successfully;
      # so we must check gpg's output
      fi, foe = os.popen4(verify_cmd)
      fi.close()
      gpg_result = foe.read()
      foe.close()
      if gpg_result.find("Good signature") == -1:
        logging.error("verifying license signature failed")
        return None, None, DECRYPT_GPG_VERIFY_FAILED

      # remove header
      verified_body = open(verified_fn, 'r').read()
      sep_poi = string.find(verified_body, "\n\n")
      if sep_poi < 0:
        logging.error("license doesn't have valid header")
        return None, None, DECRYPT_BAD_HEADER

      # NOTE: At this point, we've read the header, which is a subset of the
      # actual license (which we can't see yet, because it's encrypted).  If
      # we fail past this point, we return the header in place of the license
      # because it will look like an invalid license, and allow us to report
      # some basic information about the license.
      #
      header_body = verified_body[0:sep_poi]

      # write out the encrypted body
      try:
        open(encrypted_fn, 'w').write(verified_body[sep_poi+2:])
      except IOError:
        logging.error("writing encrypted license failed")
        return None, header_body, DECRYPT_SYSTEM_ERROR

      # decrypt it
      decrypt_cmd = "gpg --no-options --no-default-keyring --no-tty --yes --keyring %s --secret-keyring %s -o %s --decrypt %s" % (
        commands.mkarg(self.box_public_keyring),
        commands.mkarg(self.box_private_keyring),
        commands.mkarg(tgz_fn),
        commands.mkarg(encrypted_fn))
      if os.system(decrypt_cmd) != 0:
        logging.error("decrypting license failed")
        return None, header_body, DECRYPT_GPG_DECRYPT_FAILED

      # untar it (we only ask for the file we want)
      untar_cmd = "tar xvzf %s -C %s ent_license.config" % (
        commands.mkarg(tgz_fn), tempdir)
      if os.system(untar_cmd) != 0:
        logging.error("untarring license failed")
        return None, header_body, DECRYPT_TAR_FAILED

      # read in the decrypted license
      try:
        license_body = open(license_fn, 'r').read()
      except IOError:
        logging.error("reading decrypted license failed")
        return None, header_body, DECRYPT_SYSTEM_ERROR
    finally:
      # make sure to clean up all the temp files
      os.system("rm -rf %s" % commands.mkarg(tempdir))

    return license_body, header_body, DECRYPT_OK


#############################################################################
# LicenseEncryptor provides a method to encrypt an text license and return
# an encrypted/signed enterprise license file

class LicenseEncryptor:
  def __init__(self, working_dir,
               box_public_keyring, box_private_keyring,
               license_public_keyring, license_private_keyring,
               google_key_passphrase):
    self.working_dir = working_dir
    self.box_public_keyring = box_public_keyring
    self.box_private_keyring = box_private_keyring
    self.license_public_keyring = license_public_keyring
    self.license_private_keyring = license_private_keyring
    self.passphrase = google_key_passphrase

  # check that all required files exist
  def checkFiles(self):
    for dir in [self.working_dir]:
      if not os.path.isdir(dir):
        logging.error("directory %s doesn't exist" % dir)
        return 0
      if not os.path.isabs(dir):
        logging.error("directory %s is not an absolute path" % dir)
        return 0

    for file in [self.box_private_keyring,
                 self.box_public_keyring,
                 self.license_public_keyring,
                 self.license_private_keyring]:
      if not os.path.isfile(file):
        logging.error("key file %s doesn't exist" % file)
        return 0
      if not os.path.isabs(file):
        logging.error("file %s is not an absolute path" % file)
        return 0

    return 1

  # helper: takes an EnterpriseLicense and returns a dictionary containing
  # values suitable for the license file header.
  def extractHeader(self, license):
    return {'ENT_BOX_ID' :          license.getBoxId(),
            'ENT_LICENSE_ID' :      license.getLicenseId(),
            'ENT_LICENSE_VERSION' : CURRENT_LICENSE_VERSION,
            }

  # encryptLicense takes:
  # - a license (EnterpriseLicense)
  # - an optional passphrase (will override passphrase given in constructor)
  #
  # returns an encrypted license body (string) (see diagram above) or None
  # if an error occurs
  def encryptLicense(self, license, passphrase = None):
    tempdir = E.mktemp(self.working_dir, 'encrypt')

    # if no passphrase supplied, use the one given in the constructor
    if passphrase == None:
      passphrase = self.passphrase

    # make sure the license is valid (note that this is a fresh license)
    if license.isInvalid(fresh_license = 1):
      logging.error("license is not valid")
      return None

    if not self.checkFiles():
      logging.error("encryptor keys don't exist or aren't valid")
      return None

    # get the header
    header = self.extractHeader(license)

    # NOTE: this ent_license.config is important; the old license code expects
    # to find this filename.  do not change it
    license_fn = E.joinpaths([tempdir, "ent_license.config"])
    tgz_fn = E.joinpaths([tempdir, "license.tgz"])
    encrypted_fn = E.joinpaths([tempdir, "license.encrypted"])
    encrypted_w_header_fn = E.joinpaths([tempdir, "license.header"])
    signed_fn = E.joinpaths([tempdir, "license.signed"])

    try:
      # make the temp directory
      os.system("rm -rf %s" % commands.mkarg(tempdir))
      os.makedirs(tempdir)

      # write the raw license body to a file
      license_body = {}
      license_body.update(license.license)
      # overwrite the version number with the current version (just in case)
      license_body['ENT_LICENSE_VERSION'] = CURRENT_LICENSE_VERSION

      try:
        body_str = string.join(map(lambda (k,v): '%s = %s' % (k,repr(v)),
                                   license_body.items()),
                               '\n')
        open(license_fn, 'w').write(str(body_str))
      except IOError:
        logging.error("writing plain license failed")
        return None

      # tar the license body
      tar_cmd = "tar zvcf %s -C %s %s" % (
        commands.mkarg(tgz_fn),
        commands.mkarg(os.path.dirname(license_fn)),
        commands.mkarg(os.path.basename(license_fn)))
      if os.system(tar_cmd) != 0:
        logging.error("tarring license failed")
        return None

      # encrypt it
      encrypt_cmd = "gpg --no-options --no-default-keyring --no-secmem-warning  --no-tty --yes --default-recipient-self --keyring %s --secret-keyring %s -o %s -se %s" % (
        commands.mkarg(self.box_public_keyring),
        commands.mkarg(self.box_private_keyring),
        commands.mkarg(encrypted_fn),
        commands.mkarg(tgz_fn))
      if os.system(encrypt_cmd) != 0:
        logging.error("encrypting license failed")
        return None

      # write out the header (plus \n\n) to encrypted_w_header_fn
      try:
        header_str = string.join(map(lambda (k,v): '%s = %s' % (k,repr(v)),
                                     header.items()),
                                 '\n')
        header_str = header_str + '\n\n' # end of header
        open(encrypted_w_header_fn, 'w').write(header_str)
      except IOError:
        logging.error("writing license header failed")
        return None

      # append the encrypted tarred license to encrypted_w_header_fn
      cat_cmd = "cat %s >> %s" % (
        commands.mkarg(encrypted_fn),
        commands.mkarg(encrypted_w_header_fn))
      if os.system(cat_cmd) != 0:
        logging.error("reading encrypted license failed")
        return None

      # sign encrypted_w_header_fn
      sign_cmd = "gpg --no-options --no-default-keyring --no-tty --no-secmem-warning --keyring %s --secret-keyring %s --passphrase-fd 0 --yes -o %s -s %s" % (
        commands.mkarg(self.license_public_keyring),
        commands.mkarg(self.license_private_keyring),
        commands.mkarg(signed_fn),
        commands.mkarg(encrypted_w_header_fn))
      try:
        # use popen so that we can write the passphrase to stdin
        sign_fd = os.popen(sign_cmd, 'w')
        if passphrase != None:
          sign_fd.write(passphrase)
        status = sign_fd.close()
      except IOError:
        status = -1
      if status != None:
        logging.error("signing license signature failed")
        return None

      # read the signed body
      try:
        signed_body = open(signed_fn, 'r').read()
      except IOError:
        logging.error("reading signed license failed")
        return None

    finally:
      # make sure to clean up all the temp files
      os.system("rm -rf %s" % commands.mkarg(tempdir))

    return signed_body


#############################################################################
# EnterpriseLicenseCounter encapsulates a file which holds a numeric counter.
# It is implemented using a two stage write (with two files) to ensure that we
# never clobber the file if we experience a write error.

class EnterpriseLicenseCounter:
  # takes the filename and the backup_filename
  def __init__(self, filename, back_filename):
    self.filename = filename
    self.back_filename = back_filename
    self.count = 0L
    self.write_order = [filename, back_filename]
    self.error = 0

  ##########
  # accessors

  # sees if there were any load errors; each call to load() will reset this
  # value
  def hasError(self):
    return self.error

  # get the count (a long)
  def getCount(self):
    return self.count

  # returns a list containg the filename and backup_filename, in the order
  # that they will be written when saved to disk.
  def getWriteOrder(self):
    return self.write_order

  # The counter can have a special value (-1), which marks the counter as
  # "not started".  When it is in this state, incrementCount() will have no
  # effect.  It will remain in this state until startCounter() is called.
  def hasStarted(self):
    return self.count >= 0

  ##########
  # modifiers

  # increments the counter by count and calls save()
  # if the counter hasn't started, it will remain unchanged
  def incrementCount(self, count):
    # if the counter hasn't started, don't do anything
    if not self.hasStarted(): return True

    self.count = self.count + count
    return self.save()

  # resets the counter to 0 and calls save()
  # if the counter hasn't started, it will remain unchanged
  def resetCount(self):
    # if the counter hasn't started, don't do anything
    if not self.hasStarted(): return True

    self.count = 0L
    return self.save()

  # starts the counter (sets to 0) if it is unstarted and calls save()
  # if the counter is already started, it will remain unchanged
  def startCounter(self):
    # if the counter has started, don't do anything
    if self.hasStarted(): return True

    self.count = 0L
    return self.save()

  ##########
  # load/save

  # load the counter from files
  def load(self):
    self.error = 0

    # read the counter from both the primary file and backup file
    count = self.getCounterFromFile(self.filename);
    count_bck = self.getCounterFromFile(self.back_filename);

    # We read the value from two files.  It is possible that they have
    # different values, or that they were errors in reading either/both of
    # them.  If we were able to read a value from one of more of them, we want
    # the one with the largest ("freshest") value because that is the most
    # recent value.  In addition, we also determine a write order, such that
    # if there are two files and one is wrong and the other is right,
    # update the wrong one first so that we never have an invalid state on
    # disk. This ensures that if something fails while writing that we never
    # clobber the file with the fresh value, until we've already written a
    # fresher value to the previously invalid file.
    # If we are We are willing to accept

    # helper: tests if my_value is "fresher" (has a more recent counter value)
    #         than other_value
    # - both values are either numbers or None (undefined)
    def is_fresher(my_value, other_value):
      return ( my_value != None and ( other_value == None or
                                      my_value >= other_value) )

    if count == None and count_bck == None:  # both files are undefined
      # we weren't able to read either file; this is an error
      self.count = None
      self.write_order = None
      self.error = 1
    elif ( count == count_bck or             # both files are the same
           is_fresher(count, count_bck) ):   # primary file is fresher
      # use the primary value and write the backup file first
      self.write_order = [ self.back_filename, self.filename ]
      self.count = count
    else:                                    # backup file is fresher
      assert( is_fresher(count_bck, count) )
      # use the backup value and write the primary file first
      self.write_order = [ self.filename, self.back_filename ]
      self.count = count_bck

    return not self.error

  # save the counter files
  def save(self):
    # make sure we loaded sucessfully
    if self.count == None or self.write_order == None:
      return False

    # simply save the current value into both files, in the right order
    for filename in self.write_order:
      if not self.setCounterFile(filename, self.count):
        return False

    return True


  ##########
  # internal methods

  # read a counter from a file; return None on error
  def getCounterFromFile(self, filename):
    """ it reads the count from the counter file.
    return -1 on error """
    try:
      f = open(filename, "r")
      filecontent = f.read()
      f.close()
    except IOError, e:
      logging.error("IOError getting counter %s -- %s" % (filename, e))
      return None
    try:
      logging.info('filecontent = %s, filename = %s' % (filecontent, filename))
      count = long(filecontent)
    except ValueError:
      logging.error("Invalid value for counter read from file: %s" % filename)
      return None

    return count

  # write a counter file
  def setCounterFile(self, filename, count):
    """ it tries to set the file with the given counter. and it will check
    after writing. """
    # if the file already has the right value, we're done
    logging.info('Initial check to see if correct value is there')
    if self.getCounterFromFile(filename) == count: return True
    try:
      f = open(filename, "w")
      f.write(repr(long(count)))
      f.flush()
      if os.fdatasync(f.fileno()): # force data to be written
        logging.error("File %s not written to disk correctly" % filename)
        return False
      assert( f.close() == None )  # make sure close is sucessful
    except ValueError:
      logging.error("Invalid value for counter: %s" % repr(count))
      return False
    except IOError, e:
      logging.error("Error setting count on %s -- %s" % (filename, e))
      return False

    # verify that the file has the right value
    logging.info('Final check to be sure correct value was set')
    return self.getCounterFromFile(filename) == count;

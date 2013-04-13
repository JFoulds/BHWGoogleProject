#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com after the original LicenseManager.java by feng@google.com
# rewritten by: davidw@google.com
# feng@google.com
#
###############################################################################

import threading
import string
import os

from google3.enterprise.legacy.util import C
from google3.enterprise.license import license_api
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import ar_exception
from google3.enterprise.legacy.adminrunner import SendMail
from google3.enterprise.legacy.licensing import ent_license
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.license import license_api

###############################################################################

true  = 1
false = 0

###############################################################################


class LicenseManager:
  """
  The job of this class is to do the actual work for license:
  verify license, view license, import license, etc.
  """

  def __init__(self, cfg, box_key_dir, license_key_dir):
    self.cfg                 = cfg
    self.inInitialization    = true
    self.killingIsRunning    = false
    self.counter_lock        = threading.Lock()
    self.counter_file = cfg.getGlobalParam('ENT_LICENSE_COUNTER_FILE')
    self.counter_back_file = cfg.getGlobalParam('ENT_LICENSE_COUNTER_FILE_BACKUP')

    self.parser              = ent_license.LicenseParser()
    data_dir                 = cfg.getGlobalParam('DATADIR')

    working_dir = E.mktemp(data_dir, "license_manager")
    E.system('rm -rf %s/@*.0license_manager; mkdir -p %s' % (
      data_dir, working_dir))

    box_pub_keyring = E.joinpaths([box_key_dir, "ent_box_key.pub"])
    box_pri_keyring = E.joinpaths([box_key_dir, "ent_box_key.pri"])
    license_pub_keyring = E.joinpaths([license_key_dir,
                                       "google_license_key.pub"])
    self.decryptor = ent_license.LicenseDecryptor(working_dir,
                                                  box_pub_keyring,
                                                  box_pri_keyring,
                                                  license_pub_keyring)

  #############################################################################
  # these change running state

  def setInWorking(self):
    """ get out of initialization """
    self.inInitialization = false

  def setKillingIsRunning(self, running):
    """ if a killing is running already """
    self.killingIsRunning = running;

  #############################################################################

  # External interface (safe to call from handler)

  def getCurrentLicense(self):
    license = self.cfg.getGlobalParam('ENT_LICENSE_INFORMATION')
    return ent_license.EnterpriseLicense(license)

  def increaseCount(self, count):
    """increaseCount increases the counter by given # of seconds"""
    return self.increaseCountInternal(count, false)

  def startCounting(self):
    """
    The license manager will not count until it is started.
    when starting the counting, we need to re-compute the serving time again
    """
    return self.increaseCountInternal(1L, true)

  def viewCurLicense(self):
    """ it prints the current license info - used by LicenseHandler """
    license = self.getCurrentLicense()

    # check license
    if license.isInvalid():
      return license, C.LIC_INVALID

    return license, C.LIC_OK

  def importLicense(self, encrypted_license, view_only):
    """it parses and prints the input license data - used by LicenseHandler"""
    logging.info('Importing encrypted license')
    license_body, header_body, decrypt_status = self.decryptor.decryptLicense(encrypted_license)
    if header_body == None:
      # no license or header was parsed, it's an error
      assert( license_body == None )
      return None, decrypt_status

    elif decrypt_status != ent_license.DECRYPT_OK:
      # license wasn't parsed, but header was.  Since the header is a subset
      # of the actual license, we switch the header in for the license and
      # continue error checking.  It will look like an invalid license and
      # allow us to report some basic information about the license.
      #
      # We go ahead and check the license out because we want to look for
      # clues in the header, but we will still bail out before importing the
      # license.
      #
      # The most likely error is that the license is for a different box; the
      # license body is encrypted with per box keys, but the header isn't.
      assert( header_body != None )
      license_to_parse = header_body

    else:
      # everything is fine, use the license
      assert( license_body != None )
      license_to_parse = license_body

    license = self.parser.parseLicense(license_to_parse)
    if license == None:
      return None, C.LIC_WRONG_FORMAT

    # fill out all fields
    license.initServingTime()

    # check license
    status = self.checkLicenseForImport(license)
    if not self.isGoodStatus(status):
      return license, status

    if decrypt_status != ent_license.DECRYPT_OK:
      # the decryptor gave us a good license, but a bad status; be _extra_
      # careful and refuse to continue
      if decrypt_status == ent_license.DECRYPT_SYSTEM_ERROR:
        # probably a problem with the decryptor
        return license, C.LIC_PARSE
      else:
        # probably a problem with the license
        return license, C.LIC_WRONG_FORMAT

    if not view_only:
      status = self.setLicense(license)
      if self.isGoodStatus(status):
        self.cfg.DoMachineAllocation()
    return license, status

  def importClearLicense(self, license_body):
    """
    - used by LicenseHandler
    This will get a deencripted license, extracts a map and
    sets the parameters of the  license from the new one using setLicense
    -- IMPORTANT: used ONNLY in migration process ---
    """

    license = self.parser.parseLicense(license_body)
    if license == None:
      return None, C.LIC_WRONG_FORMAT

    # make sure the license matches the box id; since the license is already
    # clear, we go ahead and set it
    entConfigName = self.cfg.getGlobalParam('ENT_CONFIG_NAME')
    license.license[license_api.S.ENT_BOX_ID] =  entConfigName

    # check license
    status = self.checkLicenseForImport(license)
    if not self.isGoodStatus(status):
      return license, status

    status = self.setLicense(license)
    return license, status


  #############################################################################

  # Internal methods
  def isGoodStatus(self, status):
    return (status == C.LIC_OK or
            status == C.LIC_WARNING_SMALLER_THAN_LIMIT or
            status == C.LIC_WARNING_LESS_PAGE_NEW_LIC)

  def willingToWorkInternal(self, license, counter):
    """From license point of view, decide if we are willing to crawl/serve """

    logging.info("isInvalid:%s hasError:%s isExpired:%s hasStarted:%s" % (
      license.isInvalid(), counter.hasError(), license.isExpired(),
      license.hasStarted()))

    return ( not license.isInvalid() and
             not counter.hasError() and
             not license.isExpired() and
             license.hasStarted() )

  def checkWillingToWorkInternal(self, license, counter):
    """
    From license point of view, decide if we are willing to
    crawl/serve. This version will throw AdminRunnerException if
    not willing to work
    """
    if license.isInvalid():
      self.cfg.writeAdminRunnerOpMsg(M.MSG_LICENSE_INVALID)
      raise ar_exception.ARException((
        ar_exception.LICENSEINVALID, M.MSG_LICENSE_INVALID))

    if counter.hasError():
      self.cfg.writeAdminRunnerOpMsg(M.MSG_LICENSE_INTERNAL_ERROR)
      raise ar_exception.ARException((
        ar_exception.LICENSEERROR, M.MSG_LICENSE_INTERNAL_ERROR))

    if license.isExpired():
      self.cfg.writeAdminRunnerOpMsg(M.MSG_UI_LICENSE_EXPIRED)
      raise ar_exception.ARException((
        ar_exception.LICENSELIMIT, M.MSG_UI_LICENSE_EXPIRED))

    if not license.hasStarted():
      self.cfg.writeAdminRunnerOpMsg(M.MSG_UI_LICENSE_NOTSTARTEDYET)
      raise ar_exception.ARException((
        ar_exception.LICENSNOTSTARTEDYET, M.MSG_UI_LICENSE_NOTSTARTEDYET))

    return true

  def willingNewCollectionInternal(self, license, counter):
    """
    If we are willing to create new collection
    ** not expired
    ** not exceed ENT_LICENSE_MAX_COLLECTIONS
    """
    if not self.willingToWorkInternal(license, counter):
      return false

    num_collections = len(ent_collection.ListCollections(self.cfg.globalParams))
    maxCollections = license.getMaxNumCollections()
    logging.info("License maxCollections: %s" % maxCollections)
    if (maxCollections != 0L and   # 0 means unlimited
        maxCollections < num_collections + 1):
      return false

    # Later we'll use
    # Log.info(4, "maxCollections: " + maxCollections + "**"
    #      + cfg.getAllCrawlNames().length + "**" + cfg.getAllCrawlNames());
    # if (0 != maxCollections &&
    #     cfg.getAllCrawlNames().length >= maxCollections)
    #   return false;

    return true

  def sendWarningMsg(self, license):
    """
    sendWarningMsg send out an email when:
    * 90, 45, 30, 7, and 1 days before expiration.
    * reminder daily during the grace period.
    * one message after grace period
    it just tried its best to do so.
    """

    # We don't send warning whena we are in install mode
    if self.cfg.getInstallState() == "INSTALL": return

    todoDays = self.cfg.getGlobalParam('ENT_LICENSE_STUFF_TODO_ON_DAYS')
    doneDays = self.cfg.getGlobalParam('ENT_LICENSE_STUFF_DONE_ON_DAYS')

    timeLeft    = license.getTimeLeft()
    daysLeft    = timeLeft/C.DAY_MILLISECONDS + 1;
    if timeLeft < 0:  daysLeft = daysLeft - 1;
    graceTime = license.getGracePeriod()

    wasDone = None
    # We send a message under several conditions.  In each case we check
    # doneDays to see if we've already sent an email for this day.  Note
    # that for the isExpired() check, we use C.LONG_MIN_VALUE (instead of the
    # usual daysLeft) since we only want to send a single expiration message
    if license.isExpired() and C.LONG_MIN_VALUE not in doneDays:
      # license is expired; send an email only once!
      SendMail.send(
        self.cfg, None, false,
        M.WAR_LICENSE_EMAIL_SUBJECT_EXPIRED,
        M.WAR_LICENSE_EMAIL_EXPIRED,
        true);
      wasDone = C.LONG_MIN_VALUE
    elif license.isInGracePeriod() and daysLeft not in doneDays:
      # license is in grace period; send an email every day!
      graceDaysLeft = (timeLeft + graceTime) / C.DAY_MILLISECONDS + 1
      SendMail.send(
        self.cfg, None, false,
        M.WAR_LICENSE_EMAIL_SUBJECT_IN_GRACE_PERIOD % (graceDaysLeft),
        M.WAR_LICENSE_EMAIL_IN_GRACE_PERIOD % (graceDaysLeft),
        true)
      wasDone = daysLeft
    elif daysLeft in todoDays and daysLeft not in doneDays:
      # time to send a warning (as dictated by todoDays)
      graceDays = (graceTime + C.DAY_MILLISECONDS - 1) / C.DAY_MILLISECONDS
      SendMail.send(
        self.cfg, None, false,
        M.WAR_LICENSE_EMAIL_SUBJECT_EXPIRING % daysLeft,
        M.WAR_LICENSE_EMAIL_EXPIRING % ( daysLeft, graceDays),
        true)
      wasDone = daysLeft

    # if a message was sent, record it into ENT_LICENSE_STUFF_DONE_ON_DAYS
    if wasDone != None:
      doneDays.append(wasDone)
      self.cfg.setGlobalParam('ENT_LICENSE_STUFF_DONE_ON_DAYS',
                              doneDays)

  def updateOptionalParams(self, license, old_license):
    """
    this update the optional function params
    if license explicitly specify some optional functions, use license's value
    """
    if license.getEnableSekuLite() != old_license.getEnableSekuLite():
      # only "twist" serving if we're not in CONFIG_FILES_INITIALIZED state
      if (self.cfg.getGlobalParam(C.ENT_SYSTEM_INIT_STATE) !=
             C.CONFIG_FILES_INITIALIZED):
        for t in ["gws", "headrequestor"]:
          self.cfg.globalParams.WriteConfigManagerServerTypeRestartRequest(t)
        pass
      # regenerate stylesheets for all frontend
      ent_collection.GenerateStylesheets(self.cfg.globalParams, 0)

    pass

  def enforceLicense(self, license, counter):
    """
    This method enforces the license; it will stop serving if necessary.
    """
    # don't enforce the license if we're initializing or already killing
    if self.inInitialization or self.killingIsRunning:
      return

    if not self.willingToWorkInternal(license, counter):
      logging.info("not willing to work, starting LicenseManagerKiller")
      # no synchronization, but it's fine. we'll try again later anyway
      self.killingIsRunning = true
      # TODO : Stop serving when license stops
      # new Thread(new LicenseManagerKiller(this)).start();
    # send an email (if it's needed)
    self.sendWarningMsg(license)

  def checkLicenseForImport(self, license):
    # check for ENT_BOX_ID
    boxId = self.cfg.getGlobalParam('ENT_CONFIG_NAME')
    licenseBoxId = license.getBoxId()
    if ( licenseBoxId != None and
         string.upper(boxId) != string.upper(licenseBoxId) ):
      logging.error("License not importable: wrong box id (%s)" % licenseBoxId)
      return C.LIC_WRONG_BOX_ID

    # make sure license is valid (independent of the current license)
    if license.isInvalid():
      logging.error("License not importable: invalid")
      return C.LIC_INVALID


    curLic = self.getCurrentLicense()

    # check license date against the current license
    if license.getCreationDate() <= curLic.getCreationDate():
      # license is outdated (new license create time <= old license time)
      # (this come from EnterpirseLicense.UpdateServingTime)
      logging.error("License not importable: old license!")
      return C.LIC_OUTDATED

    # check max # of collection limit against existing collections
    num_collections = len(ent_collection.ListCollections(self.cfg.globalParams))
    license_num_collections = license.getMaxNumCollections()
    if (license_num_collections != 0L and
        license_num_collections < num_collections):
      logging.error("License not importable: too many collections exist.")
      return C.LIC_TOOMANYCOLLECTIONS

    # check new license limit against user defined maximum crawled URLs
    license_limit = int(license.getMaxPagesOverall())
    user_defined_limit = self.cfg.getGlobalParam('USER_MAX_CRAWLED_URLS')
    if license_limit < user_defined_limit:
      logging.error("The maximum overall number of pages is less than the"\
                    "user defined value")
      return C.LIC_WARNING_SMALLER_THAN_LIMIT

    # check new license limit and compare it with the previous license
    cur_license_limit = int(curLic.getMaxPagesOverall())
    if ( cur_license_limit == 0 and license_limit != 0 ) or \
       ( cur_license_limit > license_limit ):
      logging.error("Current license has more pages than new license")
      return C.LIC_WARNING_LESS_PAGE_NEW_LIC

    return C.LIC_OK

  #############################################################################

  # WARNING: all use of this method and any references to the counter it
  # returns) MUST be protected by self.counter_lock

  def getLicenseCounter(self):
    counter = ent_license.EnterpriseLicenseCounter(self.counter_file,
                                                   self.counter_back_file)
    counter.load()
    return counter


  #############################################################################

  # lock safe entry points - these methods are lock safe and should be the only
  # places where self.getLicenseCounter() is called

  def setLicense(self, license):
    """
    This sets the currnet license from the map. It does some checks:
    - used by LicenseHandler
    ++ if the license is newer
    ++ if the license doesn't say anything about serving time, should have a
        currect working license
    """

    self.counter_lock.acquire()
    try:
      curLic = self.getCurrentLicense()
      counter = self.getLicenseCounter()

      # check license for import
      status = self.checkLicenseForImport(license)
      if not self.isGoodStatus(status):
        return status

      # save the license
      self.cfg.setGlobalParam('ENT_LICENSE_INFORMATION', license.license)

      # reset and save counter
      self.cfg.setGlobalParam('ENT_LICENSE_STUFF_DONE_ON_DAYS', [])
      # reset and save
      if not counter.resetCount():
        logging.error("importLicense: counter reset failed")

      # perform any side effects of changing the license
      self.updateOptionalParams(license, curLic)

      self.cfg.saveParams()

      # enfoce the new license
      self.enforceLicense(license, counter)
    finally:
      self.counter_lock.release()

    return C.LIC_OK


  def increaseCountInternal(self, count, startCounting):
    """
    it tries to increase the counter.
     ** to prevent from corruption, it writes to two files
     ** it also checks to enforce the serving time limit
    """

    self.counter_lock.acquire()
    try:
      counter = self.getLicenseCounter()
      license = self.getCurrentLicense()

      # only mess with the counter if the license has started.  make sure
      # that we still enforce the license to avoid setting the time back to
      # pre license.
      if not license.hasStarted():
        logging.debug("license hasn't started; not incrementing")
      else:
        # if the counter hasn't started and we _want_ to start it, do so
        if not counter.hasStarted() and startCounting:
          logging.debug('starting counter')
          if not counter.startCounter(): return false

        # increment and save (if the counter hasn't started, it will ignore)
        if not counter.incrementCount(count):
          # log that we couldn't increment counter
          logging.info('Could not increment license counter')
          return false

        # update license to reflect the new counter value
        license.updateTimeLimit(counter.getCount())

        # save changes to the license
        self.cfg.setGlobalParam('ENT_LICENSE_INFORMATION', license.license)

      # make sure that we enforce any changes to the license (even if the
      # license hasn't started)
      self.enforceLicense(license, counter)
    finally:
      self.counter_lock.release()

    return true

  def willingToWork(self):
    self.counter_lock.acquire()
    try:
      license = self.getCurrentLicense()
      counter = self.getLicenseCounter()
      return self.willingToWorkInternal(license, counter)
    finally:
      self.counter_lock.release()
    return None # never reached; make pychecker happy

  def willingNewCollection(self):
    self.counter_lock.acquire()
    try:
      license = self.getCurrentLicense()
      counter = self.getLicenseCounter()
      return self.willingNewCollectionInternal(license, counter)
    finally:
      self.counter_lock.release()
    return None # never reached; make pychecker happy

  def getMaxPagesOverall(self):
    """Get the value from license, also consider about the hardlimit"""
    max_pages = self.getCurrentLicense().getMaxPagesOverall()
    hard_limit = self.cfg.globalParams.getMaxPagesHardLimit()
    if max_pages == ent_license.kUnlimitedMaxPagesOverall or \
       max_pages > hard_limit:
      max_pages = hard_limit
    return max_pages

  #############################################################################

##protected final class LicenseManagerKiller implements Runnable{
##   * This is to run function that kills the serving in a separate thread
##    private LicenseManager lm;
##    public LicenseManagerKiller(LicenseManager lm) {
##      this.lm = lm;
##    }

##    public void run() {
##      try {
##        AdminRunner.stopWholeRunning();
##        // don't kill so frequently, sleep for 30 minutes anyway
##        Thread.sleep(1800L * 1000L);
##      } catch (Exception e) {
##        Log.error("stopWholeRunning failed!");
##      }// we'll try again later anyway
##      lm.setKillingIsRunning(false);
##    }
##  }
##}

###############################################################################

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com
#
# The handlers handles prerequisites and epoch advance commands
#
###############################################################################

import commands
import os
import string
import sys
import threading
import time

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import SendMail
from google3.enterprise.legacy.production.babysitter import validatorlib

###############################################################################

class EpochHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params, cfg = None):
    # cfg is non-null only for testing (we cannot have multiple constructore)
    if cfg != None:
      self.cfg = cfg
      return

    self.epoch_lock_ = threading.Lock()
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "prereq_check":       admin_handler.CommandInfo(
      1, 1, 0, self.prereq_check),
      "advance" :           admin_handler.CommandInfo(
      0, 0, 0, self.advance),
      "get_prisoners" :     admin_handler.CommandInfo(
      0, 0, 0, self.get_prisoners),
      "drain_urlmanagers" : admin_handler.CommandInfo(
      0, 0, 0, self.drain_urlmanagers),
      "crawl_this_url" :  admin_handler.CommandInfo(
      1, 0, 0, self.crawl_this_url),
      "recrawl_url_patterns" : admin_handler.CommandInfo(
      0, 0, 1, self.recrawl_url_patterns),
      "start_crawlmanager_batch" :  admin_handler.CommandInfo(
      0, 0, 0, self.start_crawlmanager_batch),
      }

  #############################################################################

  def prereq_check(self, send_email, collections):
    """
    This checks the prerequisites for all collection, updates the epochs to
    serve from and (optionally) sends a mail.
    """
    if collections != None:
      collections = string.strip(collections)
    if not collections:
      collections = ent_collection.ListCollections(self.cfg.globalParams)
    else:
      collections = map(lambda c, p = self.cfg.globalParams:
                        ent_collection.EntCollection(c, p),
                        map(string.strip, string.split(collections, ","))
                        )
    # No collections -- exit quickly
    if not collections:
      return {}

    send_email = string.atoi(send_email)
    epochs = self.cfg.getGlobalParam('ENTERPRISE_EPOCHS')
    gwssers = self.cfg.globalParams.GetServerHostPorts("web")
    jobs = []
    for c in collections:
      collection = ent_collection.EntCollection(c, self.cfg.globalParams)
      # Write the testwords in a copy file
      filename = collection.get_var('TESTWORDS')
      filename_copy = "%s_" % filename
      open(filename_copy, "w").write(open(filename, "r").read())
      num = collection.get_var("TESTWORDS_IN_FIRST")
      jobs.append((self.cfg, gwssers, c, filename_copy, epochs, num))


    # Lock a file so we test once at a time
    lock_file = "%s/prerequisites_lock" % self.cfg.getGlobalParam("TMPDIR")
    flock = E.acquire_lock(lock_file, 12)

    try:
      # Run the tests -- one per thread ...
      # see how many threads to spawn
      if len(jobs) >= NUM_THREADS:
        num_threads = NUM_THREADS
      else:
        num_threads = len(jobs)

      # create the threads - workers
      threads = []
      for n in range(0, num_threads):
        threads.append(Runner(n, jobs))

      # start the threads
      for thread in threads[:-1]:
        thread.start()
      # I run the last one
      threads[-1].run()

      # wait to collect the errors at the end
      errors = threads[-1].errors
      max_epochs = threads[-1].max_epochs
      for thread in threads[:-1]:
        thread.join()
        for k, v in thread.max_epochs.items():
          max_epochs[k] = v
        for k, v in thread.errors.items():
          errors[k] = v

      # prepare and send a nice :) message
      if errors and send_email:
        last_msg_time = self.cfg.getGlobalParam('LAST_PREREQUISITES_EMAIL_TIME')
        email_interval  = self.cfg.getGlobalParam('ENTERPRISE_INTER_EMAIL_TIME')
        now = int(time.time())
        if now - last_msg_time > email_interval:
          msg = [M.MSG_PREREQ_FAIL]
          msg.extend(map(
            lambda (c, e): "Collection %s generated a wrong answer for %s" %
            (c, string.join(e, ",")), errors.items()))
          SendMail.send(self.cfg, None, 1, M.MSG_PREREQ_FAIL_SUBJECT,
                        string.join(msg, "\n"), 1)
          self.cfg.globalParams.set_var('LAST_PREREQUISITES_EMAIL_TIME', now)

      self.cfg.globalParams.set_var('LAST_PREREQUISITES_CHECK',
                                    time.strftime("%Y/%m/%d %H:%M:%S"))

      epochs.sort()
      cur_epoch = epochs[-1]
      for c in collections:
        collection = ent_collection.EntCollection(c, self.cfg.globalParams)
        collection.set_var('LAST_PREREQUISITES_ERRORS', errors.get(c, []))
        # EPOCH_SERVING has two values in the form of "es[0] es[1]"
        # es[0]: the epoch the prereq_check ask us to serve, or
        #        -1 means no epoch answers OK,
        #        -2 means current index answers OK
        # es[1]: the epoch the user set from UI, if -2 means use
        #        most recent valid epoch
        # the serving logic is as following:
        # -- if user set a sepcific epoch (es[1]) >= 0), serve es[1]
        # -- if user set most recent valid epoch (es[1] == -2), then
        #      serve the current index if no/all epochs answers ok
        #       (es[0] == -1 or es[0] == -2 )
        #      otherwise (es[0] >= 0) serve from the es[0]
        #
        es = string.split(string.strip(
          open(collection.get_var('EPOCHS_SERVING'), "r").read()), " ")

        # The epoch prereq_check asks us to serve
        # this from -- -2 means current index is OK,
        # -1 means no epoch answers OK (is returned by the checker)
        epoch = max_epochs.get(c, -2)
        if not errors.has_key(c): epoch = -2
        # initialize EPOCHS_SERVING
        if not es or len(es) == 1:
          es = [epoch, -2]
        else:
          es = map(string.atoi, es)
          # if this change cause automatic rollback, which means
          # - user choose the most recent valid epoch and
          # - the new epoch differs from previous epoch and
          # - the change is not from -1 -> -2 or -2 -> -1.
          # we log it in AdminRunner Operations log
          if  es[1] == -2 and  epoch != es[0] and ( es[0] + epoch != -3 ) :
            epochs_to_time = self.cfg.getGlobalParam('ENTERPRISE_EPOCHS_ENDTIME')
            epoch_time = epochs_to_time.get(epoch, M.MSG_EPOCH_CURRENT_TIME)
            self.writeAdminRunnerOpMsg(M.MSG_UI_LOG_INDEX_ROLLBACK % epoch_time)
          es[0] = epoch

        collection.set_file_var_content('EPOCHS_SERVING',
                                        string.join(map(str, es)), 0)

        # also check if the current serving epoch for the collection
        # is the most recent one, if not, send a warning email
        if send_email and ( ( es[1] == -2 and es[0] >= 0 ) or \
                            (es[1] >= 0 and es[1] != cur_epoch ) ) :
          last_msg_time = self.cfg.getGlobalParam(
            'LAST_SERVING_EPOCH_WARNING_EMAIL_TIME')
          email_interval  = self.cfg.getGlobalParam(
            'ENTERPRISE_INTER_EMAIL_TIME')
          now = int(time.time())
          if now - last_msg_time > email_interval:
            SendMail.send(self.cfg, None, 0,
                          M.MSG_SERVING_EPOCH_NOT_CURRENT % c, "", 0)
            self.cfg.globalParams.set_var(
              'LAST_SERVING_EPOCH_WARNING_EMAIL_TIME', now)

      self.cfg.saveParams()
    finally:
      flock.close()

    return errors

  def advance(self):
    """
    This function advances the epoch to the next one by taking in consideration
    the prisoner epochs (the ones that we keep because they are needed by
    various collections) and a buffer of the last X epochs for backup purposes.
    We delete (remove the epoch boundaries) for the epochs we no longer need
    and create a new epoch with the rtservers
    """

    self.epoch_lock_.acquire()
    try:

      #
      # Index Epoch Advance
      #

      # Get the input for our logic
      epochs = self.cfg.getGlobalParam('ENTERPRISE_EPOCHS')
      num_to_keep = self.cfg.getGlobalParam('ENTERPRISE_NUM_KEEP_EPOCHS')
      prisoner_epochs = self.get_prisoners()
      ent_times = self.cfg.getGlobalParam('ENTERPRISE_EPOCHS_ENDTIME')

      # Advance the index epoch
      # Apply our logic
      ( next_epoch, last_epoch, epochs, ent_times, deletable_epochs ) = \
        epoch_advance_logic(epochs, num_to_keep, prisoner_epochs, ent_times)

      # Log the operations
      logging.info("Index Epoch Advance: New epoch: %d | "\
                   "Deleting epochs: %s | Epochs: %s" % (
        next_epoch, deletable_epochs, epochs))

      # Write the config manager requests
      if deletable_epochs:
        if not self.cfg.globalParams.WriteConfigManagerEpochDeleteRequest(
          deletable_epochs, ["base_indexer"]):
          return 1
      if not self.cfg.globalParams.WriteConfigManagerEpochAdvanceRequest(
        next_epoch, ["base_indexer"]):
        return 1

      # Update the params
      self.cfg.globalParams.set_var('ENTERPRISE_EPOCHS', epochs)
      self.cfg.globalParams.set_var('ENTERPRISE_EPOCHS_ENDTIME', ent_times)
      # for each collection, if user choose the serving epoch to be last epoch
      # ("Current Time"), we also need to advance it to next epoch
      collections = ent_collection.ListCollections(self.cfg.globalParams)
      for c in collections:
        collection = ent_collection.EntCollection(c, self.cfg.globalParams)
        es = string.split(string.strip(
          open(collection.get_var('EPOCHS_SERVING'), "r").read()), " ")
        if ( len(es) == 2 ):
          es = map(string.atoi, es)
          if ( es[1] == last_epoch ) :
            es[1] = next_epoch
            collection.set_file_var_content('EPOCHS_SERVING',
                                            string.join(map(str, es)), 0)


      # Save them all
      self.cfg.saveParams()

    finally:
      self.epoch_lock_.release()

    return 0

  def get_prisoners(self):
    """
    Returns the prisoner epochs -- the ones that prerequisites or
    users force us to keep
    """
    ret = []
    collections = ent_collection.ListCollections(self.cfg.globalParams)
    for c in collections:
      collection = ent_collection.EntCollection(c, self.cfg.globalParams)
      es = map(string.strip, string.split(
        open(collection.get_var('EPOCHS_SERVING'), "r").read(), " "))
      if es and len(es) == 2:
        es = map(string.atoi, es)
        ret.extend(es)
    return ret

  def drain_urlmanagers(self):
    """
    We need to do this before advancing the epoch -- we can do it
    multiple times
    """
    urlmanagers = self.cfg.globalParams.GetServerHostPorts("urlmanager")
    num_shards = self.cfg.globalParams.GetNumShards('urlmanager')
    epoch = self.cfg.getGlobalParam('RT_EPOCH')

    for (host, port) in urlmanagers:
      # We don't do it here directly because of the timeout
      cmd = ". %s; cd %s/local/google3/enterprise/legacy/util && "\
            "./port_talker.py %s %d 'd DumpingStatusTable' %d" % (
          self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
          self.cfg.entHome,
          host, port, 300) # 5 min timeout
      err = E.execute([E.getCrtHostName()], cmd, None, 0)
      if E.ERR_OK != err:
        logging.error("Error draining urlmanagers [%s]" % err)
        return 1

      # Make sure that the file is out
      shard_num = servertype.GetPortShard(port)
      file = "%surlmanager_out_table_%02d_of_%02d_epoch%010d" % (
        self.cfg.getGlobalParam('NAMESPACE_PREFIX'),
        shard_num, num_shards, epoch)
      err, out = E.run_fileutil_command(self.cfg.globalParams, "ls %s" % file)
      if E.ERR_OK != err:
        logging.error("The status table file [%s] is not there" % file)
        return 1

    return 0

  def crawl_this_url(self, url):
    host_port = self.cfg.globalParams.GetServerHostPorts("supergsa_main")
    if len(host_port) != 1:
      logging.error("Found more than 1 supergsa_main backend : %s" %host_port)
      return 1
    # Send a request to the supergsa_main binary and timeout after 60 seconds.
    status, output = commands.getstatusoutput("curl --max-time 60 -Ssi "
        "--data-binary %s http://%s:%s/recrawlsingleurl"
        %(url, host_port[0][0], host_port[0][1]))
    if status == 0 and output.startswith('HTTP/1.1 200'):
      logging.info("Recrawl request was successfully submitted.")
      return 0
    else:
      logging.error("Recrawl request could not be submitted. "
                    "Reason (status/output)\n: %s/%s" %(status, output))
      return 1

  def send_urlmanager_command(self, command):
    ret = 0
    urlmanagers = self.cfg.globalParams.GetServerHostPorts("urlmanager")
    for (host, port) in urlmanagers:
      # We don't do it here directly because of the timeout
      cmd = ". %s; cd %s/local/google3/enterprise/legacy/util && "\
            "./port_talker.py %s %d %s %d" % (
          self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
          self.cfg.entHome,
          host, port,
          commands.mkarg(command), 300)
      err = E.execute([E.getCrtHostName()], cmd, None, 0)
      if E.ERR_OK != err:
        ret = 1
    return ret

  def send_urlscheduler_command(self, command):
    schedulers = self.cfg.globalParams.GetServerHostPorts("urlscheduler")
    timeout = 60 # 1 minute is good enough
    for (machine, port) in schedulers:
      port_talker_cmd = ". %s; cd %s/local/google3/enterprise/legacy/util && "\
            "./port_talker.py %s %d 'GET /run?Flags=%s\r\n\r\n' %d" % (
        self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
        self.cfg.entHome,
        machine, port, command, timeout)
      if E.ERR_OK != E.execute([E.getCrtHostName()], port_talker_cmd, None, 0):
        logging.error("Error talking to urlscheduler %s:%d" % (machine, port))
        return 1
    return 0

  def recrawl_url_patterns(self, url_patterns):
    ret = 0

    errors = self.cfg.globalParams.set_file_var_content('RECRAWL_URL_PATTERNS',
                                                        url_patterns, 1)
    if errors != validatorlib.VALID_OK:
      return 1

    host_port = self.cfg.globalParams.GetServerHostPorts("supergsa_main")
    if len(host_port) != 1:
      logging.error("Found more than 1 supergsa_main backend : %s" %host_port)
      return 2
    # Send a request to the supergsa_main binary and timeout after 60 seconds.
    status, output = commands.getstatusoutput("curl --max-time 60 -Ssi "
        "--data-binary @%s http://%s:%s/recrawlmatchingurls"
        %(self.cfg.getGlobalParam('RECRAWL_URL_PATTERNS'),
          host_port[0][0], host_port[0][1]))
    if status == 0 and output.startswith('HTTP/1.1 200'):
      logging.info("Recrawl request was successfully submitted.")
    else:
      logging.error("Recrawl request could not be submitted. "
          "Reason (status/output)\n: %s/%s" %(status, output))
      ret = 2

    return ret

  def start_crawlmanager_batch(self):
    logging.info("Sending start_batch_crawl command to urlmanager")
    if self.send_urlmanager_command('x start-batch'):
      logging.error("Error send start_batch_crawl command to urlmanager")
      return 0    # error

    return 1  # success


###############################################################################

def epoch_advance_logic(epochs, num_to_keep, prisoner_epochs, ent_times,
                        now = None):
  """
  Output : (next_epoch, last_epoch, epochs, ent_times, deletable_epochs)
  ent_times and epochs are also modified in place
  """
  epochs.sort()

  # The deletable epochs are not prisoners, not in the last num_to_keep and
  # not the base epoch (0)
  deletable_epochs = filter(
    lambda e, p = prisoner_epochs, n = epochs[-num_to_keep:], f = epochs[0]:
    ( e not in p ) and ( e not in n ) and e != f,
    epochs)
  deletable_epochs.sort()

  # The next epoch is the last one + 1
  last_epoch = epochs[-1]
  next_epoch = epochs[-1] + 1

  if now == None:
    now = time.strftime("%Y/%m/%d %H:%M:%S")

  # The last epoch ends at current time while the next_epoch ends at the
  # current time (ongoing)
  if last_epoch not in deletable_epochs:
    ent_times[last_epoch] = now
  ent_times[next_epoch] = M.MSG_EPOCH_CURRENT_TIME

  # Update the end time for all epochs: the delete epochs are merged to
  # the previous ones and the ending time of these becomes the one of the
  # deleted ones.
  for e in deletable_epochs:
    ndx = epochs.index(e)
    ent_times[epochs[ndx - 1]] = ent_times[e]
    del ent_times[e]

  # Update the epochs
  epochs = filter(lambda e, d = deletable_epochs: e not in d, epochs)
  epochs.append(next_epoch)

  return ( next_epoch, last_epoch, epochs, ent_times, deletable_epochs)

###############################################################################

NUM_THREADS = 7

class Runner(threading.Thread):
  """
  This class runs a test in a thread. We system the gws_production_check,
  since we have a timeout with signals that cannot run in another thread
  """

  def __init__(self, n, jobs):
    threading.Thread.__init__(self)
    self.n = n
    self.jobs = jobs
    self.errors = {}
    self.max_epochs = {}

  def run(self):
    i = self.n
    while i < len(self.jobs):
      (cfg, gwssers, site, testwords, epochs, num) = self.jobs[i]
      i = i + NUM_THREADS

      # do the tests on all gwssers - do 2 tries, 15 seconds apart
      max_epoch_site = -1
      for (gws, port) in gwssers:
        cmd = ". %s; cd %s/local/google3/enterprise/legacy/checks && "\
              "./gws_production_check.py %s %d %s %s %s %d" % (
          cfg.getGlobalParam('ENTERPRISE_BASHRC'),
          cfg.entHome,
          commands.mkarg(gws),
          port,
          commands.mkarg(site),
          commands.mkarg(testwords),
          commands.mkarg(string.join(map(str, epochs), ",")),
          num)
        logging.info("Executing %s" % cmd)
        (err, msgs) = E.getstatusoutput(cmd)
        max_epoch = None; errors = None
        exec("(max_epoch, errors) = %s" % msgs)
        if max_epoch > max_epoch_site:
          max_epoch_site = max_epoch
        if errors:
          self.errors[site] =  errors

      self.max_epochs[site] = max_epoch_site
      os.remove(testwords)


###############################################################################

if __name__ == "__main__":
  # small test -- too small for unittest
  (epochs, num_to_keep, prisoner_epochs, ent_times) = \
           ([0], 2, [], {0 : "Current Time"})
  for i in range(10):
    ( next_epoch, last_epoch, epochs, ent_times, deletable_epochs ) = \
      epoch_advance_logic(epochs, num_to_keep, prisoner_epochs, ent_times, i)
    print ( next_epoch, last_epoch, epochs, ent_times, deletable_epochs )

  sys.exit("Import this module")

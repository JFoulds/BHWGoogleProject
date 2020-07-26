#!/usr/bin/python2.4
#
# (c) 2001 and onwards Google, Inc.
# naga@google.com
# cpopescu@google.com
#
# This service is run to perform serving sepcific tasks.
# In realtime world this is everything: actual crawling + indexing + serving
#
###############################################################################

import os
import time
import stat
import string
import traceback
import tempfile
import urllib
import signal

from google3.enterprise.legacy.scripts import ent_service
from google3.enterprise.legacy.util import port_talker
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import adminrunner_client
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.core import core_utils

###############################################################################

from google3.pyglib import flags
FLAGS = flags.FLAGS

flags.DEFINE_string("components", "",
                    "components to act on: crawl. comma separrated")
flags.DEFINE_boolean("force", 0, "force execution")
flags.DEFINE_boolean("ignore_init_state", 0, "ignore initialization state")

###############################################################################

class serve_service(ent_service.ent_service):

  def __init__(self):
    ent_service.ent_service.__init__(self, "serve", 1, "15minly", 1, 3600)
    self.flags = FLAGS
    self.components = []

  # Override init_service to set some members
  def init_service(self, ent_home):
    ent_service.ent_service.init_service(self, ent_home)

    self.babydir = ("%s/local/google3/enterprise/legacy/production/babysitter"
                    % self.ent_home)
    self.bin_dir       = "%s/local/google2/bin" % self.ent_home
    self.rt_ram_dir    = self.cp.var("RTSLAVE_RAM_DIR_FOR_INDEX_CACHING")
    self.rt_local_cache_dir = self.cp.var("RTSLAVE_LOCAL_CACHE_DIR")

  # Override to parse specific flags
  def parse_args(self, argv):
    try:
      FLAGS(argv)  # parse flags
    except flags.FlagsError, e:
      sys.exit("Error: %s\n%s" % (e, self.usage()))

    if FLAGS.components:
      self.components = string.split(FLAGS.components, ",")

    # Did we force execution ?
    self.performs_only_on_main = not FLAGS.force
    self.ignore_init_state = FLAGS.ignore_init_state

  # Operations overrides
  def start(self):
    if ((not self.ignore_init_state) and
        (install_utilities.GetInitState(self.cp) != C.INITIALIZED)):
      logging.info('Not starting serve service as system is not initialized.'
                   ' AdminRunner will start this service once it completes'
                   ' Initialization')
      return
    logging.info(" -- starting serve service -- ")

    # Start everything
    self.start_all()


  def babysit(self):
    # invoke babysitting script here which checks whether required processes
    # are running, and if not, it starts them..

    if ((not self.ignore_init_state) and
        (install_utilities.GetInitState(self.cp) != C.INITIALIZED)):
      logging.info('Not babysitting serving service as system is not'
                   ' initialized. AdminRunner should complete the'
                   ' initialization before babysitting can be resumed.')
      return

    cur_time = time.time()
    if self.isLicenseExpired(long(cur_time * 1000)):
      # expired
      # to avoid killing too frequently, just kill once/twice every hour
      # localtime returns a 9-touple with element index 4 the minutes
      if time.localtime(cur_time)[4] in range(5):
        # kill everything
        self.kill_babysitter()
        self.do_babysitter_op("kill")
      return

    # For non SERVE state we babysit many things
    if self.install_state != "SERVE":
      # check the prerequisites
      self.prereq_check()

    # restart babysitter so that it picks up the latest config
    self.kill_babysitter()
    self.start_babysitter()

    # Cleanup ramdir - babysit() is only called on main whereas nop() is
    # only called on others.  By calling cleanup_ramdir() from both places
    # we ensure that we cleanup on ALL machines.
    self.cleanup_ramdir()

    # check the pagerankers -- at the end..
    if self.install_state != "SERVE":
      self.babysit_pagerankers()

  def restart(self):
    self.stop()
    self.start()

  def stop(self):
    self.kill_all()
    self.cleanup_ramdir()

  def nop(self):
    self.kill_babysitter()
    # See babysit()
    self.cleanup_ramdir()

  #############################################################################
  #
  # Starters
  #
  def start_babysitter(self):
    # Start regular babysitters
    self.do_babysitter_op("loop")

  def start_all(self):
    self.do_babysitter_op("start")

  #############################################################################
  #
  # Killers
  #
  def kill_babysitter(self):
    # sometime it's babysitter.py, sometimes it's python
    # so put both here to make sure
    # also make sure only kill this version's babysitter
    E.killBabysitter(self.util_dir, self.configfile, self.version)

  def kill_all(self):
    self.kill_babysitter()
    self.do_babysitter_op("kill")

  #############################################################################
  #
  # Helpers
  #
  def cleanup_ramdir(self):
    '''
    Rtsubordinate would delete a cached index file when it is done with it.  But if
    it crashes and restarts, it might miss a file.  Also, if the assigner moves
    it to another machine then it would never get a chance to to remove them.
    So we periodically clean up this directory and remove all files that aren't
    needed anymore.  Without this periodic cleanup, we can have a serious memory
    leak on our hands over time.
    It really doesn't pose a problem even if we delete a file that is
    still in use because, in Linux, once a file is opened by a process in
    read-only mode, other processes can remove it and it would still be available
    for the original process that opened it.  Should the rtsubordinate die and restart,
    it will again cache files that have been deleted.
    '''

    # Another caveat - as the file is copied into the directory, it does
    # NOT show up in lsof!  The last mod time does change as it is written
    # and once the writing is done, it is opened for use quickly, so we
    # exclude an unopened file if it was last used < X minutes ago.
    from google3.enterprise.legacy.scripts import cleanup_directory
    if self.rt_ram_dir:
      cleanup_directory.remove_unused_from(self.rt_ram_dir,
                                           '%s/fileutil' % self.bin_dir,
                                           3 * 60)  # X = 3 minutes
    # We can be much less aggressive with file cache - it is not as precious
    # a resource and avoids the need for rtsubordinate to copy it all over again
    # if/when it dies and restarts.
    if self.rt_local_cache_dir:
      cleanup_directory.remove_unused_from(self.rt_local_cache_dir,
                                           '%s/fileutil' % self.bin_dir,
                                           2 * 3600)  # X = 2 hours

  # license, is expired?
  # just check the current time for now (don't check counter)
  def isLicenseExpired(self, cur_mil_sec):
    lic_info = self.cp.var("ENT_LICENSE_INFORMATION")
    end_mil_sec = lic_info['ENT_LICENSE_END_DATE'] + \
                  lic_info['ENT_LICENSE_GRACE_PERIOD']
    return cur_mil_sec > end_mil_sec

  # Starts/ stops all/partial components via babysitter
  def do_babysitter_op(self, op, components = None):
    assert op in ("kill", "start", "loop")

    mode = ""
    background = ""
    if op == 'loop':
      mode = 'loop'
      background = "&"
    else:
      if not components:
        if not self.components:
          ## HACK:
          # all:0,all:1 means all in level 1 / level 2
          # In testing mode the rtsubordinates are on 31400 which
          # makes the babysitter think they are level 1
          # which in fect they are not ..
          components = ["all:0,all:1"]
        else:
          components = self.components
      if len(components) == 0:
        logging.info("No components to kill...")
        return
      mode = "%s=%s" % (op, string.join(components, ","))

    # Don't send cryptic babysitter spam (see bug 85250).
    email_preference = "--nomail"

    cmd = ". %s; cd %s; python2 ./babysitter.py --batch --setpgrp \
      --%s %s --babyalias=localhost --useinvalidconfig --lockdir=%s --delay=0 \
      --nortsignals %s >> %s/babysitter_out_%s 2>&1 %s" % (
        self.ent_bashrc, self.babydir,
        mode,
        email_preference,
        self.version_tmpdir,
        self.configfile,
        self.logdir,
        time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())),
        background)

    E.su_exe_or_fail(self.ent_user, cmd, set_ulimit = 1)

  # Checks if we think that the pageranker is down
  def is_pageranker_down(self):
    pr_machines = self.cp.GetServerHostPorts("pr_main")
    if not pr_machines:
      logging.error("No pagerankers found")
      return 0

    # pageranker's healthz does not return OK. So cannot really
    # use check_healthz.CheckHealthz().
    try:
      for (host, port) in pr_machines:
        try:
          signal.alarm(60)
          response = urllib.urlopen('http://%s:%d/healthz' % (host, port)
                                   ).read()
          if response and response.find('argv') > 0:
            return 1
        finally:  
          signal.alarm(0)
    except IOError:
      return 0

    return 0

  def delete_pagerank_barriers(self):
    """
    Deletes barrier files used by pr_main
    """
    # Sanity check to see we are indeed running pr_main
    pr_prog = self.cp.var('PAGERANKER_PROG')
    if pr_prog != 'pr_main':
      logging.fatal('Not using pr_main anymore')

    # Get all required parameter from entconfig
    barrier_name_prefix = '%s/barriers' % self.cp.var('NAMESPACE_PREFIX')
    datadir = self.cp.var('DATADIR')
    gfs_aliases = self.cp.var('GFS_ALIASES')

    # Nuke'em.  When there is only a single pr_main running (shards=1), it
    # does this during its startup.
    cmd = ('%s/fileutil --datadir=%s --gfs_aliases=%s '
           '--bnsresolver_use_svelte=false '
           ' rm -f %s.barrier_progpr_*_of_*_op*_iter*' %
          (self.bin_dir, datadir, gfs_aliases, barrier_name_prefix))
    logging.info('Deleting barriers - %s' % cmd)
    E.exe(cmd)


  # For babysitting the pageranker we need to check the server_down
  # fact for all pagerankers. If one is down we kill all and restart all
  def babysit_pagerankers(self):
    # TODO(wanli): make this a Borgmon Reactor rule
    if not self.is_pageranker_down():
      return

    logging.info("--- restarting pagerankers ---")
    self.do_babysitter_op("kill", ["pr_main"])
    # Consider this scenario with multiple shards.  The tmpout_files for
    # an iteration for a shard got lost/deleted for some reason - after the
    # iterdone barrier is met.  The receiving pageranker
    # tries to read these files and dies.  The creating shard would not
    # recreate them because the barrier is met.  And we are hosed.
    # To avoid this situation delete all the barriers before restarting
    # pagerankers so that these files are recreated.
    self.delete_pagerank_barriers()
    self.do_babysitter_op("start", ["pr_main"])

  def prereq_check(self):
    ar = adminrunner_client.AdminRunnerClient("localhost", 2100)
    print "Prereq check : %s" % repr(ar.EpochPrereqCheck(1, []))

###############################################################################

if __name__ == "__main__":
  import sys
  serve = serve_service()
  serve.execute(sys.argv)

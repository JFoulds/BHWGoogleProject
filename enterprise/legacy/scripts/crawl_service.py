#!/usr/bin/python2.4
#
# Copyright (C) 2001 and onwards Google, Inc.
#
# naga@google.com
#
###############################################################################

import os

from google3.enterprise.legacy.scripts import ent_service
from google3.pyglib import logging
from google3.enterprise.legacy.util import E

###############################################################################

class crawl_service(ent_service.ent_service):

  def __init__(self):
    ent_service.ent_service.__init__(self, "crawl", 0, "5minly", 1, 3600)

  #############################################################################

  # Operation overrides

  def activate(self):
    """ Override this for some extra links to be done / crontab"""

    ent_service.ent_service.activate(self)

    # remove any existing /root/google* symlinks and create new ones
    for link_name, target_fmt in [('/root/google',  '%s/local/google'),
                                  ('/root/google2', '%s/local/google'),
                                  ('/root/google3', '%s/local/google3')]:
      E.exe_or_fail("rm -rf %s" % link_name)
      E.exe_or_fail("ln -sf %s %s" % (target_fmt % self.ent_home, link_name))
      E.exe_or_fail("chown %s:%s %s" % (self.ent_user, self.ent_group,
                                        link_name))

    # make sure /root is publicly readable so that we can run things under it
    E.exe_or_fail("chmod 755 /root")

    # set up standard crontab on each machine
    E.su_exe_or_fail(self.ent_user,
        ". %s; cd %s/local/google3/enterprise/legacy/util; "
        "%s ./set_standard_crontab.py %s" %  (
            self.ent_bashrc, self.ent_home,
            self.entid_tag, self.ent_home))
    return 1

  def deactivate(self):
    """ Override this for some extra cleanup"""
    ent_service.ent_service.deactivate(self)

    # Remove cronjobs relating to this install version ONLY...
    tmp_cron_file = "%s/tmp/nobody_cron_crawl_" % self.ent_home
    E.exe_or_fail("""if $(/usr/bin/crontab -lu %s &>/dev/null);
    then crontab -lu %s | grep -v %s > %s; crontab -u %s %s; fi""" % \
        (self.ent_user, self.ent_user, self.entid_tag, tmp_cron_file,
         self.ent_user, tmp_cron_file))

    return 1

  def babysit(self):
    return self.do_start()

  def start(self):
    return self.do_start()

  def do_start(self):
    logging.info(" -- starting crawl service -- ")
    # sourcing /etc/profile is okay here because crawl-service is run
    # only on master-machine in active/test mode..
    os.system(""". /etc/profile; . %s; \
    cd %s; %s ./periodic_script.py %s >> \
    /%s/periodic_scriptOut_%s 2>&1 """ % (
      self.ent_bashrc, self.scripts_dir, self.entid_tag,
      self.ent_home, self.logdir, self.version))

    # signal success
    return 1

  def stop(self):
    logging.info(" -- stopping crawl service -- ")
    # kill all the processes owned by the user..
    kill_all_procs_of_a_user_cmd = "kill -9 `ps aeuxwwww|fgrep  %s|"\
                                   "fgrep -v fgrep|awk '{print $1\" \"$2}'|"\
                                   "awk '/%s/{print $2}'`" % (
      self.entid_tag, self.ent_user)

    # not using exe() because I don't care this cmd fails in case there
    # are no processes associated with user..
    os.system(kill_all_procs_of_a_user_cmd)
    # Do it a second time to make sure
    os.system(kill_all_procs_of_a_user_cmd)
    return 1

##############################################################################

if __name__ == "__main__":
  import sys
  crawl = crawl_service()
  crawl.execute(sys.argv)

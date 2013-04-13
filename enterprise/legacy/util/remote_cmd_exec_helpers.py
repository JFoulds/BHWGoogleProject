#!/usr/bin/python2.4
#
# Copyright (C) 2001 and onwards Google, Inc.
# naga@google.com
#
# These are helper routines that are used in install.py
# and vmwebserver.py and migration scripts. These provide
# functionaliy to execute commands on remote machines.

import os
import string
import sys
import threading
from google3.enterprise.legacy.util import E

from google3.pyglib import logging

# ---------------------- install functions ---------------------- #

def remote_cmd_on_explicit_inter_machine(cmd, cluster_name, explicit_inter,
                                         ssh_port = 22):
  """ generate the command wrapper to
  log into cluster_name, then through cluster_name, log into
  explicit_inter to execute the cmd"""
  return E.remote_cmd(cluster_name,
                      E.remote_cmd(explicit_inter, cmd, ssh_port),
                      ssh_port)

def remote_explicit_inter_cp(files, cluster_name, dest_dir, explicit_inter,
                             ssh_port = 22):
  """ copies a file remotely to an explicit inter machine in
  a cluster"""
  base_files = map(os.path.basename, files)
  tmp_files = map(lambda x: "%s/%s" % (dest_dir, x), base_files)
  # scp to cluster_name which could be random internal machine and inter machine
  mkdir_cmd = "rm -rf %s && mkdir -p %s" % (dest_dir, dest_dir)
  E.exe_or_fail(E.remote_cmd(cluster_name, mkdir_cmd, ssh_port))
  # copy the files to the random internal machine
  # caveat: assume this time we go to the same inter machine as last mkdir
  E.exe_or_fail("scp -P %d -p %s root@%s:%s" % (ssh_port,
                                                string.join(files, " "),
                                                cluster_name, dest_dir))
  # from this random internal machine to copy to explicit inter machine
  # (will skip it if the inter machines and explicit inter machine are same)
  # caveat: assume this time we go to the same inter machine as last scp
  scp_cmd = "scp -P %d -p %s %s:%s" % (ssh_port,
                                       string.join(tmp_files, " "),
                                       explicit_inter, dest_dir)
  check_same_machine_wrapper = "if [ `hostname` = %s ]; then "\
                               "(echo files are already on machine %s ); else "\
                               "(echo from `hostname` to %s && %s ); fi" % (
    explicit_inter, explicit_inter, explicit_inter, scp_cmd)
  E.exe_or_fail(E.remote_cmd(cluster_name, check_same_machine_wrapper,
                             ssh_port))


def run_setup_machine_on_cluster_machines(install_machines, dirs,
                                          copy_files,
                                          all_rpm_files,
                                          allow_upgrade,
                                          inter_machine = '',
                                          inter_ssh_port = '',
                                          explicit_inter = None):

  # Get ready for setup_machines
  running_threads = []
  for machine in install_machines:
    thread = InstallThread(machine, dirs, copy_files, all_rpm_files,
                           allow_upgrade, inter_machine, inter_ssh_port,
                           explicit_inter)
    running_threads.append(thread)
    thread.start()

  for thread in running_threads:
    thread.join()

  result = []
  for thread in running_threads:
    if thread.result != None:
      result.append(thread.result)

  if result:
    return string.join(result, "\n")

  return None

class InstallThread(threading.Thread):
  def __init__(self,
               machine, dirs, copy_files, all_rpm_files,
               allow_upgrade, inter_machine, inter_ssh_port,
               explicit_inter = None):
    threading.Thread.__init__(self)
    self.machine = machine
    self.dirs = dirs
    self.copy_files = copy_files
    self.all_rpm_files = all_rpm_files
    self.allow_upgrade = allow_upgrade
    self.inter_machine = inter_machine
    self.inter_ssh_port = inter_ssh_port
    self.explicit_inter = explicit_inter
    self.result = None

  def run(self):
    localhost = E.getCrtHostName()

    logging.info("\n" + "=" * 79)
    logging.info("\n----- Installing on machine: %s -----\n" % self.machine)

    if self.machine != localhost:
      # 1) Make the distribution directory on the install machines
      logging.info("\nMaking distribution dir %s ..." % (
        self.dirs.machine_dist_dir))
      cmd = "mkdir -p %(dir)s" % {
        'dir': self.dirs.machine_dist_dir }
      if not E.exe_maybe_via_inter(E.remote_cmd(self.machine, cmd), 30,
                                   self.inter_machine, self.inter_ssh_port,
                                   1): # Multiple retires
        self.result = "ERROR: while executing %s on machine %s ..." % (
          cmd, self.machine)
        return

      # 2) Copy the files over from intermedite machine to install machines
      if self.machine != localhost: # no need to copy if it is localhost
        logging.info("\nCopying files to install machine %s ..." % (
          self.machine))
        if self.inter_machine:
          files = map(lambda f, d=self.dirs.tmp_copy_dir: "%s/%s" % (d, f),
                      map(os.path.basename, self.copy_files))
        else:
          files = self.copy_files

        scp_cmd = E.remote_cp_cmd(files, self.machine,
                                  self.dirs.machine_dist_dir)
        if self.explicit_inter:
          scp_cmd = E.remote_cmd(self.explicit_inter, scp_cmd,
                                 self.inter_ssh_port)
        if not E.exe_maybe_via_inter(scp_cmd, 7200,
                                     self.inter_machine, self.inter_ssh_port,
                                     1): # Multiple retires
          self.result = "ERROR: while executing %s on machine %s ..." % (
            scp_cmd, self.machine)
          return

    # 3) Run setup_machine.py on install machines
    rpm_files = map(lambda(x): os.path.basename(x), self.all_rpm_files)
    if self.allow_upgrade:
      flags = "--upgrade"
    else:
      flags = ""
    setup_cmd = "cd %s && "\
                "chmod +x setup_machine.py && "\
                "./setup_machine.py %s %s %s" % (self.dirs.machine_dist_dir,
                                                 flags,
                                                 self.dirs.machine_dist_dir,
                                                 string.join(rpm_files, " "))
    # use nonblocking_cmd because vmanager rpm runs vmanager on install
    logging.info("\nInstalling required rpms on machine %s ..." % (
      self.machine))
    full_cmd = E.remote_cmd(self.machine, E.nonblocking_cmd(setup_cmd))
    if not E.exe_maybe_via_inter(full_cmd, 1800,
                                 self.inter_machine, self.inter_ssh_port,
                                 1): # Multiple retires
      self.result = "ERROR: while executing %s on machine %s" % (full_cmd,
                                                                 self.machine)
      return

    # done
    return

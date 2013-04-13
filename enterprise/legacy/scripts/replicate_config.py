#!/usr/bin/python2.4
#
# (c) Copyright 2000-2003 Google inc
# cpopescu@google.com
#
# This handy script will copy the enterprise configuration from a machine
# to the current machine
#
###############################################################################
"""
Usage:
       replicate_config.py <src_machine> <global_config_file>

"""
###############################################################################

import sys
import os

from google3.enterprise.legacy.production.babysitter import config_factory
from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.util import ssl_cert
from google3.enterprise.core import core_utils

###############################################################################

TRUE = 1
FALSE = 0
production_tmp = "/export/hda3/tmp"

###############################################################################

def CopyFile(machine, file, tmpdir):
  if os.system("rsync -e ssh -c -aH -T %s %s:%s %s" % (tmpdir, machine,
                                                       file, file)) :
    sys.exit("ERROR: Copying file %s from %s" % (file, machine))

def CopyFileAsRoot(machine, file, tmpdir, config, ignore_error=0):
  err = os.system('secure_script_wrapper -p2 '
      '%s/local/google3/enterprise/legacy/util/secure_copy.py %s %s %s' %
      (config.var('ENTERPRISE_HOME'), machine, file, tmpdir))
  if err and not ignore_error:
    sys.exit("ERROR: Copying file %s from %s" % (file, machine))

###############################################################################

def ReplicateDirectory(machine, dir, exclude_patterns=None):
  """ rsync's dir from machine into the local machine

  Use exclude_patterns to exclude some files/subdirs.  rsync supports
  "--exclude=PATTERN" option.  Do a "man rsync" for more details.

  Arguments:
    machine: 'ent1'
    dir:     '/export/hda3/4.6.3.G.11/local/conf'
    exclude_patterns: ['cmr_working/failure/', 'cmr_working/success/',
                       'cmr_working/statusz/']
  """

  cmd = "rsync --delete -c -e ssh -aH %s:%s %s" % (machine, dir, dir)
  if exclude_patterns != None:
   for exclude_pattern in exclude_patterns:
     cmd += " --exclude=\"%s\"" % exclude_pattern
  err = os.system(cmd)
  if err:
    sys.exit("ERROR: Replicating directory %s from %s" % (dir, machine))

###############################################################################

def main(argv):
  """ expects: argv[0] to be a machine name, argv[1] be a google_config file
  - copys google_config file from the machine specified into the local machine
    (by calling CopyFile() function)
  - calls ReplicateConfig() - which """
  if len(argv) < 2:
    sys.exit(__doc__)

  machine = argv[0]
  global_file = argv[1]
  global_dir = os.path.dirname(global_file)

  if E.getCrtHostName() == machine:
    logging.info("I do not try to replicate to myself")
    sys.exit(0)

  config = config_factory.ConfigFactory().CreateConfig(global_file)
  if not config.Load():
    sys.exit("ERROR: Cannot read file %s " % global_file)

  file_to_copy = [ C.ETC_SYSCONFIG,
                   global_file,
                   "%s/lic_counter" % global_dir,
                   "%s/lic_counter.bck" % global_dir,
                   "%s/passwd" % global_dir,
                   "/export/hda3/versionmanager/vmanager_passwd",
                   "%s/server.p12" % global_dir
                   ]
  # Sync all the files
  for f in file_to_copy:
    CopyFile(machine, f, production_tmp)

  # sync apache certificate
  CopyFileAsRoot(machine, (ssl_cert.CERT_FILENAME % config.var('ENTERPRISE_HOME')),
                 production_tmp, config)

  # sync private key
  CopyFileAsRoot(machine, (ssl_cert.KEY_FILENAME % config.var('ENTERPRISE_HOME')),
                 production_tmp, config)

  # sync the support request repository directory
  # GRR: ReplicateDirectory(machine, SUPPORTREQUEST_RECORDS_DIR)

  # replicate config including per collection/frontend stuff
  # some dirs in conf don't need to be rsync'ed
  if core_utils.CanRunGSAMaster(E.getCrtHostName()):
    exclude_patterns = ['cmr_working/failure/', 'cmr_working/success/',
                        'cmr_working/statusz/']
  else:
    exclude_patterns = ['cmr_working/', 'cmr/', 'fixer/', 'fixer_cmr/', 'gems']
  ReplicateDirectory(machine, "%s/local/conf/" % config.var('ENTERPRISE_HOME'),
                     exclude_patterns)

  # to replicate per frontend gws stuff (keymatches, gws bad urls)
  ReplicateDirectory(machine, "%s/gws/" % config.var('GOOGLEDATA'))

  # need to adjust NTP if master has changed
  # assumption : this machine is not the master
  if 'PILE' != config.var('ENT_CONFIG_TYPE'):
    ent_home = E.getEnterpriseHome()

    os.system("%s NTP %s" % (C.RECONFIGURE_COMMAND % ent_home, machine))

    # also make sure DNS is up to date
    os.system("%s DNS %s %s" % (
      C.RECONFIGURE_COMMAND % ent_home,
      config.var('BOT_DNS_SERVERS'),
      config.var('DNS_SEARCH_PATH')))

############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

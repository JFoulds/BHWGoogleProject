#!/usr/bin/python2.4
#
# (c) Google 2002 and beyond !
# cpopescu@google.com
#
# The adminrunner -- this is just a stub that parses the command line and
# creates the ardminrunner_server that servs the actual commands
#
###############################################################################
"""
Usage:
 ./adminrunner.py --port=<port> --enthome=<dir> --installstate=<installstate>
"""

import sys
import time
import string
import traceback

from google3.pyglib import app
from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import adminrunner_server
from google3.pyglib import flags
from google3.enterprise.legacy.util import C
import threading
from google3.enterprise.core import core_utils
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.adminrunner import reset_index

###############################################################################
true  = 1
false = 0

##############################################################################
FLAGS = flags.FLAGS

flags.DEFINE_integer("port", 2100, "")
flags.DEFINE_integer("reset_status_cache_timeout", 60, "")
flags.DEFINE_string("enthome", E.getEnterpriseHome(), "")
flags.DEFINE_string("installstate", None, "")
flags.DEFINE_string("box_keys_dir", None, "")
flags.DEFINE_string("license_keys_dir", None, "")

##############################################################################
def StartupWork(cfg, state):

  try:
    #############################################################################
    # check memory-total
    logging.info("check memory-total")
    if not cfg.CheckMachineMemory():
      logging.fatal("failed to check memory-total")
      return

    # One-time Initialization Work:
    # In fresh mode we first initialize the global default
    if install_utilities.GetInitState(cfg.globalParams) == C.FRESH:
      logging.info("initializing global default files")
      if not cfg.globalParams.InitGlobalDefaultFiles(overwrite=false):
        logging.fatal("failed to initialize global default files")
        return
      # Call to saveParams will also distribute the newly created global
      # default files.
      logging.info("saving params and distributing global default files.")
      logging.flush()
      # This is a best effort mechanism. We try upto 6 times to update the
      # files. We assume that we'll get the files to all alive machines. If
      # a machine can't get the files then we assume that it is dead and won't
      # become a master with missing default files.
      cfg.saveParams(retry=6)
      logging.flush()
      install_utilities.SetInitState(cfg, C.CONFIG_FILES_INITIALIZED)
      logging.info('system initialization for %s state successful' %
          C.CONFIG_FILES_INITIALIZED)

    logging.flush()
    # In install mode -- bail out now
    if state == "INSTALL":
      cfg.startupDone()
      return

    # Perform reset index if we got interrupted in the middle of it
    reset_index.ResetIndex(cfg, only_if_in_progress=1)

    try:
      localhost =  E.getCrtHostName()
      if not cfg.setGlobalParam('MASTER', localhost):
        logging.fatal("Error setting the MASTER to %s" % localhost)
    except IOError:
      logging.fatal("Couldn't set MASTER -> exiting")

    # Allocate machines for the empty slots
    logging.info("doing machine allocation")
    if not cfg.DoMachineAllocation():
      logging.info("failed to do machine allocation")

    # In the next install stage (INSTALL) mode we go and finish up the work
    if (install_utilities.GetInitState(cfg.globalParams) ==
          C.CONFIG_FILES_INITIALIZED):
      logging.info("doing system initialization")

      # datadirs are initially made (by the base rpm) to not have any data disks
      # because it doesn't know which disks to use, but the datadir is needed
      # to get things running.
      logging.info("creating datadirs")
      if not cfg.createDataDirs(cfg.getGlobalParam(C.MACHINES)):
        logging.fatal("failed to make datadirs on machines")
        return

      # Create GFS subdirectories
      if cfg.getGlobalParam(C.GFS_CELL):
        logging.info("creating gfs subdirectories")
        if not cfg.createGFSChunkSubDirs():
          logging.fatal("failed creating the gfs subdirectories")
          return

      # ensure initial spelling data is present
      cfg.EnsureSpellingData()

      # create a default collection w/content of mainCrawl / frontend
      logging.info("Creating default collection ...")
      cfg.CreateDefaultCollection()
      logging.info("Creating default frontend ...")
      cfg.CreateDefaultFrontend()
      logging.info("Assiging default collection and frontend ...")
      cfg.AssignDefaultCollAndFront()

      # create some initial files needed by various backend
      logging.info("Creating default backend files ...")
      cfg.CreateDefaultBackendFiles()

      # create built in query expansion entry
      logging.info("Creating default query expansion entry ...")
      cfg.CreateDefaultQueryExpEntry()

      install_utilities.SetInitState(cfg, C.INITIALIZED)
      logging.info("system initialization successful")
      # we start the serve_service as this is fresh install
      logging.info('Starting serve service...')
      RunServeService(cfg.globalParams, 'start')
    else:
      # we restart the babysitter because the servers map may have changed
      logging.info('Babysitting serve service after allocation...')
      RunServeService(cfg.globalParams, 'babysit')

    logging.info("Saving params")
    cfg.saveParams()

    # now we're ready to run; end startup mode
    logging.info("Done with startup")
    cfg.startupDone()

  except Exception, e:
    (t, v, tb) = sys.exc_info()
    exc_msg = string.join(traceback.format_exception(t, v, tb))
    logging.error(exc_msg)
    logging.fatal("StartupWork failed with exception: %s; %s" % (
      e, traceback.format_tb(tb)))

  try:
    # If this fails, we want to proceed...
    cfg.CompileQueryExpData()
  except Exception, e:
    (t, v, tb) = sys.exc_info()
    exc_msg = string.join(traceback.format_exception(t, v, tb))
    logging.error(exc_msg)
    logging.error("Failed compiling query exp data with exception: %s; %s" % (
      e, traceback.format_tb(tb)))

  ###########################################################################

def RunServeService(config, action, components=''):
  """Runs serve service with given parameters.
  The command template used for serve service has --ignore_init_state
  parameter passed. This will force the execution of serve service regardless
  of the initialization state of the system.

  @param config - entconfig
  @param action - any action supported by serve service
                  like 'start', 'stop', ...
  @param components - If non empty, will be supplied to serve service command.
  """
  cmd = C.SERVE_SERVICE_COMMAND % {
        'bashrc' : config.var('ENTERPRISE_BASHRC'),
        'home' : config.var('ENTERPRISE_HOME'),
        'action' : action }
  if components:
    cmd = '%s %s' % (cmd, C.SERVE_SERVICE_COMPONENTS % components)
  logging.info('Executing %s' % cmd)
  E.exe_or_fail(cmd)

def main(unused_args):
  if not E.access([E.LOCALHOST], FLAGS.enthome, 'rd'):
    sys.exit("Invalid enthome %s" % FLAGS.enthome)

  if ( not FLAGS.box_keys_dir or
       not E.access([E.LOCALHOST], FLAGS.box_keys_dir, 'rwd') ):
    sys.exit("Invalid box_keys_dir %s" % FLAGS.box_keys_dir)
  if ( not FLAGS.license_keys_dir or
       not E.access([E.LOCALHOST], FLAGS.license_keys_dir, 'rwd') ):
    sys.exit("Invalid license_keys_dir %s" % FLAGS.license_keys_dir)

  if FLAGS.installstate not in ["INSTALL", "ACTIVE", "SERVE", "TEST"]:
    sys.exit("Invalid --installstate %s" % FLAGS.installstate)

  reset_index.SetResetStatusCacheTimeout(FLAGS.reset_status_cache_timeout)

  as = adminrunner_server.AdminRunnerServer(FLAGS.enthome,
                                            FLAGS.installstate,
                                            FLAGS.port,
                                            FLAGS.box_keys_dir,
                                            FLAGS.license_keys_dir)

  # make sure we have been given a config file
  if (not as.cfg.getGlobalParam(C.ENT_SYSTEM_HAS_VALID_CONFIG) and
      as.cfg.getInstallState() != 'INSTALL'):
    logging.fatal("adminrunner doesn't have a config file; you must "\
                  "install a conf rpm or run it with "\
                  "--installstate=INSTALL (for migration)")
    return # just in case fatal doesn't exit

  ###########################################################################
  # do some startup work; this needs to run while the server is running, so
  # it needs to run in it's own thread
  startup_thread = threading.Thread(target=StartupWork,
                                    args=(as.cfg, as.cfg.getInstallState(),))
  startup_thread.start()

  ###########################################################################

  as.Loop()

if __name__ == '__main__':
  app.run()

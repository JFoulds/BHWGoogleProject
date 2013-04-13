#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# Author: Catalin Popescu
#
# ent_configmgr.py - configuration manager for enterprise.
# We us a separate one to get all enterprise specific requests dispatched,
# a custom scheduling function and handlers
#

import BaseHTTPServer
import os
import sys
import string
import thread

from google3.pyglib import logging

from google3.pyglib import flags
from google3.enterprise.legacy.production.configmgr import autorunner
from google3.enterprise.legacy.production.configmgr import server_requests
from google3.enterprise.legacy.production.configmgr import update_requests
from google3.enterprise.legacy.production.configmgr import epoch_requests
from google3.enterprise.legacy.production.configmgr import configmgr_request
from google3.enterprise.legacy.production.configmgr import request_scheduling

###############################################################################

if os.path.exists('/export/hda3/tmp/'):
  # Production machine
  default_staging_dir = '/export/hda3/tmp/'
else:
  # corp machine
  default_staging_dir = '/tmp/staging_test/'

###############################################################################

FLAGS = flags.FLAGS

flags.DEFINE_string("configmgr_request_dir", "", "The directory with requests")
flags.DEFINE_string("working_dir", "", "Working directory")
flags.DEFINE_string("staging_dir",
                    default_staging_dir,
                    "Staging directory for called scripts")
flags.DEFINE_string("replication_machines",
                    "",
                    "Comma sepparated list of machines to replicate to")
flags.DEFINE_string("logfile",
                    "/tmp/ent_configmgr",
                    "Where to send the output log messages")
flags.DEFINE_string("cwd",
                    "",
                    "Working Directory, if non empty we change to this directory")
flags.DEFINE_integer("port", 0, "healthz port")

###############################################################################

FOREVER = 100000000
MANY_TIMES = 100

HUP_SERVER_COMMAND_INFO = {
  autorunner.COMMAND: './hup_server.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: server_requests.HupServerRequest,
  }

RESTART_SERVER_COMMAND_INFO = {
  autorunner.COMMAND: './restart_server.py',
  autorunner.EXTRA_CMD_ARGS: ['--useinvalidconfig', '--use_python2'],
  autorunner.RETRIES: MANY_TIMES,
  autorunner.CLASS: server_requests.RestartServerRequest,
  }

KILL_SERVER_COMMAND_INFO = {
  autorunner.COMMAND: './restart_server.py',
  autorunner.EXTRA_CMD_ARGS: ['--useinvalidconfig', '--use_python2',
                              '--kill_only'],
  autorunner.RETRIES: MANY_TIMES,
  autorunner.CLASS: server_requests.RestartServerRequest,
  }

RESTART_ENT_SERVING_COMMAND_INFO = {
  autorunner.COMMAND: './restart_ent_serving.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: server_requests.RestartEntServingRequest,
  }

SEND_SERVER_COMMAND_COMMAND_INFO = {
  autorunner.COMMAND: './send_server_command.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: server_requests.SendServerCommandRequest
  }

CONFIG_UPDATE_COMMAND_INFO = {
  autorunner.COMMAND: './config_update.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: update_requests.ConfigUpdateRequest
  }

RESTRICT_UPDATE_COMMAND_INFO = {
  autorunner.COMMAND: './restrict_update.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: update_requests.RestrictUpdateRequest,
  }

RESTRICT_MULTI_REQUEST_CREATE_COMMAND_INFO = {
  autorunner.COMMAND: './multi_request_create.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: configmgr_request.MultiRequestCreateRequest,
  }

EPOCH_ADVANCE_COMMAND_INFO = {
  autorunner.COMMAND: './epoch_advance.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: epoch_requests.EpochAdvanceRequest,
  }

EPOCH_DELETE_COMMAND_INFO = {
  autorunner.COMMAND: './epoch_delete.py',
  autorunner.EXTRA_CMD_ARGS: [],
  autorunner.RETRIES: FOREVER,
  autorunner.CLASS: epoch_requests.EpochDeleteRequest,
  }

class HealthzServerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
      try:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write('ok\n')
      except IOError:
        pass # Client may have dropped connection

    do_HEAD = do_POST = do_GET

    def log_message(self, format, *args):
      pass # Keep quiet

###############################################################################

def main(argv):

  try:
    argv = FLAGS(argv)  # parse flags
  except flags.FlagsError, e:
    print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if not FLAGS.configmgr_request_dir:
    sys.exit("Please specify --configmgr_request_dir")
  if not FLAGS.working_dir:
    sys.exit("Please specify --working_dir")

  if FLAGS.cwd != "":
    try:
      os.chdir(FLAGS.cwd)
    except:
      print "Couldnt open change the working dir to %s" % FLAGS.cwd

  try:
    fd = open(FLAGS.logfile, 'a')
    sys.stdout = fd
    sys.stderr = fd
    logging.set_logfile(fd)
  except:
    print "Couldnt open the given logfile %s in append mode" % FLAGS.logfile

  # Create the autorunner object and register what to run for those requests.
  dispatcher = autorunner.AutorunnerDispatcher(
    FLAGS.configmgr_request_dir,
    FLAGS.working_dir, None,
    filter(None, string.split(FLAGS.replication_machines, ',')))

  # Register handlers
  dispatcher.SetSuccessHandler(request_scheduling.HandleCompletion)
  dispatcher.SetFailureHandler(request_scheduling.HandleCompletion)

  # Set the function that checks if the request is allowd
  dispatcher.SetAllowedRequestFilter(request_scheduling.AllowedFilter)

  #
  # Register the command information for the commands we process
  #
  dispatcher.RegisterTypeHandler(server_requests.HUP_SERVER,
                                 HUP_SERVER_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(server_requests.RESTART_SERVER,
                                 RESTART_SERVER_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(server_requests.KILL_SERVER,
                                 KILL_SERVER_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(server_requests.RESTART_ENT_SERVING,
                                 RESTART_ENT_SERVING_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(server_requests.SEND_SERVER_COMMAND,
                                 SEND_SERVER_COMMAND_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(update_requests.UPDATEPARAM,
                                 CONFIG_UPDATE_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(update_requests.UPDATERESTRICT,
                                 RESTRICT_UPDATE_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(configmgr_request.MULTI_REQUEST_CREATOR,
                                 RESTRICT_MULTI_REQUEST_CREATE_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(epoch_requests.EPOCHADVANCE,
                                 EPOCH_ADVANCE_COMMAND_INFO)

  dispatcher.RegisterTypeHandler(epoch_requests.EPOCHDELETE,
                                 EPOCH_DELETE_COMMAND_INFO)

  # Start healthz thread, instead of using pyserverizer
  httpd = BaseHTTPServer.HTTPServer(("", FLAGS.port),
			        HealthzServerRequestHandler)
  thread.start_new_thread(httpd.serve_forever, ())

  # Start running commands.
  dispatcher.Execute()

if __name__ == '__main__':
  main(sys.argv)

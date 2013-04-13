#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Thin wrapper for connector manager import/export.

usage: connector_import_export.py <java> <appbase> ...
"""

__author__ = 'timg@google.com (Tim Grow)'

import sys
import os

CLASSNAME = "com.google.enterprise.connector.importexport.ImportExport"
UNZIP = "/usr/bin/unzip"
CM_APPNAME = "connector-manager"

# TODO(timg): error handling

def extract_war_contents(appbase, appname):
  app_dir = "%s/%s" % (appbase, appname)
  os.mkdir("%s/%s" % (appbase, appname))
  app_war = "%s/%s.war" % (appbase, appname)
  # TODO(timg): use python zipfile library
  os.system("%s %s -d %s" % (UNZIP, app_war, app_dir))

def main(argv):
  java = argv[1]
  appbase = argv[2]
  java_options = argv[3]

  # extract war contents if necessary
  connector_manager_dir = "%s/%s" % (appbase, CM_APPNAME)
  if not os.access(connector_manager_dir, os.F_OK):
    extract_war_contents(appbase, CM_APPNAME)

  # calculate classpath
  lib_dir = "%s/%s/WEB-INF/lib" % (appbase, CM_APPNAME)
  jars = os.listdir(lib_dir)
  jars = map(lambda x: "%s/%s" % (lib_dir, x), jars)
  classpath = ":".join(jars)

  # calculate argstring
  arg_string = " ".join(argv[4:])

  # execute cmd
  os.chdir("%s/%s" % (appbase, CM_APPNAME))
  cmd = ("%s -cp %s %s %s %s" %
         (java, classpath, java_options, CLASSNAME, arg_string))
  os.system(cmd)

  return 0

if __name__ == '__main__':
  main(sys.argv)

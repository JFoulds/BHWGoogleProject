#!/usr/bin/python2.4
#
# (c) Copyright 2004 Google Inc.
# Phuong Nguyen <pn@google.com>
#
# Deal with database access configuration
#
# Commands:
#
# 1. getconfig
#             Return the configuration of database crawl.
#
# 2. setconfig
#             Set the configuration of database crawl.
#
# 3. getstylesheet:
#             Return the stylesheet of a specified database datasource entry
#             Return: 1 on error.
#                     0 on success, followed by the stylesheet.
# 4. setstylesheet:
#             Set the stylesheet of a specified database datasource entry
#             Return: 1 on error.
#                    0 on success
# 5. deletestylesheet:
#             Delete the stylesheet of a specified database datasource entry
#             Return: 1 on error.
#                     0 on success,
# 6. makestylesheeturl:
#             Return the file:/// url of the stylesheet of a specified
#               database datasource entry
#
# 7. getdatabasestatus:
#             Return a dictionary of db source name and crawling status.
#
# 8. sync:
#             Start TableCrawler to crawl a specified
#               database datasource entry
#
# 9. status:
#             Return a map of all source sync status
#
# 10. delete:
#             Delete a database source and its associated files
#
#

import time
import threading
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
import os
import urllib
from google3.enterprise.legacy.production.common import cli
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.production.babysitter import servertype_prod
from google3.enterprise.legacy.setup import serverflags
from google3.enterprise.legacy.util import E
import string

class TableCrawlerThread(threading.Thread):
  """
  A thread that:
    adds itself to a dict when it starts, and
    runs an OS command,
    removes itself from a dict when it finishes.
  """
  def __init__(self, group, source, log, last, cmd, db_handler):
    threading.Thread.__init__(self)
    self.source = source
    self.log = log
    self.last = last
    self.cmd = cmd
    self.group = group
    self.db_handler = db_handler
    group[source] = self

  def run(self):
    db_handler = self.db_handler
    # TODO(dcz): i18n
    db_handler.writeAdminRunnerOpMsg('database sync started on source %s' %
                                     self.source)
    out_lines = []
    try:
      rtn_code = E.execute(['localhost'], self.cmd, out_lines, 0)
      if rtn_code == 0:
        # TODO(dcz): i18n
        db_handler.writeAdminRunnerOpMsg(
          'database sync succeeded on source %s' % self.source)
        db_handler.distributedbfiles(self.log)
        db_handler.distributedbfiles(self.last)
      else:
        # TODO(dcz): i18n
        db_handler.writeAdminRunnerOpMsg(
          'database sync on source %s failed with status %d' %
          (self.source, rtn_code))
    finally:
      # clean-up global dict
      del self.group[self.source]

class DatabaseHandler(admin_handler.ar_handler):
  # dict to keep track of crawling threads
  crawling_sources = { }

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.updatelock = threading.Lock()

  def get_accepted_commands(self):
    return {
      "getconfig": admin_handler.CommandInfo(0, 0, 0, self.getconfig),
      "setconfig": admin_handler.CommandInfo(0, 0, 1, self.setconfig),
      "getstylesheet": admin_handler.CommandInfo(1, 0, 0, self.getstylesheet),
      "setstylesheet": admin_handler.CommandInfo(1, 0, 1, self.setstylesheet),
      "deletestylesheet": admin_handler.CommandInfo(1, 0, 0, self.deletestylesheet),
      "makestylesheeturl": admin_handler.CommandInfo(1, 0, 0, self.makestylesheeturl),
      "notifytableserver": admin_handler.CommandInfo(0, 0, 0, self.notifytableserver),
      "sync": admin_handler.CommandInfo(1, 0, 0, self.sync),
      "status": admin_handler.CommandInfo(0, 0, 0, self.getdatabasestatus),
      "delete": admin_handler.CommandInfo(1, 0, 0, self.delete),
      "getlog": admin_handler.CommandInfo(1, 0, 0, self.getlog),
      }

  def distributedbfiles(self, filenames):
    # Distribute local database files to all the nodes.
    retcode = E.distribute(self.cfg.getGlobalParam("MACHINES"),
                           filenames, 1)
    if retcode != 0:
      logging.error("Couldn't distribute %s, error %d" % (filenames, retcode))
      return "1"
    return "0"

  def distributedeletedbfile(self, filename):
    # Remove local database files from all the nodes.
    machines = self.cfg.getGlobalParam("MACHINES")
    if not E.rm(machines, filename):
      logging.error("Failed to delete %s on %s" % (filename, machines))
      return "1"
    return "0"


  def removefileifexists(self, filename):
    '''Remove a file if it exists, return 0 if removal succeeded'''
    self.updatelock.acquire()
    try:
      try:
        # The caller may want to remove GFS file or localfile,
        # call fileutil to take care of all of them.
        rm_cmd = "rm -f %s" % filename
        err, out = E.run_fileutil_command(self.cfg.globalParams, rm_cmd)
        if err != E.ERR_OK:
          logging.error("Failed to remove file %s" % filename)
          logging.error("fileutil output: %s" % out)
          return "1"
        else:
          return "0"
      except IOError, e:
        logging.error("Failed to remove file %s" % filename)
        logging.error(str(e))
        return "1"
    finally:
      self.updatelock.release()

  def delete(self, entry):
    '''Remove a db source xml file, log file, stylesheet'''
    config = self.cfg.globalParams
    feedfile = ('%s_[0-9]*_[0-9]*.xml.complete'
                % os.path.join(config.var('FEEDS_DIR'), entry))
    logdir = self.cfg.getGlobalParam('DATABASE_LOGS_DIR')
    logfile = '%s.log' % os.path.join(logdir, entry)
    lastfile = '%s.last' % os.path.join(logdir, entry)
    xsldir = self.cfg.getGlobalParam("DATABASE_STYLESHEET_DIR")
    xslfile = os.path.join(xsldir, entry)
    self.removefileifexists(feedfile)
    ret = self.distributedeletedbfile(logfile)
    ret = self.distributedeletedbfile(lastfile) and ret
    ret = self.distributedeletedbfile(xslfile) and ret
    return ret

  def getdatabasestatus(self):
    '''Check TableCrawler status'''
    out = { }
    for entry in DatabaseHandler.crawling_sources.iterkeys():
      # TODO(dcz): only one status so far, more status states may come
      out[entry] = '1'
    return "0\n%s" % out

  def sync(self, entry):
    '''Run TableCrawler to sync database source.'''
    if DatabaseHandler.crawling_sources.has_key(entry):
      return "1"
    config = self.cfg.globalParams
    cl = cli.CommandLine()
    cl.Add(servertype_prod.UlimitPrefix(config))
    # The table crawler and table server use similar commandline parameters,
    # so to reduce code, we borrow the tableserver commandline parameters
    # and change them, instead of reconstructing them again.
    binary_name = servertype.GetBinaryName('enttableserver')
    googlebin=os.path.join(config.var('MAINDIR'), 'bin')
    # change PWD to bin directory
    cl.Add('cd %s && ' % googlebin)
    libdir=os.path.join(config.var('MAINDIR'), 'bin',
                        '%s_libs' % binary_name)
    jdbcjars=''
    for jar in servertype_prod.THIRD_PARTY_JDBC_JARS:
      realpath=(jar % os.environ)
      jdbcjars=('%s:%s' % (jdbcjars, realpath))
    classpath = ('%s/bin/TableCrawler.jar:'
                 '%s/third_party/java/saxon/saxon.jar') % (
                       config.var('MAINDIR'), config.var('MAINDIR'))

    cl.Add(servertype_prod.JavaServerExecutablePrefix(config, 'enttableserver',
      ('-classpath %s '
       '-Djava.security.manager '
       '-Djava.security.policy==%s/bin/java.policy '
       '-Djavax.xml.transform.TransformerFactory='
        'com.icl.saxon.TransformerFactoryImpl '
       '-Xbootclasspath/a:%s -Djava.library.path=%s '
       '-Dswigdeps=%s/TableCrawler_swigdeps.so') % (classpath,
                                                    config.var('MAINDIR'),
                                                    jdbcjars, libdir,
                                                    libdir),
                                                      no_loop=1,
                                                      run_as_class=1,
                                                      java_max_heap_mb=900))
    cl.Add('--dbinfo=%s' % config.var('DATABASES'))
    if config.var('DATABASE_STYLESHEET_DIR'):
      cl.Add('--stylesheet_dir=%s' % config.var('DATABASE_STYLESHEET_DIR'))
    cl.Add('--tablename=%s' % entry)
    # bug 67413, use public doctype instead of system doctype
    cl.Add('--doctype_public="-//Google//DTD GSA Feeds//EN"')
    cl.Add('--doctype_system=gsafeed.dtd')
    cl.Add(servertype.mkarg("--bnsresolver_use_svelte=false"))
    if config.var('GFS_ALIASES'):
      cl.Add(servertype.mkarg("--gfs_aliases=%s" % config.var('GFS_ALIASES')))
    # bug 63082 timestamp the feed file name to separate feeds on same source
    date_string = time.strftime('%Y%m%d_%H%M%S', E.getLocaltime(time.time()))
    feedfile = os.path.join(config.var('FEEDS_DIR'),
                            '%s_%s.xml' % (entry, date_string))
    logdir = self.cfg.getGlobalParam('DATABASE_LOGS_DIR')
    if not os.path.exists(logdir):
      os.mkdir(logdir)
    logfile = '%s.log' % os.path.join(logdir, entry)
    lastfile = '%s.last' % os.path.join(logdir, entry)
    if os.path.exists(lastfile):
      # possible incremental crawl
      filemtime = time.localtime(os.path.getmtime(lastfile))
      cl.Add('--lastvisit="%s"' % time.strftime('%Y/%m/%d %H:%M:%S %Z',
                                                filemtime))
      cl.Add('--lastvisitformat="yyyy/MM/dd HH:mm:ss z"')
    cl.Add('--feedfile=%s' % feedfile)
    # feed using the static, externally visible port
    srv_mngr = config.GetServerManager()
    set = srv_mngr.Set('entfrontend')
    feedergateservers = set.BackendHostPorts('feedergate')
    cl.Add("--feedergate_servers=%s" %
           serverflags.MakeHostPortsArg(feedergateservers))
    # serve database tuples thru frontend
    cl.Add('--serveprefix=googledb://')
    tablecrawler_command = cl.ToString().replace('TableServer', 'TableCrawler')
    tablecrawler_command = tablecrawler_command.replace(' TableCrawler ',
                            ' com.google.enterprise.database.TableCrawler ')
    tablecrawler_command = ('%s >& %s && touch %s' %
                            (tablecrawler_command, logfile, lastfile))
    logging.info('TableCrawler commandline=%s' % tablecrawler_command)
    syncthread = TableCrawlerThread(group=DatabaseHandler.crawling_sources,
                                    source=entry, log=logfile, last=lastfile,
                                    cmd=tablecrawler_command, db_handler=self)
    syncthread.start()
    return "0"

  def notifytableserver(self):
    '''Notify TableServer of configuration file changes'''
    config = self.cfg.globalParams
    srv_mngr = config.GetServerManager()
    set = srv_mngr.Set('entfrontend')
    enttableservers = set.BackendHostPorts('enttableserver')
    # Currently there is only one tableserver,
    # in the future tableserver may be sharded,
    # so we use a loop.
    for tableserver in enttableservers:
      hostport = serverflags.MakeHostPortsArg([tableserver])
      url = 'http://%s/reconfig' % hostport
      try:
        logging.info('fetching %s' % url)
        file = urllib.urlopen(url)
        logging.info(file.read())
        file.close()
      except IOError, e:
        logging.error(str(e))
        return "1"
    return "0"

  def getlog(self, entry):
    '''Get the database log file.'''
    logdir = self.cfg.getGlobalParam('DATABASE_LOGS_DIR')
    filename = os.path.join(logdir, "%s.log" % entry)
    if not os.path.exists(filename):
      return "1"
    out = open(filename, "r").read()
    return "0\n%s" % out

  def getconfig(self):
    '''Get the database access configuration file.'''
    filename = self.cfg.getGlobalParam("DATABASES")
    if not os.path.exists(filename):
      return "1"

    out = open(filename, "r").read()
    return "0\n%s" % out

  def setconfig(self, configBody):
    '''Set the database access configuration file.'''

    self.updatelock.acquire()
    try:
      try:
        filename = self.cfg.getGlobalParam('DATABASES')
        open(filename, "w").write(configBody)
        retcode = self.distributedbfiles(filename)
      except IOError, e:
        logging.error(str(e))
        return "1"
    finally:
      self.updatelock.release()
    return retcode

  def getstylesheet(self, entry):
    '''Get the stylesheet of a given entry in database access configuration.'''
    try:
      filename = os.path.join(self.cfg.
                              getGlobalParam("DATABASE_STYLESHEET_DIR"), entry)
      out = open(filename, "r").read()
      return "0\n%s" % out
    except IOError, e:
      logging.error(str(e))
      return "1"

  def setstylesheet(self, entry, stylesheetData):
    '''Set the stylesheet for a given entry of database access configuration.'''
    dbStyleSheetDir = self.cfg.getGlobalParam("DATABASE_STYLESHEET_DIR")
    filename = os.path.join(dbStyleSheetDir, entry)
    self.updatelock.acquire()
    try:
      try:
        if not os.path.exists(dbStyleSheetDir):
          os.mkdir(dbStyleSheetDir)
        open(filename, "w").write(stylesheetData)
        retcode = self.distributedbfiles(filename)
      except IOError, e:
        logging.error("Exception: %s" % str(e))
        return "1"
    finally:
      self.updatelock.release()
    return retcode

  def deletestylesheet(self, entry):
    '''Delete the stylesheet of a given entry of database
       access configuration.'''
    filename = os.path.join(self.cfg.
                            getGlobalParam("DATABASE_STYLESHEET_DIR"), entry)
    self.updatelock.acquire()
    try:
      if not os.path.exists(filename):
        return "0"
      ret = self.distributedeletedbfile(filename)
      if ret != 0:
        return "1"
    finally:
      self.updatelock.release()
    return "0"

  def makestylesheeturl(self, entry):
    '''Return the URL for stylesheet of given entry in database
       access configuration.'''
    return "file://%s" % os.path.join(self.cfg.getGlobalParam("DATABASE_STYLESHEET_DIR"), entry)

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

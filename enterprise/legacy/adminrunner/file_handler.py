#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com from michal@google.com  FileHandler.java
#
# The file browse commands for AdminRunner
#
###############################################################################

import string
import commands
import os
import urllib

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import ar_exception

###############################################################################

true  = 1
false = 0

class FileTableEntry:
  def __init__(self, dir_param, file_pattern, browse_pattern,
               do_tac, aux_grep, aux_cut, multi_files, browse_dir):
    self.dir_param = dir_param
    self.file_pattern = file_pattern
    self.browse_pattern = browse_pattern
    self.do_tac = do_tac
    self.aux_grep = aux_grep
    self.aux_cut = aux_cut
    self.multi_files = multi_files
    self.browse_dir = browse_dir

  def getPathIn(self, cp, clientName, fileArg, grepString):
    return self.file_pattern % {'dir' : cp.var(self.dir_param),
                                'client' : clientName,
                                'fileArg' : fileArg,
                                'grepString' : grepString}

  def getPathOut(self, cp, clientName, fileArg, grepString):
    return self.browse_pattern % {'dir' : cp.var(self.browse_dir),
                                  'client' : clientName,
                                  'fileArg' : fileArg,
                                  'grepString' : grepString}

###############################################################################

FILE_TABLE = {
  "OPERATOR_LOG" : FileTableEntry("LOGDIR",
                                  "%(dir)s/AdminRunner.OPERATOR*",
                                  "%(dir)s/AdminRunner.browse",
                                  true, false, false, true,
                                  "LOGDIR"),

  "ASR_LOG" :  FileTableEntry("LOGDIR",
                             "%(dir)s/log_report/%(client)s/logdump_%(fileArg)s.txt",
                             "%(dir)s/log_report/%(client)s/logdump_%(fileArg)s.browse",
                             false, "^asr ",
                              # See enterprise/legacy/logs/preprocess_logs.py for the
                              # meaning of fields 3,5-
                             ' --fields=3,5- "--delimiter= " "--output-delimiter=,"',
                              true,
                             "LOGDIR"),

  "WEB_LOG" : FileTableEntry("LOGDIR",
                             "%(dir)s/log_report/%(client)s/logdump_%(fileArg)s.txt",
                             "%(dir)s/log_report/%(client)s/logdump_%(fileArg)s.browse",
                             false, "] \"", false, true,
                             "LOGDIR"),

  "FEED_LOG" : FileTableEntry("FEED_STATUS_DIR",
                              "%(dir)s/%(fileArg)s",
                              "%(dir)s/feed_log.%(fileArg)s.browse",
                              false, false, false, false,
                              "LOGDIR"),
  }

##############################################################################

class FileHandler(admin_handler.ar_handler):

  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "browse" :    admin_handler.CommandInfo(4, 1, 1, self.browse),
      "export_filename" : admin_handler.CommandInfo(2, 0, 1,
                                                    self.export_filename),
      "linecount" : admin_handler.CommandInfo(2, 1, 1, self.linecount),
      "export" :    admin_handler.CommandInfo(3, 0, 1, self.export),
      "log" :       admin_handler.CommandInfo(0, 0, 1, self.log),
      }

  ###########################################################################

  def browse(self, clientName, virtualFile, fromLine, toLine,
             grepString, fileArgs):

    grepString = urllib.quote_plus(grepString.strip())
    fromLine = string.atoi(fromLine)
    toLine   = string.atoi(toLine)

    fileLocation = self.makePhysicalFile(virtualFile, clientName, grepString,
                                         fileArgs)
    if not fileLocation:
      raise ar_exception.ARException((
        ar_exception.LOADPARAMS, M.ERR_INVALIDFILESPECIFICATION))

    # Get valid start line and end line
    numLines = toLine - fromLine + 1;
    if numLines < 0:  numLines = 0
    toLine = fromLine + numLines - 1

    # Get the lines
    result = []

    parsedGrepString = commands.mkarg(grepString)
    if ( E.ERR_OK != E.execute(
        [E.getCrtHostName()], "head -n %s %s | tail -n %s | grep -i -F -- %s" %
        (toLine, fileLocation, numLines, parsedGrepString), result, false) ):
      return "0"

    return "%s\n%s" % (len(result[0]), result[0])

  def export_filename(self, clientName, virtualFile, fileArgs):

    # mandatory argument for makePhysicalFile function
    grepString = ''
    fileLocation = self.makePhysicalFile(virtualFile, clientName, grepString,
                                         fileArgs)
    if not fileLocation:
      raise ar_exception.ARException((
        ar_exception.LOADPARAMS, M.ERR_INVALIDFILESPECIFICATION))

    # return this file location no grep operation performed on this file
    return "%s" % fileLocation

  def linecount(self, clientName, virtualFile, grepString, fileArgs):

    grepString = urllib.quote_plus(grepString.strip())

    fileLocation = self.makePhysicalFile(virtualFile, clientName, grepString,
                                         fileArgs)

    if not fileLocation:
      raise ar_exception.ARException((
        ar_exception.LOADPARAMS, M.ERR_INVALIDFILESPECIFICATION))

    # find physical file size (line count)
    parsedGrepString = commands.mkarg(grepString)
    lineCount = self.getCount(
        "grep -i -F -- %s %s | wc -l | awk '{print $1}'" %
        (parsedGrepString, fileLocation), E.getCrtHostName())

    return lineCount

  # this method is not currently used by any class
  # see com/google/enterprise/servlets/handlers/LogHandler.java
  # for exporting sys event log file
  def export(self, clientName, virtualFile, convert,
             fileArgs):

    fileLocation = self.makePhysicalFile(virtualFile, clientName, "",
                                         fileArgs)
    if not fileLocation:
      raise ar_exception.ARException((
        ar_exception.LOADPARAMS, M.ERR_INVALIDFILESPECIFICATION))

    return "%s %s" % (E.getCrtHostName(), fileLocation)

  def log(self, msg):
    self.writeAdminRunnerOpMsg(msg)

  ###########################################################################

  def makePhysicalFile(self, virtualFile, clientName, grepString, fileArg):
    """
    Makes a physical file from a virtual one
    Creates a temp file with results from grep operation/cating of files
    Returns: [machine name], [file name]
    return null on error
    """

    # Sanitize fileArg.
    fileArg = ''.join([x for x in fileArg
                       if x in string.ascii_letters + string.digits + '_-%'])

    # Translate from String to fileId
    if not virtualFile or not FILE_TABLE.has_key(virtualFile):
      return None


    # For each file that we can export we have to have an entry in the
    # global FILE_TABLE
    fe = FILE_TABLE[virtualFile]

    pathIn  = fe.getPathIn(self.cfg.globalParams,
                           clientName, fileArg, grepString)
    pathOut = fe.getPathOut(self.cfg.globalParams,
                            clientName, fileArg, grepString)
    auxGrepString = fe.aux_grep
    auxCutString = fe.aux_cut
    machine = E.getCrtHostName()

    tmpPath = None

    # Copy web log from GFS to the log directory if necessary.
    if virtualFile == 'WEB_LOG' and self.cfg.getGlobalParam('GFS_ALIASES') and \
        not os.path.exists(pathIn):
      ok = self.cfg.logmanager.CopyRawReportFromGfsToLocal(fileArg, clientName)
      if not ok or not os.path.exists(pathIn):
        logging.error('Failed on CopyRawReportFromGfsToLocal()')
        return None

    # Copy the feed log from GFS to the log directory if necessary.
    elif virtualFile == 'FEED_LOG' and self.cfg.getGlobalParam('GFS_ALIASES') and \
         not os.path.exists(pathIn):
      tmpPath = pathOut + "_fromGFS"
      (status, output) = E.run_fileutil_command(self.cfg.globalParams,
                             "cat %s > %s" % (pathIn, tmpPath), 5)
      if E.ERR_OK != status:
        logging.error("Failed to copy %s to %s" % (pathIn, tmpPath))
        return None
      pathIn = tmpPath

    # Count the files that we can get
    files = E.ls([machine], pathIn)
    if not files:
      numFiles = 0
    else:
      numFiles = len(files)

    # If we need only one file, and there are more than one, use the
    # last one.
    if numFiles > 0 and not fe.multi_files:
      pathIn = files[-1]

    # Create the auxiliary command to create the actual file
    command = None
    if numFiles == 0 :
      # No files availavle.
      command = "echo -e '' > %s" % pathOut;
    else:
      if virtualFile == 'FEED_LOG':
        command = "tail -n +2 %s " % pathIn
        if fe.do_tac:
          command = command + " | tac "
      # If we reverse the files before displaying
      elif fe.do_tac:
        command = "tac `ls -r %s` " % pathIn

      # Grep the lines we want
      if auxGrepString:
        if not command:
          command = "cat `ls -r %s`" % pathIn
        command = command + " | grep -- %s" % commands.mkarg(auxGrepString)

      # Maybe we need another grep
      if grepString:
        if not command:
          command = "cat `ls -r %s`" % pathIn
        parsedGrepString = commands.mkarg(grepString)
        command = command + " | grep -i -F -- %s" % parsedGrepString

      # Maybe a cut as well
      if auxCutString:
        if not command:
          command = "cat `ls -r %s`" % pathIn
        command = command + " | cut %s" % auxCutString

      if command:
        command = command + " > " + pathOut;

      # execute the command  "file+operation > temp_filename"
      # if the command is null just use the path we have.
      if not command:
        return pathIn

    E.execute([machine], command, None, false);
    if tmpPath:
      E.rm([machine], tmpPath)

    return pathOut

  def getCount(self, command, machine):
    """ used for wc to return # of lines """
    result = []
    if E.ERR_OK != E.execute([machine], command, result, false):
      return -1;

    # parse out the return code from the executed command
    try:
      return string.atoi(result[0])
    except:
      logging.error("Problem getting the count on %s" % command );
    return -1

###############################################################################

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

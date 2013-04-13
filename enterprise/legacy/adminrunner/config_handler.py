#!/usr/bin/python2.4
#
# Copyright 2004 Google, Inc.
#
# Original Author: Zia Syed (zsyed@google.com)
# Modifications: Hareesh Nagarajan (hareesh@google.com)

"""Implement handler for exporting/importing enterprise box configuration.

Design document: //depot/eng/designdocs/enterprise/configuration_import_export.html
"""

import urllib
import hotshot, hotshot.stats
import time
import sys
import os
import cStringIO
import re
from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import admin_handler

from google3.enterprise.legacy.adminrunner import config_filters
from google3.enterprise.legacy.adminrunner import xml_packager
from google3.enterprise.legacy.adminrunner import base_packager
from google3.enterprise.legacy.adminrunner import impexp_secmgr

FAILURE = base_packager.FAILURE
SUCCESS = base_packager.SUCCESS

class ConfigHandler(admin_handler.ar_handler):
  """Handles configuration import/export methods.
  """

  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg in non-null only for testing (we cannot have multiple constructors)
    if cfg:
      self.cfg = cfg
      self.conn = None
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "exportconfig"            : admin_handler.CommandInfo(
      2, 0, 0, self.exportconfig),
      "importconfig"            : admin_handler.CommandInfo(
      2, 0, 0, self.importconfig),
      "getencoding"             : admin_handler.CommandInfo(
      0, 0, 0, self.getencoding),
      "getconttype"             : admin_handler.CommandInfo(
      0, 0, 0, self.getconttype),
      }

  def createPackager(self, password):
    """Factory method for creating right packager. Right now only supports
    XML based packaging.
    """
    secmgr = impexp_secmgr.SecMgr(urllib.unquote_plus(password))
    return xml_packager.XMLPackageEntity('eef', config_filters.XMLConfigPackager(self.conn, self.cfg, secmgr), 1)

  def profile_exportconfig(self, password, exportInfo):
    """If you want to profile exportconfig, then call this function
    from get_accepted_commands."""
    
    # Profile
    profile_name = '/tmp/ar.export.prof.%s' % (time.time())
    p = hotshot.Profile(profile_name)
    ret = p.runcall(self.exportconfig, password, exportInfo)
    p.close()

    # Gather stats
    stats = hotshot.stats.load(profile_name)
    stats.sort_stats('time', 'calls')

    # Write stats to a file
    output = cStringIO.StringIO()
    sys.stdout = output
    stats.print_stats()
    sys.stdout = sys.__stdout__
    open(profile_name + '.txt', 'w').write(output.getvalue())
    return ret

  def profile_importconfig(self, password, import_file):
    """If you want to profile importconfig, then call this function
    from get_accepted_commands."""
    
    # Profile
    profile_name = '/tmp/ar.import.prof.%s' % (time.time())
    p = hotshot.Profile(profile_name)
    ret = p.runcall(self.importconfig, password, import_file)
    p.close()

    # Gather stats
    stats = hotshot.stats.load(profile_name)
    stats.sort_stats('time', 'calls')

    # Write stats to a file
    output = cStringIO.StringIO()
    sys.stdout = output
    stats.print_stats()
    sys.stdout = sys.__stdout__
    open(profile_name + '.txt', 'w').write(output.getvalue())
    return ret

  def exportconfig_uam_inserter(self, result, outf, uam_filename):
    """When the config gets exported, the UamFilter stores the file
    name (uam_filename) of the personalization data in the config. But
    the final config that gets exported needs to have the
    personalization data. We do this hackery to make the export ultra
    fast.
    """
    
    result_list = result.split('\n')
    uam_idx = result_list.index(uam_filename)

    # Write everthing upto personalization to the config file.
    for i in xrange(uam_idx):
      outf.write(result_list[i] + '\n')

    # Now read the uam file in 1MB chunks and write it out to the
    # config file that we want to stream.
    uamf = open(uam_filename, 'r')
    bufsize = 1048576
    while True:
      buff = uamf.read(bufsize)
      outf.write(buff)
      if len(buff) != bufsize:
        break

    # Write the remaining sections to the config file.
    for i in xrange(uam_idx + 1, len(result_list)):
      outf.write(result_list[i] + '\n')
   
  def exportconfig(self, password, exportInfo):
    """Exports configuration as XML given a password and exportInfo.
    exportInfo is not used currently but in future will provide information
    regarding what needs to be exported.

    We return the file name of the config file.
    """
    cfgpackager = self.createPackager(password)

    # The EnterpriseHandler.writeOutputFile() method which streams
    # this file back to the user, will delete the file once the file
    # has been streamed.
    export_file = '/export/hda3/tmp/config.%s.xml' % time.time()
    
    try:
      # TODO(hareesh): The whole damn configuration is stored in the
      # string result. We really need to improve upon this, because we
      # could get OverflowErrors. A single python string can only hold
      # a so much. *SIGH*
      result = ('<?xml version="1.0" encoding="%s" ?>%s'
                % (self.getencoding(), cfgpackager.encode (level=0)))
      outf = open(export_file, 'w')
      
      # Replace uam_dir tag, because all we have inside the <uam_dir>
      # tag is a file name.
      m=re.findall(impexp_secmgr.SecMgr.UAM_RE, result)
      if len(m) > 0 and m[0][1] != 'None':
        uam_filename = m[0][1]
        self.exportconfig_uam_inserter(result, outf, uam_filename)
        os.unlink(uam_filename)
      else:
        outf.write(result)
      outf.close()
      logging.info('Wrote config.xml out: %s' % export_file)
    except config_filters.ConfigExportError, e:
      logging.error(e)
      result = 'Error exporting configuration.'

    return export_file

  def importconfig_uam_extractor(self, import_file, import_file_no_uam,
                                 uam_file):
    """Extract the uam_dir section from the XML file. If the section
    does not exist we create a 0 byte file and the
    config_filters.py:UamFilter:decode() code will do the right
    thing.

    The import_file_no_uam will contain everything but the contents of
    <uam_dir> uam_file </uam_dir> and in turn the uam_file will
    contain the contents inside the <uam_dir> CDATA.
    """
    
    try:
      fin = open(import_file, 'r')
      fout = open(import_file_no_uam, 'w')
      uam_out = open(uam_file, 'w')
    except Exception, e:
      logging.error('Could not open necessary files %s' % str(e))
      return False

    # A simple finite state machine. In step1, we write all the lines
    # in the import_file just before the opening uam_dir tag to
    # import_file_no_uam. Once we are done with step1, we enter
    # step2. Here, until we find the closing tag of uam_dir, we write
    # the contents of uam_dir into uam_file. And finally, we enter
    # step3. Here, we write everything after the closing tag of
    # uam_dir, to import_file_no_uam.
    step1 = True
    step2 = step3 = False
    for line in fin.xreadlines():
      if step1:
        if line.find('<uam_dir><![CDATA[') > 0:
          step1 = False
          step2 = True
          fout.write(line)
          fout.write(uam_file + '\n')
          continue
        else:
          fout.write(line)

      if step2:
        if line.find(']]></uam_dir>') > 0:
          step2 = False
          step3 = True
          fout.write(line)
          continue
        else:
          uam_out.write(line)

      if step3:
        fout.write(line)

    logging.info('Extracted uam_dir from %s' % import_file)
    return True

  def importconfig(self, password, import_file, delete=True):
    """Imports configuration at location import_file and a given
    password. The import_file is deleted here if delete is set to
    True.
    """
    
    import_file_no_uam = '/export/hda3/tmp/stripped.%s.xml' % time.time()
    uam_file = '/export/hda3/tmp/uam.%s.xml' % time.time()

    if self.importconfig_uam_extractor(import_file, import_file_no_uam,
                                       uam_file):
      logging.info('UAM %s %s %s' % (import_file, import_file_no_uam, uam_file))
    else:
      import_file_no_uam = import_file
      logging.info('There was no uam_dir to extract: %s' % import_file)
    
    cfgpackager = self.createPackager(password)
    log = base_packager.ImportLog()
    try:
      ret = cfgpackager.decodeFromFile(import_file_no_uam, log)
    except config_filters.ConfigImportError, e:
      log.error(e)
      ret = FAILURE
    except base_packager.MalformedContentError, e:
      log.error(e)
      ret = config_filters.MALFORMED_CONTENT_ERROR
    except impexp_secmgr.InvalidPasswordError, e:
      log.error(e)
      ret = config_filters.INVALID_PASSWORD_ERROR

    if ret == SUCCESS:
      log.info('Configuration imported successfully.')
    if ret == base_packager.SUCCESS_WITH_APPS_MESSAGE:
      log.info('Configuration imported successfully but apps domain was not imported.')


    try:
      if delete:
        os.unlink(import_file)
        os.unlink(import_file_no_uam)
        os.unlink(uam_file)
    except Exception, e:
      logging.error('Could not unlink files: %s' % str(e))

    # Errors are in ugly admin_handler.formatValidatorError format, so
    # clean it up a bit.  Discard any lines except those that start with
    # ' or a letter.
    errorOut = []
    for error in log.errors:
      for line in error.splitlines():
        if len(line) > 0 and (line[0] == "'" or line[0].isalpha()):
          errorOut.append(line)
    return '%s %s' % (ret, '\n'.join(errorOut))

  def getencoding (self):
    """Returns the encoding e.g. text/XML and unicode encoding.
    """
    return xml_packager.ENCODING

  def getconttype (self):
    """Returns content type.
    """
    return xml_packager.CONTENT_TYPE

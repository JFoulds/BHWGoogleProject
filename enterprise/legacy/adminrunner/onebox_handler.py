#!/usr/bin/python2.4
#
# Copyright 2002-2006 Google, Inc.
# bpurvy@google.com
#
# The AdminRunner handler for dealing with oneboxes
#
#
###############################################################################

"""
Service to set and return the XML configuration for OneBox Modules.

For setconfig, performs some manipulations on the XSLT:
1) extracts each resultsTemplate into a separate file, and makes sure
the 'name' attribute on the xsl:template is the same as the configured
name of the OneBox Module.
2) rewrites the customer-onebox.xsl file, to call the above-mentioned
files.
Does not currently do Schema validation on the XML file, but that may
be added in the future, at least under control of a debug flag.

"""

__author__ = 'bpurvy@google.com (Bob Purvy)'

import sys
import string
import xml.dom
import xml.dom.minidom
from xml.sax._exceptions import *
import os
import types

from google3.pyglib import logging
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.util import C
from google3.enterprise.tools import M
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.util import admin_runner_utils

cfgFileName = 'oneboxes.enterprise'
custFileName =  'customer-onebox.xsl'
# the templates by which we build up the customers.xsl file:

true = 1
false = 0

customerHeader = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

"""

includeDefault = """  <!-- The holder for calls to all customer- or partner-provided stylesheets.  Do not
    customize.
  -->
  <xsl:include href="onebox-default.xsl"/>
"""

invokeDefault = """<!-- the default template if no other provided -->
  <xsl:template name="holder" match="OBRES">
    <div class="oneboxResults">
      <table>
        <xsl:call-template name="onebox-default"/>
      </table>
    </div>
  </xsl:template>
"""

# one of these per module with a stylesheet.  Must all come before the next one
# (customerInvocation):
customerImport = '  <xsl:import href="%s.xsl"/>'

# one of these per module with a stylesheet.
customerInvocation = """
  <xsl:template name="holder-%s" match="OBRES[@module_name='%s']">
    <div class="oneboxResults">
      <table>
        <xsl:call-template name="%s"/>
      </table>
    </div>
    </xsl:template>
"""

customerTrailer = "</xsl:stylesheet>\n"

xslHeader = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
"""

xslTrailer = "</xsl:stylesheet>\n"


def getText(node_list):

  """ Collect the text from (possibly) multiple Text nodes inside an element,
  into a single string.

  Args:
    nodelist:  the list of children of a node in a DOM tree

  Returns:
    A string containing the concatenated contents, with leading and trailing
    whitespace removed.
  """

  rc = ""
  for node in node_list:
    if node.nodeType == node.TEXT_NODE:
      rc = rc + node.data
  return rc.strip()


###############################################################################

class OneBoxHandler(admin_handler.ar_handler):

  """
  Service to set and return the XML configuration for OneBox Modules.
  """
  TMP_LOG = '/tmp/onebox_tmp.log'

  def get_accepted_commands(self):

    return {
      "getconfig"         : admin_handler.CommandInfo(0, 0, 0, self.getconfig),
      "setconfig"         : admin_handler.CommandInfo(0, 0, 1, self.setconfig),
      "getlog"            : admin_handler.CommandInfo(1, 0, 0, self.getlog),
      "getdefaultstylesheet" : admin_handler.CommandInfo(0, 0, 0, self.getdefaultstylesheet),
      }

  #############################################################################

  def getconfig(self):
    '''Get the onebox configuration file.'''
    filename = self.cfg.getGlobalParam("ONEBOX_MODULES")
    if filename == None:
      logging.info("failed to find config file")
      return "1\%s" % "failed to find config file"
    logging.info("config file=" + filename)
    if not os.path.exists(filename):
      logging.info("but didn't find it")
      return "1\n"
    f=open(filename, "r")
    if not f:
      logging.info("can't open " + filename)
      return "1\n"
    stat=os.stat(filename) # TODO: take out
    out = f.read()
    f.close()
    return "0\n%s" % out

  def setconfig(self, configBody):
    """
    Set the onebox configuration file.
    Args:
      configBody: an UTF-8-encoded Unicode string. If the string is not
      Unicode, a best-effort is made, biased towards Latin accented
      characters (iso-8859-1). Note that this is not a restriction, since
      Asian characters can be passed in in a Unicode string.
    """

    # convert to utf-8-encoded Unicode, if it's not
    if not isinstance(configBody, types.UnicodeType):
      try:
        uconfig = unicode(configBody, "iso-8859-1").encode("utf-8")
      except UnicodeDecodeError, e:
        logging.error(str(e))
        return "1\n%s" % str(e)
    else:
      uconfig = configBody
    res = self.parseXML(uconfig)
    if res:
      logging.info(res)
      return "1\n%s\n" % res

    try:
      filename = self.cfg.getGlobalParam("ONEBOX_MODULES")
      if filename == None:
        logging.info("failed to find config file")
        return "1\n%s" % "failed to find config file"
      cfgFile = open(filename, 'w')
      cfgFile.write(configBody)
      cfgFile.close();
      retcode = '0'
    except IOError, e:
      logging.error(str(e))
      return '1'
    return retcode

  def getlog(self, entry):
    '''Get the onebox log file.'''
    ent_config_type = self.cfg.getGlobalParam('ENT_CONFIG_TYPE')
    logfile = self.cfg.getGlobalParam('ENTERPRISE_ONEBOX_LOG')

    if logfile == None:
      logging.info("failed to find the log file")
      return "failed to find log file"


    if ent_config_type == 'CLUSTER':
      admin_runner_utils.SyncOneboxLog(self.cfg.globalParams)
      gfs_cell = self.cfg.getGlobalParam('GFS_CELL')
      filename = os.path.join(os.sep, 'gfs', gfs_cell, logfile)
    else:
      filename = os.path.join(self.cfg.getGlobalParam('TMPDIR'), logfile)

    out = self.get_log_per_module(filename, entry)
    return "0\n%s" % out

  def get_log_per_module(self, filename, module_name):
    '''Get the onebox module specific logging information.'''
    ent_config_type = self.cfg.getGlobalParam('ENT_CONFIG_TYPE')
    grep_string = '\"Query \\[\\|\\[%s\\]\"' % module_name

    if ent_config_type == 'CLUSTER':
      gfs_aliases = self.cfg.getGlobalParam('GFS_ALIASES')
      grep_command = 'fileutil --bnsresolver_use_svelte=false '\
                     '--gfs_aliases=%s cat %s | grep %s > %s' % (
                      gfs_aliases, filename, grep_string, self.TMP_LOG)
    else:
      grep_command = 'grep %s %s > %s' % (grep_string, filename, self.TMP_LOG)

    machine = E.getCrtHostName()
    E.execute([machine], grep_command, None, false)
    tmp_file = open(self.TMP_LOG, 'r')
    contents = tmp_file.read()
    tmp_file.close()
    os.remove(self.TMP_LOG)
    return contents

  def getdefaultstylesheet(self):
    '''Get the onebox default stylesheet'''
    # find the stylesheet dir:
    self.xslDir = self.cfg.getGlobalParam('ENTFRONT_STYLESHEETS_DIR')
    if not self.xslDir:
      logging.error("failed to find stylesheet dir")
      return "failed to find stylesheet dir"
    filename = os.path.join(self.xslDir, "onebox-default.xsl")
    if not os.path.exists(filename):
      return "1"
    out = open(filename, "r").read()
    return "0\n%s" % out

  # private routines to process the resultsTemplate stylesheet, if any:

  def parseXML(self, configBody):
    try:
      dom = xml.dom.minidom.parseString(configBody)
    # this comes from a C extension to Python, and can't be named any better:
    except Exception:
      logging.exception("parse error in XML")
      return "parse error in XML"
    oneboxes = dom.getElementsByTagName('onebox')
    if not oneboxes:
      logging.info('No onebox modules found')
      return None

    # find the stylesheet dir:
    self.xslDir = self.cfg.getGlobalParam('ENTFRONT_STYLESHEETS_DIR')
    if not self.xslDir:
      logging.error("failed to find stylesheet dir")
      return "failed to find stylesheet dir"
    xslNames = []  # list of the oneboxes with their own XSL

    # create
    for onebox in oneboxes:
      nameNodes = onebox.getElementsByTagName('name')
      if not nameNodes:
        return "failed to find name element"
      elif len(nameNodes) > 1:
        return "more than one name element"
      name = getText(nameNodes[0].childNodes)

      results = onebox.getElementsByTagName('resultsTemplate')
      if len(results) > 1:
        return "more than one 'resultsTemplate' node found in " + name
      elif results:
        err = self.processXSL(onebox, name, results)
        if err:
          if err[0] != '0':
            return err
          else:
            xslNames.append(name)

        # Remove resultsTemplate element from config because backend
        # doesn't understand it.
        onebox.removeChild(results[0])

    # write out a config file without resultsTemplate for the
    # backend
    backendFileName = self.cfg.getGlobalParam("ONEBOX_BACKEND_CONFIG")
    if backendFileName == None:
      logging.info("failed to find config file")
      return "1\n%s" % "failed to find config file"
    logging.info("backend config file is %s"  % backendFileName)
    backendFile = open(backendFileName, "w")
    if not backendFile:
      logging.info("can't open " + backendFileName)
      return "1\n"
    backendFile.write(dom.toxml(encoding="utf-8"));
    backendFile.close()

    # rewrite the master XSL that calls each individual one:

    custFile = open(self.xslDir + os.sep + custFileName, "w")
    custFile.write(customerHeader)
    for name in xslNames:
      custFile.write(customerImport % name)
    custFile.write('\n')

    # in XSL, the imports need to precede the includes:

    custFile.write(includeDefault)
    custFile.write(invokeDefault)
    for name in xslNames:
      custFile.write(customerInvocation %(name, name, name))
    custFile.write(customerTrailer)
    custFile.close()

    # touch each frontend stylesheet that includes any oneboxes,
    # so the file watcher will notice:
    for frontend in dom.getElementsByTagName("Frontend"):
      if frontend.attributes:
        name = frontend.attributes["name"]
        if name:
          ssName = self.xslDir + os.sep + name.nodeValue
          if os.path.exists(ssName):
            os.system("touch " + ssName)

  def processXSL(self, onebox, name, results):

    """ does the following steps with the XSL in the resultsTemplate element:
    <ol>
    <li> write each resultsTemplate to its own file, with the name of the
    onebox module.  If there was a file of that name there, it's overwritten.
    </li>
    <li> rewrite the customer-onebox.xsl file to call each module's
    stylesheet with the appropriate match statement
    </li>
    </ol>
    Returns: err string if an error occurs, True if this onebox has
    a resultsTemplate and it was written to a file, and None if both
    those were not true.
    """

    print "processXSL called for %s" % name

    # parse this XML
    stylesheet = results[0].childNodes
    if not stylesheet:
      print "no results 2"
      return None

    newdoc = xml.dom.minidom.Document()
    stylesheetNode = newdoc.createElement("xsl:stylesheet")
    stylesheetNode.setAttribute("xmlns:xsl", 'http://www.w3.org/1999/XSL/Transform')
    stylesheetNode.setAttribute("version", "1.0")
    newdoc.appendChild(stylesheetNode)
    for node in stylesheet:
      if node.nodeType != xml.dom.Node.TEXT_NODE:
        stylesheetNode.appendChild(node)
    if not stylesheetNode.firstChild: # if no nodes in there
      return None
    xsl = newdoc.toxml(encoding="utf-8")

    try:
      xslDom = xml.dom.minidom.parseString(xsl)
    # this comes from a C extension to Python, and can't be named any better:
    except Exception:
      e = sys.exc_info()[1]
      logging.exception("error in %s at line %d" % (name,e.getLineNumber()))
      logging.info("xml with error is: " + xsl)
      return "error in " + name
    temps = xslDom.getElementsByTagName('xsl:template') # NOTE namespace
    if not temps:
      return('no xsl:template element found in ' + name)
    temps[0].setAttribute('name', name)
    f = open("%s/%s.xsl" % (self.xslDir, name), "w")
    print "writing this xsl to " + name
    f.write(xslDom.toxml(encoding="utf-8"))
    f.close()
    return "0"

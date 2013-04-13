#!/usr/bin/python2.4
# (c) 2006 Google inc.
#
# The "borgmon" command handler for AdminRunner
# The following commands are accepted:
#   makegraph, getuservars, genstatusreport, gethealth, getsystemstatus,
#   getcrawlsummary
#
###############################################################################

# TODO(wanli) use borg.monitoring.borgmon import borgmon_eval_lib.
# borgmon_eval_lib needs python2.4, so we cannot use it now

import string
from google3.pyglib import logging
import os
import time
import commands

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.core import core_utils
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import SendMail
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.util import gsa_status_logic
from google3.enterprise.util import borgmon_util
import urllib

###############################################################################


GRAPH_DELAY_SECONDS = 120
# md5sum //google3/googledata/enterprise/statichtml/images/graphs/errortext.png
MD5SUM_ERROR_GRAPH = 'dbc7fb4b381f75244a8d43e599ea216c'

###############################################################################

def secsSinceMidnight():
  tups = time.localtime(time.time())
  return tups[3] * 3600 + tups[4] * 60 + tups[5]


class BorgmonHandler(admin_handler.ar_handler):
  """
  Processes all the Borgmon related commands for AdminRunner
  """

  def __init__(self, conn, command, prefixes, params):
    """ initializes parameters from /etc/google/hw_manifest.py and
    uses defaults if manifest has errors. The hw_manifest.py is
    installed by the enterprise-os rpm.
    """

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)
    self.version = self.cfg.getGlobalParam("VERSION")
    self.install_state = install_utilities.install_state(self.version)
    self.borgmon_mode = (
      borgmon_util.INSTALL_STATE_TO_MODE_MAP[self.install_state])
    self.gsa_status_logic = gsa_status_logic.GSAStatusLogic(self.cfg)

  def get_accepted_commands(self):
    return {
      "makegraph"  : admin_handler.CommandInfo(
      1, 0, 0, self.makegraph),
      "getuservars"  : admin_handler.CommandInfo(
      0, 0, 0, self.getuservars),
      "genstatusreport"  : admin_handler.CommandInfo(
      0, 0, 0, self.genstatusreport),
      "gethealth"  :    admin_handler.CommandInfo(
      0, 0, 0, self.gethealth),
      "getsystemstatus"  : admin_handler.CommandInfo(
      0, 0, 0, self.getsystemstatus),
      "getcrawlsummary"  : admin_handler.CommandInfo(
      0, 0, 0, self.getcrawlsummary),
      }

  def makegraph(self, graph_name):
    """
    Generates the sum urls crawled and queries per minute graph.
    Returns 0 if the graph gets genarated successfully, otherwise returns 0.
    For queries per minute graph - if the max QPM is less than 10 then we dont
    autoresize. This is to show foo bar queries at the bottom of the graph.
    TODO(meghna) Should we use GRAPH_DELAY_SECONDS somewhere here ?
    """
    logging.info('borgmon makegraph ' + graph_name)
    auto_resize = 1
    if (graph_name == 'QUERIES_PER_MINUTE' or
        graph_name == 'QUERIES_PER_MINUTE_THUMBNAIL'):
      bu = borgmon_util.BorgmonUtil(self.version, mode=self.borgmon_mode)
      value = bu.GetAndEvalBorgmonExpr('max(gws_searches_per_minute[24h])')
      if not value or value < 10:
        auto_resize = 0
    wide_lines = 0
    if (graph_name == 'QUERIES_PER_MINUTE_THUMBNAIL' or
        graph_name == 'SUM_URLS_TOTAL_THUMBNAIL'):
      wide_lines = 1
    graph_url = self.cfg.getGraphURL(graph_name, auto_resize, wide_lines)
    logging.info('graph_url=' + graph_url)
    if not graph_url:
      return 1

    graph_pipe = urllib.urlopen(graph_url)
    graph = graph_pipe.read()
    graph_pipe.close()
    if not graph:
      return 1

    # Checking for "Plot Error" here by comparing the md5sums:
    # make sure the graph doesn't have the same md5sum as known error text,
    # if it does log an error but don't overwrite the graph.
    # This is a very terrible hack.
    tmp_graph = 'TMP_GRAPH'
    self.cfg.setGraph(tmp_graph, graph)
    cmd = 'md5sum ' + self.cfg.getGraphFileName(tmp_graph)
    md5sum_graph_info = commands.getoutput(cmd)
    md5sum_graph = md5sum_graph_info.split()[0]
    if (MD5SUM_ERROR_GRAPH == md5sum_graph):
      logging.error('Borgmon not yet ready to display graph ' + graph_name)
      return 0
    self.cfg.setGraph(graph_name, graph)
    return 0

  def _getuservars(self):
    """Return user-facing variables that we monitor in a two forms, in a 2-ple.
       The first entry will be a formatting string of name,value pairs,
       and the second is a dict mapping the name (e.g. 'num_urls_error')
       to the value.
    """

    logging.info('borgmon_handler :: getuservars')
    vars = {
            'num_urls_in_index_total' : 'num_urls_in_index_total',
            'num_urls_available_total' : 'num_urls_available_total',
            'interval_pages_per_sec_total' : 'interval_pages_per_sec_total',
            'num_urls_error' : 'num_urls_error[%ds] - min(num_urls_error[%ds])'
            % (eval('secsSinceMidnight()'), eval('secsSinceMidnight()')),
            'num_urls_error_now' : 'num_urls_error',
            'gws_searches_per_minute' : 'gws_searches_per_minute',
            'num_urls_crawled_today' : 'num_urls_crawled[%ds] - min(num_urls_crawled[%ds])'
            % (eval('secsSinceMidnight()'), eval('secsSinceMidnight()')),
            'num_urls_crawled_now' : 'num_urls_crawled',
            'num_urls_served' : 'num_urls_served',
            'scheduled_crawl_start_time' : 'scheduled_crawl_start_time',
            'scheduled_crawl_end_time' : 'scheduled_crawl_end_time',
            'scheduled_crawl_is_running' : 'scheduled_crawl_is_running',
            'doc_bytes_received' : 'doc_bytes_received',}
    var_map = {}
    for var in vars.keys():
      bu = borgmon_util.BorgmonUtil(self.version, mode=self.borgmon_mode)
      value = bu.GetAndEvalBorgmonExpr(vars[var])
      if value:
        var_map[var] = value

    ret = '0\n' + string.join(map(lambda k:"%s=%s" % (k, str(var_map[k])),
      var_map.keys()), '\n') + '\n'
    logging.info('returning ' + ret)
    return (ret, var_map)

  def getuservars(self):
    """Return user-facing variables that we monitor as a
       string of name,value pairs. """
    return self._getuservars()[0]


  def gethealth(self):
    """Returns a value indicating the health level of the whole system. 
    value= 0 -- healthy,
    value= 1 -- warning,
    value= 2 -- panic,
    """

    return self.gsa_status_logic.GetHealth()

  def getsystemstatus(self):
    """
    returns a python string that represents the current system status:
    Health = <health_value>
    SystemStatusValues = <health values of different components>
    SystemStatusDescription = <descriptions of different components>
    e.g. Health = 0
         SystemStatusValues  =  {'Disks':  0,  'Raid':  0,  'Temperatures':  0,
                                 'Machines': 0}
         SystemStatusDescriptions  =  {'Disks': '', 'Raid': '',
                                       'Temperatures':  '', 'Machines': ''}
    """
    return self.gsa_status_logic.GetSystemStatus()

  def genstatusreport(self):
    """
    refresh the value of crawl summary, and generate system status report
    + send email if needed

    Returns:
      0
    """

    # Genrate report:
    if self.cfg.getGlobalParam('SEND_ENTERPRISE_STATUS_REPORT'):
      STATUS_STRING = [ "OK",
                        "CAUTION",
                        "WARNING",
                        ]
      SUMMARY_STRING = {
        "global-overall-urls-crawled" : M.MSG_URL_CRAWLED_SINCE_YESTERDAY,
        "global-overall-urls-crawl-error" : M.MSG_URL_ERROR_SINCE_YESTERDAY,
        }

      # get system status
      system_status = self.gsa_status_logic.GetSystemStatusMap()
      cur_time = time.strftime("%Y-%m-%d %H:%M:%S",
                               time.localtime(time.time()))
      subject = M.MSG_SYSTEM_STATUS_REPORT % cur_time
      health = max(map(lambda (x,y): y[0], system_status.items()))
      report = []
      report.append("System Status: %s" % STATUS_STRING[health])

      for param in self.gsa_status_logic.status_params_:
        if system_status.has_key(param):
          status = system_status[param]
          report.append("%s Status: %s. %s" %
                        (param, STATUS_STRING[status[0]], status[1]))

      # get crawl summary
      report.append("\nCrawl Summary:")
      summary = self._get_crawl_summary()
      for param in summary.keys():
        report.append("%s: %s" %
                      (SUMMARY_STRING[param], summary[param]))

      # notify administrator
      SendMail.send(self.cfg, None, 0,
                    subject, string.join(report, "\n"), 0)

    # refresh the value of crawl summary
    snapshot = self.cfg.getGlobalParam('ENT_CRAWL_SUMMARY')
    current = self._get_current_crawlsummary()
    for param in current.keys():
      if snapshot.has_key(param):
        snapshot[param] = current[param]
    self.cfg.setGlobalParam('ENT_CRAWL_SUMMARY', snapshot)
    self.cfg.saveParams()

    return 0

  def _get_crawl_summary(self):
    """ returns crawl summary since yesterday

    Returns:
      {'global-overall-urls-crawl-error': 0,
       'global-overall-urls-crawled': 199620.0}
    """

    # get current overall crawled summary
    summary = self._get_current_crawlsummary()
    # get yesterday's summary
    overall_summary = self.cfg.getGlobalParam('ENT_CRAWL_SUMMARY')
    for param in summary.keys():
      if overall_summary.has_key(param):
        value = summary[param] - overall_summary[param]
        if value >= 0:
          summary[param] = value
    return summary

  def _get_current_crawlsummary(self):
    """Current crawl summary from Borgmon.

    Returns:
      {'global-overall-urls-crawl-error': 0,
       'global-overall-urls-crawled': 199620.0}
    """

    # We need to map from the identifiers ('global-overall-urls-crawled')
    # to borgmon exprs ('num_urls_crawled_today')
    NAME_TO_BORGMON = {
        'global-overall-urls-crawled': 'num_urls_crawled_now',
        'global-overall-urls-crawl-error': 'num_urls_error_now'}

    summary = {}
    uservars = self._getuservars()[1]
    for param in self.cfg.getGlobalParam('ENT_CRAWL_SUMMARY').keys():
      bname = '?'
      try:
        bname = NAME_TO_BORGMON[param]
        summary[param] = uservars[bname]
      except KeyError:
        logging.warn('problem finding value for ' + param + ' aka ' + bname)
        summary[param] = 0.0
    logging.info("return: " + str(summary))
    return summary

  def getcrawlsummary(self):
    """ returns a python string that summarize the crawl since yesterday

    Returns:
      CrawlSummary = {'global-overall-urls-crawl-error': 0,
                      'global-overall-urls-crawled': 199620.0}
    """

    return "CrawlSummary = %s" % repr(self._get_crawl_summary())

if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

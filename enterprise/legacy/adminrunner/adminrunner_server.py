#!/usr/bin/python2.4
# Copyright 2002-2007 Google Inc. All rights reserved.

"""HTTP server implementation for the AdminRunner."""

__author__ = 'cpopescu@google.com'

import cgi
import string
import time
import urllib
import sys

from google3.base import pywrapbase
from google3.net.base import pywrapselectserver
from google3.net.http import pywraphttpserver
from google3.pyglib import flags
from google3.pyglib import gfile
from google3.pyglib import logging
from google3.stats.io import pywrapexpvar
from google3.thread import pywrapthreadpool
from google3.webutil.url import pywrapurl

from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.adminrunner import alerts_handler
from google3.enterprise.legacy.adminrunner import borgmon_handler
from google3.enterprise.legacy.adminrunner import collection_handler
from google3.enterprise.legacy.adminrunner import config_handler
from google3.enterprise.legacy.adminrunner import configurator
from google3.enterprise.legacy.adminrunner import crawlqueue_handler
from google3.enterprise.legacy.adminrunner import database_handler
from google3.enterprise.legacy.adminrunner import debug_handler
from google3.enterprise.legacy.adminrunner import diagnose_handler
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import epoch_handler
from google3.enterprise.legacy.adminrunner import file_handler
from google3.enterprise.legacy.adminrunner import feedstatus_handler
from google3.enterprise.legacy.adminrunner import frontend_handler
from google3.enterprise.legacy.adminrunner import gws_handler
from google3.enterprise.legacy.adminrunner import labs_handler
from google3.enterprise.legacy.adminrunner import license_handler
from google3.enterprise.legacy.adminrunner import log_handler
from google3.enterprise.legacy.adminrunner import machine_handler
from google3.enterprise.legacy.adminrunner import machparam_handler
from google3.enterprise.legacy.adminrunner import onebox_handler
from google3.enterprise.legacy.adminrunner import params_handler
from google3.enterprise.legacy.adminrunner import pattern_handler
from google3.enterprise.legacy.adminrunner import query_expansion_handler
from google3.enterprise.legacy.adminrunner import scoring_adjust_handler
from google3.enterprise.legacy.adminrunner import server_handler
from google3.enterprise.legacy.adminrunner import simple_handlers
from google3.enterprise.legacy.adminrunner import snmp_handler
from google3.enterprise.legacy.adminrunner import ssl_handler
from google3.enterprise.legacy.adminrunner import supportrequest_handler
from google3.enterprise.legacy.adminrunner import supportcall_handler
from google3.enterprise.legacy.adminrunner import trustedca_handler
from google3.enterprise.legacy.adminrunner import user_handler
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.adminrunner import federation_handler

True = 1
False = 0

class AdminRunnerServer:
  def __init__(self, enthome, installstate, port, box_keys_dir, license_keys_dir):
    ent_config = entconfig.EntConfig(enthome) # read-only entconfig object

    if not ent_config.Load():
      sys.exit('Cannot load configuration.')

    flags.FLAGS.gfs_aliases = ent_config.var('GFS_ALIASES')
    flags.FLAGS.bnsresolver_use_svelte = False
    flags.FLAGS.logtostderr = True
    gfile.Init()
    self.ss = pywrapselectserver.SelectServer()

    # Initialize the configurator.
    self.cfg = configurator.configurator(enthome,
                                         box_keys_dir = box_keys_dir,
                                         license_keys_dir = license_keys_dir,
                                         install_state = installstate,
                                         startup_mode = 1)
    self.cfg.lm.setInWorking()

    self.thread_pool = pywrapthreadpool.ThreadPool(1, 5, 5, 0)
    self.thread_pool.StartWorkers()
    self.server = pywraphttpserver.HTTPServer(self.ss, port, '1.0')
    self.server.SetTrustedClients(
      string.join(self.cfg.globalParams.var('HTTPSERVER_TRUSTED_CLIENTS'), ','))
    self.handlers = []

    self.RegisterSimpleGetHandler('/', self.RootHandler)
    self.RegisterSimpleGetHandler('/healthz', self.HealthzHandler)
    self.RegisterSimpleGetHandler('/servers', self.ServersHandler)
    self.RegisterSimpleGetHandler('/configversion', self.ConfigVersionHandler)
    self.RegisterSimpleGetHandler('/flushlog', self.FlushLogHandler)
    self.RegisterGetOrPostHandler('/legacy', self.LegacyHandler)
    self.RegisterSimplePostHandler('/legacyCommand', self.LegacyCommandHandler)

    license_handler.NewLicenseHandler(self)

  def RegisterSimpleGetHandler(self, uri, handler):
    self.RegisterHandler(uri, lambda r, s=self, h=handler:
                         s.SimpleGetHandler(r, h), None, None)

  def RegisterSimplePostHandler(self, uri, handler):
    self.RegisterHandler(uri, lambda r, s=self, h=handler:
                         s.SimplePostHandler(r, h), None, None)

  def RegisterGetOrPostHandler(self, uri, handler):
    self.RegisterHandler(uri, lambda r, s=self, h=handler:
                         s.GetOrPostHandler(r, h), None, None)

  def RegisterRequestReplyHandler(self, uri, handler):
    self.RegisterHandler(
      uri,
      lambda r, s = self, h = handler: s.RequestReplyHandler(r, h),
      None,
      None)

  def RegisterReplyHandler(self, uri, handler):
    self.RegisterHandler(
      uri,
      lambda r, s = self, h = handler: s.ReplyHandler(r, h),
      None,
      None)

  def RegisterCommandHandler(self, uri, handler):
    self.RegisterHandler(uri, lambda r, s=self, h=handler:
                         s.CommandHandler(r, h), None, None)

  def RegisterHandler(self, uri, handler, input_mapper, output_mapper):
    self.handlers.append(pywraphttpserver.HTTPServerRequestThreadHandler(
      uri, handler, input_mapper, output_mapper, self.server, self.thread_pool))

  def SimpleGetHandler(self, request, handler):
    request.SetContentTypeHTML()
    request.output().WriteString(handler())
    request.Reply()

  def GetOrPostHandler(self, request, handler):
    """Handle HTTP GET or POST request by calling handler(query).
    GetOrPostHandler expects the handler to take one argument. If the handler
    does not take an argument then use SimpleGetHandler().

    This argument will be the query string like:
    "command=params+getall&submit=Submit"

    Arguments:
      request: HTTPServerRequest object
      handler: Handler function, which takes one parameter (query string)
    """
    request.SetContentTypeHTML()
    if (request.input_headers().protocol() ==
        pywraphttpserver.HTTPHeaders.PROTO_GET):
      # Its a GET request, pull the query string from the url path
      path = request.req_path()
      query = ""
      if path.find('?') != -1:
        query = path[path.find('?') + 1:]
    elif (request.input_headers().protocol() ==
        pywraphttpserver.HTTPHeaders.PROTO_POST):
      # Its a POST request, pull the query string from the request input
      query = request.input().ReadToString()
    request.output().WriteString(handler(query))
    request.Reply()

  def CommandHandler(self, request, handler):
    ' handler would be called with an argument of type pywrapurl.URL'
    request.SetContentTypeTEXT()
    request.output().WriteString(handler(pywrapurl.URL(request.req_path())))
    request.Reply()

  def SimplePostHandler(self, request, handler):
    request.SetContentTypeHTML()
    request.output().WriteString(handler(request.input().ReadToString()))
    request.Reply()

  def RequestReplyHandler(self, request, handler):
    request.SetContentTypeTEXT()
    request.output().WriteString(handler(request.input().ReadToString()))
    request.Reply()

  def ReplyHandler(self, request, handler):
    request.SetContentTypeTEXT()
    request.output().WriteString(handler())
    request.Reply()

  def Loop(self):
    self.ss.Loop()

  # DOCTYPE declaration for HTML responses.
  STRICT_DOCTYPE = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">
'''

  ROOT_HANDLER_OUTPUT = '''
%s
<html>
<head>
<title>AdminRunner</title>
</head>
<body>
<h1>AdminRunner</h1>
<a href="/legacy">/legacy</a><br><br>
<a href="/varz">/varz</a><br><br>
<a href="/healthz">/healthz</a><br><br>
<a href="/servers">/servers</a><br><br>
<a href="/configversion">/configversion</a><br><br>
<a href="/flushlog">/flushlog</a><br><br>
</body>
</html>
''' % STRICT_DOCTYPE

  def RootHandler(self):
    return self.ROOT_HANDLER_OUTPUT

  LEGACY_HANDLER_HEADER = '''
%s
<html>
<head>
<title>/legacy</title>
<style>
  p { font: 10pt courier, monospace }
</style>
</head>
<body>
<form action="/legacy" method="POST">
<textarea name="command" cols="80" rows="20"></textarea><br>
<input type="submit" value="Submit">
</form><br>
''' % STRICT_DOCTYPE

  LEGACY_HANDLER_FOOTER = '''
<br>
</body>
</html>
'''

  HEALTHZ_OK = 'ok\n'

  def HealthzHandler(self):
    '''
    When the adminrunner runs on Python 2.1 and 2.2, E.getLocaltime has failed
    after the adminrunner has been running for several hours. This handler
    tries to run E.getLocaltime so loop_AdminRunner.py can restart the
    adminrunner if E.getLocaltime fails.
    '''

    success = True
    try:
      E.getLocaltime(time.time())
    except:
      success = False
    if success:
      return self.HEALTHZ_OK
    else:
      return ''

  SERVERS_HANDLER_HEADER = '''
%s
<html>
<head>
<title>Enterprise Servers</title>
</head>
<style>
  td { border: 1px solid black; padding: 4px }
</style>
<body>
<h1>Enterprise Servers</h1>
<table style="border-collapse: collapse">
<tr><td style="width: 20%%">Name</td><td>Instances</td></tr>
''' % STRICT_DOCTYPE

  SERVERS_HANDLER_TABLE_ROW_TEMPLATE = '<tr><td>%s</td><td>%s</td></tr>'

  SERVERS_HANDLER_FOOTER = '''
</table>
</body>
</html>
'''

  def ServersHandler(self):
    'Output a page with links to all the servers.'
    servers = self.cfg.getGlobalParam('SERVERS').items()
    for i in range(len(servers)):
      servers[i] = (servertype.GetTypeLevel(servers[i][0]), servers[i][0],
                    servers[i][1])
    servers.sort()
    output = self.SERVERS_HANDLER_HEADER
    for server in servers:
      output += self.SERVERS_HANDLER_TABLE_ROW_TEMPLATE % (
        server[0],
        string.join(map(lambda x: '<a href="http://%s/">%s</a>' % (x, x),
                        map(lambda x, y=server[1]: '%s:%d' % (x, y),
                            server[2])),
                    '<br><br>'))
    output += self.SERVERS_HANDLER_FOOTER
    return output

  def ConfigVersionHandler(self):
    return '%d\n' % self.cfg.getGlobalParam('CONFIGVERSION')

  def FlushLogHandler(self):
    logging.flush()
    return ''

  LEGACY_HANDLER_GET_OUTPUT = '%s%s' % (LEGACY_HANDLER_HEADER,
                                        LEGACY_HANDLER_FOOTER)

  def LegacyHandler(self, input):
    if input == '':
      return self.LEGACY_HANDLER_GET_OUTPUT
    args = cgi.parse_qs(input)
    command = args['command'][0] + '\n'
    response = self.LegacyCommandHandler(command)
    output = '%sCommand:<br><p>%s</p>Response:<p>%s</p>%s' % (
      self.LEGACY_HANDLER_HEADER,
      cgi.escape(command).replace('\n', '<br>'),
      cgi.escape(response).replace('\n', '<br>'),
      self.LEGACY_HANDLER_FOOTER)
    return output

  LEGACY_COMMAND_HANDLER_MAP = {
    'v'          : simple_handlers.v_handler,
    'file'       : file_handler.FileHandler,
    'gws'        : gws_handler.GwsHandler,
    'license'    : license_handler.LicenseHandler,
    'params'     : params_handler.ParamsHandler,
    'user'       : user_handler.UserHandler,
    'machine'    : machine_handler.MachinesHandler,
    'logreport'  : log_handler.LogReportsHandler,
    'pattern'    : pattern_handler.URLPatternHandler,
    'collection' : collection_handler.CollectionHandler,
    'frontend'   : frontend_handler.FrontendHandler,
    'diagnose'   : diagnose_handler.DiagnoseHandler,
    'epoch'      : epoch_handler.EpochHandler,
    'ssl'        : ssl_handler.SSLHandler,
    'server'     : server_handler.ServerHandler,
    'machparam'  : machparam_handler.MachParamHandler,
    'borgmon'    : borgmon_handler.BorgmonHandler,
    'supportrequest' : supportrequest_handler.SupportRequestHandler,
    'config'     : config_handler.ConfigHandler,
    'snmp'       : snmp_handler.SNMPHandler,
    'database'   : database_handler.DatabaseHandler,
    'trustedca'  : trustedca_handler.TrustedCAHandler,
    'supportcall': supportcall_handler.SupportCallHandler,
    'feedstatus' : feedstatus_handler.FeedStatusHandler,
    'queryexpansion' : query_expansion_handler.QueryExpansionHandler,
    'scoringadjust' : scoring_adjust_handler.ScoringAdjustHandler,
    'onebox'     : onebox_handler.OneBoxHandler,
    'crawlqueue' : crawlqueue_handler.CrawlQueueHandler,
    'debug'      : debug_handler.DebugHandler,
    'labs'       : labs_handler.LabsHandler,
    'alerts'     : alerts_handler.AlertsHandler,
    'federation': federation_handler.FederationHandler,
    }

  NON_AR_COMMANDS = ['v']

  def LegacyCommandHandler(self, data):
    # Get the command. It has the form: [key=value]* handler cmd [params]
    newline_pos = data.find('\n')
    first_line = data[:newline_pos].strip()
    logging.info('Executing legacy command: %s\n' % first_line)
    command_parts = first_line.split()
    data = data[newline_pos + 1:]

    # Get any prefixes.
    prefixes = {}
    last_prefix = -1
    for i in range(len(command_parts)):
      if command_parts[i].find('=') == -1:
        break
      key, value = command_parts[i].split('=', 1)
      prefixes[key] = value
      last_prefix = i

    # Get the handler and the command.
    handler = None
    if len(command_parts) > last_prefix + 1:
      handler = command_parts[last_prefix + 1]
    command = None
    if len(command_parts) > last_prefix + 2:
      command = command_parts[last_prefix + 2]

    # Get the parameters.
    parameters = command_parts[last_prefix + 3:]

    # Unquote if not disabled.
    if not prefixes.has_key('Q') or prefixes['Q'] != '0':
      for key, value in prefixes.items():
        prefixes[key] = urllib.unquote_plus(value)
      if command: command = urllib.unquote_plus(command)
      if parameters: parameters = map(urllib.unquote_plus, parameters)

    if handler not in self.LEGACY_COMMAND_HANDLER_MAP.keys():
      return 'NACKgoogle'

    handler_instance = self.LEGACY_COMMAND_HANDLER_MAP[handler](
      self, command, prefixes, parameters)
    handler_instance.handle_read(data)
    if handler not in self.NON_AR_COMMANDS:
      handler_instance.parse_args()
      handler_instance.execute()
    return handler_instance.handle_write()[1]

if __name__ == '__main__':
  import sys
  sys.exit('Import this module')

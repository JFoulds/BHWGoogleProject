#!/usr/bin/python2.4
#
# Generic webserver for everyone's pet projects
#
# Usage:
#   import webserver_base
#
#   def home_page():
#      print '<HTML><BODY>'
#      print '  Hi.'
#      print '</BODY></HTML>'
#
#   def cgi_search(q='foo', start='0', num='10'):
#      "This handles queries of the form /search?q=foo&start=0&num=10"
#      pass
#
#   webserver_base.handlers = vars()
#   webserver_base.go()
#
# You can define a home_page() and also a cgi_* for any /*? you want to have
#
# If you want to abort the current call and return to the webserver,
# do something like this:
#
#   class Abort: pass
#
#   def cgi_foo():
#      try:
#         my_fn_call()
#      except Abort:
#         pass
#
#   def my_fn_call():
#      if something_bad: raise Abort

# Known bugs/features:
# - the home page "/" is treated specially and cannot accept cgi arguments

import BaseHTTPServer
import cgi
from google3.enterprise.legacy.util import fast_multifile
from google3.enterprise.legacy.util import readxlb
from google3.enterprise.legacy.web import localizer
import os
import rfc822
import select
import SimpleHTTPServer
import socket
import SocketServer
import string
import sys
import tempfile
import time
import urllib

handlers = {}
extra_HTTP_headers = []


class EncodedOutput:
  """Write file output as UTF-8.
  
  This is a helper class to write to a file using utf-8.  This class wraps
  a file, and applies the utf-8 encoding to any writes.
  """

  def __init__(self, outfile):
    self.outfile = outfile

  def write(self, s):
    """Write data encoded as UTF-8."""
    self.outfile.write(s.encode('utf-8'))

class ServerClass(BaseHTTPServer.HTTPServer):
    # Override this for a custom handler
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        BaseHTTPServer.HTTPServer.server_bind(self)

    def handle_request(self):
        # Select loop .. to handle Ctrl-C properly
        while 1:
            try:
                r, _, _ = select.select([self.socket], [], [], 0.1)
            except KeyboardInterrupt:
                raise SystemExit, 'Stopping %s:%s' % (
                    sys.argv[0], self.server_address[1])
            if r:
                return BaseHTTPServer.HTTPServer.handle_request(self)
        return ""

    def setLocalizationInfo(self, xlb_file, languages):
      ''' Initializes the localization information.

      Overview of localization:
        Localized language support requires:
        a) xlb files containing the language strings
        Then call setLocalizationInfo() to initialize localization.
        Call webserver_base.GetMsgs() to get the whole message dictionary,
        or webserver_base.GetMsg() to get a single message.

      Inputs:
        xlb_file: the path to the xlb file (without _xx.xlb
          suffix) that holds the localizations.
        languages: a tuple of supported languages (['en', 'fr'])
      '''

      self.xlb_file = xlb_file
      self.supported_languages = languages
      # Setting self.catalogs to non-null turns on localization
      self.catalogs = {} # Dictionary from language to message dictionary

    def getLanguageCatalog(self, args, accept_language_header):
      ''' Returns the appropriate language catalog for the args and header,
      using the xlb_file assigned earlier.
      Returns a message catalog mapping from ids to UTF-8 messages.
      '''
      if not self.__dict__.has_key('catalogs'):
        return None
      # Determine the requested languages and then the best one to use
      desired = localizer.LangPrefs(args, accept_language_header)
      lang = localizer.BestLanguage(self.supported_languages, desired)
      # Store current language in a global variable for use later
      global current_language
      current_language = lang
      return self.getSpecificLanguageCatalog(lang)

    def getSpecificLanguageCatalog(self, lang):
      ''' Returns the language catalog specified.

      This routine caches the language catalog in self.catalogs.  If the
      catalog is not loaded it calls readxlb.
      If no catalog is available, it returns None.
      '''
      if not self.__dict__.has_key('catalogs'):
        return None
      if not self.catalogs.has_key(lang):
        # Read the xlb file and generate and cache the catalog
        xlb_file = '%s_%s.xlb' % (self.xlb_file, lang)

        # Read xlb catalog
        xlb_catalog = readxlb.Read(xlb_file)
        # Initialize catalog to English
        if lang == 'en':
          self.catalogs[lang] = xlb_catalog
        else:
          # Initialize with English catalog.
          self.catalogs[lang] = self.getSpecificLanguageCatalog('en').copy()
          # Then replace with xlb messages.
          # Thus, missing messages default to English
          self.catalogs[lang].update(xlb_catalog)

      return self.catalogs[lang]

class ForkingServer(SocketServer.ForkingMixIn, ServerClass):
    pass

class HandlerClass(SimpleHTTPServer.SimpleHTTPRequestHandler): # Override?
    # Simpler log lines
    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s: %s\n" %
                         (self.log_date_time_string(),
                          self.client_address[0], # host
                          format % args))

        # The dispatcher -- find handlers for each CGI request
    def do_POST(self):
        # a small utility function to get the ";" seperated parameters list
        # from an http header.  [same as mimetools.Message.getplist(), but for
        # _any_ header field].
        def get_header_params(message, name, default):
            s = message.getheader(name, default)
            parts = string.split(s, ';')
            pmap = {}
            for x in parts[1:]:
                x = string.strip(x)
                if '=' in x:
                    # a name=value pair; split it and strip quotes from value
                    key, value = string.split(x, '=', 1)
                    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                        value = value[1:-1]
                else:
                    # no value, use ''
                    key = x
                    value = ''
                if not pmap.has_key(key):
                    pmap[key] = value

            return parts[0], pmap

        content_type, content_params = get_header_params(self.headers,
                                                         'content-type',
                                                         "application/octet-stream")
        user_agent = self.headers.getheader('user-agent', 'Mozilla')

        content_len_str = self.headers.getheader('content-length', "0")
        try:
            content_len = int(content_len_str)
        except:
            content_len = 0


        args = {}
        mfiles = {}

        if content_type == 'multipart/form-data' and \
           content_params.has_key("boundary") and \
           content_len > 0:
            boundary = content_params["boundary"]

            mfile = fast_multifile.FastMultiFile(self.rfile,
                                                 boundary,
                                                 content_len)

            # multipart/form-data can contain files which we may want to
            # use, but these files might be too big to fit into memory.
            # We do the follow with all mutipart/form-data parts:
            #  1. take the first 1K of the body and pass it as a query arg
            #  2. read the entire body into a temp file, open an fd to it,
            #     and stick it in the special 'mfile' arg (which is a map
            #     from arg name).
            i = 0
            while 1:
                i = i + 1
                message = rfc822.Message(mfile, 0)

                disp, disp_params = get_header_params(message,
                                                      'content-disposition',
                                                      '')
                name = disp_params.get('name', None)

                # write the multipart into a temp file (it could be huge!)
                tempfile.tempdir = '/export/hda3/tmp/'
                tmp_filename = tempfile.mktemp('.webserver_multipart')

                tmp_file = None
                try:
                    tmp_file = open(tmp_filename, 'w')

                    # read the first 1K into body, we'll use it below
                    body = mfile.read(1024)
                    # write this, and the rest of the body in the temp file
                    tmp_file.write(body)
                    while 1:
                        block = mfile.read(10240)
                        if len(block) == 0: break

                        tmp_file.write(block)

                    tmp_file.close()

                    # open an fd to this file; remember it by number and name
                    mfiles[i] = open(tmp_filename, 'r')
                    if name != None:
                        mfiles[name] = mfiles[i]
                except IOError, e:
                    self.log_message("Error writing %s: %s",
                                     tmp_filename, str(e))

                # Note: we always delete the temp file.  Since we
                # opened an fd (in mfiles) to the file _before_ we delete
                # it, the file will still be accessible via the fd, but
                # will get cleaned up as soon as the fd is closed.
                # This gives us automatic file cleanup, even if the process
                # crashes.
                try:
                    os.unlink(tmp_filename)
                except OSError, e:
                    self.log_message("Error unlinking %s: %s",
                                     tmp_filename, str(e))

                # if this part had a name, take the first 1K that we
                # read earlier and treat it as a query arg
                if name != None:
                    if body[-1:] == '\n': body = body[:-1]
                    if body[-1:] == '\r': body = body[:-1]
                    args[name] = body

                if not mfile.next(): break

        elif content_type == 'application/x-www-form-urlencoded' and \
             content_len > 0:
            body = self.rfile.read(content_len)
            for key,value in cgi.parse_qs(body).items():
                args[key] = value[0]

            # IE deposits extra "\r\n" for POST.
            # If we do not flush these characters, IE complains that
            # page not found. More on this is available at:
            # http://lists.bikeworld.com/pipermail/thttpd/2000-November/000266.html

            if (string.find(string.lower(user_agent), "msie") >= 0):
                # Yikes. sometimes IE does NOT send these bytes (after timeout)
                # so we can't rely on the extra 2 bytes being there. Hence,
                # we drain the #$#@ socket.
                while 1:
                    r, _, _ = select.select([self.connection], [], [], 0.1)
                    if len(r) == 0: break
                    # be extra super careful to not block
                    data = self.connection.recv(2, socket.MSG_PEEK)
                    data = self.rfile.read(len(data))

        # insert mfiles as a special arg
        args['mfiles'] = mfiles

        self.do_GET(parsed_args = args)
        return


    # The dispatcher -- find handlers for each CGI request
    def do_GET(self, path_suffix=None, parsed_args=None):
        if parsed_args is None: parsed_args = {}
        _SetMsgs(self.server.getLanguageCatalog(parsed_args,
                        self.headers.getheader('accept-language', '')))

        if path_suffix:
            self.path = self.path + path_suffix
            sys.stderr.write("path extended:%s" % self.path)
        argpos = string.find(self.path, '?')
        if ( argpos < 0 or parsed_args != {} ) and \
           handlers.has_key('cgi_'+self.path[1:]):
            # It's a CGI call with no args but without the ?
            argpos = len(self.path)
        if self.path == '/':
            self.send_response(200)
            self.wfile.write('content-type: text/html\n\n')
            oldout = sys.stdout
            sys.stdout = EncodedOutput(self.wfile)
            try: handlers['home_page']()
            finally: sys.stdout = oldout
        elif argpos < 0:
            # based on SimpleHTTPRequestHandler.do_GET but applying
            # the localization message catalog to html files
            f = self.send_head()
            if f:
              data = f.read()
              if self.path.endswith('.html'):
                lmsgs = GetMsgs()
                if lmsgs:
                  data = data % lmsgs
              self.wfile.write(data)
              f.close()
        else:
            oldout = sys.stdout
            args = parsed_args
            args['client_ip'] = self.client_address[0]
            args['client_port'] = self.client_address[1]
            for key,value in cgi.parse_qs(self.path[argpos+1:]).items():
                args[key] = value[0]

            try:
                handler = handlers['cgi_'+self.path[1:argpos]]
            except KeyError:
                self.send_response(404)
                self.wfile.write('content-type: text/html\n\n')
                self.wfile.write('<BODY>No such handler ')
                self.wfile.write(`self.path[1:argpos]`)
                self.wfile.write('</BODY>\n')
                return

            success = 0
            try:
                t = time.time()
                sys.stdout = EncodedOutput(self.wfile)
                self.send_response(200)
                self.send_header('content-type', "text/html")
                try:
                  for header in extra_HTTP_headers:
                    self.send_header(header[0], header[1])
                except:
                  self.log_message('Could not send all optional headers')

                self.end_headers()
                try:
                    apply(handler, (), args)
                except KeyboardInterrupt:
                    raise SystemExit, 'Stopping %s' % sys.argv[0]
                success = 1
            finally:
                if not success:
                    print '(Error -- see logs for traceback)'
                sys.stdout = oldout
                self.log_message('Done: %1.3f seconds', time.time()-t)

    def list_directory(self, path):
        """Don't allow listing directories."""
        self.send_error(403, "No permission to list directory")
        return None

#
# PUBLIC SERVICE MESSAGE:
#  forking = 1 does not work at this time, don't try it or else you will
#              loose one hour to figure out what's wrong, like I did
#
def go(forking=0, port_range=None, extra_http_headers=[],
       xlb_file=None, languages=None):
    '''xlb_file is the prefix of the path to the language xlb file.
       languages is the tuple of supported languages.
       '''
    global extra_HTTP_headers
    if not handlers.has_key('__name__'):
        raise SystemExit, 'Set webserver_base.handlers before calling go()'
    if not port_range: port_range = xrange(7777,8000)
    for port in port_range:
        try:
            server = ServerClass
            if forking: server = ForkingServer
            httpd = server(('', port), HandlerClass)
            if xlb_file:
              httpd.setLocalizationInfo(xlb_file, languages)
            print 'Starting %s:%s' % (sys.argv[0], port)
            break
        except socket.error:
            pass
    else:
        print 'Failed to find a port.'
        return
    extra_HTTP_headers = extra_http_headers
    while 1:
        try: httpd.serve_forever()
        except IOError: pass # Usually a broken pipe
        except socket.error: pass # Broken connection; sometimes IE
        except KeyboardInterrupt: break

# Store localization messages in a global variable so the client can
# access them easily.  This will be okay if the server handles one
# request at a time
msgs = {}
current_language = None
def GetMsgs():
  '''Returns message catalog'''
  global msgs
  return msgs

def GetMsg(msg):
  '''Returns translation of msg'''
  global msgs
  return msgs.get(msg, msg) # Return msg if no translation

def GetLanguage():
  """Returns current language as a string"""
  global current_language
  return current_language

def _SetMsgs(in_msgs):
  '''Sets message catalog.'''
  global msgs
  msgs = in_msgs

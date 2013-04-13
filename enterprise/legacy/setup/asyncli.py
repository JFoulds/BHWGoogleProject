#!/usr/bin/python2.4

# asyncli.py

# Allow a client to query data from several sources in parallel.
#   The approach is to
#   - create a bunch of objects initialised with host, port and request
#   - asynchronously have each object connect to its host and port
#   - write the request then shutdown the socket for writes
#   - in collectresponses wait upto a specified number of seconds
#     for all responses to come in

import asyncore
from google3.enterprise.legacy.setup import prodlib
import socket
import operator
import string
import sys
import time

if sys.modules["socket"].__name__ == "timeoutsocket":
  SSocket = sys.modules["_timeoutsocket"]
else:
  SSocket = sys.modules["socket"]

def _readsum(sockets):
  return reduce(operator.add, map(lambda s : len(string.join(s.reads_, '')), sockets))

def _writesum(sockets):
  return reduce(operator.add, map(lambda s : s.sent_, sockets))

class AsynClient(asyncore.dispatcher):
  def __init__(self, hostport, request, half_shutdown=1):
    # half_shutdown: if true, the write-side of the socket will be
    # shutdown ASAP.  Note that as of 08/27/2003 gws does not handle
    # half-shutdowns well.
    asyncore.dispatcher.__init__(self)  # init base class
    self.hostport_ = hostport
    self.err_ = None
    self.sent_ = 0
    self.reads_ = []
    self.writable_ = 1
    self.readable_ = 1
    self.create_socket(SSocket.AF_INET, SSocket.SOCK_STREAM)
    self.request_ = request
    self.reqlen_ = len(request)
    self.readbuf_size_ = 4096

    self.__half_shutdown = half_shutdown
    # Ignore errors thrown in connection so that we do not
    # break out of all connections.  This will end up being reported
    # to the user in any case with self.err_.
    try:
      self.connect(self.hostport_)
    except socket.error:
      pass

  # accessors
  def host(self):
    return self.hostport_[0]
  def port(self):
    return self.hostport_[1]
  def hostport(self):
    return self.hostport_

  def failed(self):
    return self.err_ != None

  def close(self):
    self.writable_ = 0
    self.readable_ = 0
    self.log("Closing socket for %s:%s" % self.hostport_)
    asyncore.dispatcher.close(self)

  def readable(self):
    return self.readable_

  def writable(self):
    return self.writable_

  def handle_read_event(self):
    if not self.readable_:
      return
    buf = self.recv(self.readbuf_size_)

    # a readable socket returned no bytes
    if len(buf):
      self.reads_.append(buf)
    else:
      self.readable_ = 0

  def handle_error(self, *info):
    # The prototype for handle_error is different for 2.x and 1.5:
    #   2.x: def handle_error (self)
    #   1.5: def handle_error (self, *info):
    #           with exception info in info
    if not info:
      # python 2.x
      _, exc_type, exc_value, exc_traceback = asyncore.compact_traceback()
    else:
      # python 1.5
      (exc_type, exc_value, exc_traceback) = info
    self.err_ = (exc_type, exc_value)
    prodlib.log("error encountered: %s-%s" % self.err_) # stderr logging!
    del exc_traceback
    self.close()

  def handle_write_event(self):
    if not self.writable_:
      return
    self.log("sending %s" % self.request_[self.sent_:])
    n = self.send(self.request_[self.sent_:])
    self.sent_ = self.sent_ + n
    if self.sent_ >= self.reqlen_:
      self.writable_ = 0
      self.log("already sent %s > %s. Shutting down socket" %
               (self.sent_, self.reqlen_))
      # GWS does not respond if shutdown is called immediately
      # after a send.  GWS has some special code to handle
      # such cases and that code gets triggered only if we
      # add a small delay between when the send call is made
      # and the shutdown call is made
      if self.__half_shutdown:
        time.sleep(0.02)
        n = self.socket.shutdown(1) # No more sends

  def handle_close(self):
    self.log('close %s:%d' % self.hostport_)
    self.close()

  def getdata(self):
    return string.join(self.reads_, '')

  # kill asyncore logging
  def log(self, message):
    pass


# collect whatever data we can get from a number of primed sockets
# within timeout seconds
def loop(timeout, use_poll=0):
  if use_poll:
    poll_fun = asyncore.poll2
  else:
    poll_fun = asyncore.poll

  waittill = time.time() + timeout
  while asyncore.socket_map:
    nsecs = waittill - time.time()
    if nsecs < 0:
      break

    poll_fun(nsecs)

# Given a list of host/port pairs, sends the specified request to all
# servers. It also keeps a per-hostport retry cnt to accomodate
# various transient errors (like EAGAIN)
def AsynRequest(hostportlist, request, timeout, retrycnt=3, half_shutdown=1):
  retries = {}
  clients = {}

  hostports = hostportlist
  delay = 1
  while hostports:
    # Clear the asyncore socket map before every loop. Otherwise, if we have a
    # dead server, then the socket corresponding to that server will stay in
    # the map for all the following retry attempts.
    asyncore.socket_map = {}
    # For each AsynClient, a socket is created and the map updated so that
    # the socket can be polled during the next loop() call
    for hostport in hostports:
      clients[hostport] = AsynClient(hostport,
                                     request,
                                     half_shutdown=half_shutdown)  # connect
      retries[hostport] = retries.get(hostport, 0) + 1   # update counter

    # enter the select loop
    loop(timeout)

    # go through the client list and see if anyone failed
    hostports = []      # start from scratch. assume all replies came back fine
    for hostport, client in clients.items():
      if client.failed() and retries[hostport] < retrycnt:
        # Some error occured. Put it back in the list and try again
        prodlib.log("Error on %s port %s: %s %s" % (hostport + client.err_))
        hostports.append(hostport)

    if hostports:              # any retries needed?
      time.sleep(delay)        # ... then wait for better times
      if delay < 20:
        delay = delay * 2      # exponential backoff

  return clients.values()

# Utility method to find HTTP status code from an http request.  This
# currently only works with HTTP/1.0 responses.  Returns -1 if no
# status can be found.
def GetHTTPStatus(reply):

  for headerline in string.split(reply, '\n'):  # parse HTTP headers
    fields = string.split(headerline)
    if len(fields) < 2: continue    # ignore empty lines
    if fields[0] == 'HTTP/1.0':     # look for "HTTP/1.0 200 ..." lines
      reply_status = int(fields[1]) # ... and fetch the HTTP status
      return reply_status
  else:
    return -1

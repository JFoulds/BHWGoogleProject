#!/usr/bin/python2.4
#
# (c) 2000 Google inc.
#
# Catalin Popescu 7/2000
#
# This simply will start a connection with a host on a specified port
# and send a command (probably v). It stops after the first ACKgoogle
#
# This is used by start_localcrawl.py to check periodically the number of
# crawled and uncrawled urls.
#
# This includes a more versatile "TCPTalk" function that lets you specify
# what to wait for (e.g., ACKgoogle) or specify a number of bytes to receive,
# and whether the passed hostname should be looked up in the DNS database
#
#
# Note: You can run TCP talk with an external alarm, but if a timeout is
# specified, the outer alarm handler is disabled! So be careful :)
#
############################################################################

"""
Usage:
   port_talker.py <host> <port> <command> <timeout>
"""

import commands
import socket
import string
import sys
import signal
import re

############################################################################

#  some bools
TRUE = 1
FALSE = 0

digitsAndDots = re.compile('^[\d.]+$')


############################################################################

def alarmHandler(signum, frame):
  raise IOError, "Host not Responding"

############################################################################
#
# talk to a tcp server and optionally send command
#
# args : hostname, port
#        command (if '', don't send anything)
#        terminator ('' if not used)
#        max_len (max number of bytes to read)
#        external_lookup: if != None, do a DNS lookup on hostname
# returns : (status, response) tuple
# status can be
#  0 - OK
#  1 - no route to host or connection refuse or cannot resolve
#  2 timeout (ACL'ed ?)

def TCPTalk(hostname, port, timeout, command = '',
            terminator = '', max_len = 0, external_nslookup = 0):

  # Setup the alarm but save existing alarm handler
  if timeout > 0:
    prevhandler = signal.signal(signal.SIGALRM, alarmHandler)
    prevalarm = signal.alarm(timeout)

  status = 0
  response = ''
  try:
    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # this is useful if the DNS server has changed during the runtime
    # of this python script - it will force the new DNS entry to be used.
    # Don't do a lookup though if the hostname is already an IP address
    if external_nslookup and not digitsAndDots.match(hostname):
      err, hostname = commands.getstatusoutput(
        "$ENTERPRISE_HOME/local/google/bin/safe_gethostbyname %s" %
        commands.mkarg(hostname))
      hostname = string.strip(hostname)
      if err != 0:
        status = 1
        response = "Cannot resolve"

    if status == 0:
      s.connect((hostname, port))

      if (command == '' and terminator == None and max_len ==0):
        s.close() # short-circuit the case where we just wanted to test connect
      else:
        if command != '':
          s.send(command)

          # read until terminator is encountered
          # OR (if max_len >=0,) maxlen bytes are read
          while 1:
            buf = s.recv(256)
            response = response + buf
            if terminator and string.rfind(response, terminator) >= 0: break
            if max_len >= 0 and len(response) > max_len: break
            if len(buf) == 0: break # EOF

  # socket error occured
  except socket.error, e:
    status = 1
    response = str(e)
  #another exception (probably ACLed)
  except Exception, e:
    status = 2
    response = str(e)
  s.close()

  if timeout > 0:
    # done with alarm handler, reset to previous
    signal.signal(signal.SIGALRM, prevhandler)
    signal.alarm(prevalarm)

  return (status, response)


# maybe should be renamed everywhere as GoogleTalk or so
#
# this one just returns status code TRUE or FALSE, depending on whether the
# whole transaction worked
def Talk(hostname, port, command, timeout):
  stat, resp =  TCPTalk(hostname, port, timeout, command + "\nc\n",
                        "ACKgoogle\n", -1)
  # translate result codes in what the old interface likes to get
  if stat == 0:
    stat = TRUE
  else:
    stat = FALSE

  return (stat, resp)

############################################################################

def main(argv):

  # Parse the command line
  try:
    hostname = argv[0]
    port = string.atoi(argv[1])
    command = argv[2]
    timeout = string.atoi(argv[3])
  except:
    sys.exit(__doc__)


  response = Talk(hostname, port, command, timeout)
  sys.stdout.write(response[1])

  sys.exit(not response[0])

############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

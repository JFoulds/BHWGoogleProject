#!/usr/bin/python2.4
#
# (c)2001 and onward Google inc
# Max Ibel
#
# Utility to probe connectivity of current machine
#
# Test
# - gateway
# - DNS
# - SMTP
# - NTP
#
# - for each collection: try to contact each webserver
# - check date on each webserver
#
# we want to do this in stages:
# - ping gateway. If that fails. stop.
# - ping DNS/etc. If that fails, stop
# - try to perform DNS lookups, mail, etc.
#   * if connect hangs, probably ACL'ed
#   * if connect fails, probly servers got decommisioned
#   * if application errors occur, dunno
#
# - for webservers, the same applies (ACL'ed, can't connect (server down).
#   should also check return status of home page. And date
#
###############################################################################
"""
Usage:
    network_diag.py -interactive
    or
    network_diag.py -interactive fsgw_node
    or
    network_diag.py -interactive fsgw_node fsgw_port
    or
    network_diag.py <google config file> -batch test_urls

    In the first case, we read commands in from stdin, and call the
    appropriate handlers. In the second case, we check everything, plus the
    urls specified on the command line
"""

import commands
import os
import string
import sys
import urlparse
import re

# to be able to use validators
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.production.babysitter import config_namespace  ## TODO: take this out and use entconfig.py
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.util import port_talker
from google3.pyglib import logging

fsgw_port = 21200
fsgw_host = 'localhost'

###############################################################################
###############################################################################
# Santa's little helpers

# should we log or not?
LOGFILE = None

# list of status items (type, name, status)
RESULT = []

# overall status of diagnostic.
# 0 == OK
# 1 == screwed up (can't use, say all DNS servers are bad)
# 2 == messed up input to this script
STATUS = 0

# some useful ports
DNS_PORT  = 53
SMTP_PORT = 25

# This is how the services are called in the input (simple to parse)
SMTP_SERVER       = "SMTPServer"
NTP_SERVER        = "NTPServer"
DNS_SERVER        = "DNSServer"
GATEWAY           = "Gateway"
SYSLOG_SERVER     = "SYSLOGServer"
TEST_URL          = "TestURL"
EXTERNAL_WEB_NAME = "ExternalWebName" # deprecated

# This is what the service is called in the output (nice formatting)
SERVICE_NAMES = {
  SMTP_SERVER       : "SMTP Server",
  NTP_SERVER        : "NTP Server",
  DNS_SERVER        : "DNS Server",
  GATEWAY           : "Default Gateway",
  SYSLOG_SERVER     : "Syslog Server",
  TEST_URL          : "Test URL",
  EXTERNAL_WEB_NAME : "Hostname" # deprecated
  }

def add_info(name, type, status):
  """Add an error to stored errorlist"""
  global RESULT
  RESULT.append((SERVICE_NAMES[type], name, status))

def get_info(withLen=0):
  """return all current errors as a string and clear errors"""
  global RESULT

  # Format RESULT nicely, one item per line. Oh yeah!
  ret = string.join(map(lambda y: string.join(map(repr, y)), RESULT), '\n')

  if withLen: # send with length and status for AdminRunner's CommandPipe
    ret = str(len(RESULT) + 1) + '\n' + str(STATUS) + '\n' + ret

  RESULT = []
  return ret

def get_raw_info():
  """get RESULT"""
  global RESULT
  return RESULT[:]

def clear_info():
  """clear RESULT"""
  global RESULT
  RESULT = []

###############################################################################
###############################################################################
# scripts to check network components

#
# ping a machine and see if it comes up
#
# Note: if name is not specified as IP address, we'll do a DNS lookup for it
#       (which requires the DNS servers to be up).
def ping_machine(name):
  """is machine pingable?"""
  return  os.system("alarm 5 fping %s >& /dev/null" % commands.mkarg(name))
#
# try to connect to a machine via TCP on a given port
# assumes that it can resolve name
#
# returns: 0 - OK
#          1 - cannot connect
#          2 - TIMEOUT
#
def tryconnect(name, port):
  """Can we connect to machine (giving optional command)"""
  return port_talker.TCPTalk(name, port, 2, '', None, 0, 1) # use ext. resolver

#
# Looks up a host on a specified server
#
# Note: we do _not_ use 'nslookup' anymore, we use 'host' instead, as
# it works even when reverse DNS lookup is not working. nslookup requires
# reverse PTR entries for both the querying server and the DNS server itself.
#
# returns: 0 - OK
#          1 - timeout
#          2 - cannot resolve name
#
digitsAndDots = re.compile('^[\d.]+$')
def nslookup(name, dnsserver='', prevent_unqualified_dns=True):
  """check whether DNS servers are up to snuff"""
  # if it looks like an IP address, don't try to resolve it
  if digitsAndDots.match(name):
    return (0, "OK")
  if name != "localhost" and prevent_unqualified_dns:
    name = name + "." # prevent unqualified DNS lookups

  # TODO: we really want to call something along the lines of
  # google2/io/safe_gethostbyname, this will require some python trickery.

  # If dnsserver is an empty string, then mkarg() will escape it with
  # quotes and the host call will try to use "''" as a dns server and fail
  # So call mkarg only if actually given a non-empty-string dnsserver
  if not dnsserver:
    dnsserver = ''
  if dnsserver != '':
    dnsserver = commands.mkarg(dnsserver)

  executestring = commands.mkarg(
    "host -t a %s %s 2>/dev/null | grep has\ address | wc -l"
    % (commands.mkarg(name), dnsserver))

  (stat, out) = commands.getstatusoutput('alarm 5  sh -c %s' % executestring)
  if stat != 0:
    return (1, "TIMEOUT") # E.g. DNS server does not respond

  if int(out) == 0:
    return (2, "cannot resolve")

  return (0, "OK")

def check_ntpdate_output(name):
  """ run "ntpdate -q" command on a server, and return the result.

  Args:
    name - 'time1.corp.google.com'
  Returns:
    (0, {'delay': '0.02591', 'stratum': '2', 'offset': '-0.030579',
         'server': '172.24.0.11'})
  """

  cmd = '/usr/sbin/ntpdate -q  %s' % commands.mkarg(name)
  (stat, out) = commands.getstatusoutput(cmd)
  parsed_out = {}
  if stat == 0:
    # only interested in the attributes in the first line
    lines = out.split('\n')
    attrs = lines[0].split(',')
    for i in range(len(attrs)):
      list = attrs[i].split()
      parsed_out[list[0].strip()] = list[1].strip()
  else:
    logging.warn('Command "%s" failed with exit status %d: %s' % (cmd, stat,
      out))
  return (stat, parsed_out)

def Check_NTP(name):
  """this function tries to verify the NTP server.

  Args:
    name - 'time1.corp.google.com'
  Returns:
    0 - OK
    1 - cannot resolve
    2 - cannot ping
    3 - cannot NTPDATE
    4 - stratum level too high (>=15)
  """

  if nslookup(name)[0] != 0:
    add_info(name, NTP_SERVER, "cannot resolve NTP server")
    return 1
  if ping_machine(name) != 0:
    add_info(name, NTP_SERVER, "cannot ping NTP server")
    return 2

  (stat, out) = check_ntpdate_output(name)
  if stat != 0:
    add_info (name, NTP_SERVER, "unable to contact NTP server")
    return 3

  if 'stratum' in out:
    stratum = int(out['stratum'])
    if stratum >= 15:
      add_info (name, NTP_SERVER, "NTP server stratum level too high")
      return 4

  add_info (name, NTP_SERVER, "OK")
  return 0

#
# this function tries to verify the NTP server
#
# returns: 0 - OK
#          1 - cannot resolve
#          2 - cannot ping
#          3 - cannot NTPDATE
def Check_SYSLOG(name):
  """Can we contact the SYSLOG server?
  Note: only does UDP, no feedback, so I can only try to ping the server"""

  if name == None: return 0 # Syslog server is optional

  if nslookup(name)[0] != 0:
    add_info (name, SYSLOG_SERVER, "cannot resolve SYSLOG server")
    return 1

  if ping_machine(name) != 0:
    add_info(name, SYSLOG_SERVER, "cannot ping SYSLOG server")
    return 2
  add_info(name, SYSLOG_SERVER, "OK")
  return 0

#
# this function tries to verify the SMTP server
#
# returns: 0 - OK
#          1 - cannot resolve
#          2 - cannot connect
#          3 - ACL'ed ?
#          4 - cannot HELO
def Check_SMTP(name, my_ip):
  """check on our SMTP server"""

  if nslookup(name)[0] != 0:
    add_info (name, SMTP_SERVER, "cannot resolve SMTP server")
    return 1
  if ping_machine(name) != 0:
    add_info(name, SMTP_SERVER, "cannot ping SMTP server")
    return 2

  status, err = tryconnect(name, SMTP_PORT)
  if status == 1 or status == 2:
    add_info(name, SMTP_SERVER, err)
  if status == 1:
    # if we time'd out, things can still be OK (say reverse DNS problems)
    # so return only an error if no timeout
    return 3

  stat, out = port_talker.TCPTalk(name, SMTP_PORT,
                                  60, # timeout (>30sec for messed up servers)
                                  "HELO " + my_ip + "\r\nQUIT\r\n",
                                  None, # terminator
                                  1024, # max len
                                  1) # use external resolver

  # expected answer:
  #220 'mail.forobozz.com' ESMTP
  #250 mail.frobozz.com Hello grue.frobozz.com [192.168.0.21], pleased to meet ya
  #221 mail.frobozz.com closing connection

  # Each line can be repeated several times, so we check that all codes appear
  # and that no other codes appear
  codes = map(lambda x: x[:4], string.split(out, '\n'))
  valid_codes = ('220 ', '250 ', '221 ', '')
  try:
    for code in codes:
      assert(code in valid_codes)
    for valid in valid_codes:
      assert(valid in codes)
  except:
    # If we wanted, we could check whether reverse DNS lookup is not working.
    # This would be the most likely explanation
    add_info(name, SMTP_SERVER, "cannot HELO SMTP server")
    return 4
  add_info(name, SMTP_SERVER, "OK")
  return 0


# Ad-hoc-ish transformations to UNC URLs so that they exist in a format
# which urlparse can handle
def standardize_url(url):
  smb_protocols = ['smb://', 'unc://', 'unc:\\\\', '\\\\']
  for smb_protocol in smb_protocols:
    if not url.find(smb_protocol):
      url = "file://" + url[len(smb_protocol):]
      url = url.replace('\\', '/')
      break
  return url


# checks a url and returns an (errorstatus, errordescription) tuple
# returncode:
# 0 - OK
# 1 - cannot resolve
# 2 cannot ping
# 3 - cannnot connect
# 4 - returncode != 200
# 5 - exception
def check_url(u, dns_servers):
  """Check whether URL is crawlable (connectivity) and resolvable
  from all dnsservers"""

  # very first, validate URL
  standardized_u = standardize_url(u)
  validator_context = validatorlib.ValidatorContext(file_access=0,
                                                    dns_access=0)
  UrlValidator = validatorlib.URL()
  if  (UrlValidator.validate(standardized_u, validator_context)
       not in validatorlib.VALID_CODES):
    add_info(u, TEST_URL, "Not a valid URL")
    return 1

  # first, isolate protocol, and (host name and port)
  protocol, hostport, _, _, _, _ = urlparse.urlparse(standardized_u)

  # urlparse is a good_for_very_little library, we're going to parse
  # out the path ourselves:
  path = u[string.find(u, hostport)  + len(hostport):]

  hostport = string.split(hostport, ":")
  host = hostport[0]
  if len(hostport) == 1:
    port = 80
  else:
    port = int(hostport[1])

  # can we resolve the host ?
  dns_problems = 0
  for dns_server in dns_servers:
    stat,err = nslookup(host, dns_server, prevent_unqualified_dns=False)
    if stat != 0:
      add_info(u, TEST_URL, "cannot resolve on DNS server %s" % dns_server)
      dns_problems = dns_problems + 1
  # if all dns servers failed, we're done
  if dns_problems == len(dns_servers):
    return 1

  # Try to connect
  if protocol == "file":
    # Contact the filesystem gateway
    command = 'GET /getFile?origUrl=smb://' + host + path + \
      '&sessionId=CRAWL HTTP/1.0\r\nAccept: */*\r\n\r\n'
    if verify_url(u, fsgw_host, fsgw_port, command) == 1:
      test_ping(u, host)
      return 1

  else:  # We assume HTTP
    status, err = tryconnect(host, port)
    if status != 0:
      add_info(u, TEST_URL, err[string.find(err, "'") + 1: -2])
      #do ping test now since tcp connect failed
      test_ping(u, host)
      return 1
    # try to fetch homepage
    command = 'HEAD ' + path + ' HTTP/1.0\r\nAccept: */*\r\nHost: ' + host + \
      '\r\n\r\n'
    return verify_url(u, host, port, command)

def test_ping(u, host):
  if ping_machine(host) != 0:
    add_info(u, TEST_URL, "unpingable")
  else:
    #this message is LEGACY_3130
    add_info(u, TEST_URL, "OK - pingable")

def verify_url(u, host, port, command):
  errcode = 400
  try:
    _, output = port_talker.TCPTalk(host, port, 30,
                                    command, None, 1000, 1)
  except:
    add_info(u, TEST_URL, "Timed out")
    return 1
  try:
    errcode = int(string.split(output, None, 2)[1])
  except:
    add_info(u, TEST_URL, "Invalid response from the server")
    return 1

  if errcode == 200:
    add_info(u, TEST_URL, "OK")
    return 0
  else:
    add_info(u, TEST_URL, "returncode %d, should be 200" % errcode)
  return 1

# deprecated !
# given a name, look it up on all passed UrlServers
# return 0 if OK, 1 otherwise
def Check_ExternalWebName(name, dns_servers):
  dns_problems = 0
  for dns_server in dns_servers:
    stat,err = nslookup(name, dns_server)
    if stat != 0:
      add_info(name, EXTERNAL_WEB_NAME,
               "cannot resolve on DNS server %s" % dns_server)
      dns_problems = dns_problems + 1
  # if all dns servers failed, we're done
  if dns_problems != 0:
    return 1
  add_info(name, EXTERNAL_WEB_NAME, "OK")
  return 0


def Check_DNS(server):
  """Check status of DNS server.

  Args:
    server: the IP address of the DNS server to check

  Returns:
    An integer return value.
    0 - OK
    1 - can't ping
    2 - TCP connection refused
    3 - TCP connect timed out
    4 - can't nslookup localhost
    Note: it's OK for a DNS server to have return status 0 1 2 3
    However, in most cases, these errors indicate serious problems with
    the network setup, so we include the diagnotic errors anyway.
  """
  global STATUS
  ret = 0
  if server == None:
    add_info(server, DNS_SERVER, "No DNS server specified")
    STATUS = 1
    return 1
  # find out what platform we're running on
  platform = entconfig.GetPlatform()
  logging.info("pinging DNS_server %s on plaform %s" % (server, platform))
  # first try to ping the DNS server
  if ping_machine(server) != 0:
    add_info(server, DNS_SERVER, "unpingable")
    ret = 1
  # OK, that worked. Now see if we can connect to the DNS port
  # (TCP only for now)
  # Note: this mysteriously fails when using a VmWare DHCP server with
  # the NAT configuration, even though the DNS server is good
  # otherwise. To avoid confusing the user, we suppress this check.
  if platform != 'vmw':
    logging.info("connecting to DNS_server %s" % server)
    res = tryconnect(server, DNS_PORT)
    if res[0] == 1:
      add_info (server, DNS_SERVER, "TCP connection refused - %s" % res[1] )
      ret = 2
    elif res[0] == 2:
      add_info(server, DNS_SERVER, "TCP connection timed out - ACL'ed out?")
      ret = 3
  # Even if this did not work: try to issue a real request
  logging.info("testing lookup on DNS_server %s" % server)
  status, err =  nslookup("localhost.localdomain", server)
  if status == 1:
    # Error only if the request times out, not if the host can't be found
    add_info(server, DNS_SERVER, err)
    STATUS = 1
    ret = 4
  else:
    add_info(server, DNS_SERVER, "OK")
  return ret

# ping a gateway
# return 0 if OK,
#        1 if can't ping
def Check_Gateway(gateway):
  """Check whether gateway is pingable"""

  global STATUS
  logging.info("Pinging gateway")
  if ping_machine(gateway) != 0:
    add_info(gateway, GATEWAY, "unpingable")
    STATUS = 1 # can't work w/out gateway
    return 1
  else:
    add_info(gateway, GATEWAY, "OK")
    return 0


###############################################################################
###############################################################################
# Check the network config
#
# returns: 0 - OK
#          1 - error occured
#
# Note: this seems not to be used any more.
def check_network(config_name, urls = ''):
  """Check all of the network"""

  logging.info("calling obsolete network diagnotic. Use '-interactive' instead")

  config = config_namespace.ConfigNameSpace({})
  config.ExecFile(config_name)
  # get relevant parameters from config file:
  dns_servers = string.split(config.namespace['BOT_DNS_SERVERS'], ',')

  if Check_Gateway(config.namespace['EXTERNAL_DEFAULT_ROUTE']) != 0:
    return 1

  good_dns_servers = 0
  for s in dns_servers:
    if Check_DNS(s) != 4: # all other errors are non-fatal
      good_dns_servers = good_dns_servers + 1
  # if no DNS servers are up, we give up:
  if good_dns_servers == 0:
    return 1

  # First check the SMTP server
  logging.info("testing  SMTP server %s" % config.namespace['SMTP_SERVER'] )
  Check_SMTP(config.namespace['SMTP_SERVER'],
             config.namespace['EXTERNAL_CRAWL_IP'])

  # what about NTP:
  logging.info("testing NTP server %s" % config.namespace['NTP_SERVERS'])
  for s in config.namespace['NTP_SERVERS']:
    Check_NTP(s)

  # SYSLOG server:
  logging.info("testing SYSLOG server %s" % config.namespace['SYSLOG_SERVER'] )
  Check_SYSLOG(config.namespace['SYSLOG_SERVER'])

  # OK, now walk over all collections and try to get starturls
  for u in urls:
    check_url(u, dns_servers)

  return 0




###############################################################################
###############################################################################
# interactive loop

def interactiveLoop():
  """run a loop that reads request from stdin and prints out the responses
  to stdout"""
  global STATUS
  num_lines = int(sys.stdin.readline())
  for _ in range(num_lines):
    tuple = map(string.strip, string.split(sys.stdin.readline(), " "))
    if len(tuple) == 0: # wrong input (empty line) or EOF
      STATUS = 2
      break
    if tuple[0] == SMTP_SERVER:
      if len(tuple) != 3:
        STATUS = 2
        break
      Check_SMTP(tuple[1], tuple[2])
    elif tuple[0] == NTP_SERVER:
      if len(tuple) != 2:
        STATUS = 2
        break
      Check_NTP(tuple[1])
    elif tuple[0] == DNS_SERVER:
      if len(tuple) != 2:
        STATUS = 2
        break
      Check_DNS(tuple[1])
    elif tuple[0] == EXTERNAL_WEB_NAME: # deprecated
      # lookup name onna bunch of DNSServers (at least one)
      if len(tuple) < 3:
        STATUS = 2
        break
      Check_ExternalWebName(tuple[1], tuple[2:])
    elif tuple[0] == GATEWAY:
      if len(tuple) != 2:
        STATUS = 2
        break
      Check_Gateway(tuple[1])
    elif tuple[0] == SYSLOG_SERVER:
      if len(tuple) != 2:
        STATUS = 2
        break
      Check_SYSLOG(tuple[1])
    elif tuple[0] == TEST_URL:
      if len(tuple) < 2:
        STATUS = 2
        break
      check_url(tuple[1], tuple[2:])
    else:
      STATUS = 2
      break
  print get_info(1)

############################################################################

if __name__ == '__main__':
  if len(sys.argv) < 2:
    sys.exit(__doc__)

  if sys.argv[1] == "-interactive":
    if len(sys.argv) >= 3:
      fsgw_host = sys.argv[2]
    if len(sys.argv) >= 4:
      fsgw_port = sys.argv[3]
    sys.exit(interactiveLoop())

  if len(sys.argv) >= 3 and sys.argv[2] == "-batch":
    check_network(sys.argv[1], sys.argv[3:])
    print get_info()
    sys.exit(0)
  sys.exit(__doc__)

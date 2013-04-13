#!/usr/bin/python2.4
# simple dhcp client
# (c) 2002 and onward, Google, Inc.
# Author Max Ibel, Deepak Jindal

import commands
import random
import select
import socket
import string
import struct

# from RFC2131
#
#   0                   1                   2                   3
#   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |     op (1)    |   htype (1)   |   hlen (1)    |   hops (1)    |
#   +---------------+---------------+---------------+---------------+
#   |                            xid (4)                            |
#   +-------------------------------+-------------------------------+
#   |           secs (2)            |           flags (2)           |
#   +-------------------------------+-------------------------------+
#   |                          ciaddr  (4)                          |
#   +---------------------------------------------------------------+
#   |                          yiaddr  (4)                          |
#   +---------------------------------------------------------------+
#   |                          siaddr  (4)                          |
#   +---------------------------------------------------------------+
#   |                          giaddr  (4)                          |
#   +---------------------------------------------------------------+
#   |                                                               |
#   |                          chaddr  (16)                         |
#   |                                                               |
#   |                                                               |
#   +---------------------------------------------------------------+
#   |                                                               |
#   |                          sname   (64)                         |
#   +---------------------------------------------------------------+
#   |                                                               |
#   |                          file    (128)                        |
#   +---------------------------------------------------------------+
#   |                                                               |
#   |                          options (variable)                   |
#   +---------------------------------------------------------------+


def MakeDHCPPacket(op, htype, hlen, hops,
                   xid,
                   secs, flags,
                   ciaddr,
                   yiaddr,
                   siaddr,
                   giaddr,
                   chaddr,
                   sname,
                   file,
                   options):
  return struct.pack("!4BI2H4I16s64s128s%ds" % len(options),
              op, htype, hlen, hops,
              xid,
              secs, flags,
              ciaddr,
              yiaddr,
              siaddr,
              giaddr,
              chaddr,
              sname,
              file,
              options)



# Parse the options field of a DHCP packet
# DHCP packet is passed as a string
# Return value is a list of (code, value) tuples. Tuples are code-specific.
#
# parsed options include:
#
# 1  - netmask
# 2  - timeoffset from UTC in seconds
# 3  - routers
# 4  - time servers
# 6  - DNS servers
# 7  - SYSOG servers
# 15 - domain name
# 28 - broadcast address
# 42 - NTP servers
# 43 - Vendor specific
# 69 - SMTP servers
# 72 - WWW servers
# 51 - IP Address lease time
# 52 - option overload (reuse sname, file space)
# 54 - Server id
# 56 - error message
# 58 - Renewal time value
# 59 - Rebinding time value
#
# For all options check out RFC 1533
def ParseOptions(packet):
  # is length a multiple repeat or a fixed length
  FIXED = 0
  REPEATS = 1

  # result_type: string or address
  STRING = 0
  ADDRESS = 1
  INTEGER = 2
  SHORT = 3

  option_types = {
    1:  ("NETMASK",           4, FIXED,   ADDRESS),
    2:  ("TIME_OFFSET",       4, FIXED,   INTEGER),
    3:  ("ROUTERS",           4, REPEATS, ADDRESS),
    4:  ("TIME_SERVERS",      4, REPEATS, ADDRESS),
    6:  ("DNS_SERVERS",       4, REPEATS, ADDRESS),
    7:  ("SYSLOG_SERVERS",    4, REPEATS, ADDRESS),
    12: ("HOST_NAME",         1, REPEATS, STRING),
    15: ("DOMAIN_NAME",       1, REPEATS, STRING),
    28: ("BROADCAST_ADDRESS", 4, FIXED,   ADDRESS),
    42: ("NTP_SERVERS",       4, REPEATS, ADDRESS),
    51: ("IP_LEASE_TIME",     4, FIXED,   INTEGER),
    52: ("OPTION_OVERLOAD",   1, FIXED,   INTEGER),
    53: ("MESG_TYPE",         1, FIXED,   SHORT),
    54: ("SERVER_ID",         4, FIXED,   ADDRESS),
    56: ("ERROR_MESSAGE",     1, REPEATS, STRING),
    58: ("RENEWAL_TIME",      4, FIXED,   INTEGER),
    59: ("REBINDING_TIME",    4, FIXED,   INTEGER),
    69: ("SMTP_SERVERS",      4, REPEATS, ADDRESS),
    72: ("WWW_SERVERS",       4, REPEATS, ADDRESS),
    }

  options = {}
  packet = packet[236:]
  index = 0
  while index < len(packet):
    code = ord(packet[index])

    if code == 0: # catch pad bytes
      index = index + 1
      continue
    elif code == 255: # catch END_OF_OPTIONS marker
      break
    elif code == 99:  # magic key
      index = index + 4
      continue

    # get length/data
    length = ord(packet[index + 1])
    data = packet[index + 2 : index + 2 + length]
    index = index + 2 + length
    name, option_len, len_type, data_type = option_types.get(
      code, (None, None, None, None))
    if name:
      # check length is correct:
      if length % option_len or length < 1:
        options[name] = "ERROR_MESSAGE: %s has wrong length: %d" % (name,
                                                                    length)
      elif name == "OPTION_OVERLOAD":
        # special case: need to pull in more data.
        # we append it just at the end of the existing data. Not sure if this
        # is legal (requires that data in options field is properly
        # terminated with pads
        overload = ord(data[0])
        if overload == 1: # use file
          data.append(packet[108:236])
        elif overload == 2: # use sname
          data.append(packet[44:108])
        elif overload == 3: # use both
          data.append(packet[44:236])
        else:
          options["errors"] = "ERROR_MESSAGE - OPTION_OVERLOAD w/ type: %d" % overload
      else: # regular code
        # extract and prepare data
        if data_type == INTEGER:
          # have no repeating ones
          options[name] = struct.unpack("I", data)
        elif data_type == SHORT:
          # have no repeating ones
          options[name] = struct.unpack("B", data)
        elif data_type == STRING:
          # strings are repeating chars
          options[name] = data
        elif data_type == ADDRESS:
          if len_type == FIXED:
            b1,b2,b3,b4 = struct.unpack("4B", data)
            options[name] = "%d.%d.%d.%d" % (b1,b2,b3,b4)
          elif len_type == REPEATS:
            address_list = ''
            delim = ''
            for i in range (length / option_len):
              (b1, b2, b3, b4) = struct.unpack("4B", data[4 * i : 4 * i + 4])
              address_list = address_list + delim + "%d.%d.%d.%d" % (b1,b2,
                                                                     b3,b4)
              delim=','
            options[name] = address_list
    else:
      print "ignoring code %d" % code

  return options

# get our own mac address
#
def get_MAC():
  mac = commands.getoutput(
    "/sbin/ifconfig eth0 | grep HWaddr | awk '{print $5}'")
  mac = map(lambda x: eval("0x" + x), string.split(mac, ':'))
  mac = apply(struct.pack, ['6B'] + mac)
  return mac


def bind(host="", port=0):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  if host or port:
    sock.bind((host, port))
  return sock

def send(sock, client_addr, pkt=""):
  sock.sendto(pkt, client_addr)

def recv(sock, timeout, size):
  F = sock.fileno()
  r,w,e = select.select( [F], [], [F], timeout)
  if not r:
    raise Exception(4, "DHCP timed out")
  else:
    data, addr = sock.recvfrom(size)
  return data, addr


def dhcp_discover():
  s = bind("", 68)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  mac = get_MAC()
  # bootrequest packet on ethernet
  options = "%c%c%c%c" %(99,130,83,99) # It's all magic
  options = options + "%c%c%c" % (53,1,1) # type is DHCPDISCOVER
  options = options + "%c%c" % (61,6) + mac # A uniq client id
  options = options + "%c%c%c%c%c%c%c%c%c%c%c" % (55,9,1,3,6,7,15,28,42,69,72) # The params required
  options = options + "%c" % 255  # this is the end
  bootreq = MakeDHCPPacket(1, 1, 6, 0,
                           random.randint(0x0, 0x7ffffffe),
                           0, 0x8000,
                           0, 0, 0, 0,
                           mac,
                           '', '', options)

  for _ in range(3):
    s.sendto(bootreq, ("255.255.255.255", 67))
    try:
      result  = recv(s, 5, 1000)
      s.close()
      return result
    except:
      print 'timeout'
      pass

  return ('', None)


if __name__ == '__main__':

  (result, (host, _)) = dhcp_discover()
  print ParseOptions(result)

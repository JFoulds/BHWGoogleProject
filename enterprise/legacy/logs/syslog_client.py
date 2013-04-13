#!/usr/bin/python2.4
#
# (c)2000 Google inc
# cpopescu@google.com
#
# A small module to talk to remote syslog servers (per RFC 3164).
#
###############################################################################
import time
import socket
import syslog

###############################################################################

class SyslogClient:
  facilities  = {'LOCAL0' : syslog.LOG_LOCAL0,
                 'LOCAL1' : syslog.LOG_LOCAL1,
                 'LOCAL2' : syslog.LOG_LOCAL2,
                 'LOCAL3' : syslog.LOG_LOCAL3,
                 'LOCAL4' : syslog.LOG_LOCAL4,
                 'LOCAL5' : syslog.LOG_LOCAL5,
                 'LOCAL6' : syslog.LOG_LOCAL6,
                 'LOCAL7' : syslog.LOG_LOCAL7,
                 }
  severities = {'INFO' : syslog.LOG_INFO,}

  def __init__(self, server, hostname):
    self.server = (socket.gethostbyname(server), 514)
    self.hostname = hostname

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("",socket.INADDR_ANY))
    self.sock = sock

  def syslog(self, facility, severity, log_time, name, message):
    time_str = time.strftime("%b %d %H:%M:%S", time.localtime(log_time))
    packet = '<%d>%s %s %s: %s' % (self.facilities[facility]+
                                   self.severities[severity],
                                   time_str,
                                   self.hostname,
                                   name,
                                   message)
    try:
      self.sock.sendto(packet, self.server)
    except:
      pass

  def close(self):
    self.sock.close()
    self.sock = None

###############################################################################

#a = SyslogClient('127.0.0.1', 'host')
#for i in range(1000):
#  a.syslog('LOCAL0','INFO', time.time() ,'name', 'message\n')
#a.close()

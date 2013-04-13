#!/usr/bin/python2.4
#
# Copyright 2004 Google Inc.
# All Rights Reserved.
#

"""Summary description of script

makesshcall.py

The purpose of this script is to establish remote port forwards from the
customer's GSA box to Google's DMZ to provide support.

This script has two main functions: start the support call daemon and
to control the daemon.
This script is used by the Enterprise Admin Console to communicate with
the support daemon.  There is only one option for the daemon: dstart.
There are five communication options for the GUI: start, stop, statusStr,
status and test.

"""

__author__='Ryan Tai <ryantai@google.com>'

import os
import socket
import sys
import time
import getopt
from google3.enterprise.legacy.util import daemonize
import signal

from google3.third_party.python.pexpect import pexpect

_daemon_pipe = '/dev/shm/daemonpipe'
_control_pipe = '/dev/shm/controlpipe'
"""The shared pipes location for IPC between the daemon and the GUI"""

_conditions = ['Are you sure you want to continue connecting (yes/no)?',
               'GoogleSupportCall\$ ',
               'password: ',
               pexpect.EOF,
               pexpect.TIMEOUT,
              ]


def ExitNoDaemon():
  """Print error message and exit"""
  print ('No active connections')
  sys.exit(1)

def Exit():
  """Print exit code and exit"""
  print '0'
  sys.exit(0)


def Terminate():
  """Remove communication pipes and exit"""
  os.remove(_daemon_pipe)
  os.remove(_control_pipe)
  sys.exit(0)


def ReportError(error):
  print error

def SigtermHandler(signum, frame):
  os.remove(_daemon_pipe)
  os.remove(_control_pipe)

def CheckSsh(host, user, port):
  """Test SSH connection to host

  Args:
    host: A string
    user: A string
    port: An integer

  Returns:
    # 0 if success
    # error code otherwise
  """
  ssh_conditions = ['GoogleSupportCall\$ ',
                    'Host key verification failed.',
                    'password: ',
                    pexpect.EOF,
                    pexpect.TIMEOUT,
                   ]

  ssh_options = '-2 -o StrictHostKeyChecking=yes -p %s' % port
  command = 'ssh %s %s@%s' % (ssh_options, user, host)

  ssh_test = pexpect.spawn(command)
  index = ssh_test.expect(ssh_conditions, timeout=30)

  if index == 0:
    # if connected to support call prompt, gracefully disconnect
    ssh_test.sendline('c')
    end = ssh_test.expect(['goodbye', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
    if end == 0:
      ssh_test.close(wait=1)
    else:
      ssh_test.kill(9)
  # handles SSH errors
  elif index == 1:
    ReportError("SSH error: Support Call server host key verification failed.")
  elif index == 2:
    ReportError("SSH error: Public key authentication with Support \
                Call server failed.")
  elif index == 3:
    ReportError("SSH error: Unexpected EOF from SSH. Public key \
                authentication with Support Call server may have failed.")
  else:
    ReportError("SSH error: timeout while attempting to execute SSH command.")

  return index


def CheckConnection(host, port):
  """Test network route to host

  Args:
    host: A string
    port: An integer

  Returns:
    # 0 if successful
    # error code otherwise
  """
  result = 0
  # resolve host
  try:
    socket.gethostbyname(host)
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # connect to host
      s.connect((host, port))
      s.close()
    except socket.error, se:
      ReportError("Error establishing TCP connection to %s:%s: %s." %
                  (host, port, str(se)))
      result = se[0]
  except socket.gaierror, ge:
    ReportError("Error resolving hostname %s: %s." % (host, str(ge)))
    result = ge[0]
  return result


def PreRunChecks(host, user, port):
  """Prerun checks done prior to requesting ports
  or/and establishing ports forwarding.

  Args:
    host: A string
    user: A string
    port: an integer

  Returns:
    # 0 if prerun checks pass
    # error code otherwise
  """

  status = CheckConnection(host, port)
  if status != 0:
    return status
  else:
    ssh_status = CheckSsh(host, user, port)
    if ssh_status != 0:
      return ssh_status
    else:
      return 0


def RequestPorts(user, address, conditions, num_ports):
  """Request ports from Google support

  Args:
    user: A String of appliance ID
    address: A String of support address
    conditions: [ pexpect expect objects, ... ]
    num_ports:  An integer of the number of ports to request

  Returns:
    # ports are port numbers from Google support
    (success, [ports, ...])
  """
  success = 0
  forward_list = []
  ssh_options = '-2 -o StrictHostKeyChecking=yes -p 443'
  command = 'ssh %s %s@%s' % (ssh_options, user, address)
  ask_ports = pexpect.spawn(command)
  while success == 0:
    index = ask_ports.expect(conditions, timeout=30)
    if index == 0:
      ask_ports.sendline('yes')
      success = 0
    elif index >= 1:
      success = index
  if success == 1:
    ask_ports.sendline('%d' % num_ports)
    index = ask_ports.expect(['Avaliable ports', pexpect.TIMEOUT], timeout=30)
    if index == 0:
      ask_ports.readline()
      for i in range(0, num_ports):
        forward_list.append(ask_ports.readline()[:-2])
    else:
      # cannot get ports
      success = 4
    ask_ports.close()
  return (success, forward_list)


def EstablishForwards(user, address, src_ports, dest_ports,
    conditions, msg_out, success, gix):
  """Establish port forwards
  """
  start_time = 0
  ssh_options = '-2 -o StrictHostKeyChecking=yes -p 443'
  command = 'ssh %s' % ssh_options
  msg = 'DGIX %s Ports' % gix
  for i in range(0, len(dest_ports)):
    command = ('%s -R%s:localhost:%d' % (command, dest_ports[i], src_ports[i]))
    msg = ('%s %d,%s' % (msg, src_ports[i], dest_ports[i]))
    os.write(msg_out, 'Port %d forwarded to port %s\n' %
             (src_ports[i], dest_ports[i]))
  command = ('%s%s' % (command, (' %s@%s' % (user, address))))
  connections = pexpect.spawn(command)
  success = 0
  while success == 0:
    index = connections.expect(conditions, timeout=30)
    if index == 0:
      connections.sendline('yes')
      success = 0
    else:
      success = index
    if success >= 2:
      os.write(msg_out, 'Port forward failed\n')
      break  # break out of for loop
  if success == 1:
    connected = 1
    connections.sendline(msg)
    os.write(msg_out, 'All connections started successfully\n')
    os.write(msg_out, 'complete\n')
    start_time = time.time()
  else:
    connected = 0
    # clean up opened connections
    connections.close()
    os.write(msg_out, 'Start failed %d: ' % success)
    if success == 4:
      os.write(msg_out, 'connection timeout\n')
    else:
      os.write(msg_out, 'server error\n')
    os.write(msg_out, 'Closed all connections\n')
    os.write(msg_out, 'complete\n')
    Terminate()
  return (connected, connections, start_time)


def HandleStop(connected, connections, msg_out):
  """Stop active connections

  Args:
    connected: An integer to indicate active connections
    connections: [ pexpect, pexpect, ... ]
    msg_out : File discriptor

  Returns:
    no returns
  """
  if connected:
    connections.sendline('c')
    index = connections.expect(['goodbye', pexpect.EOF,
                                  pexpect.TIMEOUT], timeout=30)
    if index == 0:
      connections.close(wait=1)
    else:
      os.write(msg_out, 'Connections interrupted or timed out!\n')
      connections.kill(9)

    connected = 0
    os.write(msg_out, 'Stop successful\n')
    os.write(msg_out, 'Call terminated\n')
    os.write(msg_out, 'complete\n')
  else:
    os.write(msg_out, 'complete\n')
  Terminate()


def DisplayTime(time):
  """Convert time in seconds to string format"""
  time = int(time)
  hours = time/3600
  time = time%3600
  minutes = time/60
  seconds = time%60
  output = '%d hours %d minutes %d seconds' % (hours, minutes, seconds)
  return output


def HandleStatusStr(connected, connections, msg_out, start_time):
  """Get current status in String form

  Args:
    connected: An integer to indicate active connections
    connections: [ pexpect, pexpect, ... ]
    src_ports: [ port numbers, ... ]
    dest_ports: [ port numbers, ... ]
    msg_out : File discriptor
    start_time: time in seconds

  Returns:
    no returns
  """
  if connected:
    # check status for all connections
    connected = 0
    if not connections.isalive():
      output = 'Connection Failed\n'
    else:
      output = 'All connections: OK\n'
      connected = 1
    os.write(msg_out, output)
    # output connection duration
    cur_time = time.time()
    duration = cur_time - start_time
    os.write(msg_out, 'Connection opened for %s\n' % DisplayTime(duration))
  else:
    os.write(msg_out, 'Support call is off\n')
  os.write(msg_out, 'complete\n')


def StartDaemon():
  """Support call daemon main program
  Communicates through predetermined pipes, no args or returns.
  Exit when 'stop' is issued.
  """
  # set a signal handler for SIGTERM
  signal.signal(signal.SIGTERM, SigtermHandler)

  try:
    daemonize.Daemonize()
  except:
    sys.exit(1)

  # cleanup old pipes
  if os.path.exists(_daemon_pipe):
    os.unlink(_daemon_pipe)
  if os.path.exists(_control_pipe):
    os.unlink(_control_pipe)

  os.mkfifo(_daemon_pipe)
  os.mkfifo(_control_pipe)

  #open the pipes from both sides to keep them alive
  pipe_in = open(_daemon_pipe, 'r')
  dummyout = os.open(_daemon_pipe, os.O_WRONLY)
  pipe_out = os.open(_control_pipe, os.O_WRONLY)
  dummyin = open(_control_pipe, 'r')

  connection_on = 0
  children = None
  port_list = [22, 8000, 9941]
  forward_list = []
  start_time = 0

  while 1:
    input = pipe_in.readline()[:-1]
    if input == 'start':
      if connection_on:
        os.write(pipe_out, 'cannot start connection is already started\n')
        os.write(pipe_out, 'complete\n')
      else:
        support_address = pipe_in.readline()[:-1]
        user = pipe_in.readline()[:-1]
        gix = pipe_in.readline()[:-1]
        # ask the support box for unused ports
        success, forward_list = RequestPorts(user, support_address, _conditions,
                                             len(port_list))
        # establish port forwards
        connection_on, children, start_time = EstablishForwards(user,
                                                            support_address,
                                                            port_list,
                                                            forward_list,
                                                            _conditions,
                                                            pipe_out,
                                                            success,
                                                            gix)

    elif input == 'stop':
      HandleStop(connection_on, children, pipe_out)

    elif input == 'statusStr':
      HandleStatusStr(connection_on, children, pipe_out, start_time)

    elif input == 'status':
      if connection_on:
        os.write(pipe_out, '1\n')
      else:
        os.write(pipe_out, '0\n')


def Usage():
  print 'Usage: makesshcall.py'
  print '--command=(start|stop|status|statusStr|test|dstart)'
  print '--id=gixID'
  print '-a address'
  sys.exit(1)


if __name__ == '__main__':
  if not len(sys.argv) >= 2:
    Usage()

  try:
    opts, args = getopt.getopt(sys.argv[1:], 'a:', ['command=', 'id='])
  except getopt.GetoptError:
    Usage()

  address = 'supportcall.google.com'
  command = ''
  gix = ''
  for o, a in opts:
    if o == '-a':
      address = a
    elif o == '--command':
      command = a
    elif o == '--id':
      gix = a

  controls = ['start', 'stop', 'statusStr']
  if command in controls:
    if not os.path.exists(_daemon_pipe): ExitNoDaemon()
    if not os.path.exists(_control_pipe): ExitNoDaemon()
    pipe_out = os.open(_daemon_pipe, os.O_WRONLY)
    pipe_in = open(_control_pipe, 'r')

    if command == 'start':
      if PreRunChecks(address, 'support', 443) == 0:
        os.write(pipe_out, 'start\n')
        os.write(pipe_out, '%s\n' % address)
        os.write(pipe_out, 'support\n')
        os.write(pipe_out, '%s\n' % gix)
      else:
        os.write(pipe_out, 'stop\n')

    elif command == 'stop':
      os.write(pipe_out, 'stop\n')

    elif command == 'statusStr':
      os.write(pipe_out, 'statusStr\n')

    # wait for reply
    input = pipe_in.readline()[:-1]
    output = ''
    while input != 'complete':
      output = output + '\n' + input
      input = pipe_in.readline()[:-1]
    print output

  elif command == 'status':
    if not os.path.exists(_daemon_pipe): Exit()
    if not os.path.exists(_control_pipe): Exit()
    pipe_out = os.open(_daemon_pipe, os.O_WRONLY)
    pipe_in = open(_control_pipe, 'r')

    os.write(pipe_out, 'status\n')
    input = pipe_in.readline()[:-1]
    print input

  elif command == 'test':
    if PreRunChecks(address, 'support', 443) == 0:
      success, ports = RequestPorts('support', address, _conditions, 1)
      if success == 1:
        print 'Test successful\nSupport call ready\n'
      else:
        print 'Test failed %d\n' % success

  elif command == 'ready':
    if not os.path.exists(_daemon_pipe): Exit()
    if not os.path.exists(_control_pipe): Exit()
    print '1'

  elif command == 'dstart':
    StartDaemon()

  else:
    Usage()

  sys.exit(0)

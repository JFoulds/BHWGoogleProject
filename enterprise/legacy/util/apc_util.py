#!/usr/bin/python2.4
#
# Copyright 2004 Google Inc.
# All Rights Reserved.

"""
A utility to map ent# to acp ports

This module is built to solve the problem of more than one APC for a cluster.
This module is made general enough to go to n-way clusters to more than 2 APCs.
The requirement for wiring the cluster is following: (given 4 ports per APC)
  ent1 to APC1 port 1
  ent2 to APC1 port 2
  ...
  ent4 to APC1 port 4
  ent5 to APC2 port 1
  ent6 to APC2 port 2
  ...
"""

__author__ = "Ryan Tai <ryantai@google.com>"

# The number of ports used on an APC PDU
# (there are more ports, but using them will exceed the current capacity)
APC_PORTS = 4

# The starting APC PDU IP address
APC_BASE_ADDRESS = (216, 239, 43, 144)

def PortMap(ent_num, base_ip=APC_BASE_ADDRESS):
  """ Finds the APC address and port number given the ent number on the cluster

  Args:
    ent_num: a positive integer
    base_ip: a tuple of 4 integers (216, 239, 43, 144)

  Returns:
    # a string containing the APC ip address and port number
    216.239.43.144-1
  """
  try:
    ent_num = int(ent_num)
    if ent_num <= 0:
      return None

    ip = list(base_ip[0:3])
    ip.append(base_ip[3] + ((ent_num - 1) / APC_PORTS))
    port = ((ent_num - 1) % APC_PORTS) + 1
    ip_str = [str(byte) for byte in ip]
    str_ip = '.'.join(ip_str)
    result = '%s-%d' % (str_ip, port)
    return result
  except:
    return None

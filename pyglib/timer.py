#!/usr/bin/python2.4
#
# Original Author: Vijay Pandurangan
#
# Copyright (c) 2003+, Google
#

"""
This class provides the functionality of a timer.  Usage:

from google3.pyglib import timer
a_timer = timer.Timer()
a_timer.Start()

... do stuff
a_timer.Stop()
if a_timer.GetDuration() > 100:
  print 'This took too long'
"""

import time

class Timer:
  def __init__(self):
    """Initializes a timer"""
    self.duration = -1
    self.running = 0

  def Start(self):
    """ Resets and starts a timer"""
    self.start = time.time()
    self.running = 1

  def Stop(self):
    """ Stops a timer, and records the duration. Stop is idempotent.
    """
    
    if self.running:
      self.duration = time.time() - self.start
      self.running = 0
      
    return self.duration
  
  def IsRunning(self):
    return self.running
  
  def __str__(self):
    return str(self.GetDuration())
  

  def GetDuration(self):
    """If timer is still running, then it returns the time(in sec.) elapsed
    since the start, else returns the time(in sec.) for which the timer ran.
    """
    if self.running:
      return time.time() - self.start
    else:
      return self.duration

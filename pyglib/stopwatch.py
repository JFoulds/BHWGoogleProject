# Copyright 2005, Google Inc.

"""
A useful class for digesting, on a high-level, where time in a program goes.

Usage:

sw = StopWatch()
sw.start()
sw.start('foo')
foo()
sw.stop('foo')
args = overhead_code()
sw.start('bar')
bar(args)
sw.stop('bar')
sw.dump()

If you start a new timer when one is already running, then the other one will
  stop running, and restart when you stop this timer.  This behavior is very
  useful for when you want to try timing for a subcall without remembering
  what is already running.  For instance:

sw.start('all_this')
do_some_stuff()
sw.start('just_that')
small_but_expensive_function()
sw.stop('just_that')
cleanup_code()
sw.stop('all_this')

In this case, the output will be what you want:  the time spent in
  small_but_expensive function will show up in the timer for just_that and not
  all_this.
"""

import StringIO
import time

__author__ = 'mfoltz@google.com (mark a. foltz)'
__owner__  = 'dbentley@google.com (Dan Bentley)'
__owner__ = __owner__   # silence pychecker

class StopWatch(object):
  def __init__(self):
    """
    Timers:  Currently running stopwatches.  Maps stopwatch name -> time
      (in seconds from the epoch) this stopwatch was started

    Accum:  Accumulated time.  Maps stopwatch name -> time, in seconds,
      it has already been run for.

    Stopped:  Timers that are blocked on another timer.  Maps timer name ->
      list of timer names.

    Counters: Number of times each stopwatch has been started.
    """
    self.timers = {}
    self.accum = {}
    self.stopped = {}
    self.counters = {}

  def start(self, timer='total', stop_others = 1):
    """
    Start a timer.  By default, we start the overall timer.  If stop_others
      is set, we stop all other running timers.  If it isn't, then you
      can have time that is spent inside more than one timer and there's
      a good chance that the overhead measured will be negative.
    """
    if stop_others:
      stopped = []
      for other in self.timers.keys():
        if not other == 'total':
          self.stop(other)
          stopped.append(other)
      self.stopped[timer] = stopped
    self.counters[timer] = self.counters.get(timer,0) + 1
    self.timers[timer] = time.time()

  def stop(self, timer='total'):
    """
    Stop a running timer.  This includes restarting anything that was stopped
      on behalf of this timer.
    """
    if timer not in self.timers:
      raise RuntimeError('Tried to stop timer that was never started: %s'
        % timer)
    now = time.time()
    self.accum[timer] = self.accum.get(timer, 0.0) + (now - self.timers[timer])
    del self.timers[timer]
    for stopped in self.stopped.get(timer, []):
      self.start(stopped, stop_others = 0)

  def overhead(self):
    """
    Calculate the overhead.  That is, time spent in total but not in any
      sub timer.  This may be negative if time was counted in two
      sub timers.  Avoid this by always using stop_others.
    """
    all = reduce(lambda x, y: x+y, self.accum.values(), 0.0)
    return self.accum['total'] - (all - self.accum['total'])

  def results(self, verbose = 0):
    """
    Return a list of tuples showing the output of this stopwatch.

    Tuples are of the form (name, value, num_starts) for each timer.

    If verbose, all times.  Otherwise, only the total.
    """
    self.accum['overhead'] = self.overhead()
    self.counters['overhead'] = 1
    all_names = self.accum.keys()
    names = []

    all_names.remove('total')
    all_names.sort()
    if verbose:
      names = all_names
    names.append('total')
    results = [ (name, self.accum[name], self.counters[name]) for name in names ]
    return results

  def dump(self, verbose = 0):
    """
    Return a string that describes where time in this stopwatch was spent.

    Setting verbose shows all timers.  Verbose = 0 will only show the total.
    """
    output = StringIO.StringIO()
    results = self.results(verbose = verbose)
    maxlength = max([len(result[0]) for result in results])
    for result in results:
        output.write( '%*s: %6.2fs\n' % (maxlength, result[0], result[1]))
    return output.getvalue()

# Create a stopwatch to be publicly used.
sw = StopWatch()

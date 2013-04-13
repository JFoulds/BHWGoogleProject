#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.
#

""" Machine Parameter Cache.

Usage:
  mach_param_cache = machine_param_cache.MachineParamCache()
  value = mach_param_cache.GetFact(fact_name, machine_name)

If GetFact() is called on a fact that HasExpired() then this (and every other
interesting fact on that machine) is updated from SVS (using
get_svs_param.InitMdb([machine]) ).

Some facts never change, they should have a long expiration time, such as
cpucnt. While other facts should have a very short expiration time, such as
var_log_badhds. For unknown facts, the following adaptive expiration time is
used: When a fact is updated, if the value changes then the fact's expiration
time is halved (to a min of 5 secs), otherwise the fact's expiration time
increases by 60 seconds (to a max of 5 minutes).
"""

__author__ = 'wanli@google.com (Wanli Yang)'

import sys
import time
import os

from google3.enterprise.legacy.util import get_svs_param

MIN_CACHE_EXPIRE_SEC = 5
MAX_CACHE_EXPIRE_SEC = 300
CACHE_EXPIRE_SEC_INCREASE = 60
# pre-defind interesting facts and their expiration time
INTERESTING_FACTS_AND_EXPIRATION_TIME = {
  # fact_name: expiration_time_in_sec
  # Disks
  'disk_used_df_percent': 300,
  'hda1-problem': 5, 'hda1-size': 3600 * 24, 'hda1_full': 300,
  'hda3-problem': 5, 'hda3-size': 3600 * 24, 'hda3_full': 300,
  'hdb3-problem': 5, 'hdb3-size': 3600 * 24, 'hdb3_full': 300,
  'hdc3-problem': 5, 'hdc3-size': 3600 * 24, 'hdc3_full': 300,
  'hdd3-problem': 5, 'hdd3-size': 3600 * 24, 'hdd3_full': 300,
  'var_log_badhds': 5,
  # Memory
  'memory-total': 3600 * 24, 'memory-free': 5, 'memory-used': 5,
  # CPU
  'cpu-mhz': 3600 * 24, 'cpucnt': 3600 * 24,
  # Swap
  'swap-total': 3600, 'swap-free': 5,
  # Uptime
  'uptime-in-ms': 5,
  # Load
  'load3': 5,
  # Drives
  'mounted_drives': 300,
  'drive0': 5,
  'drive1': 5,
  'drive2': 5,
  'drive3': 5,
  'drive4': 5,
  'drive5': 5,
  # Arrays
  'array0': 5,
  'array2': 5,
  'array3': 5,
  'array4': 5,
  # SSH
  'ssh-status': 5,
  }


class ParamCacheEntry:
  """ a cache entry for a parameter of a machine
  """

  def __init__(self, factname, machine):
    """ Init Cache Entry for a (fact, machine) pair

    Arguments:
      factname: 'cpucnt'
      machine: 'ent1'
    """

    self.__factname = factname
    self.__machine = machine
    self.__update_time = 0
    self.__cached_value = None
    self.__expiration_time = 0
    self.__use_fixed_expiration_time = 0

  def UpdateVal(self, newval):
    """ update the value of a cache entry. If the entry does not have
    fixed expiration time, the expiration is also adjusted. If the cached
    value does not change, increase the expiration_time for this cache entry.
    Otherwise, shorten the expiration_time for this cache entry.

    Arguments:
      newval: 0 (can be a string or number or None)
    """

    # there is a different old value
    if self.__update_time != 0 and self.__cached_value != newval:
      self.__cached_value = newval
      if not self.__use_fixed_expiration_time:
        self.__expiration_time = max(self.__expiration_time >> 1,
                                     MIN_CACHE_EXPIRE_SEC)
    else:
      if self.__update_time is 0:
         self.__cached_value = newval
      if not self.__use_fixed_expiration_time:
        self.__expiration_time = max(
          self.__expiration_time + CACHE_EXPIRE_SEC_INCREASE,
          MAX_CACHE_EXPIRE_SEC)
    self.__update_time = time.time()

  def SetFixedExpirationTime(self, expiration_time_sec):
    """ set this entry to have fixed experiation time. Some facts never change,
    they should have a long expiration time, such as cpucnt. While other
    facts should have a very short expiration time, such as var_log_badhds.
    The adaptive expiration time is for unknown facts.
    """
    self.__expiration_time = expiration_time_sec
    self.__use_fixed_expiration_time = 1

  def HasExpired(self):
    """ if the cache entry has expired

    Returns:
      1 - has expired; 0 - otherwise
    """

    if time.time() - self.__update_time > self.__expiration_time:
      return 1
    else:
      return 0

  def CachedValue(self):
    """ returns the value of the parameter(fact)

    Returns:
      0 (can be a string, a number, or None)
    """

    return self.__cached_value

class MachineParamCache:
  """ This class represents a cache for machine facts. The facts are from SVS
  and every time the cache gets facts from SVS, it evaluates if the interesting
  facts have changed. For facts that don't change very often, next time they are
  queried, the cached value of the facts are returned.
  """

  def __init__(self):
    # facts that have been queried
    self.__interesting_facts = INTERESTING_FACTS_AND_EXPIRATION_TIME.keys()
    self.__cache_entries = {}
    self.ResetStats()

  def __GetCacheEntry(self, factname, machine):
    """ return the cache entry for a (factname, machine) pair. If the entry
        does not exist, create one.

    Arguments:
      factname: 'cpucnt'
      machine:   'ent1'
    Returns:
      A cache entry (type ParamCacheEntry)
    """

    if (factname, machine) not in self.__cache_entries:
      cache_entry = ParamCacheEntry(factname, machine)
      self.__cache_entries[(factname, machine)] = cache_entry
      if factname in INTERESTING_FACTS_AND_EXPIRATION_TIME:
        cache_entry.SetFixedExpirationTime(
          INTERESTING_FACTS_AND_EXPIRATION_TIME[factname])
    return self.__cache_entries[(factname, machine)]

  def __UpdateInterestingFacts(self, machine, mdb):
    """  Update all interesting facts (after getting all the facts from SVS)

    Arguments:
      machine: 'ent1'
      mdb: {'ent1:': {'hdcnt': '4',
                      'hda3-problme':  0,
                      'uptime-in-ms': 717540}}
    """

    # update all intersting facts for this machine
    for interesting_fact in self.__interesting_facts:
      cache_entry = self.__GetCacheEntry(interesting_fact, machine)
      newval = get_svs_param.GetFact(mdb, interesting_fact, machine)
      cache_entry.UpdateVal(newval)

  def GetFact(self, factname, machine, mdb = None):
    """ get the value of a parameter(fact) of a machine. If the value
    is cached and the cache has not expired, use the value from the cache.
    Otherwise, get the value from SVS directly. Update all interesting facts
    as well.

    Arguments:
      facatname: 'cpucnt'
      machine: 'ent1'
      mdb: {'ent1:': {'hdcnt': '4',
                      'hda3-problme':  0,
                      'uptime-in-ms': 717540}}
           for unittest purpose
    Returns:
      0 (can be a string, a number, or None)
    """

    if factname not in self.__interesting_facts:
      self.__interesting_facts.append(factname)
    else:
      cache_entry = self.__GetCacheEntry(factname, machine)
      if not cache_entry.HasExpired():
        self.__hits += 1
        return cache_entry.CachedValue()
      else:
        self.__misses += 1

    # read from SVS
    self.__reads_from_svs += 1
    if mdb is None:
      mdb = get_svs_param.InitMdb([machine])
    self.__UpdateInterestingFacts(machine, mdb)
    return  get_svs_param.GetFact(mdb, factname, machine)

  def InterestingFacts(self):
    """ return the intersting facts tracked by the cache

    Returns:
      ['ssh-status', 'uptime-in-ms', ...]
    """

    return self.__interesting_facts

  def GetStats(self):
    """ return the stats of the cache

    Returns:
      (hits, misses, reads_from_svs)
    """

    return (self.__hits, self.__misses, self.__reads_from_svs)

  def ResetStats(self):
    self.__hits = 0
    self.__misses = 0
    self.__reads_from_svs = 0

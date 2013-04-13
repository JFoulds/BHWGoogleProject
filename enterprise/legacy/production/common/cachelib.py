#!/usr/bin/python2.4
#
# cachelib.py - library for caching.
#
# Copyright 2002 and onwards, Google
# Original Author: Eugene Jhong
#

import UserDict

#
# Cache
#
# Class for caching information.  Subclasses
# should implement this interface and can implement
# their own caching interface.  This may seem a bit
# overkill for many applications (could just use a dictionary)
# but at some point we may want to cache a large amount
# of data and things like an LRUCache might be useful or
# a cache that invalidates stale items automatically.
#
# The cache interface is identical to a dictionary
# interface so cache types should be subclassed off
# of UserDict

class Cache(UserDict.UserDict):
  pass

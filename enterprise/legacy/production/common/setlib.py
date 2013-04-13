#!/usr/bin/python2.4
#
# setlib.py - List set utilities.
#
# Copyright 2002, Google, Inc.
# All Rights Reserved.
#
# Original Author: Eugene Jhong
#
# TODO: Eventually vikram will probably incorporate the bit based
# set operations found in machinedb.  These methods will then
# probably work off of that new Class but the API for these shouldn't
# need to change.

import sys
import string

# Converts a list into a list of unique items.
def make_set(set):
  set = make_dict(set).keys()
  set.sort()
  return set


# Converts a list into a dictionary of elements mapped to 1.
def make_dict(set):
  dict = {}
  for el in set:
    dict[el] = 1
  return dict


# Return the union of two list sets.
def union(set1, set2):
  ret = {}
  for el in set1:
    ret[el] = 1
  for el in set2:
    ret[el] = 1
  ret = ret.keys()
  return ret


# Return the intersection of two list sets.
def intersect(set1, set2):
  set2 = make_dict(set2)
  ret = []
  for el in set1:
    if set2.has_key(el): ret.append(el)
  return ret


# Return the difference of two list sets.
def diff(set1, set2):
  set2 = make_dict(set2)
  ret = []
  for el in set1:
    if not set2.has_key(el): ret.append(el)
  return ret


# Simple main command line routine for performing set ops.
if __name__ == '__main__':

  if len(sys.argv) < 4:
    print 'Usage: %s <union|inter|diff> "set1" "set2"' % (sys.argv[0])
    sys.exit(1)

  op = sys.argv[1]
  set1 = string.split(sys.argv[2])
  set2 = string.split(sys.argv[3])

  if op == "union":
    set = union(set1, set2)
    set.sort()
    print string.join(set)
  elif op == "inter":
    set = intersect(set1, set2)
    set.sort()
    print string.join(set)
  elif op == "diff":
    set = diff(set1, set2)
    set.sort()
    print string.join(set)

#!/usr/bin/python2.4
#
# $Id: //depot/branches/gsa_0806_release_branch/google3/pyglib/OrderedDictionary.py#1 $
#
# Copyright 2002 Google Inc.
# All Rights Reserved.
#
# Author: Eric Tiedemann
#
# This is derived from code by David Benjamin in the Python Cookbook
# (http://aspn.activestate.com/ASPN/Python/Cookbook/).

from __future__ import generators
import copy


class OrderedDictionary(dict):
  """OrderedDictionary(init={}, order_by_updatep=False)

  A dictionary the remembers the order in which keys are added to it.
  The keys(), values() and items() methods return lists in this order.
  The unordered_cmp(other) method will compare an instance against
  another without requiring an identical order of keys.  The __cmp__
  method is order-sensitive.

  INIT can be a dictionary or a list or tuple of key-value pairs.  If
  a list or tuple is provided, its ordering is preserved.

  If ORDER_BY_UPDATEP is true, then the list of keys will be
  maintained so as to represent the order of updates to the
  dictionary.  The default is to represent the order of initialization
  of entries.

  This class attempts to provide print/read idempotency.  The str() or
  repr() value for an instance should be evaluable in an environment
  with OrderedDictionary defined to recreate the instance.

  OrderedDictionary should be compatible with Python 2.2 onward.

  Methods not in dict:
    pop(key) - removes key and returns its value (dict.pop() only exists in
               Python 2.3+ but OrderedDictionary.pop() can be used in any
               supported version of Python)

    rename_key(old_key, new_key) - renames the old key to the new one, keeping
                                   its value and order in the dictionary

    replace_item(old_key, new_key, value) - shortcut for:
                                            odict.rename_key(old_key, new_key)
                                            odict[new_key] = value
  """

  def __init__(self, init=(), order_by_updatep=False):
    self._order_by_updatep = order_by_updatep

    if isinstance(init, dict):
      self._keys = init.keys()
      super(OrderedDictionary, self).__init__(init)
    elif isinstance(init, (list, tuple)):
      super(OrderedDictionary, self).__init__()
      self._keys = []
      for k, v in init:
        self[k] = v
    else:
      raise TypeError, 'init arg had type %s' % type(init)

  def __repr__(self):
    return ('OrderedDictionary((%s))'
            % ', '.join(['(%r, %r)' % (k, self.get(k)) for k in self._keys]))

  def __str__(self):
    return repr(self)

  def __delitem__(self, key):
    super(OrderedDictionary, self).__delitem__(key)
    try:
      self._keys.remove(key)
    except ValueError:
      raise KeyError, key

  def __setitem__(self, key, item):
    # The copy module attempts to restore a dictionary's items before its state,
    # even if either of __setstate__() or __getstate__() is defined.  That would
    # be okay except it does the restore by doing thedict[key] = value, thereby
    # calling thedict.__setitem__().  IMO that is wrong and broken - it should
    # be doing dict.__setitem__(thedict, key, value) - so we're left with this
    # workaround.
    if not hasattr(self, '_keys'):
      self._keys = []

    # NB: if KEY is unhashable, the membership test will raise an exception.
    # This helps protect the synchronization of our dict and our list.
    if key not in self:
      self._keys.append(key)
    elif self._order_by_updatep:
      self._keys.remove(key)
      self._keys.append(key)
    super(OrderedDictionary, self).__setitem__(key, item)

  def __getstate__(self):
    state = self.__dict__.copy()
    state['_keys'] = state['_keys'][:]
    return state

  def clear(self):
    super(OrderedDictionary, self).clear()
    self._keys = []

  def copy(self):
    return copy.copy(self)

  def items(self):
    return [(k, self.get(k)) for k in self._keys]

  def keys(self):
    return self._keys[:]

  def values(self):
    return [self.get(k) for k in self._keys]

  def setdefault(self, key, failobj=None):
    v = super(OrderedDictionary, self).setdefault(key, failobj)
    if key not in self._keys:
      self._keys.append(key)
    return v

  def update(self, dict_):
    super(OrderedDictionary, self).update(dict_)
    for key in dict_.keys():
      if key not in self._keys:
        self._keys.append(key)

  def popitem(self):
    if self._keys:
      key = self._keys[-1]
      val = self[key]
      # This deletes from the key list too.
      del self[key]
      return (key, val)
    else:
      raise KeyError, 'dictionary is empty'

  def pop(self, key, *default):
    if len(default) > 1:
      raise TypeError, 'too many arguments'
    if default and key not in self:
      return default[0]
    val = self[key]
    del self[key]
    return val

  def __iter__(self):
    for key in self._keys:
      yield key

  def iteritems(self):
    for key in self._keys:
      yield key, self[key]

  def iterkeys(self):
    for key in self._keys:
      yield key

  def itervalues(self):
    for key in self._keys:
      yield self[key]

  def unordered_cmp(self, other):
    return super(OrderedDictionary, self).__cmp__(other)

  def rename_key(self, old_key, new_key):
    if new_key in self:
      del self[new_key]
    # don't use dict.pop() for 2.2 compatibility
    val = self[old_key]
    self._keys[self._keys.index(old_key)] = new_key
    super(OrderedDictionary, self).__setitem__(new_key, val)

  def replace_item(self, old_key, new_key, val):
    if new_key in self:
      del self[new_key]
    self._keys[self._keys.index(old_key)] = new_key
    super(OrderedDictionary, self).__setitem__(new_key, val)

  def __eq__(self, other):
    # Implements ordered comparison.
    skeys = self._keys
    okeys = other._keys
    if len(skeys) != len(okeys):
      return False
    for i in xrange(len(skeys)):
      if skeys[i] != okeys[i] or self.get(skeys[i]) != other.get(okeys[i]):
        return False
    return True

  def __ne__(self, other):
    return not (self == other)  # no != because that's what this is for

  # OK, we're not supporting the full rich-comparison interface yet.
  # I'm not sure if I even believe in the one currently used for dicts.
  def __gt__(self, other):
    raise AttributeError, '__gt__'

  def __ge__(self, other):
    raise AttributeError, '__ge__'

  def __lt__(self, other):
    raise AttributeError, '__lt__'

  def __le__(self, other):
    raise AttributeError, '__le__'

  def __cmp__(self, other):
    raise AttributeError, '__cmp__'

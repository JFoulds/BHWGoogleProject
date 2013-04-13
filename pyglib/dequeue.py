# Copyright 2005 Google Inc.
# All Rights Reserved
# Original Authors: fenix@google.com (Roberto J Peon)
#                   aleax@google.com (Alex Martelli)

"""
Contains a class implementing a dequeue.
"""

################################################################################
################################################################################


class Dequeue:
  """
  The Dequeue class implements a simple dequeue as two stacks.
    This gives amortized O(1) time for pushing on one end and popping from the
    other (instead of O(n) with the native list).

  The interface to this class is substantially similar to that of the
    collections.deque class in python 2.4.
    This class differs from collections.deque in the following ways:
      1) advantage:  Has pop_k and popleft_k
      2) deficiency: Not threadsafe
      3) deficiency: Implemented in python
      4) deficiency: Doesn't do slices.. I'm not sure if the collections.deque
                     does either, however..

  See individual functions for Big-O times.

  Implementation notes: the two stacks (_frontlist and _backlist) are
  ordinary Python lists.  Elements in _frontlist are stored in reverse
  order of their logical position in the dequeue.  For example, a dequeue
  of [ 0, 1, 2, 3, 4, 5 ] could be represented as:
    _frontlist: [ 2, 1, 0 ]
    _backlist: [ 3, 4, 5 ],
  or even:
    _frontlist: [ 5, 4, 3, 2, 1, 0 ]
    _backlist: [ ]

  Bugs:
    Throws exceptions if you attempt to use slices.
        .. This may not, however, be a bug, because using slices with this
        container would likely cause the naive user to implement O(n^2)
        algorithms, which is counter to the purpose of using this container
        in the first place.
    Using popleft*() and then pop*() (or vice-versa) in sequence is likely to
        cause O(n*k) running time instead of O(k). Don't do it unless you know
        what you're doing.
  """
  def __init__(self, initial_data=None):
    self._frontlist = []
    self._backlist = []
    if initial_data:
      self.extend(initial_data)

  ########################################

  def appendleft(self, element):
    """
    Summary:
      Appends an element to the front of the dequeue.
      O(1), running time is same as list.append()
    Args:
       element - a single object
    Returns:
       Nada.

    """
    self._frontlist.append(element)

  ########################################

  def extendleft(self, items):
    """
    Summary:
      Extends elements to the front of the dequeue.
      O(k), where k is len(items). Running time is same as
        list.extend() + list.reverse()
    Args:
       items - a list or tuple of objects
    Returns:
       Nada.

    """
    items_copy = list(items)
    items_copy.reverse()
    self._frontlist.extend(items_copy)

  ########################################

  def append(self, element):
    """
    Summary:
      Appends an element to the back of the dequeue.
      O(1), running time is same as list.append()
    Args:
       element - a single object
    Returns:
       Nada.

    """
    self._backlist.append(element)

  ########################################

  def extend(self, items):
    """
    Summary:
      Extends elements to the back of the dequeue.
      O(k), where k is len(items). Running time is same as list.extend()
    Args:
       items - a list or tuple of objects
    Returns:
       Nada.

    """
    self._backlist.extend(items)

  ########################################

  def index(self, element):
    """
    Summary:
      Return the index of the first occurrence of element.
    Args:
      element - a single object
    Returns:
      index of first (i.e. left-most) occurrence of element in the dequeue
    Raises:
      ValueError if element is not in the dequeue
    """
    # Note: search frontlist from last element back, so that we find
    # the (logical) first occurrence:
    for i in xrange(len(self._frontlist) - 1, -1, -1):
      if self._frontlist[i] == element:
        return len(self._frontlist) - i - 1

    try:
      index = self._backlist.index(element)
    except ValueError:
      # Paraphrased from list.index error text:
      raise ValueError('Dequeue.index(x): x not in dequeue')

    return len(self._frontlist) + index

  ########################################

  def popleft_k(self, k):
    """
    Summary:
      Pops up to k elements from the front and returns them in a list
      Amortized O(k), where k is the parameter k
         .. Every n operations it will have to pause to reverse a list
    Args:
      k - integer >= 0 representing number of elements to pop from the front.
    Returns:
      list of up-to-k elements
    Warning:
      Popping from the front and then the back (i.e. pop*() and popleft*())
      or vice-versa will likely result in each call taking O(n) time. It is
      suggested that you only do this if you know what you're doing.
    """
    if k <= 0:
      return []
    amount_lacking = k - len(self._frontlist)
    if amount_lacking > 0:
      # not enough items in frontlist to satisfy request, use all of them
      # and then fill the rest with as many as needed from the backlist
      retval = self._frontlist
      retval.reverse()
      retval.extend(self._backlist[:amount_lacking])
      self._frontlist = self._backlist
      self._frontlist.reverse()
      del self._frontlist[-amount_lacking:]

      self._backlist = []
      return retval

    retval = self._frontlist[-k:]
    retval.reverse()
    del self._frontlist[-k:]
    return retval

  ########################################

  def pop_k(self, k):
    """
    Summary:
      Pops up to k elements from the back and returns them in a list
      Amortized O(k), where k is the parameter k
         .. Every n operations it will have to pause to reverse a list
    Args:
      k - integer >= 0 representing number of elements to pop from the back.
    Returns:
      list of up-to-k elements
    Warning:
      Popping from the front and then the back (i.e. pop*() and popleft*())
      or vice-versa will likely result in each call taking O(n) time. It is
      suggested that you only do this if you know what you're doing.
    """
    if k <= 0:
      return []
    amount_lacking = k - len(self._backlist)
    if amount_lacking > 0:
      # not enough items in backlist to satisfy request, use all of them
      # and then fill the rest with as many as needed from the frontlist
      self._frontlist.reverse()
      retval = self._frontlist[-amount_lacking:]
      retval.extend(self._backlist)
      del self._frontlist[-amount_lacking:]
      self._backlist = self._frontlist

      self._frontlist = []
      return retval

    retval = self._backlist[-k:]
    del self._backlist[-k:]
    return retval

  ########################################

  def pop(self):
    """
    Summary:
      Pops 1 element from the back.
      Throws an 'IndexError' exception if no elements left to pop.
    Returns:
      the back element of the dequeue
    Warning:
      Popping from the front and then the back (i.e. pop*() and popleft*())
      or vice-versa will likely result in each call taking O(n) time. It is
      suggested that you only do this if you know what you're doing.
    """
    if not len(self):
      raise IndexError, "IndexError: pop from an empty deque"
    return self.pop_k(1)[0]

  ########################################

  def popleft(self):
    """
    Summary:
      Pops 1 element from the front.
      Throws an 'IndexError' exception if no elements left to pop.
    Returns:
      the back element of the dequeue
    Warning:
      Popping from the front and then the back (i.e. pop*() and popleft*())
      or vice-versa will likely result in each call taking O(n) time. It is
      suggested that you only do this if you know what you're doing.
    """
    if not len(self):
      raise IndexError, "IndexError: popleft from an empty deque"
    return self.popleft_k(1)[0]

  ########################################

  def rotate(self, k):
    """
    Summary:
      If k is positive, rotates the dequeue k steps to the right.
      If k is negative, rotates the dequeue k steps to the left.
      Rotating one step to the right is equivalent to:
        dequeue.appendleft(d.pop()),
      Similarly, rotating one step to the left is equivalent to:
        dequeue.append(d.popleft()),

    """
    if k < 0:
      self.extend(self.popleft_k(-k))
    else:
      self.extendleft(self.pop_k(k))

  ########################################

  def clear(self):
    self._frontlist = []
    self._backlist = []

  ########################################

  def __contains__(self, item):
    return item in self._backlist or item in self._frontlist

  ########################################

  def __len__(self):
    return len(self._backlist) + len(self._frontlist)

  ########################################

  def __del_set_get_helper(self, key, op, except_string):
    total_items = self.__len__()

    if not isinstance(key, (int, long)):
      raise TypeError, "an integer is required"

    if key < 0:
      key = total_items + key

    if key >= total_items or key < 0:
      raise IndexError, except_string

    front_len = len(self._frontlist)
    if key < front_len:
      return op(self._frontlist, -(key + 1))
    return op(self._backlist, key - front_len)

  ########################################

  def __delitem__(self, key):
    """
    Warning:
      The running time for this is O(n), not O(1)!
    """
    def delop(list, idx):
      del list[idx]
    self.__del_set_get_helper(key,
        delop,
        'Dequeue assignment index out of range')

  ########################################

  def __getitem__(self, key):
    def getop(list, idx):
      return list[idx]
    return self.__del_set_get_helper(key,
        getop,
        'Dequeue index out of range')


  ########################################

  def __setitem__(self, key, value):
    def setop(list, idx):
      list[idx] = value
    return self.__del_set_get_helper(key,
        setop,
        'Dequeue assignment index out of range')

  ########################################

  def __eq__(self, other):
    selflen = len(self)
    if selflen != len(other):
      return 0
    for i in xrange(selflen):
      if self[i] != other[i]:
        return 0
    return 1

  ########################################

  def __cmp__(self, other):
    selflen = len(self)
    otherlen = len(other)
    minlen = selflen
    if minlen > otherlen:
      minlen = otherlen
    for i in xrange(minlen):
      self_elem = self[i]
      other_elem = other[i]

      if self_elem > other_elem:
        return 1
      elif other_elem > self_elem:
        return -1
      # otherwise, they have to be equal, so continue
      # comparing until we've gotten to the end of the
      # shorter sequence.

    if selflen > otherlen:
      return 1
    if selflen < otherlen:
      return -1
    return 0

  ########################################

  def __ne__(self, other):
    return not (self == other)

  ########################################

  def __gt__(self, other):
    return self.__cmp__(other) > 0

  ########################################

  def __lt__(self, other):
    return self.__cmp__(other) < 0

  ########################################

  def __ge__(self, other):
    return self.__cmp__(other) >= 0

  ########################################

  def __le__(self, other):
    return self.__cmp__(other) <= 0

  ########################################

  def __output_helper(self, stringify_op):
    retval = ['[']
    for i in xrange(len(self._frontlist)-1,-1,-1):
      retval.append(stringify_op(self._frontlist[i]))
      if i >= 0:
        retval.append(', ')
    backlen = len(self._backlist)
    for i in xrange(backlen):
      retval.append(stringify_op(self._backlist[i]))
      if i + 1 < backlen:
        retval.append(', ')
    retval.append(']')
    return ''.join(retval)

  ########################################

  def __str__(self):
    return self.__output_helper(str)

  ########################################

  def __repr__(self):
    return self.__output_helper(repr)

  ########################################


################################################################################
################################################################################

# Copyright 2004 Google, Inc.
# All Rights Reserved.
#
# Author: Aman Bhargava

class Lazy:
  """
  This class allows you to delay the computation of a value until it is needed.

  Usage:
    lazyfoo = Lazy(lambda: foo())

  This is equivalent to:
    lazyfoo = foo()

  except that foo() is only evaluated when the value in lazyfoo is
  first used (in a non-lazy context). Beware that all the associated
  side effects, including exceptions, will also be delayed and that
  could make debugging interesting.

  e.g.
    bum = Lazy(lambda: FooClass())
    blah = bum             # Nothing happens here
    if something:
      bum.FooMethod(100)   # FooClass() may be instantiated here ...
      bum.FooMethod(200)
    if something_else:
      bum.FooMethod(300)   # ... or possibly here
      bum.FooMethod(400)
                           # ... or never at all

  In the above example, FooClass is only instantiated if 'something'
  or 'something_else' is true. FooClass is not instantiated more than once.

  Caveats:
  - type(Lazy(lambda: x)) differs from type(x). Also, isinstance etc don't work
  - error messages about missing attributes will refer to the Lazy class
  """

  def __init__(self, val_gen):
    assert val_gen
    # We use __dict__ directly because by design self.__foo is
    # supposed to mean self._get().__foo
    self.__dict__['__val_gen'] = val_gen
    self.__dict__['__val'] = None

  def _get(self):
    """
    Evaluates val_gen when invoked the first time.
    Returns val_gen().
    """
    # We use __dict__ directly because by design self.__foo is
    # supposed to mean self._get().__foo
    if self.__dict__['__val_gen']:
      self.__dict__['__val'] = self.__dict__['__val_gen']()
      self.__dict__['__val_gen'] = None
    return self.__dict__['__val']

  def __getattr__(self, arg):
    """
    Delegate all calls to the underlying value object.
    """
    return getattr(self._get(), arg)

  def __setattr__(self, arg, val):
    """
    Set attributes on the underlying value object.
    """
    setattr(self._get(), arg, val)

  def __delattr__(self, arg):
    """
    Delete attribute from the underlying value object.
    """
    delattr(self._get(), arg)

  def __repr__(self):
    """
    Call repr on the underlying value object.
    (repr doesn't get delegated properly by __getattr__ for instances)
    """
    return repr(self._get())

  def __coerce__(self, arg):
    """
    Call coerce on the underlying value object.
    This is needed to get __r{add,mul,...}__ to work automatically
    """
    val = self._get()
    try:
      return coerce(val, arg)
    except TypeError:
      return None

  def __cmp__(self, arg):
    """
    Calls cmp() on the underlying value object.
    This is needed to avoid getting TypeErrors while comparing
    numbers to non-numbers
    """
    return cmp(self._get(), arg)

  # Extra methods for python1.5 compatibility that supercede
  # calls to __getattr__
  #
  # (This may not be a complete list. Please add to it when you find problems)

  def __len__(self):
    return len(self._get())
  def __getitem__(self, key):
    return self._get()[key]
  def __setitem__(self, key, value):
    self._get()[key] = value
  def __delitem__(self, key):
    del self._get()[key]

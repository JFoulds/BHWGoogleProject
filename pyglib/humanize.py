#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Lightweight routines for producing more friendly output.

Usage examples:

  'New messages: %s' % humanize.Commas(star_count)
    -> 'New messages: 58,192'

  'Found %s.' % humanize.Plural(error_count, 'error')
    -> 'Found 2 errors.'

  'Found %s.' % humanize.Plural(error_count, 'ox', 'oxen')
    -> 'Found 2 oxen.'

  'Copied at %s.' % humanize.DecimalPrefix(rate, 'bps')
    -> 'Copied at 42 Mbps.'

  'Free RAM: %s' % humanize.BinaryPrefix(bytes_free, 'B')
    -> 'Free RAM: 742 MiB'

These libraries are not a substitute for full localization.  If you
need localization, then you will have to think about translating
strings, formatting numbers in different ways, and so on.  Use
ICU if your application is user-facing.  Use these libraries if
your application is an English-only internal tool, and you are
tired of seeing "1 results" or "3450134804 bytes used".
"""

__author__ = 'mshields@google.com (Michael Shields)'

import math


SIBILANT_ENDINGS = set(['sh', 'ss', 'ge', 'tch', 'ix', 'ex'])

# These are included because they are common technical terms.
SPECIAL_PLURALS = {
    'index': 'indices',
    'matrix': 'matrices',
    'vertex': 'vertices',
}

VOWELS = set('AEIOUaeiou')


def Commas(value):
  """Formats an integer with thousands-separating commas.

  Args:
    value: An integer.

  Returns:
    A string.
  """
  if value < 0:
    sign = '-'
    value = -value
  else:
    sign = ''
  result = []
  while value >= 1000:
    result.append('%03d' % (value % 1000))
    value /= 1000
  result.append('%d' % value)
  return sign + ','.join(reversed(result))


def Plural(quantity, singular, plural=None):
  """Formats an integer and a string into a single pluralized string.

  Args:
    quantity: An integer.
    singular: A string, the singular form of a noun.
    plural: A string, the plural form.  If not specified, then simple
      English rules of regular pluralization will be used.

  Returns:
    A string.
  """
  if quantity == 1:
    return '%d %s' % (quantity, singular)
  if plural:
    return '%d %s' % (quantity, plural)
  if singular in SPECIAL_PLURALS:
    return '%d %s' % (quantity, SPECIAL_PLURALS[singular])

  # We need to guess what the English plural might be.  Keep this
  # function simple!  It doesn't need to know about every possiblity;
  # only regular rules and the most common special cases.
  #
  # Reference: http://en.wikipedia.org/wiki/English_plural

  for ending in SIBILANT_ENDINGS:
    if singular.endswith(ending):
      return '%d %ses' % (quantity, singular)

  if singular.endswith('o') and singular[-2:-1] not in VOWELS:
    return '%s %ses' % (quantity, singular)

  if singular.endswith('y') and singular[-2:-1] not in VOWELS:
    return '%s %sies' % (quantity, singular[:-1])

  return '%d %ss' % (quantity, singular)


def DecimalPrefix(quantity, unit):
  """Formats an integer and a unit into a string, using decimal prefixes.

  The unit will be prefixed with an appropriate multiplier such that
  the formatted integer is less than 1,000 (as long as the raw integer
  is less than 10**27).  For example:

    DecimalPrefix(576012, 'bps') -> '576 kbps'

  Only the SI prefixes which are powers of 10**3 will be used, so
  DecimalPrefix(100, 'thread') is '100 thread', not '1 hthread'.

  See also:
    BinaryPrefix()
    http://wiki/Nonconf/GigaMeansBillion

  Args:
    quantity: An integer.
    unit: A string.

  Returns:
    A string.
  """
  return _Prefix(quantity, unit, 1000,
                 ('k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'))


def BinaryPrefix(quantity, unit):
  """Formats an integer and a unit into a string, using binary prefixes.

  The unit will be prefixed with an appropriate multiplier such that
  the formatted integer is less than 1,024 (as long as the raw integer
  is less than 2**90).  For example:

    BinaryPrefix(576012, 'B') -> '562 KiB'

  See also:
    DecimalPrefix()
    http://wiki/Nonconf/GigaMeansBillion

  Args:
    quantity: An integer.
    unit: A string.

  Returns:
    A string.
  """
  return _Prefix(quantity, unit, 1024,
                 ('Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'))


def _Prefix(quantity, unit, multiplier, prefixes):
  """Formats an integer and a unit into a string.

  Args:
    quantity: An integer.
    unit: A string.
    multiplier: An integer, the ratio between prefixes.
    prefixes: A sequence of strings.

  Returns:
    A string.
  """
  if not quantity:
    return '0 %s' % unit

  if quantity < 0:
    sign = '-'
    quantity = -quantity
  else:
    sign = ''

  power = min(int(math.log(quantity, multiplier)), len(prefixes))
  if power < 1:
    return '%s%d %s' % (sign, quantity, unit)
  else:
    return '%s%d %s%s' % (sign, quantity / multiplier**power,
                          prefixes[power-1], unit)

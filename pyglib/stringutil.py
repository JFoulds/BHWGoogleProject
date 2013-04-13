#!/usr/bin/python2.4
#
# Copyright 2003 Google, Inc.
# All Rights Reserved.

"""
Some common string manipulation utilities.
"""

import re
import string
import base64

__author__ = 'Laurence Gonsalves, Li Tsun Moore'

_RE_NONASCII = re.compile(r'[^\000-\177]')

# Java Language Specification: Escape Sequences for Char and String Literals
# http://java.sun.com/docs/books/jls/second_edition/html/lexical.doc.html#101089
_JAVA_ESCAPE_MAP = {
  '\b': '\\b',
  '\t': '\\t',
  '\n': '\\n',
  '\f': '\\f',
  '\r': '\\r',
  '"' : '\\"',
  "'" : "\\'",
  '\\': '\\\\',
}
# Octal-escape unprintable characters
for i in range(256):
  c = chr(i)
  if not _JAVA_ESCAPE_MAP.has_key(c) and c not in string.printable:
    _JAVA_ESCAPE_MAP[c] = '\\%03o' % i
# Compile characters-to-be-escaped into regex for matching
_JAVA_ESCAPE_RE = re.compile('|'.join(
                    [re.escape(c) for c in _JAVA_ESCAPE_MAP.keys()]))

class Base64ValueError(Exception): "Illegal Base64-encoded value"

def UnicodeEscape(s):
  r"""
  Replace each non-ASCII character in s with its 6-character unicode
  escape sequence \uxxxx, where xxxx is a hex number.  The resulting
  string consists entirely of ASCII characters.  Existing escape
  sequences are unaffected, i.e., this operation is idempotent.
  
  Sample usage:
    >>> UnicodeEscape('asdf\xff')
    'asdf\\u00ff'
  
  This escaping differs from the built-in s.encode('unicode_escape').  The
  built-in escape function uses hex escape sequences (e.g., '\xe9') and escapes
  some control characters in lower ASCII (e.g., '\x00').
  
  Args:
    s: string to be escaped
  
  Returns:
    escaped string
  """
  return _RE_NONASCII.sub(lambda m: '\\u%04x' % ord(m.group(0)), s)


def JavaEscape(s):
  r"""
  Escape a string so it can be inserted in a Java string or char literal.
  Follows the Java Language Specification for "Escape Sequences for Character
  and String Literals":
  
  http://java.sun.com/docs/books/jls/second_edition/html/lexical.doc.html#101089
  
  Escapes unprintable and non-ASCII characters.  The resulting string consits
  entirely of ASCII characters.
  
  This operation is NOT idempotent.
  
  Sample usage:
    >>> JavaEscape('single\'double"\n\x00')
    'single\\\'double\\"\\n\\000'
  
  Args:
    s: string to be escaped
  
  Returns:
    escaped string
  """
  s_esc = _JAVA_ESCAPE_RE.sub(lambda m: _JAVA_ESCAPE_MAP[m.group(0)], s)
  # Unicode-escape remaining non-ASCII characters.  In the default Python
  # locale, printable characters are all ASCII, and we octal-escaped all
  # unprintable characters above, so this step actually does nothing.  Leave it
  # in for locales that have non-ASCII printable characters.
  return UnicodeEscape(s_esc)

def DeleteChars(s, deletechars):
  """
  Delete characters in 'deletechars' from string 's'.

  Args:
    s          : string
    deletechars: string of characters to delete from 's'

  Returns:
    modified s
  """

  return s.translate(string.maketrans('',''), deletechars)

# FYI, Python 2.4's base64 module has a websafe encode/decode. However:
#
# (1) The encode still appends =-padding. Even more annoying,
# (2) The decode still *requires* that =-padding be present. This makes it
# incompatible with the C++ or Sawzall (based on the C++) implementations.
# (3) On decode, the handling of invalid characters varies (both versions ignore
# whitespace, otherwise the C++ version fails, the Python version ignores
# invalid characters).
def WebSafeBase64Escape(unescaped, do_padding):
  """Python implementation of the Google C library's WebSafeBase64Escape().

  Python implementation of the Google C library's WebSafeBase64Escape() (from
  strings/strutil.h), using Python's base64 API and string replacement.

  params:
    unescaped: any data string (example: "12345~6")
    do_padding: whether to add =-padding (example: false)

  returns:
    The base64 encoding (with web-safe replacements) of unescaped,
    with =-padding depending on the value of do_padding
    (example: "MTIzNDV-Ng")
  """
  # Strip off the trailing newline
  escaped = (base64.binascii.b2a_base64(unescaped)[:-1].
             translate(string.maketrans('+/', '-_')))

  if not do_padding:
    escaped = escaped.rstrip("=")

  return escaped

# Mapping table to convert web-safe base64 encoding to the standard
# encoding ('-' becomes '+', '_' becomes '/', and other valid base64
# input characters map to themselves).  To maintain compatibility with
# the C++ library, characters that are neither valid base64 input
# characters nor whitespace are mapped to '!'.

_BASE64_DECODE_TRANSLATION = (
  "!!!!!!!!!     !!!!!!!!!!!!!!!!!!"
  " !!!!!!!!!!!!+!!0123456789!!!=!!"
  "!ABCDEFGHIJKLMNOPQRSTUVWXYZ!!!!/"
  "!abcdefghijklmnopqrstuvwxyz!!!!!"
  "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

def WebSafeBase64Unescape(escaped):
  """Python implementation of the Google C library's WebSafeBase64Unescape().

  Python implementation of the Google C library's WebSafeBase64Unescape() (from
  strings/strutil.h), using Python's base64 API and string replacement.

  params:
    escaped: A base64 string using the web-safe encoding (example: "MTIzNDV-Ng")

  returns:
    The corresponding unescaped string (example: "12345~6")
  """
  escaped_standard = escaped.translate(_BASE64_DECODE_TRANSLATION)
  if escaped_standard.find("!") >= 0:
    raise Base64ValueError("%s: Invalid character in encoded string." % escaped)

  # Make the encoded string a multiple of 4 characters long, adding "="
  # characters as padding.  This is the format standard base64 expects.
  if not escaped_standard.endswith("="):
    padding_len = len(escaped_standard) % 4
    escaped_standard = escaped_standard + "=" * padding_len

  try:
    return base64.binascii.a2b_base64(escaped_standard)

  except base64.binascii.Error, msg:
    raise Base64ValueError("%s: %s" % (escaped, msg))

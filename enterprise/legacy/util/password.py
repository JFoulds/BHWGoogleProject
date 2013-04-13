#!/usr/bin/python2.4

# Copyright 2004 Google Inc.

import base64

import sys
import sha

SYMBOLS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def sha1_base64_hash(password, salt):
  return base64.encodestring(sha.new(password + salt).digest())[:-1]

def createRandomPasswd(length = 12):
  symLen = len(SYMBOLS)
  passwd = []
  urandom = open('/dev/urandom')
  for _ in range(length):
    passwd.append(SYMBOLS[ord(urandom.read(1)) % symLen])
  urandom.close()
  return ''.join(passwd)

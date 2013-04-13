#!/usr/bin/python2.4
#
# (c)2000 Google inc
# cpopescu@google.com
#
# A small mail notification module
#
###############################################################################
"""
Usage:
    mailnotify.py <server> <subject> <from> <to> <message>
"""
###############################################################################
import sys
import string

import smtplib
import signal


############################################################################

# 60 secs for smtp timeout
SMTP_TIMEOUT = 60

def alarmHandler(signum, frame):
  raise IOError, "Timeout contacting the SMTP server."

# utility to strip ' and " in addresses
def StripQuotes(email_address):
  to_loop = 1
  while to_loop:
    to_loop = 0
    if email_address[0] == "\'":
      email_address = email_address[1:]
      to_loop = 1
    length = len(email_address)
    if email_address[length - 1] == "\'":
      email_address = email_address[:length - 1]
      to_loop = 1
  return email_address

###############################################################################

def SendMail(server, subject, from_address, to_addresses, body):

  numtry = 5

  while numtry > 0:

    try:
      try:
        signal.signal(signal.SIGALRM, alarmHandler)
        signal.alarm(SMTP_TIMEOUT)

        S = smtplib.SMTP(server)

        # clean up to_addresses
        list_to = string.split(to_addresses, ',')
        list_to = filter(None, map(string.strip, list_to))
        list_to = filter(None, map(StripQuotes, list_to))

        if len( list_to ) > 0:
          S.sendmail(
            from_address,
            list_to,
            string.join(["Subject: %s" % subject,
                         "", # empty line before body
                         body],
                        "\n")
            )
        S.quit();
        return 1

      finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    except IOError, e:
      print "Error: %s" % ( str(e) )
      numtry = numtry - 1

  return 0

###############################################################################

def main(argv):

  if len(argv) != 5:
    sys.exit(__doc__)

  SendMail(argv[0], argv[1], argv[2], argv[3], argv[4])


###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

###############################################################################

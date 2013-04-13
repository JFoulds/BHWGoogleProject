# Copyright 2004-2005 Google Inc.
# All Rights Reserved.
#
# Original Author: Mark D. Roth
#


def ElapsedTime(interval, fractional_seconds=0, abbreviate_days=0):
  """
  Returns a string in the form "HH:MM:SS" for the indicated interval,
  which is given in seconds.  If the time is more than a day, prepends
  "DD day(s) " to the string.

  If the fractional_seconds keyword argument is set to true, then two
  digits of sub-second accuracy will be included in the output.

  If the abbreviate_days keyword argument is set to true and the
  interval is more than a day, the number of days will be printed in an
  abbreviated fashion (e.g., "5d" instead of "5 day(s)").
  """
  # extract seconds
  interval, secs = divmod(interval, 60)

  # extract minutes
  interval, mins = divmod(interval, 60)

  # extract hours
  interval, hrs = divmod(interval, 24)

  # whatever's left is the days
  if interval:
    if abbreviate_days:
      text = '%dd ' % interval
    else:
      text = '%d day(s) ' % interval
  else:
    text = ''

  # construct and return string
  if fractional_seconds:
    text += '%02d:%02d:%05.2f' % (hrs, mins, secs)
  else:
    text += '%02d:%02d:%02d' % (hrs, mins, secs)
  return text

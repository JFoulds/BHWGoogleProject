#!/usr/bin/python2.4
# Copyright (C) 2002 and onwards Google, Inc.
#
# This module contains the functions that determine the scheduling of requests
#

from google3.pyglib import logging

###############################################################################

# global scheduled tasks -- does not allow anything else to run
GLOBAL = "global"

# This is a list that contains the scheduling info for the running requests.
# We use this to deny running two requests that have conflicting scheduling
# info.
# For our requests we return a list of scheduling info strings. For example
# for requests that concern a machine:port we have '<machine>:<port>' as
# scheduling info and we later deny running requests that affect this
# machine:port until we finished running the current request
RUNNING_INFO = []

def HandleCompletion(req):
  """
  This is called when a request is completed with failure or success.
  We use this to record the fact that the scheduling info for this request
  is freed
  """
  logging.debug("Handling  END %s" % req.GetFilename())

  scheduling_info = req.GetSchedulingInfo()
  if not scheduling_info:
    return
  global RUNNING_INFO
  for si in scheduling_info:
    if si in RUNNING_INFO:
      RUNNING_INFO.remove(si)

def AllowedFilter(req, _, dummy):
  """
  Called to check if we allow to execute request considerring it's
  scheduling info. If we schedule this one we add it's shceduling
  info to RUNNING_INFO
  """
  logging.debug("Filtering %s" % req.GetFilename())

  scheduling_info = req.GetSchedulingInfo()
  if not scheduling_info:
    return 0

  # Globals does not allow anything
  if GLOBAL in RUNNING_INFO: return 1

  # see if we running something with the same scheduling info
  for si in scheduling_info:
    if si in RUNNING_INFO: return 1

  RUNNING_INFO.extend(scheduling_info)
  logging.debug("Allowed %s" %req.GetFilename())
  return 0

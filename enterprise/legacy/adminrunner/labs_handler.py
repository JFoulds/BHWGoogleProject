#!/usr/bin/python2.4
#
# (c) Copyright 2007 Google Inc. All Rights Reserved.
# David Elworthy <dahe@google.com>
#
# Handler for labs features.

"""Handler for experimental (labs) features.

Labs features are experimental and pre-release additions to the GSA. This
handler is used as a common location for their adminrunner operations. If and
when they become full scale release features, the code should be relocated
to other handlers.

Command names should be prefixed with something to indicate which labs
feature they apply to.

Commands:
USAGEBOOST (prefix=ub):
- ubactivate 0|1
            Deactivate or activate usage boost.
- ubsettatus mask 0|1
            Update usageboost status by clearing or setting bits specified
            in the mask, depending on whether the final argument is 0 or 1.
"""

from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.adminrunner import scoring_adjust_handler
from google3.enterprise.legacy.util import C


class LabsHandler(admin_handler.ar_handler):
  """Handler for scoring policies and adjustments."""

  # Status constants for usage boost
  USAGEBOOST_DATA_LOADED = 1
  USAGEBOOST_SETTINGS_OK = 2
  USAGEBOOST_ACTIVE = 4

  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg should be non-null only when called from the unit test
    if cfg is not None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    """Provide list of commands accepted by this module.

    The name of this method does not follow the coding standards, but has
    to be this way due due to the class we inherit from.

    Returns:
      Table of commands.
    """
    return {
        "ubactivate": admin_handler.CommandInfo(1, 0, 0, self.UBActivate),
        "ubsetstatus": admin_handler.CommandInfo(2, 0, 0, self.UBSetStatus),
        }

  ############################################################################

  def UBActivate(self, action):
    """Activate or deactivate usage boost.

    Args:
      action: 0 for deactivate, 1 for activate.

    Returns:
      0 or error code.
    """
    logging.info("Usage boost activate action=%s" % action)
    action = int(action)

    # Get old status and do nothing unless we are changing
    old_status = self.cfg.getGlobalParam(C.LABS_USAGEBOOST_STATUS)
    if action == 1:
      if not old_status & self.USAGEBOOST_ACTIVE:
        # Make scoring policies for standard settings, then append extra ones
        # for usageboost.
        params = self.cfg.getGlobalParam(C.LABS_USAGEBOOST_PARAMS)
        logging.info("Params is %s" % repr(params))

        # Names of the fields in params should align with the ones in
        # config.default and UsageBoostHandler.
        weight = float(params["WEIGHT"])/100
        args = "6 t %s %s %s %s %s" % (
            weight,
            self.cfg.getGlobalParam(C.LABS_USAGEBOOST_DATA),
            params["FUNCTION"],
            params["DEFAULT_COUNT"],
            params["NORM_FACTOR"]
            )
        logging.info("args is %s" % repr(args))
        policies = (scoring_adjust_handler.MakeScoringConfig(self.cfg) +
                    "u: rescorer\n usageboost " + args + "\n :\n ;\n" +
                    "ua: composite a u;\n")
        scoring_adjust_handler.SaveScoringPolicies(self.cfg, policies)
        self.UBSetStatus(self.USAGEBOOST_ACTIVE, 1)
        logging.info("Usageboost activated with config " + policies)
      else:
        logging.info("Usageboost already active: no change")
    else:
      if old_status & self.USAGEBOOST_ACTIVE:
        # Restore the standard scoring configuration file.
        scoring_adjust_handler.ApplyAndSaveSettings(self.cfg)
        self.UBSetStatus(self.USAGEBOOST_ACTIVE, 0)
        logging.info("Usageboost deactivated")
      else:
        logging.info("Usageboost already inactive: no change")

    return "0\n"

  def UBSetStatus(self, mask, action):
    """Set or clear bits in the usageboost status."""
    logging.info("Usage boost setstatus mask=%s action=%s" % (mask, action))
    status = self.cfg.getGlobalParam(C.LABS_USAGEBOOST_STATUS)
    mask = int(mask)

    if int(action) == 1:
      status |= mask
    else:
      status &= ~mask
    self.cfg.setGlobalParam(C.LABS_USAGEBOOST_STATUS, status)

    return "0\n"

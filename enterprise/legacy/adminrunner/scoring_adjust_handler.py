#!/usr/bin/python2.4
#
# (c) Copyright 2006 Google Inc.
#
# Handler for scoring adjustment.
# Provides commands for configuring scoring policies and adjustments to
# scoring.
# To allow for different kinds of adjustment, each scoring adjustment has a
# group name, e.g. patterns, and the arguments consist of a string which
# must be interpreted specifically for that group.
#
# Commands:
#
# - create <policy>
#             Create a scoring policy with the given name.  The name
#             must either be the default policy name, as defined here
#             and in Scoring.java, or must consist of alphanumeric and
#             underscore characters.
#
# - delete <policy>
#             Delete the given scoring policy if it exists, or returns false.
#
# - list
#             Return a list of scoring policy names.
#
# - getparams <policy> <group>
#             Gets the configuration for the named policy and group.
#
# - setparams <policy> <params>
#             Sets the configuration for the params, a mapping from group name
#             to settings for the group, for the named policy.
#
# - apply
#             Applies the settings. This creates the internal scoring policies
#             file, and restarts rtserver with it.
#
# The default policy parameters are held in the configuration variable
# ENT_SCORING_ADJUST as a map from group name to the settings for the
# group.  The settings are either None or a list of strings.
# Additional policies are held in ENT_SCORING_ADDITIONAL_POLICIES as a
# map from policy names to policy maps similar to ENT_SCORING_AJUST.

__author__ = 'dahe@google.com (David Elworthy)'

import os
import string
import re
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.util import C
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.util import config_utils
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.pyglib import logging


class ScoringAdjustHandler(admin_handler.ar_handler):
  """Handler for scoring policies and adjustments."""

  # Default policy name (must match the one in Scoring.java)
  DEFAULT_POLICY_NAME = 'default_policy'

  # When filling in the template to create the scoring file, the
  # default policy name is replaced by the empty string, giving
  # the default rescorer the backwards-compatible name "a".  (This is
  # why it is legitimate for the default name to contain non-word
  # characters, since it never appears in the template).
  # If this changes, must change Scoring.ADVANCED in Scoring.java.
  DEFAULT_POLICY_LABEL = ''

  # Add underscores between the "a" and the policy_name, for
  # aesthetics, e.g. my_policy becomes a__my_policy, not
  # amy_policy.
  # If you change this, you must also change Scoring.ADVANCED_PREFIX
  # in Scoring.java.
  POLICY_NAME_PREFIX = '__'

  def __init__(self, conn, command, prefixes, params, cfg=None):
    # cfg should be non-null only when called from the unit test
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
        "create": admin_handler.CommandInfo(1, 0, 0, self.create),
        "delete": admin_handler.CommandInfo(1, 0, 0, self.delete),
        "list": admin_handler.CommandInfo(0, 0, 0, self.listpolicies),
        "getparams": admin_handler.CommandInfo(2, 0, 0, self.getparams),
        "setparams": admin_handler.CommandInfo(2, 0, 0, self.setparams),
        "apply": admin_handler.CommandInfo(0, 0, 0, self.applysettings),
      }

  def construct_collection_object(self, name):
    return self.qe_base.ConstructCollectionObject(name)

  ############################################################################

  def create(self, policy_name):
    """Creates a new scoring policy.

    Args:
      policy_name: string

    Returns:
      an integer error code:
      C.SCORING_ADJUST_POLICY_CREATE_OK if success
      C.SCORING_ADJUST_POLICY_EXISTS    if policy already exists
      C.SCORING_ADJUST_POLICY_BAD_NAME  if name not valid
      C.SCORING_ADJUST_LICENSE_LIMIT    if policy creation would exceed license
    """

    # Count current policies.
    scoring_adjust = self.cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
    policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
    num_current_policies = 0
    if policies is None:
      policies = {}
    else:
      num_current_policies = len(policies)
    if scoring_adjust is not None:
      num_current_policies += 1

    # Check license limit.
    max_policies = GetMaxLicense(self.cfg)
    if (max_policies != 0) and (num_current_policies >= max_policies):
      return C.SCORING_ADJUST_LICENSE_LIMIT

    if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
      # Default policy goes in ENT_SCORING_ADJUST
      if scoring_adjust is not None:
        return C.SCORING_ADJUST_POLICY_EXISTS
      self.cfg.setGlobalParam(C.ENT_SCORING_ADJUST, {})
      return C.SCORING_ADJUST_POLICY_CREATE_OK
    else:
      # Additional policies go in ENT_SCORING_ADDITIONAL_POLICIES
      # Validate the policy name.
      if not entconfig.IsNameValid(policy_name):
        logging.error("Invalid policy name %s -- cannot create" % policy_name)
        return C.SCORING_ADJUST_POLICY_BAD_NAME
      if policy_name in policies:
        return C.SCORING_ADJUST_POLICY_EXISTS

      # Add policy
      policies[policy_name] = {}
      self.cfg.setGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES, policies)
      return C.SCORING_ADJUST_POLICY_CREATE_OK

  def delete(self, policy_name):
    """Deletes the policy with the given name, or returns false."""
    if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
      # Default policy goes in ENT_SCORING_ADJUST
      scoring_adjust = self.cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
      if scoring_adjust is None:
        return False
      self.cfg.setGlobalParam(C.ENT_SCORING_ADJUST, None)
      return True
    else:
      policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
      if policies is None or policy_name not in policies:
        return False
      del policies[policy_name]
      self.cfg.setGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES, policies)
      return True

  def listpolicies(self):
    """Returns a list of scoring policies."""
    policy_names = []
    policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
    if policies is not None:
      policy_names = policies.keys()

    # Default policy
    scoring_adjust = self.cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
    if scoring_adjust is not None:
      policy_names.append(ScoringAdjustHandler.DEFAULT_POLICY_NAME)

    policy_names.sort()
    return '%s\n' % '\n'.join(policy_names)

  def getparams(self, policy_name, group, error_info=None):
    """Get the parameters for a group of scoring adjustments.
       Returned as a string. Result is an empty string if the group is
       unknown or has no data."""
    error_str = None
    policy = None
    if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
      policy = self.cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
    else:
      policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
      if policies and policy_name in policies:
        policy = policies[policy_name]
    if not policy:
      error_str = "No policy named '%s'" % policy_name
    elif group not in policy:
      error_str = "No group '%s' for policy '%s'" % (group, policy_name)
    elif not policy[group]:
      error_str = ("Empty param list for policy '%s' group '%s'" %
                   (policy_name, group))
    else:
      return policy[group]

    logging.info("No params available: %s" % error_str)
    if error_info is not None:
      # Return error string for testing purposes.
      error_info.append(error_str)
    return ""

  def setparams(self, policy_name, encoded_args):
    """Set the parameters for groups of scoring adjustments, including
       validation. Creates the group if it does not exist.
       If no errors, returns an empty list.
       Otherwise, returns a list of tuples of error code and detail string."""

    settings = {}
    config_utils.SafeExec(string.strip(encoded_args), settings)
    errors = []

    # Validate settings for each group.
    for group in settings.keys():
      if group == "patterns":
        # Params should be a list containing the scoring weight, then
        # alternating patterns and adjust levels. We only validate the
        # patterns.
        errors = self.validate_patterns(settings["patterns"])
      elif group == "datebias":
        # the only param, weight [0..100] is already validated in the
        # handler code (ScoringAdjustHandler)
        pass
      elif group == "metadata":
        # Params should be a list containing the scoring weight, then
        # alternating name:value metadata information and adjust levels.
        # We only validate the name:value metadata information.
        errors = self.validate_metadata(settings["metadata"])
      else:
        logging.info("Ignoring unknown scoring group " + group)

    # If no errors yet, make sure policy is present.
    policy = None
    if not errors:
      if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
        policy = self.cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
      else:
        policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
        if policies and policy_name in policies:
          policy = policies[policy_name]
      if policy is None:
        errors.append(validatorlib.ValidationError(
            policy_name, C.SCORING_ADJUST_POLICY_MISSING))

    # If no errors, now save each group (even unknown ones)
    if not errors:
      for group in settings.keys():
        policy[group] = settings[group]
      if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
        self.cfg.setGlobalParam(C.ENT_SCORING_ADJUST, policy)
      else:
        policies = self.cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
        policies[policy_name] = policy
        self.cfg.setGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES, policies)
      errors = validatorlib.VALID_OK

    return admin_handler.formatValidationErrors(errors)

  def validate_patterns(self, params):
    """Validate the provided patterns, and return a list of associated
    errors, either caused by duplicate or malformed patterns."""
    nparams = len(params)
    errors = []

    # Map each pattern to its number of occurences.
    pattern_count = {}
    for i in xrange(1, nparams, 2):
      pattern = params[i]
      pattern_count.setdefault(pattern, 0)
      pattern_count[pattern] += 1
    # Map keys with values greater than one must be duplicate patterns.
    duplicate_patterns = map(lambda x: x[0],
        filter(lambda x: x[1] > 1, pattern_count.iteritems()))
    # For the detailed string, use the pattern.
    # We can't use the actual message back from the validator, as it
    # is not internationalized.
    for pattern in duplicate_patterns:
      errors.append(validatorlib.ValidationError(
          pattern, C.SCORING_ADJUST_DUPLICATE_PATTERNS))
    if errors:
      # Do not proceed with further validation if any duplicates.
      return errors

    # Next, check for malformed patterns.
    validator = validatorlib.EnterpriseURLPattern()
    for i in xrange(1, nparams, 2):
      pattern = params[i]
      pattern_errors = validator.validate(pattern, None)
      if (pattern_errors != validatorlib.VALID_OK and
          pattern_errors != validatorlib.VALID_SHORT_CIRCUIT):
        logging.info(
          "Errors on pattern %s are %s" % (pattern, repr(pattern_errors)))
        errors.append(validatorlib.ValidationError(
            pattern, C.SCORING_ADJUST_BAD_URL_PATTERNS))
    return errors

  def validate_metadata(self, params):
    """Validate the provided name:value metadata pairs, and return
    a list of associated errors, either caused by duplicate or
    malformed pairs."""
    nparams = len(params)
    errors = []

    # Map each name:value metadata pair to its number of occurences.
    pair_count = {}
    for i in xrange(1, nparams, 2):
      pair = params[i]
      pair_count.setdefault(pair, 0)
      pair_count[pair] += 1
    # Map keys with values greater than one must be duplicate pairs.
    duplicate_pairs = map(lambda x: x[0],
                          filter(lambda x: x[1] > 1, pair_count.iteritems()))
    # For the detailed string, use the name:value metadata pair.
    # We can't use the actual message back from the validator, as it
    # is not internationalized.
    for pair in duplicate_pairs:
      errors.append(validatorlib.ValidationError(
          pair, C.SCORING_ADJUST_DUPLICATE_PAIRS))
    if errors:
      # Do not proceed with further validation if any duplicates.
      return errors

    # Next, check for malformed name:value pairs.
    validator = validatorlib.EnterpriseMetadata()
    for i in xrange(1, nparams, 2):
      pair = params[i]
      pair_errors = validator.validate(pair, None)
      if (pair_errors != validatorlib.VALID_OK and
          pair_errors != validatorlib.VALID_SHORT_CIRCUIT):
        logging.info(
            "Errors on pair %s are %s" % (pair, repr(pair_errors)))
        errors.append(validatorlib.ValidationError(
            pair, C.SCORING_ADJUST_BAD_PAIRS))
    return errors

  def applysettings(self):
    """Apply scoring adjustment settings."""
    return ApplyAndSaveSettings(self.cfg)


def GetMaxLicense(cfg):
  """Returns the number of licensed scoring policies."""
  # For a first pass, allow unlimited policies.
  return 0
  # TODO(erocke): Add a new variable ENT_LICENSE_MAX_SCORING_POLICIES
  # in the license; add getMaxScoringPolicies() to ent_license.py
  # accessor functions.


def MakeScoringConfig(cfg):
  """Apply scoring adjustment settings, returning the new scoring
  configuration as a string, suitable for storing in the scoring policies
  file, or for subsequent modification."""

  # To apply the settings, we read a template scoring policies file,
  # and substitute the values from the configuration into it.
  # The format output here has to be consistent with the file format used in
  # the enterprise scorer code within rtserver (indexserving).

  # Collect the default policy with any additional policies in a single
  # dictionary.
  scoring_adjust = cfg.getGlobalParam(C.ENT_SCORING_ADJUST)
  policies = cfg.getGlobalParam(C.ENT_SCORING_ADDITIONAL_POLICIES)
  if policies is None:
    policies = {}
  if scoring_adjust is not None:
    policies[ScoringAdjustHandler.DEFAULT_POLICY_NAME] = scoring_adjust

  # Compile each group to the internal format
  output = {}
  for policy_name, groups in policies.iteritems():
    output[policy_name] = {}
    for group, params in groups.iteritems():
      if not params:
        logging.info("Ignoring scoring group '%s' with empty params" % group)
        continue
      nparams = len(params)  # Must be >= 1 if the previous check passed.
      if group == "patterns":
        # Format is rescorer name, number of args, then weight, then patterns
        # and levels. If there are no patterns, disable this group
        if nparams > 1:
          weight = float(params[0])/100
          rescorer_args = "patterns %s %s" % (nparams, weight)
          for i in range(1, nparams, 2):
            rescorer_args += " %s %s" % (params[i], params[i+1])
          output[policy_name][group] = rescorer_args
      elif group == "datebias":
        weight = float(params[0])/100
        datebias_args = "datebias 1 %f" % (weight)
        output[policy_name][group] = datebias_args
      elif group == "metadata":
        # Format is rescorer name, number of args, then weight, then
        # pairs of name:value metadata information.  If there are no
        # name:value metadata pairs, then disable this group.
        if nparams > 1:
          if nparams % 2 != 1:
            logging.info('Ignoring bad metadata group with %d params (requires'
                         ' odd number of params)' % nparams)
            continue
          weight = float(params[0])/100
          metadata_args = "metadata %s %s" % (nparams, weight)
          for i in range(1, nparams, 2):
            metadata_args += " %s %s" % (params[i], params[i+1])
          output[policy_name][group] = metadata_args
      else:
        logging.info("Ignoring unknown scoring group " + group)

  return FormatScoringConfig(cfg, output)


def FormatScoringConfig(cfg, output):
  """Reads the template file and fills in %%group%% with appropriate values.

  Args:
    cfg: An entconfig instance, which contains global parameter values.
    output: Dictionary of values to fill in template.

  Returns:
    A string representing the filled-in template file, or an empty string
    in case of an error.
  """

  template_name = cfg.getGlobalParam(C.ENT_SCORING_TEMPLATE)
  if not template_name:
    logging.info("Missing template file name setting")
    return ""

  template_file = None
  try:
    template_file = open(template_name, "r")
  except IOError, e:
    logging.info("Cannot open scoring template file " + template_name)
    return ''

  result = template_file.read()
  template_file.close()

  # It is an error if the template contains more than one
  # %%beginscoringadjust%% or %%endscoringadjust%%
  for tag in ['%%beginscoringadjust%%', '%%endscoringadjust%%']:
    duplicate_re = re.compile('%s.*%s' % (tag, tag), re.DOTALL)
    duplicate_match = duplicate_re.search(result)
    if duplicate_match is not None:
      logging.info("Scoring template contains duplicate %s." % tag)
      return ""

  config_re = re.compile(
      r'%%beginscoringadjust%% *\n*(.*)%%endscoringadjust%% *\n*',
      re.DOTALL)
  config_match = config_re.search(result)
  if config_match is None:
    logging.info("Scoring template in incompatible format.")
    return ""
  scoring_adjust_string = config_match.group(1)

  rescorers = []
  policy_names = output.keys()
  policy_names.sort()
  for policy_name in policy_names:
    display_name = None
    if policy_name == ScoringAdjustHandler.DEFAULT_POLICY_NAME:
      display_name = ScoringAdjustHandler.DEFAULT_POLICY_LABEL
    else:
      display_name = ScoringAdjustHandler.POLICY_NAME_PREFIX + policy_name
    rescorer = scoring_adjust_string.replace("%%rescorername%%", display_name)
    for group in output[policy_name].keys():
      rescorer = rescorer.replace("%%" + group + "%%",
                                  output[policy_name][group])
    rescorers.append(rescorer)

  result = ''.join([result[0:config_match.start()]] +
                   rescorers +
                   [result[config_match.end():]])

  # In case the template contains a reference to a group that we
  # did not find, delete all remaining tags.
  param_finder = re.compile(r' *%%.+?%% *\n*')
  return param_finder.sub('', result)

def SaveScoringPolicies(cfg, policies):
  """Save the scoring policies in the standard location."""
  cfg.globalParams.set_file_var_content(C.ENT_SCORING_CONFIG, policies, None)

def ApplyAndSaveSettings(cfg):
  """Apply scoring adjustment settings. Static version, taking the
  configuration object as a parameter."""
  SaveScoringPolicies(cfg, MakeScoringConfig(cfg))

  # Restart babysitter, so that it will check for possible rtslave argv changes
  # and restart rtslave process if neccessary.
  os.system("/etc/rc.d/init.d/serve_%s babysit &" %
            cfg.getGlobalParam('VERSION'))

  return "0\n"

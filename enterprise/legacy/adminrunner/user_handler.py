#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com ==-- from UserHandler.java
#
# The "user" command handler for AdminRunner
#
###############################################################################

import string
from google3.pyglib import logging
import sys

from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.enterprise.legacy.collections import ent_collection
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.util import config_utils

###############################################################################

true  = 1
false = 0

USERDATA = ["USERNAME",
            "PASSWD_ENC",
            "EMAIL",
            "PERMISSIONS",
            ]

###############################################################################

class UserHandler(admin_handler.ar_handler):
  # The constructor gets the Configurator from the AdminRunner

  def __init__(self, conn, command, prefixes, params, cfg = None):
    # cfg in non-null only for testing (we cannot have multiple constructore)
    if cfg != None:
      self.cfg = cfg
      self.user_data = self.parse_user_data(prefixes)
      return

    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "validuser"           : admin_handler.CommandInfo(
      1, 0, 0, self.validuser),
      "validuserpasswd"     : admin_handler.CommandInfo(
      2, 0, 0, self.validuserpasswd),
      "getuserpasswd"       : admin_handler.CommandInfo(
      2, 0, 0, self.getuserpasswd),
      "setuserpasswd"       : admin_handler.CommandInfo(
      3, 0, 0, self.setuserpasswd),
      "forceuserpasswd"     : admin_handler.CommandInfo(
      2, 0, 0, self.forceuserpasswd),
      "getemail"            : admin_handler.CommandInfo(
      1, 0, 0, self.getemail),
      "setemail"            : admin_handler.CommandInfo(
      2, 0, 0, self.setemail),
      "alluserdata"         : admin_handler.CommandInfo(
      0, 0, 0, self.alluserdata),
      "getall"              : admin_handler.CommandInfo(
      0, 0, 0, self.getall),
      "createuser"          : admin_handler.CommandInfo(
      6, 0, 0, self.createuser),
      "deleteuser"          : admin_handler.CommandInfo(
      1, 0, 0, self.deleteuser),
      "getaccounttype"             : admin_handler.CommandInfo(
      1, 0, 0, self.getAccountType),
      "setaccounttype"            : admin_handler.CommandInfo(
      2, 0, 0, self.setAccountType),
      "haspermission"       : admin_handler.CommandInfo(
      2, 0, 0, self.haspermission),
      "setpermission"       : admin_handler.CommandInfo(
      3, 0, 0, self.setpermission),
      "filterpermissions"   : admin_handler.CommandInfo(
      2, 0, 0, self.filterpermissions),
      "getinfo"             : admin_handler.CommandInfo(
      1, 0, 0, self.getinfo),
      "getvar"              : admin_handler.CommandInfo(
      2, 0, 0, self.getvar),
      "setvar"              : admin_handler.CommandInfo(
      2, 1, 0, self.setvar),
      }


  def validuser(self, name):
    return not self.cfg.um.doesUserExist(name)

  def validuserpasswd(self, name, passwd):
    passed = self.cfg.um.isUserPasswdValid(name, passwd[1:])
    if passed:
      self.cfg.lm.startCounting()
    return not passed

  def getuserpasswd(self, name, ip):
    return not self.cfg.um.getPasswd(name, ip)

  def setuserpasswd(self, name, passwd, newpasswd):
    status = not self.cfg.um.changePasswd(name, passwd[1:], newpasswd[1:])
    if not status:
      # log this set UserPasswd action
      msg = M.MSG_LOG_SET_USERPASSWORD % (name)
      self.writeAdminRunnerOpMsg(msg)
    return status

  def forceuserpasswd(self, name, passwd):
    status = not self.cfg.um.forcePasswd(name, passwd[1:])
    if not status:
      # log this force UserPasswd action
      msg = M.MSG_LOG_FORCE_USERPASSWORD % (name)
      self.writeAdminRunnerOpMsg(msg)
    return status

  def getemail(self, name):
    email = self.cfg.um.getEmail(name)
    if email == None: return "1"
    return "%s\n0" % email

  def setemail(self, name, email):
    status = self.cfg.um.setEmail(name, email)
    if not status:
      # log this email change event
      msg = M.MSG_LOG_CHANGE_EMAIL % (name)
      self.writeAdminRunnerOpMsg(msg)
    return status

  def alluserdata(self):
    allUserData = self.cfg.um.getAllUserData()
    if None == allUserData: return "1"

    ret = []
    for u in allUserData.values():
      ret.append("%s %s %s %s" % (
        u.name, u.email, u.accountType, string.join(u.permissions, ",")))
    return "%s\n0" % string.join(ret, "\n")

  def getall(self):
    return string.join(self.cfg.um.getAllUserNames(), ",")

  def createuser(self, name, ip, newname, passwd, email, permissions):
    # Compatibility with old protocol ( bad thing probably)
    # dictates: protocols is a string of tokens
    permissions = string.split(permissions[1:], " ")
    status = self.cfg.um.createUser(
      name, ip,
      newname,
      passwd[1:],
      email,
      permissions[0],
      permissions[1:])
    # creation succeed if status is 0
    if not status:
      # log this creation
      msg = M.MSG_LOGNEWUSER % (newname)
      self.writeAdminRunnerOpMsg(msg)
    return status

  def deleteuser(self, name):
    userparam = ent_collection.EntUserParam(name, self.cfg.globalParams)
    if userparam.Exists():
      userparam.Delete()
    # deletion succeed if status is 1 (true)
    # however we want to return 0 on success since the
    # convention of success status for adminrunner is 0
    status = self.cfg.um.deleteUser(name)
    if status:
      # log this deletion
      msg = M.MSG_LOG_DELETE_USER % (name)
      self.writeAdminRunnerOpMsg(msg)
    return not status

  def getAccountType(self, name):
    accountType = self.cfg.um.getAccountType(name)
    if accountType == None: return "1"
    return "%s\n0" % accountType

  def setAccountType(self, name, accountType):
    status = self.cfg.um.setAccountType(name, accountType)
    # status is 0 (i.e. USER_OK) for success, unlike some other operations
    if status == 0:
      msg = M.MSG_LOG_CHANGE_ACCOUNT_TYPE % (accountType, name)
      self.writeAdminRunnerOpMsg(msg)
    return status

  def haspermission(self, name, perm):
    return not self.cfg.um.hasPermission(name, perm)

  def setpermission(self, name, perm, on):
    on = on == "ON"
    return not self.cfg.um.setPermission(name, perm, on)

  def filterpermissions(self, name, perm):
    # perms is a space separated list of permissions with an X in
    # front
    perm = string.split(perm[1:], " ")
    return " %s" % string.join(self.cfg.um.filterPermissions(name, perm), " ")

  def getinfo(self, name):
    info = self.cfg.um.getUserData(name)
    if info == None: return "1"

    # perms for output include the accountType and the actual permissions
    perms = [info.accountType]
    perms.extend(info.permissions)

    return (
      "USERNAME = %s\nPASSWD_ENC = %s\nEMAIL = %s\nPERMISSIONS = %s\n0"% (
      repr(info.name),
      repr(info.passwd),
      repr(info.email),
      repr(string.join(perms, ","))))

  def getvar(self, userName, varName):
    user = ent_collection.EntUserParam(userName,
                                       self.cfg.globalParams)
    try:
      value = user.get_var(varName)
    except KeyError:
      value = None

    return "%s = %s" % (varName, repr(value))

  def setvar(self, userName, varName, varVal):
    user = ent_collection.EntUserParam(userName,
                                       self.cfg.globalParams)
    # if user has no params yet, create them
    if not user.Exists() and not user.Create():
      logging.error("Failed to create userparam %s" % userName)
      user.Delete()
      return admin_handler.formatValidationErrors([
        validatorlib.ValidationError("Invalid User")])

    val = {}
    config_utils.SafeExec(string.strip(varVal), val)
    if not val.has_key(varName): return 1
    value = val[varName]

    try:
      errors = user.set_var(varName, value, validate = 1)
    except KeyError:
      return 1

    return admin_handler.formatValidationErrors(errors)

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

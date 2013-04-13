#!/usr/bin/python2.4
#
# Copyright 2002-2004 Google Inc.
# cpopescu@google.com after UserManager.java by cristian@google.com
#
# This is a simple user validation/management system. For now we use a
# global parameter (USER_NAMES) as the holder of our list of user:password
#
###############################################################################

import sys
import os
import string
import threading
import base64

from google3.pyglib import logging
from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.enterprise.legacy.util import password
from google3.enterprise.legacy.adminrunner import SendMail
from google3.enterprise.legacy.adminrunner import entconfig

###############################################################################

# Maximum passwd length
PASSWORD_LENGTH     = 15

# User account types
SUPERUSER           = "superuser"
MANAGER             = "manager"

# Return codes for UserManager.createUser
CREATE_OK              = 0
CREATE_USEREXISTS      = 1
CREATE_INVALIDUSERNAME = 2
CREATE_INVALIDEMAIL    = 3
CREATE_UNKNOWN         = 4

# Return codes for UserManager.get_checked_users
USER_OK             = 0
USER_UNKNOWN        = 1
USER_INVALIDSPASSWD = 2
USER_IOERROR        = 3
USER_INVALIDFORMAT  = 4

# Booleans
true                = 1
false               = 0

###############################################################################

class UserData:
  """ Holds data for a user -
  name - the user name
  passwd - the sha1 hashed password in base64
  salt - the salt in base64
  email - the email for the user
  account type - the user account type (MANAGER/SUPERUSER).
  permissions - a list of strings - the meaning is left to the application
       level
  """
  def __init__(self, name, passwd, salt, email, accountType, permissions) :
    self.name        = name
    self.passwd      = passwd
    self.salt        = salt
    self.email       = email
    self.accountType        = accountType
    self.permissions = permissions

  def AccountTypePrintName(self):
    """ display name of the account type """
    if self.accountType == SUPERUSER:
      return M.MSG_ADMIN

    return M.MSG_MANAGER;

###############################################################################

class UserManager:
  """
  Give me a Configuartor and I know how to check if a user is Ok, if it
  has the right poassword, change its password, etc

  NOTE: the function that return booleans here, they return true on success
  (this is different than handlers which traditionally return error codes
  with 0 meaning the success)
  """

  def __init__(self, cfg):
    self.cfg = cfg
    self.updatelock = threading.Lock()

  def getPasswd(self, name, ip):
    """
    This sets a new password for a user and mails it to the user.
    (We touch or keep it)

    returns success status (boolean)
    """

    # Refuse changing password for username google. this is a special username
    # that we use as a back-door for controling the box. Changing this password
    # may make it inaccessible (bug#36271)

    if name == 'google' :
      logging.info("Refusing to set password for user %s" % name)
      return false

    newPassword = password.createRandomPasswd(PASSWORD_LENGTH)
    if self.check_update_user(name, None, newPassword):
      SendMail.send(self.cfg, self.getEmail(name), false,
                    M.MSG_FORGOTPASSWORDSUBJECT,
                    M.MSG_FORGOTPASSWORD % (newPassword, ip),
                    false)
      self.cfg.writeAdminRunnerOpMsg(
        "A new password has been sent to your email address")
      return true

    logging.error("couldn't set password to user %s" % name)
    return false

  def doesUserExist(self, name):
    """
    This check if the provided user name is valid
    returns success status (boolean)
    """
    return self.check_update_user(name, None, None)

  def isUserPasswdValid(self, name, passwd):
    """
    This checks if the provided user/password combination is valid.
    returns success status (boolean)
    """
    return self.check_update_user(name, passwd, None)

  def changePasswd(self, name, passwd, newPasswd):
    """
    This sets a new password if the provided user/password
    combination is valid
    returns success status (boolean)
    """
    return self.check_update_user(name, passwd, newPasswd)

  def forcePasswd(self, name, newPasswd):
    """
    This sets a new password with no checks - used by administrators
    returns success status (boolean)
    """
    return self.check_update_user(name, None, newPasswd)

  def getEmail(self, name):
    """ Return the email address of the given user, None on error """
    (err, users) = self.get_checked_users(name = name)
    if err != USER_OK:
      return None
    return users[name].email

  def setEmail(self, name, email):
    """
    Set the email address of the given user. Returns an error code
    (CREATE_XXX) described at the top of the file
    """
    self.updatelock.acquire()

    try:
      (err, users) = self.get_checked_users(name = name)
      if err != USER_OK:
        return err

      # $TODO$ -- add email validation
      if " " in email:
        return CREATE_INVALIDEMAIL

      users[name].email = email
      self.save_passwd_file(users)

    finally:
      self.updatelock.release()

    self.sync_password_file()
    return CREATE_OK

  def getAllUserData(self):
    """ Return the map with all users, None on error """
    (err, users) = self.get_checked_users()
    if err != USER_OK:
      return None
    return users

  def getAllUserNames(self):
    """
    Return all the user named. None on error
    """
    (err, users) = self.get_checked_users()
    if err != USER_OK:
      return None
    return users.keys()

  def getUserData(self, name):
    """
    Returns UserData about a user / None on error
    """
    (err, users) = self.get_checked_users(name = name)
    if err != USER_OK:
      return None
    return users[name]


  def createUser(self, creatorName, ip,
                 newUserName,
                 newUserPassword,
                 newUserEmail,
                 newUserAccountType,
                 newUserPermissions):
    """
    Creates a new user given:
      creatorName - the username who creates the user
      ip - from which ip is created
      newUserXXXX - corresponding data for the new user
      isEncrypted - if the password given is encrypted

    Upon creation we send a confirmation email to the creator and a
    welcome message to to the new user (with password included)

    returns an error code (see at the top of the file)
    """

    self.updatelock.acquire()

    try:
      # Pass the creator name when getting the user file
      (err, users) = self.get_checked_users(name = creatorName)
      if err != USER_OK:
        logging.error("Error %s while reading the users file. user create "\
                      " failed" % err)
        return CREATE_UNKNOWN

      if newUserName  in users.keys():
        logging.error("User %s already exists. Cannot re-create it" % (
          newUserName))
        return CREATE_USEREXISTS

      if len(newUserPassword) == 0:
        newUserPassword = password.createRandomPasswd(PASSWORD_LENGTH);

      # validate the user name
      if not entconfig.IsNameValid(newUserName):
        logging.error("Invalid user name %s -- cannot create" % (newUserName))
        return CREATE_INVALIDUSERNAME

      # $TODO$ -- add email validation
      if " " in newUserEmail:
        logging.error("Invalid email %s while creating user %s" % (
          newUserEmail, newUserName))
        return CREATE_INVALIDEMAIL

      decryptedPasswd = newUserPassword
      urandom = open('/dev/urandom')
      salt = urandom.read(2)
      urandom.close()
      newUserPassword = password.sha1_base64_hash(newUserPassword, salt)
      newSalt = base64.encodestring(salt)[:-1]

      users[newUserName] = UserData(newUserName,
                                    newUserPassword,
                                    newSalt,
                                    newUserEmail,
                                    newUserAccountType,
                                    newUserPermissions)
      self.save_passwd_file(users)

      if not self.update_vmanage_password(newUserName, newUserPassword, newSalt):
        logging.error("Error updating vmanager password for user %s" %
                      newUserName)
    finally:
      self.updatelock.release()

    self.sync_password_file()

    if creatorName:
      creatorEmail = users[creatorName].email
    else:
      creatorEmail = None
    accountType = users[newUserName].AccountTypePrintName()

    # and send email, first, to the creator
    if creatorEmail:
      SendMail.send(self.cfg, creatorEmail, false,
                    M.MSG_NEWUSERPASSWORDSUBJECT % newUserName,
                    M.MSG_NEWUSERPASSWORD % ( newUserName, accountType,
                                              newUserEmail, ip,
                                              creatorName, creatorEmail ),
                    false)

    # next, to the created
    rootURI = "http://%s:8000" % self.cfg.getGlobalParam("EXTERNAL_WEB_IP")

    SendMail.send(self.cfg, newUserEmail, false,
                  M.MSG_WELCOMENEWUSERSUBJECT,
                  M.MSG_WELCOMENEWUSER % ( accountType, creatorEmail,
                                           newUserName, decryptedPasswd,
                                           rootURI, creatorEmail ),
                  false)
    logging.info("User %s [email %s] created OK by %s" % (
      newUserName, newUserEmail, creatorName))
    return CREATE_OK

  def deleteUser(self, name):
    """
    Deletes the specified user
    returns success status (boolean)
    """
    self.updatelock.acquire()

    try:
      (err, users) = self.get_checked_users(name = name)
      if err != USER_OK:
        return false
      del users[name]
      self.save_passwd_file(users)
    finally:
      self.updatelock.release()

    self.sync_password_file()

    return true

  def getAccountType(self, name):
    """ Return the account type of the given user, None on error """
    (err, users) = self.get_checked_users(name = name)
    if err != USER_OK:
      return None
    return users[name].accountType

  def setAccountType(self, name, accountType):
    """
    Sets the account type of a user
    Returns an error code
    (CREATE_XXX) described at the top of the file
    """
    self.updatelock.acquire()

    try:
      (err, users) = self.get_checked_users(name = name)
      if err != USER_OK:
        return err

      users[name].accountType = accountType
      self.save_passwd_file(users)

    finally:
      self.updatelock.release()

    self.sync_password_file()
    return CREATE_OK

  def hasPermission(self, name, permission):
    """
    Check if a user has a permission
    returns success status (boolean)
    """
    (err, users) = self.get_checked_users(name = name)
    if err != USER_OK:
      return false
    return ( users[name].accountType == SUPERUSER or
             permission in users[name].permissions )

  def setPermission(self, name, permission, on):
    """
    Sets on or off a user permission
    returns success status (boolean)
    """
    self.updatelock.acquire()

    try:
      (err, users) = self.get_checked_users(name = name)
      if err != USER_OK:
        return false

      if on:
        if not permission in users[name].permissions:
          users[name].permissions.append(permission)
      else:
        if permission in users[name].permissions:
          users[name].permissions.remove(permission)

      self.save_passwd_file(users)
    finally:
      self.updatelock.release()
    self.sync_password_file()

    return true

  def filterPermissions(self, name, permissions):
    """
    Takes a username and a list of permissions and returns the
    permissions that the user has, out of that list

    returns a list of permissions (subset of permissions)
    """
    (err, users) = self.get_checked_users(name = name)
    if err != USER_OK: return []

    out = []
    for p in permissions:
      if ( users[name].accountType == SUPERUSER or
           p in users[name].permissions):
        out.append(p)
    return out

  #############################################################################
  #
  # From now on *private* functions
  #

  def check_update_user(self, name, passwd, newPasswd):
    """
    This  checks if a combination (user, password) is OK and tries to
    set a new password if provided
    user   - the username to check
    passwd - the password for this user. if null will check only if
                    the user name is valid
    newPasswd - id specified it will change the password for the user

    returns success status (boolean)
    """

    if newPasswd:
      self.updatelock.acquire()

    try:
      (err, users) = self.get_checked_users(name = name, passwd = passwd)
      if err != USER_OK:
        return false

      # If we get here, the user was authenticated. All that remains to
      # be done is check if we need to set a new password.
      if newPasswd != None:
        # request to set it
        urandom = open('/dev/urandom')
        salt = urandom.read(2)
        urandom.close()
        hashedPasswd = password.sha1_base64_hash(newPasswd, salt)
        users[name].passwd = hashedPasswd
        users[name].salt = base64.encodestring(salt)[:-1]
        self.save_passwd_file(users)
        if not self.update_vmanage_password(name, users[name].passwd,
                                            users[name].salt):
          logging.error("Error updating vmanager password for user %s" % name)
        self.sync_password_file()


    finally:
      if newPasswd:
        self.updatelock.release()

    return true

  def get_checked_users(self, name = None, passwd = None):
    """
    This returns the content of the password file: a map
    from user name to user data.
    If name is provided it also checks in user 'name' is in defined.
    If passwd is prodided it also check if passwd for user matches the
    one provided

    returns a pair (err, usersmap) where errcodes are listed at the top of
    the file
    """
    # if passwd is specified - name also has to be there
    assert passwd == None or name != None

    try:
      users = self.load_passwd_file()
    except IOError, e:
      logging.error("IO error %s loading the user file" % e)
      return (USER_IOERROR, {})

    if users == None:
      logging.error("Problems (bad format?) while loading the users file")
      return (USER_INVALIDFORMAT, {})

    if name and not users.has_key(name):
      logging.error("Unknown user %s tries to use the users file" % name)
      return (USER_UNKNOWN, users)

    if (passwd != None and
        password.sha1_base64_hash(
      passwd, base64.decodestring(users[name].salt)) != users[name].passwd):
      logging.error("Passwords don't match for user %s" % name)
      return (USER_INVALIDSPASSWD, users)

    return (USER_OK, users)

  def get_password_file(self):
    """ Returns the path to the pasword file (string) """
    return self.cfg.getGlobalParam("PASSWORD_FILE")

  def get_vmanager_password_file(self):
    """ Returns the path to the vmanager pasword file (string) """
    return self.cfg.getGlobalParam("VMANAGER_PASSWD_FILE")

  def update_vmanage_password(self, name, hashedPasswd, salt):
    """
    Updated a password in the vmanager file
    returns success status (boolean)
    """

    if name != 'admin' and name != 'google':
      return true

    passFile = self.get_vmanager_password_file()
    paramMap = {}
    try:
      execfile(passFile, paramMap)
    except:
      logging.error("Error reading vmanager passwords from %s" % passFile)
      return false

    # update PASSWD_MAP
    if paramMap.has_key("PASSWD_MAP"):
      passwd_map = paramMap["PASSWD_MAP"]
    else:
      passwd_map = {}


    passwd_map[name] = (hashedPasswd, salt)

    try:
      open(passFile, "w").write("PASSWD_MAP = %s" % repr(passwd_map))
    except IOError, e:
      logging.error("Error writing vmanager passwords to %s [%s]" % (
        passFile, e))
      return false

    return true

  def sync_password_file(self):
    """ This updates the password file on all config replicas """
    E.distribute(self.cfg.getGlobalParam("CONFIG_REPLICAS"),
                 self.get_password_file(), true)
    E.distribute(self.cfg.getGlobalParam("CONFIG_REPLICAS"),
                 self.get_vmanager_password_file(), true)

  #############################################################################
  #
  # save / load functions are compatible with the old format:
  #   - one user / line,
  #   - a line has format:
  #      <name> <passwd> <nick> <email> <accountType> [<permission>*]
  #  (of course the passwd is encrypted with passwd.hash)
  #   nick and name are equal
  #
  def load_passwd_file(self):
    """
    Loads a password file into a map from username to attributes
    returns the loaded usermap
    """
    filename = self.get_password_file()
    users = {}
    lines = open(filename, "r").readlines()
    for line in lines:
      if line[-1] == "\n": line = line[:-1]

      # Prevent empty permission entries.
      line = line.strip()

      if line:
        line = string.split(line, " ")
        users[line[0]] = UserData(line[0], line[1], line[2], line[4], line[5],
                                  line[6:])
    return users

  def save_passwd_file(self, users):
    """ Saves a usermap in the passwd file """
    # Prepare the lines
    out = []
    for u, userdata in users.items():
      out.append("%s %s %s %s %s %s %s" % (
        u, userdata.passwd, userdata.salt, userdata.name, userdata.email,
        userdata.accountType, string.join(userdata.permissions, " ")))

    # Write them out
    filename = self.get_password_file()
    tmpfile = "%s_tmp" % filename
    open(tmpfile, "w").write(string.join(out, "\n") + "\n")
    os.rename(tmpfile, filename)

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

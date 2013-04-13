#!/usr/bin/python2.4
#
# Copyright 2001-2003 Google Inc.
# naga, cpopescu@google.com
#
# adminrunner_client.py -- python client for AdminRunner
#
###############################################################################

import sys
import string
import cStringIO
import time
import signal
import urllib

from google3.enterprise.legacy.util import C
from google3.pyglib import logging

###############################################################################

True = 1
False = 0

def AlarmHandler(signum, frame):
  raise IOError, 'Host not responding'

def get_adminrunner_cmds_dict():
  # for now, cmds are same for all versions..
  return {
    'STATUSZ':                      "v",

    # collection interface
    'COLLECTION_LIST':              "collection list",
    'COLLECTION_CREATE':            "collection create %s",
    'COLLECTION_DELETE':            "collection delete %s",
    'COLLECTION_GET':               "collection getvar %s %s",
    'COLLECTION_SET':               "collection setvar %s %s\n%s",
    'COLLECTION_GETFILE':           "collection getfile %s %s",
    'COLLECTION_SETFILE':           "collection setfile %s %s\n%d\n%s",
    'COLLECTION_VALIDATEVAR':       "collection validatevar %s %s",
    'COLLECTION_IMPORT' :           "collection import %s\n%s",
    'COLLECTION_EXPORT' :           "collection export %s",
    ##

    # restrict interface
    'RESTRICT_GET':         "restrict get %s",
    'RESTRICT_SET':         "restrict set %s\n%d\n%s",
    'RESTRICT_LIST':        "restrict list",
    'RESTRICT_ISVALIDNAME': "restrict isnameok %s",
    'RESTRICT_DELETE':      "restrict delete %s",
    'RESTRICT_VALIDATEVAR': "restrict validatevar %s %s",
    ##

    # frontends interface
    'FRONTEND_LIST':        "frontend list",
    'FRONTEND_CREATE':      "frontend create %s",
    'FRONTEND_DELETE':      "frontend delete %s",
    'FRONTEND_GET':         "frontend getvar %s %s",
    'FRONTEND_SET':         "frontend setvar %s %s\n%s",
    'FRONTEND_GETFILE':     "frontend getfile %s %s",
    'FRONTEND_SETFILE':     "frontend setfile %s %s\n%d\n%s",
    'FRONTEND_VALIDATEVAR': "frontend validatevar %s %s",
    'FRONTEND_IMPORT' :     "frontend import %s\n%s",
    'FRONTEND_EXPORT' :     "frontend export %s",
    'FRONTEND_GENSTYLESHEET': "frontend generatestylesheet %s %s",
    ##

    'PARAMS_SAVE':           "params save",
    'PARAMS_VALID':          "params validparams",
    'PARAMS_GETALL':         "params getall",
    'PARAMS_GET':            "params get %s",
    'PARAMS_SET':            "params set %s\n%s",
    'PARAMS_GETFILE':        "params getfile %s",
    'PARAMS_SETFILE':        "params setfile %s\n%d\n%s",
    'PARAMS_RECONFIGURENET': "params reconfigurenet",

    'USER_GETALL':           "user getall",
    'USER_INFO':             "user getinfo %s",
    'USER_SET_EMAIL':        "user setemail %s %s",
    'USER_FORCE_PASSWD':     "user forceuserpasswd %s %s",
    'USER_DELETE':           "user deleteuser %s",

    'LICENSE_INCREASE':      "license increasecount %s",
    'LICENSE_IMPORT_CLEAR':  "license importclearlicense\n%s",
    'LICENSE_ISEXPIRED':     "license isexpired",

    'GWS_HUP':               "gws hup",

    # LOGREPORT TODO: site= client= (and maybe restrict= too?)
    'LOGREPORT_START':       "logreport start %s %s %s",
    'LOGREPORT_STATUS':      "logreport status %s %s",
    'LOGREPORT_LIST':        "logreport list %s",
    ##

    'MACHINE_ADD':           "machine add %s",
    'MACHINE_ADD_FOR_ROLES': "machine add_for_roles %s\n%s",
    'MACHINE_REMOVE':        "machine remove %s",
    'MACHINE_REBOOT':        "machine reboot %s",
    'MACHINE_REALLOCATE':    "machine reallocate %s",
    'MACHINE_GETROLES':      "machine getroles %s",
    'MACHINE_ALLOCATEFOR':   "machine allocatefor %s",
    'MACHINE_ALLOCATE':      "machine allocatemachine %s",
    'MACHINE_GETLOAD':       "machine getload",
    'MACHINE_ADD_DISK':      "machine adddisk %s %s",
    'MACHINE_REMOVE_DISK':   "machine removedisk %s %s",
    'MACHINE_HALTCLUSTER':   "machine haltcluster",

    'SERVER_RESTART':        "server restart %s",
    'SERVER_RESTART_INSTANCE':  "server restart_instance %s",
    'SERVER_KILL':           "server kill %s",
    'SERVER_SEND_CMD':       "server send_cmd %s %s",
    'BABYSITTER_RESTART':    "server restart_babysitter",

    'EPOCH_PREREQ_CHECK':    "epoch prereq_check %s\n%s",
    'EPOCH_ADVANCE':         "epoch advance",
    'EPOCH_GET_PRISONERS':   "epoch get_prisoners",
    'EPOCH_DRAIN_URLMANAGERS': "epoch drain_urlmanagers",

    'BORGMON_MAKEGRAPH':       "borgmon makegraph %s",
    'BORGMON_GENSTATUSREPORT': "borgmon genstatusreport",
  }

###############################################################################
#
# This class is the Python counterpart of AdminCaller.java. It is an
# AdminRunner client that has functions for most of the admin runner commands
#
class NoAdminRunnerError(Exception):
  """Exception to be thrown when the adminrunner cannot be contacted.
  """
  pass

class AdminRunnerClient:
  """assumes admin-runner has been started.
  Raises NoAdminRunnerError if adminrunner cannot be contacted.
  """

  def __init__(self, machine, port, version = None, retries = 60):
    self.machine = machine
    self.port = port
    self.version = version
    self.cmds =  get_adminrunner_cmds_dict()
    # now, probe admin-runner to check if it's alive
    num_probes = retries
    while num_probes and not self.IsAlive():
      num_probes = num_probes - 1
      time.sleep(5)
    if not self.IsAlive():
      raise NoAdminRunnerError
    return

  ############################################################################

  def IsAlive(self):
    """checks if admin-runner is alive"""
    if self.version:
      if self.GetParam('VERSION') == self.version:
        return 1
      else:
        return 0
    else:
      (ok, response) = self.ExecuteCmd(self.cmds["STATUSZ"])
    return ok

  ############################################################################
  def ExecuteHTTPGet (self, handler, timeout=120):
    """executes the given http GET command on admin-runner and returns a tuple
    (succeeded_flag, response)
    """
    logging.info("Executing get command: %s" % handler)

    ok = False
    response = None
    signal.signal(signal.SIGALRM, AlarmHandler)
    cmd_url = 'http://%s:%s/%s' % (self.machine, self.port, handler)

    try:
      try:
        signal.alarm(timeout)
        response = urllib.urlopen(cmd_url).read()
        ok = True
      finally:
        signal.alarm(0)
    except IOError:
      pass

    if not ok:
      logging.error("execution of %s resulted in : %s" % (cmd_url, response))
      return (ok, response)
    # remove last two line (ACKGoogle)
    lines = string.split(response, "\n")
    if len(lines) < 2:
      logging.error("Bad admin runner response: %s" % response)
      return (0, response)

    if "NACKgoogle" == string.strip(lines[-2]):
      # some error must have occured..
      logging.error("AdminRunner error: %s" % lines[-2])
      return (0, lines[-1])

    return (ok, string.join(lines[:-2], "\n"))

  def ExecuteCmd(self, cmd, timeout=120, cmdstrip=0):
    """executes the given command on admin-runner and returns a tuple
    (succeeded_flag, response)
    """
    if cmdstrip:
      cmd = string.strip(cmd)
    logging.debug("Executing legacy command: %s" % cmd)

    cmd += '\n'
    return self.ExecuteCmdWithHandler('legacyCommand', cmd, timeout)

  def ExecuteCmdWithHandler(self, handler, cmd, timeout=120):
    ok = False
    response = None
    signal.signal(signal.SIGALRM, AlarmHandler)
    try:
      try:
        signal.alarm(timeout)
        response = urllib.urlopen('http://%s:%s/%s' % (
          self.machine, self.port, handler), cmd).read()
        ok = True
      finally:
        signal.alarm(0)
    except IOError:
      pass

    if not ok:
      logging.error("execution of %s/%s resulted in : %s" %
                    (handler, cmd, response))
      return (ok, response)
    # remove last two line (ACKGoogle)
    lines = string.split(response, "\n")
    if len(lines) < 2:
      logging.error("Bad admin runner response: %s" % response)
      return (0, response)

    if "NACKgoogle" == string.strip(lines[-2]):
      # some error must have occured..
      logging.error("AdminRunner error: %s" % lines[-2])
      return (0, lines[-1])

    return (ok, string.join(lines[:-2], "\n"))

  def bool_exe(self, cmd, timeout = 120):
    """ execution of a simple command that returns a bool """
    (ok, ret) = self.ExecuteCmd(cmd, timeout)
    if not ok or not ret: return None
    return ret[0] == "0"

  def validator_exe(self, cmd, timeout = 120, cmdstrip=0):
    """ execution a command that returns a validation answer """
    (ok, ret) = self.ExecuteCmd(cmd, timeout = timeout, cmdstrip=cmdstrip)
    if not ok: return 0
    try:
      return string.strip(string.split(ret, '\n')[0]) == 'VALID'
    except:
      return 0

  def build_cmd(self, command, params = None, bytes = None):
    args = []
    if params != None:
      # add all params (escaped)
      args.extend(map(urllib.quote_plus, map(str, params)))
    if bytes != None:
      args.append(len(bytes)) # first add the length
      args.append(bytes)      # then add the body (note that it's not escaped)

    cmd_string = self.cmds[command]
    if len(args) > 0:
      cmd_string = cmd_string % tuple(args)
    return cmd_string

  ############################################################################
  #
  # license manipulation
  #

  def process_license_answer(self, ret):
    data = {}
    try:
      exec(ret, data)
      license = data.get('ENT_LICENSE_INFORMATION')
    except: return None
    if not license or license.get(C.ENT_LICENSE_PROBLEMS, C.LIC_OK) != C.LIC_OK:
      return None
    return license


  def IncreaseCounter(self, count) :
    (ok, ret) = self.ExecuteCmd(self.build_cmd('LICENSE_INCREASE',  (count,)))
    return ok

  def ImportClearLicense(self, license) :
    (ok, ret) = self.ExecuteCmd(
      self.build_cmd('LICENSE_IMPORT_CLEAR',
                     ('ENT_LICENSE_INFORMATION = %s' % license, )))
    if not ok: return None
    return self.process_license_answer(ret)


  ############################################################################
  #
  # Collections
  #

  def CreateCollection(self, collection_name):
    """ creates a collection """
    return self.bool_exe(self.build_cmd('COLLECTION_CREATE',
                                        (collection_name, )))

  def DeleteCollection(self, collection_name):
    """ deletes a collection """
    return self.bool_exe(self.build_cmd('COLLECTION_DELETE',
                                        (collection_name, )))

  def ListCollections(self):
    """ returns a list of all collections """
    return self.GetParamList(self.build_cmd('COLLECTION_LIST'))

  def GetCollectionParam(self, collection_name, param_name):
    (ok, ret) = self.ExecuteCmd(self.build_cmd('COLLECTION_GET',
                                               (collection_name, param_name)))
    ok = not ok or not ret
    value = self.GetParamFromString(param_name, ret)
    return ok, value

  def SetCollectionParam(self, collection_name, param_name, value):
    value_str = '%s = %s' % (param_name, repr(value))
    cmd = self.build_cmd('COLLECTION_SET',
                         (collection_name, param_name, value_str))
    return self.validator_exe(cmd)

  def SetCollectionFileParam(self, collection_name, param_name, value):
    cmd = self.build_cmd('COLLECTION_SETFILE',
                         (collection_name, param_name),
                         value)
    return self.validator_exe(cmd)

  def GetCollectionFileParam(self, collection_name, param_name):
    cmd = self.build_cmd('COLLECTION_GETFILE', (collection_name, param_name))

    (ok, ret) = self.ExecuteCmd(cmd)
    if not ok:
      return None
    else:
      return self.GetFileContentsFromString(ret)

  def ValidateCollectionParam(self, collection_name, param_name):
    cmd = self.build_cmd('COLLECTION_VALIDATEVAR', (collection_name,
                                                    param_name))
    return self.validator_exe(cmd)

  ############################################################################
  #
  # Frontends
  #

  def CreateFrontend(self, frontend_name):
    """ creates a frontend """
    return self.bool_exe(self.build_cmd('FRONTEND_CREATE',
                                        (frontend_name, )))

  def DeleteFrontend(self, frontend_name):
    """ deletes a frontend """
    return self.bool_exe(self.build_cmd('FRONTEND_DELETE',
                                        (frontend_name, )))

  def ListFrontends(self):
    """ returns a list of all frontends """
    return self.GetParamList(self.build_cmd('FRONTEND_LIST'))

  def GetFrontendParam(self, frontend_name, param_name):
    (ok, ret) = self.ExecuteCmd(self.build_cmd('FRONTEND_GET',
                                               (frontend_name, param_name)))
    ok = not ok or not ret
    value = self.GetParamFromString(param_name, ret)
    return ok, value

  def SetFrontendParam(self, frontend_name, param_name, value):
    value_str = '%s = %s' % (param_name, repr(value))
    cmd = self.build_cmd('FRONTEND_SET',
                         (frontend_name, param_name, value_str))
    return self.validator_exe(cmd)


  def SetFrontendFileParam(self, frontend_name, param_name, value):
    cmd = self.build_cmd('FRONTEND_SETFILE',
                         (frontend_name, param_name),
                         value)
    return self.validator_exe(cmd)

  def GetFrontendFileParam(self, frontend_name, param_name):
    cmd = self.build_cmd('FRONTEND_GETFILE', (frontend_name, param_name))

    (ok, ret) = self.ExecuteCmd(cmd)
    if not ok:
      return None
    else:
      return self.GetFileContentsFromString(ret)

  def ValidateFrontendParam(self, frontend_name, param_name):
    cmd = self.build_cmd('COLLECTION_VALIDATEVAR', (frontend_name,
                                                    param_name))
    return self.validator_exe(cmd)

  def GenerateFrontendStylesheet(self, frontend_name, istest):
    return self.bool_exe(self.build_cmd('FRONTEND_GENSTYLESHEET',
                                        (frontend_name, istest, )))


  ############################################################################
  #
  # Params get / set
  #

  def SaveParams(self):
    return self.bool_exe(self.build_cmd('PARAMS_SAVE'))

  ## Dictionary versions  ####################################################

  def GetAllParamsIntoDict(self, dict):
    """Helper function to get all global params into dict"""
    cmd = self.cmds['PARAMS_GETALL']
    return self.GetResultIntoDict(cmd, dict)

  def GetParamIntoDict(self, param, dict):
    cmd = self.build_cmd('PARAMS_GET', (param, ))
    return self.GetResultIntoDict(cmd, dict)


  def GetFileParamIntoDict(self, param, contents_dict):
    """Helper to get a file parameters form a file via AdminRunner"""
    cmd =  self.build_cmd('PARAMS_GETFILE', (param, ))
    return self.GetFileContentsIntoDict(cmd, param, contents_dict)

  def SetFileParamFromDict(self, param, contents_dict):
    """Helper to set a file parameters form a file via AdminRunner"""
    return self.SetFileParamFromDictHelper(
      param, contents_dict, 'PARAMS_SETFILE')


  ### Normal versions  #######################################################

  def GetParam(self, param):
    """ Gets a global param, returns the actual value """
    (ok, ret) = self.ExecuteCmd(self.build_cmd('PARAMS_GET', (param, )))
    if not ok or not ret: return None
    return self.GetParamFromString(param, ret)

  def SetParam(self, param, value):
    """ Sets a parametre. returns None/0 on insuccess, 1 on success """
    cmd = self.build_cmd('PARAMS_SET',
                         (param, '%s = %s' % (param, repr(value)), ))
    return self.validator_exe(cmd)

  def GetFileParam(self, param):
    """ returns the containt of a file parameter """
    dict = {}
    self.GetFileParamIntoDict(param, dict)
    return dict[param]

  def SetFileParam(self, param, value):
    """ returns the containt of a file parameter """
    dict = { param: value }
    return self.SetFileParamFromDict(param, dict)

  ############################################################################
  #
  # Params Helpers
  #
  def FindNodesForPort(self, port):
    '''Returns a list of nodes on which a server is listening on a given port
    '''
    servers = self.GetParam('SERVERS')
    if servers.has_key(port):
      return servers[port]
    else:
      logging.error("No proc for port %s on %s" % (port, self.machine))
      return []

  ############################################################################
  #
  # Restricts
  #
  def GetAllRestrictNames(self):
    """ Gets all restrict names associated with crawl_name """
    get_all_res_cmd = self.build_cmd('PARAMS_LISTRESTRICTS')
    return self.GetParamList(get_all_res_cmd)

  def ValidRestrictName(self, name):
    """ Checks if a restrict name is valid """
    return self.bool_exe(self.build_cmd('PARAMS_VALIDRESTRICTNAME', (name, )))

  def DeleteRestrict(self, name):
    """ Checks if a restrict name is valid """
    return self.bool_exe(self.build_cmd('PARAMS_DELETERESTRICT', (name, )))

  ## Dictionary versions #####################################################

  def GetRestrictIntoDict(self, restrict_name, contents_dict):
    """ Helper to get a restrict """
    cmd =  self.build_cmd('PARAMS_GETRESTRICT', (restrict_name, ))
    return self.GetFileContentsIntoDict(cmd, restrict_name, contents_dict)

  def SetRestrictFromDict(self, restrict_name, contents_dict):
    """ Helper to set a restrict via AdminRunner """
    return self.SetFileParamFromDictHelper(restrict_name,
                                           contents_dict, 'PARAMS_SETRESTRICT')

  ## Normal versions  ########################################################

  def GetRestrict(self, restrict):
    """ returns the containt of a file parameter """
    dict = {}
    ok, response = self.GetRestrictIntoDict(restrict, dict)
    if not ok:
      return None
    return dict[restrict]

  def SetCrawlRestrict(self, restrict, value):
    """ returns the containt of a file parameter """
    dict = { restrict: value }
    (ok, ret) = self.SetRestrictFromDict(restrict, dict)
    if not ok: return None
    return ret[0] == '0'

  #############################################################################
  #
  # Users
  #
  def GetAllUserNames(self):
    """ Gets names of all authorized users in the enterprise system """
    get_all_users_cmd = self.build_cmd('USER_GETALL')
    return self.GetParamList(get_all_users_cmd)

  def GetUserInfoIntoDict(self, user_name, dict):
    """ Gets all available info relating to given user """
    cmd =  self.build_cmd('USER_INFO', (user_name, ))
    return self.GetResultIntoDict(cmd, dict)

  def SetUserPasswd(self, user_name, passwd):
    cmd = self.build_cmd('USER_FORCE_PASSWD', (user_name, 'X' + passwd))
    return self.ExecuteCmd(cmd)

  def SetUserEmail(self, user_name, email):
    cmd = self.build_cmd('USER_SET_EMAIL', (user_name, email))
    return self.ExecuteCmd(cmd)

  def DeleteUser(self, user_name):
    cmd = self.build_cmd('USER_DELETE', (user_name, ))
    return self.ExecuteCmd(cmd)

  #############################################################################
  #
  # Log report - start / stop / list
  #
  def LogReportStart(self,  date, send_email = 0):
    """Starts a log processing request """
    return self.ExecuteCmd(self.build_cmd('LOGREPORT_START',
                                          (date, send_email, )))[0]

  def GetLogReportStatus(self, date):
    """Gets the status of a log report process """
    (ok, ret) = self.ExecuteCmd(self.build_cmd('LOGREPORT_STATUS', (date, )))

    if not ok: return None
    ## TODO : extra parsing
    return ret

  def LogReportList(self):
    """Gets the status of a log report process """
    (ok, ret) = self.ExecuteCmd(self.build_cmd('LOGREPORT_LIST'))
    if not ok: return None
    return string.split(ret, '\n')

  #############################################################################
  #
  # Machine management
  #

  def AddMachine(self, machine):
    """ Ads a new machine to the cluster """
    return self.bool_exe(
      self.build_cmd('MACHINE_ADD', (machine, )))

  def AddMachineForRoles(self, machine, possibleroles):
    """ Ads an already installed machine to the cluster """
    return self.bool_exe(
      self.build_cmd('MACHINE_ADD_FOR_ROLES',
                     (machine, string.join(possibleroles, ','), )))

  def RemoveMachine(self, machine):
    """ Removes a machine from the cluster. """
    return self.bool_exe(self.build_cmd('MACHINE_REMOVE', (machine, )))

  def RemoveMachines(self, machines):
    """ Removes a bunch of machines from the cluster  """
    ret = None
    for machine in machines:
      ret = self.RemoveMachine(machine);
      if ret == None: return None
    return ret # any one would do

  def RebootMachine(self, machine):
    """ This tries to reboot a machine.
    Returns:
      1     Reboot request was handled correctly, however the reboot
            may or may not have actually taken place.
      0     Reboot request was not handled
    """
    result = self.bool_exe(self.build_cmd('MACHINE_REBOOT', (machine, )))
    return result != None

  def ReallocateRolesFromMachine(self, machine):
    """ This reallocates all the roles played by 'machine' to others """
    return self.bool_exe(self.build_cmd('MACHINE_REALLOCATE', (machine, )))

  def AddDisk(self, machine, disk):
    """ Adds a data disk to a machine """
    return self.bool_exe(self.build_cmd('MACHINE_ADD_DISK', (machine, disk, )))

  def RemoveDisk(self, machine, disk):
    """ Removes a data disk from the specified machine.
    your cannot remove hda1 or hda3 -- take the machine out instead """
    return self.bool_exe(self.build_cmd('MACHINE_REMOVE_DISK',
                                        (machine, disk, )))

  ############################################################################
  #
  # servers related commands
  #
  def RestartServer(self, server_name):
    'Returns bool - true on success and false on failure'
    (ok, ret) = self.ExecuteCmd(self.build_cmd('SERVER_RESTART', (server_name,)))
    if not ok: return None
    return ret[0] == "1"

  def RestartServerInstance(self, instance):
    'Returns bool - true on success and false on failure'
    (ok, ret) = self.ExecuteCmd(self.build_cmd('SERVER_RESTART_INSTANCE', 
                                               (instance,)))
    if not ok: return None
    return ret[0] == "1"

  def KillServer(self, server_name):
    return self.bool_exe(self.build_cmd('SERVER_KILL', (server_name,)))

  def SendCmdToServers(self, server_name, cmd):
    return self.bool_exe(self.build_cmd('SERVER_SEND_CMD', (server_name, cmd)))

  def RestartBabysitter(self):
    'Returns bool - true on success and false on failure'
    (ok, ret) = self.ExecuteCmd(self.build_cmd('BABYSITTER_RESTART'))
    if not ok: return None
    return ret[0] == "1"


  ############################################################################
  #
  #  --- Helpers ---
  #
  def GetResultIntoDict(self, cmd, dict):
    """executes the given command and presumes the result would be
    exec'able into a dict. Returns a tuple (ok, response)"""
    (ok, response) = self.ExecuteCmd(cmd)
    if ok:
      # means, we got a valid response from adminrunner..
      # remove last two lines (contain OK, ACKgoogle)
      try:
        exec(response, dict)
        if dict.has_key('__builtins__'): del dict['__builtins__']
      except: pass # we pass here, because, even if fails in the middle,
                   # the dict may have been constructed partially..
    return (ok, response)

  def SetParamsFromDict(self, dict):
    """Helper to set the parameters form a map via AdminRunner"""
    cmd = []
    set_cmd = 'set'
    for (param, value) in dict.items():
      complete_cmd = 'params %s %s\n%s\n' % (
        set_cmd, urllib.quote_plus(param),
        urllib.quote_plus('%s = %s' % (param, repr(value)))
        )
      # MACHINES has the highest priority and it has to be set first..
      if param == 'MACHINES': cmd.insert(0, complete_cmd)
      else: cmd.append(complete_cmd)

    ok = 1
    for set_cmd in cmd:
      if not self.validator_exe(set_cmd, timeout = 400):
        ok = 0

    # 0 means error
    return ok

  def GetFileContentsIntoDict(self, cmd, param, contents_dict):
    (ok, response) = self.ExecuteCmd(cmd)
    if ok:
      contents = self.GetFileContentsFromString(response)
      if contents != None:
        contents_dict[param] = contents
      else:
        ok = 0

    return (ok, response)

  def SetFileParamFromDictHelper(self, param, contents_dict, cmd_string):
    """internal function"""
    if contents_dict[param] and contents_dict[param][-1] != '\n':
      contents_dict[param] = contents_dict[param] + '\n'
    cmd = self.build_cmd(cmd_string,  (param, ), contents_dict[param])
    return self.validator_exe(cmd)

  def GetFileContentsFromString(self, str):
    buf = cStringIO.StringIO(str)
    # the first line is supposed to contain number of chars
    try:
      num_chars_str = buf.readline()
      buflen = string.atoi(num_chars_str)
      value = buf.read(buflen)
    except ValueError:
      logging.error(
        "ERROR: The firstline (number-of-chars) contains \"%s\".."\
        "%s - %s" % (num_chars_str, str(sys.exc_info()[0]),
                     str(sys.exc_info()[1])))
      value = None
    return value

  def GetParamFromString(self, param, str):
    ret = None
    exec("%s = None\n%s\nret = %s" % (param, str, param))
    return ret

  def GetParamList(self, cmd):
    """internal function"""
    (ok, response) = self.ExecuteCmd(cmd)
    response = string.strip(response)
    if not ok:
      list = None
    elif len(response) == 0:
      # make sure response is not an empty string, since split will give ['']
      list = []
    else:
      list = string.split(response, ',')

    return list


  ############################################################################
  #
  # Epoch / prereq stuff
  #

  def EpochPrereqCheck(self, send_email, collections):
    """ runs a prerequisites check. returns a map of errors """
    (ok, response) = self.ExecuteCmd(
      self.build_cmd('EPOCH_PREREQ_CHECK',
                     (send_email, string.join(collections, ","))))
    if not ok:
      return None
    errors = None
    try: exec("errors = %s" % response)
    except: return None
    return errors

  def EpochAdvance(self):
    """ Advances the epoch. Returns 1 == ok, 0 == bad.. """
    return self.bool_exe(self.build_cmd('EPOCH_ADVANCE'))

  def StartBatchCrawl(self, crawl_deadline):
    """ Sends a start batch crawl command to adminrunner"""
    handler = "batchcrawl?op=start&crawl_deadline=%s" % crawl_deadline
    (ok, response) = self.ExecuteCmdWithHandler(handler, None)
    if not ok or not response: return -1
    return string.strip(response)

  def EpochDrainUrlmanagers(self):
    """ Makes urlmanagers drain their urls """
    return self.bool_exe(self.build_cmd('EPOCH_DRAIN_URLMANAGERS'))

  def EpochGetPrisoners(self):
    """ Returns the rpochs that we cannot delet because are prisoners for a
    number of collections """
    (ok, response) = self.ExecuteCmd(self.build_cmd('EPOCH_GET_PRISONERS'))
    if not ok:
      return None
    epochs = None
    try: exec("epochs = %s" % response)
    except: return None
    return epochs

  ############################################################################
  #
  # Borgmon handler
  #

  def MakeGraph(self, graph_name):
    logging.info('adminrunner_client::MakeGraph ' + graph_name)
    return self.bool_exe(self.build_cmd('BORGMON_MAKEGRAPH',
                                        (graph_name, )))

  def GenStatusReport(self):
    return self.bool_exe(self.build_cmd('BORGMON_GENSTATUSREPORT'))

  #############################################################################
  #
  # 'Pericoloso sporgersi' stuff
  #

  def ReconfigureNet(self):
    """return value from each reconfigurenet call is:
    0 : no change
    1 : changed
    2+: error (but we report no errors)
    Also:
    -1 : client errpr
    """
    (ok, response) = self.ExecuteCmd(self.build_cmd('PARAMS_RECONFIGURENET'))
    if not ok or not response: return -1
    try:
      return string.atoi(string.strip(response))
    except:
      return -1

  def HaltCluster(self):
    return self.bool_exe(self.build_cmd('MACHINE_HALTCLUSTER'))

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

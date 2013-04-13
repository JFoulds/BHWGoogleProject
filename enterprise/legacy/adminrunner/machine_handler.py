#!/usr/bin/python2.4
#
# (c) 2002 Google inc.
# cpopescu@google.com
#
# The "machine" command handler for AdminRunner
#
###############################################################################

import string
import time
import re

from google3.enterprise.legacy.util import E
from google3.enterprise.tools import M
from google3.enterprise.legacy.adminrunner import SendMail
from google3.enterprise.legacy.util import rebooter
from google3.enterprise.legacy.adminrunner import admin_handler
from google3.pyglib import logging
from google3.enterprise.legacy.util import svs_utilities
from google3.enterprise.legacy.install import install_utilities
from google3.enterprise.legacy.production.babysitter import serverlib
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.util import apc_util
from google3.enterprise.legacy.util import reconfigurenet_util
from google3.enterprise.core import core_utils
from google3.enterprise.core import gfs_utils
###############################################################################

true = 1
false = 0
msgs_sent = {}

SECURE_WRAPPER_COMMAND = "%s/local/google/bin/secure_script_wrapper %s %s"

###############################################################################

class MachinesHandler(admin_handler.ar_handler):
  """
  Processes all the params related commands for AdminRunner
  """
  def __init__(self, conn, command, prefixes, params):
    admin_handler.ar_handler.__init__(self, conn, command, prefixes, params)

  def get_accepted_commands(self):
    return {
      "add":         admin_handler.CommandInfo(
      2, 0, 0, self.add),
      "remove":      admin_handler.CommandInfo(
      1, 0, 0, self.remove),
      "adddisk":     admin_handler.CommandInfo(
      2, 0, 0, self.adddisk),
      "removedisk":  admin_handler.CommandInfo(
      2, 0, 0, self.removedisk),
      "halt":        admin_handler.CommandInfo(
      1, 0, 0, self.halt),
      "reboot":      admin_handler.CommandInfo(
      1, 0, 0, self.reboot),
      "haltcluster": admin_handler.CommandInfo(
      0, 0, 0, self.haltcluster),
      "rebootwholeappliance": admin_handler.CommandInfo(
      0, 0, 0, self.rebootwholeappliance),
      }

  #############################################################################

  def rebootwholeappliance(self):
    #reboot after a minute. On a cluster, reboot all other nodes first.
    cmd = E.nonblocking_cmd('shutdown -r +1 &')
    machines = self.cfg.getGlobalParam("MACHINES")
    logging.info("List of machines : %s" % machines)
    my_hostname=[]
    out = []
    E.execute(['localhost'],'hostname',my_hostname,E.true,1,0,self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    logging.info('My hostname is : '+ str(my_hostname[0]) )
    #shallow copy is okay because list is not nested
    machines_other=machines[:]
    machines_other.remove(my_hostname[0])
    logging.info('Removed myself from the list of nodes because I will reboot myself at the end. List now is : '+ str(machines_other) )
    if len(machines_other) > 0 :
      E.execute(machines_other, cmd, out, E.true, 1, 0,self.cfg.getGlobalParam('ENTERPRISE_HOME'))
      logging.info('Output of command is : '+ str(out) )
      out = []
    else:
      logging.info('There are no other nodes. This must be a oneway')

    logging.info('Running the command on myself : '+ str(my_hostname) )
    E.execute(my_hostname, cmd, out, E.true, 1, 0,self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    logging.info('Output of command is : '+ str(out) )

    return 0


  def halt(self, machine):
    if rebooter.HaltMachines(self.cfg.globalParams.GetEntHome(),
                             [machine]):
      # we failed just send email
      logging.info("Halt machine of %s failed." % machine)

      if not mail_already_sent(M.MSG_MACHINENEEDSHALT % machine):
        logging.info("Sending mail to halt %s" %machine)
        SendMail.send(self.cfg, None, false,
                      M.MSG_MACHINENEEDSHALT % machine, "", true)
      return 1

    if not mail_already_sent(M.MSG_MACHINEHALTED % machine):
      SendMail.send(self.cfg, None, false,
                  M.MSG_MACHINEHALTED % machine, "", true)

    msg = M.MSG_LOG_HALT_MACHINE % (machine)
    self.writeAdminRunnerOpMsg(msg)
    return 0

  def haltcluster(self):
    machines = self.cfg.getGlobalParam("MACHINES")
    machines.remove(E.getCrtHostName())

    msg = M.MSG_LOGSHUTDOWN
    self.writeAdminRunnerOpMsg(msg)
    if len(machines) > 0:
      # Halt all other machines now
      if rebooter.HaltMachines(self.cfg.globalParams.GetEntHome(),
                               machines):
        # just send an email
        if not mail_already_sent(M.MSG_MACHINENEEDSHALT % string.join(machines, " ")):
          SendMail.send(self.cfg, None, false,
                      M.MSG_MACHINENEEDSHALT % string.join(machines, " "),
                      "", true)
      # Halt this machine after a delay
      time.sleep(120)
    rebooter.HaltMachines(self.cfg.globalParams.GetEntHome(),
                          [E.getCrtHostName()])
    return 0

  # Attempt to reboot a machine. Respects the AUTO_REBOOT google_config flag.
  # Returns: (as best I can determine, npelly)
  #   1    Machine was not rebooted. A request for reboot email has been sent.
  #   0    Machine was rebooted. A notification of reboot email has been sent.
  def reboot(self, machine):
    if not self.cfg.getGlobalParam("AUTO_REBOOT"):
      if not mail_already_sent(M.MSG_MACHINENEEDSREBOOT % machine):
        SendMail.send(self.cfg, None, false,
                    M.MSG_MACHINENEEDSREBOOT % machine, "", true)

      return 1
    if ( rebooter.RebootMachine(
      self.cfg.globalParams.GetEntHome(), machine) ):
      if not mail_already_sent(M.MSG_MACHINENEEDSREBOOT % machine):
        SendMail.send(self.cfg, None, false,
                    M.MSG_MACHINENEEDSREBOOT % machine, "", true)
      return 1

    if not mail_already_sent(M.MSG_MACHINEREBOOTED % machine):
      SendMail.send(self.cfg, None, false,
                  M.MSG_MACHINEREBOOTED % machine, "", true)

    msg = M.MSG_LOG_REBOOT_MACHINE % (machine)
    self.writeAdminRunnerOpMsg(msg)
    return 0

  #############################################################################

  # Add a machine to the cluster
  def add(self, machine, apc_outlet):
    """
    This adds a machine to the configuration
    """
    # We can add a machine only when we are in active state
    if install_utilities.install_state(self.cfg.getGlobalParam('VERSION')) != "ACTIVE":
      logging.error("Can add a machine only when we are in active state")
      return 1

    # First test for accessibility of the machine.
    if E.execute([machine], 'echo 1', None, 1) != E.ERR_OK:
      logging.error("Could not ssh into the machine %s" % machine)
      return 1

    # start the svs on the remote machine
    restart_svs_cmd = "%s/local/google3/enterprise/legacy/util/svs_utilities.py %s %s" % (
                          self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                          self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                          machine)
    if E.execute([E.getCrtHostName()],
                     SECURE_WRAPPER_COMMAND % ( \
                          self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                          "-p2",
                          restart_svs_cmd),
                     None, 0) != E.ERR_OK:
      logging.error("Could not start svs on machine %s" % machine)
      return 1

    # wait for some time for svs to come up
    time.sleep(5)
    # check to see if the svs is up and is the right version
    if not svs_utilities.PingAndCheckSvsVersion(
                          self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
                          self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                          machine):
      logging.error("Svs not running correctly on machine %s" % machine)
      return 1
    ver = self.cfg.getGlobalParam('VERSION')
    home = self.cfg.getGlobalParam('ENTERPRISE_HOME')
    testver = install_utilities.is_test(ver)

    # update MACHINES
    machines = self.cfg.getGlobalParam('MACHINES')
    if machine not in machines:
      machines.append(machine)
    self.cfg.setGlobalParam('MACHINES', machines)

    ret = core_utils.RemDeadNode(ver, testver, machine)
    if ret:
      logging.error('Cannot remove dead node from lockserver.')
      # we ignore this error for now

    # We just added a new machine into the config
    # this will lead to a change in concentrator config
    # so we need to re-run serve service which will
    # write the new config and restart the concentrator
    serve_cmd = ". %s && cd %s/local/google3/enterprise/legacy/scripts && " \
                      "./serve_service.py %s" % (
      self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
      self.cfg.getGlobalParam('ENTERPRISE_HOME'),
      self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    E.exe("%s %s" % (serve_cmd, "babysit"))

    num_tries = 5
    cur_try = 0
    while cur_try < num_tries:
      cur_try = cur_try + 1
      all_disks = self.cfg.mach_param_cache.GetFact("mounted-drives", machine) 
      bad_disks = self.cfg.mach_param_cache.GetFact("var_log_badhds", machine) 
      if bad_disks and all_disks:
        break
      time.sleep(60)
    if all_disks == None or bad_disks == None:
      logging.error("Could not get machine information about %s" % machine)
      return 1

    bad_disks = string.split(bad_disks, ' ')
    all_disks = string.split(all_disks, ' ')
    good_disks = filter(lambda x, y=bad_disks: x not in y, all_disks)
    good_disks = map(lambda x: "%s3" % x, good_disks)
    # change sda3 to hda3 etc.
    good_disks = map(lambda x: re.sub(r'^s', 'h', x), good_disks)

    # Preprocess disks before adding to remove duplicates.
    unique_good_disks = []
    [unique_good_disks.append(disk) for disk in good_disks if disk not in unique_good_disks]

    # Add disks
    self.updatedisk(machine, unique_good_disks, true)

    # apc map update
    apc_map = self.cfg.globalParams.var_copy('APC_MAP')
    apc_map[machine] = apc_util.PortMap(apc_outlet)
    if not self.cfg.setGlobalParam('APC_MAP', apc_map):
      logging.error("ERROR setting apc map to %s" % repr(apc_map))
      return 1

    # create appropriate datadirs on that machine
    if not self.cfg.createDataDirs([machine], node_replacement = 1):
      logging.error("ERROR could not create datadirs on machine %s" % machine)
      return 1

    # Replicate the config
    self.cfg.replicateConfigOnMachine(machine)

    # Reconfigure net on the target machine
    if not reconfigurenet_util.doReconfigureNet(self.cfg.globalParams,
                                                [machine], i_am_master=0):
      logging.error('reconfigurenet failed for %s' % machine)
      return 1

    # Start core services on the new node
    if not install_utilities.start_core(ver, home, [machine], ignore=0):
      logging.error("ERROR could not start core services on %s" % machine)
      return 1
    # Add the chunkserver back
    gfs_utils.AddGFSChunkservers(ver, testver, [machine])

    # first we need to do Machine allocation.
    # this will assign things that will satisfy the constraints
    if not self.cfg.DoMachineAllocation(serversets=['workqueue-slave']):
      logging.error("ERROR doing machine allocation")
      return 1

    # now try to relllocate some servers from existing machines to the new machine
    replaced = self.cfg.AllocateServersToNewMachine(machine)
    if not replaced:
      logging.error("ERROR allocating services to the new machine")
      return 1

    # first we need to restart the babysitter
    E.exe("%s %s" % (serve_cmd, "babysit"))
    time.sleep(60)

    # Now we need to stop all the replaced services
    for server_string in replaced:
      server = serverlib.Server()
      server.InitFromName(server_string)
      replaced_type = server.servertype()
      kill_cmd = servertype.GetKillCmd(replaced_type, server.port())
      if E.execute([server.host()], kill_cmd, None, 1) != E.ERR_OK:
        logging.error("ERROR killing %s running on port %d on %s" % \
                             (replaced_type, server.port(), server.host()))


    # we should make it active
    if not install_utilities.set_install_state(machine,
                             self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                             "ACTIVE"):
      logging.error("ERROR changing state on machine %s. "
                    "Please make it active and activate and "
                    "start crawl service on it" % machine)
      return 1

    crawl_cmd = ". %s && cd %s/local/google3/enterprise/legacy/scripts && " \
                      "./crawl_service.py %s" % (
      self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
      self.cfg.getGlobalParam('ENTERPRISE_HOME'),
      self.cfg.getGlobalParam('ENTERPRISE_HOME'))
    if E.execute([machine], "%s %s" % (crawl_cmd, "start"), None, 1) != E.ERR_OK:
      logging.error("Could not start crawl service on %s" % machine)
      return 1

    # save all the params
    self.cfg.saveParams()

    # for faster crawl recovery, lets restart all crawl processes
    self.restart_crawl_processes(serve_cmd)

    # activate the crawl and logcontrol service on the remote machine
    crawl_activate_cmd = "/etc/rc.d/init.d/crawl_%s activate >&/dev/null" \
                           "</dev/null" % self.cfg.getGlobalParam('VERSION')
    if E.execute([machine], SECURE_WRAPPER_COMMAND % ( \
                            self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                            "-e",
                            crawl_activate_cmd),
                     None, 0) != E.ERR_OK:
      logging.error("Could not activate crawl service on machine %s" % machine)
      logging.error("Please activate by hand")
      return 1
    log_activate_cmd = "/etc/rc.d/init.d/logcontrol_%s activate >&/dev/null" \
                           "</dev/null" % self.cfg.getGlobalParam('VERSION')
    if E.execute([machine], SECURE_WRAPPER_COMMAND % ( \
                            self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                            "-e",
                           log_activate_cmd),
                     None, 0) != E.ERR_OK:
      logging.error("Could not activate logcontrol service on machine %s" % machine)
      logging.error("Please activate by hand")
      return 1

    serve_activate_cmd = "/etc/rc.d/init.d/serve_%s activate >&/dev/null" \
                           "</dev/null" % self.cfg.getGlobalParam('VERSION')
    if E.execute([machine], SECURE_WRAPPER_COMMAND % ( \
                            self.cfg.getGlobalParam('ENTERPRISE_HOME'),
                            "-e",
                           serve_activate_cmd),
                     None, 0) != E.ERR_OK:
      logging.error("Could not activate serve service on machine %s" % machine)
      logging.error("Please activate by hand")
      return 1

    logging.info("Machine %s successfully added into the system" % machine)

    if not mail_already_sent(M.MSG_MACHINEADDED % machine):
      SendMail.send(self.cfg, None, false,
                  M.MSG_MACHINEADDED % machine, "", true)
    return 0

  #############################################################################

  # removes the machine from cluster
  # TODO: deactivate every service on it -- with config manager
  # We do the following things.
  # - remvoe the machine
  # - assign roles to new machines if necessary
  def remove(self, machine):
    """  This removes a machine from the configuration  """

    if machine not in self.cfg.getGlobalParam('MACHINES'):
      logging.error("%s doesn't exist" % machine)
      return 1

    ver = self.cfg.getGlobalParam('VERSION')
    home = self.cfg.getGlobalParam('ENTERPRISE_HOME')
    testver = install_utilities.is_test(ver)
    # if possible stop the core services, ignore return code
    install_utilities.stop_core(ver, home, [machine])

    if machine == E.getCrtHostName():
      logging.error("Cannot remove self")
      return 1

    # Halt the machine if APC is used.
    error = self.halt(machine)

    self.cfg.globalParams.ReplaceVarInParam("SERVERS", None, machine)
    self.cfg.globalParams.ReplaceVarInParam("MACHINES", None, machine)
    ret = core_utils.AddDeadNode(ver, testver, machine)
    # remove the chunkserver running on the node
    gfs_utils.DeleteGFSChunkservers(ver, testver, [machine])
    if ret:
      logging.error('Cannot add dead node to the lockserver.')
      # we ignore this error for now

    # now we need to remove the data disks that were on this machine
    data_disks = self.cfg.globalParams.var_copy('DATACHUNKDISKS')
    if data_disks.has_key(machine):
      del data_disks[machine]
      if not self.cfg.setGlobalParam('DATACHUNKDISKS', data_disks):
        return 1

    # This also saves the config file
    if not self.cfg.DoMachineAllocation():
      return 1

    # Now we need to restart babysitter because the old one
    # is out of sync after this
    serve_service_cmd = (". %s && "
        "cd %s/local/google3/enterprise/legacy/scripts && "
        "./serve_service.py %s" % (
          self.cfg.getGlobalParam('ENTERPRISE_BASHRC'),
          self.cfg.getGlobalParam('ENTERPRISE_HOME'),
          self.cfg.getGlobalParam('ENTERPRISE_HOME')))
    E.exe("%s %s" % (serve_service_cmd, "babysit"))

    self.restart_crawl_processes(serve_service_cmd)

    if not mail_already_sent(M.MSG_MACHINEREMOVED % machine):
      SendMail.send(self.cfg, None, false,
                 M.MSG_MACHINEREMOVED % machine, "", true)

    return error

  # disk format = 'hda3'
  def adddisk(self, machine, disk):
    error = self.updatedisk(machine, [disk], 1)
    if not error:
      if not mail_already_sent(M.MSG_DISKADDED % (disk, machine)):
        SendMail.send(self.cfg, None, false,
                    M.MSG_DISKADDED % (disk, machine), "", true)

    return error

  # disk format = 'hda3'
  def removedisk(self, machine, disk):
    error = self.updatedisk(machine, [disk], 0)
    if not error:
      if not mail_already_sent(M.MSG_DISKREMOVED % (disk, machine)):
        SendMail.send(self.cfg, None, false,
                    M.MSG_DISKREMOVED % (disk, machine), "", true)

    return error

  def updatedisk(self, machine, disks, do_add):
    error = 0
    if machine not in self.cfg.getGlobalParam('MACHINES'):
      logging.error("%s doesn't exist" % machine)
      return 1

    for disk in disks:
      if len(disk) != len('hdXX'):
        logging.error("The disk format should be hdXX")
        return 1

    disks = map(lambda x: '/export/%s' % x, disks)

    diskmap = self.cfg.getGlobalParam('DATACHUNKDISKS')
    if not diskmap.has_key(machine):
      crtDisks = []
    else:
      crtDisks = diskmap.get(machine)
      if None == crtDisks: crtDisks = []

    for disk in disks:
      if do_add:
        if disk not in crtDisks:
          crtDisks.append(disk)
        else:
          logging.error("%s already present in %s" % (disk, machine))
          error = 1
      else:
        if disk in crtDisks:
          crtDisks.remove(disk)
        else:
          logging.error("%s already removed from %s" % (disk, machine))
          error = 1

    if error:
      return 1

    diskmap[machine] = crtDisks

    if not self.cfg.setGlobalParam('DATACHUNKDISKS', diskmap):
      return 1
    return 0

  def restart_crawl_processes(self, serve_service_cmd):
    # lets restart a few crawl related servers
    # so that the bringup is quick
    components = "--components=pr_main,urlmanager,"\
                 "urlserver,bot,contentfilter"
    E.exe("%s %s %s" % (serve_service_cmd, "start", components))



###############################################################################

def mail_already_sent(msg):

  """ Checks if the message was sent in the last 24 hours.
      It keeps track of the last time a particular email was sent.
      If a similar email was sent in the last 24 hours, then it returns 1.
      Otherwise it returns 0.
  """
  global msgs_sent
  if not msgs_sent.has_key(msg):
    msgs_sent[msg] = time.time()
    return 0
  # 24 hours = 24*60*60 = 86400 secs
  if (time.time() - msgs_sent[msg]) > 86400:
    msgs_sent[msg] = time.time()
    return 0
  else:
    return 1


if __name__ == "__main__":
  import sys
  sys.exit("Import this module")

#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# This script holds the functionality for making sure a series of
# servers (eg index servers, doc servers, webservers, etc)
# are up and running -- or at least limping, able to answer a simple
# query.

##### load_adsdb_config
##### TODOs in get_webargs
##### 1. gws that want to talk to backends without benefit of mixers
##### 2. entmixer?

__pychecker__ = 'maxargs=20 maxbranches=62'

import os                             # for os.system()
import re                             # for restricting the hosts to start
import select
import socket
import string                         # for changing the arguments
import sys
import time                           # for sleep in restart
import traceback                      # so we know what went wrong
import types

import sitecustomize                  # for GOOGLEBASE

from google3.pyglib import logging

from google3.enterprise.legacy.production.babysitter import babysitter_argv_checker
from google3.enterprise.legacy.production.babysitter import config_namespace
from google3.enterprise.legacy.production.babysitter import googleconfig
from google3.enterprise.legacy.production.babysitter import segment_data
from google3.enterprise.legacy.production.babysitter import servertype
from google3.enterprise.legacy.setup import lockfile                       # for acquiring/releasing lock
from google3.enterprise.legacy.setup import prodlib                        # for processing types

send_mail = 1                         # send email on failure by default
MAILTO = []                           # list of users to be notified
LOCKFILE = 'admin.lock'               # don't change this name. Lot of
                                      # other programs require it to be
                                      # exactly this :(

# This is just a global; we encapsulate it in a function so other
# modules can import us and still modify the global
po = 0
def print_only(newval = None): # None to leave value unchanged; returns oldval
  global po
  if newval: po = newval
  return po

###############################################################################
#
# This class loads and saves restart data in a file that can be
# given to the babysitter to restart while babysits all the other
# servers
#
class BabyRestartData:
  def __init__(self, filename, require_lock, lockdir):
    self.filename_ = filename
    self.require_lock_ = require_lock
    self.lockdir_ = lockdir
    self.restarts_ = {}

  def _acquire_lock(self):
    if self.require_lock_:
      rc = lockfile.AcquireLockFile(LOCKFILE, lockdir=self.lockdir_, verbose=1)
      if rc != 0: raise RuntimeError, "Cannot acqire the admin lock"

  def _release_lock(self):
    if self.require_lock_:
      lockfile.ReleaseLockFile(LOCKFILE, lockdir=self.lockdir_)

  def _load_locked(self):
    cn = config_namespace.ConfigNameSpace({})
    try:
      cn.ExecFile(self.filename_)
      self.restarts_ = cn.namespace['RESTARTS']
      return 1
    except (IOError, KeyError):
      return 0

  def _save_locked(self):
    tmp_file = "%s_temp" % self.filename_
    fd = open(tmp_file, "w")
    try:
      fd.write("RESTARTS = %s" % repr(self.restarts_))
      os.fdatasync(fd.fileno()) # put it on the disk
    finally:
      fd.close()
    os.rename(tmp_file, self.filename_)

  def Load(self):
    self._acquire_lock()
    try:
      return self._load_locked()
    finally:
      self._release_lock()
    return 0

  def Save(self):
    self._acquire_lock()
    try:
      self._save_locked()
    finally:
      self._release_lock()

  def restarts(self):
    return self.restarts_

  def MarkRestarted(self, server):
    self._acquire_lock()
    try:
      self._load_locked()
      if self.restarts_.has_key(server):
        del self.restarts_[server]
      self._save_locked()
    finally:
      self._release_lock()

  def AddRestart(self, server):
    self.restarts_[server] = 1

  def RemoveRestart(self, server):
    if self.restarts_.has_key(server):
      del self.restarts_[server]

###############################################################################

# The C++ monitor takes a list of machines, and instructions for how
# to monitor them, on stdin.  Then it does the monitoring, and
# every time it notices someone to restart it prints the name to
# stdout.  We use a popen2 -- whatever the monitor prodlib.logs to stderr
# gets passed through to our stdout.  maxiters is the maximum number of
# checks the monitor process should make of each machine before exiting;
# if 0, it checks forever.
class monitor_event_loop:
  def __init__ (self, monitor_program_name, maxiters):
    import popen2
    assert type(maxiters) == types.IntType
    assert maxiters >= 0
    # TODO: when new monitor is everywhere, always pass the --maxiters flag
    if maxiters > 0:
      cmdline = '%s --maxiters=%d' % (monitor_program_name, maxiters)
    else:
      cmdline = monitor_program_name
    # end if
    if not print_only():
      (self.monitor_out, self.monitor_in) = popen2.popen2(cmdline)
    else:
      (self.monitor_out, self.monitor_in) = (None, None)

    self.restartfns = {}                 # hash from host:port to restart cmd
    self.maxiters = maxiters
    self.originaldata = {}               # original host/port
    self.restarts = {}                   # from (host, port) to # of restarts

  # The input has the format:
  #    host port printable-hostport timeout,timeout,... minlen delimiter\n
  #    command...
  #    command...
  #    command...delimiter\n
  def register (self, serverinfo, command, minlen, requested_timeouts):
    (host, port, original_port, ip, restartfn) = serverinfo
    printable_hostport = "%s:%d" % (host, port)
    delimiter = "COMMAND_DELIMITER"  # must not appear in cmd, must not have \n
    if self.maxiters > 0:
      timeouts = requested_timeouts[:self.maxiters] # fewer than maxiters t/os
    else:
      timeouts = requested_timeouts
    # end if
    if not print_only():
      self.monitor_in.write("%s %d %s %s %d %s\n%s%s\n" % (
        ip, port, printable_hostport,
        string.join(map(lambda x: str(x), timeouts), ","),  # stringify numbers
        minlen, delimiter, command, delimiter))
    self.restartfns[printable_hostport] = restartfn    # all we need to know
    self.originaldata[printable_hostport] = (host, original_port)

  def go (self, timeout = None):
    # done registering the machines
    if self.monitor_in != None:
      self.monitor_in.close()
      self.monitor_in = None

    # if we have nothing to do just return
    if not self.restartfns:
      return self.restarts

    reached_maxiters = 0
    while timeout > 0 or timeout == None:
      start_time = time.time()
      # We select to give wait most the specified timeout
      (ioready, _, _) = select.select([self.monitor_out],
                                      [],    # don't care about "write"-s
                                      [],    # ... or errors
                                      timeout)

      if self.monitor_out not in ioready:
        return self.restarts

      # Adjust the time left for us
      if timeout != None:
        timeout =  timeout - time.time() + start_time

      line = self.monitor_out.readline() # each line now means "restart me!"
      if 'MAXITERS\n' == line:
        assert self.maxiters > 0
        assert not reached_maxiters
        reached_maxiters = 1
        continue
      if not line:
        if reached_maxiters:
          break
        prodlib.log("EOF from monitor subprocess! (Subprocess died?) Exiting.")
        prodlib.log("Make sure you have monitor installed " +
                    "(google/bin/monitor)")
        sys.exit(1)
      assert not reached_maxiters
      print "Restarting %s" % line[:-1]
      sys.stdout.flush()                 # mix this with monitor's messages
      printable_hostport = line[:-1]
      self.restartfns[printable_hostport]() # line (minus \n) is key to table
      original_hostport = self.originaldata[printable_hostport]
      self.restarts[original_hostport] = self.restarts.get(original_hostport, 0) + 1

    return self.restarts

###############################################################################

# Test if this host/port is to be acted upon by the babysitter.
def WantedServer(host, port, mtype, config, machine_re,
                 myhostname, excluded):

  if excluded.has_key((host, port)):
    # machine was explicitly excluded
    return 0

  if machine_re and not machine_re.search(host):
    # if we have an re, skip things that don't match
    return 0

  if mtype in config.var('NOBABYSIT_TYPES', []):
    # this config wants to ignore some types from babysitting
    # for various reasons (most likely double-babysitting) so
    # we drop them from the machine list.
    # PHJ - do we really want to print this message?  If another
    #   config _is_ babysitting the machine, it's a little misleading.
    print "Not babysitting %s:%s type %s." % (host, port, mtype)
    return 0

  if host in config.var('NOBABYSIT_HOSTS', []):
    # this config wants to ignore some hosts from babysitting
    # for various reasons (most likely for denying bad machines from
    # being started automatically or for testing new binaries) so
    # we drop them from the machine list.
    print "Not babysitting %s:%s type %s." % (host, port, mtype)
    return 0

  # Passed all tests so return true.
  return 1


# Return list of server objects to restart.
# server_restrict is to further restrict the machines to specific servers
def ComputeServers(config, types, machine_re,
                   restrictports, myhostname, excluded, do_ckpt, ckpt_time,
                   sets, restrict_servers=None, ssh_user=None):

  srv_mgr = config.GetServerManager()
  servers = srv_mgr.Servers(wanted_sets=types, wanted_ports=restrictports,
                            wanted_indices=sets)
  computed_servers = []

  for server in servers:

    set = srv_mgr.Set(server.srvset())
    host = server.host()
    port = server.port()

    if restrict_servers and not restrict_servers.get(str(server), 0):
      continue

    mtype = server.servertype()

    if not WantedServer(host, port, mtype, config,
                        machine_re, myhostname, excluded):
      # Server has not been selected for inclusion.
      continue

    # Allow overriding ssh_user.
    if server.property('ssh_user'):
      ssh_user = server.property('ssh_user')

    # For AM transition, if there is no binary user set, then
    # do not use the ssh_user so we can still go on as root.
    # We will run the babysitter as root and it will ssh into
    # machines with binary_user set as prodsetup, and it will
    # ssh into machines without binary_user set as root.
    # TODO: Remove this when we are finished with conversion.
    binary_user = set.property('binary_user')
    if not binary_user or binary_user == 'root':
      ssh_user = None

    # Print out an informational string for the user.
    set_str = ''
    if sets: set_str = ' - set %s' % server.index()
    print "Checking %s:%d (%s%s)" % \
          (host, servertype.GetServingPort(port), mtype, set_str)

    safe_start_time = server.index() * server.property('inter_set_delay')

    try:
      hostip = socket.gethostbyname(host)
    except socket.error, e:
      prodlib.log("DNS error for %s: %s. Skipping." % (host, e))
      continue

    # Form restart closure
    restartfn = lambda f=server.Start, m=print_only(), u=ssh_user: \
      f(m, u)

    # Form kill closure
    killfn = lambda f=server.Stop, u=ssh_user, ck=do_ckpt, ct=ckpt_time: \
      f(2, u, ck, ct)

    server.set_property('hostip', hostip)
    server.set_property('safe_start_time', safe_start_time)
    server.set_property('restartfn', restartfn)
    server.set_property('killfn', killfn)

    computed_servers.append(server)

  return computed_servers


# Given a machine list with associated information, we restart the
# servers in a certain order.  Restart delay is only given
# between sets.
def DoRestarts(servers, delay, sets=None):

  prev_setidx = -1

  for server in servers:

    # Sleep between distinct sets.
    if delay and prev_setidx != -1 and \
      ((sets and server.index() != prev_setidx) or (not sets)):
      print "Sleeping for %s secs..." % delay
      sys.stdout.flush()
      time.sleep(delay)

    prev_setidx = server.index()

    # Call restart function.
    try:
      server.property('restartfn')()
    except Exception, e:
      prodlib.logtrace('ERROR in restart command: %s:%s - %s in %s' %
                       (server.host(), server.port(),
                        server.srv_mgr().config().GetConfigFileName(),
                        server.srvset()))
      raise e


# Classify servers into whether they are alive, dead or unknown.
def ClassifyServerStates(servers):
  dead = []
  alive = []
  unknown = []
  for server in servers:
    host = server.host()
    port = server.port()
    state = servertype.CheckServer(host, servertype.GetServingPort(port))
    if state == 0:
      alive.append(server)
    elif state == 2:
      unknown.append(server)
    else:
      dead.append(server)
  return alive, dead, unknown


# Given a machine list with associated information, we kill the
# servers in a certain order.  If checkpointing is specified, the
# appropriate checkpoint command will be sent to the servers and they
# will be given up to checkpoint_time to complete the command.
#
# This function tries several times to kill servers and tests
# aliveness by connecting to the specified host/port.  It forks
# up to kill_batch_size processes at a time to perform the kills.
def DoKills(servers, kill_batch_size, do_checkpoint,
            checkpoint_time):

  # Kill list of servers.
  def KillServers(servers, kill_batch_size, do_checkpoint, checkpoint_time):

    kill_cmds = []

    for server in servers:
      host = server.host()
      port = server.port()
      kill_cmd = server.property('killfn')()
      if kill_cmd:
        kill_cmds.append(((host, port), kill_cmd))

    if print_only():
      for (host, port), kill_cmd in kill_cmds:
        print "%s:%s => %s" % (host, servertype.GetServingPort(port), kill_cmd)
      return

    timeout = 30
    if do_checkpoint: timeout = timeout + checkpoint_time
    results = prodlib.ForkShCommands(kill_cmds, timeout, kill_batch_size,
                                     machname=lambda x: x[0])
    for (host, port), (status, output, errors) in results.items():
      if status != 0:
        print "Failed to kill server at %s:%s" % \
              (host, servertype.GetServingPort(port))

  ### end def KillServers

  # Kill the first time.
  KillServers(servers, kill_batch_size, do_checkpoint, checkpoint_time)

  if print_only(): return

  # Test servers and repeat up to num_tries times.
  num_tries = 3
  attempt = 1

  while len(servers) > 0 and num_tries > 0:
    print "Sleeping while processes are killed"
    time.sleep(10)
    print "Checking for alive/unknown processes"
    num_tries = num_tries - 1
    attempt = attempt + 1
    (alive, dead, unknown) = ClassifyServerStates(servers)
    servers = alive + unknown
    if len(servers) > 0:
      print "%s still alive/unknown, killing" % len(servers)
      KillServers(servers, kill_batch_size, 0, checkpoint_time)

  # Check if any still remaining.
  (alive, dead, unknown) = ClassifyServerStates(servers)
  if len(alive) > 0:
    print "Failed to kill (still alive): %s" % \
          map(lambda x: '%s:%s' % (x.host(), x.port()), alive)
  if len(unknown) > 0:
    print "Failed to kill (timeout/unknown): %s" % \
          map(lambda x: '%s:%s' % (x.host(), x.port()), unknown)

# Main babysitter loop. You give me a list of machines (with arguments
# and all as returned by CollectMachines) and I'll babysit them in an
# infinite loop.  If maxiters is nonzero, the event loop will exit after
# the specified number of iterations.
# returns: list of servers that restarted during the monitoring
def DoBabysit(servers, config, maxiters=0, monitor_port_increment=0,
              extra_restarts=None, restart_requests=None, nolooprestarts=0,
              nortsignals=0, succinterval=None, failinterval=None):

  # map from (host, port) to the corresponding server . We need this
  # because el.go returns us results in form of host ports while we
  # want servers.
  hostport_srvinfo_map = {}

  if nolooprestarts:
    if extra_restarts:
      sleep_time = max(map(lambda m: m.property('safe_start_time'),
                           extra_restarts))
    else:
      prodlib.log('Babysitter loop has nothing to do.. exiting')
      sys.exit()
    # endif
    monitor_command = "sleep %d # " % sleep_time
  else:
    monitor_command = "%s/google/bin/monitor --status_port=%s" % (
                             sitecustomize.GOOGLEBASE,
                             servertype.GetPortBase('monitor') +
                             monitor_port_increment)
  # endif

  if nortsignals:
    monitor_command = monitor_command + " --nortsignals"
  if succinterval:
    monitor_command = monitor_command + " --succinterval=%s" % succinterval
  if failinterval:
    monitor_command = monitor_command + " --failinterval=%s" % failinterval

  el = monitor_event_loop(monitor_command, maxiters)

  for server in servers:
    # Cannot babysit virtual servers (ports >= 65536)
    if server.port() >= 65536:
      continue
    if server.property('skip_babysitting'):
      print "WARNING: babysitting disabled for %s:%s" % (server.host(),
                                                         server.port())
      continue

    if not nolooprestarts:

      datadir = server.datadir()
      if datadir is None: datadir = ''
      query = server.property('request_info')
      # some queries require dataversion. Right now dataversion is
      # the datadir for all servers.
      query = query % {'dataversion': datadir}

      el.register((server.host(), servertype.GetServingPort(server.balport()),
                   server.port(), server.property('hostip'),
                   server.property('restartfn')),
                   query, server.property('response_len'),
                   server.property('test_timeouts'))
      host_port = (server.host(), server.port())
      hostport_srvinfo_map[host_port] = server
    # endif

  if extra_restarts and restart_requests:
    start_time = time.time()
    for server in extra_restarts:
      # Insure that enough seconds have passed since we start
      passed_time = time.time() - start_time
      if server.property('safe_start_time') > passed_time:
        delay = server.property('safe_start_time') - passed_time
        print "Spending  %s seconds monitoring." % delay
        if not print_only():
          el.go(timeout=delay)
        else:
          print "Actually simulating a sleep of %s" % delay

      # Call restart function.
      server.property('restartfn')()
      # And mark this guy restarted
      restart_requests.MarkRestarted(str(server))

  # Start the actual babysitter.
  restarted_srv_list = []
  argv_checker = babysitter_argv_checker.BabysitterArgvChecker(config)
  logging.info("%s %s: Restarting servers whose argv has changed. "
                   % (time.ctime(), time.tzname[0]))
  hostports = argv_checker.RestartIfArgvChanged()
  for hostport in hostports:
    restarted_srv_list.append(hostport_srvinfo_map[hostport])

  if not print_only():
    restarts = el.go()
    restarts = restarts.keys()
    for hostport in restarts:
      restarted_srv_list.append(hostport_srvinfo_map[hostport])

  return restarted_srv_list

def usage():
    print "FORMAT: %s [--loop] [-n|--noexec]" % sys.argv[0]
    print "  [--start=<types>] "
    print "  [<other options>] <configspec>\n"
    print " --start/kill=<types>  limits restarts/kills to specified types "
    print "            (use 'all' if want to restart all) neg groups are ok."
    print "      ex. --start=index    restarts only index servers."
    print "          --start=-doc     restarts everything but doc servers"
    print "          --start=mixer:1  restarts only level 1 mixers"
    print "          --start=+index:1 restarts only level 1 index balancers"
    print " --re=regex    limits babysitter to hosts that match regexp"
    print " --mach        alternative to --re. Only consider machines in the"
    print "               specified list."
    print " --delay=time   delays 'time' sec between restarts or kills (fraction ok)"
    print " --sets=0,2,5     Triggers by-set separation and does restarts"
    print "                  set-by-set. If 'all' is listed, all sets are"
    print "                  restarted. Otherwise, only specified sets are "
    print "                  affected."
    print " --ports=<port>      limits to hosts on the specified port(s)"
    print "                     ex. --ports=4024,4027,5012"
    print " --nodataversion   turns off data versioning in the restart"
    print "                   commands. For emergencies only!"
    print " --mailto=<email>  who to notify if the babysitter is broken "
    print "                   and throws exceptions (default: <production>)"
    print " --nomail       disable emails"
    print " --fromcron     ignored. For human use only."
    print " --batch        dont ask whether to start - just do it."
    print " --setpgrp      start in our own process group"
    print " --sandbox=<b|c|...>   run in the specified preprod sandbox."
    print "                       Shifts all ports by N*100."
    print " --kill_batch_size=<size>   procs to kill at same time."
    print " --nocheckpoint        do not checkpoint servers before killing."
    print " --checkpoint_time=<time>   max time for checkpointing."
    print " --corptest   for testing the babysitter on corp machines."
    print "              causes bypassing of gethostname and gethostbyname."
    print "              NOTE: this creates restart cmds that may have fake"
    print "              IP addresses embedded within the cmd."
    print "              This only works with the -n flag."
    print " --corphack   for running the babysitter on corp machines."
    print "              WARNING: babysitter often assumes it runs at a coloc."
    print "              !!!USE AT YOUR OWN RISK!!!"
    print " --nobabycheck Ignore safety checks that ensure that the"
    print "               local machine is an appropriate babyistter machine"
    print "               to operate from"
    print " --restarts_file=<file> "
    print "              Read some extra restarts to do (safely)  while "
    print "              babysitting "
    print " --babyalias=<localhost|alias suffix) how to find the babysitter"
    print " --config_dir=<dir> Use this directory to default all includes to it"
    print " --lockdir=<dir>    The directory where lock is created"
    print " --force_lock       Forces locking even if we don't run on "
    print "                    babysittermachine"
    print " --nolock           Do not use the lock - don't use this flag "
    print "                    unless you know what you are doing "
    print "                    (professional drivers on closed course)"
    print " --maxiters=<cnt>   The max number of iterations of the loop."
    print " --nolooprestarts   Run the loop but do not perform restarts in it"
    print " --ssh_user         The user to ssh as - defaults to not specified"
    print "<configspec>        has three forms:"
    print "   <coloc>          load all production configs for named colo "
    print '                    (eg. "ex")'
    print "   <coloc> <name>   load the named production config at specified "
    print '                    coloc (eg. "ex www")'
    print "   filename [filename...]  load the specified file(s)"
    print "The first two forms can only be used on the babysitter machine."

    sys.exit(1)

def main(argv):
  import getopt

  global send_mail, MAILTO  # so mail works regardless where we fail!

  send_mail = 0         # disable mail unless user wants it. It is enabled
                        # by default only so we can catch major syntax errors.
  batch = 0             # assume we're running from command line

  try:
    (optlist, args) = getopt.getopt(argv, 'n',
                     ['re=', 'delay=', 'ports=', 'loop', 'noexec',
                      'nolock', 'force_lock', 'start=', 'kill=',
                      'mailto=', 'nomail', 'fromcron', 'batch', 'mach=',
                      'nodataversion', 'sets=', 'sandbox=', 'setpgrp',
                      'kill_batch_size=', 'nocheckpoint', 'checkpoint_time=',
                      'validate', 'useinvalidconfig', 'nolooprestarts',
                      'corphack', 'corptest', 'babyalias=',
                      'lockdir=', 'maxiters=', 'config_dir=',
                      'restarts_file=', 'nobabycheck', 'ssh_user=',
                      'nortsignals', 'regtest',
                      ]
                    )
  except getopt.error, e:
    prodlib.log("getopt error: %s" % e)
    usage()

  loop = 0  # make sure is defined even if we skip the for loop
  nolooprestarts = 0
  machine_re = None
  restrictports = {}
  delay = None
  types = {}
  nolock = 0
  force_lock = 0
  sets = {}
  mode = 'start'
  kill_batch_size = 30
  do_checkpoint = 1
  checkpoint_time = 1200
  sandbox_offset = 0
  corphack = 0
  babyalias = 'baby.prodz.google.com'
  lockdir = '/root'
  corptest = 0
  maxiters = 0
  config_dir = None
  restarts_file = None
  babycheck = 1
  ssh_user = 'prodsetup'
  nortsignals = 0
  regtest = 0

  for flag,value in optlist:
    if flag in ['--re', '--mach']:
      if flag == '--mach':
        # list of machines specified. Compute the corresponding regexp
        # that will match them all (and only them): (mach1)|(mach2)|...
        machines = string.split(value, ',')
        if len(machines) == 1:
          machines = string.split(value)     # maybe it's space-separated?
        regexpstr = '^((%s))$' % string.join(machines, ')|(')
      else:
        regexpstr = value

      # TODO: allow multiple regexps
      if not machine_re:
        machine_re = re.compile(regexpstr)
      else:
        prodlib.log("Only one of --re= or --mach= is allowed")
        usage()
    elif flag == '--delay':
      delay = float(value)
    elif flag == '--ports':
      restrictports = prodlib.CollectTypes(value, {})
    elif flag == '--noexec' or flag == '-n':
      print_only(1)
    elif flag == '--corptest':
      # For testing, don't do any DNS lookups to speed up processing.
      # Also, sprinkled through the code are calls to machdistance.ParseMachine
      # which fail for corp machines - hack local hostname into something
      # that passes it.
      socket.gethostbyname = lambda x: x
      socket.gethostname = lambda : 'exyz1'
      corptest = 1
    elif flag == '--corphack':
      # Allow us to run babysitter on local machine.  However, not all
      # retstart methods are guaranteed to run since some rely on
      # on localhost name elswhere in the code.
      corphack = 1
    elif flag == '--babyalias':
      babyalias = value
    elif flag == '--nolock':
      nolock = 1
    elif flag == '--force_lock':
      force_lock = 1
    elif flag == '--loop':
      loop = 1
      send_mail = 1               # send email on failure if you are going
                                  # to stay in infinite loop
    elif flag == '--nolooprestarts':
      nolooprestarts = 1
    elif flag == '--restarts_file':
      restarts_file = value
    elif flag == '--start' or flag == '--kill':
      mode = flag[2:]
      types = prodlib.CollectTypes(value, {})
    elif flag == '--mailto':
      # override the mailto default, filtering out empty strings
      MAILTO = filter(lambda x:string.strip(x), string.split(value, ','))
      send_mail = MAILTO and 1 or 0      # enable mail sending if nonempty
    elif flag == '--lockdir':
      lockdir = value
    elif flag == '--maxiters':
      maxiters = int(value)
    elif flag == '--nomail':
      send_mail = 0                      # disable mail sending
    elif flag == '--batch':
      batch = 1                          # don't ask no steeking questions
    elif flag == '--sets':
      sets = prodlib.CollectTypes(value, {})
    elif flag == '--nodataversion':
      from google3.enterprise.legacy.production.babysitter import servertype_prod
      servertype_prod.no_data_versions() # drop versioning capabilities
    elif flag == '--sandbox':
      if len(value) != 1 or ord(value) not in range(ord('b'), ord('z')+1):
        prodlib.log("Invalid sandbox name. Sandboxes are named b to z")
        return 1
      # TODO: We use 100 for all servers here.  The reason is that we
      #       don't have enough port ranges for sandboxes to have
      #       unique ports. Instead, sandbox port ranges will overlap
      #       with "normal" port ranges. E.g.  sandbox K indexserver
      #       at port 5000 will overlap with the regular docserver at
      #       port 5000. It can't be helped.  So, for simplicity, we
      #       simply use +100 for each servertype, instead of
      #       GetLevelSize() or similar, and avoid collisions through
      #       careful machine allocation.
      sandbox_offset = (ord(value) - ord('a')) * 100
      servertype.SetSandBoxOffset(sandbox_offset)
    elif flag == '--setpgrp':            # start in our own process group
      os.setpgrp()
    elif flag == '--kill_batch_size':
      kill_batch_size = int(value)
    elif flag == '--nocheckpoint':
      do_checkpoint = 0
    elif flag == '--checkpoint_time':
      checkpoint_time = int(value)
    elif flag == '--nobabycheck':
      babycheck = 0
    elif flag == '--config_dir':
      config_dir = value
    elif flag == '--ssh_user':
      ssh_user = value
    elif flag == '--nortsignals':
      nortsignals = 1
    elif flag == '--regtest':
      regtest = 1

  # corptest only when printing
  if corptest and not print_only():
    prodlib.log("--corptest may only be used with -n")
    return 1

  if delay is not None and delay < 0:
    prodlib.log("Invalid delay %g." % delay)
    return 1

  if maxiters < 0:
    prodlib.log("Invalid maxiters %g." % maxiters)
    return 1

  if maxiters > 0 and not loop:
    prodlib.log("Cannot specify --maxiters without --loop.")
    return 1

  if regtest and not print_only():
    prodlib.log("--regtest may only be used with -n")
    return 1

  # set flag in segment_data indicating that we want to allow test configs
  if print_only():
    segment_data.SetDisallowTestMode(0)

  # set flag in segment_data indicating to use fake data.  This is
  # useful for regression testing.  It causes data.* files to look
  # standard even if their data is changing.
  if regtest:
    segment_data.SetUseFakeData(1)


  require_lock = 0
  try:

    # fetch local babysitter machine
    myhostname = socket.gethostname()
    babymach = myhostname

    # lock if forced or running without nolock flag on a babysitter machine.
    require_lock = force_lock or ( myhostname == babymach and not nolock )
    if require_lock:
      rc = lockfile.AcquireLockFile(LOCKFILE, lockdir=lockdir, verbose=1)
      if rc != 0:
        return 1

    # acceptable config specs:
    #   <config> [config] ...          eg. "config.apr02index.ex"
    configfiles = args

    if not configfiles:
      usage()

    configs = []
    has_servers = 0
    config = None

    # load configs
    for configfile in configfiles:

      try:
        # load config
        config = googleconfig.Load(configfile, config_dir = config_dir)

        # Dummy data files may not be used to start the babysitter.
        if segment_data.DisallowTestMode() and config.var('SEGMENT_TEST_MODE'):
          raise RuntimeError, "babysitter may not be run with " \
                              "a testing data segment file: %s" % configfile

        # if we're in sand box mode set some overriding config values.
        if sandbox_offset:
          config.set_var('USE_LOOP', 0)
          config.set_var('ALLOW_COREFILES', 1)

        if config.GetServerManager().Servers(): has_servers = 1

        # Append to list of configs.
        configs.append(config)

      except Exception, e:
        # collect the exception traceback so we know what went wrong
        (t, v, tb) = sys.exc_info()
        exc_msg = string.join(traceback.format_exception(t, v, tb))
        prodlib.log('Unable to load config: %s - %s' % (configfile, exc_msg))
        continue

    if len(configs) != len(configfiles):
      raise RuntimeError, "Some configs are invalid: aborting."

    if not configs:
      raise RuntimeError, "Could not load any configs: aborting."

    if not has_servers:
      sys.stderr.write("No servers in configs. Exiting.\n")
      sys.exit(0)

    excluded = {}

    # find out if to use a different monitor port
    babysitter_monitor_port_increment = 0
    for config in configs:
      if config.var('BABYSITTER_MONITOR_PORT_INCREMENT') > 0:
        babysitter_monitor_port_increment = config.var(
          'BABYSITTER_MONITOR_PORT_INCREMENT')

    servers = []
    for config in configs:
      # add machine information to list
      servers.extend(ComputeServers(config, types, machine_re,
                                    restrictports, myhostname, excluded,
                                    do_checkpoint, checkpoint_time, sets,
                                    ssh_user=ssh_user))

    # HACK: because of the balancer port hack and the fact that currently
    # we only run one bal process even if it is balancing multiple backends,
    # we uniquify balancers on same host/dif't ports to only include one.
    # This should be REMOVED and the server.balport() call above in register should
    # be changed to server.port().  It may require ensuring that balancers
    # respond to varz on all their balanced ports which is believed to be
    # true for the current balancer but may not be true for some services
    # running very old balancers.  If we ever move to separate balancer processes
    # this will *have* to be changed.
    tmp = []
    seen_hps = {}
    for server in servers:
      key = (server.host(), server.balport())
      if seen_hps.has_key(key): continue
      seen_hps[key] = 1
      tmp.append(server)
    servers = tmp

    #
    # Compute the restarts to do while babysitting. This are normally
    # written by the restarter in a well specified file, and are
    # restarts that need to be done in order to make the backends match
    # the config. This does not contain the probe or new starts (see restarter
    # for details of what these are)
    #
    # We do this in the following way:
    #   - We load the restarts and compute the corresponding machine infos
    #   - Put these arrange per (config, mtype, port) sets
    #   - Compute safe start times for each of this sets :
    #      - the first machine is started now, next after the corresponding
    #        inter_set_delay, next after 2*inter_set_delay etc
    #
    restart_requests = None
    extra_restarts = []
    if restarts_file:
      restart_requests = BabyRestartData(restarts_file, require_lock, lockdir)
      restart_requests.Load()
      if restart_requests.restarts():
        per_config_host_port = {}
        for config in configs:
          # add machine information to list
          extras = ComputeServers(config, types, machine_re,
                                  restrictports, myhostname, excluded,
                                  do_checkpoint, checkpoint_time, sets,
                                  restrict_servers=restart_requests.restarts(),
                                  ssh_user=ssh_user)

          for server in extras:
            extra_restarts.append(server)
            key = (config, server.servertype(), server.port())
            if not per_config_host_port.has_key(key):
              per_config_host_port[key] = []
            per_config_host_port[key].append(server)

        # Now per each row determine rearrange the start times to
        # do not have holes.
        for srv_list in per_config_host_port.values():
          srv_list.sort(lambda x,y: cmp(x.index(), y.index()))
          i = 0
          for server in srv_list:
            server.set_property('safe_start_time',
                                i * server.property('inter_set_delay'))
            i = i + 1

        # Sort the extra restarts in the start time order
        extra_restarts.sort(lambda x,y: cmp(x.property('safe_start_time'),
                                    y.property('safe_start_time')))
        for server in extra_restarts:
          print "Restart : %s | Index %s | Start Time %s" % \
                (server,
                 server.index(),
                 server.property('safe_start_time'))
      else:
        restart_requests = None

    if sets:
      # Sort by setidx (to get a deterministic process order) and use reverse
      # order so enterprise index switchovers remain smooth (set 0 needs
      # to be killed last as it's the only guaranteed complete set).
      servers.sort(lambda x,y: -cmp(x.index(), y.index()))
    else:
      # If no sets are specified sort by mach to spread across shards.
      servers.sort(lambda x,y: cmp((x.host(), x.port()), (y.host(), y.port())))

  finally:
    if require_lock:
      lockfile.ReleaseLockFile(LOCKFILE, lockdir=lockdir)

  if not servers:               # never found a server to babysit
    prodlib.log("No suitable machines found in the configs\n")
    sys.exit(1)

  #### We are ready to do some real work now.

  servertype.LoadRestartInfo()

  # start/kill everyone we were asked to (if any), after getting confirmation
  if types:   # set if any --start/--kill param.

    # If no delay is specified then use max of inter set delay for safety
    # if we are doing restarts.  If we're just printing, default to 0.
    if delay is None:
      delay = 0
      # TODO: Uncomment this when dependencies are updated.
      #if not print_only():
      #  for server in servers:
      #    if server.property('inter_set_delay') > delay:
      #      delay = server.property('inter_set_delay')

    if not print_only():
      if delay == 0:
        print "\nWARNING: NO DELAY HAS BEEN SET\n"
      else:
        print "\nUsing delay of: %s secs\n" % delay

    if mode == 'start':
      if loop:
        print "WARNING: USING --start WITH --loop"
      print "Restarting the above services. ",
    else:
      print "Killing the above services. ",

    # Check for confirmation
    if not batch:
      print "Confirm (y/N)? ",
      confirm = sys.stdin.readline();
      print
    else:
      confirm = 'y'
    if confirm[0] != 'y' and confirm[0] != 'Y':
      return 0

    if mode == 'start':
      DoRestarts(servers, delay, sets=sets)
      # fall through to run the loop, if requested
    else:
      DoKills(servers, kill_batch_size, do_checkpoint, checkpoint_time)
      return 0

  # babysit everyone by adding them to the request loop and calling it
  if loop and not print_only() and servers:
    DoBabysit(servers, config,
              maxiters=maxiters,
              extra_restarts=extra_restarts,
              monitor_port_increment = babysitter_monitor_port_increment,
              restart_requests=restart_requests,
              nolooprestarts=nolooprestarts,
              nortsignals=nortsignals)

  return 0


if __name__ == '__main__':
  try:
    main(sys.argv[1:])
  except SystemExit, e:
    sys.exit(e)    # "normal" exit
  except KeyboardInterrupt:
    sys.exit(1)    # I guess this is fine
  except:
    # collect the exception traceback so we know what went wrong
    (t, v, tb) = sys.exc_info()
    exc_msg = string.join(traceback.format_exception(t, v, tb))
    if send_mail and MAILTO:
      myhostname = socket.gethostname()
      prodlib.log("Warning email sent to %s" % string.join(MAILTO, ','))
      prodlib.Sendmail(MAILTO, "%s babysitter broken" % myhostname, exc_msg)

    # prodlib.log the message regardless
    prodlib.log(exc_msg)

    sys.exit(1)

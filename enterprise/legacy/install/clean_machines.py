#!/usr/bin/python2.4
#
# Copyright (C) 2000 and onwards Google, Inc.
# Author: David Watson
#
# This cleans up a system of all traces of any enterprise system.
#
###############################################################################
"""
Usage :
   clean_machines supports two forms:

   ./clean_machines.py <inter_machine> <machine list>
   ./clean_machines.py [--machines=<machine_list>] [--version=<version>]
                       [--inter=<inter_machine>] [--inter_ssh=<port>]

   Flags:
     --machines : Clean the specified machines (required)
     --version  : Clean only the specified version (default: all)
     --inter    : Install via the specified machine (default: none)
     --inter_ssh: Use the given port for inter machine (default: 22)
     --force    : Force the clean even if the machine is active.  Also
                  kill any active processes.
"""
###############################################################################

import sys
import string
import time
import commands
import os
import getopt

REMOVE_EXPORT_DIRS = '/export/hd?3/*'

RESTORE_DIRS = ['/export/hda3/tmp']

def comment(s):
  return "echo %s" % commands.mkarg(s)

def remote_cmd(machine, cmd, ssh_port = 22):
  """ runs a command remotely """
  return "ssh -p %d -l root %s %s" % (ssh_port,
                                      machine,
                                      commands.mkarg(cmd))
def uninstall_all_rpms():
  cmd = ("rpm -qa | fgrep -v vmanager | fgrep google-enterprise | "
         "xargs rpm -e --allmatches; rpm -qa | fgrep -v vmanager | "
         "fgrep google-enterprise | xargs rpm -e --nodeps --allmatches "
         "--noscripts")
  return [ comment('Uninstalling RPMS'), cmd ]

def uninstall_version_rpms(version):
  """Uninstall all enteprise software rpms of the given version."""

  # The version can be major version only (e.g. 5.1.16). Rpms of the same
  # major version but different minor versions (release numbers) (e.g.
  # 5.1.16-2 and 5.1.16-4) can never coexist in the GSA as they would overwrite
  # each other. So using the major version is sufficient to identify the right
  # rpms to uninstall.

  # Complete list of versioned RPMS to uninstall. Do not change this
  # order. Read http://b/1156814 for reasons why.
  rpm_list = [ 'google-enterprise-support-tools-%s' % version,
               'google-enterprise-archbins-%s' % version,
               'google-enterprise-data-%s' % version,
               'google-enterprise-base-%s' % version,
               'google-enterprise-bins-%s' % version,
               'google-enterprise-java-%s' % version ]
  rpm_cmd = 'rpm -e %s' % (' '.join(rpm_list))
  return [ comment('Uninstalling (version %s) RPMS' % version), rpm_cmd ]

def version_independent_misc_cleanup():
  commands = []

  # Remove /export/hd?3 dirs
  rm_cmd = ("echo %s | tr \\  \\\\n | fgrep -v versionmanager | xargs rm -rf" %
            REMOVE_EXPORT_DIRS)
  commands.append(comment('Removing %s') % REMOVE_EXPORT_DIRS )
  commands.append(rm_cmd)

  # Restore dirs
  for dir in RESTORE_DIRS:
    commands.append(comment('Creating %s') % dir )
    commands.append("mkdir -p %s" % dir)
    commands.append("chown nobody:nobody %s" % dir)

  return commands

def version_dependent_named_cleanup(version):
  commands = []

  # Removing version specific zone information from named. Starting from zone "ent<version> ,
  # 5 lines need to be removed.
  commands.append(comment('Modifying named for version: %s' %version))
  commands.append("sed '/^zone \"ent%s/{N;N;N;N;d;}' /etc/named.conf > /etc/named.conf.new" % version.replace('.', '-'))
  commands.append("cp /etc/named.conf /etc/named.conf.bak")
  commands.append("mv /etc/named.conf.new /etc/named.conf")

  return commands

def version_independent_named_cleanup():
  commands = []

  # Removing all the zone information from named. Starting from zone "ent ,
  # 5 lines need to be removed.
  commands.append(comment('Modifying named for all versions'))
  commands.append("sed '/^zone \"ent/{N;N;N;N;d;}' /etc/named.conf > /etc/named.conf.new" )
  commands.append("cp /etc/named.conf /etc/named.conf.bak")
  commands.append("mv /etc/named.conf.new /etc/named.conf")

  return commands

def main(args):
  try:
    opts, pargs = getopt.getopt(args, "", ["inter=", "inter_ssh=",
                                           "version=", "machines=",
                                           "force" ])
  except:
    sys.exit(__doc__)

  # default values
  machines = []
  inter_machine = None
  inter_ssh_port = 22
  version = None
  force = 0

  if len(opts) == 0:
    # no flags were given, use old style args: <inter> <machine_list>
    if len(pargs) < 2: sys.exit(__doc__)
    inter_machine = pargs[0]
    machines = pargs[1:]
  else:
    # flags were given, use new style
    if len(pargs) != 0: sys.exit(__doc__)

    for name,value in opts:
      if name == '--inter': inter_machine = value
      elif name == '--inter_ssh': inter_ssh_port = string.atoi(value)
      elif name == '--version': version = value
      elif name == '--machines': machines = string.split(value, ',')
      elif name == '--force': force = 1

  if len(machines) == 0:
    sys.exit("ERROR: Must specify machines to clean")

  commands = []

  if version:
    # Cleanup up only a specific version of RPMS
    test_cmd = 'cat /export/hda3/%s/STATE 2>/dev/null' % version

    # Change the STATE file to "REMOVE"
    commands.append('echo REMOVE > /export/hda3/%s/STATE' % version)

    commands.extend( uninstall_version_rpms(version) )
    commands.append( "rm -rf /export/hd?3/%s" % version )

    # Remove any lingering chubby config info and localbabysitter files
    commands.append( "rm -f /etc/google/ent%s.chubby_cell "
                     "/etc/localbabysitter.d/*-%s.conf" %
                     (version.replace('.', '-'), version) )

    if force:
      # Kill any lingering processes with this version number
      commands.append( "/usr/bin/pkill -KILL -f '/%s/'" %
                       version.replace('.', '\\.') )
      commands.append( "/usr/bin/pkill -KILL -f '/%s/'" %
                       version.replace('.', '\\.') )

    commands.extend( version_dependent_named_cleanup(version) )

  else:
    # Uninstall all enterprise RPMS
    # all new versions should clean up after themselves in %preun/%postun
    test_cmd = 'cat /export/hda3/*/STATE 2>/dev/null'

    # Change the STATE file(s) to "REMOVE"
    commands.append('echo REMOVE | tee `ls /export/hda3/*/STATE` > /dev/null')

    commands.extend(uninstall_all_rpms())

    # Cleanup legacy versions and third party RPMS and some other files
    commands.extend(version_independent_misc_cleanup())

    # Remove any lingering chubby config info and version related
    # localbabysitter files. syslogd.conf and klogd.conf belong to
    # OS and cannot be removed.
    commands.append( "rm -f /etc/google/ent*.chubby_cell "
                     "/etc/localbabysitter.d/*-*.conf")

    # Remove zone stuff from named.conf
    commands.extend( version_independent_named_cleanup() )

    if force:
      # Kill any lingering processes belonging to nobody
      commands.append( "/usr/bin/pkill -KILL -u nobody" )
      commands.append( "/usr/bin/pkill -KILL -u nobody" )

  raw_cmd = string.join(commands, '; ')

  for machine in machines:
    print
    print "#################"
    print "Cleaning machine %s" % machine
    print "#################"

    ssh_cmd = remote_cmd(machine, test_cmd)

    if inter_machine:
      cmd = remote_cmd(inter_machine, ssh_cmd, inter_ssh_port)
    else:
      cmd = ssh_cmd

    p = os.popen(cmd, 'r')
    for line in p.readlines():
      if line.find('ACTIVE') == 0:
        sys.stdout.write('Warning: Machine %s in active state\n' % machine)
        if not force:
          sys.exit('Quitting.  Use --force flag to force clean.')

    p.close()

    ssh_cmd = remote_cmd(machine, raw_cmd)

    if inter_machine:
      cmd = remote_cmd(inter_machine, ssh_cmd, inter_ssh_port)
    else:
      cmd = ssh_cmd

    os.system(cmd)

if __name__ == '__main__':
  main(sys.argv[1:])

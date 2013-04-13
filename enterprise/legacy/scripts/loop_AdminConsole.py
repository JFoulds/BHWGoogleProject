#!/usr/bin/python2.4
#
# Copyright 2000-2003 Google, Inc.
#
'Runs GSE and stunnel in a loop.'

import sys
import os
import time
import commands

from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.scripts import check_healthz

True = 1
False = 0

# With the 5.2 release the settings on the GSA will contain
# alerts/personalization settings. This could get huge. So when an
# admin re-imports a "massive" configuration, they should be able to
# and the GSE should not crap out at get go. Note, the flag
# com.google.gse.GoogleServletEngine.maxpostsize is an integer and the
# max was can go upto is 2147483647.
GSE_MAXPOSTSIZE = 2147483647 # 2GB

def main(argv):
  # for cluster, gfs_aliases is passed as argv[6]
  if len(argv) != 7 and len(argv) != 8:
    sys.exit(__doc__)

  # gse_kill_command is roughly based on the babysitter's kill code.
  # The whole kill mechanism should be re-examined at some point.
  gse_kill_command = (
    'kill $(lsof -t -i :8000); sleep 3; '
    'kill -9 $(lsof -t -i :8000); sleep 3; '
    'kill -9 `ps axwwwwo pgid,pid,args | egrep "port=8000 " | egrep "java" | '
    'fgrep -v "egrep" | cut -b1-6 | sort -n | uniq | sed "s/[0-9]/-&/"`; ')

  if len(argv) == 8:
    gfs_aliases = argv[7]
  else:
    gfs_aliases = ''

  # LANG=en_US.utf-8 is specified so Java will use utf-8 as the default
  # encoding.
  # The maximum memory allowed for AdminConsole (-Xmx256m) directly
  # limits the size of import/export files supported. However, if it
  # set to 512m, other issues begin to appear, including adminrunner
  # timing out while processing the request.
  #
  # For the 1GB Lite virtual GSA, we do not specify any -Xm? flags

  # first, find out what product we are
  config = {}
  execfile('/etc/sysconfig/enterprise_config', config)
  ent_product = config.get('ENT_CONFIG_TYPE', '')

  gse_memory_flags = ' -Xms128m -Xmx256m '
  if ent_product == 'LITE':
    gse_memory_flags = ''

  gse_restart_command = (
    'su -c %s nobody' %
    commands.mkarg(
    'LD_LIBRARY_PATH=%s LANG=en_US.utf-8 '
    '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java '
    '%s -Dswigdeps=EnterpriseAdminConsole_swigdeps.so '
    '-classpath %s com.google.enterprise.servlets.EnterpriseAdminConsole '
    '--port=8000 '
    '--useripheader=X-User-Ip --secureheader=X-GFE-SSL --no_gwslog '
    '--maxthreads=3 '
    '--stderr_level=INFO %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s&')
    % (('%(ENTERPRISE_HOME)s/local/google/bin/EnterpriseAdminConsole_libs'
         % os.environ), # not mkarg, just a string for LD_LIBRARY_PATH
       gse_memory_flags, # not mkarg, just a string for -Xm? flags
    commands.mkarg(
      '%(ENTERPRISE_HOME)s/local/google:'
      '%(ENTERPRISE_HOME)s/local/google/bin/EnterpriseAdminConsole.jar'
    % os.environ),
    commands.mkarg(
    '--propertyfile=%(ENTERPRISE_HOME)s/local/conf/config.txt'
    % os.environ),
    commands.mkarg(
    '--contextbase=%(ENTERPRISE_HOME)s/local/googledata/html'
    % os.environ),
    commands.mkarg(
    '--ipwhitelist=%(ENTERPRISE_HOME)s/local/conf/AdminConsole_ipwhitelist'
    % os.environ),
    '--nowhitelist_internal_networks --forbidden_code=404', # /varz security
    commands.mkarg(
    '--maxpostsize=%s'
    % GSE_MAXPOSTSIZE),
    commands.mkarg(
    '--keystore=%(ENTERPRISE_HOME)s/local/conf/server.p12'
    % os.environ),
    commands.mkarg(
    '--trustedca_path=%(ENTERPRISE_HOME)s/local/conf/certs'
    % os.environ),
    commands.mkarg(
    '--crl_path=%(ENTERPRISE_HOME)s/local/conf/certs'
    % os.environ),
    commands.mkarg(
    '--connector_config_dir=%(ENTERPRISE_HOME)s/local/conf/connector/'
    % os.environ),
    commands.mkarg('--sso_rules_log_file=%s' %  argv[0]),
    commands.mkarg('--sso_log_file=%s' % argv[1]),
    commands.mkarg('--sso_serving_efe_log_file=%s' % argv[2]),
    commands.mkarg('--sso_serving_headrequestor_log_file=%s' % argv[3]),
    commands.mkarg('--gfs_aliases=%s' % gfs_aliases),
    commands.mkarg('--bnsresolver_use_svelte=false'),
    commands.mkarg('--external_web_ip=%s' % argv[4]),
    commands.mkarg('--sitesearch_interface=%s' % argv[5]),
    commands.mkarg('--license_notices=%s' % argv[6])))

  # Check stunnel config
  stunnel_config = ('''
    cert = %(ENTERPRISE_HOME)s/local/conf/certs/server.crt
    key = %(ENTERPRISE_HOME)s/local/conf/certs/server.key
    chroot = %(ENTERPRISE_HOME)s/tmp
    setuid = nobody
    setgid = nobody
    pid = /stunnel.pid
    socket = l:TCP_NODELAY=1
    socket = r:TCP_NODELAY=1
    debug = 7
    output = %(ENTERPRISE_HOME)s/logs/stunnel.log
    ciphers = HIGH:MEDIUM:!MD5:!RC4:!RC2:!EXP:@STRENGTH

    [https]
    accept  = 8443
    connect = 8000
  ''' % os.environ)
  stunnel_restart_command = (
    'kill $(lsof -t -i :8443); sleep 3; '
    'kill -9 $(lsof -t -i :8443); sleep 3; '
    'echo %s | stunnel -fd 0 ' %
    commands.mkarg(stunnel_config))

  pidfile = E.GetPidFileName('loop_AdminConsole')
  E.WritePidFile(pidfile)

  while True:
    # Check if GSE is running.
    if not check_healthz.CheckHealthz(8000):
      os.system(gse_kill_command)
      os.system(gse_restart_command)

    else:
      # Check if stunnel is running.
      stunnel_pid = E.ReadPidFile("%(ENTERPRISE_HOME)s/tmp/stunnel.pid" %
          os.environ)
      (status, output) = E.getstatusoutput("lsof -i:8443 -t")
      if not output or int(output) != stunnel_pid:
        os.system(stunnel_restart_command)

    # Sleep for a while.
    time.sleep(60)

if __name__ == '__main__':
  main(sys.argv[1:])

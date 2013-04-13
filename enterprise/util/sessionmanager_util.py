#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Module to provide Localbabysitter related commands for SessionManager

sessionmanager_util will be used as a binary to generate/start/stop the
sessionmanager on the box. This is specific to oneway as on clusters this task
was done using ent_core during activation.
"""

__author__ = 'vardhmanjain@google.com (Vardhman Jain)'

import os
import stat
import time

from google3.enterprise.core import core_utils
from google3.enterprise.util import localbabysitter_util
from google3.pyglib import logging

SESSIONMANAGER_BIN = 'sessionmanagerserver'

def ActivateSessionManager(ver, testver):
  """Generates the sessionmanager config file for localbabysitter.

  This method is meant exclusively for oneways for doing what ent_core does
  during activation. Its meant to just creat the file in /etc/localbabysitter.d
  which localbabysitter then uses to start the service.
  Args:
    ver: Version of GSA softare
    testver: If this version is in test mode
  """
  # we should run on a cluster
  # TODO (vardhman): consider removing core_utils.GetTotalNodes() it breaks
  # unittest for absense of /etc/sysconfig/enterprise_config file
  if core_utils.GetTotalNodes() != 1:
    return None

  # we first construct the sessionmanager-<version>.sh scrip
  # we are sure this is oneway, so we can call the is_cluster=0
  sm_prefix = core_utils.GetSessionManagerPrefix(is_cluster=0)
  lb_dict = {'ver': ver,
             'testver': testver,
             'sm_prefix': sm_prefix,
             'unq': ver.replace('.', '_'),
             'homedir': '/export/hda3/%s' % ver,
             'smport': core_utils.GetSessionManagerPort(testver),
             'trusted_clients': '127.0.0.1,216.239.43.0/24',
             }
  cmdline = ('%(homedir)s/local/google/bin/sessionmanagerserver '
             '--sessionmanager_port=%(smport)s '
             '--trusted_clients=%(trusted_clients)s '
             '--bnsresolver_use_svelte=false '
             '--svelte_servers=localhost:6297 '
             '--svelte_retry_interval_ms=214787777 '
             '--sessionmanager_prefix=%(sm_prefix)s '
             '--nobinarylog '
             #
             # TODO(josecasillas):  See "servertype_prod.py", for example...
             #
             # 'entconfig' is an EntConfig (entconfig.py) object, containing a
             #             dictionary (config.var) of global Enterprise params.
             #
             # Meanwhile, we hard code these file pathnames in line.
             #
             # In what follows, the "krb5.conf" line should be replaced with:
             #
             # entconfig.var('KERBEROS_KRB5_CONF') ' '
             #
             # ... and the "keytab" line should ultimately be replaced with:
             #
             # entconfig.var('KERBEROS_KRB5_KEYTAB') ' '  # Not this one, yet.
             #
             # ... but until the file sharing workaround is sorted out, it's:
             #
             # entconfig.var('KERBEROS_KEYTAB') ' '  # This is UI scratch copy.
             #
             '--kerberos_config_path='
             '%(homedir)s/local/conf/kerberos_krb5.conf.enterprise '
             # TODO(mrb):  For now, use single shared ``scratch'' keytab file.
             '--kerberos_keytab_path='
             '%(homedir)s/local/conf/kerberos_keytab.enterprise '
             % lb_dict)

  logging.info('Configuring Session Manager script')
  script = '#!/bin/bash\n%s' % cmdline
  script_file = '%(homedir)s/bin/sessionmanager-%(ver)s.sh' % lb_dict
  AtomicSaveFileWBackup(script_file, script)

  lb_util = localbabysitter_util.LocalBabysitterUtil(ver)
  lb_util.StartLBService('sessionmanager', SESSIONMANAGER_BIN, lb_dict)
  lb_util.ForceLocalBabysitterConfigReload()
  logging.info("Configured Session Manager successfully")

# copied from enterprise/core/ent_core.py
# make a time stamped backup of a file
def MakeBackup(fname):
  """Makes backup of a file. Preserves ownership and permission. Doesn't
  deal with filenames with spaces.
  """
  if os.path.exists(fname):
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
    core_utils.ExecCmd('cp -p %s /tmp/%s-%s' %
                       (fname, os.path.basename(fname), timestamp),
                       'Backing up %s.' % fname)

# copied from enterprise/core/ent_core.py
def AtomicSaveFileWBackup(fname, content):
  """Atomically changes the contents of a file and keeps a backup.
  Preserves file permissions and ownership.
  """
  MakeBackup(fname)
  # create a temporary file
  auxfname = fname + '.tomove'
  f = open(auxfname, 'w')
  f.write(content)
  f.flush()
  os.fdatasync(f.fileno())
  f.close()
  old_stats = os.stat(fname)
  # apply old permission bits and ownership
  os.chmod(auxfname, stat.S_IMODE(old_stats.st_mode))
  os.chown(auxfname, old_stats.st_uid, old_stats.st_gid)
  # rename temporary file to the actual file
  os.rename(auxfname, fname)

def DeactivateSessionManager(ver, testver):
  """Removes the session manager conf file from localbabysitter
  """
  lb_util = localbabysitter_util.LocalBabysitterUtil(ver)
  lb_util.KillLBService('sessionmanager', SESSIONMANAGER_BIN)
  lb_util.ForceLocalBabysitterConfigReload()
  logging.info("Stopped Session Manager successfully")

#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.

"""Takes backup of google_config file.

This script takes backup of google_config file. This script runs daily and
maintains last 21(default) valid copies of google_config file in
/export/hda3/<version>/data/googleconfig.bak directory. This script backs up
google_config of active version always.
"""

__author__ = 'gopinath@google.com (Gopinath Thota)'

import errno
import os
import shutil
import time

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.install import install_utilities
from google3.pyglib import flags
from google3.pyglib import logging


def GetFilesSortByDate(backup_dir):
  """Retruns list of files in backup_dir in ascending order
     (by last modified time).
  Args:
    backup_dir directory to list files from.
  Returns:
    returns list of files in backup_dir in ascending order
    (by last modified time).
  """
  file_list = os.listdir(backup_dir)
  cmp_mtime = lambda f1,f2: os.path.getmtime(f1)-os.path.getmtime(f2)

  sorted_files = []
  for file_name in file_list:
    abs_file_name = os.path.join(backup_dir, file_name)
    sorted_files.append(abs_file_name)

  sorted_files.sort(cmp_mtime)

  return sorted_files


def CleanOldFiles(backup_dir, max_backups, prefix):
  """Deletes old backup files if exist.
  Args:
     backup_dir directory where the backup files are stored.
     max_backups maximum number of backups that sbould be stored.
     prefix prefix of backed-up files.
  """
  backup_files = GetFilesSortByDate(backup_dir)

  # To avoid deleting other files, only files starting with
  # prefix should be delted.
  starts_with = os.path.join(backup_dir, prefix)
  related_backup_files = \
      [f for f in backup_files if f.startswith(starts_with)]

  for file_name in related_backup_files[:-max_backups]:
    logging.info('Removing old backup file %s' % file_name)
    os.remove(file_name)
  return True


def IsGoogleConfigValid(google_config):
  """Valid criteria for google_config is file-size should be non-zero.
  Args:
    google_config Name of the google_config file.

  Returns:
    True if config file is valid.
    False if config file is not valid.
  """
  try:
    size = os.path.getsize(google_config)
  except OSError, e:
    logging.error(str(e))
    return False

  # Check if the size of google config is non-zero
  if size == 0:
    logging.error('Size of google config file is 0')
    return False

  # Check if google config file valid python importable.
  try:
    google_config_dict = {}
    execfile(google_config, google_config_dict)
  except Exception, e:
    logging.error('google config is not a valid python file.')
    logging.error(str(e))
    return False
  return True


def BackupFile(file_name, backup_dir, prefix, max_backups):
  """
     Takes backup of file.
  Args:
    file_name name of the file to take backup.
    backup_dir directory to store backup files.
    prefix prefix of backed up files.
    max_backups maximum number of backups that should be stored.
  Returns
    True if file is backedup successfully.
    False if file is not backeup.
  """
  time_stamp = time.strftime('-%b-%d-%H:%M:%S')
  backup_file_name = os.path.join(backup_dir, '%s%s' % (prefix, time_stamp))
  logging.info('Creating Google Config backup file %s' % backup_file_name)

  try:
    os.makedirs(backup_dir)
  except OSError, e:
    if e.errno != errno.EEXIST:    # if directory exist error then no problem.
      logging.error(str(e))
      return False

  try:
    shutil.copy(file_name, backup_file_name)
  except IOError, e:
    logging.error(str(e))
    return False

  CleanOldFiles(backup_dir, max_backups, prefix)
  return True


def BackupGoogleConfigFile(config, backup_dir, max_backups=21):
  """Backsup google_config file if valid.
  Args:
    config entconfig object.
    backup_dir directory to store google_config backup file.
    max_backups maximum number of backups that should be stored.
                 default value is 21 (3 weeks).
  Returns
    True  if backup is successful.
    False if google_config is not backed up.
  """
  google_config = config.GetConfigFileName()

  if not IsGoogleConfigValid(google_config):
    return False

  prefix = 'google_config'
  return BackupFile(google_config, backup_dir, prefix, max_backups)


def main():
  latest_version = install_utilities.get_latest_version()
  ent_home = '/export/hda3/%s' % latest_version
  backup_dir = '/export/hda3/%s/data/googleconfig.bak' % latest_version
  log_file_name = '/export/hda3/tmp/google_config_backup.log'

  log_file = open(log_file_name, 'a')
  logging.set_logfile(log_file)

  config = entconfig.EntConfig(ent_home)
  number_of_backups = 21
  return BackupGoogleConfigFile(config, backup_dir, number_of_backups)


if __name__ == '__main__':
  main()

#!/usr/bin/python2.4
#
# Copyright 2006 Google Inc. All Rights Reserved.

"""Help create and Destroy a Chroot Jail for Stunnel."""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

import commands
import os
import popen2
import time

from google3.pyglib import logging

# add additional directories that need to be mounted as ro bound to root 
# WARNING!!!. Add only readonly or transient directories under this mount
JAIL_MOUNT_BINDS = ['/proc', '/dev/pts']
JAIL_MOUNT_RW_BINDS = []

# directories that need to be in the chroot jail
JAIL_SYSTEM_DIRS = ['/var/run', '/etc/ppp', '/dev/pts', '/lib', '/usr/sbin',
                    '/usr/lib', '/usr/bin', '/bin']

# files to be copied to the chroot jail
JAIL_SYSTEM_FILES = ['/usr/sbin/pppd', '/usr/lib', '/usr/lib/libpcap.so.0.9.4',
                     '/lib', '/lib/libutil.so.1', '/lib/libcrypt.so.1',
                     '/lib/libpam.so.0', '/lib/libdl.so.2', '/lib/libc.so.6',
                     '/lib/libaudit.so.0', '/lib/libtermcap.so.2',
                     '/lib/ld-linux.so.2', '/usr/sbin/stunnel',
                     '/usr/lib/libz.so.1', '/lib/libnsl.so.1',
                     '/lib/libssl.so.6', '/lib/libcrypto.so.6',
                     '/lib/libpthread.so.0', '/usr/lib/libwrap.so.0',
                     '/usr/lib/libgssapi_krb5.so.2', '/usr/lib/libkrb5.so.3',
                     '/lib/libcom_err.so.2', '/usr/lib/libk5crypto.so.3',
                     '/lib/libresolv.so.2', '/usr/lib/libkrb5support.so.0',
                     '/bin/sh']

# device files to be created - Device, mode, c
JAIL_DEVICE_FILES = ['/dev/ppp', '/dev/null', '/dev/ptmx', '/dev/urandom']
JAIL_DEVICE_WILDCARD_FILES = ['/dev/pty', '/dev/tty']


# System Commands
SYS_MKDIR        = 'mkdir'
SYS_MOUNT        = 'mount'
SYS_UMOUNT       = 'umount'
SYS_RMDIR        = 'rmdir'
SYS_MKNOD        = 'mknod -m %(MODE)s %(ROOT)s%(DEVICE)s c %(MAJOR)s %(MINOR)s'

# ERROR Codes
ERROR_MKNOD_FILE_EXISTS = 256


class SystemAbstraction(object):
  def Execute(self, command):
    return commands.getstatusoutput(command)
  
  def ExecuteInOut(self, command):
    return popen2.popen2(command)
  
  def ExistsPath(self, path):
    return os.path.exists(path)
  
  def OpenRead(self, file_name):
    return open(file_name, 'r')
  
  def OpenWrite(self, file_name):
    return open(file_name, 'w')
    

def GetSystemAbstraction():
  return SystemAbstraction()
  

class StunnelJail(object):
  """The utility class to create and maintain a chroot jail."""
  
  def __init__(self, root, sys_abstraction):
    self.__root = root
    self.__os = sys_abstraction
    self._MkDir(root)
  
  def CheckMounts(self, mount, mounted):
    """Check if a directory is already mounted or not.

    A typical response to the 'mount -l -t none' lists all the mounted
    points, where it is on the second column.
    /dev on /export/hda3/tmp/fed/dev type none (rw,bind)
    /bin on /export/hda3/tmp/fed/bin type none (rw,bind)
    
    Args:
      mount: The mount point to be checked.
      mounted: The response to a mount -l -t none.
    
    Returns:
      0 if found -1 if not.
    """
    list_mounts = mounted.rsplit('\n')
    for mount_line in list_mounts:
      mount_info = mount_line.rsplit(' ')
      if len(mount_info) > 3 and mount_info[2] == mount:
        return 0
    return -1

  def GetModeForString(self, mode):
    """Given the mode triad returns the octal."""
    if len(mode) == 3:
      return_val = 0
      if mode[0:1] == 'r':
        return_val |= 4
      if mode[1:2] == 'w':
        return_val |= 2
      if mode[2:3] == 'x':
        return_val |= 1
      return return_val
    return 0
      
    
  def ProcessModeString(self, mode):
    """Process mode string of a device file.
    
    Args:
      mode: string that specifies the permissions.
    
    Returns:
      None if the mode is invalid or device is not character
      or the permissions in octal format '666' for success.
    """
    if len(mode) == 10:
      device = mode[0:1]
      if device == 'c':
        owner = mode[1:4]
        group = mode[4:7]
        others = mode[7:10]
        owner_mode = self.GetModeForString(owner)
        group_mode = self.GetModeForString(group)
        others_mode = self.GetModeForString(others)
        return_val = ('%d%d%d') % (owner_mode, group_mode, others_mode)
        return return_val
    return None
      
  def ProcessLsCommandResponse(self, response):
    """Process the device detail response.
    
    Returns:
      Returns a dict of MODE, the MAJOR device number,
      the MINOR device number, the DEVICE name and the
      root of the chroot.
    """
    return_dict = {}
    response_list = response.split()
    if len(response_list) == 10:
      mode = self.ProcessModeString(response_list[0])
      if mode:
        return_dict['MODE'] = mode
        major_device_num = response_list[4]
        major_device_num = major_device_num[0:-1]
        return_dict['MAJOR'] = major_device_num
        minor_device_num = response_list[5]
        return_dict['MINOR'] = minor_device_num
        return_dict['DEVICE'] = response_list[9]
        return_dict['ROOT'] = self.__root
        return return_dict
    return None

  def GetDeviceListMatchingWildcard(self, pattern):
    """Get all Device names matching the pattern."""
    return_list = []
    ls_command = 'ls -1 %s*' % pattern
    (status, message) = self.__os.Execute(ls_command)
    if message:
      return_list = message.rsplit('\n')
    return return_list
    
  def CreateJailDeviceFile(self, device):
    """Create a device file inside the chroot jail.
    
    Args:
      device: The device file that will be created in jail.
      
    Returns:
      (1, 'Failure') for failures and or the mknod response.
    """
    ls_command = 'ls -l %s' % device
    (status, ls_response) = self.__os.Execute(ls_command)
    if not status and ls_response:
      command_dict = self.ProcessLsCommandResponse(ls_response)
      if command_dict:
        mknod_command = SYS_MKNOD % command_dict
        (status, mknod_response) = self.__os.Execute(mknod_command)
        return (status, mknod_response)
    return (1, 'Failed device file')
    
  def SetupJailDeviceFileSystem(self):
    """Create specific device files and wild cards under the jail."""
    return_status = (0, 'Success')
    for device_file in JAIL_DEVICE_FILES:
      (status, response) = self.CreateJailDeviceFile(device_file)
      if status and not (status == 256):
        return_status = (status, response)
        logging.error('Return status %d %s', status, response)
    
    for device_wildcard in JAIL_DEVICE_WILDCARD_FILES:
      device_file_list = self.GetDeviceListMatchingWildcard(device_wildcard)
      for device_file in device_file_list:
        (status, response) = self.CreateJailDeviceFile(device_file)
        if status and not (status == ERROR_MKNOD_FILE_EXISTS):
          return_status = (status, response)
          logging.error('Return status %d %s', status, response)
    return return_status

  def CopySystemFiles(self):
    """Copy system files to the chroot directory."""
    file_list = JAIL_SYSTEM_FILES
    for sys_file in file_list:
      if self.__os.ExistsPath(sys_file):
        command = 'cp -f %s %s/%s' % (sys_file, self.__root, sys_file)
        (create_status, message) = self.__os.Execute(command)
    verify_file_list = JAIL_SYSTEM_FILES
    for sys_file in file_list:
      if not self.__os.ExistsPath(sys_file):
        return (1, 'System file missing')
    return (0, 'Success')
    
  def _MkDir(self, directory):
    """Create a directory if not existing.
    
    Args:
      directory: The directory to be created.
    
    Returns:
      0, message on success and failure_status, message on failure.
    """
    sub_dirs = directory.rsplit('/')
    path = ''
    for sub_dir in sub_dirs:
      path = ('%s%s/') % (path, sub_dir)
      if not self.__os.ExistsPath(path):
        mkdir_command = ('%s %s') % (SYS_MKDIR, path)
        (status_mkdir, result) = self.__os.Execute(mkdir_command)
        if status_mkdir:
          return (status_mkdir, result)
    return (0, 'created or exists')
  
  def Setup(self, mounted_points=None):
    """Create the mount and system dirs and mount the directories.
    
    Args:
      mounted_points: If available send the list of mounted points in system.
      
    Returns:
      (0, message) on success or (failure_status, message) on failure.
    """
    if mounted_points is None:
      command = ('mount -l -t none')
      (status, mounted_points) = self.__os.Execute(command)  # discard status
          
    # handle all the ro mount points required in jail
    (status, result) = (0, 'Success')
    for mount in JAIL_MOUNT_BINDS:
      root_mount = ('%s%s') % (self.__root, mount)
      (status, result) = self._MkDir(root_mount)
      if status:
        logging.error('Root mount dir %s create failed with %d' %
                      (root_mount, status))
        break
      # mount if not already mounted
      if self.CheckMounts(root_mount, mounted_points):
        mount_command = ('%s -r -o bind %s %s') % (SYS_MOUNT, mount, root_mount)
        (status, result) = self.__os.Execute(mount_command)
        if status:
          logging.error('Mount command returned (%s,%s)' % (status, result))
          break
    if status:
      return (status, result)

    # handle all the rw mount points required in jail
    (status, result) = (0, 'Success')
    for mount in JAIL_MOUNT_RW_BINDS:
      root_mount = ('%s%s') % (self.__root, mount)
      (status, result) = self._MkDir(root_mount)
      if status:
        logging.error('Root mount dir %s create failed with %d' %
                      (root_mount, status))
        break
      # mount if not already mounted
      if self.CheckMounts(root_mount, mounted_points):
        mount_command = ('%s -w -o bind %s %s') % (SYS_MOUNT, mount, root_mount)
        (status, result) = self.__os.Execute(mount_command)
        if status:
          logging.error('Mount command returned (%s,%s)' % (status, result))
          break
    if status:
      return (status, result)

    # create all the system directories required in jail
    for mount in JAIL_SYSTEM_DIRS:
      root_mount = ('%s%s') % (self.__root, mount)
      (status, result) = self._MkDir(root_mount)
      if status:
        return (status, result)
    
    # Copy all the required system files into the created jail
    (status, result) = self.CopySystemFiles()
    if status:
      logging.error('Copy System Files returned with %d %s', status, result)
      return (status, result)
    
    # Create the device file system under the chroot
    (status, result) = self.SetupJailDeviceFileSystem()
    if status:
      logging.error('Create DevFS returned with %d %s', status, result)
      return (status, result)
    return (status, result)
    
  def Destroy(self):
    """Unmount the mounted directories and remove the dirs under chroot."""
    retry_count = 3
    while retry_count:
      (in_use, process_list) = self.IsUsed()
      if in_use:
        logging.info('Chroot in use, stop processes using it')
        status_stop = self.StopProcesses(process_list)
        retry_count -= 1
        time.sleep(1)
      else:
        break
    (in_use, process_list) = self.IsUsed()
    if in_use:
      logging.error('Unable to umount the directories')
      return (-1, 'Failed to unmount directories')
    return_status = 0
    return_message = 'Success'
    for mount in JAIL_MOUNT_RW_BINDS:
      root_mount = ('%s%s') % (self.__root, mount)
      umount_command = ('%s %s') % (SYS_UMOUNT, root_mount)
      (status_umount, result) = self.__os.Execute(umount_command)
      if status_umount:
        return_status = status_umount
        return_message = result
        logging.error('Umount the bind mount %s failed with %s' %
                      (root_mount, result))
    for mount in JAIL_MOUNT_BINDS:
      root_mount = ('%s%s') % (self.__root, mount)
      umount_command = ('%s %s') % (SYS_UMOUNT, root_mount)
      (status_umount, result) = self.__os.Execute(umount_command)
      if status_umount:
        return_status = status_umount
        return_message = result
        logging.error('Umount the bind mount %s failed with %s' %
                      (root_mount, result))
    return (return_status, return_message)

  def IsUsed(self):
    """Check if the chroot is being used.
    
    Returns:
    (0, []) - no processes using it , (-1, list of using processes.
    """
    command = 'lsof +d %s' % self.__root
    (status , results) = self.__os.Execute(command)
    logging.info(results)
    list_response = results.rsplit('\n')
    return_list = []
    for record in list_response:
      if record:
        list_fields = record.split()
        if len(list_fields) > 2 and list_fields[1]:
          if not list_fields[1] == 'PID':
            return_list.append(list_fields[1])
    if len(return_list):
      logging.info('Chroot in In use with %s' % str(return_list))
      return -1, return_list
    else:
      logging.info('Chroot not In use')
      return 0, return_list
  
  def StopProcesses(self, process_list):
    return_status = 0
    for process in process_list:
      command = 'kill -15 %s' % process
      (status, result) = self.__os.Execute(command)
      if status:
        return_status = -1
        logging.error('Kill of process %s failed' % process)
    return return_status

if __name__ == '__main__':
  logging.set_verbosity(logging.INFO)


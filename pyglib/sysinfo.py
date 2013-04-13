# pylint: disable-msg=C6302
#
# Copyright 2006 Google Inc.
# All Rights Reserved.
#
# Original Author: Mark D. Roth
#

"""Functions that provide system information.

These functions mimic some of the functions provided in
google3/base/sysinfo.{cc,h}.

Not all of the functions present there have been implemented here; only
the ones for which there has been a need, or which were simple to
implement.
"""

import os
import resource


class SysInfoError(Exception):
  """Exception class."""
  pass


###############################################################################
###  utility methods
###############################################################################

def _Int(value):
  try:
    return int(value)
  except ValueError, e:
    raise SysInfoError('can\'t convert result to int: %s' % e)


def _Float(value):
  try:
    return float(value)
  except ValueError, e:
    raise SysInfoError('can\'t convert result to float: %s' % e)


def _ProcFilename(filename, pid):
  """Helper for _ReadProcField() and _ReadProcKeyword()."""
  if filename.find('%d') >= 0:
    if pid is None:
      pid = os.getpid()
    filename = filename % pid
  filename = '/proc/' + filename
  return filename


def _ReadProcField(filename, pid, field):
  """Returns the specified field from the specified proc file.

  Args:
    filename: path of file, relative to '/proc'
    pid:      if filename contains the string '%d', it will be replaced
              with this value.  if pid is None, os.getpid() is used.
    field:    the field offset to return

  Returns:
    The contents of the specified field.
  """
  filename = _ProcFilename(filename, pid)
  try:
    f = file(filename, 'r')
    contents = f.read()
    f.close()
    return contents.split()[field]
  except IOError:
    raise SysInfoError('cannot read %s' % filename)
  except IndexError:
    raise SysInfoError('cannot find field %d in %s' % (field, filename))


def _ReadProcKeyword(filename, pid, keyword):
  """Returns the specified keyword value from the specified proc file.

  Scans a /proc file for a line starting with the specified keyword, and
  returns the value to the right of the keyword on the same line.

  Args:
    filename: path of file, relative to '/proc'
    pid:      if filename contains the string '%d', it will be replaced
              with this value.  if pid is None, os.getpid() is used.
    keyword:  the keyword to search for.

  Returns:
    The value to the right of the keyword on the first line containing
    the keyword.
  """
  filename = _ProcFilename(filename, pid)
  try:
    try:
      f = file(filename, 'r')
      for line in f:
        if line.startswith(keyword):
          return line[len(keyword):].strip()
      else:
        raise SysInfoError('keyword %s not found in %s' % (keyword, filename))
    finally:
      f.close()
  except IOError:
    raise SysInfoError('cannot read %s' % filename)


###############################################################################
###  system info (not associated with an individual process)
###############################################################################

def CPUSpeed():
  """Returns a list containing the speed in MHz of each (logical) CPU."""
  # TODO(roth): this is much more complicated in the C++ code...
  f = file('/proc/cpuinfo', 'r')
  cpus = []
  for line in f:
    if line.find('MHz') >= 0:
      cpus.append(_Float(line.split()[-1]))
  return cpus


def NumCPUs():
  """Number of logical CPUs in system.

  On systems with hyperthreading this may be greater than (e.g. double)
  the number of physical CPUs.
  See also: NumPhysicalCPUs().

  Returns:
    The number of logical CPUs.
  """
  return len(CPUSpeed())


def NumPhysicalCPUs():
  """Number of physical CPU cores in system.

  May be lower than the number of logical CPUs if the system supports
  hyperthreading.
  See also: NumCPUs().

  Returns:
    The number of physical CPU cores.
  """
  f = file('/proc/cpuinfo', 'r')
  physical_cpus = []
  for line in f:
    if line.find('physical id') >= 0:
      physical_id = _Int(line.split()[-1])
      if not physical_cpus.count(physical_id):
        physical_cpus.append(physical_id)
  num_physical_cpus = len(physical_cpus)
  if num_physical_cpus:
    return num_physical_cpus
  else:
    return NumCPUs()


def ProcessorUsage():
  """Returns the 1-minute load average."""
  # TODO(roth): C++ version uses sysinfo(2) so that it works even when
  # /proc is not mounted (e.g., a chroot'ed server)
  return _Float(_ReadProcField('loadavg', None, 0))


def PhysicalMem():
  """The amount of physical memory available on a machine in bytes."""
  out = _ReadProcKeyword('meminfo', None, 'MemTotal:')
  out = out.split()[0]  # result is '#### kB'
  return _Int(out) * 1024


def FreeMem():
  """Amount of free memory in bytes."""
  mem = 0
  f = file('/proc/meminfo', 'r')
  for line in f:
    for keyword in ('MemFree:', 'Buffers:', 'Cached:'):
      if line.startswith(keyword):
        mem += _Int(line.split()[1])
  f.close()
  return mem * 1024


def BootTime():
  """System boot time."""
  return _Int(_ReadProcKeyword('stat', None, 'btime'))


###############################################################################
###  per-process info
###############################################################################

def MemoryUsage(pid=None):
  """Memory usage (RSS) in bytes of the specified (or current) process.

  Args:
    pid: a process id, or 'None'.

  Returns:
    The memory usage (RSS) in bytes of the specified process, or of
    the current process if pid is not specified.
  """
  # TODO(roth): We should really be using resource.getrusage() here,
  # but it doesn't work under Linux.  The getrusage(2) man page says:
  #
  #   The above struct was taken from BSD 4.3 Reno.  Not all fields are mean-
  #   ingful  under  Linux.   Right now (Linux 2.4) only the fields ru_utime,
  #   ru_stime, ru_minflt, ru_majflt, and ru_nswap are maintained.
  #
  # Also, from the Linux proc(5) man page:
  #
  #   Resident Set Size: number of  pages  the  process
  #   has  in  real  memory, minus 3 for administrative
  #   purposes. This is  just  the  pages  which count
  #   towards  text,  data,  or stack space.  This does
  #   not include pages which  have  not  been demand-
  #   loaded in, or which are swapped out.
  #
  out = _Int(_ReadProcField('%d/stat', pid, 23))
  return (out + 3) * resource.getpagesize()


def VirtualMemorySize(pid=None):
  """Virtual memory size of the specified (or current) process.

  Args:
    pid: a process id, or 'None'.

  Returns:
    The virtual memory size of the specified process (or the
    current process, if pid is not specified).
    Raises SysInfoError on error (e.g. if the process doesn't exist).
  """
  return _Int(_ReadProcField('%d/stat', pid, 22))


def ProcessParent(pid=None):
  """pid of parent of the given process."""
  return _Int(_ReadProcKeyword('%d/status', pid, 'PPid:'))


def Nice():
  """Nice level of the current process."""
  # Note: We can't use os.nice() here, since it always returns 0 due to a
  # problem with the version of glibc we run in production.
  return _Int(_ReadProcField('%d/stat', None, 18))


def MyCPUUsage():
  """Returns CPU usage for the current process."""
  try:
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r[0] + r[1]
  except resource.error, e:
    raise SysInfoError('getrusage() failed: %s' % e)


def NumOpenFDs():
  """Returns the number of open file descriptors for the current process."""
  proc_dir = '/proc/%d/fd' % os.getpid()
  try:
    return len(os.listdir(proc_dir))
  except OSError, e:
    raise SysInfoError('could not read directory %s: %s' % (proc_dir, e))

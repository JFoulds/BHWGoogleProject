#!/usr/bin/python2.4
#
# (c) 2001 Google inc
# cpopescu@google.com
#
###############################################################################

"""
Usage:
  ent_exec.py [-s|-q|-p <procs>|-b|-d <delay>|-m <hosts>|-h] [-x command | -f file(s)]
   -h           This help.
   -w           It's OK if a password/passphrase is required for ssh.
   -b           Barrier. Wait for children to finish before returning.
   -s           Run on each machine sequentially.  Normal behavior is
                to run each command in the background.
   -q           Do not print \"Executing XXX\" for each host.
   -a <delay>   Wrap the rsync in an alarm with the specified timeout.
   -p <procs>   Do not run more than <procs> processes at once.
   -d <delay>   Delay to wait between succesive cmds (default: 0)
   -m <machine> A single machine to run the command on.  Can be specified
                more than once.
   -i <count>   Number of failures to ignore. Default is 0.
   -f <file(s)> Rsync a files
   -x <command> Execute the command
"""

###############################################################################

import sys
import os
import string
import getopt
import time
import commands
import threading
import sitecustomize

from google3.pyglib import logging

###############################################################################

BATCHMODE_YES = "-o BatchMode=yes"
BATCHMODE_NO  = "-o BatchMode=no"

#
# Some options
#
BATCHMODE            = BATCHMODE_YES
QUIET                = 0
BARRIER              = 0
ALARM                = ""
DELAY                = 0

# We get this rsync error if the source file doesn't exist.
RSYNC_PARTIAL_TRANSFER_ERROR = 23

def python_exec_wrapper(command):
  '''
  python_exec_wrapper resets the signal mask because non-main threads in Python
  2.2 block SIGPOLL. Some programs such as ntpdate and rsync expect SIGPOLL to
  be unblocked.  python_exec_wrapper allows Python 2.2 programs to run these
  programs from non-main threads.
  '''
  return '%s/google2/bin/python_exec_wrapper /bin/sh -c %s' % (
    sitecustomize.GOOGLEBASE, commands.mkarg(command))

class Runner(threading.Thread):
  def __init__(self, n,  machines, command, files, num_threads):
    threading.Thread.__init__(self)
    self.n = n
    self.machines = machines
    self.command = command
    self.files = files
    self.err = 0
    self.num_threads = num_threads

  def run(self):
    i = self.n
    while i < len(self.machines):
      machine = self.machines[i]
      i = i + self.num_threads

      cmds = []
      if self.command:
        cmds.append("ssh %s -n %s %s" % (BATCHMODE, machine,
                                             commands.mkarg(self.command)))
      if self.files:
        cmds.extend(map(
          lambda f, m = machine: "rsync -u -e \"ssh %s\" -aH %s %s:%s" % (
          BATCHMODE, f, m, f),
          string.split(self.files," ")))

      for cmd in cmds:
        cmd = "%s%s" % (ALARM, cmd)
        # Run and get the error
        if not QUIET:
          logging.info("%s: Executing [%s]." % (self.n, cmd))
        this_err = os.system(python_exec_wrapper(cmd))
        if this_err:
          # Divide by 256 to get error code from the exit status.
          this_err = this_err >> 8
          if self.files:  # we were doing an rsync
            if this_err == RSYNC_PARTIAL_TRANSFER_ERROR:
              # If the file went missing then we didn't need the transfer
              # anyway, so we just continue.
              logging.warn('%s: File does not exist.' % self.n)
              continue
          logging.error("%s: Error %d." % (self.n, this_err))
          self.err = this_err
          break

      if DELAY:
        time.sleep(DELAY)

###############################################################################

def main(argv):

  global BATCHMODE, QUIET, DELAY, BARRIER, ALARM

  machines    = []
  command     = None
  files       = None
  ignore      = 0
  threads     = 0
  try:
    opts, args = getopt.getopt(argv, "hwbsqi:a:p:d:f:m:x:", [])
    for (opt, arg) in opts:
      if   opt == "-h":   sys.exit(__doc__)
      elif opt == "-w":   BATCHMODE   = BATCHMODE_NO
      elif opt == "-s":   threads = 1
      elif opt == "-q":   QUIET       = 1
      elif opt == "-b":   BARRIER     = 1
      elif opt == "-p":   threads     = int(arg)
      elif opt == "-a":   ALARM       = "alarm %d " % int(arg)
      elif opt == "-m":   machines    = string.split(arg, " ")
      elif opt == "-i":   ignore      = int(arg)
      elif opt == "-x":   command     = arg
      elif opt == "-f":   files       = arg
      elif opt == "-d":   DELAY       = int(arg)
  except:
    sys.exit(__doc__)

  if 0 == len(machines):
    return


  # see how many threads to spawn
  if threads == 0 or len(machines) < threads:
    threads = len(machines)

  # Save threads when we have to wait the ending
  if BARRIER:
    num_to_run = threads - 1
  else:
    num_to_run = threads

  # Create the threads
  list_threads = []
  for n in range(0, threads):
    list_threads.append(Runner(n, machines, command, files, threads))

  # start the threads
  for thread in list_threads[0:num_to_run]:
    thread.start()

  if BARRIER:
    list_threads[-1].run()

  err = 0
  failed = 0
  if BARRIER:
    # wait for them
    for thread in list_threads:
      if thread in list_threads[0:num_to_run]:
        thread.join()
      if thread.err != 0:
        failed += 1
        terr = 0
        if os.WIFEXITED(thread.err):
          terr = os.WEXITSTATUS(thread.err)
        else:
          terr = thread.err
        err = err or terr
  if failed <= ignore:
    err = 0
  sys.exit(err)

###############################################################################

if __name__ == '__main__':
  main(sys.argv[1:])

#!/usr/bin/python2.4
# (c) 2002 Google inc
# cpopescu@google
#
# Creates and deletes data directories
#
#############################################################################

import sys
import string
from google3.enterprise.legacy.util import E
from google3.enterprise.legacy.util import C
from google3.pyglib import logging

#############################################################################

true  = 1
false = 0

#############################################################################

def create(linkFarmDir,
           chunkDisksMap, chunkPrefix, chunkTermination,
           binDir,
           machines):
  """
  This does the create job.
   @param linkFarmDir the directory where is the link frm. Here we create
     a data link, a log dir and log dir
   @param chunkDisks the map from machines to datadisks
   @param chunkPrefix
   @param chunkTermination the dir termination
   @param machines on which machines we create this datadir

   @return boolean - the succes status
  """
  ok = 1

  for machine in machines:
    if not chunkDisksMap.has_key(machine):
      logging.error(
        "ERROR: No entry for machine %s in data chunk disk map %s" % (
        machine, chunkDisksMap))
      ok = 0
      continue

    chunkDisks = chunkDisksMap[machine]

    # Prepare search.config content
    searchConfig = []
    searchConfig.append("""datapath %s
urlbuckets urlbuckets
sorttempdir .
""" % chunkTermination)

    dirs  = []
    for d in ["-data", "-data/logs", "-data/%s" % C.RUNCONFIGDIR_DIRNAME]:
      dirs.append("%s/%s%s" % (linkFarmDir, chunkTermination, d))

    for d in chunkDisks:
      searchConfig.append("disk %s/%s 1000\n" % (d, chunkPrefix))
      dirs.append("%s/%s/%s" % (d, chunkPrefix, chunkTermination))
      dirs.append("%s/%s/workqueue" % (d, chunkPrefix))
      dirs.append("%s/%s/workqueue/bin" % (d, chunkPrefix))

    if ( not E.mkdir([machine], string.join(dirs, " ")) or
         not E.ln([machine],
                  "%s/%s-data" % (linkFarmDir, chunkTermination),
                  "%s/%s-data/data" % (linkFarmDir, chunkTermination)) ):
        return false

    # create the search.config and distribute it
    fileName = "%s/%s-data/search.config" % (linkFarmDir,
                                             chunkTermination)
    tmpFile = "/tmp/search.config.tmp-%s" % chunkTermination;
    try:
      open(tmpFile, "w").write(string.join(searchConfig, ""))
      if ( E.ERR_OK != E.distribute([machine], tmpFile, 1) or
           E.ERR_OK != E.execute([machine],
                                 "mv -f %s %s" % (tmpFile, fileName),
                                 None, true) ):
        ok = 0
      E.rm([E.LOCALHOST, machine], tmpFile)
    except IOError:
      ok = 0

    # set up link in workqueue slave binary directory (bin) to workqueue-slave
    # binary so that workqueue-slave can checksum/update itself
    for d in chunkDisks:
      if not E.ln([machine],
                  '%s/workqueue-slave' % binDir['workqueue-slave'],
                  '%s/%s/workqueue/bin/current' % (d, chunkPrefix)):
        ok = 0

  return ok;

def delete(linkFarmDir,
           chunkDisksMap, chunkPrefix, chunkTermination,
           machines):
  """
  This does the delete job..

  @param linkFarmDir the directory where is the link frm. Here we create
  a data link, a log dir and log dir
  @param chunkDisks the map from machines to datadisks
  @param chunkPrefix
  @param chunkTermination the dir termination
  @param machines - on which machines we create this

  @return boolean - the succes status
  """
  ok = 1
  for machine in machines:
    if not chunkDisksMap.has_key(machine): continue

    chunkDisks = chunkDisksMap.get(machine)

    dirs = []
    for d in chunkDisks:
      dirs.append("%s/%s/%s" % (d, chunkPrefix, chunkTermination))

    dirs.append("%s/%s-data" % (linkFarmDir, chunkTermination))
    if not E.rmallfast([machine], dirs):
      ok = 0

  return ok

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")

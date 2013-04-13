#!/bin/bash
#
# this script executes a binary in a loop which will restart the binary if
# the binary has exited for any reason.  the script has options for specifying 
# the location of the binary, what directory to execute in, whether to execute
# a python script or a java binary. But the flags for specifying whether it's
# running a python or java program (--python2 and --java) are deprecated. The
# right way to do it now is to use the --exec flag. For example, to run
# fooserver.py:
#
#   loop.sh --exec=/usr/bin/python fooserver.py ...
#
# and to run a java binary of fooserver.jar:
#
#   loop.sh --exec='/usr/bin/java -jar' fooserver.jar ...
#
# this script replaces all the loop.[server] scripts in which code
# was duplicated in many files.  thus you will notice
# there is a lot of hardcoding in "startbin" for different types
# of servers.  these hardcodings should be kept to a minimum in the future and
# the different flags should be used instead.
#
# the main functional changes have been to start everything in the "bin"
# directory unless overridden and to inherit the ulimit from the shell
# instead of forcing it to 0 like many old loop.sh's used to do.
# However, hopefully these are both backwards compatible because
# binaries can run in any directory and testserver was sending
# the ulimit commands when necessary anyway.
#
# NOTE:
#
# If you make any changes that will produce external side effects like
# touch'ing or chmod'ing files, wrap those commands in a wrapper function and
# call the wrapper function instead. This way, we can do some basic unit tests
# without actually messing with the system. Take a look at one of the wrapper
# functions like _mkdir and _chmod.

# location of account management prodsu
PRODSU=/usr/local/bin/prodsu

# variable declarations for some default settings

UPDATE_LOCK_PROGRAM=/root/google3/enterprise/legacy/setup/update_lock.py
GOOGLEDIR=/root/google
HOST=$(hostname)
LOOP_USER=$(id -un)

# just print out the actual command that would be executed without actually
# running it. Also, all commands that involve side-effect are trapped to just
# print out what they would do instead of doing it. Finally, some sanity checks
# like existence of file/directory are skipped in test mode.
testmode=false

# in verbose mode, print out what we're doing as we do it. Note that if
# testmode is true, this is ignored.
verbose=false

# default location to find specified binary
bindir=$GOOGLEDIR/bin

# default location for binary to execute is always bindir unless set explicitly
rundir=

# default location for log files
logdir=/export/hda3/tmp

# default is to loop
doloop=true

# default initial sleep time
sleeptime=1

# default max sleep time
sleeptimemax=10

# rate at which the sleep time decays cut off by max sleep time
sleepdecay=2

# save output of binary to log file? if false send it to /dev/null
logoutput=true

# exec mods - set these to things to precede execution i.e. "nohup nice"
binmods=

# the actual command to execute. If this is null, then the binary is the
# executable
exec_cmd=

# set this to true if trying to execute a java program
dojava=false

# user running the program.  If this is null, then the binary is
# run as the user executing loop.sh.
user=

# group used for file permissions when user is set to a non-null value.
group=

# classpath for java program
javacp=.:bin/adjava.jar:./mysql.jar

# library path for java program
javald=./bin:/usr/java/jdk1.3/lib/i386/:$bindir

# package path for java program, e.g. com/google/common
# Example usage: loop.sh --java --javapp=com/google/common GoogleServer ...
# This will cause com/google/common/GoogleServer to be executed, but the
# logbinname will be GoogleServer.
javapp=

# flags to pass to java when running program
javaflags="-Xmx900m "

# which python program to use - default is python, but may be set to python2
pythonprog="python"

# something to add to the log file names (usually nothing)
lognamesuffix=

##############################################################################
# Wrapper functions
# The purpose of these functions are to wrap any calls that produce external
# side effects like chmod and writing to disk. With these, we can easily do
# testing without actually producing those side effects.

_chmod() {
  side_effect_cmd_wrapper chmod "$@"
}

_chown() {
  side_effect_cmd_wrapper chown "$@"
}

_touch() {
  side_effect_cmd_wrapper touch "$@"
}

_mkdir() {
  side_effect_cmd_wrapper mkdir "$@"
}

_cd() {
  side_effect_cmd_wrapper cd "$@"
}

_rm() {
  side_effect_cmd_wrapper rm "$@"
}

_ulimit() {
  side_effect_cmd_wrapper ulimit "$@"
}

_mv() {
  side_effect_cmd_wrapper mv "$@"
}

_ln() {
  side_effect_cmd_wrapper ln "$@"
}

# End of wrapper functions
##############################################################################

side_effect_cmd_wrapper() {
  if istestmode; then
    testprint "FAKE: $@"
  else
    print_if_verbose "$@"
    eval "$@"
  fi
}

istestmode() {
  if [ "$testmode" = "true" ]; then
    return 0  # 0 for success
  else
    return 1  # non-zero for failure
  fi
}

#
# use this to print stuff to stderr when in test mode
#
testprint() {
  echo "TESTMODE: $*" 1>&2
}

#
# print stuff to stderr if in verbose mode. Otherwise, do nothing.
#
print_if_verbose() {
  if [ "$verbose" = "true" ]; then
    echo "$*" 1>&2
  fi
}

#
# get a command string that is to be run as another user.
# give user and command as args.
#
get_command_as_user() {
  if [ "$testmode" != "true" ] && [ -x $PRODSU ]; then
    echo $PRODSU $1 sh -c \"$2\"
  elif [ "$user" = "$LOOP_USER" ]; then
    echo sh -c \"$2\"
  else
    echo su $1 -c \"$2\"
  fi
}

#
# handle per binary specific starting parameters.  this function is called
# once each time before the executable is run in the loop. this is for 
# hardcoding different behaviors for servers.
#
startbin() {

  binname=$1; shift

  case $binname in
  directoryserver)
    # before starting directory server, HUP apache to release
    # connection it thinks it has opened to an earlier directoryserver
    killall -HUP httpd
    start_server $binname "$@"
    ;;

  *) 
    start_server $binname "$@"
    ;;
  esac
    
}

#
# start server and generate log files.
#
start_server() {
  binname=$1; shift

  # ensure executable exists
  if ! istestmode; then
    if [ "$dojava" != "true" -a ! -s $binpath ]; then
      log "binary '$binpath' does not exist."
    fi
  fi

  # generate log name
  logprefix=$logdir/$logbinname.${HOST}
  if [ "$port" != "" ]; then
    logprefix=$logprefix.$port
  fi
  time=`date +%Y-%m-%d.%H`;
  curlog=$logprefix.$time

  # ensure log dir exists and has proper ownership/permissions
  # we jump through the chown loops to ensure we can set permissions
  # since prodsetup cannot chmod.

  _mkdir -p $logdir
  _chown $LOOP_USER $logdir
  _chmod +rwx,+t $logdir
  _chown root:root $logdir 2> /dev/null
  if ! istestmode; then
    if [ ! -d $logdir ]; then
      log "log directory '$logdir' does not exist."
    fi
  fi

  # try and touch and change permission of logfile - ignore errors
  # because this log may already be owned by the binary user
  _touch $curlog >& /dev/null || true
  _chown $LOOP_USER $curlog
  _chmod +rw $curlog

  # determine where to send output to
  outlog="$curlog"
  if [ "$logoutput" = "false" ]; then
    outlog=/dev/null
  fi
  if ! istestmode; then
    if [ ! -f $curlog ]; then
      outlog=/dev/null
    fi
  fi

  # test whether it is really possible to run as other user
  if [ "$user" != "" ]; then
    if [ "$exec_cmd" = "" ]; then
      exec_file="$binpath"
    else
      # the first argument of exec_cmd is the executable file. so take out
      # everything after the first space.
      exec_file=${exec_cmd%% *}
    fi

    if istestmode; then
      testprint "Would have tested if runnable as user"
    else
      test_cmd="$(get_command_as_user $user "test -x $exec_file && echo ok")"
      if [ ! $(eval "$test_cmd") = ok ]; then
        error "unable to run as $user"
      fi
    fi
  fi

  # user specific settings
  if [ "$user" != "" ]; then
    # chown log just in case to be owned by the binary user.
    _chown $user:$group $curlog
    # chown other log links as a stop-gap for transition.
    _chown -f $user:$group \
      $logdir/$binname.{INFO,FATAL,ERROR,WARNING,BINARY_INFO}

  fi

  # Make sure our process can obtain lots of fd's
  #
  # We use the /proc/sys/fs/file-nr data to compute a large but safe
  # per-process FD limit. We want to give a process as many fds as
  # possible but still reserve a few for the rest of the system so
  # that a runaway process can't eat all fds and prevent ssh to
  # connect for example (thus, effectively, killing the machine)
  #
  # Note: The numbers of open fds in a system can be arbitrarily
  #       large! There is a 64k limit for the number of fds that can
  #       be used in a select() call but as long as you are not
  #       using select() you can use as many fds as you want.
  # Note2: we reserve 1000 fds for all other processes in the system
  #        (we assume not more than 1 runaway process per machine)
  # Note3: the per-process fd limit should be lower than the
  #        system-wide limit (/proc/sys/fs/file-max) or the change
  #        won't matter anyway.
  # TODO: add the "-t 3" option back in once we use bash2 everywhere
  read allocated_fds unused_fds system_max_fds < /proc/sys/fs/file-nr
  if [ -n "$system_max_fds" ]; then
    # we've parsed file-nr data correctly. Use it.
    numusedfds=$[$allocated_fds - $unused_fds]   # num of fds actually in use
    process_max_fd=$[ $system_max_fds - $numusedfds - 1000 ]  # safe limit
  fi
  if [ ${process_max_fd:-0} -lt 50000 ]; then
    # something went wrong with file-nr parsing (most likely, the
    # format changed or file-nr no longer exists) or the computed
    # limit is too low (due to some fd hog). Use some large value
    # instead (hopefully, smaller than /proc/sys/fs/file-max limit)
    process_max_fd=50000
  fi
  _ulimit -HSn $process_max_fd

  # The core story: we try to dump core unless there's not enough space
  # free, or there's already a recent core.  The former keeps us from
  # filling up disk, the latter from spending all our time dumping core.
  # ulimit is inherited from the shell - if it is 0 it is kept at 0
  # else it is set to unlimited

  ulimit=`ulimit -Hc`
  if [ "$ulimit" = "unlimited" ] || [ $ulimit -ne 0 ]; then
    ulimit="unlimited"

    # test for free space
    # -P forces the df output to always be a single line per mountpoint
    if [ `df -k -P . | awk '{print $4}' | tail -n1` -lt 256000 ]; then
      log "warning: not enough disk space for core, setting ulimit to 0"
      ulimit="0"
    fi
    if [ `df -k -P $logdir | awk '{print $4}' | tail -n1` -lt 256000 ]; then
      log "warning: not enough disk space in $logdir for core, setting ulimit to 0"
      ulimit="0"
    fi

    if [ -s $logdir/core.$binname ]; then   # we renamed from core to core.{binname}
      if [ `date +%s -r $logdir/core.$binname` -gt `date +%s -d "7 days ago"` -a \
           `date +%s -r $logdir/core.$binname` -gt `date +%s -r $binpath` ]; then
        ulimit="0"                   # don't overwrite our recent core
      fi
    fi

    _rm -f core  # probably garbage; *we* rename to core.{binname}

    # Other users doesn't have write permissions, so set up an accessible file
    if [ "$user" != "" ]; then
      _touch core                  # only create if we're willing to dump core
      _chown $user:$group core     # now user can write to the core
    fi
  fi

  # set run command handle cases for java, python and regular binaries.
  if [ "$exec_cmd" != "" ]; then
    if istestmode; then
      testprint "WOULD LOG: `date`: starting in $rundir: $exec_cmd $binpath $*"
    else
      echo "`date`: starting in $rundir: $exec_cmd $binpath $*" >> $curlog
    fi
    cmd="$exec_cmd $binpath $*"
  elif [ "$dojava" = "true" ]; then
    if istestmode; then
      testprint "WOULD LOG: `date`: starting ${binname} in ${rundir} $*"
    else
      echo "`date`: starting ${binname} in ${rundir} $*" >> $curlog
    fi
    cmd="export LD_LIBRARY_PATH=$javald && export CLASSPATH=$javacp && java $javaflags $binname $*"
  else
    if istestmode; then
      testprint "WOULD LOG: `date`: starting ${binpath} $*"
    else
      echo "`date`: starting ${binpath} $*" >> $curlog
    fi
    case $binname in
      *.py) 
        cmd="$pythonprog -u $binpath $*"
        ;;
      *)
        cmd="$binpath $*"
        ;;
    esac
  fi

  # execute command
  if [ "$user" != "" ]; then
    # We ulimit after su, since su resets ulimit to 0 under bash 1.x.
    # Note that this won't work if the ulimit was previously lowered 
    # by root (as happened on some machines in /etc/profile).
    final_cmd=$(get_command_as_user $user "ulimit -Sc $ulimit && $binmods $cmd >> $outlog 2>&1")
  else
    final_cmd="ulimit -Sc $ulimit && $binmods $cmd >> $outlog 2>&1"
  fi

  if istestmode; then
    testprint "CMD: $final_cmd"
  else
    print_if_verbose "$final_cmd"
    eval "$final_cmd"
  fi

  # core related post-processing
  if [ -s core ] ; then
    # Probably, core is owned by prodbin, and we are prodsetup.
    # Make ourselves the owner of the core file, otherwise we will
    # have problems later because $logdir has the sticky bit set.
    _chown $LOOP_USER core $logdir/core.$binname
    # save away core, if we crashed
    _mv -f core $logdir/core.$binname
    # create symlink so people know where the core went
    _ln -s $logdir/core.$binname core.$binname
  fi
}

#
# usage
#
usage() {
  echo "usage: $0 [options] <binary> <binary's arguments ... >"
  echo ""
  echo "  options:"
  echo ""
  echo "  --testmode (print out the actual command that would be executed"
  echo "              without actually running it.)"
  echo "  --verbose (verbose output. This is ignored if --testmode is specified.)"
  echo "  --exec=<cmd> (the command to execute. If not specified, execute"
  echo "                the binary)"
  echo "  --bindir=<dir> (dir where binary is found)"
  echo "  --rundir=<dir> (dir in which to execute binary - defaults to bindir)"
  echo "  --user=<user> (user to execute binary as - if dif't from loop owner)"
  echo "  --group=<group> (group for file permissions - defaults to prim group)"
  echo "  --nobody (try and run as nobody - DEPRECATED use --user)"
  echo "  --logdir=<dir> (dir in which to place logs)"
  echo "  --noloop (do not loop)"
  echo "  --sleeptime=<secs> (sleep time between execs - lengthens by 2 every iter. till max)"
  echo "  --sleeptimemax=<secs> (max sleep time between execs)"
  echo "  --binmods=<cmd> (these are prepended to the binary exec cmd)"
  echo "  --nooutput (output of binary directed to /dev/null instead of logs)"
  echo "  --java (the binary specified is actually a java class name)"
  echo "  --javacp=<classpath> (classpath to use for java program)"
  echo "  --javald=<ldpath> (ld library path to use for java program)"
  echo "  --javapp=<package path> (package java program belongs to, e.g. com/google/common)"
  echo "  --javaflags=<flags> (flags to send to java when executing class)"
  echo "  --python2 (use python2 instead of python)"
  echo "  --lognamesuffix=<suffix> (something to add to the log name)"
  echo ""
  echo "$0 executes a binary, python script (detected by .py extension)"
  echo "or java program (use --java flag) in a loop so that"
  echo "if the program is killed or crashes, it will be restarted.  The script"
  echo "also takes care of logging information of the program and moving old"
  echo "log files out of the way.  To hardcode some behavior for specific"
  echo "binaries, edit startbin() in this script."
  echo "Default behavior is below:"
  echo ""
  echo "  look in $bindir for binary (--bindir or full path of bin to override)"
  echo "  run binary in $bindir (--rundir to override)"
  echo "  log directory is $logdir (--logdir to override)"
  echo ""
  echo "NOTE:  even if you override some of the options, they may have no"
  echo "effect for a particular server since they are hardcoded in startbin"
  echo "in this script for backwards compatibility.  Most of these"
  echo "hard codings probably should be removed."
  echo ""

  exit 1
}

#
# log to system log
#
log() {
  if istestmode; then
    testprint "log(): $@"
  else
    print_if_verbose "$@"
    /usr/bin/logger -p local1.info -t loop.$binname "$@"
  fi
}

#
# error
#
error() {
  log "ERROR: $@"
  echo $@ 1>&2
  exit 2
}

#
# main code
#

# Check if loop is disabled.
if [ -x $UPDATE_LOCK_PROGRAM ]; then
  $UPDATE_LOCK_PROGRAM loop check
  case $? in
    0)   ;;
    255) error "Loop is disabled" ;;
    *)   log "Update lock returned unexpected status: $?" ;;
  esac
fi  

# TEMPORARY HACK FOR AM TRANSITION: If we come in as prodadmin
# then rerun this script as root so that we can continue to run binaries
# that only run properly as root while slowly converting binaries
# to run as prodbin.  Once all binaries are running as prodbin,
# and the babysitter is running as prodsetup, this can be removed.
# It's not clear we'll actually take this approach (rather than
# continuing to run the babysitter as root, or just biting the
# bullet and running it as prodsetup), but this code is here just
# in case.
if [ "$LOOP_USER" = "prodadmin" ] && [ "$1" != "--changeuser" ]; then
  sudo sh -c "$0 --changeuser $*"
  exit $?
fi

binary=""

# these command line options are for backwards compatibility 
# and should not be used.
case $1 in
   -binpath=*) bindir=`echo $1 | sed 's/-binpath=//'`; shift;;
   -path=*)
     path=`echo $1 | sed 's/-path=//'`;
     if [ "$path" = "${path#\/}" ]; then
       bindir=$rundir/$path;
     else
       rundir=$(dirname $path);
       bindir=$path;
     fi
     shift;;
  -binary=*) binary=`echo $1 | sed 's/-binary=//'`; shift;;
esac;

# set command line options
while true; do
  case $1 in
    --*) case $1 in
         --testmode) testmode=true;;
         --verbose) verbose=true;;
         --exec=*) exec_cmd=`echo $1 | sed 's/--exec=//'`;;
         --bindir=*) bindir=`echo $1 | sed 's/--bindir=//'`;;
         --rundir=*) rundir=`echo $1 | sed 's/--rundir=//'`;;
         --user=*) user=`echo $1 | sed 's/--user=//'`;;
         --group=*) group=`echo $1 | sed 's/--group=//'`;;
         --logdir=*) logdir=`echo $1 | sed 's/--logdir=//'`;;
         --noloop) doloop=false;;
         --sleeptime=*) sleeptime=`echo $1 | sed 's/--sleeptime=//'`;;
         --sleeptimemax=*) sleeptimemax=`echo $1 | sed 's/--sleeptimemax=//'`;;
         --binmods=*) binmods=`echo $1 | sed 's/--binmods=//'`;;
         --nooutput) logoutput=false;;
         --nobody) user=nobody;;
         --java) dojava=true;;
         --javacp=*) javacp=`echo $1 | sed 's/--javacp=//'`;;
         --javald=*) javald=`echo $1 | sed 's/--javald=//'`;;
         --javapp=*) javapp=`echo $1 | sed 's/--javapp=//'`;;
         --javaflags=*) javaflags=`echo $1 | sed 's/--javaflags=//'`;;
         --python2) pythonprog="python2";;
         --lognamesuffix=*) 
             lognamesuffix=`echo $1 | sed 's/--lognamesuffix=//'`;;
         --changeuser) ;;
         *) usage;;
         esac;
         shift;;
    *) break;;
  esac
done

if [ "$*" = "" ]; then
  usage
fi
  
# set binary name
if [ "$binary" = "" ]; then
  binary=$1;
fi

shift

# if binary starts with a / means it is absolute -> change bindir
case $binary in
  /*) bindir=$(dirname $binary);;
esac

binname=$(basename $binary)

# Binary name for logfile use - this should be same as binname
# usually.
# Sometimes it will have a suffix added to it as a command line option
# to the loop
logbinname=$binname

if [ "$lognamesuffix" != "" ]; then
  logbinname="$logbinname.$lognamesuffix"
fi

# build full java class name if --javapp is used
if [ "$dojava" = "true" -a "$javapp" != "" ]; then
  binname="${javapp%/}/$binname"
fi

# cd into assumed rundir
if [ "$rundir" = "" ]; then
  _cd $bindir || log "cannot cd into $rundir.";
else
  _cd $rundir || log "cannot cd into $rundir.";
fi

binpath="$bindir/$binname"

# move into the target run directory if specified
if [ "$rundir" = "" ]; then
  rundir=$bindir
fi

_cd $rundir || log "cannot cd into $rundir.";

# save start time
loopstarttime=`date +%s`

# extract port number from command line, so we can add the portnum to
# our log file names, allowing us to run multiple shards on same machine
port=`echo $* | sed -ne 's/.*-port=\([0-9][0-9]*\).*/\1/p'`

# try and set group if user is specified and group is not specified.
if [ "$user" != "" ] && [ "$group" = "" ]; then
  group=$(id -gn $user) || error "cannot find group for $user";
fi

# start the restart loop
while true; do

  # log checksum
  if ! istestmode; then
    if [ "$dojava" != "true" ]; then
      s=`fileprint.py $binpath | awk '{print $NF}'`
    else
      s=na
    fi
  fi

  log "starting $binname binary fileprint:$s"

  # start the binary
  startbin $binname $@

  if [ "$doloop" != "true" ]; then
    break
  fi

  sleep $sleeptime
  sleeptime=`expr $sleeptime \* $sleepdecay`
  if [ $sleeptime -gt $sleeptimemax ]; then
    sleeptime=$sleeptimemax
  fi

done


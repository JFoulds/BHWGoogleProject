//
// Copyright (C) 2000 and onwards Google, Inc.
//
// Author: Craig Silverstein
//
// Returns the date and time the executable was built.
// We never make an object file out of this (since then we'd be
// recording the date and time the object file was built), which
// is why this tiny function is in a file of its own.
//
// This will also return the version of the binary as well as the
// version of everything it was built against (only meaningful in
// google3).
//
// These strings are used directly as an exported variable.
// It's also used with the "V" prefix to a commands, as a versioning
// system.
//
// This system works best when you pass in the build-time using
// the macro BUILD_TIMESTAMP, when linking in timestamp.cc.
//
// To not rely on the timezone PST/PDT being set on the build host, you should
// also pass in the clear text date and time for the Google standard timezone
// (i.e. PST/PDT) as BUILD_DATE_TIME_PST, which should have the form '"Aug 3
// 2006 15:45:38"' (including the double quotes!).  (Another minor glitch is
// that without passing in BUILD_DATE_TIME_PST, the clear text date and time
// will differ from the numerical timestamp, because the latter is passed in as
// BUILD_TIMESTAMP, while the former is generated via preprocessor macros
// __TIME__ and __DATE__ if no BUILD_DATE_TIME_PST is passed in.)
//
// Passing in BUILD_CHANGELIST, BUILD_CLIENT_MINT_STATUS,
// BUILD_CLIENT, and BUILD_DEPOT_PATH can be helpful too, and is
// easily done in google3 via the '-b' flag to
// make-opt/make-dbg. BUILD_LABEL can also be defined via the '-l'
// flag. When these flags are not passed, the variables are given
// empty definitions by base/BUILD.
//
// If you're using the build changelist to ensure a repeatable build
// of a binary, you probably don't want to pull in anything from
// /home/build/google3.  To avoid that, the '--package_path' flag to
// gconfig is helpful, as in 'tools/gconfig
// --package_path=.:/home/build/google3_releases'.

#include <time.h>
#include <string.h>
#include "base/timestamp.h"

#ifndef COMPILE_CACHE

#define AS_STRING2(x) #x
#define AS_STRING(x)  AS_STRING2(x)

#ifndef BUILD_TIMESTAMP
# error Must specify -DBUILD_TIMESTAMP=`date +%s` when linking in timestamp.cc
#endif

#ifndef BUILD_INFO
# error Must specify -DBUILD_INFO=`whoami`@`hostname`:`pwd` when linking in timestamp.cc
#endif

#ifndef BUILD_LABEL
# error Must specify -DBUILD_LABEL=... when linking in timestamp.cc
#endif

#ifndef BUILD_DEPOT_PATH
# error Must specify -DBUILD_DEPOT_PATH="<path>" when liking in timestamp.cc
#endif

#ifndef G3_VERSION_INFO
# error Must specify -DG3_VERSION_INFO=... when linking in timestamp.cc
#endif

#ifndef G3_TARGET_NAME
# error Must specify -DG3_TARGET_NAME=... when linking in timestamp.cc
#endif

#ifndef G3_BUILD_TARGET
# error Must specify -DG3_BUILD_TARGET=... when linking in timestamp.cc
#endif

#ifndef GPLATFORM
#define GPLATFORM "Unknown. Are you using an old gconfig?"
#endif

#ifndef __DATE__
# define __DATE__ "<unknown_date>"
#endif

#ifndef __TIME__
# define __TIME__ "<unknown_time>"
#endif

#ifndef BUILD_TOOL
# define BUILD_TOOL "<unknown>"
#endif

#ifndef BUILD_DATE_TIME_PST
// fallback to bad old behavior (not timezone safe, not in sync with
// BUILD_TIMESTAMP):
# define BUILD_DATE_TIME_PST __DATE__ " " __TIME__
#endif

#ifndef BUILD_CHANGELIST
# define BUILD_CHANGELIST -1  // as good as undefined
#endif

#ifndef BUILD_CLIENT_MINT_STATUS
# define BUILD_CLIENT_MINT_STATUS -2  // as good as undefined
#endif

static const char buildinfo_str[] = AS_STRING(BUILD_INFO);

static const char buildtool_str[] = BUILD_TOOL;

static const char buildlabel_str[] = BUILD_LABEL;

// make-dbg|make-opt don't pass -DBUILD_CLIENT unless -b or -ocl is used
#ifdef BUILD_CLIENT
static const char buildclient_str[] = BUILD_CLIENT;
#else
static const char buildclient_str[] = "";
#endif

static const char timestamp_str[] =
"Built on " BUILD_DATE_TIME_PST " (" AS_STRING(BUILD_TIMESTAMP) ")";

static time_t timestamp_as_int = BUILD_TIMESTAMP;

const char* BuildData::StaticLibPath() {
#ifdef STATIC_LIB_PATH
  return STATIC_LIB_PATH;
#else
  return NULL;
#endif
}

#else   /* COMPILE_CACHE */

// The following three static data items are modified post-link by the
// build/build_stamp tool after the final link has completed.  In this
// way, the compile/link cache can store fully linked executables, serve
// them to users, and then attach the build-audit information afterward.
//
// Note that string variables intended for patching with build_stamp
// should be declared as char arrays, and not like 'char * foo = "___"'.
// In the latter case, the compiler has the right to coalesce equivalent
// strings in the .rodata section, and the value of 'foo' as a symbol
// is the address of a pointer variable which points to the string data.
// Declared as arrays, the symbols indicate the address of the first
// element, which is what we want.
//
// The build_stamp tool won't write over anything that's not a continuous
// array of '_' characters, and ints should be initialized to zero.  This
// provides a bit of defense against corruption.


static char buildinfo_str[] =
    "____________________________________________________________________________________________________\0";
static char timestamp_str[] =
    "______________________________________________________________________\0";
static time_t timestamp_as_int = 0;


const char* BuildData::StaticLibPath() {
#ifdef STATIC_LIB_PATH
  // Currently I'm hoping that no-one compiles completely static
  // binaries via the compile cache (since it doesn't appear to be
  // supported under google3 anyway). If this error occurs please
  // contact menage@google.com and I'll change build_stamp
#error Static binaries not currently supported via compile cache
#else
  return NULL;
#endif
}

#endif  /* COMPILE_CACHE */

const char* BuildData::BuildInfo() {
  return buildinfo_str;
}

const char* BuildData::BuildTool() {
  return buildtool_str;
}

const char* BuildData::BuildDir() {
  const char* dir = strchr(buildinfo_str, ':');
  // Empty case should not really happen: see -DBUILD_INFO in base/BUILD
  return dir ? dir + 1 : "";
}

static char build_host_str[100];

const char* BuildData::BuildHost() {
  const char* b = strchr(buildinfo_str, '@');
  if (b == NULL) return "";
  b = b + 1;
  const char* e = strchr(buildinfo_str, ':');
  if (e == NULL) return "";
  if (e-b > sizeof(build_host_str) - 1) {
    return NULL;  // oveflow: should never happen
  }
  memcpy(build_host_str, b, e-b);
    // a thread race here is not a problem: we always write the same things
  // 0-initialization of build_host_str ensures 0-termination
  return build_host_str;
}

// We already quote this before passing it into the linker, since it
// might have //'s in it, which are significant to the preprocessor.
static const char builddata_buildtarget[] = G3_BUILD_TARGET;
// NOTE: We could assemble the data for BuildTarget()
//       from pieces of TargetName(), GPlatform(), NDEBUG
//       and the knowledge of how our build system places the binaries
//       it makes, but it would be a bad far dependency on gconfig/make-dbg.
const char* BuildData::BuildTarget() {
  return builddata_buildtarget;
}

const char* BuildData::BuildLabel() {
  if (buildlabel_str[0] != '\0') {
    return buildlabel_str;
  } else {
    return NULL;
  }
}

const char* BuildData::BuildClient() {
  if (buildclient_str[0] != '\0') {
    return buildclient_str;
  } else {
    return NULL;
  }
}

const char* BuildData::Timestamp() {
  return timestamp_str;
}

time_t BuildData::TimestampAsInt() {
  return timestamp_as_int;
}

// The //tools:build_stamp tool will only write over fields
// of underscores.  We set up one of these to receive the 
// MPM version number, if/when this binary is introduced into
// that system.

static char mpm_version_str[] = "________________________________";

const char* BuildData::MpmVersion() { 
  return mpm_version_str;
}

const char* BuildData::MpmVersionIfSet() { 
  if (mpm_version_str[0] == '_') {
    return NULL;
  } else {
    return mpm_version_str;
  }
}

static char unstripped_location[] = 
"____________________________________________________________________________________________________"
"____________________________________________________________________________________________________";

const char *BuildData::UnstrippedLocation() {
  if (unstripped_location[0] == '_') {
    return NULL;
  } else {
    return unstripped_location;
  }
}

#define STRINGIFY2(x) #x
#define STRINGIFY(x)  STRINGIFY2(x)

const char* BuildData::Changelist() {
#if BUILD_CHANGELIST == -1
  return NULL;
#elif BUILD_CHANGELIST == 0
  return "<unknown>";
#else
  return STRINGIFY(BUILD_CHANGELIST);
#endif
}

int BuildData::ChangelistAsInt() {
#if BUILD_CHANGELIST > 0
  return BUILD_CHANGELIST;
#else
  return -1;
#endif
}

BuildData::ClientStatusType BuildData::ClientStatus() {
#if BUILD_CLIENT_MINT_STATUS == 1
  return MINT;
#elif BUILD_CLIENT_MINT_STATUS == 0
  return MODIFIED;
#else
  return UNKNOWN;
#endif
}

const char* BuildData::ClientStatusAsString() {
#if BUILD_CLIENT_MINT_STATUS == 1
  return "mint";
#elif BUILD_CLIENT_MINT_STATUS == 0
  return "modified";
#else
  return "unknown";
#endif
}

const char* BuildData::BuildDepotPath() {
  // We already quote this before passing it into the linker, since it
  // has //'s in it, which are significant to the preprocessor.
  return BUILD_DEPOT_PATH;
}

const char* BuildData::ClientInfo() {
#if BUILD_CHANGELIST == -1
  return NULL;
#elif BUILD_CHANGELIST == 0
  return "unknown changelist";
#else
  return "changelist " STRINGIFY(BUILD_CHANGELIST)
# if BUILD_CLIENT_MINT_STATUS == 1
         " in a mint client based on " BUILD_DEPOT_PATH
# elif BUILD_CLIENT_MINT_STATUS == 0
         " in a modified client based on " BUILD_DEPOT_PATH
# else
         " possibly in a modified client"
# endif
  ;
#endif
}

// We already quote this before passing it into the linker, since it
// has //'s in it, which are significant to the preprocessor.
static const char builddata_targetname[] = G3_TARGET_NAME;
const char* BuildData::TargetName() {
  return builddata_targetname;
}

// This is not affected by the compile cache
const char* BuildData::VersionInfo() {
  // We already quote this before passing it into the linker, since it
  // has commas and //'s in it, which are significant to the
  // preprocessor.
  return G3_VERSION_INFO;
}

const char* BuildData::GPlatform() {
  return GPLATFORM;
}

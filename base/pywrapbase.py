# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _base_pywrapbase

def _swig_setattr(self,class_type,name,value):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    self.__dict__[name] = value

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


class stringVector(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, stringVector, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, stringVector, name)
    def __repr__(self):
        return "<C std::vector<(string)> instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, stringVector, 'this', _base_pywrapbase.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_base_pywrapbase.stringVector_swigregister(stringVectorPtr)


InitGoogleScript = _base_pywrapbase.InitGoogleScript

InitGoogleExceptChangeRootAndUserScript = _base_pywrapbase.InitGoogleExceptChangeRootAndUserScript

ParseCommandLineFlagsScript = _base_pywrapbase.ParseCommandLineFlagsScript

SetArgvScript = _base_pywrapbase.SetArgvScript
class CommandLineFlagInfo(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CommandLineFlagInfo, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CommandLineFlagInfo, name)
    def __repr__(self):
        return "<C CommandLineFlagInfo instance at %s>" % (self.this,)
    __swig_setmethods__["name"] = _base_pywrapbase.CommandLineFlagInfo_name_set
    __swig_getmethods__["name"] = _base_pywrapbase.CommandLineFlagInfo_name_get
    if _newclass:name = property(_base_pywrapbase.CommandLineFlagInfo_name_get, _base_pywrapbase.CommandLineFlagInfo_name_set)
    __swig_setmethods__["type"] = _base_pywrapbase.CommandLineFlagInfo_type_set
    __swig_getmethods__["type"] = _base_pywrapbase.CommandLineFlagInfo_type_get
    if _newclass:type = property(_base_pywrapbase.CommandLineFlagInfo_type_get, _base_pywrapbase.CommandLineFlagInfo_type_set)
    __swig_setmethods__["description"] = _base_pywrapbase.CommandLineFlagInfo_description_set
    __swig_getmethods__["description"] = _base_pywrapbase.CommandLineFlagInfo_description_get
    if _newclass:description = property(_base_pywrapbase.CommandLineFlagInfo_description_get, _base_pywrapbase.CommandLineFlagInfo_description_set)
    __swig_setmethods__["current_value"] = _base_pywrapbase.CommandLineFlagInfo_current_value_set
    __swig_getmethods__["current_value"] = _base_pywrapbase.CommandLineFlagInfo_current_value_get
    if _newclass:current_value = property(_base_pywrapbase.CommandLineFlagInfo_current_value_get, _base_pywrapbase.CommandLineFlagInfo_current_value_set)
    __swig_setmethods__["default_value"] = _base_pywrapbase.CommandLineFlagInfo_default_value_set
    __swig_getmethods__["default_value"] = _base_pywrapbase.CommandLineFlagInfo_default_value_get
    if _newclass:default_value = property(_base_pywrapbase.CommandLineFlagInfo_default_value_get, _base_pywrapbase.CommandLineFlagInfo_default_value_set)
    __swig_setmethods__["filename"] = _base_pywrapbase.CommandLineFlagInfo_filename_set
    __swig_getmethods__["filename"] = _base_pywrapbase.CommandLineFlagInfo_filename_get
    if _newclass:filename = property(_base_pywrapbase.CommandLineFlagInfo_filename_get, _base_pywrapbase.CommandLineFlagInfo_filename_set)
    __swig_setmethods__["is_default"] = _base_pywrapbase.CommandLineFlagInfo_is_default_set
    __swig_getmethods__["is_default"] = _base_pywrapbase.CommandLineFlagInfo_is_default_get
    if _newclass:is_default = property(_base_pywrapbase.CommandLineFlagInfo_is_default_get, _base_pywrapbase.CommandLineFlagInfo_is_default_set)
    __swig_setmethods__["has_validator_fn"] = _base_pywrapbase.CommandLineFlagInfo_has_validator_fn_set
    __swig_getmethods__["has_validator_fn"] = _base_pywrapbase.CommandLineFlagInfo_has_validator_fn_get
    if _newclass:has_validator_fn = property(_base_pywrapbase.CommandLineFlagInfo_has_validator_fn_get, _base_pywrapbase.CommandLineFlagInfo_has_validator_fn_set)
    def __init__(self, *args):
        _swig_setattr(self, CommandLineFlagInfo, 'this', _base_pywrapbase.new_CommandLineFlagInfo(*args))
        _swig_setattr(self, CommandLineFlagInfo, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_CommandLineFlagInfo):
        try:
            if self.thisown: destroy(self)
        except: pass

class CommandLineFlagInfoPtr(CommandLineFlagInfo):
    def __init__(self, this):
        _swig_setattr(self, CommandLineFlagInfo, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, CommandLineFlagInfo, 'thisown', 0)
        _swig_setattr(self, CommandLineFlagInfo,self.__class__,CommandLineFlagInfo)
_base_pywrapbase.CommandLineFlagInfo_swigregister(CommandLineFlagInfoPtr)

RegisterFlagValidator = _base_pywrapbase.RegisterFlagValidator


GetAllFlags = _base_pywrapbase.GetAllFlags

ShowUsageWithFlags = _base_pywrapbase.ShowUsageWithFlags

ShowUsageWithFlagsRestrict = _base_pywrapbase.ShowUsageWithFlagsRestrict

DescribeOneFlag = _base_pywrapbase.DescribeOneFlag

SetArgv = _base_pywrapbase.SetArgv

GetArgvs = _base_pywrapbase.GetArgvs

GetArgv = _base_pywrapbase.GetArgv

GetArgv0 = _base_pywrapbase.GetArgv0

GetArgvSum = _base_pywrapbase.GetArgvSum

ProgramInvocationName = _base_pywrapbase.ProgramInvocationName

ProgramInvocationShortName = _base_pywrapbase.ProgramInvocationShortName

ProgramUsage = _base_pywrapbase.ProgramUsage

GetCommandLineOption = _base_pywrapbase.GetCommandLineOption

GetCommandLineFlagInfo = _base_pywrapbase.GetCommandLineFlagInfo

GetCommandLineFlagInfoOrDie = _base_pywrapbase.GetCommandLineFlagInfoOrDie
SET_FLAGS_VALUE = _base_pywrapbase.SET_FLAGS_VALUE
SET_FLAG_IF_DEFAULT = _base_pywrapbase.SET_FLAG_IF_DEFAULT
SET_FLAGS_DEFAULT = _base_pywrapbase.SET_FLAGS_DEFAULT

SetCommandLineOption = _base_pywrapbase.SetCommandLineOption

SetCommandLineOptionWithMode = _base_pywrapbase.SetCommandLineOptionWithMode
class FlagSaver(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FlagSaver, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FlagSaver, name)
    def __repr__(self):
        return "<C FlagSaver instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FlagSaver, 'this', _base_pywrapbase.new_FlagSaver(*args))
        _swig_setattr(self, FlagSaver, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_FlagSaver):
        try:
            if self.thisown: destroy(self)
        except: pass

class FlagSaverPtr(FlagSaver):
    def __init__(self, this):
        _swig_setattr(self, FlagSaver, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FlagSaver, 'thisown', 0)
        _swig_setattr(self, FlagSaver,self.__class__,FlagSaver)
_base_pywrapbase.FlagSaver_swigregister(FlagSaverPtr)


CommandlineFlagsIntoString = _base_pywrapbase.CommandlineFlagsIntoString

ReadFlagsFromString = _base_pywrapbase.ReadFlagsFromString

AppendFlagsIntoFile = _base_pywrapbase.AppendFlagsIntoFile

SaveCommandFlags = _base_pywrapbase.SaveCommandFlags

ReadFromFlagsFile = _base_pywrapbase.ReadFromFlagsFile

BoolFromEnv = _base_pywrapbase.BoolFromEnv

Int32FromEnv = _base_pywrapbase.Int32FromEnv

Int64FromEnv = _base_pywrapbase.Int64FromEnv

Uint64FromEnv = _base_pywrapbase.Uint64FromEnv

DoubleFromEnv = _base_pywrapbase.DoubleFromEnv

StringFromEnv = _base_pywrapbase.StringFromEnv

SetUsageMessage = _base_pywrapbase.SetUsageMessage

ParseCommandLineNonHelpFlags = _base_pywrapbase.ParseCommandLineNonHelpFlags

HandleCommandLineHelpFlags = _base_pywrapbase.HandleCommandLineHelpFlags

AllowCommandLineReparsing = _base_pywrapbase.AllowCommandLineReparsing

ReparseCommandLineNonHelpFlags = _base_pywrapbase.ReparseCommandLineNonHelpFlags
class FlagRegisterer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FlagRegisterer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FlagRegisterer, name)
    def __repr__(self):
        return "<C FlagRegisterer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FlagRegisterer, 'this', _base_pywrapbase.new_FlagRegisterer(*args))
        _swig_setattr(self, FlagRegisterer, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_FlagRegisterer):
        try:
            if self.thisown: destroy(self)
        except: pass

class FlagRegistererPtr(FlagRegisterer):
    def __init__(self, this):
        _swig_setattr(self, FlagRegisterer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FlagRegisterer, 'thisown', 0)
        _swig_setattr(self, FlagRegisterer,self.__class__,FlagRegisterer)
_base_pywrapbase.FlagRegisterer_swigregister(FlagRegistererPtr)

INFO = _base_pywrapbase.INFO
WARNING = _base_pywrapbase.WARNING
ERROR = _base_pywrapbase.ERROR
FATAL = _base_pywrapbase.FATAL
NUM_SEVERITIES = _base_pywrapbase.NUM_SEVERITIES

FlushLogFiles = _base_pywrapbase.FlushLogFiles

FlushLogFilesUnsafe = _base_pywrapbase.FlushLogFilesUnsafe

SetLogDestination = _base_pywrapbase.SetLogDestination

SetLogSymlink = _base_pywrapbase.SetLogSymlink

SetLogFilenameExtension = _base_pywrapbase.SetLogFilenameExtension

SetStderrLogging = _base_pywrapbase.SetStderrLogging

LogToStderr = _base_pywrapbase.LogToStderr

SetEmailLogging = _base_pywrapbase.SetEmailLogging

StatusMessage = _base_pywrapbase.StatusMessage

GWQStatusMessage = _base_pywrapbase.GWQStatusMessage

LogMessageScript = _base_pywrapbase.LogMessageScript
class BuildData(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, BuildData, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, BuildData, name)
    def __repr__(self):
        return "<C BuildData instance at %s>" % (self.this,)
    __swig_getmethods__["BuildInfo"] = lambda x: _base_pywrapbase.BuildData_BuildInfo
    if _newclass:BuildInfo = staticmethod(_base_pywrapbase.BuildData_BuildInfo)
    __swig_getmethods__["BuildTool"] = lambda x: _base_pywrapbase.BuildData_BuildTool
    if _newclass:BuildTool = staticmethod(_base_pywrapbase.BuildData_BuildTool)
    __swig_getmethods__["BuildDir"] = lambda x: _base_pywrapbase.BuildData_BuildDir
    if _newclass:BuildDir = staticmethod(_base_pywrapbase.BuildData_BuildDir)
    __swig_getmethods__["BuildHost"] = lambda x: _base_pywrapbase.BuildData_BuildHost
    if _newclass:BuildHost = staticmethod(_base_pywrapbase.BuildData_BuildHost)
    __swig_getmethods__["BuildTarget"] = lambda x: _base_pywrapbase.BuildData_BuildTarget
    if _newclass:BuildTarget = staticmethod(_base_pywrapbase.BuildData_BuildTarget)
    __swig_getmethods__["BuildLabel"] = lambda x: _base_pywrapbase.BuildData_BuildLabel
    if _newclass:BuildLabel = staticmethod(_base_pywrapbase.BuildData_BuildLabel)
    __swig_getmethods__["BuildClient"] = lambda x: _base_pywrapbase.BuildData_BuildClient
    if _newclass:BuildClient = staticmethod(_base_pywrapbase.BuildData_BuildClient)
    __swig_getmethods__["Timestamp"] = lambda x: _base_pywrapbase.BuildData_Timestamp
    if _newclass:Timestamp = staticmethod(_base_pywrapbase.BuildData_Timestamp)
    __swig_getmethods__["MpmVersion"] = lambda x: _base_pywrapbase.BuildData_MpmVersion
    if _newclass:MpmVersion = staticmethod(_base_pywrapbase.BuildData_MpmVersion)
    __swig_getmethods__["MpmVersionIfSet"] = lambda x: _base_pywrapbase.BuildData_MpmVersionIfSet
    if _newclass:MpmVersionIfSet = staticmethod(_base_pywrapbase.BuildData_MpmVersionIfSet)
    __swig_getmethods__["TimestampAsInt"] = lambda x: _base_pywrapbase.BuildData_TimestampAsInt
    if _newclass:TimestampAsInt = staticmethod(_base_pywrapbase.BuildData_TimestampAsInt)
    __swig_getmethods__["StaticLibPath"] = lambda x: _base_pywrapbase.BuildData_StaticLibPath
    if _newclass:StaticLibPath = staticmethod(_base_pywrapbase.BuildData_StaticLibPath)
    __swig_getmethods__["Changelist"] = lambda x: _base_pywrapbase.BuildData_Changelist
    if _newclass:Changelist = staticmethod(_base_pywrapbase.BuildData_Changelist)
    __swig_getmethods__["ChangelistAsInt"] = lambda x: _base_pywrapbase.BuildData_ChangelistAsInt
    if _newclass:ChangelistAsInt = staticmethod(_base_pywrapbase.BuildData_ChangelistAsInt)
    MINT = _base_pywrapbase.BuildData_MINT
    MODIFIED = _base_pywrapbase.BuildData_MODIFIED
    UNKNOWN = _base_pywrapbase.BuildData_UNKNOWN
    __swig_getmethods__["ClientStatus"] = lambda x: _base_pywrapbase.BuildData_ClientStatus
    if _newclass:ClientStatus = staticmethod(_base_pywrapbase.BuildData_ClientStatus)
    __swig_getmethods__["ClientStatusAsString"] = lambda x: _base_pywrapbase.BuildData_ClientStatusAsString
    if _newclass:ClientStatusAsString = staticmethod(_base_pywrapbase.BuildData_ClientStatusAsString)
    __swig_getmethods__["BuildDepotPath"] = lambda x: _base_pywrapbase.BuildData_BuildDepotPath
    if _newclass:BuildDepotPath = staticmethod(_base_pywrapbase.BuildData_BuildDepotPath)
    __swig_getmethods__["ClientInfo"] = lambda x: _base_pywrapbase.BuildData_ClientInfo
    if _newclass:ClientInfo = staticmethod(_base_pywrapbase.BuildData_ClientInfo)
    __swig_getmethods__["TargetName"] = lambda x: _base_pywrapbase.BuildData_TargetName
    if _newclass:TargetName = staticmethod(_base_pywrapbase.BuildData_TargetName)
    __swig_getmethods__["VersionInfo"] = lambda x: _base_pywrapbase.BuildData_VersionInfo
    if _newclass:VersionInfo = staticmethod(_base_pywrapbase.BuildData_VersionInfo)
    __swig_getmethods__["GPlatform"] = lambda x: _base_pywrapbase.BuildData_GPlatform
    if _newclass:GPlatform = staticmethod(_base_pywrapbase.BuildData_GPlatform)
    __swig_getmethods__["UnstrippedLocation"] = lambda x: _base_pywrapbase.BuildData_UnstrippedLocation
    if _newclass:UnstrippedLocation = staticmethod(_base_pywrapbase.BuildData_UnstrippedLocation)
    def __init__(self, *args):
        _swig_setattr(self, BuildData, 'this', _base_pywrapbase.new_BuildData(*args))
        _swig_setattr(self, BuildData, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_BuildData):
        try:
            if self.thisown: destroy(self)
        except: pass

class BuildDataPtr(BuildData):
    def __init__(self, this):
        _swig_setattr(self, BuildData, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, BuildData, 'thisown', 0)
        _swig_setattr(self, BuildData,self.__class__,BuildData)
_base_pywrapbase.BuildData_swigregister(BuildDataPtr)

BuildData_BuildInfo = _base_pywrapbase.BuildData_BuildInfo

BuildData_BuildTool = _base_pywrapbase.BuildData_BuildTool

BuildData_BuildDir = _base_pywrapbase.BuildData_BuildDir

BuildData_BuildHost = _base_pywrapbase.BuildData_BuildHost

BuildData_BuildTarget = _base_pywrapbase.BuildData_BuildTarget

BuildData_BuildLabel = _base_pywrapbase.BuildData_BuildLabel

BuildData_BuildClient = _base_pywrapbase.BuildData_BuildClient

BuildData_Timestamp = _base_pywrapbase.BuildData_Timestamp

BuildData_MpmVersion = _base_pywrapbase.BuildData_MpmVersion

BuildData_MpmVersionIfSet = _base_pywrapbase.BuildData_MpmVersionIfSet

BuildData_TimestampAsInt = _base_pywrapbase.BuildData_TimestampAsInt

BuildData_StaticLibPath = _base_pywrapbase.BuildData_StaticLibPath

BuildData_Changelist = _base_pywrapbase.BuildData_Changelist

BuildData_ChangelistAsInt = _base_pywrapbase.BuildData_ChangelistAsInt

BuildData_ClientStatus = _base_pywrapbase.BuildData_ClientStatus

BuildData_ClientStatusAsString = _base_pywrapbase.BuildData_ClientStatusAsString

BuildData_BuildDepotPath = _base_pywrapbase.BuildData_BuildDepotPath

BuildData_ClientInfo = _base_pywrapbase.BuildData_ClientInfo

BuildData_TargetName = _base_pywrapbase.BuildData_TargetName

BuildData_VersionInfo = _base_pywrapbase.BuildData_VersionInfo

BuildData_GPlatform = _base_pywrapbase.BuildData_GPlatform

BuildData_UnstrippedLocation = _base_pywrapbase.BuildData_UnstrippedLocation


BuildInfo = _base_pywrapbase.BuildInfo

Timestamp = _base_pywrapbase.Timestamp

TimestampAsInt = _base_pywrapbase.TimestampAsInt

StaticLibPath = _base_pywrapbase.StaticLibPath

BuildChangelist = _base_pywrapbase.BuildChangelist

VersionInfo = _base_pywrapbase.VersionInfo
class CallbackUtils_(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CallbackUtils_, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CallbackUtils_, name)
    def __repr__(self):
        return "<C CallbackUtils_ instance at %s>" % (self.this,)
    __swig_getmethods__["FailIsRepeatable"] = lambda x: _base_pywrapbase.CallbackUtils__FailIsRepeatable
    if _newclass:FailIsRepeatable = staticmethod(_base_pywrapbase.CallbackUtils__FailIsRepeatable)
    def __init__(self, *args):
        _swig_setattr(self, CallbackUtils_, 'this', _base_pywrapbase.new_CallbackUtils_(*args))
        _swig_setattr(self, CallbackUtils_, 'thisown', 1)
    def __del__(self, destroy=_base_pywrapbase.delete_CallbackUtils_):
        try:
            if self.thisown: destroy(self)
        except: pass

class CallbackUtils_Ptr(CallbackUtils_):
    def __init__(self, this):
        _swig_setattr(self, CallbackUtils_, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, CallbackUtils_, 'thisown', 0)
        _swig_setattr(self, CallbackUtils_,self.__class__,CallbackUtils_)
_base_pywrapbase.CallbackUtils__swigregister(CallbackUtils_Ptr)

CallbackUtils__FailIsRepeatable = _base_pywrapbase.CallbackUtils__FailIsRepeatable

class Closure(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Closure, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Closure, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C Closure instance at %s>" % (self.this,)
    def __del__(self, destroy=_base_pywrapbase.delete_Closure):
        try:
            if self.thisown: destroy(self)
        except: pass
    def IsRepeatable(*args): return _base_pywrapbase.Closure_IsRepeatable(*args)
    def CheckIsRepeatable(*args): return _base_pywrapbase.Closure_CheckIsRepeatable(*args)
    def Run(*args): return _base_pywrapbase.Closure_Run(*args)
    def trace_context_ptr(*args): return _base_pywrapbase.Closure_trace_context_ptr(*args)

class ClosurePtr(Closure):
    def __init__(self, this):
        _swig_setattr(self, Closure, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Closure, 'thisown', 0)
        _swig_setattr(self, Closure,self.__class__,Closure)
_base_pywrapbase.Closure_swigregister(ClosurePtr)


PhysicalMem = _base_pywrapbase.PhysicalMem

MaxPageId = _base_pywrapbase.MaxPageId

UnmappedMem = _base_pywrapbase.UnmappedMem

NonKernelMem64 = _base_pywrapbase.NonKernelMem64

MaxVMArea = _base_pywrapbase.MaxVMArea

BiosMem = _base_pywrapbase.BiosMem

FreeMem = _base_pywrapbase.FreeMem

CyclesPerSecond = _base_pywrapbase.CyclesPerSecond

NumCPUs = _base_pywrapbase.NumCPUs

SupportSSE = _base_pywrapbase.SupportSSE

SupportSSE2 = _base_pywrapbase.SupportSSE2

VirtualProcessSize = _base_pywrapbase.VirtualProcessSize

VirtualProcessSizeForExport = _base_pywrapbase.VirtualProcessSizeForExport

MemoryUsage = _base_pywrapbase.MemoryUsage

VirtualMemorySize = _base_pywrapbase.VirtualMemorySize

ProcessParent = _base_pywrapbase.ProcessParent

Nice = _base_pywrapbase.Nice

CommandLine = _base_pywrapbase.CommandLine

MemoryUsageForExport = _base_pywrapbase.MemoryUsageForExport
PROC_USAGE_1MIN = _base_pywrapbase.PROC_USAGE_1MIN
PROC_USAGE_5MIN = _base_pywrapbase.PROC_USAGE_5MIN
PROC_USAGE_15MIN = _base_pywrapbase.PROC_USAGE_15MIN

ProcessorUsageForTimeRange = _base_pywrapbase.ProcessorUsageForTimeRange

ProcessorUsage = _base_pywrapbase.ProcessorUsage

BootTime = _base_pywrapbase.BootTime

ProcessList = _base_pywrapbase.ProcessList

ProcessGroup = _base_pywrapbase.ProcessGroup

ThreadGroup = _base_pywrapbase.ThreadGroup

UserName = _base_pywrapbase.UserName

MyUserName = _base_pywrapbase.MyUserName

GetTID = _base_pywrapbase.GetTID

ProcessName = _base_pywrapbase.ProcessName

ProcessPageFaults = _base_pywrapbase.ProcessPageFaults

ProcessCPUUsage = _base_pywrapbase.ProcessCPUUsage

MyCPUUsage = _base_pywrapbase.MyCPUUsage

ChildrenCPUUsage = _base_pywrapbase.ChildrenCPUUsage

GetIdleTime = _base_pywrapbase.GetIdleTime

NumOpenFDs = _base_pywrapbase.NumOpenFDs

GetSwapDisks = _base_pywrapbase.GetSwapDisks


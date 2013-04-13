# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _file_base_pywrapfile

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
        _swig_setattr(self, stringVector, 'this', _file_base_pywrapfile.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_file_base_pywrapfile.stringVector_swigregister(stringVectorPtr)


FromFileStat = _file_base_pywrapfile.FromFileStat

FromFile = _file_base_pywrapfile.FromFile
class AsyncIO(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, AsyncIO, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, AsyncIO, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C AsyncIO instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywrapfile.delete_AsyncIO):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Finish(*args): return _file_base_pywrapfile.AsyncIO_Finish(*args)
    def SetAbandonCallback(*args): return _file_base_pywrapfile.AsyncIO_SetAbandonCallback(*args)

class AsyncIOPtr(AsyncIO):
    def __init__(self, this):
        _swig_setattr(self, AsyncIO, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AsyncIO, 'thisown', 0)
        _swig_setattr(self, AsyncIO,self.__class__,AsyncIO)
_file_base_pywrapfile.AsyncIO_swigregister(AsyncIOPtr)

class AsyncIOWatcher(AsyncIO):
    __swig_setmethods__ = {}
    for _s in [AsyncIO]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, AsyncIOWatcher, name, value)
    __swig_getmethods__ = {}
    for _s in [AsyncIO]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, AsyncIOWatcher, name)
    def __repr__(self):
        return "<C AsyncIOWatcher instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, AsyncIOWatcher, 'this', _file_base_pywrapfile.new_AsyncIOWatcher(*args))
        _swig_setattr(self, AsyncIOWatcher, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_AsyncIOWatcher):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Abandon(*args): return _file_base_pywrapfile.AsyncIOWatcher_Abandon(*args)
    def AbandonAndRelease(*args): return _file_base_pywrapfile.AsyncIOWatcher_AbandonAndRelease(*args)
    def Detach(*args): return _file_base_pywrapfile.AsyncIOWatcher_Detach(*args)
    def WaitWithTimeout(*args): return _file_base_pywrapfile.AsyncIOWatcher_WaitWithTimeout(*args)
    def Wait(*args): return _file_base_pywrapfile.AsyncIOWatcher_Wait(*args)
    def IsFinished(*args): return _file_base_pywrapfile.AsyncIOWatcher_IsFinished(*args)
    def Error(*args): return _file_base_pywrapfile.AsyncIOWatcher_Error(*args)
    def Bytes(*args): return _file_base_pywrapfile.AsyncIOWatcher_Bytes(*args)
    def HandleFinish(*args): return _file_base_pywrapfile.AsyncIOWatcher_HandleFinish(*args)
    def Finish(*args): return _file_base_pywrapfile.AsyncIOWatcher_Finish(*args)
    def SetAbandonCallback(*args): return _file_base_pywrapfile.AsyncIOWatcher_SetAbandonCallback(*args)

class AsyncIOWatcherPtr(AsyncIOWatcher):
    def __init__(self, this):
        _swig_setattr(self, AsyncIOWatcher, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AsyncIOWatcher, 'thisown', 0)
        _swig_setattr(self, AsyncIOWatcher,self.__class__,AsyncIOWatcher)
_file_base_pywrapfile.AsyncIOWatcher_swigregister(AsyncIOWatcherPtr)

class AsyncIOForSS(AsyncIO):
    __swig_setmethods__ = {}
    for _s in [AsyncIO]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, AsyncIOForSS, name, value)
    __swig_getmethods__ = {}
    for _s in [AsyncIO]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, AsyncIOForSS, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C AsyncIOForSS instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywrapfile.delete_AsyncIOForSS):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Run(*args): return _file_base_pywrapfile.AsyncIOForSS_Run(*args)
    def Error(*args): return _file_base_pywrapfile.AsyncIOForSS_Error(*args)
    def Bytes(*args): return _file_base_pywrapfile.AsyncIOForSS_Bytes(*args)
    def Finish(*args): return _file_base_pywrapfile.AsyncIOForSS_Finish(*args)

class AsyncIOForSSPtr(AsyncIOForSS):
    def __init__(self, this):
        _swig_setattr(self, AsyncIOForSS, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AsyncIOForSS, 'thisown', 0)
        _swig_setattr(self, AsyncIOForSS,self.__class__,AsyncIOForSS)
_file_base_pywrapfile.AsyncIOForSS_swigregister(AsyncIOForSSPtr)

OK = _file_base_pywrapfile.OK
ERROR_INVALID_ARGUMENT = _file_base_pywrapfile.ERROR_INVALID_ARGUMENT
ERROR_DEADLINE_EXCEEDED = _file_base_pywrapfile.ERROR_DEADLINE_EXCEEDED
ERROR_NOT_FOUND = _file_base_pywrapfile.ERROR_NOT_FOUND
ERROR_ALREADY_EXISTS = _file_base_pywrapfile.ERROR_ALREADY_EXISTS
ERROR_PERMISSION_DENIED = _file_base_pywrapfile.ERROR_PERMISSION_DENIED
ERROR_WRONG_TYPE = _file_base_pywrapfile.ERROR_WRONG_TYPE
ERROR_NOT_EMPTY = _file_base_pywrapfile.ERROR_NOT_EMPTY
ERROR_NO_SPACE = _file_base_pywrapfile.ERROR_NO_SPACE
ERROR_PAST_EOF = _file_base_pywrapfile.ERROR_PAST_EOF
ERROR_UNKNOWN = _file_base_pywrapfile.ERROR_UNKNOWN
ERROR_UNIMPLEMENTED = _file_base_pywrapfile.ERROR_UNIMPLEMENTED
INTERNAL_ERROR = _file_base_pywrapfile.INTERNAL_ERROR
ERROR_TEMPORARY = _file_base_pywrapfile.ERROR_TEMPORARY
MAX_ERROR_CODE = _file_base_pywrapfile.MAX_ERROR_CODE

ErrorToString = _file_base_pywrapfile.ErrorToString
USE_FREAD = _file_base_pywrapfile.USE_FREAD
USE_MMAP = _file_base_pywrapfile.USE_MMAP
USE_RAWIO = _file_base_pywrapfile.USE_RAWIO
class Attr_t(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Attr_t, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Attr_t, name)
    def __repr__(self):
        return "<C Attr_t instance at %s>" % (self.this,)
    NONE = _file_base_pywrapfile.Attr_t_NONE
    APPEND = _file_base_pywrapfile.Attr_t_APPEND
    PROTECTED = _file_base_pywrapfile.Attr_t_PROTECTED
    FINALIZED = _file_base_pywrapfile.Attr_t_FINALIZED
    FROZEN = _file_base_pywrapfile.Attr_t_FROZEN
    ARCHIVAL_PENDING = _file_base_pywrapfile.Attr_t_ARCHIVAL_PENDING
    DEFAULT = _file_base_pywrapfile.Attr_t_DEFAULT
    __swig_setmethods__["attr"] = _file_base_pywrapfile.Attr_t_attr_set
    __swig_getmethods__["attr"] = _file_base_pywrapfile.Attr_t_attr_get
    if _newclass:attr = property(_file_base_pywrapfile.Attr_t_attr_get, _file_base_pywrapfile.Attr_t_attr_set)
    def __init__(self, *args):
        _swig_setattr(self, Attr_t, 'this', _file_base_pywrapfile.new_Attr_t(*args))
        _swig_setattr(self, Attr_t, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_Attr_t):
        try:
            if self.thisown: destroy(self)
        except: pass

class Attr_tPtr(Attr_t):
    def __init__(self, this):
        _swig_setattr(self, Attr_t, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Attr_t, 'thisown', 0)
        _swig_setattr(self, Attr_t,self.__class__,Attr_t)
_file_base_pywrapfile.Attr_t_swigregister(Attr_tPtr)
cvar = _file_base_pywrapfile.cvar
kMinMMapSize = cvar.kMinMMapSize

NONE = _file_base_pywrapfile.NONE
NORMAL = _file_base_pywrapfile.NORMAL
RANDOM = _file_base_pywrapfile.RANDOM
SEQUENTIAL = _file_base_pywrapfile.SEQUENTIAL
CACHED = _file_base_pywrapfile.CACHED
UNCACHED = _file_base_pywrapfile.UNCACHED
DEFAULT_FILE_MODE = _file_base_pywrapfile.DEFAULT_FILE_MODE
class FileStat(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileStat, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileStat, name)
    def __repr__(self):
        return "<C FileStat instance at %s>" % (self.this,)
    __swig_setmethods__["length"] = _file_base_pywrapfile.FileStat_length_set
    __swig_getmethods__["length"] = _file_base_pywrapfile.FileStat_length_get
    if _newclass:length = property(_file_base_pywrapfile.FileStat_length_get, _file_base_pywrapfile.FileStat_length_set)
    __swig_setmethods__["mtime"] = _file_base_pywrapfile.FileStat_mtime_set
    __swig_getmethods__["mtime"] = _file_base_pywrapfile.FileStat_mtime_get
    if _newclass:mtime = property(_file_base_pywrapfile.FileStat_mtime_get, _file_base_pywrapfile.FileStat_mtime_set)
    __swig_setmethods__["attributes"] = _file_base_pywrapfile.FileStat_attributes_set
    __swig_getmethods__["attributes"] = _file_base_pywrapfile.FileStat_attributes_get
    if _newclass:attributes = property(_file_base_pywrapfile.FileStat_attributes_get, _file_base_pywrapfile.FileStat_attributes_set)
    __swig_setmethods__["mode"] = _file_base_pywrapfile.FileStat_mode_set
    __swig_getmethods__["mode"] = _file_base_pywrapfile.FileStat_mode_get
    if _newclass:mode = property(_file_base_pywrapfile.FileStat_mode_get, _file_base_pywrapfile.FileStat_mode_set)
    __swig_setmethods__["owner"] = _file_base_pywrapfile.FileStat_owner_set
    __swig_getmethods__["owner"] = _file_base_pywrapfile.FileStat_owner_get
    if _newclass:owner = property(_file_base_pywrapfile.FileStat_owner_get, _file_base_pywrapfile.FileStat_owner_set)
    __swig_setmethods__["group"] = _file_base_pywrapfile.FileStat_group_set
    __swig_getmethods__["group"] = _file_base_pywrapfile.FileStat_group_get
    if _newclass:group = property(_file_base_pywrapfile.FileStat_group_get, _file_base_pywrapfile.FileStat_group_set)
    __swig_setmethods__["data_members"] = _file_base_pywrapfile.FileStat_data_members_set
    __swig_getmethods__["data_members"] = _file_base_pywrapfile.FileStat_data_members_get
    if _newclass:data_members = property(_file_base_pywrapfile.FileStat_data_members_get, _file_base_pywrapfile.FileStat_data_members_set)
    __swig_setmethods__["code_members"] = _file_base_pywrapfile.FileStat_code_members_set
    __swig_getmethods__["code_members"] = _file_base_pywrapfile.FileStat_code_members_get
    if _newclass:code_members = property(_file_base_pywrapfile.FileStat_code_members_get, _file_base_pywrapfile.FileStat_code_members_set)
    def IsDirectory(*args): return _file_base_pywrapfile.FileStat_IsDirectory(*args)
    def Clear(*args): return _file_base_pywrapfile.FileStat_Clear(*args)
    def __init__(self, *args):
        _swig_setattr(self, FileStat, 'this', _file_base_pywrapfile.new_FileStat(*args))
        _swig_setattr(self, FileStat, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileStat):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileStatPtr(FileStat):
    def __init__(self, this):
        _swig_setattr(self, FileStat, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileStat, 'thisown', 0)
        _swig_setattr(self, FileStat,self.__class__,FileStat)
_file_base_pywrapfile.FileStat_swigregister(FileStatPtr)

class FileOpenOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileOpenOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileOpenOptions, name)
    def __repr__(self):
        return "<C FileOpenOptions instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileOpenOptions, 'this', _file_base_pywrapfile.new_FileOpenOptions(*args))
        _swig_setattr(self, FileOpenOptions, 'thisown', 1)
    def set_attributes(*args): return _file_base_pywrapfile.FileOpenOptions_set_attributes(*args)
    def set_access_pattern(*args): return _file_base_pywrapfile.FileOpenOptions_set_access_pattern(*args)
    def set_cache_policy(*args): return _file_base_pywrapfile.FileOpenOptions_set_cache_policy(*args)
    def set_permissions(*args): return _file_base_pywrapfile.FileOpenOptions_set_permissions(*args)
    def set_group(*args): return _file_base_pywrapfile.FileOpenOptions_set_group(*args)
    def set_requested_role(*args): return _file_base_pywrapfile.FileOpenOptions_set_requested_role(*args)
    def set_checkpoint(*args): return _file_base_pywrapfile.FileOpenOptions_set_checkpoint(*args)
    def set_lock_info(*args): return _file_base_pywrapfile.FileOpenOptions_set_lock_info(*args)
    def set_attr_file(*args): return _file_base_pywrapfile.FileOpenOptions_set_attr_file(*args)
    def set_operation(*args): return _file_base_pywrapfile.FileOpenOptions_set_operation(*args)
    def set_direct_io(*args): return _file_base_pywrapfile.FileOpenOptions_set_direct_io(*args)
    def direct_io(*args): return _file_base_pywrapfile.FileOpenOptions_direct_io(*args)
    def attributes(*args): return _file_base_pywrapfile.FileOpenOptions_attributes(*args)
    def access_pattern(*args): return _file_base_pywrapfile.FileOpenOptions_access_pattern(*args)
    def cache_policy(*args): return _file_base_pywrapfile.FileOpenOptions_cache_policy(*args)
    def permissions(*args): return _file_base_pywrapfile.FileOpenOptions_permissions(*args)
    def group(*args): return _file_base_pywrapfile.FileOpenOptions_group(*args)
    def requested_role(*args): return _file_base_pywrapfile.FileOpenOptions_requested_role(*args)
    def operation(*args): return _file_base_pywrapfile.FileOpenOptions_operation(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileOpenOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileOpenOptionsPtr(FileOpenOptions):
    def __init__(self, this):
        _swig_setattr(self, FileOpenOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileOpenOptions, 'thisown', 0)
        _swig_setattr(self, FileOpenOptions,self.__class__,FileOpenOptions)
_file_base_pywrapfile.FileOpenOptions_swigregister(FileOpenOptionsPtr)

class File(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, File, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, File, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C File instance at %s>" % (self.this,)
    __swig_getmethods__["Stat"] = lambda x: _file_base_pywrapfile.File_Stat
    if _newclass:Stat = staticmethod(_file_base_pywrapfile.File_Stat)
    def PReadStringWithOp(*args): return _file_base_pywrapfile.File_PReadStringWithOp(*args)
    def PWriteStringWithOp(*args): return _file_base_pywrapfile.File_PWriteStringWithOp(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_File):
        try:
            if self.thisown: destroy(self)
        except: pass
    __swig_getmethods__["Init"] = lambda x: _file_base_pywrapfile.File_Init
    if _newclass:Init = staticmethod(_file_base_pywrapfile.File_Init)
    __swig_getmethods__["InitWithDatadirFrom"] = lambda x: _file_base_pywrapfile.File_InitWithDatadirFrom
    if _newclass:InitWithDatadirFrom = staticmethod(_file_base_pywrapfile.File_InitWithDatadirFrom)
    __swig_getmethods__["init_called"] = lambda x: _file_base_pywrapfile.File_init_called
    if _newclass:init_called = staticmethod(_file_base_pywrapfile.File_init_called)
    __swig_getmethods__["CreateFullySpecified"] = lambda x: _file_base_pywrapfile.File_CreateFullySpecified
    if _newclass:CreateFullySpecified = staticmethod(_file_base_pywrapfile.File_CreateFullySpecified)
    __swig_getmethods__["CreateWithOptions"] = lambda x: _file_base_pywrapfile.File_CreateWithOptions
    if _newclass:CreateWithOptions = staticmethod(_file_base_pywrapfile.File_CreateWithOptions)
    __swig_getmethods__["CreateWithAttr"] = lambda x: _file_base_pywrapfile.File_CreateWithAttr
    if _newclass:CreateWithAttr = staticmethod(_file_base_pywrapfile.File_CreateWithAttr)
    __swig_getmethods__["Create"] = lambda x: _file_base_pywrapfile.File_Create
    if _newclass:Create = staticmethod(_file_base_pywrapfile.File_Create)
    __swig_getmethods__["OpenFullySpecified"] = lambda x: _file_base_pywrapfile.File_OpenFullySpecified
    if _newclass:OpenFullySpecified = staticmethod(_file_base_pywrapfile.File_OpenFullySpecified)
    __swig_getmethods__["OpenFullySpecifiedLocked"] = lambda x: _file_base_pywrapfile.File_OpenFullySpecifiedLocked
    if _newclass:OpenFullySpecifiedLocked = staticmethod(_file_base_pywrapfile.File_OpenFullySpecifiedLocked)
    __swig_getmethods__["OpenWithAttr"] = lambda x: _file_base_pywrapfile.File_OpenWithAttr
    if _newclass:OpenWithAttr = staticmethod(_file_base_pywrapfile.File_OpenWithAttr)
    __swig_getmethods__["OpenWithOptions"] = lambda x: _file_base_pywrapfile.File_OpenWithOptions
    if _newclass:OpenWithOptions = staticmethod(_file_base_pywrapfile.File_OpenWithOptions)
    __swig_getmethods__["Open"] = lambda x: _file_base_pywrapfile.File_Open
    if _newclass:Open = staticmethod(_file_base_pywrapfile.File_Open)
    __swig_getmethods__["OpenLocked"] = lambda x: _file_base_pywrapfile.File_OpenLocked
    if _newclass:OpenLocked = staticmethod(_file_base_pywrapfile.File_OpenLocked)
    __swig_getmethods__["OpenFullySpecifiedOrDie"] = lambda x: _file_base_pywrapfile.File_OpenFullySpecifiedOrDie
    if _newclass:OpenFullySpecifiedOrDie = staticmethod(_file_base_pywrapfile.File_OpenFullySpecifiedOrDie)
    __swig_getmethods__["OpenWithAttrOrDie"] = lambda x: _file_base_pywrapfile.File_OpenWithAttrOrDie
    if _newclass:OpenWithAttrOrDie = staticmethod(_file_base_pywrapfile.File_OpenWithAttrOrDie)
    __swig_getmethods__["OpenOrDie"] = lambda x: _file_base_pywrapfile.File_OpenOrDie
    if _newclass:OpenOrDie = staticmethod(_file_base_pywrapfile.File_OpenOrDie)
    __swig_getmethods__["OpenForAppend"] = lambda x: _file_base_pywrapfile.File_OpenForAppend
    if _newclass:OpenForAppend = staticmethod(_file_base_pywrapfile.File_OpenForAppend)
    __swig_getmethods__["OpenForAppendOrDie"] = lambda x: _file_base_pywrapfile.File_OpenForAppendOrDie
    if _newclass:OpenForAppendOrDie = staticmethod(_file_base_pywrapfile.File_OpenForAppendOrDie)
    __swig_getmethods__["OpenToCheckpointOrDie"] = lambda x: _file_base_pywrapfile.File_OpenToCheckpointOrDie
    if _newclass:OpenToCheckpointOrDie = staticmethod(_file_base_pywrapfile.File_OpenToCheckpointOrDie)
    __swig_getmethods__["OpenOrDieForWriting"] = lambda x: _file_base_pywrapfile.File_OpenOrDieForWriting
    if _newclass:OpenOrDieForWriting = staticmethod(_file_base_pywrapfile.File_OpenOrDieForWriting)
    __swig_getmethods__["Readable"] = lambda x: _file_base_pywrapfile.File_Readable
    if _newclass:Readable = staticmethod(_file_base_pywrapfile.File_Readable)
    __swig_getmethods__["Exists"] = lambda x: _file_base_pywrapfile.File_Exists
    if _newclass:Exists = staticmethod(_file_base_pywrapfile.File_Exists)
    __swig_getmethods__["ExistsWithOp"] = lambda x: _file_base_pywrapfile.File_ExistsWithOp
    if _newclass:ExistsWithOp = staticmethod(_file_base_pywrapfile.File_ExistsWithOp)
    __swig_getmethods__["IsReplicatedFileName"] = lambda x: _file_base_pywrapfile.File_IsReplicatedFileName
    if _newclass:IsReplicatedFileName = staticmethod(_file_base_pywrapfile.File_IsReplicatedFileName)
    TYPE_RFSERVER = _file_base_pywrapfile.File_TYPE_RFSERVER
    TYPE_SREMOTE_SERVER = _file_base_pywrapfile.File_TYPE_SREMOTE_SERVER
    __swig_getmethods__["ConstructFullFileName"] = lambda x: _file_base_pywrapfile.File_ConstructFullFileName
    if _newclass:ConstructFullFileName = staticmethod(_file_base_pywrapfile.File_ConstructFullFileName)
    __swig_getmethods__["CanonicalizeFileName"] = lambda x: _file_base_pywrapfile.File_CanonicalizeFileName
    if _newclass:CanonicalizeFileName = staticmethod(_file_base_pywrapfile.File_CanonicalizeFileName)
    __swig_getmethods__["CanonicalizeFileNameList"] = lambda x: _file_base_pywrapfile.File_CanonicalizeFileNameList
    if _newclass:CanonicalizeFileNameList = staticmethod(_file_base_pywrapfile.File_CanonicalizeFileNameList)
    __swig_getmethods__["CleanPath"] = lambda x: _file_base_pywrapfile.File_CleanPath
    if _newclass:CleanPath = staticmethod(_file_base_pywrapfile.File_CleanPath)
    __swig_getmethods__["Basename"] = lambda x: _file_base_pywrapfile.File_Basename
    if _newclass:Basename = staticmethod(_file_base_pywrapfile.File_Basename)
    __swig_getmethods__["Suffix"] = lambda x: _file_base_pywrapfile.File_Suffix
    if _newclass:Suffix = staticmethod(_file_base_pywrapfile.File_Suffix)
    __swig_getmethods__["ShardedBasenameWithNumShards"] = lambda x: _file_base_pywrapfile.File_ShardedBasenameWithNumShards
    if _newclass:ShardedBasenameWithNumShards = staticmethod(_file_base_pywrapfile.File_ShardedBasenameWithNumShards)
    __swig_getmethods__["StripBasename"] = lambda x: _file_base_pywrapfile.File_StripBasename
    if _newclass:StripBasename = staticmethod(_file_base_pywrapfile.File_StripBasename)
    __swig_getmethods__["AddSlash"] = lambda x: _file_base_pywrapfile.File_AddSlash
    if _newclass:AddSlash = staticmethod(_file_base_pywrapfile.File_AddSlash)
    __swig_getmethods__["JoinPath"] = lambda x: _file_base_pywrapfile.File_JoinPath
    if _newclass:JoinPath = staticmethod(_file_base_pywrapfile.File_JoinPath)
    __swig_getmethods__["RemoveHosts"] = lambda x: _file_base_pywrapfile.File_RemoveHosts
    if _newclass:RemoveHosts = staticmethod(_file_base_pywrapfile.File_RemoveHosts)
    __swig_getmethods__["RewriteDatadir"] = lambda x: _file_base_pywrapfile.File_RewriteDatadir
    if _newclass:RewriteDatadir = staticmethod(_file_base_pywrapfile.File_RewriteDatadir)
    MATCH_DEFAULT = _file_base_pywrapfile.File_MATCH_DEFAULT
    MATCH_DOTFILES = _file_base_pywrapfile.File_MATCH_DOTFILES
    MATCH_BACKUPS = _file_base_pywrapfile.File_MATCH_BACKUPS
    MATCH_ALL = _file_base_pywrapfile.File_MATCH_ALL
    __swig_getmethods__["ExtendedMatch"] = lambda x: _file_base_pywrapfile.File_ExtendedMatch
    if _newclass:ExtendedMatch = staticmethod(_file_base_pywrapfile.File_ExtendedMatch)
    __swig_getmethods__["ExtendedMatchWithOp"] = lambda x: _file_base_pywrapfile.File_ExtendedMatchWithOp
    if _newclass:ExtendedMatchWithOp = staticmethod(_file_base_pywrapfile.File_ExtendedMatchWithOp)
    __swig_getmethods__["ExtendedMatchLocked"] = lambda x: _file_base_pywrapfile.File_ExtendedMatchLocked
    if _newclass:ExtendedMatchLocked = staticmethod(_file_base_pywrapfile.File_ExtendedMatchLocked)
    __swig_getmethods__["ExtendedMatchLockedWithOp"] = lambda x: _file_base_pywrapfile.File_ExtendedMatchLockedWithOp
    if _newclass:ExtendedMatchLockedWithOp = staticmethod(_file_base_pywrapfile.File_ExtendedMatchLockedWithOp)
    __swig_getmethods__["Match"] = lambda x: _file_base_pywrapfile.File_Match
    if _newclass:Match = staticmethod(_file_base_pywrapfile.File_Match)
    __swig_getmethods__["MatchLocked"] = lambda x: _file_base_pywrapfile.File_MatchLocked
    if _newclass:MatchLocked = staticmethod(_file_base_pywrapfile.File_MatchLocked)
    __swig_getmethods__["MatchWithOp"] = lambda x: _file_base_pywrapfile.File_MatchWithOp
    if _newclass:MatchWithOp = staticmethod(_file_base_pywrapfile.File_MatchWithOp)
    __swig_getmethods__["MatchLockedWithOp"] = lambda x: _file_base_pywrapfile.File_MatchLockedWithOp
    if _newclass:MatchLockedWithOp = staticmethod(_file_base_pywrapfile.File_MatchLockedWithOp)
    __swig_getmethods__["GetMatchingFiles"] = lambda x: _file_base_pywrapfile.File_GetMatchingFiles
    if _newclass:GetMatchingFiles = staticmethod(_file_base_pywrapfile.File_GetMatchingFiles)
    __swig_getmethods__["GetMatchingFilesLocked"] = lambda x: _file_base_pywrapfile.File_GetMatchingFilesLocked
    if _newclass:GetMatchingFilesLocked = staticmethod(_file_base_pywrapfile.File_GetMatchingFilesLocked)
    __swig_getmethods__["Rename"] = lambda x: _file_base_pywrapfile.File_Rename
    if _newclass:Rename = staticmethod(_file_base_pywrapfile.File_Rename)
    __swig_getmethods__["CopyFullySpecified"] = lambda x: _file_base_pywrapfile.File_CopyFullySpecified
    if _newclass:CopyFullySpecified = staticmethod(_file_base_pywrapfile.File_CopyFullySpecified)
    __swig_getmethods__["CopyFullySpecified"] = lambda x: _file_base_pywrapfile.File_CopyFullySpecified
    if _newclass:CopyFullySpecified = staticmethod(_file_base_pywrapfile.File_CopyFullySpecified)
    __swig_getmethods__["CopyWithAttr"] = lambda x: _file_base_pywrapfile.File_CopyWithAttr
    if _newclass:CopyWithAttr = staticmethod(_file_base_pywrapfile.File_CopyWithAttr)
    __swig_getmethods__["Copy"] = lambda x: _file_base_pywrapfile.File_Copy
    if _newclass:Copy = staticmethod(_file_base_pywrapfile.File_Copy)
    __swig_getmethods__["CopyBytes"] = lambda x: _file_base_pywrapfile.File_CopyBytes
    if _newclass:CopyBytes = staticmethod(_file_base_pywrapfile.File_CopyBytes)
    __swig_getmethods__["CopyBytes"] = lambda x: _file_base_pywrapfile.File_CopyBytes
    if _newclass:CopyBytes = staticmethod(_file_base_pywrapfile.File_CopyBytes)
    __swig_getmethods__["CopyNBytes"] = lambda x: _file_base_pywrapfile.File_CopyNBytes
    if _newclass:CopyNBytes = staticmethod(_file_base_pywrapfile.File_CopyNBytes)
    __swig_getmethods__["CopyToEof"] = lambda x: _file_base_pywrapfile.File_CopyToEof
    if _newclass:CopyToEof = staticmethod(_file_base_pywrapfile.File_CopyToEof)
    __swig_getmethods__["CopyToEof"] = lambda x: _file_base_pywrapfile.File_CopyToEof
    if _newclass:CopyToEof = staticmethod(_file_base_pywrapfile.File_CopyToEof)
    __swig_getmethods__["Delete"] = lambda x: _file_base_pywrapfile.File_Delete
    if _newclass:Delete = staticmethod(_file_base_pywrapfile.File_Delete)
    __swig_getmethods__["DeleteWithOp"] = lambda x: _file_base_pywrapfile.File_DeleteWithOp
    if _newclass:DeleteWithOp = staticmethod(_file_base_pywrapfile.File_DeleteWithOp)
    __swig_getmethods__["DeleteMatchingFiles"] = lambda x: _file_base_pywrapfile.File_DeleteMatchingFiles
    if _newclass:DeleteMatchingFiles = staticmethod(_file_base_pywrapfile.File_DeleteMatchingFiles)
    __swig_getmethods__["DeleteMatchingFilesWithOp"] = lambda x: _file_base_pywrapfile.File_DeleteMatchingFilesWithOp
    if _newclass:DeleteMatchingFilesWithOp = staticmethod(_file_base_pywrapfile.File_DeleteMatchingFilesWithOp)
    __swig_getmethods__["IsAttributeFilename"] = lambda x: _file_base_pywrapfile.File_IsAttributeFilename
    if _newclass:IsAttributeFilename = staticmethod(_file_base_pywrapfile.File_IsAttributeFilename)
    __swig_getmethods__["DeleteFileAttributes"] = lambda x: _file_base_pywrapfile.File_DeleteFileAttributes
    if _newclass:DeleteFileAttributes = staticmethod(_file_base_pywrapfile.File_DeleteFileAttributes)
    __swig_getmethods__["DeleteFileAttributesWithOp"] = lambda x: _file_base_pywrapfile.File_DeleteFileAttributesWithOp
    if _newclass:DeleteFileAttributesWithOp = staticmethod(_file_base_pywrapfile.File_DeleteFileAttributesWithOp)
    __swig_getmethods__["BulkDeleteAttributes"] = lambda x: _file_base_pywrapfile.File_BulkDeleteAttributes
    if _newclass:BulkDeleteAttributes = staticmethod(_file_base_pywrapfile.File_BulkDeleteAttributes)
    __swig_getmethods__["BulkDeleteAttributesWithOp"] = lambda x: _file_base_pywrapfile.File_BulkDeleteAttributesWithOp
    if _newclass:BulkDeleteAttributesWithOp = staticmethod(_file_base_pywrapfile.File_BulkDeleteAttributesWithOp)
    __swig_getmethods__["DFListFileAndDir"] = lambda x: _file_base_pywrapfile.File_DFListFileAndDir
    if _newclass:DFListFileAndDir = staticmethod(_file_base_pywrapfile.File_DFListFileAndDir)
    __swig_getmethods__["DeleteRecursively"] = lambda x: _file_base_pywrapfile.File_DeleteRecursively
    if _newclass:DeleteRecursively = staticmethod(_file_base_pywrapfile.File_DeleteRecursively)
    __swig_getmethods__["SyncAll"] = lambda x: _file_base_pywrapfile.File_SyncAll
    if _newclass:SyncAll = staticmethod(_file_base_pywrapfile.File_SyncAll)
    __swig_getmethods__["GetFileSize"] = lambda x: _file_base_pywrapfile.File_GetFileSize
    if _newclass:GetFileSize = staticmethod(_file_base_pywrapfile.File_GetFileSize)
    def OpenThis(*args): return _file_base_pywrapfile.File_OpenThis(*args)
    def OpenWithOp(*args): return _file_base_pywrapfile.File_OpenWithOp(*args)
    def AccessWithLock(*args): return _file_base_pywrapfile.File_AccessWithLock(*args)
    def SupportsChubbyLockedAccess(*args): return _file_base_pywrapfile.File_SupportsChubbyLockedAccess(*args)
    def SupportsConcurrentAppenders(*args): return _file_base_pywrapfile.File_SupportsConcurrentAppenders(*args)
    def Close(*args): return _file_base_pywrapfile.File_Close(*args)
    def DeleteThis(*args): return _file_base_pywrapfile.File_DeleteThis(*args)
    def DeleteWithOp(*args): return _file_base_pywrapfile.File_DeleteWithOp(*args)
    __swig_getmethods__["StatWithOp"] = lambda x: _file_base_pywrapfile.File_StatWithOp
    if _newclass:StatWithOp = staticmethod(_file_base_pywrapfile.File_StatWithOp)
    __swig_getmethods__["Stat"] = lambda x: _file_base_pywrapfile.File_Stat
    if _newclass:Stat = staticmethod(_file_base_pywrapfile.File_Stat)
    __swig_getmethods__["StatLockedWithOp"] = lambda x: _file_base_pywrapfile.File_StatLockedWithOp
    if _newclass:StatLockedWithOp = staticmethod(_file_base_pywrapfile.File_StatLockedWithOp)
    __swig_getmethods__["StatLocked"] = lambda x: _file_base_pywrapfile.File_StatLocked
    if _newclass:StatLocked = staticmethod(_file_base_pywrapfile.File_StatLocked)
    def StatThis(*args): return _file_base_pywrapfile.File_StatThis(*args)
    def StatWithOp(*args): return _file_base_pywrapfile.File_StatWithOp(*args)
    __swig_getmethods__["Statfs"] = lambda x: _file_base_pywrapfile.File_Statfs
    if _newclass:Statfs = staticmethod(_file_base_pywrapfile.File_Statfs)
    def Truncate(*args): return _file_base_pywrapfile.File_Truncate(*args)
    def TruncateAsync(*args): return _file_base_pywrapfile.File_TruncateAsync(*args)
    def TruncateWithOp(*args): return _file_base_pywrapfile.File_TruncateWithOp(*args)
    def Size(*args): return _file_base_pywrapfile.File_Size(*args)
    def SizeHint(*args): return _file_base_pywrapfile.File_SizeHint(*args)
    def Flush(*args): return _file_base_pywrapfile.File_Flush(*args)
    def Sync(*args): return _file_base_pywrapfile.File_Sync(*args)
    def DataSync(*args): return _file_base_pywrapfile.File_DataSync(*args)
    def Tell(*args): return _file_base_pywrapfile.File_Tell(*args)
    def eof(*args): return _file_base_pywrapfile.File_eof(*args)
    def Seek(*args): return _file_base_pywrapfile.File_Seek(*args)
    def Read(*args): return _file_base_pywrapfile.File_Read(*args)
    def Write(*args): return _file_base_pywrapfile.File_Write(*args)
    def ReadRegion(*args): return _file_base_pywrapfile.File_ReadRegion(*args)
    def WriteRegion(*args): return _file_base_pywrapfile.File_WriteRegion(*args)
    def Append(*args): return _file_base_pywrapfile.File_Append(*args)
    def RecordAppend(*args): return _file_base_pywrapfile.File_RecordAppend(*args)
    def PWriteAsync(*args): return _file_base_pywrapfile.File_PWriteAsync(*args)
    def RecordAppendAsync(*args): return _file_base_pywrapfile.File_RecordAppendAsync(*args)
    __swig_getmethods__["OpenAsync"] = lambda x: _file_base_pywrapfile.File_OpenAsync
    if _newclass:OpenAsync = staticmethod(_file_base_pywrapfile.File_OpenAsync)
    __swig_getmethods__["OpenAsyncLocked"] = lambda x: _file_base_pywrapfile.File_OpenAsyncLocked
    if _newclass:OpenAsyncLocked = staticmethod(_file_base_pywrapfile.File_OpenAsyncLocked)
    def OpenAsyncThis(*args): return _file_base_pywrapfile.File_OpenAsyncThis(*args)
    __swig_getmethods__["OpenFullySpecifiedAsync"] = lambda x: _file_base_pywrapfile.File_OpenFullySpecifiedAsync
    if _newclass:OpenFullySpecifiedAsync = staticmethod(_file_base_pywrapfile.File_OpenFullySpecifiedAsync)
    __swig_getmethods__["OpenFullySpecifiedAsyncLocked"] = lambda x: _file_base_pywrapfile.File_OpenFullySpecifiedAsyncLocked
    if _newclass:OpenFullySpecifiedAsyncLocked = staticmethod(_file_base_pywrapfile.File_OpenFullySpecifiedAsyncLocked)
    def SupportsAsyncWrite(*args): return _file_base_pywrapfile.File_SupportsAsyncWrite(*args)
    def SupportsAsyncOpen(*args): return _file_base_pywrapfile.File_SupportsAsyncOpen(*args)
    def ReadLine(*args): return _file_base_pywrapfile.File_ReadLine(*args)
    def ReadToString(*args): return _file_base_pywrapfile.File_ReadToString(*args)
    __swig_getmethods__["ReadFileToStringOrDie"] = lambda x: _file_base_pywrapfile.File_ReadFileToStringOrDie
    if _newclass:ReadFileToStringOrDie = staticmethod(_file_base_pywrapfile.File_ReadFileToStringOrDie)
    __swig_getmethods__["WriteStringToFileOrDie"] = lambda x: _file_base_pywrapfile.File_WriteStringToFileOrDie
    if _newclass:WriteStringToFileOrDie = staticmethod(_file_base_pywrapfile.File_WriteStringToFileOrDie)
    __swig_getmethods__["ReadFileToString"] = lambda x: _file_base_pywrapfile.File_ReadFileToString
    if _newclass:ReadFileToString = staticmethod(_file_base_pywrapfile.File_ReadFileToString)
    __swig_getmethods__["WriteStringToFile"] = lambda x: _file_base_pywrapfile.File_WriteStringToFile
    if _newclass:WriteStringToFile = staticmethod(_file_base_pywrapfile.File_WriteStringToFile)
    def GetMemBlock(*args): return _file_base_pywrapfile.File_GetMemBlock(*args)
    def GetMemBlockFromDisk(*args): return _file_base_pywrapfile.File_GetMemBlockFromDisk(*args)
    def PReadWithOp(*args): return _file_base_pywrapfile.File_PReadWithOp(*args)
    def PRead(*args): return _file_base_pywrapfile.File_PRead(*args)
    def PWrite(*args): return _file_base_pywrapfile.File_PWrite(*args)
    def PWriteWithOp(*args): return _file_base_pywrapfile.File_PWriteWithOp(*args)
    def PReadAsync(*args): return _file_base_pywrapfile.File_PReadAsync(*args)
    def ReadWithVerifier(*args): return _file_base_pywrapfile.File_ReadWithVerifier(*args)
    def PReadWithVerifier(*args): return _file_base_pywrapfile.File_PReadWithVerifier(*args)
    def ReadMultipleDataVariants(*args): return _file_base_pywrapfile.File_ReadMultipleDataVariants(*args)
    __swig_getmethods__["DeleteAsync"] = lambda x: _file_base_pywrapfile.File_DeleteAsync
    if _newclass:DeleteAsync = staticmethod(_file_base_pywrapfile.File_DeleteAsync)
    __swig_getmethods__["DeleteAsyncLocked"] = lambda x: _file_base_pywrapfile.File_DeleteAsyncLocked
    if _newclass:DeleteAsyncLocked = staticmethod(_file_base_pywrapfile.File_DeleteAsyncLocked)
    __swig_getmethods__["StatAsync"] = lambda x: _file_base_pywrapfile.File_StatAsync
    if _newclass:StatAsync = staticmethod(_file_base_pywrapfile.File_StatAsync)
    __swig_getmethods__["StatAsyncLocked"] = lambda x: _file_base_pywrapfile.File_StatAsyncLocked
    if _newclass:StatAsyncLocked = staticmethod(_file_base_pywrapfile.File_StatAsyncLocked)
    __swig_getmethods__["MatchAsync"] = lambda x: _file_base_pywrapfile.File_MatchAsync
    if _newclass:MatchAsync = staticmethod(_file_base_pywrapfile.File_MatchAsync)
    __swig_getmethods__["MatchAsyncLocked"] = lambda x: _file_base_pywrapfile.File_MatchAsyncLocked
    if _newclass:MatchAsyncLocked = staticmethod(_file_base_pywrapfile.File_MatchAsyncLocked)
    __swig_getmethods__["ExtendedMatchAsync"] = lambda x: _file_base_pywrapfile.File_ExtendedMatchAsync
    if _newclass:ExtendedMatchAsync = staticmethod(_file_base_pywrapfile.File_ExtendedMatchAsync)
    __swig_getmethods__["ExtendedMatchAsyncLocked"] = lambda x: _file_base_pywrapfile.File_ExtendedMatchAsyncLocked
    if _newclass:ExtendedMatchAsyncLocked = staticmethod(_file_base_pywrapfile.File_ExtendedMatchAsyncLocked)
    def DeleteAsync(*args): return _file_base_pywrapfile.File_DeleteAsync(*args)
    def StatAsync(*args): return _file_base_pywrapfile.File_StatAsync(*args)
    def SyncAsync(*args): return _file_base_pywrapfile.File_SyncAsync(*args)
    def SupportsAsyncRead(*args): return _file_base_pywrapfile.File_SupportsAsyncRead(*args)
    def SupportsAsyncGetMatchingFiles(*args): return _file_base_pywrapfile.File_SupportsAsyncGetMatchingFiles(*args)
    def SupportsAsyncStat(*args): return _file_base_pywrapfile.File_SupportsAsyncStat(*args)
    def SupportsAsyncDelete(*args): return _file_base_pywrapfile.File_SupportsAsyncDelete(*args)
    def SupportsAsyncSync(*args): return _file_base_pywrapfile.File_SupportsAsyncSync(*args)
    def SupportsAIORelease(*args): return _file_base_pywrapfile.File_SupportsAIORelease(*args)
    def TryMMap(*args): return _file_base_pywrapfile.File_TryMMap(*args)
    def FindAllMirrors(*args): return _file_base_pywrapfile.File_FindAllMirrors(*args)
    def IsMirrorOnDisk(*args): return _file_base_pywrapfile.File_IsMirrorOnDisk(*args)
    def FindAllMirrorDisks(*args): return _file_base_pywrapfile.File_FindAllMirrorDisks(*args)
    def IsSoftError(*args): return _file_base_pywrapfile.File_IsSoftError(*args)
    def IsFifo(*args): return _file_base_pywrapfile.File_IsFifo(*args)
    def GetCurrentErrorMessage(*args): return _file_base_pywrapfile.File_GetCurrentErrorMessage(*args)
    def GetCurrentErrorCode(*args): return _file_base_pywrapfile.File_GetCurrentErrorCode(*args)
    def ClearError(*args): return _file_base_pywrapfile.File_ClearError(*args)
    def CreateFileName(*args): return _file_base_pywrapfile.File_CreateFileName(*args)
    def IsLocalFile(*args): return _file_base_pywrapfile.File_IsLocalFile(*args)
    def RawIOPRead(*args): return _file_base_pywrapfile.File_RawIOPRead(*args)
    __swig_getmethods__["CreateDirFullySpecified"] = lambda x: _file_base_pywrapfile.File_CreateDirFullySpecified
    if _newclass:CreateDirFullySpecified = staticmethod(_file_base_pywrapfile.File_CreateDirFullySpecified)
    __swig_getmethods__["CreateDirFullySpecifiedWithOp"] = lambda x: _file_base_pywrapfile.File_CreateDirFullySpecifiedWithOp
    if _newclass:CreateDirFullySpecifiedWithOp = staticmethod(_file_base_pywrapfile.File_CreateDirFullySpecifiedWithOp)
    __swig_getmethods__["CreateDir"] = lambda x: _file_base_pywrapfile.File_CreateDir
    if _newclass:CreateDir = staticmethod(_file_base_pywrapfile.File_CreateDir)
    __swig_getmethods__["CreateDirWithOp"] = lambda x: _file_base_pywrapfile.File_CreateDirWithOp
    if _newclass:CreateDirWithOp = staticmethod(_file_base_pywrapfile.File_CreateDirWithOp)
    __swig_getmethods__["RecursivelyCreateDirFullySpecified"] = lambda x: _file_base_pywrapfile.File_RecursivelyCreateDirFullySpecified
    if _newclass:RecursivelyCreateDirFullySpecified = staticmethod(_file_base_pywrapfile.File_RecursivelyCreateDirFullySpecified)
    __swig_getmethods__["RecursivelyCreateDir"] = lambda x: _file_base_pywrapfile.File_RecursivelyCreateDir
    if _newclass:RecursivelyCreateDir = staticmethod(_file_base_pywrapfile.File_RecursivelyCreateDir)
    __swig_getmethods__["IsDirectory"] = lambda x: _file_base_pywrapfile.File_IsDirectory
    if _newclass:IsDirectory = staticmethod(_file_base_pywrapfile.File_IsDirectory)
    __swig_getmethods__["IsDirectoryWithOp"] = lambda x: _file_base_pywrapfile.File_IsDirectoryWithOp
    if _newclass:IsDirectoryWithOp = staticmethod(_file_base_pywrapfile.File_IsDirectoryWithOp)
    __swig_getmethods__["DeleteDir"] = lambda x: _file_base_pywrapfile.File_DeleteDir
    if _newclass:DeleteDir = staticmethod(_file_base_pywrapfile.File_DeleteDir)
    kWriteMask = _file_base_pywrapfile.File_kWriteMask
    __swig_getmethods__["Snapshot"] = lambda x: _file_base_pywrapfile.File_Snapshot
    if _newclass:Snapshot = staticmethod(_file_base_pywrapfile.File_Snapshot)
    __swig_getmethods__["SnapshotFile"] = lambda x: _file_base_pywrapfile.File_SnapshotFile
    if _newclass:SnapshotFile = staticmethod(_file_base_pywrapfile.File_SnapshotFile)
    __swig_getmethods__["SetOwner"] = lambda x: _file_base_pywrapfile.File_SetOwner
    if _newclass:SetOwner = staticmethod(_file_base_pywrapfile.File_SetOwner)
    __swig_getmethods__["SetAttributes"] = lambda x: _file_base_pywrapfile.File_SetAttributes
    if _newclass:SetAttributes = staticmethod(_file_base_pywrapfile.File_SetAttributes)
    __swig_getmethods__["SetMode"] = lambda x: _file_base_pywrapfile.File_SetMode
    if _newclass:SetMode = staticmethod(_file_base_pywrapfile.File_SetMode)
    __swig_getmethods__["SetMtime"] = lambda x: _file_base_pywrapfile.File_SetMtime
    if _newclass:SetMtime = staticmethod(_file_base_pywrapfile.File_SetMtime)
    __swig_getmethods__["SetGroup"] = lambda x: _file_base_pywrapfile.File_SetGroup
    if _newclass:SetGroup = staticmethod(_file_base_pywrapfile.File_SetGroup)
    __swig_getmethods__["Archive"] = lambda x: _file_base_pywrapfile.File_Archive
    if _newclass:Archive = staticmethod(_file_base_pywrapfile.File_Archive)
    __swig_getmethods__["LogOpStats"] = lambda x: _file_base_pywrapfile.File_LogOpStats
    if _newclass:LogOpStats = staticmethod(_file_base_pywrapfile.File_LogOpStats)
    __swig_getmethods__["LogUnsupportedFile"] = lambda x: _file_base_pywrapfile.File_LogUnsupportedFile
    if _newclass:LogUnsupportedFile = staticmethod(_file_base_pywrapfile.File_LogUnsupportedFile)
    __swig_getmethods__["GenerateShardedFilenames"] = lambda x: _file_base_pywrapfile.File_GenerateShardedFilenames
    if _newclass:GenerateShardedFilenames = staticmethod(_file_base_pywrapfile.File_GenerateShardedFilenames)
    __swig_getmethods__["GenerateShardedFilename"] = lambda x: _file_base_pywrapfile.File_GenerateShardedFilename
    if _newclass:GenerateShardedFilename = staticmethod(_file_base_pywrapfile.File_GenerateShardedFilename)
    __swig_getmethods__["BulkOpenFullySpecified"] = lambda x: _file_base_pywrapfile.File_BulkOpenFullySpecified
    if _newclass:BulkOpenFullySpecified = staticmethod(_file_base_pywrapfile.File_BulkOpenFullySpecified)
    __swig_getmethods__["BulkOpenWithAttr"] = lambda x: _file_base_pywrapfile.File_BulkOpenWithAttr
    if _newclass:BulkOpenWithAttr = staticmethod(_file_base_pywrapfile.File_BulkOpenWithAttr)
    __swig_getmethods__["BulkOpen"] = lambda x: _file_base_pywrapfile.File_BulkOpen
    if _newclass:BulkOpen = staticmethod(_file_base_pywrapfile.File_BulkOpen)
    __swig_getmethods__["BulkRename"] = lambda x: _file_base_pywrapfile.File_BulkRename
    if _newclass:BulkRename = staticmethod(_file_base_pywrapfile.File_BulkRename)
    __swig_getmethods__["BulkStat"] = lambda x: _file_base_pywrapfile.File_BulkStat
    if _newclass:BulkStat = staticmethod(_file_base_pywrapfile.File_BulkStat)
    __swig_getmethods__["BulkStatWithOp"] = lambda x: _file_base_pywrapfile.File_BulkStatWithOp
    if _newclass:BulkStatWithOp = staticmethod(_file_base_pywrapfile.File_BulkStatWithOp)
    __swig_getmethods__["BulkExist"] = lambda x: _file_base_pywrapfile.File_BulkExist
    if _newclass:BulkExist = staticmethod(_file_base_pywrapfile.File_BulkExist)
    __swig_getmethods__["BulkDelete"] = lambda x: _file_base_pywrapfile.File_BulkDelete
    if _newclass:BulkDelete = staticmethod(_file_base_pywrapfile.File_BulkDelete)
    __swig_getmethods__["BulkDeleteWithOp"] = lambda x: _file_base_pywrapfile.File_BulkDeleteWithOp
    if _newclass:BulkDeleteWithOp = staticmethod(_file_base_pywrapfile.File_BulkDeleteWithOp)
    __swig_getmethods__["BulkDeleteDir"] = lambda x: _file_base_pywrapfile.File_BulkDeleteDir
    if _newclass:BulkDeleteDir = staticmethod(_file_base_pywrapfile.File_BulkDeleteDir)
    __swig_getmethods__["BulkSetMode"] = lambda x: _file_base_pywrapfile.File_BulkSetMode
    if _newclass:BulkSetMode = staticmethod(_file_base_pywrapfile.File_BulkSetMode)
    __swig_getmethods__["BulkSetAttributes"] = lambda x: _file_base_pywrapfile.File_BulkSetAttributes
    if _newclass:BulkSetAttributes = staticmethod(_file_base_pywrapfile.File_BulkSetAttributes)
    __swig_getmethods__["BulkSetOwner"] = lambda x: _file_base_pywrapfile.File_BulkSetOwner
    if _newclass:BulkSetOwner = staticmethod(_file_base_pywrapfile.File_BulkSetOwner)
    __swig_getmethods__["BulkSetGroup"] = lambda x: _file_base_pywrapfile.File_BulkSetGroup
    if _newclass:BulkSetGroup = staticmethod(_file_base_pywrapfile.File_BulkSetGroup)
    __swig_getmethods__["pagesize"] = lambda x: _file_base_pywrapfile.File_pagesize
    if _newclass:pagesize = staticmethod(_file_base_pywrapfile.File_pagesize)
    def SetAccessPattern(*args): return _file_base_pywrapfile.File_SetAccessPattern(*args)
    __swig_getmethods__["localhost_name"] = lambda x: _file_base_pywrapfile.File_localhost_name
    if _newclass:localhost_name = staticmethod(_file_base_pywrapfile.File_localhost_name)
    __swig_getmethods__["opstats"] = lambda x: _file_base_pywrapfile.File_opstats
    if _newclass:opstats = staticmethod(_file_base_pywrapfile.File_opstats)
    __swig_getmethods__["GetOpenFiles"] = lambda x: _file_base_pywrapfile.File_GetOpenFiles
    if _newclass:GetOpenFiles = staticmethod(_file_base_pywrapfile.File_GetOpenFiles)
    __swig_getmethods__["SetCurrentThreadUserName"] = lambda x: _file_base_pywrapfile.File_SetCurrentThreadUserName
    if _newclass:SetCurrentThreadUserName = staticmethod(_file_base_pywrapfile.File_SetCurrentThreadUserName)
    __swig_getmethods__["GetCurrentThreadUserName"] = lambda x: _file_base_pywrapfile.File_GetCurrentThreadUserName
    if _newclass:GetCurrentThreadUserName = staticmethod(_file_base_pywrapfile.File_GetCurrentThreadUserName)
    def WriteString(*args): return _file_base_pywrapfile.File_WriteString(*args)

class FilePtr(File):
    def __init__(self, this):
        _swig_setattr(self, File, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, File, 'thisown', 0)
        _swig_setattr(self, File,self.__class__,File)
_file_base_pywrapfile.File_swigregister(FilePtr)

File_Stat = _file_base_pywrapfile.File_Stat

File_Init = _file_base_pywrapfile.File_Init

File_InitWithDatadirFrom = _file_base_pywrapfile.File_InitWithDatadirFrom

File_init_called = _file_base_pywrapfile.File_init_called

File_CreateFullySpecified = _file_base_pywrapfile.File_CreateFullySpecified

File_CreateWithOptions = _file_base_pywrapfile.File_CreateWithOptions

File_CreateWithAttr = _file_base_pywrapfile.File_CreateWithAttr

File_Create = _file_base_pywrapfile.File_Create

File_OpenFullySpecified = _file_base_pywrapfile.File_OpenFullySpecified

File_OpenFullySpecifiedLocked = _file_base_pywrapfile.File_OpenFullySpecifiedLocked

File_OpenWithAttr = _file_base_pywrapfile.File_OpenWithAttr

File_OpenWithOptions = _file_base_pywrapfile.File_OpenWithOptions

File_Open = _file_base_pywrapfile.File_Open

File_OpenLocked = _file_base_pywrapfile.File_OpenLocked

File_OpenFullySpecifiedOrDie = _file_base_pywrapfile.File_OpenFullySpecifiedOrDie

File_OpenWithAttrOrDie = _file_base_pywrapfile.File_OpenWithAttrOrDie

File_OpenOrDie = _file_base_pywrapfile.File_OpenOrDie

File_OpenForAppend = _file_base_pywrapfile.File_OpenForAppend

File_OpenForAppendOrDie = _file_base_pywrapfile.File_OpenForAppendOrDie

File_OpenToCheckpointOrDie = _file_base_pywrapfile.File_OpenToCheckpointOrDie

File_OpenOrDieForWriting = _file_base_pywrapfile.File_OpenOrDieForWriting

File_Readable = _file_base_pywrapfile.File_Readable

File_Exists = _file_base_pywrapfile.File_Exists

File_ExistsWithOp = _file_base_pywrapfile.File_ExistsWithOp

File_IsReplicatedFileName = _file_base_pywrapfile.File_IsReplicatedFileName

File_ConstructFullFileName = _file_base_pywrapfile.File_ConstructFullFileName

File_CanonicalizeFileName = _file_base_pywrapfile.File_CanonicalizeFileName

File_CanonicalizeFileNameList = _file_base_pywrapfile.File_CanonicalizeFileNameList

File_CleanPath = _file_base_pywrapfile.File_CleanPath

File_Basename = _file_base_pywrapfile.File_Basename

File_Suffix = _file_base_pywrapfile.File_Suffix

File_ShardedBasenameWithNumShards = _file_base_pywrapfile.File_ShardedBasenameWithNumShards

File_StripBasename = _file_base_pywrapfile.File_StripBasename

File_AddSlash = _file_base_pywrapfile.File_AddSlash

File_JoinPath = _file_base_pywrapfile.File_JoinPath

File_RemoveHosts = _file_base_pywrapfile.File_RemoveHosts

File_RewriteDatadir = _file_base_pywrapfile.File_RewriteDatadir

File_ExtendedMatch = _file_base_pywrapfile.File_ExtendedMatch

File_ExtendedMatchWithOp = _file_base_pywrapfile.File_ExtendedMatchWithOp

File_ExtendedMatchLocked = _file_base_pywrapfile.File_ExtendedMatchLocked

File_ExtendedMatchLockedWithOp = _file_base_pywrapfile.File_ExtendedMatchLockedWithOp

File_Match = _file_base_pywrapfile.File_Match

File_MatchLocked = _file_base_pywrapfile.File_MatchLocked

File_MatchWithOp = _file_base_pywrapfile.File_MatchWithOp

File_MatchLockedWithOp = _file_base_pywrapfile.File_MatchLockedWithOp

File_GetMatchingFiles = _file_base_pywrapfile.File_GetMatchingFiles

File_GetMatchingFilesLocked = _file_base_pywrapfile.File_GetMatchingFilesLocked

File_Rename = _file_base_pywrapfile.File_Rename

File_CopyFullySpecified = _file_base_pywrapfile.File_CopyFullySpecified

File_CopyWithAttr = _file_base_pywrapfile.File_CopyWithAttr

File_Copy = _file_base_pywrapfile.File_Copy

File_CopyBytes = _file_base_pywrapfile.File_CopyBytes

File_CopyNBytes = _file_base_pywrapfile.File_CopyNBytes

File_CopyToEof = _file_base_pywrapfile.File_CopyToEof

File_Delete = _file_base_pywrapfile.File_Delete

File_DeleteMatchingFiles = _file_base_pywrapfile.File_DeleteMatchingFiles

File_DeleteMatchingFilesWithOp = _file_base_pywrapfile.File_DeleteMatchingFilesWithOp

File_IsAttributeFilename = _file_base_pywrapfile.File_IsAttributeFilename

File_DeleteFileAttributes = _file_base_pywrapfile.File_DeleteFileAttributes

File_DeleteFileAttributesWithOp = _file_base_pywrapfile.File_DeleteFileAttributesWithOp

File_BulkDeleteAttributes = _file_base_pywrapfile.File_BulkDeleteAttributes

File_BulkDeleteAttributesWithOp = _file_base_pywrapfile.File_BulkDeleteAttributesWithOp

File_DFListFileAndDir = _file_base_pywrapfile.File_DFListFileAndDir

File_DeleteRecursively = _file_base_pywrapfile.File_DeleteRecursively

File_SyncAll = _file_base_pywrapfile.File_SyncAll

File_GetFileSize = _file_base_pywrapfile.File_GetFileSize

File_StatLockedWithOp = _file_base_pywrapfile.File_StatLockedWithOp

File_StatLocked = _file_base_pywrapfile.File_StatLocked

File_Statfs = _file_base_pywrapfile.File_Statfs

File_OpenAsync = _file_base_pywrapfile.File_OpenAsync

File_OpenAsyncLocked = _file_base_pywrapfile.File_OpenAsyncLocked

File_OpenFullySpecifiedAsync = _file_base_pywrapfile.File_OpenFullySpecifiedAsync

File_OpenFullySpecifiedAsyncLocked = _file_base_pywrapfile.File_OpenFullySpecifiedAsyncLocked

File_ReadFileToStringOrDie = _file_base_pywrapfile.File_ReadFileToStringOrDie

File_WriteStringToFileOrDie = _file_base_pywrapfile.File_WriteStringToFileOrDie

File_ReadFileToString = _file_base_pywrapfile.File_ReadFileToString

File_WriteStringToFile = _file_base_pywrapfile.File_WriteStringToFile

File_DeleteAsyncLocked = _file_base_pywrapfile.File_DeleteAsyncLocked

File_StatAsyncLocked = _file_base_pywrapfile.File_StatAsyncLocked

File_MatchAsync = _file_base_pywrapfile.File_MatchAsync

File_MatchAsyncLocked = _file_base_pywrapfile.File_MatchAsyncLocked

File_ExtendedMatchAsync = _file_base_pywrapfile.File_ExtendedMatchAsync

File_ExtendedMatchAsyncLocked = _file_base_pywrapfile.File_ExtendedMatchAsyncLocked

File_CreateDirFullySpecified = _file_base_pywrapfile.File_CreateDirFullySpecified

File_CreateDirFullySpecifiedWithOp = _file_base_pywrapfile.File_CreateDirFullySpecifiedWithOp

File_CreateDir = _file_base_pywrapfile.File_CreateDir

File_CreateDirWithOp = _file_base_pywrapfile.File_CreateDirWithOp

File_RecursivelyCreateDirFullySpecified = _file_base_pywrapfile.File_RecursivelyCreateDirFullySpecified

File_RecursivelyCreateDir = _file_base_pywrapfile.File_RecursivelyCreateDir

File_IsDirectory = _file_base_pywrapfile.File_IsDirectory

File_IsDirectoryWithOp = _file_base_pywrapfile.File_IsDirectoryWithOp

File_DeleteDir = _file_base_pywrapfile.File_DeleteDir

File_Snapshot = _file_base_pywrapfile.File_Snapshot

File_SnapshotFile = _file_base_pywrapfile.File_SnapshotFile

File_SetOwner = _file_base_pywrapfile.File_SetOwner

File_SetAttributes = _file_base_pywrapfile.File_SetAttributes

File_SetMode = _file_base_pywrapfile.File_SetMode

File_SetMtime = _file_base_pywrapfile.File_SetMtime

File_SetGroup = _file_base_pywrapfile.File_SetGroup

File_Archive = _file_base_pywrapfile.File_Archive

File_LogOpStats = _file_base_pywrapfile.File_LogOpStats

File_LogUnsupportedFile = _file_base_pywrapfile.File_LogUnsupportedFile

File_GenerateShardedFilenames = _file_base_pywrapfile.File_GenerateShardedFilenames

File_GenerateShardedFilename = _file_base_pywrapfile.File_GenerateShardedFilename

File_BulkOpenFullySpecified = _file_base_pywrapfile.File_BulkOpenFullySpecified

File_BulkOpenWithAttr = _file_base_pywrapfile.File_BulkOpenWithAttr

File_BulkOpen = _file_base_pywrapfile.File_BulkOpen

File_BulkRename = _file_base_pywrapfile.File_BulkRename

File_BulkStat = _file_base_pywrapfile.File_BulkStat

File_BulkStatWithOp = _file_base_pywrapfile.File_BulkStatWithOp

File_BulkExist = _file_base_pywrapfile.File_BulkExist

File_BulkDelete = _file_base_pywrapfile.File_BulkDelete

File_BulkDeleteWithOp = _file_base_pywrapfile.File_BulkDeleteWithOp

File_BulkDeleteDir = _file_base_pywrapfile.File_BulkDeleteDir

File_BulkSetMode = _file_base_pywrapfile.File_BulkSetMode

File_BulkSetAttributes = _file_base_pywrapfile.File_BulkSetAttributes

File_BulkSetOwner = _file_base_pywrapfile.File_BulkSetOwner

File_BulkSetGroup = _file_base_pywrapfile.File_BulkSetGroup

File_pagesize = _file_base_pywrapfile.File_pagesize

File_localhost_name = _file_base_pywrapfile.File_localhost_name

File_opstats = _file_base_pywrapfile.File_opstats

File_GetOpenFiles = _file_base_pywrapfile.File_GetOpenFiles

File_SetCurrentThreadUserName = _file_base_pywrapfile.File_SetCurrentThreadUserName

File_GetCurrentThreadUserName = _file_base_pywrapfile.File_GetCurrentThreadUserName

class FileCloser(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileCloser, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileCloser, name)
    def __repr__(self):
        return "<C FileCloser instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileCloser, 'this', _file_base_pywrapfile.new_FileCloser(*args))
        _swig_setattr(self, FileCloser, 'thisown', 1)
    def get(*args): return _file_base_pywrapfile.FileCloser_get(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileCloser):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __mul__(*args): return _file_base_pywrapfile.FileCloser___mul__(*args)
    def __deref__(*args): return _file_base_pywrapfile.FileCloser___deref__(*args)
    def release(*args): return _file_base_pywrapfile.FileCloser_release(*args)
    def reset(*args): return _file_base_pywrapfile.FileCloser_reset(*args)
    def OpenThis(*args): return _file_base_pywrapfile.FileCloser_OpenThis(*args)
    def OpenWithOp(*args): return _file_base_pywrapfile.FileCloser_OpenWithOp(*args)
    def AccessWithLock(*args): return _file_base_pywrapfile.FileCloser_AccessWithLock(*args)
    def SupportsChubbyLockedAccess(*args): return _file_base_pywrapfile.FileCloser_SupportsChubbyLockedAccess(*args)
    def SupportsConcurrentAppenders(*args): return _file_base_pywrapfile.FileCloser_SupportsConcurrentAppenders(*args)
    def Close(*args): return _file_base_pywrapfile.FileCloser_Close(*args)
    def DeleteThis(*args): return _file_base_pywrapfile.FileCloser_DeleteThis(*args)
    def DeleteWithOp(*args): return _file_base_pywrapfile.FileCloser_DeleteWithOp(*args)
    def StatThis(*args): return _file_base_pywrapfile.FileCloser_StatThis(*args)
    def StatWithOp(*args): return _file_base_pywrapfile.FileCloser_StatWithOp(*args)
    def Truncate(*args): return _file_base_pywrapfile.FileCloser_Truncate(*args)
    def TruncateAsync(*args): return _file_base_pywrapfile.FileCloser_TruncateAsync(*args)
    def TruncateWithOp(*args): return _file_base_pywrapfile.FileCloser_TruncateWithOp(*args)
    def Size(*args): return _file_base_pywrapfile.FileCloser_Size(*args)
    def SizeHint(*args): return _file_base_pywrapfile.FileCloser_SizeHint(*args)
    def Flush(*args): return _file_base_pywrapfile.FileCloser_Flush(*args)
    def Sync(*args): return _file_base_pywrapfile.FileCloser_Sync(*args)
    def DataSync(*args): return _file_base_pywrapfile.FileCloser_DataSync(*args)
    def Tell(*args): return _file_base_pywrapfile.FileCloser_Tell(*args)
    def eof(*args): return _file_base_pywrapfile.FileCloser_eof(*args)
    def Seek(*args): return _file_base_pywrapfile.FileCloser_Seek(*args)
    def Read(*args): return _file_base_pywrapfile.FileCloser_Read(*args)
    def Write(*args): return _file_base_pywrapfile.FileCloser_Write(*args)
    def ReadRegion(*args): return _file_base_pywrapfile.FileCloser_ReadRegion(*args)
    def WriteRegion(*args): return _file_base_pywrapfile.FileCloser_WriteRegion(*args)
    def Append(*args): return _file_base_pywrapfile.FileCloser_Append(*args)
    def RecordAppend(*args): return _file_base_pywrapfile.FileCloser_RecordAppend(*args)
    def PWriteAsync(*args): return _file_base_pywrapfile.FileCloser_PWriteAsync(*args)
    def RecordAppendAsync(*args): return _file_base_pywrapfile.FileCloser_RecordAppendAsync(*args)
    def OpenAsyncThis(*args): return _file_base_pywrapfile.FileCloser_OpenAsyncThis(*args)
    def SupportsAsyncWrite(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncWrite(*args)
    def SupportsAsyncOpen(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncOpen(*args)
    def ReadLine(*args): return _file_base_pywrapfile.FileCloser_ReadLine(*args)
    def ReadToString(*args): return _file_base_pywrapfile.FileCloser_ReadToString(*args)
    def GetMemBlock(*args): return _file_base_pywrapfile.FileCloser_GetMemBlock(*args)
    def GetMemBlockFromDisk(*args): return _file_base_pywrapfile.FileCloser_GetMemBlockFromDisk(*args)
    def PReadWithOp(*args): return _file_base_pywrapfile.FileCloser_PReadWithOp(*args)
    def PRead(*args): return _file_base_pywrapfile.FileCloser_PRead(*args)
    def PWrite(*args): return _file_base_pywrapfile.FileCloser_PWrite(*args)
    def PWriteWithOp(*args): return _file_base_pywrapfile.FileCloser_PWriteWithOp(*args)
    def PReadAsync(*args): return _file_base_pywrapfile.FileCloser_PReadAsync(*args)
    def ReadWithVerifier(*args): return _file_base_pywrapfile.FileCloser_ReadWithVerifier(*args)
    def PReadWithVerifier(*args): return _file_base_pywrapfile.FileCloser_PReadWithVerifier(*args)
    def ReadMultipleDataVariants(*args): return _file_base_pywrapfile.FileCloser_ReadMultipleDataVariants(*args)
    def DeleteAsync(*args): return _file_base_pywrapfile.FileCloser_DeleteAsync(*args)
    def StatAsync(*args): return _file_base_pywrapfile.FileCloser_StatAsync(*args)
    def SyncAsync(*args): return _file_base_pywrapfile.FileCloser_SyncAsync(*args)
    def SupportsAsyncRead(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncRead(*args)
    def SupportsAsyncGetMatchingFiles(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncGetMatchingFiles(*args)
    def SupportsAsyncStat(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncStat(*args)
    def SupportsAsyncDelete(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncDelete(*args)
    def SupportsAsyncSync(*args): return _file_base_pywrapfile.FileCloser_SupportsAsyncSync(*args)
    def SupportsAIORelease(*args): return _file_base_pywrapfile.FileCloser_SupportsAIORelease(*args)
    def TryMMap(*args): return _file_base_pywrapfile.FileCloser_TryMMap(*args)
    def FindAllMirrors(*args): return _file_base_pywrapfile.FileCloser_FindAllMirrors(*args)
    def IsMirrorOnDisk(*args): return _file_base_pywrapfile.FileCloser_IsMirrorOnDisk(*args)
    def FindAllMirrorDisks(*args): return _file_base_pywrapfile.FileCloser_FindAllMirrorDisks(*args)
    def IsSoftError(*args): return _file_base_pywrapfile.FileCloser_IsSoftError(*args)
    def IsFifo(*args): return _file_base_pywrapfile.FileCloser_IsFifo(*args)
    def GetCurrentErrorMessage(*args): return _file_base_pywrapfile.FileCloser_GetCurrentErrorMessage(*args)
    def GetCurrentErrorCode(*args): return _file_base_pywrapfile.FileCloser_GetCurrentErrorCode(*args)
    def ClearError(*args): return _file_base_pywrapfile.FileCloser_ClearError(*args)
    def CreateFileName(*args): return _file_base_pywrapfile.FileCloser_CreateFileName(*args)
    def IsLocalFile(*args): return _file_base_pywrapfile.FileCloser_IsLocalFile(*args)
    def RawIOPRead(*args): return _file_base_pywrapfile.FileCloser_RawIOPRead(*args)
    def SetAccessPattern(*args): return _file_base_pywrapfile.FileCloser_SetAccessPattern(*args)

class FileCloserPtr(FileCloser):
    def __init__(self, this):
        _swig_setattr(self, FileCloser, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileCloser, 'thisown', 0)
        _swig_setattr(self, FileCloser,self.__class__,FileCloser)
_file_base_pywrapfile.FileCloser_swigregister(FileCloserPtr)

class FileDeleter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileDeleter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileDeleter, name)
    def __repr__(self):
        return "<C FileDeleter instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileDeleter, 'this', _file_base_pywrapfile.new_FileDeleter(*args))
        _swig_setattr(self, FileDeleter, 'thisown', 1)
    def get(*args): return _file_base_pywrapfile.FileDeleter_get(*args)
    def __mul__(*args): return _file_base_pywrapfile.FileDeleter___mul__(*args)
    def __deref__(*args): return _file_base_pywrapfile.FileDeleter___deref__(*args)
    def release(*args): return _file_base_pywrapfile.FileDeleter_release(*args)
    def reset(*args): return _file_base_pywrapfile.FileDeleter_reset(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileDeleter):
        try:
            if self.thisown: destroy(self)
        except: pass
    def OpenThis(*args): return _file_base_pywrapfile.FileDeleter_OpenThis(*args)
    def OpenWithOp(*args): return _file_base_pywrapfile.FileDeleter_OpenWithOp(*args)
    def AccessWithLock(*args): return _file_base_pywrapfile.FileDeleter_AccessWithLock(*args)
    def SupportsChubbyLockedAccess(*args): return _file_base_pywrapfile.FileDeleter_SupportsChubbyLockedAccess(*args)
    def SupportsConcurrentAppenders(*args): return _file_base_pywrapfile.FileDeleter_SupportsConcurrentAppenders(*args)
    def Close(*args): return _file_base_pywrapfile.FileDeleter_Close(*args)
    def DeleteThis(*args): return _file_base_pywrapfile.FileDeleter_DeleteThis(*args)
    def DeleteWithOp(*args): return _file_base_pywrapfile.FileDeleter_DeleteWithOp(*args)
    def StatThis(*args): return _file_base_pywrapfile.FileDeleter_StatThis(*args)
    def StatWithOp(*args): return _file_base_pywrapfile.FileDeleter_StatWithOp(*args)
    def Truncate(*args): return _file_base_pywrapfile.FileDeleter_Truncate(*args)
    def TruncateAsync(*args): return _file_base_pywrapfile.FileDeleter_TruncateAsync(*args)
    def TruncateWithOp(*args): return _file_base_pywrapfile.FileDeleter_TruncateWithOp(*args)
    def Size(*args): return _file_base_pywrapfile.FileDeleter_Size(*args)
    def SizeHint(*args): return _file_base_pywrapfile.FileDeleter_SizeHint(*args)
    def Flush(*args): return _file_base_pywrapfile.FileDeleter_Flush(*args)
    def Sync(*args): return _file_base_pywrapfile.FileDeleter_Sync(*args)
    def DataSync(*args): return _file_base_pywrapfile.FileDeleter_DataSync(*args)
    def Tell(*args): return _file_base_pywrapfile.FileDeleter_Tell(*args)
    def eof(*args): return _file_base_pywrapfile.FileDeleter_eof(*args)
    def Seek(*args): return _file_base_pywrapfile.FileDeleter_Seek(*args)
    def Read(*args): return _file_base_pywrapfile.FileDeleter_Read(*args)
    def Write(*args): return _file_base_pywrapfile.FileDeleter_Write(*args)
    def ReadRegion(*args): return _file_base_pywrapfile.FileDeleter_ReadRegion(*args)
    def WriteRegion(*args): return _file_base_pywrapfile.FileDeleter_WriteRegion(*args)
    def Append(*args): return _file_base_pywrapfile.FileDeleter_Append(*args)
    def RecordAppend(*args): return _file_base_pywrapfile.FileDeleter_RecordAppend(*args)
    def PWriteAsync(*args): return _file_base_pywrapfile.FileDeleter_PWriteAsync(*args)
    def RecordAppendAsync(*args): return _file_base_pywrapfile.FileDeleter_RecordAppendAsync(*args)
    def OpenAsyncThis(*args): return _file_base_pywrapfile.FileDeleter_OpenAsyncThis(*args)
    def SupportsAsyncWrite(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncWrite(*args)
    def SupportsAsyncOpen(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncOpen(*args)
    def ReadLine(*args): return _file_base_pywrapfile.FileDeleter_ReadLine(*args)
    def ReadToString(*args): return _file_base_pywrapfile.FileDeleter_ReadToString(*args)
    def GetMemBlock(*args): return _file_base_pywrapfile.FileDeleter_GetMemBlock(*args)
    def GetMemBlockFromDisk(*args): return _file_base_pywrapfile.FileDeleter_GetMemBlockFromDisk(*args)
    def PReadWithOp(*args): return _file_base_pywrapfile.FileDeleter_PReadWithOp(*args)
    def PRead(*args): return _file_base_pywrapfile.FileDeleter_PRead(*args)
    def PWrite(*args): return _file_base_pywrapfile.FileDeleter_PWrite(*args)
    def PWriteWithOp(*args): return _file_base_pywrapfile.FileDeleter_PWriteWithOp(*args)
    def PReadAsync(*args): return _file_base_pywrapfile.FileDeleter_PReadAsync(*args)
    def ReadWithVerifier(*args): return _file_base_pywrapfile.FileDeleter_ReadWithVerifier(*args)
    def PReadWithVerifier(*args): return _file_base_pywrapfile.FileDeleter_PReadWithVerifier(*args)
    def ReadMultipleDataVariants(*args): return _file_base_pywrapfile.FileDeleter_ReadMultipleDataVariants(*args)
    def DeleteAsync(*args): return _file_base_pywrapfile.FileDeleter_DeleteAsync(*args)
    def StatAsync(*args): return _file_base_pywrapfile.FileDeleter_StatAsync(*args)
    def SyncAsync(*args): return _file_base_pywrapfile.FileDeleter_SyncAsync(*args)
    def SupportsAsyncRead(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncRead(*args)
    def SupportsAsyncGetMatchingFiles(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncGetMatchingFiles(*args)
    def SupportsAsyncStat(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncStat(*args)
    def SupportsAsyncDelete(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncDelete(*args)
    def SupportsAsyncSync(*args): return _file_base_pywrapfile.FileDeleter_SupportsAsyncSync(*args)
    def SupportsAIORelease(*args): return _file_base_pywrapfile.FileDeleter_SupportsAIORelease(*args)
    def TryMMap(*args): return _file_base_pywrapfile.FileDeleter_TryMMap(*args)
    def FindAllMirrors(*args): return _file_base_pywrapfile.FileDeleter_FindAllMirrors(*args)
    def IsMirrorOnDisk(*args): return _file_base_pywrapfile.FileDeleter_IsMirrorOnDisk(*args)
    def FindAllMirrorDisks(*args): return _file_base_pywrapfile.FileDeleter_FindAllMirrorDisks(*args)
    def IsSoftError(*args): return _file_base_pywrapfile.FileDeleter_IsSoftError(*args)
    def IsFifo(*args): return _file_base_pywrapfile.FileDeleter_IsFifo(*args)
    def GetCurrentErrorMessage(*args): return _file_base_pywrapfile.FileDeleter_GetCurrentErrorMessage(*args)
    def GetCurrentErrorCode(*args): return _file_base_pywrapfile.FileDeleter_GetCurrentErrorCode(*args)
    def ClearError(*args): return _file_base_pywrapfile.FileDeleter_ClearError(*args)
    def CreateFileName(*args): return _file_base_pywrapfile.FileDeleter_CreateFileName(*args)
    def IsLocalFile(*args): return _file_base_pywrapfile.FileDeleter_IsLocalFile(*args)
    def RawIOPRead(*args): return _file_base_pywrapfile.FileDeleter_RawIOPRead(*args)
    def SetAccessPattern(*args): return _file_base_pywrapfile.FileDeleter_SetAccessPattern(*args)

class FileDeleterPtr(FileDeleter):
    def __init__(self, this):
        _swig_setattr(self, FileDeleter, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileDeleter, 'thisown', 0)
        _swig_setattr(self, FileDeleter,self.__class__,FileDeleter)
_file_base_pywrapfile.FileDeleter_swigregister(FileDeleterPtr)


MultiProtocolReplicatedFileNameToOpen = _file_base_pywrapfile.MultiProtocolReplicatedFileNameToOpen

ReplicatedFileNameToOpen = _file_base_pywrapfile.ReplicatedFileNameToOpen

ParseStubbyRemoteName = _file_base_pywrapfile.ParseStubbyRemoteName

ReplicatedFileNameAppend = _file_base_pywrapfile.ReplicatedFileNameAppend

FindFullPath = _file_base_pywrapfile.FindFullPath
class FileName(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileName, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileName, name)
    def __repr__(self):
        return "<C FileName instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileName, 'this', _file_base_pywrapfile.new_FileName(*args))
        _swig_setattr(self, FileName, 'thisown', 1)
    def Parse(*args): return _file_base_pywrapfile.FileName_Parse(*args)
    GFS_PRIMARY = _file_base_pywrapfile.FileName_GFS_PRIMARY
    GFS_SHADOW = _file_base_pywrapfile.FileName_GFS_SHADOW
    def MakeGFSName(*args): return _file_base_pywrapfile.FileName_MakeGFSName(*args)
    def is_root_directory(*args): return _file_base_pywrapfile.FileName_is_root_directory(*args)
    def is_simple(*args): return _file_base_pywrapfile.FileName_is_simple(*args)
    def is_replicated(*args): return _file_base_pywrapfile.FileName_is_replicated(*args)
    def is_remote(*args): return _file_base_pywrapfile.FileName_is_remote(*args)
    def is_stubby_remote(*args): return _file_base_pywrapfile.FileName_is_stubby_remote(*args)
    def is_bigfile(*args): return _file_base_pywrapfile.FileName_is_bigfile(*args)
    def is_striped(*args): return _file_base_pywrapfile.FileName_is_striped(*args)
    def is_gfs(*args): return _file_base_pywrapfile.FileName_is_gfs(*args)
    def is_gfs_shadow(*args): return _file_base_pywrapfile.FileName_is_gfs_shadow(*args)
    def is_cached(*args): return _file_base_pywrapfile.FileName_is_cached(*args)
    def is_cached_check(*args): return _file_base_pywrapfile.FileName_is_cached_check(*args)
    def is_lock_server(*args): return _file_base_pywrapfile.FileName_is_lock_server(*args)
    def is_namespace(*args): return _file_base_pywrapfile.FileName_is_namespace(*args)
    def is_cfs(*args): return _file_base_pywrapfile.FileName_is_cfs(*args)
    def is_registered_prefix(*args): return _file_base_pywrapfile.FileName_is_registered_prefix(*args)
    def host(*args): return _file_base_pywrapfile.FileName_host(*args)
    def cellname(*args): return _file_base_pywrapfile.FileName_cellname(*args)
    def directory_noslash(*args): return _file_base_pywrapfile.FileName_directory_noslash(*args)
    def basename(*args): return _file_base_pywrapfile.FileName_basename(*args)
    def rest(*args): return _file_base_pywrapfile.FileName_rest(*args)
    def prefix(*args): return _file_base_pywrapfile.FileName_prefix(*args)
    def strip_basename(*args): return _file_base_pywrapfile.FileName_strip_basename(*args)
    def directory(*args): return _file_base_pywrapfile.FileName_directory(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileName):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileNamePtr(FileName):
    def __init__(self, this):
        _swig_setattr(self, FileName, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileName, 'thisown', 0)
        _swig_setattr(self, FileName,self.__class__,FileName)
_file_base_pywrapfile.FileName_swigregister(FileNamePtr)

class FileFactory(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileFactory, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileFactory, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C FileFactory instance at %s>" % (self.this,)
    __swig_getmethods__["RegisterFactory"] = lambda x: _file_base_pywrapfile.FileFactory_RegisterFactory
    if _newclass:RegisterFactory = staticmethod(_file_base_pywrapfile.FileFactory_RegisterFactory)
    __swig_getmethods__["RegisterFactoryPrefix"] = lambda x: _file_base_pywrapfile.FileFactory_RegisterFactoryPrefix
    if _newclass:RegisterFactoryPrefix = staticmethod(_file_base_pywrapfile.FileFactory_RegisterFactoryPrefix)
    __swig_getmethods__["UnRegisterFactoryPrefix"] = lambda x: _file_base_pywrapfile.FileFactory_UnRegisterFactoryPrefix
    if _newclass:UnRegisterFactoryPrefix = staticmethod(_file_base_pywrapfile.FileFactory_UnRegisterFactoryPrefix)
    __swig_getmethods__["Find"] = lambda x: _file_base_pywrapfile.FileFactory_Find
    if _newclass:Find = staticmethod(_file_base_pywrapfile.FileFactory_Find)
    __swig_getmethods__["FindPrefixFactory"] = lambda x: _file_base_pywrapfile.FileFactory_FindPrefixFactory
    if _newclass:FindPrefixFactory = staticmethod(_file_base_pywrapfile.FileFactory_FindPrefixFactory)
    __swig_getmethods__["FindPrefixFactoryAndPrefix"] = lambda x: _file_base_pywrapfile.FileFactory_FindPrefixFactoryAndPrefix
    if _newclass:FindPrefixFactoryAndPrefix = staticmethod(_file_base_pywrapfile.FileFactory_FindPrefixFactoryAndPrefix)
    __swig_getmethods__["FindBestFactory"] = lambda x: _file_base_pywrapfile.FileFactory_FindBestFactory
    if _newclass:FindBestFactory = staticmethod(_file_base_pywrapfile.FileFactory_FindBestFactory)
    def Create(*args): return _file_base_pywrapfile.FileFactory_Create(*args)
    def CreateFullySpecified(*args): return _file_base_pywrapfile.FileFactory_CreateFullySpecified(*args)
    def CreateWithOptions(*args): return _file_base_pywrapfile.FileFactory_CreateWithOptions(*args)
    def Rename(*args): return _file_base_pywrapfile.FileFactory_Rename(*args)
    def Match(*args): return _file_base_pywrapfile.FileFactory_Match(*args)
    def MatchLocked(*args): return _file_base_pywrapfile.FileFactory_MatchLocked(*args)
    def MatchLockedWithOp(*args): return _file_base_pywrapfile.FileFactory_MatchLockedWithOp(*args)
    def MatchWithOp(*args): return _file_base_pywrapfile.FileFactory_MatchWithOp(*args)
    def Stat(*args): return _file_base_pywrapfile.FileFactory_Stat(*args)
    def StatWithOp(*args): return _file_base_pywrapfile.FileFactory_StatWithOp(*args)
    def StatLocked(*args): return _file_base_pywrapfile.FileFactory_StatLocked(*args)
    def StatLockedWithOp(*args): return _file_base_pywrapfile.FileFactory_StatLockedWithOp(*args)
    def MatchAsync(*args): return _file_base_pywrapfile.FileFactory_MatchAsync(*args)
    def MatchAsyncLocked(*args): return _file_base_pywrapfile.FileFactory_MatchAsyncLocked(*args)
    def StatAsync(*args): return _file_base_pywrapfile.FileFactory_StatAsync(*args)
    def StatAsyncLocked(*args): return _file_base_pywrapfile.FileFactory_StatAsyncLocked(*args)
    def Statfs(*args): return _file_base_pywrapfile.FileFactory_Statfs(*args)
    def Readable(*args): return _file_base_pywrapfile.FileFactory_Readable(*args)
    def CreateDir(*args): return _file_base_pywrapfile.FileFactory_CreateDir(*args)
    def CreateDirWithOp(*args): return _file_base_pywrapfile.FileFactory_CreateDirWithOp(*args)
    def CreateDirFullySpecified(*args): return _file_base_pywrapfile.FileFactory_CreateDirFullySpecified(*args)
    def CreateDirFullySpecifiedWithOp(*args): return _file_base_pywrapfile.FileFactory_CreateDirFullySpecifiedWithOp(*args)
    def RecursivelyCreateDirFullySpecified(*args): return _file_base_pywrapfile.FileFactory_RecursivelyCreateDirFullySpecified(*args)
    def DeleteDir(*args): return _file_base_pywrapfile.FileFactory_DeleteDir(*args)
    def Snapshot(*args): return _file_base_pywrapfile.FileFactory_Snapshot(*args)
    def SetOwner(*args): return _file_base_pywrapfile.FileFactory_SetOwner(*args)
    def SetAttributes(*args): return _file_base_pywrapfile.FileFactory_SetAttributes(*args)
    def SetMode(*args): return _file_base_pywrapfile.FileFactory_SetMode(*args)
    def SetMtime(*args): return _file_base_pywrapfile.FileFactory_SetMtime(*args)
    def SetGroup(*args): return _file_base_pywrapfile.FileFactory_SetGroup(*args)
    def Archive(*args): return _file_base_pywrapfile.FileFactory_Archive(*args)
    __swig_getmethods__["FilterMatches"] = lambda x: _file_base_pywrapfile.FileFactory_FilterMatches
    if _newclass:FilterMatches = staticmethod(_file_base_pywrapfile.FileFactory_FilterMatches)
    def BulkOpen(*args): return _file_base_pywrapfile.FileFactory_BulkOpen(*args)
    def BulkOpenFullySpecified(*args): return _file_base_pywrapfile.FileFactory_BulkOpenFullySpecified(*args)
    def BulkRename(*args): return _file_base_pywrapfile.FileFactory_BulkRename(*args)
    def BulkStat(*args): return _file_base_pywrapfile.FileFactory_BulkStat(*args)
    def BulkStatWithOp(*args): return _file_base_pywrapfile.FileFactory_BulkStatWithOp(*args)
    def BulkExist(*args): return _file_base_pywrapfile.FileFactory_BulkExist(*args)
    def BulkDelete(*args): return _file_base_pywrapfile.FileFactory_BulkDelete(*args)
    def BulkDeleteWithOp(*args): return _file_base_pywrapfile.FileFactory_BulkDeleteWithOp(*args)
    def BulkDeleteDir(*args): return _file_base_pywrapfile.FileFactory_BulkDeleteDir(*args)
    def BulkSetAttributes(*args): return _file_base_pywrapfile.FileFactory_BulkSetAttributes(*args)
    def BulkSetMode(*args): return _file_base_pywrapfile.FileFactory_BulkSetMode(*args)
    def BulkSetOwner(*args): return _file_base_pywrapfile.FileFactory_BulkSetOwner(*args)
    def BulkSetGroup(*args): return _file_base_pywrapfile.FileFactory_BulkSetGroup(*args)

class FileFactoryPtr(FileFactory):
    def __init__(self, this):
        _swig_setattr(self, FileFactory, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileFactory, 'thisown', 0)
        _swig_setattr(self, FileFactory,self.__class__,FileFactory)
_file_base_pywrapfile.FileFactory_swigregister(FileFactoryPtr)

FileFactory_RegisterFactory = _file_base_pywrapfile.FileFactory_RegisterFactory

FileFactory_RegisterFactoryPrefix = _file_base_pywrapfile.FileFactory_RegisterFactoryPrefix

FileFactory_UnRegisterFactoryPrefix = _file_base_pywrapfile.FileFactory_UnRegisterFactoryPrefix

FileFactory_Find = _file_base_pywrapfile.FileFactory_Find

FileFactory_FindPrefixFactory = _file_base_pywrapfile.FileFactory_FindPrefixFactory

FileFactory_FindPrefixFactoryAndPrefix = _file_base_pywrapfile.FileFactory_FindPrefixFactoryAndPrefix

FileFactory_FindBestFactory = _file_base_pywrapfile.FileFactory_FindBestFactory

FileFactory_FilterMatches = _file_base_pywrapfile.FileFactory_FilterMatches


IsUInt64ANegativeInt64 = _file_base_pywrapfile.IsUInt64ANegativeInt64
class FileReedSolomon(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileReedSolomon, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileReedSolomon, name)
    def __repr__(self):
        return "<C FileReedSolomon instance at %s>" % (self.this,)
    ENCODING_5_8 = _file_base_pywrapfile.FileReedSolomon_ENCODING_5_8
    ENCODING_9_13 = _file_base_pywrapfile.FileReedSolomon_ENCODING_9_13
    ENCODING_20_30 = _file_base_pywrapfile.FileReedSolomon_ENCODING_20_30
    NUM_ENCODINGS = _file_base_pywrapfile.FileReedSolomon_NUM_ENCODINGS
    __swig_getmethods__["Encoding2Params"] = lambda x: _file_base_pywrapfile.FileReedSolomon_Encoding2Params
    if _newclass:Encoding2Params = staticmethod(_file_base_pywrapfile.FileReedSolomon_Encoding2Params)
    __swig_getmethods__["Name2Encoding"] = lambda x: _file_base_pywrapfile.FileReedSolomon_Name2Encoding
    if _newclass:Name2Encoding = staticmethod(_file_base_pywrapfile.FileReedSolomon_Name2Encoding)
    __swig_getmethods__["Encoding2Name"] = lambda x: _file_base_pywrapfile.FileReedSolomon_Encoding2Name
    if _newclass:Encoding2Name = staticmethod(_file_base_pywrapfile.FileReedSolomon_Encoding2Name)
    def __init__(self, *args):
        _swig_setattr(self, FileReedSolomon, 'this', _file_base_pywrapfile.new_FileReedSolomon(*args))
        _swig_setattr(self, FileReedSolomon, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileReedSolomon):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileReedSolomonPtr(FileReedSolomon):
    def __init__(self, this):
        _swig_setattr(self, FileReedSolomon, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileReedSolomon, 'thisown', 0)
        _swig_setattr(self, FileReedSolomon,self.__class__,FileReedSolomon)
_file_base_pywrapfile.FileReedSolomon_swigregister(FileReedSolomonPtr)

FileReedSolomon_Encoding2Params = _file_base_pywrapfile.FileReedSolomon_Encoding2Params

FileReedSolomon_Name2Encoding = _file_base_pywrapfile.FileReedSolomon_Name2Encoding

FileReedSolomon_Encoding2Name = _file_base_pywrapfile.FileReedSolomon_Encoding2Name

class InputBuffer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, InputBuffer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, InputBuffer, name)
    def __repr__(self):
        return "<C InputBuffer instance at %s>" % (self.this,)
    kDefaultBufferSize = _file_base_pywrapfile.InputBuffer_kDefaultBufferSize
    def __init__(self, *args):
        _swig_setattr(self, InputBuffer, 'this', _file_base_pywrapfile.new_InputBuffer(*args))
        _swig_setattr(self, InputBuffer, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_InputBuffer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CloseFile(*args): return _file_base_pywrapfile.InputBuffer_CloseFile(*args)
    def Read(*args): return _file_base_pywrapfile.InputBuffer_Read(*args)
    def ReadToString(*args): return _file_base_pywrapfile.InputBuffer_ReadToString(*args)
    def TryRead(*args): return _file_base_pywrapfile.InputBuffer_TryRead(*args)
    def Prefetch(*args): return _file_base_pywrapfile.InputBuffer_Prefetch(*args)
    def Unfetch(*args): return _file_base_pywrapfile.InputBuffer_Unfetch(*args)
    def AsyncReadEnabled(*args): return _file_base_pywrapfile.InputBuffer_AsyncReadEnabled(*args)
    def UseAIO(*args): return _file_base_pywrapfile.InputBuffer_UseAIO(*args)
    def Tell(*args): return _file_base_pywrapfile.InputBuffer_Tell(*args)
    def Seek(*args): return _file_base_pywrapfile.InputBuffer_Seek(*args)
    def Size(*args): return _file_base_pywrapfile.InputBuffer_Size(*args)
    def SizeHint(*args): return _file_base_pywrapfile.InputBuffer_SizeHint(*args)
    def eof(*args): return _file_base_pywrapfile.InputBuffer_eof(*args)
    def AvailableData(*args): return _file_base_pywrapfile.InputBuffer_AvailableData(*args)
    def ReadLine(*args): return _file_base_pywrapfile.InputBuffer_ReadLine(*args)
    def ReadLineAsString(*args): return _file_base_pywrapfile.InputBuffer_ReadLineAsString(*args)
    def GetFile(*args): return _file_base_pywrapfile.InputBuffer_GetFile(*args)
    def ReadVarint32(*args): return _file_base_pywrapfile.InputBuffer_ReadVarint32(*args)
    def SetFile(*args): return _file_base_pywrapfile.InputBuffer_SetFile(*args)
    def CreateFileName(*args): return _file_base_pywrapfile.InputBuffer_CreateFileName(*args)
    def SetReadSize(*args): return _file_base_pywrapfile.InputBuffer_SetReadSize(*args)
    def SetLookahead(*args): return _file_base_pywrapfile.InputBuffer_SetLookahead(*args)
    def ReadGeneral(*args): return _file_base_pywrapfile.InputBuffer_ReadGeneral(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywrapfile.InputBuffer_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywrapfile.InputBuffer_owns_file(*args)
    def die_on_error(*args): return _file_base_pywrapfile.InputBuffer_die_on_error(*args)
    def set_die_on_error(*args): return _file_base_pywrapfile.InputBuffer_set_die_on_error(*args)
    def read_error(*args): return _file_base_pywrapfile.InputBuffer_read_error(*args)
    def SetChecksumming(*args): return _file_base_pywrapfile.InputBuffer_SetChecksumming(*args)
    NO_CHECKSUMMING = _file_base_pywrapfile.InputBuffer_NO_CHECKSUMMING
    NO_ATTRIBUTE_FILE = _file_base_pywrapfile.InputBuffer_NO_ATTRIBUTE_FILE
    MATCHES_PREFIX = _file_base_pywrapfile.InputBuffer_MATCHES_PREFIX
    MATCHES_FULL = _file_base_pywrapfile.InputBuffer_MATCHES_FULL
    MISMATCH = _file_base_pywrapfile.InputBuffer_MISMATCH
    def VerifyChecksum(*args): return _file_base_pywrapfile.InputBuffer_VerifyChecksum(*args)

class InputBufferPtr(InputBuffer):
    def __init__(self, this):
        _swig_setattr(self, InputBuffer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, InputBuffer, 'thisown', 0)
        _swig_setattr(self, InputBuffer,self.__class__,InputBuffer)
_file_base_pywrapfile.InputBuffer_swigregister(InputBufferPtr)

class InputBufferOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, InputBufferOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, InputBufferOptions, name)
    def __repr__(self):
        return "<C InputBufferOptions instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, InputBufferOptions, 'this', _file_base_pywrapfile.new_InputBufferOptions(*args))
        _swig_setattr(self, InputBufferOptions, 'thisown', 1)
    def set_memory_budget(*args): return _file_base_pywrapfile.InputBufferOptions_set_memory_budget(*args)
    def memory_budget(*args): return _file_base_pywrapfile.InputBufferOptions_memory_budget(*args)
    def set_buffer_size(*args): return _file_base_pywrapfile.InputBufferOptions_set_buffer_size(*args)
    def buffer_size(*args): return _file_base_pywrapfile.InputBufferOptions_buffer_size(*args)
    def set_lookahead(*args): return _file_base_pywrapfile.InputBufferOptions_set_lookahead(*args)
    def lookahead(*args): return _file_base_pywrapfile.InputBufferOptions_lookahead(*args)
    def set_fixed_size(*args): return _file_base_pywrapfile.InputBufferOptions_set_fixed_size(*args)
    def fixed_size(*args): return _file_base_pywrapfile.InputBufferOptions_fixed_size(*args)
    def set_lookahead_on_open(*args): return _file_base_pywrapfile.InputBufferOptions_set_lookahead_on_open(*args)
    def lookahead_on_open(*args): return _file_base_pywrapfile.InputBufferOptions_lookahead_on_open(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_InputBufferOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class InputBufferOptionsPtr(InputBufferOptions):
    def __init__(self, this):
        _swig_setattr(self, InputBufferOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, InputBufferOptions, 'thisown', 0)
        _swig_setattr(self, InputBufferOptions,self.__class__,InputBufferOptions)
_file_base_pywrapfile.InputBufferOptions_swigregister(InputBufferOptionsPtr)

class Operation(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Operation, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Operation, name)
    def __repr__(self):
        return "<C file::Operation instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, Operation, 'this', _file_base_pywrapfile.new_Operation(*args))
        _swig_setattr(self, Operation, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_Operation):
        try:
            if self.thisown: destroy(self)
        except: pass
    def error(*args): return _file_base_pywrapfile.Operation_error(*args)
    def ok(*args): return _file_base_pywrapfile.Operation_ok(*args)
    def CheckSuccess(*args): return _file_base_pywrapfile.Operation_CheckSuccess(*args)
    def Status(*args): return _file_base_pywrapfile.Operation_Status(*args)
    def CopyFrom(*args): return _file_base_pywrapfile.Operation_CopyFrom(*args)
    def SetDeadlineLength(*args): return _file_base_pywrapfile.Operation_SetDeadlineLength(*args)
    def SetAbsoluteDeadline(*args): return _file_base_pywrapfile.Operation_SetAbsoluteDeadline(*args)
    def ClearDeadline(*args): return _file_base_pywrapfile.Operation_ClearDeadline(*args)
    def HasDeadline(*args): return _file_base_pywrapfile.Operation_HasDeadline(*args)
    def GetDeadline(*args): return _file_base_pywrapfile.Operation_GetDeadline(*args)
    def priority(*args): return _file_base_pywrapfile.Operation_priority(*args)
    def set_priority(*args): return _file_base_pywrapfile.Operation_set_priority(*args)
    def InternalStart(*args): return _file_base_pywrapfile.Operation_InternalStart(*args)
    def InternalFinish(*args): return _file_base_pywrapfile.Operation_InternalFinish(*args)
    def SetError(*args): return _file_base_pywrapfile.Operation_SetError(*args)
    def ClearError(*args): return _file_base_pywrapfile.Operation_ClearError(*args)
    def retry(*args): return _file_base_pywrapfile.Operation_retry(*args)
    def set_retry(*args): return _file_base_pywrapfile.Operation_set_retry(*args)
    def descriptor(*args): return _file_base_pywrapfile.Operation_descriptor(*args)
    def resource_user(*args): return _file_base_pywrapfile.Operation_resource_user(*args)
    def set_resource_user(*args): return _file_base_pywrapfile.Operation_set_resource_user(*args)

class OperationPtr(Operation):
    def __init__(self, this):
        _swig_setattr(self, Operation, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Operation, 'thisown', 0)
        _swig_setattr(self, Operation,self.__class__,Operation)
_file_base_pywrapfile.Operation_swigregister(OperationPtr)


TranslateFromErrno = _file_base_pywrapfile.TranslateFromErrno
class OutputBufferOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, OutputBufferOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, OutputBufferOptions, name)
    def __repr__(self):
        return "<C OutputBufferOptions instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, OutputBufferOptions, 'this', _file_base_pywrapfile.new_OutputBufferOptions(*args))
        _swig_setattr(self, OutputBufferOptions, 'thisown', 1)
    def set_file_attributes(*args): return _file_base_pywrapfile.OutputBufferOptions_set_file_attributes(*args)
    def set_file_permissions(*args): return _file_base_pywrapfile.OutputBufferOptions_set_file_permissions(*args)
    def set_file_group(*args): return _file_base_pywrapfile.OutputBufferOptions_set_file_group(*args)
    def set_aio_budget(*args): return _file_base_pywrapfile.OutputBufferOptions_set_aio_budget(*args)
    def set_memory_budget(*args): return _file_base_pywrapfile.OutputBufferOptions_set_memory_budget(*args)
    def set_checkpoint(*args): return _file_base_pywrapfile.OutputBufferOptions_set_checkpoint(*args)
    def set_attribute_file(*args): return _file_base_pywrapfile.OutputBufferOptions_set_attribute_file(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_OutputBufferOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class OutputBufferOptionsPtr(OutputBufferOptions):
    def __init__(self, this):
        _swig_setattr(self, OutputBufferOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, OutputBufferOptions, 'thisown', 0)
        _swig_setattr(self, OutputBufferOptions,self.__class__,OutputBufferOptions)
_file_base_pywrapfile.OutputBufferOptions_swigregister(OutputBufferOptionsPtr)

class OutputBuffer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, OutputBuffer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, OutputBuffer, name)
    def __repr__(self):
        return "<C OutputBuffer instance at %s>" % (self.this,)
    kDefaultBufferSize = _file_base_pywrapfile.OutputBuffer_kDefaultBufferSize
    __swig_getmethods__["OpenWithOptions"] = lambda x: _file_base_pywrapfile.OutputBuffer_OpenWithOptions
    if _newclass:OpenWithOptions = staticmethod(_file_base_pywrapfile.OutputBuffer_OpenWithOptions)
    __swig_getmethods__["OpenWithFile"] = lambda x: _file_base_pywrapfile.OutputBuffer_OpenWithFile
    if _newclass:OpenWithFile = staticmethod(_file_base_pywrapfile.OutputBuffer_OpenWithFile)
    __swig_getmethods__["OpenOrDie"] = lambda x: _file_base_pywrapfile.OutputBuffer_OpenOrDie
    if _newclass:OpenOrDie = staticmethod(_file_base_pywrapfile.OutputBuffer_OpenOrDie)
    def __init__(self, *args):
        _swig_setattr(self, OutputBuffer, 'this', _file_base_pywrapfile.new_OutputBuffer(*args))
        _swig_setattr(self, OutputBuffer, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_OutputBuffer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CloseFile(*args): return _file_base_pywrapfile.OutputBuffer_CloseFile(*args)
    def Write(*args): return _file_base_pywrapfile.OutputBuffer_Write(*args)
    def TryWrite(*args): return _file_base_pywrapfile.OutputBuffer_TryWrite(*args)
    def Flush(*args): return _file_base_pywrapfile.OutputBuffer_Flush(*args)
    def Size(*args): return _file_base_pywrapfile.OutputBuffer_Size(*args)
    def Tell(*args): return _file_base_pywrapfile.OutputBuffer_Tell(*args)
    def AvailableBuffer(*args): return _file_base_pywrapfile.OutputBuffer_AvailableBuffer(*args)
    def Seek(*args): return _file_base_pywrapfile.OutputBuffer_Seek(*args)
    def Truncate(*args): return _file_base_pywrapfile.OutputBuffer_Truncate(*args)
    def RewindOrDie(*args): return _file_base_pywrapfile.OutputBuffer_RewindOrDie(*args)
    def AsyncEnabled(*args): return _file_base_pywrapfile.OutputBuffer_AsyncEnabled(*args)
    def WriteString(*args): return _file_base_pywrapfile.OutputBuffer_WriteString(*args)
    def WriteLine(*args): return _file_base_pywrapfile.OutputBuffer_WriteLine(*args)
    def Align(*args): return _file_base_pywrapfile.OutputBuffer_Align(*args)
    def AlignDefault(*args): return _file_base_pywrapfile.OutputBuffer_AlignDefault(*args)
    def GetFile(*args): return _file_base_pywrapfile.OutputBuffer_GetFile(*args)
    def CreateFileName(*args): return _file_base_pywrapfile.OutputBuffer_CreateFileName(*args)
    def GetAttributes(*args): return _file_base_pywrapfile.OutputBuffer_GetAttributes(*args)
    def Checkpoint(*args): return _file_base_pywrapfile.OutputBuffer_Checkpoint(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywrapfile.OutputBuffer_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywrapfile.OutputBuffer_owns_file(*args)
    def keeps_checksum(*args): return _file_base_pywrapfile.OutputBuffer_keeps_checksum(*args)

class OutputBufferPtr(OutputBuffer):
    def __init__(self, this):
        _swig_setattr(self, OutputBuffer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, OutputBuffer, 'thisown', 0)
        _swig_setattr(self, OutputBuffer,self.__class__,OutputBuffer)
_file_base_pywrapfile.OutputBuffer_swigregister(OutputBufferPtr)

OutputBuffer_OpenWithOptions = _file_base_pywrapfile.OutputBuffer_OpenWithOptions

OutputBuffer_OpenWithFile = _file_base_pywrapfile.OutputBuffer_OpenWithFile

OutputBuffer_OpenOrDie = _file_base_pywrapfile.OutputBuffer_OpenOrDie

class Sha1(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Sha1, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Sha1, name)
    def __repr__(self):
        return "<C Sha1 instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, Sha1, 'this', _file_base_pywrapfile.new_Sha1(*args))
        _swig_setattr(self, Sha1, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_Sha1):
        try:
            if self.thisown: destroy(self)
        except: pass

class Sha1Ptr(Sha1):
    def __init__(self, this):
        _swig_setattr(self, Sha1, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Sha1, 'thisown', 0)
        _swig_setattr(self, Sha1,self.__class__,Sha1)
_file_base_pywrapfile.Sha1_swigregister(Sha1Ptr)

class ChecksumState(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ChecksumState, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ChecksumState, name)
    def __repr__(self):
        return "<C ChecksumState instance at %s>" % (self.this,)
    kBlockSize = _file_base_pywrapfile.ChecksumState_kBlockSize
    kChunkSize = _file_base_pywrapfile.ChecksumState_kChunkSize
    def __init__(self, *args):
        _swig_setattr(self, ChecksumState, 'this', _file_base_pywrapfile.new_ChecksumState(*args))
        _swig_setattr(self, ChecksumState, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_ChecksumState):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __eq__(*args): return _file_base_pywrapfile.ChecksumState___eq__(*args)
    def __ne__(*args): return _file_base_pywrapfile.ChecksumState___ne__(*args)
    def Equals(*args): return _file_base_pywrapfile.ChecksumState_Equals(*args)
    def Add(*args): return _file_base_pywrapfile.ChecksumState_Add(*args)
    def Clear(*args): return _file_base_pywrapfile.ChecksumState_Clear(*args)
    def Checksum(*args): return _file_base_pywrapfile.ChecksumState_Checksum(*args)
    def AlignedChecksum(*args): return _file_base_pywrapfile.ChecksumState_AlignedChecksum(*args)
    def Length(*args): return _file_base_pywrapfile.ChecksumState_Length(*args)
    def History(*args): return _file_base_pywrapfile.ChecksumState_History(*args)
    def HistoryLength(*args): return _file_base_pywrapfile.ChecksumState_HistoryLength(*args)
    def AddFile(*args): return _file_base_pywrapfile.ChecksumState_AddFile(*args)
    def AddOpenFile(*args): return _file_base_pywrapfile.ChecksumState_AddOpenFile(*args)
    def AddFileBytes(*args): return _file_base_pywrapfile.ChecksumState_AddFileBytes(*args)
    def AddOpenFileBytes(*args): return _file_base_pywrapfile.ChecksumState_AddOpenFileBytes(*args)
    __swig_getmethods__["VerifyChecksum"] = lambda x: _file_base_pywrapfile.ChecksumState_VerifyChecksum
    if _newclass:VerifyChecksum = staticmethod(_file_base_pywrapfile.ChecksumState_VerifyChecksum)
    __swig_getmethods__["SparseChecksumFile"] = lambda x: _file_base_pywrapfile.ChecksumState_SparseChecksumFile
    if _newclass:SparseChecksumFile = staticmethod(_file_base_pywrapfile.ChecksumState_SparseChecksumFile)
    __swig_getmethods__["VerifyChecksum"] = lambda x: _file_base_pywrapfile.ChecksumState_VerifyChecksum
    if _newclass:VerifyChecksum = staticmethod(_file_base_pywrapfile.ChecksumState_VerifyChecksum)
    __swig_getmethods__["TruncateChecksummedFile"] = lambda x: _file_base_pywrapfile.ChecksumState_TruncateChecksummedFile
    if _newclass:TruncateChecksummedFile = staticmethod(_file_base_pywrapfile.ChecksumState_TruncateChecksummedFile)
    def TruncateToPosition(*args): return _file_base_pywrapfile.ChecksumState_TruncateToPosition(*args)
    def HistoryIndexToPositionRange(*args): return _file_base_pywrapfile.ChecksumState_HistoryIndexToPositionRange(*args)
    def SetRunningChecksum(*args): return _file_base_pywrapfile.ChecksumState_SetRunningChecksum(*args)

class ChecksumStatePtr(ChecksumState):
    def __init__(self, this):
        _swig_setattr(self, ChecksumState, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ChecksumState, 'thisown', 0)
        _swig_setattr(self, ChecksumState,self.__class__,ChecksumState)
_file_base_pywrapfile.ChecksumState_swigregister(ChecksumStatePtr)

ChecksumState_SparseChecksumFile = _file_base_pywrapfile.ChecksumState_SparseChecksumFile

ChecksumState_VerifyChecksum = _file_base_pywrapfile.ChecksumState_VerifyChecksum

ChecksumState_TruncateChecksummedFile = _file_base_pywrapfile.ChecksumState_TruncateChecksummedFile

class Sha1Checksum(Sha1):
    __swig_setmethods__ = {}
    for _s in [Sha1]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, Sha1Checksum, name, value)
    __swig_getmethods__ = {}
    for _s in [Sha1]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, Sha1Checksum, name)
    def __repr__(self):
        return "<C Sha1Checksum instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, Sha1Checksum, 'this', _file_base_pywrapfile.new_Sha1Checksum(*args))
        _swig_setattr(self, Sha1Checksum, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_Sha1Checksum):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Add(*args): return _file_base_pywrapfile.Sha1Checksum_Add(*args)
    def AddFile(*args): return _file_base_pywrapfile.Sha1Checksum_AddFile(*args)
    def AddOpenFile(*args): return _file_base_pywrapfile.Sha1Checksum_AddOpenFile(*args)

class Sha1ChecksumPtr(Sha1Checksum):
    def __init__(self, this):
        _swig_setattr(self, Sha1Checksum, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Sha1Checksum, 'thisown', 0)
        _swig_setattr(self, Sha1Checksum,self.__class__,Sha1Checksum)
_file_base_pywrapfile.Sha1Checksum_swigregister(Sha1ChecksumPtr)

class FileVersion(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileVersion, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileVersion, name)
    def __repr__(self):
        return "<C FileVersion instance at %s>" % (self.this,)
    __swig_setmethods__["time"] = _file_base_pywrapfile.FileVersion_time_set
    __swig_getmethods__["time"] = _file_base_pywrapfile.FileVersion_time_get
    if _newclass:time = property(_file_base_pywrapfile.FileVersion_time_get, _file_base_pywrapfile.FileVersion_time_set)
    __swig_setmethods__["creator"] = _file_base_pywrapfile.FileVersion_creator_set
    __swig_getmethods__["creator"] = _file_base_pywrapfile.FileVersion_creator_get
    if _newclass:creator = property(_file_base_pywrapfile.FileVersion_creator_get, _file_base_pywrapfile.FileVersion_creator_set)
    def __init__(self, *args):
        _swig_setattr(self, FileVersion, 'this', _file_base_pywrapfile.new_FileVersion(*args))
        _swig_setattr(self, FileVersion, 'thisown', 1)
    def Clear(*args): return _file_base_pywrapfile.FileVersion_Clear(*args)
    def IsEmpty(*args): return _file_base_pywrapfile.FileVersion_IsEmpty(*args)
    def ToString(*args): return _file_base_pywrapfile.FileVersion_ToString(*args)
    __swig_getmethods__["FromString"] = lambda x: _file_base_pywrapfile.FileVersion_FromString
    if _newclass:FromString = staticmethod(_file_base_pywrapfile.FileVersion_FromString)
    __swig_getmethods__["cmp"] = lambda x: _file_base_pywrapfile.FileVersion_cmp
    if _newclass:cmp = staticmethod(_file_base_pywrapfile.FileVersion_cmp)
    def __eq__(*args): return _file_base_pywrapfile.FileVersion___eq__(*args)
    def __ne__(*args): return _file_base_pywrapfile.FileVersion___ne__(*args)
    def __le__(*args): return _file_base_pywrapfile.FileVersion___le__(*args)
    def __ge__(*args): return _file_base_pywrapfile.FileVersion___ge__(*args)
    def __lt__(*args): return _file_base_pywrapfile.FileVersion___lt__(*args)
    def __gt__(*args): return _file_base_pywrapfile.FileVersion___gt__(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileVersion):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileVersionPtr(FileVersion):
    def __init__(self, this):
        _swig_setattr(self, FileVersion, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileVersion, 'thisown', 0)
        _swig_setattr(self, FileVersion,self.__class__,FileVersion)
_file_base_pywrapfile.FileVersion_swigregister(FileVersionPtr)

FileVersion_FromString = _file_base_pywrapfile.FileVersion_FromString

FileVersion_cmp = _file_base_pywrapfile.FileVersion_cmp

class FileAttr(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileAttr, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileAttr, name)
    def __repr__(self):
        return "<C FileAttr instance at %s>" % (self.this,)
    __swig_setmethods__["checksum"] = _file_base_pywrapfile.FileAttr_checksum_set
    __swig_getmethods__["checksum"] = _file_base_pywrapfile.FileAttr_checksum_get
    if _newclass:checksum = property(_file_base_pywrapfile.FileAttr_checksum_get, _file_base_pywrapfile.FileAttr_checksum_set)
    __swig_setmethods__["version"] = _file_base_pywrapfile.FileAttr_version_set
    __swig_getmethods__["version"] = _file_base_pywrapfile.FileAttr_version_get
    if _newclass:version = property(_file_base_pywrapfile.FileAttr_version_get, _file_base_pywrapfile.FileAttr_version_set)
    __swig_setmethods__["finalized"] = _file_base_pywrapfile.FileAttr_finalized_set
    __swig_getmethods__["finalized"] = _file_base_pywrapfile.FileAttr_finalized_get
    if _newclass:finalized = property(_file_base_pywrapfile.FileAttr_finalized_get, _file_base_pywrapfile.FileAttr_finalized_set)
    def __init__(self, *args):
        _swig_setattr(self, FileAttr, 'this', _file_base_pywrapfile.new_FileAttr(*args))
        _swig_setattr(self, FileAttr, 'thisown', 1)
    def Clear(*args): return _file_base_pywrapfile.FileAttr_Clear(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileAttr):
        try:
            if self.thisown: destroy(self)
        except: pass

class FileAttrPtr(FileAttr):
    def __init__(self, this):
        _swig_setattr(self, FileAttr, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileAttr, 'thisown', 0)
        _swig_setattr(self, FileAttr,self.__class__,FileAttr)
_file_base_pywrapfile.FileAttr_swigregister(FileAttrPtr)

class FileAttributes(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileAttributes, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileAttributes, name)
    def __repr__(self):
        return "<C FileAttributes instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileAttributes, 'this', _file_base_pywrapfile.new_FileAttributes(*args))
        _swig_setattr(self, FileAttributes, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_FileAttributes):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Load(*args): return _file_base_pywrapfile.FileAttributes_Load(*args)
    def Store(*args): return _file_base_pywrapfile.FileAttributes_Store(*args)
    def LoadPrefix(*args): return _file_base_pywrapfile.FileAttributes_LoadPrefix(*args)
    def Delete(*args): return _file_base_pywrapfile.FileAttributes_Delete(*args)
    def DeleteWithOp(*args): return _file_base_pywrapfile.FileAttributes_DeleteWithOp(*args)
    def BulkDelete(*args): return _file_base_pywrapfile.FileAttributes_BulkDelete(*args)
    def BulkDeleteWithOp(*args): return _file_base_pywrapfile.FileAttributes_BulkDeleteWithOp(*args)
    __swig_getmethods__["GetAttributeFileName"] = lambda x: _file_base_pywrapfile.FileAttributes_GetAttributeFileName
    if _newclass:GetAttributeFileName = staticmethod(_file_base_pywrapfile.FileAttributes_GetAttributeFileName)
    def CreateVersion(*args): return _file_base_pywrapfile.FileAttributes_CreateVersion(*args)
    def ClearCache(*args): return _file_base_pywrapfile.FileAttributes_ClearCache(*args)
    def Finalize(*args): return _file_base_pywrapfile.FileAttributes_Finalize(*args)

class FileAttributesPtr(FileAttributes):
    def __init__(self, this):
        _swig_setattr(self, FileAttributes, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileAttributes, 'thisown', 0)
        _swig_setattr(self, FileAttributes,self.__class__,FileAttributes)
_file_base_pywrapfile.FileAttributes_swigregister(FileAttributesPtr)

FileAttributes_GetAttributeFileName = _file_base_pywrapfile.FileAttributes_GetAttributeFileName

class RecordIO(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordIO, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordIO, name)
    def __repr__(self):
        return "<C RecordIO instance at %s>" % (self.this,)
    kRecSize = _file_base_pywrapfile.RecordIO_kRecSize
    kHeaderSize = _file_base_pywrapfile.RecordIO_kHeaderSize
    kPhysicalRecSize = _file_base_pywrapfile.RecordIO_kPhysicalRecSize
    kLegacySyncMarker = _file_base_pywrapfile.RecordIO_kLegacySyncMarker
    kMaxRecordSize = _file_base_pywrapfile.RecordIO_kMaxRecordSize
    SINGLETON = _file_base_pywrapfile.RecordIO_SINGLETON
    FIXED_SIZE = _file_base_pywrapfile.RecordIO_FIXED_SIZE
    VARIABLE_SIZE = _file_base_pywrapfile.RecordIO_VARIABLE_SIZE
    OTHER_TAG = _file_base_pywrapfile.RecordIO_OTHER_TAG
    ZLIB_TAG = _file_base_pywrapfile.RecordIO_ZLIB_TAG
    CWZ_TAG = _file_base_pywrapfile.RecordIO_CWZ_TAG
    CW_TAG = _file_base_pywrapfile.RecordIO_CW_TAG
    ZIPPY_TAG = _file_base_pywrapfile.RecordIO_ZIPPY_TAG
    MIN_TAG = _file_base_pywrapfile.RecordIO_MIN_TAG
    MAX_TAG = _file_base_pywrapfile.RecordIO_MAX_TAG
    NUM_TAGS = _file_base_pywrapfile.RecordIO_NUM_TAGS
    def __init__(self, *args):
        _swig_setattr(self, RecordIO, 'this', _file_base_pywrapfile.new_RecordIO(*args))
        _swig_setattr(self, RecordIO, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordIO):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordIOPtr(RecordIO):
    def __init__(self, this):
        _swig_setattr(self, RecordIO, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordIO, 'thisown', 0)
        _swig_setattr(self, RecordIO,self.__class__,RecordIO)
_file_base_pywrapfile.RecordIO_swigregister(RecordIOPtr)

class RecordWriter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordWriter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordWriter, name)
    def __repr__(self):
        return "<C RecordWriter instance at %s>" % (self.this,)
    kDefaultBufferSize = _file_base_pywrapfile.RecordWriter_kDefaultBufferSize
    SINGLE_WRITER = _file_base_pywrapfile.RecordWriter_SINGLE_WRITER
    CONCURRENT_APPENDERS = _file_base_pywrapfile.RecordWriter_CONCURRENT_APPENDERS
    AUTO = _file_base_pywrapfile.RecordWriter_AUTO
    def __init__(self, *args):
        _swig_setattr(self, RecordWriter, 'this', _file_base_pywrapfile.new_RecordWriter(*args))
        _swig_setattr(self, RecordWriter, 'thisown', 1)
    __swig_getmethods__["Open"] = lambda x: _file_base_pywrapfile.RecordWriter_Open
    if _newclass:Open = staticmethod(_file_base_pywrapfile.RecordWriter_Open)
    __swig_getmethods__["OpenOrDie"] = lambda x: _file_base_pywrapfile.RecordWriter_OpenOrDie
    if _newclass:OpenOrDie = staticmethod(_file_base_pywrapfile.RecordWriter_OpenOrDie)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordWriter):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetVerifier(*args): return _file_base_pywrapfile.RecordWriter_SetVerifier(*args)
    def Close(*args): return _file_base_pywrapfile.RecordWriter_Close(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywrapfile.RecordWriter_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywrapfile.RecordWriter_owns_file(*args)
    def NoSyncOnClose(*args): return _file_base_pywrapfile.RecordWriter_NoSyncOnClose(*args)
    def EnableCompression(*args): return _file_base_pywrapfile.RecordWriter_EnableCompression(*args)
    def EnableZippyCompression(*args): return _file_base_pywrapfile.RecordWriter_EnableZippyCompression(*args)
    def EnableCWCompression(*args): return _file_base_pywrapfile.RecordWriter_EnableCWCompression(*args)
    def DisableCompression(*args): return _file_base_pywrapfile.RecordWriter_DisableCompression(*args)
    WRITE_ERROR = _file_base_pywrapfile.RecordWriter_WRITE_ERROR
    WRITE_OK = _file_base_pywrapfile.RecordWriter_WRITE_OK
    WRITE_RETRY = _file_base_pywrapfile.RecordWriter_WRITE_RETRY
    def WriteRecord(*args): return _file_base_pywrapfile.RecordWriter_WriteRecord(*args)
    def TryWriteRecord(*args): return _file_base_pywrapfile.RecordWriter_TryWriteRecord(*args)
    def WriteProtocolMessage(*args): return _file_base_pywrapfile.RecordWriter_WriteProtocolMessage(*args)
    def TryWriteProtocolMessage(*args): return _file_base_pywrapfile.RecordWriter_TryWriteProtocolMessage(*args)
    def Flush(*args): return _file_base_pywrapfile.RecordWriter_Flush(*args)
    def Sync(*args): return _file_base_pywrapfile.RecordWriter_Sync(*args)
    def DataSync(*args): return _file_base_pywrapfile.RecordWriter_DataSync(*args)
    def Tell(*args): return _file_base_pywrapfile.RecordWriter_Tell(*args)
    def ApproximateTell(*args): return _file_base_pywrapfile.RecordWriter_ApproximateTell(*args)
    def GetCurrentErrorMessage(*args): return _file_base_pywrapfile.RecordWriter_GetCurrentErrorMessage(*args)
    def GetCurrentErrorCode(*args): return _file_base_pywrapfile.RecordWriter_GetCurrentErrorCode(*args)
    def Checkpoint(*args): return _file_base_pywrapfile.RecordWriter_Checkpoint(*args)
    def GetFileName(*args): return _file_base_pywrapfile.RecordWriter_GetFileName(*args)
    def max_record_size(*args): return _file_base_pywrapfile.RecordWriter_max_record_size(*args)
    def SetMaxFileLength(*args): return _file_base_pywrapfile.RecordWriter_SetMaxFileLength(*args)
    def AsyncEnabled(*args): return _file_base_pywrapfile.RecordWriter_AsyncEnabled(*args)
    def FormatHeader(*args): return _file_base_pywrapfile.RecordWriter_FormatHeader(*args)
    def VerifyRecord(*args): return _file_base_pywrapfile.RecordWriter_VerifyRecord(*args)
    def WriteRecordString(*args): return _file_base_pywrapfile.RecordWriter_WriteRecordString(*args)

class RecordWriterPtr(RecordWriter):
    def __init__(self, this):
        _swig_setattr(self, RecordWriter, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordWriter, 'thisown', 0)
        _swig_setattr(self, RecordWriter,self.__class__,RecordWriter)
_file_base_pywrapfile.RecordWriter_swigregister(RecordWriterPtr)

RecordWriter_Open = _file_base_pywrapfile.RecordWriter_Open

RecordWriter_OpenOrDie = _file_base_pywrapfile.RecordWriter_OpenOrDie

class RecordReader(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReader, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReader, name)
    def __repr__(self):
        return "<C RecordReader instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReader, 'this', _file_base_pywrapfile.new_RecordReader(*args))
        _swig_setattr(self, RecordReader, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordReader):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Close(*args): return _file_base_pywrapfile.RecordReader_Close(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywrapfile.RecordReader_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywrapfile.RecordReader_owns_file(*args)
    def AsyncReadEnabled(*args): return _file_base_pywrapfile.RecordReader_AsyncReadEnabled(*args)
    READ_OK = _file_base_pywrapfile.RecordReader_READ_OK
    READ_DONE = _file_base_pywrapfile.RecordReader_READ_DONE
    READ_RETRY = _file_base_pywrapfile.RecordReader_READ_RETRY
    def Tell(*args): return _file_base_pywrapfile.RecordReader_Tell(*args)
    def PhysicalTell(*args): return _file_base_pywrapfile.RecordReader_PhysicalTell(*args)
    def FileTell(*args): return _file_base_pywrapfile.RecordReader_FileTell(*args)
    def LastRecordPosition(*args): return _file_base_pywrapfile.RecordReader_LastRecordPosition(*args)
    def Size(*args): return _file_base_pywrapfile.RecordReader_Size(*args)
    def AtEOF(*args): return _file_base_pywrapfile.RecordReader_AtEOF(*args)
    def Seek(*args): return _file_base_pywrapfile.RecordReader_Seek(*args)
    def FileSeek(*args): return _file_base_pywrapfile.RecordReader_FileSeek(*args)
    def GetPosition(*args): return _file_base_pywrapfile.RecordReader_GetPosition(*args)
    def SetPosition(*args): return _file_base_pywrapfile.RecordReader_SetPosition(*args)
    def Prefetch(*args): return _file_base_pywrapfile.RecordReader_Prefetch(*args)
    def Unfetch(*args): return _file_base_pywrapfile.RecordReader_Unfetch(*args)
    def GetFileName(*args): return _file_base_pywrapfile.RecordReader_GetFileName(*args)
    def Stat(*args): return _file_base_pywrapfile.RecordReader_Stat(*args)
    def set_log_skips(*args): return _file_base_pywrapfile.RecordReader_set_log_skips(*args)
    def skipped_bytes(*args): return _file_base_pywrapfile.RecordReader_skipped_bytes(*args)
    def skipped_regions(*args): return _file_base_pywrapfile.RecordReader_skipped_regions(*args)
    def read_error(*args): return _file_base_pywrapfile.RecordReader_read_error(*args)
    def clear_read_error(*args): return _file_base_pywrapfile.RecordReader_clear_read_error(*args)
    def set_max_record_length(*args): return _file_base_pywrapfile.RecordReader_set_max_record_length(*args)
    def set_max_decoded_record_length(*args): return _file_base_pywrapfile.RecordReader_set_max_decoded_record_length(*args)
    kDefaultMaxExpectedRecordLength = _file_base_pywrapfile.RecordReader_kDefaultMaxExpectedRecordLength
    def set_max_expected_record_length(*args): return _file_base_pywrapfile.RecordReader_set_max_expected_record_length(*args)
    def set_die_on_error(*args): return _file_base_pywrapfile.RecordReader_set_die_on_error(*args)

class RecordReaderPtr(RecordReader):
    def __init__(self, this):
        _swig_setattr(self, RecordReader, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReader, 'thisown', 0)
        _swig_setattr(self, RecordReader,self.__class__,RecordReader)
_file_base_pywrapfile.RecordReader_swigregister(RecordReaderPtr)

class RecordReaderOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReaderOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReaderOptions, name)
    def __repr__(self):
        return "<C RecordReaderOptions instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReaderOptions, 'this', _file_base_pywrapfile.new_RecordReaderOptions(*args))
        _swig_setattr(self, RecordReaderOptions, 'thisown', 1)
    def set_memory_budget(*args): return _file_base_pywrapfile.RecordReaderOptions_set_memory_budget(*args)
    def memory_budget(*args): return _file_base_pywrapfile.RecordReaderOptions_memory_budget(*args)
    def set_enable_aio(*args): return _file_base_pywrapfile.RecordReaderOptions_set_enable_aio(*args)
    def enable_aio(*args): return _file_base_pywrapfile.RecordReaderOptions_enable_aio(*args)
    def set_buffer_size(*args): return _file_base_pywrapfile.RecordReaderOptions_set_buffer_size(*args)
    def buffer_size(*args): return _file_base_pywrapfile.RecordReaderOptions_buffer_size(*args)
    def set_lookahead(*args): return _file_base_pywrapfile.RecordReaderOptions_set_lookahead(*args)
    def lookahead(*args): return _file_base_pywrapfile.RecordReaderOptions_lookahead(*args)
    def set_fixed_size(*args): return _file_base_pywrapfile.RecordReaderOptions_set_fixed_size(*args)
    def fixed_size(*args): return _file_base_pywrapfile.RecordReaderOptions_fixed_size(*args)
    def set_lookahead_on_open(*args): return _file_base_pywrapfile.RecordReaderOptions_set_lookahead_on_open(*args)
    def lookahead_on_open(*args): return _file_base_pywrapfile.RecordReaderOptions_lookahead_on_open(*args)
    def set_initial_seek_back(*args): return _file_base_pywrapfile.RecordReaderOptions_set_initial_seek_back(*args)
    def initial_seek_back(*args): return _file_base_pywrapfile.RecordReaderOptions_initial_seek_back(*args)
    def set_allow_unchecked_records(*args): return _file_base_pywrapfile.RecordReaderOptions_set_allow_unchecked_records(*args)
    def allow_unchecked_records(*args): return _file_base_pywrapfile.RecordReaderOptions_allow_unchecked_records(*args)
    def LoadOptionsFromString(*args): return _file_base_pywrapfile.RecordReaderOptions_LoadOptionsFromString(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordReaderOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordReaderOptionsPtr(RecordReaderOptions):
    def __init__(self, this):
        _swig_setattr(self, RecordReaderOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReaderOptions, 'thisown', 0)
        _swig_setattr(self, RecordReaderOptions,self.__class__,RecordReaderOptions)
_file_base_pywrapfile.RecordReaderOptions_swigregister(RecordReaderOptionsPtr)

class RecordVerifier(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordVerifier, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordVerifier, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C RecordVerifier instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordVerifier):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Verify(*args): return _file_base_pywrapfile.RecordVerifier_Verify(*args)

class RecordVerifierPtr(RecordVerifier):
    def __init__(self, this):
        _swig_setattr(self, RecordVerifier, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordVerifier, 'thisown', 0)
        _swig_setattr(self, RecordVerifier,self.__class__,RecordVerifier)
_file_base_pywrapfile.RecordVerifier_swigregister(RecordVerifierPtr)

class RecordWriterOpener(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordWriterOpener, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordWriterOpener, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C RecordWriterOpener instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordWriterOpener):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordWriterOpenerPtr(RecordWriterOpener):
    def __init__(self, this):
        _swig_setattr(self, RecordWriterOpener, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordWriterOpener, 'thisown', 0)
        _swig_setattr(self, RecordWriterOpener,self.__class__,RecordWriterOpener)
_file_base_pywrapfile.RecordWriterOpener_swigregister(RecordWriterOpenerPtr)

class RecordReaderScript(RecordReader):
    __swig_setmethods__ = {}
    for _s in [RecordReader]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReaderScript, name, value)
    __swig_getmethods__ = {}
    for _s in [RecordReader]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReaderScript, name)
    def __repr__(self):
        return "<C RecordReaderScript instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReaderScript, 'this', _file_base_pywrapfile.new_RecordReaderScript(*args))
        _swig_setattr(self, RecordReaderScript, 'thisown', 1)
    def ReadRecordIntoString(*args): return _file_base_pywrapfile.RecordReaderScript_ReadRecordIntoString(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_RecordReaderScript):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordReaderScriptPtr(RecordReaderScript):
    def __init__(self, this):
        _swig_setattr(self, RecordReaderScript, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReaderScript, 'thisown', 0)
        _swig_setattr(self, RecordReaderScript,self.__class__,RecordReaderScript)
_file_base_pywrapfile.RecordReaderScript_swigregister(RecordReaderScriptPtr)

class LogBase(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, LogBase, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, LogBase, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C LogBase instance at %s>" % (self.this,)
    def base_file(*args): return _file_base_pywrapfile.LogBase_base_file(*args)
    def base_name(*args): return _file_base_pywrapfile.LogBase_base_name(*args)
    def FileBase(*args): return _file_base_pywrapfile.LogBase_FileBase(*args)
    def FileName(*args): return _file_base_pywrapfile.LogBase_FileName(*args)
    __swig_getmethods__["MakeLogPosition"] = lambda x: _file_base_pywrapfile.LogBase_MakeLogPosition
    if _newclass:MakeLogPosition = staticmethod(_file_base_pywrapfile.LogBase_MakeLogPosition)
    __swig_getmethods__["LogPositionToFileNumber"] = lambda x: _file_base_pywrapfile.LogBase_LogPositionToFileNumber
    if _newclass:LogPositionToFileNumber = staticmethod(_file_base_pywrapfile.LogBase_LogPositionToFileNumber)
    __swig_getmethods__["LogPositionToOffset"] = lambda x: _file_base_pywrapfile.LogBase_LogPositionToOffset
    if _newclass:LogPositionToOffset = staticmethod(_file_base_pywrapfile.LogBase_LogPositionToOffset)
    __swig_getmethods__["LogFileNameToFileNumber"] = lambda x: _file_base_pywrapfile.LogBase_LogFileNameToFileNumber
    if _newclass:LogFileNameToFileNumber = staticmethod(_file_base_pywrapfile.LogBase_LogFileNameToFileNumber)
    __swig_getmethods__["GetLogChunkSize"] = lambda x: _file_base_pywrapfile.LogBase_GetLogChunkSize
    if _newclass:GetLogChunkSize = staticmethod(_file_base_pywrapfile.LogBase_GetLogChunkSize)

class LogBasePtr(LogBase):
    def __init__(self, this):
        _swig_setattr(self, LogBase, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, LogBase, 'thisown', 0)
        _swig_setattr(self, LogBase,self.__class__,LogBase)
_file_base_pywrapfile.LogBase_swigregister(LogBasePtr)
kDefaultBufferSize = cvar.kDefaultBufferSize
kMaxLogReaderPosLen = cvar.kMaxLogReaderPosLen

LogBase_MakeLogPosition = _file_base_pywrapfile.LogBase_MakeLogPosition

LogBase_LogPositionToFileNumber = _file_base_pywrapfile.LogBase_LogPositionToFileNumber

LogBase_LogPositionToOffset = _file_base_pywrapfile.LogBase_LogPositionToOffset

LogBase_LogFileNameToFileNumber = _file_base_pywrapfile.LogBase_LogFileNameToFileNumber

LogBase_GetLogChunkSize = _file_base_pywrapfile.LogBase_GetLogChunkSize

class LogReader(LogBase):
    __swig_setmethods__ = {}
    for _s in [LogBase]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, LogReader, name, value)
    __swig_getmethods__ = {}
    for _s in [LogBase]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, LogReader, name)
    def __repr__(self):
        return "<C LogReader instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, LogReader, 'this', _file_base_pywrapfile.new_LogReader(*args))
        _swig_setattr(self, LogReader, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_LogReader):
        try:
            if self.thisown: destroy(self)
        except: pass
    def EOFPosition(*args): return _file_base_pywrapfile.LogReader_EOFPosition(*args)
    def GetPosition(*args): return _file_base_pywrapfile.LogReader_GetPosition(*args)
    def SetInitialPosition(*args): return _file_base_pywrapfile.LogReader_SetInitialPosition(*args)
    def GetEOFPosition(*args): return _file_base_pywrapfile.LogReader_GetEOFPosition(*args)
    def UnreadBytes(*args): return _file_base_pywrapfile.LogReader_UnreadBytes(*args)
    def ReadRecordIfAvailable(*args): return _file_base_pywrapfile.LogReader_ReadRecordIfAvailable(*args)
    def ReadProtocolMessageIfAvailable(*args): return _file_base_pywrapfile.LogReader_ReadProtocolMessageIfAvailable(*args)
    def ReadRecordAsStringIfAvailable(*args): return _file_base_pywrapfile.LogReader_ReadRecordAsStringIfAvailable(*args)
    def AsyncReadEnabled(*args): return _file_base_pywrapfile.LogReader_AsyncReadEnabled(*args)
    def Tell(*args): return _file_base_pywrapfile.LogReader_Tell(*args)
    def LastRecordPosition(*args): return _file_base_pywrapfile.LogReader_LastRecordPosition(*args)
    def Seek(*args): return _file_base_pywrapfile.LogReader_Seek(*args)
    def LogPositionAdd(*args): return _file_base_pywrapfile.LogReader_LogPositionAdd(*args)
    __swig_getmethods__["GarbageCollect"] = lambda x: _file_base_pywrapfile.LogReader_GarbageCollect
    if _newclass:GarbageCollect = staticmethod(_file_base_pywrapfile.LogReader_GarbageCollect)
    __swig_getmethods__["GarbageCollect"] = lambda x: _file_base_pywrapfile.LogReader_GarbageCollect
    if _newclass:GarbageCollect = staticmethod(_file_base_pywrapfile.LogReader_GarbageCollect)
    def NumBytesSkipped(*args): return _file_base_pywrapfile.LogReader_NumBytesSkipped(*args)
    def ExportNumBytesSkipped(*args): return _file_base_pywrapfile.LogReader_ExportNumBytesSkipped(*args)

class LogReaderPtr(LogReader):
    def __init__(self, this):
        _swig_setattr(self, LogReader, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, LogReader, 'thisown', 0)
        _swig_setattr(self, LogReader,self.__class__,LogReader)
_file_base_pywrapfile.LogReader_swigregister(LogReaderPtr)

LogReader_GarbageCollect = _file_base_pywrapfile.LogReader_GarbageCollect

class BackgroundLogReader(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, BackgroundLogReader, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, BackgroundLogReader, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C BackgroundLogReader instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywrapfile.delete_BackgroundLogReader):
        try:
            if self.thisown: destroy(self)
        except: pass
    def MakeExit(*args): return _file_base_pywrapfile.BackgroundLogReader_MakeExit(*args)
    def ProcessRecord(*args): return _file_base_pywrapfile.BackgroundLogReader_ProcessRecord(*args)
    def log_reader(*args): return _file_base_pywrapfile.BackgroundLogReader_log_reader(*args)
    __swig_setmethods__["log_reader_"] = _file_base_pywrapfile.BackgroundLogReader_log_reader__set
    __swig_getmethods__["log_reader_"] = _file_base_pywrapfile.BackgroundLogReader_log_reader__get
    if _newclass:log_reader_ = property(_file_base_pywrapfile.BackgroundLogReader_log_reader__get, _file_base_pywrapfile.BackgroundLogReader_log_reader__set)

class BackgroundLogReaderPtr(BackgroundLogReader):
    def __init__(self, this):
        _swig_setattr(self, BackgroundLogReader, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, BackgroundLogReader, 'thisown', 0)
        _swig_setattr(self, BackgroundLogReader,self.__class__,BackgroundLogReader)
_file_base_pywrapfile.BackgroundLogReader_swigregister(BackgroundLogReaderPtr)

class LogWriter(LogBase):
    __swig_setmethods__ = {}
    for _s in [LogBase]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, LogWriter, name, value)
    __swig_getmethods__ = {}
    for _s in [LogBase]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, LogWriter, name)
    def __repr__(self):
        return "<C LogWriter instance at %s>" % (self.this,)
    kDefaultBufferSize = _file_base_pywrapfile.LogWriter_kDefaultBufferSize
    SINGLE_WRITER = _file_base_pywrapfile.LogWriter_SINGLE_WRITER
    CONCURRENT_APPENDERS = _file_base_pywrapfile.LogWriter_CONCURRENT_APPENDERS
    AUTO = _file_base_pywrapfile.LogWriter_AUTO
    WRITE_OK = _file_base_pywrapfile.LogWriter_WRITE_OK
    WRITE_ERROR = _file_base_pywrapfile.LogWriter_WRITE_ERROR
    WRITE_RETRY = _file_base_pywrapfile.LogWriter_WRITE_RETRY
    def __init__(self, *args):
        _swig_setattr(self, LogWriter, 'this', _file_base_pywrapfile.new_LogWriter(*args))
        _swig_setattr(self, LogWriter, 'thisown', 1)
    def Open(*args): return _file_base_pywrapfile.LogWriter_Open(*args)
    def __del__(self, destroy=_file_base_pywrapfile.delete_LogWriter):
        try:
            if self.thisown: destroy(self)
        except: pass
    def WriteRecord(*args): return _file_base_pywrapfile.LogWriter_WriteRecord(*args)
    def WriteProtocolMessage(*args): return _file_base_pywrapfile.LogWriter_WriteProtocolMessage(*args)
    def TryWriteRecord(*args): return _file_base_pywrapfile.LogWriter_TryWriteRecord(*args)
    def TryWriteProtocolMessage(*args): return _file_base_pywrapfile.LogWriter_TryWriteProtocolMessage(*args)
    def AsyncEnabled(*args): return _file_base_pywrapfile.LogWriter_AsyncEnabled(*args)
    def Flush(*args): return _file_base_pywrapfile.LogWriter_Flush(*args)
    def Close(*args): return _file_base_pywrapfile.LogWriter_Close(*args)
    def EnableCompression(*args): return _file_base_pywrapfile.LogWriter_EnableCompression(*args)
    def EnableCWCompression(*args): return _file_base_pywrapfile.LogWriter_EnableCWCompression(*args)
    def DisableCompression(*args): return _file_base_pywrapfile.LogWriter_DisableCompression(*args)
    def ApproximateTell(*args): return _file_base_pywrapfile.LogWriter_ApproximateTell(*args)
    def ApproximateEOFPosition(*args): return _file_base_pywrapfile.LogWriter_ApproximateEOFPosition(*args)
    def GetPosition(*args): return _file_base_pywrapfile.LogWriter_GetPosition(*args)
    def EOFPosition(*args): return _file_base_pywrapfile.LogWriter_EOFPosition(*args)
    def max_record_size(*args): return _file_base_pywrapfile.LogWriter_max_record_size(*args)
    __swig_getmethods__["GetInitialPosition"] = lambda x: _file_base_pywrapfile.LogWriter_GetInitialPosition
    if _newclass:GetInitialPosition = staticmethod(_file_base_pywrapfile.LogWriter_GetInitialPosition)
    __swig_getmethods__["TruncateLog"] = lambda x: _file_base_pywrapfile.LogWriter_TruncateLog
    if _newclass:TruncateLog = staticmethod(_file_base_pywrapfile.LogWriter_TruncateLog)
    __swig_getmethods__["setLogChunkSize_TEST"] = lambda x: _file_base_pywrapfile.LogWriter_setLogChunkSize_TEST
    if _newclass:setLogChunkSize_TEST = staticmethod(_file_base_pywrapfile.LogWriter_setLogChunkSize_TEST)
    def WriteRecordString(*args): return _file_base_pywrapfile.LogWriter_WriteRecordString(*args)

class LogWriterPtr(LogWriter):
    def __init__(self, this):
        _swig_setattr(self, LogWriter, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, LogWriter, 'thisown', 0)
        _swig_setattr(self, LogWriter,self.__class__,LogWriter)
_file_base_pywrapfile.LogWriter_swigregister(LogWriterPtr)

LogWriter_GetInitialPosition = _file_base_pywrapfile.LogWriter_GetInitialPosition

LogWriter_TruncateLog = _file_base_pywrapfile.LogWriter_TruncateLog

LogWriter_setLogChunkSize_TEST = _file_base_pywrapfile.LogWriter_setLogChunkSize_TEST

class LogReaderScript(LogReader):
    __swig_setmethods__ = {}
    for _s in [LogReader]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, LogReaderScript, name, value)
    __swig_getmethods__ = {}
    for _s in [LogReader]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, LogReaderScript, name)
    def __repr__(self):
        return "<C LogReaderScript instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, LogReaderScript, 'this', _file_base_pywrapfile.new_LogReaderScript(*args))
        _swig_setattr(self, LogReaderScript, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywrapfile.delete_LogReaderScript):
        try:
            if self.thisown: destroy(self)
        except: pass
    def ReadRecordIntoString(*args): return _file_base_pywrapfile.LogReaderScript_ReadRecordIntoString(*args)

class LogReaderScriptPtr(LogReaderScript):
    def __init__(self, this):
        _swig_setattr(self, LogReaderScript, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, LogReaderScript, 'thisown', 0)
        _swig_setattr(self, LogReaderScript,self.__class__,LogReaderScript)
_file_base_pywrapfile.LogReaderScript_swigregister(LogReaderScriptPtr)



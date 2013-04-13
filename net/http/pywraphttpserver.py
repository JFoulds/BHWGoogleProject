# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _net_http_pywraphttpserver

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
        _swig_setattr(self, stringVector, 'this', _net_http_pywraphttpserver.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_net_http_pywraphttpserver.stringVector_swigregister(stringVectorPtr)

class IOBuffer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, IOBuffer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, IOBuffer, name)
    def __repr__(self):
        return "<C IOBuffer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, IOBuffer, 'this', _net_http_pywraphttpserver.new_IOBuffer(*args))
        _swig_setattr(self, IOBuffer, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_IOBuffer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Swap(*args): return _net_http_pywraphttpserver.IOBuffer_Swap(*args)
    def AppendIOBuffer(*args): return _net_http_pywraphttpserver.IOBuffer_AppendIOBuffer(*args)
    def AppendIOBufferNonDestructive(*args): return _net_http_pywraphttpserver.IOBuffer_AppendIOBufferNonDestructive(*args)
    def AppendIOBufferN(*args): return _net_http_pywraphttpserver.IOBuffer_AppendIOBufferN(*args)
    def AppendIOBufferNonDestructiveN(*args): return _net_http_pywraphttpserver.IOBuffer_AppendIOBufferNonDestructiveN(*args)
    def AppendRawBlock(*args): return _net_http_pywraphttpserver.IOBuffer_AppendRawBlock(*args)
    def Write(*args): return _net_http_pywraphttpserver.IOBuffer_Write(*args)
    def WriteUntil(*args): return _net_http_pywraphttpserver.IOBuffer_WriteUntil(*args)
    def WriteString(*args): return _net_http_pywraphttpserver.IOBuffer_WriteString(*args)
    def WriteInt(*args): return _net_http_pywraphttpserver.IOBuffer_WriteInt(*args)
    def WriteInt64(*args): return _net_http_pywraphttpserver.IOBuffer_WriteInt64(*args)
    def WriteFloat(*args): return _net_http_pywraphttpserver.IOBuffer_WriteFloat(*args)
    def WriteDouble(*args): return _net_http_pywraphttpserver.IOBuffer_WriteDouble(*args)
    def WriteShort(*args): return _net_http_pywraphttpserver.IOBuffer_WriteShort(*args)
    def WriteVarint32(*args): return _net_http_pywraphttpserver.IOBuffer_WriteVarint32(*args)
    def WriteVarint64(*args): return _net_http_pywraphttpserver.IOBuffer_WriteVarint64(*args)
    def Prepend(*args): return _net_http_pywraphttpserver.IOBuffer_Prepend(*args)
    def PrependUntil(*args): return _net_http_pywraphttpserver.IOBuffer_PrependUntil(*args)
    def PrependString(*args): return _net_http_pywraphttpserver.IOBuffer_PrependString(*args)
    def GrowPrependRegion(*args): return _net_http_pywraphttpserver.IOBuffer_GrowPrependRegion(*args)
    def ReadToString(*args): return _net_http_pywraphttpserver.IOBuffer_ReadToString(*args)
    def ReadToStringN(*args): return _net_http_pywraphttpserver.IOBuffer_ReadToStringN(*args)
    def ReadVarint32(*args): return _net_http_pywraphttpserver.IOBuffer_ReadVarint32(*args)
    def ReadVarint64(*args): return _net_http_pywraphttpserver.IOBuffer_ReadVarint64(*args)
    def Unread(*args): return _net_http_pywraphttpserver.IOBuffer_Unread(*args)
    def Skip(*args): return _net_http_pywraphttpserver.IOBuffer_Skip(*args)
    def SetPin(*args): return _net_http_pywraphttpserver.IOBuffer_SetPin(*args)
    def ClearPin(*args): return _net_http_pywraphttpserver.IOBuffer_ClearPin(*args)
    def UnreadToPin(*args): return _net_http_pywraphttpserver.IOBuffer_UnreadToPin(*args)
    def is_pinned(*args): return _net_http_pywraphttpserver.IOBuffer_is_pinned(*args)
    def PrefixMatch(*args): return _net_http_pywraphttpserver.IOBuffer_PrefixMatch(*args)
    def SuffixMatch(*args): return _net_http_pywraphttpserver.IOBuffer_SuffixMatch(*args)
    def TruncateToLength(*args): return _net_http_pywraphttpserver.IOBuffer_TruncateToLength(*args)
    def WriteFD(*args): return _net_http_pywraphttpserver.IOBuffer_WriteFD(*args)
    def ReadFDOld(*args): return _net_http_pywraphttpserver.IOBuffer_ReadFDOld(*args)
    def ReadFD(*args): return _net_http_pywraphttpserver.IOBuffer_ReadFD(*args)
    def Length(*args): return _net_http_pywraphttpserver.IOBuffer_Length(*args)
    def LengthAtLeast(*args): return _net_http_pywraphttpserver.IOBuffer_LengthAtLeast(*args)
    def IsEmpty(*args): return _net_http_pywraphttpserver.IOBuffer_IsEmpty(*args)
    def Clear(*args): return _net_http_pywraphttpserver.IOBuffer_Clear(*args)
    def Index(*args): return _net_http_pywraphttpserver.IOBuffer_Index(*args)
    def IndexN(*args): return _net_http_pywraphttpserver.IOBuffer_IndexN(*args)
    def block_size(*args): return _net_http_pywraphttpserver.IOBuffer_block_size(*args)
    def prepend_size(*args): return _net_http_pywraphttpserver.IOBuffer_prepend_size(*args)
    def set_block_size(*args): return _net_http_pywraphttpserver.IOBuffer_set_block_size(*args)
    def set_max_readfd_length(*args): return _net_http_pywraphttpserver.IOBuffer_set_max_readfd_length(*args)
    def reset_max_readfd_length(*args): return _net_http_pywraphttpserver.IOBuffer_reset_max_readfd_length(*args)
    def GetMaxReadLength(*args): return _net_http_pywraphttpserver.IOBuffer_GetMaxReadLength(*args)
    def GetReadPosition(*args): return _net_http_pywraphttpserver.IOBuffer_GetReadPosition(*args)
    def SetReadPosition(*args): return _net_http_pywraphttpserver.IOBuffer_SetReadPosition(*args)
    def Buffer(*args): return _net_http_pywraphttpserver.IOBuffer_Buffer(*args)
    def CheckRep(*args): return _net_http_pywraphttpserver.IOBuffer_CheckRep(*args)
    def Prefetch(*args): return _net_http_pywraphttpserver.IOBuffer_Prefetch(*args)
    def Read(*args): return _net_http_pywraphttpserver.IOBuffer_Read(*args)
    def ReadAtMost(*args): return _net_http_pywraphttpserver.IOBuffer_ReadAtMost(*args)
    def ReadFast(*args): return _net_http_pywraphttpserver.IOBuffer_ReadFast(*args)
    def ReadUntil(*args): return _net_http_pywraphttpserver.IOBuffer_ReadUntil(*args)
    def ReadLine(*args): return _net_http_pywraphttpserver.IOBuffer_ReadLine(*args)

class IOBufferPtr(IOBuffer):
    def __init__(self, this):
        _swig_setattr(self, IOBuffer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, IOBuffer, 'thisown', 0)
        _swig_setattr(self, IOBuffer,self.__class__,IOBuffer)
_net_http_pywraphttpserver.IOBuffer_swigregister(IOBufferPtr)


Swap = _net_http_pywraphttpserver.Swap
class Executor(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Executor, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Executor, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C thread::Executor instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_Executor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Add(*args): return _net_http_pywraphttpserver.Executor_Add(*args)
    def TryAdd(*args): return _net_http_pywraphttpserver.Executor_TryAdd(*args)
    def AddIfReadyToRun(*args): return _net_http_pywraphttpserver.Executor_AddIfReadyToRun(*args)
    def AddAfter(*args): return _net_http_pywraphttpserver.Executor_AddAfter(*args)
    def num_pending_closures(*args): return _net_http_pywraphttpserver.Executor_num_pending_closures(*args)
    __swig_getmethods__["DefaultExecutor"] = lambda x: _net_http_pywraphttpserver.Executor_DefaultExecutor
    if _newclass:DefaultExecutor = staticmethod(_net_http_pywraphttpserver.Executor_DefaultExecutor)
    __swig_getmethods__["SetDefaultExecutor"] = lambda x: _net_http_pywraphttpserver.Executor_SetDefaultExecutor
    if _newclass:SetDefaultExecutor = staticmethod(_net_http_pywraphttpserver.Executor_SetDefaultExecutor)
    __swig_getmethods__["CurrentExecutor"] = lambda x: _net_http_pywraphttpserver.Executor_CurrentExecutor
    if _newclass:CurrentExecutor = staticmethod(_net_http_pywraphttpserver.Executor_CurrentExecutor)
    __swig_getmethods__["CurrentExecutorPointerInternal"] = lambda x: _net_http_pywraphttpserver.Executor_CurrentExecutorPointerInternal
    if _newclass:CurrentExecutorPointerInternal = staticmethod(_net_http_pywraphttpserver.Executor_CurrentExecutorPointerInternal)

class ExecutorPtr(Executor):
    def __init__(self, this):
        _swig_setattr(self, Executor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Executor, 'thisown', 0)
        _swig_setattr(self, Executor,self.__class__,Executor)
_net_http_pywraphttpserver.Executor_swigregister(ExecutorPtr)

Executor_DefaultExecutor = _net_http_pywraphttpserver.Executor_DefaultExecutor

Executor_SetDefaultExecutor = _net_http_pywraphttpserver.Executor_SetDefaultExecutor

Executor_CurrentExecutor = _net_http_pywraphttpserver.Executor_CurrentExecutor

Executor_CurrentExecutorPointerInternal = _net_http_pywraphttpserver.Executor_CurrentExecutorPointerInternal


NewInlineExecutor = _net_http_pywraphttpserver.NewInlineExecutor

SingletonInlineExecutor = _net_http_pywraphttpserver.SingletonInlineExecutor

NewSynchronizedInlineExecutor = _net_http_pywraphttpserver.NewSynchronizedInlineExecutor
class AbstractThreadPool(Executor):
    __swig_setmethods__ = {}
    for _s in [Executor]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, AbstractThreadPool, name, value)
    __swig_getmethods__ = {}
    for _s in [Executor]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, AbstractThreadPool, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C AbstractThreadPool instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_AbstractThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _net_http_pywraphttpserver.AbstractThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _net_http_pywraphttpserver.AbstractThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _net_http_pywraphttpserver.AbstractThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _net_http_pywraphttpserver.AbstractThreadPool_SetThreadNamePrefix(*args)
    def StartWorkers(*args): return _net_http_pywraphttpserver.AbstractThreadPool_StartWorkers(*args)
    def num_pending_closures(*args): return _net_http_pywraphttpserver.AbstractThreadPool_num_pending_closures(*args)
    def SetWatchdogTimeout(*args): return _net_http_pywraphttpserver.AbstractThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _net_http_pywraphttpserver.AbstractThreadPool_watchdog_timeout(*args)
    def thread_options(*args): return _net_http_pywraphttpserver.AbstractThreadPool_thread_options(*args)
    def queue_count(*args): return _net_http_pywraphttpserver.AbstractThreadPool_queue_count(*args)
    def queue_capacity(*args): return _net_http_pywraphttpserver.AbstractThreadPool_queue_capacity(*args)

class AbstractThreadPoolPtr(AbstractThreadPool):
    def __init__(self, this):
        _swig_setattr(self, AbstractThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AbstractThreadPool, 'thisown', 0)
        _swig_setattr(self, AbstractThreadPool,self.__class__,AbstractThreadPool)
_net_http_pywraphttpserver.AbstractThreadPool_swigregister(AbstractThreadPoolPtr)

class ThreadPool(AbstractThreadPool):
    __swig_setmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ThreadPool, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ThreadPool, name)
    def __repr__(self):
        return "<C ThreadPool instance at %s>" % (self.this,)
    kDefaultStackBytes = _net_http_pywraphttpserver.ThreadPool_kDefaultStackBytes
    def __init__(self, *args):
        _swig_setattr(self, ThreadPool, 'this', _net_http_pywraphttpserver.new_ThreadPool(*args))
        _swig_setattr(self, ThreadPool, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_ThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _net_http_pywraphttpserver.ThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _net_http_pywraphttpserver.ThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _net_http_pywraphttpserver.ThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _net_http_pywraphttpserver.ThreadPool_SetThreadNamePrefix(*args)
    def SetWatchdogTimeout(*args): return _net_http_pywraphttpserver.ThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _net_http_pywraphttpserver.ThreadPool_watchdog_timeout(*args)
    def StartWorkers(*args): return _net_http_pywraphttpserver.ThreadPool_StartWorkers(*args)
    def thread_options(*args): return _net_http_pywraphttpserver.ThreadPool_thread_options(*args)
    def Add(*args): return _net_http_pywraphttpserver.ThreadPool_Add(*args)
    def AddAfter(*args): return _net_http_pywraphttpserver.ThreadPool_AddAfter(*args)
    def TryAdd(*args): return _net_http_pywraphttpserver.ThreadPool_TryAdd(*args)
    def AddIfReadyToRun(*args): return _net_http_pywraphttpserver.ThreadPool_AddIfReadyToRun(*args)
    def queue_count(*args): return _net_http_pywraphttpserver.ThreadPool_queue_count(*args)
    def queue_capacity(*args): return _net_http_pywraphttpserver.ThreadPool_queue_capacity(*args)
    def num_threads(*args): return _net_http_pywraphttpserver.ThreadPool_num_threads(*args)
    def thread(*args): return _net_http_pywraphttpserver.ThreadPool_thread(*args)

class ThreadPoolPtr(ThreadPool):
    def __init__(self, this):
        _swig_setattr(self, ThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ThreadPool, 'thisown', 0)
        _swig_setattr(self, ThreadPool,self.__class__,ThreadPool)
_net_http_pywraphttpserver.ThreadPool_swigregister(ThreadPoolPtr)

SSL_OTHER = _net_http_pywraphttpserver.SSL_OTHER
SSL_SECURITY_MIN = _net_http_pywraphttpserver.SSL_SECURITY_MIN
SSL_NONE = _net_http_pywraphttpserver.SSL_NONE
SSL_INTEGRITY = _net_http_pywraphttpserver.SSL_INTEGRITY
SSL_PRIVACY_AND_INTEGRITY = _net_http_pywraphttpserver.SSL_PRIVACY_AND_INTEGRITY
SSL_STRONG_PRIVACY_AND_INTEGRITY = _net_http_pywraphttpserver.SSL_STRONG_PRIVACY_AND_INTEGRITY
SSL_SECURITY_MAX = _net_http_pywraphttpserver.SSL_SECURITY_MAX

StringToSecurityLevel = _net_http_pywraphttpserver.StringToSecurityLevel
class Peer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Peer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Peer, name)
    def __repr__(self):
        return "<C Peer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, Peer, 'this', _net_http_pywraphttpserver.new_Peer(*args))
        _swig_setattr(self, Peer, 'thisown', 1)
    def primary_role(*args): return _net_http_pywraphttpserver.Peer_primary_role(*args)
    def set_primary_role(*args): return _net_http_pywraphttpserver.Peer_set_primary_role(*args)
    def username(*args): return _net_http_pywraphttpserver.Peer_username(*args)
    def requested_role(*args): return _net_http_pywraphttpserver.Peer_requested_role(*args)
    def set_requested_role(*args): return _net_http_pywraphttpserver.Peer_set_requested_role(*args)
    def host(*args): return _net_http_pywraphttpserver.Peer_host(*args)
    def set_host(*args): return _net_http_pywraphttpserver.Peer_set_host(*args)
    def security_level(*args): return _net_http_pywraphttpserver.Peer_security_level(*args)
    def set_security_level(*args): return _net_http_pywraphttpserver.Peer_set_security_level(*args)
    def protocol(*args): return _net_http_pywraphttpserver.Peer_protocol(*args)
    def set_protocol(*args): return _net_http_pywraphttpserver.Peer_set_protocol(*args)
    def borgcell(*args): return _net_http_pywraphttpserver.Peer_borgcell(*args)
    def set_borgcell(*args): return _net_http_pywraphttpserver.Peer_set_borgcell(*args)
    def jobname_chosen_by_user(*args): return _net_http_pywraphttpserver.Peer_jobname_chosen_by_user(*args)
    def set_jobname_chosen_by_user(*args): return _net_http_pywraphttpserver.Peer_set_jobname_chosen_by_user(*args)
    def IsBorgJob(*args): return _net_http_pywraphttpserver.Peer_IsBorgJob(*args)
    def SetBorgJob(*args): return _net_http_pywraphttpserver.Peer_SetBorgJob(*args)
    def HasRole(*args): return _net_http_pywraphttpserver.Peer_HasRole(*args)
    def roles(*args): return _net_http_pywraphttpserver.Peer_roles(*args)
    def mutable_roles(*args): return _net_http_pywraphttpserver.Peer_mutable_roles(*args)
    def Ref(*args): return _net_http_pywraphttpserver.Peer_Ref(*args)
    def Unref(*args): return _net_http_pywraphttpserver.Peer_Unref(*args)
    def CopyFrom(*args): return _net_http_pywraphttpserver.Peer_CopyFrom(*args)

class PeerPtr(Peer):
    def __init__(self, this):
        _swig_setattr(self, Peer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Peer, 'thisown', 0)
        _swig_setattr(self, Peer,self.__class__,Peer)
_net_http_pywraphttpserver.Peer_swigregister(PeerPtr)


NewDummyPeer = _net_http_pywraphttpserver.NewDummyPeer
NO_AUTHENTICATE_PEER = _net_http_pywraphttpserver.NO_AUTHENTICATE_PEER
AUTHENTICATE_PEER = _net_http_pywraphttpserver.AUTHENTICATE_PEER
OPTIONAL_AUTHENTICATE_PEER = _net_http_pywraphttpserver.OPTIONAL_AUTHENTICATE_PEER
class HTTPResponse(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPResponse, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPResponse, name)
    def __repr__(self):
        return "<C HTTPResponse instance at %s>" % (self.this,)
    RC_UNDEFINED = _net_http_pywraphttpserver.HTTPResponse_RC_UNDEFINED
    RC_FIRST_CODE = _net_http_pywraphttpserver.HTTPResponse_RC_FIRST_CODE
    RC_CONTINUE = _net_http_pywraphttpserver.HTTPResponse_RC_CONTINUE
    RC_SWITCHING = _net_http_pywraphttpserver.HTTPResponse_RC_SWITCHING
    RC_PROCESSING = _net_http_pywraphttpserver.HTTPResponse_RC_PROCESSING
    RC_REQUEST_OK = _net_http_pywraphttpserver.HTTPResponse_RC_REQUEST_OK
    RC_CREATED = _net_http_pywraphttpserver.HTTPResponse_RC_CREATED
    RC_ACCEPTED = _net_http_pywraphttpserver.HTTPResponse_RC_ACCEPTED
    RC_PROVISIONAL = _net_http_pywraphttpserver.HTTPResponse_RC_PROVISIONAL
    RC_NO_CONTENT = _net_http_pywraphttpserver.HTTPResponse_RC_NO_CONTENT
    RC_RESET_CONTENT = _net_http_pywraphttpserver.HTTPResponse_RC_RESET_CONTENT
    RC_PART_CONTENT = _net_http_pywraphttpserver.HTTPResponse_RC_PART_CONTENT
    RC_MULTI_STATUS = _net_http_pywraphttpserver.HTTPResponse_RC_MULTI_STATUS
    RC_RTSP_LOW_STORAGE = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_LOW_STORAGE
    RC_MULTIPLE = _net_http_pywraphttpserver.HTTPResponse_RC_MULTIPLE
    RC_MOVED_PERM = _net_http_pywraphttpserver.HTTPResponse_RC_MOVED_PERM
    RC_MOVED_TEMP = _net_http_pywraphttpserver.HTTPResponse_RC_MOVED_TEMP
    RC_SEE_OTHER = _net_http_pywraphttpserver.HTTPResponse_RC_SEE_OTHER
    RC_NOT_MODIFIED = _net_http_pywraphttpserver.HTTPResponse_RC_NOT_MODIFIED
    RC_USE_PROXY = _net_http_pywraphttpserver.HTTPResponse_RC_USE_PROXY
    RC_TEMP_REDIRECT = _net_http_pywraphttpserver.HTTPResponse_RC_TEMP_REDIRECT
    RC_BAD_REQUEST = _net_http_pywraphttpserver.HTTPResponse_RC_BAD_REQUEST
    RC_UNAUTHORIZED = _net_http_pywraphttpserver.HTTPResponse_RC_UNAUTHORIZED
    RC_PAYMENT = _net_http_pywraphttpserver.HTTPResponse_RC_PAYMENT
    RC_FORBIDDEN = _net_http_pywraphttpserver.HTTPResponse_RC_FORBIDDEN
    RC_NOT_FOUND = _net_http_pywraphttpserver.HTTPResponse_RC_NOT_FOUND
    RC_METHOD_NA = _net_http_pywraphttpserver.HTTPResponse_RC_METHOD_NA
    RC_NONE_ACC = _net_http_pywraphttpserver.HTTPResponse_RC_NONE_ACC
    RC_PROXY = _net_http_pywraphttpserver.HTTPResponse_RC_PROXY
    RC_REQUEST_TO = _net_http_pywraphttpserver.HTTPResponse_RC_REQUEST_TO
    RC_CONFLICT = _net_http_pywraphttpserver.HTTPResponse_RC_CONFLICT
    RC_GONE = _net_http_pywraphttpserver.HTTPResponse_RC_GONE
    RC_LEN_REQUIRED = _net_http_pywraphttpserver.HTTPResponse_RC_LEN_REQUIRED
    RC_PRECOND_FAILED = _net_http_pywraphttpserver.HTTPResponse_RC_PRECOND_FAILED
    RC_ENTITY_TOO_BIG = _net_http_pywraphttpserver.HTTPResponse_RC_ENTITY_TOO_BIG
    RC_URI_TOO_BIG = _net_http_pywraphttpserver.HTTPResponse_RC_URI_TOO_BIG
    RC_UNKNOWN_MEDIA = _net_http_pywraphttpserver.HTTPResponse_RC_UNKNOWN_MEDIA
    RC_BAD_RANGE = _net_http_pywraphttpserver.HTTPResponse_RC_BAD_RANGE
    RC_BAD_EXPECTATION = _net_http_pywraphttpserver.HTTPResponse_RC_BAD_EXPECTATION
    RC_UNPROC_ENTITY = _net_http_pywraphttpserver.HTTPResponse_RC_UNPROC_ENTITY
    RC_LOCKED = _net_http_pywraphttpserver.HTTPResponse_RC_LOCKED
    RC_FAILED_DEP = _net_http_pywraphttpserver.HTTPResponse_RC_FAILED_DEP
    RC_RTSP_INVALID_PARAM = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_INVALID_PARAM
    RC_RTSP_ILLEGAL_CONF = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_ILLEGAL_CONF
    RC_RTSP_INSUF_BANDWIDTH = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_INSUF_BANDWIDTH
    RC_RTSP_UNKNOWN_SESSION = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_UNKNOWN_SESSION
    RC_RTSP_BAD_METHOD = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_METHOD
    RC_RTSP_BAD_HEADER = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_HEADER
    RC_RTSP_INVALID_RANGE = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_INVALID_RANGE
    RC_RTSP_READONLY_PARAM = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_READONLY_PARAM
    RC_RTSP_BAD_AGGREGATE = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_AGGREGATE
    RC_RTSP_AGGREGATE_ONLY = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_AGGREGATE_ONLY
    RC_RTSP_BAD_TRANSPORT = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_TRANSPORT
    RC_RTSP_BAD_DESTINATION = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_DESTINATION
    RC_ERROR = _net_http_pywraphttpserver.HTTPResponse_RC_ERROR
    RC_NOT_IMP = _net_http_pywraphttpserver.HTTPResponse_RC_NOT_IMP
    RC_BAD_GATEWAY = _net_http_pywraphttpserver.HTTPResponse_RC_BAD_GATEWAY
    RC_SERVICE_UNAV = _net_http_pywraphttpserver.HTTPResponse_RC_SERVICE_UNAV
    RC_GATEWAY_TO = _net_http_pywraphttpserver.HTTPResponse_RC_GATEWAY_TO
    RC_BAD_VERSION = _net_http_pywraphttpserver.HTTPResponse_RC_BAD_VERSION
    RC_INSUF_STORAGE = _net_http_pywraphttpserver.HTTPResponse_RC_INSUF_STORAGE
    RC_RTSP_BAD_OPTION = _net_http_pywraphttpserver.HTTPResponse_RC_RTSP_BAD_OPTION
    RC_LAST_CODE = _net_http_pywraphttpserver.HTTPResponse_RC_LAST_CODE
    CC_NO_STORE = _net_http_pywraphttpserver.HTTPResponse_CC_NO_STORE
    CC_MUST_REVALIDATE = _net_http_pywraphttpserver.HTTPResponse_CC_MUST_REVALIDATE
    CC_PROXY_REVALIDATE = _net_http_pywraphttpserver.HTTPResponse_CC_PROXY_REVALIDATE
    CC_GZIP_EMPTY_OK = _net_http_pywraphttpserver.HTTPResponse_CC_GZIP_EMPTY_OK
    EXPIRES_OMIT = _net_http_pywraphttpserver.HTTPResponse_EXPIRES_OMIT
    EXPIRES_SHORTEN = _net_http_pywraphttpserver.HTTPResponse_EXPIRES_SHORTEN
    num_response_codes = _net_http_pywraphttpserver.cvar.HTTPResponse_num_response_codes
    num_cacheable_response_codes = _net_http_pywraphttpserver.cvar.HTTPResponse_num_cacheable_response_codes
    __swig_getmethods__["GetReasonPhrase"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_GetReasonPhrase
    if _newclass:GetReasonPhrase = staticmethod(_net_http_pywraphttpserver.HTTPResponse_GetReasonPhrase)
    __swig_getmethods__["AddStandardHeaders"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_AddStandardHeaders
    if _newclass:AddStandardHeaders = staticmethod(_net_http_pywraphttpserver.HTTPResponse_AddStandardHeaders)
    __swig_getmethods__["SetCacheablePublic"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_SetCacheablePublic
    if _newclass:SetCacheablePublic = staticmethod(_net_http_pywraphttpserver.HTTPResponse_SetCacheablePublic)
    __swig_getmethods__["SetCacheablePrivate"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivate
    if _newclass:SetCacheablePrivate = staticmethod(_net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivate)
    __swig_getmethods__["SetNotCacheable"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_SetNotCacheable
    if _newclass:SetNotCacheable = staticmethod(_net_http_pywraphttpserver.HTTPResponse_SetNotCacheable)
    __swig_getmethods__["SetCacheablePrivateIfNeeded"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivateIfNeeded
    if _newclass:SetCacheablePrivateIfNeeded = staticmethod(_net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivateIfNeeded)
    __swig_getmethods__["IsRedirectResponseCode"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_IsRedirectResponseCode
    if _newclass:IsRedirectResponseCode = staticmethod(_net_http_pywraphttpserver.HTTPResponse_IsRedirectResponseCode)
    __swig_getmethods__["IsCacheableResponseCode"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_IsCacheableResponseCode
    if _newclass:IsCacheableResponseCode = staticmethod(_net_http_pywraphttpserver.HTTPResponse_IsCacheableResponseCode)
    __swig_getmethods__["CreateErrorPage"] = lambda x: _net_http_pywraphttpserver.HTTPResponse_CreateErrorPage
    if _newclass:CreateErrorPage = staticmethod(_net_http_pywraphttpserver.HTTPResponse_CreateErrorPage)
    def __init__(self, *args):
        _swig_setattr(self, HTTPResponse, 'this', _net_http_pywraphttpserver.new_HTTPResponse(*args))
        _swig_setattr(self, HTTPResponse, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPResponse):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPResponsePtr(HTTPResponse):
    def __init__(self, this):
        _swig_setattr(self, HTTPResponse, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPResponse, 'thisown', 0)
        _swig_setattr(self, HTTPResponse,self.__class__,HTTPResponse)
_net_http_pywraphttpserver.HTTPResponse_swigregister(HTTPResponsePtr)
cvar = _net_http_pywraphttpserver.cvar

HTTPResponse_GetReasonPhrase = _net_http_pywraphttpserver.HTTPResponse_GetReasonPhrase

HTTPResponse_AddStandardHeaders = _net_http_pywraphttpserver.HTTPResponse_AddStandardHeaders

HTTPResponse_SetCacheablePublic = _net_http_pywraphttpserver.HTTPResponse_SetCacheablePublic

HTTPResponse_SetCacheablePrivate = _net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivate

HTTPResponse_SetNotCacheable = _net_http_pywraphttpserver.HTTPResponse_SetNotCacheable

HTTPResponse_SetCacheablePrivateIfNeeded = _net_http_pywraphttpserver.HTTPResponse_SetCacheablePrivateIfNeeded

HTTPResponse_IsRedirectResponseCode = _net_http_pywraphttpserver.HTTPResponse_IsRedirectResponseCode

HTTPResponse_IsCacheableResponseCode = _net_http_pywraphttpserver.HTTPResponse_IsCacheableResponseCode

HTTPResponse_CreateErrorPage = _net_http_pywraphttpserver.HTTPResponse_CreateErrorPage

class HTTPHeaders(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPHeaders, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPHeaders, name)
    def __repr__(self):
        return "<C HTTPHeaders instance at %s>" % (self.this,)
    ACCEPT = _net_http_pywraphttpserver.cvar.HTTPHeaders_ACCEPT
    ACCEPT_CHARSET = _net_http_pywraphttpserver.cvar.HTTPHeaders_ACCEPT_CHARSET
    ACCEPT_ENCODING = _net_http_pywraphttpserver.cvar.HTTPHeaders_ACCEPT_ENCODING
    ACCEPT_LANGUAGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_ACCEPT_LANGUAGE
    ACCEPT_RANGES = _net_http_pywraphttpserver.cvar.HTTPHeaders_ACCEPT_RANGES
    AGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_AGE
    AUTHORIZATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_AUTHORIZATION
    CACHE_CONTROL = _net_http_pywraphttpserver.cvar.HTTPHeaders_CACHE_CONTROL
    CONNECTION = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONNECTION
    CONTENT_DISPOSITION = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_DISPOSITION
    CONTENT_ENCODING = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_ENCODING
    CONTENT_LANGUAGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_LANGUAGE
    CONTENT_LENGTH = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_LENGTH
    CONTENT_LOCATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_LOCATION
    CONTENT_RANGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_RANGE
    CONTENT_TYPE = _net_http_pywraphttpserver.cvar.HTTPHeaders_CONTENT_TYPE
    COOKIE = _net_http_pywraphttpserver.cvar.HTTPHeaders_COOKIE
    DATE = _net_http_pywraphttpserver.cvar.HTTPHeaders_DATE
    DAV = _net_http_pywraphttpserver.cvar.HTTPHeaders_DAV
    DEPTH = _net_http_pywraphttpserver.cvar.HTTPHeaders_DEPTH
    DESTINATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_DESTINATION
    ETAG = _net_http_pywraphttpserver.cvar.HTTPHeaders_ETAG
    EXPECT = _net_http_pywraphttpserver.cvar.HTTPHeaders_EXPECT
    EXPIRES = _net_http_pywraphttpserver.cvar.HTTPHeaders_EXPIRES
    FROM = _net_http_pywraphttpserver.cvar.HTTPHeaders_FROM
    HOST = _net_http_pywraphttpserver.cvar.HTTPHeaders_HOST
    IF = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF
    IF_MATCH = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF_MATCH
    IF_MODIFIED_SINCE = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF_MODIFIED_SINCE
    IF_NONE_MATCH = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF_NONE_MATCH
    IF_RANGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF_RANGE
    IF_UNMODIFIED_SINCE = _net_http_pywraphttpserver.cvar.HTTPHeaders_IF_UNMODIFIED_SINCE
    KEEP_ALIVE = _net_http_pywraphttpserver.cvar.HTTPHeaders_KEEP_ALIVE
    LABEL = _net_http_pywraphttpserver.cvar.HTTPHeaders_LABEL
    LAST_MODIFIED = _net_http_pywraphttpserver.cvar.HTTPHeaders_LAST_MODIFIED
    LOCATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_LOCATION
    LOCK_TOKEN = _net_http_pywraphttpserver.cvar.HTTPHeaders_LOCK_TOKEN
    MS_AUTHOR_VIA = _net_http_pywraphttpserver.cvar.HTTPHeaders_MS_AUTHOR_VIA
    OVERWRITE_HDR = _net_http_pywraphttpserver.cvar.HTTPHeaders_OVERWRITE_HDR
    P3P = _net_http_pywraphttpserver.cvar.HTTPHeaders_P3P
    PRAGMA = _net_http_pywraphttpserver.cvar.HTTPHeaders_PRAGMA
    PROXY_CONNECTION = _net_http_pywraphttpserver.cvar.HTTPHeaders_PROXY_CONNECTION
    PROXY_AUTHENTICATE = _net_http_pywraphttpserver.cvar.HTTPHeaders_PROXY_AUTHENTICATE
    PROXY_AUTHORIZATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_PROXY_AUTHORIZATION
    RANGE = _net_http_pywraphttpserver.cvar.HTTPHeaders_RANGE
    REFERER = _net_http_pywraphttpserver.cvar.HTTPHeaders_REFERER
    REFRESH = _net_http_pywraphttpserver.cvar.HTTPHeaders_REFRESH
    SERVER = _net_http_pywraphttpserver.cvar.HTTPHeaders_SERVER
    SET_COOKIE = _net_http_pywraphttpserver.cvar.HTTPHeaders_SET_COOKIE
    STATUS_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_STATUS_URI
    TIMEOUT = _net_http_pywraphttpserver.cvar.HTTPHeaders_TIMEOUT
    TRAILERS = _net_http_pywraphttpserver.cvar.HTTPHeaders_TRAILERS
    TRANSFER_ENCODING = _net_http_pywraphttpserver.cvar.HTTPHeaders_TRANSFER_ENCODING
    TRANSFER_ENCODING_ABBRV = _net_http_pywraphttpserver.cvar.HTTPHeaders_TRANSFER_ENCODING_ABBRV
    UPGRADE = _net_http_pywraphttpserver.cvar.HTTPHeaders_UPGRADE
    USER_AGENT = _net_http_pywraphttpserver.cvar.HTTPHeaders_USER_AGENT
    VARY = _net_http_pywraphttpserver.cvar.HTTPHeaders_VARY
    VIA = _net_http_pywraphttpserver.cvar.HTTPHeaders_VIA
    WWW_AUTHENTICATE = _net_http_pywraphttpserver.cvar.HTTPHeaders_WWW_AUTHENTICATE
    X_FORWARDED_FOR = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_FORWARDED_FOR
    X_JPHONE_COPYRIGHT = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_JPHONE_COPYRIGHT
    X_XRDS_LOCATION = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_XRDS_LOCATION
    X_PROXYUSER_IP = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_PROXYUSER_IP
    X_UP_SUBNO = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_UP_SUBNO
    XID = _net_http_pywraphttpserver.cvar.HTTPHeaders_XID
    X_ROBOTS = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_ROBOTS
    GZIP_CACHE_CONTROL = _net_http_pywraphttpserver.cvar.HTTPHeaders_GZIP_CACHE_CONTROL
    GOOGLE_REQUEST_ID = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_REQUEST_ID
    GOOGLE_REQUEST_ID_ABBRV = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_REQUEST_ID_ABBRV
    GOOGLE_COMMAND = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_COMMAND
    GOOGLE_TOTAL_RECALL = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_TOTAL_RECALL
    X_USER_IP = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_USER_IP
    X_CLIENT_IP = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_CLIENT_IP
    X_DONT_COUNT_ADS = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_DONT_COUNT_ADS
    X_DONT_SHOW_ADS = _net_http_pywraphttpserver.cvar.HTTPHeaders_X_DONT_SHOW_ADS
    GSA_SUBJECT_DN = _net_http_pywraphttpserver.cvar.HTTPHeaders_GSA_SUBJECT_DN
    GSA_SUBJECT_GRPS = _net_http_pywraphttpserver.cvar.HTTPHeaders_GSA_SUBJECT_GRPS
    GSA_CONNECTOR_USER_INFO = _net_http_pywraphttpserver.cvar.HTTPHeaders_GSA_CONNECTOR_USER_INFO
    GSA_SESSION_ID = _net_http_pywraphttpserver.cvar.HTTPHeaders_GSA_SESSION_ID
    GOOGLE_ATTACK = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_ATTACK
    GOOGLE_ISUNSAFE = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_ISUNSAFE
    GOOGLE_BACKENDS = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_BACKENDS
    GOOGLE_DEBUG = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_DEBUG
    GOOGLE_PAYLOAD_LENGTH = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PAYLOAD_LENGTH
    GOOGLE_LOGENTRY = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_LOGENTRY
    GOOGLE_RETURN_WEBLOG_IN_HEADER = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_RETURN_WEBLOG_IN_HEADER
    GOOGLE_COUNTRY = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_COUNTRY
    GOOGLE_PROXY_IP = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PROXY_IP
    GOOGLE_PROXY_COUNTRY = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PROXY_COUNTRY
    GOOGLE_PROXY_RESTRICT = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PROXY_RESTRICT
    GOOGLE_PROXY_ENCODING = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PROXY_ENCODING
    GOOGLE_PROXY_POST_ENCODING = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PROXY_POST_ENCODING
    GOOGLE_EXPERIMENT = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_EXPERIMENT
    GOOGLE_LOGGING_RC = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_LOGGING_RC
    GOOGLE_EVENTID = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_EVENTID
    GOOGLE_PARTIAL_REPLIES_OFF = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PARTIAL_REPLIES_OFF
    GOOGLE_LOADTEST = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_LOADTEST
    GOOGLE_PRODUCTION_CONVERSION_EVENT = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_PRODUCTION_CONVERSION_EVENT
    GOOGLE_REQUEST_SOURCE = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_REQUEST_SOURCE
    GOOGLE_G_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_G_COMMAND_URI
    GOOGLE_T_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_T_COMMAND_URI
    GOOGLE_D_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_D_COMMAND_URI
    GOOGLE_H_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_H_COMMAND_URI
    GOOGLE_I_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_I_COMMAND_URI
    GOOGLE_M_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_M_COMMAND_URI
    GOOGLE_K_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_K_COMMAND_URI
    GOOGLE_P_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_P_COMMAND_URI
    GOOGLE_R_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_R_COMMAND_URI
    GOOGLE_U_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_U_COMMAND_URI
    GOOGLE_F_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_F_COMMAND_URI
    GOOGLE_B_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_B_COMMAND_URI
    GOOGLE_L_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_L_COMMAND_URI
    GOOGLE_X_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_X_COMMAND_URI
    GOOGLE_S_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_S_COMMAND_URI
    GOOGLE_O_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_O_COMMAND_URI
    GOOGLE_O2_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_O2_COMMAND_URI
    GOOGLE_O3_COMMAND_URI = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_O3_COMMAND_URI
    GOOGLE_DAPPER_TRACE_INFO = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_DAPPER_TRACE_INFO
    GOOGLE_NETMON_LABEL = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_NETMON_LABEL
    GOOGLE_SUPPRESS_ERROR_BODY = _net_http_pywraphttpserver.cvar.HTTPHeaders_GOOGLE_SUPPRESS_ERROR_BODY
    def __init__(self, *args):
        _swig_setattr(self, HTTPHeaders, 'this', _net_http_pywraphttpserver.new_HTTPHeaders(*args))
        _swig_setattr(self, HTTPHeaders, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPHeaders):
        try:
            if self.thisown: destroy(self)
        except: pass
    def ClearHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearHeaders(*args)
    def CopyHeader(*args): return _net_http_pywraphttpserver.HTTPHeaders_CopyHeader(*args)
    def CopyFrom(*args): return _net_http_pywraphttpserver.HTTPHeaders_CopyFrom(*args)
    def IsEmpty(*args): return _net_http_pywraphttpserver.HTTPHeaders_IsEmpty(*args)
    TR_NO_ONEBOX = _net_http_pywraphttpserver.cvar.HTTPHeaders_TR_NO_ONEBOX
    TR_ONEBOX = _net_http_pywraphttpserver.cvar.HTTPHeaders_TR_ONEBOX
    UNUSED = _net_http_pywraphttpserver.HTTPHeaders_UNUSED
    NO_OVERWRITE = _net_http_pywraphttpserver.HTTPHeaders_NO_OVERWRITE
    APPEND = _net_http_pywraphttpserver.HTTPHeaders_APPEND
    OVERWRITE = _net_http_pywraphttpserver.HTTPHeaders_OVERWRITE
    def GetHeader(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetHeader(*args)
    def GetHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetHeaders(*args)
    def GetHeaderOr(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetHeaderOr(*args)
    def HeaderIs(*args): return _net_http_pywraphttpserver.HTTPHeaders_HeaderIs(*args)
    def HeaderStartsWith(*args): return _net_http_pywraphttpserver.HTTPHeaders_HeaderStartsWith(*args)
    def SetHeader(*args): return _net_http_pywraphttpserver.HTTPHeaders_SetHeader(*args)
    def AddNewHeader(*args): return _net_http_pywraphttpserver.HTTPHeaders_AddNewHeader(*args)
    def ClearHeader(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearHeader(*args)
    def ClearHeadersWithPrefix(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearHeadersWithPrefix(*args)
    def ClearGoogleHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearGoogleHeaders(*args)
    def ClearHopByHopHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearHopByHopHeaders(*args)
    def ClearSafeHopByHopHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ClearSafeHopByHopHeaders(*args)
    def firstline(*args): return _net_http_pywraphttpserver.HTTPHeaders_firstline(*args)
    HTTP_ERROR = _net_http_pywraphttpserver.HTTPHeaders_HTTP_ERROR
    HTTP_OTHER = _net_http_pywraphttpserver.HTTPHeaders_HTTP_OTHER
    HTTP_ICY = _net_http_pywraphttpserver.HTTPHeaders_HTTP_ICY
    HTTP_09 = _net_http_pywraphttpserver.HTTPHeaders_HTTP_09
    HTTP_10 = _net_http_pywraphttpserver.HTTPHeaders_HTTP_10
    HTTP_11 = _net_http_pywraphttpserver.HTTPHeaders_HTTP_11
    HTTP_RTSP = _net_http_pywraphttpserver.HTTPHeaders_HTTP_RTSP
    def http_version(*args): return _net_http_pywraphttpserver.HTTPHeaders_http_version(*args)
    def http_version_str(*args): return _net_http_pywraphttpserver.HTTPHeaders_http_version_str(*args)
    def set_http_version(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_http_version(*args)
    PROTO_ERROR = _net_http_pywraphttpserver.HTTPHeaders_PROTO_ERROR
    PROTO_GET = _net_http_pywraphttpserver.HTTPHeaders_PROTO_GET
    PROTO_POST = _net_http_pywraphttpserver.HTTPHeaders_PROTO_POST
    PROTO_HEAD = _net_http_pywraphttpserver.HTTPHeaders_PROTO_HEAD
    PROTO_GOOGLE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_GOOGLE
    PROTO_PUT = _net_http_pywraphttpserver.HTTPHeaders_PROTO_PUT
    PROTO_DELETE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_DELETE
    PROTO_PROPFIND = _net_http_pywraphttpserver.HTTPHeaders_PROTO_PROPFIND
    PROTO_PROPPATCH = _net_http_pywraphttpserver.HTTPHeaders_PROTO_PROPPATCH
    PROTO_MKCOL = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MKCOL
    PROTO_COPY = _net_http_pywraphttpserver.HTTPHeaders_PROTO_COPY
    PROTO_MOVE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MOVE
    PROTO_LOCK = _net_http_pywraphttpserver.HTTPHeaders_PROTO_LOCK
    PROTO_UNLOCK = _net_http_pywraphttpserver.HTTPHeaders_PROTO_UNLOCK
    PROTO_TRACE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_TRACE
    PROTO_OPTIONS = _net_http_pywraphttpserver.HTTPHeaders_PROTO_OPTIONS
    PROTO_CONNECT = _net_http_pywraphttpserver.HTTPHeaders_PROTO_CONNECT
    PROTO_ICP_QUERY = _net_http_pywraphttpserver.HTTPHeaders_PROTO_ICP_QUERY
    PROTO_PURGE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_PURGE
    PROTO_VERSION_CONTROL = _net_http_pywraphttpserver.HTTPHeaders_PROTO_VERSION_CONTROL
    PROTO_REPORT = _net_http_pywraphttpserver.HTTPHeaders_PROTO_REPORT
    PROTO_CHECKOUT = _net_http_pywraphttpserver.HTTPHeaders_PROTO_CHECKOUT
    PROTO_CHECKIN = _net_http_pywraphttpserver.HTTPHeaders_PROTO_CHECKIN
    PROTO_UNCHECKOUT = _net_http_pywraphttpserver.HTTPHeaders_PROTO_UNCHECKOUT
    PROTO_MKWORKSPACE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MKWORKSPACE
    PROTO_UPDATE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_UPDATE
    PROTO_LABEL = _net_http_pywraphttpserver.HTTPHeaders_PROTO_LABEL
    PROTO_MERGE = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MERGE
    PROTO_BASELINE_CONTROL = _net_http_pywraphttpserver.HTTPHeaders_PROTO_BASELINE_CONTROL
    PROTO_MKACTIVITY = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MKACTIVITY
    PROTO_ACL = _net_http_pywraphttpserver.HTTPHeaders_PROTO_ACL
    PROTO_MKCALENDAR = _net_http_pywraphttpserver.HTTPHeaders_PROTO_MKCALENDAR
    def protocol(*args): return _net_http_pywraphttpserver.HTTPHeaders_protocol(*args)
    def protocol_str(*args): return _net_http_pywraphttpserver.HTTPHeaders_protocol_str(*args)
    def set_protocol(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_protocol(*args)
    def req_path(*args): return _net_http_pywraphttpserver.HTTPHeaders_req_path(*args)
    def req_path_string(*args): return _net_http_pywraphttpserver.HTTPHeaders_req_path_string(*args)
    def GetFirstlineRawUri(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetFirstlineRawUri(*args)
    def uri(*args): return _net_http_pywraphttpserver.HTTPHeaders_uri(*args)
    def set_uri(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_uri(*args)
    def uri_as_str(*args): return _net_http_pywraphttpserver.HTTPHeaders_uri_as_str(*args)
    def response_code(*args): return _net_http_pywraphttpserver.HTTPHeaders_response_code(*args)
    def set_response_code(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_response_code(*args)
    def reason_phrase(*args): return _net_http_pywraphttpserver.HTTPHeaders_reason_phrase(*args)
    def set_reason_phrase(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_reason_phrase(*args)
    def set_max_memory_allocated(*args): return _net_http_pywraphttpserver.HTTPHeaders_set_max_memory_allocated(*args)
    def memory_allocated(*args): return _net_http_pywraphttpserver.HTTPHeaders_memory_allocated(*args)
    def num_bytes_read_from_buffer(*args): return _net_http_pywraphttpserver.HTTPHeaders_num_bytes_read_from_buffer(*args)
    def IsUsingTooMuchMemory(*args): return _net_http_pywraphttpserver.HTTPHeaders_IsUsingTooMuchMemory(*args)
    def PrependHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_PrependHeaders(*args)
    def AppendAllHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_AppendAllHeaders(*args)
    def HeaderOrder(*args): return _net_http_pywraphttpserver.HTTPHeaders_HeaderOrder(*args)
    def DebugString(*args): return _net_http_pywraphttpserver.HTTPHeaders_DebugString(*args)
    def String(*args): return _net_http_pywraphttpserver.HTTPHeaders_String(*args)
    def GetHostAndPort(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetHostAndPort(*args)
    def GetHostName(*args): return _net_http_pywraphttpserver.HTTPHeaders_GetHostName(*args)
    def ForceRelativeURI(*args): return _net_http_pywraphttpserver.HTTPHeaders_ForceRelativeURI(*args)
    def ReadMoreInfo(*args): return _net_http_pywraphttpserver.HTTPHeaders_ReadMoreInfo(*args)
    def parse_error(*args): return _net_http_pywraphttpserver.HTTPHeaders_parse_error(*args)
    def AddRequestFirstline(*args): return _net_http_pywraphttpserver.HTTPHeaders_AddRequestFirstline(*args)
    def AddResponseFirstline(*args): return _net_http_pywraphttpserver.HTTPHeaders_AddResponseFirstline(*args)
    def MakeRequestFirstLine(*args): return _net_http_pywraphttpserver.HTTPHeaders_MakeRequestFirstLine(*args)
    def MakeQuickFirstLine(*args): return _net_http_pywraphttpserver.HTTPHeaders_MakeQuickFirstLine(*args)
    def SetHeaderFromLine(*args): return _net_http_pywraphttpserver.HTTPHeaders_SetHeaderFromLine(*args)
    def SetHeaderFromLines(*args): return _net_http_pywraphttpserver.HTTPHeaders_SetHeaderFromLines(*args)
    def WriteHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_WriteHeaders(*args)
    def ParseContentTypeFromHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ParseContentTypeFromHeaders(*args)
    def ParseContentLanguageFromHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ParseContentLanguageFromHeaders(*args)
    def ParseContentDispositionFromHeaders(*args): return _net_http_pywraphttpserver.HTTPHeaders_ParseContentDispositionFromHeaders(*args)
    def Swap(*args): return _net_http_pywraphttpserver.HTTPHeaders_Swap(*args)

class HTTPHeadersPtr(HTTPHeaders):
    def __init__(self, this):
        _swig_setattr(self, HTTPHeaders, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPHeaders, 'thisown', 0)
        _swig_setattr(self, HTTPHeaders,self.__class__,HTTPHeaders)
_net_http_pywraphttpserver.HTTPHeaders_swigregister(HTTPHeadersPtr)

class GnutellaHeaders(HTTPHeaders):
    __swig_setmethods__ = {}
    for _s in [HTTPHeaders]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, GnutellaHeaders, name, value)
    __swig_getmethods__ = {}
    for _s in [HTTPHeaders]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, GnutellaHeaders, name)
    def __repr__(self):
        return "<C GnutellaHeaders instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, GnutellaHeaders, 'this', _net_http_pywraphttpserver.new_GnutellaHeaders(*args))
        _swig_setattr(self, GnutellaHeaders, 'thisown', 1)
    GNUTELLA_ERROR = _net_http_pywraphttpserver.GnutellaHeaders_GNUTELLA_ERROR
    GNUTELLA_04 = _net_http_pywraphttpserver.GnutellaHeaders_GNUTELLA_04
    GNUTELLA_06 = _net_http_pywraphttpserver.GnutellaHeaders_GNUTELLA_06
    GNUTELLA_07 = _net_http_pywraphttpserver.GnutellaHeaders_GNUTELLA_07
    def gnutella_version(*args): return _net_http_pywraphttpserver.GnutellaHeaders_gnutella_version(*args)
    __swig_getmethods__["gnutella_version_str"] = lambda x: _net_http_pywraphttpserver.GnutellaHeaders_gnutella_version_str
    if _newclass:gnutella_version_str = staticmethod(_net_http_pywraphttpserver.GnutellaHeaders_gnutella_version_str)
    def gnutella_version_str(*args): return _net_http_pywraphttpserver.GnutellaHeaders_gnutella_version_str(*args)
    __swig_getmethods__["gnutella_connect_str"] = lambda x: _net_http_pywraphttpserver.GnutellaHeaders_gnutella_connect_str
    if _newclass:gnutella_connect_str = staticmethod(_net_http_pywraphttpserver.GnutellaHeaders_gnutella_connect_str)
    def gnutella_connect_str(*args): return _net_http_pywraphttpserver.GnutellaHeaders_gnutella_connect_str(*args)
    def set_gnutella_version(*args): return _net_http_pywraphttpserver.GnutellaHeaders_set_gnutella_version(*args)
    def CopyFrom(*args): return _net_http_pywraphttpserver.GnutellaHeaders_CopyFrom(*args)
    def Swap(*args): return _net_http_pywraphttpserver.GnutellaHeaders_Swap(*args)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_GnutellaHeaders):
        try:
            if self.thisown: destroy(self)
        except: pass

class GnutellaHeadersPtr(GnutellaHeaders):
    def __init__(self, this):
        _swig_setattr(self, GnutellaHeaders, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, GnutellaHeaders, 'thisown', 0)
        _swig_setattr(self, GnutellaHeaders,self.__class__,GnutellaHeaders)
_net_http_pywraphttpserver.GnutellaHeaders_swigregister(GnutellaHeadersPtr)
kNoHTTPAuthMethod = cvar.kNoHTTPAuthMethod
kHTTPAuthBasic = cvar.kHTTPAuthBasic
kHTTPAuthNTLM = cvar.kHTTPAuthNTLM
kHTTPAuthSSO = cvar.kHTTPAuthSSO
kHTTPAuthX509ClientCertificate = cvar.kHTTPAuthX509ClientCertificate

class HTTPUtils(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPUtils, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPUtils, name)
    def __repr__(self):
        return "<C HTTPUtils instance at %s>" % (self.this,)
    __swig_getmethods__["ParseContentTypeFromMetaTag"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseContentTypeFromMetaTag
    if _newclass:ParseContentTypeFromMetaTag = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseContentTypeFromMetaTag)
    __swig_getmethods__["ParseContentLanguageFromMetaTag"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseContentLanguageFromMetaTag
    if _newclass:ParseContentLanguageFromMetaTag = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseContentLanguageFromMetaTag)
    __swig_getmethods__["ParseContentDisposition"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseContentDisposition
    if _newclass:ParseContentDisposition = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseContentDisposition)
    __swig_getmethods__["ExtractBody"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ExtractBody
    if _newclass:ExtractBody = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ExtractBody)
    __swig_getmethods__["ParseHTTPHeaders"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseHTTPHeaders
    if _newclass:ParseHTTPHeaders = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseHTTPHeaders)
    __swig_getmethods__["SkipHttpHeaders"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_SkipHttpHeaders
    if _newclass:SkipHttpHeaders = staticmethod(_net_http_pywraphttpserver.HTTPUtils_SkipHttpHeaders)
    __swig_getmethods__["ParseHostHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseHostHeader
    if _newclass:ParseHostHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseHostHeader)
    __swig_getmethods__["ParseContentLengthHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseContentLengthHeader
    if _newclass:ParseContentLengthHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseContentLengthHeader)
    __swig_getmethods__["ParseAuthMethods"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseAuthMethods
    if _newclass:ParseAuthMethods = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseAuthMethods)
    __swig_getmethods__["AuthMethodString"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_AuthMethodString
    if _newclass:AuthMethodString = staticmethod(_net_http_pywraphttpserver.HTTPUtils_AuthMethodString)
    __swig_getmethods__["SkipBadContent"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_SkipBadContent
    if _newclass:SkipBadContent = staticmethod(_net_http_pywraphttpserver.HTTPUtils_SkipBadContent)
    __swig_getmethods__["IsDocumentBad"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_IsDocumentBad
    if _newclass:IsDocumentBad = staticmethod(_net_http_pywraphttpserver.HTTPUtils_IsDocumentBad)
    __swig_getmethods__["IsContentGzipEncoded"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_IsContentGzipEncoded
    if _newclass:IsContentGzipEncoded = staticmethod(_net_http_pywraphttpserver.HTTPUtils_IsContentGzipEncoded)
    __swig_getmethods__["IsContentDeflateEncoded"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_IsContentDeflateEncoded
    if _newclass:IsContentDeflateEncoded = staticmethod(_net_http_pywraphttpserver.HTTPUtils_IsContentDeflateEncoded)
    __swig_getmethods__["IsResponseFirstline"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_IsResponseFirstline
    if _newclass:IsResponseFirstline = staticmethod(_net_http_pywraphttpserver.HTTPUtils_IsResponseFirstline)
    __swig_getmethods__["ParseHeaderField"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseHeaderField
    if _newclass:ParseHeaderField = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseHeaderField)
    __swig_getmethods__["ParseAbbreviatedGoogleID"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseAbbreviatedGoogleID
    if _newclass:ParseAbbreviatedGoogleID = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseAbbreviatedGoogleID)
    __swig_getmethods__["ParseXForwardedFor"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseXForwardedFor
    if _newclass:ParseXForwardedFor = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseXForwardedFor)
    __swig_getmethods__["ParseBasicAuthHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseBasicAuthHeader
    if _newclass:ParseBasicAuthHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseBasicAuthHeader)
    __swig_getmethods__["UpdateHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_UpdateHeader
    if _newclass:UpdateHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_UpdateHeader)
    __swig_getmethods__["HTTPTime"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_HTTPTime
    if _newclass:HTTPTime = staticmethod(_net_http_pywraphttpserver.HTTPUtils_HTTPTime)
    __swig_getmethods__["RobustHTTPTime"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_RobustHTTPTime
    if _newclass:RobustHTTPTime = staticmethod(_net_http_pywraphttpserver.HTTPUtils_RobustHTTPTime)
    __swig_getmethods__["ParseHeaderDirective"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirective
    if _newclass:ParseHeaderDirective = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirective)
    __swig_getmethods__["ParseHeaderDirectiveInt"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirectiveInt
    if _newclass:ParseHeaderDirectiveInt = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirectiveInt)
    __swig_getmethods__["ListHeaderDirectiveKeys"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ListHeaderDirectiveKeys
    if _newclass:ListHeaderDirectiveKeys = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ListHeaderDirectiveKeys)
    __swig_getmethods__["HasHeaderDirective"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_HasHeaderDirective
    if _newclass:HasHeaderDirective = staticmethod(_net_http_pywraphttpserver.HTTPUtils_HasHeaderDirective)
    __swig_getmethods__["DisableBrowserCaching"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_DisableBrowserCaching
    if _newclass:DisableBrowserCaching = staticmethod(_net_http_pywraphttpserver.HTTPUtils_DisableBrowserCaching)
    __swig_getmethods__["ParseCacheExpirationTimeFromHeaders"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseCacheExpirationTimeFromHeaders
    if _newclass:ParseCacheExpirationTimeFromHeaders = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseCacheExpirationTimeFromHeaders)
    __swig_getmethods__["AddGoogleRequestSourceHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_AddGoogleRequestSourceHeader
    if _newclass:AddGoogleRequestSourceHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_AddGoogleRequestSourceHeader)
    __swig_getmethods__["ParseUsernameAndProcessNameFromRequestSourceHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader
    if _newclass:ParseUsernameAndProcessNameFromRequestSourceHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader)
    __swig_getmethods__["EligibleForNotModified"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_EligibleForNotModified
    if _newclass:EligibleForNotModified = staticmethod(_net_http_pywraphttpserver.HTTPUtils_EligibleForNotModified)
    __swig_getmethods__["SetNetmonLabelHTTPHeader"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_SetNetmonLabelHTTPHeader
    if _newclass:SetNetmonLabelHTTPHeader = staticmethod(_net_http_pywraphttpserver.HTTPUtils_SetNetmonLabelHTTPHeader)
    __swig_getmethods__["ExpireCookieRecursively"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ExpireCookieRecursively
    if _newclass:ExpireCookieRecursively = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ExpireCookieRecursively)
    __swig_getmethods__["ExpireAllCookiesRecursively"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_ExpireAllCookiesRecursively
    if _newclass:ExpireAllCookiesRecursively = staticmethod(_net_http_pywraphttpserver.HTTPUtils_ExpireAllCookiesRecursively)
    __swig_getmethods__["IsValidHeaderOrder"] = lambda x: _net_http_pywraphttpserver.HTTPUtils_IsValidHeaderOrder
    if _newclass:IsValidHeaderOrder = staticmethod(_net_http_pywraphttpserver.HTTPUtils_IsValidHeaderOrder)
    def __init__(self, *args):
        _swig_setattr(self, HTTPUtils, 'this', _net_http_pywraphttpserver.new_HTTPUtils(*args))
        _swig_setattr(self, HTTPUtils, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPUtils):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPUtilsPtr(HTTPUtils):
    def __init__(self, this):
        _swig_setattr(self, HTTPUtils, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPUtils, 'thisown', 0)
        _swig_setattr(self, HTTPUtils,self.__class__,HTTPUtils)
_net_http_pywraphttpserver.HTTPUtils_swigregister(HTTPUtilsPtr)

HTTPUtils_ParseContentTypeFromMetaTag = _net_http_pywraphttpserver.HTTPUtils_ParseContentTypeFromMetaTag

HTTPUtils_ParseContentLanguageFromMetaTag = _net_http_pywraphttpserver.HTTPUtils_ParseContentLanguageFromMetaTag

HTTPUtils_ParseContentDisposition = _net_http_pywraphttpserver.HTTPUtils_ParseContentDisposition

HTTPUtils_ExtractBody = _net_http_pywraphttpserver.HTTPUtils_ExtractBody

HTTPUtils_ParseHTTPHeaders = _net_http_pywraphttpserver.HTTPUtils_ParseHTTPHeaders

HTTPUtils_SkipHttpHeaders = _net_http_pywraphttpserver.HTTPUtils_SkipHttpHeaders

HTTPUtils_ParseHostHeader = _net_http_pywraphttpserver.HTTPUtils_ParseHostHeader

HTTPUtils_ParseContentLengthHeader = _net_http_pywraphttpserver.HTTPUtils_ParseContentLengthHeader

HTTPUtils_ParseAuthMethods = _net_http_pywraphttpserver.HTTPUtils_ParseAuthMethods

HTTPUtils_AuthMethodString = _net_http_pywraphttpserver.HTTPUtils_AuthMethodString

HTTPUtils_SkipBadContent = _net_http_pywraphttpserver.HTTPUtils_SkipBadContent

HTTPUtils_IsDocumentBad = _net_http_pywraphttpserver.HTTPUtils_IsDocumentBad

HTTPUtils_IsContentGzipEncoded = _net_http_pywraphttpserver.HTTPUtils_IsContentGzipEncoded

HTTPUtils_IsContentDeflateEncoded = _net_http_pywraphttpserver.HTTPUtils_IsContentDeflateEncoded

HTTPUtils_IsResponseFirstline = _net_http_pywraphttpserver.HTTPUtils_IsResponseFirstline

HTTPUtils_ParseHeaderField = _net_http_pywraphttpserver.HTTPUtils_ParseHeaderField

HTTPUtils_ParseAbbreviatedGoogleID = _net_http_pywraphttpserver.HTTPUtils_ParseAbbreviatedGoogleID

HTTPUtils_ParseXForwardedFor = _net_http_pywraphttpserver.HTTPUtils_ParseXForwardedFor

HTTPUtils_ParseBasicAuthHeader = _net_http_pywraphttpserver.HTTPUtils_ParseBasicAuthHeader

HTTPUtils_UpdateHeader = _net_http_pywraphttpserver.HTTPUtils_UpdateHeader

HTTPUtils_HTTPTime = _net_http_pywraphttpserver.HTTPUtils_HTTPTime

HTTPUtils_RobustHTTPTime = _net_http_pywraphttpserver.HTTPUtils_RobustHTTPTime

HTTPUtils_ParseHeaderDirective = _net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirective

HTTPUtils_ParseHeaderDirectiveInt = _net_http_pywraphttpserver.HTTPUtils_ParseHeaderDirectiveInt

HTTPUtils_ListHeaderDirectiveKeys = _net_http_pywraphttpserver.HTTPUtils_ListHeaderDirectiveKeys

HTTPUtils_HasHeaderDirective = _net_http_pywraphttpserver.HTTPUtils_HasHeaderDirective

HTTPUtils_DisableBrowserCaching = _net_http_pywraphttpserver.HTTPUtils_DisableBrowserCaching

HTTPUtils_ParseCacheExpirationTimeFromHeaders = _net_http_pywraphttpserver.HTTPUtils_ParseCacheExpirationTimeFromHeaders

HTTPUtils_AddGoogleRequestSourceHeader = _net_http_pywraphttpserver.HTTPUtils_AddGoogleRequestSourceHeader

HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader = _net_http_pywraphttpserver.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader

HTTPUtils_EligibleForNotModified = _net_http_pywraphttpserver.HTTPUtils_EligibleForNotModified

HTTPUtils_SetNetmonLabelHTTPHeader = _net_http_pywraphttpserver.HTTPUtils_SetNetmonLabelHTTPHeader

HTTPUtils_ExpireCookieRecursively = _net_http_pywraphttpserver.HTTPUtils_ExpireCookieRecursively

HTTPUtils_ExpireAllCookiesRecursively = _net_http_pywraphttpserver.HTTPUtils_ExpireAllCookiesRecursively

HTTPUtils_IsValidHeaderOrder = _net_http_pywraphttpserver.HTTPUtils_IsValidHeaderOrder

class HTTPServerConnectionPolicy(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerConnectionPolicy, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerConnectionPolicy, name)
    def __repr__(self):
        return "<C HTTPServerConnectionPolicy instance at %s>" % (self.this,)
    __swig_setmethods__["read_timeout"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_read_timeout_set
    __swig_getmethods__["read_timeout"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_read_timeout_get
    if _newclass:read_timeout = property(_net_http_pywraphttpserver.HTTPServerConnectionPolicy_read_timeout_get, _net_http_pywraphttpserver.HTTPServerConnectionPolicy_read_timeout_set)
    __swig_setmethods__["write_timeout"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_write_timeout_set
    __swig_getmethods__["write_timeout"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_write_timeout_get
    if _newclass:write_timeout = property(_net_http_pywraphttpserver.HTTPServerConnectionPolicy_write_timeout_get, _net_http_pywraphttpserver.HTTPServerConnectionPolicy_write_timeout_set)
    __swig_setmethods__["max_requests"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_max_requests_set
    __swig_getmethods__["max_requests"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_max_requests_get
    if _newclass:max_requests = property(_net_http_pywraphttpserver.HTTPServerConnectionPolicy_max_requests_get, _net_http_pywraphttpserver.HTTPServerConnectionPolicy_max_requests_set)
    __swig_setmethods__["unlimited_url_length"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_unlimited_url_length_set
    __swig_getmethods__["unlimited_url_length"] = _net_http_pywraphttpserver.HTTPServerConnectionPolicy_unlimited_url_length_get
    if _newclass:unlimited_url_length = property(_net_http_pywraphttpserver.HTTPServerConnectionPolicy_unlimited_url_length_get, _net_http_pywraphttpserver.HTTPServerConnectionPolicy_unlimited_url_length_set)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerConnectionPolicy, 'this', _net_http_pywraphttpserver.new_HTTPServerConnectionPolicy(*args))
        _swig_setattr(self, HTTPServerConnectionPolicy, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerConnectionPolicy):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPServerConnectionPolicyPtr(HTTPServerConnectionPolicy):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerConnectionPolicy, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerConnectionPolicy, 'thisown', 0)
        _swig_setattr(self, HTTPServerConnectionPolicy,self.__class__,HTTPServerConnectionPolicy)
_net_http_pywraphttpserver.HTTPServerConnectionPolicy_swigregister(HTTPServerConnectionPolicyPtr)

class HTTPServerHealthCheckInterface(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerHealthCheckInterface, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerHealthCheckInterface, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C HTTPServerHealthCheckInterface instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerHealthCheckInterface):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CanServeRequest(*args): return _net_http_pywraphttpserver.HTTPServerHealthCheckInterface_CanServeRequest(*args)
    __swig_getmethods__["NewPeriodicHealthChecker"] = lambda x: _net_http_pywraphttpserver.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker
    if _newclass:NewPeriodicHealthChecker = staticmethod(_net_http_pywraphttpserver.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker)

class HTTPServerHealthCheckInterfacePtr(HTTPServerHealthCheckInterface):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerHealthCheckInterface, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerHealthCheckInterface, 'thisown', 0)
        _swig_setattr(self, HTTPServerHealthCheckInterface,self.__class__,HTTPServerHealthCheckInterface)
_net_http_pywraphttpserver.HTTPServerHealthCheckInterface_swigregister(HTTPServerHealthCheckInterfacePtr)

HTTPServerHealthCheckInterface_NewPeriodicHealthChecker = _net_http_pywraphttpserver.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker

class HTTPServerPlugin(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerPlugin, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerPlugin, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C HTTPServerPlugin instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerPlugin):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Startup(*args): return _net_http_pywraphttpserver.HTTPServerPlugin_Startup(*args)
    def Shutdown(*args): return _net_http_pywraphttpserver.HTTPServerPlugin_Shutdown(*args)

class HTTPServerPluginPtr(HTTPServerPlugin):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerPlugin, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerPlugin, 'thisown', 0)
        _swig_setattr(self, HTTPServerPlugin,self.__class__,HTTPServerPlugin)
_net_http_pywraphttpserver.HTTPServerPlugin_swigregister(HTTPServerPluginPtr)

class HTTPServerOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerOptions, name)
    def __repr__(self):
        return "<C HTTPServerOptions instance at %s>" % (self.this,)
    RPC_UNKNOWN = _net_http_pywraphttpserver.HTTPServerOptions_RPC_UNKNOWN
    RPC1 = _net_http_pywraphttpserver.HTTPServerOptions_RPC1
    RPC2 = _net_http_pywraphttpserver.HTTPServerOptions_RPC2
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerOptions, 'this', _net_http_pywraphttpserver.new_HTTPServerOptions(*args))
        _swig_setattr(self, HTTPServerOptions, 'thisown', 1)
    __swig_setmethods__["rpc_version"] = _net_http_pywraphttpserver.HTTPServerOptions_rpc_version_set
    __swig_getmethods__["rpc_version"] = _net_http_pywraphttpserver.HTTPServerOptions_rpc_version_get
    if _newclass:rpc_version = property(_net_http_pywraphttpserver.HTTPServerOptions_rpc_version_get, _net_http_pywraphttpserver.HTTPServerOptions_rpc_version_set)
    __swig_setmethods__["event_manager"] = _net_http_pywraphttpserver.HTTPServerOptions_event_manager_set
    __swig_getmethods__["event_manager"] = _net_http_pywraphttpserver.HTTPServerOptions_event_manager_get
    if _newclass:event_manager = property(_net_http_pywraphttpserver.HTTPServerOptions_event_manager_get, _net_http_pywraphttpserver.HTTPServerOptions_event_manager_set)
    __swig_setmethods__["multithreaded_udp"] = _net_http_pywraphttpserver.HTTPServerOptions_multithreaded_udp_set
    __swig_getmethods__["multithreaded_udp"] = _net_http_pywraphttpserver.HTTPServerOptions_multithreaded_udp_get
    if _newclass:multithreaded_udp = property(_net_http_pywraphttpserver.HTTPServerOptions_multithreaded_udp_get, _net_http_pywraphttpserver.HTTPServerOptions_multithreaded_udp_set)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPServerOptionsPtr(HTTPServerOptions):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerOptions, 'thisown', 0)
        _swig_setattr(self, HTTPServerOptions,self.__class__,HTTPServerOptions)
_net_http_pywraphttpserver.HTTPServerOptions_swigregister(HTTPServerOptionsPtr)

class HTTPServer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServer, name)
    def __repr__(self):
        return "<C HTTPServer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServer, 'this', _net_http_pywraphttpserver.new_HTTPServer(*args))
        _swig_setattr(self, HTTPServer, 'thisown', 1)
        
        
        
        
        
        
        self.ss = args[0]

    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServer):
        try:
            if self.thisown: destroy(self)
        except: pass
    CLIENT_TRUSTED = _net_http_pywraphttpserver.HTTPServer_CLIENT_TRUSTED
    CLIENT_UNTRUSTED = _net_http_pywraphttpserver.HTTPServer_CLIENT_UNTRUSTED
    def GetConnectionPolicy(*args): return _net_http_pywraphttpserver.HTTPServer_GetConnectionPolicy(*args)
    __swig_getmethods__["InitConnectionPolicy"] = lambda x: _net_http_pywraphttpserver.HTTPServer_InitConnectionPolicy
    if _newclass:InitConnectionPolicy = staticmethod(_net_http_pywraphttpserver.HTTPServer_InitConnectionPolicy)
    def SetConnectionPolicy(*args): return _net_http_pywraphttpserver.HTTPServer_SetConnectionPolicy(*args)
    def AcceptUDP(*args): return _net_http_pywraphttpserver.HTTPServer_AcceptUDP(*args)
    def SetUDPBufferSizes(*args): return _net_http_pywraphttpserver.HTTPServer_SetUDPBufferSizes(*args)
    def SetWindowSizesAndLatency(*args): return _net_http_pywraphttpserver.HTTPServer_SetWindowSizesAndLatency(*args)
    def AlsoListenOnPort(*args): return _net_http_pywraphttpserver.HTTPServer_AlsoListenOnPort(*args)
    def RegisterHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RegisterHandler(*args)
    def RegisterSecureHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RegisterSecureHandler(*args)
    def RegisterSecureRPCHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RegisterSecureRPCHandler(*args)
    def RemoveHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RemoveHandler(*args)
    def GetRegisteredURIs(*args): return _net_http_pywraphttpserver.HTTPServer_GetRegisteredURIs(*args)
    def GetRegisteredURIHandlers(*args): return _net_http_pywraphttpserver.HTTPServer_GetRegisteredURIHandlers(*args)
    def RegisterApplication(*args): return _net_http_pywraphttpserver.HTTPServer_RegisterApplication(*args)
    DISPATCH_BY_PATH = _net_http_pywraphttpserver.HTTPServer_DISPATCH_BY_PATH
    DISPATCH_AS_PROXY = _net_http_pywraphttpserver.HTTPServer_DISPATCH_AS_PROXY
    def set_dispatch_mode(*args): return _net_http_pywraphttpserver.HTTPServer_set_dispatch_mode(*args)
    def RegisterSigTermHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RegisterSigTermHandler(*args)
    def sigterm_handler(*args): return _net_http_pywraphttpserver.HTTPServer_sigterm_handler(*args)
    def Suspend(*args): return _net_http_pywraphttpserver.HTTPServer_Suspend(*args)
    def Resume(*args): return _net_http_pywraphttpserver.HTTPServer_Resume(*args)
    def suspended(*args): return _net_http_pywraphttpserver.HTTPServer_suspended(*args)
    def SuspendAccepting(*args): return _net_http_pywraphttpserver.HTTPServer_SuspendAccepting(*args)
    def ResumeAccepting(*args): return _net_http_pywraphttpserver.HTTPServer_ResumeAccepting(*args)
    def SetExecutor(*args): return _net_http_pywraphttpserver.HTTPServer_SetExecutor(*args)
    def SetDefaultExecutor(*args): return _net_http_pywraphttpserver.HTTPServer_SetDefaultExecutor(*args)
    def SetThreadPool(*args): return _net_http_pywraphttpserver.HTTPServer_SetThreadPool(*args)
    def SetSelectServer(*args): return _net_http_pywraphttpserver.HTTPServer_SetSelectServer(*args)
    def IsTrustedClient(*args): return _net_http_pywraphttpserver.HTTPServer_IsTrustedClient(*args)
    def SetTrustedClients(*args): return _net_http_pywraphttpserver.HTTPServer_SetTrustedClients(*args)
    def MakePublic(*args): return _net_http_pywraphttpserver.HTTPServer_MakePublic(*args)
    def MakePrivate(*args): return _net_http_pywraphttpserver.HTTPServer_MakePrivate(*args)
    def SetUncompressInput(*args): return _net_http_pywraphttpserver.HTTPServer_SetUncompressInput(*args)
    def SetCompressOutput(*args): return _net_http_pywraphttpserver.HTTPServer_SetCompressOutput(*args)
    def QuitHandler(*args): return _net_http_pywraphttpserver.HTTPServer_QuitHandler(*args)
    def AbortHandler(*args): return _net_http_pywraphttpserver.HTTPServer_AbortHandler(*args)
    def PassthruHandler(*args): return _net_http_pywraphttpserver.HTTPServer_PassthruHandler(*args)
    def VarzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_VarzHandler(*args)
    def VarzDocHandler(*args): return _net_http_pywraphttpserver.HTTPServer_VarzDocHandler(*args)
    def HealthzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_HealthzHandler(*args)
    def ProfilezHandler(*args): return _net_http_pywraphttpserver.HTTPServer_ProfilezHandler(*args)
    def StatuszHandler(*args): return _net_http_pywraphttpserver.HTTPServer_StatuszHandler(*args)
    def FormlistHandler(*args): return _net_http_pywraphttpserver.HTTPServer_FormlistHandler(*args)
    def ThreadzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_ThreadzHandler(*args)
    def SymbolzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_SymbolzHandler(*args)
    def ContentionzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_ContentionzHandler(*args)
    def HeapzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_HeapzHandler(*args)
    def GrowthzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_GrowthzHandler(*args)
    def ProczHandler(*args): return _net_http_pywraphttpserver.HTTPServer_ProczHandler(*args)
    def RequestzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RequestzHandler(*args)
    def TracezHandler(*args): return _net_http_pywraphttpserver.HTTPServer_TracezHandler(*args)
    def StyleHandler(*args): return _net_http_pywraphttpserver.HTTPServer_StyleHandler(*args)
    def EventLogHandler(*args): return _net_http_pywraphttpserver.HTTPServer_EventLogHandler(*args)
    def HelpzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_HelpzHandler(*args)
    def FlushLogzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_FlushLogzHandler(*args)
    def ShowEventLogPage(*args): return _net_http_pywraphttpserver.HTTPServer_ShowEventLogPage(*args)
    def PrintEventLog(*args): return _net_http_pywraphttpserver.HTTPServer_PrintEventLog(*args)
    def NullHandler(*args): return _net_http_pywraphttpserver.HTTPServer_NullHandler(*args)
    def VHandler(*args): return _net_http_pywraphttpserver.HTTPServer_VHandler(*args)
    def AHandler(*args): return _net_http_pywraphttpserver.HTTPServer_AHandler(*args)
    def PortmapzHandler(*args): return _net_http_pywraphttpserver.HTTPServer_PortmapzHandler(*args)
    def SetHealthCheck(*args): return _net_http_pywraphttpserver.HTTPServer_SetHealthCheck(*args)
    def RobotsHandler(*args): return _net_http_pywraphttpserver.HTTPServer_RobotsHandler(*args)
    def GenerateUsefulLinks(*args): return _net_http_pywraphttpserver.HTTPServer_GenerateUsefulLinks(*args)
    def set_data_version(*args): return _net_http_pywraphttpserver.HTTPServer_set_data_version(*args)
    def server_version(*args): return _net_http_pywraphttpserver.HTTPServer_server_version(*args)
    def set_server_type(*args): return _net_http_pywraphttpserver.HTTPServer_set_server_type(*args)
    def server_type(*args): return _net_http_pywraphttpserver.HTTPServer_server_type(*args)
    def options(*args): return _net_http_pywraphttpserver.HTTPServer_options(*args)
    def set_options(*args): return _net_http_pywraphttpserver.HTTPServer_set_options(*args)
    def selectserver(*args): return _net_http_pywraphttpserver.HTTPServer_selectserver(*args)
    def port(*args): return _net_http_pywraphttpserver.HTTPServer_port(*args)
    def set_port(*args): return _net_http_pywraphttpserver.HTTPServer_set_port(*args)
    def set_secure_port(*args): return _net_http_pywraphttpserver.HTTPServer_set_secure_port(*args)
    def udp_socket(*args): return _net_http_pywraphttpserver.HTTPServer_udp_socket(*args)
    def SetManager(*args): return _net_http_pywraphttpserver.HTTPServer_SetManager(*args)
    RPC_SWITCH_URL = _net_http_pywraphttpserver.cvar.HTTPServer_RPC_SWITCH_URL
    RPC_SECURITY_PROTOCOL = _net_http_pywraphttpserver.cvar.HTTPServer_RPC_SECURITY_PROTOCOL
    def SetMinSecurityLevel(*args): return _net_http_pywraphttpserver.HTTPServer_SetMinSecurityLevel(*args)
    def ssl_ctx(*args): return _net_http_pywraphttpserver.HTTPServer_ssl_ctx(*args)
    def ssl_level(*args): return _net_http_pywraphttpserver.HTTPServer_ssl_level(*args)
    def SetListenRetryCount(*args): return _net_http_pywraphttpserver.HTTPServer_SetListenRetryCount(*args)
    def StealTCPConnection(*args): return _net_http_pywraphttpserver.HTTPServer_StealTCPConnection(*args)
    def ProcessExternalRequest(*args): return _net_http_pywraphttpserver.HTTPServer_ProcessExternalRequest(*args)
    __swig_getmethods__["RegisterPlugin"] = lambda x: _net_http_pywraphttpserver.HTTPServer_RegisterPlugin
    if _newclass:RegisterPlugin = staticmethod(_net_http_pywraphttpserver.HTTPServer_RegisterPlugin)

class HTTPServerPtr(HTTPServer):
    def __init__(self, this):
        _swig_setattr(self, HTTPServer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServer, 'thisown', 0)
        _swig_setattr(self, HTTPServer,self.__class__,HTTPServer)
_net_http_pywraphttpserver.HTTPServer_swigregister(HTTPServerPtr)

HTTPServer_InitConnectionPolicy = _net_http_pywraphttpserver.HTTPServer_InitConnectionPolicy

HTTPServer_RegisterPlugin = _net_http_pywraphttpserver.HTTPServer_RegisterPlugin

class HTTPServerRequest(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerRequest, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerRequest, name)
    def __repr__(self):
        return "<C HTTPServerRequest instance at %s>" % (self.this,)
    def GetHeaderNames(*args): return _net_http_pywraphttpserver.HTTPServerRequest_GetHeaderNames(*args)
    def sender_ipaddress(*args): return _net_http_pywraphttpserver.HTTPServerRequest_sender_ipaddress(*args)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerRequest, 'this', _net_http_pywraphttpserver.new_HTTPServerRequest(*args))
        _swig_setattr(self, HTTPServerRequest, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerRequest):
        try:
            if self.thisown: destroy(self)
        except: pass
    def req_path(*args): return _net_http_pywraphttpserver.HTTPServerRequest_req_path(*args)
    def req_path_string(*args): return _net_http_pywraphttpserver.HTTPServerRequest_req_path_string(*args)
    def uri(*args): return _net_http_pywraphttpserver.HTTPServerRequest_uri(*args)
    def uri_as_str(*args): return _net_http_pywraphttpserver.HTTPServerRequest_uri_as_str(*args)
    def input(*args): return _net_http_pywraphttpserver.HTTPServerRequest_input(*args)
    def input_length(*args): return _net_http_pywraphttpserver.HTTPServerRequest_input_length(*args)
    def input_headers(*args): return _net_http_pywraphttpserver.HTTPServerRequest_input_headers(*args)
    def host_port(*args): return _net_http_pywraphttpserver.HTTPServerRequest_host_port(*args)
    def immediate_sender(*args): return _net_http_pywraphttpserver.HTTPServerRequest_immediate_sender(*args)
    def original_sender(*args): return _net_http_pywraphttpserver.HTTPServerRequest_original_sender(*args)
    def ipaddress(*args): return _net_http_pywraphttpserver.HTTPServerRequest_ipaddress(*args)
    def sender(*args): return _net_http_pywraphttpserver.HTTPServerRequest_sender(*args)
    def set_ipaddress(*args): return _net_http_pywraphttpserver.HTTPServerRequest_set_ipaddress(*args)
    def output(*args): return _net_http_pywraphttpserver.HTTPServerRequest_output(*args)
    def output_headers(*args): return _net_http_pywraphttpserver.HTTPServerRequest_output_headers(*args)
    def SetContentTypeHTML(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SetContentTypeHTML(*args)
    def SetContentTypeTEXT(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SetContentTypeTEXT(*args)
    def SetContentType(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SetContentType(*args)
    def SetNoStandardErrorMessage(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SetNoStandardErrorMessage(*args)
    def SetStandardErrorMessageExtraText(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SetStandardErrorMessageExtraText(*args)
    def used_chunking(*args): return _net_http_pywraphttpserver.HTTPServerRequest_used_chunking(*args)
    def sent_partial_reply(*args): return _net_http_pywraphttpserver.HTTPServerRequest_sent_partial_reply(*args)
    def DisableCompression(*args): return _net_http_pywraphttpserver.HTTPServerRequest_DisableCompression(*args)
    def WillUseCompression(*args): return _net_http_pywraphttpserver.HTTPServerRequest_WillUseCompression(*args)
    def WillClientUseCompression(*args): return _net_http_pywraphttpserver.HTTPServerRequest_WillClientUseCompression(*args)
    def MaybeShowCompressMessage(*args): return _net_http_pywraphttpserver.HTTPServerRequest_MaybeShowCompressMessage(*args)
    def ReplyWithStatus(*args): return _net_http_pywraphttpserver.HTTPServerRequest_ReplyWithStatus(*args)
    def Reply(*args): return _net_http_pywraphttpserver.HTTPServerRequest_Reply(*args)
    def SendPartialReply(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SendPartialReply(*args)
    def SendPartialReplyThreshold(*args): return _net_http_pywraphttpserver.HTTPServerRequest_SendPartialReplyThreshold(*args)
    def RequestClose(*args): return _net_http_pywraphttpserver.HTTPServerRequest_RequestClose(*args)
    def IsConnected(*args): return _net_http_pywraphttpserver.HTTPServerRequest_IsConnected(*args)
    def IsIdle(*args): return _net_http_pywraphttpserver.HTTPServerRequest_IsIdle(*args)
    def AbortRequest(*args): return _net_http_pywraphttpserver.HTTPServerRequest_AbortRequest(*args)
    def in_network_thread(*args): return _net_http_pywraphttpserver.HTTPServerRequest_in_network_thread(*args)
    def in_worker_thread(*args): return _net_http_pywraphttpserver.HTTPServerRequest_in_worker_thread(*args)
    def set_xml_mapper(*args): return _net_http_pywraphttpserver.HTTPServerRequest_set_xml_mapper(*args)
    def GenerateUsefulLinks(*args): return _net_http_pywraphttpserver.HTTPServerRequest_GenerateUsefulLinks(*args)
    def peer_role(*args): return _net_http_pywraphttpserver.HTTPServerRequest_peer_role(*args)
    def peer_host(*args): return _net_http_pywraphttpserver.HTTPServerRequest_peer_host(*args)
    def security_level(*args): return _net_http_pywraphttpserver.HTTPServerRequest_security_level(*args)
    def peer(*args): return _net_http_pywraphttpserver.HTTPServerRequest_peer(*args)
    def set_peer(*args): return _net_http_pywraphttpserver.HTTPServerRequest_set_peer(*args)
    def FillRequest(*args): return _net_http_pywraphttpserver.HTTPServerRequest_FillRequest(*args)
    def server(*args): return _net_http_pywraphttpserver.HTTPServerRequest_server(*args)
    def BytesWritten(*args): return _net_http_pywraphttpserver.HTTPServerRequest_BytesWritten(*args)
    def NumRequestBytes(*args): return _net_http_pywraphttpserver.HTTPServerRequest_NumRequestBytes(*args)

class HTTPServerRequestPtr(HTTPServerRequest):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerRequest, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerRequest, 'thisown', 0)
        _swig_setattr(self, HTTPServerRequest,self.__class__,HTTPServerRequest)
_net_http_pywraphttpserver.HTTPServerRequest_swigregister(HTTPServerRequestPtr)

class HTTPServerRequestThreadHandler(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerRequestThreadHandler, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerRequestThreadHandler, name)
    def __repr__(self):
        return "<C HTTPServerRequestThreadHandler instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'this', _net_http_pywraphttpserver.new_HTTPServerRequestThreadHandler(*args))
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerRequestThreadHandler):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Call(*args): return _net_http_pywraphttpserver.HTTPServerRequestThreadHandler_Call(*args)

class HTTPServerRequestThreadHandlerPtr(HTTPServerRequestThreadHandler):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerRequestThreadHandler, 'thisown', 0)
        _swig_setattr(self, HTTPServerRequestThreadHandler,self.__class__,HTTPServerRequestThreadHandler)
_net_http_pywraphttpserver.HTTPServerRequestThreadHandler_swigregister(HTTPServerRequestThreadHandlerPtr)

class HTTPServerHealthChecker(HTTPServerHealthCheckInterface):
    __swig_setmethods__ = {}
    for _s in [HTTPServerHealthCheckInterface]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerHealthChecker, name, value)
    __swig_getmethods__ = {}
    for _s in [HTTPServerHealthCheckInterface]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerHealthChecker, name)
    def __repr__(self):
        return "<C HTTPServerHealthChecker instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerHealthChecker, 'this', _net_http_pywraphttpserver.new_HTTPServerHealthChecker(*args))
        _swig_setattr(self, HTTPServerHealthChecker, 'thisown', 1)
    def __del__(self, destroy=_net_http_pywraphttpserver.delete_HTTPServerHealthChecker):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CanServeRequest(*args): return _net_http_pywraphttpserver.HTTPServerHealthChecker_CanServeRequest(*args)

class HTTPServerHealthCheckerPtr(HTTPServerHealthChecker):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerHealthChecker, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerHealthChecker, 'thisown', 0)
        _swig_setattr(self, HTTPServerHealthChecker,self.__class__,HTTPServerHealthChecker)
_net_http_pywraphttpserver.HTTPServerHealthChecker_swigregister(HTTPServerHealthCheckerPtr)

# An alias, since the full name is so very, very long.
NewPeriodicHealthChecker = HTTPServerHealthCheckInterface.NewPeriodicHealthChecker



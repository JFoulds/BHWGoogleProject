# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _googlebot_cookieserver_util_pywrapcookierule

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
        _swig_setattr(self, stringVector, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_googlebot_cookieserver_util_pywrapcookierule.stringVector_swigregister(stringVectorPtr)

class IOBuffer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, IOBuffer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, IOBuffer, name)
    def __repr__(self):
        return "<C IOBuffer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, IOBuffer, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_IOBuffer(*args))
        _swig_setattr(self, IOBuffer, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_IOBuffer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Swap(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Swap(*args)
    def AppendIOBuffer(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_AppendIOBuffer(*args)
    def AppendIOBufferNonDestructive(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_AppendIOBufferNonDestructive(*args)
    def AppendIOBufferN(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_AppendIOBufferN(*args)
    def AppendIOBufferNonDestructiveN(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_AppendIOBufferNonDestructiveN(*args)
    def AppendRawBlock(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_AppendRawBlock(*args)
    def Write(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Write(*args)
    def WriteUntil(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteUntil(*args)
    def WriteString(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteString(*args)
    def WriteInt(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteInt(*args)
    def WriteInt64(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteInt64(*args)
    def WriteFloat(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteFloat(*args)
    def WriteDouble(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteDouble(*args)
    def WriteShort(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteShort(*args)
    def WriteVarint32(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteVarint32(*args)
    def WriteVarint64(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteVarint64(*args)
    def Prepend(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Prepend(*args)
    def PrependUntil(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_PrependUntil(*args)
    def PrependString(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_PrependString(*args)
    def GrowPrependRegion(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_GrowPrependRegion(*args)
    def ReadToString(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadToString(*args)
    def ReadToStringN(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadToStringN(*args)
    def ReadVarint32(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadVarint32(*args)
    def ReadVarint64(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadVarint64(*args)
    def Unread(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Unread(*args)
    def Skip(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Skip(*args)
    def SetPin(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_SetPin(*args)
    def ClearPin(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ClearPin(*args)
    def UnreadToPin(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_UnreadToPin(*args)
    def is_pinned(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_is_pinned(*args)
    def PrefixMatch(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_PrefixMatch(*args)
    def SuffixMatch(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_SuffixMatch(*args)
    def TruncateToLength(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_TruncateToLength(*args)
    def WriteFD(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_WriteFD(*args)
    def ReadFDOld(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadFDOld(*args)
    def ReadFD(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadFD(*args)
    def Length(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Length(*args)
    def LengthAtLeast(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_LengthAtLeast(*args)
    def IsEmpty(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_IsEmpty(*args)
    def Clear(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Clear(*args)
    def Index(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Index(*args)
    def IndexN(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_IndexN(*args)
    def block_size(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_block_size(*args)
    def prepend_size(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_prepend_size(*args)
    def set_block_size(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_set_block_size(*args)
    def set_max_readfd_length(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_set_max_readfd_length(*args)
    def reset_max_readfd_length(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_reset_max_readfd_length(*args)
    def GetMaxReadLength(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_GetMaxReadLength(*args)
    def GetReadPosition(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_GetReadPosition(*args)
    def SetReadPosition(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_SetReadPosition(*args)
    def Buffer(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Buffer(*args)
    def CheckRep(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_CheckRep(*args)
    def Prefetch(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Prefetch(*args)
    def Read(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_Read(*args)
    def ReadAtMost(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadAtMost(*args)
    def ReadFast(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadFast(*args)
    def ReadUntil(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadUntil(*args)
    def ReadLine(*args): return _googlebot_cookieserver_util_pywrapcookierule.IOBuffer_ReadLine(*args)

class IOBufferPtr(IOBuffer):
    def __init__(self, this):
        _swig_setattr(self, IOBuffer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, IOBuffer, 'thisown', 0)
        _swig_setattr(self, IOBuffer,self.__class__,IOBuffer)
_googlebot_cookieserver_util_pywrapcookierule.IOBuffer_swigregister(IOBufferPtr)


Swap = _googlebot_cookieserver_util_pywrapcookierule.Swap
class Executor(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Executor, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Executor, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C thread::Executor instance at %s>" % (self.this,)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_Executor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Add(*args): return _googlebot_cookieserver_util_pywrapcookierule.Executor_Add(*args)
    def TryAdd(*args): return _googlebot_cookieserver_util_pywrapcookierule.Executor_TryAdd(*args)
    def AddIfReadyToRun(*args): return _googlebot_cookieserver_util_pywrapcookierule.Executor_AddIfReadyToRun(*args)
    def AddAfter(*args): return _googlebot_cookieserver_util_pywrapcookierule.Executor_AddAfter(*args)
    def num_pending_closures(*args): return _googlebot_cookieserver_util_pywrapcookierule.Executor_num_pending_closures(*args)
    __swig_getmethods__["DefaultExecutor"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.Executor_DefaultExecutor
    if _newclass:DefaultExecutor = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.Executor_DefaultExecutor)
    __swig_getmethods__["SetDefaultExecutor"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.Executor_SetDefaultExecutor
    if _newclass:SetDefaultExecutor = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.Executor_SetDefaultExecutor)
    __swig_getmethods__["CurrentExecutor"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutor
    if _newclass:CurrentExecutor = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutor)
    __swig_getmethods__["CurrentExecutorPointerInternal"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutorPointerInternal
    if _newclass:CurrentExecutorPointerInternal = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutorPointerInternal)

class ExecutorPtr(Executor):
    def __init__(self, this):
        _swig_setattr(self, Executor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Executor, 'thisown', 0)
        _swig_setattr(self, Executor,self.__class__,Executor)
_googlebot_cookieserver_util_pywrapcookierule.Executor_swigregister(ExecutorPtr)

Executor_DefaultExecutor = _googlebot_cookieserver_util_pywrapcookierule.Executor_DefaultExecutor

Executor_SetDefaultExecutor = _googlebot_cookieserver_util_pywrapcookierule.Executor_SetDefaultExecutor

Executor_CurrentExecutor = _googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutor

Executor_CurrentExecutorPointerInternal = _googlebot_cookieserver_util_pywrapcookierule.Executor_CurrentExecutorPointerInternal


NewInlineExecutor = _googlebot_cookieserver_util_pywrapcookierule.NewInlineExecutor

SingletonInlineExecutor = _googlebot_cookieserver_util_pywrapcookierule.SingletonInlineExecutor

NewSynchronizedInlineExecutor = _googlebot_cookieserver_util_pywrapcookierule.NewSynchronizedInlineExecutor
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
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_AbstractThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_SetThreadNamePrefix(*args)
    def StartWorkers(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_StartWorkers(*args)
    def num_pending_closures(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_num_pending_closures(*args)
    def SetWatchdogTimeout(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_watchdog_timeout(*args)
    def thread_options(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_thread_options(*args)
    def queue_count(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_queue_count(*args)
    def queue_capacity(*args): return _googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_queue_capacity(*args)

class AbstractThreadPoolPtr(AbstractThreadPool):
    def __init__(self, this):
        _swig_setattr(self, AbstractThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AbstractThreadPool, 'thisown', 0)
        _swig_setattr(self, AbstractThreadPool,self.__class__,AbstractThreadPool)
_googlebot_cookieserver_util_pywrapcookierule.AbstractThreadPool_swigregister(AbstractThreadPoolPtr)

class ThreadPool(AbstractThreadPool):
    __swig_setmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ThreadPool, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ThreadPool, name)
    def __repr__(self):
        return "<C ThreadPool instance at %s>" % (self.this,)
    kDefaultStackBytes = _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_kDefaultStackBytes
    def __init__(self, *args):
        _swig_setattr(self, ThreadPool, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_ThreadPool(*args))
        _swig_setattr(self, ThreadPool, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_ThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_SetThreadNamePrefix(*args)
    def SetWatchdogTimeout(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_watchdog_timeout(*args)
    def StartWorkers(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_StartWorkers(*args)
    def thread_options(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_thread_options(*args)
    def Add(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_Add(*args)
    def AddAfter(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_AddAfter(*args)
    def TryAdd(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_TryAdd(*args)
    def AddIfReadyToRun(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_AddIfReadyToRun(*args)
    def queue_count(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_queue_count(*args)
    def queue_capacity(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_queue_capacity(*args)
    def num_threads(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_num_threads(*args)
    def thread(*args): return _googlebot_cookieserver_util_pywrapcookierule.ThreadPool_thread(*args)

class ThreadPoolPtr(ThreadPool):
    def __init__(self, this):
        _swig_setattr(self, ThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ThreadPool, 'thisown', 0)
        _swig_setattr(self, ThreadPool,self.__class__,ThreadPool)
_googlebot_cookieserver_util_pywrapcookierule.ThreadPool_swigregister(ThreadPoolPtr)

SSL_OTHER = _googlebot_cookieserver_util_pywrapcookierule.SSL_OTHER
SSL_SECURITY_MIN = _googlebot_cookieserver_util_pywrapcookierule.SSL_SECURITY_MIN
SSL_NONE = _googlebot_cookieserver_util_pywrapcookierule.SSL_NONE
SSL_INTEGRITY = _googlebot_cookieserver_util_pywrapcookierule.SSL_INTEGRITY
SSL_PRIVACY_AND_INTEGRITY = _googlebot_cookieserver_util_pywrapcookierule.SSL_PRIVACY_AND_INTEGRITY
SSL_STRONG_PRIVACY_AND_INTEGRITY = _googlebot_cookieserver_util_pywrapcookierule.SSL_STRONG_PRIVACY_AND_INTEGRITY
SSL_SECURITY_MAX = _googlebot_cookieserver_util_pywrapcookierule.SSL_SECURITY_MAX

StringToSecurityLevel = _googlebot_cookieserver_util_pywrapcookierule.StringToSecurityLevel
class Peer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Peer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Peer, name)
    def __repr__(self):
        return "<C Peer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, Peer, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_Peer(*args))
        _swig_setattr(self, Peer, 'thisown', 1)
    def primary_role(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_primary_role(*args)
    def set_primary_role(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_primary_role(*args)
    def username(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_username(*args)
    def requested_role(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_requested_role(*args)
    def set_requested_role(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_requested_role(*args)
    def host(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_host(*args)
    def set_host(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_host(*args)
    def security_level(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_security_level(*args)
    def set_security_level(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_security_level(*args)
    def protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_protocol(*args)
    def set_protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_protocol(*args)
    def borgcell(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_borgcell(*args)
    def set_borgcell(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_borgcell(*args)
    def jobname_chosen_by_user(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_jobname_chosen_by_user(*args)
    def set_jobname_chosen_by_user(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_set_jobname_chosen_by_user(*args)
    def IsBorgJob(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_IsBorgJob(*args)
    def SetBorgJob(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_SetBorgJob(*args)
    def HasRole(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_HasRole(*args)
    def roles(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_roles(*args)
    def mutable_roles(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_mutable_roles(*args)
    def Ref(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_Ref(*args)
    def Unref(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_Unref(*args)
    def CopyFrom(*args): return _googlebot_cookieserver_util_pywrapcookierule.Peer_CopyFrom(*args)

class PeerPtr(Peer):
    def __init__(self, this):
        _swig_setattr(self, Peer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Peer, 'thisown', 0)
        _swig_setattr(self, Peer,self.__class__,Peer)
_googlebot_cookieserver_util_pywrapcookierule.Peer_swigregister(PeerPtr)


NewDummyPeer = _googlebot_cookieserver_util_pywrapcookierule.NewDummyPeer
NO_AUTHENTICATE_PEER = _googlebot_cookieserver_util_pywrapcookierule.NO_AUTHENTICATE_PEER
AUTHENTICATE_PEER = _googlebot_cookieserver_util_pywrapcookierule.AUTHENTICATE_PEER
OPTIONAL_AUTHENTICATE_PEER = _googlebot_cookieserver_util_pywrapcookierule.OPTIONAL_AUTHENTICATE_PEER
class HTTPResponse(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPResponse, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPResponse, name)
    def __repr__(self):
        return "<C HTTPResponse instance at %s>" % (self.this,)
    RC_UNDEFINED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_UNDEFINED
    RC_FIRST_CODE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_FIRST_CODE
    RC_CONTINUE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_CONTINUE
    RC_SWITCHING = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_SWITCHING
    RC_PROCESSING = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PROCESSING
    RC_REQUEST_OK = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_REQUEST_OK
    RC_CREATED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_CREATED
    RC_ACCEPTED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_ACCEPTED
    RC_PROVISIONAL = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PROVISIONAL
    RC_NO_CONTENT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_NO_CONTENT
    RC_RESET_CONTENT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RESET_CONTENT
    RC_PART_CONTENT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PART_CONTENT
    RC_MULTI_STATUS = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_MULTI_STATUS
    RC_RTSP_LOW_STORAGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_LOW_STORAGE
    RC_MULTIPLE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_MULTIPLE
    RC_MOVED_PERM = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_MOVED_PERM
    RC_MOVED_TEMP = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_MOVED_TEMP
    RC_SEE_OTHER = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_SEE_OTHER
    RC_NOT_MODIFIED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_NOT_MODIFIED
    RC_USE_PROXY = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_USE_PROXY
    RC_TEMP_REDIRECT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_TEMP_REDIRECT
    RC_BAD_REQUEST = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_BAD_REQUEST
    RC_UNAUTHORIZED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_UNAUTHORIZED
    RC_PAYMENT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PAYMENT
    RC_FORBIDDEN = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_FORBIDDEN
    RC_NOT_FOUND = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_NOT_FOUND
    RC_METHOD_NA = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_METHOD_NA
    RC_NONE_ACC = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_NONE_ACC
    RC_PROXY = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PROXY
    RC_REQUEST_TO = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_REQUEST_TO
    RC_CONFLICT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_CONFLICT
    RC_GONE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_GONE
    RC_LEN_REQUIRED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_LEN_REQUIRED
    RC_PRECOND_FAILED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_PRECOND_FAILED
    RC_ENTITY_TOO_BIG = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_ENTITY_TOO_BIG
    RC_URI_TOO_BIG = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_URI_TOO_BIG
    RC_UNKNOWN_MEDIA = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_UNKNOWN_MEDIA
    RC_BAD_RANGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_BAD_RANGE
    RC_BAD_EXPECTATION = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_BAD_EXPECTATION
    RC_UNPROC_ENTITY = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_UNPROC_ENTITY
    RC_LOCKED = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_LOCKED
    RC_FAILED_DEP = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_FAILED_DEP
    RC_RTSP_INVALID_PARAM = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_INVALID_PARAM
    RC_RTSP_ILLEGAL_CONF = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_ILLEGAL_CONF
    RC_RTSP_INSUF_BANDWIDTH = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_INSUF_BANDWIDTH
    RC_RTSP_UNKNOWN_SESSION = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_UNKNOWN_SESSION
    RC_RTSP_BAD_METHOD = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_METHOD
    RC_RTSP_BAD_HEADER = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_HEADER
    RC_RTSP_INVALID_RANGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_INVALID_RANGE
    RC_RTSP_READONLY_PARAM = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_READONLY_PARAM
    RC_RTSP_BAD_AGGREGATE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_AGGREGATE
    RC_RTSP_AGGREGATE_ONLY = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_AGGREGATE_ONLY
    RC_RTSP_BAD_TRANSPORT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_TRANSPORT
    RC_RTSP_BAD_DESTINATION = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_DESTINATION
    RC_ERROR = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_ERROR
    RC_NOT_IMP = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_NOT_IMP
    RC_BAD_GATEWAY = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_BAD_GATEWAY
    RC_SERVICE_UNAV = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_SERVICE_UNAV
    RC_GATEWAY_TO = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_GATEWAY_TO
    RC_BAD_VERSION = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_BAD_VERSION
    RC_INSUF_STORAGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_INSUF_STORAGE
    RC_RTSP_BAD_OPTION = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_RTSP_BAD_OPTION
    RC_LAST_CODE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_RC_LAST_CODE
    CC_NO_STORE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CC_NO_STORE
    CC_MUST_REVALIDATE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CC_MUST_REVALIDATE
    CC_PROXY_REVALIDATE = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CC_PROXY_REVALIDATE
    CC_GZIP_EMPTY_OK = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CC_GZIP_EMPTY_OK
    EXPIRES_OMIT = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_EXPIRES_OMIT
    EXPIRES_SHORTEN = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_EXPIRES_SHORTEN
    num_response_codes = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPResponse_num_response_codes
    num_cacheable_response_codes = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPResponse_num_cacheable_response_codes
    __swig_getmethods__["GetReasonPhrase"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_GetReasonPhrase
    if _newclass:GetReasonPhrase = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_GetReasonPhrase)
    __swig_getmethods__["AddStandardHeaders"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_AddStandardHeaders
    if _newclass:AddStandardHeaders = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_AddStandardHeaders)
    __swig_getmethods__["SetCacheablePublic"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePublic
    if _newclass:SetCacheablePublic = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePublic)
    __swig_getmethods__["SetCacheablePrivate"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivate
    if _newclass:SetCacheablePrivate = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivate)
    __swig_getmethods__["SetNotCacheable"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetNotCacheable
    if _newclass:SetNotCacheable = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetNotCacheable)
    __swig_getmethods__["SetCacheablePrivateIfNeeded"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivateIfNeeded
    if _newclass:SetCacheablePrivateIfNeeded = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivateIfNeeded)
    __swig_getmethods__["IsRedirectResponseCode"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsRedirectResponseCode
    if _newclass:IsRedirectResponseCode = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsRedirectResponseCode)
    __swig_getmethods__["IsCacheableResponseCode"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsCacheableResponseCode
    if _newclass:IsCacheableResponseCode = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsCacheableResponseCode)
    __swig_getmethods__["CreateErrorPage"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CreateErrorPage
    if _newclass:CreateErrorPage = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CreateErrorPage)
    def __init__(self, *args):
        _swig_setattr(self, HTTPResponse, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPResponse(*args))
        _swig_setattr(self, HTTPResponse, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPResponse):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPResponsePtr(HTTPResponse):
    def __init__(self, this):
        _swig_setattr(self, HTTPResponse, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPResponse, 'thisown', 0)
        _swig_setattr(self, HTTPResponse,self.__class__,HTTPResponse)
_googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_swigregister(HTTPResponsePtr)
cvar = _googlebot_cookieserver_util_pywrapcookierule.cvar

HTTPResponse_GetReasonPhrase = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_GetReasonPhrase

HTTPResponse_AddStandardHeaders = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_AddStandardHeaders

HTTPResponse_SetCacheablePublic = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePublic

HTTPResponse_SetCacheablePrivate = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivate

HTTPResponse_SetNotCacheable = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetNotCacheable

HTTPResponse_SetCacheablePrivateIfNeeded = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_SetCacheablePrivateIfNeeded

HTTPResponse_IsRedirectResponseCode = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsRedirectResponseCode

HTTPResponse_IsCacheableResponseCode = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_IsCacheableResponseCode

HTTPResponse_CreateErrorPage = _googlebot_cookieserver_util_pywrapcookierule.HTTPResponse_CreateErrorPage

class HTTPHeaders(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPHeaders, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPHeaders, name)
    def __repr__(self):
        return "<C HTTPHeaders instance at %s>" % (self.this,)
    ACCEPT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ACCEPT
    ACCEPT_CHARSET = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ACCEPT_CHARSET
    ACCEPT_ENCODING = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ACCEPT_ENCODING
    ACCEPT_LANGUAGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ACCEPT_LANGUAGE
    ACCEPT_RANGES = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ACCEPT_RANGES
    AGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_AGE
    AUTHORIZATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_AUTHORIZATION
    CACHE_CONTROL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CACHE_CONTROL
    CONNECTION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONNECTION
    CONTENT_DISPOSITION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_DISPOSITION
    CONTENT_ENCODING = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_ENCODING
    CONTENT_LANGUAGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_LANGUAGE
    CONTENT_LENGTH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_LENGTH
    CONTENT_LOCATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_LOCATION
    CONTENT_RANGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_RANGE
    CONTENT_TYPE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_CONTENT_TYPE
    COOKIE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_COOKIE
    DATE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_DATE
    DAV = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_DAV
    DEPTH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_DEPTH
    DESTINATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_DESTINATION
    ETAG = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_ETAG
    EXPECT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_EXPECT
    EXPIRES = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_EXPIRES
    FROM = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_FROM
    HOST = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_HOST
    IF = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF
    IF_MATCH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF_MATCH
    IF_MODIFIED_SINCE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF_MODIFIED_SINCE
    IF_NONE_MATCH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF_NONE_MATCH
    IF_RANGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF_RANGE
    IF_UNMODIFIED_SINCE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_IF_UNMODIFIED_SINCE
    KEEP_ALIVE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_KEEP_ALIVE
    LABEL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_LABEL
    LAST_MODIFIED = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_LAST_MODIFIED
    LOCATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_LOCATION
    LOCK_TOKEN = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_LOCK_TOKEN
    MS_AUTHOR_VIA = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_MS_AUTHOR_VIA
    OVERWRITE_HDR = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_OVERWRITE_HDR
    P3P = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_P3P
    PRAGMA = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_PRAGMA
    PROXY_CONNECTION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_PROXY_CONNECTION
    PROXY_AUTHENTICATE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_PROXY_AUTHENTICATE
    PROXY_AUTHORIZATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_PROXY_AUTHORIZATION
    RANGE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_RANGE
    REFERER = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_REFERER
    REFRESH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_REFRESH
    SERVER = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_SERVER
    SET_COOKIE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_SET_COOKIE
    STATUS_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_STATUS_URI
    TIMEOUT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TIMEOUT
    TRAILERS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TRAILERS
    TRANSFER_ENCODING = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TRANSFER_ENCODING
    TRANSFER_ENCODING_ABBRV = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TRANSFER_ENCODING_ABBRV
    UPGRADE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_UPGRADE
    USER_AGENT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_USER_AGENT
    VARY = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_VARY
    VIA = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_VIA
    WWW_AUTHENTICATE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_WWW_AUTHENTICATE
    X_FORWARDED_FOR = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_FORWARDED_FOR
    X_JPHONE_COPYRIGHT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_JPHONE_COPYRIGHT
    X_XRDS_LOCATION = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_XRDS_LOCATION
    X_PROXYUSER_IP = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_PROXYUSER_IP
    X_UP_SUBNO = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_UP_SUBNO
    XID = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_XID
    X_ROBOTS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_ROBOTS
    GZIP_CACHE_CONTROL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GZIP_CACHE_CONTROL
    GOOGLE_REQUEST_ID = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_REQUEST_ID
    GOOGLE_REQUEST_ID_ABBRV = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_REQUEST_ID_ABBRV
    GOOGLE_COMMAND = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_COMMAND
    GOOGLE_TOTAL_RECALL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_TOTAL_RECALL
    X_USER_IP = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_USER_IP
    X_CLIENT_IP = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_CLIENT_IP
    X_DONT_COUNT_ADS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_DONT_COUNT_ADS
    X_DONT_SHOW_ADS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_X_DONT_SHOW_ADS
    GSA_SUBJECT_DN = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GSA_SUBJECT_DN
    GSA_SUBJECT_GRPS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GSA_SUBJECT_GRPS
    GSA_CONNECTOR_USER_INFO = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GSA_CONNECTOR_USER_INFO
    GSA_SESSION_ID = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GSA_SESSION_ID
    GOOGLE_ATTACK = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_ATTACK
    GOOGLE_ISUNSAFE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_ISUNSAFE
    GOOGLE_BACKENDS = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_BACKENDS
    GOOGLE_DEBUG = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_DEBUG
    GOOGLE_PAYLOAD_LENGTH = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PAYLOAD_LENGTH
    GOOGLE_LOGENTRY = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_LOGENTRY
    GOOGLE_RETURN_WEBLOG_IN_HEADER = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_RETURN_WEBLOG_IN_HEADER
    GOOGLE_COUNTRY = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_COUNTRY
    GOOGLE_PROXY_IP = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PROXY_IP
    GOOGLE_PROXY_COUNTRY = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PROXY_COUNTRY
    GOOGLE_PROXY_RESTRICT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PROXY_RESTRICT
    GOOGLE_PROXY_ENCODING = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PROXY_ENCODING
    GOOGLE_PROXY_POST_ENCODING = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PROXY_POST_ENCODING
    GOOGLE_EXPERIMENT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_EXPERIMENT
    GOOGLE_LOGGING_RC = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_LOGGING_RC
    GOOGLE_EVENTID = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_EVENTID
    GOOGLE_PARTIAL_REPLIES_OFF = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PARTIAL_REPLIES_OFF
    GOOGLE_LOADTEST = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_LOADTEST
    GOOGLE_PRODUCTION_CONVERSION_EVENT = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_PRODUCTION_CONVERSION_EVENT
    GOOGLE_REQUEST_SOURCE = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_REQUEST_SOURCE
    GOOGLE_G_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_G_COMMAND_URI
    GOOGLE_T_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_T_COMMAND_URI
    GOOGLE_D_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_D_COMMAND_URI
    GOOGLE_H_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_H_COMMAND_URI
    GOOGLE_I_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_I_COMMAND_URI
    GOOGLE_M_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_M_COMMAND_URI
    GOOGLE_K_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_K_COMMAND_URI
    GOOGLE_P_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_P_COMMAND_URI
    GOOGLE_R_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_R_COMMAND_URI
    GOOGLE_U_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_U_COMMAND_URI
    GOOGLE_F_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_F_COMMAND_URI
    GOOGLE_B_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_B_COMMAND_URI
    GOOGLE_L_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_L_COMMAND_URI
    GOOGLE_X_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_X_COMMAND_URI
    GOOGLE_S_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_S_COMMAND_URI
    GOOGLE_O_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_O_COMMAND_URI
    GOOGLE_O2_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_O2_COMMAND_URI
    GOOGLE_O3_COMMAND_URI = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_O3_COMMAND_URI
    GOOGLE_DAPPER_TRACE_INFO = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_DAPPER_TRACE_INFO
    GOOGLE_NETMON_LABEL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_NETMON_LABEL
    GOOGLE_SUPPRESS_ERROR_BODY = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_GOOGLE_SUPPRESS_ERROR_BODY
    def __init__(self, *args):
        _swig_setattr(self, HTTPHeaders, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPHeaders(*args))
        _swig_setattr(self, HTTPHeaders, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPHeaders):
        try:
            if self.thisown: destroy(self)
        except: pass
    def ClearHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearHeaders(*args)
    def CopyHeader(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_CopyHeader(*args)
    def CopyFrom(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_CopyFrom(*args)
    def IsEmpty(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_IsEmpty(*args)
    TR_NO_ONEBOX = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TR_NO_ONEBOX
    TR_ONEBOX = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPHeaders_TR_ONEBOX
    UNUSED = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_UNUSED
    NO_OVERWRITE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_NO_OVERWRITE
    APPEND = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_APPEND
    OVERWRITE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_OVERWRITE
    def GetHeader(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetHeader(*args)
    def GetHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetHeaders(*args)
    def GetHeaderOr(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetHeaderOr(*args)
    def HeaderIs(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HeaderIs(*args)
    def HeaderStartsWith(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HeaderStartsWith(*args)
    def SetHeader(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_SetHeader(*args)
    def AddNewHeader(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_AddNewHeader(*args)
    def ClearHeader(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearHeader(*args)
    def ClearHeadersWithPrefix(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearHeadersWithPrefix(*args)
    def ClearGoogleHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearGoogleHeaders(*args)
    def ClearHopByHopHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearHopByHopHeaders(*args)
    def ClearSafeHopByHopHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ClearSafeHopByHopHeaders(*args)
    def firstline(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_firstline(*args)
    HTTP_ERROR = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_ERROR
    HTTP_OTHER = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_OTHER
    HTTP_ICY = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_ICY
    HTTP_09 = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_09
    HTTP_10 = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_10
    HTTP_11 = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_11
    HTTP_RTSP = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HTTP_RTSP
    def http_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_http_version(*args)
    def http_version_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_http_version_str(*args)
    def set_http_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_http_version(*args)
    PROTO_ERROR = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_ERROR
    PROTO_GET = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_GET
    PROTO_POST = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_POST
    PROTO_HEAD = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_HEAD
    PROTO_GOOGLE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_GOOGLE
    PROTO_PUT = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_PUT
    PROTO_DELETE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_DELETE
    PROTO_PROPFIND = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_PROPFIND
    PROTO_PROPPATCH = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_PROPPATCH
    PROTO_MKCOL = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MKCOL
    PROTO_COPY = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_COPY
    PROTO_MOVE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MOVE
    PROTO_LOCK = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_LOCK
    PROTO_UNLOCK = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_UNLOCK
    PROTO_TRACE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_TRACE
    PROTO_OPTIONS = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_OPTIONS
    PROTO_CONNECT = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_CONNECT
    PROTO_ICP_QUERY = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_ICP_QUERY
    PROTO_PURGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_PURGE
    PROTO_VERSION_CONTROL = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_VERSION_CONTROL
    PROTO_REPORT = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_REPORT
    PROTO_CHECKOUT = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_CHECKOUT
    PROTO_CHECKIN = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_CHECKIN
    PROTO_UNCHECKOUT = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_UNCHECKOUT
    PROTO_MKWORKSPACE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MKWORKSPACE
    PROTO_UPDATE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_UPDATE
    PROTO_LABEL = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_LABEL
    PROTO_MERGE = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MERGE
    PROTO_BASELINE_CONTROL = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_BASELINE_CONTROL
    PROTO_MKACTIVITY = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MKACTIVITY
    PROTO_ACL = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_ACL
    PROTO_MKCALENDAR = _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PROTO_MKCALENDAR
    def protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_protocol(*args)
    def protocol_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_protocol_str(*args)
    def set_protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_protocol(*args)
    def req_path(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_req_path(*args)
    def req_path_string(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_req_path_string(*args)
    def GetFirstlineRawUri(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetFirstlineRawUri(*args)
    def uri(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_uri(*args)
    def set_uri(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_uri(*args)
    def uri_as_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_uri_as_str(*args)
    def response_code(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_response_code(*args)
    def set_response_code(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_response_code(*args)
    def reason_phrase(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_reason_phrase(*args)
    def set_reason_phrase(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_reason_phrase(*args)
    def set_max_memory_allocated(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_set_max_memory_allocated(*args)
    def memory_allocated(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_memory_allocated(*args)
    def num_bytes_read_from_buffer(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_num_bytes_read_from_buffer(*args)
    def IsUsingTooMuchMemory(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_IsUsingTooMuchMemory(*args)
    def PrependHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_PrependHeaders(*args)
    def AppendAllHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_AppendAllHeaders(*args)
    def HeaderOrder(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_HeaderOrder(*args)
    def DebugString(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_DebugString(*args)
    def String(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_String(*args)
    def GetHostAndPort(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetHostAndPort(*args)
    def GetHostName(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_GetHostName(*args)
    def ForceRelativeURI(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ForceRelativeURI(*args)
    def ReadMoreInfo(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ReadMoreInfo(*args)
    def parse_error(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_parse_error(*args)
    def AddRequestFirstline(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_AddRequestFirstline(*args)
    def AddResponseFirstline(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_AddResponseFirstline(*args)
    def MakeRequestFirstLine(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_MakeRequestFirstLine(*args)
    def MakeQuickFirstLine(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_MakeQuickFirstLine(*args)
    def SetHeaderFromLine(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_SetHeaderFromLine(*args)
    def SetHeaderFromLines(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_SetHeaderFromLines(*args)
    def WriteHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_WriteHeaders(*args)
    def ParseContentTypeFromHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ParseContentTypeFromHeaders(*args)
    def ParseContentLanguageFromHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ParseContentLanguageFromHeaders(*args)
    def ParseContentDispositionFromHeaders(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_ParseContentDispositionFromHeaders(*args)
    def Swap(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_Swap(*args)

class HTTPHeadersPtr(HTTPHeaders):
    def __init__(self, this):
        _swig_setattr(self, HTTPHeaders, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPHeaders, 'thisown', 0)
        _swig_setattr(self, HTTPHeaders,self.__class__,HTTPHeaders)
_googlebot_cookieserver_util_pywrapcookierule.HTTPHeaders_swigregister(HTTPHeadersPtr)

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
        _swig_setattr(self, GnutellaHeaders, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_GnutellaHeaders(*args))
        _swig_setattr(self, GnutellaHeaders, 'thisown', 1)
    GNUTELLA_ERROR = _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_GNUTELLA_ERROR
    GNUTELLA_04 = _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_GNUTELLA_04
    GNUTELLA_06 = _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_GNUTELLA_06
    GNUTELLA_07 = _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_GNUTELLA_07
    def gnutella_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_version(*args)
    __swig_getmethods__["gnutella_version_str"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_version_str
    if _newclass:gnutella_version_str = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_version_str)
    def gnutella_version_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_version_str(*args)
    __swig_getmethods__["gnutella_connect_str"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_connect_str
    if _newclass:gnutella_connect_str = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_connect_str)
    def gnutella_connect_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_gnutella_connect_str(*args)
    def set_gnutella_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_set_gnutella_version(*args)
    def CopyFrom(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_CopyFrom(*args)
    def Swap(*args): return _googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_Swap(*args)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_GnutellaHeaders):
        try:
            if self.thisown: destroy(self)
        except: pass

class GnutellaHeadersPtr(GnutellaHeaders):
    def __init__(self, this):
        _swig_setattr(self, GnutellaHeaders, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, GnutellaHeaders, 'thisown', 0)
        _swig_setattr(self, GnutellaHeaders,self.__class__,GnutellaHeaders)
_googlebot_cookieserver_util_pywrapcookierule.GnutellaHeaders_swigregister(GnutellaHeadersPtr)
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
    __swig_getmethods__["ParseContentTypeFromMetaTag"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentTypeFromMetaTag
    if _newclass:ParseContentTypeFromMetaTag = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentTypeFromMetaTag)
    __swig_getmethods__["ParseContentLanguageFromMetaTag"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLanguageFromMetaTag
    if _newclass:ParseContentLanguageFromMetaTag = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLanguageFromMetaTag)
    __swig_getmethods__["ParseContentDisposition"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentDisposition
    if _newclass:ParseContentDisposition = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentDisposition)
    __swig_getmethods__["ExtractBody"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExtractBody
    if _newclass:ExtractBody = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExtractBody)
    __swig_getmethods__["ParseHTTPHeaders"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHTTPHeaders
    if _newclass:ParseHTTPHeaders = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHTTPHeaders)
    __swig_getmethods__["SkipHttpHeaders"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipHttpHeaders
    if _newclass:SkipHttpHeaders = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipHttpHeaders)
    __swig_getmethods__["ParseHostHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHostHeader
    if _newclass:ParseHostHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHostHeader)
    __swig_getmethods__["ParseContentLengthHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLengthHeader
    if _newclass:ParseContentLengthHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLengthHeader)
    __swig_getmethods__["ParseAuthMethods"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAuthMethods
    if _newclass:ParseAuthMethods = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAuthMethods)
    __swig_getmethods__["AuthMethodString"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AuthMethodString
    if _newclass:AuthMethodString = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AuthMethodString)
    __swig_getmethods__["SkipBadContent"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipBadContent
    if _newclass:SkipBadContent = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipBadContent)
    __swig_getmethods__["IsDocumentBad"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsDocumentBad
    if _newclass:IsDocumentBad = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsDocumentBad)
    __swig_getmethods__["IsContentGzipEncoded"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentGzipEncoded
    if _newclass:IsContentGzipEncoded = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentGzipEncoded)
    __swig_getmethods__["IsContentDeflateEncoded"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentDeflateEncoded
    if _newclass:IsContentDeflateEncoded = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentDeflateEncoded)
    __swig_getmethods__["IsResponseFirstline"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsResponseFirstline
    if _newclass:IsResponseFirstline = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsResponseFirstline)
    __swig_getmethods__["ParseHeaderField"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderField
    if _newclass:ParseHeaderField = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderField)
    __swig_getmethods__["ParseAbbreviatedGoogleID"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAbbreviatedGoogleID
    if _newclass:ParseAbbreviatedGoogleID = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAbbreviatedGoogleID)
    __swig_getmethods__["ParseXForwardedFor"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseXForwardedFor
    if _newclass:ParseXForwardedFor = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseXForwardedFor)
    __swig_getmethods__["ParseBasicAuthHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseBasicAuthHeader
    if _newclass:ParseBasicAuthHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseBasicAuthHeader)
    __swig_getmethods__["UpdateHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_UpdateHeader
    if _newclass:UpdateHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_UpdateHeader)
    __swig_getmethods__["HTTPTime"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HTTPTime
    if _newclass:HTTPTime = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HTTPTime)
    __swig_getmethods__["RobustHTTPTime"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_RobustHTTPTime
    if _newclass:RobustHTTPTime = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_RobustHTTPTime)
    __swig_getmethods__["ParseHeaderDirective"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirective
    if _newclass:ParseHeaderDirective = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirective)
    __swig_getmethods__["ParseHeaderDirectiveInt"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirectiveInt
    if _newclass:ParseHeaderDirectiveInt = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirectiveInt)
    __swig_getmethods__["ListHeaderDirectiveKeys"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ListHeaderDirectiveKeys
    if _newclass:ListHeaderDirectiveKeys = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ListHeaderDirectiveKeys)
    __swig_getmethods__["HasHeaderDirective"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HasHeaderDirective
    if _newclass:HasHeaderDirective = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HasHeaderDirective)
    __swig_getmethods__["DisableBrowserCaching"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_DisableBrowserCaching
    if _newclass:DisableBrowserCaching = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_DisableBrowserCaching)
    __swig_getmethods__["ParseCacheExpirationTimeFromHeaders"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseCacheExpirationTimeFromHeaders
    if _newclass:ParseCacheExpirationTimeFromHeaders = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseCacheExpirationTimeFromHeaders)
    __swig_getmethods__["AddGoogleRequestSourceHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AddGoogleRequestSourceHeader
    if _newclass:AddGoogleRequestSourceHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AddGoogleRequestSourceHeader)
    __swig_getmethods__["ParseUsernameAndProcessNameFromRequestSourceHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader
    if _newclass:ParseUsernameAndProcessNameFromRequestSourceHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader)
    __swig_getmethods__["EligibleForNotModified"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_EligibleForNotModified
    if _newclass:EligibleForNotModified = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_EligibleForNotModified)
    __swig_getmethods__["SetNetmonLabelHTTPHeader"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SetNetmonLabelHTTPHeader
    if _newclass:SetNetmonLabelHTTPHeader = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SetNetmonLabelHTTPHeader)
    __swig_getmethods__["ExpireCookieRecursively"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireCookieRecursively
    if _newclass:ExpireCookieRecursively = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireCookieRecursively)
    __swig_getmethods__["ExpireAllCookiesRecursively"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireAllCookiesRecursively
    if _newclass:ExpireAllCookiesRecursively = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireAllCookiesRecursively)
    __swig_getmethods__["IsValidHeaderOrder"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsValidHeaderOrder
    if _newclass:IsValidHeaderOrder = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsValidHeaderOrder)
    def __init__(self, *args):
        _swig_setattr(self, HTTPUtils, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPUtils(*args))
        _swig_setattr(self, HTTPUtils, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPUtils):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPUtilsPtr(HTTPUtils):
    def __init__(self, this):
        _swig_setattr(self, HTTPUtils, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPUtils, 'thisown', 0)
        _swig_setattr(self, HTTPUtils,self.__class__,HTTPUtils)
_googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_swigregister(HTTPUtilsPtr)

HTTPUtils_ParseContentTypeFromMetaTag = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentTypeFromMetaTag

HTTPUtils_ParseContentLanguageFromMetaTag = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLanguageFromMetaTag

HTTPUtils_ParseContentDisposition = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentDisposition

HTTPUtils_ExtractBody = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExtractBody

HTTPUtils_ParseHTTPHeaders = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHTTPHeaders

HTTPUtils_SkipHttpHeaders = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipHttpHeaders

HTTPUtils_ParseHostHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHostHeader

HTTPUtils_ParseContentLengthHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseContentLengthHeader

HTTPUtils_ParseAuthMethods = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAuthMethods

HTTPUtils_AuthMethodString = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AuthMethodString

HTTPUtils_SkipBadContent = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SkipBadContent

HTTPUtils_IsDocumentBad = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsDocumentBad

HTTPUtils_IsContentGzipEncoded = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentGzipEncoded

HTTPUtils_IsContentDeflateEncoded = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsContentDeflateEncoded

HTTPUtils_IsResponseFirstline = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsResponseFirstline

HTTPUtils_ParseHeaderField = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderField

HTTPUtils_ParseAbbreviatedGoogleID = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseAbbreviatedGoogleID

HTTPUtils_ParseXForwardedFor = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseXForwardedFor

HTTPUtils_ParseBasicAuthHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseBasicAuthHeader

HTTPUtils_UpdateHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_UpdateHeader

HTTPUtils_HTTPTime = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HTTPTime

HTTPUtils_RobustHTTPTime = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_RobustHTTPTime

HTTPUtils_ParseHeaderDirective = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirective

HTTPUtils_ParseHeaderDirectiveInt = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseHeaderDirectiveInt

HTTPUtils_ListHeaderDirectiveKeys = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ListHeaderDirectiveKeys

HTTPUtils_HasHeaderDirective = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_HasHeaderDirective

HTTPUtils_DisableBrowserCaching = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_DisableBrowserCaching

HTTPUtils_ParseCacheExpirationTimeFromHeaders = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseCacheExpirationTimeFromHeaders

HTTPUtils_AddGoogleRequestSourceHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_AddGoogleRequestSourceHeader

HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ParseUsernameAndProcessNameFromRequestSourceHeader

HTTPUtils_EligibleForNotModified = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_EligibleForNotModified

HTTPUtils_SetNetmonLabelHTTPHeader = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_SetNetmonLabelHTTPHeader

HTTPUtils_ExpireCookieRecursively = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireCookieRecursively

HTTPUtils_ExpireAllCookiesRecursively = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_ExpireAllCookiesRecursively

HTTPUtils_IsValidHeaderOrder = _googlebot_cookieserver_util_pywrapcookierule.HTTPUtils_IsValidHeaderOrder

class HTTPServerConnectionPolicy(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerConnectionPolicy, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerConnectionPolicy, name)
    def __repr__(self):
        return "<C HTTPServerConnectionPolicy instance at %s>" % (self.this,)
    __swig_setmethods__["read_timeout"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_read_timeout_set
    __swig_getmethods__["read_timeout"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_read_timeout_get
    if _newclass:read_timeout = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_read_timeout_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_read_timeout_set)
    __swig_setmethods__["write_timeout"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_write_timeout_set
    __swig_getmethods__["write_timeout"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_write_timeout_get
    if _newclass:write_timeout = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_write_timeout_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_write_timeout_set)
    __swig_setmethods__["max_requests"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_max_requests_set
    __swig_getmethods__["max_requests"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_max_requests_get
    if _newclass:max_requests = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_max_requests_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_max_requests_set)
    __swig_setmethods__["unlimited_url_length"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_unlimited_url_length_set
    __swig_getmethods__["unlimited_url_length"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_unlimited_url_length_get
    if _newclass:unlimited_url_length = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_unlimited_url_length_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_unlimited_url_length_set)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerConnectionPolicy, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServerConnectionPolicy(*args))
        _swig_setattr(self, HTTPServerConnectionPolicy, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerConnectionPolicy):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPServerConnectionPolicyPtr(HTTPServerConnectionPolicy):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerConnectionPolicy, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerConnectionPolicy, 'thisown', 0)
        _swig_setattr(self, HTTPServerConnectionPolicy,self.__class__,HTTPServerConnectionPolicy)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerConnectionPolicy_swigregister(HTTPServerConnectionPolicyPtr)

class HTTPServerHealthCheckInterface(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerHealthCheckInterface, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerHealthCheckInterface, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C HTTPServerHealthCheckInterface instance at %s>" % (self.this,)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerHealthCheckInterface):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CanServeRequest(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthCheckInterface_CanServeRequest(*args)
    __swig_getmethods__["NewPeriodicHealthChecker"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker
    if _newclass:NewPeriodicHealthChecker = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker)

class HTTPServerHealthCheckInterfacePtr(HTTPServerHealthCheckInterface):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerHealthCheckInterface, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerHealthCheckInterface, 'thisown', 0)
        _swig_setattr(self, HTTPServerHealthCheckInterface,self.__class__,HTTPServerHealthCheckInterface)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthCheckInterface_swigregister(HTTPServerHealthCheckInterfacePtr)

HTTPServerHealthCheckInterface_NewPeriodicHealthChecker = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthCheckInterface_NewPeriodicHealthChecker

class HTTPServerPlugin(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerPlugin, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerPlugin, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C HTTPServerPlugin instance at %s>" % (self.this,)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerPlugin):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Startup(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerPlugin_Startup(*args)
    def Shutdown(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerPlugin_Shutdown(*args)

class HTTPServerPluginPtr(HTTPServerPlugin):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerPlugin, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerPlugin, 'thisown', 0)
        _swig_setattr(self, HTTPServerPlugin,self.__class__,HTTPServerPlugin)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerPlugin_swigregister(HTTPServerPluginPtr)

class HTTPServerOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerOptions, name)
    def __repr__(self):
        return "<C HTTPServerOptions instance at %s>" % (self.this,)
    RPC_UNKNOWN = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_RPC_UNKNOWN
    RPC1 = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_RPC1
    RPC2 = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_RPC2
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerOptions, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServerOptions(*args))
        _swig_setattr(self, HTTPServerOptions, 'thisown', 1)
    __swig_setmethods__["rpc_version"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_rpc_version_set
    __swig_getmethods__["rpc_version"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_rpc_version_get
    if _newclass:rpc_version = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_rpc_version_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_rpc_version_set)
    __swig_setmethods__["event_manager"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_event_manager_set
    __swig_getmethods__["event_manager"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_event_manager_get
    if _newclass:event_manager = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_event_manager_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_event_manager_set)
    __swig_setmethods__["multithreaded_udp"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_multithreaded_udp_set
    __swig_getmethods__["multithreaded_udp"] = _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_multithreaded_udp_get
    if _newclass:multithreaded_udp = property(_googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_multithreaded_udp_get, _googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_multithreaded_udp_set)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class HTTPServerOptionsPtr(HTTPServerOptions):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerOptions, 'thisown', 0)
        _swig_setattr(self, HTTPServerOptions,self.__class__,HTTPServerOptions)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerOptions_swigregister(HTTPServerOptionsPtr)

class HTTPServer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServer, name)
    def __repr__(self):
        return "<C HTTPServer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServer, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServer(*args))
        _swig_setattr(self, HTTPServer, 'thisown', 1)
        
        
        
        
        
        
        self.ss = args[0]

    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServer):
        try:
            if self.thisown: destroy(self)
        except: pass
    CLIENT_TRUSTED = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_CLIENT_TRUSTED
    CLIENT_UNTRUSTED = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_CLIENT_UNTRUSTED
    def GetConnectionPolicy(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_GetConnectionPolicy(*args)
    __swig_getmethods__["InitConnectionPolicy"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_InitConnectionPolicy
    if _newclass:InitConnectionPolicy = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPServer_InitConnectionPolicy)
    def SetConnectionPolicy(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetConnectionPolicy(*args)
    def AcceptUDP(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_AcceptUDP(*args)
    def SetUDPBufferSizes(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetUDPBufferSizes(*args)
    def SetWindowSizesAndLatency(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetWindowSizesAndLatency(*args)
    def AlsoListenOnPort(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_AlsoListenOnPort(*args)
    def RegisterHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterHandler(*args)
    def RegisterSecureHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterSecureHandler(*args)
    def RegisterSecureRPCHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterSecureRPCHandler(*args)
    def RemoveHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RemoveHandler(*args)
    def GetRegisteredURIs(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_GetRegisteredURIs(*args)
    def GetRegisteredURIHandlers(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_GetRegisteredURIHandlers(*args)
    def RegisterApplication(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterApplication(*args)
    DISPATCH_BY_PATH = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_DISPATCH_BY_PATH
    DISPATCH_AS_PROXY = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_DISPATCH_AS_PROXY
    def set_dispatch_mode(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_dispatch_mode(*args)
    def RegisterSigTermHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterSigTermHandler(*args)
    def sigterm_handler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_sigterm_handler(*args)
    def Suspend(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_Suspend(*args)
    def Resume(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_Resume(*args)
    def suspended(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_suspended(*args)
    def SuspendAccepting(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SuspendAccepting(*args)
    def ResumeAccepting(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ResumeAccepting(*args)
    def SetExecutor(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetExecutor(*args)
    def SetDefaultExecutor(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetDefaultExecutor(*args)
    def SetThreadPool(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetThreadPool(*args)
    def SetSelectServer(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetSelectServer(*args)
    def IsTrustedClient(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_IsTrustedClient(*args)
    def SetTrustedClients(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetTrustedClients(*args)
    def MakePublic(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_MakePublic(*args)
    def MakePrivate(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_MakePrivate(*args)
    def SetUncompressInput(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetUncompressInput(*args)
    def SetCompressOutput(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetCompressOutput(*args)
    def QuitHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_QuitHandler(*args)
    def AbortHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_AbortHandler(*args)
    def PassthruHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_PassthruHandler(*args)
    def VarzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_VarzHandler(*args)
    def VarzDocHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_VarzDocHandler(*args)
    def HealthzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_HealthzHandler(*args)
    def ProfilezHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ProfilezHandler(*args)
    def StatuszHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_StatuszHandler(*args)
    def FormlistHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_FormlistHandler(*args)
    def ThreadzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ThreadzHandler(*args)
    def SymbolzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SymbolzHandler(*args)
    def ContentionzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ContentionzHandler(*args)
    def HeapzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_HeapzHandler(*args)
    def GrowthzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_GrowthzHandler(*args)
    def ProczHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ProczHandler(*args)
    def RequestzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RequestzHandler(*args)
    def TracezHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_TracezHandler(*args)
    def StyleHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_StyleHandler(*args)
    def EventLogHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_EventLogHandler(*args)
    def HelpzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_HelpzHandler(*args)
    def FlushLogzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_FlushLogzHandler(*args)
    def ShowEventLogPage(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ShowEventLogPage(*args)
    def PrintEventLog(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_PrintEventLog(*args)
    def NullHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_NullHandler(*args)
    def VHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_VHandler(*args)
    def AHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_AHandler(*args)
    def PortmapzHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_PortmapzHandler(*args)
    def SetHealthCheck(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetHealthCheck(*args)
    def RobotsHandler(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RobotsHandler(*args)
    def GenerateUsefulLinks(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_GenerateUsefulLinks(*args)
    def set_data_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_data_version(*args)
    def server_version(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_server_version(*args)
    def set_server_type(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_server_type(*args)
    def server_type(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_server_type(*args)
    def options(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_options(*args)
    def set_options(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_options(*args)
    def selectserver(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_selectserver(*args)
    def port(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_port(*args)
    def set_port(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_port(*args)
    def set_secure_port(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_set_secure_port(*args)
    def udp_socket(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_udp_socket(*args)
    def SetManager(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetManager(*args)
    RPC_SWITCH_URL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPServer_RPC_SWITCH_URL
    RPC_SECURITY_PROTOCOL = _googlebot_cookieserver_util_pywrapcookierule.cvar.HTTPServer_RPC_SECURITY_PROTOCOL
    def SetMinSecurityLevel(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetMinSecurityLevel(*args)
    def ssl_ctx(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ssl_ctx(*args)
    def ssl_level(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ssl_level(*args)
    def SetListenRetryCount(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_SetListenRetryCount(*args)
    def StealTCPConnection(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_StealTCPConnection(*args)
    def ProcessExternalRequest(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_ProcessExternalRequest(*args)
    __swig_getmethods__["RegisterPlugin"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterPlugin
    if _newclass:RegisterPlugin = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterPlugin)

class HTTPServerPtr(HTTPServer):
    def __init__(self, this):
        _swig_setattr(self, HTTPServer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServer, 'thisown', 0)
        _swig_setattr(self, HTTPServer,self.__class__,HTTPServer)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServer_swigregister(HTTPServerPtr)

HTTPServer_InitConnectionPolicy = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_InitConnectionPolicy

HTTPServer_RegisterPlugin = _googlebot_cookieserver_util_pywrapcookierule.HTTPServer_RegisterPlugin

class HTTPServerRequest(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerRequest, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerRequest, name)
    def __repr__(self):
        return "<C HTTPServerRequest instance at %s>" % (self.this,)
    def GetHeaderNames(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_GetHeaderNames(*args)
    def sender_ipaddress(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_sender_ipaddress(*args)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerRequest, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServerRequest(*args))
        _swig_setattr(self, HTTPServerRequest, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerRequest):
        try:
            if self.thisown: destroy(self)
        except: pass
    def req_path(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_req_path(*args)
    def req_path_string(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_req_path_string(*args)
    def uri(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_uri(*args)
    def uri_as_str(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_uri_as_str(*args)
    def input(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_input(*args)
    def input_length(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_input_length(*args)
    def input_headers(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_input_headers(*args)
    def host_port(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_host_port(*args)
    def immediate_sender(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_immediate_sender(*args)
    def original_sender(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_original_sender(*args)
    def ipaddress(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_ipaddress(*args)
    def sender(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_sender(*args)
    def set_ipaddress(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_set_ipaddress(*args)
    def output(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_output(*args)
    def output_headers(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_output_headers(*args)
    def SetContentTypeHTML(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SetContentTypeHTML(*args)
    def SetContentTypeTEXT(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SetContentTypeTEXT(*args)
    def SetContentType(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SetContentType(*args)
    def SetNoStandardErrorMessage(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SetNoStandardErrorMessage(*args)
    def SetStandardErrorMessageExtraText(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SetStandardErrorMessageExtraText(*args)
    def used_chunking(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_used_chunking(*args)
    def sent_partial_reply(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_sent_partial_reply(*args)
    def DisableCompression(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_DisableCompression(*args)
    def WillUseCompression(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_WillUseCompression(*args)
    def WillClientUseCompression(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_WillClientUseCompression(*args)
    def MaybeShowCompressMessage(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_MaybeShowCompressMessage(*args)
    def ReplyWithStatus(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_ReplyWithStatus(*args)
    def Reply(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_Reply(*args)
    def SendPartialReply(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SendPartialReply(*args)
    def SendPartialReplyThreshold(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_SendPartialReplyThreshold(*args)
    def RequestClose(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_RequestClose(*args)
    def IsConnected(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_IsConnected(*args)
    def IsIdle(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_IsIdle(*args)
    def AbortRequest(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_AbortRequest(*args)
    def in_network_thread(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_in_network_thread(*args)
    def in_worker_thread(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_in_worker_thread(*args)
    def set_xml_mapper(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_set_xml_mapper(*args)
    def GenerateUsefulLinks(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_GenerateUsefulLinks(*args)
    def peer_role(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_peer_role(*args)
    def peer_host(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_peer_host(*args)
    def security_level(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_security_level(*args)
    def peer(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_peer(*args)
    def set_peer(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_set_peer(*args)
    def FillRequest(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_FillRequest(*args)
    def server(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_server(*args)
    def BytesWritten(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_BytesWritten(*args)
    def NumRequestBytes(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_NumRequestBytes(*args)

class HTTPServerRequestPtr(HTTPServerRequest):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerRequest, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerRequest, 'thisown', 0)
        _swig_setattr(self, HTTPServerRequest,self.__class__,HTTPServerRequest)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequest_swigregister(HTTPServerRequestPtr)

class HTTPServerRequestThreadHandler(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, HTTPServerRequestThreadHandler, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, HTTPServerRequestThreadHandler, name)
    def __repr__(self):
        return "<C HTTPServerRequestThreadHandler instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServerRequestThreadHandler(*args))
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerRequestThreadHandler):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Call(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequestThreadHandler_Call(*args)

class HTTPServerRequestThreadHandlerPtr(HTTPServerRequestThreadHandler):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerRequestThreadHandler, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerRequestThreadHandler, 'thisown', 0)
        _swig_setattr(self, HTTPServerRequestThreadHandler,self.__class__,HTTPServerRequestThreadHandler)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerRequestThreadHandler_swigregister(HTTPServerRequestThreadHandlerPtr)

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
        _swig_setattr(self, HTTPServerHealthChecker, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_HTTPServerHealthChecker(*args))
        _swig_setattr(self, HTTPServerHealthChecker, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_HTTPServerHealthChecker):
        try:
            if self.thisown: destroy(self)
        except: pass
    def CanServeRequest(*args): return _googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthChecker_CanServeRequest(*args)

class HTTPServerHealthCheckerPtr(HTTPServerHealthChecker):
    def __init__(self, this):
        _swig_setattr(self, HTTPServerHealthChecker, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, HTTPServerHealthChecker, 'thisown', 0)
        _swig_setattr(self, HTTPServerHealthChecker,self.__class__,HTTPServerHealthChecker)
_googlebot_cookieserver_util_pywrapcookierule.HTTPServerHealthChecker_swigregister(HTTPServerHealthCheckerPtr)

# An alias, since the full name is so very, very long.
NewPeriodicHealthChecker = HTTPServerHealthCheckInterface.NewPeriodicHealthChecker

class ProtocolFlags(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolFlags, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolFlags, name)
    def __repr__(self):
        return "<C ProtocolFlags instance at %s>" % (self.this,)
    __swig_setmethods__["uses_login"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_login_set
    __swig_getmethods__["uses_login"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_login_get
    if _newclass:uses_login = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_login_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_login_set)
    __swig_setmethods__["uses_relative"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_relative_set
    __swig_getmethods__["uses_relative"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_relative_get
    if _newclass:uses_relative = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_relative_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_relative_set)
    __swig_setmethods__["uses_netloc"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_netloc_set
    __swig_getmethods__["uses_netloc"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_netloc_get
    if _newclass:uses_netloc = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_netloc_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_netloc_set)
    __swig_setmethods__["allow_empty_host"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_allow_empty_host_set
    __swig_getmethods__["allow_empty_host"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_allow_empty_host_get
    if _newclass:allow_empty_host = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_allow_empty_host_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_allow_empty_host_set)
    __swig_setmethods__["non_hierarchical"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_non_hierarchical_set
    __swig_getmethods__["non_hierarchical"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_non_hierarchical_get
    if _newclass:non_hierarchical = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_non_hierarchical_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_non_hierarchical_set)
    __swig_setmethods__["uses_params"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_params_set
    __swig_getmethods__["uses_params"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_params_get
    if _newclass:uses_params = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_params_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_params_set)
    __swig_setmethods__["uses_query"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_query_set
    __swig_getmethods__["uses_query"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_query_get
    if _newclass:uses_query = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_query_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_query_set)
    __swig_setmethods__["uses_fragment"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_fragment_set
    __swig_getmethods__["uses_fragment"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_fragment_get
    if _newclass:uses_fragment = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_fragment_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_uses_fragment_set)
    __swig_setmethods__["default_port"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_default_port_set
    __swig_getmethods__["default_port"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_default_port_get
    if _newclass:default_port = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_default_port_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_default_port_set)
    __swig_setmethods__["protocol"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_protocol_set
    __swig_getmethods__["protocol"] = _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_protocol_get
    if _newclass:protocol = property(_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_protocol_get, _googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_protocol_set)
    def __init__(self, *args):
        _swig_setattr(self, ProtocolFlags, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_ProtocolFlags(*args))
        _swig_setattr(self, ProtocolFlags, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_ProtocolFlags):
        try:
            if self.thisown: destroy(self)
        except: pass

class ProtocolFlagsPtr(ProtocolFlags):
    def __init__(self, this):
        _swig_setattr(self, ProtocolFlags, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolFlags, 'thisown', 0)
        _swig_setattr(self, ProtocolFlags,self.__class__,ProtocolFlags)
_googlebot_cookieserver_util_pywrapcookierule.ProtocolFlags_swigregister(ProtocolFlagsPtr)

class URL(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, URL, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, URL, name)
    def __repr__(self):
        return "<C URL instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, URL, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_URL(*args))
        _swig_setattr(self, URL, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_URL):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetComponents(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetComponents(*args)
    def Parse(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_Parse(*args)
    def ParseWithLen(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_ParseWithLen(*args)
    def Assemble(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_Assemble(*args)
    def PathParamsQuery(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_PathParamsQuery(*args)
    def is_valid(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_is_valid(*args)
    def QueryComponents(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_QueryComponents(*args)
    def HostnameIsPunycode(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_HostnameIsPunycode(*args)
    def HostnameIsUnicode(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_HostnameIsUnicode(*args)
    def HostnameToPunycode(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_HostnameToPunycode(*args)
    def HostnameToUnicode(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_HostnameToUnicode(*args)
    def LightlyCanonicalizeAndVerify(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_LightlyCanonicalizeAndVerify(*args)
    def GetNthQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_GetNthQueryComponent(*args)
    def GetQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_GetQueryComponent(*args)
    def GetQueryComponentDefault(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_GetQueryComponentDefault(*args)
    def GetIntQueryComponentDefault(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_GetIntQueryComponentDefault(*args)
    def AddQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_AddQueryComponent(*args)
    def AddIntQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_AddIntQueryComponent(*args)
    def DeleteNthQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_DeleteNthQueryComponent(*args)
    def DeleteQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_DeleteQueryComponent(*args)
    def DeleteAllQueryComponents(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_DeleteAllQueryComponents(*args)
    def SetNthQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetNthQueryComponent(*args)
    def SetQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetQueryComponent(*args)
    def SetNthQueryComponentEscaped(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetNthQueryComponentEscaped(*args)
    def SetQueryComponentEscaped(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetQueryComponentEscaped(*args)
    def SetIntQueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetIntQueryComponent(*args)
    def SetInt64QueryComponent(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_SetInt64QueryComponent(*args)
    __swig_getmethods__["IsLegalHostname"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_IsLegalHostname
    if _newclass:IsLegalHostname = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_IsLegalHostname)
    __swig_getmethods__["NComponentSuffix"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_NComponentSuffix
    if _newclass:NComponentSuffix = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_NComponentSuffix)
    def IsLikelyInfiniteSpace(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_IsLikelyInfiniteSpace(*args)
    def Fingerprint(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_Fingerprint(*args)
    def HostFingerprint(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_HostFingerprint(*args)
    def DomainFingerprint(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_DomainFingerprint(*args)
    __swig_getmethods__["FastHostName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastHostName
    if _newclass:FastHostName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastHostName)
    __swig_getmethods__["FastHostName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastHostName
    if _newclass:FastHostName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastHostName)
    __swig_getmethods__["FastDomainName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastDomainName
    if _newclass:FastDomainName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastDomainName)
    __swig_getmethods__["FastDomainName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastDomainName
    if _newclass:FastDomainName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastDomainName)
    __swig_getmethods__["FastOrgName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastOrgName
    if _newclass:FastOrgName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastOrgName)
    __swig_getmethods__["FastOrgName"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_FastOrgName
    if _newclass:FastOrgName = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_FastOrgName)
    def IsHomePage(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_IsHomePage(*args)
    def protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_protocol(*args)
    def login(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_login(*args)
    def host(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_host(*args)
    def domain(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_domain(*args)
    def port(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_port(*args)
    def default_port(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_default_port(*args)
    def path(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_path(*args)
    def params(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_params(*args)
    def query(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_query(*args)
    def extension(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_extension(*args)
    def fragment(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_fragment(*args)
    def set_protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_protocol(*args)
    def set_host(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_host(*args)
    def set_port(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_port(*args)
    def set_path(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_path(*args)
    def set_params(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_params(*args)
    def set_query(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_query(*args)
    def set_fragment(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_fragment(*args)
    def set_login(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_set_login(*args)
    def CanonicalizePath(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_CanonicalizePath(*args)
    def NormalizePath(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_NormalizePath(*args)
    __swig_getmethods__["Escape"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_Escape
    if _newclass:Escape = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_Escape)
    __swig_getmethods__["Unescape"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_Unescape
    if _newclass:Unescape = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_Unescape)
    __swig_getmethods__["RegisterCustomProtocol"] = lambda x: _googlebot_cookieserver_util_pywrapcookierule.URL_RegisterCustomProtocol
    if _newclass:RegisterCustomProtocol = staticmethod(_googlebot_cookieserver_util_pywrapcookierule.URL_RegisterCustomProtocol)
    def MakeDomainNameAbsolute(*args): return _googlebot_cookieserver_util_pywrapcookierule.URL_MakeDomainNameAbsolute(*args)

class URLPtr(URL):
    def __init__(self, this):
        _swig_setattr(self, URL, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, URL, 'thisown', 0)
        _swig_setattr(self, URL,self.__class__,URL)
_googlebot_cookieserver_util_pywrapcookierule.URL_swigregister(URLPtr)

URL_IsLegalHostname = _googlebot_cookieserver_util_pywrapcookierule.URL_IsLegalHostname

URL_NComponentSuffix = _googlebot_cookieserver_util_pywrapcookierule.URL_NComponentSuffix

URL_FastHostName = _googlebot_cookieserver_util_pywrapcookierule.URL_FastHostName

URL_FastDomainName = _googlebot_cookieserver_util_pywrapcookierule.URL_FastDomainName

URL_FastOrgName = _googlebot_cookieserver_util_pywrapcookierule.URL_FastOrgName

URL_Escape = _googlebot_cookieserver_util_pywrapcookierule.URL_Escape

URL_Unescape = _googlebot_cookieserver_util_pywrapcookierule.URL_Unescape

URL_RegisterCustomProtocol = _googlebot_cookieserver_util_pywrapcookierule.URL_RegisterCustomProtocol

class CookieAction(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CookieAction, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CookieAction, name)
    def __repr__(self):
        return "<C CookieAction instance at %s>" % (self.this,)
    HIDDEN_ATTR_PREFIX = _googlebot_cookieserver_util_pywrapcookierule.cvar.CookieAction_HIDDEN_ATTR_PREFIX
    PASSWD_ATTR_PREFIX = _googlebot_cookieserver_util_pywrapcookierule.cvar.CookieAction_PASSWD_ATTR_PREFIX
    NO_ATTR_PREFIX = _googlebot_cookieserver_util_pywrapcookierule.cvar.CookieAction_NO_ATTR_PREFIX
    def __init__(self, *args):
        _swig_setattr(self, CookieAction, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_CookieAction(*args))
        _swig_setattr(self, CookieAction, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_CookieAction):
        try:
            if self.thisown: destroy(self)
        except: pass
    def url(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_url(*args)
    def attr(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_attr(*args)
    def value(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_value(*args)
    def type(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_type(*args)
    def protocol(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_protocol(*args)
    def GetNumAVPairs(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_GetNumAVPairs(*args)
    def GetRequestURL(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_GetRequestURL(*args)
    def GetRequestContent(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieAction_GetRequestContent(*args)

class CookieActionPtr(CookieAction):
    def __init__(self, this):
        _swig_setattr(self, CookieAction, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, CookieAction, 'thisown', 0)
        _swig_setattr(self, CookieAction,self.__class__,CookieAction)
_googlebot_cookieserver_util_pywrapcookierule.CookieAction_swigregister(CookieActionPtr)

class CookieRule(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CookieRule, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CookieRule, name)
    def __repr__(self):
        return "<C CookieRule instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, CookieRule, 'this', _googlebot_cookieserver_util_pywrapcookierule.new_CookieRule(*args))
        _swig_setattr(self, CookieRule, 'thisown', 1)
    def __del__(self, destroy=_googlebot_cookieserver_util_pywrapcookierule.delete_CookieRule):
        try:
            if self.thisown: destroy(self)
        except: pass
    def ParseFromStream(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_ParseFromStream(*args)
    def ParseFromString(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_ParseFromString(*args)
    def action(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_action(*args)
    def expiration(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_expiration(*args)
    def GetNumNames(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_GetNumNames(*args)
    def NamesBeginIterator(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_NamesBeginIterator(*args)
    def NamesEndIterator(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_NamesEndIterator(*args)
    def ClearNames(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_ClearNames(*args)
    def AddName(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_AddName(*args)
    def HasName(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_HasName(*args)
    def KnowRequiredCookieNames(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_KnowRequiredCookieNames(*args)
    def SetKnowRequiredCookieNames(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_SetKnowRequiredCookieNames(*args)
    def GetNumActions(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_GetNumActions(*args)
    def fetcher(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_fetcher(*args)
    def set_fetcher(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_set_fetcher(*args)
    def GetURLContent(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_GetURLContent(*args)
    def SetURLContent(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_SetURLContent(*args)
    def ContainsActionWithURL(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_ContainsActionWithURL(*args)
    def HasLastActionURL(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_HasLastActionURL(*args)
    def GetCookieJar(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_GetCookieJar(*args)
    def GetCookies(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_GetCookies(*args)
    def isPublic(*args): return _googlebot_cookieserver_util_pywrapcookierule.CookieRule_isPublic(*args)

class CookieRulePtr(CookieRule):
    def __init__(self, this):
        _swig_setattr(self, CookieRule, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, CookieRule, 'thisown', 0)
        _swig_setattr(self, CookieRule,self.__class__,CookieRule)
_googlebot_cookieserver_util_pywrapcookierule.CookieRule_swigregister(CookieRulePtr)



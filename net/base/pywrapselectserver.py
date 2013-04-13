# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _net_base_pywrapselectserver

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
        _swig_setattr(self, stringVector, 'this', _net_base_pywrapselectserver.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_net_base_pywrapselectserver.stringVector_swigregister(stringVectorPtr)

class Executor(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Executor, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Executor, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C thread::Executor instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_Executor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Add(*args): return _net_base_pywrapselectserver.Executor_Add(*args)
    def TryAdd(*args): return _net_base_pywrapselectserver.Executor_TryAdd(*args)
    def AddIfReadyToRun(*args): return _net_base_pywrapselectserver.Executor_AddIfReadyToRun(*args)
    def AddAfter(*args): return _net_base_pywrapselectserver.Executor_AddAfter(*args)
    def num_pending_closures(*args): return _net_base_pywrapselectserver.Executor_num_pending_closures(*args)
    __swig_getmethods__["DefaultExecutor"] = lambda x: _net_base_pywrapselectserver.Executor_DefaultExecutor
    if _newclass:DefaultExecutor = staticmethod(_net_base_pywrapselectserver.Executor_DefaultExecutor)
    __swig_getmethods__["SetDefaultExecutor"] = lambda x: _net_base_pywrapselectserver.Executor_SetDefaultExecutor
    if _newclass:SetDefaultExecutor = staticmethod(_net_base_pywrapselectserver.Executor_SetDefaultExecutor)
    __swig_getmethods__["CurrentExecutor"] = lambda x: _net_base_pywrapselectserver.Executor_CurrentExecutor
    if _newclass:CurrentExecutor = staticmethod(_net_base_pywrapselectserver.Executor_CurrentExecutor)
    __swig_getmethods__["CurrentExecutorPointerInternal"] = lambda x: _net_base_pywrapselectserver.Executor_CurrentExecutorPointerInternal
    if _newclass:CurrentExecutorPointerInternal = staticmethod(_net_base_pywrapselectserver.Executor_CurrentExecutorPointerInternal)

class ExecutorPtr(Executor):
    def __init__(self, this):
        _swig_setattr(self, Executor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Executor, 'thisown', 0)
        _swig_setattr(self, Executor,self.__class__,Executor)
_net_base_pywrapselectserver.Executor_swigregister(ExecutorPtr)

Executor_DefaultExecutor = _net_base_pywrapselectserver.Executor_DefaultExecutor

Executor_SetDefaultExecutor = _net_base_pywrapselectserver.Executor_SetDefaultExecutor

Executor_CurrentExecutor = _net_base_pywrapselectserver.Executor_CurrentExecutor

Executor_CurrentExecutorPointerInternal = _net_base_pywrapselectserver.Executor_CurrentExecutorPointerInternal


NewInlineExecutor = _net_base_pywrapselectserver.NewInlineExecutor

SingletonInlineExecutor = _net_base_pywrapselectserver.SingletonInlineExecutor

NewSynchronizedInlineExecutor = _net_base_pywrapselectserver.NewSynchronizedInlineExecutor
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
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_AbstractThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _net_base_pywrapselectserver.AbstractThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _net_base_pywrapselectserver.AbstractThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _net_base_pywrapselectserver.AbstractThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _net_base_pywrapselectserver.AbstractThreadPool_SetThreadNamePrefix(*args)
    def StartWorkers(*args): return _net_base_pywrapselectserver.AbstractThreadPool_StartWorkers(*args)
    def num_pending_closures(*args): return _net_base_pywrapselectserver.AbstractThreadPool_num_pending_closures(*args)
    def SetWatchdogTimeout(*args): return _net_base_pywrapselectserver.AbstractThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _net_base_pywrapselectserver.AbstractThreadPool_watchdog_timeout(*args)
    def thread_options(*args): return _net_base_pywrapselectserver.AbstractThreadPool_thread_options(*args)
    def queue_count(*args): return _net_base_pywrapselectserver.AbstractThreadPool_queue_count(*args)
    def queue_capacity(*args): return _net_base_pywrapselectserver.AbstractThreadPool_queue_capacity(*args)

class AbstractThreadPoolPtr(AbstractThreadPool):
    def __init__(self, this):
        _swig_setattr(self, AbstractThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AbstractThreadPool, 'thisown', 0)
        _swig_setattr(self, AbstractThreadPool,self.__class__,AbstractThreadPool)
_net_base_pywrapselectserver.AbstractThreadPool_swigregister(AbstractThreadPoolPtr)

class ThreadPool(AbstractThreadPool):
    __swig_setmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ThreadPool, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ThreadPool, name)
    def __repr__(self):
        return "<C ThreadPool instance at %s>" % (self.this,)
    kDefaultStackBytes = _net_base_pywrapselectserver.ThreadPool_kDefaultStackBytes
    def __init__(self, *args):
        _swig_setattr(self, ThreadPool, 'this', _net_base_pywrapselectserver.new_ThreadPool(*args))
        _swig_setattr(self, ThreadPool, 'thisown', 1)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_ThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _net_base_pywrapselectserver.ThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _net_base_pywrapselectserver.ThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _net_base_pywrapselectserver.ThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _net_base_pywrapselectserver.ThreadPool_SetThreadNamePrefix(*args)
    def SetWatchdogTimeout(*args): return _net_base_pywrapselectserver.ThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _net_base_pywrapselectserver.ThreadPool_watchdog_timeout(*args)
    def StartWorkers(*args): return _net_base_pywrapselectserver.ThreadPool_StartWorkers(*args)
    def thread_options(*args): return _net_base_pywrapselectserver.ThreadPool_thread_options(*args)
    def Add(*args): return _net_base_pywrapselectserver.ThreadPool_Add(*args)
    def AddAfter(*args): return _net_base_pywrapselectserver.ThreadPool_AddAfter(*args)
    def TryAdd(*args): return _net_base_pywrapselectserver.ThreadPool_TryAdd(*args)
    def AddIfReadyToRun(*args): return _net_base_pywrapselectserver.ThreadPool_AddIfReadyToRun(*args)
    def queue_count(*args): return _net_base_pywrapselectserver.ThreadPool_queue_count(*args)
    def queue_capacity(*args): return _net_base_pywrapselectserver.ThreadPool_queue_capacity(*args)
    def num_threads(*args): return _net_base_pywrapselectserver.ThreadPool_num_threads(*args)
    def thread(*args): return _net_base_pywrapselectserver.ThreadPool_thread(*args)

class ThreadPoolPtr(ThreadPool):
    def __init__(self, this):
        _swig_setattr(self, ThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ThreadPool, 'thisown', 0)
        _swig_setattr(self, ThreadPool,self.__class__,ThreadPool)
_net_base_pywrapselectserver.ThreadPool_swigregister(ThreadPoolPtr)


MaximizeNumFiles = _net_base_pywrapselectserver.MaximizeNumFiles
class SSDeadObject(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SSDeadObject, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SSDeadObject, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SSDeadObject instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_SSDeadObject):
        try:
            if self.thisown: destroy(self)
        except: pass
    def key(*args): return _net_base_pywrapselectserver.SSDeadObject_key(*args)
    def Cancel(*args): return _net_base_pywrapselectserver.SSDeadObject_Cancel(*args)

class SSDeadObjectPtr(SSDeadObject):
    def __init__(self, this):
        _swig_setattr(self, SSDeadObject, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SSDeadObject, 'thisown', 0)
        _swig_setattr(self, SSDeadObject,self.__class__,SSDeadObject)
_net_base_pywrapselectserver.SSDeadObject_swigregister(SSDeadObjectPtr)
cvar = _net_base_pywrapselectserver.cvar
kMaxEINTRAttempts = cvar.kMaxEINTRAttempts

class SelectService(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SelectService, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SelectService, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SelectService instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_SelectService):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetupRequest(*args): return _net_base_pywrapselectserver.SelectService_SetupRequest(*args)
    def Poll(*args): return _net_base_pywrapselectserver.SelectService_Poll(*args)
    def SendFakeSignal(*args): return _net_base_pywrapselectserver.SelectService_SendFakeSignal(*args)

class SelectServicePtr(SelectService):
    def __init__(self, this):
        _swig_setattr(self, SelectService, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SelectService, 'thisown', 0)
        _swig_setattr(self, SelectService,self.__class__,SelectService)
_net_base_pywrapselectserver.SelectService_swigregister(SelectServicePtr)

class SelectServer(Executor):
    __swig_setmethods__ = {}
    for _s in [Executor]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, SelectServer, name, value)
    __swig_getmethods__ = {}
    for _s in [Executor]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, SelectServer, name)
    def __repr__(self):
        return "<C SelectServer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, SelectServer, 'this', _net_base_pywrapselectserver.new_SelectServer(*args))
        _swig_setattr(self, SelectServer, 'thisown', 1)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_SelectServer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Loop(*args): return _net_base_pywrapselectserver.SelectServer_Loop(*args)
    def Poll(*args): return _net_base_pywrapselectserver.SelectServer_Poll(*args)
    def is_looping(*args): return _net_base_pywrapselectserver.SelectServer_is_looping(*args)
    def LoopIfNecessary(*args): return _net_base_pywrapselectserver.SelectServer_LoopIfNecessary(*args)
    def MakeLoopExit(*args): return _net_base_pywrapselectserver.SelectServer_MakeLoopExit(*args)
    def MakeLoopExitSoon(*args): return _net_base_pywrapselectserver.SelectServer_MakeLoopExitSoon(*args)
    def EnableLameDuckMode(*args): return _net_base_pywrapselectserver.SelectServer_EnableLameDuckMode(*args)
    def in_lame_duck_mode(*args): return _net_base_pywrapselectserver.SelectServer_in_lame_duck_mode(*args)
    def exit_closure(*args): return _net_base_pywrapselectserver.SelectServer_exit_closure(*args)
    def GetRequest(*args): return _net_base_pywrapselectserver.SelectServer_GetRequest(*args)
    def SetRequest(*args): return _net_base_pywrapselectserver.SelectServer_SetRequest(*args)
    def RequestWrite(*args): return _net_base_pywrapselectserver.SelectServer_RequestWrite(*args)
    def StopRequestWrite(*args): return _net_base_pywrapselectserver.SelectServer_StopRequestWrite(*args)
    def RequestRead(*args): return _net_base_pywrapselectserver.SelectServer_RequestRead(*args)
    def StopRequestRead(*args): return _net_base_pywrapselectserver.SelectServer_StopRequestRead(*args)
    def RunInSelectLoop(*args): return _net_base_pywrapselectserver.SelectServer_RunInSelectLoop(*args)
    def Add(*args): return _net_base_pywrapselectserver.SelectServer_Add(*args)
    def TryAdd(*args): return _net_base_pywrapselectserver.SelectServer_TryAdd(*args)
    def AddIfReadyToRun(*args): return _net_base_pywrapselectserver.SelectServer_AddIfReadyToRun(*args)
    def AddAfter(*args): return _net_base_pywrapselectserver.SelectServer_AddAfter(*args)
    def num_pending_closures(*args): return _net_base_pywrapselectserver.SelectServer_num_pending_closures(*args)
    def AddAlarm(*args): return _net_base_pywrapselectserver.SelectServer_AddAlarm(*args)
    def AddPeriodicAlarm(*args): return _net_base_pywrapselectserver.SelectServer_AddPeriodicAlarm(*args)
    def RemoveAlarm(*args): return _net_base_pywrapselectserver.SelectServer_RemoveAlarm(*args)
    def HasAlarm(*args): return _net_base_pywrapselectserver.SelectServer_HasAlarm(*args)
    def RemoveAllAlarms(*args): return _net_base_pywrapselectserver.SelectServer_RemoveAllAlarms(*args)
    def DisableAlarms(*args): return _net_base_pywrapselectserver.SelectServer_DisableAlarms(*args)
    def ReenableAlarms(*args): return _net_base_pywrapselectserver.SelectServer_ReenableAlarms(*args)
    def RunAfter(*args): return _net_base_pywrapselectserver.SelectServer_RunAfter(*args)
    def RunForever(*args): return _net_base_pywrapselectserver.SelectServer_RunForever(*args)
    def AddSignalHandler(*args): return _net_base_pywrapselectserver.SelectServer_AddSignalHandler(*args)
    def RemoveSignalHandler(*args): return _net_base_pywrapselectserver.SelectServer_RemoveSignalHandler(*args)
    def RemoveAllSignalHandlers(*args): return _net_base_pywrapselectserver.SelectServer_RemoveAllSignalHandlers(*args)
    def DisableSignalHandlers(*args): return _net_base_pywrapselectserver.SelectServer_DisableSignalHandlers(*args)
    def ReenableSignalHandlers(*args): return _net_base_pywrapselectserver.SelectServer_ReenableSignalHandlers(*args)
    def SetupExportedVariables(*args): return _net_base_pywrapselectserver.SelectServer_SetupExportedVariables(*args)
    def PrintAlarms(*args): return _net_base_pywrapselectserver.SelectServer_PrintAlarms(*args)
    def AsynchronousDelete(*args): return _net_base_pywrapselectserver.SelectServer_AsynchronousDelete(*args)
    def InDeathRow(*args): return _net_base_pywrapselectserver.SelectServer_InDeathRow(*args)
    def HasConnections(*args): return _net_base_pywrapselectserver.SelectServer_HasConnections(*args)
    def numpolls(*args): return _net_base_pywrapselectserver.SelectServer_numpolls(*args)
    def sumpolls(*args): return _net_base_pywrapselectserver.SelectServer_sumpolls(*args)
    def walltimer(*args): return _net_base_pywrapselectserver.SelectServer_walltimer(*args)
    def polltimer(*args): return _net_base_pywrapselectserver.SelectServer_polltimer(*args)
    def EnablePollTimer(*args): return _net_base_pywrapselectserver.SelectServer_EnablePollTimer(*args)
    def local_data(*args): return _net_base_pywrapselectserver.SelectServer_local_data(*args)
    def Verify(*args): return _net_base_pywrapselectserver.SelectServer_Verify(*args)
    def set_warn_cross_thread_use(*args): return _net_base_pywrapselectserver.SelectServer_set_warn_cross_thread_use(*args)
    def SendFakeSignal(*args): return _net_base_pywrapselectserver.SelectServer_SendFakeSignal(*args)
    def RegularPollForOneFD(*args): return _net_base_pywrapselectserver.SelectServer_RegularPollForOneFD(*args)
    def InSelectThread(*args): return _net_base_pywrapselectserver.SelectServer_InSelectThread(*args)
    __swig_getmethods__["MakeAllLoopsExit"] = lambda x: _net_base_pywrapselectserver.SelectServer_MakeAllLoopsExit
    if _newclass:MakeAllLoopsExit = staticmethod(_net_base_pywrapselectserver.SelectServer_MakeAllLoopsExit)
    __swig_getmethods__["MakeAllLoopsExitSoon"] = lambda x: _net_base_pywrapselectserver.SelectServer_MakeAllLoopsExitSoon
    if _newclass:MakeAllLoopsExitSoon = staticmethod(_net_base_pywrapselectserver.SelectServer_MakeAllLoopsExitSoon)
    __swig_getmethods__["SetupLameDuckMode"] = lambda x: _net_base_pywrapselectserver.SelectServer_SetupLameDuckMode
    if _newclass:SetupLameDuckMode = staticmethod(_net_base_pywrapselectserver.SelectServer_SetupLameDuckMode)

class SelectServerPtr(SelectServer):
    def __init__(self, this):
        _swig_setattr(self, SelectServer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SelectServer, 'thisown', 0)
        _swig_setattr(self, SelectServer,self.__class__,SelectServer)
_net_base_pywrapselectserver.SelectServer_swigregister(SelectServerPtr)

SelectServer_MakeAllLoopsExit = _net_base_pywrapselectserver.SelectServer_MakeAllLoopsExit

SelectServer_MakeAllLoopsExitSoon = _net_base_pywrapselectserver.SelectServer_MakeAllLoopsExitSoon

SelectServer_SetupLameDuckMode = _net_base_pywrapselectserver.SelectServer_SetupLameDuckMode

class PollSelectService(SelectService):
    __swig_setmethods__ = {}
    for _s in [SelectService]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, PollSelectService, name, value)
    __swig_getmethods__ = {}
    for _s in [SelectService]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, PollSelectService, name)
    def __repr__(self):
        return "<C PollSelectService instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, PollSelectService, 'this', _net_base_pywrapselectserver.new_PollSelectService(*args))
        _swig_setattr(self, PollSelectService, 'thisown', 1)
    def SetupRequest(*args): return _net_base_pywrapselectserver.PollSelectService_SetupRequest(*args)
    def Poll(*args): return _net_base_pywrapselectserver.PollSelectService_Poll(*args)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_PollSelectService):
        try:
            if self.thisown: destroy(self)
        except: pass

class PollSelectServicePtr(PollSelectService):
    def __init__(self, this):
        _swig_setattr(self, PollSelectService, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, PollSelectService, 'thisown', 0)
        _swig_setattr(self, PollSelectService,self.__class__,PollSelectService)
_net_base_pywrapselectserver.PollSelectService_swigregister(PollSelectServicePtr)

class RtSigSelectService(SelectService):
    __swig_setmethods__ = {}
    for _s in [SelectService]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RtSigSelectService, name, value)
    __swig_getmethods__ = {}
    for _s in [SelectService]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RtSigSelectService, name)
    def __repr__(self):
        return "<C RtSigSelectService instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RtSigSelectService, 'this', _net_base_pywrapselectserver.new_RtSigSelectService(*args))
        _swig_setattr(self, RtSigSelectService, 'thisown', 1)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_RtSigSelectService):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetupRequest(*args): return _net_base_pywrapselectserver.RtSigSelectService_SetupRequest(*args)
    def Poll(*args): return _net_base_pywrapselectserver.RtSigSelectService_Poll(*args)
    def SendFakeSignal(*args): return _net_base_pywrapselectserver.RtSigSelectService_SendFakeSignal(*args)

class RtSigSelectServicePtr(RtSigSelectService):
    def __init__(self, this):
        _swig_setattr(self, RtSigSelectService, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RtSigSelectService, 'thisown', 0)
        _swig_setattr(self, RtSigSelectService,self.__class__,RtSigSelectService)
_net_base_pywrapselectserver.RtSigSelectService_swigregister(RtSigSelectServicePtr)

class EPollSelectService(SelectService):
    __swig_setmethods__ = {}
    for _s in [SelectService]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, EPollSelectService, name, value)
    __swig_getmethods__ = {}
    for _s in [SelectService]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, EPollSelectService, name)
    def __repr__(self):
        return "<C EPollSelectService instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, EPollSelectService, 'this', _net_base_pywrapselectserver.new_EPollSelectService(*args))
        _swig_setattr(self, EPollSelectService, 'thisown', 1)
    def __del__(self, destroy=_net_base_pywrapselectserver.delete_EPollSelectService):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetupRequest(*args): return _net_base_pywrapselectserver.EPollSelectService_SetupRequest(*args)
    def Poll(*args): return _net_base_pywrapselectserver.EPollSelectService_Poll(*args)
    __swig_getmethods__["EPollIsSupported"] = lambda x: _net_base_pywrapselectserver.EPollSelectService_EPollIsSupported
    if _newclass:EPollIsSupported = staticmethod(_net_base_pywrapselectserver.EPollSelectService_EPollIsSupported)

class EPollSelectServicePtr(EPollSelectService):
    def __init__(self, this):
        _swig_setattr(self, EPollSelectService, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, EPollSelectService, 'thisown', 0)
        _swig_setattr(self, EPollSelectService,self.__class__,EPollSelectService)
_net_base_pywrapselectserver.EPollSelectService_swigregister(EPollSelectServicePtr)

EPollSelectService_EPollIsSupported = _net_base_pywrapselectserver.EPollSelectService_EPollIsSupported



# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _thread_pywrapthreadpool

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
        _swig_setattr(self, stringVector, 'this', _thread_pywrapthreadpool.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_thread_pywrapthreadpool.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_thread_pywrapthreadpool.stringVector_swigregister(stringVectorPtr)

class Executor(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Executor, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Executor, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C thread::Executor instance at %s>" % (self.this,)
    def __del__(self, destroy=_thread_pywrapthreadpool.delete_Executor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Add(*args): return _thread_pywrapthreadpool.Executor_Add(*args)
    def TryAdd(*args): return _thread_pywrapthreadpool.Executor_TryAdd(*args)
    def AddIfReadyToRun(*args): return _thread_pywrapthreadpool.Executor_AddIfReadyToRun(*args)
    def AddAfter(*args): return _thread_pywrapthreadpool.Executor_AddAfter(*args)
    def num_pending_closures(*args): return _thread_pywrapthreadpool.Executor_num_pending_closures(*args)
    __swig_getmethods__["DefaultExecutor"] = lambda x: _thread_pywrapthreadpool.Executor_DefaultExecutor
    if _newclass:DefaultExecutor = staticmethod(_thread_pywrapthreadpool.Executor_DefaultExecutor)
    __swig_getmethods__["SetDefaultExecutor"] = lambda x: _thread_pywrapthreadpool.Executor_SetDefaultExecutor
    if _newclass:SetDefaultExecutor = staticmethod(_thread_pywrapthreadpool.Executor_SetDefaultExecutor)
    __swig_getmethods__["CurrentExecutor"] = lambda x: _thread_pywrapthreadpool.Executor_CurrentExecutor
    if _newclass:CurrentExecutor = staticmethod(_thread_pywrapthreadpool.Executor_CurrentExecutor)
    __swig_getmethods__["CurrentExecutorPointerInternal"] = lambda x: _thread_pywrapthreadpool.Executor_CurrentExecutorPointerInternal
    if _newclass:CurrentExecutorPointerInternal = staticmethod(_thread_pywrapthreadpool.Executor_CurrentExecutorPointerInternal)

class ExecutorPtr(Executor):
    def __init__(self, this):
        _swig_setattr(self, Executor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Executor, 'thisown', 0)
        _swig_setattr(self, Executor,self.__class__,Executor)
_thread_pywrapthreadpool.Executor_swigregister(ExecutorPtr)

Executor_DefaultExecutor = _thread_pywrapthreadpool.Executor_DefaultExecutor

Executor_SetDefaultExecutor = _thread_pywrapthreadpool.Executor_SetDefaultExecutor

Executor_CurrentExecutor = _thread_pywrapthreadpool.Executor_CurrentExecutor

Executor_CurrentExecutorPointerInternal = _thread_pywrapthreadpool.Executor_CurrentExecutorPointerInternal


NewInlineExecutor = _thread_pywrapthreadpool.NewInlineExecutor

SingletonInlineExecutor = _thread_pywrapthreadpool.SingletonInlineExecutor

NewSynchronizedInlineExecutor = _thread_pywrapthreadpool.NewSynchronizedInlineExecutor
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
    def __del__(self, destroy=_thread_pywrapthreadpool.delete_AbstractThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _thread_pywrapthreadpool.AbstractThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _thread_pywrapthreadpool.AbstractThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _thread_pywrapthreadpool.AbstractThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _thread_pywrapthreadpool.AbstractThreadPool_SetThreadNamePrefix(*args)
    def StartWorkers(*args): return _thread_pywrapthreadpool.AbstractThreadPool_StartWorkers(*args)
    def num_pending_closures(*args): return _thread_pywrapthreadpool.AbstractThreadPool_num_pending_closures(*args)
    def SetWatchdogTimeout(*args): return _thread_pywrapthreadpool.AbstractThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _thread_pywrapthreadpool.AbstractThreadPool_watchdog_timeout(*args)
    def thread_options(*args): return _thread_pywrapthreadpool.AbstractThreadPool_thread_options(*args)
    def queue_count(*args): return _thread_pywrapthreadpool.AbstractThreadPool_queue_count(*args)
    def queue_capacity(*args): return _thread_pywrapthreadpool.AbstractThreadPool_queue_capacity(*args)

class AbstractThreadPoolPtr(AbstractThreadPool):
    def __init__(self, this):
        _swig_setattr(self, AbstractThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AbstractThreadPool, 'thisown', 0)
        _swig_setattr(self, AbstractThreadPool,self.__class__,AbstractThreadPool)
_thread_pywrapthreadpool.AbstractThreadPool_swigregister(AbstractThreadPoolPtr)

class ThreadPool(AbstractThreadPool):
    __swig_setmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ThreadPool, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractThreadPool]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ThreadPool, name)
    def __repr__(self):
        return "<C ThreadPool instance at %s>" % (self.this,)
    kDefaultStackBytes = _thread_pywrapthreadpool.ThreadPool_kDefaultStackBytes
    def __init__(self, *args):
        _swig_setattr(self, ThreadPool, 'this', _thread_pywrapthreadpool.new_ThreadPool(*args))
        _swig_setattr(self, ThreadPool, 'thisown', 1)
    def __del__(self, destroy=_thread_pywrapthreadpool.delete_ThreadPool):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetStackSize(*args): return _thread_pywrapthreadpool.ThreadPool_SetStackSize(*args)
    def SetFIFOScheduling(*args): return _thread_pywrapthreadpool.ThreadPool_SetFIFOScheduling(*args)
    def SetNiceLevel(*args): return _thread_pywrapthreadpool.ThreadPool_SetNiceLevel(*args)
    def SetThreadNamePrefix(*args): return _thread_pywrapthreadpool.ThreadPool_SetThreadNamePrefix(*args)
    def SetWatchdogTimeout(*args): return _thread_pywrapthreadpool.ThreadPool_SetWatchdogTimeout(*args)
    def watchdog_timeout(*args): return _thread_pywrapthreadpool.ThreadPool_watchdog_timeout(*args)
    def StartWorkers(*args): return _thread_pywrapthreadpool.ThreadPool_StartWorkers(*args)
    def thread_options(*args): return _thread_pywrapthreadpool.ThreadPool_thread_options(*args)
    def Add(*args): return _thread_pywrapthreadpool.ThreadPool_Add(*args)
    def AddAfter(*args): return _thread_pywrapthreadpool.ThreadPool_AddAfter(*args)
    def TryAdd(*args): return _thread_pywrapthreadpool.ThreadPool_TryAdd(*args)
    def AddIfReadyToRun(*args): return _thread_pywrapthreadpool.ThreadPool_AddIfReadyToRun(*args)
    def queue_count(*args): return _thread_pywrapthreadpool.ThreadPool_queue_count(*args)
    def queue_capacity(*args): return _thread_pywrapthreadpool.ThreadPool_queue_capacity(*args)
    def num_threads(*args): return _thread_pywrapthreadpool.ThreadPool_num_threads(*args)
    def thread(*args): return _thread_pywrapthreadpool.ThreadPool_thread(*args)

class ThreadPoolPtr(ThreadPool):
    def __init__(self, this):
        _swig_setattr(self, ThreadPool, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ThreadPool, 'thisown', 0)
        _swig_setattr(self, ThreadPool,self.__class__,ThreadPool)
_thread_pywrapthreadpool.ThreadPool_swigregister(ThreadPoolPtr)



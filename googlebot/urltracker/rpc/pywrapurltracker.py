# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _googlebot_urltracker_rpc_pywrapurltracker

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
        _swig_setattr(self, stringVector, 'this', _googlebot_urltracker_rpc_pywrapurltracker.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_googlebot_urltracker_rpc_pywrapurltracker.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_googlebot_urltracker_rpc_pywrapurltracker.stringVector_swigregister(stringVectorPtr)

class UrlTrackerData(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlTrackerData, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UrlTrackerData, name)
    def __repr__(self):
        return "<C UrlTrackerData instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, UrlTrackerData, 'this', _googlebot_urltracker_rpc_pywrapurltracker.new_UrlTrackerData(*args))
        _swig_setattr(self, UrlTrackerData, 'thisown', 1)
    def __del__(self, destroy=_googlebot_urltracker_rpc_pywrapurltracker.delete_UrlTrackerData):
        try:
            if self.thisown: destroy(self)
        except: pass

class UrlTrackerDataPtr(UrlTrackerData):
    def __init__(self, this):
        _swig_setattr(self, UrlTrackerData, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlTrackerData, 'thisown', 0)
        _swig_setattr(self, UrlTrackerData,self.__class__,UrlTrackerData)
_googlebot_urltracker_rpc_pywrapurltracker.UrlTrackerData_swigregister(UrlTrackerDataPtr)

kMaxURLStateNameLen = _googlebot_urltracker_rpc_pywrapurltracker.kMaxURLStateNameLen
URL_UNKNOWN = _googlebot_urltracker_rpc_pywrapurltracker.URL_UNKNOWN
URL_FIRST_STATE = _googlebot_urltracker_rpc_pywrapurltracker.URL_FIRST_STATE
URL_PR_ONLY = _googlebot_urltracker_rpc_pywrapurltracker.URL_PR_ONLY
URL_UNCRAWLED = _googlebot_urltracker_rpc_pywrapurltracker.URL_UNCRAWLED
URL_INFLIGHT = _googlebot_urltracker_rpc_pywrapurltracker.URL_INFLIGHT
URL_INFLIGHT_LONGTIME = _googlebot_urltracker_rpc_pywrapurltracker.URL_INFLIGHT_LONGTIME
URL_CRAWLED = _googlebot_urltracker_rpc_pywrapurltracker.URL_CRAWLED
URL_ROBOTS = _googlebot_urltracker_rpc_pywrapurltracker.URL_ROBOTS
URL_UNREACHABLE = _googlebot_urltracker_rpc_pywrapurltracker.URL_UNREACHABLE
URL_ERROR = _googlebot_urltracker_rpc_pywrapurltracker.URL_ERROR
URL_NUM_STATES = _googlebot_urltracker_rpc_pywrapurltracker.URL_NUM_STATES

URLStateName = _googlebot_urltracker_rpc_pywrapurltracker.URLStateName

URLStateFromName = _googlebot_urltracker_rpc_pywrapurltracker.URLStateFromName

URLStateIsTerminal = _googlebot_urltracker_rpc_pywrapurltracker.URLStateIsTerminal

URLStateIsTransitionValid = _googlebot_urltracker_rpc_pywrapurltracker.URLStateIsTransitionValid
class UrlTracker(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlTracker, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UrlTracker, name)
    def __repr__(self):
        return "<C UrlTracker instance at %s>" % (self.this,)
    __swig_getmethods__["get_url_state"] = lambda x: _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_url_state
    if _newclass:get_url_state = staticmethod(_googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_url_state)
    __swig_getmethods__["get_state_name"] = lambda x: _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_state_name
    if _newclass:get_state_name = staticmethod(_googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_state_name)
    __swig_getmethods__["is_info_state"] = lambda x: _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_is_info_state
    if _newclass:is_info_state = staticmethod(_googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_is_info_state)
    __swig_getmethods__["SanityCheck"] = lambda x: _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_SanityCheck
    if _newclass:SanityCheck = staticmethod(_googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_SanityCheck)
    def __init__(self, *args):
        _swig_setattr(self, UrlTracker, 'this', _googlebot_urltracker_rpc_pywrapurltracker.new_UrlTracker(*args))
        _swig_setattr(self, UrlTracker, 'thisown', 1)
    def __del__(self, destroy=_googlebot_urltracker_rpc_pywrapurltracker.delete_UrlTracker):
        try:
            if self.thisown: destroy(self)
        except: pass

class UrlTrackerPtr(UrlTracker):
    def __init__(self, this):
        _swig_setattr(self, UrlTracker, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlTracker, 'thisown', 0)
        _swig_setattr(self, UrlTracker,self.__class__,UrlTracker)
_googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_swigregister(UrlTrackerPtr)

UrlTracker_get_url_state = _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_url_state

UrlTracker_get_state_name = _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_get_state_name

UrlTracker_is_info_state = _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_is_info_state

UrlTracker_SanityCheck = _googlebot_urltracker_rpc_pywrapurltracker.UrlTracker_SanityCheck



# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _webutil_urlutil_pywrapurlmatch

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
        _swig_setattr(self, stringVector, 'this', _webutil_urlutil_pywrapurlmatch.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_webutil_urlutil_pywrapurlmatch.stringVector_swigregister(stringVectorPtr)

class ConstVectorConstCharPtr(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ConstVectorConstCharPtr, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ConstVectorConstCharPtr, name)
    def __repr__(self):
        return "<C std::vector<(p.q(const).char)> instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, ConstVectorConstCharPtr, 'this', _webutil_urlutil_pywrapurlmatch.new_ConstVectorConstCharPtr(*args))
        _swig_setattr(self, ConstVectorConstCharPtr, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_ConstVectorConstCharPtr):
        try:
            if self.thisown: destroy(self)
        except: pass

class ConstVectorConstCharPtrPtr(ConstVectorConstCharPtr):
    def __init__(self, this):
        _swig_setattr(self, ConstVectorConstCharPtr, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ConstVectorConstCharPtr, 'thisown', 0)
        _swig_setattr(self, ConstVectorConstCharPtr,self.__class__,ConstVectorConstCharPtr)
_webutil_urlutil_pywrapurlmatch.ConstVectorConstCharPtr_swigregister(ConstVectorConstCharPtrPtr)

class AbstractUrlMatcher(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, AbstractUrlMatcher, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, AbstractUrlMatcher, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C AbstractUrlMatcher instance at %s>" % (self.this,)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_AbstractUrlMatcher):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Reload(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_Reload(*args)
    def ReloadIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_ReloadIfChanged(*args)
    def HasChanged(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_HasChanged(*args)
    def NewIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_NewIfChanged(*args)
    def Test(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_Test(*args)
    def DebugPrint(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_DebugPrint(*args)
    def IsHealthy(*args): return _webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_IsHealthy(*args)

class AbstractUrlMatcherPtr(AbstractUrlMatcher):
    def __init__(self, this):
        _swig_setattr(self, AbstractUrlMatcher, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, AbstractUrlMatcher, 'thisown', 0)
        _swig_setattr(self, AbstractUrlMatcher,self.__class__,AbstractUrlMatcher)
_webutil_urlutil_pywrapurlmatch.AbstractUrlMatcher_swigregister(AbstractUrlMatcherPtr)

class UrlMatcher(AbstractUrlMatcher):
    __swig_setmethods__ = {}
    for _s in [AbstractUrlMatcher]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlMatcher, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractUrlMatcher]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, UrlMatcher, name)
    def __repr__(self):
        return "<C UrlMatcher instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, UrlMatcher, 'this', _webutil_urlutil_pywrapurlmatch.new_UrlMatcher(*args))
        _swig_setattr(self, UrlMatcher, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_UrlMatcher):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Reload(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Reload(*args)
    def Clear(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Clear(*args)
    def Insert(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Insert(*args)
    def Compile(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Compile(*args)
    def Optimize(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Optimize(*args)
    def IsOptimized(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsOptimized(*args)
    def IsEmpty(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsEmpty(*args)
    def IsHealthy(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsHealthy(*args)
    def Size(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Size(*args)
    def DebugPrint(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_DebugPrint(*args)
    def ShowSpaceUsage(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_ShowSpaceUsage(*args)
    __swig_getmethods__["CreateUrlMatcher"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_CreateUrlMatcher
    if _newclass:CreateUrlMatcher = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_CreateUrlMatcher)
    __swig_getmethods__["IsTriePattern"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsTriePattern
    if _newclass:IsTriePattern = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_IsTriePattern)
    __swig_getmethods__["TrieFilename"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieFilename
    if _newclass:TrieFilename = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieFilename)
    __swig_getmethods__["TrieResidFilename"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieResidFilename
    if _newclass:TrieResidFilename = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieResidFilename)
    def ReloadIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_ReloadIfChanged(*args)
    def NewIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_NewIfChanged(*args)
    def ReloadPatternReader(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_ReloadPatternReader(*args)
    def file(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_file(*args)
    def IsUsingTrieFiles(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsUsingTrieFiles(*args)
    def set_file(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_set_file(*args)
    def loaded_successfully(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_loaded_successfully(*args)
    def HasChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_HasChanged(*args)
    def line_num(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_line_num(*args)
    POSITIVE_PATTERNS = _webutil_urlutil_pywrapurlmatch.UrlMatcher_POSITIVE_PATTERNS
    NEGATIVE_PATTERNS = _webutil_urlutil_pywrapurlmatch.UrlMatcher_NEGATIVE_PATTERNS
    POSITIVE_NEGATIVE_PATTERNS = _webutil_urlutil_pywrapurlmatch.UrlMatcher_POSITIVE_NEGATIVE_PATTERNS
    def DumpPatternsToVector(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_DumpPatternsToVector(*args)
    PATTERN_NONE = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_NONE
    PATTERN_SLASH_TRIE = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_SLASH_TRIE
    PATTERN_SUFFIX_TRIE = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_SUFFIX_TRIE
    PATTERN_CHAR = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_CHAR
    PATTERN_PREFIX = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_PREFIX
    PATTERN_CONTAINS = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_CONTAINS
    PATTERN_EXACT_MATCH = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_EXACT_MATCH
    PATTERN_EXACT_PATH_MATCH = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_EXACT_PATH_MATCH
    PATTERN_REGEXP = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_REGEXP
    PATTERN_TYPE_MAX = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PATTERN_TYPE_MAX
    RANGE_NONE = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_NONE
    RANGE_WHOLE = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_WHOLE
    RANGE_DIFFICULT = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_DIFFICULT
    RANGE_PREFIX = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_PREFIX
    RANGE_EXACT = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_EXACT
    RANGE_WWW_PREFIX = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_WWW_PREFIX
    RANGE_WWW_EXACT = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_WWW_EXACT
    RANGE_TYPE_MAX = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RANGE_TYPE_MAX
    __swig_getmethods__["PatternTypeName"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_PatternTypeName
    if _newclass:PatternTypeName = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_PatternTypeName)
    __swig_getmethods__["RangeTypeName"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcher_RangeTypeName
    if _newclass:RangeTypeName = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcher_RangeTypeName)
    def Test(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatcher_Test(*args)

class UrlMatcherPtr(UrlMatcher):
    def __init__(self, this):
        _swig_setattr(self, UrlMatcher, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlMatcher, 'thisown', 0)
        _swig_setattr(self, UrlMatcher,self.__class__,UrlMatcher)
_webutil_urlutil_pywrapurlmatch.UrlMatcher_swigregister(UrlMatcherPtr)

UrlMatcher_CreateUrlMatcher = _webutil_urlutil_pywrapurlmatch.UrlMatcher_CreateUrlMatcher

UrlMatcher_IsTriePattern = _webutil_urlutil_pywrapurlmatch.UrlMatcher_IsTriePattern

UrlMatcher_TrieFilename = _webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieFilename

UrlMatcher_TrieResidFilename = _webutil_urlutil_pywrapurlmatch.UrlMatcher_TrieResidFilename

UrlMatcher_PatternTypeName = _webutil_urlutil_pywrapurlmatch.UrlMatcher_PatternTypeName

UrlMatcher_RangeTypeName = _webutil_urlutil_pywrapurlmatch.UrlMatcher_RangeTypeName

class UrlAnalyzed(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlAnalyzed, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UrlAnalyzed, name)
    def __repr__(self):
        return "<C UrlAnalyzed instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, UrlAnalyzed, 'this', _webutil_urlutil_pywrapurlmatch.new_UrlAnalyzed(*args))
        _swig_setattr(self, UrlAnalyzed, 'thisown', 1)
    def Init(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Init(*args)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_UrlAnalyzed):
        try:
            if self.thisown: destroy(self)
        except: pass
    def is_initialized(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_is_initialized(*args)
    def url(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_url(*args)
    def offset(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_offset(*args)
    def lowercased_url(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_lowercased_url(*args)
    def split_succeeded(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_split_succeeded(*args)
    def slash(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_slash(*args)
    def host(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_host(*args)
    def path(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_path(*args)
    def hostlen(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_hostlen(*args)
    def pathlen(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_pathlen(*args)
    def fingerprints_computed(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_fingerprints_computed(*args)
    def fingerprints(*args): return _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_fingerprints(*args)
    __swig_getmethods__["Slash"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Slash
    if _newclass:Slash = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Slash)
    __swig_getmethods__["LowerHostname"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_LowerHostname
    if _newclass:LowerHostname = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlAnalyzed_LowerHostname)
    __swig_getmethods__["Split"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Split
    if _newclass:Split = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Split)

class UrlAnalyzedPtr(UrlAnalyzed):
    def __init__(self, this):
        _swig_setattr(self, UrlAnalyzed, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlAnalyzed, 'thisown', 0)
        _swig_setattr(self, UrlAnalyzed,self.__class__,UrlAnalyzed)
_webutil_urlutil_pywrapurlmatch.UrlAnalyzed_swigregister(UrlAnalyzedPtr)

UrlAnalyzed_Slash = _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Slash

UrlAnalyzed_LowerHostname = _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_LowerHostname

UrlAnalyzed_Split = _webutil_urlutil_pywrapurlmatch.UrlAnalyzed_Split

class UrlMatchers(AbstractUrlMatcher):
    __swig_setmethods__ = {}
    for _s in [AbstractUrlMatcher]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlMatchers, name, value)
    __swig_getmethods__ = {}
    for _s in [AbstractUrlMatcher]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, UrlMatchers, name)
    def __repr__(self):
        return "<C UrlMatchers instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, UrlMatchers, 'this', _webutil_urlutil_pywrapurlmatch.new_UrlMatchers(*args))
        _swig_setattr(self, UrlMatchers, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_UrlMatchers):
        try:
            if self.thisown: destroy(self)
        except: pass
    def AddFile(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_AddFile(*args)
    def AddBinaryFile(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_AddBinaryFile(*args)
    def AddBinAndResidFiles(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_AddBinAndResidFiles(*args)
    def AddMatcher(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_AddMatcher(*args)
    def MergeUrlMatchers(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_MergeUrlMatchers(*args)
    def IsHealthy(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_IsHealthy(*args)
    def Reload(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_Reload(*args)
    def ReloadIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_ReloadIfChanged(*args)
    def HasChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_HasChanged(*args)
    def NewIfChanged(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_NewIfChanged(*args)
    def ThreadSafeReload(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_ThreadSafeReload(*args)
    def Insert(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_Insert(*args)
    def DebugPrint(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_DebugPrint(*args)
    def Test(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchers_Test(*args)

class UrlMatchersPtr(UrlMatchers):
    def __init__(self, this):
        _swig_setattr(self, UrlMatchers, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlMatchers, 'thisown', 0)
        _swig_setattr(self, UrlMatchers,self.__class__,UrlMatchers)
_webutil_urlutil_pywrapurlmatch.UrlMatchers_swigregister(UrlMatchersPtr)

class UrlMatchersIterator(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlMatchersIterator, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UrlMatchersIterator, name)
    def __repr__(self):
        return "<C UrlMatchersIterator instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, UrlMatchersIterator, 'this', _webutil_urlutil_pywrapurlmatch.new_UrlMatchersIterator(*args))
        _swig_setattr(self, UrlMatchersIterator, 'thisown', 1)
    def Next(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchersIterator_Next(*args)
    def AtEnd(*args): return _webutil_urlutil_pywrapurlmatch.UrlMatchersIterator_AtEnd(*args)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_UrlMatchersIterator):
        try:
            if self.thisown: destroy(self)
        except: pass

class UrlMatchersIteratorPtr(UrlMatchersIterator):
    def __init__(self, this):
        _swig_setattr(self, UrlMatchersIterator, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlMatchersIterator, 'thisown', 0)
        _swig_setattr(self, UrlMatchersIterator,self.__class__,UrlMatchersIterator)
_webutil_urlutil_pywrapurlmatch.UrlMatchersIterator_swigregister(UrlMatchersIteratorPtr)

class UrlMatcherIo(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UrlMatcherIo, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UrlMatcherIo, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C UrlMatcherIo instance at %s>" % (self.this,)
    __swig_getmethods__["LoadUrlMatcherFromProtoBuffer"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_LoadUrlMatcherFromProtoBuffer
    if _newclass:LoadUrlMatcherFromProtoBuffer = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcherIo_LoadUrlMatcherFromProtoBuffer)
    __swig_getmethods__["SaveUrlMatcherToProtoBuffer"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_SaveUrlMatcherToProtoBuffer
    if _newclass:SaveUrlMatcherToProtoBuffer = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcherIo_SaveUrlMatcherToProtoBuffer)
    __swig_getmethods__["AreUrlMatchersEqual"] = lambda x: _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_AreUrlMatchersEqual
    if _newclass:AreUrlMatchersEqual = staticmethod(_webutil_urlutil_pywrapurlmatch.UrlMatcherIo_AreUrlMatchersEqual)
    def __del__(self, destroy=_webutil_urlutil_pywrapurlmatch.delete_UrlMatcherIo):
        try:
            if self.thisown: destroy(self)
        except: pass

class UrlMatcherIoPtr(UrlMatcherIo):
    def __init__(self, this):
        _swig_setattr(self, UrlMatcherIo, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, UrlMatcherIo, 'thisown', 0)
        _swig_setattr(self, UrlMatcherIo,self.__class__,UrlMatcherIo)
_webutil_urlutil_pywrapurlmatch.UrlMatcherIo_swigregister(UrlMatcherIoPtr)

UrlMatcherIo_LoadUrlMatcherFromProtoBuffer = _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_LoadUrlMatcherFromProtoBuffer

UrlMatcherIo_SaveUrlMatcherToProtoBuffer = _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_SaveUrlMatcherToProtoBuffer

UrlMatcherIo_AreUrlMatchersEqual = _webutil_urlutil_pywrapurlmatch.UrlMatcherIo_AreUrlMatchersEqual



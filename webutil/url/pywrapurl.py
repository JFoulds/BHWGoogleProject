# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _webutil_url_pywrapurl

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
        _swig_setattr(self, stringVector, 'this', _webutil_url_pywrapurl.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_webutil_url_pywrapurl.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_webutil_url_pywrapurl.stringVector_swigregister(stringVectorPtr)

class ProtocolFlags(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolFlags, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolFlags, name)
    def __repr__(self):
        return "<C ProtocolFlags instance at %s>" % (self.this,)
    __swig_setmethods__["uses_login"] = _webutil_url_pywrapurl.ProtocolFlags_uses_login_set
    __swig_getmethods__["uses_login"] = _webutil_url_pywrapurl.ProtocolFlags_uses_login_get
    if _newclass:uses_login = property(_webutil_url_pywrapurl.ProtocolFlags_uses_login_get, _webutil_url_pywrapurl.ProtocolFlags_uses_login_set)
    __swig_setmethods__["uses_relative"] = _webutil_url_pywrapurl.ProtocolFlags_uses_relative_set
    __swig_getmethods__["uses_relative"] = _webutil_url_pywrapurl.ProtocolFlags_uses_relative_get
    if _newclass:uses_relative = property(_webutil_url_pywrapurl.ProtocolFlags_uses_relative_get, _webutil_url_pywrapurl.ProtocolFlags_uses_relative_set)
    __swig_setmethods__["uses_netloc"] = _webutil_url_pywrapurl.ProtocolFlags_uses_netloc_set
    __swig_getmethods__["uses_netloc"] = _webutil_url_pywrapurl.ProtocolFlags_uses_netloc_get
    if _newclass:uses_netloc = property(_webutil_url_pywrapurl.ProtocolFlags_uses_netloc_get, _webutil_url_pywrapurl.ProtocolFlags_uses_netloc_set)
    __swig_setmethods__["allow_empty_host"] = _webutil_url_pywrapurl.ProtocolFlags_allow_empty_host_set
    __swig_getmethods__["allow_empty_host"] = _webutil_url_pywrapurl.ProtocolFlags_allow_empty_host_get
    if _newclass:allow_empty_host = property(_webutil_url_pywrapurl.ProtocolFlags_allow_empty_host_get, _webutil_url_pywrapurl.ProtocolFlags_allow_empty_host_set)
    __swig_setmethods__["non_hierarchical"] = _webutil_url_pywrapurl.ProtocolFlags_non_hierarchical_set
    __swig_getmethods__["non_hierarchical"] = _webutil_url_pywrapurl.ProtocolFlags_non_hierarchical_get
    if _newclass:non_hierarchical = property(_webutil_url_pywrapurl.ProtocolFlags_non_hierarchical_get, _webutil_url_pywrapurl.ProtocolFlags_non_hierarchical_set)
    __swig_setmethods__["uses_params"] = _webutil_url_pywrapurl.ProtocolFlags_uses_params_set
    __swig_getmethods__["uses_params"] = _webutil_url_pywrapurl.ProtocolFlags_uses_params_get
    if _newclass:uses_params = property(_webutil_url_pywrapurl.ProtocolFlags_uses_params_get, _webutil_url_pywrapurl.ProtocolFlags_uses_params_set)
    __swig_setmethods__["uses_query"] = _webutil_url_pywrapurl.ProtocolFlags_uses_query_set
    __swig_getmethods__["uses_query"] = _webutil_url_pywrapurl.ProtocolFlags_uses_query_get
    if _newclass:uses_query = property(_webutil_url_pywrapurl.ProtocolFlags_uses_query_get, _webutil_url_pywrapurl.ProtocolFlags_uses_query_set)
    __swig_setmethods__["uses_fragment"] = _webutil_url_pywrapurl.ProtocolFlags_uses_fragment_set
    __swig_getmethods__["uses_fragment"] = _webutil_url_pywrapurl.ProtocolFlags_uses_fragment_get
    if _newclass:uses_fragment = property(_webutil_url_pywrapurl.ProtocolFlags_uses_fragment_get, _webutil_url_pywrapurl.ProtocolFlags_uses_fragment_set)
    __swig_setmethods__["default_port"] = _webutil_url_pywrapurl.ProtocolFlags_default_port_set
    __swig_getmethods__["default_port"] = _webutil_url_pywrapurl.ProtocolFlags_default_port_get
    if _newclass:default_port = property(_webutil_url_pywrapurl.ProtocolFlags_default_port_get, _webutil_url_pywrapurl.ProtocolFlags_default_port_set)
    __swig_setmethods__["protocol"] = _webutil_url_pywrapurl.ProtocolFlags_protocol_set
    __swig_getmethods__["protocol"] = _webutil_url_pywrapurl.ProtocolFlags_protocol_get
    if _newclass:protocol = property(_webutil_url_pywrapurl.ProtocolFlags_protocol_get, _webutil_url_pywrapurl.ProtocolFlags_protocol_set)
    def __init__(self, *args):
        _swig_setattr(self, ProtocolFlags, 'this', _webutil_url_pywrapurl.new_ProtocolFlags(*args))
        _swig_setattr(self, ProtocolFlags, 'thisown', 1)
    def __del__(self, destroy=_webutil_url_pywrapurl.delete_ProtocolFlags):
        try:
            if self.thisown: destroy(self)
        except: pass

class ProtocolFlagsPtr(ProtocolFlags):
    def __init__(self, this):
        _swig_setattr(self, ProtocolFlags, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolFlags, 'thisown', 0)
        _swig_setattr(self, ProtocolFlags,self.__class__,ProtocolFlags)
_webutil_url_pywrapurl.ProtocolFlags_swigregister(ProtocolFlagsPtr)

class URL(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, URL, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, URL, name)
    def __repr__(self):
        return "<C URL instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, URL, 'this', _webutil_url_pywrapurl.new_URL(*args))
        _swig_setattr(self, URL, 'thisown', 1)
    def __del__(self, destroy=_webutil_url_pywrapurl.delete_URL):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetComponents(*args): return _webutil_url_pywrapurl.URL_SetComponents(*args)
    def Parse(*args): return _webutil_url_pywrapurl.URL_Parse(*args)
    def ParseWithLen(*args): return _webutil_url_pywrapurl.URL_ParseWithLen(*args)
    def Assemble(*args): return _webutil_url_pywrapurl.URL_Assemble(*args)
    def PathParamsQuery(*args): return _webutil_url_pywrapurl.URL_PathParamsQuery(*args)
    def is_valid(*args): return _webutil_url_pywrapurl.URL_is_valid(*args)
    def QueryComponents(*args): return _webutil_url_pywrapurl.URL_QueryComponents(*args)
    def HostnameIsPunycode(*args): return _webutil_url_pywrapurl.URL_HostnameIsPunycode(*args)
    def HostnameIsUnicode(*args): return _webutil_url_pywrapurl.URL_HostnameIsUnicode(*args)
    def HostnameToPunycode(*args): return _webutil_url_pywrapurl.URL_HostnameToPunycode(*args)
    def HostnameToUnicode(*args): return _webutil_url_pywrapurl.URL_HostnameToUnicode(*args)
    def LightlyCanonicalizeAndVerify(*args): return _webutil_url_pywrapurl.URL_LightlyCanonicalizeAndVerify(*args)
    def GetNthQueryComponent(*args): return _webutil_url_pywrapurl.URL_GetNthQueryComponent(*args)
    def GetQueryComponent(*args): return _webutil_url_pywrapurl.URL_GetQueryComponent(*args)
    def GetQueryComponentDefault(*args): return _webutil_url_pywrapurl.URL_GetQueryComponentDefault(*args)
    def GetIntQueryComponentDefault(*args): return _webutil_url_pywrapurl.URL_GetIntQueryComponentDefault(*args)
    def AddQueryComponent(*args): return _webutil_url_pywrapurl.URL_AddQueryComponent(*args)
    def AddIntQueryComponent(*args): return _webutil_url_pywrapurl.URL_AddIntQueryComponent(*args)
    def DeleteNthQueryComponent(*args): return _webutil_url_pywrapurl.URL_DeleteNthQueryComponent(*args)
    def DeleteQueryComponent(*args): return _webutil_url_pywrapurl.URL_DeleteQueryComponent(*args)
    def DeleteAllQueryComponents(*args): return _webutil_url_pywrapurl.URL_DeleteAllQueryComponents(*args)
    def SetNthQueryComponent(*args): return _webutil_url_pywrapurl.URL_SetNthQueryComponent(*args)
    def SetQueryComponent(*args): return _webutil_url_pywrapurl.URL_SetQueryComponent(*args)
    def SetNthQueryComponentEscaped(*args): return _webutil_url_pywrapurl.URL_SetNthQueryComponentEscaped(*args)
    def SetQueryComponentEscaped(*args): return _webutil_url_pywrapurl.URL_SetQueryComponentEscaped(*args)
    def SetIntQueryComponent(*args): return _webutil_url_pywrapurl.URL_SetIntQueryComponent(*args)
    def SetInt64QueryComponent(*args): return _webutil_url_pywrapurl.URL_SetInt64QueryComponent(*args)
    __swig_getmethods__["IsLegalHostname"] = lambda x: _webutil_url_pywrapurl.URL_IsLegalHostname
    if _newclass:IsLegalHostname = staticmethod(_webutil_url_pywrapurl.URL_IsLegalHostname)
    __swig_getmethods__["NComponentSuffix"] = lambda x: _webutil_url_pywrapurl.URL_NComponentSuffix
    if _newclass:NComponentSuffix = staticmethod(_webutil_url_pywrapurl.URL_NComponentSuffix)
    def IsLikelyInfiniteSpace(*args): return _webutil_url_pywrapurl.URL_IsLikelyInfiniteSpace(*args)
    def Fingerprint(*args): return _webutil_url_pywrapurl.URL_Fingerprint(*args)
    def HostFingerprint(*args): return _webutil_url_pywrapurl.URL_HostFingerprint(*args)
    def DomainFingerprint(*args): return _webutil_url_pywrapurl.URL_DomainFingerprint(*args)
    __swig_getmethods__["FastHostName"] = lambda x: _webutil_url_pywrapurl.URL_FastHostName
    if _newclass:FastHostName = staticmethod(_webutil_url_pywrapurl.URL_FastHostName)
    __swig_getmethods__["FastHostName"] = lambda x: _webutil_url_pywrapurl.URL_FastHostName
    if _newclass:FastHostName = staticmethod(_webutil_url_pywrapurl.URL_FastHostName)
    __swig_getmethods__["FastDomainName"] = lambda x: _webutil_url_pywrapurl.URL_FastDomainName
    if _newclass:FastDomainName = staticmethod(_webutil_url_pywrapurl.URL_FastDomainName)
    __swig_getmethods__["FastDomainName"] = lambda x: _webutil_url_pywrapurl.URL_FastDomainName
    if _newclass:FastDomainName = staticmethod(_webutil_url_pywrapurl.URL_FastDomainName)
    __swig_getmethods__["FastOrgName"] = lambda x: _webutil_url_pywrapurl.URL_FastOrgName
    if _newclass:FastOrgName = staticmethod(_webutil_url_pywrapurl.URL_FastOrgName)
    __swig_getmethods__["FastOrgName"] = lambda x: _webutil_url_pywrapurl.URL_FastOrgName
    if _newclass:FastOrgName = staticmethod(_webutil_url_pywrapurl.URL_FastOrgName)
    def IsHomePage(*args): return _webutil_url_pywrapurl.URL_IsHomePage(*args)
    def protocol(*args): return _webutil_url_pywrapurl.URL_protocol(*args)
    def login(*args): return _webutil_url_pywrapurl.URL_login(*args)
    def host(*args): return _webutil_url_pywrapurl.URL_host(*args)
    def domain(*args): return _webutil_url_pywrapurl.URL_domain(*args)
    def port(*args): return _webutil_url_pywrapurl.URL_port(*args)
    def default_port(*args): return _webutil_url_pywrapurl.URL_default_port(*args)
    def path(*args): return _webutil_url_pywrapurl.URL_path(*args)
    def params(*args): return _webutil_url_pywrapurl.URL_params(*args)
    def query(*args): return _webutil_url_pywrapurl.URL_query(*args)
    def extension(*args): return _webutil_url_pywrapurl.URL_extension(*args)
    def fragment(*args): return _webutil_url_pywrapurl.URL_fragment(*args)
    def set_protocol(*args): return _webutil_url_pywrapurl.URL_set_protocol(*args)
    def set_host(*args): return _webutil_url_pywrapurl.URL_set_host(*args)
    def set_port(*args): return _webutil_url_pywrapurl.URL_set_port(*args)
    def set_path(*args): return _webutil_url_pywrapurl.URL_set_path(*args)
    def set_params(*args): return _webutil_url_pywrapurl.URL_set_params(*args)
    def set_query(*args): return _webutil_url_pywrapurl.URL_set_query(*args)
    def set_fragment(*args): return _webutil_url_pywrapurl.URL_set_fragment(*args)
    def set_login(*args): return _webutil_url_pywrapurl.URL_set_login(*args)
    def CanonicalizePath(*args): return _webutil_url_pywrapurl.URL_CanonicalizePath(*args)
    def NormalizePath(*args): return _webutil_url_pywrapurl.URL_NormalizePath(*args)
    __swig_getmethods__["Escape"] = lambda x: _webutil_url_pywrapurl.URL_Escape
    if _newclass:Escape = staticmethod(_webutil_url_pywrapurl.URL_Escape)
    __swig_getmethods__["Unescape"] = lambda x: _webutil_url_pywrapurl.URL_Unescape
    if _newclass:Unescape = staticmethod(_webutil_url_pywrapurl.URL_Unescape)
    __swig_getmethods__["RegisterCustomProtocol"] = lambda x: _webutil_url_pywrapurl.URL_RegisterCustomProtocol
    if _newclass:RegisterCustomProtocol = staticmethod(_webutil_url_pywrapurl.URL_RegisterCustomProtocol)
    def MakeDomainNameAbsolute(*args): return _webutil_url_pywrapurl.URL_MakeDomainNameAbsolute(*args)

class URLPtr(URL):
    def __init__(self, this):
        _swig_setattr(self, URL, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, URL, 'thisown', 0)
        _swig_setattr(self, URL,self.__class__,URL)
_webutil_url_pywrapurl.URL_swigregister(URLPtr)

URL_IsLegalHostname = _webutil_url_pywrapurl.URL_IsLegalHostname

URL_NComponentSuffix = _webutil_url_pywrapurl.URL_NComponentSuffix

URL_FastHostName = _webutil_url_pywrapurl.URL_FastHostName

URL_FastDomainName = _webutil_url_pywrapurl.URL_FastDomainName

URL_FastOrgName = _webutil_url_pywrapurl.URL_FastOrgName

URL_Escape = _webutil_url_pywrapurl.URL_Escape

URL_Unescape = _webutil_url_pywrapurl.URL_Unescape

URL_RegisterCustomProtocol = _webutil_url_pywrapurl.URL_RegisterCustomProtocol



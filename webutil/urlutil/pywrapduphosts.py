# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _webutil_urlutil_pywrapduphosts

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
        _swig_setattr(self, stringVector, 'this', _webutil_urlutil_pywrapduphosts.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapduphosts.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_webutil_urlutil_pywrapduphosts.stringVector_swigregister(stringVectorPtr)

class FileLineReader(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileLineReader, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileLineReader, name)
    def __repr__(self):
        return "<C FileLineReader instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, FileLineReader, 'this', _webutil_urlutil_pywrapduphosts.new_FileLineReader(*args))
        _swig_setattr(self, FileLineReader, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapduphosts.delete_FileLineReader):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Reload(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_Reload(*args)
    def ReloadIfChanged(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_ReloadIfChanged(*args)
    def HasChanged(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_HasChanged(*args)
    def file(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_file(*args)
    def set_file(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_file(*args)
    def load_from_string(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_load_from_string(*args)
    def set_begin_callback(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_begin_callback(*args)
    def set_line_callback(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_line_callback(*args)
    def set_rawline_callback(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_rawline_callback(*args)
    def set_end_callback(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_end_callback(*args)
    def loaded_successfully(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_loaded_successfully(*args)
    __swig_getmethods__["MaxLineLength"] = lambda x: _webutil_urlutil_pywrapduphosts.FileLineReader_MaxLineLength
    if _newclass:MaxLineLength = staticmethod(_webutil_urlutil_pywrapduphosts.FileLineReader_MaxLineLength)
    def line_buffer_size(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_line_buffer_size(*args)
    def comment_char(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_comment_char(*args)
    def set_comment_char(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_comment_char(*args)
    def drop_blank_lines(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_drop_blank_lines(*args)
    def set_drop_blank_lines(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_drop_blank_lines(*args)
    def line_num(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_line_num(*args)
    __swig_getmethods__["FileMTime"] = lambda x: _webutil_urlutil_pywrapduphosts.FileLineReader_FileMTime
    if _newclass:FileMTime = staticmethod(_webutil_urlutil_pywrapduphosts.FileLineReader_FileMTime)
    def set_signature_verification(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_set_signature_verification(*args)
    def signature_verification(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_signature_verification(*args)
    def HasValidSignature(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_HasValidSignature(*args)
    def SignatureTime(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_SignatureTime(*args)
    def CreateSignatureLine(*args): return _webutil_urlutil_pywrapduphosts.FileLineReader_CreateSignatureLine(*args)

class FileLineReaderPtr(FileLineReader):
    def __init__(self, this):
        _swig_setattr(self, FileLineReader, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, FileLineReader, 'thisown', 0)
        _swig_setattr(self, FileLineReader,self.__class__,FileLineReader)
_webutil_urlutil_pywrapduphosts.FileLineReader_swigregister(FileLineReaderPtr)

FileLineReader_MaxLineLength = _webutil_urlutil_pywrapduphosts.FileLineReader_MaxLineLength

FileLineReader_FileMTime = _webutil_urlutil_pywrapduphosts.FileLineReader_FileMTime


ParseFileByLines = _webutil_urlutil_pywrapduphosts.ParseFileByLines
class DuplicateHostDB(FileLineReader):
    __swig_setmethods__ = {}
    for _s in [FileLineReader]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, DuplicateHostDB, name, value)
    __swig_getmethods__ = {}
    for _s in [FileLineReader]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, DuplicateHostDB, name)
    def __repr__(self):
        return "<C DuplicateHostDB instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, DuplicateHostDB, 'this', _webutil_urlutil_pywrapduphosts.new_DuplicateHostDB(*args))
        _swig_setattr(self, DuplicateHostDB, 'thisown', 1)
    def __del__(self, destroy=_webutil_urlutil_pywrapduphosts.delete_DuplicateHostDB):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Insert(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_Insert(*args)
    def Reload(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_Reload(*args)
    def ReloadIfChanged(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_ReloadIfChanged(*args)
    def FindHost(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_FindHost(*args)
    def FindCanonicalHost(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_FindCanonicalHost(*args)
    def FindCanonicalHostAndWildcard(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_FindCanonicalHostAndWildcard(*args)
    def Canonicalize(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_Canonicalize(*args)
    __swig_getmethods__["AreTheseObvious"] = lambda x: _webutil_urlutil_pywrapduphosts.DuplicateHostDB_AreTheseObvious
    if _newclass:AreTheseObvious = staticmethod(_webutil_urlutil_pywrapduphosts.DuplicateHostDB_AreTheseObvious)
    def IsCanonicalEntry(*args): return _webutil_urlutil_pywrapduphosts.DuplicateHostDB_IsCanonicalEntry(*args)

class DuplicateHostDBPtr(DuplicateHostDB):
    def __init__(self, this):
        _swig_setattr(self, DuplicateHostDB, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, DuplicateHostDB, 'thisown', 0)
        _swig_setattr(self, DuplicateHostDB,self.__class__,DuplicateHostDB)
_webutil_urlutil_pywrapduphosts.DuplicateHostDB_swigregister(DuplicateHostDBPtr)

def EmptyDuplicateHostDB(*args):
    val = _webutil_urlutil_pywrapduphosts.new_EmptyDuplicateHostDB(*args)
    val.thisown = 1
    return val

DuplicateHostDB_AreTheseObvious = _webutil_urlutil_pywrapduphosts.DuplicateHostDB_AreTheseObvious


CreateDuplicateHostDB = _webutil_urlutil_pywrapduphosts.CreateDuplicateHostDB


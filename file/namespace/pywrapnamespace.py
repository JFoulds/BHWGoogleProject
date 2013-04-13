# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _file_namespace_pywrapnamespace

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
        _swig_setattr(self, stringVector, 'this', _file_namespace_pywrapnamespace.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_file_namespace_pywrapnamespace.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_file_namespace_pywrapnamespace.stringVector_swigregister(stringVectorPtr)

class NamespaceFileFactory(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, NamespaceFileFactory, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, NamespaceFileFactory, name)
    def __repr__(self):
        return "<C NamespaceFileFactory instance at %s>" % (self.this,)
    __swig_getmethods__["TranslateFilename"] = lambda x: _file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFilename
    if _newclass:TranslateFilename = staticmethod(_file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFilename)
    __swig_getmethods__["TranslateFully"] = lambda x: _file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFully
    if _newclass:TranslateFully = staticmethod(_file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFully)
    def __init__(self, *args):
        _swig_setattr(self, NamespaceFileFactory, 'this', _file_namespace_pywrapnamespace.new_NamespaceFileFactory(*args))
        _swig_setattr(self, NamespaceFileFactory, 'thisown', 1)
    def __del__(self, destroy=_file_namespace_pywrapnamespace.delete_NamespaceFileFactory):
        try:
            if self.thisown: destroy(self)
        except: pass

class NamespaceFileFactoryPtr(NamespaceFileFactory):
    def __init__(self, this):
        _swig_setattr(self, NamespaceFileFactory, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, NamespaceFileFactory, 'thisown', 0)
        _swig_setattr(self, NamespaceFileFactory,self.__class__,NamespaceFileFactory)
_file_namespace_pywrapnamespace.NamespaceFileFactory_swigregister(NamespaceFileFactoryPtr)

NamespaceFileFactory_TranslateFilename = _file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFilename

NamespaceFileFactory_TranslateFully = _file_namespace_pywrapnamespace.NamespaceFileFactory_TranslateFully



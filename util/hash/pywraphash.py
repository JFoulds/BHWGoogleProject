# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _util_hash_pywraphash

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
        _swig_setattr(self, stringVector, 'this', _util_hash_pywraphash.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_util_hash_pywraphash.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_util_hash_pywraphash.stringVector_swigregister(stringVectorPtr)


Hash32StringWithSeed = _util_hash_pywraphash.Hash32StringWithSeed

Hash64StringWithSeed = _util_hash_pywraphash.Hash64StringWithSeed

Fingerprint = _util_hash_pywraphash.Fingerprint

FingerprintInt64 = _util_hash_pywraphash.FingerprintInt64


# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _iobuffer_pywrapiobuffer

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
        _swig_setattr(self, stringVector, 'this', _iobuffer_pywrapiobuffer.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_iobuffer_pywrapiobuffer.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_iobuffer_pywrapiobuffer.stringVector_swigregister(stringVectorPtr)

class IOBuffer(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, IOBuffer, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, IOBuffer, name)
    def __repr__(self):
        return "<C IOBuffer instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, IOBuffer, 'this', _iobuffer_pywrapiobuffer.new_IOBuffer(*args))
        _swig_setattr(self, IOBuffer, 'thisown', 1)
    def __del__(self, destroy=_iobuffer_pywrapiobuffer.delete_IOBuffer):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Swap(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Swap(*args)
    def AppendIOBuffer(*args): return _iobuffer_pywrapiobuffer.IOBuffer_AppendIOBuffer(*args)
    def AppendIOBufferNonDestructive(*args): return _iobuffer_pywrapiobuffer.IOBuffer_AppendIOBufferNonDestructive(*args)
    def AppendIOBufferN(*args): return _iobuffer_pywrapiobuffer.IOBuffer_AppendIOBufferN(*args)
    def AppendIOBufferNonDestructiveN(*args): return _iobuffer_pywrapiobuffer.IOBuffer_AppendIOBufferNonDestructiveN(*args)
    def AppendRawBlock(*args): return _iobuffer_pywrapiobuffer.IOBuffer_AppendRawBlock(*args)
    def Write(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Write(*args)
    def WriteUntil(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteUntil(*args)
    def WriteString(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteString(*args)
    def WriteInt(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteInt(*args)
    def WriteInt64(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteInt64(*args)
    def WriteFloat(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteFloat(*args)
    def WriteDouble(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteDouble(*args)
    def WriteShort(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteShort(*args)
    def WriteVarint32(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteVarint32(*args)
    def WriteVarint64(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteVarint64(*args)
    def Prepend(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Prepend(*args)
    def PrependUntil(*args): return _iobuffer_pywrapiobuffer.IOBuffer_PrependUntil(*args)
    def PrependString(*args): return _iobuffer_pywrapiobuffer.IOBuffer_PrependString(*args)
    def GrowPrependRegion(*args): return _iobuffer_pywrapiobuffer.IOBuffer_GrowPrependRegion(*args)
    def ReadToString(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadToString(*args)
    def ReadToStringN(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadToStringN(*args)
    def ReadVarint32(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadVarint32(*args)
    def ReadVarint64(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadVarint64(*args)
    def Unread(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Unread(*args)
    def Skip(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Skip(*args)
    def SetPin(*args): return _iobuffer_pywrapiobuffer.IOBuffer_SetPin(*args)
    def ClearPin(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ClearPin(*args)
    def UnreadToPin(*args): return _iobuffer_pywrapiobuffer.IOBuffer_UnreadToPin(*args)
    def is_pinned(*args): return _iobuffer_pywrapiobuffer.IOBuffer_is_pinned(*args)
    def PrefixMatch(*args): return _iobuffer_pywrapiobuffer.IOBuffer_PrefixMatch(*args)
    def SuffixMatch(*args): return _iobuffer_pywrapiobuffer.IOBuffer_SuffixMatch(*args)
    def TruncateToLength(*args): return _iobuffer_pywrapiobuffer.IOBuffer_TruncateToLength(*args)
    def WriteFD(*args): return _iobuffer_pywrapiobuffer.IOBuffer_WriteFD(*args)
    def ReadFDOld(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadFDOld(*args)
    def ReadFD(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadFD(*args)
    def Length(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Length(*args)
    def LengthAtLeast(*args): return _iobuffer_pywrapiobuffer.IOBuffer_LengthAtLeast(*args)
    def IsEmpty(*args): return _iobuffer_pywrapiobuffer.IOBuffer_IsEmpty(*args)
    def Clear(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Clear(*args)
    def Index(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Index(*args)
    def IndexN(*args): return _iobuffer_pywrapiobuffer.IOBuffer_IndexN(*args)
    def block_size(*args): return _iobuffer_pywrapiobuffer.IOBuffer_block_size(*args)
    def prepend_size(*args): return _iobuffer_pywrapiobuffer.IOBuffer_prepend_size(*args)
    def set_block_size(*args): return _iobuffer_pywrapiobuffer.IOBuffer_set_block_size(*args)
    def set_max_readfd_length(*args): return _iobuffer_pywrapiobuffer.IOBuffer_set_max_readfd_length(*args)
    def reset_max_readfd_length(*args): return _iobuffer_pywrapiobuffer.IOBuffer_reset_max_readfd_length(*args)
    def GetMaxReadLength(*args): return _iobuffer_pywrapiobuffer.IOBuffer_GetMaxReadLength(*args)
    def GetReadPosition(*args): return _iobuffer_pywrapiobuffer.IOBuffer_GetReadPosition(*args)
    def SetReadPosition(*args): return _iobuffer_pywrapiobuffer.IOBuffer_SetReadPosition(*args)
    def Buffer(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Buffer(*args)
    def CheckRep(*args): return _iobuffer_pywrapiobuffer.IOBuffer_CheckRep(*args)
    def Prefetch(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Prefetch(*args)
    def Read(*args): return _iobuffer_pywrapiobuffer.IOBuffer_Read(*args)
    def ReadAtMost(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadAtMost(*args)
    def ReadFast(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadFast(*args)
    def ReadUntil(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadUntil(*args)
    def ReadLine(*args): return _iobuffer_pywrapiobuffer.IOBuffer_ReadLine(*args)

class IOBufferPtr(IOBuffer):
    def __init__(self, this):
        _swig_setattr(self, IOBuffer, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, IOBuffer, 'thisown', 0)
        _swig_setattr(self, IOBuffer,self.__class__,IOBuffer)
_iobuffer_pywrapiobuffer.IOBuffer_swigregister(IOBufferPtr)


Swap = _iobuffer_pywrapiobuffer.Swap


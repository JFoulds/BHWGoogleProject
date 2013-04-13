# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _stats_io_pywrapexpvar

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
        _swig_setattr(self, stringVector, 'this', _stats_io_pywrapexpvar.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_stats_io_pywrapexpvar.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_stats_io_pywrapexpvar.stringVector_swigregister(stringVectorPtr)

EV_SENTINEL = _stats_io_pywrapexpvar.EV_SENTINEL

SetExportedVariableFormatTestMode = _stats_io_pywrapexpvar.SetExportedVariableFormatTestMode
class ExportedVariableList(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ExportedVariableList, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ExportedVariableList, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C ExportedVariableList instance at %s>" % (self.this,)
    def __del__(self, destroy=_stats_io_pywrapexpvar.delete_ExportedVariableList):
        try:
            if self.thisown: destroy(self)
        except: pass
    EMIT_VALUE = _stats_io_pywrapexpvar.ExportedVariableList_EMIT_VALUE
    EMIT_DOCSTRING = _stats_io_pywrapexpvar.ExportedVariableList_EMIT_DOCSTRING
    EMIT_BOTH = _stats_io_pywrapexpvar.ExportedVariableList_EMIT_BOTH
    __swig_getmethods__["PrintAll"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintAll
    if _newclass:PrintAll = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintAll)
    __swig_getmethods__["PrintAllInHTML"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintAllInHTML
    if _newclass:PrintAllInHTML = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintAllInHTML)
    __swig_getmethods__["PrintAllToPB"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintAllToPB
    if _newclass:PrintAllToPB = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintAllToPB)
    __swig_getmethods__["PrintSelected"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintSelected
    if _newclass:PrintSelected = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintSelected)
    __swig_getmethods__["PrintSelectedInHTML"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedInHTML
    if _newclass:PrintSelectedInHTML = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedInHTML)
    __swig_getmethods__["PrintSelectedToPB"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedToPB
    if _newclass:PrintSelectedToPB = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedToPB)
    __swig_getmethods__["PrintMatched"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintMatched
    if _newclass:PrintMatched = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintMatched)
    __swig_getmethods__["PrintMatchedInHTML"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedInHTML
    if _newclass:PrintMatchedInHTML = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedInHTML)
    __swig_getmethods__["PrintMatchedToPB"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedToPB
    if _newclass:PrintMatchedToPB = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedToPB)
    __swig_getmethods__["Print"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_Print
    if _newclass:Print = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_Print)
    __swig_getmethods__["PrintQuotedString"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_PrintQuotedString
    if _newclass:PrintQuotedString = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_PrintQuotedString)
    __swig_getmethods__["ExtractAll"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_ExtractAll
    if _newclass:ExtractAll = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_ExtractAll)
    __swig_getmethods__["ExtractSelected"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_ExtractSelected
    if _newclass:ExtractSelected = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_ExtractSelected)
    __swig_getmethods__["ExtractMatched"] = lambda x: _stats_io_pywrapexpvar.ExportedVariableList_ExtractMatched
    if _newclass:ExtractMatched = staticmethod(_stats_io_pywrapexpvar.ExportedVariableList_ExtractMatched)

class ExportedVariableListPtr(ExportedVariableList):
    def __init__(self, this):
        _swig_setattr(self, ExportedVariableList, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ExportedVariableList, 'thisown', 0)
        _swig_setattr(self, ExportedVariableList,self.__class__,ExportedVariableList)
_stats_io_pywrapexpvar.ExportedVariableList_swigregister(ExportedVariableListPtr)

ExportedVariableList_PrintAll = _stats_io_pywrapexpvar.ExportedVariableList_PrintAll

ExportedVariableList_PrintAllInHTML = _stats_io_pywrapexpvar.ExportedVariableList_PrintAllInHTML

ExportedVariableList_PrintAllToPB = _stats_io_pywrapexpvar.ExportedVariableList_PrintAllToPB

ExportedVariableList_PrintSelected = _stats_io_pywrapexpvar.ExportedVariableList_PrintSelected

ExportedVariableList_PrintSelectedInHTML = _stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedInHTML

ExportedVariableList_PrintSelectedToPB = _stats_io_pywrapexpvar.ExportedVariableList_PrintSelectedToPB

ExportedVariableList_PrintMatched = _stats_io_pywrapexpvar.ExportedVariableList_PrintMatched

ExportedVariableList_PrintMatchedInHTML = _stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedInHTML

ExportedVariableList_PrintMatchedToPB = _stats_io_pywrapexpvar.ExportedVariableList_PrintMatchedToPB

ExportedVariableList_Print = _stats_io_pywrapexpvar.ExportedVariableList_Print

ExportedVariableList_PrintQuotedString = _stats_io_pywrapexpvar.ExportedVariableList_PrintQuotedString

ExportedVariableList_ExtractAll = _stats_io_pywrapexpvar.ExportedVariableList_ExtractAll

ExportedVariableList_ExtractSelected = _stats_io_pywrapexpvar.ExportedVariableList_ExtractSelected

ExportedVariableList_ExtractMatched = _stats_io_pywrapexpvar.ExportedVariableList_ExtractMatched

class ExportedVariableMapExportInterface(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ExportedVariableMapExportInterface, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ExportedVariableMapExportInterface, name)
    def __repr__(self):
        return "<C ExportedVariableMapExportInterface instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, ExportedVariableMapExportInterface, 'this', _stats_io_pywrapexpvar.new_ExportedVariableMapExportInterface(*args))
        _swig_setattr(self, ExportedVariableMapExportInterface, 'thisown', 1)
    def __del__(self, destroy=_stats_io_pywrapexpvar.delete_ExportedVariableMapExportInterface):
        try:
            if self.thisown: destroy(self)
        except: pass

class ExportedVariableMapExportInterfacePtr(ExportedVariableMapExportInterface):
    def __init__(self, this):
        _swig_setattr(self, ExportedVariableMapExportInterface, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ExportedVariableMapExportInterface, 'thisown', 0)
        _swig_setattr(self, ExportedVariableMapExportInterface,self.__class__,ExportedVariableMapExportInterface)
_stats_io_pywrapexpvar.ExportedVariableMapExportInterface_swigregister(ExportedVariableMapExportInterfacePtr)

class ExportedVariableMap(ExportedVariableList):
    __swig_setmethods__ = {}
    for _s in [ExportedVariableList]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ExportedVariableMap, name, value)
    __swig_getmethods__ = {}
    for _s in [ExportedVariableList]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ExportedVariableMap, name)
    def __repr__(self):
        return "<C ExportedVariableMap instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, ExportedVariableMap, 'this', _stats_io_pywrapexpvar.new_ExportedVariableMap(*args))
        _swig_setattr(self, ExportedVariableMap, 'thisown', 1)
    def __del__(self, destroy=_stats_io_pywrapexpvar.delete_ExportedVariableMap):
        try:
            if self.thisown: destroy(self)
        except: pass
    def RegisterQueryCallback(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_RegisterQueryCallback(*args)
    def RemoveQueryCallback(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_RemoveQueryCallback(*args)
    def HasKey(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_HasKey(*args)
    def GetKeys(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_GetKeys(*args)
    def Erase(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_Erase(*args)
    def Clear(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_Clear(*args)
    def Size(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_Size(*args)
    def SetValue(*args): return _stats_io_pywrapexpvar.ExportedVariableMap_SetValue(*args)

class ExportedVariableMapPtr(ExportedVariableMap):
    def __init__(self, this):
        _swig_setattr(self, ExportedVariableMap, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ExportedVariableMap, 'thisown', 0)
        _swig_setattr(self, ExportedVariableMap,self.__class__,ExportedVariableMap)
_stats_io_pywrapexpvar.ExportedVariableMap_swigregister(ExportedVariableMapPtr)

import inspect

def ExpVarAnnotate(docstring, depth=2):
  """Add expvar annotation to the docstring, similar to EV_DOC macro.

  This function gets filename/line information about function one level above
  in the python stack. Filename is changed to be relative to google3.
  EV_SENTINEL is prepended at the beginning of the string.

  Args:
    docstring: the docstring.
    depth: number of frames to go up.
  Returns:
    a string, the docstring with added annotation.
  """
  filename, line = ("unknown(python)", -1)
  # TODO(bohdan): Use better detection method as discussed in http://cl/5776621
  try:
    c_frame = inspect.currentframe()
    outer_frame = inspect.getouterframes(c_frame)[depth]
    filename, line = (outer_frame[1], outer_frame[2])
  except Exception:  # We don't want to abort the program if introspection
                     # fails. It may fail, for example, if psyco is used.
    pass
  google3_string = "google3/"
  google3_index = filename.rfind(google3_string)
  if google3_index != -1:
    filename = filename[google3_index + len(google3_string):]
  return "%s%s:%s: %s" % (EV_SENTINEL, filename, line == -1 and "?" or line,
                          docstring)

def ExportedResultCallback(name, cb, docstring=None):
  if docstring is None:
    return WrapExportedResultCallback(name, cb)
  else:
    return WrapExportedResultCallback(name, cb, ExpVarAnnotate(docstring))

class WrapExportedResultCallback(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, WrapExportedResultCallback, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, WrapExportedResultCallback, name)
    def __repr__(self):
        return "<C WrapExportedResultCallback instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, WrapExportedResultCallback, 'this', _stats_io_pywrapexpvar.new_WrapExportedResultCallback(*args))
        _swig_setattr(self, WrapExportedResultCallback, 'thisown', 1)
    def __del__(self, destroy=_stats_io_pywrapexpvar.delete_WrapExportedResultCallback):
        try:
            if self.thisown: destroy(self)
        except: pass

class WrapExportedResultCallbackPtr(WrapExportedResultCallback):
    def __init__(self, this):
        _swig_setattr(self, WrapExportedResultCallback, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, WrapExportedResultCallback, 'thisown', 0)
        _swig_setattr(self, WrapExportedResultCallback,self.__class__,WrapExportedResultCallback)
_stats_io_pywrapexpvar.WrapExportedResultCallback_swigregister(WrapExportedResultCallbackPtr)



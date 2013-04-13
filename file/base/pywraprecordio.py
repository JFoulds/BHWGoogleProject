# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _file_base_pywraprecordio

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
        _swig_setattr(self, stringVector, 'this', _file_base_pywraprecordio.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_file_base_pywraprecordio.stringVector_swigregister(stringVectorPtr)

class RecordIO(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordIO, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordIO, name)
    def __repr__(self):
        return "<C RecordIO instance at %s>" % (self.this,)
    kRecSize = _file_base_pywraprecordio.RecordIO_kRecSize
    kHeaderSize = _file_base_pywraprecordio.RecordIO_kHeaderSize
    kPhysicalRecSize = _file_base_pywraprecordio.RecordIO_kPhysicalRecSize
    kLegacySyncMarker = _file_base_pywraprecordio.RecordIO_kLegacySyncMarker
    kMaxRecordSize = _file_base_pywraprecordio.RecordIO_kMaxRecordSize
    SINGLETON = _file_base_pywraprecordio.RecordIO_SINGLETON
    FIXED_SIZE = _file_base_pywraprecordio.RecordIO_FIXED_SIZE
    VARIABLE_SIZE = _file_base_pywraprecordio.RecordIO_VARIABLE_SIZE
    OTHER_TAG = _file_base_pywraprecordio.RecordIO_OTHER_TAG
    ZLIB_TAG = _file_base_pywraprecordio.RecordIO_ZLIB_TAG
    CWZ_TAG = _file_base_pywraprecordio.RecordIO_CWZ_TAG
    CW_TAG = _file_base_pywraprecordio.RecordIO_CW_TAG
    ZIPPY_TAG = _file_base_pywraprecordio.RecordIO_ZIPPY_TAG
    MIN_TAG = _file_base_pywraprecordio.RecordIO_MIN_TAG
    MAX_TAG = _file_base_pywraprecordio.RecordIO_MAX_TAG
    NUM_TAGS = _file_base_pywraprecordio.RecordIO_NUM_TAGS
    def __init__(self, *args):
        _swig_setattr(self, RecordIO, 'this', _file_base_pywraprecordio.new_RecordIO(*args))
        _swig_setattr(self, RecordIO, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordIO):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordIOPtr(RecordIO):
    def __init__(self, this):
        _swig_setattr(self, RecordIO, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordIO, 'thisown', 0)
        _swig_setattr(self, RecordIO,self.__class__,RecordIO)
_file_base_pywraprecordio.RecordIO_swigregister(RecordIOPtr)

class RecordWriter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordWriter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordWriter, name)
    def __repr__(self):
        return "<C RecordWriter instance at %s>" % (self.this,)
    kDefaultBufferSize = _file_base_pywraprecordio.RecordWriter_kDefaultBufferSize
    SINGLE_WRITER = _file_base_pywraprecordio.RecordWriter_SINGLE_WRITER
    CONCURRENT_APPENDERS = _file_base_pywraprecordio.RecordWriter_CONCURRENT_APPENDERS
    AUTO = _file_base_pywraprecordio.RecordWriter_AUTO
    def __init__(self, *args):
        _swig_setattr(self, RecordWriter, 'this', _file_base_pywraprecordio.new_RecordWriter(*args))
        _swig_setattr(self, RecordWriter, 'thisown', 1)
    __swig_getmethods__["Open"] = lambda x: _file_base_pywraprecordio.RecordWriter_Open
    if _newclass:Open = staticmethod(_file_base_pywraprecordio.RecordWriter_Open)
    __swig_getmethods__["OpenOrDie"] = lambda x: _file_base_pywraprecordio.RecordWriter_OpenOrDie
    if _newclass:OpenOrDie = staticmethod(_file_base_pywraprecordio.RecordWriter_OpenOrDie)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordWriter):
        try:
            if self.thisown: destroy(self)
        except: pass
    def SetVerifier(*args): return _file_base_pywraprecordio.RecordWriter_SetVerifier(*args)
    def Close(*args): return _file_base_pywraprecordio.RecordWriter_Close(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywraprecordio.RecordWriter_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywraprecordio.RecordWriter_owns_file(*args)
    def NoSyncOnClose(*args): return _file_base_pywraprecordio.RecordWriter_NoSyncOnClose(*args)
    def EnableCompression(*args): return _file_base_pywraprecordio.RecordWriter_EnableCompression(*args)
    def EnableZippyCompression(*args): return _file_base_pywraprecordio.RecordWriter_EnableZippyCompression(*args)
    def EnableCWCompression(*args): return _file_base_pywraprecordio.RecordWriter_EnableCWCompression(*args)
    def DisableCompression(*args): return _file_base_pywraprecordio.RecordWriter_DisableCompression(*args)
    WRITE_ERROR = _file_base_pywraprecordio.RecordWriter_WRITE_ERROR
    WRITE_OK = _file_base_pywraprecordio.RecordWriter_WRITE_OK
    WRITE_RETRY = _file_base_pywraprecordio.RecordWriter_WRITE_RETRY
    def WriteRecord(*args): return _file_base_pywraprecordio.RecordWriter_WriteRecord(*args)
    def TryWriteRecord(*args): return _file_base_pywraprecordio.RecordWriter_TryWriteRecord(*args)
    def WriteProtocolMessage(*args): return _file_base_pywraprecordio.RecordWriter_WriteProtocolMessage(*args)
    def TryWriteProtocolMessage(*args): return _file_base_pywraprecordio.RecordWriter_TryWriteProtocolMessage(*args)
    def Flush(*args): return _file_base_pywraprecordio.RecordWriter_Flush(*args)
    def Sync(*args): return _file_base_pywraprecordio.RecordWriter_Sync(*args)
    def DataSync(*args): return _file_base_pywraprecordio.RecordWriter_DataSync(*args)
    def Tell(*args): return _file_base_pywraprecordio.RecordWriter_Tell(*args)
    def ApproximateTell(*args): return _file_base_pywraprecordio.RecordWriter_ApproximateTell(*args)
    def GetCurrentErrorMessage(*args): return _file_base_pywraprecordio.RecordWriter_GetCurrentErrorMessage(*args)
    def GetCurrentErrorCode(*args): return _file_base_pywraprecordio.RecordWriter_GetCurrentErrorCode(*args)
    def Checkpoint(*args): return _file_base_pywraprecordio.RecordWriter_Checkpoint(*args)
    def GetFileName(*args): return _file_base_pywraprecordio.RecordWriter_GetFileName(*args)
    def max_record_size(*args): return _file_base_pywraprecordio.RecordWriter_max_record_size(*args)
    def SetMaxFileLength(*args): return _file_base_pywraprecordio.RecordWriter_SetMaxFileLength(*args)
    def AsyncEnabled(*args): return _file_base_pywraprecordio.RecordWriter_AsyncEnabled(*args)
    def FormatHeader(*args): return _file_base_pywraprecordio.RecordWriter_FormatHeader(*args)
    def VerifyRecord(*args): return _file_base_pywraprecordio.RecordWriter_VerifyRecord(*args)
    def WriteRecordString(*args): return _file_base_pywraprecordio.RecordWriter_WriteRecordString(*args)

class RecordWriterPtr(RecordWriter):
    def __init__(self, this):
        _swig_setattr(self, RecordWriter, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordWriter, 'thisown', 0)
        _swig_setattr(self, RecordWriter,self.__class__,RecordWriter)
_file_base_pywraprecordio.RecordWriter_swigregister(RecordWriterPtr)

RecordWriter_Open = _file_base_pywraprecordio.RecordWriter_Open

RecordWriter_OpenOrDie = _file_base_pywraprecordio.RecordWriter_OpenOrDie

class RecordReader(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReader, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReader, name)
    def __repr__(self):
        return "<C RecordReader instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReader, 'this', _file_base_pywraprecordio.new_RecordReader(*args))
        _swig_setattr(self, RecordReader, 'thisown', 1)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordReader):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Close(*args): return _file_base_pywraprecordio.RecordReader_Close(*args)
    def RelinquishFileOwnership(*args): return _file_base_pywraprecordio.RecordReader_RelinquishFileOwnership(*args)
    def owns_file(*args): return _file_base_pywraprecordio.RecordReader_owns_file(*args)
    def AsyncReadEnabled(*args): return _file_base_pywraprecordio.RecordReader_AsyncReadEnabled(*args)
    READ_OK = _file_base_pywraprecordio.RecordReader_READ_OK
    READ_DONE = _file_base_pywraprecordio.RecordReader_READ_DONE
    READ_RETRY = _file_base_pywraprecordio.RecordReader_READ_RETRY
    def Tell(*args): return _file_base_pywraprecordio.RecordReader_Tell(*args)
    def PhysicalTell(*args): return _file_base_pywraprecordio.RecordReader_PhysicalTell(*args)
    def FileTell(*args): return _file_base_pywraprecordio.RecordReader_FileTell(*args)
    def LastRecordPosition(*args): return _file_base_pywraprecordio.RecordReader_LastRecordPosition(*args)
    def Size(*args): return _file_base_pywraprecordio.RecordReader_Size(*args)
    def AtEOF(*args): return _file_base_pywraprecordio.RecordReader_AtEOF(*args)
    def Seek(*args): return _file_base_pywraprecordio.RecordReader_Seek(*args)
    def FileSeek(*args): return _file_base_pywraprecordio.RecordReader_FileSeek(*args)
    def GetPosition(*args): return _file_base_pywraprecordio.RecordReader_GetPosition(*args)
    def SetPosition(*args): return _file_base_pywraprecordio.RecordReader_SetPosition(*args)
    def Prefetch(*args): return _file_base_pywraprecordio.RecordReader_Prefetch(*args)
    def Unfetch(*args): return _file_base_pywraprecordio.RecordReader_Unfetch(*args)
    def GetFileName(*args): return _file_base_pywraprecordio.RecordReader_GetFileName(*args)
    def Stat(*args): return _file_base_pywraprecordio.RecordReader_Stat(*args)
    def set_log_skips(*args): return _file_base_pywraprecordio.RecordReader_set_log_skips(*args)
    def skipped_bytes(*args): return _file_base_pywraprecordio.RecordReader_skipped_bytes(*args)
    def skipped_regions(*args): return _file_base_pywraprecordio.RecordReader_skipped_regions(*args)
    def read_error(*args): return _file_base_pywraprecordio.RecordReader_read_error(*args)
    def clear_read_error(*args): return _file_base_pywraprecordio.RecordReader_clear_read_error(*args)
    def set_max_record_length(*args): return _file_base_pywraprecordio.RecordReader_set_max_record_length(*args)
    def set_max_decoded_record_length(*args): return _file_base_pywraprecordio.RecordReader_set_max_decoded_record_length(*args)
    kDefaultMaxExpectedRecordLength = _file_base_pywraprecordio.RecordReader_kDefaultMaxExpectedRecordLength
    def set_max_expected_record_length(*args): return _file_base_pywraprecordio.RecordReader_set_max_expected_record_length(*args)
    def set_die_on_error(*args): return _file_base_pywraprecordio.RecordReader_set_die_on_error(*args)

class RecordReaderPtr(RecordReader):
    def __init__(self, this):
        _swig_setattr(self, RecordReader, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReader, 'thisown', 0)
        _swig_setattr(self, RecordReader,self.__class__,RecordReader)
_file_base_pywraprecordio.RecordReader_swigregister(RecordReaderPtr)

class RecordReaderOptions(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReaderOptions, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReaderOptions, name)
    def __repr__(self):
        return "<C RecordReaderOptions instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReaderOptions, 'this', _file_base_pywraprecordio.new_RecordReaderOptions(*args))
        _swig_setattr(self, RecordReaderOptions, 'thisown', 1)
    def set_memory_budget(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_memory_budget(*args)
    def memory_budget(*args): return _file_base_pywraprecordio.RecordReaderOptions_memory_budget(*args)
    def set_enable_aio(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_enable_aio(*args)
    def enable_aio(*args): return _file_base_pywraprecordio.RecordReaderOptions_enable_aio(*args)
    def set_buffer_size(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_buffer_size(*args)
    def buffer_size(*args): return _file_base_pywraprecordio.RecordReaderOptions_buffer_size(*args)
    def set_lookahead(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_lookahead(*args)
    def lookahead(*args): return _file_base_pywraprecordio.RecordReaderOptions_lookahead(*args)
    def set_fixed_size(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_fixed_size(*args)
    def fixed_size(*args): return _file_base_pywraprecordio.RecordReaderOptions_fixed_size(*args)
    def set_lookahead_on_open(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_lookahead_on_open(*args)
    def lookahead_on_open(*args): return _file_base_pywraprecordio.RecordReaderOptions_lookahead_on_open(*args)
    def set_initial_seek_back(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_initial_seek_back(*args)
    def initial_seek_back(*args): return _file_base_pywraprecordio.RecordReaderOptions_initial_seek_back(*args)
    def set_allow_unchecked_records(*args): return _file_base_pywraprecordio.RecordReaderOptions_set_allow_unchecked_records(*args)
    def allow_unchecked_records(*args): return _file_base_pywraprecordio.RecordReaderOptions_allow_unchecked_records(*args)
    def LoadOptionsFromString(*args): return _file_base_pywraprecordio.RecordReaderOptions_LoadOptionsFromString(*args)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordReaderOptions):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordReaderOptionsPtr(RecordReaderOptions):
    def __init__(self, this):
        _swig_setattr(self, RecordReaderOptions, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReaderOptions, 'thisown', 0)
        _swig_setattr(self, RecordReaderOptions,self.__class__,RecordReaderOptions)
_file_base_pywraprecordio.RecordReaderOptions_swigregister(RecordReaderOptionsPtr)

class RecordVerifier(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordVerifier, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordVerifier, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C RecordVerifier instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordVerifier):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Verify(*args): return _file_base_pywraprecordio.RecordVerifier_Verify(*args)

class RecordVerifierPtr(RecordVerifier):
    def __init__(self, this):
        _swig_setattr(self, RecordVerifier, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordVerifier, 'thisown', 0)
        _swig_setattr(self, RecordVerifier,self.__class__,RecordVerifier)
_file_base_pywraprecordio.RecordVerifier_swigregister(RecordVerifierPtr)

class RecordWriterOpener(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordWriterOpener, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RecordWriterOpener, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C RecordWriterOpener instance at %s>" % (self.this,)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordWriterOpener):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordWriterOpenerPtr(RecordWriterOpener):
    def __init__(self, this):
        _swig_setattr(self, RecordWriterOpener, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordWriterOpener, 'thisown', 0)
        _swig_setattr(self, RecordWriterOpener,self.__class__,RecordWriterOpener)
_file_base_pywraprecordio.RecordWriterOpener_swigregister(RecordWriterOpenerPtr)

class RecordReaderScript(RecordReader):
    __swig_setmethods__ = {}
    for _s in [RecordReader]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RecordReaderScript, name, value)
    __swig_getmethods__ = {}
    for _s in [RecordReader]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RecordReaderScript, name)
    def __repr__(self):
        return "<C RecordReaderScript instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RecordReaderScript, 'this', _file_base_pywraprecordio.new_RecordReaderScript(*args))
        _swig_setattr(self, RecordReaderScript, 'thisown', 1)
    def ReadRecordIntoString(*args): return _file_base_pywraprecordio.RecordReaderScript_ReadRecordIntoString(*args)
    def __del__(self, destroy=_file_base_pywraprecordio.delete_RecordReaderScript):
        try:
            if self.thisown: destroy(self)
        except: pass

class RecordReaderScriptPtr(RecordReaderScript):
    def __init__(self, this):
        _swig_setattr(self, RecordReaderScript, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RecordReaderScript, 'thisown', 0)
        _swig_setattr(self, RecordReaderScript,self.__class__,RecordReaderScript)
_file_base_pywraprecordio.RecordReaderScript_swigregister(RecordReaderScriptPtr)



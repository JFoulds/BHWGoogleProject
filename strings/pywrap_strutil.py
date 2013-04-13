# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _strings_pywrap__strutil

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
        _swig_setattr(self, stringVector, 'this', _strings_pywrap__strutil.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_strings_pywrap__strutil.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_strings_pywrap__strutil.stringVector_swigregister(stringVectorPtr)

class TagMapper(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TagMapper, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TagMapper, name)
    def __repr__(self):
        return "<C TagMapper instance at %s>" % (self.this,)
    TYPE_ERROR = _strings_pywrap__strutil.TagMapper_TYPE_ERROR
    TYPE_DOUBLE = _strings_pywrap__strutil.TagMapper_TYPE_DOUBLE
    TYPE_FLOAT = _strings_pywrap__strutil.TagMapper_TYPE_FLOAT
    TYPE_INT64 = _strings_pywrap__strutil.TagMapper_TYPE_INT64
    TYPE_UINT64 = _strings_pywrap__strutil.TagMapper_TYPE_UINT64
    TYPE_INT32 = _strings_pywrap__strutil.TagMapper_TYPE_INT32
    TYPE_FIXED64 = _strings_pywrap__strutil.TagMapper_TYPE_FIXED64
    TYPE_FIXED32 = _strings_pywrap__strutil.TagMapper_TYPE_FIXED32
    TYPE_BOOL = _strings_pywrap__strutil.TagMapper_TYPE_BOOL
    TYPE_STRING = _strings_pywrap__strutil.TagMapper_TYPE_STRING
    TYPE_GROUP = _strings_pywrap__strutil.TagMapper_TYPE_GROUP
    TYPE_FOREIGN = _strings_pywrap__strutil.TagMapper_TYPE_FOREIGN
    NUM_TYPES = _strings_pywrap__strutil.TagMapper_NUM_TYPES
    TAG_OPTION_DPL_NOINDEX = _strings_pywrap__strutil.TagMapper_TAG_OPTION_DPL_NOINDEX
    TAG_OPTION_DPL_SNIPPETS = _strings_pywrap__strutil.TagMapper_TAG_OPTION_DPL_SNIPPETS
    TAG_OPTION_DPL_FLATTEN = _strings_pywrap__strutil.TagMapper_TAG_OPTION_DPL_FLATTEN
    UTF8_STRINGS = _strings_pywrap__strutil.TagMapper_UTF8_STRINGS
    RAW_STRINGS = _strings_pywrap__strutil.TagMapper_RAW_STRINGS
    UTF8_AND_RAW_STRINGS = _strings_pywrap__strutil.TagMapper_UTF8_AND_RAW_STRINGS
    LATIN1_STRINGS = _strings_pywrap__strutil.TagMapper_LATIN1_STRINGS
    def __del__(self, destroy=_strings_pywrap__strutil.delete_TagMapper):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, TagMapper, 'this', _strings_pywrap__strutil.new_TagMapper(*args))
        _swig_setattr(self, TagMapper, 'thisown', 1)
    def FixForeignFields(*args): return _strings_pywrap__strutil.TagMapper_FixForeignFields(*args)
    __swig_getmethods__["FixAllForeignFields"] = lambda x: _strings_pywrap__strutil.TagMapper_FixAllForeignFields
    if _newclass:FixAllForeignFields = staticmethod(_strings_pywrap__strutil.TagMapper_FixAllForeignFields)
    def tag_count(*args): return _strings_pywrap__strutil.TagMapper_tag_count(*args)
    def largest_tag(*args): return _strings_pywrap__strutil.TagMapper_largest_tag(*args)
    def name(*args): return _strings_pywrap__strutil.TagMapper_name(*args)
    def type_id(*args): return _strings_pywrap__strutil.TagMapper_type_id(*args)
    def stylesheet(*args): return _strings_pywrap__strutil.TagMapper_stylesheet(*args)
    def stylesheet_content_type(*args): return _strings_pywrap__strutil.TagMapper_stylesheet_content_type(*args)
    def GetProtocolDescriptor(*args): return _strings_pywrap__strutil.TagMapper_GetProtocolDescriptor(*args)
    def FromTag(*args): return _strings_pywrap__strutil.TagMapper_FromTag(*args)
    def FromName(*args): return _strings_pywrap__strutil.TagMapper_FromName(*args)
    def FromOrderInFile(*args): return _strings_pywrap__strutil.TagMapper_FromOrderInFile(*args)
    def GenerateASCII(*args): return _strings_pywrap__strutil.TagMapper_GenerateASCII(*args)
    def GenerateCompactASCII(*args): return _strings_pywrap__strutil.TagMapper_GenerateCompactASCII(*args)
    def GenerateShortASCII(*args): return _strings_pywrap__strutil.TagMapper_GenerateShortASCII(*args)
    def ParseASCII(*args): return _strings_pywrap__strutil.TagMapper_ParseASCII(*args)
    def GenerateXmlProlog(*args): return _strings_pywrap__strutil.TagMapper_GenerateXmlProlog(*args)
    def GenerateXmlElements(*args): return _strings_pywrap__strutil.TagMapper_GenerateXmlElements(*args)
    def GenerateXmlDocument(*args): return _strings_pywrap__strutil.TagMapper_GenerateXmlDocument(*args)
    def ParseURLArgs(*args): return _strings_pywrap__strutil.TagMapper_ParseURLArgs(*args)
    def ParseSimpleASCII(*args): return _strings_pywrap__strutil.TagMapper_ParseSimpleASCII(*args)
    def GenerateSimpleASCII(*args): return _strings_pywrap__strutil.TagMapper_GenerateSimpleASCII(*args)
    __swig_getmethods__["GenerateForm"] = lambda x: _strings_pywrap__strutil.TagMapper_GenerateForm
    if _newclass:GenerateForm = staticmethod(_strings_pywrap__strutil.TagMapper_GenerateForm)
    __swig_getmethods__["ParseURLArgsFromForm"] = lambda x: _strings_pywrap__strutil.TagMapper_ParseURLArgsFromForm
    if _newclass:ParseURLArgsFromForm = staticmethod(_strings_pywrap__strutil.TagMapper_ParseURLArgsFromForm)
    def GenerateFormRedirect(*args): return _strings_pywrap__strutil.TagMapper_GenerateFormRedirect(*args)
    def GenerateForm(*args): return _strings_pywrap__strutil.TagMapper_GenerateForm(*args)
    def GenerateFormInstructions(*args): return _strings_pywrap__strutil.TagMapper_GenerateFormInstructions(*args)
    def DebugString(*args): return _strings_pywrap__strutil.TagMapper_DebugString(*args)
    __swig_getmethods__["LengthString"] = lambda x: _strings_pywrap__strutil.TagMapper_LengthString
    if _newclass:LengthString = staticmethod(_strings_pywrap__strutil.TagMapper_LengthString)
    __swig_getmethods__["FindByName"] = lambda x: _strings_pywrap__strutil.TagMapper_FindByName
    if _newclass:FindByName = staticmethod(_strings_pywrap__strutil.TagMapper_FindByName)
    __swig_getmethods__["FindByTypeId"] = lambda x: _strings_pywrap__strutil.TagMapper_FindByTypeId
    if _newclass:FindByTypeId = staticmethod(_strings_pywrap__strutil.TagMapper_FindByTypeId)
    __swig_getmethods__["FindByFileName"] = lambda x: _strings_pywrap__strutil.TagMapper_FindByFileName
    if _newclass:FindByFileName = staticmethod(_strings_pywrap__strutil.TagMapper_FindByFileName)
    def GetReflection(*args): return _strings_pywrap__strutil.TagMapper_GetReflection(*args)
    def message_filter(*args): return _strings_pywrap__strutil.TagMapper_message_filter(*args)
    def set_message_filter(*args): return _strings_pywrap__strutil.TagMapper_set_message_filter(*args)

class TagMapperPtr(TagMapper):
    def __init__(self, this):
        _swig_setattr(self, TagMapper, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, TagMapper, 'thisown', 0)
        _swig_setattr(self, TagMapper,self.__class__,TagMapper)
_strings_pywrap__strutil.TagMapper_swigregister(TagMapperPtr)

TagMapper_FixAllForeignFields = _strings_pywrap__strutil.TagMapper_FixAllForeignFields

TagMapper_ParseURLArgsFromForm = _strings_pywrap__strutil.TagMapper_ParseURLArgsFromForm
cvar = _strings_pywrap__strutil.cvar

TagMapper_LengthString = _strings_pywrap__strutil.TagMapper_LengthString

TagMapper_FindByName = _strings_pywrap__strutil.TagMapper_FindByName

TagMapper_FindByTypeId = _strings_pywrap__strutil.TagMapper_FindByTypeId

TagMapper_FindByFileName = _strings_pywrap__strutil.TagMapper_FindByFileName

class Protocol(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Protocol, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Protocol, name)
    def __repr__(self):
        return "<C Protocol instance at %s>" % (self.this,)
    __swig_getmethods__["tag"] = lambda x: _strings_pywrap__strutil.Protocol_tag
    if _newclass:tag = staticmethod(_strings_pywrap__strutil.Protocol_tag)
    __swig_getmethods__["type"] = lambda x: _strings_pywrap__strutil.Protocol_type
    if _newclass:type = staticmethod(_strings_pywrap__strutil.Protocol_type)
    __swig_getmethods__["combine"] = lambda x: _strings_pywrap__strutil.Protocol_combine
    if _newclass:combine = staticmethod(_strings_pywrap__strutil.Protocol_combine)
    __swig_getmethods__["Skip"] = lambda x: _strings_pywrap__strutil.Protocol_Skip
    if _newclass:Skip = staticmethod(_strings_pywrap__strutil.Protocol_Skip)
    __swig_getmethods__["SkipAndSave"] = lambda x: _strings_pywrap__strutil.Protocol_SkipAndSave
    if _newclass:SkipAndSave = staticmethod(_strings_pywrap__strutil.Protocol_SkipAndSave)
    __swig_getmethods__["SkipUnknown"] = lambda x: _strings_pywrap__strutil.Protocol_SkipUnknown
    if _newclass:SkipUnknown = staticmethod(_strings_pywrap__strutil.Protocol_SkipUnknown)
    __swig_getmethods__["ReadBool"] = lambda x: _strings_pywrap__strutil.Protocol_ReadBool
    if _newclass:ReadBool = staticmethod(_strings_pywrap__strutil.Protocol_ReadBool)
    __swig_getmethods__["ReadDouble"] = lambda x: _strings_pywrap__strutil.Protocol_ReadDouble
    if _newclass:ReadDouble = staticmethod(_strings_pywrap__strutil.Protocol_ReadDouble)
    __swig_getmethods__["ReadFloat"] = lambda x: _strings_pywrap__strutil.Protocol_ReadFloat
    if _newclass:ReadFloat = staticmethod(_strings_pywrap__strutil.Protocol_ReadFloat)
    __swig_getmethods__["ReadInt64"] = lambda x: _strings_pywrap__strutil.Protocol_ReadInt64
    if _newclass:ReadInt64 = staticmethod(_strings_pywrap__strutil.Protocol_ReadInt64)
    __swig_getmethods__["ReadUint64"] = lambda x: _strings_pywrap__strutil.Protocol_ReadUint64
    if _newclass:ReadUint64 = staticmethod(_strings_pywrap__strutil.Protocol_ReadUint64)
    __swig_getmethods__["ReadInt32"] = lambda x: _strings_pywrap__strutil.Protocol_ReadInt32
    if _newclass:ReadInt32 = staticmethod(_strings_pywrap__strutil.Protocol_ReadInt32)
    __swig_getmethods__["ReadFixed64"] = lambda x: _strings_pywrap__strutil.Protocol_ReadFixed64
    if _newclass:ReadFixed64 = staticmethod(_strings_pywrap__strutil.Protocol_ReadFixed64)
    __swig_getmethods__["ReadFixed32"] = lambda x: _strings_pywrap__strutil.Protocol_ReadFixed32
    if _newclass:ReadFixed32 = staticmethod(_strings_pywrap__strutil.Protocol_ReadFixed32)
    __swig_getmethods__["ReadString"] = lambda x: _strings_pywrap__strutil.Protocol_ReadString
    if _newclass:ReadString = staticmethod(_strings_pywrap__strutil.Protocol_ReadString)
    __swig_getmethods__["WriteTag"] = lambda x: _strings_pywrap__strutil.Protocol_WriteTag
    if _newclass:WriteTag = staticmethod(_strings_pywrap__strutil.Protocol_WriteTag)
    __swig_getmethods__["BeginGroup"] = lambda x: _strings_pywrap__strutil.Protocol_BeginGroup
    if _newclass:BeginGroup = staticmethod(_strings_pywrap__strutil.Protocol_BeginGroup)
    __swig_getmethods__["EndGroup"] = lambda x: _strings_pywrap__strutil.Protocol_EndGroup
    if _newclass:EndGroup = staticmethod(_strings_pywrap__strutil.Protocol_EndGroup)
    __swig_getmethods__["WriteDouble"] = lambda x: _strings_pywrap__strutil.Protocol_WriteDouble
    if _newclass:WriteDouble = staticmethod(_strings_pywrap__strutil.Protocol_WriteDouble)
    __swig_getmethods__["WriteFloat"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFloat
    if _newclass:WriteFloat = staticmethod(_strings_pywrap__strutil.Protocol_WriteFloat)
    __swig_getmethods__["WriteFixed64"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFixed64
    if _newclass:WriteFixed64 = staticmethod(_strings_pywrap__strutil.Protocol_WriteFixed64)
    __swig_getmethods__["WriteFixed32"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFixed32
    if _newclass:WriteFixed32 = staticmethod(_strings_pywrap__strutil.Protocol_WriteFixed32)
    __swig_getmethods__["WriteUint64"] = lambda x: _strings_pywrap__strutil.Protocol_WriteUint64
    if _newclass:WriteUint64 = staticmethod(_strings_pywrap__strutil.Protocol_WriteUint64)
    __swig_getmethods__["WriteInt32"] = lambda x: _strings_pywrap__strutil.Protocol_WriteInt32
    if _newclass:WriteInt32 = staticmethod(_strings_pywrap__strutil.Protocol_WriteInt32)
    __swig_getmethods__["WriteBool"] = lambda x: _strings_pywrap__strutil.Protocol_WriteBool
    if _newclass:WriteBool = staticmethod(_strings_pywrap__strutil.Protocol_WriteBool)
    __swig_getmethods__["WriteString"] = lambda x: _strings_pywrap__strutil.Protocol_WriteString
    if _newclass:WriteString = staticmethod(_strings_pywrap__strutil.Protocol_WriteString)
    __swig_getmethods__["WriteCString"] = lambda x: _strings_pywrap__strutil.Protocol_WriteCString
    if _newclass:WriteCString = staticmethod(_strings_pywrap__strutil.Protocol_WriteCString)
    __swig_getmethods__["WriteCord"] = lambda x: _strings_pywrap__strutil.Protocol_WriteCord
    if _newclass:WriteCord = staticmethod(_strings_pywrap__strutil.Protocol_WriteCord)
    __swig_getmethods__["WriteStringHeader"] = lambda x: _strings_pywrap__strutil.Protocol_WriteStringHeader
    if _newclass:WriteStringHeader = staticmethod(_strings_pywrap__strutil.Protocol_WriteStringHeader)
    __swig_getmethods__["WriteDoubleArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteDoubleArrayToBuffer
    if _newclass:WriteDoubleArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteDoubleArrayToBuffer)
    __swig_getmethods__["WriteFloatArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFloatArrayToBuffer
    if _newclass:WriteFloatArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteFloatArrayToBuffer)
    __swig_getmethods__["WriteFixed64ArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFixed64ArrayToBuffer
    if _newclass:WriteFixed64ArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteFixed64ArrayToBuffer)
    __swig_getmethods__["WriteFixed32ArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteFixed32ArrayToBuffer
    if _newclass:WriteFixed32ArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteFixed32ArrayToBuffer)
    __swig_getmethods__["WriteUint64ArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteUint64ArrayToBuffer
    if _newclass:WriteUint64ArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteUint64ArrayToBuffer)
    __swig_getmethods__["WriteUint64ArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteUint64ArrayToBuffer
    if _newclass:WriteUint64ArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteUint64ArrayToBuffer)
    __swig_getmethods__["WriteInt32ArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteInt32ArrayToBuffer
    if _newclass:WriteInt32ArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteInt32ArrayToBuffer)
    __swig_getmethods__["WriteBoolArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteBoolArrayToBuffer
    if _newclass:WriteBoolArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteBoolArrayToBuffer)
    __swig_getmethods__["WriteStringArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteStringArrayToBuffer
    if _newclass:WriteStringArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteStringArrayToBuffer)
    __swig_getmethods__["WriteCordArrayToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_WriteCordArrayToBuffer
    if _newclass:WriteCordArrayToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_WriteCordArrayToBuffer)
    __swig_getmethods__["MoveStringFromDataBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_MoveStringFromDataBuffer
    if _newclass:MoveStringFromDataBuffer = staticmethod(_strings_pywrap__strutil.Protocol_MoveStringFromDataBuffer)
    __swig_getmethods__["CopyBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_CopyBuffer
    if _newclass:CopyBuffer = staticmethod(_strings_pywrap__strutil.Protocol_CopyBuffer)
    __swig_getmethods__["LengthForeignMessage"] = lambda x: _strings_pywrap__strutil.Protocol_LengthForeignMessage
    if _newclass:LengthForeignMessage = staticmethod(_strings_pywrap__strutil.Protocol_LengthForeignMessage)
    __swig_getmethods__["LengthStringNonInlined"] = lambda x: _strings_pywrap__strutil.Protocol_LengthStringNonInlined
    if _newclass:LengthStringNonInlined = staticmethod(_strings_pywrap__strutil.Protocol_LengthStringNonInlined)
    __swig_getmethods__["LengthUninterpreted"] = lambda x: _strings_pywrap__strutil.Protocol_LengthUninterpreted
    if _newclass:LengthUninterpreted = staticmethod(_strings_pywrap__strutil.Protocol_LengthUninterpreted)
    __swig_getmethods__["LengthInt32"] = lambda x: _strings_pywrap__strutil.Protocol_LengthInt32
    if _newclass:LengthInt32 = staticmethod(_strings_pywrap__strutil.Protocol_LengthInt32)
    __swig_getmethods__["EmitInt32"] = lambda x: _strings_pywrap__strutil.Protocol_EmitInt32
    if _newclass:EmitInt32 = staticmethod(_strings_pywrap__strutil.Protocol_EmitInt32)
    __swig_getmethods__["PatchLengthIntoHole"] = lambda x: _strings_pywrap__strutil.Protocol_PatchLengthIntoHole
    if _newclass:PatchLengthIntoHole = staticmethod(_strings_pywrap__strutil.Protocol_PatchLengthIntoHole)
    __swig_getmethods__["SpaceUsedOutOfLineString"] = lambda x: _strings_pywrap__strutil.Protocol_SpaceUsedOutOfLineString
    if _newclass:SpaceUsedOutOfLineString = staticmethod(_strings_pywrap__strutil.Protocol_SpaceUsedOutOfLineString)
    __swig_getmethods__["CopyUninterpreted"] = lambda x: _strings_pywrap__strutil.Protocol_CopyUninterpreted
    if _newclass:CopyUninterpreted = staticmethod(_strings_pywrap__strutil.Protocol_CopyUninterpreted)
    __swig_getmethods__["AppendCordToBuffer"] = lambda x: _strings_pywrap__strutil.Protocol_AppendCordToBuffer
    if _newclass:AppendCordToBuffer = staticmethod(_strings_pywrap__strutil.Protocol_AppendCordToBuffer)
    __swig_getmethods__["AppendCordToArray"] = lambda x: _strings_pywrap__strutil.Protocol_AppendCordToArray
    if _newclass:AppendCordToArray = staticmethod(_strings_pywrap__strutil.Protocol_AppendCordToArray)
    __swig_getmethods__["RawWriteString"] = lambda x: _strings_pywrap__strutil.Protocol_RawWriteString
    if _newclass:RawWriteString = staticmethod(_strings_pywrap__strutil.Protocol_RawWriteString)
    __swig_getmethods__["RawWriteCord"] = lambda x: _strings_pywrap__strutil.Protocol_RawWriteCord
    if _newclass:RawWriteCord = staticmethod(_strings_pywrap__strutil.Protocol_RawWriteCord)
    __swig_getmethods__["SwapTypeMismatch"] = lambda x: _strings_pywrap__strutil.Protocol_SwapTypeMismatch
    if _newclass:SwapTypeMismatch = staticmethod(_strings_pywrap__strutil.Protocol_SwapTypeMismatch)
    def __init__(self, *args):
        _swig_setattr(self, Protocol, 'this', _strings_pywrap__strutil.new_Protocol(*args))
        _swig_setattr(self, Protocol, 'thisown', 1)
    def __del__(self, destroy=_strings_pywrap__strutil.delete_Protocol):
        try:
            if self.thisown: destroy(self)
        except: pass

class ProtocolPtr(Protocol):
    def __init__(self, this):
        _swig_setattr(self, Protocol, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Protocol, 'thisown', 0)
        _swig_setattr(self, Protocol,self.__class__,Protocol)
_strings_pywrap__strutil.Protocol_swigregister(ProtocolPtr)

Protocol_tag = _strings_pywrap__strutil.Protocol_tag

Protocol_type = _strings_pywrap__strutil.Protocol_type

Protocol_combine = _strings_pywrap__strutil.Protocol_combine

Protocol_Skip = _strings_pywrap__strutil.Protocol_Skip

Protocol_SkipAndSave = _strings_pywrap__strutil.Protocol_SkipAndSave

Protocol_SkipUnknown = _strings_pywrap__strutil.Protocol_SkipUnknown

Protocol_ReadBool = _strings_pywrap__strutil.Protocol_ReadBool

Protocol_ReadDouble = _strings_pywrap__strutil.Protocol_ReadDouble

Protocol_ReadFloat = _strings_pywrap__strutil.Protocol_ReadFloat

Protocol_ReadInt64 = _strings_pywrap__strutil.Protocol_ReadInt64

Protocol_ReadUint64 = _strings_pywrap__strutil.Protocol_ReadUint64

Protocol_ReadInt32 = _strings_pywrap__strutil.Protocol_ReadInt32

Protocol_ReadFixed64 = _strings_pywrap__strutil.Protocol_ReadFixed64

Protocol_ReadFixed32 = _strings_pywrap__strutil.Protocol_ReadFixed32

Protocol_ReadString = _strings_pywrap__strutil.Protocol_ReadString

Protocol_WriteTag = _strings_pywrap__strutil.Protocol_WriteTag

Protocol_BeginGroup = _strings_pywrap__strutil.Protocol_BeginGroup

Protocol_EndGroup = _strings_pywrap__strutil.Protocol_EndGroup

Protocol_WriteDouble = _strings_pywrap__strutil.Protocol_WriteDouble

Protocol_WriteFloat = _strings_pywrap__strutil.Protocol_WriteFloat

Protocol_WriteFixed64 = _strings_pywrap__strutil.Protocol_WriteFixed64

Protocol_WriteFixed32 = _strings_pywrap__strutil.Protocol_WriteFixed32

Protocol_WriteUint64 = _strings_pywrap__strutil.Protocol_WriteUint64

Protocol_WriteInt32 = _strings_pywrap__strutil.Protocol_WriteInt32

Protocol_WriteBool = _strings_pywrap__strutil.Protocol_WriteBool

Protocol_WriteString = _strings_pywrap__strutil.Protocol_WriteString

Protocol_WriteCString = _strings_pywrap__strutil.Protocol_WriteCString

Protocol_WriteCord = _strings_pywrap__strutil.Protocol_WriteCord

Protocol_WriteStringHeader = _strings_pywrap__strutil.Protocol_WriteStringHeader

Protocol_WriteDoubleArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteDoubleArrayToBuffer

Protocol_WriteFloatArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteFloatArrayToBuffer

Protocol_WriteFixed64ArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteFixed64ArrayToBuffer

Protocol_WriteFixed32ArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteFixed32ArrayToBuffer

Protocol_WriteUint64ArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteUint64ArrayToBuffer

Protocol_WriteInt32ArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteInt32ArrayToBuffer

Protocol_WriteBoolArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteBoolArrayToBuffer

Protocol_WriteStringArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteStringArrayToBuffer

Protocol_WriteCordArrayToBuffer = _strings_pywrap__strutil.Protocol_WriteCordArrayToBuffer

Protocol_MoveStringFromDataBuffer = _strings_pywrap__strutil.Protocol_MoveStringFromDataBuffer

Protocol_CopyBuffer = _strings_pywrap__strutil.Protocol_CopyBuffer

Protocol_LengthForeignMessage = _strings_pywrap__strutil.Protocol_LengthForeignMessage

Protocol_LengthStringNonInlined = _strings_pywrap__strutil.Protocol_LengthStringNonInlined

Protocol_LengthUninterpreted = _strings_pywrap__strutil.Protocol_LengthUninterpreted

Protocol_LengthInt32 = _strings_pywrap__strutil.Protocol_LengthInt32

Protocol_EmitInt32 = _strings_pywrap__strutil.Protocol_EmitInt32

Protocol_PatchLengthIntoHole = _strings_pywrap__strutil.Protocol_PatchLengthIntoHole

Protocol_SpaceUsedOutOfLineString = _strings_pywrap__strutil.Protocol_SpaceUsedOutOfLineString

Protocol_CopyUninterpreted = _strings_pywrap__strutil.Protocol_CopyUninterpreted

Protocol_AppendCordToBuffer = _strings_pywrap__strutil.Protocol_AppendCordToBuffer

Protocol_AppendCordToArray = _strings_pywrap__strutil.Protocol_AppendCordToArray

Protocol_RawWriteString = _strings_pywrap__strutil.Protocol_RawWriteString

Protocol_RawWriteCord = _strings_pywrap__strutil.Protocol_RawWriteCord

Protocol_SwapTypeMismatch = _strings_pywrap__strutil.Protocol_SwapTypeMismatch

class ProtocolMessageGroup(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolMessageGroup, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolMessageGroup, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C ProtocolMessageGroup instance at %s>" % (self.this,)
    def __del__(self, destroy=_strings_pywrap__strutil.delete_ProtocolMessageGroup):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Clear(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_Clear(*args)
    def clear(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_clear(*args)
    def FindInitializationError(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_FindInitializationError(*args)
    def CheckInitialized(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_CheckInitialized(*args)
    def AssertInitialized(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_AssertInitialized(*args)
    def AppendToString(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_AppendToString(*args)
    def RawAppendToString(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_RawAppendToString(*args)
    def AppendToStringWithOuterTags(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_AppendToStringWithOuterTags(*args)
    def RawAppendToStringWithOuterTags(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_RawAppendToStringWithOuterTags(*args)
    def MergeFromArrayWithOuterTags(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_MergeFromArrayWithOuterTags(*args)
    def ParseFromArrayWithOuterTags(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_ParseFromArrayWithOuterTags(*args)
    def ParseFromStringWithOuterTags(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_ParseFromStringWithOuterTags(*args)
    def RawOutputToBuffer(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_InternalMergeFrom(*args)
    def ByteSize(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_ByteSize(*args)
    def New(*args): return _strings_pywrap__strutil.ProtocolMessageGroup_New(*args)

class ProtocolMessageGroupPtr(ProtocolMessageGroup):
    def __init__(self, this):
        _swig_setattr(self, ProtocolMessageGroup, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolMessageGroup, 'thisown', 0)
        _swig_setattr(self, ProtocolMessageGroup,self.__class__,ProtocolMessageGroup)
_strings_pywrap__strutil.ProtocolMessageGroup_swigregister(ProtocolMessageGroupPtr)

class ProtocolMessage(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolMessage, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolMessage, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C ProtocolMessage instance at %s>" % (self.this,)
    def __del__(self, destroy=_strings_pywrap__strutil.delete_ProtocolMessage):
        try:
            if self.thisown: destroy(self)
        except: pass
    def FindInitializationError(*args): return _strings_pywrap__strutil.ProtocolMessage_FindInitializationError(*args)
    def Clear(*args): return _strings_pywrap__strutil.ProtocolMessage_Clear(*args)
    def clear(*args): return _strings_pywrap__strutil.ProtocolMessage_clear(*args)
    def RawOutputToBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _strings_pywrap__strutil.ProtocolMessage_RawOutputToArray(*args)
    def RawAppendToString(*args): return _strings_pywrap__strutil.ProtocolMessage_RawAppendToString(*args)
    def InternalMergeFrom(*args): return _strings_pywrap__strutil.ProtocolMessage_InternalMergeFrom(*args)
    def GetMapper(*args): return _strings_pywrap__strutil.ProtocolMessage_GetMapper(*args)
    def GetProtocolDescriptor(*args): return _strings_pywrap__strutil.ProtocolMessage_GetProtocolDescriptor(*args)
    def New(*args): return _strings_pywrap__strutil.ProtocolMessage_New(*args)
    def ByteSize(*args): return _strings_pywrap__strutil.ProtocolMessage_ByteSize(*args)
    def SpaceUsed(*args): return _strings_pywrap__strutil.ProtocolMessage_SpaceUsed(*args)
    def DiscardUnknownFields(*args): return _strings_pywrap__strutil.ProtocolMessage_DiscardUnknownFields(*args)
    def IsInitialized(*args): return _strings_pywrap__strutil.ProtocolMessage_IsInitialized(*args)
    def CheckInitialized(*args): return _strings_pywrap__strutil.ProtocolMessage_CheckInitialized(*args)
    def AssertInitialized(*args): return _strings_pywrap__strutil.ProtocolMessage_AssertInitialized(*args)
    def OutputToDataBufferUnchecked(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputToDataBufferUnchecked(*args)
    def OutputToDataBufferUncheckedWithSize(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputToDataBufferUncheckedWithSize(*args)
    def OutputToDataBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputToDataBuffer(*args)
    def AppendToCordUnchecked(*args): return _strings_pywrap__strutil.ProtocolMessage_AppendToCordUnchecked(*args)
    def AppendToCord(*args): return _strings_pywrap__strutil.ProtocolMessage_AppendToCord(*args)
    NO_CHECK = _strings_pywrap__strutil.ProtocolMessage_NO_CHECK
    CHECK = _strings_pywrap__strutil.ProtocolMessage_CHECK
    def OutputToDataBufferChecked(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputToDataBufferChecked(*args)
    def OutputToIOBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputToIOBuffer(*args)
    def AppendToString(*args): return _strings_pywrap__strutil.ProtocolMessage_AppendToString(*args)
    def OutputAsString(*args): return _strings_pywrap__strutil.ProtocolMessage_OutputAsString(*args)
    def DebugString(*args): return _strings_pywrap__strutil.ProtocolMessage_DebugString(*args)
    def PrintDebugString(*args): return _strings_pywrap__strutil.ProtocolMessage_PrintDebugString(*args)
    def ShortDebugString(*args): return _strings_pywrap__strutil.ProtocolMessage_ShortDebugString(*args)
    def ParseFromDataBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromDataBuffer(*args)
    def ParseFromDataBufferPrefix(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromDataBufferPrefix(*args)
    def ParseFromIOBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromIOBuffer(*args)
    def ParseFromArray(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromArray(*args)
    def ParseFromArrayWithExtra(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromArrayWithExtra(*args)
    def ParseFromString(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromString(*args)
    def ParseFromCord(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseFromCord(*args)
    def ToASCII(*args): return _strings_pywrap__strutil.ProtocolMessage_ToASCII(*args)
    def ToCompactASCII(*args): return _strings_pywrap__strutil.ProtocolMessage_ToCompactASCII(*args)
    def ToShortASCII(*args): return _strings_pywrap__strutil.ProtocolMessage_ToShortASCII(*args)
    def ParseASCII(*args): return _strings_pywrap__strutil.ProtocolMessage_ParseASCII(*args)
    def CheckTypeAndSwap(*args): return _strings_pywrap__strutil.ProtocolMessage_CheckTypeAndSwap(*args)
    def MergeFromIOBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromIOBuffer(*args)
    def MergeFromArray(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromArray(*args)
    def MergeFromArrayWithExtra(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromArrayWithExtra(*args)
    def MergeFromString(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromString(*args)
    def MergeFromCord(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromCord(*args)
    def MergeFromDataBuffer(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromDataBuffer(*args)
    def MergeFromDataBufferPrefix(*args): return _strings_pywrap__strutil.ProtocolMessage_MergeFromDataBufferPrefix(*args)
    kUninterpretedBlockSize = _strings_pywrap__strutil.ProtocolMessage_kUninterpretedBlockSize
    __swig_getmethods__["internal_string_assign"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_string_assign
    if _newclass:internal_string_assign = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_string_assign)
    __swig_getmethods__["internal_string_assign_c"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_string_assign_c
    if _newclass:internal_string_assign_c = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_string_assign_c)
    __swig_getmethods__["internal_string_assign_c"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_string_assign_c
    if _newclass:internal_string_assign_c = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_string_assign_c)
    __swig_getmethods__["internal_optional_string_assign"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign
    if _newclass:internal_optional_string_assign = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign)
    __swig_getmethods__["internal_optional_string_assign_c"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign_c
    if _newclass:internal_optional_string_assign_c = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign_c)
    __swig_getmethods__["internal_optional_string_assign_c"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign_c
    if _newclass:internal_optional_string_assign_c = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign_c)
    __swig_getmethods__["internal_ensure_created"] = lambda x: _strings_pywrap__strutil.ProtocolMessage_internal_ensure_created
    if _newclass:internal_ensure_created = staticmethod(_strings_pywrap__strutil.ProtocolMessage_internal_ensure_created)
    def Encode(*args): return _strings_pywrap__strutil.ProtocolMessage_Encode(*args)
    def __str__(*args): return _strings_pywrap__strutil.ProtocolMessage___str__(*args)

class ProtocolMessagePtr(ProtocolMessage):
    def __init__(self, this):
        _swig_setattr(self, ProtocolMessage, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolMessage, 'thisown', 0)
        _swig_setattr(self, ProtocolMessage,self.__class__,ProtocolMessage)
_strings_pywrap__strutil.ProtocolMessage_swigregister(ProtocolMessagePtr)

ProtocolMessage_internal_string_assign = _strings_pywrap__strutil.ProtocolMessage_internal_string_assign

ProtocolMessage_internal_string_assign_c = _strings_pywrap__strutil.ProtocolMessage_internal_string_assign_c

ProtocolMessage_internal_optional_string_assign = _strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign

ProtocolMessage_internal_optional_string_assign_c = _strings_pywrap__strutil.ProtocolMessage_internal_optional_string_assign_c

ProtocolMessage_internal_ensure_created = _strings_pywrap__strutil.ProtocolMessage_internal_ensure_created


ParseFromCord = _strings_pywrap__strutil.ParseFromCord

AppendToCord = _strings_pywrap__strutil.AppendToCord
class TagMapperInternalHolder(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TagMapperInternalHolder, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TagMapperInternalHolder, name)
    def __repr__(self):
        return "<C TagMapperInternalHolder instance at %s>" % (self.this,)
    __swig_setmethods__["storage_"] = _strings_pywrap__strutil.TagMapperInternalHolder_storage__set
    __swig_getmethods__["storage_"] = _strings_pywrap__strutil.TagMapperInternalHolder_storage__get
    if _newclass:storage_ = property(_strings_pywrap__strutil.TagMapperInternalHolder_storage__get, _strings_pywrap__strutil.TagMapperInternalHolder_storage__set)
    def __init__(self, *args):
        _swig_setattr(self, TagMapperInternalHolder, 'this', _strings_pywrap__strutil.new_TagMapperInternalHolder(*args))
        _swig_setattr(self, TagMapperInternalHolder, 'thisown', 1)
    def ref(*args): return _strings_pywrap__strutil.TagMapperInternalHolder_ref(*args)
    def __del__(self, destroy=_strings_pywrap__strutil.delete_TagMapperInternalHolder):
        try:
            if self.thisown: destroy(self)
        except: pass

class TagMapperInternalHolderPtr(TagMapperInternalHolder):
    def __init__(self, this):
        _swig_setattr(self, TagMapperInternalHolder, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, TagMapperInternalHolder, 'thisown', 0)
        _swig_setattr(self, TagMapperInternalHolder,self.__class__,TagMapperInternalHolder)
_strings_pywrap__strutil.TagMapperInternalHolder_swigregister(TagMapperInternalHolderPtr)

# we need a level of indirection to make the Equals lookup
# dynamic. Therefore we cannot just do setattr(ProtocolMessage,
# '__eq__', ProtocolMessage.Equals)
def _Equals(self, other):
  """Test equality of derived protocol buffers

  Args:
    other: a protocol buffer of the same class as self

  Returns: the return value of C++ Equals
  """
  return self.Equals(other)
setattr(ProtocolMessage, '__eq__', _Equals)
setattr(ProtocolMessage, '__ne__', lambda self, other: not self.Equals(other))



SplitCSVLine = _strings_pywrap__strutil.SplitCSVLine

JoinCSVLine = _strings_pywrap__strutil.JoinCSVLine

KeyFromDouble = _strings_pywrap__strutil.KeyFromDouble

KeyToDouble = _strings_pywrap__strutil.KeyToDouble

ExpandBraces = _strings_pywrap__strutil.ExpandBraces

Uint64ToKey = _strings_pywrap__strutil.Uint64ToKey

KeyToUint64 = _strings_pywrap__strutil.KeyToUint64

GlobToRegexp = _strings_pywrap__strutil.GlobToRegexp

SplitStructuredLine = _strings_pywrap__strutil.SplitStructuredLine


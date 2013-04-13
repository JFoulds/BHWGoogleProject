# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _net_proto_pywraptagmapper

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
        _swig_setattr(self, stringVector, 'this', _net_proto_pywraptagmapper.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_net_proto_pywraptagmapper.stringVector_swigregister(stringVectorPtr)

class TagMapper(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TagMapper, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TagMapper, name)
    def __repr__(self):
        return "<C TagMapper instance at %s>" % (self.this,)
    TYPE_ERROR = _net_proto_pywraptagmapper.TagMapper_TYPE_ERROR
    TYPE_DOUBLE = _net_proto_pywraptagmapper.TagMapper_TYPE_DOUBLE
    TYPE_FLOAT = _net_proto_pywraptagmapper.TagMapper_TYPE_FLOAT
    TYPE_INT64 = _net_proto_pywraptagmapper.TagMapper_TYPE_INT64
    TYPE_UINT64 = _net_proto_pywraptagmapper.TagMapper_TYPE_UINT64
    TYPE_INT32 = _net_proto_pywraptagmapper.TagMapper_TYPE_INT32
    TYPE_FIXED64 = _net_proto_pywraptagmapper.TagMapper_TYPE_FIXED64
    TYPE_FIXED32 = _net_proto_pywraptagmapper.TagMapper_TYPE_FIXED32
    TYPE_BOOL = _net_proto_pywraptagmapper.TagMapper_TYPE_BOOL
    TYPE_STRING = _net_proto_pywraptagmapper.TagMapper_TYPE_STRING
    TYPE_GROUP = _net_proto_pywraptagmapper.TagMapper_TYPE_GROUP
    TYPE_FOREIGN = _net_proto_pywraptagmapper.TagMapper_TYPE_FOREIGN
    NUM_TYPES = _net_proto_pywraptagmapper.TagMapper_NUM_TYPES
    TAG_OPTION_DPL_NOINDEX = _net_proto_pywraptagmapper.TagMapper_TAG_OPTION_DPL_NOINDEX
    TAG_OPTION_DPL_SNIPPETS = _net_proto_pywraptagmapper.TagMapper_TAG_OPTION_DPL_SNIPPETS
    TAG_OPTION_DPL_FLATTEN = _net_proto_pywraptagmapper.TagMapper_TAG_OPTION_DPL_FLATTEN
    UTF8_STRINGS = _net_proto_pywraptagmapper.TagMapper_UTF8_STRINGS
    RAW_STRINGS = _net_proto_pywraptagmapper.TagMapper_RAW_STRINGS
    UTF8_AND_RAW_STRINGS = _net_proto_pywraptagmapper.TagMapper_UTF8_AND_RAW_STRINGS
    LATIN1_STRINGS = _net_proto_pywraptagmapper.TagMapper_LATIN1_STRINGS
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_TagMapper):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, TagMapper, 'this', _net_proto_pywraptagmapper.new_TagMapper(*args))
        _swig_setattr(self, TagMapper, 'thisown', 1)
    def FixForeignFields(*args): return _net_proto_pywraptagmapper.TagMapper_FixForeignFields(*args)
    __swig_getmethods__["FixAllForeignFields"] = lambda x: _net_proto_pywraptagmapper.TagMapper_FixAllForeignFields
    if _newclass:FixAllForeignFields = staticmethod(_net_proto_pywraptagmapper.TagMapper_FixAllForeignFields)
    def tag_count(*args): return _net_proto_pywraptagmapper.TagMapper_tag_count(*args)
    def largest_tag(*args): return _net_proto_pywraptagmapper.TagMapper_largest_tag(*args)
    def name(*args): return _net_proto_pywraptagmapper.TagMapper_name(*args)
    def type_id(*args): return _net_proto_pywraptagmapper.TagMapper_type_id(*args)
    def stylesheet(*args): return _net_proto_pywraptagmapper.TagMapper_stylesheet(*args)
    def stylesheet_content_type(*args): return _net_proto_pywraptagmapper.TagMapper_stylesheet_content_type(*args)
    def GetProtocolDescriptor(*args): return _net_proto_pywraptagmapper.TagMapper_GetProtocolDescriptor(*args)
    def FromTag(*args): return _net_proto_pywraptagmapper.TagMapper_FromTag(*args)
    def FromName(*args): return _net_proto_pywraptagmapper.TagMapper_FromName(*args)
    def FromOrderInFile(*args): return _net_proto_pywraptagmapper.TagMapper_FromOrderInFile(*args)
    def GenerateASCII(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateASCII(*args)
    def GenerateCompactASCII(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateCompactASCII(*args)
    def GenerateShortASCII(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateShortASCII(*args)
    def ParseASCII(*args): return _net_proto_pywraptagmapper.TagMapper_ParseASCII(*args)
    def GenerateXmlProlog(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateXmlProlog(*args)
    def GenerateXmlElements(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateXmlElements(*args)
    def GenerateXmlDocument(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateXmlDocument(*args)
    def ParseURLArgs(*args): return _net_proto_pywraptagmapper.TagMapper_ParseURLArgs(*args)
    def ParseSimpleASCII(*args): return _net_proto_pywraptagmapper.TagMapper_ParseSimpleASCII(*args)
    def GenerateSimpleASCII(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateSimpleASCII(*args)
    __swig_getmethods__["GenerateForm"] = lambda x: _net_proto_pywraptagmapper.TagMapper_GenerateForm
    if _newclass:GenerateForm = staticmethod(_net_proto_pywraptagmapper.TagMapper_GenerateForm)
    __swig_getmethods__["ParseURLArgsFromForm"] = lambda x: _net_proto_pywraptagmapper.TagMapper_ParseURLArgsFromForm
    if _newclass:ParseURLArgsFromForm = staticmethod(_net_proto_pywraptagmapper.TagMapper_ParseURLArgsFromForm)
    def GenerateFormRedirect(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateFormRedirect(*args)
    def GenerateForm(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateForm(*args)
    def GenerateFormInstructions(*args): return _net_proto_pywraptagmapper.TagMapper_GenerateFormInstructions(*args)
    def DebugString(*args): return _net_proto_pywraptagmapper.TagMapper_DebugString(*args)
    __swig_getmethods__["LengthString"] = lambda x: _net_proto_pywraptagmapper.TagMapper_LengthString
    if _newclass:LengthString = staticmethod(_net_proto_pywraptagmapper.TagMapper_LengthString)
    __swig_getmethods__["FindByName"] = lambda x: _net_proto_pywraptagmapper.TagMapper_FindByName
    if _newclass:FindByName = staticmethod(_net_proto_pywraptagmapper.TagMapper_FindByName)
    __swig_getmethods__["FindByTypeId"] = lambda x: _net_proto_pywraptagmapper.TagMapper_FindByTypeId
    if _newclass:FindByTypeId = staticmethod(_net_proto_pywraptagmapper.TagMapper_FindByTypeId)
    __swig_getmethods__["FindByFileName"] = lambda x: _net_proto_pywraptagmapper.TagMapper_FindByFileName
    if _newclass:FindByFileName = staticmethod(_net_proto_pywraptagmapper.TagMapper_FindByFileName)
    def GetReflection(*args): return _net_proto_pywraptagmapper.TagMapper_GetReflection(*args)
    def message_filter(*args): return _net_proto_pywraptagmapper.TagMapper_message_filter(*args)
    def set_message_filter(*args): return _net_proto_pywraptagmapper.TagMapper_set_message_filter(*args)

class TagMapperPtr(TagMapper):
    def __init__(self, this):
        _swig_setattr(self, TagMapper, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, TagMapper, 'thisown', 0)
        _swig_setattr(self, TagMapper,self.__class__,TagMapper)
_net_proto_pywraptagmapper.TagMapper_swigregister(TagMapperPtr)

TagMapper_FixAllForeignFields = _net_proto_pywraptagmapper.TagMapper_FixAllForeignFields

TagMapper_ParseURLArgsFromForm = _net_proto_pywraptagmapper.TagMapper_ParseURLArgsFromForm
cvar = _net_proto_pywraptagmapper.cvar

TagMapper_LengthString = _net_proto_pywraptagmapper.TagMapper_LengthString

TagMapper_FindByName = _net_proto_pywraptagmapper.TagMapper_FindByName

TagMapper_FindByTypeId = _net_proto_pywraptagmapper.TagMapper_FindByTypeId

TagMapper_FindByFileName = _net_proto_pywraptagmapper.TagMapper_FindByFileName

class Protocol(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Protocol, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Protocol, name)
    def __repr__(self):
        return "<C Protocol instance at %s>" % (self.this,)
    __swig_getmethods__["tag"] = lambda x: _net_proto_pywraptagmapper.Protocol_tag
    if _newclass:tag = staticmethod(_net_proto_pywraptagmapper.Protocol_tag)
    __swig_getmethods__["type"] = lambda x: _net_proto_pywraptagmapper.Protocol_type
    if _newclass:type = staticmethod(_net_proto_pywraptagmapper.Protocol_type)
    __swig_getmethods__["combine"] = lambda x: _net_proto_pywraptagmapper.Protocol_combine
    if _newclass:combine = staticmethod(_net_proto_pywraptagmapper.Protocol_combine)
    __swig_getmethods__["Skip"] = lambda x: _net_proto_pywraptagmapper.Protocol_Skip
    if _newclass:Skip = staticmethod(_net_proto_pywraptagmapper.Protocol_Skip)
    __swig_getmethods__["SkipAndSave"] = lambda x: _net_proto_pywraptagmapper.Protocol_SkipAndSave
    if _newclass:SkipAndSave = staticmethod(_net_proto_pywraptagmapper.Protocol_SkipAndSave)
    __swig_getmethods__["SkipUnknown"] = lambda x: _net_proto_pywraptagmapper.Protocol_SkipUnknown
    if _newclass:SkipUnknown = staticmethod(_net_proto_pywraptagmapper.Protocol_SkipUnknown)
    __swig_getmethods__["ReadBool"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadBool
    if _newclass:ReadBool = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadBool)
    __swig_getmethods__["ReadDouble"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadDouble
    if _newclass:ReadDouble = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadDouble)
    __swig_getmethods__["ReadFloat"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadFloat
    if _newclass:ReadFloat = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadFloat)
    __swig_getmethods__["ReadInt64"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadInt64
    if _newclass:ReadInt64 = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadInt64)
    __swig_getmethods__["ReadUint64"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadUint64
    if _newclass:ReadUint64 = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadUint64)
    __swig_getmethods__["ReadInt32"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadInt32
    if _newclass:ReadInt32 = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadInt32)
    __swig_getmethods__["ReadFixed64"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadFixed64
    if _newclass:ReadFixed64 = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadFixed64)
    __swig_getmethods__["ReadFixed32"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadFixed32
    if _newclass:ReadFixed32 = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadFixed32)
    __swig_getmethods__["ReadString"] = lambda x: _net_proto_pywraptagmapper.Protocol_ReadString
    if _newclass:ReadString = staticmethod(_net_proto_pywraptagmapper.Protocol_ReadString)
    __swig_getmethods__["WriteTag"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteTag
    if _newclass:WriteTag = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteTag)
    __swig_getmethods__["BeginGroup"] = lambda x: _net_proto_pywraptagmapper.Protocol_BeginGroup
    if _newclass:BeginGroup = staticmethod(_net_proto_pywraptagmapper.Protocol_BeginGroup)
    __swig_getmethods__["EndGroup"] = lambda x: _net_proto_pywraptagmapper.Protocol_EndGroup
    if _newclass:EndGroup = staticmethod(_net_proto_pywraptagmapper.Protocol_EndGroup)
    __swig_getmethods__["WriteDouble"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteDouble
    if _newclass:WriteDouble = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteDouble)
    __swig_getmethods__["WriteFloat"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFloat
    if _newclass:WriteFloat = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFloat)
    __swig_getmethods__["WriteFixed64"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFixed64
    if _newclass:WriteFixed64 = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFixed64)
    __swig_getmethods__["WriteFixed32"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFixed32
    if _newclass:WriteFixed32 = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFixed32)
    __swig_getmethods__["WriteUint64"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteUint64
    if _newclass:WriteUint64 = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteUint64)
    __swig_getmethods__["WriteInt32"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteInt32
    if _newclass:WriteInt32 = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteInt32)
    __swig_getmethods__["WriteBool"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteBool
    if _newclass:WriteBool = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteBool)
    __swig_getmethods__["WriteString"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteString
    if _newclass:WriteString = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteString)
    __swig_getmethods__["WriteCString"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteCString
    if _newclass:WriteCString = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteCString)
    __swig_getmethods__["WriteCord"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteCord
    if _newclass:WriteCord = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteCord)
    __swig_getmethods__["WriteStringHeader"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteStringHeader
    if _newclass:WriteStringHeader = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteStringHeader)
    __swig_getmethods__["WriteDoubleArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteDoubleArrayToBuffer
    if _newclass:WriteDoubleArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteDoubleArrayToBuffer)
    __swig_getmethods__["WriteFloatArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFloatArrayToBuffer
    if _newclass:WriteFloatArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFloatArrayToBuffer)
    __swig_getmethods__["WriteFixed64ArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFixed64ArrayToBuffer
    if _newclass:WriteFixed64ArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFixed64ArrayToBuffer)
    __swig_getmethods__["WriteFixed32ArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteFixed32ArrayToBuffer
    if _newclass:WriteFixed32ArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteFixed32ArrayToBuffer)
    __swig_getmethods__["WriteUint64ArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteUint64ArrayToBuffer
    if _newclass:WriteUint64ArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteUint64ArrayToBuffer)
    __swig_getmethods__["WriteUint64ArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteUint64ArrayToBuffer
    if _newclass:WriteUint64ArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteUint64ArrayToBuffer)
    __swig_getmethods__["WriteInt32ArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteInt32ArrayToBuffer
    if _newclass:WriteInt32ArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteInt32ArrayToBuffer)
    __swig_getmethods__["WriteBoolArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteBoolArrayToBuffer
    if _newclass:WriteBoolArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteBoolArrayToBuffer)
    __swig_getmethods__["WriteStringArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteStringArrayToBuffer
    if _newclass:WriteStringArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteStringArrayToBuffer)
    __swig_getmethods__["WriteCordArrayToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_WriteCordArrayToBuffer
    if _newclass:WriteCordArrayToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_WriteCordArrayToBuffer)
    __swig_getmethods__["MoveStringFromDataBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_MoveStringFromDataBuffer
    if _newclass:MoveStringFromDataBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_MoveStringFromDataBuffer)
    __swig_getmethods__["CopyBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_CopyBuffer
    if _newclass:CopyBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_CopyBuffer)
    __swig_getmethods__["LengthForeignMessage"] = lambda x: _net_proto_pywraptagmapper.Protocol_LengthForeignMessage
    if _newclass:LengthForeignMessage = staticmethod(_net_proto_pywraptagmapper.Protocol_LengthForeignMessage)
    __swig_getmethods__["LengthStringNonInlined"] = lambda x: _net_proto_pywraptagmapper.Protocol_LengthStringNonInlined
    if _newclass:LengthStringNonInlined = staticmethod(_net_proto_pywraptagmapper.Protocol_LengthStringNonInlined)
    __swig_getmethods__["LengthUninterpreted"] = lambda x: _net_proto_pywraptagmapper.Protocol_LengthUninterpreted
    if _newclass:LengthUninterpreted = staticmethod(_net_proto_pywraptagmapper.Protocol_LengthUninterpreted)
    __swig_getmethods__["LengthInt32"] = lambda x: _net_proto_pywraptagmapper.Protocol_LengthInt32
    if _newclass:LengthInt32 = staticmethod(_net_proto_pywraptagmapper.Protocol_LengthInt32)
    __swig_getmethods__["EmitInt32"] = lambda x: _net_proto_pywraptagmapper.Protocol_EmitInt32
    if _newclass:EmitInt32 = staticmethod(_net_proto_pywraptagmapper.Protocol_EmitInt32)
    __swig_getmethods__["PatchLengthIntoHole"] = lambda x: _net_proto_pywraptagmapper.Protocol_PatchLengthIntoHole
    if _newclass:PatchLengthIntoHole = staticmethod(_net_proto_pywraptagmapper.Protocol_PatchLengthIntoHole)
    __swig_getmethods__["SpaceUsedOutOfLineString"] = lambda x: _net_proto_pywraptagmapper.Protocol_SpaceUsedOutOfLineString
    if _newclass:SpaceUsedOutOfLineString = staticmethod(_net_proto_pywraptagmapper.Protocol_SpaceUsedOutOfLineString)
    __swig_getmethods__["CopyUninterpreted"] = lambda x: _net_proto_pywraptagmapper.Protocol_CopyUninterpreted
    if _newclass:CopyUninterpreted = staticmethod(_net_proto_pywraptagmapper.Protocol_CopyUninterpreted)
    __swig_getmethods__["AppendCordToBuffer"] = lambda x: _net_proto_pywraptagmapper.Protocol_AppendCordToBuffer
    if _newclass:AppendCordToBuffer = staticmethod(_net_proto_pywraptagmapper.Protocol_AppendCordToBuffer)
    __swig_getmethods__["AppendCordToArray"] = lambda x: _net_proto_pywraptagmapper.Protocol_AppendCordToArray
    if _newclass:AppendCordToArray = staticmethod(_net_proto_pywraptagmapper.Protocol_AppendCordToArray)
    __swig_getmethods__["RawWriteString"] = lambda x: _net_proto_pywraptagmapper.Protocol_RawWriteString
    if _newclass:RawWriteString = staticmethod(_net_proto_pywraptagmapper.Protocol_RawWriteString)
    __swig_getmethods__["RawWriteCord"] = lambda x: _net_proto_pywraptagmapper.Protocol_RawWriteCord
    if _newclass:RawWriteCord = staticmethod(_net_proto_pywraptagmapper.Protocol_RawWriteCord)
    __swig_getmethods__["SwapTypeMismatch"] = lambda x: _net_proto_pywraptagmapper.Protocol_SwapTypeMismatch
    if _newclass:SwapTypeMismatch = staticmethod(_net_proto_pywraptagmapper.Protocol_SwapTypeMismatch)
    def __init__(self, *args):
        _swig_setattr(self, Protocol, 'this', _net_proto_pywraptagmapper.new_Protocol(*args))
        _swig_setattr(self, Protocol, 'thisown', 1)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_Protocol):
        try:
            if self.thisown: destroy(self)
        except: pass

class ProtocolPtr(Protocol):
    def __init__(self, this):
        _swig_setattr(self, Protocol, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, Protocol, 'thisown', 0)
        _swig_setattr(self, Protocol,self.__class__,Protocol)
_net_proto_pywraptagmapper.Protocol_swigregister(ProtocolPtr)

Protocol_tag = _net_proto_pywraptagmapper.Protocol_tag

Protocol_type = _net_proto_pywraptagmapper.Protocol_type

Protocol_combine = _net_proto_pywraptagmapper.Protocol_combine

Protocol_Skip = _net_proto_pywraptagmapper.Protocol_Skip

Protocol_SkipAndSave = _net_proto_pywraptagmapper.Protocol_SkipAndSave

Protocol_SkipUnknown = _net_proto_pywraptagmapper.Protocol_SkipUnknown

Protocol_ReadBool = _net_proto_pywraptagmapper.Protocol_ReadBool

Protocol_ReadDouble = _net_proto_pywraptagmapper.Protocol_ReadDouble

Protocol_ReadFloat = _net_proto_pywraptagmapper.Protocol_ReadFloat

Protocol_ReadInt64 = _net_proto_pywraptagmapper.Protocol_ReadInt64

Protocol_ReadUint64 = _net_proto_pywraptagmapper.Protocol_ReadUint64

Protocol_ReadInt32 = _net_proto_pywraptagmapper.Protocol_ReadInt32

Protocol_ReadFixed64 = _net_proto_pywraptagmapper.Protocol_ReadFixed64

Protocol_ReadFixed32 = _net_proto_pywraptagmapper.Protocol_ReadFixed32

Protocol_ReadString = _net_proto_pywraptagmapper.Protocol_ReadString

Protocol_WriteTag = _net_proto_pywraptagmapper.Protocol_WriteTag

Protocol_BeginGroup = _net_proto_pywraptagmapper.Protocol_BeginGroup

Protocol_EndGroup = _net_proto_pywraptagmapper.Protocol_EndGroup

Protocol_WriteDouble = _net_proto_pywraptagmapper.Protocol_WriteDouble

Protocol_WriteFloat = _net_proto_pywraptagmapper.Protocol_WriteFloat

Protocol_WriteFixed64 = _net_proto_pywraptagmapper.Protocol_WriteFixed64

Protocol_WriteFixed32 = _net_proto_pywraptagmapper.Protocol_WriteFixed32

Protocol_WriteUint64 = _net_proto_pywraptagmapper.Protocol_WriteUint64

Protocol_WriteInt32 = _net_proto_pywraptagmapper.Protocol_WriteInt32

Protocol_WriteBool = _net_proto_pywraptagmapper.Protocol_WriteBool

Protocol_WriteString = _net_proto_pywraptagmapper.Protocol_WriteString

Protocol_WriteCString = _net_proto_pywraptagmapper.Protocol_WriteCString

Protocol_WriteCord = _net_proto_pywraptagmapper.Protocol_WriteCord

Protocol_WriteStringHeader = _net_proto_pywraptagmapper.Protocol_WriteStringHeader

Protocol_WriteDoubleArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteDoubleArrayToBuffer

Protocol_WriteFloatArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteFloatArrayToBuffer

Protocol_WriteFixed64ArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteFixed64ArrayToBuffer

Protocol_WriteFixed32ArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteFixed32ArrayToBuffer

Protocol_WriteUint64ArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteUint64ArrayToBuffer

Protocol_WriteInt32ArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteInt32ArrayToBuffer

Protocol_WriteBoolArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteBoolArrayToBuffer

Protocol_WriteStringArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteStringArrayToBuffer

Protocol_WriteCordArrayToBuffer = _net_proto_pywraptagmapper.Protocol_WriteCordArrayToBuffer

Protocol_MoveStringFromDataBuffer = _net_proto_pywraptagmapper.Protocol_MoveStringFromDataBuffer

Protocol_CopyBuffer = _net_proto_pywraptagmapper.Protocol_CopyBuffer

Protocol_LengthForeignMessage = _net_proto_pywraptagmapper.Protocol_LengthForeignMessage

Protocol_LengthStringNonInlined = _net_proto_pywraptagmapper.Protocol_LengthStringNonInlined

Protocol_LengthUninterpreted = _net_proto_pywraptagmapper.Protocol_LengthUninterpreted

Protocol_LengthInt32 = _net_proto_pywraptagmapper.Protocol_LengthInt32

Protocol_EmitInt32 = _net_proto_pywraptagmapper.Protocol_EmitInt32

Protocol_PatchLengthIntoHole = _net_proto_pywraptagmapper.Protocol_PatchLengthIntoHole

Protocol_SpaceUsedOutOfLineString = _net_proto_pywraptagmapper.Protocol_SpaceUsedOutOfLineString

Protocol_CopyUninterpreted = _net_proto_pywraptagmapper.Protocol_CopyUninterpreted

Protocol_AppendCordToBuffer = _net_proto_pywraptagmapper.Protocol_AppendCordToBuffer

Protocol_AppendCordToArray = _net_proto_pywraptagmapper.Protocol_AppendCordToArray

Protocol_RawWriteString = _net_proto_pywraptagmapper.Protocol_RawWriteString

Protocol_RawWriteCord = _net_proto_pywraptagmapper.Protocol_RawWriteCord

Protocol_SwapTypeMismatch = _net_proto_pywraptagmapper.Protocol_SwapTypeMismatch

class ProtocolMessageGroup(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolMessageGroup, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolMessageGroup, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C ProtocolMessageGroup instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolMessageGroup):
        try:
            if self.thisown: destroy(self)
        except: pass
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_Clear(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_clear(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_FindInitializationError(*args)
    def CheckInitialized(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_CheckInitialized(*args)
    def AssertInitialized(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_AssertInitialized(*args)
    def AppendToString(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_AppendToString(*args)
    def RawAppendToString(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_RawAppendToString(*args)
    def AppendToStringWithOuterTags(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_AppendToStringWithOuterTags(*args)
    def RawAppendToStringWithOuterTags(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_RawAppendToStringWithOuterTags(*args)
    def MergeFromArrayWithOuterTags(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_MergeFromArrayWithOuterTags(*args)
    def ParseFromArrayWithOuterTags(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_ParseFromArrayWithOuterTags(*args)
    def ParseFromStringWithOuterTags(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_ParseFromStringWithOuterTags(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_ByteSize(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolMessageGroup_New(*args)

class ProtocolMessageGroupPtr(ProtocolMessageGroup):
    def __init__(self, this):
        _swig_setattr(self, ProtocolMessageGroup, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolMessageGroup, 'thisown', 0)
        _swig_setattr(self, ProtocolMessageGroup,self.__class__,ProtocolMessageGroup)
_net_proto_pywraptagmapper.ProtocolMessageGroup_swigregister(ProtocolMessageGroupPtr)

class ProtocolMessage(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolMessage, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolMessage, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C ProtocolMessage instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolMessage):
        try:
            if self.thisown: destroy(self)
        except: pass
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolMessage_FindInitializationError(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolMessage_Clear(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolMessage_clear(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolMessage_RawOutputToArray(*args)
    def RawAppendToString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_RawAppendToString(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolMessage_InternalMergeFrom(*args)
    def GetMapper(*args): return _net_proto_pywraptagmapper.ProtocolMessage_GetMapper(*args)
    def GetProtocolDescriptor(*args): return _net_proto_pywraptagmapper.ProtocolMessage_GetProtocolDescriptor(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolMessage_New(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolMessage_SpaceUsed(*args)
    def DiscardUnknownFields(*args): return _net_proto_pywraptagmapper.ProtocolMessage_DiscardUnknownFields(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.ProtocolMessage_IsInitialized(*args)
    def CheckInitialized(*args): return _net_proto_pywraptagmapper.ProtocolMessage_CheckInitialized(*args)
    def AssertInitialized(*args): return _net_proto_pywraptagmapper.ProtocolMessage_AssertInitialized(*args)
    def OutputToDataBufferUnchecked(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputToDataBufferUnchecked(*args)
    def OutputToDataBufferUncheckedWithSize(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputToDataBufferUncheckedWithSize(*args)
    def OutputToDataBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputToDataBuffer(*args)
    def AppendToCordUnchecked(*args): return _net_proto_pywraptagmapper.ProtocolMessage_AppendToCordUnchecked(*args)
    def AppendToCord(*args): return _net_proto_pywraptagmapper.ProtocolMessage_AppendToCord(*args)
    NO_CHECK = _net_proto_pywraptagmapper.ProtocolMessage_NO_CHECK
    CHECK = _net_proto_pywraptagmapper.ProtocolMessage_CHECK
    def OutputToDataBufferChecked(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputToDataBufferChecked(*args)
    def OutputToIOBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputToIOBuffer(*args)
    def AppendToString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_AppendToString(*args)
    def OutputAsString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_OutputAsString(*args)
    def DebugString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_DebugString(*args)
    def PrintDebugString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_PrintDebugString(*args)
    def ShortDebugString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ShortDebugString(*args)
    def ParseFromDataBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromDataBuffer(*args)
    def ParseFromDataBufferPrefix(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromDataBufferPrefix(*args)
    def ParseFromIOBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromIOBuffer(*args)
    def ParseFromArray(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromArray(*args)
    def ParseFromArrayWithExtra(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromArrayWithExtra(*args)
    def ParseFromString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromString(*args)
    def ParseFromCord(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseFromCord(*args)
    def ToASCII(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ToASCII(*args)
    def ToCompactASCII(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ToCompactASCII(*args)
    def ToShortASCII(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ToShortASCII(*args)
    def ParseASCII(*args): return _net_proto_pywraptagmapper.ProtocolMessage_ParseASCII(*args)
    def CheckTypeAndSwap(*args): return _net_proto_pywraptagmapper.ProtocolMessage_CheckTypeAndSwap(*args)
    def MergeFromIOBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromIOBuffer(*args)
    def MergeFromArray(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromArray(*args)
    def MergeFromArrayWithExtra(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromArrayWithExtra(*args)
    def MergeFromString(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromString(*args)
    def MergeFromCord(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromCord(*args)
    def MergeFromDataBuffer(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromDataBuffer(*args)
    def MergeFromDataBufferPrefix(*args): return _net_proto_pywraptagmapper.ProtocolMessage_MergeFromDataBufferPrefix(*args)
    kUninterpretedBlockSize = _net_proto_pywraptagmapper.ProtocolMessage_kUninterpretedBlockSize
    __swig_getmethods__["internal_string_assign"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign
    if _newclass:internal_string_assign = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign)
    __swig_getmethods__["internal_string_assign_c"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign_c
    if _newclass:internal_string_assign_c = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign_c)
    __swig_getmethods__["internal_string_assign_c"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign_c
    if _newclass:internal_string_assign_c = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign_c)
    __swig_getmethods__["internal_optional_string_assign"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign
    if _newclass:internal_optional_string_assign = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign)
    __swig_getmethods__["internal_optional_string_assign_c"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign_c
    if _newclass:internal_optional_string_assign_c = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign_c)
    __swig_getmethods__["internal_optional_string_assign_c"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign_c
    if _newclass:internal_optional_string_assign_c = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign_c)
    __swig_getmethods__["internal_ensure_created"] = lambda x: _net_proto_pywraptagmapper.ProtocolMessage_internal_ensure_created
    if _newclass:internal_ensure_created = staticmethod(_net_proto_pywraptagmapper.ProtocolMessage_internal_ensure_created)

class ProtocolMessagePtr(ProtocolMessage):
    def __init__(self, this):
        _swig_setattr(self, ProtocolMessage, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolMessage, 'thisown', 0)
        _swig_setattr(self, ProtocolMessage,self.__class__,ProtocolMessage)
_net_proto_pywraptagmapper.ProtocolMessage_swigregister(ProtocolMessagePtr)

ProtocolMessage_internal_string_assign = _net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign

ProtocolMessage_internal_string_assign_c = _net_proto_pywraptagmapper.ProtocolMessage_internal_string_assign_c

ProtocolMessage_internal_optional_string_assign = _net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign

ProtocolMessage_internal_optional_string_assign_c = _net_proto_pywraptagmapper.ProtocolMessage_internal_optional_string_assign_c

ProtocolMessage_internal_ensure_created = _net_proto_pywraptagmapper.ProtocolMessage_internal_ensure_created


ParseFromCord = _net_proto_pywraptagmapper.ParseFromCord

AppendToCord = _net_proto_pywraptagmapper.AppendToCord
class TagMapperInternalHolder(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TagMapperInternalHolder, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TagMapperInternalHolder, name)
    def __repr__(self):
        return "<C TagMapperInternalHolder instance at %s>" % (self.this,)
    __swig_setmethods__["storage_"] = _net_proto_pywraptagmapper.TagMapperInternalHolder_storage__set
    __swig_getmethods__["storage_"] = _net_proto_pywraptagmapper.TagMapperInternalHolder_storage__get
    if _newclass:storage_ = property(_net_proto_pywraptagmapper.TagMapperInternalHolder_storage__get, _net_proto_pywraptagmapper.TagMapperInternalHolder_storage__set)
    def __init__(self, *args):
        _swig_setattr(self, TagMapperInternalHolder, 'this', _net_proto_pywraptagmapper.new_TagMapperInternalHolder(*args))
        _swig_setattr(self, TagMapperInternalHolder, 'thisown', 1)
    def ref(*args): return _net_proto_pywraptagmapper.TagMapperInternalHolder_ref(*args)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_TagMapperInternalHolder):
        try:
            if self.thisown: destroy(self)
        except: pass

class TagMapperInternalHolderPtr(TagMapperInternalHolder):
    def __init__(self, this):
        _swig_setattr(self, TagMapperInternalHolder, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, TagMapperInternalHolder, 'thisown', 0)
        _swig_setattr(self, TagMapperInternalHolder,self.__class__,TagMapperInternalHolder)
_net_proto_pywraptagmapper.TagMapperInternalHolder_swigregister(TagMapperInternalHolderPtr)

class ProtocolDescriptor_EnumTypeTag(ProtocolMessageGroup):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolDescriptor_EnumTypeTag, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolDescriptor_EnumTypeTag, name)
    def __repr__(self):
        return "<C ProtocolDescriptor_EnumTypeTag instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolDescriptor_EnumTypeTag):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolDescriptor_EnumTypeTag, 'this', _net_proto_pywraptagmapper.new_ProtocolDescriptor_EnumTypeTag(*args))
        _swig_setattr(self, ProtocolDescriptor_EnumTypeTag, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_EnumTypeTag__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_Swap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_Clear(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_IsInitialized(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_New(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_SpaceUsed(*args)
    def name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_clear_name(*args)
    def value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_value(*args)
    def set_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_set_value(*args)
    def clear_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_clear_value(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_has_name(*args)
    def has_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_has_value(*args)

class ProtocolDescriptor_EnumTypeTagPtr(ProtocolDescriptor_EnumTypeTag):
    def __init__(self, this):
        _swig_setattr(self, ProtocolDescriptor_EnumTypeTag, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolDescriptor_EnumTypeTag, 'thisown', 0)
        _swig_setattr(self, ProtocolDescriptor_EnumTypeTag,self.__class__,ProtocolDescriptor_EnumTypeTag)
_net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_swigregister(ProtocolDescriptor_EnumTypeTagPtr)

ProtocolDescriptor_EnumTypeTag_default_instance = _net_proto_pywraptagmapper.ProtocolDescriptor_EnumTypeTag_default_instance

class ProtocolDescriptor_TagOption(ProtocolMessageGroup):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolDescriptor_TagOption, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolDescriptor_TagOption, name)
    def __repr__(self):
        return "<C ProtocolDescriptor_TagOption instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolDescriptor_TagOption):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolDescriptor_TagOption, 'this', _net_proto_pywraptagmapper.new_ProtocolDescriptor_TagOption(*args))
        _swig_setattr(self, ProtocolDescriptor_TagOption, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_TagOption__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_Swap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_Clear(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_IsInitialized(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_New(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_SpaceUsed(*args)
    def name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_clear_name(*args)
    def value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_value(*args)
    def set_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_set_value(*args)
    def mutable_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_mutable_value(*args)
    def clear_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_clear_value(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_has_name(*args)
    def has_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_has_value(*args)

class ProtocolDescriptor_TagOptionPtr(ProtocolDescriptor_TagOption):
    def __init__(self, this):
        _swig_setattr(self, ProtocolDescriptor_TagOption, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolDescriptor_TagOption, 'thisown', 0)
        _swig_setattr(self, ProtocolDescriptor_TagOption,self.__class__,ProtocolDescriptor_TagOption)
_net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_swigregister(ProtocolDescriptor_TagOptionPtr)

ProtocolDescriptor_TagOption_default_instance = _net_proto_pywraptagmapper.ProtocolDescriptor_TagOption_default_instance

class ProtocolDescriptor_Tag(ProtocolMessageGroup):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolDescriptor_Tag, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolDescriptor_Tag, name)
    def __repr__(self):
        return "<C ProtocolDescriptor_Tag instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolDescriptor_Tag):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolDescriptor_Tag, 'this', _net_proto_pywraptagmapper.new_ProtocolDescriptor_Tag(*args))
        _swig_setattr(self, ProtocolDescriptor_Tag, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_Tag__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_Tag_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_Swap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_Clear(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_IsInitialized(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_New(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_SpaceUsed(*args)
    def name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_name(*args)
    def number(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_number(*args)
    def set_number(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_number(*args)
    def clear_number(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_number(*args)
    def wire_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_wire_type(*args)
    def set_wire_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_wire_type(*args)
    def clear_wire_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_wire_type(*args)
    def declared_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_declared_type(*args)
    def set_declared_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_declared_type(*args)
    def clear_declared_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_declared_type(*args)
    def label(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_label(*args)
    def set_label(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_label(*args)
    def clear_label(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_label(*args)
    def default_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_default_value(*args)
    def set_default_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_default_value(*args)
    def mutable_default_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_mutable_default_value(*args)
    def clear_default_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_default_value(*args)
    def foreign(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_foreign(*args)
    def set_foreign(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_foreign(*args)
    def mutable_foreign(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_mutable_foreign(*args)
    def clear_foreign(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_foreign(*args)
    def flags(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_flags(*args)
    def set_flags(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_flags(*args)
    def clear_flags(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_flags(*args)
    def parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_parent(*args)
    def set_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_parent(*args)
    def clear_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_parent(*args)
    def enum_id(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_enum_id(*args)
    def set_enum_id(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_set_enum_id(*args)
    def clear_enum_id(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_enum_id(*args)
    def option_size(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_option_size(*args)
    def clear_option(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_clear_option(*args)
    def option(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_option(*args)
    def option_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_option_array(*args)
    def mutable_option(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_mutable_option(*args)
    def mutable_option_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_mutable_option_array(*args)
    def add_option(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_add_option(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_name(*args)
    def has_number(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_number(*args)
    def has_wire_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_wire_type(*args)
    def has_declared_type(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_declared_type(*args)
    def has_label(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_label(*args)
    def has_default_value(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_default_value(*args)
    def has_foreign(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_foreign(*args)
    def has_flags(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_flags(*args)
    def has_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_parent(*args)
    def has_enum_id(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_has_enum_id(*args)

class ProtocolDescriptor_TagPtr(ProtocolDescriptor_Tag):
    def __init__(self, this):
        _swig_setattr(self, ProtocolDescriptor_Tag, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolDescriptor_Tag, 'thisown', 0)
        _swig_setattr(self, ProtocolDescriptor_Tag,self.__class__,ProtocolDescriptor_Tag)
_net_proto_pywraptagmapper.ProtocolDescriptor_Tag_swigregister(ProtocolDescriptor_TagPtr)

ProtocolDescriptor_Tag_default_instance = _net_proto_pywraptagmapper.ProtocolDescriptor_Tag_default_instance

class ProtocolDescriptor_EnumType(ProtocolMessageGroup):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolDescriptor_EnumType, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolDescriptor_EnumType, name)
    def __repr__(self):
        return "<C ProtocolDescriptor_EnumType instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolDescriptor_EnumType):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolDescriptor_EnumType, 'this', _net_proto_pywraptagmapper.new_ProtocolDescriptor_EnumType(*args))
        _swig_setattr(self, ProtocolDescriptor_EnumType, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_EnumType__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_Swap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_Clear(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_IsInitialized(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_New(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_SpaceUsed(*args)
    def name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_clear_name(*args)
    def parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_parent(*args)
    def set_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_set_parent(*args)
    def clear_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_clear_parent(*args)
    def tag_size(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_tag_size(*args)
    def clear_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_clear_tag(*args)
    def tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_tag(*args)
    def tag_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_tag_array(*args)
    def mutable_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_mutable_tag(*args)
    def mutable_tag_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_mutable_tag_array(*args)
    def add_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_add_tag(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_has_name(*args)
    def has_parent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_has_parent(*args)

class ProtocolDescriptor_EnumTypePtr(ProtocolDescriptor_EnumType):
    def __init__(self, this):
        _swig_setattr(self, ProtocolDescriptor_EnumType, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolDescriptor_EnumType, 'thisown', 0)
        _swig_setattr(self, ProtocolDescriptor_EnumType,self.__class__,ProtocolDescriptor_EnumType)
_net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_swigregister(ProtocolDescriptor_EnumTypePtr)

ProtocolDescriptor_EnumType_default_instance = _net_proto_pywraptagmapper.ProtocolDescriptor_EnumType_default_instance

class ProtocolDescriptor(ProtocolMessage):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessage]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolDescriptor, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessage]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolDescriptor, name)
    def __repr__(self):
        return "<C ProtocolDescriptor instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolDescriptor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolDescriptor, 'this', _net_proto_pywraptagmapper.new_ProtocolDescriptor(*args))
        _swig_setattr(self, ProtocolDescriptor, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Swap(*args)
    def CheckTypeAndSwap(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_CheckTypeAndSwap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_Clear(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_SpaceUsed(*args)
    def GetMapper(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_GetMapper(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_New(*args)
    def filename(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_filename(*args)
    def set_filename(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_set_filename(*args)
    def mutable_filename(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_filename(*args)
    def clear_filename(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_clear_filename(*args)
    def name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_clear_name(*args)
    def tag_size(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_tag_size(*args)
    def clear_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_clear_tag(*args)
    def tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_tag(*args)
    def tag_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_tag_array(*args)
    def mutable_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_tag(*args)
    def mutable_tag_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_tag_array(*args)
    def add_tag(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_add_tag(*args)
    def enumtype_size(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_enumtype_size(*args)
    def clear_enumtype(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_clear_enumtype(*args)
    def enumtype(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_enumtype(*args)
    def enumtype_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_enumtype_array(*args)
    def mutable_enumtype(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_enumtype(*args)
    def mutable_enumtype_array(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_mutable_enumtype_array(*args)
    def add_enumtype(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_add_enumtype(*args)
    def has_filename(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_has_filename(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.ProtocolDescriptor_has_name(*args)
    WIRETYPE_NUMERIC = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_NUMERIC
    WIRETYPE_DOUBLE = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_DOUBLE
    WIRETYPE_STRING = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_STRING
    WIRETYPE_STARTGROUP = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_STARTGROUP
    WIRETYPE_ENDGROUP = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_ENDGROUP
    WIRETYPE_FLOAT = _net_proto_pywraptagmapper.ProtocolDescriptor_WIRETYPE_FLOAT
    __swig_getmethods__["WireType_Parse"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Parse
    if _newclass:WireType_Parse = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Parse)
    __swig_getmethods__["WireType_Name"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Name
    if _newclass:WireType_Name = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Name)
    WireType_MIN = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_MIN
    WireType_MAX = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_MAX
    WireType_ARRAYSIZE = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_ARRAYSIZE
    __swig_getmethods__["WireType_IsValid"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_IsValid
    if _newclass:WireType_IsValid = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_WireType_IsValid)
    WireType_USES_DOUBLE_HASHING = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_WireType_USES_DOUBLE_HASHING
    LABEL_OPTIONAL = _net_proto_pywraptagmapper.ProtocolDescriptor_LABEL_OPTIONAL
    LABEL_REQUIRED = _net_proto_pywraptagmapper.ProtocolDescriptor_LABEL_REQUIRED
    LABEL_REPEATED = _net_proto_pywraptagmapper.ProtocolDescriptor_LABEL_REPEATED
    __swig_getmethods__["Label_Parse"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_Label_Parse
    if _newclass:Label_Parse = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_Label_Parse)
    __swig_getmethods__["Label_Name"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_Label_Name
    if _newclass:Label_Name = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_Label_Name)
    Label_MIN = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_MIN
    Label_MAX = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_MAX
    Label_ARRAYSIZE = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_ARRAYSIZE
    __swig_getmethods__["Label_IsValid"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_Label_IsValid
    if _newclass:Label_IsValid = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_Label_IsValid)
    Label_USES_DOUBLE_HASHING = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_Label_USES_DOUBLE_HASHING
    TYPE_DOUBLE = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_DOUBLE
    TYPE_FLOAT = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_FLOAT
    TYPE_INT64 = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_INT64
    TYPE_UINT64 = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_UINT64
    TYPE_INT32 = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_INT32
    TYPE_FIXED64 = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_FIXED64
    TYPE_FIXED32 = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_FIXED32
    TYPE_BOOL = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_BOOL
    TYPE_STRING = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_STRING
    TYPE_GROUP = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_GROUP
    TYPE_FOREIGN = _net_proto_pywraptagmapper.ProtocolDescriptor_TYPE_FOREIGN
    __swig_getmethods__["DeclaredType_Parse"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Parse
    if _newclass:DeclaredType_Parse = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Parse)
    __swig_getmethods__["DeclaredType_Name"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Name
    if _newclass:DeclaredType_Name = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Name)
    DeclaredType_MIN = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_MIN
    DeclaredType_MAX = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_MAX
    DeclaredType_ARRAYSIZE = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_ARRAYSIZE
    __swig_getmethods__["DeclaredType_IsValid"] = lambda x: _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_IsValid
    if _newclass:DeclaredType_IsValid = staticmethod(_net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_IsValid)
    DeclaredType_USES_DOUBLE_HASHING = _net_proto_pywraptagmapper.cvar.ProtocolDescriptor_DeclaredType_USES_DOUBLE_HASHING
    kfilename = _net_proto_pywraptagmapper.ProtocolDescriptor_kfilename
    kname = _net_proto_pywraptagmapper.ProtocolDescriptor_kname
    kTagGroup = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagGroup
    kTagname = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagname
    kTagnumber = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagnumber
    kTagwire_type = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagwire_type
    kTagdeclared_type = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagdeclared_type
    kTaglabel = _net_proto_pywraptagmapper.ProtocolDescriptor_kTaglabel
    kTagdefault_value = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagdefault_value
    kTagforeign = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagforeign
    kTagflags = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagflags
    kTagparent = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagparent
    kTagenum_id = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagenum_id
    kTagOptionGroup = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagOptionGroup
    kTagOptionname = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagOptionname
    kTagOptionvalue = _net_proto_pywraptagmapper.ProtocolDescriptor_kTagOptionvalue
    kEnumTypeGroup = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypeGroup
    kEnumTypename = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypename
    kEnumTypeparent = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypeparent
    kEnumTypeTagGroup = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypeTagGroup
    kEnumTypeTagname = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypeTagname
    kEnumTypeTagvalue = _net_proto_pywraptagmapper.ProtocolDescriptor_kEnumTypeTagvalue

class ProtocolDescriptorPtr(ProtocolDescriptor):
    def __init__(self, this):
        _swig_setattr(self, ProtocolDescriptor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolDescriptor, 'thisown', 0)
        _swig_setattr(self, ProtocolDescriptor,self.__class__,ProtocolDescriptor)
_net_proto_pywraptagmapper.ProtocolDescriptor_swigregister(ProtocolDescriptorPtr)

ProtocolDescriptor_default_instance = _net_proto_pywraptagmapper.ProtocolDescriptor_default_instance

ProtocolDescriptor_WireType_Parse = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Parse

ProtocolDescriptor_WireType_Name = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_Name

ProtocolDescriptor_WireType_IsValid = _net_proto_pywraptagmapper.ProtocolDescriptor_WireType_IsValid

ProtocolDescriptor_Label_Parse = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_Parse

ProtocolDescriptor_Label_Name = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_Name

ProtocolDescriptor_Label_IsValid = _net_proto_pywraptagmapper.ProtocolDescriptor_Label_IsValid

ProtocolDescriptor_DeclaredType_Parse = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Parse

ProtocolDescriptor_DeclaredType_Name = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_Name

ProtocolDescriptor_DeclaredType_IsValid = _net_proto_pywraptagmapper.ProtocolDescriptor_DeclaredType_IsValid

class ProtocolFileDescriptor(ProtocolMessage):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessage]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, ProtocolFileDescriptor, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessage]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, ProtocolFileDescriptor, name)
    def __repr__(self):
        return "<C ProtocolFileDescriptor instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_ProtocolFileDescriptor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, ProtocolFileDescriptor, 'this', _net_proto_pywraptagmapper.new_ProtocolFileDescriptor(*args))
        _swig_setattr(self, ProtocolFileDescriptor, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.ProtocolFileDescriptor__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.ProtocolFileDescriptor_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.ProtocolFileDescriptor_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_Swap(*args)
    def CheckTypeAndSwap(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_CheckTypeAndSwap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_Clear(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_SpaceUsed(*args)
    def GetMapper(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_GetMapper(*args)
    def New(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_New(*args)
    def filename(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_filename(*args)
    def set_filename(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_set_filename(*args)
    def mutable_filename(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_mutable_filename(*args)
    def clear_filename(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_clear_filename(*args)
    def type_size(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_type_size(*args)
    def clear_type(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_clear_type(*args)
    def type(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_type(*args)
    def set_type(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_set_type(*args)
    def mutable_type(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_mutable_type(*args)
    def mutable_type_array(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_mutable_type_array(*args)
    def type_array(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_type_array(*args)
    def add_type(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_add_type(*args)
    def service_size(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_service_size(*args)
    def clear_service(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_clear_service(*args)
    def service(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_service(*args)
    def set_service(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_set_service(*args)
    def mutable_service(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_mutable_service(*args)
    def mutable_service_array(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_mutable_service_array(*args)
    def service_array(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_service_array(*args)
    def add_service(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_add_service(*args)
    def has_filename(*args): return _net_proto_pywraptagmapper.ProtocolFileDescriptor_has_filename(*args)
    kfilename = _net_proto_pywraptagmapper.ProtocolFileDescriptor_kfilename
    ktype = _net_proto_pywraptagmapper.ProtocolFileDescriptor_ktype
    kservice = _net_proto_pywraptagmapper.ProtocolFileDescriptor_kservice

class ProtocolFileDescriptorPtr(ProtocolFileDescriptor):
    def __init__(self, this):
        _swig_setattr(self, ProtocolFileDescriptor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, ProtocolFileDescriptor, 'thisown', 0)
        _swig_setattr(self, ProtocolFileDescriptor,self.__class__,ProtocolFileDescriptor)
_net_proto_pywraptagmapper.ProtocolFileDescriptor_swigregister(ProtocolFileDescriptorPtr)

ProtocolFileDescriptor_default_instance = _net_proto_pywraptagmapper.ProtocolFileDescriptor_default_instance

class RPC_ServiceDescriptor_Method(ProtocolMessageGroup):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RPC_ServiceDescriptor_Method, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessageGroup]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RPC_ServiceDescriptor_Method, name)
    def __repr__(self):
        return "<C RPC_ServiceDescriptor_Method instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_RPC_ServiceDescriptor_Method):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, RPC_ServiceDescriptor_Method, 'this', _net_proto_pywraptagmapper.new_RPC_ServiceDescriptor_Method(*args))
        _swig_setattr(self, RPC_ServiceDescriptor_Method, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.RPC_ServiceDescriptor_Method__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_Swap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_Clear(*args)
    def IsInitialized(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_IsInitialized(*args)
    def New(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_New(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_SpaceUsed(*args)
    def name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_name(*args)
    def argument_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_argument_type(*args)
    def set_argument_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_argument_type(*args)
    def mutable_argument_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_argument_type(*args)
    def clear_argument_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_argument_type(*args)
    def result_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_result_type(*args)
    def set_result_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_result_type(*args)
    def mutable_result_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_result_type(*args)
    def clear_result_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_result_type(*args)
    def stream_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_stream_type(*args)
    def set_stream_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_stream_type(*args)
    def mutable_stream_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_stream_type(*args)
    def clear_stream_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_stream_type(*args)
    def protocol(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_protocol(*args)
    def set_protocol(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_protocol(*args)
    def mutable_protocol(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_protocol(*args)
    def clear_protocol(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_protocol(*args)
    def deadline(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_deadline(*args)
    def set_deadline(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_deadline(*args)
    def clear_deadline(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_deadline(*args)
    def duplicate_suppression(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_duplicate_suppression(*args)
    def set_duplicate_suppression(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_duplicate_suppression(*args)
    def clear_duplicate_suppression(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_duplicate_suppression(*args)
    def fail_fast(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_fail_fast(*args)
    def set_fail_fast(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_fail_fast(*args)
    def clear_fail_fast(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_fail_fast(*args)
    def client_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_client_logging(*args)
    def set_client_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_client_logging(*args)
    def clear_client_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_client_logging(*args)
    def server_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_server_logging(*args)
    def set_server_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_server_logging(*args)
    def clear_server_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_server_logging(*args)
    def security_level(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_security_level(*args)
    def set_security_level(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_security_level(*args)
    def mutable_security_level(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_security_level(*args)
    def clear_security_level(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_security_level(*args)
    def response_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_response_format(*args)
    def set_response_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_response_format(*args)
    def mutable_response_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_response_format(*args)
    def clear_response_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_response_format(*args)
    def request_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_request_format(*args)
    def set_request_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_set_request_format(*args)
    def mutable_request_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_mutable_request_format(*args)
    def clear_request_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_clear_request_format(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_name(*args)
    def has_argument_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_argument_type(*args)
    def has_result_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_result_type(*args)
    def has_stream_type(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_stream_type(*args)
    def has_protocol(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_protocol(*args)
    def has_deadline(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_deadline(*args)
    def has_duplicate_suppression(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_duplicate_suppression(*args)
    def has_fail_fast(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_fail_fast(*args)
    def has_client_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_client_logging(*args)
    def has_server_logging(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_server_logging(*args)
    def has_security_level(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_security_level(*args)
    def has_response_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_response_format(*args)
    def has_request_format(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_has_request_format(*args)

class RPC_ServiceDescriptor_MethodPtr(RPC_ServiceDescriptor_Method):
    def __init__(self, this):
        _swig_setattr(self, RPC_ServiceDescriptor_Method, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RPC_ServiceDescriptor_Method, 'thisown', 0)
        _swig_setattr(self, RPC_ServiceDescriptor_Method,self.__class__,RPC_ServiceDescriptor_Method)
_net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_swigregister(RPC_ServiceDescriptor_MethodPtr)

RPC_ServiceDescriptor_Method_default_instance = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Method_default_instance

class RPC_ServiceDescriptor(ProtocolMessage):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessage]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RPC_ServiceDescriptor, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessage]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RPC_ServiceDescriptor, name)
    def __repr__(self):
        return "<C RPC_ServiceDescriptor instance at %s>" % (self.this,)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_RPC_ServiceDescriptor):
        try:
            if self.thisown: destroy(self)
        except: pass
    def __init__(self, *args):
        _swig_setattr(self, RPC_ServiceDescriptor, 'this', _net_proto_pywraptagmapper.new_RPC_ServiceDescriptor(*args))
        _swig_setattr(self, RPC_ServiceDescriptor, 'thisown', 1)
    _internal_layout = _net_proto_pywraptagmapper.cvar.RPC_ServiceDescriptor__internal_layout
    __swig_getmethods__["default_instance"] = lambda x: _net_proto_pywraptagmapper.RPC_ServiceDescriptor_default_instance
    if _newclass:default_instance = staticmethod(_net_proto_pywraptagmapper.RPC_ServiceDescriptor_default_instance)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_MergeFrom(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_CopyFrom(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Equivalent(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Swap(*args)
    def CheckTypeAndSwap(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_CheckTypeAndSwap(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_FindInitializationError(*args)
    def clear(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_Clear(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_RawOutputToBuffer(*args)
    def RawOutputToArray(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_RawOutputToArray(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_InternalMergeFrom(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_SpaceUsed(*args)
    def GetMapper(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_GetMapper(*args)
    def New(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_New(*args)
    def filename(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_filename(*args)
    def set_filename(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_set_filename(*args)
    def mutable_filename(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_mutable_filename(*args)
    def clear_filename(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear_filename(*args)
    def name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_name(*args)
    def set_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_set_name(*args)
    def mutable_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_mutable_name(*args)
    def clear_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear_name(*args)
    def full_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_full_name(*args)
    def set_full_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_set_full_name(*args)
    def mutable_full_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_mutable_full_name(*args)
    def clear_full_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear_full_name(*args)
    def failure_detection_delay(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_failure_detection_delay(*args)
    def set_failure_detection_delay(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_set_failure_detection_delay(*args)
    def clear_failure_detection_delay(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear_failure_detection_delay(*args)
    def method_size(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_method_size(*args)
    def clear_method(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_clear_method(*args)
    def method(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_method(*args)
    def method_array(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_method_array(*args)
    def mutable_method(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_mutable_method(*args)
    def mutable_method_array(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_mutable_method_array(*args)
    def add_method(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_add_method(*args)
    def has_filename(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_has_filename(*args)
    def has_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_has_name(*args)
    def has_full_name(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_has_full_name(*args)
    def has_failure_detection_delay(*args): return _net_proto_pywraptagmapper.RPC_ServiceDescriptor_has_failure_detection_delay(*args)
    kfilename = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kfilename
    kname = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kname
    kfull_name = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kfull_name
    kfailure_detection_delay = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kfailure_detection_delay
    kMethodGroup = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodGroup
    kMethodname = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodname
    kMethodargument_type = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodargument_type
    kMethodresult_type = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodresult_type
    kMethodstream_type = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodstream_type
    kMethodprotocol = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodprotocol
    kMethoddeadline = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethoddeadline
    kMethodduplicate_suppression = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodduplicate_suppression
    kMethodfail_fast = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodfail_fast
    kMethodclient_logging = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodclient_logging
    kMethodserver_logging = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodserver_logging
    kMethodsecurity_level = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodsecurity_level
    kMethodresponse_format = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodresponse_format
    kMethodrequest_format = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_kMethodrequest_format

class RPC_ServiceDescriptorPtr(RPC_ServiceDescriptor):
    def __init__(self, this):
        _swig_setattr(self, RPC_ServiceDescriptor, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RPC_ServiceDescriptor, 'thisown', 0)
        _swig_setattr(self, RPC_ServiceDescriptor,self.__class__,RPC_ServiceDescriptor)
_net_proto_pywraptagmapper.RPC_ServiceDescriptor_swigregister(RPC_ServiceDescriptorPtr)

RPC_ServiceDescriptor_default_instance = _net_proto_pywraptagmapper.RPC_ServiceDescriptor_default_instance

class TagMapper__NameInfo(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TagMapper__NameInfo, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TagMapper__NameInfo, name)
    def __repr__(self):
        return "<C TagMapper__NameInfo instance at %s>" % (self.this,)
    __swig_setmethods__["name"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_name_set
    __swig_getmethods__["name"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_name_get
    if _newclass:name = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_name_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_name_set)
    __swig_setmethods__["basename"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_basename_set
    __swig_getmethods__["basename"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_basename_get
    if _newclass:basename = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_basename_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_basename_set)
    __swig_setmethods__["tag"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_tag_set
    __swig_getmethods__["tag"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_tag_get
    if _newclass:tag = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_tag_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_tag_set)
    __swig_setmethods__["wire_type"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_wire_type_set
    __swig_getmethods__["wire_type"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_wire_type_get
    if _newclass:wire_type = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_wire_type_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_wire_type_set)
    __swig_setmethods__["declared_type"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_declared_type_set
    __swig_getmethods__["declared_type"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_declared_type_get
    if _newclass:declared_type = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_declared_type_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_declared_type_set)
    __swig_setmethods__["label"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_label_set
    __swig_getmethods__["label"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_label_get
    if _newclass:label = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_label_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_label_set)
    __swig_setmethods__["defaultval"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_defaultval_set
    __swig_getmethods__["defaultval"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_defaultval_get
    if _newclass:defaultval = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_defaultval_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_defaultval_set)
    __swig_setmethods__["foreign"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_foreign_set
    __swig_getmethods__["foreign"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_foreign_get
    if _newclass:foreign = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_foreign_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_foreign_set)
    __swig_setmethods__["flags"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_flags_set
    __swig_getmethods__["flags"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_flags_get
    if _newclass:flags = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_flags_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_flags_set)
    __swig_setmethods__["field_offset_in_bytes"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_field_offset_in_bytes_set
    __swig_getmethods__["field_offset_in_bytes"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_field_offset_in_bytes_get
    if _newclass:field_offset_in_bytes = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_field_offset_in_bytes_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_field_offset_in_bytes_set)
    __swig_setmethods__["has_bit_index"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_has_bit_index_set
    __swig_getmethods__["has_bit_index"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_has_bit_index_get
    if _newclass:has_bit_index = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_has_bit_index_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_has_bit_index_set)
    __swig_setmethods__["held_via_pointer"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_held_via_pointer_set
    __swig_getmethods__["held_via_pointer"] = _net_proto_pywraptagmapper.TagMapper__NameInfo_held_via_pointer_get
    if _newclass:held_via_pointer = property(_net_proto_pywraptagmapper.TagMapper__NameInfo_held_via_pointer_get, _net_proto_pywraptagmapper.TagMapper__NameInfo_held_via_pointer_set)
    def __init__(self, *args):
        _swig_setattr(self, TagMapper__NameInfo, 'this', _net_proto_pywraptagmapper.new_TagMapper__NameInfo(*args))
        _swig_setattr(self, TagMapper__NameInfo, 'thisown', 1)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_TagMapper__NameInfo):
        try:
            if self.thisown: destroy(self)
        except: pass

class TagMapper__NameInfoPtr(TagMapper__NameInfo):
    def __init__(self, this):
        _swig_setattr(self, TagMapper__NameInfo, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, TagMapper__NameInfo, 'thisown', 0)
        _swig_setattr(self, TagMapper__NameInfo,self.__class__,TagMapper__NameInfo)
_net_proto_pywraptagmapper.TagMapper__NameInfo_swigregister(TagMapper__NameInfoPtr)


ProtocolMessagetoASCII = _net_proto_pywraptagmapper.ProtocolMessagetoASCII

ASCIItoProtocolMessage = _net_proto_pywraptagmapper.ASCIItoProtocolMessage
class RawMessage(ProtocolMessage):
    __swig_setmethods__ = {}
    for _s in [ProtocolMessage]: __swig_setmethods__.update(_s.__swig_setmethods__)
    __setattr__ = lambda self, name, value: _swig_setattr(self, RawMessage, name, value)
    __swig_getmethods__ = {}
    for _s in [ProtocolMessage]: __swig_getmethods__.update(_s.__swig_getmethods__)
    __getattr__ = lambda self, name: _swig_getattr(self, RawMessage, name)
    def __repr__(self):
        return "<C RawMessage instance at %s>" % (self.this,)
    def __init__(self, *args):
        _swig_setattr(self, RawMessage, 'this', _net_proto_pywraptagmapper.new_RawMessage(*args))
        _swig_setattr(self, RawMessage, 'thisown', 1)
    def __del__(self, destroy=_net_proto_pywraptagmapper.delete_RawMessage):
        try:
            if self.thisown: destroy(self)
        except: pass
    _internal_layout = _net_proto_pywraptagmapper.cvar.RawMessage__internal_layout
    def contents(*args): return _net_proto_pywraptagmapper.RawMessage_contents(*args)
    def const_contents(*args): return _net_proto_pywraptagmapper.RawMessage_const_contents(*args)
    def FindInitializationError(*args): return _net_proto_pywraptagmapper.RawMessage_FindInitializationError(*args)
    def Clear(*args): return _net_proto_pywraptagmapper.RawMessage_Clear(*args)
    def RawOutputToBuffer(*args): return _net_proto_pywraptagmapper.RawMessage_RawOutputToBuffer(*args)
    def InternalMergeFrom(*args): return _net_proto_pywraptagmapper.RawMessage_InternalMergeFrom(*args)
    def GetMapper(*args): return _net_proto_pywraptagmapper.RawMessage_GetMapper(*args)
    def New(*args): return _net_proto_pywraptagmapper.RawMessage_New(*args)
    def ByteSize(*args): return _net_proto_pywraptagmapper.RawMessage_ByteSize(*args)
    def SpaceUsed(*args): return _net_proto_pywraptagmapper.RawMessage_SpaceUsed(*args)
    def CopyFrom(*args): return _net_proto_pywraptagmapper.RawMessage_CopyFrom(*args)
    def MergeFrom(*args): return _net_proto_pywraptagmapper.RawMessage_MergeFrom(*args)
    def Swap(*args): return _net_proto_pywraptagmapper.RawMessage_Swap(*args)
    def Compare(*args): return _net_proto_pywraptagmapper.RawMessage_Compare(*args)
    def Equals(*args): return _net_proto_pywraptagmapper.RawMessage_Equals(*args)
    def Equivalent(*args): return _net_proto_pywraptagmapper.RawMessage_Equivalent(*args)
    def clear(*args): return _net_proto_pywraptagmapper.RawMessage_clear(*args)
    def PM(*args): return _net_proto_pywraptagmapper.RawMessage_PM(*args)
    def GetValue(*args): return _net_proto_pywraptagmapper.RawMessage_GetValue(*args)

class RawMessagePtr(RawMessage):
    def __init__(self, this):
        _swig_setattr(self, RawMessage, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, RawMessage, 'thisown', 0)
        _swig_setattr(self, RawMessage,self.__class__,RawMessage)
_net_proto_pywraptagmapper.RawMessage_swigregister(RawMessagePtr)



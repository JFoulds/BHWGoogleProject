# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _webutil_http_pywrapcontenttype

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
        _swig_setattr(self, stringVector, 'this', _webutil_http_pywrapcontenttype.new_stringVector(*args))
        _swig_setattr(self, stringVector, 'thisown', 1)
    def __del__(self, destroy=_webutil_http_pywrapcontenttype.delete_stringVector):
        try:
            if self.thisown: destroy(self)
        except: pass

class stringVectorPtr(stringVector):
    def __init__(self, this):
        _swig_setattr(self, stringVector, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, stringVector, 'thisown', 0)
        _swig_setattr(self, stringVector,self.__class__,stringVector)
_webutil_http_pywrapcontenttype.stringVector_swigregister(stringVectorPtr)

CONTENT_FIRST_TYPE = _webutil_http_pywrapcontenttype.CONTENT_FIRST_TYPE
CONTENT_GOOGLE_ERROR = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_ERROR
CONTENT_GOOGLE_EMPTY = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_EMPTY
CONTENT_GOOGLE_OTHER = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_OTHER
CONTENT_TEXT_HTML = _webutil_http_pywrapcontenttype.CONTENT_TEXT_HTML
CONTENT_TEXT_PLAIN = _webutil_http_pywrapcontenttype.CONTENT_TEXT_PLAIN
CONTENT_APPLICATION_POSTSCRIPT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_POSTSCRIPT
CONTENT_APPLICATION_PDF = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_PDF
CONTENT_TEXT_WML = _webutil_http_pywrapcontenttype.CONTENT_TEXT_WML
CONTENT_GOOGLE_WHITEPAGE = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_WHITEPAGE
CONTENT_TEXT_HDML = _webutil_http_pywrapcontenttype.CONTENT_TEXT_HDML
CONTENT_TEXT_PDF = _webutil_http_pywrapcontenttype.CONTENT_TEXT_PDF
CONTENT_GOOGLE_USENET = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_USENET
CONTENT_IMAGE = _webutil_http_pywrapcontenttype.CONTENT_IMAGE
CONTENT_IMAGE_THUMBNAIL = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_THUMBNAIL
CONTENT_AUDIO_MP3 = _webutil_http_pywrapcontenttype.CONTENT_AUDIO_MP3
CONTENT_TEXT_POSTSCRIPT = _webutil_http_pywrapcontenttype.CONTENT_TEXT_POSTSCRIPT
CONTENT_APPLICATION_MSWORD = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_MSWORD
CONTENT_TEXT_MSWORD = _webutil_http_pywrapcontenttype.CONTENT_TEXT_MSWORD
CONTENT_APPLICATION_MS_POWERPOINT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_MS_POWERPOINT
CONTENT_TEXT_MS_POWERPOINT = _webutil_http_pywrapcontenttype.CONTENT_TEXT_MS_POWERPOINT
CONTENT_APPLICATION_RTF = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_RTF
CONTENT_TEXT_RTF = _webutil_http_pywrapcontenttype.CONTENT_TEXT_RTF
CONTENT_APPLICATION_MS_EXCEL = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_MS_EXCEL
CONTENT_TEXT_MS_EXCEL = _webutil_http_pywrapcontenttype.CONTENT_TEXT_MS_EXCEL
CONTENT_TEXT_OTHER = _webutil_http_pywrapcontenttype.CONTENT_TEXT_OTHER
CONTENT_APPLICATION_XSHOCKWAVEFLASH = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XSHOCKWAVEFLASH
CONTENT_TEXT_XSHOCKWAVEFLASH = _webutil_http_pywrapcontenttype.CONTENT_TEXT_XSHOCKWAVEFLASH
CONTENT_APPLICATION_XGZIP = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XGZIP
CONTENT_IMAGE_JPEG = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_JPEG
CONTENT_IMAGE_XDJVU = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_XDJVU
CONTENT_SCAN_ATTR = _webutil_http_pywrapcontenttype.CONTENT_SCAN_ATTR
CONTENT_SCAN_FAKE_HTML = _webutil_http_pywrapcontenttype.CONTENT_SCAN_FAKE_HTML
CONTENT_GOOGLE_QECONOMY = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_QECONOMY
CONTENT_GOOGLE_FROOGLE_OFFER = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_FROOGLE_OFFER
CONTENT_GOOGLE_DPL = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_DPL
CONTENT_GOOGLE_YP = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_YP
CONTENT_APPLICATION_XML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XML
CONTENT_GOOGLE_OCEAN_METADATA = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_OCEAN_METADATA
CONTENT_GOOGLE_LOCALSEARCH = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_LOCALSEARCH
CONTENT_BINARY_OTHER = _webutil_http_pywrapcontenttype.CONTENT_BINARY_OTHER
CONTENT_APPLICATION_ATOM_XML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_ATOM_XML
CONTENT_APPLICATION_RDF_XML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_RDF_XML
CONTENT_APPLICATION_RSS_XML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_RSS_XML
CONTENT_APPLICATION_XHTML_XML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XHTML_XML
CONTENT_APPLICATION_OCTET_STREAM = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_OCTET_STREAM
CONTENT_TEXT_XML = _webutil_http_pywrapcontenttype.CONTENT_TEXT_XML
CONTENT_GOOGLE_OCEAN_DOC = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_OCEAN_DOC
CONTENT_IMAGE_PNG = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_PNG
CONTENT_IMAGE_GIF = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_GIF
CONTENT_IMAGE_TIFF = _webutil_http_pywrapcontenttype.CONTENT_IMAGE_TIFF
CONTENT_APPLICATION_ZIP_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_ZIP_ARCHIVE
CONTENT_TEXT_ZIP_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_TEXT_ZIP_ARCHIVE
CONTENT_APPLICATION_XGZIP_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XGZIP_ARCHIVE
CONTENT_TEXT_XGZIP_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_TEXT_XGZIP_ARCHIVE
CONTENT_APPLICATION_XTAR_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XTAR_ARCHIVE
CONTENT_TEXT_XTAR_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_TEXT_XTAR_ARCHIVE
CONTENT_APPLICATION_XCOMPRESS_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XCOMPRESS_ARCHIVE
CONTENT_TEXT_XCOMPRESS_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_TEXT_XCOMPRESS_ARCHIVE
CONTENT_APPLICATION_WAP_XHTML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_WAP_XHTML
CONTENT_APPLICATION_XJAVASCRIPT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_XJAVASCRIPT
CONTENT_APPLICATION_JAVASCRIPT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_JAVASCRIPT
CONTENT_APPLICATION_ECMASCRIPT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_ECMASCRIPT
CONTENT_TEXT_JAVASCRIPT = _webutil_http_pywrapcontenttype.CONTENT_TEXT_JAVASCRIPT
CONTENT_TEXT_ECMASCRIPT = _webutil_http_pywrapcontenttype.CONTENT_TEXT_ECMASCRIPT
CONTENT_APPLICATION_KML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_KML
CONTENT_APPLICATION_KMZ_ARCHIVE = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_KMZ_ARCHIVE
CONTENT_TEXT_KML = _webutil_http_pywrapcontenttype.CONTENT_TEXT_KML
CONTENT_APPLICATION_DWF = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_DWF
CONTENT_DRAWING_DWF = _webutil_http_pywrapcontenttype.CONTENT_DRAWING_DWF
CONTENT_TEXT_DWF = _webutil_http_pywrapcontenttype.CONTENT_TEXT_DWF
CONTENT_APPLICATION_ODF = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_ODF
CONTENT_TEXT_ODF = _webutil_http_pywrapcontenttype.CONTENT_TEXT_ODF
CONTENT_GOOGLE_NEW = _webutil_http_pywrapcontenttype.CONTENT_GOOGLE_NEW
CONTENT_APPLICATION_OPENXML_WORD = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_OPENXML_WORD
CONTENT_TEXT_OPENXML_WORD = _webutil_http_pywrapcontenttype.CONTENT_TEXT_OPENXML_WORD
CONTENT_APPLICATION_OPENXML_EXCEL = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_OPENXML_EXCEL
CONTENT_TEXT_OPENXML_EXCEL = _webutil_http_pywrapcontenttype.CONTENT_TEXT_OPENXML_EXCEL
CONTENT_APPLICATION_OPENXML_POWERPOINT = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_OPENXML_POWERPOINT
CONTENT_TEXT_OPENXML_POWERPOINT = _webutil_http_pywrapcontenttype.CONTENT_TEXT_OPENXML_POWERPOINT
CONTENT_APPLICATION_OPENXML = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_OPENXML
CONTENT_TEXT_CSS = _webutil_http_pywrapcontenttype.CONTENT_TEXT_CSS
CONTENT_APPLICATION_JSON = _webutil_http_pywrapcontenttype.CONTENT_APPLICATION_JSON
CONTENT_NUM_TYPES = _webutil_http_pywrapcontenttype.CONTENT_NUM_TYPES

IsKnownContentType = _webutil_http_pywrapcontenttype.IsKnownContentType

ToKnownContentType = _webutil_http_pywrapcontenttype.ToKnownContentType

LogUnknownContentType = _webutil_http_pywrapcontenttype.LogUnknownContentType

LogIfUnknownContentType = _webutil_http_pywrapcontenttype.LogIfUnknownContentType

ContentTypeName = _webutil_http_pywrapcontenttype.ContentTypeName

ContentTypeMime = _webutil_http_pywrapcontenttype.ContentTypeMime

ContentTypeProperties = _webutil_http_pywrapcontenttype.ContentTypeProperties

ContentTypeFromName = _webutil_http_pywrapcontenttype.ContentTypeFromName

ContentTypeFromMime = _webutil_http_pywrapcontenttype.ContentTypeFromMime

ContentTypeFromExt = _webutil_http_pywrapcontenttype.ContentTypeFromExt

ConvertedContentTypeFromExt = _webutil_http_pywrapcontenttype.ConvertedContentTypeFromExt

ConvertedContentType = _webutil_http_pywrapcontenttype.ConvertedContentType

ValidTextExtension = _webutil_http_pywrapcontenttype.ValidTextExtension

GetOpenXMLSubType = _webutil_http_pywrapcontenttype.GetOpenXMLSubType

GetMimeTypeFromContent = _webutil_http_pywrapcontenttype.GetMimeTypeFromContent

ContentTypeFromHttpHeadersExtAndContent = _webutil_http_pywrapcontenttype.ContentTypeFromHttpHeadersExtAndContent

ContentTypeFromNameNoFail = _webutil_http_pywrapcontenttype.ContentTypeFromNameNoFail

ContentTypeFromMimeNoFail = _webutil_http_pywrapcontenttype.ContentTypeFromMimeNoFail

ContentTypeFromExtNoFail = _webutil_http_pywrapcontenttype.ContentTypeFromExtNoFail

ConvertedContentTypeFromExtNoFail = _webutil_http_pywrapcontenttype.ConvertedContentTypeFromExtNoFail

ContentTypeUsesPDFToHTML = _webutil_http_pywrapcontenttype.ContentTypeUsesPDFToHTML

ContentTypeCanConvertEncoding = _webutil_http_pywrapcontenttype.ContentTypeCanConvertEncoding

ContentTypeCanTranslate = _webutil_http_pywrapcontenttype.ContentTypeCanTranslate

ContentTypeShowUntitled = _webutil_http_pywrapcontenttype.ContentTypeShowUntitled

ContentTypeHasBogusLength = _webutil_http_pywrapcontenttype.ContentTypeHasBogusLength

ContentTypeHasTextVersion = _webutil_http_pywrapcontenttype.ContentTypeHasTextVersion

ContentTypeHasHTMLVersion = _webutil_http_pywrapcontenttype.ContentTypeHasHTMLVersion

ContentTypeHasAlternateVersion = _webutil_http_pywrapcontenttype.ContentTypeHasAlternateVersion

ContentTypeIsJavascript = _webutil_http_pywrapcontenttype.ContentTypeIsJavascript

ContentTypeDontUncompress = _webutil_http_pywrapcontenttype.ContentTypeDontUncompress

ContentTypeIsXML = _webutil_http_pywrapcontenttype.ContentTypeIsXML

ContentTypeIsAllowedInOutput = _webutil_http_pywrapcontenttype.ContentTypeIsAllowedInOutput
cvar = _webutil_http_pywrapcontenttype.cvar
kMaxContentTypeNameLen = cvar.kMaxContentTypeNameLen
CT_PROPERTY_NONE = cvar.CT_PROPERTY_NONE
CT_PROPERTY_BOGUS_LEN = cvar.CT_PROPERTY_BOGUS_LEN
CT_PROPERTY_TEXT_VERSION = cvar.CT_PROPERTY_TEXT_VERSION
CT_PROPERTY_HTML_VERSION = cvar.CT_PROPERTY_HTML_VERSION
CT_PROPERTY_NO_UNTITLED = cvar.CT_PROPERTY_NO_UNTITLED
CT_PROPERTY_CAN_TRANSLATE = cvar.CT_PROPERTY_CAN_TRANSLATE
CT_PROPERTY_CAN_CONVERT_ENCODING = cvar.CT_PROPERTY_CAN_CONVERT_ENCODING
CT_PROPERTY_USES_PDFTOHTML = cvar.CT_PROPERTY_USES_PDFTOHTML
CT_PROPERTY_IS_JAVASCRIPT = cvar.CT_PROPERTY_IS_JAVASCRIPT
CT_PROPERTY_DONT_UNCOMPRESS = cvar.CT_PROPERTY_DONT_UNCOMPRESS
CT_PROPERTY_IS_XML = cvar.CT_PROPERTY_IS_XML
CT_PROPERTY_CONTENT_DISPOSITION_ATTACHMENT = cvar.CT_PROPERTY_CONTENT_DISPOSITION_ATTACHMENT
CT_PROPERTY_ALLOWED_IN_OUTPUT = cvar.CT_PROPERTY_ALLOWED_IN_OUTPUT


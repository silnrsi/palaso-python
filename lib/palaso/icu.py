from ctypes import *
from ctypes.util import *
import sys, os


class icu(object) :

    UChar = c_uint16
    UCharP = POINTER(c_uint16)
    UChar32 = c_uint32
    UChar32P = POINTER(c_uint32)
    UDate = c_double
    UErrorCode = c_int
    UErrorCodeP = POINTER(c_int)
    def U_SUCCESS(self, x) : return x <= 0
    UVersionInfo = c_uint8 * 4
    UEnumerationP = c_void_p
    StringEnumerationP = c_void_p
    UTextP = c_void_p
    ULocDataLocaleType = c_int
    ULayoutType = c_int
    UAcceptResult = c_int
    UNESCAPE_CHAR_AT = CFUNCTYPE(c_uint16, c_int32, c_void_p)
    UCaseMapP = c_void_p
    UResourceBundleP = c_void_p
    UResType = c_int

    # uchar.h
    UProperty = c_int
    UCharCategory = c_int
    UCharDirection = c_int
    UBlockCode = c_int
    UEastAsianWidth = c_int
    UCharNameChoice = c_int
    UPropertyNameChoice = c_int
    UDecompositionType = c_int
    UJoiningType = c_int
    UJoiningGroup = c_int
    UGraphemeClusterBreak = c_int
    UWordBreakValues = c_int
    USentenceBreak = c_int
    ULineBreak = c_int
    UNumericType = c_int
    UHangulSyllableType = c_int
    UCharEnumTypeRange = CFUNCTYPE(c_bool, c_void_p, c_uint32, c_uint32, c_int)
    UEnumCharNamesFn = CFUNCTYPE(c_bool, c_void_p, c_uint32, c_int, c_char_p, c_int32)

    # ubidi.h
    UBiDiLevel = c_uint8
    UBiDiDirection = c_int
    UBiDiP = c_void_p
    UBiDiReorderingMode = c_int
    UBiDiReorderingOption = c_int
    UBiDiClassCallback = CFUNCTYPE(c_int, c_void_p, c_uint32)

    # ubrk.h
    UParseErrorP = c_void_p
    UBreakIteratorP = c_void_p
    UBreakIteratorType = c_int
    UWordBreak = c_int
    ULineBreakTag = c_int
    USentenceBreakTag = c_int

    # uclean.h
    UMTX = c_void_p
    UMtxInitFn = CFUNCTYPE(None, c_void_p, POINTER(c_void_p), POINTER(c_int)),
    UMtxFn = CFUNCTYPE(None, c_void_p, POINTER(c_void_p))
    UMtxAtomicFn = CFUNCTYPE(c_int32, c_void_p, POINTER(c_int32))
    UMemAllocFn = CFUNCTYPE(c_void_p, c_void_p, c_size_t)
    UMemReallocFn = CFUNCTYPE(c_void_p, c_void_p, c_size_t)
    UMemFreeFn = CFUNCTYPE(None, c_void_p, c_void_p)

    # ucnv.h and friends
    UConverterP = c_void_p
    UConverterCallbackReason = c_int
    UConverterFromUnicodeArgsP = c_void_p
    UConverterToUnicodeArgsP = c_void_p
    UCNV_FROM_U_CALLBACK_STOP = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_uint32, c_int, POINTER(c_int))
    UCNV_TO_U_CALLBACK_STOP = CFUNCTYPE(None, c_void_p, c_void_p, c_char_p, c_int32, c_int, POINTER(c_int))
    UCNV_FROM_U_CALLBACK_SKIP = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_uint32, c_int, POINTER(c_int))
    UCNV_FROM_U_CALLBACK_SUBSTITUTE = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_uint32, c_int, POINTER(c_int))
    UCNV_FROM_U_CALLBACK_ESCAPE = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_uint32, c_int, POINTER(c_int))
    UCNV_TO_U_CALLBACK_SKIP = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_int, POINTER(c_int))
    UCNV_TO_U_CALLBACK_SUBSTITUTE = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_int, POINTER(c_int))
    UCNV_TO_U_CALLBACK_ESCAPE = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_int, POINTER(c_int))
    USetP = c_void_p
    UConverterType = c_int
    UConverterPlatform = c_int
    UConverterToUCallback = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_int, POINTER(c_int))
    UConverterFromUCallback = CFUNCTYPE(None, c_void_p, c_void_p, POINTER(c_uint16), c_int32, c_uint32, c_int, POINTER(c_int))
    UConverterUnicodeSet = c_int

    # uset.h
    USetP = c_void_p
    USetSpanCondition = c_int
    USerializedSetP = c_void_p



    def __init__(self) :
        if sys.platform == 'win32' :
            version = 0
            curr = None
            for p in os.environ['PATH'].split(os.pathsep) :
                for f in os.listdir(p) :
                    if f.startswith('icuuc') and f.endswith('.dll') :
                        m = re.search(ur'\d+', f)
                        if m :
                            v = int(f[m.start():m.end()], 10)
                            if v > version :
                                curr = os.path.join(p, f)
                                version = v
            if version == 0 :
                raise ImportError("Unable to find icu library")
            else :
                self._iculib = windll.LoadLibrary(curr)
                self._icuversion = version
        else :
            b = find_library('icuuc')
            if b is None :
                raise ImportError("Unable to find icu library")
            while os.path.islink(b) :
                b = os.readlink(b)
            m = re.search(ur'\d+', b)
            if m :
                v = int(b[m.start():m.end()], 10)
                self._icuversion = v
                self._iculib = cdll.LoadLibrary(b)
            else :
                raise ImportError("Unable to ascertain icu version from icu library")

    def __getattr__(self, name) :
        if name in self.__icufns__ :
            f = getattr(self._iculib, name + '_' + str(self._icuversion))
            i = self.__icufns__[name]
            f.restype = i[0]
            if i[1][-1] == self.UErrorCodeP :
                f.argtypes = i[1][:-1]
                def g (*parms) :
                    e = c_int(0);
                    parms.append(e)
                    res = f(*parms)
                    if e.val > 0 :
                        raise self.ICUError("Error: %d" % e)
                    return res
                setattr(self, name, g)
            else :
                f.argtypes = i[1]
                setattr(self, name, f)
            return getattr(self, name)
        else :
            raise AttributeError(name)

icu.__icufns__ = {
    # utypes.h
    'u_errorName' : (c_char_p, (icu.UErrorCode, )),

    # uenum.h
    'uenum_close' : (None, (icu.UEnumerationP, )),
    'uenum_count' : (c_int32, (icu.UEnumerationP, icu.UErrorCodeP)),
    'uenum_unext' : (icu.UCharP, (icu.UEnumerationP, POINTER(c_int32), icu.UErrorCodeP)),
    'uenum_next' : (c_char_p, (icu.UEnumerationP, POINTER(c_int32), icu.UErrorCodeP)),
    'uenum_reset' : (None, (icu.UEnumerationP, icu.UErrorCodeP)),
    'uenum_openFromString' : (icu.UEnumerationP, (icu.StringEnumerationP, icu.UErrorCodeP)),

    # uversion.h
    'u_versionFromString' : (None, (icu.UVersionInfo, c_char_p)),
    'u_versionFromUString' : (None, (icu.UVersionInfo, icu.UCharP)),
    'u_versionToString' : (None, (icu.UVersionInfo, c_char_p)),
    'u_getVersion' : (None, (icu.UVersionInfo, )),

    # ustring.h
    'u_strlen' : (c_int32, (icu.UCharP, )),
    'u_countChar32' : (c_int32, (icu.UCharP, c_int32)),
    'u_strHasMOreChar32Than' : (c_bool, (icu.UCharP, c_int32, c_int32)),
    'u_strcat' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_strncat' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_strstr' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_strFindFirst' : (icu.UCharP, (icu.UCharP, c_int32, icu.UCharP, c_int32)),
    'u_strchr' : (icu.UCharP, (icu.UCharP, icu.UChar)),
    'u_strchr32' : (icu.UCharP, (icu.UCharP, icu.UChar32)),
    'u_strrstr' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_strFindLast' : (icu.UCharP, (icu.UCharP, c_int32, icu.UCharP, c_int32)),
    'u_strrchr' : (icu.UCharP, (icu.UCharP, icu.UChar)),
    'u_strrchr32' : (icu.UCharP, (icu.UCharP, icu.UChar32)),
    'u_strpbrk' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_strcspn' : (c_int32, (icu.UCharP, icu.UCharP)),
    'u_strspn' : (c_int32, (icu.UCharP, icu.UCharP)),
    'u_strtok_r' : (icu.UCharP, (icu.UCharP, icu.UCharP, POINTER(icu.UCharP))),
    'u_strcmp' : (c_int32, (icu.UCharP, icu.UCharP)),
    'u_strcmpCodePointOrder' : (c_int32, (icu.UCharP, icu.UCharP)),
    'u_strCompare' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_bool)),
    'u_strCaseCompare' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_int32, icu.UErrorCodeP)),
    'u_strncmp' : (c_int32, (icu.UCharP, icu.UCharP, c_int32)),
    'u_strncmpCodePointOrder' : (c_int32, (icu.UCharP, icu.UCharP, c_int32)),
    'u_strcasecmp' : (c_int32, (icu.UCharP, icu.UCharP, c_int32)),
    'u_strncasecmp' : (c_int32, (icu.UCharP, icu.UCharP, c_int32, c_int32)),
    'u_memcasecmp' : (c_int32, (icu.UCharP, icu.UCharP, c_int32, c_int32)),
    'u_strcpy' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_strncpy' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_uastrcpy' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_uastrncpy' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_austrcpy' : (icu.UCharP, (icu.UCharP, icu.UCharP)),
    'u_austrncpy' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_memcpy' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_memmove' : (icu.UCharP, (icu.UCharP, icu.UCharP, c_int32)),
    'u_memset' : (icu.UCharP, (icu.UCharP, icu.UChar, c_int32)),
    'u_memcmp' : (c_int32, (icu.UCharP, icu.UCharP, c_int32)),
    'u_memcmpCodePointOrder' : (c_int32, (icu.UCharP, icu.UCharP, c_int32)),
    'u_memchr' : (icu.UCharP, (icu.UCharP, icu.UChar, c_int32)),
    'u_memchr32' : (icu.UCharP, (icu.UCharP, icu.UChar32, c_int32)),
    'u_memrchr' : (icu.UCharP, (icu.UCharP, icu.UChar, c_int32)),
    'u_memrchr32' : (icu.UCharP, (icu.UCharP, icu.UChar32, c_int32)),
    'u_unescape' : (c_int32, (c_char_p, icu.UCharP, c_int32)),
    'u_unescapeAt' : (icu.UChar32, (icu.UNESCAPE_CHAR_AT, POINTER(c_int32), c_int32, c_void_p)),
    'u_strToUpper' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_char_p, icu.UErrorCodeP)),
    'u_strToLower' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_char_p, icu.UErrorCodeP)),
    'u_strToTitle' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_char_p, icu.UErrorCodeP)),
    'u_strFoldCase' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_int32, icu.UErrorCodeP)),
    'u_strToWCS' : (c_wchar_p, (c_wchar_p, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UErrorCodeP)),
    'u_strFromWCS' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), c_wchar_p, c_int32, icu.UErrorCodeP)),
    'u_strToUTF8' : (c_char_p, (c_char_p, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UErrorCodeP)),
    'u_strFromUTF8' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), c_char_p, c_int32, icu.UErrorCodeP)),
    'u_strToUTF8WithSub' : (c_char_p, (c_char_p, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UChar32, POINTER(c_int32), icu.UErrorCodeP)),
    'u_strFromUTF8' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), c_char_p, c_int32, icu.UChar32, POINTER(c_int32), icu.UErrorCodeP)),
    'u_strFromUTF8Lenient' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), c_char_p, c_int32, icu.UErrorCodeP)),
    'u_strToUTF32' : (icu.UChar32P, (icu.UChar32P, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UErrorCodeP)),
    'u_strFromUTF32' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), icu.UChar32P, c_int32, icu.UErrorCodeP)),
    'u_strToUTF32WithSub' : (icu.UChar32P, (icu.UChar32P, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UChar32, POINTER(c_int32), icu.UErrorCodeP)),
    'u_strFromUTF32' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), icu.UChar32P, c_int32, icu.UChar32, POINTER(c_int32), icu.UErrorCodeP)),
    'u_strToJavaModifiedUTF8' : (c_char_p, (c_char_p, c_int32, POINTER(c_int32), icu.UCharP, c_int32, icu.UErrorCodeP)),
    'u_strFromJavaModifiedUTF8WithSub' : (icu.UCharP, (icu.UCharP, c_int32, POINTER(c_int32), c_char_p, c_int32, icu.UChar32, POINTER(c_int32), icu.UErrorCodeP)),

    # uchar.h
    'u_hasBinaryProperty' : (c_bool, (icu.UChar32, icu.UProperty)),
    'u_isUAlphabetic' : (c_bool, (icu.UChar32, )),
    'u_isULowercase' : (c_bool, (icu.UChar32, )),
    'u_isUUppercase' : (c_bool, (icu.UChar32, )),
    'u_isUWhiteSpace' : (c_bool, (icu.UChar32, )),
    'u_getIntProperty' : (c_int32, (icu.UChar32, icu.UProperty)),
    'u_getIntPropertyMinValue' : (c_int32, (icu.UProperty, )),
    'u_getIntPropertyMaxValue' : (c_int32, (icu.UProperty, )),
    'u_getNumericValue': (c_double, (icu.UChar32, )),
    'u_islower' : (c_bool, (icu.UChar32, )),
    'u_isupper' : (c_bool, (icu.UChar32, )),
    'u_istitle' : (c_bool, (icu.UChar32, )),
    'u_isdigit' : (c_bool, (icu.UChar32, )),
    'u_isalpha' : (c_bool, (icu.UChar32, )),
    'u_isalnum' : (c_bool, (icu.UChar32, )),
    'u_isxdigit' : (c_bool, (icu.UChar32, )),
    'u_ispunct' : (c_bool, (icu.UChar32, )),
    'u_isgraph' : (c_bool, (icu.UChar32, )),
    'u_isblank' : (c_bool, (icu.UChar32, )),
    'u_isdefined' : (c_bool, (icu.UChar32, )),
    'u_isspace' : (c_bool, (icu.UChar32, )),
    'u_isJavaSpaceChar' : (c_bool, (icu.UChar32, )),
    'u_isWhitespace' : (c_bool, (icu.UChar32, )),
    'u_iscntrl' : (c_bool, (icu.UChar32, )),
    'u_isISOControl' : (c_bool, (icu.UChar32, )),
    'u_isprint' : (c_bool, (icu.UChar32, )),
    'u_isbase' : (c_bool, (icu.UChar32, )),
    'u_charDirection' : (icu.UCharDirection, (icu.UChar32, )),
    'u_isMirrored' : (c_bool, (icu.UChar32, )),
    'u_charMirror' : (icu.UChar32, (icu.UChar32, )),
    'u_charType' : (c_int8, (icu.UChar32, )),
    'u_enumCharType' : (None, (icu.UCharEnumTypeRange, c_void_p)),
    'u_getCombingClass' : (c_uint8, (icu.UChar32, )),
    'u_charDigitValue' : (c_int32, (icu.UChar32, )),
    'ublock_getCode' : (icu.UBlockCode, (icu.UChar32, )),
    'u_charName' : (c_int32, (icu.UChar32, icu.UCharNameChoice, c_char_p, c_int32, icu.UErrorCodeP)),
    'u_getISOComment' : (c_int32, (icu.UChar32, c_char_p, c_int32, icu.UErrorCodeP)),
    'u_charFromName' : (icu.UChar32, (icu.UCharNameChoice, c_char_p, icu.UErrorCodeP)),
    'u_enumCharNames' : (None, (icu.UChar32, icu.UChar32, icu.UEnumCharNamesFn, c_void_p, icu.UCharNameChoice, icu.UErrorCodeP)),
    'u_getPropertyName' : (c_char_p, (icu.UProperty, icu.UPropertyNameChoice)),
    'u_getPropertyEnum' : (icu.UProperty, (c_char_p, )),
    'u_getPropertyValueName' : (c_char_p, (icu.UProperty, c_int32, icu.UPropertyNameChoice)),
    'u_getPropertValueEnum' : (c_int32, (icu.UProperty, c_char_p)),
    'u_isIDStart' : (c_bool, (icu.UChar32, )),
    'u_isIDPart' : (c_bool, (icu.UChar32, )),
    'u_isIDIgnorable' : (c_bool, (icu.UChar32, )),
    'u_isIDJavaIDStart' : (c_bool, (icu.UChar32, )),
    'u_isIDJavaIDPart' : (c_bool, (icu.UChar32, )),
    'u_tolower' : (icu.UChar32, (icu.UChar32, )),
    'u_toupper' : (icu.UChar32, (icu.UChar32, )),
    'u_totitle' : (icu.UChar32, (icu.UChar32, )),
    'u_foldCase' : (icu.UChar32, (icu.UChar32, c_uint32)),
    'u_digit' : (c_int32, (icu.UChar32, c_int8)),
    'u_forDigit' : (c_int32, (icu.UChar32, c_int8)),
    'u_charAge' : (None, (icu.UChar32, icu.UVersionInfo)),
    'u_getUnicodeVErsion' : (None, (icu.UVersionInfo, )),
    'u_getFC_NFKC_Closure' : (c_int32, (icu.UChar32, icu.UCharP, c_int32, icu.UErrorCodeP)),

    # utext.h
    'utext_close' : (icu.UTextP, (icu.UTextP, )),
    'utext_openUTF8' : (icu.UTextP, (icu.UTextP, c_char_p, c_int64, icu.UErrorCodeP)),
    'utext_openUChars' : (icu.UTextP, (icu.UTextP, icu.UCharP, c_int64, icu.UErrorCodeP)),
    # skip using UnicodeString, Replaceable, CharIterator
    'utext_clone' : (icu.UTextP, (icu.UTextP, icu.UTextP, c_bool, c_bool, icu.UErrorCodeP)),
    'utext_equals' : (c_bool, (icu.UTextP, icu.UTextP)),
    'utext_nativeLength' : (c_int64, (icu.UTextP, )),
    'utext_isLengthExpensive' : (c_bool, (icu.UTextP, )),
    'utext_char32At' : (icu.UChar32, (icu.UTextP, c_int64)),
    'utext_current32' : (icu.UChar32, (icu.UTextP, )),
    'utext_next32' : (icu.UChar32, (icu.UTextP, )),
    'utext_previous32' : (icu.UChar32, (icu.UTextP, )),
    'utext_next32From' : (icu.UChar32, (icu.UTextP, c_int64)),
    'utext_previous32From' : (icu.UChar32, (icu.UTextP, c_int64)),
    'utext_getNativeIndex' : (c_int64, (icu.UTextP, )),
    'utext_setNativeIndex' : (None, (icu.UTextP, c_int64)),
    'utext_moveIndex' : (c_bool, (icu.UTextP, c_int32)),
    'utext_getPreviousNativeIndex' : (c_int64, (icu.UTextP, )),
    'utext_extract' : (c_int32, (icu.UTextP, c_int64, c_int64, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'utext_compare' : (c_int32, (icu.UTextP, c_int32, icu.UTextP, c_int32)),
    'utext_comparNativeLimit' : (c_int32, (icu.UTextP, c_int64, icu.UTextP, c_int64)),
    'utext_caseCompare' : (c_int32, (icu.UTextP, c_int32, icu.UTextP, c_int32, c_int32, icu.UErrorCodeP)),
    'utext_caseComparNativeLimit' : (c_int32, (icu.UTextP, c_int64, icu.UTextP, c_int64, c_int32, icu.UErrorCodeP)),
    'utext_isWritable' : (c_bool, (icu.UTextP, )),
    'utext_hasMetaData' : (c_bool, (icu.UTextP, )),
    'utext_replace' : (c_int32, (icu.UTextP, c_int64, c_int64, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'utext_copy' : (None, (icu.UTextP, c_int64, c_int64, c_int64, c_bool, icu.UErrorCodeP)),
    'utext_freeze' : (None, (icu.UTextP, )),
    'UTextClone' : (icu.UTextP, (icu.UTextP, icu.UTextP, c_bool, c_bool, icu.UErrorCodeP)),
    'UTextNativeLength' : (c_int64, (icu.UTextP, )),
    # skip the UTextFuncs and internal structure of UText

    # uloc.h
    'uloc_getDefault' : (c_char_p, (None,  )),
    'uloc_setDefault' : (None, (c_char_p, icu.UErrorCodeP)),
    'uloc_getLanguage' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getScript' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getCountry' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getVariant' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getName' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_canonicalize' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getISO3Language' : (c_char_p, (c_char_p, )),
    'uloc_getISO3Country' : (c_char_p, (c_char_p, )),
    'uloc_getLCID' : (c_int32, (c_char_p, )),
    'uloc_getDisplayLanguage' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayScript' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayCountry' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayVariant' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayKeyword' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayKeywordValue' : (c_int32, (c_char_p, c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getDisplayName' : (c_int32, (c_char_p, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uloc_getAvailable' : (c_char_p, (c_int32, )),
    'uloc_countAvailable' : (c_int32, (None,  )),
    'uloc_getISOLanguages' : (POINTER(c_char_p), (None,  )),
    'uloc_getISOCountries' : (POINTER(c_char_p), (None,  )),
    'uloc_getParent' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getBaseName' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_openKeywords' : (icu.UEnumerationP, (c_char_p, icu.UErrorCodeP)),
    'uloc_getKeywordValues' : (c_int32, (c_char_p, c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_setKeywordValue' : (c_int32, (c_char_p, c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_getCharacterOrientation' : (icu.ULayoutType, (c_char_p, icu.UErrorCodeP)),
    'uloc_getLineOrientation' : (icu.ULayoutType, (c_char_p, icu.UErrorCodeP)),
    'uloc_acceptLanguageFromHTTP' : (c_int32, (c_char_p, c_int32, POINTER(icu.UAcceptResult), c_char_p, icu.UEnumerationP, icu.UErrorCodeP)),
    'uloc_acceptLanguage' : (c_int32, (c_char_p, c_int32, POINTER(icu.UAcceptResult), POINTER(c_char_p), c_int32, icu.UEnumerationP, icu.UErrorCodeP)),
    'uloc_getLocaleFromLCID' : (c_int32, (c_uint32, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_addLikelySubtags' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_minimizeSubtags' : (c_int32, (c_char_p, c_char_p, c_int32, icu.UErrorCodeP)),
    'uloc_forLanguageTag' : (c_int32, (c_char_p, c_char_p, c_int32, POINTER(c_int32), icu.UErrorCodeP)),
    'uloc_toLanguageTag' : (c_int32, (c_char_p, c_char_p, c_int32, c_bool, icu.UErrorCodeP)),

    # ubidi.h
    'ubidi_open' : (icu.UBiDiP, (None, )),
    'ubidi_openSized' : (icu.UBiDiP, (c_int32, c_int32, icu.UErrorCodeP)),
    'ubidi_close' : (None, (icu.UBiDiP, )),
    'ubidi_setInverse' : (None, (icu.UBiDiP, c_bool)),
    'ubidi_isInverse' : (c_bool, (icu.UBiDiP, )),
    'ubidi_orderParagraphsLTR' : (None, (icu.UBiDiP, c_bool)),
    'ubidi_isOrderParagraphsLTR' : (c_bool, (icu.UBiDiP, )),
    'ubidi_setReorderingMode' : (None, (icu.UBiDiP, icu.UBiDiReorderingMode)),
    'ubidi_getReorderingMode' : (icu.UBiDiReorderingMode, (icu.UBiDiP, )),
    'ubidi_setReorderingOptions' : (None, (icu.UBiDiP, c_uint32)),
    'ubidi_getReorderingOptions' : (c_uint32, (icu.UBiDiP, )),
    'ubidi_setPara' : (None, (icu.UBiDiP, icu.UCharP, c_int32, icu.UBiDiLevel, POINTER(icu.UBiDiLevel), icu.UErrorCodeP)),
    'ubidi_setLine' : (None, (icu.UBiDiP, c_int32, c_int32, icu.UBiDiP, icu.UErrorCodeP)),
    'ubidi_getDirection' : (icu.UBiDiDirection, (icu.UBiDiP, )),
    'ubidi_getText' : (icu.UCharP, (icu.UBiDiP, )),
    'ubidi_getLength' : (c_int32, (icu.UBiDiP, )),
    'ubidi_getParaLevel' : (icu.UBiDiLevel, (icu.UBiDiP, )),
    'ubidi_countParagraphs' : (c_int32, (icu.UBiDiP, )),
    'ubidi_getParagraph' : (c_int32, (icu.UBiDiP, c_int32, POINTER(c_int32), POINTER(c_int32), POINTER(icu.UBiDiLevel), icu.UErrorCodeP)),
    'ubidi_getParagraphByIndex' : (c_int32, (icu.UBiDiP, c_int32, POINTER(c_int32), POINTER(c_int32), POINTER(icu.UBiDiLevel), icu.UErrorCodeP)),
    'ubidi_getLevelAt' : (icu.UBiDiLevel, (icu.UBiDiP, c_int32)),
    'ubidi_getLevels' : (POINTER(icu.UBiDiLevel), (icu.UBiDiP, icu.UErrorCodeP)),
    'ubidi_getLogicalRun' : (None, (icu.UBiDiP, c_int32, POINTER(c_int32), POINTER(icu.UBiDiLevel))),
    'ubidi_countRuns' : (c_int32, (icu.UBiDiP, icu.UErrorCodeP)),
    'ubidi_getVisualRun' : (icu.UBiDiDirection, (icu.UBiDiP, c_int32, POINTER(c_int32), POINTER(c_int32))),
    'ubidi_getVisualIndex' : (c_int32, (icu.UBiDiP, c_int32, icu.UErrorCodeP)),
    'ubidi_getLogicalIndex' : (c_int32, (icu.UBiDiP, c_int32, icu.UErrorCodeP)),
    'ubidi_getLogicalMap' : (None, (icu.UBiDiP, POINTER(c_int32), icu.UErrorCodeP)),
    'ubidi_getVisualMap' : (None, (icu.UBiDiP, POINTER(c_int32), icu.UErrorCodeP)),
    'ubidi_reorderLogical' : (None, (POINTER(icu.UBiDiLevel), c_int32, POINTER(c_int32))),
    'ubidi_reorderVisual' : (None, (POINTER(icu.UBiDiLevel), c_int32, POINTER(c_int32))),
    'ubidi_invertMap' : (None, (POINTER(c_int32), POINTER(c_int32), c_int32)),
    'ubidi_getProcessedLength' : (c_int32, (icu.UBiDiP, )),
    'ubidi_getResultLength' : (c_int32, (icu.UBiDiP, )),
    'ubidi_getCustomized' : (icu.UCharDirection, (icu.UBiDiP, icu.UChar32)),
    'ubidi_setClassCallback' : (None, (icu.UBiDiP, icu.UBiDiClassCallback, c_void_p, POINTER(icu.UBiDiClassCallback), POINTER(c_void_p), icu.UErrorCodeP)),
    'ubidi_getClassCallback' : (None, (icu.UBiDiP, POINTER(icu.UBiDiClassCallback), POINTER(c_void_p))),
    'ubidi_writeReordered' : (c_int32, (icu.UBiDiP, icu.UCharP, c_int32, c_uint16, icu.UErrorCodeP)),
    'ubidi_writeReverse' : (c_int32, (icu.UCharP, c_int32, icu.UCharP, c_int32, c_uint16, icu.UErrorCodeP)),

    # ubrk.h
    'ubrk_open' : (icu.UBreakIteratorP, (icu.UBreakIteratorType, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ubrk_openRules' : (icu.UBreakIteratorP, (icu.UCharP, c_int32, icu.UCharP, c_int32, icu.UParseErrorP, icu.UErrorCodeP)),
    'ubrk_safeClone' : (icu.UBreakIteratorP, (icu.UBreakIteratorP, c_void_p, POINTER(c_int32), icu.UErrorCodeP)),
    'ubrk_close' : (None, (icu.UBreakIteratorP, )),
    'ubrk_setText' : (None, (icu.UBreakIteratorP, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ubrk_setUText' : (None, (icu.UBreakIteratorP, icu.UTextP, icu.UErrorCodeP)),
    'ubrk_current' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_next' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_previous' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_first' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_last' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_preceding' : (c_int32, (icu.UBreakIteratorP, c_int32)),
    'ubrk_following' : (c_int32, (icu.UBreakIteratorP, c_int32)),
    'ubrk_getAvailable' : (c_char_p, (c_int32, )),
    'ubrk_countAvailable' : (c_int32, (None, )),
    'ubrk_isBoundary' : (c_bool, (icu.UBreakIteratorP, c_int32)),
    'ubrk_getRuleStatus' : (c_int32, (icu.UBreakIteratorP, )),
    'ubrk_getRuleStatusVec' : (c_int32, (icu.UBreakIteratorP, POINTER(c_int32), c_int32, icu.UErrorCodeP)),
    'ubrk_getLocaleByType' : (c_char_p, (icu.UBreakIteratorP, icu.ULocDataLocaleType, icu.UErrorCodeP)),

    # ucasemap.h
    'ucasemap_close' : (None, (icu.UCaseMapP, )),
    'ucasemap_getLocale' : (c_char_p, (icu.UCaseMapP, )),
    'ucasemap_getOptions' : (c_int32, (icu.UCaseMapP, )),
    'ucasemap_setLocale' : (None, (icu.UCaseMapP, c_char_p, icu.UErrorCodeP)),
    'ucasemap_setOptions' : (None, (icu.UCaseMapP, c_int32, icu.UErrorCodeP)),
    'ucasemap_getBreakIterator' : (icu.UBreakIteratorP, (icu.UCaseMapP, )),
    'ucasemap_setBreakIterator' : (None, (icu.UCaseMapP, icu.UBreakIteratorP, icu.UErrorCodeP)),
    'ucasemap_toTitle' : (c_int32, (icu.UCaseMapP, icu.UCharP, c_int32, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ucasemap_utf8ToLower' : (c_int32, (icu.UCaseMapP, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucasemap_utf8ToUpper' : (c_int32, (icu.UCaseMapP, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucasemap_utf8ToTitle' : (c_int32, (icu.UCaseMapP, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucasemap_utf8FoldCase' : (c_int32, (icu.UCaseMapP, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),

    # ures.h
    'ures_open' : (icu.UResourceBundleP, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ures_openDirect' : (icu.UResourceBundleP, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ures_openU' : (icu.UResourceBundleP, (icu.UCharP, c_char_p, icu.UErrorCodeP)),
    'ures_countArrayItems' : (c_int32, (icu.UResourceBundleP, c_char_p, icu.UErrorCodeP)),
    'ures_close' : (None, (icu.UResourceBundleP, )),
    'ures_getVersionNumber' : (c_char_p, (icu.UResourceBundleP, )),
    'ures_getVersion' : (None, (icu.UResourceBundleP, icu.UVersionInfo)),
    'ures_getLocale' : (c_char_p, (icu.UResourceBundleP, icu.UErrorCodeP)), 
    'ures_getLocaleByType' : (c_char_p, (icu.UResourceBundleP, icu.ULocDataLocaleType, icu.UErrorCodeP)), 
    'ures_openFillIn' : (None, (icu.UResourceBundleP, c_char_p, c_char_p, icu.UErrorCodeP)),
    'ures_getString' : (icu.UCharP, (icu.UResourceBundleP, POINTER(c_int32), icu.UErrorCodeP)),
    'ures_getUTF8String' : (c_char_p, (icu.UResourceBundleP, c_char_p, POINTER(c_int32), c_bool, icu.UErrorCodeP)),
    'ures_getBinary' : (POINTER(c_uint8), (icu.UResourceBundleP, POINTER(c_int32), icu.UErrorCodeP)),
    'ures_getIntVector' : (POINTER(c_int32), (icu.UResourceBundleP, POINTER(c_int32), icu.UErrorCodeP)),
    'ures_getUInt' : (c_uint32, (icu.UResourceBundleP, icu.UErrorCodeP)),
    'ures_getInt' : (c_int32, (icu.UResourceBundleP, icu.UErrorCodeP)),
    'ures_getType' : (icu.UResType, (icu.UResourceBundleP, )),
    'ures_getKey' : (c_char_p, (icu.UResourceBundleP, )),
    'ures_resetIterator' : (None, (icu.UResourceBundleP, )),
    'ures_hasNext' : (c_bool, (icu.UResourceBundleP, )),
    'ures_getNextResource' : (icu.UResourceBundleP, (icu.UResourceBundleP, icu.UResourceBundleP, icu.UErrorCodeP)),
    'ures_getNextString' : (icu.UCharP, (icu.UResourceBundleP, POINTER(c_int32), POINTER(c_char_p), icu.UErrorCodeP)),
    'ures_getBuIndex' : (icu.UResourceBundleP, (icu.UResourceBundleP, c_int32, icu.UResourceBundleP, icu.UErrorCodeP)),
    'ures_getStringByIndex' : (icu.UCharP, (icu.UResourceBundleP, c_int32, POINTER(c_int32), icu.UErrorCodeP)),
    'ures_getUTF8StringByIndex' : (c_char_p, (icu.UResourceBundleP, c_int32, c_char_p, POINTER(c_int32), c_bool, icu.UErrorCodeP)),
    'ures_getByKey' : (icu.UResourceBundleP, (icu.UResourceBundleP, c_char_p, icu.UResourceBundleP, icu.UErrorCodeP)),
    'ures_getStringByKey' : (icu.UCharP, (icu.UResourceBundleP, c_char_p, POINTER(c_int32), icu.UErrorCodeP)),
    'ures_getUTF8StringByKey' : (c_char_p, (icu.UResourceBundleP, c_char_p, c_char_p, POINTER(c_int32), c_bool, icu.UErrorCodeP)),
    'ures_openAvailableLocales' : (icu.UEnumerationP, (c_char_p, icu.UErrorCodeP)),

    # ucat.h
    'u_catopen' : (icu.UResourceBundleP, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'u_catclose' : (None, (icu.UResourceBundleP, )),
    'u_catgets' : (icu.UCharP, (icu.UResourceBundleP, c_int32, c_int32, icu.UCharP, POINTER(c_int32), icu.UErrorCodeP)),

    # uclean.h
    'u_init' : (None, (icu.UErrorCodeP, )),
    'u_cleanup' : (None, (None, )),
    'u_setMutexFunctions' : (None, (c_void_p, icu.UMtxFn, icu.UMtxFn, icu.UMtxFn, icu.UErrorCodeP)),
    'u_setAtomicIncDecFunctions' : (None, (c_void_p, icu.UMtxAtomicFn, icu.UMtxAtomicFn, icu.UErrorCodeP)),
    'u_setMemoryFunctions' : (None, (c_void_p, icu.UMemAllocFn, icu.UMemReallocFn, icu.UMemFreeFn, icu.UErrorCodeP)),

    # ucnv.h and friends
    'ucnv_compareNames' : (c_int, (c_char_p, c_char_p)),
    'ucnv_open' : (icu.UConverterP, (c_char_p, icu.UErrorCodeP)),
    'ucnv_openU' : (icu.UConverterP, (icu.UCharP, icu.UErrorCodeP)),
    'ucnv_openCCSID' : (icu.UConverterP, (c_int32, icu.UConverterPlatform, icu.UErrorCodeP)),
    'ucnv_openPackage' : (icu.UConverterP, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ucnv_safeClone' : (icu.UConverterP, (icu.UConverterP, c_void_p, POINTER(c_int32), icu.UErrorCodeP)),
    'ucnv_close' : (None, (icu.UConverterP, )),
    'ucnv_getSubstChars' : (None, (icu.UConverterP, c_char_p, POINTER(c_int8), icu.UErrorCodeP)),
    'ucnv_setSubstChars' : (None, (icu.UConverterP, c_char_p, POINTER(c_int8), icu.UErrorCodeP)),
    'ucnv_setSubstString' : (None, (icu.UConverterP, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ucnv_getInvalideChars' : (None, (icu.UConverterP, c_char_p, POINTER(c_int8), icu.UErrorCodeP)),
    'ucnv_getInvalideUChars' : (None, (icu.UConverterP, icu.UCharP, POINTER(c_int8), icu.UErrorCodeP)),
    'ucnv_reset' : (None, (icu.UConverterP, )),
    'ucnv_resetToUnicode' : (None, (icu.UConverterP, )),
    'ucnv_resetFromUnicode' : (None, (icu.UConverterP, )),
    'ucnv_getMaxCharSize' : (c_int8, (icu.UConverterP, )),
    'ucnv_getMinCharSize' : (c_int8, (icu.UConverterP, )),
    'ucnv_getDisplayName' : (c_int32, (icu.UConverterP, c_char_p, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ucnv_getName' : (c_char_p, (icu.UConverterP, icu.UErrorCodeP)),
    'ucnv_getCCSID' : (c_int32, (icu.UConverterP, icu.UErrorCodeP)),
    'ucnv_getPlatform' : (icu.UConverterPlatform, (icu.UConverterP, icu.UErrorCodeP)),
    'ucnv_getType' : (icu.UConverterType, (icu.UConverterP, icu.UErrorCodeP)),
    'ucnv_getStarters' : (None, (icu.UConverterP, c_bool, icu.UErrorCodeP)),
    'ucnv_getUnicodeSet' : (None, (icu.UConverterP, icu.USetP, icu.UConverterUnicodeSet, icu.UErrorCodeP)),
    'ucnv_getToUCallBack' : (None, (icu.UConverterP, icu.UConverterToUCallback, POINTER(c_void_p))),
    'ucnv_getFromUCallBack' : (None, (icu.UConverterP, icu.UConverterFromUCallback, POINTER(c_void_p))),
    'ucnv_setToUCallBack' : (None, (icu.UConverterP, icu.UConverterToUCallback, c_void_p, icu.UConverterToUCallback, POINTER(c_void_p), icu.UErrorCodeP)),
    'ucnv_setFromUCallBack' : (None, (icu.UConverterP, icu.UConverterFromUCallback, c_void_p, icu.UConverterFromUCallback, POINTER(c_void_p), icu.UErrorCodeP)),
    'ucnv_fromUnicode' : (None, (icu.UConverterP, POINTER(c_char_p), c_char_p, POINTER(icu.UCharP), icu.UCharP, POINTER(c_int32), c_bool, icu.UErrorCodeP)),
    'ucnv_toUnicode' : (None, (icu.UConverterP, POINTER(icu.UCharP), icu.UCharP, POINTER(c_char_p), c_char_p, POINTER(c_int32), c_bool, icu.UErrorCodeP)),
    'ucnv_fromUChars' : (c_int32, (icu.UConverterP, c_char_p, c_int32, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'ucnv_toUChars' : (c_int32, (icu.UConverterP, icu.UCharP, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucnv_getNextUChar' : (icu.UChar32, (icu.UConverterP, POINTER(c_char_p), c_char_p, icu.UErrorCodeP)),
    'ucnv_convertEx' : (None, (icu.UConverterP, icu.UConverterP, POINTER(c_char_p), c_char_p, POINTER(c_char_p), c_char_p, icu.UCharP, POINTER(icu.UCharP), POINTER(icu.UCharP), icu.UCharP, c_bool, c_bool, icu.UErrorCodeP)),
    'ucnv_conver' : (c_int32, (c_char_p, c_char_p, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucnv_toAlgorithmic' : (c_int32, (icu.UConverterType, icu.UConverterP, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucnv_fromAlgorithmic' : (c_int32, (icu.UConverterP, icu.UConverterType, c_char_p, c_int32, c_char_p, c_int32, icu.UErrorCodeP)),
    'ucnv_flushCache' : (c_int32, (None, )),
    'ucnv_countAvailable' : (c_int32, (None, )),
    'ucnv_getAvailableName' : (c_char_p, (c_int32, )),
    'ucnv_openAllNames' : (icu.UEnumerationP, (icu.UErrorCodeP, )),
    'ucnv_countAliases' : (c_uint16, (c_char_p, icu.UErrorCodeP)),
    'ucnv_getAlias' : (c_char_p, (c_char_p, c_uint16, icu.UErrorCodeP)),
    'ucnv_getAliases' : (None, (c_char_p, POINTER(c_char_p), icu.UErrorCodeP)),
    'ucnv_openStandardNames' : (icu.UEnumerationP, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ucnv_countStandards' : (c_uint16, (None, )),
    'ucnv_getStandard' : (c_char_p, (c_uint16, icu.UErrorCodeP)),
    'ucnv_getStandardName' : (c_char_p, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ucnv_getCanonicalName' : (c_char_p, (c_char_p, c_char_p, icu.UErrorCodeP)),
    'ucnv_getDefaultName' : (c_char_p, (None, )),
    'ucnv_setDefaultName' : (None, (c_char_p)),
    'ucnv_fixFileSeparator' : (None, (icu.UConverterP, icu.UCharP, c_int32)),
    'ucnv_isAmbiguous' : (c_bool, (icu.UConverterP, )),
    'ucnv_setFallback' : (None, (icu.UConverterP, c_bool)),
    'ucnv_usesFallback' : (c_bool, (icu.UConverterP, )),
    'udnv_detectUnicodeSignature' : (c_char_p, (c_char_p, c_int32, POINTER(c_int32), icu.UErrorCodeP)),
    'ucnv_fromUCountPending' : (c_int32, (icu.UConverterP, icu.UErrorCodeP)),
    'ucnv_toUCountPending' : (c_int32, (icu.UConverterP, icu.UErrorCodeP)),

    # uset.h
    'uset_openEmpty' : (icu.USetP, (None, )),
    'uset_open' : (icu.USetP, (icu.UChar32, icu.UChar32)),
    'uset_openPattern' : (icu.USetP, (icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uset_openPatternOptions' : (icu.USetP, (icu.UCharP, c_int32, c_uint32, icu.UErrorCodeP)),
    'uset_close' : (None, (icu.USetP, )),
    'uset_clone' : (icu.USetP, (icu.USetP, )),
    'uset_isFrozen' : (c_bool, (icu.USetP, )),
    'uset_freeze' : (None, (icu.USetP, )),
    'uset_cloneAsThawed' : (icu.USetP, (icu.USetP, )),
    'uset_set' : (None, (icu.USetP, icu.UChar32, icu.UChar32)),
    'uset_applyPattern' : (c_int32, (icu.USetP, icu.UCharP, c_int32, c_uint32, icu.UErrorCodeP)),
    'uset_applyIntPropertyValue' : (None, (icu.USetP, icu.UProperty, c_int32, icu.UErrorCodeP)),
    'uset_applyPropertyAlias' : (None, (icu.USetP, icu.UCharP, c_int32, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uset_resemblesPattern' : (c_bool, (icu.UCharP, c_int32, c_int32)),
    'uset_toPattern' : (c_int32, (icu.USetP, icu.UCharP, c_int32, c_bool, icu.UErrorCodeP)),
    'uset_add' : (None, (icu.USetP, icu.UChar32)),
    'uset_addAll' : (None, (icu.USetP, icu.USetP)),
    'uset_addRange' : (None, (icu.USetP, icu.UChar32, icu.UChar32)),
    'uset_addString' : (None, (icu.USetP, icu.UCharP, c_int32)),
    'uset_addAllCodePoints' : (None, (icu.USetP, icu.UCharP, c_int32)),
    'uset_remove' : (None, (icu.USetP, icu.UChar32)),
    'uset_removeRange' : (None, (icu.USetP, icu.UChar32, icu.UChar32)),
    'uset_removeString' : (None, (icu.USetP, icu.UCharP, c_int32)),
    'uset_removeAll' : (None, (icu.USetP, icu.USetP)),
    'uset_retain' : (None, (icu.USetP, icu.UChar32, icu.UChar32)),
    'uset_retainAll' : (None, (icu.USetP, icu.USetP)),
    'uset_compact' : (None, (icu.USetP, )),
    'uset_complement' : (None, (icu.USetP, )),
    'uset_complementAll' : (None, (icu.USetP, icu.USetP)),
    'uset_clear' : (None, (icu.USetP, )),
    'uset_closeOver' : (None, (icu.USetP, c_int32)),
    'uset_removeAllStrings' : (None, (icu.USetP, )),
    'uset_isEmpty' : (c_bool, (icu.USetP, )),
    'uset_contains' : (c_bool, (icu.USetP, icu.UChar32)),
    'uset_containsRange' : (c_bool, (icu.USetP, icu.UChar32, icu.UChar32)),
    'uset_containsString' : (c_bool, (icu.USetP, icu.UCharP, c_int32)),
    'uset_indexOf' : (c_int32, (icu.USetP, icu.UChar32)),
    'uset_charAt' : (icu.UChar32, (icu.USetP, c_int32)),
    'uset_size' : (c_int32, (icu.USetP, )),
    'uset_getItemCount' : (c_int32, (icu.USetP, )),
    'uset_getItem' : (c_int32, (icu.USetP, c_int32, icu.UChar32, icu.UChar32, icu.UCharP, c_int32, icu.UErrorCodeP)),
    'uset_containsAll' : (c_bool, (icu.USetP, icu.USetP)),
    'uset_containsAllCodePoints' : (c_bool, (icu.USetP, icu.UCharP, c_int32)),
    'uset_containsNone' : (c_bool, (icu.USetP, icu.USetP)),
    'uset_containsSome' : (c_bool, (icu.USetP, icu.USetP)),
    'uset_span' : (c_int32, (icu.USetP, icu.UCharP, c_int32, icu.USetSpanCondition)),
    'uset_spanBack' : (c_int32, (icu.USetP, icu.UCharP, c_int32, icu.USetSpanCondition)),
    'uset_spanUTF8' : (c_int32, (icu.USetP, c_char_p, c_int32, icu.USetSpanCondition)),
    'uset_spanBackUTF8' : (c_int32, (icu.USetP, c_char_p, c_int32, icu.USetSpanCondition)),
    'uset_equals' : (c_bool, (icu.USetP, icu.USetP)),
    'uset_serialize' : (c_int32, (icu.USetP, POINTER(c_uint16), c_int32, icu.UErrorCodeP)),
    'uset_getSerializedSet' : (c_bool, (icu.USerializedSetP, POINTER(c_uint16), c_int32)),
    'uset_setSerializedToOne' : (None, (icu.USerializedSetP, icu.UChar32)),
    'uset_serializedContains' : (c_bool, (icu.USerializedSetP, icu.UChar32)),
    'uset_getSerializedRangeCount' : (c_int32, (icu.USerializedSetP, )),
    'uset_getSerializedRange' : (c_bool, (icu.USerializedSetP, c_int32, icu.UChar32P, icu.UChar32P)),


    
}

if __name__ == '__main__' :
    i = icu()
    v = i.UVersionInfo(0, 0, 0, 0)
    i.u_getVersion(v)
    st = c_char * 20
    s = st()
    i.u_versionToString(v, s)
    print "Found ICU version: " + s.value
else:
    sys.modules[__name__] = icu()

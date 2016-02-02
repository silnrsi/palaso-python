from ctypes import *
from ctypes.util import *
import sys, os


class icu(object) :

    UChar = c_uint16
    UCharP = POINTER(c_uint16)
    UChar32 = c_uint32
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

    # ubidi.h
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

    # ubrk.h
    UParseErrorP = c_void_p
    UBreakIteratorP = c_void_p
    UBreakIteratorType = c_int
    UWordBreak = c_int
    ULineBreakTag = c_int
    USentenceBreakTag = c_int

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
            f.argtypes = i[1]
            setattr(self, name, f)
            return f
        else :
            raise AttributeError(name)

icu.__icufns__ = {
    'u_errorName' : (c_char_p, (icu.UErrorCode, )),
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

    # ubidi.h
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

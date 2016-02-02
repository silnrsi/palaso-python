from ctypes import *
from ctypes.util import *
import sys, os


class icu(object) :

    UChar = c_uint16
    UCharP = POINTER(c_uint16)
    UChar32 = c_uint32
    UDate = c_double
    UErrorCode = c_int
    def U_SUCCESS(self, x) : return x <= 0
    UVersionInfo = c_uint8 * 4

    c_int_p = POINTER(c_int)
    c_uint_p = POINTER(c_uint)
    c_uint16_p = POINTER(c_uint16)
    c_int32_p = POINTER(c_int32)

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
    'u_versionFromString' : (None, (icu.UVersionInfo, c_char_p)),
    'u_versionFromUString' : (None, (icu.UVersionInfo, icu.UCharP)),
    'u_versionToString' : (None, (icu.UVersionInfo, c_char_p)),
    'u_getVersion' : (None, (icu.UVersionInfo, ))
}

if __name__ == '__main__' :
    i = icu()
    v = i.UVersionInfo(0, 0, 0, 0)
    i.u_getVersion(v)
    st = c_char * 20
    s = st()
    i.u_versionToString(v, s)
    print s.value
else:
    sys.modules[__name__] = icu()

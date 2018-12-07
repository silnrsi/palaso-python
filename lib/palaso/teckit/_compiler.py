#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides python definitions of the Public API to the TECkit 
# compiler library.
#
# Author: Tim Eves
#
# History:
#   10-Jun-2009     tse     Converted to python representationsm and 
#                            added ctypes function defintitions for the 
#                            public API.
# History of TECKit_Compiler.h this is based on:
#   18-Jan-2008     jk      added EXPORTED to declarations, for mingw32 
#                            cross-build
#   16-Sep-2006     jk      added APIs to convert USVs to names and
#                            vice versa
#   21-May-2005     jk      changes based on Ulrik Petersen's patch for
#                            MS VC++ 6
#   18-Mar-2005     jk      added option to generate XML representation
#    5-Jul-2002     jk      corrected placement of WINAPI/CALLBACK to 
#   14-May-2002     jk      added WINAPI to function declarations
#                            keep MS compiler happy

from ctypes import *
from ctypes.util import find_library
from palaso.teckit._common import *
import platform


# We need to use windll instead of cdll on Windows.
if platform.system() == "Windows" :
    libteckit_compile = windll.LoadLibrary(find_library('TECkit_Compiler_' + platform.machine()))
    LOCALFUNCTYPE = WINFUNCTYPE
else :
    libteckit_compile = cdll.LoadLibrary(find_library('TECkit_Compiler'))
    LOCALFUNCTYPE = CFUNCTYPE


Opts_FormMask   = 0x0000000F    # see TECkit_Common.h for encoding form constants
Opt = ENUM(
    Compress=0x10,   # generate compressed mapping table
    XML     =0x20)   # instead of a compiled binary table, generate an XML 
                     #   representation of the mapping

teckit_error_fn = LOCALFUNCTYPE(None, c_void_p, c_char_p, c_char_p, c_uint32)

def key_error(err_val,msg):
    def check(res,func,args):
        if res != err_val: return res
        else:              raise KeyError(msg % args[0])
    return check

prototype = LOCALFUNCTYPE(status, c_char_p, c_size_t, c_bool, teckit_error_fn, c_void_p, POINTER(mapping), POINTER(c_size_t))
paramflags = (1,'txt'),(1,'len'),(1,'doCompression'),(1,'errFunc'),(1,'userData'),(2,'outTable'),(2,'outLen')
compile = prototype(('TECkit_Compile',libteckit_compile),paramflags)
compile.err_check = status_code

prototype = LOCALFUNCTYPE(status, c_char_p, c_size_t, teckit_error_fn, c_void_p, POINTER(mapping), POINTER(c_size_t), c_uint32)
paramflags = (1,'txt'),(1,'len'),(1,'errFunc'),(1,'userData'),(2,'outTable'),(2,'outLen'),(1,'opts')
compileOpt = prototype(('TECkit_CompileOpt',libteckit_compile),paramflags)
compileOpt.err_check = status_code

prototype = LOCALFUNCTYPE(None, mapping)
paramflags = (1,'table'),
disposeCompiled = prototype(('TECkit_DisposeCompiled',libteckit_compile),paramflags)

prototype = LOCALFUNCTYPE(c_uint32)
getCompilerVersion = prototype(('TECkit_GetCompilerVersion', libteckit_compile))

#
# new APIs for looking up Unicode names (as NUL-terminated C strings)
#
# returns the Unicode name of usv, if available, else NULL
prototype = LOCALFUNCTYPE(c_char_p, c_uint32)
paramflags = (1,'usv'),
getUnicodeName = prototype(('TECkit_GetUnicodeName',libteckit_compile),paramflags)
getUnicodeName.err_check = key_error(0, 'no name for U+%x')

# returns the TECkit form of the name of usv, or "U+xxxx" if no name
# NB: returns value is a pointer to a static string, which will be
#   overwritten by subsequent calls.
prototype = LOCALFUNCTYPE(c_char_p,c_uint32)
paramflags = (1,'usv'),
getTECkitName = prototype(('TECkit_GetTECkitName',libteckit_compile),paramflags)
getTECkitName.err_check = key_error(0, 'no name for U+%x')

prototype = LOCALFUNCTYPE(c_int,c_char_p)
paramflags = (1,'name'),
getUnicodeValue = prototype(('TECkit_GetUnicodeValue',libteckit_compile),paramflags)
getUnicodeValue.err_check = key_error(-1,'no USV for %s')


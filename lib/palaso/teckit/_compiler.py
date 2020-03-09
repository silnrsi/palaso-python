"""
TECkit Compiler library C API for python.

Provides python ctypes definitions and functions for the public API to
the TECkit compiler library.
"""
__author__ = "Tim Eves"
__date__ = "23 January 2020"
__credits__ = '''\
Jonathon Kew for TECkit_Compiler.h this is based on.
'''
__copyright__ = "Copyright © 2020 SIL International"
__license__ = "MIT"
__email__ = "tim_eves@sil.org"
# History:
# 20-Jan-2020 tse   Converted to python3 and replaced custom flag and enum
#                   meta classes with std lib versions. Added type hints.
# 10-Jun-2009 tse   Created ctypes  function defintitions for the public API.

from enum import IntFlag, unique
from ctypes import (
    POINTER,
    c_bool, c_int, c_size_t, c_uint32,
    c_void_p, c_char_p)
from typing import Callable, List, Tuple
from palaso.teckit._common import (
    LOCALFUNCTYPE, mapping, status,
    load_teckit_library, status_code)

# We need to use windll instead of cdll on Windows.
__library__ = load_teckit_library('Compiler')

Opts_FormMask = 0x0000000F    # see TECkit_Common.h for encoding form constants


@unique
class Opt(IntFlag):
    FormMask = 0x0000000F

    Compress = 0x10
    # Generate compressed mapping table.

    XML = 0x20
    # Instead of a compiled binary table, generate an XML representation of
    # the mapping.


teckit_error_fn: Callable = LOCALFUNCTYPE(None, c_void_p, c_char_p, c_char_p,
                                          c_uint32)


def key_error(err_val: int, msg: str) -> Callable:
    def check(res: status, f, args: List) -> status:
        if res != err_val:
            return res
        else:
            raise KeyError(msg % args[0])

    return check


paramflags: Tuple = ()

prototype = LOCALFUNCTYPE(status, c_char_p, c_size_t, c_bool, teckit_error_fn,
                          c_void_p, POINTER(mapping), POINTER(c_size_t))
paramflags = ((1, 'txt'), (1, 'len'), (1, 'doCompression'), (1, 'errFunc'),
              (1, 'userData'), (2, 'outTable'), (2, 'outLen'))
compile = prototype(('TECkit_Compile', __library__), paramflags)
compile.err_check = status_code


prototype = LOCALFUNCTYPE(status, c_char_p, c_size_t, teckit_error_fn,
                          c_void_p, POINTER(mapping), POINTER(c_size_t),
                          c_uint32)
paramflags = ((1, 'txt'), (1, 'len'), (1, 'errFunc'), (1, 'userData'),
              (2, 'outTable'), (2, 'outLen'), (1, 'opts'))
compileOpt = prototype(('TECkit_CompileOpt', __library__), paramflags)
compileOpt.err_check = status_code

prototype = LOCALFUNCTYPE(None, mapping)
paramflags = (1, 'table'),
disposeCompiled = prototype(('TECkit_DisposeCompiled', __library__),
                            paramflags)

prototype = LOCALFUNCTYPE(c_uint32)
getCompilerVersion = prototype(('TECkit_GetCompilerVersion', __library__))

#
# new APIs for looking up Unicode names (as NUL-terminated C strings)
#
# returns the Unicode name of usv, if available, else NULL
prototype = LOCALFUNCTYPE(c_char_p, c_uint32)
paramflags = (1, 'usv'),
getUnicodeName = prototype(('TECkit_GetUnicodeName', __library__), paramflags)
getUnicodeName.err_check = key_error(0, 'no name for U+%x')

# returns the TECkit form of the name of usv, or "U+xxxx" if no name
# NB: returns value is a pointer to a static string, which will be
#   overwritten by subsequent calls.
prototype = LOCALFUNCTYPE(c_char_p, c_uint32)
paramflags = (1, 'usv'),
getTECkitName = prototype(('TECkit_GetTECkitName', __library__), paramflags)
getTECkitName.err_check = key_error(0, 'no name for U+%x')

prototype = LOCALFUNCTYPE(c_int, c_char_p)
paramflags = (1, 'name'),
getUnicodeValue = prototype(('TECkit_GetUnicodeValue', __library__),
                            paramflags)
getUnicodeValue.err_check = key_error(-1, 'no USV for %s')

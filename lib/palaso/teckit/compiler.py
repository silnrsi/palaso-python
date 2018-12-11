#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides a python module to interface with SIL's TECKit library compiler API.
#
# Author: Tim Eves
#
# History:
#   2009-06-10  tse     Initial version using the ctypes FFI
#

import palaso.teckit._compiler as _tc
from palaso.teckit._compiler import getUnicodeName, getTECkitName, getUnicodeValue
from palaso.teckit.engine import Mapping


class CompilationError(_tc.CompilationError):
    def __init__(self, errors):
        self.errors = errors
    
    def __str__(self):
        return 'compilation failed with errors:\n%s' % '\n'.join('line %d: %s' % (line, msg +': ' + param if param else msg) for (msg, param, line) in self.errors)


class _Compiled(Mapping):
    def __new__(cls,  txt, compress=True):
        compile_errors = []
        callback = _tc.teckit_error_fn(lambda dummy, *err: compile_errors.append(err))
        (tbl, tbl_len) = _tc.compile(txt, len(txt), compress, callback, None)

        if compile_errors: raise CompilationError(compile_errors)
        
        buf = super(Mapping,cls).__new__(cls,tbl[:tbl_len])
        _tc.disposeCompiled(tbl)
        return buf


    def __init__(self, *args):
        res = []
        for arg in args:
            res.append(repr(arg[:20] + '...'
                            if isinstance(arg, str) else arg))
        self._repr_args = ','.join(res)


def translate(txt):
    compile_errors = []
    callback = _tc.teckit_error_fn(lambda dummy, *err: compile_errors.append(err))
    (tbl, tbl_len) = _tc.compileOpt(txt, len(txt), callback, None, _tc.Opt.XML)
    
    if compile_errors: raise CompilationError(compile_errors)
        
    xml_doc = bytes(tbl[:tbl_len])
    _tc.disposeCompiled(tbl)
    return xml_doc


compile = _Compiled

getVersion = _tc.getCompilerVersion

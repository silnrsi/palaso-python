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

import _compiler as _tc
from _compiler import CompilationError, Opt, \
                      getUnicodeName, getTECkitName, getUnicodeValue
from engine import Mapping


def _err_fn(user_data, msg, param, line):
    import sys
    sys.stderr.write('compilation error at line %d: %s\n' % (line,msg +': ' + param if param else msg)) 



class _Compiled(Mapping):
    def __new__(cls,  txt, opts=Opt.Compress):
        (tbl, tbl_len) = _tc.compileOpt(txt, len(txt), 
                                        _tc.teckit_error_fn(_err_fn, ), 
                                        None, opts)
        buf = super(Mapping,cls).__new__(cls,tbl[:tbl_len])
        buf.__table = tbl
        return buf

    def __init__(self, *args):
        res = []
        for arg in args:
            res.append(repr(arg[:20] + '...'
                            if isinstance(arg, str) else arg))
        self._repr_args = ','.join(res)
            
    def __del__(self):
        _tc.disposeCompiled(self.__table)


compile = _Compiled


getVersion = _tc.getCompilerVersion

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

import _compiler
from _compiler import CompilationError, Opt, \
                      getUnicodeName, getTECkitName, getUnicodeValue
from engine import Mapping


def _err_fn(user_data, msg, param, line):
    os.stderr.write('compilation error: %s at line %d\n' % (msg % param, line)) 



class _Compiled(Mapping):
    def __init__(self, txt, opts=Opt.Compress):
        if txt:
            (tbl, tbl_len) = _compiler.compileOpt(txt, len(txt),
                teckit_error_fn(_err_fn, ), None, opts)
            self.__table = tbl
        else:
            self.__table = None
    
    
    def __del__(self):
        self.close()
    
    
    def close(self):
        if self.table:
            _compiler.disposeCompiled(self.table)
            self.__table = None



compile = _Compiled


getVersion = _compiler.getCompilerVersion

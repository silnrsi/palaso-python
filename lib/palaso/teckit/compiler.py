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
from palaso.teckit import _compiler
from palaso.teckit import _common
from typing import Any, AnyStr, List
from itertools import starmap

from palaso.teckit._compiler import (
    getUnicodeName,
    getTECkitName,
    getUnicodeValue)
from palaso.teckit.engine import Mapping

__all__ = ['Mapping',
           'CompilationError',
           'translate', 'compile',
           'getTECkitName', 'getVersion',
           'getUnicodeName', 'getUnicodeValue']


class CompilationError(_common.CompilationError):
    @staticmethod
    def __format_err(msg, param, line):
        return f'line {line}: {msg} {": " + param if param else ""}'

    def __init__(self, errors: List) -> None:
        self.errors = errors

    def __str__(self):
        errors = '\n'.join(starmap(self.__format_err, self.errors))
        return 'compilation failed with errors:\n' + errors


class _Compiled(Mapping):
    def __new__(cls,  txt: AnyStr, compress: bool = True) -> Any:
        compile_errors = []
        if isinstance(txt, str):
            txt = txt.encode('utf_8')
        callback = _compiler.teckit_error_fn(
            lambda _, *err: compile_errors.append(err))
        (tbl, tbl_len) = _compiler.compile(txt, len(txt), compress, callback,
                                           None)
        if compile_errors:
            raise CompilationError(compile_errors)

        buf = super(Mapping, cls).__new__(cls, tbl[:tbl_len])
        _compiler.disposeCompiled(tbl)
        return buf

    def __init__(self, *args) -> None:
        res = []
        for arg in args:
            res.append(repr(arg[:20] + '...'
                            if isinstance(arg, str) else arg))
        self._repr_args = ','.join(res)


def translate(txt: AnyStr) -> bytes:
    compile_errors = []
    if isinstance(txt, str):
        txt = txt.encode('utf_8')
    callback = _compiler.teckit_error_fn(
        lambda _, *err: compile_errors.append(err))
    (tbl, tbl_len) = _compiler.compileOpt(txt, len(txt), callback, None,
                                          _compiler.Opt.XML)

    if compile_errors:
        raise CompilationError(compile_errors)

    xml_doc = bytes(tbl[:tbl_len])
    _compiler.disposeCompiled(tbl)
    return xml_doc


compile = _Compiled

getVersion = _compiler.getCompilerVersion

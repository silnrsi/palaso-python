#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides a python module to interface with SIL's TECKit library compiler API.
#
# Author: Tim Eves
#
# History:
# 20-Jan-2020 tse   Port to Python3 and use updated _engine module.
# 10-Jun-2009 tse   Initial version using the ctypes FFI

from itertools import starmap
from typing import Any, AnyStr, List

from palaso.teckit import _compiler
from palaso.teckit import _common
from palaso.teckit._common import Form
from palaso.teckit._compiler import (
    getUnicodeName,
    getTECkitName,
    getUnicodeValue)
from palaso.teckit.engine import Mapping

__all__ = ['Form', 'Mapping',
           'CompilationError',
           'translate', 'compile',
           'getTECkitName', 'getVersion',
           'getUnicodeName', 'getUnicodeValue']


class CompilationError(_common.CompilationError):
    @staticmethod
    def __format_err(msg: bytes, param: bytes, line: int) -> str:
        msg = msg.decode('utf_8')
        param = (param or b'').decode('utf_8')
        return f'line {line}: {msg}{param and ": "+param}'

    def __init__(self, errors: List) -> None:
        self.errors = errors

    def __str__(self):
        errors = '\n'.join(starmap(self.__format_err, self.errors))
        return 'compilation failed with errors:\n' + errors


def compile(txt: AnyStr,
            compress: bool = True,
            form: Form = Form.Unspecified) -> Any:
    errors = []
    if isinstance(txt, str):
        txt = txt.encode('utf_8_sig')

    @_compiler.teckit_error_fn
    def callback(_, *err): errors.append(err)

    try:
        (tbl, tbl_len) = _compiler.compileOpt(
                            txt, len(txt),
                            compress,
                            callback, None,
                            form)
    except _common.CompilationError:
        if errors:
            raise CompilationError(errors) from None
        else:
            raise

    buf = Mapping(tbl[:tbl_len])
    _compiler.disposeCompiled(tbl)
    return buf


def translate(txt: AnyStr, form: Form = Form.Unspecified) -> bytes:
    errors = []
    if isinstance(txt, str):
        txt = txt.encode('utf_8_sig')

    @_compiler.teckit_error_fn
    def callback(_, *err): errors.append(err)
    try:
        (tbl, tbl_len) = _compiler.compileOpt(
                            txt, len(txt),
                            callback, None,
                            _compiler.Opt.XML)
    except _common.CompilationError:
        if errors:
            raise CompilationError(errors) from None
        else:
            raise

    xml_doc = bytes(tbl[:tbl_len])
    _compiler.disposeCompiled(tbl)
    return xml_doc


getVersion = _compiler.getCompilerVersion

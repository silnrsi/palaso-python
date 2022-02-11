"""
TECkit engine Pythonic interface.

Provides a python module to interface with SIL's TECKit compiler library API.
"""
__author__ = "Tim Eves"
__date__ = "23 January 2020"
__credits__ = None
__copyright__ = "Copyright © 2020 SIL International"
__license__ = "MIT"
__email__ = "tim_eves@sil.org"
# History:
# 20-Jan-2020 tse   Port to Python3 and use updated _engine module.
# 10-Jun-2009 tse   Initial version using the ctypes FFI

from itertools import starmap
from typing import AnyStr, List, cast

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
    def __format_err(msg_: bytes, param_: bytes, line: int) -> str:
        msg = msg_.decode('utf_8')
        param = (param_ or b'').decode('utf_8')
        return f'line {line}: {msg}{param and ": "+param}'

    def __init__(self, errors: List) -> None:
        self.errors = errors

    def __str__(self):
        errors = '\n'.join(starmap(self.__format_err, self.errors))
        return 'compilation failed with errors:\n' + errors


def __compile_opts(txt_: AnyStr, opts: Form):
    errors = []
    if isinstance(txt_, str):
        txt = txt_.encode('utf_8_sig')
    elif isinstance(txt_, bytes):
        txt = cast(str, txt_)
    else:
        raise TypeError("txt is not a str type (either str or bytes")

    @_compiler.teckit_error_fn
    def callback(_, *err): errors.append(err)

    try:
        (tbl, tbl_len) = _compiler.compileOpt(
                            txt, len(txt),
                            callback, None,
                            opts)
        res = tbl[:tbl_len]
        _compiler.disposeCompiled(tbl)
    except _common.CompilationError:
        if errors:
            raise CompilationError(errors) from None
        else:
            raise
    return res


def compile(txt: AnyStr,
            compress: bool = True,
            form: Form = Form.Unspecified) -> Mapping:
    form &= Form.EncodingMask
    tbl = __compile_opts(
        txt,
        (form | _compiler.Opt.Compress) if compress else form)

    buf = Mapping(tbl)
    return buf


def translate(txt: AnyStr, form: Form = Form.Unspecified) -> bytes:
    form &= Form.EncodingMask
    tbl = __compile_opts(txt, form | _compiler.Opt.XML)
    xml_doc = bytes(tbl)
    return xml_doc


getVersion = _compiler.getCompilerVersion

"""
TECkit engine Pythonic interface.

Provides a python module to a Pythonic interface with SIL's TECKit
engine library.
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

import codecs
import ctypes
import sys
from typing import Any, AnyStr, Tuple, Union, cast
from functools import lru_cache
from os import PathLike
from palaso.teckit import _engine
from palaso.teckit._common import (
    ConverterBusy, Form, MappingVersionError)
from palaso.teckit._engine import (
    FullBuffer, EmptyBuffer, UnmappedChar,
    Flags, Option,
    getVersion, getConverterName)

__all__ = ['ConverterBusy', 'MappingVersionError',
           'FullBuffer', 'EmptyBuffer', 'UnmappedChar',
           'Converter', 'Flags', 'Form', 'Mapping', 'Option',
           'getVersion']


class Mapping(bytes):
    def __new__(cls, data: Union[PathLike, bytes]):
        if isinstance(data, bytes):
            return super(Mapping, cls).__new__(cls, data)
        else:
            with open(data, 'rb') as mf:
                return super(Mapping, cls).__new__(cls, mf.read())

    def __init__(self, *args, **kw) -> None:
        res = []
        for arg in args:
            res.append(repr(arg[:20] + b'...'
                            if isinstance(arg, bytes) else arg))
        for k, v in kw.items():
            res.append(
                f'{k}={v[:20]+ b"..." if isinstance(v, bytes) else v!r}')
        self._repr_args = ','.join(res)

    @lru_cache(maxsize=16)
    def __getattr__(self, name: str) -> str:
        try:
            nid = getattr(_engine.NameID, name)
            nlen = _engine.getMappingName(self, len(self), nid)
        except AttributeError:
            raise AttributeError(f'{self!r} object has no attribute {name!r}')
        except IndexError:
            raise
        buf = ctypes.create_string_buffer(nlen)
        nlen = _engine.getMappingName(self, len(self), nid, buf, nlen)
        return bytes(buf[:nlen]).decode('utf8')

    def __str__(self) -> str:
        return self.lhsName + ' <-> ' + self.rhsName

    def __repr__(self) -> str:
        return (f'Mapping({self._repr_args})' if hasattr(self, '_repr_args')
                else self.__str__())

    @property
    @lru_cache(maxsize=8)
    def flags(self) -> Tuple[Flags, Flags]:
        lf, rf = _engine.getMappingFlags(self, len(self))
        return Flags(lf), Flags(rf)

    @property
    def lhsFlags(self) -> Flags:
        return self.flags[0]

    @property
    def rhsFlags(self) -> Flags:
        return self.flags[1]


if sys.byteorder == 'little':
    _Form_UNICODE = Form.UTF32LE
    _unicode_encoder_name = 'utf-32le'
else:
    _Form_UNICODE = Form.UTF32BE
    _unicode_encoder_name = 'utf-32be'

_unicode_encoder = codecs.getencoder(_unicode_encoder_name)
_unicode_decoder = codecs.getdecoder(_unicode_encoder_name)


def _form_from_flags(form: Form, flags: Flags) -> Form:
    if form is Form.Unspecified or form is None:
        if Flags.expectsNFD in flags or Flags.generatesNFD in flags:
            form = Form.NFD
        elif Flags.expectsNFC in flags or Flags.generatesNFC in flags:
            form = Form.NFC
    else:
        form &= Form.NormalizationMask
    return form | (_Form_UNICODE if Flags.unicode in flags else Form.Bytes)


class Converter(object):
    def __init__(self, mapping: Mapping, forward: bool = True,
                 source: Form = Form.Unspecified,
                 target: Form = Form.Unspecified) -> None:
        source = _form_from_flags(
            source,
            mapping.lhsFlags if forward else mapping.rhsFlags)
        target = _form_from_flags(
            target,
            mapping.rhsFlags if forward else mapping.lhsFlags)
        self._converter = _engine.createConverter(
                            mapping, len(mapping), forward,
                            source, target)
        self._buffer = ctypes.create_string_buffer(80*4)

    def __del__(self):
        _engine.disposeConverter(self._converter)

    @lru_cache(maxsize=32)
    def __getattr__(self, name: str) -> str:
        try:
            nid = getattr(_engine.NameID, name)
            nlen = getConverterName(self._converter, nid)
        except (AttributeError):
            raise AttributeError(f'{self!r} object has no attribute {name!r}')
        except IndexError:
            raise

        buf = ctypes.create_string_buffer(nlen)
        nlen = getConverterName(self._converter, nid, buf, nlen)
        return str(cast(bytes, buf[:nlen]), 'ascii')

    @property
    @lru_cache(maxsize=8)
    def flags(self) -> Tuple[Flags, Flags]:
        lf, rf = _engine.getConverterFlags(self._converter)
        return Flags(lf), Flags(rf)

    @property
    def sourceFlags(self) -> Flags:
        return self.flags[0]

    @property
    def targetFlags(self) -> Flags:
        return self.flags[1]

    def reset(self):
        _engine.resetConverter(self._converter)

    def _handle_unmapped_char(self, input: AnyStr, context: str,
                              uc: UnmappedChar):
        # This looks like a nasty hack because it is. Sorry
        cons, outs, lhc = uc.args
        _engine.resetConverter(self._converter)
        name = (self.lhsName + '<->' + self.rhsName).lower()
        errtype = (UnicodeEncodeError if Flags.unicode in self.sourceFlags
                   else UnicodeDecodeError)
        if Flags.unicode in self.sourceFlags:
            end = cons//4
            end -= (lhc if end != len(input) else 0)
            start = end - 1
        else:
            start = cons - 1
            end = start + lhc
        end = min(end, len(input))
        raise errtype(name, cast(Any, input), start, end,
                      context + ' stopped at unmapped character')

    def _coerce_to_target(self, data: bytes):
        return (_unicode_decoder(data)[0]
                if Flags.unicode in self.targetFlags
                else data)

    def convert(self, input: AnyStr, finished: bool = False,
                options: Option = Option.UseReplacementCharSilently) -> AnyStr:
        # Validate input parameters and do an necessary conversions
        if Flags.unicode in self.sourceFlags:
            if isinstance(input, bytes):
                raise TypeError(
                    "source is type 'bytes' but type 'str' is expected")
            data: bytes = _unicode_encoder(input)[0]
        else:
            if isinstance(input, str):
                raise TypeError(
                    "source is type 'str' but type 'bytes' is expected")
            data: bytes = input
        options |= finished and Option.InputIsComplete

        buf = self._buffer
        cons = outs = 0
        res: Any = '' if Flags.unicode in self.targetFlags else b''
        while data:
            try:
                cons, outs, lhc = _engine.convertBufferOpt(
                                    self._converter,
                                    data, len(data),
                                    buf, len(buf),
                                    options)
            except FullBuffer as err:
                cons, outs, lhc = err.args
            except EmptyBuffer:
                if finished:
                    raise
            except UnmappedChar as err:
                self._handle_unmapped_char(input, 'convert', err)

            res += self._coerce_to_target(cast(bytes, buf[:outs]))
            data = data[cons:]

        if finished:
            res += self.flush()
        return res

    def flush(self, finished: bool = True,
              options: Option = Option.UseReplacementCharSilently) -> AnyStr:
        options = cast(Option, options | (finished and Option.InputIsComplete))

        buf = self._buffer
        outs = 0
        res: Any = '' if Flags.unicode in self.targetFlags else b''
        while True:
            try:
                outs, lhc = _engine.flushOpt(
                                self._converter, buf, len(buf), options)
                return res + self._coerce_to_target(cast(bytes, buf[:outs]))
            except FullBuffer as err:
                outs, lhc = err.args
                res += self._coerce_to_target(cast(bytes, buf[:outs]))
            except UnmappedChar as err:
                self._handle_unmapped_char('', 'flush', err)

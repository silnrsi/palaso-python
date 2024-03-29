import codecs
from typing import Dict, Optional, Union, cast
from os import PathLike
from pathlib import Path
from palaso.teckit import engine, compiler
from palaso.teckit._engine import Option

__all__ = ['engine', 'compiler']


class _mapping(object):
    def __init__(self, mapping: engine.Mapping):
        self.map = mapping
        self.replacement = ''


_tec_mapping_cache_: Dict[str, _mapping] = {}


def register(mapping: Union[PathLike, engine.Mapping]):
    if isinstance(mapping, str):
        mapping = engine.Mapping(mapping)
    elif not isinstance(mapping, engine.Mapping):
        raise TypeError('object %r is not type engine.Mapping' % mapping)

    key = f'{mapping.lhsName}<->{mapping.rhsName}'.lower()
    _tec_mapping_cache_[key] = _mapping(mapping)


def register_library(path: Path):
    for mapfile in path.glob('*.tec'):
        register(mapfile)


def list_mappings() -> Dict[str, str]:
    return {n: repr(m.map) for (n, m) in _tec_mapping_cache_.items()}


def _teckit_search(mapping: str) -> Optional[codecs.CodecInfo]:
    mapobj = _tec_mapping_cache_.get(mapping)
    if not mapobj:
        return None

    def incrementalencoder(errors='strict'):
        return IncrementalEncoder(mapobj, errors)

    def incrementaldecoder(errors='strict'):
        return IncrementalDecoder(mapobj, errors)

    def streamreader(stream, errors='strict'):
        return StreamReader(mapobj, stream, errors)

    def streamwriter(stream, errors='strict'):
        return StreamWriter(mapobj, stream, errors)

    codec = Codec(mapobj)
    return codecs.CodecInfo(
        name=str(mapobj),
        encode=codec.encode,
        decode=codec.decode,
        incrementalencoder=incrementalencoder,
        incrementaldecoder=incrementaldecoder,
        streamreader=streamreader,
        streamwriter=streamwriter)


class Codec(codecs.Codec):
    def __init__(self, mapping: _mapping):
        self.__enc = engine.Converter(mapping.map, forward=False)
        self.__dec = engine.Converter(mapping.map, forward=True)
        mapping.replacement = self.__dec.convert(
                                self.__enc.convert('\ufffd', finished=True),
                                finished=True)
        self.__enc.reset()

    @staticmethod
    def convert(conv, data, final, errors='strict'):
        try:
            res = conv.convert(data, finished=final,
                               options=Option.DontUseReplacementChar)
            return (res, len(res))
        except UnicodeEncodeError as uerr:
            rep, rp = codecs.lookup_error(errors)(uerr)
            try:
                prefix = conv.convert(
                            uerr.object[:uerr.start] + cast(str, rep),
                            finished=final,
                            options=Option.DontUseReplacementChar)
            except UnicodeEncodeError:
                raise UnicodeEncodeError(uerr.args[0], uerr.args[1],
                                         uerr.args[2], uerr.args[3],
                                         f'cannot convert replacement {rep}'
                                         ' to target encoding') \
                    from None
            suffix = Codec.convert(conv, data[rp:], final, errors)
            return (prefix+suffix[0], rp+suffix[1])
        except UnicodeDecodeError as uerr:
            rep, rp = codecs.lookup_error(errors)(uerr)
            prefix = conv.convert(uerr.object[:uerr.start], finished=final,
                                  options=Option.DontUseReplacementChar)
            suffix = Codec.convert(conv, data[rp:], final, errors)
            return (prefix+rep+suffix[0], rp+suffix[1])

    def encode(self, input, errors='strict'):
        return Codec.convert(self.__enc, input, True, errors)

    def decode(self, input, errors='strict'):
        return Codec.convert(self.__dec, input, True, errors)


class IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, mapping, errors='strict'):
        super(IncrementalEncoder).__init__(errors)
        self._conv = engine.Converter(mapping.map, False)

    def encode(self, object, final=False):
        return Codec.convert(self._conv, object, final, self.errors)[0]

    def reset(self): return self._conv.reset()

    def getstate(self): return self._conv

    def setstate(self, state): return self._conv


class IncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, mapping, errors='strict'):
        super(IncrementalEncoder).__init__(errors)
        self._conv = engine.Converter(mapping.map, True)

    def decode(self, object, final=False):
        return Codec.convert(self._conv, object, final, self.errors)[0]

    def reset(self): return self._conv.reset()

    def getstate(self): return self._conv

    def setstate(self, state): return self._conv


class StreamWriter(Codec, codecs.StreamWriter):
    def __init__(self, mapping, stream, errors='strict'):
        Codec.__init__(self, mapping)
        codecs.StreamWriter.__init__(self, stream, errors)


class StreamReader(Codec, codecs.StreamReader):
    def __init__(self, mapping, stream, errors='strict'):
        Codec.__init__(self, mapping)
        codecs.StreamReader.__init__(self, stream, errors)


def teckit_replace_errors(exception):
    if isinstance(exception, UnicodeDecodeError):
        raise TypeError(
            "don't know how to handle UnicodeDecodeError in error callback")
    rep = _tec_mapping_cache_[exception.encoding].replacement
    return (rep, exception.end)


codecs.register(_teckit_search)
codecs.register_error('teckitreplace', teckit_replace_errors)

import codecs
import engine
import glob
import os.path
from _engine import Option

__all__ = ['engine','compiler']

_tec_mapping_cache_ = {}

def register(mapping):
    if isinstance(mapping, (str,unicode)):
        mapping=engine.Mapping(mapping)
    elif not isinstance(mapping,engine.Mapping):
        raise TypeError('object %r is not type engine.Mapping' % mapping)
    
    _tec_mapping_cache_[('%s<->%s' % (mapping.lhsName,mapping.rhsName)).lower()] = mapping

def register_library(path):
    map(register, glob.glob(os.path.join(path,'*.tec')))

def list_mappings():
    return _tec_mapping_cache_

def _teckit_search(mapping):
    mapobj = _tec_mapping_cache_.get(mapping)
    if mapobj :
        _dec = engine.Converter(mapobj)
        _enc = engine.Converter(mapobj, forward = False)
        return codecs.CodecInfo(
            name = mapobj.__str__(),
            encode = _enc.encode,
            decode = _dec.decode,
            incrementalencoder = _CreateIncrementalEncoder(_enc),
            incrementaldecoder = _CreateIncrementalDecoder(_dec),
            streamreader = _CreateStreamReader(_dec),
            streamwriter = _CreateStreamWriter(_enc))
    else : return None 

_errors = {
    'strict':Option.DontUseReplacementChar,
    'ignore':Option.DontUseReplacementChar,
    'replace':Option.UseReplacementCharSilently,
    'xmlcharrefreplace':Option.UseReplacementCharWithWarning,
    'xmlcharrefreplace':Option.UseReplacementCharWithWarning
    }



class _CodecInfo (object):
    def __init__(self,name,mapping):
        self._map = mapping
        self.name = name
        self._enc = engine.Converter(self._map, forward=False)
        self._dec = engine.Converter(self._map, forward=True)
    
    def encode(input,errors='strict'):
        enc = engine.Converter(self._map, forward=False)
        res = enc.convert(input,_errors[errors] + Option.InputIsComplete)
        return res + enc.flush(_errors[errors])
    
    def decode(input,errors='strict'):
        dec = engine.Converter(self._map)
        res = dec.convert(input,_errors[errors] + Option.InputIsComplete)
        return res + enc.flush(_errors[errors])

# Don't need to store residue in these objects since new converter
# created for each instance, so store state in the converter
def _CreateIncrementalEncoder(converter) :
    class _IncrementalEncoder(codecs.IncrementalEncoder) :
        _conv = converter
        def encode(self, input, final = False) :
            return self._conv.convert(input, finished = final, options = _errors[self.errors])
    return _IncrementalEncoder

def _CreateIncrementalDecoder(converter) :
    class _IncrementalDecoder(codecs.IncrementalDecoder) :
        _conv = converter
        def decode(self, input, final = False) :
            return self._conv.convert(input, finished = final, options = _errors[self.errors])
    return _IncrementalDecoder

def _CreateStreamWriter(converter) :
    class _StreamWriter(codecs.StreamWriter) :
        _conv = converter
        def encode(self, stream, errors = 'strict') :
            return self._conv.encode(stream, errors = _errors[errors])
    return _StreamWriter

def _CreateStreamReader(converter) :
    class _StreamReader(codecs.StreamReader) :
        _conv = converter
        def decode(self, stream, errors = 'strict') :
            return self._conv.decode(stream, errors = _errors[errors])
    return _StreamReader

codecs.register(_teckit_search)

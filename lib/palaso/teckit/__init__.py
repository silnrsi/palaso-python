from __future__ import absolute_import
import codecs
import palaso.teckit.engine
import glob
import os.path
from palaso.teckit._engine import Option

__all__ = ['engine','compiler']

_tec_mapping_cache_ = {}

class _mapping(object):
    def __init__(self, mapping):
        self.map = mapping
        self.replacement = None

def register(mapping):
    if isinstance(mapping, (str,unicode)):
        mapping=engine.Mapping(mapping)
    elif not isinstance(mapping,engine.Mapping):
        raise TypeError('object %r is not type engine.Mapping' % mapping)
    
    _tec_mapping_cache_[('%s<->%s' % (mapping.lhsName,mapping.rhsName)).lower()] = _mapping(mapping)

def register_library(path):
    map(register, glob.glob(os.path.join(path,'*.tec')))

def list_mappings():
    return dict((n,repr(m.map)) for (n,m) in _tec_mapping_cache_.iteritems())

def _teckit_search(mapping):
    mapobj = _tec_mapping_cache_.get(mapping)
    if not mapobj: return None

    def incrementalencoder(errors='strict'): return IncrementalEncoder(mapobj, errors)
    def incrementaldecoder(errors='strict'): return IncrementalDecoder(mapobj, errors)
    def streamreader(stream, errors='strict'):return StreamReader(mapobj, stream, errors)
    def streamwriter(stream, errors='strict'):return StreamWriter(mapobj, stream, errors)

    codec = Codec(mapobj)            
    return codecs.CodecInfo(
        name = mapobj.__str__(),
        encode = codec.encode,
        decode = codec.decode,
        incrementalencoder = incrementalencoder,
        incrementaldecoder = incrementaldecoder,
        streamreader = streamreader,
        streamwriter = streamwriter)


class Codec(codecs.Codec):
    def __init__(self, mapping):
        self.__enc = engine.Converter(mapping.map, forward=False)
        self.__dec = engine.Converter(mapping.map, forward=True)
        mapping.replacement = self.__dec.convert(
                                self.__enc.convert(u'\ufffd', finished=True),
                                finished=True)
        self.__enc.reset()
        
    
    @staticmethod
    def convert(conv, data, final, errors='strict'):
        try:
            res = conv.convert(data, finished=final, 
                               options=Option.DontUseReplacementChar)
            return (res,len(res))
        except UnicodeEncodeError as uerr:
            rep,rp = codecs.lookup_error(errors)(uerr)
            try:
                prefix = conv.convert(uerr.object[:uerr.start] + rep, finished=final, 
                                      options=Option.DontUseReplacementChar)
            except UnicodeEncodeError:
                raise UnicodeEncodeError(*(uerr.args[:4] + ('cannot convert replacement %r to target encoding' % rep,)))
            suffix = Codec.convert(conv, data[rp:], final, errors)
            return (prefix+suffix[0],rp+suffix[1])
        except UnicodeDecodeError as uerr:
            rep,rp = codecs.lookup_error(errors)(uerr)
            prefix = conv.convert(uerr.object[:uerr.start], finished=final, 
                                  options=Option.DontUseReplacementChar)
            suffix = Codec.convert(conv, data[rp:], final, errors)
            return (prefix+rep+suffix[0],rp+suffix[1])
        

    def encode(self, input, errors='strict'):
        return Codec.convert(self.__enc, input, True, errors)

    def decode(self, input, errors='strict'):
        return Codec.convert(self.__dec, input, True, errors)
        

class IncrementalCommon(object):
    def __init__(self, forward, mapping, errors):
        base = codecs.IncrementalDecoder if forward else codecs.IncrementalEncoder
        base.__init__(self, errors)
        self._conv = engine.Converter(mapping.map, forward)
    
    def convert(self, object, final=False):
        return Codec.convert(self._conv, object, final, self.errors)[0]
    
    def reset(self):    return self._conv.reset()
    
    def getstate(self): return self._conv
    
    def setstate(self, state): return self._conv


class IncrementalEncoder(IncrementalCommon, codecs.IncrementalEncoder):
    def __init__(self, mapping, errors='strict'):
        super(IncrementalEncoder,self).__init__(False, mapping, errors)

    encode = IncrementalCommon.convert


class IncrementalDecoder(IncrementalCommon, codecs.IncrementalDecoder):
    def __init__(self, mapping, errors='strict'):
        super(IncrementalDecoder,self).__init__(True, mapping, errors)

    decode = IncrementalCommon.convert


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
        raise TypeError("don't know how to handle UnicodeDecodeError in error callback")
    rep = _tec_mapping_cache_[exception.encoding].replacement
    return (rep, exception.end)

codecs.register(_teckit_search)
codecs.register_error('teckitreplace', teckit_replace_errors)



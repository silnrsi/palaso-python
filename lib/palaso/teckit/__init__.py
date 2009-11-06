import codecs
import engine
import glob
import os.path

__all__ = ['engine','compiler']

__tec_mapping_cache__ = {}

def register(mapping):
    if isinstance(mapping, (str,unicode)):
        mapping=engine.Mapping(mapping)
    elif not isinstance(mapping,engine.Mapping):
        raise TypeError('object %r is not type engine.Mapping' % mapping)
    
    __tec_mapping_cache__[('%s<->%s' % (mapping.lhsName,mapping.rhsName)).lower()] = mapping

def register_library(path):
    map(register, glob.glob(os.path.join(path,'*.tec')))

def list_mappings():
    return __tec_mapping_cache__

def _teckit_search(mapping):
    print 'looking up',mapping
    try:
        mapping = __tec_mapping_cache__[mapping]
    except KeyError:
        return None
    
    return None

__errors = {
    'strict':engine.Option.DontUseReplacementChar,
    'ignore':engine.Option.DontUseReplacementChar,
    'replace':engine.Option.UseReplacementCharSilently,
    'xmlcharrefreplace':engine.Option.UseReplacementCharWithWarning,
    'xmlcharrefreplace':engine.Option.UseReplacementCharWithWarning
    }



class _CodecInfo (object):
    def __init__(self,name,mapping):
        self.__map = mapping
        self.name = name
        self.__enc = engine.Converter(self.__map, forward=False)
        self.__dec = engine.Converter(self.__map, forward=True)
    
    def encode(input,errors='strict'):
        enc = engine.Converter(self.__map, forward=False)
        res = enc.convert(input,__errors[errors] + Option.InputIsComplete)
        return res + enc.flush(__errors[errors])
    
    def decode(input,errors='strict'):
        dec = engine.Converter(self.__map)
        res = dec.convert(input,__errors[errors] + Option.InputIsComplete)
        return res + enc.flush(__errors[errors])



class _IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self,errors='strict'):
        self.__options = __errors[errors]

codecs.register(_teckit_search)

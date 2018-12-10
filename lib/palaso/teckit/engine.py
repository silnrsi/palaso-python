#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides a python module to interface with SIL's TECKit library engine.
#
# Author: Tim Eves
#
# History:
#   2009-06-10  tse     Initial version using the ctypes FFI
#
from __future__ import with_statement

import palaso.teckit._engine as _engine
import codecs, sys

from palaso.teckit._engine import getVersion, memoize
from palaso.teckit._engine import Option
from palaso.teckit._engine import \
    CompilationError, ConverterBusy, MappingVersionError, \
    FullBuffer, EmptyBuffer, UnmappedChar, flags, Form


class Mapping(str):
    def __new__(cls, path):
        with open(path, 'rb') as mf:
            return super(Mapping,cls).__new__(cls,mf.read())
    
    def __init__(self, path):
        self._repr_args = repr(path)

    @memoize   
    def __getattr__(self, name):
        from palaso.teckit._engine import getMappingName
        try:
            nid = getattr(_engine.NameID,name)
            nlen = getMappingName(self, len(self), nid)
        except (AttributeError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
        except IndexError:
            return None
        buf  = _engine.create_string_buffer(nlen)
        nlen = getMappingName(self, len(self), nid, buf, nlen)
        return str(buf[:nlen])

    def __str__(self):  return self.lhsName + ' <-> ' + self.rhsName
    
    def __repr__(self): return ('Mapping(%s)' % self._repr_args 
                                if hasattr(self,'_repr_args') 
                                else self.__str__())
    
    @property
    @memoize
    def flags(self):
        return _engine.getMappingFlags(self, len(self))
    
    @property
    def lhsFlags(self):
        return self.flags[0]
    
    @property
    def rhsFlags(self):
        return self.flags[1]


if sys.byteorder == 'little':
    _Form_UNICODE = Form.UTF32LE
    _unicode_encoder_name = 'utf-32le'
else:
    _Form_UNICODE = Form.UTF32BE
    _unicode_encoder_name = 'utf-32be'

_unicode_encoder = codecs.getencoder(_unicode_encoder_name)
_unicode_decoder = codecs.getdecoder(_unicode_encoder_name)


def _form_from_flags(form, flags):
    if form==Form.Unspecified or form==None:
        if   flags.expectsNFD or flags.generatesNFD:  form = Form.NFD
        elif flags.expectsNFC or flags.generatesNFC:  form = Form.NFC
    else:
        form &= Form_NormalizationMask
    return form + (_Form_UNICODE if flags.unicode else Form.Bytes)


class Converter(object):
    def __init__(self, mapping, forward=True,source=Form.Unspecified,target=Form.Unspecified):
        source = _form_from_flags(source, mapping.lhsFlags if forward else mapping.rhsFlags)
        target = _form_from_flags(target, mapping.rhsFlags if forward else mapping.lhsFlags)
        self._converter = _engine.createConverter(mapping, len(mapping), forward, source, target)
        self._buffer    = _engine.create_string_buffer(80*4)
    
    
    def __del__(self):
        _engine.disposeConverter(self._converter)
    
    
    @memoize
    def __getattr__(self, name):
        from _engine import getConverterName
        try:
            nid = getattr(_engine.NameID,name)
            nlen = getConverterName(self._converter, nid)
        except (AttributeError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
        except IndexError:
            return None
        
        buf  = _engine.create_string_buffer(nlen)
        nlen = getConverterName(self._converter, nid, buf, nlen)
        return str(buf[:nlen])
    
    
    @property 
    @memoize
    def flags(self):
        return _engine.getConverterFlags(self._converter)
    
    
    @property
    def sourceFlags(self):
        return self.flags[0]
    
    
    @property
    def targetFlags(self):
        return self.flags[1]
    
    
    def reset(self):
        _engine.resetConverter(self._converter)
    
    
    def _handle_unmapped_char(self, input, context, cons, outs, lhc):
        # This looks like a nasty hack because it is. Sorry
        _engine.resetConverter(self._converter)
        name = (self.lhsName + '<->' + self.rhsName).lower()
        errtype = UnicodeEncodeError if self.sourceFlags.unicode else UnicodeDecodeError
        if self.sourceFlags.unicode:
            end = cons/4
            end -= (lhc if end != len(input) else 0)
            start = end -1
        else:
            start = cons - 1
            end = start + lhc
        end = min(end,len(input))
        raise errtype(name, input, start, end, 
                      context + ' stopped at unmapped character')
        
    
    def _coerce_to_target(self, data):
        return _unicode_decoder(data)[0] if self.targetFlags.unicode else data
    
    
    def convert(self, input, finished=False, options=Option.UseReplacementCharSilently):
        # Validate input parameters and do an necessary conversions
        if self.sourceFlags.unicode and isinstance(input,str):
            raise TypeError("source is type 'str' but type 'unicode' is expected")
        if not self.sourceFlags.unicode and isinstance(input, unicode):
            raise TypeError("source is type 'unicode' but type 'str' is expected")    
        data = _unicode_encoder(input)[0] if self.sourceFlags.unicode else input
        options |= finished and Option.InputIsComplete
        
        buf = self._buffer; cons = outs = 0; res = ''
        while data:
            try:
                cons,outs,lhc = _engine.convertBufferOpt(self._converter, 
                                                         data, len(data), 
                                                         buf, len(buf), 
                                                         options)
            except FullBuffer as e: pass
            except EmptyBuffer as e:
                if finished: 
                    raise self._unicode_error('expected more data.')
            except UnmappedChar as err:
                self._handle_unmapped_char(input, 'convert', err)
            
            res += self._coerce_to_target(str(buf[:outs]))
            data = data[cons:]
        
        if finished:
            res += self.flush()
        return res
    
    
    def flush(self,finished=True,options=Option.UseReplacementCharSilently):
        options |= finished and Option.InputIsComplete
        
        buf = self._buffer; outs = 0; res  = ''
        while True:
            try:
                outs,lhc = _engine.flushOpt(self._converter, 
                                            buf, len(buf), 
                                            options)
                return res + self._coerce_to_target(str(buf[:outs]))
            except FullBuffer as outs:
                res += self._coerce_to_target(str(buf[:outs]))
            except UnmappedChar as err:
                self._handle_unmapped_char(input, 'flush', err)



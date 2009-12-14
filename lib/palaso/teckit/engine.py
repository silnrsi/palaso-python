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

import _engine
import codecs

from _engine import getVersion, memoize
from _engine import Option
from _engine import \
    CompilationError, ConverterBusy, MappingVersionError, \
    FullBuffer, EmptyBuffer, flags, Form

_errors = {
    'strict':Option.DontUseReplacementChar,
    'ignore':Option.DontUseReplacementChar,
    'replace':Option.UseReplacementCharSilently,
    'xmlcharrefreplace':Option.UseReplacementCharWithWarning,
    'xmlcharrefreplace':Option.UseReplacementCharWithWarning
    }

class Mapping(str):
    def __new__(cls, path):
        with open(path, 'rb') as mf:
            data = mf.read()
        return str.__new__(cls, data)
    
    def __init__(self, path):
        self._repr_args = repr(path)

    @memoize   
    def __getattr__(self, name):
        from _engine import getMappingName
        try:
            nid = getattr(_engine.NameID,name)
            nlen = getMappingName(self, len(self), nid)
        except (AttributeError,IndexError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
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


def _form_from_flags(form, flags):
    if form==Form.Unspecified:
        if   flags.expectsNFD or flags.generatesNFD:  form = Form.NFD
        elif flags.expectsNFC or flags.generatesNFC:  form = Form.NFC
    return form + (Form.UTF8 if flags.unicode else Form.Bytes)


class Converter(object):
    def __init__(self, mapping, forward=True,source=Form.Unspecified,target=Form.Unspecified):
        source = _form_from_flags(source, mapping.lhsFlags if forward else mapping.rhsFlags)
        target = _form_from_flags(target, mapping.rhsFlags if forward else mapping.lhsFlags)
        self._converter = _engine.createConverter(mapping, len(mapping), forward, source, target)
        self._residue  = ''

    def __del__(self):
        _engine.disposeConverter(self._converter)
    
    @memoize
    def __getattr__(self, name):
        from _engine import getConverterName
        try:
            nid = getattr(_engine.NameID,name)
            nlen = getConverterName(self._converter, nid)
        except (AttributeError,IndexError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
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
        self._residue = ''
    
    def encode(self, input, errors = 'strict') :
        res = self.convert(input, finished = True, options = _errors[errors])
        residue = len(self._residue)
        self.reset()
        return (res, residue)

    def decode(self, input, errors = 'strict') :
        res = self.convert(input, finished = True, options = _errors[errors])
        residue = len(self._residue)
        self.reset()
        return (res, residue)
    
    def convert(self, data, finished=False, options=Option.UseReplacementCharSilently):
        if self.sourceFlags.unicode and isinstance(data,str):
            raise TypeError("data is type 'str' but unicode is expected")
        
        options += Option.InputIsComplete if finished else 0
        if self.sourceFlags.unicode:
            data = codecs.encode(data,'utf-8')
        data = self._residue + data
        
        buf = _engine.create_string_buffer(long(len(data)*3/2))
        out = 0
        while True:
            try:
                #print 'trying with buffer size %d' % len(buf)
                cons,outs,lhc = _engine.convertBufferOpt(self._converter, data, len(data), buf, len(buf), options)
                if finished:
                    self.reset()
                break
            except FullBuffer, (cons,outs,lhc):
                #print 'conv:',(cons,outs,lhc)
                outstr = self.flush(finished,options)
                #print 'conv:',repr(unicode(str(buf[:outs]),'utf-8') + outstr)
                buf=_engine.create_string_buffer(long(len(buf)*3/2))
            except EmptyBuffer, (cons,outs,lhc):
                break
        
        self.__residue = data[cons:]
        
        buf = str(buf[:outs])
        return unicode(buf,'utf-8') if self.targetFlags.unicode else buf
    
    def flush(self,finished=True,options=Option.UseReplacementCharSilently):
        options += Option.InputIsComplete if finished else 0
        buf = _engine.create_string_buffer(128L)
        outs = 0
        while True:
            try:
                outs,lhc = _engine.flushOpt(self._converter, buf, len(buf), options)
                if finished:
                    self.reset()
                break
            except FullBuffer:
                #print 'flush:',(cons,outs,lhc)
                #print 'flush:',repr(unicode(str(buf[:outs]),'utf-8'))
                buf=_engine.create_string_buffer(long(len(buf)*3/2))

        buf = str(buf[:outs])
        return unicode(buf,'utf-8') if self.targetFlags.unicode else buf

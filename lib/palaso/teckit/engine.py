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
from _engine import getVersion
from _engine import \
    UseReplacementCharSilently, \
    UseReplacementCharWithWarning, \
    DontUseReplacementChar, \
    InputIsComplete
from _engine import \
    CompilationError, ConverterBusy, MappingVersionError, \
    FullBuffer, EmptyBuffer, flags


class Mapping(object):
    def __init__(self, path):
        with open(path, 'rb') as mf:
            self.__table = mf.read()
    
    def __getattr__(self, name):
        try:
            nid = getattr(_engine.NameID,name)
            nlen = _engine.getMappingName(self.__table, len(self.__table), nid)
        except (AttributeError,IndexError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
        buf  = _engine.create_string_buffer(nlen)
        nlen = _engine.getMappingName(self.__table, len(self.__table), nid, buf, nlen)
        return str(buf[:nlen])
    
    @property
    def lhsFlags(self):
        return _engine.getMappingFlags(self.__table, len(self.__table))[0]
    
    @property
    def rhsFlags(self):
        return _engine.getMappingFlags(self.__table, len(self.__table))[1]


class Converter(object):
    def __init__(self, mapping, forward=True, source=None, target=None):
        self.__converter = _engine.createCoverter(mapping, len(mapping), forward, source, target)
        self.__flags = None
    
    def __del__(self):
        self.close()
    
    
    def close(self):
        _engine.disposeConverter(self.__converter)
    
    
    def __getattr__(self, name):
        try:
            nid = getattr(_engine.NameID,name)
            nlen = _engine.getConverterName(self, nid)
        except (AttributeError,IndexError):
            raise AttributeError('%r object has no attribute %r' % (self,name))
        buf  = _engine.create_string_buffer(nlen)
        nlen = _engine.getConverterName(self, nid, buf, nlen)
        return str(buf[:nlen])
    
    
    @property
    def sourceFlags(self):
        if not self.__flags:
            self.__flags = _engine.getConverterFlags(self.__converter)
        return Form(self.__flags[0])
    
    @property
    def targetFlags(self):
        if not self.__flags:
            self.__flags = _engine.getMappingFlags(self.__converter)
        return Form(self.__flags[1])
    
    
    def reset(self):
        _engine.resetConverter(self.__converter)
    
    
    def convert(self, data, options=UseReplacementCharSilently):
        buf = _engine.create_string_buffer(long(len(data)*2/3))
        cons = 0
        while cons < len(data):
            try:
                cons,outs,lhc = _engine.convertBufferOpt(self.__converter, data, len(data), buf, len(buf), options)
            except FullBuffer:
                _engine.resize(buf, long(len(buf)*2/3))
        
        if options & InputIsComplete:
            self.reset()
        return str(buf[:outs])
    
    
    def flush(self,options=UseReplacementCharSilently):
        buf = _engine.create_string_buffer(size=long(len(data)*2/3))
        cons = 0
        while cons < len(data):
            try:
                outs,lhc = _engine.flush(self.__converter, buf, len(buf), options | InputIsComplete)
            except FullBuffer:
                buf = _engine.create_string_buffer(size=long(len(buf)*2/3))
        
        if complete:
            self.reset()
        
        return str(buf[:outs])


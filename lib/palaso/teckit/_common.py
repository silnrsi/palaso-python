#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides python definitions of the common types and defines for the 
# engine and compiler.
#
# Author: Tim Eves
#
# History:
#   10-Jun-2009     tse     converted to python ctypes and added the
#                            status_check function for the ctypes errcheck 
#                            protocol.
# History of TECKit_Common.h this is based on:
#   16-Sep-2006     jk      updated version to 2.4 (adding new 
#                            compiler APIs for Bob E)
#   23-May-2005     jk      patch for 64-bit architectures (thanks to 
#                            Ulrik P)
#   18-Mar-2005     jk      updated minor version for 2.3 (engine unchanged,
#                            XML option in compiler)
#   23-Sep-2003     jk      updated for version 2.1 - extended status values
#   xx-xxx-2002     jk      version 2.0 initial release
#

from __future__ import with_statement

from ctypes import *
from itertools import chain,count

currentTECKitVersion = 0x00020004   # 16.16 version number


def ENUM(*names, **kwds):
    base=object
    if names:
        if not isinstance(names[0],basestring):
            base=names[0]
            names=names[1:]
        if names:
            kwds = dict(zip(names, kwds.get('values',range(len(names)))))
    cls = type('_ENUM',(base,),kwds)
    return cls

# low byte is the basic status of the conversion process */
StatusMask_Basic        = 0x000000FF

# one byte of the status value is used for warning flags
StatusMask_Warning      = 0x0000FF00

Status = ENUM(
    NoError = 0,

# positive values are informational status values */
    OutputBufferFull = 1,  # ConvertBuffer or Flush: output buffer full, so not all input was processed 
    NeedMoreInput    = 2,  # ConvertBuffer: processed all input data, ready for next chunk 

# only returned in version 2.1 or later, with DontUseReplacementChar option
    UnmappedChar     = 3,  # ConvertBuffer or Flush: stopped at unmapped character 

# additional warning status in 2.1, only returned if 2.1-specific options are used
    UsedReplacement  = 0x00000100, # ConvertBuffer or Flush: used default replacement character during mapping 

# negative values are errors
    InvalidForm          = -1,  # inForm or outForm parameter doesn't match mapping (bytes/Unicode mismatch) 
    ConverterBusy        = -2,  # can't initiate a conversion, as the converter is already in the midst of an operation 
    InvalidConverter     = -3,  # converter object is corrupted (or not really a TECkit_Converter at all) 
    InvalidMapping       = -4,  # compiled mapping data is not recognizable 
    BadMappingVersion    = -5,  # compiled mapping is not a version we can handle 
    Exception            = -6,  # an internal error has occurred 
    NameNotFound         = -7,  # couldn't find the requested name in the compiled mapping 
    IncompleteChar       = -8,  # bad input data (lone surrogate, incomplete UTF8 sequence) 
    CompilationFailed    = -9,  # mapping compilation failed (syntax errors, etc) 
    OutOfMemory          = -10) # unable to allocate required memory 

#
#  encoding form constants for TECkit_CreateConverter and TECkit_Compile
#

#EncodingFormMask = 0x000F
Form = ENUM('Unspecified',  # invalid as argument to TECkit_CreateConverter 
    'Bytes','UTF8',
    'UTF16BE','UTF16LE',
    'UTF32BE','UTF32LE')


class CompilationError(StandardError): pass
class ConverterBusy(RuntimeError): pass
class MappingVersionError(ValueError): pass
class FullBuffer(Exception): pass
class EmptyBuffer(Exception): pass

# Define some 'typedefs' these make the argtypes list slight less opaque.
converter = c_void_p
mapping   = POINTER(c_char)
nameid    = c_uint16
status    = c_long
c_bool    = c_ubyte



# ctypes errcheck function ensure nothing is wrong.
def status_code(s,f,args):
    if   s >= 0:
        w = s & StatusMask_Warning      # Not really sure how to handle warnings
        s = c_int8(s).value
        if   s == Status.NoError:          return args
        elif s == Status.OutputBufferFull: raise FullBuffer(*(v.value for v in args[3:4] + args[6:7] + args[8:9]))
        elif s == Status.NeedMoreInput:    raise EmptyBuffer(*(v.value for v in args[3:4] + args[6:7] + args[8:9]))
    elif s == Status.InvalidForm:      raise ValueError('inForm or outForm parameter does not match mapping: %r' % args[0])
    elif s == Status.ConverterBusy:    raise ConverterBusy('cannot initiate conversion: %r busy' % args[0])
    elif s == Status.InvalidConverter: raise TypeError('converter object is unrecongizable: %r' % args[0]) 
    elif s == Status.InvalidMapping:   raise TypeError('mapping data is unrecognizable: %r' % args[0]) 
    elif s == Status.BadMappingVersion:raise MappingVersionError('TECKit: cannot handle this mapping version')
    elif s == Status.Exception:        raise RuntimeError('TECkit: an internal error has occurred')
    elif s == Status.NameNotFound:     raise IndexError('TECkit: nameID index out of range')
    elif s == Status.IncompleteChar:   raise UnicodeDecodeError('bad UTF data (lone surrogate, incomplete UTF8 sequence)') 
    elif s == Status.CompilationFailed:raise CompilationError('mapping compilation failed')
    elif s == Status.OutOfMemory:      raise MemoryError('TECkit: allocation failed in: %r' % f)
    else: raise RuntimeError('unknown status code %s returned' % status)



def FLAGS(ctype, *flags):
    names = chain(['_reserved_'],('_reserved_%n_' % n for n in count(1)))
    
    class _BITS(Structure):
        _pack_ = 0
        _fields_ = [(n, ctype, 1) if isinstance(n,basestring) else (names.next(),ctype,len(n)) for n in flags]
    
    class _FLAGS(Union):
        _fields_    = [('bits', _BITS), ('value', ctype)]
        _anonymous_ = ('bits',)
    
        def __init__(self, *value,**bits):
            Union.__init__(self,**bits)
            if len(value) == 1:
                self.value = value[0]
        
        def __str__(self):
            return '(' + ' + '.join(fn[0] for fn in _BITS._fields_ if getattr(self,fn[0],False)) + ')'
        
        @property
        def _as_parameter_(self): return self.value
        
    return _FLAGS


def memoize(fn):
    from functools import wraps
    memo = {}
    @wraps(fn)
    def _decor(*args):
        try:
            return memo[args]
        except KeyError:
            memo[args] = val = fn(*args)
            return val
    return _decor

#
# Copyright (C) 2009 SIL International. All rights reserved.
#
# Provides python ctypes definitions and functions of the public API to 
# the TECkit conversion engine.
#
# Author: Tim Eves
#
# History:
#   10-Jun-2009     tse     Converted to python representationsm and 
#                            added ctypes function defintitions for the 
#                            public API.
# History of TECKit_Engine.h this is based on:
#   18-Jan-2008     jk      added EXPORTED to declarations, for mingw32 
#                            cross-build
#   18-Mar-2005     jk      moved version number to TECkit_Common.h as it
#                            is shared with the compiler
#   19-Mar-2004     jk      updated minor version for 2.2 engine
#                            (improved matching functionality)
#   23-Sep-2003     jk      updated for version 2.1 - new "...Opt" APIs
#    5-Jul-2002     jk      corrected placement of WINAPI to keep MS
#                            compiler happy
#   14-May-2002     jk      added WINAPI to function declarations
#   22-Dec-2001     jk      initial version

from ctypes import *
from ctypes.util import find_library
from _common import *
from itertools import chain, count
import platform, warnings

# formFlags bits for normalization; if none are set, then this side of the 
#  mapping is normalization-form-agnostic on input, and may generate an 
#  unspecified mixture 
flags = FLAGS(c_uint32,
            'expectsNFC',   # expects fully composed text (NFC) 
            'expectsNFD',   # expects fully decomposed text (NCD) 
            'generatesNFC', # generates fully composed text (NFC) 
            'generatesNFD', # generates fully decomposed text (NCD)
            [None]*11,      # 11 unused bits here
            'visualOrder',  # visual rather than logical order
            'unicode')      # this is Unicode rather than a byte encoding

NameID = ENUM(
# required names
    'lhsName',       # "source" or LHS encoding name, e.g. "SIL-EEG_URDU-2001"
    'rhsName',        # "destination" or RHS encoding name, e.g. "UNICODE-3-1"
    'lhsDescription', # source encoding description, e.g. "SIL East Eurasia Group Extended Urdu (Mac OS)"
    'rhsDescription', # destination description, e.g. "Unicode 3.1"
# additional recommended names (parallel to UTR-22)
    'version',        # "1.0b1"
    'contact',        # "mailto:jonathan_kew@sil.org"
    'regAuthority',   # "SIL International"
    'regName',        # "Greek (Galatia)"
    'copyright')       # "(c)2002 SIL International"
# additional name IDs may be defined in the future


#
#	encoding form options for TECkit_CreateConverter
#
Form_NormalizationMask = 0x0F00
Form = ENUM(Form,
    NFC = 0x0100,
    NFD = 0x0200)

#
#	end of text value for TECkit_DataSource functions to return
#
EndOfText = 0xffffffffL


# ctypes errcheck function ensure nothing is wrong with the ConvertXXX of Flush calls.
def _converter_status_code(s,f,args):
    if s < 0:   dispatch_error_status_code(s,f,args)
    _dispatch_warnings(s & StatusMask_Warning)
    s = c_int8(s).value
    if   s == Status.NoError:           return args
    elif s == Status.OutputBufferFull:  raise FullBuffer(*(v.value for v in args[3:4] + args[6:7] + args[8:9]))
    elif s == Status.NeedMoreInput:     raise EmptyBuffer(*(v.value for v in args[3:4] + args[6:7] + args[8:9]))
    elif s == Status.UnmappedChar:      raise UnmappedChar(*(v.value for v in args[3:4] + args[6:7] + args[8:9]))
    raise RuntimeError('unknown status code %s returned' % s)

def _dispatch_warnings(w):
    if w == Status.UsedReplacement:  
        warnings.warn('used default replacement character during mapping', 
                      UnicodeWarning, 
                      stacklevel=4)



# Load the library we use windll instead of cdll on Windows.
if platform.system() == "Windows" :
    arches = {'32bit' : 'x86', '64bit' : 'amd64'}
    arch = arches[platform.architecture[0]]
    libname = find_library('TECkit_' + arch)
    if libname is None :
        raise OSError("Unable to open TECkit_" + arch + ".dll")
    libteckit = windll.LoadLibrary(find_library('TECkit_' + platform.machine()))
    LOCALFUNCTYPE = WINFUNCTYPE
else :
    libteckit = cdll.LoadLibrary(find_library('TECkit'))
    LOCALFUNCTYPE = CFUNCTYPE

#
# Create a converter object from a compiled mapping and dispose of it
#
prototype = LOCALFUNCTYPE(status, mapping, c_size_t, c_bool, c_uint16, c_uint16, POINTER(converter))
paramflags = (1,'mapping'),(1,'mappingSize'),(1,'forward'),(1,'sourceForm'),(1,'targetForm'),(2,'converter')
createConverter = prototype(('TECkit_CreateConverter', libteckit), paramflags)
createConverter.errcheck = status_code

prototype = LOCALFUNCTYPE(status, converter)
paramflags = (1,'converter'),
disposeConverter = prototype(('TECkit_DisposeConverter', libteckit), paramflags)
disposeConverter.errcheck = status_code


#
# Read a name record or the flags from a converter object
#
prototype = LOCALFUNCTYPE(status, converter, nameid, c_char_p, c_size_t, POINTER(c_size_t))
paramflags = (1,'converter'),(1,'nameID'),(1,'nameBuffer',None),(1,'bufferSize',0),(2,'nameLength')
getConverterName = prototype(('TECkit_GetConverterName', libteckit), paramflags)
getConverterName.errcheck = status_code

prototype = LOCALFUNCTYPE(status, converter, POINTER(flags), POINTER(flags))
paramflags = (1,'converter'),(2,'sourceFlags'),(2,'targetFlags')
getConverterFlags = prototype(('TECkit_GetConverterFlags', libteckit), paramflags)
getConverterFlags.errcheck = status_code


#
# Reset a converter object, forgetting any buffered context/state
#
prototype = LOCALFUNCTYPE(status, converter)
paramflags = (1,'converter'),
resetConverter = prototype(('TECkit_ResetConverter',libteckit), paramflags)
resetConverter.errcheck = status_code


#
# Convert text from a buffer in memory
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t, POINTER(c_size_t),c_char_p, c_size_t, POINTER(c_size_t), c_bool)
paramflags = (1,'converter'),(1,'inBuffer'),(1,'inLength'),(2,'inUsed'),(1,'outBuffer'),(1,'outLength'),(2,'outUsed'),(1,'inputIsComplete',False)
convertBuffer = prototype(('TECkit_ConvertBuffer',libteckit),paramflags)
convertBuffer.errcheck = _converter_status_code

#
# Flush any buffered text from a converter object
# (at end of input, if inputIsComplete flag not set for ConvertBuffer)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t, POINTER(c_size_t))
paramflags = (1,'converter'),(1,'outBuffer'),(1,'outLength'),(2,'outUsed')
flush = prototype(('TECkit_Flush',libteckit),paramflags)
flush.errcheck = _converter_status_code

#
# Read name and flags directly from a compiled mapping, before making a converter object
#
prototype = LOCALFUNCTYPE(status, mapping, c_size_t, nameid, c_char_p, c_size_t, POINTER(c_size_t))
paramflags = (1,'mapping'),(1,'mappingSize'),(1,'nameID'),(1,'nameBuffer',None),(1,'bufferSize',0),(2,'nameLength')
getMappingName = prototype(('TECkit_GetMappingName',libteckit),paramflags)
getMappingName.errcheck = status_code

prototype = LOCALFUNCTYPE(status, mapping, c_size_t, POINTER(flags), POINTER(flags))
paramflags = (1,'mapping'),(1,'mappingSize'),(2,'lhsFlags'),(2,'rhsFlags')
getMappingFlags = prototype(('TECkit_GetMappingFlags', libteckit), paramflags)
getMappingFlags.errcheck = status_code


#
# Return the version number of the TECkit library
#
prototype = LOCALFUNCTYPE(c_uint32)
getVersion = prototype(('TECkit_GetVersion', libteckit))

#
#   ***** New APIs for version 2.1 of the engine *****
#
#   A converter object now has options to control behavior when "unmappable" characters
#   occur in the input text.
#   Choices are:
#       UseReplacementCharSilently
#           - original behavior, just uses "replacement character" in the mapping
#       UseReplacementCharWithWarning
#           - do the same mapping, but return a warning in the status value
#       DontUseReplacementChar
#           - stop conversion, returning immediately on encountering an unmapped character
#

OptionsMask_UnmappedBehavior = 0x000F
OptionsMask_InputComplete = 0x0100
Option = ENUM(
    UseReplacementCharSilently=0,
    UseReplacementCharWithWarning=1,
    DontUseReplacementChar=2,
    InputIsComplete=0x100)

#
# Convert text from a buffer in memory, with options
# (note that former inputIsComplete flag is now a bit in the options parameter)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t, POINTER(c_size_t),c_char_p, c_size_t, POINTER(c_size_t), c_uint32, POINTER(c_size_t))
paramflags = (1,'converter'),(1,'inBuffer'),(1,'inLength'),(2,'inUsed'),(1,'outBuffer'),(1,'outLength'),(2,'outUsed'),(1,'inOptions'),(2,'lookaheadCount')
convertBufferOpt = prototype(('TECkit_ConvertBufferOpt',libteckit),paramflags)
convertBufferOpt.errcheck = _converter_status_code

#
# Flush any buffered text from a converter object, with options
# (at end of input, if inputIsComplete flag not set for ConvertBuffer)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t, POINTER(c_size_t), c_uint32, POINTER(c_size_t))
paramflags = (1,'converter'),(1,'outBuffer'),(1,'outLength'),(2,'outUsed'),(1,'inOptions'),(2,'lookaheadCount')
flushOpt = prototype(('TECkit_FlushOpt',libteckit),paramflags)
flushOpt.errcheck = _converter_status_code


"""
TECkit library C API for python.

Provides python ctypes definitions and functions for the public API to
the TECkit conversion engine.
"""
__author__ = "Tim Eves"
__date__ = "23 January 2020"
__credits__ = '''\
Jonathon Kew for TECKit_Engine.h this is based on.
'''
__copyright__ = "Copyright © 2020 SIL International"
__license__ = "MIT"
__email__ = "tim_eves@sil.org"
# History:
# 20-Jan-2020 tse   Converted to python3 and replaced custom flag enum meta
#                   classes with std lib versions. Added type hints.
# 10-Jun-2009 tse   Created ctypes function defintitions for the public API.

import warnings
from typing import Any, List, Tuple, cast
from enum import IntEnum, IntFlag, auto, unique
from ctypes import (
    POINTER,
    c_bool, c_uint16, c_uint32, c_size_t,
    c_char_p, c_void_p)
from palaso.teckit._common import (
    EmptyBuffer, FullBuffer, UnmappedChar,
    LOCALFUNCTYPE, Status, mapping, status,
    dispatch_error_status_code, load_teckit_library, status_code)

flags = c_uint32
"""C type of flags enum"""

nameid = c_uint16
"""C type of NameID enum"""


@unique
class Flags(IntFlag):
    """formFlags bits for normalization

    if none are set, then this side of the
    mapping is normalization-form-agnostic on input, and may generate an
    unspecified mixture.
    """
    none = 0

    expectsNFC = auto()
    """expects fully composed text (NFC)."""

    expectsNFD = auto()
    """expects fully decomposed text (NCD)."""

    generatesNFC = auto()
    """generates fully composed text (NFC)."""

    generatesNFD = auto()
    """generates fully decomposed text (NCD)."""

    visualOrder = generatesNFD << 12  # 11 unused bits here
    """visual rather than logical order."""

    unicode = auto()
    """this is Unicode rather than a byte encoding."""


@unique
class NameID(IntEnum):
    """Permited names stored in a TECKit mapping.

    These are the onlny permissable values for the nameid value passed to
    TECkit_GetMappingName() or TECkit_GetConverterName().

    Additional name IDs may be defined in the future.
    """

    lhsName = 0
    '''"source" or LHS encoding name, e.g. "SIL-EEG_URDU-2001"'''

    rhsName = auto()
    '''"destination" or RHS encoding name, e.g. "UNICODE-3-1"'''

    lhsDescription = auto()
    '''source encoding description, e.g. "SIL East Eurasia Group Extended Urdu
    (Mac OS)"'''

    rhsDescription = auto()
    '''destination description, e.g. "Unicode 3.1"'''

    # additional recommended names (parallel to UTR-22)
    version = auto()
    '''version of the mapping e.g. 1.0b1'''

    contact = auto()
    '''e.g. mailto:jonathan_kew@sil.org'''

    regAuthority = auto()
    '''e.g. "SIL International"'''

    regName = auto()
    '''e.g. "Greek (Galatia)"'''

    copyright = auto()
    '''Copyright notice'''


#
# end of text value for TECkit_DataSource functions to return
#
EndOfText = 0xffffffff

__library__ = load_teckit_library()


# ctypes errcheck function ensure nothing is wrong with the ConvertXXX of
# Flush calls.
def _converter_status_code(s_: status,
                           f,
                           args: List[Any]) -> List[Any]:
    s = cast(Status, s_)
    if s < 0:
        dispatch_error_status_code(s, f, args)
    _dispatch_warnings(s)
    s = cast(Status, s & Status.BasicMask)
    params = args[3:4] + args[6:7] + args[8:9]
    if s == Status.NoError:
        return args
    elif s == Status.OutputBufferFull:
        raise FullBuffer(*(v.value for v in params))
    elif s == Status.NeedMoreInput:
        raise EmptyBuffer(*(v.value for v in params))
    elif s == Status.UnmappedChar:
        raise UnmappedChar(*(v.value for v in params))
    raise RuntimeError(f'unknown status code {s} returned')


def _flush_status_code(s_: status,
                       f,
                       args: List[Any]) -> List[Any]:
    s = cast(Status, s_)
    if s < 0:
        dispatch_error_status_code(s, f, args)
    _dispatch_warnings(s)
    s = cast(Status, s & Status.BasicMask)
    params = args[3:4] + args[5:6]
    if s == Status.NoError:
        return args
    elif s == Status.OutputBufferFull:
        raise FullBuffer(*(v.value for v in params))
    elif s == Status.NeedMoreInput:
        raise EmptyBuffer(*(v.value for v in params))
    elif s == Status.UnmappedChar:
        raise UnmappedChar(*(v.value for v in params))
    raise RuntimeError(f'unknown status code {s} returned')


def _dispatch_warnings(w: Status):
    if w == Status.UsedReplacement:
        warnings.warn('used default replacement character during mapping',
                      UnicodeWarning,
                      stacklevel=4)


converter = c_void_p

paramflags: Tuple = ()

#
# Create a converter object from a compiled mapping and dispose of it
#
prototype = LOCALFUNCTYPE(status, mapping, c_size_t, c_bool, c_uint16,
                          c_uint16, POINTER(converter))
paramflags = ((1, 'mapping'), (1, 'mappingSize'), (1, 'forward'),
              (1, 'sourceForm'), (1, 'targetForm'), (2, 'converter'))
createConverter = prototype(('TECkit_CreateConverter', __library__),
                            paramflags)
createConverter.errcheck = status_code

prototype = LOCALFUNCTYPE(status, converter)
paramflags = (1, 'converter'),
disposeConverter = prototype(('TECkit_DisposeConverter', __library__),
                             paramflags)
disposeConverter.errcheck = status_code


#
# Read a name record or the flags from a converter object
#
prototype = LOCALFUNCTYPE(status, converter, nameid, c_char_p, c_size_t,
                          POINTER(c_size_t))
paramflags = ((1, 'converter'), (1, 'nameID'), (1, 'nameBuffer', None),
              (1, 'bufferSize', 0), (2, 'nameLength'))
getConverterName = prototype(('TECkit_GetConverterName', __library__),
                             paramflags)
getConverterName.errcheck = status_code

prototype = LOCALFUNCTYPE(status, converter, POINTER(flags), POINTER(flags))
paramflags = (1, 'converter'), (2, 'sourceFlags'), (2, 'targetFlags')
getConverterFlags = prototype(('TECkit_GetConverterFlags', __library__),
                              paramflags)
getConverterFlags.errcheck = status_code


#
# Reset a converter object, forgetting any buffered context/state
#
prototype = LOCALFUNCTYPE(status, converter)
paramflags = (1, 'converter'),
resetConverter = prototype(('TECkit_ResetConverter', __library__), paramflags)
resetConverter.errcheck = status_code


#
# Convert text from a buffer in memory
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t,
                          POINTER(c_size_t), c_char_p, c_size_t,
                          POINTER(c_size_t), c_bool)
paramflags = ((1, 'converter'), (1, 'inBuffer'), (1, 'inLength'),
              (2, 'inUsed'), (1, 'outBuffer'), (1, 'outLength'),
              (2, 'outUsed'), (1, 'inputIsComplete', False))
convertBuffer = prototype(('TECkit_ConvertBuffer', __library__), paramflags)
convertBuffer.errcheck = _converter_status_code

#
# Flush any buffered text from a converter object
# (at end of input, if inputIsComplete flag not set for ConvertBuffer)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t,
                          POINTER(c_size_t))
paramflags = ((1, 'converter'), (1, 'outBuffer'), (1, 'outLength'),
              (2, 'outUsed'))
flush = prototype(('TECkit_Flush', __library__), paramflags)
flush.errcheck = _flush_status_code

#
# Read name and flags directly from a compiled mapping, before making a
# converter object.
#
prototype = LOCALFUNCTYPE(status, mapping, c_size_t, nameid, c_char_p,
                          c_size_t, POINTER(c_size_t))
paramflags = ((1, 'mapping'), (1, 'mappingSize'), (1, 'nameID'),
              (1, 'nameBuffer', None), (1, 'bufferSize', 0), (2, 'nameLength'))
getMappingName = prototype(('TECkit_GetMappingName', __library__), paramflags)
getMappingName.errcheck = status_code

prototype = LOCALFUNCTYPE(status, mapping, c_size_t, POINTER(flags),
                          POINTER(flags))
paramflags = ((1, 'mapping'), (1, 'mappingSize'),
              (2, 'lhsFlags'), (2, 'rhsFlags'))
getMappingFlags = prototype(('TECkit_GetMappingFlags', __library__),
                            paramflags)
getMappingFlags.errcheck = status_code


#
# Return the version number of the TECkit library
#
prototype = LOCALFUNCTYPE(c_uint32)
getVersion = prototype(('TECkit_GetVersion', __library__))


#
#   ***** New APIs for version 2.1 of the engine *****
#
@unique
class Option(IntFlag):
    """How to handle an unmappable character.

    Control converter behavior when "unmappable" characters occur in the
    input text.
    """

    UseReplacementCharSilently = 0
    """Default behavior, just uses "replacement character" in the mapping."""

    UseReplacementCharWithWarning = 1
    """Same as UseReplacementCharSilently, but return a warning status."""

    DontUseReplacementChar = 2
    """stop conversion, returning immediately."""

    InputIsComplete = 0x100
    """Dont operating in streaming mode."""

    UnmappedBehavior = 0x000F


#
# Convert text from a buffer in memory, with options
# (note that former inputIsComplete flag is now a bit in the options parameter)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t,
                          POINTER(c_size_t), c_char_p, c_size_t,
                          POINTER(c_size_t), c_uint32, POINTER(c_size_t))
paramflags = ((1, 'converter'), (1, 'inBuffer'), (1, 'inLength'),
              (2, 'inUsed'), (1, 'outBuffer'), (1, 'outLength'),
              (2, 'outUsed'), (1, 'inOptions'), (2, 'lookaheadCount'))
convertBufferOpt = prototype(('TECkit_ConvertBufferOpt', __library__),
                             paramflags)
convertBufferOpt.errcheck = _converter_status_code

#
# Flush any buffered text from a converter object, with options
# (at end of input, if inputIsComplete flag not set for ConvertBuffer)
#
prototype = LOCALFUNCTYPE(status, converter, c_char_p, c_size_t,
                          POINTER(c_size_t), c_uint32, POINTER(c_size_t))
paramflags = ((1, 'converter'), (1, 'outBuffer'), (1, 'outLength'),
              (2, 'outUsed'), (1, 'inOptions'), (2, 'lookaheadCount'))
flushOpt = prototype(('TECkit_FlushOpt', __library__), paramflags)
flushOpt.errcheck = _flush_status_code

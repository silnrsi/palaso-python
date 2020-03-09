"""
Common implmentation functions and variables for TECKit python API.

Provides python definitions of the common types and defines for the
engine and compiler.
"""
__author__ = "Tim Eves"
__date__ = "23 January 2020"
__credits__ = '''\
Jonathon Kew for TECkit_Common.h this is based on.
'''
__copyright__ = "Copyright © 2020 SIL International"
__license__ = "MIT"
__email__ = "tim_eves@sil.org"
# History:
# 20-Jan-2020     tse     Converted to python3 and replaced custom flag and
#                         enum meta classes with std lib versions. Added
#                         type hints.
# 10-Jun-2009     tse     Created ctypes bindings and added the status_check
#                         function for the ctypes errcheck protocol.

import ctypes.util
import platform

from typing import List, Callable
from enum import IntFlag, unique
from ctypes import c_char_p, c_long

LOCALFUNCTYPE: Callable = (ctypes.WINFUNCTYPE if platform.system() == "Windows"
                           else ctypes.CFUNCTYPE)


def load_teckit_library(component: str = ''):
    libname = f'TECkit{component and "_"+component}'
    libloader = ctypes.cdll

    if platform.system() == "Windows":
        # Load the library we use windll instead of cdll on Windows.
        arches = {'32bit': '_x86', '64bit': '_amd64'}
        arch = arches[platform.architecture()[0]]
        libname += arch
        libloader = ctypes.windll

    libpath = ctypes.util.find_library(libname)
    if libpath is None:
        raise OSError(f'Unable to find library: {libname}')

    return libloader.LoadLibrary(libpath)


@unique
class Status(IntFlag):
    NoError = 0
    BasicMask = 0x000000FF

# positive values are informational status values
    OutputBufferFull = 1
    # ConvertBuffer or Flush: output buffer full, so not all input was
    # processed.

    NeedMoreInput = 2
    # ConvertBuffer: processed all input data, ready for next chunk.

# only returned in version 2.1 or later, with DontUseReplacementChar option.
    UnmappedChar = 3
    # ConvertBuffer or Flush: stopped at unmapped character

    WarningMask = 0x0000FF00
# additional warning status in 2.1, only returned if 2.1-specific options are
# used.
    UsedReplacement = 0x00000100
    # ConvertBuffer or Flush: used default replacement character during
    # mapping.

# negative values are errors
    InvalidForm = -1
    # inForm or outForm parameter doesn't match mapping
    # bytes/Unicode mismatch).

    ConverterBusy = -2
    # can't initiate a conversion, as the converter is already in the midst of
    # an operation.

    InvalidConverter = -3
    # converter object is corrupted (or not really a TECkit_Converter at all).

    InvalidMapping = -4
    # compiled mapping data is not recognizable

    BadMappingVersion = -5
    # compiled mapping is not a version we can handle

    Exception = -6
    # an internal error has occurred

    NameNotFound = -7
    # couldn't find the requested name in the compiled mapping

    IncompleteChar = -8
    # bad input data (lone surrogate, incomplete UTF8 sequence)_FuncPointer

    CompilationFailed = -9
    # mapping compilation failed (syntax errors, etc)

    OutOfMemory = -10
    # unable to allocate required memory


#
#  encoding form constants for TECkit_CreateConverterOpt and TECkit_CompileOpt
#
class Form(IntFlag):
    EncodingMask = 0x000F
    Unspecified = 0  # invalid as argument to TECkit_CreateConverter
    Bytes = 1
    UTF8 = 2
    UTF16BE = 3
    UTF16LE = 4
    UTF32BE = 5
    UTF32LE = 6
    NormalizationMask = 0x0F00
    NFC = 0x0100
    NFD = 0x0200


class CompilationError(Exception):
    pass


class ConverterBusy(RuntimeError):
    pass


class MappingVersionError(ValueError):
    pass


class FullBuffer(Exception):
    pass


class EmptyBuffer(Exception):
    pass


class UnmappedChar(Exception):
    pass


# Define some 'typedefs' these make the argtypes list slight less opaque.
mapping = c_char_p
status = c_long


def dispatch_error_status_code(s: Status, fn, args: List):
    if s == Status.InvalidForm:
        raise ValueError(
            f'inForm or outForm parameter does not match mapping: {args[0]!r}')
    elif s == Status.ConverterBusy:
        raise ConverterBusy(f'cannot initiate conversion: {args[0]!r} busy')
    elif s == Status.InvalidConverter:
        raise TypeError(f'converter object is unrecongizable: {args[0]!r}')
    elif s == Status.InvalidMapping:
        raise TypeError(f'mapping data is unrecognizable: {args[0]!r}')
    elif s == Status.BadMappingVersion:
        raise MappingVersionError('TECKit: cannot handle this mapping version')
    elif s == Status.Exception:
        raise RuntimeError('TECkit: an internal error has occurred')
    elif s == Status.NameNotFound:
        raise IndexError('TECkit: nameID index out of range')
    elif s == Status.IncompleteChar:
        raise UnicodeError(
            'bad UTF data (lone surrogate, incomplete UTF8 sequence)')
    elif s == Status.CompilationFailed:
        raise CompilationError('mapping compilation failed')
    elif s == Status.OutOfMemory:
        raise MemoryError(f'TECkit: allocation failed in: {fn!r}')
    raise RuntimeError(f'unknown status code {s} returned')


def status_code(s_: status, fn, args: List) -> List:
    s = Status(s_)
    if s < Status.NoError:
        dispatch_error_status_code(s, fn, args)
    s = s & Status.BasicMask
    if s == Status.NoError:
        return args
    raise RuntimeError(f'unknown status code {s_} returned')

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
import ctypes.util
import platform

from typing import Any, Callable, List, cast
from enum import IntEnum, auto, unique
from ctypes import POINTER, c_char, c_long, c_ubyte

currentTECKitVersion: int = 0x00020004   # 16.16 version number

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
class Status(IntEnum):
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
#  encoding form constants for TECkit_CreateConverter and TECkit_Compile
#
# EncodingFormMask = 0x000F
class Form(IntEnum):
    EncodingMask = 0x000F
    Unspecified = 0  # invalid as argument to TECkit_CreateConverter
    Bytes = auto()
    UTF8 = auto()
    UTF16BE = auto()
    UTF16LE = auto()
    UTF32BE = auto()
    UTF32LE = auto()
    NormalizationMask = 0x0F00
    NFC = 0x0100
    NFD = 0x0200


class CompilationError(SyntaxError):
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
mapping = POINTER(c_char)
status = c_long
c_bool = c_ubyte


def dispatch_error_status_code(s: Status, fn, args: List[Any]):
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
    s = cast(Status, s_)
    if s < Status.NoError:
        dispatch_error_status_code(s, fn, args)
    s = cast(Status, s & Status.BasicMask)
    if s == Status.NoError:
        return args
    raise RuntimeError(f'unknown status code {s_} returned')

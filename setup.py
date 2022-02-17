#!/usr/bin/env python3
from contextlib import contextmanager
import platform
import sys
from glob import glob
from pathlib import Path
from setuptools import setup


@contextmanager
def strip_suffix(suffix, paths):
    if platform.system() == "Windows":
        yield [str(s) for s in paths]
    else:
        unsuffixed = [s.with_suffix('') for s in paths if s.suffix == suffix]
        for s in unsuffixed:
            s.with_suffix(suffix).rename(s)
        yield [str(s) for s in unsuffixed]
        for s in unsuffixed:
            s.rename(s.with_suffix(suffix))


scripts = {s for s in Path('scripts').glob('*/*') if s.is_file()}
# Exclude testusfm for now: it's a debugging tool
scripts -= {Path('scripts/sfm/testusfm.py')}

try:
    from Cython.Build import cythonize
    from setuptools import Extension
    ext = cythonize([Extension("palaso.kmfl",
                     ["lib/palaso.kmfl.pyx"],
                     libraries=["kmfl", "kmflcomp"])])
except ImportError:
    print("No Cython found: not building keyman support", sys.stderr)
    ext = []
    kmn = Path('scripts/kmn')
    scripts -= {kmn / p for p in ('keymancoverage.py',
                                  'kmfltestkeys.py',
                                  'kmn2c.py',
                                  'kmn2klc.py',
                                  'kmn2ldml.py',
                                  'kmn2xml.py',
                                  'kmnxml2svg.py')}

with strip_suffix('.py', scripts) as scripts:
    setup(
        ext_modules=ext,
        scripts=scripts)

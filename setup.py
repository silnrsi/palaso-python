#!/usr/bin/env python3
import cmd
import platform
import sys
from glob import glob
from pathlib import Path
from setuptools import setup

scripts = {s for s in Path('scripts').glob('*/*') if s.is_file()}
# Exclude testusfm for now: it's a debugging tool
scripts -= {Path('scripts/sfm/testusfm')}

try:
    from Cython.Build import cythonize
    from setuptools import Extension
    ext = cythonize([Extension("palaso.kmfl",
                     ["lib/palaso.kmfl.pyx"],
                     libraries=["kmfl", "kmflcomp"])])
except ImportError:
    print("No Cython found: not building keyman support", sys.stderr)
    ext = []
    scripts -= {Path('scripts/kmn/keymancoverage'),
                Path('scripts/kmn/kmfltestkeys'),
                Path('scripts/kmn/kmn2c'),
                Path('scripts/kmn/kmn2klc'),
                Path('scripts/kmn/kmn2ldml'),
                Path('scripts/kmn/kmn2xml'),
                Path('scripts/kmn/kmnxml2svg')}

scripts = list(scripts)
print(scripts)

if platform.system() == "Windows":
    cmd_scripts = [s for s in scripts if s.suffix != '.py']
    py_scripts = [s.with_suffix('.py') for s in cmd_scripts]
    for o,t in zip(cmd_scripts, py_scripts):
        o.rename(t)
    scripts = py_scripts

setup(
    #   ext_modules=ext,
    scripts=[str(s) for s in scripts])

if platform.system() == "Windows":
    for o,p in zip(cmd_scripts, py_scripts):
        p.rename(o)


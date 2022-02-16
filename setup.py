#!/usr/bin/env python3
from setuptools import setup
scripts = {s for s in glob('scripts/*/*') if s.rfind('.') == -1}
# Exclude testusfm for now: it's a debugging tool
scripts -= {'scripts/sfm/testusfm'}

try:
    from Cython.Build import cythonize
    from setuptools import Extension
    ext = cythonize([Extension("palaso.kmfl",
                     ["lib/palaso.kmfl.pyx"],
                     libraries=["kmfl", "kmflcomp"])])
except ImportError:
    print("No Cython found: not building keyman support", sys.stderr)
    ext = []
    scripts -= {'scripts/kmn/keymancoverage',
                'scripts/kmn/kmfltestkeys',
                'scripts/kmn/kmn2c',
                'scripts/kmn/kmn2klc',
                'scripts/kmn/kmn2ldml',
                'scripts/kmn/kmn2xml',
                'scripts/kmn/kmnxml2svg'}

setup(
    #   ext_modules=ext,
          scripts=list(scripts)

      )

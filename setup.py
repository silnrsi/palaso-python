#!/usr/bin/env python3
from setuptools import setup
scripts = {s for s in glob('scripts/*/*') if s.rfind('.') == -1}
# Exclude testusfm for now: it's a debugging tool
scripts -= {'scripts/sfm/testusfm'}


setup(
    #   ext_modules=ext,
          scripts=list(scripts)

      )

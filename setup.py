#!/usr/bin/env python3
import sys
from setuptools import setup
from glob import glob

packages = ['palaso',
            'palaso.collation',
            'palaso.font',
            'palaso.kmn',
            'palaso.sfm',
            'palaso.sldr',
            'palaso.teckit',
            'palaso.text',
            'palaso.unicode']

scripts = {s for s in glob('scripts/*/*') if s.rfind('.') == -1}
# Exclude testusfm for now: it's a debugging tool
scripts -= {'scripts/sfm/testusfm'}

try:
    from Pyrex.Distutils.extension import Extension  # type: ignore
    from Pyrex.Distutils import build_ext            # type: ignore
    ext = [Extension("palaso.kmfl",
                     ["lib/palaso.kmfl.pyx"],
                     libraries=["kmfl", "kmflcomp"])]
    cmd = {'build_ext': build_ext}
except ImportError:
    print("No Pyrex found: not building keyman support", sys.stderr)
    ext = []
    cmd = {}
    scripts -= {'scripts/kmn/keymancoverage',
                'scripts/kmn/kmfltestkeys',
                'scripts/kmn/kmn2c',
                'scripts/kmn/kmn2klc',
                'scripts/kmn/kmn2ldml',
                'scripts/kmn/kmn2xml',
                'scripts/kmn/kmnxml2svg'}

setup(name='palaso',
      version='0.7.6',
      description='Payap Language Software python package and scripts',
      long_description="""Modules and scripts useful for building language
                          software.""",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://github.com/silnrsi/palaso-python',
      packages=packages,
      ext_modules=ext,
      scripts=list(scripts),
      license='LGPL',
      platforms=['Linux', 'Win32', 'Mac OS X'],
      package_dir={'': 'lib'},
      package_data={'palaso.collation': ['sort_trainer.glade'],
                    'palaso.kmn': ['keyboard.svg'],
                    'palaso.sfm': ['usfm.sty'],
                    'palaso.sldr': ['allkeys.txt',
                                    'language-subtag-registry.txt',
                                    'ldml.dtd',
                                    'likelySubtags.xml',
                                    'supplementalData.xml',
                                    'supplementalMetadata.xml'],
                    'palaso.unicode': ['ucdata_pickle.bz2'],
                    'palaso': ['langtags.json']}
      )

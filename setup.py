#!/usr/bin/env python

from setuptools import setup
from glob import glob

packages = ['palaso',
            'palaso.collation',
            'palaso.contrib',
            'palaso.contrib.freetype',
            'palaso.contrib.freetype.ft_enums',
            'palaso.contrib.funcparserlib',
            'palaso.font',
            'palaso.kmn',
            'palaso.sfm',
            'palaso.sldr',
            'palaso.teckit',
            'palaso.text',
            'palaso.unicode']

scripts = set(filter(lambda x: x.rfind(".") == -1, glob('scripts/*/*')))

try:
    from Pyrex.Distutils.extension import Extension
    from Pyrex.Distutils import build_ext
    ext = [Extension("palaso.kmfl", ["lib/palaso.kmfl.pyx"],
                     libraries=["kmfl", "kmflcomp"])]
    cmd = {'build_ext': build_ext}
except ImportError:
    print("No Pyrex!")
    ext = []
    cmd = {}
    scripts = scripts - set(['scripts/kmn/keymancoverage',
                             'scripts/kmn/kmfltestkeys',
                             'scripts/kmn/kmn2c',
                             'scripts/kmn/kmn2klc',
                             'scripts/kmn/kmn2ldml',
                             'scripts/kmn/kmn2xml',
                             'scripts/kmn/kmnxml2svg'])

setup(name='palaso',
      version='0.7.5',
      description='Payap Language Software python package and scripts',
      long_description="""Modules and scripts useful for building language
                          software.""",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://github.com/silnrsi/palaso-python',
      packages=packages,
      ext_modules=ext,
      cmdclass=cmd,
      scripts=scripts,
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

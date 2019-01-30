#!/usr/bin/env python

from setuptools import setup
from glob import glob
import platform, sys

packages=['palaso', 'palaso.collation', 'palaso.kmn', 'palaso.sfm', 
          'palaso.teckit', 'palaso.text', 'palaso.font', 'palaso.contrib',
          'palaso.contrib.freetype', 'palaso.contrib.freetype.ft_enums',
          'palaso.contrib.funcparserlib', 'palaso.unicode', 'palaso.sldr']
try:
    from Pyrex.Distutils.extension import Extension
    from Pyrex.Distutils import build_ext
    ext =[ Extension("palaso.kmfl", ["lib/palaso.kmfl.pyx"], libraries=["kmfl", "kmflcomp"]) ] 
    cmd = {'build_ext': build_ext}
    packages.insert(0, '')
except ImportError:
    print("No Pyrex!")
    ext = []
    cmd = {}

setup(name='palaso',
      version='0.7.4',
      description='Payap Language Software python package and scripts',
      long_description="Modules and scripts useful for building language software.",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://github.com/silnrsi/palaso-python',
      packages=packages,
      ext_modules = ext,
      cmdclass = cmd,
      scripts=list(filter(lambda x : x.rfind(".") == -1, glob('scripts/*/*'))),
      license='LGPL',
      platforms=['Linux','Win32','Mac OS X'],
      package_dir={'':'lib'},
      package_data={'palaso.sfm':['usfm.sty'], 'palaso.kmn':['keyboard.svg'], 
                    'palaso.collation' : ['sort_trainer.glade'],
                    'palaso.sldr': ['allkeys.txt', 'language-subtag-registry.txt',
                                    'likelySubtags.xml', 'supplementalData.xml',
                                    'supplementalMetadata.xml']}
     )


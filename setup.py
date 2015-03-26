#!/usr/bin/env python

from distutils.core import setup
from glob import glob
import platform, sys

if '--nokmn' in sys.argv:
    ext = []
    cmd = {}
    sys.argv.remove('--nokmn')
elif platform.system() == "Windows":
    ext = []
    cmd = {}
else :
    from Pyrex.Distutils.extension import Extension
    from Pyrex.Distutils import build_ext
    ext =[ Extension("palaso.kmfl", ["lib/palaso.kmfl.pyx"], libraries=["kmfl", "kmflcomp"]) ] 
    cmd = {'build_ext': build_ext}

setup(name='palaso',
      version='0.7.3',
      description='Payap Language Software python package and scripts',
      long_description="Modules and scripts useful for building language software.",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://projects.palaso.org/projects/show/palaso-python',
      packages=['', 'palaso', 'palaso.collation', 'palaso.kmn', 'palaso.sfm', 'palaso.teckit', 'palaso.text', 'palaso.font', 'palaso.contrib', 'palaso.contrib.freetype', 'palaso.contrib.freetype.ft_enums'],
      ext_modules = ext,
      cmdclass = cmd,
      scripts=filter(lambda x : x.rfind(".") == -1, glob('scripts/*/*')),
      license='LGPL',
      platforms=['Linux','Win32','Mac OS X'],
      package_dir={'':'lib'},
      package_data={'palaso.sfm':['usfm.sty'], 'palaso.kmn':['keyboard.svg'], 'palaso.collation' : ['sort_trainer.glade']}
     )


#!/usr/bin/env python

from distutils.core import setup
from glob import glob
from Pyrex.Distutils.extension import Extension
from Pyrex.Distutils import build_ext


setup(name='palaso',
      version='0.4.0b1',
      description='Payap Language Software python package and scripts',
      long_description="Modules and scripts useful for building language software.",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://projects.palaso.org/projects/show/palaso-python',
      packages=['', 'palaso', 'palaso.collation', 'palaso.kmn', 'palaso.sfm'],
      ext_modules = [
        Extension("palaso.kmfl", ["lib/palaso.kmfl.pyx"], libraries=["kmfl", "kmflcomp"])
        ],
      cmdclass = {'build_ext': build_ext},
      scripts=glob('scripts/*/*'),
      license='LGPL',
      platforms=['Linux','Win32','Mac OS X'],
      package_dir={'':'lib'}
     )


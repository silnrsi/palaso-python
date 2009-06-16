#!/usr/bin/env python

from distutils.core import setup
from glob import glob


setup(name='palaso',
      version='0.1.0a1',
      description='Payap Language Software python package and scripts',
      long_description="Modules and scripts useful for building language software.",
      maintainer='Tim Eves',
      maintainer_email='tim_eves@sil.org',
      url='http://projects.palaso.org/projects/show/palaso-python',
      packages=['', 'palaso', 'palaso.collation'],
      scripts=glob('scripts/*/*'),
      license='LGPL',
      platforms=['Linux','Win32','Mac OS X'],
      package_dir={'':'lib'}
     )


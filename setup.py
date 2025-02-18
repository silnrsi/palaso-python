from setuptools import setup, Extension
from Cython.Build import cythonize
from pathlib import Path

if Path("/usr/include/kmfl").exists():
    extensions = cythonize(
        [Extension(
            name="palaso.kmfl",
            sources=["src/palaso.kmfl.pyx"],
            libraries=["kmfl", "kmflcomp"]
        )]
    )
else: 
    extensions = []

setup(ext_modules=extensions)

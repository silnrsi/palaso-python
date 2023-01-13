from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        [Extension(
            name="palaso.kmfl",
            sources=["src/palaso.kmfl.pyx"],
            libraries=["kmfl", "kmflcomp"]
        )]
    )
)

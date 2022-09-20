from setuptools import setup

try:
    from Cython.Build import cythonize
    from setuptools import Extension
    ext = cythonize([
            Extension(
                name="palaso.kmfl",
                sources=["src/palaso.kmfl.pyx"],
                libraries=["kmfl", "kmflcomp"]
            )
        ])
except ImportError:
    import sys
    print("No Cython found: not building keyman support", sys.stderr)
    ext = []

setup(ext_modules=ext)

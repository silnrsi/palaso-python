import importlib.resources
import unittest

try:
    import palaso.teckit  # noqa
except OSError as err:
    raise unittest.SkipTest(*err.args) from err

pkg_data = importlib.resources.files(__name__) / 'data'

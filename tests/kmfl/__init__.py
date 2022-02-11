import importlib.util
import unittest

if (importlib.util.find_spec('palaso.kmfl') is None):
    raise unittest.SkipTest('palaso.kmfl python extension not available.')

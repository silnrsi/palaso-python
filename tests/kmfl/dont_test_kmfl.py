import unittest
from . import pkg_data
from importlib import resources
from palaso.kmfl import kmfl
from palaso.kmn import keysyms_items
from palaso.kmn.coverage import Coverage


class TestKmfl(unittest.TestCase) :
    def runtest(self, fname, keys, output) :
        with resources.as_file(pkg_data / fname) as path:
            k = kmfl(path)
        res = k.run_items(keysyms_items(keys))
        self.assertEqual(res, output, ("Keying difference for: {0}\n"
                                       "expected:\t{1!r}\n"
                                       "     got:\t{2!r}\n").format(keys,output,res))

    def runcoverage(self, fname, testfile) :
        with resources.as_file(pkg_data / fname) as path:
            x = Coverage(path)
        with (pkg_data / testfile).open(encoding='utf-8') as f:
            indata = [l.rstrip() for l in f.readlines()]

        res = list(x.coverage_test(mode = 'all'))
        self.assertEqual(res, indata, "coverage results are not the same")

    def test_kyu(self) :
        self.runtest("kyu-mymr.kmn", "aaiU", "\u1004\u1031\u1074")

    def test_coverage_kyu(self) :
        self.runcoverage("kyu-mymr.kmn", "kyu-mymr-coverage.txt")

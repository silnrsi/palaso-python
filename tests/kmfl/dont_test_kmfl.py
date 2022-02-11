#!/usr/bin/env python3
import unittest
from palaso.kmfl import kmfl
from palaso.kmn import keysyms_items
from palaso.kmn.coverage import Coverage


class TestKmfl(unittest.TestCase) :
    def runtest(self, fname, keys, output) :
        k = kmfl("kbds/" + fname)
        res = k.run_items(keysyms_items(keys))
        self.assertEqual(res, output, ("Keying difference for: {0}\n"
                                       "expected:\t{1!r}\n"
                                       "     got:\t{2!r}\n").format(keys,output,res))

    def runcoverage(self, fname, testfile) :
        x = Coverage("kbds/" + fname)
        inf = codecs.open(os.path.join('base', testfile), "r", "utf-8")
        indata = [l.rstrip() for l in inf.readlines()]
        inf.close
        res = list(x.coverage_test(mode = 'all'))
        self.assertEqual(res, indata, "coverage results are not the same")

    def test_kyu(self) :
        self.runtest("kyu-mymr.kmn", "aaiU", "\u1004\u1031\u1074")

    def test_coverage_kyu(self) :
        self.runcoverage("kyu-mymr.kmn", "kyu-mymr-coverage.txt")

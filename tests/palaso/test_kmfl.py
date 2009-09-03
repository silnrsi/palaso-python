import unittest, os, codecs
from palaso.kmfl import kmfl
from palaso.kmn.coverage import Coverage

class TestKmfl(unittest.TestCase) :
    def runtest(self, fname, keys, output) :
        k = kmfl("kbds/" + fname)
        res = k.run_string(keys)
        self.assertEqual(res, output, "Keying difference for: " + keys + " giving " + res)

    def runcoverage(self, fname, testfile) :
        x = Coverage("kbds/" + fname)
        inf = codecs.open(os.path.join('base', testfile), "r", "utf-8")
        indata = [l.rstrip() for l in inf.readlines()]
        inf.close
        res = [y for y in x.coverage_test(mode = 'first')]
        self.assertEqual(res, indata, "coverage results are not the same")

    def test_kyu(self) :
        self.runtest("kyu-mymr.kmn", "aiU", u"\u1004\u1031\u1074")

    def test_coverage_kyu(self) :
        self.runcoverage("kyu-mymr.kmn", "kyu-mymr-coverage.txt")

if __name__ == "__main__" :
    unittest.main()

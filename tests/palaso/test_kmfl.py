import unittest, os, codecs
from palaso.kmfl import kmfl

class TestKmfl(unittest.TestCase) :
    def runtest(self, fname, keys, output) :
        k = kmfl("kbds/" + fname)
        res = k.run_string(keys)
        self.assertEqual(res, output, "Keying difference for: " + keys + " giving " + res)

    def test_kyu(self) :
        self.runtest("kyu-mymr.kmn", "aiU", u"\u1004\u1031\u1074")

if __name__ == "__main__" :
    unittest.main()

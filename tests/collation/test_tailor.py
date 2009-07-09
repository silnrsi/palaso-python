import unittest, palaso, os
from palaso.collation import *
import xml.sax

class TestCollation(unittest.TestCase) :
    def sortldml(self, ldml, infile, alt='', depth=15) :
        inf = open(os.path.join('base', infile))
        indata = inf.readlines()
        handler = palaso.collation.tailor.LDMLHandler()
        ldmlparser = xml.sax.make_parser()
        ldmlparser.setContentHandler(handler)
        ldmlparser.setFeature(xml.sax.handler.feature_namespaces, 1)
        ldmlparser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
        ldmlparser.parse(os.path.join('data', ldml))
        collation = handler.collations[0]
        for c in handler.collations :
            if c.type == alt :
                collation = c
                break

        tailor = collation.asICU()
        outdata = palaso.collation.icu.sorted(tailor, indata, level = depth, preproc = collation.reorders)
        self.assertEqual(indata, outdata, "preprocessed lists do not sort equally")

        collation.flattenOrders()
        errors = collation.testPrimaryMultiple()
        self.failIf(len(errors), "\n".join("Reset had multiple elements: %s" % (f) for f in errors))
        tailor = collation.asICU()
        outdata = palaso.collation.icu.sorted(tailor, indata, level = depth)
        self.assertEqual(indata, outdata, "lists do not sort equally")
       
    def test_my(self) :
        self.sortldml('my-reg2.xml', 'my-reg1.txt')

    def test_kht(self) :
        self.sortldml('kht.xml', 'kht_words.txt')

if __name__ == "__main__" :
    unittest.main()

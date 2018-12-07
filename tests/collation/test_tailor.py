import unittest, palaso, os, codecs
from palaso.collation import *
import xml.sax

class TestCollation(unittest.TestCase) :
    def sortldml(self, ldml, infile, alt='', depth=15) :
        inf = codecs.open(os.path.join(os.path.dirname(__file__), 'base', infile), "r", "utf-8")
        indata = inf.readlines()
        inf.close()
        handler = palaso.collation.tailor.LDMLHandler()
        ldmlparser = xml.sax.make_parser()
        ldmlparser.setContentHandler(handler)
        ldmlparser.setFeature(xml.sax.handler.feature_namespaces, 1)
        ldmlparser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
        ldmlparser.parse(os.path.join(os.path.dirname(__file__), 'data', ldml))
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
        self.sortldml('my-reg1.xml', 'my-reg1.txt')

    def test_kht(self) :
        self.sortldml('kht.xml', 'kht_words.txt')

if __name__ == "__main__" :
    unittest.main()

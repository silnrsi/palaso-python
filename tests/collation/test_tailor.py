import unittest, palaso, os
from palaso.collation import *
import xml.sax

class TestCollation(unittest.TestCase) :
    def sortldml(self, ldml, infile, alt='', depth=15) :
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

        collation.flattenOrders()
        errors = collation.testPrimaryMultiple()
        self.failIf(len(errors), "\n".join("Reset had multiple elements: %s" % (f) for f in errors))
        tailor = collation.asICU()
        inf = open(os.path.join('base', infile))
        indata = inf.readlines()
        outdata = palaso.collation.icu.sorted(tailor, indata, depth)
        self.assertEqual(indata, outdata, "lists do not sort equally")
       
    def test_my(self) :
        self.sortldml('my-reg1.xml', 'my-reg1.txt')

if __name__ == "__main__" :
    unittest.main()

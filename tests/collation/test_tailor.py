import codecs
import os
import palaso.collation.icu
import palaso.collation.tailor
import unittest
from . import resources
from palaso.collation import *
import xml.sax


class TestCollation(unittest.TestCase) :
    def sortldml(self, ldml, infile, alt='', depth=15) :
        with resources.joinpath(infile).open(encoding='utf-8') as f:
            indata = f.readlines()
        handler = palaso.collation.tailor.LDMLHandler()
        ldmlparser = xml.sax.make_parser()
        ldmlparser.setContentHandler(handler)
        ldmlparser.setFeature(xml.sax.handler.feature_namespaces, 1)
        # ldmlparser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
        ldmlparser.parse(resources.joinpath(ldml))
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
        self.assertFalse(
            len(errors),
            "\n".join(f"Reset had multiple elements: {f!s}" for f in errors))
        tailor = collation.asICU()
        outdata = palaso.collation.icu.sorted(tailor, indata, level = depth)
        self.assertEqual(indata, outdata, "lists do not sort equally")

    # def test_my(self) :
    #    self.sortldml('my-reg1.xml', 'my-reg1.txt')

    # def test_kht(self) :
    #    self.sortldml('kht.xml', 'kht_words.txt')

#!/usr/bin/python

import unittest, sys, os
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from palaso.sldr.ldml import Ldml, draftratings
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lib')))
    from palaso.sldr.ldml import Ldml, draftratings, etwrite


class LDMLTests(unittest.TestCase):

    def setUp(self):
        self.tf = u'''<?xml version="1.0" encoding="utf-8"?>
<ldml xmlns:sil="urn://www.sil.org/ldml/0.1">
	<identity>
		<special>
			<!-- not very interesting -->
			<sil:identity uid="test1"/>
		</special>
	</identity>
	<characters>
		<exemplarCharacters>[d e f a u l t]</exemplarCharacters>
	</characters>
</ldml>'''
        tf = StringIO(self.tf)
        self.ldml = Ldml(tf)
        self.tpath ='characters/exemplarCharacters[@type=""]'
        self.tstring = "[" + " ".join("default") + "]"
        self.teststrs = dict((x, "[" + " ".join(x) + "]") for x in draftratings.keys())

    def tearDown(self):
        if '-v' in sys.argv:
            self.ldml.serialize_xml(sys.stdout.write)

    def test_exemplar_basic(self):
        teststr = self.teststrs['generated']
        e = self.ldml.ensure_path(self.tpath, draft="generated", matchdraft="draft")
        e[0].text = teststr
        x = self.ldml.ensure_path(self.tpath, draft="generated", matchdraft="draft")
        self.assertTrue(x[0].text == teststr)

    def test_exemplar_double(self):
        testdrafts = ('generated', 'suspect')
        testalts = {'generated': None, 'suspect': 'proposed2'}
        for t in testdrafts:
            e = self.ldml.ensure_path(self.tpath, draft=t, alt=testalts[t], matchdraft="draft")
            e[0].text = self.teststrs[t]
        for t in testdrafts:
            x = self.ldml.ensure_path(self.tpath, draft=t, matchdraft="draft")
            self.assertTrue(x[0].text == self.teststrs[t])

    def test_change_draft(self):
        b = self.ldml.ensure_path(self.tpath)[0]
        e = self.ldml.ensure_path(self.tpath, draft='generated', matchdraft='draft')[0]
        e.text = self.teststrs['generated']
        n = self.ldml.change_draft(b, 'suspect')
        b = self.ldml.ensure_path(self.tpath)[0]
        self.assertTrue(b.text == self.teststrs['generated'])
        self.assertTrue(id(b) == id(n))

    def test_change_draft2(self):
        b = self.ldml.ensure_path(self.tpath)[0]
        n = self.ldml.change_draft(b, 'suspect')
        e = self.ldml.ensure_path(self.tpath, draft='generated', matchdraft='draft')[0]
        e.text = self.teststrs['generated']
        b = self.ldml.ensure_path(self.tpath)[0]
        self.assertTrue(b.text == self.teststrs['generated'])
        self.assertTrue(id(b) == id(e))

    def test_ensure_text(self):
        """ Get an existing node """
        b = self.ldml.ensure_path(self.tpath, text=self.tstring, draft="generated")[0]
        self.assertTrue(b.get('draft', "") != "generated")

    def test_ensure_text2(self):
        """ Create a node and check we get it back """
        b = self.ldml.ensure_path("identity/special/fred", text="Hello World", draft="contributed")[0]
        n = self.ldml.ensure_path("identity/special/fred", text="Hello World", draft="generated")[0]
        self.assertTrue(n.get('draft', "") != "generated")

    def test_ensure_text3(self):
        """ Create a node and another once, checking we get a new node """
        b = self.ldml.ensure_path("identity/special/ensure_test3", text="Hello World", draft="contributed")
        n = self.ldml.ensure_path("identity/special/ensure_test3", text="test3", draft="generated", alt="pytest")[0]
        self.assertTrue(n.get('draft', "") == "generated")

    def test_ensure_text4(self):
        """ Create a node and check we can increase its draft """
        b = self.ldml.ensure_path("identity/special/fred", text="Hello World", draft="generated")[0]
        n = self.ldml.ensure_path("identity/special/fred", text="Hello World", draft="contributed")[0]
        self.assertTrue(n.get('draft', "") != "generated")

    def test_output(self):
        res = StringIO()
        self.ldml.serialize_xml(res.write)
        self.assertEqual(res.getvalue().strip(), self.tf)

if __name__ == '__main__':
    unittest.main()

import unittest, os.path, glob
import doctest 
from palaso.teckit import engine

#class TestConverter:
#    def setUp(self):
#        self.map = engine.Mapping(os.path.join('data',self.tec_file))
#        
#    def test_encode(self):
#        for (src,tgt) in self.tests:
#            self.assertEqual(engine.Converter(self.map,forward=True).convert(src,finished=True),
#                             tgt,"Table %r: encoding doesn't match reference" % self.tec_file)
#
#    def test_decode(self):
#        for (src,tgt) in self.tests:
#            self.assertEqual(engine.Converter(self.map,forward=False).convert(tgt,finished=True),
#                             src,"Table %r: decoding doesn't match reference" % self.tec_file)
#
#
#class TestEngineWithSILIPA93(TestConverter, unittest.TestCase):
#    tec_file = 'silipa93.tec'
#    tests    = [('D"\xe2s i\xf9z ?\xab tHEstH', u'\u00F0i\u0303s i\u02D0z \u0294\u0259 t\u02B0\u025Bst\u02B0')]
#
#    
#class TestEngineWithAcademy(TestConverter, unittest.TestCase):
#    tec_file = 'academy.tec'
#    tests    = [('upkdu|Gm:',u'\u1000\u1005\u102F\u102D\u1000\u101B\u1039\u101D\u102C\u1038')]

def test_main():
    suite = unittest.TestSuite(
        [doctest.DocFileTest('test_mapping.doctest', encoding='utf-8'),
         doctest.DocFileTest('test_engine_simple.doctest', encoding='utf-8'),
         unittest.defaultTestLoader.loadTestsFromName(__name__)])
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test_main()


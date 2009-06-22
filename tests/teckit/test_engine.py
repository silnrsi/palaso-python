import doctest
import unittest
import os.path
from palaso.teckit import engine

 
class TestEngine(unittest.TestCase):

    def convertTest(self, tec, tests):
        m = engine.Mapping(os.path.join('data',tec))
        enc = engine.Converter(m)
        dec = engine.Converter(m,forward=False)
        print 'Table %r' % str(m)
        for (src,tgt) in tests:
            res = enc.convert(src,finished=True)
            self.assertEqual(res,tgt,'unexpected encoding conversion result')
            res = dec.convert(tgt,finished=True)
            self.assertEqual(res,src,'unexpected decoding conversion result')

    def test_with_silipa93(self):
        self.convertTest('silipa93.tec', 
                         [('D"\xe2s i\xf9z ?\xab tHEstH', 
                           u'\u00F0i\u0303s i\u02D0z \u0294\u0259 t\u02B0\u025Bst\u02B0')])
    
    def test_with_academy(self):
        self.convertTest('academy.tec',
                         [('upkdu|Gm:',
                           u'\u1000\u1005\u102F\u102D\u1000\u101B\u1039\u101D\u102C\u1038')])


if __name__ == '__main__':
    suite = unittest.TestSuite(
            [doctest.DocFileTest('test_mapping.txt'), 
             unittest.TestLoader().loadTestsFromTestCase(TestEngine)])
    unittest.TextTestRunner(verbosity=2).run(suite)


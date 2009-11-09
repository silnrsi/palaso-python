'''
Created on Nov 2, 2009

@author: tim_eves@sil.org
'''
import unittest
import codecs, itertools, operator, warnings

from palaso import sfm
from palaso.sfm import event


class SFMTestCase(unittest.TestCase):
    def test_markers(self):
        marker_tests = {
            '\\test' : ['start{} test','end{} test'],
            '\\test text' : ['start{} test',"text{test} 'text'",'end{} test'],
            '\\test\\inline text\\inline*' : ['start{} test', 'start{test} inline', "text{inline} 'text'", 'end{test} inline', 'end{} test'],
            '\\test \\i1\\i2 deep\\i2* \\i1* ' : ['start{} test', 'start{test} i1', 'start{i1} i2', "text{i2} 'deep'", 'end{i1} i2', 'end{test} i1', 'end{} test'],
            } 
        
        for src,ref in marker_tests.items():
            self.assertEqual(map(str,sfm.parser(src)),ref)

    
    def test_text(self):
        self.assertEqual(map(str,sfm.parser('')),[])
        self.assertEqual(map(str,sfm.parser('text with no markers')),
                         ["text{} 'text with no markers'"])
    

    def test_mixed(self):
        self.assertEqual(map(str,sfm.parser('\\sfm text\n'
                                            'bare text\n'
                                            '\\more-sfm more text\n')),
                         ['start{} sfm',"text{sfm} 'text'",'end{} sfm',
                          "text{} 'bare text'",
                          'start{} more-sfm',"text{more-sfm} 'more text'",'end{} more-sfm'])

    
    def test_line_ends(self):
        self.assertEqual(map(str,sfm.parser(['\\le unix\n',
                                             '\\le windows\r\n',
                                             '\\le missing'])),
                         ['start{} le',"text{le} 'unix'",'end{} le',
                          'start{} le',"text{le} 'windows'",'end{} le',
                          'start{} le',"text{le} 'missing'",'end{} le'])
        

    def test_position(self):
        p=sfm.parser('\\li1 text\n\\l2\n\\l3\n')
        self.assertEqual([tuple(p.pos) for _ in p],
                         [(1,1),(1,6),(1,10),    # \li1 text
                          (2,1),(2,4),          # \l2
                          (3,1),(3,4)])          # \l3
        

    def test_sytax_error(self):
        self.assertRaises(SyntaxError,list,sfm.parser('\\test \\i2 deep text\\i2* \\i1*'))
    
    
    def test_sytax_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", sfm.SyntaxWarning)
            self.assertRaises(sfm.SyntaxWarning,list,sfm.parser('\\test \\i1\\i2 deep text\\i1*'))
            self.assertRaises(sfm.SyntaxWarning,list,sfm.parser('\\test \\i1\\i2 deep text'))
            self.assertRaises(sfm.SyntaxWarning,list,sfm.parser('normal text \\evil-inline more text'))
        
    
    def test_transduction(self):
        src = ['\\test\n',
               '\\test text\n',
               '\\sfm text\n',
               'bare text\n',
               '\\more-sfm more text\n',
               '\\le unix\n',
               # These forms do not transduce identically due to whitespace differences
               '\\test\\inline text\\inline*\n',
               '\\test \\i1\\i2 deep\\i2* \\i1* \n',
               '\\le windows\r\n',
               '\\le missing\n',
               # These forms produce syntactic warnings but parse
               '\\test \\i1\\i2 deep text\\i1*\n',
               '\\test \\i1\\i2 deep text\n']
        
        with warnings.catch_warnings(record=True) as ref_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", sfm.SyntaxWarning)
            ref = list(sfm.parser(src))
        trans = sfm.handler()
        trans_src = list(sfm.transduce(trans, src))

        # Check known straight through transductions.
        self.assertEqual(trans_src[:6], src[:6])
        # Check the errors match 
        for ref_err,trans_err in zip(ref_parse_errors,trans.errors):
            self.assertEqual(str(ref_err),str(trans_err))
        # Check the rest but do not ignore syntax warnings as there should be none
        # produced by parser the transduced output.
        self.assertEqual(list(sfm.parser(trans_src)), ref)


if __name__ == "__main__":
    import doctest, warnings
    #import sys;sys.argv = ['', 'Test.testName']
    suite = unittest.TestSuite(
       [doctest.DocTestSuite(event),
        unittest.defaultTestLoader.loadTestsFromName(__name__)])
    warnings.simplefilter("error", sfm.SyntaxWarning)
    unittest.TextTestRunner(verbosity=2).run(suite)

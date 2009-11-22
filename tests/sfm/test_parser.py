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
            '\\test' : ['start{} test'],
            '\\test text' : ['start{} test',"text{} 'text'"],
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
                                            '\\more-sfm more text\n'
                                            'over a line break\\marker')),
                         ['start{} sfm',"text{} 'text\\n'",
                          "text{} 'bare text\\n'",
                          'start{} more-sfm',"text{} 'more text\\n'",
                          "text{} 'over a line break'",'start{} marker'])

    
    def test_line_ends(self):
        self.assertEqual(map(str,sfm.parser(['\\le unix\n',
                                             '\\le windows\r\n',
                                             '\\empty\n',
                                             '\\le missing'])),
                         ['start{} le',r"text{} 'unix\n'",
                          'start{} le',r"text{} 'windows\r\n'",
                          'start{} empty',r"text{} '\n'",
                          'start{} le',r"text{} 'missing'"])
        

    def test_position(self):
        p=sfm.parser('\\li1 text\n\\l2\n\\l3\n')
        self.assertEqual([tuple(e.pos) for e in p],
                         [(0,0),(0,5),  # \li1 text\n
                          (1,0),(1,3),  # \l2\n
                          (2,0),(2,3)]) # \l3\n
                
    
    def test_transduction(self):
        src = ['\\test\n',
               '\\test text\n',
               '\\sfm text\n',
               'bare text\n',
               '\\more-sfm more text\n',
               'over a line break\\marker'
               '\\le unix\n',
               # These forms do not transduce identically due to whitespace differences
               '\\test \\inline text\\inline*\n',
               '\\test \\i1\\i2 deep\\i2*\\i1*\n',
               '\\le windows\r\n',
               '\\le missing\n',
               '\\test\\i1\\i2 deep text\\i1*\n',
               '\\test\\i1\\i2 deep text\n']
        
        with warnings.catch_warnings(record=True) as ref_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", sfm.SyntaxWarning)
            ref = list(sfm.parser(src))
        trans = sfm.handler()
        trans_src = list(sfm.transduce(sfm.parser, trans, src))

        # Check known straight through transductions.
        map(self.assertEqual, trans_src[:6], src[:6])
        # Check the errors match 
        map(self.assertEqual, map(str,ref_parse_errors), map(str,trans.errors))
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

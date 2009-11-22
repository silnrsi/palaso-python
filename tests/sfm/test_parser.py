'''
Created on Nov 2, 2009

@author: tim_eves@sil.org
'''
import unittest
import codecs, itertools, operator, warnings

from palaso import sfm
from palaso.sfm import event,usfm


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
                         [(1,1),(1,6),  # \li1 text\n
                          (2,1),(2,4),  # \l2\n
                          (3,1),(3,4)]) # \l3\n
                
    
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
        # produced by parse of the transduced output.
        # Ignore the column posiions as whitespace differences will cause 
        # differences there however line numbers should remain stable
        map(self.assertEqual, ((e.pos.line,)+e[1:] for e in sfm.parser(trans_src)), ((e.pos.line,)+e[1:] for e in ref))



class USFMTestCase(unittest.TestCase):
    def test_inline_markers(self):
        tests = [(r'\test', ['start{} test','end{} test']),
                 (r'\test text', ['start{} test',"text{test} 'text'",'end{} test']),
                 (r'\test\sig text\sig*', ['start{} test', 'start{test} sig', "text{sig} 'text'", 'end{test} sig', 'end{} test']),
                 (r'\test \f\fk deep\fk*\f* ', ['start{} test', 'start{test} f', 'start{f} fk', "text{fk} 'deep'", 'end{f} fk', 'end{test} f', 'end{} test']),] 
        for r in [(map(str,usfm.parser(s)),r) for s,r in tests]: self.assertEqual(*r)

    def test_sytax_error(self):
        self.assertRaises(SyntaxError,list,usfm.parser('\\test \\fk deep text\\fk* \\f*'))
        self.assertRaises(SyntaxError,list,usfm.parser('\\id\n\\p test text'))
        self.assertRaises(SyntaxError,list,usfm.parser('\\c \\p \\v 1 test text'))
        self.assertRaises(SyntaxError,list,usfm.parser('\\c 1 \\v \\p test text'))

    def test_value_error(self):
        self.assertRaises(ValueError,list,usfm.parser('\\c one \\p \\v 1 test text'))
        self.assertRaises(ValueError,list,usfm.parser('\\c 1 \\v test text'))

    def test_sytax_warning(self):
        with warnings.catch_warnings():
            warnings.resetwarnings()
            warnings.simplefilter("error", sfm.SyntaxWarning)
            self.assertRaises(sfm.SyntaxWarning,list,usfm.parser('\\test \\f\\fr deep text\\f*'))
            self.assertRaises(sfm.SyntaxWarning,list,usfm.parser('\\test \\f\\fr deep text'))
            self.assertRaises(sfm.SyntaxWarning,list,usfm.parser('normal text \\f more text'))

    def test_parameters(self):
        tests = [(r'\c 1', ['start{} c 1', 'end{} c']),
                 (r'\c 2 text', ['start{} c 2', "text{c} 'text'", 'end{} c']),
                 (r'\v 1', ['start{} v 1', 'end{} v']),
                 (r'\v 2 text', ['start{} v 2', "text{v} 'text'", 'end{} v']),
                 (r'\c 2\v 3 text\v 4 verse', ['start{} c 2', 'start{c} v 3', "text{v} 'text'", 'end{c} v', 'start{c} v 4', "text{v} 'verse'", 'end{c} v', 'end{} c']),]
        for r in [(map(str,usfm.parser(s)),r) for s,r in tests]: self.assertEqual(*r)
        
    def test_ischar(self):
        tests = [(r'\c 2\v 3 text\v 4 verse', ['start{} c 2', 'start{c} v 3', "text{v} 'text'", 'end{c} v', 'start{c} v 4', "text{v} 'verse'", 'end{c} v', 'end{} c']),]
        for r in [(map(str,usfm.parser(s)),r) for s,r in tests]: self.assertEqual(*r)

    def test_mixed(self):
        self.assertEqual(map(str,usfm.parser('\\sfm text\n'
                                            'bare text\n'
                                            '\\more-sfm more text\n'
                                            'over a line break\\marker')),
                         ['start{} sfm',"text{sfm} 'text\\n'",
                          "text{sfm} 'bare text\\n'",'end{} sfm',
                          'start{} more-sfm',"text{more-sfm} 'more text\\n'",
                          "text{more-sfm} 'over a line break'",'end{} more-sfm','start{} marker','end{} marker'])

    def test_line_ends(self):
        self.assertEqual(map(str,usfm.parser(['\\le unix\n',
                                             '\\le windows\r\n',
                                             '\\empty\n',
                                             '\\le missing'])),
                         ['start{} le',r"text{le} 'unix\n'",'end{} le',
                          'start{} le',r"text{le} 'windows\r\n'",'end{} le',
                          'start{} empty',r"text{empty} '\n'",'end{} empty',
                          'start{} le',r"text{le} 'missing'",'end{} le'])

    def test_position(self):
        p=usfm.parser('\\li1 text\n\\l2\n\\l3\n')
        self.assertEqual([tuple(e.pos[:2]) for e in p],
                         [(1,1),(1,6),(1,11),   # \li1 text\n
                          (2,1),(2,4),(2,5),    # \l2\n
                          (3,1),(3,4),(3,5)])   # \l3\n

    def test_reference(self):
        p=usfm.parser('\\id MAT\n\\c 1 \\v 1\n\\id JHN\n\\c 3 \\v 16')
        self.assertEqual([tuple(e.pos) for e in p],
                         [(0, 0, None, 0, 0), (0, 4, 'MAT', 0, 0), (0, 8, 'MAT', 0, 0),     # \id MAT\n 
                          (1, 0, 'MAT', 1, 0),                                              # \c 1 
                          (1, 5, 'MAT', 1, 1), (1, 10, 'MAT', 1, 1), (1, 10, 'MAT', 1, 1),  # \v 1\n 
                          (2, 0, None, 0, 0), (2, 4, 'JHN', 0, 0), (2, 8, 'JHN', 0, 0),     # \id JHN\n
                          (3, 0, 'JHN', 3, 0),                                              # \c 3 
                          (3, 5, 'JHN', 3, 16), (3, 10, 'JHN', 3, 16), (3, 10, 'JHN', 3, 16)]) # \v 16
                            
    def test_transduction(self):
        src = ['\\test\n',
               '\\test text\n',
               '\\sfm text\n',
               'bare text\n',
               '\\more-sfm more text\n',
               'over a line break\\marker'
               '\\le unix\n',
               # These forms do not transduce identically due to whitespace differences
               '\\test\\sig text\\sig*\n',
               '\\test \\f\\fk deep\\fk*\\f*\n',
               '\\le windows\r\n',
               '\\le missing\n',
               '\\test\\f\\fk deep text\\f*\n',
               '\\test\\f\\fr deep text\n',
               '\\id MAT\n',
#               '\\c 1 \\v 1\n',
               '\\id JHN\n',
               '\\c 3 \\v 16',
               ]
        
        with warnings.catch_warnings(record=True) as ref_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", sfm.SyntaxWarning)
            ref = list(usfm.parser(src))
        trans = usfm.handler()
        trans_src = list(sfm.transduce(usfm.parser,trans, src))

        # Check known straight through transductions.
        map(self.assertEqual, trans_src[:6], src[:6])
        # Check the errors match 
        map(self.assertEqual, map(str,ref_parse_errors), map(str,trans.errors))
        # Check the rest but do not ignore syntax warnings as there should be none
        # produced by parse of the transduced output.
        # Ignore the column posiions as whitespace differences will cause 
        # differences there however line numbers should remain stable
        map(self.assertEqual, ((e.pos.line,)+e[1:] for e in usfm.parser(trans_src)), ((e.pos.line,)+e[1:] for e in ref))



if __name__ == "__main__":
    import doctest, warnings
    #import sys;sys.argv = ['', 'Test.testName']
    suite = unittest.TestSuite(
       [doctest.DocTestSuite(event),
        unittest.defaultTestLoader.loadTestsFromName(__name__)])
    warnings.simplefilter("error", sfm.SyntaxWarning)
    unittest.TextTestRunner(verbosity=2).run(suite)

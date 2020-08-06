'''
Created on Nov 2, 2009

@author: tim_eves@sil.org
'''
import unittest
import codecs, itertools, operator, warnings

import palaso.sfm as sfm
from palaso.sfm import usfm, text, handler

try:
    from itertools import imap
except ImportError:
    imap = map

def elem(name, *content):
    name, args = (name[0],list(name[1:])) if type(name) == tuple else (name, [])
    e = sfm.element(name, args=args, meta=usfm.default_stylesheet.get(name,{}))
    e.extend(content)
    return e

def depos(doc):
    doc = list(doc)
    for e in doc:
        e.pos = sfm.position(1,1)
        if isinstance(e, sfm.element): depos(e)
    return doc

def flatten(doc):
    def _g(e):
        yield e
        if isinstance(e, sfm.element):
            for c in flatten(e): yield c
    return itertools.chain.from_iterable(imap(_g, doc))

def _test_round_trip_parse(self, source, parser, *args, **kwds):
#    src_name = getattr(source,'name',None)
#    src_encoding = getattr(source, 'encoding', None)
    source = list(source)
    doc = list(parser(source, *args, **kwds))
    rt_doc = list(parser(sfm.format(doc).splitlines(True),*args,**kwds))
    # Check for equivilent parse.
    self.assertEqual(doc, rt_doc, 'roundtrip parse unequal')


def _test_round_trip_source(self, source, parser, leave_file=False, *args, **kwds):
    src_name = getattr(source,'name',None)
    src_encoding = getattr(source, 'encoding', None)
    source = list(source)
    rt_src = sfm.pprint(parser(source, *args, **kwds)).splitlines(True)
    
    # Try for perfect match first
    if source == rt_src:
        self.assert_(True)
        return
    
    # Normalise line endings
    source = map(operator.methodcaller('rstrip'), source)
    rt_src = map(operator.methodcaller('rstrip'), rt_src)
    if source == rt_src:
        self.assert_(True)
        return
    
    # Normalise the \f ..\f* marker forms in the source
    source = map(operator.methodcaller('replace', u'\\ft ',u'\\fr*'), source)
    rt_src = map(operator.methodcaller('replace', u'\\ft ',u'\\fr*'), rt_src)
    
    if leave_file and src_name:
        codecs.open(src_name+'.normalised','w', 
                    encoding=src_encoding).writelines(l+'\n' for l in source)
        codecs.open(src_name+'.roundtrip','w', 
                    encoding=src_encoding).writelines(l+'\n' for l in rt_src)
    
    self.assertEqual(source, rt_src, 'roundtriped source not equal')



class SFMTestCase(unittest.TestCase):
    def test_line_ends(self):
        self.assertEqual(list(sfm.parser(['\\le unix\n',
                                         '\\le windows\r\n',
                                         '\\empty\n',
                                         '\\le missing'])),
                        [elem('le',text('unix\n')),
                         elem('le',text('windows\r\n')),
                         elem('empty',text('\n')),
                         elem('le', text('missing'))])

    def test_position(self):
        p=sfm.parser(['\\li1 text\n',
                     '\\l2\n',
                     '\\l3\n'])
        self.assertEqual([tuple(e.pos) for e in flatten(p)],
                         [(1,1),(1,6),  # \li1 text\n
                          (2,1),(2,4),  # \l2\n
                          (3,1),(3,4)]) # \l3\n
                
    
    def test_format(self):
        src = ['\\test\n',
               '\\test text\n',
               '\\sfm text\n',
               'bare text\n',
               '\\more-sfm more text\n',
               'over a line break\\marker'
               '\\le unix\n',
               '\\le windows\r\n',
               '\\le missing\n',
               '\\test\\i1\\i2 deep text\\i1*\n',
               '\\test\\i1\\i2 deep text\n',
               # These forms do not transduce identically due to whitespace differences
               '\\test \\inline text\\inline*\n',
               '\\test \\i1\\i2 deep\\i2*\\i1*\n']
        
        with warnings.catch_warnings(record=True) as ref_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", SyntaxWarning)
            ref_parse = list(sfm.parser(src))
        trans_src = sfm.pprint(ref_parse).splitlines(True)
        
        with warnings.catch_warnings(record=True) as trans_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", SyntaxWarning)
            trans_parse = list(sfm.parser(trans_src))
        
        # Check pretty printer output matches input, skip the last 2
        map(self.assertEqual, src[:10], trans_src[:10])
        # Check the parsed pretty printed doc matches the reference
        self.assertEqual(ref_parse, trans_parse)
        # Check the errors match 
        map(self.assertEqual, 
            map(str,ref_parse_errors[:10]), 
            map(str,trans_parse_errors[:10]))
        # Check the positions line up for the first 10 items
        map(self.assertEqual, 
            (e.pos for e in flatten(ref_parse[:16])), 
            (e.pos for e in flatten(trans_parse[:16])))
        # Check all the line positions, meta data and annotations line up
        map(self.assertEqual, 
            ((e.pos.line, getattr(e,'meta',None), getattr(e,'annotations',None)) for e in flatten(ref_parse)), 
            ((e.pos.line, getattr(e,'meta',None), getattr(e,'annotations',None)) for e in flatten(trans_parse)))
    

class USFMTestCase(unittest.TestCase):
    def test_footnote_content(self):
        def ft(src,doc): return (r'\id TEST\mt '+src, [elem('id', text('TEST'), elem('mt', doc))])
        tests = [ft(r'\f - bare text\f*',           elem(('f','-'), text('bare text'))),
                 ft(r'\f - \ft bare text\ft*\f*',   elem(('f','-'), text('bare text'))),
                 ft(r'\f + \fk Issac:\ft In Hebrew means "laughter"\f*',                            elem(('f','+'), elem('fk',text('Issac:')), text('In Hebrew means "laughter"'))),
                 ft(r'\f + \fk Issac:\fk*In Hebrew means "laughter"\f*',                            elem(('f','+'), elem('fk',text('Issac:')), text('In Hebrew means "laughter"'))),
                 ft(r'\f + \fr 1.14 \fq religious festivals;\ft or \fq seasons.\f*',                elem(('f','+'), elem('fr',text('1.14 ')), elem('fq',text('religious festivals;')), text('or '), elem('fq',text('seasons.')))),
                 ft(r'\f + \fr 1.14 \fr*\fq religious festivals;\fq*or \fq seasons.\fq*\f*',        elem(('f','+'), elem('fr',text('1.14 ')), elem('fq',text('religious festivals;')), text('or '), elem('fq',text('seasons.'))))]
        for r in [(list(usfm.parser([s], error_level=usfm.level.Note)),r) for s,r in tests]:
            self.assertEqual(*r)

#    def test_sytax_warning(self):
#        with warnings.catch_warnings():
#            warnings.resetwarnings()
#            warnings.simplefilter("error", SyntaxWarning)
#            self.assertRaises(SyntaxWarning,list,usfm.parser(['\\id TEST\\mt \\whoops']))
#            self.assertRaises(SyntaxError,  list,usfm.parser(['\\id TEST\\mt \\whoops'], error_level=sfm.level.Marker))
#            self.assertRaises(SyntaxWarning,list,usfm.parser(['\\id TEST\\mt \\zwhoops']))
#            self.assertRaises(SyntaxWarning,list,usfm.parser(['\\id TEST\\mt \\zwhoops'], error_level=sfm.level.Marker))

#    def test_reference(self):
#        p=usfm.parser('\\id MAT EN\n\\c 1 \\v 1 \\v 2-3\n\\id JHN\n\\c 3 \\v 16')
#        self.assertEqual([tuple(e.pos) for e in p],
#                         [(1, 1, None, None, None),     # start{}   id
#                          (1, 5, 'MAT', None, None),    # text{id}  'MAT EN\n'
#                          (1, 12, 'MAT', None, None),   # end{}     id 
#                          (2, 1, 'MAT', '1', None),     # start{}   c 1
#                          (2, 6, 'MAT', '1', '1'),      # start{c}  v 1
#                          (2, 11, 'MAT', '1', '1'),     # end{c}    v
#                          (2, 11, 'MAT', '1', '2-3'),   # start{c}  v 2-3
#                          (2,17, 'MAT','1','2-3'),      # text{v}   '\n'
#                          (2,18, 'MAT','1','2-3'),      # end{c}    v
#                          (2,18, 'MAT','1','2-3'),      # end{}     c
#                          (3, 1, None, None, None),     # start{}   id
#                          (3, 5, 'JHN', None, None),    # text{id}  'JHN\n'
#                          (3, 9, 'JHN', None, None),    # end{}     id
#                          (4, 1, 'JHN', '3', None),     # start{}   c 3                                      # \c 3 
#                          (4, 6, 'JHN', '3', '16'),     # start{c}  v 16
#                          (4, 11, 'JHN', '3', '16'),    # end{c}    v
#                          (4, 11, 'JHN', '3', '16')])   # end{}     c
#                            

    def test_round_trip_parse(self):
        pass
#        _test_round_trip_parse(self, codecs.open('data/mat.1.usfm','r',encoding='utf_8_sig'), usfm.parser)

    def test_round_trip_src(self):
        pass
#        _test_round_trip_source(self, codecs.open('data/mat.1.usfm','r',encoding='utf_8_sig'), usfm.parser, leave_file=True)

if __name__ == "__main__":
    import doctest
    suite = unittest.TestSuite(
        [doctest.DocTestSuite('palaso.sfm'),
         doctest.DocTestSuite('palaso.sfm.records'),
         doctest.DocTestSuite('palaso.sfm.style'),
         doctest.DocTestSuite('palaso.sfm.usfm'),
         unittest.defaultTestLoader.loadTestsFromName(__name__)
         ])
    warnings.simplefilter("ignore", SyntaxWarning)
    unittest.TextTestRunner(verbosity=2).run(suite)


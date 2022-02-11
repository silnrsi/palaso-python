#!/usr/bin/env python3
'''
Created on Nov 2, 2009

@author: tim_eves@sil.org
'''
import copy
import palaso.sfm as sfm
import unittest
import warnings
from itertools import chain
from palaso.sfm import usfm, Text
from pathlib import Path


def elem(name, *content):
    args = []
    if isinstance(name, tuple):
        name, args = name[0], list(name[1:])
    e = sfm.Element(name, args=args,
                    meta=usfm.default_stylesheet.get(name, {}))
    e.extend(content)
    return e


def flatten(doc):
    def _g(e):
        if isinstance(e, sfm.Text):
            yield e
        elif isinstance(e, sfm.Element):
            e_ = copy.copy(e)
            e_.clear()
            yield e_
            yield from flatten(e)

    return chain.from_iterable(map(_g, doc))


class SFMTestCase(unittest.TestCase):
    def test_line_ends(self):
        self.assertEqual(list(sfm.parser(['\\le unix\n',
                                          '\\le windows\r\n',
                                          '\\empty\n',
                                          '\\le missing'])),
                         [elem('le', Text('unix\n')),
                          elem('le', Text('windows\r\n')),
                          elem('empty', Text('\n')),
                          elem('le', Text('missing'))])

    def test_position(self):
        p = sfm.parser(['\\li1 text\n',
                        '\\l2\n',
                        '\\l3\n'])
        self.assertEqual([tuple(e.pos) for e in flatten(p)],
                         [(1, 1), (1, 6),   # \li1 text\n
                          (2, 1), (2, 4),   # \l2\n
                          (3, 1), (3, 4)])  # \l3\n

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
               # These forms do not transduce identically due to whitespace
               # differences
               '\\test \\inline text\\inline*\n',
               '\\test \\i1\\i2 deep\\i2*\\i1*\n']

        with warnings.catch_warnings(record=True) as ref_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", SyntaxWarning)
            ref_parse = list(sfm.parser(src))
        trans_src = sfm.generate(ref_parse).splitlines(True)

        with warnings.catch_warnings(record=True) as trans_parse_errors:
            warnings.resetwarnings()
            warnings.simplefilter("always", SyntaxWarning)
            trans_parse = list(sfm.parser(trans_src))

        # Check the parsed pretty printed doc matches the reference
        self.assertEqual(trans_parse, ref_parse)
        # Check pretty printer output matches input, skip the last 2
        self.assertEqual(trans_src[:10], src[:10])
        # Check the errors match
        for a, e in zip(trans_parse_errors[:31], ref_parse_errors):
            with self.subTest(warning=str(e)):
                self.assertEqual(a.message.args, e.message.args)

        # Check all the line positions, meta data and annotations line up
        for a, e in zip(flatten(trans_parse), flatten(ref_parse)):
            with self.subTest():
                self.assertEqual(a.pos.line, e.pos.line)
                self.assertAlmostEqual(a.pos.col, e.pos.col, delta=1)
                self.assertEqual(getattr(a, 'meta', None),
                                 getattr(e, 'meta', None))
                self.assertEqual(getattr(a, 'annotations', None),
                                 getattr(e, 'annotations', None))

    def test_escaping(self):
        # Test without special escaping. Only \ is escaped
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(
                list(sfm.parser([
                    r"\marker text",
                    r"\escaped backslash\\character",
                    r"\test1 \test2 \\backslash \^hat \%\test3\\\^"])),
                [elem('marker', Text('text')),
                 elem('escaped', Text(r'backslash\\character')),
                 elem('test1'),
                 elem('test2', Text(r'\\backslash ')),
                 elem('^hat'),
                 elem('%'),
                 elem('test3', Text(r'\\')),
                 elem('^')])
        # Test with extended escaping rules.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(
                list(sfm.parser([
                    "\\test1 \\test2 \\\\backslash \\^hat \\%\\test3\\\\\\^"],
                    tag_escapes="[^0-9a-zA-Z]")),
                [elem('test1'),
                 elem('test2', Text('\\\\backslash \\^hat \\%')),
                 elem('test3', Text('\\\\\\^'))])


class USFMTestCase(unittest.TestCase):
    def _test_round_trip_source(self, file_obj, parser, leave_file=False,
                                *args, **kwds):
        source = list(file_obj)
        rt_src = sfm.generate(parser(source, *args, **kwds)).splitlines(True)

        # Try for perfect match first
        if source == rt_src:
            self.assertTrue(True)
            return

        # Normalise line endings
        source = [x.rstrip() for x in source]
        rt_src = [x.rstrip() for x in rt_src]
        if source == rt_src:
            self.assertTrue(True)
            return

        # Normalise the \f ..\f* marker forms in the source
        source = [x.replace(r'\ft ', r'\fr*') for x in source]
        rt_src = [x.replace(r'\ft ', r'\fr*') for x in rt_src]

        if leave_file and hasattr(file_obj, 'name'):
            path = Path(Path(file_obj.name).name)
            enc = getattr(file_obj, 'encoding', None)

            with path.with_suffix('.normalised').open('w', encoding=enc) as f:
                f.writelines(x+'\n' for x in source)
            with path.with_suffix('.roundtrip').open('w', encoding=enc) as f:
                f.writelines(x+'\n' for x in rt_src)

        self.assertEqual(source, rt_src, 'roundtriped source not equal')

    def _test_round_trip_parse(self, file, parser,
                               leave_file=False,
                               *args, **kwds):
        doc = list(parser(file, *args, **kwds))
        regenerated = sfm.generate(doc)
        try:
            doc = list(flatten(doc))
            rt_doc = list(flatten(parser(regenerated.splitlines(True),
                                         *args, **kwds)))

            # Check for equivilent parse.
            self.assertEqual(doc,
                             rt_doc,
                             'roundtrip parse unequal')
        except (SyntaxError, AssertionError) as se:
            if leave_file and hasattr(file, 'name'):
                path = Path(Path(file.name).name).with_suffix('.regenerated')
                enc = getattr(file, 'encoding', None)
                with path.open('w', encoding=enc) as f:
                    f.write(regenerated)
                    se.filename = f.name
            if isinstance(se, AssertionError):
                raise
            print(str(se))

    def test_footnote_content(self):
        def ft(src, doc):
            return (r'\id TEST\mt '+src, [elem('id', Text('TEST'),
                                          elem('mt', doc))])

        tests = [ft(r'\f - bare text\f*',
                    elem(('f', '-'), Text('bare text'))),
                 ft(r'\f - \ft bare text\ft*\f*',
                    elem(('f', '-'), Text('bare text'))),
                 ft(r'\f + \fk Issac:\ft In Hebrew means "laughter"\f*',
                    elem(('f', '+'),
                         elem('fk', Text('Issac:')),
                         Text('In Hebrew means "laughter"'))),
                 ft(r'\f + \fk Issac:\fk*In Hebrew means "laughter"\f*',
                    elem(('f', '+'),
                         elem('fk', Text('Issac:')),
                         Text('In Hebrew means "laughter"'))),
                 ft(r'\f + \fr 1.14 \fq religious festivals;\ft or'
                    r' \fq seasons.\f*',
                    elem(('f', '+'),
                         elem('fr', Text('1.14 ')),
                         elem('fq', Text('religious festivals;')),
                         Text('or '),
                         elem('fq', Text('seasons.')))),
                 ft(r'\f + \fr 1.14 \fr*\fq religious festivals;\fq*or'
                    r' \fq seasons.\fq*\f*',
                    elem(('f', '+'),
                         elem('fr', Text('1.14 ')),
                         elem('fq', Text('religious festivals;')),
                         Text('or '),
                         elem('fq', Text('seasons.'))))]
        run_tests = ((list(usfm.parser([s],
                                       error_level=usfm.ErrorLevel.Note)), r)
                     for s, r in tests)
        for r in run_tests:
            self.assertEqual(*r)

    def test_reference(self):
        p = flatten(
                usfm.decorate_references(
                    usfm.parser('\\id MAT EN\n\\c 1\n\\p\n\\v 1 \\v 2-3\n'
                                '\\id JHN DE\n\\c 3\n\\p\n\\v 16'.splitlines())))
        self.assertEqual(
            [(*e.pos, e.pos.book, e.pos.chapter, e.pos.verse, str(e)) for e in p],
            [(1, 1, 'MAT', None, None, '\\id'),
             (1, 5, 'MAT', None, None, 'MAT EN'),
             (2, 1, 'MAT', '1', None, '\\c 1'),
             (3, 1, 'MAT', '1', None, '\\p'),
             (4, 1, 'MAT', '1', '1', '\\v 1 '),
             (4, 6, 'MAT', '1', '2-3', '\\v 2-3 '),
             (5, 1, 'JHN', None, None, '\\id'),
             (5, 5, 'JHN', None, None, 'JHN DE'),
             (6, 1, 'JHN', '3', None, '\\c 3'),
             (7, 1, 'JHN', '3', None, '\\p'),
             (8, 1, 'JHN', '3', '16', '\\v 16 ')])

    def test_round_trip_parse(self):
        data_dir = Path(__file__).parent / 'data'
        self._test_round_trip_parse(
            (data_dir / '41MATWEBorig.SFM').open(encoding='utf_8_sig'),
            usfm.parser,
            leave_file=True)

    def test_round_trip_src(self):
        data_dir = Path(__file__).parent / 'data'
        self._test_round_trip_source(
            (data_dir / '41MATWEBorig.SFM').open(encoding='utf_8_sig'),
            usfm.parser,
            leave_file=True)


def load_tests(loader, standard_tests, ignore):
    import doctest
    return unittest.TestSuite(
        [
            doctest.DocTestSuite('palaso.sfm'),
            doctest.DocTestSuite('palaso.sfm.records'),
            doctest.DocTestSuite('palaso.sfm.style'),
            doctest.DocTestSuite('palaso.sfm.usfm'),
            standard_tests,
        ])


def setUpModule():
    warnings.simplefilter("ignore", SyntaxWarning)


def tearDownModule():
    warnings.resetwarnings()

'''
The STY stylesheet file parser module.  This defines the database schema for 
STY files necessary to drive the SFM DB parser.
'''
__version__ = '20101011'
__date__    = '11 October 2010'
__author__  = 'Tim Eves <tim_eves@sil.org>'
__history__ = '''
	20100111 - tse - Initial version
	20101026 - tse - rewrote to use new palaso.sfm.records module
	20101109 - tse - Update to use unique field type's set object and fix 
		poor quality error messages that fail to identify the source file.
'''
import re
import palaso.sfm.records as records
from palaso.sfm.records import sequence,flag,unique
from itertools import imap
from functools import partial



_fields = {'Marker'         : (str,             SyntaxError('missing Marker marker missing')),
           'Endmarker'      : (str,             None),
           'Name'           : (str,             SyntaxError('Marker {0} defintion missing: {1}')),
           'Description'    : (str,             SyntaxError('Marker {0} defintion missing: {1}')),
           'OccursUnder'    : (unique(sequence(str)),   [None]),
           'Rank'           : (int,             None),
           'TextProperties' : (unique(sequence(str)),   []),
           'TextType'       : (str,             SyntaxError('Marker {0} defintion missing: {1}')),
           'StyleType'      : (str,             None),
           'FontSize'       : (int,             None),
           'Regular'        : (flag,            False),
           'Bold'           : (flag,            False),
           'Italic'         : (flag,            False),
           'Underline'      : (flag,            False),
           'Superscript'    : (flag,            False),
           'Justification'  : (str,             'Left'),
           'SpaceBefore'    : (int,             0),
           'SpaceAfter'     : (int,             0),
           'FirstLineIndent': (float,           0),
           'LeftMargin'     : (float,           0),
           'RightMargin'    : (float,           0),
           'Color'          : (int,             0)
           }



_comment = re.compile(r'\s*#.*$')



def _munge_record(r):
    tag = r.pop('Marker').lstrip()
    ous = r['OccursUnder']
    if 'NEST' in ous:
        ous.remove('NEST')
        ous.add(tag)
    return (tag, r)


def parse(source):
    '''
    >>> from pprint import pprint
    >>> pprint(parse("""
    ... \Marker toc1
    ... \Name toc1 - File - Long Table of Contents Text
    ... \Description Long table of contents text
    ... \OccursUnder h h1 h2 h3 
    ... \Rank 1
    ... \TextType Other
    ... \TextProperties paragraph publishable vernacular
    ... \StyleType Paragraph
    ... \FontSize 12
    ... \Italic
    ... \Bold
    ... \Color 16384""".splitlines(True)))
    {'toc1': {'Bold': True,
              'Color': 16384,
              'Description': 'Long table of contents text',
              'Endmarker': None,
              'FirstLineIndent': 0,
              'FontSize': 12,
              'Italic': True,
              'Justification': 'Left',
              'LeftMargin': 0,
              'Name': 'toc1 - File - Long Table of Contents Text',
              'OccursUnder': set(['h', 'h1', 'h2', 'h3']),
              'Rank': 1,
              'Regular': False,
              'RightMargin': 0,
              'SpaceAfter': 0,
              'SpaceBefore': 0,
              'StyleType': 'Paragraph',
              'Superscript': False,
              'TextProperties': set(['paragraph', 'publishable', 'vernacular']),
              'TextType': 'Other',
              'Underline': False}}
    >>> pprint(parse("""
    ... \Marker dummy1
    ... \Name dummy1 - File - dummy marker definition
    ... \Description A marker used for demos
    ... \OccursUnder id NEST
    ... \TextType Other
    ... \Bold
    ... \Color 12345""".splitlines(True)))
    {'dummy1': {'Bold': True,
                'Color': 12345,
                'Description': 'A marker used for demos',
                'Endmarker': None,
                'FirstLineIndent': 0,
                'FontSize': None,
                'Italic': False,
                'Justification': 'Left',
                'LeftMargin': 0,
                'Name': 'dummy1 - File - dummy marker definition',
                'OccursUnder': set(['dummy1', 'id']),
                'Rank': None,
                'Regular': False,
                'RightMargin': 0,
                'SpaceAfter': 0,
                'SpaceBefore': 0,
                'StyleType': None,
                'Superscript': False,
                'TextProperties': [],
                'TextType': 'Other',
                'Underline': False}}
    >>> pprint(parse("""
    ... \Marker error
    ... \Name error - File - cause a marker definition parse error
    ... \Description A marker to demostrate error reporting
    ... \Bold
    ... \Color 12345""".splitlines(True)))
    Traceback (most recent call last):
    ...
    SyntaxError: <string>: line 2,1: Marker error defintion missing: TextType
    '''
    no_comments = imap(partial(_comment.sub,''), source)
    rec_parser = records.parser(no_comments, records.schema('Marker', _fields))
    rec_parser.source = getattr(source, 'name', '<string>')
    recs = iter(rec_parser)
    next(recs,None)
    return dict(imap(_munge_record, recs))


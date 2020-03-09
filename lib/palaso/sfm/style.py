"""
The STY stylesheet file parser module.

This defines the database schema for STY files necessary to drive the SFM DB
parser and pre-processing to remove comments, etc.
"""
__author__ = "Tim Eves"
__date__ = "06 January 2020"
__copyright__ = "Copyright © 2020 SIL International"
__license__ = "MIT"
__email__ = "tim_eves@sil.org"
# History:
# 09-Nov-2010 tse   Update to use unique field type's set object and fix poor
#                   quality error messages that fail to identify the source
#                   file.
# 26-Jan-2010 tse   Rewrote to use new palaso.sfm.records module.
# 11-Jan-2010 tse   Initial version.

import re

import palaso.sfm.records as records
from palaso.sfm.records import sequence, flag, unique, level
from palaso.sfm.records import UnrecoverableError
from functools import partial

_fields = {
    'Marker': (str, UnrecoverableError(
                        'Start of record marker: {0} missing')),
    'Endmarker':      (str, None),
    # For Name and Description, a default
    #  StructureError('Marker {0} defintion missing: {1}') causes
    #  problems with real world STY files.
    'Name':            (str,   None),
    'Description':     (str,   None),
    'OccursUnder':     (unique(sequence(str)), [None]),
    'Rank':            (int,   None),
    'TextProperties':  (unique(sequence(str)), []),
    'TextType':        (str,   "Unspecified"),
    'StyleType':       (str,   None),
    'FontSize':        (int,   None),
    'Regular':         (flag,  False),
    'Bold':            (flag,  False),
    'Italic':          (flag,  False),
    'Underline':       (flag,  False),
    'Superscript':     (flag,  False),
    'Smallcaps':       (flag,  False),
    'Justification':   (str,   'Left'),
    'SpaceBefore':     (int,   0),
    'SpaceAfter':      (int,   0),
    'FirstLineIndent': (float, 0),
    'LeftMargin':      (float, 0),
    'RightMargin':     (float, 0),
    'Color':           (int,   0),
    'color':           (int,   0)
}

_comment = re.compile(r'\s*#.*$')
_markers = re.compile(r'^\s*\\[^\s\\]+\s')


def _lower_match(m):
    return m.group().lower()


def _munge_record(r):
    tag = r.pop('Marker').lstrip()
    ous = r['OccursUnder']
    if 'NEST' in ous:
        ous.remove('NEST')
        ous.add(tag)
    return (tag, r)


def parse(source, error_level=level.Content, base=None):
    '''
    >>> from pprint import pprint
    >>> pprint(parse("""
    ... \\Marker toc1
    ... \\Name toc1 - File - Long Table of Contents Text
    ... \\Description Long table of contents text
    ... \\OccursUnder h h1 h2 h3
    ... \\Rank 1
    ... \\TextType Other
    ... \\TextProperties paragraph publishable vernacular
    ... \\StyleType Paragraph
    ... \\FontSize 12
    ... \\Italic
    ... \\Bold
    ... \\Color 16384""".splitlines(True)))
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
    ... \\Marker dummy1
    ... \\Name dummy1 - File - dummy marker definition
    ... \\Description A marker used for demos
    ... \\OccursUnder id NEST
    ... \\TextType Other
    ... \\Bold
    ... \\Color 12345""".splitlines(True)))
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
    ... \\Marker error
    ... \\Name error - File - cause a marker definition parse error
    ... \\Description A marker to demostrate error reporting
    ... \\Bold
    ... \\Color 12345""".splitlines(True)))
    Traceback (most recent call last):
    ...
    SyntaxError: <string>: line 2,1: Marker error defintion missing: TextType
    ''' # noqa
    # strip comments out
    no_comments = map(partial(_comment.sub, ''), source)
    # lowercase all markers
    lower_source = map(partial(_markers.sub, _lower_match), no_comments)
    # lowercase all field names.
    lower_fields = {k.lower(): v for k, v in _fields.items()}

    rec_parser = records.parser(
                    lower_source,
                    records.schema('Marker', lower_fields),
                    error_level=error_level,
                    base=base)
    rec_parser.source = getattr(source, 'name', '<string>')
    recs = iter(rec_parser)
    next(recs, None)
    res = dict(map(_munge_record, recs))
    if base is not None:
        base.update(res)
        res = base
    return res

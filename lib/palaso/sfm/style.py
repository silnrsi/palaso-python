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
from collections import abc
from palaso.sfm.records import sequence, flag, unique, level
from palaso.sfm.records import UnrecoverableError
from functools import partial

_fields = {
    'Marker': (str, UnrecoverableError(
                        'Start of record marker: {0} missing')),
    'Endmarker':      (str, None),
    'Name':            (str,   None),
    'Description':     (str,   None),
    'OccursUnder':     (unique(sequence(str)), {None}),
    'Rank':            (int,   None),
    'TextProperties':  (unique(sequence(str)), {}),
    'TextType':        (str,   'Unspecified'),
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


class marker(dict):
    def __init__(self, iterable=(), **kwarg):
        self.update(iterable)
        self.update(kwarg)

    def __getitem__(self, key):
        return super().__getitem__(key.casefold())

    def __setitem__(self, key, value):
        return super().__setitem__(key.casefold(), value)

    def __delitem__(self, key):
        return super().__delitem__(key.casefold())

    def __contains__(self, key):
        return super().__contains__(key.casefold())

    def copy(self):
        return marker(self)

    def pop(self, key, *args, **kwargs):
        return super().pop(key.casefold(), *args, **kwargs)

    def setdefault(self, key, default=None):
        super().setdefault(key, default)

    def update(self, iterable=(), **kwarg):
        if isinstance(iterable, abc.Mapping):
            iterable = iterable.items()
        super().update((k.casefold(), v) for k, v in iterable)
        super().update((k.casefold(), v) for k, v in kwarg.items())


def parse(source, error_level=level.Content, base=None):
    '''
    >>> from pprint import pprint
    >>> r = parse(r"""
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
    ... \\Color 16384""".splitlines(True))
    >>> pprint((r, 
    ...         sorted(r['toc1']['OccursUnder']),
    ...         sorted(r['toc1']['TextProperties'])))
    ... # doctest: +ELLIPSIS
    ({'toc1': {'bold': True,
               'color': 16384,
               'description': 'Long table of contents text',
               'endmarker': None,
               'firstlineindent': 0,
               'fontsize': 12,
               'italic': True,
               'justification': 'Left',
               'leftmargin': 0,
               'name': 'toc1 - File - Long Table of Contents Text',
               'occursunder': {...},
               'rank': 1,
               'regular': False,
               'rightmargin': 0,
               'smallcaps': False,
               'spaceafter': 0,
               'spacebefore': 0,
               'styletype': 'Paragraph',
               'superscript': False,
               'textproperties': {...},
               'texttype': 'Other',
               'underline': False}},
     ['h', 'h1', 'h2', 'h3'],
     ['paragraph', 'publishable', 'vernacular'])
    >>> r = parse(r"""
    ... \\Marker dummy1
    ... \\Name dummy1 - File - dummy marker definition
    ... \\Description A marker used for demos
    ... \\OccursUnder id NEST
    ... \\TextType Other
    ... \\Bold
    ... \\Color 12345""".splitlines(True))
    >>> pprint((r, sorted(r['dummy1']['OccursUnder'])))
    ... # doctest: +ELLIPSIS
    ({'dummy1': {'bold': True,
                 'color': 12345,
                 'description': 'A marker used for demos',
                 'endmarker': None,
                 'firstlineindent': 0,
                 'fontsize': None,
                 'italic': False,
                 'justification': 'Left',
                 'leftmargin': 0,
                 'name': 'dummy1 - File - dummy marker definition',
                 'occursunder': {...},
                 'rank': None,
                 'regular': False,
                 'rightmargin': 0,
                 'smallcaps': False,
                 'spaceafter': 0,
                 'spacebefore': 0,
                 'styletype': None,
                 'superscript': False,
                 'textproperties': {},
                 'texttype': 'Other',
                 'underline': False}},
     ['dummy1', 'id'])
    ''' # noqa

    # strip comments out
    no_comments = map(partial(_comment.sub, ''), source)

    rec_parser = records.parser(
                    no_comments,
                    records.schema('Marker', _fields),
                    error_level=error_level,
                    base={None: marker()} if base is None else base)
    rec_parser.source = getattr(source, 'name', '<string>')
    recs = iter(rec_parser)
    next(recs, None)
    res = dict(map(_munge_record, recs))
    if base is not None:
        base.update(res)
        res = base
    return res

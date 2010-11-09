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
    tag = r.pop('Marker')
    ous = r['OccursUnder']
    if 'NEST' in ous:
        ous.remove('NEST')
        ous.add(tag)
    return (tag, r)


def parse(source):
    source = imap(partial(_comment.sub,''), source)
    recs = iter(records.parser(source, records.schema('Marker', _fields)))
    next(recs,None)
    return dict(imap(_munge_record, recs))


# -*- coding: utf-8 -*-
'''
The SFM DB file parser module.  Given a database schema defining field names 
and types it generates the necessary sytlesheet for that SFM DB to drive the
palaso.sfm module.  This guide the palaso.sfm parser to so it can correctly 
parser an SFM database document.

The schema datatype permits the definition of value parsers and default values
for optional fields and exceptions to be throw for required fields. 
(see palaso.sfm.style for an example)
'''
__version__ = '20101011'
__date__    = '11 October 2010'
__author__  = 'Tim Eves <tim_eves@sil.org>'
__history__ = '''
	20101026 - tse - Initial version
	20101109 - tse - Fixes for poor error reporting and add a unique sequence 
		field type to return deduplicated sets as field types.
		Extend the flag field type parser to accept common textual 
		boolean false descriptions 'off','no' etc.
		Make the field value parser accept empty field values.
'''
import collections
import palaso.sfm as sfm
from functools import partial, reduce
from itertools import chain
from palaso.sfm import level

try:
    from itertools import ifilter, imap
except ImportError:
    ifilter = filter
    imap = map

try:
    unicode
except NameError:
    unicode = str

class schema(collections.namedtuple('schema','start fields')): pass
_schema = schema

def flag(v):
    '''
    >>> flag('')
    True
    >>> flag('on') and flag('true') and flag('whatever')
    True
    >>> flag('0') or flag('no') or flag('off') or flag('false') or flag('none')
    False
    '''
    return v is not None \
            and v.strip().lower() not in ('0','no','off','false','none')

def sequence(p,delim=' '):
    '''
    >>> sequence(int)(' 1 2  3   4   5  ')
    [1, 2, 3, 4, 5]
    >>> sequence(int, ',')('1,2, 3,  4,   5,')
    [1, 2, 3, 4, 5]
    '''
    return lambda v: map(p,filter(bool, v.strip().split(delim)))

def unique(p):
    '''
    >>> unique(sequence(int))(' 1 2  3   4   5 4 3 2 1 ')
    set([1, 2, 3, 4, 5])
    '''
    return lambda v: set(p(v))


class ErrorLevel(object):
    __slots__ = ('msg','level')
    def __new__(cls, level, msg):
        el = super(ErrorLevel, cls).__new__(cls)
        el.msg = msg
        el.level = level
        return el

NoteError = partial(ErrorLevel, level.Note)
MarkerError = partial(ErrorLevel, level.Marker)
ContentError = partial(ErrorLevel, level.Content)
StructureError = partial(ErrorLevel, level.Structure)
UnrecoverableError = partial(ErrorLevel, level.Unrecoverable)


class parser(sfm.parser):
    '''
    >>> from pprint import pprint
    >>> import warnings
    >>> doc = """\\Marker toc1
    ...          \\Name toc1 - File - Long Table of Contents Text
    ...          \\OccursUnder h h1 h2 h3
    ...          \\FontSize 12
    ...          \\Bold"""
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("ignore")
    ...     pprint(list(parser(doc.splitlines(True), schema('Marker',{}))))
    [{},
     {u'Bold': '',
      u'FontSize': text(u'12'),
      u'Marker': text(u'toc1'),
      u'Name': text(u'toc1 - File - Long Table of Contents Text'),
      u'OccursUnder': text(u'h h1 h2 h3')}]
    >>> demo_schema = schema('Marker', 
    ...     {'Marker' : (str, UnrecoverableError('Start of record marker: {0} missing')),
    ...      'Name'   : (str, StructureError('Marker {0} defintion missing: {1}')),
    ...      'Description'    : (str, ''),
    ...      'OccursUnder'    : (unique(sequence(str)), [None]),
    ...      'FontSize'       : (int,                   None),
    ...      'Bold'           : (flag,                  False)})
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("error")
    ...     pprint(list(parser(doc.splitlines(True), demo_schema)))
    [{},
     {'Bold': True,
      'Description': '',
      'FontSize': 12,
      'Marker': 'toc1',
      'Name': 'toc1 - File - Long Table of Contents Text',
      'OccursUnder': set(['h', 'h1', 'h2', 'h3'])}]
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("error")
    ...     pprint(list(parser("""
    ... \\Description this goes in the header since it's before the 
    ... key marker Marker as does the following marker.
    ... \\FontSize 15
    ... \\Marker toc1
    ... \\Name toc1 - File - Long Table of Contents Text
    ... \\FontSize 12""".splitlines(True), demo_schema)))
    [{u'Description': "this goes in the header since it's before the \\nkey marker Marker as does the following marker.",
      u'FontSize': 15},
     {'Bold': False,
      'Description': '',
      'FontSize': 12,
      'Marker': 'toc1',
      'Name': 'toc1 - File - Long Table of Contents Text',
      'OccursUnder': [None]}]
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("error")
    ...     pprint(list(parser("""\Marker toc1
    ...                           \FontSize 12""".splitlines(True), demo_schema)))
    Traceback (most recent call last):
    ...
    SyntaxError: <string>: line 1,1: Marker toc1 defintion missing: Name
    '''
    def __init__(self, source, schema, error_level=level.Content, base=None):
        if not isinstance(schema, _schema): 
            raise TypeError('arg 2 must a \'schema\' not {0!r}'.format(schema))
        metas = dict((k,super(parser,self).default_meta) for k in schema.fields)
        super(parser,self).__init__(source, 
                    metas, error_level=error_level)
        self._schema = schema
        self._base = base
    
    def __iter__(self):
        start,fields = self._schema
        mapping = next(iter(self._base.values()), {}).__class__
        proto = mapping((k,dv) for k,(_,dv) in fields.items())
        default_field = (lambda x:x, None)
        def record(rec):
            rec = mapping(rec)
            rec_ = self._base.get(rec[start]) if self._base is not None and rec[start] in self._base else proto.copy()
            rec_.update(rec)
            for fn,err in ifilter(lambda i: isinstance(i[1], ErrorLevel), rec_.items()):
                if err: 
                    self._error(err.level, err.msg, rec, rec.name, fn)
                    rec_[fn] = None
            return rec_
        
        def accum(db, m):
            valuator = fields.get(m.name, default_field)
            try:
                field = (m.name, valuator[0](m[0].rstrip() if m else ''))
            except Exception as err:
                self._error(level.Content, err.msg if hasattr(err,'msg') else unicode(err), m)
                field = (m.name, valuator[1])
            if m.name == start:
                if isinstance(field[1], ErrorLevel): 
                    self._error(err.level, err.msg, m, m.name)
                    field = (m.name, '')
                db.append(sfm.element(field[1], m.pos, content=[field]))
            else:
                db[-1].append(field)
            return db
        
        es = super(parser,self).__iter__()
        fs = ifilter(lambda v: isinstance(v, sfm.element), es)
        fgs = reduce(accum, fs, [sfm.element('header')])
        return chain((dict(fgs[0]),), imap(record, fgs[1:]))

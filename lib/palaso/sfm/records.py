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
import collections, operator, sys
import palaso.sfm as sfm
from itertools import groupby, ifilter, imap, chain
from functools import partial



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


class parser(sfm.parser):
    '''
    >>> from pprint import pprint
    >>> doc = """\\Marker toc1
    ...          \\Name toc1 - File - Long Table of Contents Text
    ...          \\OccursUnder h h1 h2 h3
    ...          \\FontSize 12
    ...          \\Bold"""
    >>> pprint(list(parser(doc.splitlines(True), schema('Marker',{}))))
    [{},
     {u'Bold': '',
      u'FontSize': text(u'12', pos=position(line=4, col=20)),
      u'Marker': text(u'toc1', pos=position(line=1, col=9)),
      u'Name': text(u'toc1 - File - Long Table of Contents Text', pos=position(line=2, col=16)),
      u'OccursUnder': text(u'h h1 h2 h3', pos=position(line=3, col=23))}]
    >>> demo_schema = schema('Marker', 
    ...     {'Marker' : (str, SyntaxError('Marker start marker missing')),
    ...      'Name'   : (str, SyntaxError('Marker {0} defintion missing: {1}')),
    ...      'Description'    : (str, ''),
    ...      'OccursUnder'    : (unique(sequence(str)), [None]),
    ...      'FontSize'       : (int,                   None),
    ...      'Bold'           : (flag,                  False)})
    >>> pprint(list(parser(doc.splitlines(True), demo_schema)))
    [{},
     {'Bold': True,
      'Description': '',
      'FontSize': 12,
      'Marker': 'toc1',
      'Name': 'toc1 - File - Long Table of Contents Text',
      'OccursUnder': set(['h', 'h1', 'h2', 'h3'])}]
    >>> pprint(list(parser("""
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
    >>> pprint(list(parser("""\Marker toc1
    ...                       \FontSize 12""".splitlines(True), demo_schema)))
    Traceback (most recent call last):
    ...
    SyntaxError: <string>: line 1,1: Marker toc1 defintion missing: Name
    '''
    
    
    def __init__(self, source, schema):
        if not isinstance(schema, _schema): 
            raise TypeError('arg 2 must a \'schema\' not {0!r}'.format(schema))
        metas = dict((k,super(parser,self).default_meta) for k in schema.fields)
        super(parser,self).__init__(source, 
                    metas, 
                    default_meta=None if metas else super(parser,self).default_meta,
                    private_prefix=False)
        self.__schema = schema
    
    
    def __iter__(self):
        start,fields = self.__schema
        proto = dict((k,dv) for k,(_,dv) in fields.iteritems())
        default_field = (lambda x:x, None)
        def record(rec):
            rec_ = proto.copy()
            rec_.update(rec)
            fn,err = next(ifilter(lambda i: isinstance(i[1],Exception),rec_.iteritems()),('',None))
            if err: self._error(type(err), err.msg, rec, rec.name, fn)
            return rec_
        
        def accum(db, m):
            try:
                field = (m.name, fields.get(m.name, default_field)[0](m[0].rstrip() if m else ''))
            except Exception, err:
                self._error(type(err), err.msg if hasattr(err,'msg') else unicode(err), m)
            if m.name == start:
                db.append(sfm.element(field[1], m.pos, content=[field]))
            else:
                db[-1].append(field)
            return db
        
        es = super(parser,self).__iter__()
        fs = ifilter(lambda v: isinstance(v, sfm.element), es)
        fgs = reduce(accum, fs, [sfm.element('header')])
        return chain((dict(fgs[0]),), imap(record, fgs[1:]))



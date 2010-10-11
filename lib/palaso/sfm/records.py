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
'''
import collections, operator, sys
import palaso.sfm as sfm
from itertools import groupby, ifilter, imap, chain
from functools import partial



class schema(collections.namedtuple('schema','start fields')): pass
_schema = schema



def flag(v):                return v != None
def sequence(p,delim=' '):  return lambda v: map(p,v.strip().split(delim))



class parser(sfm.parser):
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
        
        def record(rec):
            rec_ = proto.copy()
            rec_.update(rec)
            fn,err = next(ifilter(lambda i: isinstance(i[1],Exception),rec_.iteritems()),('',None))
            if err: self._error(type(err), err.msg, rec, rec.name, fn)
            return rec_
        
        def accum(db, m):
            try:
                field = (m.name, fields.get(m.name)[0](m[0].rstrip()))
            except Exception, err:
                self._error(type(err), err.msg, m)
            if m.name == start:
                db.append(sfm.element(field[1], m.pos, content=[field]))
            else:
                db[-1].append(field)
            return db
        
        es = super(parser,self).__iter__()
        fs = ifilter(lambda v: isinstance(v, sfm.element), es)
        fgs = reduce(accum, fs, [sfm.element('header')])
        return chain((dict(fgs[0]),), imap(record, fgs[1:]))



# -*- coding: utf-8 -*-
'''
The SFM parser module. It provides the basic stylesheet guided sfm parser and 
default TextType parser.  This parser provides detailed error and diagnostic 
messages including accurate line and column information as well as context 
information for structure errors. 
The default marker meta data makes this produce only top-level marker-text
pairs.
'''
__version__ = '20101011'
__date__    = '11 October 2010'
__author__  = 'Tim Eves <tim_eves@sil.org>'
__history__ = '''
	20081210 - djd - Seperated SFM definitions from the module
		to allow for parsing other kinds of SFM models
		Also changed the name to parse_sfm.py as the
		module is more generalized now
	20091026 - tse - renamed and refactored generatoion of markers
		dict to module import time as part of import into palaso 
		package.
	20101026 - tse - rewrote to enable the parser to use the stylesheets to 
		direct how to parse document structure and TextType to permit
		specific semantics on subsections.
	20101028 - tse - Handle endmarkers as a special case so the do no require
		a space to separate them from the following text.
'''
import collections, codecs, functools, operator, re, warnings
from itertools import chain, groupby, ifilter, imap
from functools import partial



__all__ = ('event','usfm',                          # Sub modules
           'position','element','text', 'parser',   # data types
           'reduce','map_tree','pprint')               # functions



'''Immutable position data that attach to tokens'''
position = collections.namedtuple('position', 'line col')



class element(list):
    __slots__ = ('pos', 'name', 'args', 'parent', 'meta')
    
    
    def __init__(self, name, pos=position(1,1), args=[], parent=None, meta=None, content=[]):
        super(element,self).__init__(content)
        self.name = unicode(name)
        self.pos = pos
        self.args = args
        self.parent = parent
        self.meta = meta
    
    
    def __repr__(self):
        return u'element({0!r},pos={1!r},args={2!r})'.format(self.name, 
                                                             self.pos, 
                                                             self.args)
    
    
    def __str__(self):
        return u'\\{0!s}'. format(' '.join([self.name] + self.args))



class text(unicode):
    def __new__(cls, content, pos=position(0,0), parent=None):
        return super(text,cls).__new__(cls, content)
    
    
    def __init__(self, content, pos=position(0,0), parent=None):
        self.pos = pos
        self.parent = parent
    
    
    @staticmethod
    def concat(iterable):
        i = next(iterable)
        return text(u''.join(chain([i],iterable)), i.pos)
    
    
    def split(self, sep, maxsplit=-1):
        tail = self
        result = []
        while tail and maxsplit != 0:
            e = tail.find(sep)
            if e == -1:
                result.append(tail)
                tail=text(u'',position(self.pos.line,self.pos.col+len(tail)))
                break
            result.append(tail[:e])
            tail = tail[e+len(sep):]
            maxsplit -= 1
        result.append(tail)
        return result
    
    
    def lstrip(self,*args,**kwds):
        l = len(self)
        s_ = super(text,self).lstrip(*args,**kwds)
        return text(s_, position(self.pos.line, self.pos.col + l-len(s_)))
    
    
    def __repr__(self):
        return u'text({0!s},pos={1!r})'.format(super(text,self).__repr__(), getattr(self,'pos',position(0,0)))
    
    
    def __add__(self, rhs):
        return text(super(text,self).__add__(rhs),self.pos)
    
    
    def __getslice__(self, i, j): return self.__getitem__(slice(i,j))
    
    
    def __getitem__(self,i):
        return text(super(text,self).__getitem__(i), 
                    position(self.pos.line, self.pos.col 
                                + (i.start if isinstance(i,slice) else i)))



class _put_back_iter(collections.Iterator):
    def __init__(self, iterable):
        self.__itr = iter(iterable)
        self.__pbq = []
    
    
    def next(self):
        if self.__pbq:
            try:    return self.__pbq.pop()
            except: raise StopIteration
        return next(self.__itr)
    
    
    def put_back(self, value):
        self.__pbq.append(value)
    
    
    def peek(self):
        if not self.__pbq:
            self.__pbq.append(next(self.__itr))
        return self.__pbq[-1]



_default_meta = {'TextType':'default', 'OccursUnder':[None], 'Endmarker':None}



class parser(collections.Iterable):
    default_meta = _default_meta
    __tokeniser = re.compile(r'(?<!\\)\\[^\s\\]+|(?:\\\\|[^\\])+',re.DOTALL | re.UNICODE)
    
    
    @classmethod
    def extend_stylesheet(cls, stylesheet, *names):
        return dict(((m,cls.default_meta) for m in names), **stylesheet)
    
    
    def __init__(self, source, stylesheet={}, 
                               default_meta=_default_meta, 
                               private_prefix=None):
        # Pick the marker lookup failure mode.
        assert default_meta or not private_prefix, 'default_meta must be provided when using private_prefix'
        if   private_prefix:    self.__get_style = self.__get_style_pua_strict
        elif default_meta:      self.__get_style = self.__get_style_lax
        else:                   self.__get_style = self.__get_style_full_strict
        
        # Set simple attributes
        self.source  = source.name if hasattr(source,'name') else '<string>'
        self.__default_meta = default_meta
        self.__pua_prefix   = private_prefix
        self._tokens        = _put_back_iter(self.__lexer(source))
        
        # Compute end marker stylesheet definitions
        em_def = {'TextType':None, 'Endmarker':None}
        self.__sty = stylesheet.copy()
        self.__sty.update(ifilter(operator.itemgetter(0), 
                          imap(lambda (k,m): (m['Endmarker'],
                                              dict(em_def, OccursUnder=[k])), 
                               stylesheet.iteritems())))
    
    
    def _error(self, err_type, msg, ev, *args, **kwds):
        if issubclass(err_type, StandardError):
            msg = (u'{source}: line {token.pos.line},{token.pos.col}: ' + unicode(msg)).format(token=ev,source=self.source,
                                                               *args).encode('utf_8')
            raise err_type, msg
        elif issubclass(err_type, Warning):
            msg = unicode(msg).format(token=ev,*args,**kwds).encode('utf_8')
            warnings.warn_explicit(msg, err_type, self.source, ev.pos.line)
        else:
            raise ValueError, u"'{0!r}' is not an StandardError or Warning object".format(err_type).encode('utf_8')
    
    
    def __get_style_lax(self, tag):
        meta = self.__sty.get(tag)
        if not meta:
            self._error(SyntaxWarning, u'unknown marker \\{token}: not in styesheet', 
                       tag)
            return self.__default_meta
        return meta
    
    
    def __get_style_full_strict(self, tag):
        meta = self.__sty.get(tag)
        if not meta:
            self._error(SyntaxError, 'unknown marker \\{token}: not in styesheet', 
                       tag)
        return meta
    
    
    def __get_style_pua_strict(self, tag):
        meta = self.__sty.get(tag)
        if not meta:
            if tag.startswith(self.__pua_prefix):
                self._error(SyntaxWarning, 
                            'unknown private marker \\{token}: '
                            'not it stylesheet using default marker definition', 
                            tag)
                meta = self.__default_meta
            else:
                self._error(SyntaxError, 'unknown marker \\{token}: not in styesheet', 
                            tag)
        return meta
    
    
    def __iter__(self):
        return self._default_(None)
    
    
    @staticmethod
    def _pp_marker_list(tags):
        return ', '.join('\\'+c if c else 'toplevel' for c in tags)
    
    
    @staticmethod
    def __lexer(lines):
        lmss = enumerate(imap(parser.__tokeniser.finditer, lines))
        fs = (text(m.group(), position(l+1,m.start()+1)) for l,ms in lmss for m in ms)
        gs = groupby(fs, operator.methodcaller('startswith','\\'))
        return chain.from_iterable(g if istag else (text.concat(g),) for istag,g in gs)
    
    
    def _default_(self, parent):
        get_meta = self.__get_style
        for tok in self._tokens:
            if tok[0] == u'\\':  # Parse markers.
                tag  = tok[1:]
                
                # Check for the expected end markers with no separator and
                # break them apart
                if parent and parent.meta['Endmarker'] \
                        and tag.startswith(parent.meta['Endmarker']):
                    cut = len(parent.meta['Endmarker'])
                    if cut != len(tag):
                        if self._tokens.peek()[0] == u'\\':
                            self._tokens.put_back(tag[cut:])
                        else:
                            # If the next token isn't a marker coaleces the 
                            # remainder with it into a single text node.
                            self._tokens.put_back(tag[cut:] + next(self._tokens,''))
                        tag = tag[:cut]
                meta = get_meta(tag)
                if not meta['OccursUnder'] or (parent is not None and parent.name or None) in meta['OccursUnder']:
                    sub_parse = meta['TextType']
                    if not sub_parse: return
                    
                    # Spawn a sub-node
                    e = element(tag, tok.pos, parent=parent, meta=meta)
                    e.extend(getattr(self,'_'+meta['TextType']+'_',self._default_) (e))
                    yield e
                elif parent is None:
                    # We've failed to find a home for marker tag, poor thing.
                    if not meta['TextType']:
                        self._error(SyntaxError, 
                                      'orphan end marker {token}: '
                                      'no matching opening marker \\{0}', 
                                      tok, meta['OccursUnder'][0])
                    else:
                        self._error(SyntaxError, 
                                      'orphan marker {token}: '
                                      'may only occur under {0}', tok, 
                                      self._pp_marker_list(meta['OccursUnder']))
                else:
                    # Do implicit closure only for non-inline markers or 
                    # 'character' style markers'.
                    if parent.meta['Endmarker'] and 'Character' not in parent.meta['StyleType']:
                        self._error(SyntaxError, 
                            'invalid end marker {token}: \\{0} '
                            '(line {0.pos.line},{0.pos.col}) '
                            'is only be closed with \\{1}', tok, parent,
                            parent.meta['Endmarker'])
                    
                    self._tokens.put_back(tok)
                    return
            else:   # Pass non marker data through with a litte fix-up
                if parent:
                    tok = tok if len(parent) else tok[1:]
                if tok:
                    tok.parent = parent
                    yield tok
    
    
    def _Milestone_(self, parent):
        return tuple()
    _milestone_ = _Milestone_
    
    _Other_ = _default_
    _other_ = _Other_



def sreduce(elementf, textf, trees, initial=None):
    def _g(a, e):
        if isinstance(e, basestring): return textf(e,a)
        return elementf(e, a, reduce(_g, e, initial))
    return reduce(_g, trees, initial)



def smap(elementf, textf, doc):
    def _g(e):
        if isinstance(e,element):
            (name,args,cs) = elementf(e.name, e.args, map(_g, e))
            e = element(name, e.pos, args, content=cs, meta=e.meta)
            reduce(lambda _,e_: setattr(e_,'parent',e), e, None)
            return e
        else:
            e_ = textf(e)
            return text(e_, e.pos, e)
    return map(_g, doc)



def sfilter(pred, doc):
    def _g(a, e):
        if isinstance(e, text): 
            if pred(e.parent):
                a.append(text(e,e.pos,a or None))
            return a
        e_ = element(e.name, e.pos, e.args, parent=a or None, meta=e.meta)
        reduce(_g, e, e_)
        if len(e_) or pred(e):
            a.append(e_)
        return a
    return reduce(_g, doc, [])



def _path(e):
    r = []
    while (e != None): 
        r.append(e.name)
        e = e.parent
    r.reverse()
    return r



def mpath(*path):
    path = list(path)
    pr_slice = slice(len(path))
    def _pred(e): return path == _path(e)[pr_slice]
    return _pred



def text_properties(*props):
    props = set(props)
    def _props(e): return props <= set(e.meta.get('TextProperties',[]))
    return _props



def pprint(doc):
    def _marker(e,r, cr):
        m = e.meta['Endmarker']
        r += unicode(e)
        if cr or e.args:
            r += '\n' if e and isinstance(e[0], element) \
                         and e.meta.get('StyleType') == 'Paragraph'else ' '
        r += cr
        if m:
            r += '\\' + m
        return r
    
    return sreduce(_marker, lambda e,r: r + unicode(e), doc, u'')



def copy(doc):
    def id_element(name, args, children): return (name, args[:], children)
    def id_text(t): return t
    return smap(id_element, id_text, doc)


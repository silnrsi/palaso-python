# -*- coding: utf-8 -*-
'''
The USFM parser module, provides the default sytlesheet for USFM and
USFM specific textype parsers to the palaso.sfm module.  These guide the 
palaso.sfm parser to so it can correctly parser USFM document structure.
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
		direct how to parse structure and USFM specific semantics.
	20101109 - tse - Ensure cached usfm.sty is upto date after package code 
		changes.
'''
import bz2, contextlib, operator, os, re, site
import cPickle as pickle
import palaso.sfm.style as style
import palaso.sfm as sfm
from palaso.sfm import level
from itertools import chain, ifilter, imap
from functools import *



_PALASO_DATA = os.path.join(
        os.path.expanduser(os.path.dirname(os.path.normpath(site.USER_SITE))),
        'palaso-python','sfm')



def _check_paths(pred, paths):
    return next(ifilter(pred, imap(os.path.normpath, paths)),None)

def _newer(cache, benchmark):
    return os.path.getmtime(benchmark) <= os.path.getmtime(cache)

def _is_fresh(cached_path, benchmarks):
    return reduce(operator.and_, 
                  imap(partial(_newer, cached_path), benchmarks))

def _cached_stylesheet(path):
    package_dir = os.path.dirname(__file__)
    source_path = _check_paths(os.path.exists, 
        [ os.path.join(_PALASO_DATA, path),
          os.path.join(package_dir, path)])
    
    cached_path = os.path.normpath(os.path.join(
                        _PALASO_DATA,
                        path+os.extsep+'cz'))
    if os.path.exists(cached_path):
        import glob
        if _is_fresh(cached_path, [source_path] 
                + glob.glob(os.path.join(package_dir, '*.py'))):
            return cached_path
    else:
        path = os.path.dirname(cached_path)
        if not os.path.exists(path):
            os.makedirs(path)
    
    import pickletools
    with contextlib.closing(bz2.BZ2File(cached_path, 'wb')) as zf:
        zf.write(pickletools.optimize(
            pickle.dumps(style.parse(open(source_path,'r')))))
    return cached_path



def _load_cached_stylesheet(path):
    cached_path = _cached_stylesheet(path)
    try:
        try:
            with contextlib.closing(bz2.BZ2File(cached_path,'rb')) as sf:
                return pickle.load(sf)
        except:
            os.unlink(cached_path)
            cached_path = _cached_stylesheet(path)
            with contextlib.closing(bz2.BZ2File(cached_path,'rb')) as sf:
                return pickle.load(sf)
    except:
        os.unlink(cached_path)
        raise



default_stylesheet=_load_cached_stylesheet('usfm.sty')



_default_meta = {'TextType':'Milestone', 'OccursUnder':None, 'Endmarker':None}



class parser(sfm.parser):
    default_meta = _default_meta
    numeric_re = re.compile(r'\s*(\d+(:?[-\u2010\2011]\d+)?)',re.UNICODE)
    caller_re = re.compile(r'\s*([-+\w])',re.UNICODE)
    sep_re = re.compile(r'\s|$',re.UNICODE)
    
    @classmethod
    def extend_stylesheet(cls, *names, **kwds):
        return super(parser,cls).extend_stylesheet(
                kwds.get('stylesheet', default_stylesheet), *names)
    
    
    def __init__(self, source, stylesheet=default_stylesheet,
                               default_meta=_default_meta, *args, **kwds):
        super(parser, self).__init__(source, stylesheet, default_meta,
                                     private_prefix='z',*args, **kwds)
    
    
    def _ChapterNumber_(self, chapter_marker):
        tok = next(self._tokens)
        chapter = self.numeric_re.match(tok)
        if not chapter:
            self._error(level.Content, 'missing chapter number after \\c', 
                                     chapter_marker)
            chapter_marker.args = [u'\uFFFD']
        else:
            chapter_marker.args = [unicode(tok[chapter.start(1):chapter.end(1)])]
            tok = tok[chapter.end():]
        #import pdb; pdb.set_trace()
        if tok and not self.sep_re.match(tok):
            self._error(level.Content, 'missing space after chapter number \'{chapter}\'',
                                    tok, chapter=chapter_marker.args[0])
        tok  = tok.lstrip()
        if tok:
            if tok[0] == '\\': 
                self._tokens.put_back(tok)
            else:
                self._error(level.Structure, 'text cannot follow chapter marker \'{0}\'', tok, chapter_marker, )
                chapter_marker.append(sfm.element(None, meta=self.default_meta, content=[tok]))
                tok = None
                
        return self._default_(chapter_marker)
    _chapternumber_ = _ChapterNumber_

      
    def _VerseNumber_(self, verse_marker):
        tok = next(self._tokens)
        verse = self.numeric_re.match(tok)
        if not verse:
            self._error(level.Content, 'missing verse number after \\v', 
                                     verse_marker)
            verse_marker.args = [u'\uFFFD']
        else:
            verse_marker.args = [unicode(tok[verse.start(1):verse.end(1)])]
            tok = tok[verse.end():]
        
        if not self.sep_re.match(tok):
            self._error(level.Content, 'missing space after verse number \'{verse}\'',
                                    tok, verse=verse_marker.args[0])
        tok = tok.lstrip()
        
        if tok: self._tokens.put_back(tok)
        return tuple()
    _versenumber_ = _VerseNumber_
    
    
    @staticmethod
    def _canonicalise_footnote(content):
        def g(e):
            if getattr(e,'name', None) == 'ft':
                e.parent.annotations['content-promoted'] = True
                return e
            else:
                return [e]
        return chain.from_iterable(imap(g, content))
    
    
    def _NoteText_(self,parent):
        if parent.meta['StyleType'] != 'Note': return self._default_(parent)
        
        tok = next(self._tokens)
        caller = self.caller_re.match(tok)
        if not caller:
            self._error(level.Content, 'missing caller parameter after \\{token.name}',
                        parent)
            parent.args = [u'\uFFFD']
        else:
            parent.args = [unicode(tok[caller.start(1):caller.end(1)])]
            tok = tok[caller.end():]
        
        if not self.sep_re.match(tok):
            self._error(level.Content, 'missing space after caller parameter \'{caller}\'',
                                    tok, caller=parent.args[0])
        
        tok = tok.lstrip()
        if tok: self._tokens.put_back(tok)
        return self._canonicalise_footnote(self._default_(parent))

_test = ['test text\n', '\\test text\\\\words\n', 'more text \\test2\n', 'inline \\i text\\i* more text']


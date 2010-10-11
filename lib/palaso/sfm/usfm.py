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
'''
import bz2, contextlib, os, re, site, sys
import cPickle as pickle
import palaso.sfm.style as style
import palaso.sfm as sfm
from itertools import chain, ifilter, imap
from functools import *



_PALASO_DATA = os.path.join(
        os.path.expanduser(os.path.dirname(os.path.normpath(site.USER_SITE))),
        'palaso-python','sfm')



def _check_paths(pred, paths):
    return next(ifilter(pred, imap(os.path.normpath, paths)),None)



def _cached_stylesheet(path):
    source_path = _check_paths(os.path.exists, 
        [ os.path.join(_PALASO_DATA, path),
          os.path.join(os.path.dirname(sys.modules[__name__].__file__), path)])
    
    cached_path = os.path.normpath(os.path.join(
                        _PALASO_DATA,
                        path+os.extsep+'cz'))
    if os.path.exists(cached_path):
        original = os.stat(source_path)
        cached   = os.stat(cached_path)
        if original.st_mtime <= cached.st_mtime:
            return cached_path
    else:
        path = os.path.dirname(cached_path)
        if not os.path.exists(path):
            os.makedirs(path)
    
    import bz2, pickletools
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
    numeric_re = re.compile(r'\s*(\d+(:?[-\u2010\2011]\d+)?)\s+',re.UNICODE)
    
    
    @classmethod
    def extend_stylesheet(cls, *names, **kwds):
        return super(parser,cls).extend_stylesheet(
                kwds.get('stylesheet', default_stylesheet), *names)
    
    
    def __init__(self, source, stylesheet=default_stylesheet,
                               default_meta=_default_meta, private = True):
        super(parser, self).__init__(source, stylesheet, default_meta,
                                     private_prefix=private and 'z')
    
    
    def _ChapterNumber_(self, chapter_marker):
        tok = next(self._tokens)
        if tok[0] == '\\':
            self._error(SyntaxError, 'missing chapter number after \\c', 
                                     chapter_marker)
        
        # Match against digits:
        chapter = self.numeric_re.match(tok)
        if not chapter:
            self._error(SyntaxError, 'invalid chapter number after \\c: '
                        '{token} is not a valid chapter number', tok.split(' ',1)[0])
        chapter_marker.args = [unicode(tok[chapter.start(1):chapter.end(1)])]
        tok = tok[chapter.end():]
        
        if tok and tok[0] != '\\': 
            self._error(SyntaxError, 'text cannot follow a chapter marker', tok)
        
        if tok: self._tokens.put_back(tok)
        return self._default_(chapter_marker)
    _chapternumber_ = _ChapterNumber_
    
    
    def _VerseNumber_(self, verse_marker):
        tok = next(self._tokens)
        if tok[0] == '\\':
            self._error(SyntaxError, 'missing verse number after \\v', 
                                     verse_marker)
        
        # Match against digits:
        verse = self.numeric_re.match(tok)
        if not verse:
            self._error(SyntaxError, 'invalid verse number after \\v: '
                        '{token} is not a valid verse number', tok.split(' ',1)[0])
        verse_marker.args = [unicode(tok[verse.start(1):verse.end(1)])]
        tok = tok[verse.end():]
        
        if tok: self._tokens.put_back(tok)
        return tuple()
    _versenumber_ = _VerseNumber_
    
    
    def _NoteText_(self,parent):
        if parent.meta['StyleType'] != 'Note':
            return self._default_(parent)

        tok = next(self._tokens)
        if tok[0] == '\\':
            self._error(SyntaxError, 'missing caller parameter number after {0}',
                        tok, parent)
        parent.args = [unicode(tok.strip())]
        content = self._default_(parent)
        return chain.from_iterable(e if getattr(e,'name',None) == 'ft' else (e,) for e in content)



_test = ['test text\n', '\\test text\\\\words\n', 'more text \\test2\n', 'inline \\i text\\i* more text']


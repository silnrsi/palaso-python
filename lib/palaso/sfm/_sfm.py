#!/usr/bin/env python
'''
Created on Oct 31, 2009

@author: tim
'''
import re, collections, warnings
from itertools import chain

import event

eol = '\n'
pos    = collections.namedtuple('pos', 'line col')

class SyntaxWarning(SyntaxWarning): pass

def ismarker(tok): return tok and tok[0] == '\\'
def isopen(tok):   return tok and tok[-1] != '*' 


class parser(object):
    def __init__(self, source):
        self.__pos = None
        self.source = source.name if hasattr(source,'name') else '<string>'
        self._context =[None]
        self._events = self.__scanner(self.__tokens(source.splitlines() if isinstance(source,basestring) else source))
    
    def __iter__(self): return self._events
    
    @property
    def pos(self): return self.__pos
    def set_pos(self, line,col): self.__pos = pos(line+1,col+1)

    @property
    def context(self):  return self._context[-1]
    
    def __tokens(self,source):
        tokenise = re.compile(r'(\\[^\\\s]+|(?:^|(?<=\s))[^\\]*)',re.U)        
        nlines = 1
        for line_no,line in enumerate(source):
            for m in tokenise.finditer(line.rstrip("\r\n")):
                tok = m.group(1)
                if not tok: continue
                self.set_pos(line_no,m.start(1))
                yield tok
            self.set_pos(line_no,len(line))
            yield eol

    
    def _error(self,err_type, msg,*args,**kwds):
        if issubclass(err_type, StandardError):
            msg = ('{source}: line {line},{col}: '+msg).format(line=self.pos.line,
                                                               col=self.pos.col,
                                                               source=self.source,
                                                               *args)
            raise SyntaxError, msg
        elif issubclass(err_type, Warning):
            msg = msg.format(col=self.pos.col,*args,**kwds)
            warnings.warn_explicit(msg, SyntaxWarning, self.source, self.pos.line)
        else:
            raise ValueError, "'{0!r}' is not an StandardError or Warning object".format(err_type)
    
    
    def __scanner(self,tokens):
        need_close=0
        for tok in tokens:
            if ismarker(tok):
                tag = tok[1:]
                if isopen(tok):
                    yield event.start(self.context, tag)
                    self._context.append(tag)
                else:
                    try:
                        need_close = list(reversed(self._context)).index(tag[:-1])+1
                    except ValueError:
                        self._error(SyntaxError, 'missing opening tag for in-line tag \\{0}',tag)
            elif tok == eol:
                if self._context:
                    need_close = len(self._context)-1
            else:
                # A text token without a context is a bare text line, in SFM 
                # this would probably be an error however in USFM it's permissable so
                # we'll log it as a warning.
                if not self.context:
                    tag = tokens.next()
                    if tag != eol:
                        self._error(SyntaxWarning, 'in-line tag \\{0} used outside of a marker',tag)
                yield event.text(self.context, tok)
            # This loop closes any open tags between the top of opened and
            # the opening tag for this closing tag.
            if need_close:
                need_close -= 1
                while need_close:
                    need_close -= 1
                    self._error(SyntaxWarning, 'expected closing tag at {col}, for in-line tag \\{0}',self.context)
                    tag = self._context.pop()
                    yield event.end(self.context, tag)
                tag = self._context.pop()
                yield event.end(self.context, tag)



class handler(object):
    def __init__(self):
        self.errors = []
    def start(self, ctag, tag, pos): return tag
    def text(self, ctag, text, pos): return text
    def end(self, ctag, tag, pos):   return tag
    def error(self, *warn_msg):      self.errors.append(warnings.WarningMessage(*warn_msg))


def transduce(handler, source):
    events = parser(source)
    line = ''
    
    with warnings.catch_warnings():
        warnings.showwarning = handler.error
        warnings.resetwarnings()
        warnings.simplefilter("always", SyntaxWarning)
        
        for ev in events:
            if event.isstart(ev):
                if ev.context: line += ' '
                line += '\\' + handler.start(*ev + (events.pos,))
            elif event.isend(ev):
                if ev.context:
                    line += '\\' + handler.end(*ev + (events.pos,)) + '*'
                else:
                    yield line + '\n'
                    line = ''
            elif event.istext(ev):
                text = handler.text(*ev + (events.pos,))
                if ev.context:
                    line += ' ' + text
                else:
                    yield line + text + '\n'
                    line = '' 
        if line: yield line


def parse(handler,source):
    for _ in transduce(handler,source): pass


if __name__ == '__main__':
    import palaso.sfm.usfm as usfm
    import sfm
    import sys, codecs
    mat=codecs.open(sys.argv[1],'rb',encoding='utf-8_sig')
    out=codecs.open(sys.argv[2],'wb',encoding='utf-8',buffering=1)
    out.writelines(sfm.transduce(sfm.handler(), mat))

#    with warnings.catch_warnings():
#        warnings.simplefilter("ignore",sfm.SyntaxWarning)
#        for ev in sfm.parser(mat):
#            if   sfm.event.isstart(ev): fmt = u'start: ctxt={0:8} {1}\n'
#            elif sfm.event.isend(ev):   fmt = u'  end: ctxt={0:8} {1}\n'
#            elif sfm.event.istext(ev):  fmt = u' text: ctxt={0:8} {1:.20}\n'
#            out.write(fmt.format(ev[0],ev[1].rstrip()))

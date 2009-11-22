#!/usr/bin/env python
'''
Created on Oct 31, 2009

@author: tim
'''
import re, collections, warnings
from itertools import chain

import event

eol = '\n'
endofline = ('\r\n','\n','\n\r')

pos    = collections.namedtuple('pos', 'line col')

class SyntaxWarning(SyntaxWarning): pass

def ismarker(tok): return tok and tok[0] == '\\'


class parser(object):
    def __init__(self, source):
        self.source = source.name if hasattr(source,'name') else '<string>'
        self._events = self.__scanner(self.__tokens(source.splitlines(True) if isinstance(source,basestring) else source))
    
    def __iter__(self): return self._events
    
    def _error(self, err_type, msg, ev, *args, **kwds):
        if issubclass(err_type, StandardError):
            msg = ('{source}: line {event.pos.line},{event.pos.col}: '+msg).format(event=ev,source=self.source,
                                                               *args)
            raise err_type, msg
        elif issubclass(err_type, Warning):
            msg = msg.format(event=ev,*args,**kwds)
            warnings.warn_explicit(msg, err_type, self.source, ev.pos.line)
        else:
            raise ValueError, "'{0!r}' is not an StandardError or Warning object".format(err_type)

    @staticmethod
    def __tokens(source):
        tokenise = re.compile(r'(\\[^\\\s]+|(?:^|$|(?<=[ \t]))[^\\]*)',re.U)        
        nlines = 1
        for line_no,line in enumerate(source):
            for m in tokenise.finditer(line):
                tok = m.group(1)
                if not tok: continue
                yield (pos(line_no+1,m.start(1)+1), tok)


    @staticmethod
    def __scanner(tokens):
        return (event.start(None, tok[1:], p) if ismarker(tok) else event.text(None, tok, p) for p,tok in tokens)



class handler(object):
    def __init__(self):
        self.errors = []
    def start(self, pos, ctag, tag, params): return ' '.join([tag]+params)
    def text(self, pos, ctag, text): return text
    def end(self, pos, ctag, tag):   return ''
    def error(self, *warn_msg):      self.errors.append(warnings.WarningMessage(*warn_msg))


def transduce(parser, handler, source):
    with warnings.catch_warnings():
        warnings.showwarning = handler.error
        warnings.resetwarnings()
        warnings.simplefilter("always", SyntaxWarning)
        
        events = parser(source)
        line = ''
        textprefix = ''
    
        for ev in events:
            if event.isstart(ev):
                line += '\\' + handler.start(*ev)
                textprefix = ' '
            elif event.isend(ev):
                    tag = handler.end(*ev)
                    line += tag and '\\' + tag
                    textprefix = tag and ' '
            elif event.istext(ev):
                text = handler.text(*ev)
                line += text if text.startswith(endofline) else textprefix + text
                textprefix = ''
            lines = line.splitlines(True)
            if len(lines) > 1:
                for line in lines[:-1]: yield line
            if lines:
                line[0]
                if line.endswith(endofline):
                    yield line
                else: continue
            line = ''
        if line: 
            yield line


def parse(parser,handler,source):
    for _ in transduce(parser,handler,source): pass


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

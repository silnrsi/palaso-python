'''
Define the sfm parser event types it emits and utility functions and classes
'''
__date__    = 'Nov 3, 2009'
__author__  = 'Tim Eves <tim_eves@sil.org>'

from collections import namedtuple


class _start(namedtuple('start', 'pos context tag params')):
    '''
    Represents a start event
    
    >>> start(None,'test').type
    'start'
    
    >>> start(None, 'test')
    start(pos=None, context=None, tag='test', params=[])
    
    >>> start(context='marker', tag='inline-tag')
    start(pos=None, context='marker', tag='inline-tag', params=[])
    
    >>> start(None, 'c',params=['32'])
    start(pos=None, context=None, tag='c', params=['32'])
    
    >>> str(start(None,'test')); str(start('marker', 'inline-tag')); str(start('c', 'v',params=['11']))
    'start{} test'
    'start{marker} inline-tag'
    'start{c} v 11'
    '''
    type = 'start'
    def __str__(self):  return 'start{{{1}}} {2}{3}'.format('',self.context or '', self.tag, ' '.join([''] + self.params))

 


class _text(namedtuple('text', 'pos context text')):
    '''
    Represents a start event
    
    >>> text(None,'test').type
    'text'
    
    >>> text(None, 'some test text')
    text(pos=None, context=None, text='some test text')
    
    >>> text(context='marker', text='some test text')
    text(pos=None, context='marker', text='some test text')
    
    >>> str(text(None,'hello')); str(text('marker', 'world'))
    "text{} 'hello'"
    "text{marker} 'world'"
    '''
    type = 'text'
    def __str__(self): return 'text{{{0}}} {1!r}'.format(self.context or '', self.text)



class _end(namedtuple('end', 'pos context tag')):
    '''
    Represents a start event
    
    >>> end(None,'test').type
    'end'
    
    >>> end(None, 'test')
    end(pos=None, context=None, tag='test')
    
    >>> end(context='marker', tag='inline-tag')
    end(pos=None, context='marker', tag='inline-tag')
    
    >>> str(end(None,'test')); str(end('marker', 'inline-tag'))
    'end{} test'
    'end{marker} inline-tag'
    '''
    type = 'end'
    def __str__(self): return 'end{{{0}}} {1}'.format(self.context or '', self.tag)


def start(context,tag,pos=None,params=[]):  return _start(pos,context,tag,params)
def text(context,text,pos=None):            return _text(pos,context,text)
def end(context,tag,pos=None):              return _end(pos,context,tag)

def isstart(e): return isinstance(e,_start)
def istext(e):  return isinstance(e,_text)
def isend(e):   return isinstance(e,_end)

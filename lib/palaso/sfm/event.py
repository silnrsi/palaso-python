'''
Define the sfm parser event types it emits and utility functions and classes
'''
__date__    = 'Nov 3, 2009'
__author__  = 'Tim Eves <tim_eves@sil.org>'

from collections import namedtuple


class start(namedtuple('start', 'context tag')):
    '''
    Represents a start event
    
    >>> start(None,'test').type
    'start'
    
    >>> start(None, 'test')
    start(context=None, tag='test')
    
    >>> start(context='marker', tag='inline-tag')
    start(context='marker', tag='inline-tag')
    
    >>> str(start(None,'test')); str(start('marker', 'inline-tag'))
    'start{} test'
    'start{marker} inline-tag'
    '''
    type = property(lambda _:'start')
    def __str__(self):  return 'start{{{0}}} {1}'.format(self.context or '', self.tag)

 


class text(namedtuple('text', 'context text')):
    '''
    Represents a start event
    
    >>> text(None,'test').type
    'text'
    
    >>> text(None, 'some test text')
    text(context=None, text='some test text')
    
    >>> text(context='marker', text='some test text')
    text(context='marker', text='some test text')
    
    >>> str(text(None,'hello')); str(text('marker', 'world'))
    "text{} 'hello'"
    "text{marker} 'world'"
    '''
    type = property(lambda _:'text')
    def __str__(self): return 'text{{{0}}} {1!r}'.format(self.context or '', self.text)



class end(namedtuple('end', 'context tag')):
    '''
    Represents a start event
    
    >>> end(None,'test').type
    'end'
    
    >>> end(None, 'test')
    end(context=None, tag='test')
    
    >>> end(context='marker', tag='inline-tag')
    end(context='marker', tag='inline-tag')
    
    >>> str(end(None,'test')); str(end('marker', 'inline-tag'))
    'end{} test'
    'end{marker} inline-tag'
    '''
    type = property(lambda _:'end')
    def __str__(self): return 'end{{{0}}} {1}'.format(self.context or '', self.tag)



def isstart(e): return isinstance(e,start)
def istext(e):  return isinstance(e,text)
def isend(e):   return isinstance(e,end)

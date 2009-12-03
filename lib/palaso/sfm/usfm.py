# -*- coding: utf-8 -*-
'''
This is the SFM definition module. It provides guidence on how the 
palaso.sfm.parse module will act as it parses SFM text.
Default types of SFM text should be defined here
'''
__version__ = '20091026'
__date__    = '26 October 2009'
__author__  = 'Dennis Drescher <dennis_drescher@sil.org>'
__history__ = '''
	20081210 - djd - Seperated SFM definitions from the module
		to allow for parsing other kinds of SFM models
		Also changed the name to parse_sfm.py as the
		module is more generalized now
	20091026 - tse - renamed and refactored generatoion of markers
		dict to module import time as part of import into palaso 
		package.
'''
import palaso.sfm as sfm
from palaso.sfm import event
import collections, re, warnings

def istype(tag,type):   return type in types(tag)
def types(tag):         return markers.get(tag,['isEnd','isChar'])
def isinline(tag):      return istype(tag,'isInline')
def isnum(tag):         return istype(tag,'isNum')
def ischar(tag):        return istype(tag,'isChar')
def isendtag(tag):      return tag[-1] == '*' and isinline(tag[:-1])
def isnesting(tag):     return ischar(tag) or isinline(tag)
def endtag(tag):        return tag+'*' if isinline(tag) else ''
def opentag(tag):       return tag[:-1] if tag[-1] == '*'  and isinline(tag[:-1]) else ''

TOP = -1

	
		
class parser(sfm.parser):
	chap_no  = re.compile(r'\d+',re.UNICODE)
	verse_no = re.compile(r'\d+(-\d+)?',re.UNICODE)
	def __init__(self, source):
		super(parser,self).__init__(source)
		self._events = self.__scripture(self.__params(self.__contextualise(iter(self)))) 

	def __contextualise(self,events):
		contexts = [None]
		lastp = None
		for e in events:
			if event.isstart(e):
				if (isendtag(e.tag) 
				        or not isnesting(e.tag)):
					octxt = opentag(e.tag) if isendtag(e.tag) else None
					if octxt not in contexts:
						self._error(SyntaxError, 'missing opening tag for inline tag \\{event.tag}',e)
					while contexts[TOP] != octxt:
						ee = event.end(contexts[-2], contexts.pop(), lastp) 
						if isinline(ee.tag): self._error(sfm.SyntaxWarning, 'expected closing tag at {event.pos.col}, for in-line tag \\{event.tag}',ee)
						yield ee
				if e.tag == contexts[TOP] or isendtag(e.tag):
					yield event.end(contexts[-2], contexts.pop(), lastp)
				if not isendtag(e.tag):
					yield event.start(contexts[TOP], e.tag, e.pos)   
					contexts.append(e.tag)
			else:
				if isinline(contexts[TOP]) and e.text.endswith(sfm.endofline):
					text = e.text.rstrip('\r\n')
					yield event.text(contexts[TOP], text, e.pos)
					lastp = sfm.pos(e.pos.line,e.pos.col+len(text))
					while isinline(contexts[TOP]):
						ee = event.end(contexts[-2], contexts.pop(), lastp) 
						if isinline(ee.tag): self._error(sfm.SyntaxWarning, 'expected closing tag at end-of-line, for in-line tag \\{event.tag}',ee)
						yield ee
					yield event.text(contexts[TOP], '\n', lastp)
				else:
					yield event.text(contexts[TOP], e.text, e.pos)
			lastp = sfm.pos(e.pos.line,e.pos.col+len(e[2]))
		while contexts[TOP]:
			e = event.end(contexts[-2], contexts.pop(), lastp)
			if isinline(e.tag):
				self._error(sfm.SyntaxWarning, 'expected closing tag at {event.pos.col}, for in-line tag \\{event.tag}',e)
			yield e


	def __params(self,events):
		for e in events:
			if event.isstart(e) and isnum(e.tag):
				try:
					params = events.next()
					if not event.istext(params): raise StopIteration
				except StopIteration:
					self._error(SyntaxError, 'missing required number parameter for \\{0}', params, e.tag)
				ps = params.text.split(' ',1)
				if ps[0].endswith(sfm.endofline): 
					ps[0] = ps[0].rstrip('\r\n')
					ps.append('\n')
				yield event.start(e.context, e.tag, e.pos, ps[:1])
				if len(ps) > 1 and ps[1]:
					yield event.text(e.tag, ps[1], sfm.pos(params.pos.line,params.pos.col+len(ps[0])))
			else:
				yield e


	def __scripture(self,events):
		ref = (None,None,None)
		for e in events:
			if event.isstart(e):
				try:
					if e.tag == 'c':    ref = (ref[0],self.chap_no.match(e.params[0]).group(),ref[2]) 
					elif e.tag == 'v':  ref = (ref[0],ref[1],self.verse_no.match(e.params[0]).group())
					elif e.tag == 'id': ref = (None,None,None)
				except AttributeError:
					self._error(ValueError, '\\{event.tag} parameter {event.params[0]!r} is not a number or range', e)
			elif event.istext(e) and e.context == 'id':
				try:    ref = (e.text.split(None,1)[0].strip(),None,None)
				except: self._error(SyntaxError, 'missing required book name on \\id tag',e)
#			elif event.isend(e):
#				if   e.tag == 'c':  ref = (ref[0],None,None)
#				elif e.tag == 'v':  ref = (ref[0],ref[1],None)					
			yield getattr(event,'_'+e.type)(pos(*e.pos+ref),*e[1:])
					
pos = collections.namedtuple('pos', 'line col book chapter verse')

class handler(sfm.handler):
    def __init__(self):
        self.errors = []
    def start(self, pos, ctag, tag, params): return ' '.join([tag]+params)
    def text(self, pos, ctag, text): return text
    def end(self, pos, ctag, tag):   return endtag(tag)
    def error(self, *warn_msg):      self.errors.append(warnings.WarningMessage(*warn_msg))

# Initialize markers with global defaults for USFM standard.
markers = {
# Attributes for common USFM markers
    'id'		: ['isNonV', 'isNonPub'],
	'ide'		: ['isNonV', 'isNonPub'],
	'rem'		: ['isNonV', 'isNonPub'],
	'c'			: ['isNum'],
	'v'			: ['isNum', 'isChar'],
	'va'		: ['isEnd', 'isChar', 'isInline'],
	'vp'		: ['isEnd', 'isChar', 'isInline'],
	'qs'		: ['isEnd', 'isChar', 'isInline'],
	'qac'		: ['isEnd', 'isChar', 'isInline'],
	'f'			: ['isEnd', 'isChar', 'isNote', 'isNonPub', 'isInline'],
	'fe'		: ['isEnd', 'isChar', 'isNote', 'isInline'],
	'fr'		: ['isChar', 'isNote', 'isInline', 'isRef'],
	'fk'		: ['isChar', 'isNote', 'isInline'],
	'ft'		: ['isChar', 'isNote', 'isInline'],
	'fq'		: ['isChar', 'isNote', 'isInline'],
	'fqa'		: ['isChar', 'isNote', 'isInline'],
	'fl'		: ['isChar', 'isNote', 'isInline'],
	'fp'		: ['isChar', 'isNote', 'isInline'],
	'fv'		: ['isChar', 'isNote', 'isInline'],
	'fdc'		: ['isEnd', 'isChar', 'isNote', 'isInline'],
	'fm'		: ['isEnd', 'isChar', 'isNote', 'isInline'],
	'x'			: ['isEnd', 'isChar', 'isNote', 'isNonPub', 'isInline'],
	'xo'		: ['isChar', 'isNote', 'isInline', 'isRef'],
	'xt'		: ['isChar', 'isNote', 'isInline'],
	'xk'		: ['isChar', 'isNote', 'isInline'],
	'xq'		: ['isChar', 'isNote', 'isInline'],
	'xdc'		: ['isEnd', 'isChar', 'isNote', 'isInline'],
	'qt'		: ['isEnd', 'isChar', 'isInline'],
	'nd'		: ['isEnd', 'isChar', 'isInline'],
	'tl'		: ['isEnd', 'isChar', 'isInline'],
	'dc'		: ['isEnd', 'isChar', 'isInline'],
	'bk'		: ['isEnd', 'isChar', 'isInline'],
	'sig'		: ['isEnd', 'isChar', 'isInline'],
	'pn'		: ['isEnd', 'isChar', 'isInline'],
	'k'			: ['isEnd', 'isChar', 'isInline'],
	'sls'		: ['isEnd', 'isChar', 'isInline'],
	'add'		: ['isEnd', 'isChar', 'isInline'],
	'ord'		: ['isEnd', 'isChar', 'isInline'],
	'no'		: ['isEnd', 'isChar', 'isInline'],
	'it'		: ['isEnd', 'isChar', 'isInline', 'isFormat'],
	'bd'		: ['isEnd', 'isChar', 'isInline', 'isFormat'],
	'bdit'		: ['isEnd', 'isChar', 'isInline', 'isFormat'],
	'em'		: ['isEnd', 'isChar', 'isInline'],
	'sc'		: ['isEnd', 'isChar', 'isInline'],
	'pb'		: ['isEmpty'],
	'pro'		: ['isEnd', 'isNonPub', 'isChar', 'isInline'],
	'w'			: ['isEnd', 'isChar', 'isInline'],
	'wg'		: ['isEnd', 'isChar', 'isInline'],
	'wh'		: ['isEnd', 'isChar', 'isInline'],
	'wj'		: ['isEnd', 'isChar', 'isInline'],
	'ndx'		: ['isEnd', 'isChar', 'isInline'],
	'periph'	: ['isNonPub', 'isNonV'],
	'efm'		: ['isEnd', 'isChar', 'isNonV', 'isNote', 'isInline'],
	'ef'		: ['isEnd', 'isNote', 'isNonPub'],
	'fig'		: ['isEnd', 'isInline', 'isNonV'],
# Normal paragraph elements and attributes
	'p'			: ['isPara', 'isChar'],
	'm'			: ['isPara', 'isChar'],
	'pmo'		: ['isPara', 'isChar'],
	'pm'		: ['isPara', 'isChar'],
	'pmc'		: ['isPara', 'isChar'],
	'pmr'		: ['isPara', 'isChar'],
	'mi'		: ['isPara', 'isChar'],
	'nb'		: ['isPara', 'isChar'],
	'cls'		: ['isPara', 'isChar'],
	'pc'		: ['isPara', 'isChar'],
	'pr'		: ['isPara', 'isChar'],
	'b'			: ['isPara', 'isChar'],
# Introduction elements and attributes. This will not contain numbered
# 	elements
#	'ip'			: ['isPara', 'isChar', 'isIntro'],
#	'ipi'			: ['isPara', 'isChar', 'isIntro'],
#	'im'			: ['isPara', 'isChar', 'isIntro'],
#	'imi'			: ['isPara', 'isChar', 'isIntro'],
#	'ipq'			: ['isPara', 'isChar', 'isIntro'],
#	'imq'			: ['isPara', 'isChar', 'isIntro'],
#	'ipr'			: ['isPara', 'isChar', 'isIntro'],
#	'ib'			: ['isPara', 'isChar', 'isIntro'],
#	'iot'			: ['isPara', 'isChar', 'isIntro'],
#	'iex'			: ['isPara', 'isChar', 'isIntro'],
#	'imte'			: ['isPara', 'isChar', 'isIntro'],
#	'ie'			: ['isPara', 'isChar', 'isIntro'],
#	'ior'			: ['isEnd', 'isChar', 'isInline', 'isIntro']
}


# Attributes for para markers with levels, including poetry 
_v  = ['isPara', 'isChar']
_t = dict((k,_v) for k in ('pi', 'li', 'ili', 'ph', 'q', 'iq'))
markers.update(((k+str(n), _v) for k in _t for n in range(1, 4)), **_t)

# Attributes for heading markers with levels. This can be
# used for all kinds of title markers that use level numbers
# since the range is always 1-4
_v = ['isTitle', 'isChar']
_t = dict((k,_v) for k in ('h', 'mt', 'mte', 'ms', 's', 'imt', 'is', 'io'))
markers.update(((k+str(n), _v) for k in _t for n in range(1, 4)), **_t)

# Attributes for reference markers
_v = ['isTitle', 'isChar']
markers.update((k,_v) for k in ('mr', 'sr', 'r', 'rq', 'd', 'sp'))

# Attributes for table markers
_v = ['isEnd', 'isChar']
markers.update((k+str(n),_v) for k in ('th', 'tc', 'thr', 'tcr') for n in range(1, 4))

# Supplemental, non-USFM markup used in peripheral material
_v = ['isPara', 'isTitle', 'isChar']
markers.update(('ct' + str(n), _v) for n in range(1, 4))

markers.update(spacer=['isFormat'],
			   tah=['isEnd', 'isChar', 'isInline', 'isFormat'],
			   tar=['isEnd', 'isChar', 'isInline', 'isFormat'])			


if __name__ == '__main__':
	print [str(e) for e in parser(r'\test \fr\fk deep text\fr*')]
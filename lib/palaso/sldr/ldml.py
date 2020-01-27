# -*- coding: utf-8

from __future__ import print_function

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from xml.etree import ElementTree as et
from xml.etree import ElementPath as ep
import re, os, codecs
import xml.parsers.expat
import functools
#from six import string_types
from .py3xmlparser import XMLParser, TreeBuilder

try:
    basestring
    string_types = basestring
except NameError:
    string_types = str

def iterate_files(root, ext=".xml"):
    """ Iterate a directory and subdirectories finding files with given extension """
    return sorted(functools.reduce(lambda a,x: a + x,
            ([os.path.join(w[0], f) for f in w[2] if f.endswith(ext)]
                    for w in os.walk(root)), []))

_elementprotect = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;' }
_attribprotect = dict(_elementprotect)
_attribprotect['"'] = '&quot;'

class ETWriter(object):
    """ General purpose ElementTree pretty printer complete with options for attribute order
        beyond simple sorting, and which elements should use cdata """

    nscount = 0
    indent = "\t"

    def __init__(self, et, namespaces = None, attributeOrder = {}, takesCData = set()):
        self.root = et
        if namespaces is not None:
            self.namespaces = namespaces
        if self.namespaces is None:
            self.namespaces = {'http://www.w3.org/XML/1998/namespaces': 'xml'}
        self.attributeOrder = attributeOrder
        self.takesCData = takesCData

    def _localisens(self, tag):
        ''' Convert {url}localname into ns:localname'''
        if tag[0] == '{':
            ns, localname = tag[1:].split('}', 1)
            qname = self.namespaces.get(ns, '')
            if qname:
                return ('{}:{}'.format(qname, localname), qname, ns)
            else:
                self.nscount += 1
                return (localname, 'ns' + str(self.nscount), ns)
        else:
            return (tag, None, None)

    def _protect(self, txt, base=_attribprotect):
        ''' Turn key characters into entities'''
        return re.sub(u'['+u"".join(base.keys())+u"]", lambda m: base[m.group(0)], txt)

    def _nsprotectattribs(self, attribs, localattribs, namespaces):
        ''' Prepare attributes for output by protecting, converting ns: form
            and collecting any xmlns attributes needing to be added'''
        if attribs is not None:
            for k, v in attribs.items():
                (lt, lq, lns) = self._localisens(k)
                if lns and lns not in namespaces:
                    namespaces[lns] = lq
                    localattribs['xmlns:'+lq] = lns
                localattribs[lt] = v
        
    def _sortedattrs(self, n, attribs=None):
        ''' Sorts attributes into appropriate attributes order'''
        def getorder(x):
            return self.attributeOrder.get(n.tag, {}).get(x, self.maxAts)
        return sorted((attribs if attribs is not None else n.keys()), key=lambda x:(getorder(x), x))

    def serialize_xml(self, write, base = None, indent = '', topns = True, namespaces = {}):
        """ Output the object using write() in a normalised way:
            topns if set puts all namespaces in root element else put them as low as possible"""
        if base is None:
            base = self.root
            write('<?xml version="1.0" encoding="utf-8"?>\n')
            namespaces['http://www.w3.org/XML/1998/namespace'] = 'xml'
        (tag, q, ns) = self._localisens(base.tag)
        localattribs = {}
        if ns and ns not in namespaces:
            namespaces[ns] = q
            localattribs['xmlns:'+q] = ns
        if topns:
            if base == self.root:
                for n,q in self.namespaces.items():
                    if q == "xml": continue
                    localattribs['xmlns:'+q] = n
                    namespaces[n] = q
        else:
            for c in base:
                (lt, lq, lns) = self._localisens(c.tag)
                if lns and lns not in namespaces:
                    namespaces[lns] = q
                    localattribs['xmlns:'+lq] = lns
        self._nsprotectattribs(getattr(base, 'attrib', None), localattribs, namespaces)
        for c in getattr(base, 'comments', []):
            write(u'{}<!--{}-->\n'.format(indent, c))
        write(u'{}<{}'.format(indent, tag))
        if len(localattribs):
            def getorder(x):
                return self.attributeOrder.get(tag, {}).get(x, self.maxAts)
            def cmpattrib(x, y):
                return cmp(getorder(x), getorder(y)) or cmp(x, y)
            for k in self._sortedattrs(base, localattribs):
                write(u' {}="{}"'.format(self._localisens(k)[0], self._protect(localattribs[k])))
        if len(base):
            write('>\n')
            for b in base:
                self.serialize_xml(write, base=b, indent=indent + self.indent, topns=topns, namespaces=namespaces.copy())
            write('{}</{}>\n'.format(indent, tag))
        elif base.text:
            if tag not in self.takesCData:
                t = self._protect(base.text.replace('\n', '\n' + indent), base=_elementprotect)
            else:
                t = "<![CDATA[\n\t" + indent + base.text.replace('\n', '\n\t' + indent) + "\n" + indent + "]]>"
            write(u'>{}</{}>\n'.format(t, tag))
        else:
            write('/>\n')
        for c in getattr(base, 'commentsafter', []):
            write(u'{}<!--{}-->\n'.format(indent, c))

    def save_as(self, fname, base = None, indent = '', topns = False, namespaces = {}):
        """ A more comfortable serialize_xml using a filename"""
        with codecs.open(fname, "w", encoding="utf-8") as outf:
            self.serialize_xml(outf.write, base=base, indent=indent, topns=topns, namespaces=namespaces)

    def add_namespace(self, q, ns):
        """ Adds a namespace mapping"""
        if ns in self.namespaces: return self.namespaces[ns]
        self.namespaces[ns] = q
        return q

    def addnode(self, parent, tag, **kw):
        """ Appends a new node to a parent, returning the new node.
            Empty (None) attributes are stripped"""
        kw = dict((k, v) for k, v in kw.items() if v is not None)
        return et.SubElement(parent, tag, **kw)

    def _reverselocalns(self, tag):
        ''' Convert ns:tag -> {url}tag'''
        nsi = tag.find(":")
        if nsi > 0:
            ns = tag[:nsi]
            for k, v in self.namespaces.items():
                if ns == v:
                    tag = "{" + k + "}" + tag[nsi+1:]
                    break
        return tag

    def subelement(self, parent, tag, **kw):
        """ Create a new SubElement and do localns replacement as in ns:tag -> {url}tag"""
        tag = self._reverselocalns(tag)
        kw = dict((self._reverselocalns(k), v) for k, v in kw.items() if v is not None)
        return et.SubElement(parent, tag, **k)


def etwrite(et, write, topns = True, namespaces = None):
    """ Converts an ElementTree into ETWriter and serialze_xml() on it"""
    if namespaces is None: namespaces = {}
    base = ETWriter(et, namespaces)
    base.serialize_xml(write, topns = topns)
    
_alldrafts = ('approved', 'contributed', 'provisional', 'unconfirmed', 'tentative', 'generated', 'suspect')
draftratings = dict(map(lambda x: (x[1], x[0]), enumerate(_alldrafts)))

class _minhash(object):
    ''' Hash class that can hash vectors. Also supports minimal hashing with hamming distance.'''
    _maxbits = 56
    _bits = 4
    _mask = 0xFFFFFFFFFFFFFFFF

    def __init__(self, hasher = hash, nominhash = True):
        self.minhash = None if nominhash else (1 << self._maxbits) - 1
        self.hashed = 0
        self.hasher = hasher

    def __eq__(self, other):
        return self.hashed == other.hashed and self.minhash == other.minhash

    def __repr__(self):
        return "<{} {:0X}>".format(type(self), self.hashed)

    def __hash__(self):
        return self.hashed

    def update(self, *vec):
        h = map(self.hasher, vec)
        if self.minhash is not None: map(self._minhashupdate, h)
        self.hashed = functools.reduce(lambda x,y:x * 1000003 + y, h, self.hashed) & self._mask

    def merge(self, aminh):
        if self.minhash is not None and aminh.minhash is not None: self._minhashupdate(aminh.minhash)
        self.hashed = (self.hashed * 1000003 + aminh.hashed) & self._mask

    def _minhashupdate(self, ahash):
        x = (1 << self._bits) - 1
        for i in range(self._maxbits / self._bits):
            if (ahash & x) < (self.minhash & x):
                self.minhash = (self.minhash & ~x) | (ahash & x)
            x <<= self._bits

    def hamming(self, amin):
        x = (1 << self._bits) - 1
        res = 0
        for i in range(self._maxbits / self._bits):
            if (self.minhash & x) != (amin & x): res += 1
            x <<= self._bits
        return res


class Ldml(ETWriter):
    takesCData = set(('cr',))
    silns = "urn://www.sil.org/ldml/0.1"
    use_draft = None

    @classmethod
    def ReadMetadata(cls, fname = None):
        """ Reads supplementalMetadata.xml from CLDR to get useful structural information on LDML"""
        cls.ReadDTD()
        if fname is None:
            fname = os.path.join(os.path.dirname(__file__), 'supplementalMetadata.xml')
        doc = et.parse(fname)
        base = doc.getroot().find('metadata')
        cls.variables = {}
        for v in base.findall('validity/variable'):
            name = v.get('id')[1:]
            if v.get('type') == 'choice':
                cls.variables[name] = v.text.split()
            elif v.text:
                cls.variables[name] = v.text.strip()
        cls.blocks = set(base.find('blocking/blockingItems').get('elements', '').split())
        cls.nonkeyContexts = {}         # cls.nonkeyContexts[element] = set(attributes)
        cls.keyContexts = {}            # cls.keyContexts[element] = set(attributes)
        cls.keys = set()
        for e in base.findall('distinguishing/distinguishingItems'):
            if 'elements' in e.attrib:
                if e.get('exclude', 'false') == 'true':
                    target = cls.nonkeyContexts
                else:
                    target = cls.keyContexts
                localset = set(e.get('attributes').split())
                for a in e.get('elements').split():
                    if a in target:
                        target[a].update(localset)
                    else:
                        target[a] = set(localset)
            else:
                cls.keys.update(e.get('attributes').split())
        cls.keyContexts['{'+cls.silns+'}matched-pair'] = set(['open', 'close'])
        cls.keyContexts['{'+cls.silns+'}quotation'] = set(['level'])

    @classmethod
    def ReadSupplementalData(cls, fname = None):
        """ Reads supplementalData.xml from CLDR to get useful structural information on LDML"""
        if fname is None:
            fname = os.path.join(os.path.dirname(__file__), 'supplementalData.xml')
        doc = et.parse(fname)
        cls.parentLocales = {}
        ps = doc.getroot().find('parentLocales')
        for p in ps.findall('parentLocale'):
            parent = p.get('parent')
            for l in p.get('locales').split():
                if l in cls.parentLocales:
                    cls.parentLocales[l].append(parent)
                else:
                    cls.parentLocales[l] = [parent]
    @classmethod
    def ReadDTD(cls, fname = None):
        """ Reads LDML DTD to get element and attribute orders"""
        if fname is None:
            fname = os.path.join(os.path.dirname(__file__), 'ldml.dtd')
        cls.elementCount = 0
        cls.attributeOrder = {}
        cls.elementOrder = {}
        attribCount = {}
        cls.maxEls = 0
        def procmodel(name, nodes, cls, elementCount):
            for n in nodes:
                if n[2] is not None:
                    elementCount += 1
                    cls.elementOrder.setdefault(name, {})[n[2]] = elementCount
                if len(n[3]):
                    elementCount = procmodel(name, n[3], cls, elementCount)
            return elementCount
        def elementDecl(name, model):
            elementCount = procmodel(name, model[3], cls, 0)
            cls.maxEls = max(cls.maxEls, elementCount + 1)
            cls.attributeOrder[name] = {}
            attribCount[name] = 0
        def attlistDecl(elname, attname, xmltype, default, required):
            attribCount[elname] += 1
            cls.attributeOrder[elname][attname] = attribCount[elname]
        parser = xml.parsers.expat.ParserCreate()
        parser.ElementDeclHandler = elementDecl
        parser.AttlistDeclHandler = attlistDecl
        with open(fname) as f :
            ldmltext = "".join(f.readlines())
        parsetext = "<?xml version='1.0'?>\n<!DOCTYPE LDML [\n" + ldmltext + "]>\n"
        parser.Parse(parsetext)
        cls.maxAts = max(attribCount.values()) + 1

    def __init__(self, fname, usedrafts=True, uparrows=False):
        if not hasattr(self, 'elementOrder'):
            self.__class__.ReadMetadata()
        self.namespaces = {'http://www.w3.org/XML/1998/namespace': 'xml'}
        self.namespaces[self.silns] = 'sil'
        self.useDrafts = usedrafts
        curr = None
        comments = []

        if fname is None:
            self.root = getattr(et, '_Element_Py', et.Element)('ldml')
            self.root.document = self
            self.default_draft = 'unconfirmed'
            return
        elif isinstance(fname, string_types):
            self.fname = fname
            fh = open(self.fname, 'rb')     # expat does utf-8 decoding itself. Don't do it twice
        else:
            fh = fname
        if hasattr(et, '_Element_Py'):
            tb = TreeBuilder(element_factory=et._Element_Py)
        else:
            tb = TreeBuilder()
        parser = XMLParser(target=tb, encoding="UTF-8")
        def doComment(data):
            # resubmit as new start tag=!-- and sort out in main loop
            parser.parser.StartElementHandler("!--", ('text', data))
            parser.parser.EndElementHandler("!--")
        parser.parser.CommentHandler = doComment
        for event, elem in et.iterparse(fh, events=('start', 'start-ns', 'end'), parser=parser):
            if event == 'start-ns':
                self.namespaces[elem[1]] = elem[0]
            elif event == 'start':
                elem.document = self
                if elem.tag == '!--':
                    comments.append(elem.get('text'))
                else:
                    if len(comments):
                        elem.comments = comments
                        comments = []
                    if curr is not None:
                        elem.parent = curr
                    else:
                        self.root = elem
                    curr = elem
            elif elem.tag == '!--':
                if curr is not None:
                    curr.remove(elem)
            else:
                if len(comments) and len(elem):
                    elem[-1].commentsafter = comments
                    comments = []
                curr = getattr(elem, 'parent', None)
                if not uparrows:
                    if elem.text == u"↑↑↑" or \
                                (getattr(elem, 'hasdeletedchild', False) and len(elem) == 0):
                        curr.remove(elem)
                        curr.hasdeletedchild = True
                    elif curr is not None:
                        curr.hasdeletedchild = False
        fh.close()
        self._analyse()
        self.normalise(self.root, usedrafts=usedrafts)

    def _copynode(self, n, parent=None):
        res = n.copy()
        for a in ('contentHash', 'attrHash', 'comments', 'commentsafter', 'parent', 'document'):
            if hasattr(n, a):
                setattr(res, a, getattr(n, a, None))
        if parent is not None:
            res.parent = parent
        return res

    def addnode(self, parent, tag, attrib=None, alt=None, **attribs):
        ''' Adds a node, keeping the best alternate at the front '''
        if attrib is not None:
            attrib = dict((k,v) for k,v in attrib.items() if v) # filter @x=""
        else:
            attrib = {}
        attrib.update(attribs)
        tag = self._reverselocalns(tag)
        e = parent.makeelement(tag, attrib)
        e.parent = parent
        e.document = parent.document
        if self.useDrafts:
            alt = self.alt(alt)
            if 'draft' not in e.attrib and self.use_draft is not None:
                e.set('draft', self.use_draft)
            self._calc_hashes(e, self.useDrafts)
            equivs = [x for x in parent if x.attrHash == e.attrHash]
            if len(equivs):
                if 'alt' not in e.attrib:
                    e.set('alt', alt)
                return self._add_alt_leaf(equivs[0], e, default=e.get('draft', None), leaf=True, alt=alt)
        parent.append(e)
        return e

    def _add_alt_leaf(self, target, origin, default='unconfirmed', leaf=True, alt=None):
        odraft = self.get_draft(origin, default)
        res = origin
        if leaf:
            tdraft = self.get_draft(target, default)
            if odraft < tdraft:
                self._promote(target, origin, alt=alt)
                (origin, target) = (target, origin)
                res = target
            if not hasattr(target, 'alternates'):
                target.alternates = {}
            elif alt in target.alternates:
                v = target.alternates[alt]
                if self.get_draft(v, default) < odraft:
                    return v
            target.alternates[alt] = origin
            if hasattr(origin, 'alternates'):
                for k, v in origin.alternates.items():
                    if k not in target.alternates or \
                            (self.get_draft(v, default) > self.get_draft(target.alternates[k], default)):
                        target.alternates[k] = v
        elif hasattr(target, 'alternates') and alt in target.alternates:
            v = target.alternates[alt]
            if self.get_draft(v, default) >= odraft:
                del target.alternates[alt]
        return res

    def _find_best(self, node, threshold=len(draftratings), alt=None):
        ''' Find the best alternate in node. The alt parameter chooses that alt
            if it is a possible winner'''
        maxr = len(draftratings)
        if not hasattr(node, 'alternates'):
            return None
        res = None
        if alt is not None:
            bestalt = node.alternates.get(alt, None)
            if bestalt is not None:
                bestalt = draftratings.get(bestalt.get('draft', None), maxr)
            else:
                bestalt = None
        else:
            bestalt = None

        for k, v in node.alternates.items():
            d = draftratings.get(v.get('draft', self.use_draft), maxr)
            if d < threshold:
                res = k
                threshold = d
        if bestalt is not None and threshold == bestalt:
            res = alt
        return res

    def _promote(self, old, new, alt=None):
        ''' promote the new alternate node to be the primary node instead of old '''
        nalt = getattr(new, 'alternates', None)
        oalt = getattr(old, 'alternates', {})
        if nalt is not None:
            old.alternates = nalt
        if oalt is not None:
            new.alternates = oalt
        if alt is None:
            alt = new.get('alt', None)
        elif 'alt' in new.attrib and new.attrib['alt'] in new.alternates:
            del new.alternates[new.attrib['alt']]
        new.alternates[alt] = old
        if 'alt' in new.attrib:
            del new.attrib['alt']
            old.set('alt', alt)
        for i, e in enumerate(old.parent):
            if id(e) == id(old):
                break
        old.parent.insert(i, new)
        old.parent.remove(old)
        return new

    def change_draft(self, node, draft, alt=None):
        ''' Change the draft on a node, moving it in the alts hierarchy if necessary. '''
        alt = self.alt(alt)
        best = self._find_best(node, draftratings.get(draft, len(draftratings)), alt=alt)
        node.set('draft', draft)
        if best is None:
            return node
        elif alt is None:
            alt = best
        return self._promote(node, node.alternates[best], alt=alt)

    def _add_inserted_node(self, before, draft, text, parent, tag, **kw):
        if draft is not None:
            kw['draft'] = draft
        se = self.addnode(parent, tag, **kw)
        if before is not None:
            for j, e in enumerate(parent):
                if e.tag == before:
                    parent.remove(se)
                    parent.insert(j, se)
                    break
        if text is not None:
            se.text = text
        return se

    def _unify_path(self, path, base=None, action="add", text=None, draft=None, alt=None, matchdraft=None, before=None):
        ''' Path contains a list of tags or (tag, attrs) to search in succession'''
        if base is None:
            base = self.root
        newcurr = [base]
        if matchdraft is not None:
            realalt = self.alt(alt)
        parent = base
        for i, p in enumerate(path):
            curr = newcurr
            newcurr = []
            if isinstance(p, tuple):
                tag, attrs = p
            else:
                tag, attrs = (p, {})
            for job in curr:
                for c in job:
                    if c.tag != tag:
                        continue
                    for k, v in attrs.items():
                        if c.get(k, '') != v:
                            break
                    else:
                        newcurr.append(c)
            if matchdraft is not None and i == len(path)-1:
                temp = newcurr
                newcurr = []
                # matchdraft == 'draft' (find all alternates with given draft, including not alternate)
                # matchdraft == 'alt' (find all alternates with given alt)
                # matchdraft == 'both' (find all alternates with given alt and draft)
                for c in temp:
                    if matchdraft == 'draft' and c.get('draft', '') == draft:
                        newcurr.append(c)
                    if not hasattr(c, 'alternates'):
                        continue
                    if matchdraft == 'draft':
                        tests = c.alternates.keys()
                    else:
                        tests = [realalt]
                    for r in (c.alternates.get(t, None) for t in tests):
                        if r is None:
                            continue
                        elif matchdraft == 'alt' or r.get('draft', '') == draft:
                            newcurr.append(r)
            if not len(newcurr):
                if action == "add":
                    newcurr.append(self._add_inserted_node(before, draft, text, parent, tag, attrib=attrs, alt=alt))
                else:
                    return []
            parent = newcurr[0]
        return newcurr

    def _process_path(self, path, base=None, action="add", text=None, draft=None, alt=None, matchdraft=None, before=None):
        draft = self.use_draft if draft is None else draft
        if path.startswith("/"):
            raise SyntaxError
        steps = []
        for s in path.split("/"):
            parts = re.split(r"\[(.*?)\]", s)
            tag = parts.pop(0)
            tag = self._reverselocalns(tag)
            if not len(parts):
                steps.append(tag)
                continue
            attrs = {}
            for p in parts:
                if not len(p): continue
                (k, v) = p.replace(' ','').split("=")
                if k.startswith("@") and v[0] in '"\'':
                    attrs[k[1:]] = v[1:-1]
            steps.append((tag, attrs))
        res = self._unify_path(steps, base=base, action=action, text=text, draft=draft, alt=alt, matchdraft=matchdraft, before=before)
        return (res, steps)

    def ensure_path(self, path, text=None, draft=None, alt=None, before=None, **kw):
        """ Find a node in a path and create any intermediate nodes, including the final, necessary
            Returns a list of nodes found, or created, even if only 1.
            If text is given, only return matching nodes, creating if necessary. If the draft of a matching
            string is worse then improve it."""
        (newcurr, steps) = self._process_path(path, action="add", text=text, draft=draft, alt=alt, **kw)
        if text is not None:
            curr = newcurr
            newcurr = []
            for job in curr:
                extras = [] if draft is None or not hasattr(job, 'alternates') else job.alternates.keys()
                for j in [job] + extras:
                    if j.text == text:
                        if draft is not None and self.get_draft(j) > draftratings.get(draft, len(draftratings)):
                            self.change_draft(j, draft, alt=alt)
                        newcurr.append(j)
            tag = steps[-1]
            if not isinstance(tag, str):
                tag = tag[0]
                attrs = tag[1]
            else:
                attrs = {}
            if not len(newcurr):
                newcurr.append(self._add_inserted_node(before, draft, text, curr[0].parent, tag, 
                    attrib = attrs, alt=alt))
        return newcurr

    def remove_path(self, path, **kw):
        """ Finds the given nodes from the path and deletes them.
            Takes same parameters as ensure_path. Returns nodes deleted. """
        newcurr, steps = self._process_path(path, action="remove", **kw)
        if len(newcurr):
            for c in newcurr:
                c.parent.remove(c)
        return newcurr

    def _invertns(self, ns):
        return {v:k for k, v in ns.items()}

    def find(self, path, elem=None, ns=None):
        return (elem or self.root).find(path, self._invertns(ns or self.namespaces))

    def findall(self, path, elem=None, ns=None):
        return (elem or self.root).findall(path, self._invertns(ns or self.namespaces))

    def get_parent_locales(self, thislangtag):
        """ Find the parent locales for this ldml, given its langtag"""
        if not hasattr(self, 'parentLocales'):
            self.__class__.ReadSupplementalData()
        fall = self.root.find('fallback')
        if fall is not None:
            return fall.split()
        elif thislangtag in self.parentLocales:
            return self.parentLocales[thislangtag]
        else:
            return []

    def normalise(self, base=None, addguids=True, usedrafts=False):
        """ Normalise according to LDML rules"""
        _digits = set('0123456789.')
        if base is None:
            base = self.root
        if len(base):
            for b in base:
                self.normalise(b, addguids=addguids, usedrafts=usedrafts)
            def getorder(x):
                return self.attributeOrder.get(base.tag, {}).get(x, self.maxAts)
            def cmpat(x, y):
                return cmp(getorder(x), getorder(y)) or cmp(x, y)
            def keyel(x):
                xl = self._sortedattrs(x)
                res = [self.elementOrder.get(base.tag, {}).get(x.tag, self.maxEls), x.tag]
                for k, a in ((l, x.get(l)) for l in xl):
                    if k == 'id' and all(q in _digits for q in a):
                        res += (k, float(a))
                    else:
                        res += (k, a)
                return res
            children = sorted(base, key=keyel)              # if base.tag not in self.blocks else list(base)
            base[:] = children
        if base.text:
            t = base.text.strip()
            base.text = re.sub(r'\s*\n\s*', '\n', t)       # content hash has text in lines
        base.tail = None
        if usedrafts or addguids:
            self._calc_hashes(base, usedrafts=usedrafts)
        if usedrafts:                                       # pack up all alternates
            temp = {}
            for c in base:
                a = c.get('alt', None)
                if a is None or a.find("proposed") == -1:
                    temp[c.attrHash] = c
            tbase = list(base)
            for c in tbase:
                a = c.get('alt', '')
                if a.find("proposed") != -1 and c.attrHash in temp:
                    #a = re.sub(r"-?proposed.*$", "", a)
                    t = temp[c.attrHash]
                    if not hasattr(t, 'alternates'):
                        t.alternates = {}
                    t.alternates[a] = c
                    base.remove(c)

    def _analyse(self):
        """ Pull out key information from the ldml for its processing."""
        identity = self.root.find('./identity/special/{' + self.silns + '}identity')
        if identity is not None:
            self.default_draft = identity.get('draft', 'unconfirmed')
            self.uid = identity.get('uid', None)
        else:
            self.default_draft = 'unconfirmed'
            self.uid = None

    def _distattributes(self, tag, usedrafts):
        ''' Return a list of distinguishing attributes for this tag'''
        distkeys = set(self.keys)
        if tag in self.nonkeyContexts:
            distkeys -= self.nonkeyContexts[tag]
        if tag in self.keyContexts:
            distkeys |= self.keyContexts[tag]
        if usedrafts:
            distkeys.discard('draft')
        return distkeys

    def _calc_hashes(self, base, usedrafts=False):
        ''' Calculate content and attribute hashes for this node and all children '''
        base.contentHash = _minhash(nominhash = True)
        for b in base:
            base.contentHash.merge(b.contentHash)
        if base.text: base.contentHash.update(*(base.text.split("\n")))
        distkeys = set(self.keys)
        if base.tag in self.nonkeyContexts:
            distkeys -= self.nonkeyContexts[base.tag]
        if base.tag in self.keyContexts:
            distkeys |= self.keyContexts[base.tag]
        if usedrafts:
            distkeys.discard('draft')
        base.attrHash = _minhash(nominhash = True)
        base.attrHash.update(base.tag)                      # keying hash has tag
        for k, v in sorted(base.items()):                      # any consistent order is fine
            if usedrafts and k == 'alt' and v.find("proposed") != -1:
                val = re.sub(r"-?proposed.*$", "", v)
                if len(val):
                    base.attrHash.update(k, val)
            elif k in distkeys:
                base.attrHash.update(k, v)        # keying hash has key attributes
            elif not usedrafts or (k != 'draft' and k != 'alt' and k != '{'+self.silns+'}alias'):
                base.contentHash.update(k, v)     # content hash has non key attributes
        base.contentHash.merge(base.attrHash)               #   and keying hash

    def as_xpath(self, n, usedrafts=False):
        """ Return an xpath description for this element """
        distkeys = self._distattributes(n.tag, usedrafts)
        p = getattr(n, 'parent', None)
        if p is None:
            return ""
        res = self.as_xpath(p, usedrafts=usedrafts)
        if len(res):
            res += "/" 
        tests = [(k, n.get(k)) for k in self._sortedattrs(n) if k in distkeys]
        res += n.tag + u"".join(u'[@{}="{}"]'.format(*x) for x in tests)
        return res

    def serialize_xml(self, write, base = None, indent = '', topns = True, namespaces = {}, nouid=True):
        """ Output this LDML to the given io stream """
        if base is None and self.uid is not None and not nouid:
            dstatus = self.use_draft
            self.use_draft = None
            self.ensure_path('identity/special/sil:identity[@uid="{}"]'.format(self.uid))
            self.use_draft = dstatus
        if self.useDrafts:
            n = base if base is not None else self.root
            draft = n.get('draft', '')
            if draft and (len(n) or draft == self.default_draft) and n.tag != "{" + self.silns + "}identity":
                del n.attrib['draft']
            offset = 0
            alt = n.get('alt', '')
            for (i, c) in enumerate(list(n)):
                if not hasattr(c, 'alternates'): continue
                for a in sorted(c.alternates.keys()):
                    c.alternates[a].set('alt', (alt+"-"+a if alt else a))
                    offset += 1
                    n.insert(i + offset, c.alternates[a])
                    c.alternates[a].tempnode = True
        super(Ldml, self).serialize_xml(write, base, indent, topns, namespaces)
        if self.useDrafts:
            n = base if base is not None else self.root
            for c in list(n):
                if hasattr(c, 'tempnode') and c.tempnode:
                    n.remove(c)

    def get_draft(self, e, default=None):
        """ Return a draft numeric level for this node """
        ldraft = e.get('draft', None) if e is not None else None
        if ldraft is not None: return draftratings.get(ldraft, 5)
        return draftratings.get(default, draftratings[self.default_draft])

    def resolve_aliases(self, this=None, _cache=None):
        """ Go through resolving aliases to actual content nodes """
        if this is None: this = self.root
        hasalias = False
        if _cache is None:
            _cache = set()
        for (i, c) in enumerate(list(this)):
            if c.tag == 'alias':
                v = c.get('path', None)
                if v is None: continue
                this.remove(c)
                count = 1
                for res in this.findall(v + "/*"):
                    res = self._copynode(res, parent=this)
                    if v in _cache:
                        print("Alias loop discovered: %s in %s" % (v, self.fname))
                        return True
                    _cache.add(v)
                    self.resolve_aliases(res, _cache)
                    _cache.remove(v)
                    this.insert(i+count, res)
                    count += 1
                hasalias = True
            else:
                hasalias |= self.resolve_aliases(c)
        if hasalias and self.useDrafts:
            self._calc_hashes(this)
            return True
        return False

    def alt(self, *a):
        """ Calculates an appropriate alt given up to two values:
                type - defaults to proposed
                context - may be missing
            It then appends the uid """
        proposed = a[0] if len(a) > 0 and a[0] else 'proposed'
        res = ((a[1] + "-") if len(a) > 1 and a[1] else "") + proposed
        if getattr(self, 'uid', None) is not None:
            return res + "-" + str(self.uid)
        else:
            return res
        
    def add_silidentity(self, **kws):
        """ Inserts attributes in identity/special/sil:identity"""
        s = self.ensure_path('identity/special/sil:identity')[0]
        for k, v in kws.items():
            s.set(k, v)

    def flatten_collation(self, collstr, importfn):
        """ Flattens [import] statements in a collation tailoring"""
        def doimport(m):
            return self.flatten_collation(importfn(m.group('lang'), m.group('coll')), importfn)
        return re.sub(r'\[import\s*(?P<lang>.*?)-u-co-(?P<coll>.*?)\s*\]', doimport, collstr)


def _prepare_parent(next, token):
    def select(context, result):
        for elem in result:
            if hasattr(elem, 'parent'):
                yield elem.parent
    return select
ep.ops['..'] = _prepare_parent


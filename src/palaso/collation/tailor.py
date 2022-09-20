"""Module to handle sort tailorings"""

import palaso.reggen
import re
import sys
import unicodedata
import warnings
import xml.sax
from functools import reduce
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

class Duplicate(RuntimeError) : 
    def __init__(self, str) :
        RuntimeError.__init__(self, str.encode('utf-8'))

class Multiple(RuntimeError) : pass

class LDMLHandler(xml.sax.ContentHandler) :
    def __init__(self, *args) :
        xml.sax.ContentHandler.__init__(self, *args)
        self.collations = []
        self.text = ""
        self.textelement = ""
        self.reorders = []
    def startElementNS(self, nsname, qname, attributes) :
        ns = 'www.palaso.org/ldml/0.1'
        tag = nsname[1]
        if nsname[0] == ns and nsname[1] == 'reorder' :
            self.currcollation.reorders.append((attributes.getValueByQName(attributes.getQNameByName((ns, 'match'))), attributes.getValueByQName(attributes.getQNameByName((ns, 'reorder')))))
        elif tag == 'collation' :
            self.currcollation = Collation(attributes.get('alt'))
            self.collations.append(self.currcollation)
            self.currcontext = None
        elif tag == 'settings' :
            for q in attributes.getNames() :
                v = attributes.getValue(q)
                self.currcollation.settings[q[1]] = v
        elif tag in ('first_variable', 'last_variable', 'first_tertiary_ignorable', 'last_tertiary_ignorable', 'first_secondary_ignorable', 'last_secondary_ignorable', 'first_primary_ignorable', 'last_primary_ignorable', 'first_non_ignorable', 'last_non_ignorable', 'first_trailing', 'last_trailing') :
            self.textelement = tag
        elif tag == 'cp' :
            self.text += chr(attributes.get('hex'))
        elif tag == 'reset' :
            self.resetattr = attributes.get('before')
        elif tag == 'x' :
            self.currcontext = Context()
        self.text = ''
    def endElementNS(self, nsname, qname) :
        tag = nsname[1]
        # self.text = self.text.strip()
        if tag == 'reset' :
            if self.textelement :
                self.currelement = self.currcollation.addreset(self.textelement, 1)
                self.textelement = None
            else :
                self.currelement = self.currcollation.addreset(self.text, 0)
            if self.resetattr :
                self.currelement.addbefore(self.resetattr[0])
                self.resetattr = None
        elif tag in ('p', 's', 't', 'q', 'i') :
            self.currelement = self.currelement.addElement(self.text, tag, self.currcontext)
        elif tag in ('pc', 'sc', 'tc', 'qc', 'ic') :
            for c in self.text :
                self.currelement = self.currelement.addElement(c, tag[0], self.currcontext)
        elif tag == 'x' :
            self.currcontext = None
        elif tag == 'context' :
            self.currcontext.context = self.text
        elif tag == 'extend' :
            self.currcontext.extend = self.text
        self.text = ''
    def characters(self, data) :
        self.text += data
    def asLDML(self, sax) :
        sax.startElement('collations', AttributesImpl({}))
        for c in self.collations :
            c.asLDML(sax)
        sax.endElement('collations')

class Collation :
    icu_relation_values = {'r' : 0, 'p' : 1, 's' : 2, 't' : 3, 'q' : 4, 'i' : 5}
    def __init__(self, type) :
        self.settings = {}
        self.rules = []
        self.type = type
        self.reorders = []
        self.flattened = 0
    def addreset(self, value, isSpecial, flattenrule=0) :
        element = Element(self)
        if isSpecial :
            element.special = value
        else :
            element.string = value
        element.relation = 'r'
        element.flattenrule = flattenrule
        self.rules.append(element)
        return element
    def addIdentity(self, reset, value, context=None) :
        e = self.addreset(reset, 0, flattenrule=1)
        e = e.addElement(value, 'i', context, flattenrule=1)
    def asICU(self) :
        strengths = {'primary' : '1', 'secondary' : '2', 'tertiary' : '3', 'quaternary' : '4'}
        res = ""
        for k, v in self.settings.items() :
            if k == 'backwards' and v == 'on' : v = '2'
            if k == 'hiraganaQuarternary' : k = 'hiraganaQ'
            if k == 'strength' : v = strengths[v]
            res = res + "[" + k + " " + v + "]\n"
        for r in self.rules :
            for e in r :
                res += e.asICU() + " "
            res += "\n"
        return res
    def asLDML(self, sax) :
        sax.startElement('collation', AttributesImpl({'type' : self.type} if self.type else {}))
        if len(self.settings) > 0 :
            sax.startElement('settings', AttributesImpl(self.settings))
            sax.endElement('settings')
        sax.startElement('rules', AttributesImpl({}))
        for r in self.rules :
            r.asLDML(sax)
        sax.endElement('rules')
        sax.endElement('collation')
    def getElements(self) :
        allstr = set()
        for r in self.rules :
            for e in r :
                for i in range(0, len(e.string)) :
                    allstr.add(e.string[0:i+1])
        return allstr
    def flattenOrders(self, debug = 0) :
        if self.flattened : return
        types = 'i', 'p', 's', 't', 'q'
        tailor = self.asICU()
        results = []
        inputs = {}
        outputs = {}
        ces = set()
        for r in self.reorders :
            for b, s in palaso.reggen.expand_sub(r[0], r[1], debug=debug) :
                if b == s : continue
                for bi in inputs :
                    if b != bi and b.find(bi) != -1 :
                        warnings.warn(("Input %s masked by %s" % (b, bi)).encode("utf-8"), UserWarning)
                        break
                inputs[b] = s
                if s in outputs :
                    outputs[s].append(b)
                else :
                    outputs[s] = [b]
                # add map for &output=input
                self.addIdentity(s, b)
                if debug :
                    print(("%s -> %s" % (b, s)).encode("utf-8"))

        # go through the rules collecting sequences which are collation elements
        # convert &abc < x -> &a < x/bc type thing everywhere
        # for each rhs that is the result of a regexp subst, create a corresponding original string
        # and add an identity (with a possible corresponding extension)
        for r in self.rules :
            expansion = None
            i = reduce(lambda m, x: max(m, x if r.string[0:x] in ces else 0), range(1, len(r.string)+1), 0)
            if i == 0 : i = 1
            if i < len(r.string) :
                expansion = Context()
                expansion.extend = r.string[i:]
                r.string = r.string[:i]
            elif r.flattenrule :
                continue
            for e in r :
                if e.relation != 'r' and expansion and not e.context :
                    e.context = expansion
                ces.add(e.string)
                if r.flattenrule or e.relation == 'r' or e.string in outputs : continue
                idents = (o for o in longestReplace(e.string, outputs) if o != e.string)
                for o in idents :
                    passed = False
                    for n in self.rules :
                        if n.relation != 'r' and n.string != e.string : continue
                        for f in n :
                            if f.string == o :
                                passed = True
                                break
                        if passed : break
                    if not passed :
                        self.addIdentity(e.string, o, context=e.context)
                        ces.add(o)
        self.flattened = 1
    def testPrimaryMultiple(self) :
        ces = set()
        res = []
        for r in self.rules :
            min = 10
            ok = (len(r.string) <= 1 or r.string in ces)
            for e in r :
                if e.relation != 'r' and e.string != '':
                    ces.add(e.string)
                val = self.icu_relation_values.get(e.relation, 0)
                if val > 0 and val < min : min = val
            if not ok and min == 1 :
                res.append(r.string)
        return res

class Element :
    icu_relation_map = {
        'r' : '&',
        'p' : '<',
        's' : '<<',
        't' : '<<<',
        'q' : '=',
        'i' : '=' }
    icu_protect = set([s for s in ' !"#$%^&\'()*+,-./:;<=>?[\\]^_`{|}~@'])
    icu_categories = set(['Zs', 'Zl', 'Zp', 'Cc', 'Cf'])
    def __init__(self, parent) :
        self.parent = parent
        self.special = None
        self.string = ""
        self.child = None
        self.context = None
        self.flattenrule = 0
    def __iter__(self) : return ElementIter(self)
    def addElement(self, string, type, context, flattenrule=0) :
        element = Element(self)
        element.string = string
        element.relation = type
        element.context = context
        element.flattenrule = flattenrule
        self.child = element
        return element
    def asICU(self) :
        res = str(Element.icu_relation_map[self.relation])
        if self.context and self.context.context :
            res += " " + self.context.context + "|"
        if self.special :
            command = self.special.replace('non_ignorable', 'regular')
            res += "[" + command.replace('_', ' ') + "]"
        else :
            st = self.string
            for s in self.string :
                if s in self.icu_protect or unicodedata.category(s) in self.icu_categories :
                    st = "'" + re.sub("['(]", "\\\1", st) + "'"
                    break
            res += " " + st
        if self.context and self.context.extend :
            res += "/" + self.context.extend
        return res
    def asLDML(self, sax, currcontext = None) :
        if not currcontext and self.context :
            sax.startElement('x', AttributesImpl({}))
            if self.context.context :
                sax.startElement('context', AttributesImpl({}))
                sax.characters(self.context.context)
                sax.endElement('context')
            currcontext = self.context
        tag = 'reset' if self.relation == 'r' else self.relation
        sax.startElement(tag, AttributesImpl({}))
        if self.special :
            sax.startElement(self.special, AttributesImpl({}))
            sax.endElement(self.special)
        else :
            sax.characters(self.string)
        sax.endElement(tag)
        
        if currcontext and (not self.child or self.child.context != currcontext) :
            if self.context.extend :
                sax.startElement('extend', AttributesImpl({}))
                sax.characters(self.context.extend)
                sax.endElement('extend')
            sax.endElement('x')
        currcontext = self.context

        if self.child :
            self.child.asLDML(sax, currcontext)

class ElementIter :
    def __init__(self, start) :
        self.curr = start
    def __iter__(self) : return self
    def __next__(self) :
        res = self.curr
        if not res : raise StopIteration()
        self.curr = res.child
        return res

class Context : 
    def __init__(self) :
        self.context = None
        self.extend = None

def overlap(base, str) :
    run = list(range(0, len(str)))
    return (base.find(str) != -1 or 
        base.endswith(tuple(str[0:i] for i in run)) or
        base.startswith(tuple(str[-i:] for i in run)))

def longestReplace(s, d) :
    i = reduce(lambda m, x: max(m, x if s[0:x] in d else 0), range(1, len(s)+1), 0)
    if i > 0 :
        for a in d[s[0:i]] :
            if i < len(s) :
                for y in longestReplace(s[i:], d) :
                    yield a + y
            else :
                yield a
    elif len(s) == 1 :
        yield s
    else :
        for y in longestReplace(s[1:], d) :
            yield s[0:1] + y

if __name__ == "__main__" :
    filename = sys.argv[1]
    print(filename)
    handler = LDMLHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
    parser.parse(filename)
    outsax = XMLGenerator()
    for c in handler.collations :
        print("---------- %s ----------" % (c.type))
        if len(c.reorders) > 0 :
            c.flattenOrders()
        print(c.asICU().encode('utf-8'))

    handler.asLDML(outsax)


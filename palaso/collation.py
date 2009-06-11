"""Module to handle sort tailorings"""

import xml.sax, sys, palaso.reggen
from xml.sax.xmlreader import AttributesImpl
from xml.sax.saxutils import XMLGenerator

class LDMLHandler(xml.sax.ContentHandler) :
    def startDocument(self) :
        self.collations = []
        self.text = ""
        self.textelement = ""
        self.reorders = []
    def startElement(self, tag, attributes) :
        if tag == 'collation' :
            self.currcollation = Collation(attributes.get('type'))
            self.collations.append(self.currcollation)
        elif tag == 'settings' :
            for q in attributes.getNames() :
                v = attributes.getValue(q)
                self.currcollation.settings[q] = v
        elif tag in ('first_variable', 'last_variable', 'first_tertiary_ignorable', 'last_tertiary_ignorable', 'first_secondary_ignorable', 'last_secondary_ignorable', 'first_primary_ignorable', 'last_primary_ignorable', 'first_non_ignorable', 'last_non_ignorable', 'first_trailing', 'last_trailing') :
            self.textelement = tag
        elif tag == 'cp' :
            self.text += unichr(attributes.get('hex'))
        elif tag == 'reset' :
            self.resetattr = attributes.get('before')

    def startElementNS(self, name, qname, attrs) :
        ns = 'www.palaso.org/ldml/0.1'
        if name[0] != ns : return
        if name[1] == 'reorder' :
            self.reorders.append((attrs.getValueByQName(attrs.getQNameByName((ns, 'match'))), attrs.getValueByQName(attrs.getQNameByName((ns, 'reorder')))))

    def endElement(self, tag) :
        self.text = self.text.strip()
        if tag == 'reset' :
            if self.textelement :
                self.currelement = self.currcollation.addreset(self.textelement, 1)
            else :
                self.currelement = self.currcollation.addreset(self.text, 0)
            if self.resetattr :
                self.currelement.addbefore(self.resetattr[0])
                self.resetattr = None
        elif tag in ('p', 's', 't', 'q', 'i') :
            self.currelement = self.currelement.addElement(self.text, tag)
        elif tag in ('pc', 'sc', 'tc', 'qc', 'ic') :
            for c in self.text :
                self.currelement = self.currelement.addElement(c, tag[0])
        self.text = ''

    def characters(self, data) :
        self.text += data

    def asLDML(self, sax) :
        sax.startElement('collations', AttributesImpl({}))
        for c in self.collations :
            c.asLDML(sax)
        sax.endElement('collations')

class Collation :
    def __init__(self, type) :
        self.settings = {}
        self.rules = []
        self.type = type
    def addrule(self, rule) :
        self.rules.append(rule)
    def addreset(self, value, isSpecial) :
        element = Element(self)
        if isSpecial :
            element.special = value
        else :
            element.string = value
        element.relation = 'r'
        self.rules.append(element)
        return element
    def asICU(self) :
        res = ""
        for k, v in self.settings.items() :
            res = res + "[" + k + " " + v + "]"
        for r in self.rules :
            res += r.asICU()
            res += "\n"
        return res
    def asLDML(self, sax) :
        sax.startElement('collation', AttributesImpl({'type' : self.type}))
        if len(self.settings) > 0 :
            sax.startElement('settings', AttributesImpl(self.settings))
            sax.endElement('settings')
        sax.startElement('rules', AttributesImpl({}))
        for r in self.rules :
            r.asLDML(sax)
        sax.endElement('rules')
        sax.endElement('collation')

class Element :
    icu_relation_map = {
        'r' : '&',
        'p' : '<',
        's' : '<<',
        't' : '<<<',
        'q' : '=',
        'i' : '=' }
    def __init__(self, parent) :
        self.parent = parent
        self.special = None
        self.string = ""
        self.child = None
    def addElement(self, string, type) :
        element = Element(self)
        element.string = string
        element.relation = type
        self.child = element
        return element
    def asICU(self) :
        res = Element.icu_relation_map[self.relation]
        if self.special :
            res += "[" + self.special.sub('_', ' ') + "]"
        else :
            res += self.string
        if self.child :
            res += self.child.asICU()
        return res
    def asLDML(self, sax) :
        tag = 'reset' if self.relation == 'r' else self.relation
        sax.startElement(tag , AttributesImpl({}))
        if self.special :
            sax.startElement(self.special, AttributesImpl({}))
            sax.endElement(self.special)
        else :
            sax.characters(self.string)
        sax.endElement(tag)
        if self.child :
            self.child.asLDML(sax)

def test(filename) :
    print filename
    handler = LDMLHandler()
    xml.sax.parse(filename, handler)
    outsax = XMLGenerator()
    for c in handler.collations :
        print "---------- %s ----------" % (c.type)
        print c.asICU().encode('utf-8')
    handler.asLDML(outsax)

if __name__ == "__main__" :
    test(sys.argv[1])


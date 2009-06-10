"""Module to handle sort tailorings"""

import xml.sax, sys

class LDMLHandler(xml.sax.ContentHandler) :
    def startDocument(self) :
        self.collations = []
        self.text = ""
        self.textelement = ""
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
        for r in self.rules :
            res += r.asICU()
            res += "\n"
        return res

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

def test(filename) :
    print filename
    handler = LDMLHandler()
    xml.sax.parse(filename, handler)
    for c in handler.collations :
        print "---------- %s ----------" % (c.type)
        print c.asICU().encode('utf-8')

if __name__ == "__main__" :
    test(sys.argv[1])


#!/usr/bin/env python3

import palaso.collation.tailor, xml.sax, sys, codecs

class Flattener(xml.sax.handler.ContentHandler) :
    def __init__(self, *args) :
#        super(Flattener, self).__init__(*args)
        xml.sax.handler.ContentHandler.__init__(self)
        self.processing = 0
        self.ldmlhandler = palaso.collation.tailor.LDMLHandler()
    def startElementNS(self, nsname, qname, attributes) :
        if nsname[1] == 'collations' :
            self.processing = 1
        if self.processing :
            self.ldmlhandler.startElementNS(nsname, qname, attributes)
    def endElementNS(self, nsname, qname) :
        if nsname[1] == 'collations' :
            for c in self.ldmlhandler.collations :
                if len(c.reorders) :
                    c.flattenOrders()
            self.processing = 0
            self.icu = ""
            for c in self.ldmlhandler.collations :
                self.icu = c.asICU()
        elif self.processing :
            self.ldmlhandler.endElementNS(nsname, qname)
    def characters(self, data) :
        if self.processing :
            self.ldmlhandler.characters(data)

def main(infile) :
    parser = xml.sax.make_parser()
    handler = Flattener(parser)
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
#    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
    parser.parse(infile)
    print(handler.icu)

if __name__ == "__main__" :
    main(sys.argv[1])

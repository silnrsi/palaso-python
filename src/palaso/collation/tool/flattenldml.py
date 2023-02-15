#!/usr/bin/env python3

import palaso.collation.tailor
import xml.sax
import xml.sax.handler
import xml.sax.saxutils
import sys


class Flattener(xml.sax.saxutils.XMLFilterBase):
    def __init__(self, *args):
        # super(Flattener, self).__init__(*args)
        xml.sax.saxutils.XMLFilterBase.__init__(self, *args)
        self.processing = 0
        self.ldmlhandler = palaso.collation.tailor.LDMLHandler()

    def startElementNS(self, nsname, qname, attributes):
        if nsname[1] == 'collations':
            self.processing = 1
        if self.processing:
            self.ldmlhandler.startElementNS(nsname, qname, attributes)
        else:
            xml.sax.saxutils.XMLFilterBase.startElementNS(
                self,
                nsname,
                qname,
                attributes)

    def endElementNS(self, nsname, qname):
        if not self.processing:
            xml.sax.saxutils.XMLFilterBase.endElementNS(self, nsname, qname)
        if nsname[1] == 'collations':
            for c in self.ldmlhandler.collations:
                if len(c.reorders):
                    c.flattenOrders()
            self.processing = 0
            self.ldmlhandler.asLDML(self)
        else:
            self.ldmlhandler.endElementNS(nsname, qname)

    def characters(self, data):
        if self.processing:
            self.ldmlhandler.characters(data)
        else:
            xml.sax.saxutils.XMLFilterBase.characters(self, data)


def main():
    infile = sys.argv[1]
    outfile = sys.argv[2]
    output = xml.sax.saxutils.XMLGenerator(open(outfile, "w"), "utf-8")
    parser = xml.sax.make_parser()
    handler = Flattener(parser)
    handler.setContentHandler(output)
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
    handler.parse(infile)


if __name__ == "__main__":
    main()

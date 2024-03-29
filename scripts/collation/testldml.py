#!/usr/bin/env python3

import sys, xml.sax, palaso, pprint, icu, re
from optparse import OptionParser
from palaso.collation import *
from palaso.contexts import defaultapp
from functools import reduce

with defaultapp() :
    usage = "%prog [options] codes"
    parser = OptionParser(usage)
    parser.add_option("-l", "--ldml", help = "LDML file containing collation")
    parser.add_option("-a", "--alt", help = "Optional alternate collation to use")
    parser.add_option("-d", "--depth", default = 15, help = "sort level")
    parser.add_option("-p", "--preprocess", action="store_true", help = "Preprocess strings rather than flatten")
    parser.add_option("-z", action="store_true")
    (options, args) = parser.parse_args()

    str = "".join(chr(int(s, 16)) for s in args)

    if options.ldml :
        handler = palaso.collation.tailor.LDMLHandler()
        ldmlparser = xml.sax.make_parser()
        ldmlparser.setContentHandler(handler)
        ldmlparser.setFeature(xml.sax.handler.feature_namespaces, 1)
        ldmlparser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
        ldmlparser.parse(options.ldml)
        if str:
            if len(handler.collations) :
                collation = handler.collations[0]
                for c in handler.collations :
                    if c.type == options.alt :
                        collation = c
                        break
                if not options.preprocess :
                    collation.flattenOrders(debug=options.z)
                tailor = collation.asICU()
            else :
                tailor = ""
    else :
        tailor = ""
    if str :
        if options.z :
            print(tailor.encode("utf-8"))
        icuCollation = icu.RuleBasedCollator(tailor, options.depth)
        if options.z :
            for s in sorted(collation.getElements()) :
                print("%s : %s" % (pprint.pformat(s), palaso.collation.icu.strkey(icuCollation.getCollationKey(s))))
        if options.preprocess and collation and collation.reorders :
            preproc = [(re.compile(p[0]), p[1]) for p in collation.reorders]
            str = reduce(lambda s, p: p[0].sub(p[1], s), preproc, str)
        print("%s : %s" % (pprint.pformat(str), palaso.collation.icu.strkey(icuCollation.getCollationKey(str))))
    else :
        print(options.ldml)
        sys.stderr.write(options.ldml + "\n")
        for collation in handler.collations: 
            print(f"--- {collation.type!s} ---")
            tailor = collation.asICU()
            if options.z : print(tailor.encode("utf-8"))
            icuCollation = icu.RuleBasedCollator(tailor, options.depth)
            for s in sorted(collation.getElements()) :
                print("%s : %s" % (pprint.pformat(s), palaso.collation.icu.strkey(icuCollation.getCollationKey(s))))

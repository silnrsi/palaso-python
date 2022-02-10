#!/usr/bin/env python3

import sys, xml.sax, palaso, pprint, icu, re, codecs
from optparse import OptionParser
from palaso.collation import *
from palaso.contexts import defaultapp
from contextlib import nested
from functools import reduce

with defaultapp() :
    usage = "%prog -l ldml_file [infile [outfile]]"
    parser = OptionParser(usage)
    parser.add_option("-l", "--ldml", help = "LDML file containing collation")
    parser.add_option("-i", "--icu", help = "ICU file containing collation")
    parser.add_option("-a", "--alt", help = "Optional alternate collation to use")
    parser.add_option("-d", "--depth", default = 15, type = int, help = "sort level")
    parser.add_option("-p", "--preprocess", action="store_true", help = "Preprocess strings rather than flatten")
    parser.add_option("--prefile", help = "Store preprocessed strings here")
    parser.add_option("-z", action="store_true")
    (options, args) = parser.parse_args()

    if len(args) > 0 :
        infile = codecs.open(args[0], "r", "utf-8")
    else :
        infile = sys.stdin

    if len(args) > 1 :
        outfile = codecs.open(args[1], "w", "utf-8")
    else :
        outfile = sys.stdout

    if options.ldml :
        handler = palaso.collation.tailor.LDMLHandler()
        ldmlparser = xml.sax.make_parser()
        ldmlparser.setContentHandler(handler)
        ldmlparser.setFeature(xml.sax.handler.feature_namespaces, 1)
        ldmlparser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
        ldmlparser.parse(options.ldml)
        collation = handler.collations[0]
        for c in handler.collations :
            if c.type == options.alt :
                collation = c
                break

        if not options.preprocess :
            collation.flattenOrders(debug=options.z)
            errors = collation.testPrimaryMultiple()
            for e in errors :
                sys.stderr.write("Reset with primary: " + e.encode('utf-8') + " has multiple elements\n")
        tailor = collation.asICU()
    elif options.icu :
        f = codecs.open(options.icu, encoding="utf8")
        tailor = "".join(f.readlines())
        f.close()
    else :
        tailor = ""
    results = palaso.collation.icu.sorted(tailor, infile.readlines(), level=options.depth, preproc = collation.reorders if options.preprocess else ())
    outfile.write("".join(results))
    if options.prefile :
        preprocs = [(re.compile(p[0]), p[1]) for p in collation.reorders]
        prefile = codecs.open(options.prefile, "w", "utf-8")
        for r in results :
            st = r.replace("\n", "")
            mods = reduce(lambda s, p: p[0].sub(p[1], s), preprocs, st)
            prefile.write(", ".join((st, mods)) + "\n")
    if options.z :
        print(tailor.encode("utf-8"))
        if collation :
            icuCollation = icu.RuleBasedCollator(tailor, options.depth)
            for s in palaso.collation.icu.sorted(tailor, collation.getElements(), level=options.depth, preproc = collation.reorders if options.preprocess else ()) :
                print("%s : %s" % (pprint.pformat(s), palaso.collation.icu.strkey(icuCollation.getCollationKey(s))))

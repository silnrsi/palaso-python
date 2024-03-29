#!/usr/bin/env python3

import icu
from optparse import OptionParser
from palaso.contexts import defaultapp

with defaultapp() :
    parser = OptionParser()
    parser.add_option("-i","--input",help="Break specification .txt file")
    parser.add_option("-c","--codes",action="store_true",help="final arguments are hex character codes")
    parser.add_option("-f","--file",help="Read text from file")
    parser.add_option("-s","--separator",default="|",help="Separator character")
    parser.add_option("-x","--hex",action="store_true",help="output in hex codes")
    (opts, args) = parser.parse_args()
    if not len(args) :
        parser.error("Insufficient arguments, try -h for help")

    if opts.input :
        spec = "".join(file(opts.input).readlines())
        brk = icu.RuleBasedBreakIterator(spec)
    else :
        brk = icu.RuleBasedBreakIterator()

    print(brk.getRules())

    if opts.codes :
        text = "".join(chr(int(x, 16)) for x in args)
    elif opts.file :
        text = "".join(file(args[0]).readlines())
    else :
        text = args[0]

    res = []
    brk.setText(icu.UnicodeString(text))
    last = brk.first()
    try :
        while True :
            next = brk.next()
#            print(next, " ", brk.getRuleStatus())
            res.append(text[last:next])
            last = next
    except :
        res.append(text[last:])

    if opts.hex :
        print(f" {opts.separator} ".join(
                " ".join(hex(ord(x)) for x in res)
                for y in res))
    else :
        print(opts.separator.join(res))


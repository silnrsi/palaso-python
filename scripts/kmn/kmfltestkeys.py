#!/usr/bin/env python3
'''
Given a sequence of key tops from a US 101 key keyboard or keyman symbol
notation on stdin print the key names followed by the output the keyman
keyboard would generate.  This allows us to try the keyboard without
needing to install it.
'''
__version__ = '1.0'
__date__ = '21 October 2009'
__author__ = 'Martin Hosken <martin_hosken@sil.org>'
import sys
from optparse import OptionParser
from palaso.contexts import defaultapp
from palaso.kmfl import kmfl
from palaso.kmn import keysyms_items

assert __doc__ is not None
parser = OptionParser(usage='%prog [options] <KEYMAN FILE>\n' + __doc__)
_, kmns = parser.parse_args()
if len(kmns) == 0:
    sys.stderr.write(parser.expand_prog_name('%prog: missing KEYMAN FILE\n'))
    parser.print_help(file=sys.stderr)
    sys.exit(1)

with defaultapp():
    k = kmfl(sys.argv[1])
    for ln in sys.stdin.readlines():
        r = k.run_items(keysyms_items(ln.strip()))
        print(f"{ln}\t{r}")

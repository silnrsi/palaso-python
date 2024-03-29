#!/usr/bin/env python3
'''
Generate a sorted list of all possible key presses that produce output 
for a keyman keyboard. The results of this program used as input for  
kmfltestkeys.  
Depending on the mode chosen this may take a long time to complete. 
'''
__version__ = '1.0'
__date__    = '15 October 2009'
__author__  = 'Martin Hosken <martin_hosken@sil.org>'
__credits__ = 'Tim Eves <tim_eves@sil.org> for some optimisations and code tidy-ups'

import contextlib, optparse, palaso.contexts, sys
from palaso.kmn.coverage import Coverage

parser = optparse.OptionParser(usage='%prog [options] <KEYMAN FILE>\n' + __doc__)
parser.add_option("-m","--mode", 
                  default='all', choices=('all','first1','random','random1'),
                  help='Specify the search mode: all, first1, random, random1 (default: %default)')

(opts,kmns) = parser.parse_args()
if len(kmns) == 0:
    sys.stderr.write(parser.expand_prog_name('%prog: missing KEYMAN FILE\n'))
    parser.print_help(file=sys.stderr)
    sys.exit(1)

with palaso.contexts.utf8out():
    k = Coverage(kmns[0])
    results = sorted(sorted(k.coverage_test(opts.mode)),key=len,reverse=True)
    sys.stdout.writelines(l + '\n' for l in results)

#!/usr/bin/env python3

from palaso.teckit.engine import Converter, Mapping
import csv
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-c','--column',action="append",type='int',help="Column number to convert")
parser.add_option('-t','--teckit',action="store",help="TECkit .tec file to apply to given columns")
parser.add_option('-r','--reverse',action="store_true",help="Run TECkit file in reverse")
parser.add_option('-u','--unicode',action='store_true',help='Input is in Unicode, so decode by utf-8')
parser.add_option('--codepage',action='store',help="Convert Unicode to bytes using codepage first [cp1252]")

(opts, argv) = parser.parse_args()

if not opts.codepage : opts.codepage = 'cp1252'

eng = Converter(Mapping(opts.teckit), forward = not opts.reverse)
rdr = csv.reader(open(argv[0], 'rb'))
wtr = csv.writer(open(argv[1], 'wb'))
for row in rdr :
    for c in opts.column :
        chrs = row[c]
        if opts.unicode : chrs = chrs.decode('utf-8').encode(opts.codepage)
        row[c] = eng.convert(row[c].decode('utf-8').encode('cp1252'), finished=True).encode('utf-8')
    wtr.writerow(row)

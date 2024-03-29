#!/usr/bin/env python3
import argparse
import os
import sys
from pprint import pprint
from palaso import sfm
from palaso.sfm import usfm, style


def appendsheet(fname, sheet):
    if os.path.exists(fname):
        with open(fname) as s:
            sheet = style.update_sheet(sheet, style.parse(s))
    return sheet


parser = argparse.ArgumentParser()
parser.add_argument('usfm', nargs='+', help='usfm string components')
parser.add_argument('-i', '--input', action='store_true',
                    help='strings are files')
parser.add_argument('-s', '--stylesheet', action='append', default=[])
parser.add_argument('-e', '--error', action='store_const',
                    default=sfm.ErrorLevel.Unrecoverable,
                    const=sfm.ErrorLevel.Marker)
parser.add_argument('-o', '--outfile', help='Store output in a file')
parser.add_argument('-l', '--literal', action="store_true",
                    help="pretty print the python data structure")
args = parser.parse_args()

sheet = usfm.default_stylesheet
if not args.stylesheet:
    args.stylesheet = filter(None,
                             os.environ
                             .get('TESTSFM_STYLESHEETS', '')
                             .split(';'))
for s in args.stylesheet:
    sheet = appendsheet(s, sheet)

if args.outfile is not None:
    outf = open(args.outfile, "w", encoding="utf-8")
else:
    outf = sys.stdout

if args.input:
    for f in args.usfm:
        with open(f, encoding="utf-8") as inf:
            doc = list(usfm.parser(inf,
                                   stylesheet=sheet,
                                   tag_escapes=r"[%$]"))
            outf.write(sfm.generate(doc))
else:
    doc = list(usfm.parser(
        [s.encode("utf-8").decode("raw_unicode_escape") for s in args.usfm],
        stylesheet=sheet, canonicalise_footnotes=True))
    if args.literal:
        pprint(doc)
    else:
        print("\n".join(str(x) for x in doc))

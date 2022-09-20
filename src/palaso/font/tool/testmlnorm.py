#!/usr/bin/env python3

from palaso.font.testml import TestFile
from argparse import ArgumentParser
import re


def main():
    parser = ArgumentParser(description="converts testml to TeX")
    parser.add_argument('-e','--entities',action='store_true', help='Output non-ASCII text as entities')
    parser.add_argument('fnames', nargs=2, help='input.xml output.tex')
    args = parser.parse_args()

    tests = TestFile().fromFile(args.fnames[0])
    if args.entities :
        res = tests.toFile()
        res = re.sub(r'([^\u0000-\u007F])', lambda m: f'&#x{ord(m.group(1)):04X};', res.decode('utf-8'))
        f = open(args.fnames[1], "wb")
        f.write(res)
        f.close()
    else :
        tests.toFile(args.fnames[1])


if __name__ == "__main__":
    main()

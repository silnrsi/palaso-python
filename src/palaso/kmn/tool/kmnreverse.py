#!/usr/bin/env python3

from palaso.kmn import Key, Keyman
import sys, codecs
from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    parser.add_argument("kmn", help="Keyman file")
    parser.add_argument("test", help="Test file")
    args = parser.parse_args()

    kmn = Keyman(args.kmn)
    cache = {}
    with codecs.open(args.test, encoding="utf-8") as f :
        for l in f.readlines() :
            res = kmn.reverse(l.strip())[0]
            print("".join(map(str, res)))


if __name__ == "__main__":
    main()

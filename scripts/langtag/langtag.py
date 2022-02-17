#!/usr/bin/env python3

import argparse
from palaso.langtag import LangTags, langtag


def addtag(t, alltags, regioncode, regionlangs):
    alltags.add(t)
    if getattr(t, 'region', '') == regioncode:
        regionlangs.add(t)

parser = argparse.ArgumentParser()
parser.add_argument('names',nargs='*',help='name to look up')
parser.add_argument('-t','--tag',help='Specifies tag to use')
parser.add_argument('-r','--region',help='Give information on region code or name')
parser.add_argument('-v','--verbose',action='store_true',help='Specifies tag to use')
parser.add_argument('--langtags',help='langtags.json to use')
args = parser.parse_args()

lts = LangTags(fname=args.langtags)
if args.tag is not None:
    args.tag = langtag(args.tag)
alltags = set()
name = " ".join(args.names)
regioncode = None
regionname = None
regionlangs = set()
for t in lts.values():
    if args.region is not None and regioncode is None:
        if args.region.lower() == getattr(t, 'region', '').lower() \
                or (len(args.region) != 2 and args.region.lower() in getattr(t, 'regionname', '').lower()):
            regioncode = t.region
            regionname = t.regionname
    if args.tag is not None:
        if t.matched(args.tag):
            addtag(t, alltags, regioncode, regionlangs)
        continue
    if len(name) and (name in getattr(t, 'name', "").lower() or \
                      any(name in x.lower() for x in getattr(t, 'names', []))):
        addtag(t, alltags, regioncode, regionlangs)
    if regioncode and getattr(t, 'region', '') == regioncode:
        regionlangs.add(t)

if not len(alltags) and args.tag is not None:
    try:
        addtag(lts[str(args.tag)], alltags, regioncode, regionlangs)
    except KeyError:
        pass
if args.verbose:
    formatstr = "{tag!s} = {full!s} {tags!s}, {name!s}, {names!s}"
else:
    formatstr = "{tag!s} = {full!s}\t {name!s}"

print("\n".join(formatstr.format(**(t.asdict(format=str, tags="", names=""))) for t in alltags))
if args.region and regioncode is not None:
    print("Region: {} = {}".format(regioncode, regionname))
    print("    " + " ".join(str(x.tag) for x in sorted(regionlangs, key=str)))

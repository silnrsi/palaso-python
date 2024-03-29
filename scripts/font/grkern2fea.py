#!/usr/bin/env python3

import argparse, logging, os, gc
from multiprocessing import Pool, current_process, cpu_count
from collections import UserString
from functools import reduce
from fontTools import ttLib
from palaso.font.shape import GrFont
from palaso.font.grstrings import makestring, parseftml
from palaso.font.glyphstring import Collection, String, RuleSet

def read_stringsFile(infile, cmap):
    rmap = {n:i for i,n in enumerate(cmap)}
    with open(infile) as fh:
        res = [String.fromStr(l, cmap=rmap) for l in fh.readlines()]
    return (res, )
    
def initprocess(fname, rtl):
    proc = current_process()
    proc.grface = GrFont(fname, rtl=(1 if rtl else 0))
def proc_makestring(s):
    proc = current_process()
    return makestring(proc.grface, s)

def run_graphite(args, *a):
    """ Create strings from running real text strings through Graphite """
    logging.info("Running graphite on input data")
    strings = []
    for inf in args.input:
        for d in args.directory:
            fname = os.path.join(d, inf)
            if not os.path.exists(fname):
                continue
            if fname.endswith(".xml") or fname.endswith(".ftml"):
                strings.extend(parseftml(fname, feats=args.feats))
            else:
                with open(fname, "r") as fh:
                    strings.extend([UserString(x.strip()) for l in fh.readlines() for x in l.split()])
                if args.rtl or args.feats is not None:
                    for s in strings:
                        s.rtl = args.rtl
                        if args.feats is not None:
                            s.feats = args.feats
            break
    if args.jobs == 1:
        grfont = GrFont(args.font, 1 if args.rtl else 0)
        res = [makestring(grfont, s) for s in strings]
    else:
        pool = Pool(processes=args.jobs, initializer=initprocess, initargs=[args.font, args.rtl])
        res = list(pool.imap_unordered(proc_makestring, strings))
    return (res, )

def run_strings(args, strings, *a):
    """ Flatten strings with more than one kern into single strings for each kern """
    colls = {}
    res = []
    for s in strings:
        for n in s.splitall():
            g = n.match[0].gid
            if g not in colls:
                colls[g] = Collection()
            colls[g].addString(n, rounding=args.rounding)
            res.append(n)
    logging.info("{} Input strings flattened to {} rules".format(len(strings), len(res)))
    return (res, colls)

def run_reduced(args, strings, colls, *a):
    """ Apply clustering. Remove resulting duplicates. Remove 0 kerns where there is nothing shorter """
    rules = {}
    keylengths = {k: sum(len(x) for x in v.gidmap.values()) for k, v in colls.items()}
    rules = {k: v.process(k, args.rounding)[1] for k,v in sorted(colls.items(), key=lambda x:-keylengths[x[0]])}
    res = [r for vg in sorted(rules.keys()) for v in sorted(rules[vg].keys()) for r in rules[vg][v]]
    logging.info("{} rules after clustering".format(len(res)))
    return (res, )

def run_classes(args, res, *a):
    """ Group strings into strings of classes """
    lastlen = 0
    # import pdb; pdb.set_trace()
    for r in res:
        r.dropme = False
    maxlen = max(len(x) for x in res)
    while len(res) != lastlen:
        lastlen = len(res)
        newres = set()
        finder = {}
        for i in range(maxlen):
            for r in res:
                if len(r) <= i:
                    continue
                j = r.weightedIndex(i)
                k = b"".join(x.pack() for x in r[:j] + r[j+1:])
                if k in finder:
                    for s in finder[k]:
                        if not s.dropme and s.addString(r):
                            r.dropme = True
                            newres.discard(r)
                            newres.add(s)
                            break
                    else:
                        finder[k].append(r)
                else:
                    finder[k] = [r]
        for r in res:
            if not r.dropme:
                newres.add(r)
        res = list(newres)
    logging.info("{} rules after grouping into classes".format(len(res)))
    return (res, )

def reduce_lookups(args, res, *a):
    """ Create kerning adjustment lookups and associate strings and minimise """
    outrules = RuleSet(res)
    outrules.make_ruleSets()
    logging.info ("Lookups: {} sum {}, Strings: {}".format(outrules.numlookups(), outrules.totallookuplength(), len(outrules.strings)))
    outrules.reduceSets()
    outrules.rebuild_strings()
    return (outrules, )

def add_layers(args, outrules, *a):
    """ Create layered string matching lookups. One layer only """
    outrules.addLayers()
    logging.debug("Created {} layers of {} strings".format(len(outrules.layers), ["{}/{}".format(len(l.strings), len(l.contextset)) for l in outrules.layers]))
    outrules.addIntoLayers()
    return (outrules, )

fnindices = {k:i for i,k in enumerate(['graphite', 'strings', 'reduced', 'classes', 'lookups', 'layers'])}
fnmap = [run_graphite, run_strings, run_reduced, run_classes, reduce_lookups, add_layers]

parser=argparse.ArgumentParser()
parser.add_argument("outfile",help="Output file of results")
parser.add_argument("-i","--input",action="append",help="Input test text file")
parser.add_argument("-s","--start",default='graphite',help="start with [graphite, strings, reduced, classes, lookups, layers]")
parser.add_argument("-e","--end",default='end',help="end after given start value")
parser.add_argument("-f","--font",required=True,help="Path to font file")
parser.add_argument("-d","--directory",action="append",default=['.'],help="Directories to search for input test files")
parser.add_argument("-R","--rtl",action="store_true",help="Render strings rtl")
parser.add_argument("-r","--rounding",default=10,type=int,help="Cluster rounding")
parser.add_argument("-F","--feature",default=[],action="append",help="Add feat=value to each string. Can repeat")
parser.add_argument("-j","--jobs",type=int,default=cpu_count(),help="Number of parallel jobs to run")
parser.add_argument("-L","--log",default="INFO",help="Logging level [DEBUG, *INFO*, WARN, ERROR]")
parser.add_argument("--logfile",help="Log to file")
args = parser.parse_args()

if len(args.feature):
    args.feats = {}
    for a in args.feature:
        x = a.split('=')
        args.feats[x[0].strip()] = int(x[1])
else:
    args.feats = None
 
if args.log:
    loglevel = getattr(logging, args.log.upper(), None)
    if isinstance(loglevel, int):
        parms = {'level': loglevel, 'format': ''}
        if args.logfile is not None:
            parms.update(filename=args.logfile, filemode="w")
        logging.basicConfig(**parms)

tt = ttLib.TTFont(args.font)
cmap = tt.getGlyphOrder()
String.cmap = cmap
start = fnindices[args.start.lower()]
if args.end == "end":
    end = len(fnindices) - 1
else:
    end = fnindices[args.end.lower()]

if start > 0:
    res = read_stringsFile(args.input[0], cmap)
else:
    res = ([], )

for i in range(start, end+1):
    res = fnmap[i](args, *res)
    logging.debug("Garbage collected {}".format(gc.collect()))

if end < fnindices['lookups']:
    outrules = RuleSet(res[0])
    outrules.make_ruleSets()
else:
    outrules = res[0]

logging.info ("Lookups: {} sum {}, Strings: {}".format(outrules.numlookups(), outrules.totallookuplength(), outrules.stringslength()))

if args.outfile.endswith(".fea"):
    outrules.outfea(args.outfile, cmap, rtl=args.rtl)
else:
    outrules.outtext(args.outfile, cmap)



"""Module to interact with PyICU"""

import PyICU, operator, struct, re, palaso.reggen, palaso.contexts

def sorted(tailor, strs, level=15, preproc=()) :
    """sorts a list of strings against the given tailoring and level, returning the resultant sorted list.
Level = 0 - PRIMARY, 1 - SECONDARY, 2 - TERTIARY, 3 - QUARTENARY, 15 - IDENTICAL. Defaults to IDENTICAL
"""
    procreg = [(re.compile(p[0]), p[1]) for p in preproc]
    collator = PyICU.RuleBasedCollator(tailor, level)
    results = [(_sortkey(collator, procreg, s), s) for s in strs]
    results.sort(cmp = lambda a, b: a.compareTo(b), key=operator.itemgetter(0))
    return [s[1] for s in results]

def _sortkey(coll, proc, str) :
    with palaso.contexts.relaxedsubs() :
        str = reduce(lambda s, p : p[0].sub(p[1], s), proc, str)
    return coll.getCollationKey(str)

def strkey(key) :
    """Returns a string representation of a collation key"""
    keyinfo=[]
    keyinfo_size = 0
    for b in key.getByteArray().rstrip('\000').split('\001'):
        if len(b) % 2: b += "\000"
        keyinfo.append([struct.unpack('>H', x+(y or "\000")) for (x, y) in zip(b[::2], b[1::2])])
        if len(keyinfo[-1]) > keyinfo_size: keyinfo_size = len(keyinfo[-1])
    line = ""
    for k in keyinfo :
        line += "[" + ".".join(["%04X" % (i) for i in k]) + "]"
#    for k in range(keyinfo_size):
#        line += "[" + ".".join(["%04X" % (0 if len(e) <= k else e[k]) for e in keyinfo]) + "]"
    return line

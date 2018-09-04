#!/usr/bin/python

from collections import namedtuple, Sequence
from six import string_types
import re

CharCode = namedtuple('CharCode', ['primary', 'tertiary_base', 'tertiary', 'prebase'])
SortKey = namedtuple('SortKey', ['primary', 'index', 'tertiary', 'tiebreak'])

def pad_results(res, num):
    if isinstance(res[0], Sequence):    # already a list of things
        final = []
        for r in res:
            final.append(r if isinstance(r, CharCode) else CharCode(r))
        final.extend(final[-1] * (num - len(final)))
    else:
        f = res if isinstance(res, CharCode) else CharCode(res)
        return [f] * num


class ClassString():

    def __init__(self, classes, result, pref=None):
        self.classes = classes
        self.result = pad_results(result, len(classes))
        self.pref = pref

    def match(self, instr, start):
        if len(instr) - start < len(self.classes):
            return None
        for i, c in enumerate(self.classes):
            if instr[start + i] not in c:
                return None
        if self.pref is not None and self.pref.revmatch(instr, start - 1) is None:
            return None
        return self.result

    def revmatch(self, instr, start):
        if start < len(self.classes) - 1:
            return None
        for i, c in enumerate(reversed(self.classes)):
            if instr[start - i] not in c:
                return None
        if self.pref is not None and self.pref.match(instr, start+1) is None:
            return None
        return self.result


class MatchString():

    def __init__(self, instr, result, pref=None):
        self.str = instr
        self.result = pad_results(result, len(instr))
        self.pref = pref

    def match(self, instr, start):
        if len(instr) - start < len(self.str) or not instr[start:].startswith(self.str):
            return None
        if self.pref is not None and self.pref.revmatch(instr, start - 1) is None:
            return None
        return self.result

    def revmatch(self, instr, start):
        if start < len(self.str) - 1 or not instr[:-start].endswith(self.str):
            return None
        if self.pref is not None and self.pref.match(instr, start+1) is None:
            return None
        return self.result

class REMatch():

    def __init__(self, instr, result, pref=None):
        self.re = re.compile(instr)
        self.result = result
        self.pref = pref

    def match(self, instr, start):
        m = self.re.match(instr, start)
        if m is None:
            return None
        num = m.end() - m.start()
        if self.pref is not None and not re.search(self.pref+"$", instr[:start]):
            return None
        return pad_results(self.result, num)
            

class ReOrder():
    
    def __init__(self, rulelist):
        self.rules = []
        for r in rulelist:
            pref = r[2] if len(r) > 2 else None
            self.rules.append(REMatch(r[0], r[1], pref=pref))

    def _sort(self, begin, end, chars, keys, rev=False):
        s = chars[begin:end]
        k = keys[:end-begin]
        if not len(s):
            return (chars[:begin], u"", chars[end:])
        # if there is no base, insert one
        if not rev and (0, 0) not in [(x.primary, x.tertiary) for x in k]:
            s += u"\u200B"
            k += SortKey(0, 0, 0, 0)  # push this to the front
        # sort key is (primary, secondary, string index)
        res = u"".join(s[y] for y in sorted(range(len(s)), key=lambda x:k[x]))
        if rev:
            # remove a \u200B if the cluster start after a prevowel
            foundpre = False
            for i, key in enumerate(sorted(k)):
                if key.primary < 0:
                    foundpre = True
                elif key.primary > 0:
                    break
                elif foundpre and res[i] == u"\u200B":
                    res = res[:i] + res[i+1:]
                    break
        return (chars[:begin], res, chars[end:])

    def _padlist(self, val, num):
        boolmap = {'false' : 0, 'true': 1}
        res = [boolmap.get(x.lower(), x) for x in val.split()]
        if len(res) < num:
            res += [res[-1]] * (num - len(res))
        return res

    def _get_charcodes(self, instr, curr, rev=False):
        '''Returns a list of some CharCodes, 1 per char, for the string at curr''' 
        r = self.revmatch(instr, curr) if rev else self.match(instr, curr)
        return r if r is not None else [CharCode(0, 0, 0, False)]

    def reorder(self, instr, start=0):
        '''Handle the reorder transforms'''
        # scan for start of sortable run. Normally empty
        # import pdb; pdb.set_trace()
        curr = start
        res = ""
        while curr < len(instr):
            codes = self._get_charcodes(instr, curr)
            for c in codes:
                if c.prebase or c.primary == 0:
                    break
                curr += 1
            else:
                continue        # if didn't break inner loop, don't break outer loop
            break               # if we broke in the inner loop, break the outer loop
        if curr > start:        # just copy the odd characters across
            res = instr[start:curr]

        for pre, ordered, post in self._reorder(instr, start=curr):
            res += ordered
        return res

    def _reorder(self, instr, start):
        '''Presumes we are at the start of a cluster'''
        curr = start
        end = len(instr)
        keys = [None] * (len(instr) - start)
        isinit = True           # inside the start of a run (.{prebase}* .{order==0 && tertiary==0})
        currprimary = 0
        currbaseindex = curr
        while curr < end:
            codes = self._get_charcodes(instr, curr)
            for i, c in enumerate(codes):               # calculate sort key for each character in turn
                if c.tertiary and curr + i > start:      # can't start with tertiary, treat as primary 0
                    key = SortKey(currprimary, currbaseindex, c.tertiary, curr + i)
                else:
                    key = SortKey(c.primary, curr + i, 0, curr + i)
                    if c.primary == 0 or c.tertiary_base:   # primary 0 is always a tertiary base
                        currprimary = c.primary
                        currbaseindex = curr + i

                if ((key.primary != 0 or key.tertiary != 0) and not c.prebase) \
                        or (c.prebase and curr + i > start \
                            and keys[curr+i-start-1].primary == 0):  # prebase can't have tertiary
                    isinit = False      # After the prefix, so any following prefix char starts a new run

                # identify a run boundary
                if not isinit and ((key.primary == 0 and key.tertiary == 0) or c.prebase):
                    # output sorted run and reset for new run
                    yield self._sort(0, curr + i - start, instr[start:], keys)
                    start = curr + i
                    keys = [None] * (len(instr) - start)
                    isinit = True
                keys[curr+i-start] = key
            curr += len(codes)
        # yield a final result with the residue and no post text
        if curr > start:
            yield self._sort(0, curr-start, instr[start:], keys)
        else:
            yield ("", "", "")

    def _unreorder(self, instr):
        ''' Create a string that when reordered gives the input string.
            This relies on well designed reorders, but is generally what happens.'''
        end = 0
        trans = self.transforms['reorder']
        hitbase = False
        keys = []
        tertiaries = []
        while end < len(instr):
            # work backwards from the end of the string
            codes = self._get_charcodes(instr, end, trans, rev=True)
            for c in codes:
                # having hit a cluster prefix do we now hit the end of the last cluster?
                if hitbase and (c.primary >= 0 or c.tertiary > 0):
                    break
                # hit the end of a cluster prefix
                elif c.primary == 0 and c.tertiary == 0:
                    hitbase = True
                    keys.append(SortKey(0, -end, 0, -end))
                    # bases are always tertiary_bases so update tertiary references
                    for e in tertiaries:
                        keys[e] = SortKey(0, -end, keys[e].tertiary, keys[e].tiebreak)
                    tertiaries = []
                # tertiary characters get given a key and a reference to update
                elif c.tertiary != 0:
                    tertiaries.append(end)
                    keys.append(SortKey(0, -end, c.tertiary, -end))
                # normal case
                else:
                    # if this is reordered before the start of a cluster, reorder it to the end
                    # doesn't really matter where it ends up, it'll get sorted back
                    v = c.primary + (127 if c.primary < 0 else 0)
                    # sort prebases before base
                    if c.prebase:
                        v = c.prebase - 10
                    keys.append(SortKey(v, -end, c.tertiary, -end))
                    # update tertiary references
                    if c.tertiary_base:
                        for e in tertiaries:
                            keys[e] = SortKey(v, -end, keys[e].tertiary, keys[e].tiebreak)
                        tertiaries = []
                end += 1
            else:
                continue
            break
        keys = list(reversed(keys))
        res = self._sort(len(instr) - len(keys), len(instr), instr, keys, rev=True)
        return res

    def match(self, instr, start):
        for r in self.rules:
            res = r.match(instr, start)
            if res is not None:
                return res
        return None

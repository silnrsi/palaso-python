#!/usr/bin/python3

from struct import pack
from collections import namedtuple
import itertools
import re, struct, os, itertools
import numpy as np
from sklearn.cluster import ward_tree
import logging as log

def skipws(s, i):
    while i < len(s):
        if s[i] not in " \t\n":
            break
        i += 1
    return i

def remove_duplicates(b):
    i = 1
    while i < len(b):
        if b[i-1] == b[i]:
            b.pop(i)
        else:
            i += 1
    return b

def listPrefix(a, b):
    ''' Return the first index at which the alignments of the two lists don't match '''
    c = list(zip(a, b))
    for i, d in enumerate(c):
        if not d[0].contains(d[1]):
            return i
        #if d[0] != d[1]:
            #return i
    return len(c)

def myCombinations(pool):
    n = len(pool)
    indices = [len(p)-1 for p in pool]
    yield [pool[j][i] for j, i in enumerate(indices)]
    while True:
        for i in reversed(range(n)):
            if indices[i] > 0:
                break
        else:
            return
        indices[i] -= 1
        yield [pool[j][i] for j, i in enumerate(indices)]

class Collection(object):
    ''' Collections for one glyph '''
    def __init__(self):
        self.gidmap = {}

    def addString(self, s, rounding=0):
        k = s.match[0].keystr(rounding=1)
        self.gidmap.setdefault(k, []).append(s)

    def _get_children(self, n, X, children, n_leaves):
        # calculate node centres
        res = []
        if n < n_leaves:
            return [X[n]]
        for j in range(2):
            m = children[n-n_leaves][j]
            if m >= n_leaves:
                res.extend(self._get_children(m, X, children, n_leaves))
            else:
                res.append(X[m])
        return res

    def round(self, rounding, k):
        ''' Apply clustering '''
        X = np.array([(int(x[0]), int(x[1])) for x in ((y[y.find(":")+1:]+",0").split(",") for y in self.gidmap.keys())])
        (children, _, n_leaves, parents, distances) = ward_tree(X, return_distance = True)
        done = set()
        res = []
        for i in range(len(distances)):
            if distances[i] > rounding:
                for j in range(2):
                    c = children[i][j]
                    if c not in done:
                        res.append(c)
                done.add(i+n_leaves)
        nodes = [self._get_children(x, X, children, n_leaves) for x in res]
        centres = [((min(x, key=lambda y:y[0])[0] + max(x, key=lambda y:y[0])[0]) // 2, 
                    (min(x, key=lambda y:y[1])[1] + max(x, key=lambda y:y[1])[1]) // 2) for x in nodes]
        for i, n in enumerate(nodes):
            if any(x[0] == 0 and x[1] == 0 for x in n):
                centres[i] = (0, 0)
        newmap = {}
        for i in range(len(nodes)):
            key = "{}:{},{}".format(k, centres[i][0], centres[i][1])
            newmap[key] = []
            for v in nodes[i]:
                dat = self.gidmap["{}:{},{}".format(k, v[0], v[1])]
                newmap[key].extend(dat)
                for s in dat:
                    s.match[0].positions[0] = Position(*centres[i])
        self.gidmap = newmap

    def process(self, k, rounding):
        ''' Remove small positioned strings, duplicates; cluster and reduce '''
        # need to keep small (0) movements around to help mask shorter strings
        if rounding > 0:
            self.mergeSmalls(rounding)
        self.stripDuplicates()
        if len(self.gidmap) > 1:
            self.round(rounding, k)
        self.reduce()
        self.stripSmalls()
        return (len(self.gidmap), self.gidmap)

    def stripDuplicates(self):
        for k, v in self.gidmap.items():
            self.gidmap[k] = remove_duplicates(sorted(v, key=lambda x:x.key()))

    def mergeSmalls(self, rounding):
        ''' Remove any string that has positions < rounding close to 0 '''
        newmap = {}
        for k, v in self.gidmap.items():
            for s in v:
                if s.testPos(rounding):
                    newmap.setdefault(k, []).append(s)
                else:
                    newk = k[:k.find(":")] + ":0,0"
                    newmap.setdefault(newk, []).append(s)
        self.gidmap = newmap

    def reduce(self):
        ''' Reduce rules to their minimum context and remove rules covered by others '''
        res = {}
        for k, v in sorted(self.gidmap.items(), key=lambda x:len(x[1])):
            # if k.endswith(":0,0"):
            #     continue
            res[k] = []
            for r in v:
                if any(t.isSubstringOf(r) for t in res[k]):
                    continue
                res[k].append(r)
        self.gidmap = res
        return res

    def stripSmalls(self):
        ''' Remove 0 kerns for those strings for which there is no shorter string anywhere '''
        allitems = sorted(self.gidmap.items(), key=lambda x:len(x[1]))
        for k, v in [x for x in allitems if x[0].endswith(":0,0")]:
            newlist = []
            for r in v:
                for l, w in [x for x in allitems if not x[0].endswith(":0,0")]:
                    if any(t.isSubstringOf(r) for t in w):
                        newlist.append(r)
                        break
            if len(newlist):
                self.gidmap[k] = newlist
            else:
                del self.gidmap[k]

    def isUnique(self, key, rule, prelen, postlen):
        ''' Returns whether a rule context is unique in this collection '''
        for k, v in self.gidmap.items():
            if k == key:
                continue
            for r in v:
                if len(r.pre) < prelen or len(r.post) < postlen:
                    continue
                if r.pre[-prelen:] == rule.pre[-prelen:] and r.post[:postlen] == rule.post[:postlen]:
                    return False
        return True

class String(object):

    cmap = []
    def __init__(self, pre=None, post=None, match=None, text=None):
        self.pre = pre or []
        self.post = post or []
        self.match = match or []
        self.text = text
        self.gnps = []

    def copy(self):
        res = String()
        res.pre = self.pre[:]
        res.post = self.post[:]
        res.match = self.match[:]
        res.text = self.text
        res.gnps = self.gnps[:]
        return res

    @classmethod
    def fromBytes(cls, dat, variables=[]):
        # todo: support self.text
        res = cls()
        n = unpack(">H", dat[:2])[0]
        flags = n >> 12
        n = n & 0xFFF
        i = 2
        curr = self.pre
        while i < len(dat):
            if flags & 2:
                r = Node.fromBytes(dat[i:i+6*n+6], variables)
                i += 6*n + 6
            else:
                r = Node.fromBytes(dat[i:i+3+2*n], variables)
                i += 2*n + 3
            if r is not None:
                curr = self.addNode(r, curr)
        return res

    @classmethod
    def fromStr(cls, dat, variables=[], cmap={}):
        self = cls()
        end = skipws(dat, 0)
        if end >= len(dat):
            return self
        if dat[end] == '"':
            e = dat[end+1:].find('"')
            self.text = dat[end+1:e]
            end = skipws(dat, e+1)
        curr = self.pre
        while end < len(dat):
            end = skipws(dat, end)
            n, i = Node.fromStr(dat[end:], variables, cmap)
            end = skipws(dat, end+i)
            if n is not None:
                curr = self.addNode(n, curr)
        return self

    def addNode(self, r, curr):
        if id(curr) == id(self.pre) and r.hasPositions():
            curr = self.match
        elif id(curr) == id(self.match) and not r.hasPositions():
            curr = self.post
        elif id(curr) == id(self.post) and r.hasPositions():
            self.match.extend(self.post)
            self.post = []
            curr = self.match
        curr.append(r)
        return curr

    def addString(self, r):
        if self == r or len(self) != len(r):
            return False
        mp = -1
        for i in range(len(self)):
            if r[i].pack() == self[i].pack():
                pass
            elif mp == -1:
                mp = i
            else:
                return False
        if mp == -1:
            return True
        rmp, smp = r[mp], self[mp]
        if rmp.hasPositions():
            if not smp.hasPositions():
                smp.positions = [Position(0,0)] * (len(smp.keys) - 1)
        for i, g in enumerate(rmp.keys):
            if g not in smp.keys:
                smp.keys.append(g)
                if smp.hasPositions():
                    smp.positions.append(rmp.positions[i] if rmp.hasPositions() else Position(0, 0))
        return True

    def splitgnp(self, gnps, newindex):
        newnode = self.match[0].splitwith(gnps)
        res = None
        if newnode is not None:
            newmatch = [newnode] + self.match[1:]
            res = String([x.copy() for x in self.pre], [x.copy() for x in self.post], newmatch, self.text[:])
            res.gnps = [newindex]
        return res

    def movegnp(self, f, t):
        for i, v in enumerate(self.gnps[:]):
            if v == f:
                self.gnps[i] = t

    def key(self):
        return [x.key() for x in self.pre + self.match + self.post]

    def __hash__(self):
        return hash(struct.pack("{}H".format(len(self)), *self.gids()))

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.key() == other.key()

    def __str__(self):
        return self.asStr()

    def __repr__(self):
        return self.asStr()

    def asBytes(self):
        return b"".join(x.asBytes() for x in self.pre + self.match + self.post)

    def asStr(self, cmap=None):
        if cmap is None:
            cmap = self.cmap
        if self.text is not None:
            res = '"'+self.text+'" '
        else:
            res = ""
        return res + " ".join(x.asStr(cmap) for x in self.pre + self.match + self.post)

    def subOverlap(self, other, layer=None, eqok=True):
        """ If self were tested before other, would other be masked and not match? """
        selfstr = self.pre + self.match + self.post
        otherstr = list(other.pre) + list(other.match) + list(other.post)
        if len(selfstr) > len(otherstr):
            return False
        matched = False
        for i in range(len(otherstr)):
            for j in range(len(selfstr)):
                if not otherstr[i+j].contains(selfstr[j], includepos=False):
                    break
            else:
                matched = True
                break
        else:
            return False
        return True

    def subOverlapLayer(self, other, layer, eqok=True):
        if not self.subOverlap(other, eqok=eqok):
            return False
        return any(self.subOverlap(o, eqok=eqok) for o in layer.makeStrings(other))

    def differences(self, other, assumeOverlap=False):
        """ Returns a list of strings that are matched by other but not by self. """
        if not assumeOverlap and not self.subOverlap(other):
            return [other]
        pres = [(x[0], x[0].diff(x[1])) for x in zip(self.pre, other.pre)]
        matches = [(x[0], x[0].diff(x[1])) for x in zip(self.match, other.match)]
        posts = [(x[0], x[0].diff(x[1])) for x in zip(self.post, other.post)]
        res = []
        total = pres + matches + posts
        for c in myCombinations(total):
            if any(r is None for r in c):
                continue
            s = String(c[:len(pres)], c[len(pres)+len(matches):], c[len(pres):len(pres)+len(matches)])
            if s == self:
                continue
            s.gnps = self.gnps[:]
            res.append(s)
        return res

    def extractSubStringDiff(self, other):
        newmatch = []
        for z in zip(self.match, other.match):
            d = z[0].diff(z[1])
            if len(d) == len(z[0]):
                return None
            newmatch.append(d)
        return String(self.pre, self.post, newmatch)

    def isSubstringOf(self, other):
        if len(self.match) != len(other.match):
            return False
        if len(self.pre) > len(other.pre):
            return False
        if len(self.post) > len(other.post):
            return False
        if any(self.match[i].gid != other.match[i].gid for i in range(len(self.match))):
            return False
        if any(self.pre[-i-1].gid != other.pre[-i-1].gid for i in range(len(self.pre))):
            return False
        if any(self.post[i].gid != other.post[i].gid for i in range(len(self.post))):
            return False
        return True

    def splitall(self):
        me = self.copy()
        while len(me.match):
            res = String()
            res.pre = me.pre[:]
            res.match = [me.match[0]]
            res.post = [x.copy(nopositions=True) for x in me.match[1:]] + self.post
            res.text = me.text
            res.gnps = me.gnps[:]
            yield res
            me.pre.append(me.match.pop(0).copy(nopositions=True))
            while len(me.match) and not me.match[0].hasPositions():
                me.pre.append(me.match.pop(0))

    def gids(self):
        return [x.gid for x in self.pre + self.match + self.post]

    def __len__(self):
        return len(self.pre) + len(self.match) + len(self.post)

    def __getitem__(self, y):
        if isinstance(y, slice):
            start, stop, stride = y.indices(len(self))
        else:
            start = y if y >= 0 else len(self) + y
            stride = 1
            stop = start + 1
        last = 0
        res = []
        for a in (self.pre, self.match, self.post):
            l = len(a)
            if start >= last:
                while start < stop and start < l + last:
                    res.append(a[start - last])
                    start += stride
            last += l
        if start != stop:
            raise IndexError
        if isinstance(y, slice):
            return res
        elif len(res) != 1:
            raise IndexError
        else:
            return res[0]

    def weightedIndex(self, i):
        if i < len(self.match):
            return len(self.pre) + i
        i -= len(self.match)
        x = (i + 1) // 2
        if x < len(self.pre):
            return len(self.pre) - x - 1
        x = i - len(self.pre)
        if x < len(self.post):
            return len(self) - i - 1
        raise IndexError

    def filterempties(self):
        self.match = [x for x in self.match if len(x.keys)]
        return len(self.match) != 0

    def testPos(self, rounding):
        ''' Returns whether all nodes in the string have position > rounding '''
        return all(x.testPos(rounding) for x in self.match)


class Node(object):
    def __init__(self, keys=None, positions=None, index=None):
        self.keys = keys or []
        self.positions = positions or []        # one position per key
        self.var = None
        self.gid = keys[0] if keys else None
        self.index = index

    def copy(self, nopositions=False):
        res = Node(keys=self.keys[:], positions=(self.positions[:] if not nopositions else None))
        res.var = self.var
        return res

    @classmethod
    def fromBytes(cls, dat, variables=[]):
        # support self.index
        self = cls()
        if len(dat) < 5:
            return None
        n = unpack(">H", dat[:2])[0]
        flags = n >> 12
        n = n & 0xFFF
        if flags & 1:
            self.var = unpack(">H", dat[2:4])
            start = 4
        else:
            self.keys = unpack(">" + ("H" * n), dat[2:2+2*n])
            start = 2 + 2*n
        if flags & 2:
            poses = unpack(">" + ("H" * (2*n)), dat[start:])
            self.positions = [Position(*x) for x in zip(poses[:n], poses[n:])]
        self.gid = self.keys[0]
        return self

    @classmethod
    def fromStr(cls, dat, variables=[], cmap={}):
        self = cls()
        if dat[0] == "@":
            m = re.match(r"^@(\d+)\s*", dat)
            self.var = int(m.group(1))
            end = m.end(0)
        elif dat[0] == "[":
            end = dat.find("]")
            gnames = re.split(r"[,\s]\s*", dat[1:end])
            self.keys = [cmap.get(g, 0) for g in gnames]
        else:
            return None, 1
        end = skipws(dat, end+1)
        if end < len(dat) and dat[end] == "{":
            end = skipws(dat, end+1)
            while end < len(dat) and dat[end] != "}":
                (p, i) = Position.fromStr(dat[end:])
                if p is None:
                    p = Position(0, 0)
                self.positions.append(p)
                end = skipws(dat, end+i)
            end = skipws(dat, end+1)
        if end < len(dat) and dat[end] == "!":
            m = re.match(r"!(\d+)", dat[end:])
            if m:
                #self.index = int(m.group(1))
                end = skipws(dat, end+m.end())
        self.gid = self.keys[0]
        return (self, end)

    @property
    def pos(self):
        return self.positions[0] if len(self.positions) > 0 else None

    def asBytes(self):
        if len(self.positions):
            flags = 2
        if self.var is not None:
            flags = 1
            res = pack("b>H", flags, 1)
        else:
            res = pack("b>H" + ("H" * len(self.keys)), flags, len(self.keys), *self.keys)
        if len(self.positions):
            res += b"".join(pack(">HH", x.x, x.y) for x in self.positions)
        return res

    def asStr(self, cmap=[]):
        order = sorted(range(len(self.keys)), key=lambda x:self.keys[x])
        if self.var is not None:
            res = "@{}".format(self.var)
        else:
            keys = [self.keys[x] for x in order]
            res = "[" + ", ".join(cmap[x] if x < len(cmap) else "gid{}".format(x) for x in keys) + "]"
        if len(self.positions):
            order = sorted(range(min(len(self.positions), len(self.keys))), key=lambda x:self.keys[x])
            res += "{" + ", ".join(str(self.positions[i]) for i in order) + "}"
        if self.index is not None:
            res += "!{}".format(self.index)
        return res

    def key(self):
        return (self.var or self.keys, self.positions)

    def __hash__(self):
        return hash(tuple(tuple(k) for k in self.key()))

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.key() == other.key()

    def __contains__(self, gid):
        return gid in self.keys

    def __len__(self):
        return len(self.keys)

    def _diff(self, other, includepos=True):
        if includepos and self.hasPositions():
            skp = set(zip(self.keys, self.positions))
            okp = set(zip(other.keys, other.positions))
        else:
            skp = set(self.keys)
            okp = set(other.keys)
        return (skp, okp)

    def contains(self, other, includepos=True):
        skp, okp = other._diff(self, includepos=includepos)
        return not skp.isdisjoint(okp)

    def diff(self, other, includepos=True):
        skp, okp = self._diff(other, includepos=includepos)
        reskp = sorted(skp.difference(okp))
        if reskp is None or len(reskp) == 0:
            return None
        if includepos and self.hasPositions():
            resk, resp = zip(*reskp)
            return Node(resk, resp)
        elif other.hasPositions():
            poses = [self.positions[self.keys.index(g)] for g in reskp]
            return Node(reskp, poses)
        else:
            return Node(reskp)

    def hasPositions(self):
        return len(self.positions) > 0

    def testPos(self, rounding):
        ''' Test that all positions are > rounding '''
        if not len(self.positions):
            return True
        return all(x.testPos(rounding) for x in self.positions)

    def keystr(self, rounding=0):
        p = self.positions[0] if len(self.positions) else None
        s = str(self.gid)
        if p is None:
            return s
        if rounding:
            ps = "{},{}".format(int(p.x / rounding + 0.5), int(p.y / rounding + 0.5))
        else:
            ps = "{},{}"
        return s + ":" + ps

    def pack(self):
        try:
            order = sorted(range(len(self.keys)), key=lambda x:self.keys[x])
            k = struct.pack("{}H".format(len(self.keys)), *[self.keys[x] for x in order])
            if len(self.positions):
                order = sorted(range(min(len(self.positions), len(self.keys))), key=lambda x:self.keys[x])
                poses = [self.positions[i] for i in order]
                p = struct.pack("{0}h{0}h".format(len(order)),
                                *(list(zip(*poses))[0] + list(zip(*poses))[1]))
            else:
                p = b""
            return k+p
        except TypeError:
            import pdb; pdb.set_trace()

    def match(self, gnp):
        try:
            i = self.keys.index(gnp[0])
        except ValueError:
            return None
        if len(self.positions) and len(gnp) >= 2:
            return i if self.positions[i] == gnp[1] else None
        return i

    def splitwith(self, gnps):
        newkeys = []
        newpositions = []
        for g in gnps:
            i = self.match(g)
            if i is not None:
                newkeys.append(g[0])
                del self.keys[i]
                if len(self.positions) and len(g) > 1:
                    newpositions.append(g[1])
                    del self.positions[i]
        if len(newkeys):
            return Node(newkeys, newpositions, self.index)
        else:
            return None


class Position(namedtuple('Position', ['x', 'y'])):
    def __str__(self):
        if self.y == 0:
            return str(self.x)
        else:
            return "({},{})".format(self.x, self.y)

    @classmethod
    def fromStr(cls, dat):
        m = re.match(r"^\(\s*(-?\d+(?:\.\d+(?:e-?\d+)?)?)\s*,\s*(-?\d+(?:\.\d+(?:e-?\d+)?)?)\s*\)", dat)
        if m:
            self = cls(int(float(m.group(1))), int(float(m.group(2))))
            end = m.end(0)
        elif dat[0] in "-1234567890.":
            m = re.match(r"^(-?\d*(?:\.\d+(?:e-?\d+)?)?)", dat)
            try:
                self = cls(int(float(m.group(1))), 0)
            except ValueError:
                self = None
                print(m.group(1))
            end = m.end(0)
        else:
            self = None
            end = 1
        return self, end

    def isZero(self, rounding=0):
        if rounding > 0:
            return int(self.x / rounding + 0.5) == 0 and int(self.y / rounding + 0.5) == 0
        else:
            return self.x == 0 and self.y == 0

    def testPos(self, rounding):
        return self.x * self.x + self.y * self.y > rounding * rounding


class RuleSet:
    newlkupcost = 8
    gnpformat = "{0}:{1[0]},{1[1]}"
    def __init__(self, strings):
        self.strings = strings
        self.sets = []      # list of GNPset
        self.layers = []

    def make_ruleSets(self):
        '''For each glyphnpos group into sets and collect a list of strings for each'''
        allgnps = {}
        count = 0
        order = sorted(range(len(self.strings)), key=lambda x:(self.strings[x].key(), self.strings[x]))
        for i, r in ((x, self.strings[x]) for x in order):
            for j, m in enumerate(r.match):
                if m.hasPositions():
                    s = m.asStr()
                    if s not in allgnps:
                        allgnps[s] = count
                        gnp = GNPSet(m.keys, m.positions)
                        self.sets.append(gnp)
                        gnp.rules.append(r)
                        r.gnps.append(count)
                        count += 1
                    else:
                        self.sets[allgnps[s]].rules.append(r)
                        r.gnps.append(allgnps[s])

    def cost_sets(self):
        jobs = []
        results = []
        # find all lookup intersections that might save us something
        for i, left in enumerate(self.sets):
            for j, right in enumerate(self.sets[i+1:]):
                diff = left & right
                saving = len(diff)
                if saving == 0:
                    continue
                splitcost = 10
                if saving == len(left) or saving == len(right):
                    splitcost = 0
                jobs.append([-saving + splitcost, saving, diff, i, i+j+1, []])
        jobs.sort()
        # see which ones actually save us something (through moves)
        for i, left in enumerate(self.sets):
            if len(left) == 0:      # due to previous move probably
                continue
            for j in jobs:
                if len(left) > j[1]:
                    break
                if len(j[2] & left.set) == len(left):
                    j[0] -= j[1] + 10
                    j[5].append(i)
                    break
        jobs.sort()
        if len(jobs):
            log.debug("jobs[{}]: {}".format(len(jobs), jobs[0]))
        count = len(self.sets)
        # turn useful intersections into actions
        for j in jobs:
            if j[0] >= 0:
                break
            if len(j[5]) == 0:
                if j[0] >= -self.sets[j[3]].rulecost() - self.sets[j[4]].rulecost():
                    continue
                results.append((j[0], j[3], j[4], 0))
                c = count
                count += 1
            elif len(self.sets[j[3]]) == j[1]:
                c = j[3]
            else:
                c = j[4]
            for k in j[5]:
                if c != k:
                    results.append((j[0] + 1, c, k, 2))
        return results

    def reduceSets(self, tracefile=None):
        ''' Split and merge sets to reduce overall GPOS size '''
        finished = False
        cs = self.cost_sets()
        while not finished and len(cs) > 0:
            finished = True
            for cost, i, j, action in sorted(cs):
                log.debug("Cost: {}, {}, {} doing {}".format(-cost, i, j, action))
                if action == 2:
                    self.sets[j].moveto(self.sets, j, self.sets[i], i)
                    finished = False
                elif action == 1:
                    self.sets[i].moveto(self.sets, i, self.sets[j], j)
                    finished = False
                else:
                    newset = GNPSet(list(self.sets[i] & self.sets[j]))
                    count = len(self.sets)
                    self.sets[i].remove(newset, count)
                    self.sets[j].remove(newset, count)
                    if len(newset.rules):
                        finished = False
                        self.sets.append(newset)
                if tracefile is not None:
                    self.outtext(tracefile, {}, mode="a")
            cs = self.cost_sets()
        if tracefile is not None:
            self.outtext(tracefile, {}, mode="a")

    def numlookups(self):
        c = sum(1 if len(x.rules) else 0 for x in self.sets)
        c += len(self.layers)
        return c

    def totallookuplength(self):
        c = sum(len(x) if len(x.rules) else 0 for x in self.sets)
        c += sum(len(l.strings) for l in self.layers)
        return c

    def stringslength(self):
        c = sum(1 if not any(s in l for l in self.layers) else 0 for s in self.strings)
        c += sum(len(list(l.contexts())) for l in self.layers)
        d = sum(len(l.strings) for l in self.layers)
        if d > 0:
            return "{}+{}".format(c, d)
        else:
            return c

    def rebuild_strings(self):
        ''' Merge rules in a set and recreate strings from sets '''
        self.strings = []
        for i, s in enumerate(self.sets):
            ri = 0
            s.rules = [r for r in s.rules if len(r.match) and len(r.match[0].keys)]
            while ri < len(s.rules):
                s.rules = s.rules[:ri+1] + [r for r in s.rules[ri+1:] if not s.rules[ri].addString(r)]
                ri += 1
            self.strings.extend(s.rules)

    def addLayers(self):
        """ Create layers """
        layers = {}
        # Find all context substrings and create lists of strings matching them
        for r in self.strings:
            for i in range(len(r.pre)+1):
                prek = ":".join(x.asStr() for x in r.pre[0:i])
                for j in range(len(r.post)+1):
                    postk = ":".join(x.asStr() for x in r.post[-j:])
                    k = prek + "=" + postk
                    if k == "=":        # Don't want empty context
                        continue
                    if k not in layers:
                        l = Layer()
                        layers[k] = l
                        l.addContext(r.pre[0:i], r.post[-j:])
                    else:
                        l = layers[k]
                    l.addString(r)
        log.debug("Start with {} layers".format(len(layers)))
        jobs = []
        keys = list(layers.keys())
        # find all mergeable contexts
        for i in range(len(keys)):
            if len(layers[keys[i]].strings) < 5:
                del layers[keys[i]]
                continue
            for j in range(i+1, len(keys)):
                if len(layers[keys[j]].strings) < 5:
                    continue
                s = layers[keys[i]].mergeScore(layers[keys[j]])
                if s > 5:
                    jobs.append((s, keys[i], keys[j]))
        log.debug("Start with {} jobs {}".format(len(jobs), jobs))
        # merge context groups into layers finding maximum overlap
        while len(jobs):
            jobs.sort(reverse=True)
            j = jobs.pop(0)
            if j[0] < 10 or j[1] not in layers or j[2] not in layers:
                break
            layers[j[1]].merge(layers[j[2]])
            del layers[j[2]]
            for k in jobs:
                if k[1] == j[2]:
                    l = 2
                elif k[2] == j[2]:
                    l = 1
                else:
                    continue
                jobs.remove(k)
                if k[l] != j[1]:
                    s = layers[j[1]].mergeScore(layers[k[l]])
                    jobs.append((s, j[1], k[l]))
        self.layers = [l for l in layers.values() if l.reduce() > 10]

    def addIntoLayers(self):
        newstrings = [set() for i in range(len(self.layers))]
        debug_count = 0
        for r in self.strings:
            r.afterchain = False
            if any(r in l for l in self.layers):
                continue
            for i, l in enumerate(self.layers):
                for s in sum((list(l.inAllContexts(x)) for x in list(l.strings)), []):
                    for t in list(newstrings[i]):
                        if t.subOverlap(s):
                            newstrings[i].remove(t)
                            d = t.differences(s)
                            newstrings[i].update(d)
                            debug_count += 1
                    if r.subOverlap(s):
                        d = r.differences(s, assumeOverlap=True)
                        if d is not None and len(d):
                            newstrings[i].update(d)
                        r.afterchain = True
        log.debug("Reworked {}".format(debug_count))
        for i, l in enumerate(self.layers):
            if len(newstrings[i]):
                l.strings.update(newstrings[i])

    def learnClasses(self, keys, cmap, count=1):
        if len(keys) > 1:
            k = " ".join(cmap[x] for x in sorted(keys))
            if k not in self.classes:
                self.classes[k] = count
            else:
                self.classes[k] += count

    def assignClasses(self):
        res = []
        count = 1
        for k, v in sorted(self.classes.items(), key=lambda x: (-x[1], len(x[0]), x[0])):
            if v > 1:
                self.classes[k] = "@kernClass_{}".format(count)
                count += 1
                res.append("{} = [{}];  # used {} times".format(self.classes[k], k, v))
            else:
                del self.classes[k]
        return "\n".join(res)

    def lookupClass(self, keys, cmap):
        if len(keys) > 1:
            k = " ".join(cmap[x] for x in sorted(keys))
            return self.classes.get(k, "["+k+"]")
        else:
            return cmap[keys[0]]

    def sortkey(self, s):
        return (-len(s.match), -len(s.pre), -len(s.post), getattr(s, 'gnps', [10000])[0])

    def outfea(self, outfile, cmap, rtl=False):
        self.classes = {}
        rules = []
        allPositions = {}
        lkupmap = {}
        rlkupmap = [0] * len(self.sets)
        posfmt = "    pos {0} " + ("<{1[0]} 0 {1[0]} 0>;" if rtl else "{1[0]};")
        count = 0
        with open(outfile, "w") as outf:
            poslkups = []
            for i, g in enumerate(self.sets):
                if not len(g.rules):
                    continue
                poslkup = []
                for k in g: #sorted(g):
                    p = g.parseKey(k)
                    if p[1][0] != 0 or p[1][1] != 0:
                        poslkup.append(posfmt.format(cmap[p[0]], p[1]))
                if not len(poslkup):
                    continue
                #poslkups.append(sorted(poslkup))
                poslkups.append(poslkup)
                rlkupmap[count] = i
                count += 1
            print("Number of lookups {}".format(len(poslkups)))
            for i, li in enumerate(sorted(range(len(poslkups)), 
                        key=lambda x:(len(poslkups[x]), "\n".join(y.split()[1] for y in poslkups[x])))):
                l = poslkups[li]
                lkupmap[rlkupmap[li]] = i
                poslkup = ["lookup kernpos_{} {{".format(i)] + l + ["}} kernpos_{};".format(i)]
                outf.write("\n".join(poslkup) + "\n\n")

            for r in sorted(self.strings, key=lambda x:-len(x)):
                for m in r.pre + r.match + r.post:
                    self.learnClasses(m.keys, cmap)
            for l in self.layers:
                l.makeSets(self, cmap)
            outf.write("\n")
            outf.write(self.assignClasses())
            outf.write("\n")
            for i, l in enumerate(self.layers):
                rules = (l.outFeaLookup(i, cmap, self, lkupmap))
                outf.write("\n".join(rules) + "\n")
            rules = []
            for r in sorted(self.strings, key=self.sortkey):
                if not getattr(r, 'afterchain', False) and not any(r in l for l in self.layers):
                    rules.append(self.outFeaString(r, cmap, lkupmap))
            rules.append("")
            for i, l in enumerate(self.layers):
                rules.extend(l.outFeaRef(i, cmap, self))
            rules.append("")
            for r in sorted(self.strings, key=self.sortkey):
                if getattr(r, 'afterchain', False):
                    rules.append(self.outFeaString(r, cmap, lkupmap))
            outf.write("lookup mainkern {\n    ")
            outf.write("\n    ".join(rules))
            outf.write("\n} mainkern;\n")

    def outFeaMatch(self, r, match, cmap, lkupmap):
        count = 0
        rule = []
        for m in match:
            if m.hasPositions and r.gnps[count] in lkupmap:
                s = m.asStr(cmap)
                lnum = lkupmap[r.gnps[count]]
                count += 1
                rule.append(self.lookupClass(m.keys, cmap) + "' lookup kernpos_{}".format(lnum))
            else:
                rule.append(self.lookupClass(m.keys, cmap) + "'")
        return rule

    def outFeaString(self, r, cmap, lkupmap):
        rule = []
        for m in r.pre:
            rule.append(self.lookupClass(m.keys, cmap))
        rule.extend(self.outFeaMatch(r, r.match, cmap, lkupmap))
        for m in r.post:
            rule.append(self.lookupClass(m.keys, cmap))
        return "pos " + " ".join(rule) + ";"

    def outtext(self, outfile, cmap, mode="w"):
        self.classes = {}
        with open(outfile, mode) as fh:
            if len(self.layers):
                for r in sorted(self.strings, key=lambda x:-len(x)):
                    for m in r.pre + r.match + r.post:
                        self.learnClasses(m.keys, cmap)
                for i, l in enumerate(self.layers):
                    fh.write(l.outText(cmap, i))
                fh.write("\nMain rules:\n")
            else:
                for r in sorted(self.strings, key=lambda x:(-len(x), x.key())):
                    fh.write(r.asStr(cmap=cmap)+"\n")
            if mode == "a":
                fh.write("\n----------\n")


class GNPSet:
    ''' Corresponds to a single positioning lookup with all the rules that feed into it '''
    gnpformat = "{0}:{1[0]},{1[1]}"
    def __init__(self, gids, positions=None):
        if positions is None:  # treat gids as keys
            self.set = set(gids)
        else:
            self.set = set(self.gnpformat.format(gids[i], positions[i]) for i in range(len(gids)))
        self.rules = []
        self.setcosts = []
        self.movedto = None

    def __str__(self):
        return " ".join(self.set)

    def __contains__(self, v):
        return v in self.set

    def __len__(self):
        return len(self.set)

    def __iter__(self):
        return iter(self.set)

    def __and__(self, othergnpset):
        return self.set & othergnpset.set

    def __eq__(self, other):
        return self.set == other.set

    def add(self, gid, position=None):
        if position is None:
            self.set.add(gid)
        else:
            self.set.add(self.gnpformat.format(gid, position))

    def set_cost(self, i, cost=None):
        if i >= len(self.setcosts):
            self.setcosts += [0] * (i - len(self.setcosts) + 1)
        if cost is None:
            return self.setcosts[i]
        else:
            self.setcosts[i] = cost
            return cost

    def asgnps(self):
        res = [self.parseKey(k) for k in sorted(self.set)]
        return res
            
    def parseKey(self, key):
        gid, poses = key.split(":")
        pos = Position(*[int(float(x)) for x in poses.split(",")])
        return (int(gid), pos)

    def remove(self, newgnps, newindex):
        log.debug("Removing {}: {}".format(newindex, newgnps))
        self.set = self.set - newgnps.set
        results = []
        newg = newgnps.asgnps()
        removedc = 0
        for i, r in enumerate(self.rules[:]):
            news = r.splitgnp(newg, newindex)
            if news is not None:
                for nr in newgnps.rules:
                    if nr.addString(news):
                        break
                else:
                    results.append(news)
                    newgnps.rules.append(news)
                # why doesn't this work?
                if 0:
                    for nr in self.rules[:i-removedc]:
                        if nr.addString(r):
                            del self.rules[i - removedc]
                            # self.rules.remove(r)
                            removedc += 1
                            break
        return results

    def moveto(self, allsets, currindex, newgnps, newindex):
        log.debug("Moving {} to {}".format(currindex, newindex))
        for r in self.rules:
            for nr in newgnps.rules:
                if nr.addString(r):
                    break
            else:
                newgnps.rules.append(r)
            r.movegnp(currindex, newindex)
        newgnps.set.update(self.set)
        self.rules = []
        self.set = set()
        self.movedto = newindex

    def rulecost(self):
        return sum(3 * len(r) + 2 * len(r.match) + 10 for r in self.rules)

class Layer:
    def __init__(self):
        self.contextset = set()
        self.base_context = None
        self.strings = set()
        self.covered_strings = set()
        self.all_contexts = []

    def __contains__(self, s):
        ''' Does this layer contain the given string '''
        return s in self.strings or s in self.covered_strings

    def contexts(self):
        ''' Iterates over all the contexts shortest first '''
        return self.all_contexts

    def calc_vals(self):
        self.all_contexts = sorted(self.contextset, key=lambda x:len(x[0])+len(x[1]))

    def addContext(self, pre, post):
        c = (tuple(pre), tuple(post))
        if self.base_context == None or sum(self.base_context) < sum(c):
            self.base_context = c
        if c not in self.contextset:
            self.contextset.add(c)
            self.calc_vals()

    def inAllContexts(self, s):
        ''' Iterate returning a string expanded by all contexts '''
        for c in self.contexts():
            yield String(pre = c[0], post = c[1], match = (s[len(c[0]):-len(c[1])] if len(c[1]) else s[len(c[0]):]))

    def findContext(self, s):
        ''' If we could add a string, return True '''
        res = None
        for c in self.contexts():
            cpre = listPrefix(s.pre, c[0])
            cpost = listPrefix(reversed(s.post), reversed(c[1]))
            if cpre < len(c[0]) or cpost < len(c[1]):
                return False
        return True

    def findCLengths(self, s):
        ''' Finds the longest matching context and the amount to trim off the string to match it '''
        return max((listPrefix(c[0], s.pre), listPrefix(reversed(c[1]), reversed(s.post))) for c in self.contexts())

    def findAllCLengths(self, s):
        ''' Iterates all the contexts that this string matches and the amount of trim for each one '''
        for c in self.contexts():
            res = (listPrefix(c[0], s.pre), listPrefix(reversed(c[1]), reversed(s.post)))
            # include any contexts we are a substring of
            if (res[0] == len(s.pre) or res[0] == len(c[0])) \
                    and (res[1] == len(s.post) or res[1] == len(c[1])):
                yield (res, c)

    def makeStrings(self, s):
        for c in self.contexts():
            pre = listPrefix(c[0], s.pre)
            post = listPrefix(reversed(c[1]), reversed(s.post))
            if pre == len(s.pre) and post == len(s.post):
                yield ((c[0][:-pre] if pre else c[0]) + s.pre,
                       s.post + c[1][post:], s.match)
            
    def addString(self, s):
        ''' Adds a string if we can '''
        if self.findContext(s):
            self.strings.add(s)
            return True
        return False

    def removeString(self, s):
        self.strings.discard(s)

    def mergeScore(self, other):
        ''' Returns a count of the number of strings other would add to self '''
        mode = None
        for c in self.contexts():
            for d in other.contexts():
                cpre = listPrefix(c[0], d[0])
                cpost = listPrefix(reversed(c[1]), reversed(d[1]))
                if mode is None:
                    if cpre == len(c[0]) and cpre == len(d[0]) and cpost == len(c[1]) and cpost == len(d[1]):
                        pass
                    elif cpre == len(c[0]) and cpost == len(c[1]):
                        mode = 1
                    elif cpre == len(d[1]) and cpost == len(d[1]):
                        mode = 2
                    else:
                        return 0
                elif mode == 1 and (cpre != len(c[0]) or cpost != len(c[1])):
                    return 0
                elif mode == 2 and (cpre != len(d[0]) or cpost != len(d[1])):
                    return 0
        count = 0
        for s in other.strings:
            if self.findContext(s):
                count += 1
        return count

    def merge(self, other):
        ''' Assumes a mergeScore > 0 which means contexts can merge '''
        for c in other.contexts():
            self.contextset.add(c)
        for s in list(other.strings):
            if self.addString(s):
                other.removeString(s)
        self.calc_vals()

    def reduce(self):
        ''' Removes duplicate strings. Returns True if there is more than one unique string
            with the same lookup/gnp in the strings. Also removes strings if the string does
            not occur in all contexts '''
        count = 0
        def skey(x):
            return getattr(x, 'gnps', [10000])
        # Use mark and sweep
        for r in self.strings:
            r.keepme = 0
        for g in itertools.groupby(sorted(self.strings, key=skey), key=skey):
            cache = {}
            strings = {}
            for r in g[1]:
                for p, c  in self.findAllCLengths(r):
                    k = " ".join(x.asStr() for x in (r[p[0]:-p[1]] if p[1] else r[p[0]:]))
                    if k in cache:
                        if id(c) in cache[k]:
                            self.strings.remove(r)
                            self.covered_strings.add(r)
                            count += 1
                        else:
                            cache[k].add(id(c))
                            strings[k].add(r)
                    else:
                        cache[k] = set([id(c)])
                        strings[k] = {r}
            allvals = []
            for k, v in cache.items():
                if len(v) == len(self.contextset):
                    count += len(strings[k])-1
                    allvals.append(strings[k])
            if len(allvals):
                allrs = set.union(*allvals)
                bestset = next(set(picks) for size in itertools.count(1)
                    for picks in itertools.combinations(allrs, size)
                    if all(any(i in s for i in picks) for s in allvals))
                for r in allrs:
                    # r.keepme = 1 if r in bestset else 2
                    r.keepme = 1
        if count > 0:
            for r in list(self.strings):
                if r.keepme != 1:
                    self.strings.remove(r)
                if r.keepme == 2:
                    self.covered_strings.add(r)
        log.debug(self.strings)
        return count

    def makeSets(self, parent, cmap):
        ''' Creates sets of glyphs for each main lookup match string to this lookup.
            Creates different sets for each length of match string '''
        allsets = []
        alllengths = set()
        # import pdb; pdb.set_trace()
        for s in self.strings:
            p = self.findCLengths(s)
            l = len(s) - p[0] - p[1]
            if l == 0:          # this shouldn't happen
                continue
            if l not in alllengths:
                alllengths.add(l)
                while l >= len(allsets):
                    allsets.append([])
            for j, a in enumerate(allsets[l]):
                count = 0
                for i, r in enumerate((s[p[0]:-p[1]] if p[1] else s[p[0]:])):
                    rset = set(r.keys)
                    rset.difference_update(a[i])
                    if not len(rset):
                        count += 1
                if count == l - 1:
                    updatei = j
                    break
            else:
                allsets[l].append([set() for i in range(l)])
                updatei = len(allsets[l]) - 1
            for i, r in enumerate((s[p[0]:-p[1]] if p[1] else s[p[0]:])):
                allsets[l][updatei][i].update(r.keys)
        self.sets = [[[sorted(s) for s in l] for l in a] for a in allsets]
        self.lengths = sorted(alllengths)
        for a in self.sets:
            for l in a:
                for s in l:
                    parent.learnClasses(s, cmap, count=len(self.contextset))

    def outFeaRef(self, index, cmap, parent):
        ''' Creates rules to match and call our lookup, in the main lookup '''
        rules = []
        allrules = set()
        log.debug(self.sets)
        for c in self.contexts():
            for l in self.lengths:
                for a in self.sets[l]:
                    rule = ["pos"]
                    for p in c[0]:
                        rule.append(parent.lookupClass(p.keys, cmap))
                    rule.append(parent.lookupClass(sorted(a[0]), cmap) + "' lookup kernposchain_{}".format(index))
                    for s in a[1:l]:
                        rule.append(parent.lookupClass(sorted(s), cmap) + "'")
                    for p in c[1]:
                        rule.append(parent.lookupClass(p.keys, cmap))
                    arule = (" ".join(rule) + ";").replace("'", "")
                    if arule not in allrules:
                        allrules.add(arule)
                        rules.append(" ".join(rule) + ";")
        return rules

    def outFeaLookup(self, index, cmap, parent, lkupmap):
        ''' Creates the lookup itself '''
        rules = []
        rules.append("lookup kernposchain_{} {{".format(index))
        ruleset = set()
        for s in sorted(self.strings, key=lambda x:(getattr(x, 'gnps', [10000])[0], -len(x))):
            p = self.findCLengths(s)
            rule = ["    pos"]
            rule.extend(parent.lookupClass(n.keys, cmap) for n in s.pre[p[0]:])
            rule.extend(parent.outFeaMatch(s, s.match, cmap, lkupmap))
            rule.extend(parent.lookupClass(n.keys, cmap) for n in (s.post[:-p[1]] if p[1] else s.post))
            if getattr(s, 'afterchain', False):
                print(rule, p, s.asStr(), (len(s.pre), len(s.match), len(s.post)))
            ruleset.add((-len(rule), " ".join(rule) + ";"))
        rules.extend(r[1] for r in sorted(ruleset))
        rules.append("}} kernposchain_{};".format(index))
        return rules

    def outText(self, cmap, index):
        res = ["---layer {}---".format(index)]
        for s in sorted(self.strings, key=lambda x:(getattr(x, 'gnps', [10000])[0], -len(x))):
            res.append(s.asStr(cmap=cmap))
        return "\n".join(res)


def addString(collections, s, rounding=0):
    for n in s.splitall():
        g = n.match[0].gid
        if g not in collections:
            collections[g] = Collection()
        collections[g].addString(n, rounding=rounding)

def printall(res, go):
    return "\n".join(r.asStr(cmap=go) for r in sorted(res, key=lambda x:x.key()))

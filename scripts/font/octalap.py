#!/usr/bin/env python3

# Copyright (c) 2018,2020 SIL International  (http://www.sil.org)
# Released under the MIT License (http://opensource.org/licenses/MIT)

import sys, os

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from beziers.path import BezierPath
from beziers.utils import isclose
from beziers.line import Line
from beziers.point import Point
from beziers.affinetransformation import AffineTransformation
from beziers.utils.pens import BezierPathCreatingPen
from fontTools.ttLib import TTFont
from collections import namedtuple
from math import floor
import argparse, json
from multiprocessing import Pool

def fromFonttoolsGlyph(font, glyphname):
    """Returns an *array of BezierPaths* from a FontTools font object and glyph name."""
    glyphset = font.getGlyphSet()
    pen = BezierPathCreatingPen(glyphset)
    _glyph = font.getGlyphSet()[glyphname]
    _glyph.draw(pen)
    return pen.paths

class _Object():
    pass

OctaScore = namedtuple("OctaScore", "left right score")
subbox_map = {'left' : 'xi', 'right': 'xa', 'bottom': 'yi', 'top': 'ya',
              'diagNegMin': 'si', 'diagNegMax': 'sa', 'diagPosMin': 'di', 'diagPosMax': 'da'}
scalings = {'x': lambda o, v: (v - o.xi) / (o.xa - o.xi),
            'y': lambda o, v: (v - o.yi) / (o.ya - o.yi),
            's': lambda o, v: (v - o.xi - o.yi) / (o.xa + o.ya - o.xi - o.yi),
            'd': lambda o, v: (v - o.xi + o.ya) / (o.xa - o.yi - o.xi + o.ya)}

class Octabox(object):
    """Holds a list of segments and calculates its bounding octabox"""
    def __init__(self, segs, subbox=None, scale=None, clip=None, **kw):
        """ Either pass in a list of segments or a fonttools.Glat.octabox.subbox
            And/or you can supplement with explicit xa, xi type values"""
        self.clip = clip
        def clipv(x, y=None):
            if clip is None:
                return None
            elif y is None:
                return clip[x]
            elif y < 0:
                return clip[x] - clip[-y]
            else:
                return clip[x] + clip[y]
        self.segs = segs
        for a in 'xysd':
            setattr(self, a+'i', 1e6)
            setattr(self, a+'a', -1e6)
        if len(self.segs):
            for s in segs:
                self._update_box(s[0])
                self._update_box(s[-1])
                if len(s) == 3:
                    self._update_curve(s, 'x', lambda p: p.x, (clipv(0), clipv(2)))
                    self._update_curve(s, 'y', lambda p: p.y, (clipv(1), clipv(3)))
                    self._update_curve(s, 's', lambda p: p.x + p.y, (clipv(0, 1), clipv(2, 3)))
                    self._update_curve(s, 'd', lambda p: p.x - p.y, (clipv(0, -3), clipv(2, -1)))
        elif subbox is not None and scale is not None:
            for k, v in subbox_map.items():
                r = getattr(subbox, k, 0.) / 255.
                if v.startswith('d'):
                    val = (scale.xi - scale.ya) * (1-r) + (scale.xa - scale.yi) * r
                elif v.startswith('s'):
                    val = (scale.xi + scale.yi) * (1-r) + (scale.xa + scale.ya) * r
                elif v.startswith('x'):
                    val = scale.xi * (1-r) + scale.xa * r
                elif v.startswith('y'):
                    val = scale.yi * (1-r) + scale.ya * r
                setattr(self, v, val)
        for k, v in kw.items():
            setattr(self, k, v)
        for k in 'xysd':
            a = getattr(self, k+'a')
            i = getattr(self, k+'i')
            if i == 1e6:
                i = 0
                setattr(self, k+'i', i)
            if a < i:
                a = i
                setattr(self, k+'a', a)

    def __str__(self):
        return "[({},{}), ({},{}), ({},{}), ({},{})]".format(self.xi, self.xa,
                self.yi, self.ya, self.si, self.sa, self.di, self.da)

    def as_tuple(self):
        return tuple([self.xi, self.xa, self.yi, self.ya, self.si, self.sa, self.di, self.da])

    def _update_curve(self, s, attrib, fn, clip):
        d2 = fn(s[0]) - 2*fn(s[1]) + fn(s[2])
        if isclose(d2, 0):
            return
        t = (fn(s[0]) - fn(s[1])) / d2
        if 0 <= t <= 1:
            p = s.pointAtTime(t)
            v = fn(p)
            if clip[0] is not None and v < clip[0]:
                if clip[0] - v > 0.1:
                    print(f"Clipping out of box curve point underflow {v} to {clip[0]}")
                v = clip[0]
            elif clip[1] is not None and v > clip[1]:
                if v - clip[1] > 0.1:
                    print(f"Clipping out of box curve point overflow {v} to {clip[1]}")
                v = clip[1]
            if v < getattr(self, attrib+"i"):
                setattr(self, attrib+"i", v)
            if v > getattr(self, attrib+"a"):
                setattr(self, attrib+"a", v)

    def _update_box(self, p):
        if p.x < self.xi:
            self.xi = p.x
        if p.x > self.xa:
            self.xa = p.x
        if p.y < self.yi:
            self.yi = p.y
        if p.y > self.ya:
            self.ya = p.y
        if p.x + p.y < self.si:
            self.si = p.x + p.y
        if p.x + p.y > self.sa:
            self.sa = p.x + p.y
        if p.x - p.y < self.di:
            self.di = p.x - p.y
        if p.x - p.y > self.da:
            self.da = p.x - p.y

    @property
    def area(self):
        """ Returns the area of the octabox. """
        a = (self.xa - self.xi) * (self.ya - self.yi)
        c = (self.ya - self.xi + self.di) ** 2 + (self.xa - self.sa + self.ya) ** 2
        c += (self.xa - self.da - self.yi) ** 2 + (self.si - self.xi - self.yi) ** 2
        return a - 0.5 * c

    def bestcut(self, args=None):
        """ Find the best line that cuts this octabox and its segments so that the
            resulting two bounding octaboxes (of the two sets of segments) is minimised."""
        currbest = OctaScore(self, None, self.area)
        for x,d in enumerate(((1, 0), (0, 1), (-1, 1), (1, 1))):
            splitline = Line(Point(d[0]*self.xi, d[1]*self.yi), Point(d[0]*self.xa, d[1]*self.ya))
            for sl in findshifts(self.segs, splitline):
                r, l = splitWith(self.segs, sl)
                rightbox = Octabox(r, clip=self.clip)
                leftbox = Octabox(l, clip=self.clip)
                score = rightbox.area + leftbox.area
                if args is not None and args.detail & 8:
                    print("    {}:L[{}, {}], R[{}, {}]".format("xysd"[x], leftbox.area, sum(s.area for s in leftbox.segs),
                        rightbox.area, sum(s.area for s in rightbox.segs)))
                if score < currbest.score:
                    currbest = OctaScore(leftbox, rightbox, score)
        return currbest


def splitWith(segs, splitline, args=None):
    """ Splits a list of segments given a straight splitting line. Returns
        2 lists of segments such that the resulting segments are closed paths. """
    trans = splitline.alignmentTransformation()
    lefts = []
    rights = []
    splits = []
    for _s in segs:
        # transform so splitline is horizontal and is y=0
        s = _s.transformed(trans)
        roots = s._findRoots("y")
        # does y=0 cut this segment?
        if len(roots) == 2:
            # chop a quadratic cuver and put parts in left and right collection
            l, r = s.splitAtTime(roots[0])
            (rights if s.start.y < 0 else lefts).append(l)
            l, r = r.splitAtTime(roots[1])
            (rights if s.end.y < 0 else lefts).append(r)
            # keep split points so we can add joinup lines later
            splits.append((l.start.x, (l.start.x < s.start.x) ^ (s.start.y < 0)))
            splits.append((l.end.x, (l.end.x > s.end.x) ^ (s.start.y < 0)))
        elif len(roots) == 1:
            # chop a straight line
            l, r = s.splitAtTime(roots[0])
            if s.start.y < 0:
                rights.append(l)
                lefts.append(r)
                splits.append((r.start.x, True))
            else:
                lefts.append(l)
                rights.append(r)
                splits.append((r.start.x, False))
        # otherwise no cut and simply allocate the segment
        elif s.start.y < 0 or s.end.y < 0:
            rights.append(s)
        else:
            lefts.append(s)
    # to convert from y=0 back to original co-ordinates
    backt = AffineTransformation()
    backt.apply_backwards(trans)
    backt.invert()
    if args is not None and args.detail & 8:
        print("      ", [(Point(s[0], 0).transformed(backt), s[1]) for s in sorted(splits)])
    curr = False
    lastP = None
    # find adjacent pairs of bounding points on the splitline and join them up on either side
    # thus making closed paths, even if the segments aren't end to start all the way round.
    for x, d in sorted(splits):
        newP = Point(x, 0)
        if d != curr:
            curr = d
        if lastP is None:
            lastP = newP
            continue
        l = Line(lastP, newP)
        r = Line(newP, lastP)
        if not d:
            rights.append(l)
            lefts.append(r)
        lastP = newP
    rights = [s.transformed(backt) for s in rights]
    lefts = [s.transformed(backt) for s in lefts]
    return (rights, lefts)

Bound = namedtuple("Bound", "x y max slope")

def _same_bounds(b1, b2):
    """ Calculate if a point is 'inline' with a point we have already seen.
        If the point is close and the slopes are both in the same direction, then
        we say yes. The points must also be at opposite ends of the segment. """
    if b1.max == b2.max:
        return False
    if isclose(b1.x, b2.x) and isclose(b1.y, b2.y):
        return b1.slope * b2.slope >= 0
    return False

def _addBound(bounds, bound):
    return []
    if any(True for b in bounds if _same_bounds(b, bound)):
        return bounds
    else:
        return bounds + [bound]
        
def findshifts(segs, splitline):
    """ Yields lines which are possible positions of splitline. This includes
        all maxima and minima on the segments list and also every 20 units. """
    trans = splitline.alignmentTransformation()
    bounds = []
    maxy = -1e6
    miny = 1e6
    for _s in segs:
        # rotate segment so dealing purely in y, the splitline is in effect horizontal
        s = _s.transformed(trans)
        # add segment ends or any maxima to the list of possible positions
        if len(s) == 2:
            bounds = _addBound(bounds, Bound(s[0].x, s[0].y, s[0].y > s[1].y, s.slope))
            bounds = _addBound(bounds, Bound(s[1].x, s[1].y, s[1].y >= s[0].y, s.slope))
            # collect overall segment list extrema in y
            maxy = max(maxy, s[0].y, s[1].y)
            miny = min(miny, s[0].y, s[1].y)
        elif len(s) == 3:
            d2 = s[0].y-2*s[1].y+s[2].y
            if not isclose(d2, 0.):
                rt = (s[0].y-s[1].y)/d2
                if 0 <= rt <= 1.:
                    p = s.pointAtTime(rt)
                    bounds.append(Bound(p.x, p.y, d2 < 0., 0.))
                    maxy = max(maxy, s[0].y, s[2].y, p.y)
                    miny = min(miny, s[0].y, s[2].y, p.y)
                    continue
            bounds = _addBound(bounds, Bound(s[0].x, s[0].y, s[0].y > s[2].y, s.derivative()[0].slope))
            bounds = _addBound(bounds, Bound(s[2].x, s[2].y, s[2].y >= s[0].y, s.derivative()[1].slope))
            maxy = max(maxy, s[0].y, s[2].y)
            miny = min(miny, s[0].y, s[2].y)
    # create transform back from horizontal to original direction
    backt = AffineTransformation()
    backt.apply_backwards(trans)
    backt.invert()
    last = None
    # yield each of the calculated bounds as a splitline
    for b in sorted(bounds, key=lambda b:(b[1], b)):
        if last is not None and isclose(last, b[1]):
            continue
        res = splitline.transformed(trans)
        res[0].y += b.y
        res[1].y += b.y
#        yield res.transformed(backt)
        last = b[1]
    # Now yield every 20 em units as a splitline
    for y in range(int(miny), int(maxy), max(20, int((maxy - miny) * .05))):
        res = splitline.transformed(trans)
        res[0].y += y
        res[1].y += y
        yield res.transformed(backt)

def isEncompassed(inside, outside):
    """ Is inside completely enclosed by outside path? """
    for s in inside.asSegments():
        for r in outside.asSegments():
            l = (s[0].x - r[0].x)*(r[1].y - r[0].y) - (s[0].y - r[0].y)*(r[1].x - r[0].x)
            if l > 0:
                return False
    return True

def removeEncompassed(paths, verbose):
    """ Remove all completely enclosed paths """
    res = []
    for i in range(len(paths)):
        p1 = paths[i]
        for p2 in res + paths[i+1:]:
            if isEncompassed(p1, p2):
                if verbose:
                    print("Removing encompassed path")
                break
        else:
            res.append(p1)
    return res

def calcStart(f, n, verbose):
    g = f['glyf'][n]
    bbox = (g.xMin, g.yMin, g.xMax, g.yMax)
    #bs = BezierPath.fromFonttoolsGlyph(g, gset, f['glyf'])
    bs = fromFonttoolsGlyph(f, n)
#    for b in bs:
#        b.removeOverlap()
    bs = removeEncompassed(bs, verbose)
    segs = sum((b.asSegments() for b in bs), [])
    area = sum(s.area for s in segs)
    start = Octabox(segs, clip=bbox)
    return start

def processone(f, hasOctaBoxes, n, verbose, args):
    """ Process a single glyph to calculate the best set of Octabox objects
        to cover this glyph. """
    if verbose:
        print("Processing glyph {}".format(n))
    start = calcStart(f, n, verbose)
    curr = [start]
    for i in range(15):
        best = OctaScore(start, None, 0)
        bestj = -1
        for j, c in enumerate(curr):
            b = c.bestcut(args)
            # how much does the best cut of this octabox reduce the area of that octabox?
            score = c.area - (b.left.area + (b.right.area if b.right is not None else 0))
            if score > best.score:
                best = b
                bestj = j
        # Update list of octaboxes with the best split
        if bestj >= 0:
            if args.threshold > 0. and best.score < args.threshold ** 2:
                break
            if len(best.left.segs):
                curr[bestj] = best.left
                if best.right is not None and best.right.area > 0.:
                    curr.append(best.right)
            elif best.right is not None and best.right.area > 0. and len(best.right.segs):
                curr[bestj] = best.right
    return (curr, n, start)

def outputone(f, outjson, start, hasOctaBoxes, args, curr, n):
    """ Updates a glyph with the set of Octabox objects as subboxes, if an output
        file is requested. Also does textual results reporting. """
    g = f['glyf'][n]
    boxarea = sum(c.area for c in curr)
    area = sum(sum(s.area for s in c.segs) for c in curr)
    if hasOctaBoxes:
        bboxbase = f['Glat'].attributes[n].octabox
        obase = Octabox([], xi = g.xMin, xa = g.xMax, yi = g.yMin, ya = g.yMax)
        # Convert Graphite scaled subbox into an Octabox
        # Can't use Octabox constructor because the bounding octabox has different bounds for scaling
        for k, v in subbox_map.items():
            if not hasattr(bboxbase, k):
                continue
            r = getattr(bboxbase, k, 0.) / 255.
            if v.startswith('d'):
                setattr(obase, v, (obase.xi - obase.ya) * (1-r) + (obase.xa - obase.yi) * r)
            elif v.startswith('s'):
                setattr(obase, v, (obase.xi + obase.yi) * (1-r) + (obase.xa + obase.ya) * r)
        bboxes = bboxbase.subboxes
        bbox_area = 0
        for b in bboxes:
            o = Octabox([], b, scale=obase)
            bbox_area += o.area
        if bbox_area == 0:
            bbox_area = obase.area
        if args.detail & 2:
            print("{}: {} -> {}[{}] vs {}[{}] - {}".format(n, start.area, boxarea, len(curr), bbox_area, len(bboxes), area))
        if outjson:
            g.json = curr
        elif args.output and len(bboxes):
            # put back new results
            if boxarea > bbox_area and args.detail & 1:
                print("{}: Worse {}[{}] vs {}[{}]".format(n, boxarea, len(curr), bbox_area, len(bboxes)))
            newboxes = []
            for c in curr:
                newb = _Object()
                # convert from Octabox into subbox - (should this be a method in Octabox?)
                for k, v in subbox_map.items():
                    val = int(scalings[v[0]](obase, getattr(c, v)) * 255. + 0.5)
                    if val < 0:
                        print("Clipping {} to 0 for {} in {}".format(val, v, n))
                        val = 0
                    elif val > 255:
                        print("Clipping {} to 255 for {} in {}".format(val, v, n))
                        val = 255
                    setattr(newb, k, val)
                newboxes.append(newb)
            bboxbase.subboxes = newboxes
            bboxbase.subboxBitmap = (1 << len(newboxes)) - 1
    elif args.detail & 2:
        print("{}: {} -> {}[{}] - {}".format(n, start.area, boxarea, len(curr), area))
    if args.detail & 4:
        for c in curr:
            segarea = sum(s.area for s in c.segs)
            print("  "+str(c), c.area, segarea)

def multiprocessone(a):
    return processone(*a)

parser = argparse.ArgumentParser()
parser.add_argument("infont",help="Font to process")
parser.add_argument("-m","--merge",help="json file to merge in. Stops calculation")
parser.add_argument("-g","--glyph",action="append",help="Glyphs names to process")
parser.add_argument("-d","--detail",default=0,type=int,help="Give details: 0-points either side of split")
parser.add_argument("-y","--ysplit",type=int,help="y-coord for split")
parser.add_argument("-t","--threshold",type=int,default=150,help="Stop making boxes if improvement less than this em units squared")
parser.add_argument("-o","--output",help="Output font or json")
parser.add_argument("-q","--quick",action="store_true",help="Onlyl process glyphs that have subboxes already")
parser.add_argument("-v","--verbose",action="store_true",help="Be chatty")
parser.add_argument("-j","--jobs",type=int,help="How many parallel processes or 0 for arbitrary")
args = parser.parse_args()

f = TTFont(args.infont)
gset = f.getGlyphSet()
if args.glyph is None or not len(args.glyph):
    args.glyph = f.getGlyphNames()
hasOctaBoxes = f['Glat'].hasOctaboxes
if args.merge is None:
    outjson = args.output.lower().endswith(".json")
    if args.jobs is not None:
        pool = Pool(args.jobs or None)
        def multiproc(jobs):
            ress = pool.imap_unordered(multiprocessone, ((f, hasOctaBoxes, n, args.verbose, args) for n in jobs))
            for curr, n, start in ress:
                outputone(f, outjson, start, hasOctaBoxes, args, curr, n)
        process = multiproc
    else:
        def singleproc(jobs):
            for n in jobs:
                (curr, _, start) = processone(f, hasOctaBoxes, n, args.verbose, args)
                outputone(f, outjson, start, hasOctaBoxes, args, curr, n)
        process = singleproc

    jobs = []
    for n in args.glyph:
        g = f['glyf'][n]
        if g.numberOfContours == 0:
            continue
        if args.quick and hasOctaBoxes and not len(f['Glat'].attributes[n].octabox.subboxes):
            continue
        jobs.append(n)
    if args.verbose:
        print(f"Processing {len(jobs)} glyphs")
    process(jobs)
    if args.jobs is not None:
        pool.close()
        pool.join()

    if args.output:
        if outjson:
            res = {}
            for n in f['glyf'].keys():
                g = f['glyf'][n]
                if hasattr(g, 'json'):
                    res[n] = [x.as_tuple() for x in g.json]
            with open(args.output, "w") as outf:
                json.dump(res, outf, indent=4)
        else:
            f.save(args.output)
else:
    with open(args.merge, "r") as inf:
        res = json.load(inf)
        for n, vals in res.items():
            if n not in f['glyf']: continue
            start = calcStart(f, n, args.verbose)
            curr = [Octabox([], **dict(zip("xi xa yi ya si sa di da".split(' '), v))) for v in vals]
            outputone(f, False, start, hasOctaBoxes, args, curr, n)
        if args.output:
            f.save(args.output)

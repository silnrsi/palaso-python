#!/usr/bin/env python3

import fontforge
from palaso.font.fontforge import addAnchorClass
import palaso.font.ufo as ufo
from xml.etree import ElementTree
import sys, os
from optparse import OptionParser

class Point :
    def __init__(self, name, type, x, y) :
        self.name = name
        self.x = x
        self.y = y
        self.type = type    # base or mark only

    def change_name(self, name) :
        self.name = name

    def copy(self, name) :
        return Point(name, self.type, self.x, self.y)

class Glyph :
    def __init__(self, name) :
        self.isDia = False
        self.aps = []
        self.name = name
        self.props = {}

    def set_isDia(self) :
        self.isDia = True

    def addAp(self, name, type, x, y) :
        self.aps.append(Point(name, type, x, y))

    def addProperty(self, name, value) :
        self.props[name] = value

    def handleboths(self, pointinfo) :
        s = {x.name for x in self.aps}
        self.marks = {}
        for p in self.aps :
            if p.name not in pointinfo or pointinfo[p.name] != "both" : continue
            if p.type == "mark" or self.isDia :
                n = p.name + "M"
                if n not in s :
                    s.add(n)
                    self.aps.append(p.copy(n))
                if p.type == "mark" : self.marks[p.name] = p

pointinfo = {}
glyphs = {}               

parser = OptionParser(usage='%prog [options] inufo [outsfd]' )
parser.add_option("-a", "--apxml", help="Attachment point XML file to incoroprate")
parser.add_option("-b", "--base", help="List of AP names that don't imply a diacritic")

(opts, args) = parser.parse_args()


lfname = os.path.join(args[0], "lib.plist")
cfname = os.path.join(args[0], "glyphs", "contents.plist")
ufo.read_robofab_glyphlist(lfname, cfname)

font = fontforge.open(os.path.abspath(args[0]))
font.encoding = "Original"

# fixup special glyph names
if "CR" in font : font["CR"].glyphname = "nonmarkingreturn"

if opts.apxml :
    nondias = set(opts.base.split() or ())
    aps = ElementTree.parse(opts.apxml)

    # analyse APs to find whether each is a base, mark or both. If both then
    # need to generate 2 APs for each _a and an am when a is used as a base on
    # a diacritic

    # collect all points, work out what type each point is
    for ap in aps.iterfind(".//glyph") :
        name = ap.get("PSName")
        g = Glyph(name)
        glyphs[name] = g
        for p in ap.iterfind("point") :
            n = p.get("type")
            if not n : continue
            loc = p.find("location")
            if loc is None : continue

            if n.startswith("_") :
                n = n[1:]
                g.addAp(n, "mark", int(loc.get('x')), int(loc.get('y')))
                if n not in nondias : g.set_isDia()
            else :
                g.addAp(n, "base", int(loc.get('x')), int(loc.get('y')))
        for p in g.aps :
            if p.type == "mark" : continue
            if g.isDia :
                if p.name in pointinfo and pointinfo[p.name] != "mark" :
                    pointinfo[p.name] = "both"
                else :
                    pointinfo[p.name] = "mark"
            else :
                if p.name in pointinfo and pointinfo[p.name] != "base" :
                    pointinfo[p.name] = "both"
                else :
                    pointinfo[p.name] = "base"
        for p in ap.iterfind("property") :
            g.addProperty(p.get("name"), p.get("value"))

    # duplicate or rename aps and reset both to base + mark
    for g in glyphs.values() :
        g.handleboths(pointinfo)

    for k, v in pointinfo.items() :
        if v == "both" :
            pointinfo[k + "M"] = "mark"
            pointinfo[k] = "base"
            addAnchorClass(font, k + "M", type = "mark")
        addAnchorClass(font, k, type = pointinfo[k])

    for name in font :
        g = font[name]

        # remove single point paths
        g.foreground.simplify(0, ("removesingletonpoints"), 0, 0, 0)
        if name not in glyphs : continue

        gl = glyphs[name]
        for p in gl.aps :
            if p.type == "mark" :
                g.addAnchorPoint(p.name, p.type, p.x, p.y)
            elif p.name not in gl.marks :
                g.addAnchorPoint(p.name, "basemark" if pointinfo[p.name] == "mark" else "base", p.x, p.y)
        c = ""
        for k, v in gl.props.items() :
            c += "{0}: {1}\n".format(k, v)
        if c : g.comment = c

font.save(args[1] if len(args) > 1 else args[0].replace(".ufo", ".sfd"))

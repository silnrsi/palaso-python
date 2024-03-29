#!/usr/bin/env python3

import fontforge
from palaso.font.fontforge import addAnchorClass
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
    def __init__(self, etree) :
        self.isDia = False
        self.aps = []
        self.props = {}
        n = etree.find('note')
        self.notes = n.text if n is not None else ""
        for p in etree.iterfind('property') :
            self.notes = p.get('name') + ': ' + p.get('value') + "\n" + self.notes

    def set_isDia(self) :
        self.isDia = True

    def addAp(self, name, type, x, y) :
        self.aps.append(Point(name, type, x, y))

    def handleboths(self, pointinfo) :
        extras = []
        for p in self.aps :
            if pointinfo[p.name] != "both" : continue
            if p.type == "mark" :
                extras.append(p.copy(p.name + "M"))
            elif self.isDia :
                p.change_name(p.name + "M")

pointinfo = {}
glyphs = {}               

parser = OptionParser(usage="usage: %prog [options] infontfile ap.xml outfontfile")
parser.add_option("-b", "--base", help="List of AP names that don't imply a diacritic")

(opts, args) = parser.parse_args()

nondias = set(opts.base.split())
aps = ElementTree.parse(args[1])

# analyse APs to find whether each is a base, mark or both. If both then
# need to generate 2 APs for each _a and an am when a is used as a base on
# a diacritic

# collect all points, work out what type each point is
for ap in aps.iterfind(".//glyph") :
    name = ap.get("PSName")
    g = Glyph(ap)
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

# duplicate or rename aps and reset both to base + mark
for g in glyphs.values() :
    g.handleboths(pointinfo)

font = fontforge.open(os.path.abspath(args[0]))

for k, v in pointinfo.items() :
    if v == "both" :
        pointinfo[k + "M"] = "mark"
        pointinfo[k] = "base"
        addAnchorClass(font, k + "M", type = "mark")
    addAnchorClass(font, k, type = pointinfo[k])

for name in font :
    if name not in glyphs : continue
    g = font[name]
    gl = glyphs[name]
    for p in gl.aps :
        if p.type == "mark" :
            g.addAnchorPoint(p.name, p.type, p.x, p.y)
        else :
            g.addAnchorPoint(p.name, "basemark" if pointinfo[p.name] == "mark" else "base", p.x, p.y)
    g.comment = gl.notes

font.save(args[2])

#!/usr/bin/env python3

import argparse, re, time
from palaso.font.shape import HbFont
from fontTools import ttLib
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

def setname(font, nameid, s):
    font['name'].setName(s, nameid, 0, 3, 0)
    font['name'].setName(s, nameid, 3, 1, 0x409)

def copyglyph(gname, infont, outfont, lsb, x):
    lsb = min(infont['hmtx'].metrics[gname][1] + x, lsb)
    if gname in outfont['glyf']:
        return lsb
    g = infont['glyf'].get(gname, None)
    if g is None:
        return lsb
    outfont['hmtx'].metrics[gname] = infont['hmtx'].metrics[gname]
    if g.isComposite():
        glyph = Glyph()
        glyph.numberOfContours = -1
        glyph.components = []
        for gc in g.components:
            glyph.components.append(gc)
            lsb = copyglyph(gc.glyphName, infont, outfont, lsb, x + gc.x)
    elif not hasattr(g, "data"):
        glyph = Glyph(g.compile(infont['glyf']))
    else:
        glyph = Glyph(g.data)
    outfont['glyf'][gname] = glyph
    return lsb

def copyfont(infont, outfont, glyphs=False):
    for a in ("post", "name"):
        outfont[a] = infont[a]
    outfont['post'].mapping = {}
    outfont['post'].extraNames = []
    for a in ("cmap", "glyf", "hmtx", "loca"):
        if not glyphs:
            outfont[a] = ttLib.newTable(a)
        elif a in infont:
            outfont[a] = infont[a]
    if not glyphs:
        cmap = CmapSubtable.newSubtable(4)
        cmap.cmap = {}
        cmap.platformID = 0
        cmap.platEncID = 3
        cmap.language = 0
        cmapt = outfont['cmap']
        cmapt.tableVersion = 0
        cmapt.tables = [cmap]
        outfont['glyf'].glyphs = {}
        outfont['hmtx'].metrics = {}

    for a in ("head", "maxp", "hhea", "OS/2", "cvt ", "gasp"):
        if a in infont:
            outfont[a] = infont[a]

parser = argparse.ArgumentParser()
parser.add_argument("infont", help="Input TTF font file")
parser.add_argument("-o", "--outfont", required=True, help="Output TTF font file")
parser.add_argument("-c", "--config", required=True, help="Input config file")
parser.add_argument("-n", "--name", required=True, help="Output font name")
parser.add_argument("-F", "--feat", action="append", help="feat=val repeatable")
args = parser.parse_args()

infont = ttLib.TTFont(args.infont)
outfont = ttLib.TTFont()
copyfont(infont, outfont, glyphs=False)

jobs = {}
if args.config.lower().endswith(".txt"):
    with open(args.config, encoding="UTF-8") as inf:
        for l in inf.readlines():
            t = re.sub(r"#.*$", "", l.strip())
            b = t.split()
            if len(b) < 2:
                continue
            try:
                bv = [int(x, 16) for x in b]
            except ValueError:
                continue
            jobs[bv[0]] = "".join(chr(x) for x in bv[1:])

if args.feat and len(args.feat):
    feats = {b[0].strip(): b[1].strip() for x in args.feat for b in x.split("=")}
else:
    feats = None
hb = HbFont(args.infont, 0, False, feats=feats)

inglyphorder = infont.getGlyphOrder()
outglyphorder = []
outfont.setGlyphOrder(outglyphorder)
cmap = outfont['cmap'].getBestCmap()
copyglyph('.notdef', infont, outfont, 10000, 0)
for k, v in jobs.items():
    gs = hb.glyphs(v, includewidth=True)
    adv = gs.pop()[1][0]
    lsb = 10000
    glyph = Glyph()
    glyph.numberOfContours = -1
    glyph.components = []
    glyphname = ttLib.TTFont._makeGlyphName(k)
    outfont['glyf'][glyphname] = glyph
    cmap[k] = glyphname
    # outglyphorder.append(glyphname) 
    for g in gs:
        gname = inglyphorder[g[0]]
        lsb = copyglyph(gname, infont, outfont, lsb, g[1][0])
        gc = GlyphComponent()
        gc.flags = 0
        gc.glyphName = gname
        gc.x = g[1][0]
        gc.y = g[1][1]
        glyph.components.append(gc)
    outfont['hmtx'].metrics[glyphname] = [adv, lsb]

subfamily = infont['name'].getBestSubFamilyName()
full = (" " + subfamily) if subfamily.lower() not in ("regular", "standard") else ""
setname(outfont, 1, args.name)
setname(outfont, 3, "{}:{}".format(args.name, time.strftime("%Y-%m-%d")))
setname(outfont, 4, args.name + full)
setname(outfont, 16, args.name)
setname(outfont, 18, args.name + full)

outfont.save(args.outfont)

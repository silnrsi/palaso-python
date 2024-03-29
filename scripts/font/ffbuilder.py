#!/usr/bin/env python3

import psMat, fontforge, os, re, sys
from optparse import OptionParser
from xml.etree.ElementTree import parse
from palaso.font.fontforge import addAnchorClass

anchortypes = {
    'mark' : (1, None),
    'base' : (0, 'base'),
    'ligature' : (0, None),
    'basemark' : (0, None),
    'entry' : (1, None),
    'exit' : (0, 'cursive')
}

def pointMult(point, mat) :
    if point is None : return None
    x = mat[0] * point[0] + mat[2] * point[1] + mat[4]
    y = mat[1] * point[0] + mat[3] * point[1] + mat[5]
    return (x, y)

def findGlyph(e) :
    try :
        font = fonts[int(e.get("font", 0))]
    except IndexError :
        print(f"You need to specify at least {e.get('font')} extra fonts using -f")
        sys.exit(1)
    name = e.get("PSName")
    if not name and e.get("UID") :
        s = font.findEncodingSlot(int(e.get("UID"), 16))
        if s >= 0 :
            name = font[s].glyphname
    if not name and e.get("GID") :
        name = font[int(e.get("GID"))].glyphname
    font.temporary['names'][name] = None
    return (font, name)

def getanchor(glyph, name, isMark = False) :
    if not name : return (None, 0)
    for a in glyph.anchorPoints :
        if a[0] != name : continue
        if (isMark and a[1] == "mark") or (not isMark and (a[1] == "base" or a[1] == "basemark")) :
            return (a[2], a[3])
    return (None, 0)

def copyglyph(glyph, target) :
    pen = target.glyphPen()
    glyph.draw(pen)
    pen = None

class Glyph :
    def __init__(self, name, uid) :
        self.name = name            # name by which we are known
        self.uid = uid
        self.glyph = None           # concrete ff glyph object that we are a copy of
        self.children = []          # bases that constitute us
        self.scale = psMat.identity()   # scaling of concrete ff glyph points
        self.advance = -1
        self.rsb = -1
        self.lsb = -1
        self.props = {}
        self.notes = ""
        self.realGlyphs = []
        self.points = {}

    def addChild(self, gref) :
        self.children.append(gref)

    def readXml(self, elem) :
        for e in elem :
            if e.tag == "property" :
                self.props[e.get("name")] = e.get("value")
            elif e.tag == "note" :
                self.notes = e.text
            elif e.tag == "point" :
                name = e.get("name")
                p = (int(e.get("x", 0)), int(e.get("y", 0)))
                i = 0           # we don't know whether it could be a basemark yet
                if name.startswith("_") :
                    name = name[1:]
                    i = 1
                if name not in self.points :
                    self.points[name] = [None] * 3
                self.points[name][i] = p
            elif e.tag == "advance" :
                self.advance = int(e.get("width", -1))
            elif e.tag == "rsb" :
                self.rsb = int(e.get("rsb", -1))
            elif e.tag == "lsb" :
                self.lsb = int(e.get("lsb", -1))
            elif e.tag == "base" :
                (font, name) = findGlyph(e)
                g = font[name]
                for k, v in g.temporary['properties'].items() :
                    self.props[k] = v
                child = GlyphRef(font, name)
                self.addChild(child)
                child.readXml(e)

    def resolveGlyph(self, allowScaled = False) :
        if len(self.children) == 1 and len(self.children[0].children) == 0 :
            child = self.children[0]
            if not child.font.temporary['names'][child.name] and (not allowScaled or child.scale == psMat.identity()) :
                self.glyph = child.font[child.name]
                child.font.temporary['names'][child.name] = self
                self.scale = child.scale

    def resolveReferences(self, anchorMap) :
        for p, v in self.points.items() :       # sort out config defined points
            anchorMap[p][0] == "basemark" 
            self.points[p] = (None, v[1], v[0])
        scale = psMat.identity()
        for c in self.children :
            adv = c.resolveReferences(self, scale, anchorMap)
            scale = psMat.compose(scale, psMat.translate(adv, 0))
        if self.advance < 0 :
            if self.glyph :
                self.advance = pointMult((self.glyph.width, 0), self.scale)[0]
            else :
                self.advance = adv
            if self.advance < 0 : self.advance = 0

    def addRealGlyph(self, glyph, scale) :
        self.realGlyphs.append((glyph, scale))

    def mergeAnchors(self, anchors, scale) :
        for a, av in anchors.items() :
            if a in self.points :
                bv = self.points[a]
                for i in range(len(av)) :
                    if not bv[i] : bv[i] = av[i]
            else :
                self.points[a] = [pointMult(x, scale) for x in av]
            
class GlyphRef :
    def __init__(self, font, name, parent = None, at = None, withap = None) :
        self.font = font            # font we are from
        self.name = name            # our name in the font
        self.parent = parent        # what we are attached to
        self.at = at
        self.withap = re.sub("^_", "", withap) if withap else None
        self.children = []          # what is attached to us
        self.advance = None
        self.lsb = None
        self.rsb = None
        self.glyph = None           # Glyph that carries our concrete glyph which we reference
        self.scale = psMat.identity()   # scaling of glyph reference
        self.anchors = {}
        if parent :
            parent.addChild(self)

    def addChild(self, gref) :
        self.children.append(gref)

    def readXml(self, elem) :
        for e in elem :
            if e.tag == "advance" :
                self.advance = int(e.get("width", None))
            elif e.tag == "rsb" :
                self.rsb = int(e.get("rsb", None))
            elif e.tag == "lsb" :
                self.lsb = int(e.get("lsb", None))
            elif e.tag == "shift" :
                self.scale = psMat.compose(self.scale, psMat.translate(int(e.get("x", 0)), int(e.get("y", 0))))
            elif e.tag == "scale" :
                self.scale = psMat.compose(self.scale, psMat.scale(float(e.get("x", 1.)), float(e.get("y", 1.))))
            elif e.tag == "attach" :
                (font, name) = findGlyph(e)
                child = GlyphRef(font, name, parent = self, at = e.get("at"), withap = e.get("with"))
                child.readXml(e)

    def resolveReferences(self, owner, scale, anchorMap) :
        self.glyph = self.font.temporary['names'][self.name]
        glyph = self.glyph.glyph
        if self.parent :
            pglyph = self.parent.glyph.glyph
            (px, py) = getanchor(pglyph, self.at)
            if px is None :
                px = pglyph.width / 2
            (cx, cy) = getanchor(glyph, self.withap, isMark = True)
            if cx is None :
                cx = glyph.width / 2
            self.scale = psMat.compose(self.scale, psMat.translate(px - cx, py - cy))
        if self.rsb is not None :
            self.advance = glyph.width - (self.rsb - pointMult((self.rsb, 0), self.scale)[0])
        self.setGlyphAnchors(glyph, anchorMap)      # after attached scale established
        scale = psMat.compose(scale, self.scale)
        owner.addRealGlyph(self.glyph, scale)
        for c in self.children :
            c.resolveReferences(owner, scale, anchorMap)
        if self.parent :
            self.parent.mergeAnchors(self.anchors)
        else :
            owner.mergeAnchors(self.anchors, scale)
        return pointMult((self.advance if self.advance is not None else glyph.width, 0), self.scale)[0]

    def setGlyphAnchors(self, glyph, anchorMap) :
        for a in glyph.anchorPoints :
            if a[0] not in self.anchors : self.anchors[a[0]] = [None] * 3
            self.anchors[a[0]][anchortypes[a[1]][0]] = (a[2], a[3])  # pointMult((a[2], a[3]), self.scale)
            if a[1] == "basemark" :
                b = anchorMap[a[0]][1]
                if b :
                    if b not in self.anchors : self.anchors[b] = [None] * 3
                    self.anchors[b][2] = self.anchors[a[0]][anchortypes[a[1]][0]]

    def mergeAnchors(self, anchors) :
        for a, av in anchors.items() :
            if a not in self.anchors :
                self.anchors[a] = list(av)
            else :
                bv = self.anchors[a]
                if not bv[1] : bv[1] = av[1]
                if bv[0] :
                    bv[0] = av[2] if av[2] else av[0]
                else :
                    bv[2] = av[2]

def analyseAnchorRelations(anchorMap, g) :
    if not g.glyph : return
    for a in g.glyph.anchorPoints :
        if a[1] in anchorMap : continue         # don't overdo it
        if a[1] == "basemark" :                 # only interested in basemarks
            mark = None
            for b in g.glyph.anchorPoints :
                if b[1] == "mark" and b[0] == a[0] :
                    mark = b
                    break
            for b in g.glyph.anchorPoints :
                if b[1] == "mark" and b[0] != a[0] and mark is not None and \
                        abs(b[2] - mark[2]) < 5 and abs(b[3] - mark[3]) < 5 and \
                        (b[0] not in anchorMap or anchorMap[b[0]][1] is None) :
                    anchorMap[a[0]] = ("basemark", b[0])
                    anchorMap[b[0]] = ("base", a[0])
                    break
            if a[0] not in anchorMap : anchorMap[a[0]] = ("basemark", None)
        elif a[1] == "base" or a[1] == "exit" :
            anchorMap[a[0]] = ("cursive" if a[1] == "exit" else a[1], None)

namemap = ('copyright', 'family', 'subfamily', 'fontid', 'fullname', 'version', 'psname',
    'trademark', 'vendor', 'designer', 'description', 'vendor_url', 'designer_url', 'license',
    'license_url', 'reserved', 'preferred_family', 'preferred_subfamily', 'compat_full',
    'text', 'CID_name')
    

def setname(font, elem) :
    num = elem.get('num')
    lid = int(elem.get('lid', 1033))
    text = (elem.text + expandname(elem, lid)).strip()
    if num == 'name' :
        f.familyname = text
        if f.weight != "Normal" :
            f.fullname = text + " " + f.weight
        else :
            f.fullname = text
        fulltext = f.fullname.replace(" ", "")
        f.fontname = fulltext
        return
    elif num in namemap :
        num = namemap.index(num)
    f.appendSFNTName(lid, int(num), text)

def expandname(elem, lid) :
    res = ""
    for c in elem :
        if c.tag == "name" :
            num = c.get('num')
            if num in namemap : num = namemap.index(num)
            for n in f.sfnt_names :
                if n[0] == lid and n[1] == num :
                    res += n[2]
                    break
            if c.tail : res += c.tail
    return res

def readprops(f) :
    for name in f :
        g = f[name]
        g.temporary = {'properties' : {}}
        if g.comment :
            for l in g.comment.splitlines() :
                p = l.split(':')
                if len(p) == 2 :
                    g.temporary['properties'][p[0].strip()] = p[1].strip()

parser = OptionParser(usage='%prog [options] infont outfont')
parser.add_option("-c","--config",help="Configuration file to process. Required")
parser.add_option("-a","--append",action="store_true",help="append glyphs to output font")
parser.add_option("-f","--font",action="append",help="Extra font to reference")
(opts, args) = parser.parse_args()

if len(args) != 2 or not opts.config :
    parser.print_help()
    sys.exit(1)

# setup fonts[] to find fonts by numeric index
fonts = []
if not opts.font : opts.font = []
opts.font.insert(0, args.pop(0))
for f in opts.font :
    fabs = os.path.abspath(f)
    if not os.path.exists(fabs) :
        print(f"font {f} at {fabs} is missing")
        sys.exit(1)
    font = fontforge.open(fabs)
    fonts.append(font)
    font.temporary = { 'names' : {}}
    readprops(font)

# Create Glyphs for each entry in config file
glyphs = []
point_relations = {}
etree = parse(opts.config)
for e in etree.getroot().iterfind("glyphs/glyph") :
    g = Glyph(e.get("PSName"), e.get("UID"))
    g.readXml(e)
    glyphs.append(g)
# identify output Glyph for each referenced glyph
    g.resolveGlyph()

for g in glyphs : g.resolveGlyph(True)
count = 0
for f in fonts :
    for k, v in f.temporary['names'].items() :
        if not v :
            v = Glyph(f"_temp{count!s}", "")
            v.glyph = f[k]
            v.scale = psMat.identity()
            glyphs.append(v)
            f.temporary['names'][k] = v
            count += 1
# analyse anchors to find relations
        analyseAnchorRelations(point_relations, v)

# fill in anchors for each glyph

# do attachment, concrete glyph resolution and absolute positioning
for g in glyphs : g.resolveReferences(point_relations)

if opts.append :
    f = fonts[0]
else :
    # generate output font
    f = fontforge.font()
    f.encoding = "Original"

    for a in ('ascent', 'copyright', 'descent', 'em', 'gasp', 'hasvmetrics',
            'hhea_ascent', 'hhea_ascent_add', 'hhea_descent', 'hhea_descent_add',
            'hhea_linegap', 'horizontalBaseline', 'italicangle', 'macstyle',
            'os2_codepages', 'os2_family_class', 'os2_fstype', 'os2_panose',
            'os2_strikeypos', 'os2_strikeysize', 'os2_subxoff', 'os2_subxsize',
            'os2_subyoff', 'os2_subysize', 'os2_supxoff', 'os2_supxsize',
            'os2_supyoff', 'os2_supysize', 'os2_typoascent', 'os2_typoascent_add',
            'os2_typodescent', 'os2_typodescent_add', 'os2_typolinegap',
            'os2_use_typo_metrics', 'os2_vendor', # 'os2_unicoderanges', 
            'os2_version', 'os2_weight', 'os2_weight_width_slope_only',
            'os2_width', 'os2_winascent', 'os2_winascent_add', 'os2_windescent',
            'os2_windescent_add', 'sfnt_names', 'upos', 'uwidth', 'version',
            'verticalBaseline', 'weight') :
        setattr(f, a, getattr(fonts[0], a, None))

    for n in fonts[0].layers :
        if n not in f.layers :
            f.layers.add(n, fonts[0].layers[n].is_quadratic)
        else :
            f.layers[n].is_quadratic = fonts[0].layers[n].is_quadratic

    for i in ('.notdef', 'nonmarkingreturn', '.null') :
        g = f.createChar(-1, i)
        if i in fonts[0] :
            copyglyph(fonts[0][i], g)

for a, av in point_relations.items() :
    addAnchorClass(f, a, "mark" if av[0] == "basemark" else av[0])
    
for g in glyphs :
    if g.glyph :
        g1 = f.createChar(int(g.uid, 16) if g.uid else -1, g.name if g.name is not None else "")
        print(g.name)
        copyglyph(g.glyph, g1)
        g1.transform(g.scale, ("round",))
        c = ""
        for k, v in g.props.items() :
            c += "{0}: {1}\n".format(k, v)
        g1.comment = c
        g.outglyph = g1

for g in glyphs :
    if not g.glyph :
        g1 = f.createChar(int(g.uid, 16) if g.uid else -1, g.name)
        pen = g1.glyphPen()
        for c in g.realGlyphs :
            g2 = f[c[0].name]
            pen.addComponent(c[0].name, c[1])
        pen = None
    else :
        g1 = g.outglyph
    g1.width = g.advance
    for a, v in g.points.items() :
        if v[0] :
            g1.addAnchorPoint(a, point_relations[a][0], v[0][0], v[0][1])
        if v[1] :
            g1.addAnchorPoint(a, "mark", v[1][0], v[1][1])

# handle <names>
for s in etree.getroot().iterfind("names/string") :
    setname(f, s)

# handle <font> attributes
felem = etree.getroot()
finfos = {
    'ascent' : ('ascent', 'hhea_ascent', 'os2_typoascent', 'os2_winascent'),
    'descent' : ('descent', 'hhea_descent', 'os2_typodescent', 'os2_windescent'),
    'linegap' : ('hhea_linegap', 'os2_typolinegap', 'os2_winlinegap')
}
for k, v in finfos.items() :
    num = int(felem.get(k, 0))
    if num :
        for a in v :
            setattr(f, a, num)

cpinfos = {
    'cp' : (2, 'os2_codepages'),
    # 'coverage' : (4, 'os2_unicoderanges')
}
for k, v in cpinfos.items() :
    val = felem.get(k, None)
    if val :
        val = "0" * (8 * v[0] - len(val)) + val
        res = []
        for i in range(v[0] * 8, 0, -8) :
            res.append(int(val[i-8:i], 16))
        setattr(f, v[1], tuple(res))

f.save(args[0])

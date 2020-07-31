
"""FontForge support module"""

from collections import namedtuple
from math import sin, cos, pi

Box = namedtuple('Box','xmin ymin xmax ymax')
Box.xmid = property(lambda self: self[0]/2 + self[2]/2)
Box.ymid = property(lambda self: self[1]/2 + self[3]/2)
Box.width   = property(lambda self: self[2]-self[0])
Box.height  = property(lambda self: self[3]-self[1])
Box.aspect  = property(lambda self: self.width/self.height)
Box.pos     = lambda self, pos: (getattr(self,pos[0]),getattr(self,pos[1]))


def addAnchorClass(font, name, type = "base") :
    """ Adds a new anchor class to a font, if it is not already added.
        If necessary, it will create a lookup to hold the anchor in.

        Optionally type gives the type of attachment: base, mark, cursive

        Returns: name of sublookup containing the anchor
"""
    types = {
        "base" : "gpos_mark2base",
        "mark" : "gpos_mark2mark",
        "cursive" : "gpos_cursive"
    }
    try:
        sub = font.getSubtableOfAnchor(name)
        return sub
    except EnvironmentError :
        addClass = True

    try:
        lkp = font.getLookupInfo("_holdAnchors" + type)
    except:
        font.addLookup("_holdAnchors" + type, (types[type]), (), ())
        font.addLookupSubtable("_holdAnchors" + type, "_someAnchors" + type)

    font.addAnchorClass("_someAnchors" + type, name)
    return "_someAnchors" + type


def resolve_glyph_name(font, name):
    """ Given a font and glyphname try to find the glyph in the font any which way"""
    # Try psname first
    if name in font:
        return font[name]        
    # Maybe it's a glyph id?
    if name.isdigit():
        return font[int(name)]
    # Lastly try a unicode codepoint.    
    try:
        return font['uni%04X' % parse_codepoint(name)]
    except KeyError:
        raise KeyError('%s: no glyph mapped at codepoint %s' % (font.path,name))


def create_from_copy(src_glyph, uni):
    """ Copies a glyph to a new unicode value """
    font = src_glyph.font
    glyph = font.createChar(uni, 'uni%04X' % uni)
    font.selection.select(src_glyph); font.copy()
    font.selection.select(glyph); font.paste()
    return glyph


def copy_contours(src_glyph, glyph):
    """ Copy contours in one glyph into another """
    font = glyph.font
    font.selection.select(glyph);
    src_glyph.draw(glyph.glyphPen())


def make_trans_matrix(tgt, ref, pos, scale):
    """ construct a transformation matrix based on the glyph bounding boxes 
        and constraints supplied """
    t = Box(*tgt.boundingBox()); r = Box(*ref.boundingBox())
    if scale == 'auto':
        scale = 'height' if r.aspect < t.aspect else 'width'
    sf = getattr(r,scale)/getattr(t,scale) if scale else 1.0
    (tx,ty) = t.pos(pos); (rx,ry) = r.pos(pos)
    return reduce(m.compose, (m.translate(-tx,-ty), m.scale(sf), m.translate(rx,ry)))


def copy_anchors(tgt, ref, pos, scale):
    """ Copy anchors from one glyph to another applying constraints """
    tb = Box(*tgt.boundingBox()); rb = Box(*ref.boundingBox())
    # Get positions and scale factors
    (rx,ry) = rb.pos(pos)
    sx = tb.width/rb.width if scale else 1.0; sy = tb.height/rb.height if scale else 1.0
    for rap in ref.anchorPoints:
        tap = rap[:2] + ((rap[2]-rx)*sx+rx,(rap[3]-ry)*sy+ry) + rap[4:]
        tgt.addAnchorPoint(*tap)

def layer_area(layer) :
    area = 0.
    for j in range(len(layer)) :
        c = layer[j]
        for i in range(len(c)) :
            area += c[i-1].x * c[i].y - c[i].x * c[i-1].y
    return area / 2

def layer_centroid(layer) :
    cx = 0.
    cy = 0.
    a = layer_area(layer)
    if abs(a) < .00001 : return complex(0, 0)
    for j in range(len(layer)) :
        c = layer[j]
        for i in range(len(c)) :
            t = c[i-1].x * c[i].y - c[i].x * c[i-1].y
            cx += (c[i-1].x + c[i].x) * t
            cy += (c[i-1].y + c[i].y) * t
    return complex(cx / a / 6, cy / a / 6)


_magic = 0.5522847498

def do_circle(font, width, stem, num, uni = 0x25CC, name = 'uni25CC') :
    g = font.createChar(uni, name)
    if font.layers[font.activeLayer].is_quadratic :
        do_circle_quadratic(g, width, stem, num)
    else :
        do_circle_cubic(g, width, stem, num)

def do_circle_cubic(g, width, stem, num) :
    stem = stem / 2
    width = width / 2 - stem
    offsets = [(stem, 0), (0, stem), (-stem, 0), (0, -stem)]
    pen = g.glyphPen()
    for i in range(num) :
        org = (width * cos(2 * pi * i / num) + width + stem , width * sin(2 * pi * i / num) + width + stem)
        curr = (org[0] + offsets[3][0], org[1] + offsets[3][1])
        pen.moveTo(curr[0], curr[1])
        for j in range(4) :
            ncurr = (org[0] + offsets[j][0], org[1] + offsets[j][1])
            pen.curveTo((curr[0] + _magic * offsets[j][0], curr[1] + _magic * offsets[j][1]),
                        (ncurr[0] + _magic * offsets[j-1][0], ncurr[1] + _magic * offsets[j-1][1]),
                        (ncurr[0], ncurr[1]))
            curr = ncurr
        pen.closePath()
    g.width = width

def do_circle_quadratic(g, width, stem, num) :
    stem = stem / 2
    width = width / 2 - stem
    pen = g.glyphPen()
    for i in range(num) :
        org = (width * cos(2 * pi * i / num) + width + stem , width * sin(2 * pi * i / num) + width + stem)
        curr = (org[0] + stem, org[1])
        pen.moveTo(curr[0], curr[1])
        for j in range(8) :
            k = j + 1
            ncurr = (org[0] + stem * cos(2 * pi * k / 8), org[1] + stem * sin(2 * pi * k / 8))
            pcurr = (org[0] + stem / cos(2 * pi / 16) * cos(2 * pi * (2 * k - 1) / 16),
                     org[1] + stem / cos(2 * pi / 16) * sin(2 * pi * (2 * k - 1) / 16))
            pen.curveTo(pcurr, ncurr)
        pen.closePath()
    g.width = width
    return g


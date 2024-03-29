#!/usr/bin/env python3

import argparse, ctypes
import numpy as np
import freetype as ft
from palaso.font import shape

def monobits(x, depth = 1) :
    """Convert from bits to numbers"""
    if depth == 8 : return [x]
    data = []
    mask = 2 * depth - 1
    for i in range(8 / depth) :
        data.insert(0, x & mask)
        x = x >> depth
    return data

def bitmap_array(b, depth = 8) :
    """Converts a ft bitmap into a 2D array with y=0 being the top row of the bitmap"""
    if depth == 8 and b.pitch == b.width : return np.array(b.buffer).resize(b.rows, b.width)
    data = []
    for i in range(b.rows) :
        row = []
        for j in range(b.pitch) :
            row.extend(monobits(b.buffer[i * b.pitch + j]))
        data.extend(row[:b.width])
    res = np.array(data, dtype=np.int8)
    res.resize(b.rows, b.width)
    return res

class Glyph(object) :
    """Holds a glyph, its position and bitmap"""

    def __init__(self, gid, origin, name = "") :
        self.gid = gid
        self.org = (origin[0] / 64, origin[1] / 64)
        self.name = name

    def addBitmap(self, ftGlyph, depth = 8) :
        b = ftGlyph.bitmap
        self.left = ftGlyph.bitmap_left
        self.top = ftGlyph.bitmap_top
        self.width = b.width
        self.height = b.rows
        self.data = bitmap_array(b, depth)

    def thicken(self, t) :
        self.thick = np.zeros((self.height + 2*t, self.width + 2 * t), dtype = np.int8)
        for i in range(-t, t+1) :
            for j in range(-t, t+1) :
                self.thick[i+t:i+t+self.height, j+t:j+t+self.width] |= self.data

    def clashTest(s, o, t = 0) :
        # calculate left and right of overlap
        x = max(o.org[0] + o.left - t, s.org[0] + s.left)
        r = min(o.org[0] + o.left + o.width + t, s.org[0] + s.left + s.width)
        if r < x : return False

        # calculate top and bottom of overlap
        y = min(o.org[1] + o.top + t, s.org[1] + s.top)
        b = max(o.org[1] + o.top - o.height - t, s.org[1] + s.top - s.height)
        if y < b : return False

        # iterate over the overlap rectangle
        if t :
            for i in range(r - x) :
                for j in range(y - b) :
                    if s.data[s.top - 1 - (j + b - s.org[1])][i + x - s.org[0] - s.left] > 0 and \
                            o.thick[o.top - 1 - (j + b - o.org[1]) + t][i + x + t - o.org[0] - o.left] > 0 :
                        return True
        else :
            for i in range(r - x) :
                for j in range(y - b) :
                    # if both bitmap cells are non-white, then collision has occurred.
                    if s.data[s.top - 1 - (j + b - s.org[1])][i + x - s.org[0] - s.left] > 0 and \
                            o.data[o.top - 1 - (j + b - o.org[1])][i + x - o.org[0] - o.left] > 0 :
                        return True
        return False


parser = argparse.ArgumentParser()
parser.add_argument('font', help='Font file')
parser.add_argument('text', help='Text to render')
parser.add_argument('--size', type=int, default=40, help='Pixels per em to work at [40]')
parser.add_argument('--depth', type=int, default=1, choices=(1,8), help='Bit depth to work at [1]')
parser.add_argument('--shaper', '-s', choices=('ot', 'gr', 'hb', 'icu'), default='ot', help='shaper to use [ot]')
parser.add_argument('--script', help='Script to pass to shaper')
parser.add_argument('--lang', help='Language to pass to shaper')
parser.add_argument('--rtl', action='store_true', default=False, help='Render right to left')
parser.add_argument('--feat', '-f', action='append', help='id=value pairs, may be repeated')
parser.add_argument('--thicken', '-t', type=int, help="Consider collisions with error of thicken")
args = parser.parse_args()

feats={}
if args.feat :
    # iterate over all --feat parameters and parse into x=y and store in a dict
    for f in args.feat :
        k,v = f.split('=')
        feats[k.strip()] = int(v.strip())

# options to pass to Load_Glyph for each bit depth. Don't know for 2 or 4.
styleflags = { 1 : ft.FT_LOAD_TARGET_MONO, 8 : 0 }
# flags to pass to Load_Glyph to render at specified bit depth
freestyle = ft.FT_LOAD_RENDER | styleflags[args.depth]

# parse utf8 with \u type stuff in it
text = args.text.decode('raw_unicode_escape')
# Get a smart font engine according to what's been asked for
shaper = shape.make_shaper(args.shaper, args.font, args.size, args.rtl, feats, args.script, args.lang)

# get a ft face
face = ft.Face(args.font)
# shift left 6 bits to account for fractional point sizes
face.set_char_size(args.size * 64)

glyphs = []
# render the string using the engine and iterate over the glyphs it makes
for g in shaper.glyphs(text) :
    # g is (gid, pos) pos is (x, y). so g is (gid, (x, y))
    # get the glyph name
    n = ctypes.create_string_buffer(64)
    ft.FT_Get_Glyph_Name(face._FT_Face, g[0], n, ctypes.sizeof(n))
    # make a glyph object with info from shaper
    glyph = Glyph(g[0], g[1], n.value)
    # render glyph to bitmap
    ft.FT_Load_Glyph(face._FT_Face, g[0], freestyle)
    # store bitmap in glyph object
    glyph.addBitmap(face.glyph, args.depth)
    glyphs.append(glyph)
    if args.thicken : glyph.thicken(args.thicken)

# iterate over every unordered pair of glyphs in the string
for i in range(len(glyphs) - 1) :
    for j in range(i + 1, len(glyphs)) :
        # if two glyphs collide, report it
        if i != j and glyphs[i].clashTest(glyphs[j], args.thicken) :
            print(f"Glyphs {glyphs[i].name} and {glyphs[j].name} collide")

#!/usr/bin/python

import palaso.contrib.freetype as ft
import palaso.font.hbng as hbng
import sys

ftface = ft.Face('./Padauk.ttf')
ftface.set_char_size(12 * 64)
face = hbng.FTFace(ftface)
font = hbng.FTFont(ftface)
buff = hbng.Buffer(sys.argv[1])
buff.shape(font)
x, y = (0., 0.)
for g in buff.glyphs :
    print "{0:d}({1:f}, {2:f}) ".format(g.gid, x + g.offset[0] / 64., y + g.offset[1] / 64.)
    x += g.advance[0] / 64.
    y += g.advance[1] / 64.

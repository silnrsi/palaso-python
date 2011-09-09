#!/usr/bin/python

import freetype as ft
import palaso.font.hbng as hbng
import palaso.font.graphite as gr
import sys, codecs
from fontTools.ttLib import TTFont
from gc import collect
from palaso.font.icufont import TTXLEFont
import icu
from optparse import OptionParser

parser = OptionParser(usage='%prog [options] fontfile textfile')
parser.add_option('-s','--script',help='specifies script to ICU')
parser.add_option('-c','--compare',help='Compare against icu/graphite [icu]')
(opts, args) = parser.parse_args()

ftface = ft.Face(sys.argv[1])
ftface.set_char_size(12 * 64)
hbface = hbng.FTFace(ftface)
hbfont = hbng.FTFont(ftface)
grface = gr.Face(sys.argv[1])
grfont = gr.Font(grface, 12 * 96 / 72.)
tt = TTFont(sys.argv[1])
icufont = TTXLEFont(sys.argv[1], ttx=tt)
iculayout = icu.LayoutEngine(icufont, icu.ScriptCodes.index(opts.script) if opts.script else 0, 0)

lf = codecs.open(sys.argv[2], "r", "utf_8")
count = 0
for line in lf.readlines() :
    count += 1
    text = line.strip()
    b = hbng.Buffer(text)
    b.shape(hbfont, shapers=["ot"])
    hbres = [x.gid for x in b.glyphs]
    s = gr.Segment(grfont, grface, 0, text, 0)
    grres = [x.gid for x in s.slots]
    iculayout.layoutChars(text, 0)
    icures = filter(lambda x: x != 65535, list(iculayout.getGlyphs()))
    if opts.compare == 'graphite' :
        if hbres != grres :
            hbnres = [tt.getGlyphName(x) for x in hbres]
            grnres = [tt.getGlyphName(x) for x in grres]
            print "Failed at line %d: %s %r, %r" % (count, text.encode('utf_8'), hbnres, grnres)
    else :
        if hbres != icures :
            hbnres = [tt.getGlyphName(x) for x in hbres]
            icunres = [tt.getGlyphName(x) for x in icures]
            print "Failed at line %d: %s %r, %r" % (count, text.encode('utf_8'), hbnres, icunres)


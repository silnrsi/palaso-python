from icu import LEFontInstance
from fontTools.ttLib import TTFont

# emulate PortableFontInstance.cpp in python
class TTXLEFont(LEFontInstance) :
    def __init__(self, fname, size = 12, ttx = None) :
        super(TTXLEFont, self).__init__()
        self.ttx = ttx or TTFont(fname)
        self.size = size
        self.upem = self.ttx['head'].unitsPerEm
        self.cmap = self.ttx['cmap'].getcmap(3, 1).cmap
        self.tables = {}

    def getFontTable(self, table) :
        if table in self.tables :
            res = self.tables[table]
        else :
            res = self.ttx.getTableData(table)
            self.tables[table] = res
        return res

    def getAscent(self) :
        self.ttx['hhea'].ascent * self.size * 1. / self.upem

    def getDescent(self) :
        self.ttx['hhea'].descent * self.size * 1. / self.upem

    def getLeading(self) :
        self.ttx['hhea'].lineGap * self.size * 1. / self.upem

    def getUnitsPerEM(self) :
        return self.upem

    def mapCharToGlyph(self, code) :
        res = 0
        try :
            id = self.cmap[code]
            res = self.ttx.getGlyphID(id)
        except :
            pass
        return res

    def getGlyphAdvance(self, glyph) :
        if glyph >= self.ttx['maxp'].numGlyphs :
            return (0., 0.)
        name = self.ttx.getGlyphName(glyph)
        x = self.ttx['hmtx'][name][0] * self.size * 1. / self.upem
        y = 0.
        try :
            y = self.ttx['vmtx'][name][0] * self.size * 1. / self.upem
        except :
            pass
        return (x, y)

    def getGlyphPoint(self, glyph, point) :
        return (0., 0.)

    def getXPixelsPerEm(self) :
        return self.size

    def getYPixelsPerEm(self) :
        return self.size

    def getScaleFactorX(self) :
        return 1.

    def getScaleFactorY(self) :
        return 1.



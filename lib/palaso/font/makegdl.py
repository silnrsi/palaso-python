from . import psnames


class PointClass(object):

    def __init__(self, name):
        self.name = name
        self.glyphs = []
        self.dias = []
        self.isBase = False

    def addBaseGlyph(self, g):
        self.glyphs.append(g)
        if g.isBase:
            self.isBase = True

    def addDiaGlyph(self, g):
        self.dias.append(g)

    def classGlyphs(self, isDia=False):
        if isDia:
            return self.dias
        else:
            return self.glyphs

    def isNotInClass(self, g, isDia=False):
        if isDia:
            return g not in self.dias
        else:
            return g not in self.dias and g not in self.glyphs


class Font(object):
    def __init__(self):
        self.glyphs = []
        self.psnames = {}
        self.canons = {}
        self.gdls = {}
        self.anchors = {}

    def emunits(self):
        return 0

    def addGlyph(self, g):
        self.glyphs.append(g)
        n = g.GDLName()
        if n in self.gdls:
            count = 1
            index = -2
            n = n + "_1"
            while n in self.gdls:
                count = count + 1
                n = n[0:index] + "_" + str(count)
                if count == 10:
                    index = -3
                if count == 100:
                    index = -4
            g.name.GDLName = n
        self.gdls[n] = g
        for n in g.parseNames():
            self.psnames[n.psname] = g
            self.canons[n.canonical()] = (n, g)
        return g

    def createClasses(self):
        self.classes = {}
        for k, v in self.canons.items():
            if v[0].ext:
                h = v[0].head()
                o = self.canons.get(h.canonical(), None)
                if o:
                    if v[0].ext not in self.classes:
                        self.classes[v[0].ext] = {}
                    self.classes[v[0].ext][o[1].GDLName()] = v[1].GDLName()

    def pointClasses(self):
        self.points = {}
        for g in self.glyphs:
            for a in g.anchors.keys():
                b = a
                if a.startswith("_"):
                    b = a[1:]
                if a not in self.points:
                    self.points[b] = PointClass(b)
                if a == b:
                    self.points[b].addBaseGlyph(g)
                else:
                    self.points[b].addDiaGlyph(g)

    def outGDL(self, fh):
        munits = self.emunits()
        fh.write('table(glyph) {MUnits = ' + str(munits) + '};\n')
        for g in self.glyphs:
            fh.write(g.GDLName() + ' = postscript("' + g.PSName + '")')
            if len(g.anchors):
                fh.write('{')
                outs = []
                for a in g.anchors.keys():
                    v = g.anchors[a]
                    if a.startswith("_"):
                        name = a[1:] + "M"
                    else:
                        name = a + "S"
                    outs.append(
                        f"{name}=point({str(int(v[0]))}m,"
                        f" {str(int(v[1]))}m)")
                fh.write(", ".join(outs) + "}")
            fh.write(";\n")
        fh.write("\n")
        fh.write("\n/* Point Classes */\n")
        for p in self.points.values():
            n = p.name + "Dia"
            self.outclass(fh, "c" + n, p.classGlyphs(True))
            self.outclass(fh, "cTakes" + n, p.classGlyphs(False))
            self.outclass(fh, 'cn' + n,
                          filter(lambda x: p.isNotInClass(x, True),
                                 self.glyphs))
            self.outclass(fh, 'cnTakes' + n,
                          filter(lambda x: p.isNotInClass(x, False),
                                 self.glyphs))
        fh.write("\n/* Classes */\n")
        for p in self.classes.keys():
            ins = []
            outs = []
            for k, v in self.classes[p].items():
                ins.append(k)
                outs.append(v)
            self.outclass(fh, 'cno_' + p, ins)
            self.outclass(fh, 'c' + p, outs)

    def outclass(self, fh, name, glyphs):
        fh.write(name + " = (")
        count = 1
        sep = ""
        for g in glyphs:
            if isinstance(g, str):
                fh.write(sep + g)
            else:
                fh.write(sep + g.GDLName())
            if count % 8 == 0:
                sep = ',\n         '
            else:
                sep = ', '
            count += 1
        fh.write(');\n\n')


class Glyph(object):
    def __init__(self, name):
        self.PSName = name
        self.isBase = False
        self.name = next(self.parseNames())
        self.anchors = {}

    def addAnchor(self, name, x, y, t=None):
        self.anchors[name] = (x, y)
        if not name.startswith("_") and t != 'basemark':
            self.isBase = True

    def parseNames(self):
        for name in self.PSName.split("/"):
            res = psnames.Name(name)
            yield res

    def GDLName(self):
        return self.name.GDL()

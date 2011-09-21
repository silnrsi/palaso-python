
import palaso.font.graphite as gr
import palaso.font.hbng as hb
import freetype as ft

class Font(object) :
    def __init__(self, fname, size, rtl) :
        self.fname = fname
        self.size = size
        self.rtl = rtl

class GrFont(Font) :
    def __init__(self, fname, size, rtl, feats = {}, script = 0, lang = 0) :
        super(GrFont, self).__init__(fname, size, rtl)
        self.grface = gr.Face(fname)
        self.feats = self.grface.get_featureval(lang)
        self.script = script
        for f,v in feats.items() :
            fref = self.grface.get_featureref(f)
            self.feats.set(fref, v)
        self.font = gr.Font(self.grface, size * 96 / 72.)

    def measure(self, text, after) :
        """Returns a list of x positions for before/after the indexth character and
        a list of breakweights"""
        seg = gr.Segment(self.font, self.grface, self.script, text, self.rtl, feats = self.feats)
        num = seg.num_cinfo()
        pos = []
        bw = []
        for i in range(num) :
            c = seg.cinfo(i)
            bw.append(c.breakweight)
            if after :
                s = c.slots[c.after]
            else :
                s = c.slots[c.before]
            pos.append(s.origin[0])
        return (pos, bw)

    def width(self, text) :
        seg = gr.Segment(self.font, self.grface, self.script, text, self.rtl, feats = self.feats)
        return seg.advance[0]

    def glyphs(self, text) :
        seg = gr.Segment(self.font, self.grface, self.script, text, self.rtl, feats = self.feats)
        res = []
        for s in seg.slots :
            res.append((s.gid, s.origin))
        return res

class HbFont(Font) :
    def __init__(self, fname, size, rtl, feats = {}, script = 0, lang = 0) :
        super(HbFont, self).__init__(fname, size, rtl)
        self.ftface = ft.Face(fname)
        self.ftface.set_char_size(size * 64)
        self.face = hb.FTFace(self.ftface)
        self.font = hb.FTFont(self.ftface)
        self.shapers = ["ot"]
        self.script = script
        self.lang = lang

    def glyphs(self, text) :
        buf = hb.Buffer(text, script = self.script, lang = self.lang)
        buf.shape(self.font)
        res = []
        x = 0
        y = 0
        for g in buf.glyphs :
            res.append((g.gid, (x + g.offset[0], y + g.offset[1])))
            x += g.advance[0]
            y += g.advance[1]
        return res

        
class StringCutter(object) :
    def __init__(self, tfont, wfont, rfont, befores, afters, width, refspace = None) :
        self.befores = befores
        self.afters = afters
        self.tfont = tfont
        self.wfont = wfont
        self.rfont = rfont
        self.width = width * 96 / 72.
        self.refspace = refspace * 96 / 72.
        if rfont :
            if not self.refspace :
                self.refspace = rfont.width(' ')
            else :
                self.refspace = refspace * 96 / 72.

    def cut(self, ref, before, word, after) :
        """Takes stripped strings and returns character cut positions for before and after"""
        width = self.width
        if self.rfont :
            width -= self.rfont.width(ref) + self.refspace
        # split befores on self.befores to get indices
        # split afters on self.afters to get indices
        # get widths for all those indices
        # choose before and after indices
        # if no choice
            # get word break indices for before and after up to first split
            # get widths and choose
            # if still no choice
                # get cluster break indices for before and after up to first word
                # get widths and choose
        


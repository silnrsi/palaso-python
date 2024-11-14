
import palaso.font.graphite as gr
import uharfbuzz as uhb
import palaso.font.hbng as hb
#import palaso.font.icule as icule
import freetype as ft
#from icu import LayoutEngine as le
#from icu import ScriptCode, LanguageCode

class Font(object) :
    def __init__(self, fname, size, rtl) :
        self.fname = fname
        self.size = size
        self.rtl = rtl

class GrFont(Font) :
    def __init__(self, fname, size = 0, rtl = 0, feats = {}, script = 0, lang = 0) :
        super(GrFont, self).__init__(fname, size, rtl)
        self.grface = gr.Face(fname)
        self.lang = lang
        self.feats = self._featureval(feats, lang)
        self.script = script
        if size > 0 :
            size = size * 96 / 72.
        else :
            size = float(self.grface.get_upem())
        self.font = gr.Font(self.grface, size)

    def _featureval(self, feats, lang):
        res = self.grface.get_featureval(lang)
        for f,v in feats.items() :
            if v is None:
                continue
            try:
                fref = self.grface.get_featureref(f.encode("utf-8"))
                if fref is not None:
                    res.set(fref, v)
            except ValueError:
                pass
        return res
        
    def measure(self, text, after = False) :
        """Returns a list of x positions for before/after the indexth character and
        a list of breakweights"""
        seg = gr.Segment(self.font, self.grface, self.script, str(text), self.rtl, feats = self.feats)
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

    def glyphs(self, text, includewidth = False, feats = None, rtl = None, lang = None, **kw) :
        if feats is None:
            feats = self.feats
        else:
            feats = self._featureval(feats, lang if lang is not None else self.lang)
        if rtl is None:
            rtl = self.rtl
        seg = gr.Segment(self.font, self.grface, self.script, str(text), rtl, feats = feats)
        res = []
        for s in seg.slots :
            res.append((s.gid, s.origin, seg.cinfo(s.original).unicode))
        if includewidth : res.append((None, seg.advance))
        return res


class UHarfBuzzFont(Font) :
    def __init__(self, fname, size, rtl, feats=None, script=0, lang=0):
        super(UHarfBuzzFont, self).__init__(fname, size, rtl)
        blob = uhb.Blob.from_file_path(fname)
        face = uhb.Face(blob)
        self.font = uhb.Font(face)
        self.script = script
        self.lang = 'c' if lang == 0 else lang
        self.rtl = rtl
        self.features = {} if feats is None else feats

    def glyphs(self, text, includewidth = False, lang=None, feats=None, script=None, **kw):
        if not len(text):
            return [(None, (0, 0))]

        buf = uhb.Buffer()
        buf.add_str(text)

        # Not needed since we set the script and direction separately
        # buf.guess_segment_properties()

        # Set script
        buf.set_script_from_ot_tag(self.script if script is None else script)

        # Set language
        # Sets the language with a modifier like -x-hbot-<digits>
        # buf.set_language_from_ot_tag(self.lang if lang is None else lang)
        # Simpler and gives better results
        buf.language = self.lang if lang is None else lang

        # Set direction
        buf.direction = 'rtl' if self.rtl else 'ltr'

        # Set features
        features = self.features if feats is None else feats

        uhb.shape(self.font, buf, features)
        res = []
        clus = []
        x = 0
        y = 0
        infos = buf.glyph_infos
        positions = buf.glyph_positions
        for info, position in zip(infos, positions):
            gid = info.codepoint
            res.append((gid, (x + position.x_offset, y + position.y_offset), 0))
            clus.append(info.cluster)
            x += position.x_advance
            y += position.y_advance
        if includewidth:
            res.append((None, (x, y)))
        return res


class HbFont(Font) :
    def __init__(self, fname, size, rtl, feats = None, script = 0, lang = 0) :
        super(HbFont, self).__init__(fname, size, rtl)
        self.ftface = ft.Face(fname)
        if size <= 0 :
            size = self.ftface.units_per_EM
        else :
            size *= 64
        self.ftface.set_char_size(size)
        self.face = hb.FTFace(self.ftface)
        self.font = hb.FTFont(self.ftface)
        self.shapers = None
        self.script = script
        self.lang = lang
        self.rtl = rtl
        self.feats = {} if feats is None else feats

    def glyphs(self, text, includewidth = False, lang=None, feats=None, script=None, **kw) :
        if kw.get('dir', 0) == 0 and self.rtl:
            kw['dir'] = 1
        buf = hb.Buffer(text, script = (self.script if script is None else script), lang = (self.lang if lang is None else lang), **kw)
        buf.shape(self.font, shapers = self.shapers, feats = self.feats if feats is None else feats)
        if kw.get('trace', False):
            print("\n".join(buf.trace))
        res = []
        clus = []
        x = 0
        y = 0
        for g in buf.glyphs :
            res.append((g.gid, (x + g.offset[0], y + g.offset[1]), 0))
            clus.append(g.cluster)
            x += g.advance[0]
            y += g.advance[1]
        if self.rtl :
            temp = []
            last = 0
            currclus = -1
            for i in range(len(clus)) :
                if clus[i] != currclus :
                    if currclus >= 0 :
                        temp.extend(reversed(res[last:i]))
                        last = i
                    currclus = clus[i]
            temp.extend(reversed(res[last:]))
            res = list(reversed(temp))
        if includewidth : res.append((None, (x, y)))
        return res

class HbOTFont(HbFont) :
    def __init__(self, fname, size, rtl, feats = {}, script = 0, lang = 0) :
        super(HbOTFont, self).__init__(fname, size, rtl, feats, script, lang)
        self.shapers = ["ot"]

class IcuFont(Font) :
    def __init__(self, fname, size, rtl, feats={}, script=0, lang=0) :
        super(IcuFont, self).__init__(fname, size, rtl)
        self.font = icule.TTXLEFont(fname)
        self.layout = le.layoutEngineFactory(self.font, getattr(ScriptCode, script, ScriptCode.zyyy) if script else ScriptCode.zyyy, getattr(LanguageCode, lang, LanguageCode.nul) if lang else LanguageCode.nul)

    def glyphs(self, text, includewidth = False) :
        if not len(text) : return []
        self.layout.layoutChars(str(text))
        gids = self.layout.getGlyphs()
        poss = self.layout.getGlyphPositions()
        res = []
        for i in range(len(gids)) :
            res.append((gids[i], poss[i], 0))
        return res

_shapers = {
    'gr' : GrFont,
    'uhb' : UHarfBuzzFont,
    'ot' : HbOTFont,
    'hb' : HbFont
#    'icu' : IcuFont
}
 
def make_shaper(engine, fname, size, rtl, feats = {}, script = 0, lang = 0) :
    res = _shapers[engine](fname, size, rtl, feats, script, lang)
    return res


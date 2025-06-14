
from ctypes import *
import ctypes.util

hbng = None
hbnglib = ctypes.util.find_library("harfbuzz")
if not hbnglib :
    try :
        hbng = CDLL("libharfbuzz.so")
    except OSError :
        hbng = None

if not hbnglib and not hbng :
    raise RuntimeError("harfbuzz library not found")
if not hbng :
    hbng = CDLL(hbnglib)
if not hbng :
    raise RuntimeError("Failed to load harfbuzz: {0}".format(hbnglib))

def fn(name, res, *params) :
    f = getattr(hbng, name)
    f.restype = res
    f.argtypes = params

# hb-buffer.h
class GlyphInfo(Structure) :
    _fields_ = [('codepoint', c_uint32),
                ('mask', c_uint32),
                ('cluster', c_uint32),
                ('var1', c_uint32),
                ('var2', c_uint32)]

class GlyphPosition(Structure) :
    _fields_ = [('x_advance', c_int32),
                ('y_advance', c_int32),
                ('x_offset', c_int32),
                ('y_offset', c_int32),
                ('var', c_uint32)]

fndestroy = CFUNCTYPE(None, c_void_p)
fnmessage = CFUNCTYPE(c_bool, c_void_p, c_void_p, c_char_p, c_void_p)
fn('hb_buffer_create', c_void_p)
fn('hb_buffer_get_empty', c_void_p)
fn('hb_buffer_reference', c_void_p, c_void_p)
fn('hb_buffer_destroy', None, c_void_p)
fn('hb_buffer_set_user_data', c_int, c_void_p, c_void_p, c_void_p, fndestroy, c_int)
fn('hb_buffer_get_user_data', c_void_p, c_void_p, c_void_p)
fn('hb_buffer_set_content_type', None, c_void_p, c_int)
fn('hb_buffer_get_content_type', c_int, c_void_p)
fn('hb_buffer_set_unicode_funcs', c_void_p, c_void_p)
fn('hb_buffer_get_unicode_funcs', c_void_p, c_void_p)
fn('hb_buffer_set_direction', None, c_void_p, c_int)
fn('hb_buffer_set_script', None, c_void_p, c_uint32)
fn('hb_buffer_get_script', c_uint32, c_void_p)
fn('hb_buffer_set_language', None, c_void_p, c_void_p)
fn('hb_buffer_get_language', c_void_p, c_void_p)
fn('hb_buffer_reset', None, c_void_p)
fn('hb_buffer_allocation_successful', c_int, c_void_p)
fn('hb_buffer_reverse', None, c_void_p)
fn('hb_buffer_reverse_clusters', None, c_void_p)
fn('hb_buffer_add', None, c_void_p, c_uint32, c_uint32, c_uint)
fn('hb_buffer_add_utf8', None, c_void_p, c_char_p, c_int, c_uint, c_int)
fn('hb_buffer_add_utf16', None, c_void_p, POINTER(c_uint16), c_int, c_uint, c_int)
fn('hb_buffer_add_utf32', None, c_void_p, POINTER(c_uint32), c_int, c_uint, c_int)
fn('hb_buffer_set_length', c_int, c_void_p, c_uint)
fn('hb_buffer_get_length', c_int, c_void_p)
fn('hb_buffer_get_glyph_infos', POINTER(GlyphInfo), c_void_p, POINTER(c_uint))
fn('hb_buffer_get_glyph_positions', POINTER(GlyphPosition), c_void_p, POINTER(c_uint))
fn('hb_buffer_has_positions', c_bool, c_void_p)
fn('hb_buffer_guess_segment_properties', None, c_void_p)
fn('hb_buffer_serialize', c_int, c_void_p, c_uint, c_uint, c_char_p, c_uint, POINTER(c_uint), c_void_p, c_uint, c_uint)
fn('hb_buffer_set_message_func', None, c_void_p, fnmessage, c_void_p, fndestroy)

# hb-common.h
fn('hb_tag_from_string', c_uint32, c_char_p)
fn('hb_direction_from_string', c_int, c_char_p)
fn('hb_direction_to_string', c_char_p, c_int)
fn('hb_language_from_string', c_void_p, c_char_p, c_int)
fn('hb_language_to_string', c_char_p, c_void_p)
fn('hb_language_get_default', c_void_p)
fn('hb_script_from_iso15924_tag', c_int, c_uint32)
fn('hb_script_from_string', c_int, c_char_p)
fn('hb_script_to_iso15924_tag', c_uint32, c_int)
fn('hb_script_get_horizontal_direction', c_int, c_int)
try :
    fn('hb_version_string', c_char_p)
    version_string = hbng.hb_version_string().decode("utf_8")
except :
    version_string = ""    

# hb-ot-tag.h
fn('hb_ot_tag_to_script', c_int, c_uint32)
fn('hb_ot_tag_from_language', c_int32, c_void_p)
fn('hb_ot_tag_to_language', c_void_p, c_uint32)

# hb-font.h
fnhbreftable = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_void_p)
fn('hb_face_create', c_void_p, c_void_p, c_uint)
fn('hb_face_create_for_tables', c_void_p, fnhbreftable, c_void_p, fndestroy)
fn('hb_face_get_empty', c_void_p)
fn('hb_face_reference', c_void_p, c_void_p)
fn('hb_face_destroy', None, c_void_p)
fn('hb_face_set_user_data', c_int, c_void_p, c_void_p, c_void_p, fndestroy, c_int)
fn('hb_face_get_user_data', c_void_p, c_void_p, c_void_p)
fn('hb_face_make_immutable', None, c_void_p)
fn('hb_face_is_immutable', c_int, c_void_p)
fn('hb_face_reference_table', c_void_p, c_void_p, c_uint32)
fn('hb_face_reference_blob', c_void_p, c_void_p)
fn('hb_face_set_index', None, c_void_p, c_uint)
fn('hb_face_get_index', c_uint, c_void_p)
fn('hb_face_set_upem', None, c_void_p, c_uint)
fn('hb_face_get_upem', c_uint, c_void_p)

fn('hb_font_funcs_create', c_void_p)
fn('hb_font_funcs_get_empty', c_void_p)
fn('hb_font_funcs_reference', c_void_p, c_void_p)
fn('hb_font_funcs_destroy', None, c_void_p)
fn('hb_font_funcs_set_user_data', c_int, c_void_p, c_void_p, c_void_p, fndestroy, c_int)
fn('hb_font_funcs_get_user_data', c_void_p, c_void_p, c_void_p)
fn('hb_font_funcs_make_immutable', None, c_void_p)
fn('hb_font_funcs_is_immutable', c_int, c_void_p)

class GlyphExtents(Structure) :
    _fields_ = [('x_bearing', c_int32),
                ('y_bearing', c_int32),
                ('width', c_int32),
                ('height', c_int32)]

fnfontgetglyph = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_uint32, POINTER(c_uint32), c_void_p)
fnfontgetglyphadv = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_void_p)
fnfontgetglyphhadv = fnfontgetglyphadv
fnfontgetglyphvadv = fnfontgetglyphadv
fnfontgetglyphorg = CFUNCTYPE(c_void_p, c_void_p, c_uint32, POINTER(c_int32), POINTER(c_int32), c_void_p)
fnfontgetglyphhorg = fnfontgetglyphorg
fnfontgetglyphvorg = fnfontgetglyphorg
fnfontgetglyphkern = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_uint32, c_void_p)
fnfontgetglyphhkern = fnfontgetglyphkern
fnfontgetglyphvkern = fnfontgetglyphkern
fnfontgetglyphextents = CFUNCTYPE(c_void_p, c_void_p, c_uint32, POINTER(GlyphExtents), c_void_p)
fnfontgetglyphcpoint = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_uint, POINTER(c_int32), POINTER(c_int32), c_void_p)

fn('hb_font_funcs_set_glyph_func', None, c_void_p, fnfontgetglyph, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_h_advance_func', None, c_void_p, fnfontgetglyphhadv, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_v_advance_func', None, c_void_p, fnfontgetglyphvadv, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_h_origin_func', None, c_void_p, fnfontgetglyphhorg, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_v_origin_func', None, c_void_p, fnfontgetglyphvorg, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_h_kerning_func', None, c_void_p, fnfontgetglyphhkern, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_v_kerning_func', None, c_void_p, fnfontgetglyphvkern, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_extents_func', None, c_void_p, fnfontgetglyphextents, c_void_p, fndestroy)
fn('hb_font_funcs_set_glyph_contour_point_func', None, c_void_p, fnfontgetglyphcpoint, c_void_p, fndestroy)

fn('hb_font_get_glyph', c_int, c_void_p, c_uint32, c_uint32, POINTER(c_uint32))
fn('hb_font_get_glyph_h_advance', c_int32, c_void_p, c_uint32)
fn('hb_font_get_glyph_v_advance', c_int32, c_void_p, c_uint32)
fn('hb_font_get_glyph_h_origin', c_int, c_void_p, c_uint32, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_get_glyph_v_origin', c_int, c_void_p, c_uint32, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_get_glyph_h_kerning', c_int32, c_void_p, c_uint32, c_uint32)
fn('hb_font_get_glyph_v_kerning', c_int32, c_void_p, c_uint32, c_uint32)
fn('hb_font_get_glyph_extents', c_int, c_void_p, c_uint32, POINTER(GlyphExtents))
fn('hb_font_get_glyph_contour_point', c_int, c_void_p, c_uint32, c_uint, POINTER(c_int32), POINTER(c_int32))

fn('hb_font_get_glyph_advance_for_direction', None, c_void_p, c_uint32, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_get_glyph_origin_for_direction', None, c_void_p, c_uint32, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_add_glyph_origin_for_direction', None, c_void_p, c_uint32, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_subtract_glyph_origin_for_direction', None, c_void_p, c_uint32, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_get_glyph_kerning_for_direction', None, c_void_p, c_uint32, c_uint32, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_get_glyph_extents_for_origin', c_int, c_void_p, c_uint32, c_int, POINTER(GlyphExtents))
fn('hb_font_get_glyph_contour_point_for_origin', c_int, c_void_p, c_uint32, c_uint, c_int, POINTER(c_int32), POINTER(c_int32))
fn('hb_font_glyph_to_string', None, c_void_p, c_uint32, c_char_p, c_uint32)

fn('hb_font_create', c_void_p, c_void_p)
fn('hb_font_create_sub_font', c_void_p, c_void_p)
fn('hb_font_get_empty', c_void_p)
fn('hb_font_reference', c_void_p, c_void_p)
fn('hb_font_destroy', None, c_void_p)
fn('hb_font_set_user_data', c_int, c_void_p, c_void_p, c_void_p, fndestroy, c_int)
fn('hb_font_get_user_data', c_void_p, c_void_p, c_void_p)
fn('hb_font_make_immutable', None, c_void_p)
fn('hb_font_is_immutable', c_int, c_void_p)
fn('hb_font_get_parent', c_void_p, c_void_p)
fn('hb_font_get_face', c_void_p, c_void_p)
fn('hb_font_set_funcs', None, c_void_p, c_void_p, c_void_p, fndestroy)
fn('hb_font_set_funcs_data', None, c_void_p, c_void_p, fndestroy)
fn('hb_font_set_scale', None, c_void_p, c_int, c_int)
fn('hb_font_get_scale', None, c_void_p, POINTER(c_int), POINTER(c_int))
fn('hb_font_set_ppem', None, c_void_p, c_uint, c_uint)
fn('hb_font_get_ppem', None, c_void_p, POINTER(c_int), POINTER(c_int))

# hb-shape.h

class Feature(Structure) :
    _fields_ = [('tag', c_uint32),
                ('value', c_uint32),
                ('start', c_uint),
                ('end', c_uint)]
fn('hb_shape', None, c_void_p, c_void_p, POINTER(Feature), c_uint)
fn('hb_shape_full', c_int, c_void_p, c_void_p, POINTER(Feature), c_uint, POINTER(c_char_p))

# hb-unicode.h

fn('hb_unicode_funcs_get_default', c_void_p)
fn('hb_unicode_funcs_create', c_void_p, c_void_p)
fn('hb_unicode_funcs_get_empty', c_void_p)
fn('hb_unicode_funcs_reference', c_void_p, c_void_p)
fn('hb_unicode_funcs_destroy', None, c_void_p)
fn('hb_unicode_funcs_set_user_data', c_int, c_void_p, c_void_p, c_void_p, fndestroy, c_int)
fn('hb_unicode_funcs_get_user_data', c_void_p, c_void_p, c_void_p)
fn('hb_unicode_funcs_make_immutable', None, c_void_p)
fn('hb_unicode_funcs_is_immutable', c_int, c_void_p)
fn('hb_unicode_funcs_get_parent', c_void_p, c_void_p)

fnunicombiningclass = CFUNCTYPE(c_uint, c_void_p, c_uint32, c_void_p)
fnunieawidth = CFUNCTYPE(c_uint, c_void_p, c_uint32, c_void_p)
fnunigc = CFUNCTYPE(c_int, c_void_p, c_uint32, c_void_p)
fnunimirror = CFUNCTYPE(c_uint32, c_void_p, c_uint32, c_void_p)
fnuniscript = CFUNCTYPE(c_int, c_void_p, c_uint32, c_void_p)
fnunicompose = CFUNCTYPE(c_int, c_void_p, c_uint32, c_uint32, POINTER(c_uint32), c_void_p)
fnunidecompose = CFUNCTYPE(c_int, c_void_p, c_uint32, POINTER(c_uint32), POINTER(c_uint32), c_void_p)
fn('hb_unicode_funcs_set_combining_class_func', None, c_void_p, fnunicombiningclass, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_eastasian_width_func', None, c_void_p, fnunieawidth, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_general_category_func', None, c_void_p, fnunigc, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_mirroring_func', None, c_void_p, fnunimirror, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_script_func', None, c_void_p, fnuniscript, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_compose_func', None, c_void_p, fnunicompose, c_void_p, fndestroy)
fn('hb_unicode_funcs_set_decompose_func', None, c_void_p, fnunidecompose, c_void_p, fndestroy)

fn('hb_unicode_combining_class', c_uint, c_void_p, c_uint32)
fn('hb_unicode_eastasian_width', c_uint, c_void_p, c_uint32)
fn('hb_unicode_general_category', c_int, c_void_p, c_uint32)
fn('hb_unicode_mirroring', c_uint32, c_void_p, c_uint32)
fn('hb_unicode_script', c_int, c_void_p, c_uint32)
fn('hb_unicode_compose', c_int, c_void_p, c_uint32, c_uint32, POINTER(c_uint32))
fn('hb_unicode_decompose', c_int, c_void_p, c_uint32, POINTER(c_uint32), POINTER(c_uint32))

# hb-ft.h
fn('hb_ft_face_create', c_void_p, c_void_p, fndestroy)
fn('hb_ft_face_create_cached', c_void_p, c_void_p)
fn('hb_ft_font_create', c_void_p, c_void_p, fndestroy)
fn('hb_ft_font_set_funcs', None, c_void_p)
fn('hb_ft_font_get_face', c_void_p, c_void_p)

# hb-glib.h
#fn('hb_glib_script_to_script', c_int, c_int)
#fn('hb_glib_script_from_script', c_int, c_int)
#fn('hb_glib_get_unicode_funcs', c_void_p)

def trace(hbbuf, hbfont, msg, userdat):
    self = cast(userdat, py_object).value
    return self.printbuf(hbbuf, hbfont, prefix=msg.decode("utf-8") + ": ")
    return True

gbuf = ctypes.create_string_buffer(128)
def serialize(hbbuf, hbfont):
    length = c_uint(0)
    num_glyphs = hbng.hb_buffer_get_length(hbbuf)
    info = hbng.hb_buffer_get_glyph_infos (hbbuf, byref(length))
    if hbng.hb_buffer_has_positions(hbbuf):
        pos = hbng.hb_buffer_get_glyph_positions (hbbuf, byref(length))
    else:
        pos = None
    content = hbng.hb_buffer_get_content_type(hbbuf)
    if content < 1 or content > 2:
        return []
    # print(hbbuf, info, content, num_glyphs, length)
    res = []
    for i in range(num_glyphs):
        entry = {'type': content}
        #g = ctypes.create_string_buffer(128)
        if content == 2:
            hbng.hb_font_glyph_to_string(hbfont, info[i].codepoint, gbuf, 128)
            entry["g"] = gbuf.value.decode("utf-8")
            entry["cl"] = info[i].cluster
            entry["v1"] = "%08X" % info[i].var1
            entry["v2"] = "%08X" % info[i].var2
            if pos is not None:
                entry["dx"] = pos[i].x_offset
                entry["dy"] = pos[i].y_offset
                entry["ax"] = pos[i].x_advance
                entry["ay"] = pos[i].y_advance
                entry["v"] = "%08X" % pos[i].var
        elif content == 1:
            entry["u"] = "U+%04X" % info[i].codepoint
            entry["cl"] = info[i].cluster
            entry["v1"] = "%08X" % info[i].var1
            entry["v2"] = "%08X" % info[i].var2
        res.append(entry)
    return res

def glyph_text(glyph):
    if glyph['type'] == 1:  # Unicode
        return "[{u}={cl}|{v1},{v2}]".format(**glyph)
    elif "dx" in glyph:
        return "[{g}={cl}+{ax},{ay}@{dx},{dy}|{v1},{v2},{v}]".format(**glyph)
    else:
        return "[{g}={cl}|{v1},{v2}]".format(**glyph)

def serialize_text(hbbuf, hbfont):
    glyphs = serialize(hbbuf, hbfont)
    res = ", ".join(glyph_text(g) for g in glyphs)
    return (res, len(glyphs))

class Trace(list):
    bufstr = create_string_buffer(32768)

    def __init__(self, callback):
        self.callback = callback

    def printbuf(self, hbbuf, hbfont, prefix=""):
        #hbbuf = cast(hbbuf, c_void_p)
        #hbfont = cast(hbfont, c_void_p)
        res, numg = serialize_text(hbbuf, hbfont)
        #res = str(hbng.hb_buffer_get_length(hbbuf))
        #res = hbng.hb_buffer_serialize(hbbuf, 0, hblen, self.bufstr, 32767, None, hbfont, mode,  0)
        out = prefix + res
        self.append(out)
        return numg

    def trace(self, hbbuf, hbfont, msg, userdat):
        return self.printbuf(hbbuf, hbfont, prefix=msg.decode("utf-8") + ": ")

class Glyph(object) :
    def __init__(self, ginfo, position) :
        self.gid = ginfo.codepoint
        self.cluster = ginfo.cluster
        self.offset = (position.x_offset, position.y_offset)
        self.advance = (position.x_advance, position.y_advance)

    def __repr__(self) :
        return "{0}={1}@{2[0]},{2[1]}+{3[0]},{3[1]}".format(self.gid, self.cluster, self.offset, self.advance)

class Buffer(object) :
    def __init__(self, text, script=None, lang=None, unicodefuncs=None, rtl=False, **kwds) :
        """Takes a text string, script (string, optional), lang (string, optional)
        """
        self.text = text.encode('utf_8')
        length = len(self.text)
        self.buffer = hbng.hb_buffer_create(len(text))
        hbng.hb_buffer_add_utf8(self.buffer, self.text, length, 0, length)
        # if script is not None and script != 0:
        #     tag = hbng.hb_tag_from_string(script.encode("utf_8"))
        #     script = hbng.hb_ot_tag_to_script(tag) or -1
        #     hbng.hb_buffer_set_script(self.buffer, script)
        if lang is not None and lang != 0:
            tlang = hbng.hb_language_from_string(lang.encode("utf_8"), len(lang))
            hbng.hb_buffer_set_language(self.buffer, tlang)
        # if rtl:
        #     hbng.hb_buffer_set_direction(self.buffer, 5)
        # else:
        #     hbng.hb_buffer_guess_segment_properties(self.buffer)
        hbng.hb_buffer_guess_segment_properties(self.buffer)
        (major, minor, macro) = [int(s) for s in version_string.split('.')] if version_string else (0, 0, 0)
        if unicodefuncs :
            hbng.hb_buffer_set_unicode_funcs(unicodefuncs)
#        elif (major < 1 and minor <= 9 and macro <= 20) :
#            unicodefuncs = hbng.hb_glib_get_unicode_funcs()
#            hbng.hb_buffer_set_unicode_funcs(unicodefuncs)
        if kwds.get('trace', False):
            self.trace = Trace(fnmessage(trace))
            hbng.hb_buffer_set_message_func(self.buffer, self.trace.callback, c_void_p.from_buffer(py_object(self.trace)), fndestroy(0))

    def __del__(self) :
        hbng.hb_buffer_destroy(self.buffer)

# feats = {'feat' : (20, 0, 10), 'fea1' : 1}
    def shape(self, font, feats = None, options = None, shapers = None, **kwds) :
        """Takes a Font, feats is a dict for tagstr: either value int or tuple (value, start, finish)
            shapers and options are optional lists of strings.
        """
        if feats :
            lenfeats = len(feats)
            feattype = Feature * lenfeats
            featinit = []
            for k, v in feats.items() :
                if not isinstance(v, tuple) :
                    v = (v, 0, -1) # len(self.text))
                featinit.append(Feature(hbng.hb_tag_from_string(k.encode("utf-8")), v[0], v[1], v[2]))
            featinfo = feattype(*featinit)
        else :
            featinfo = None
            lenfeats = 0
        if shapers :
            shaperstype = c_char_p * (len(shapers) + 1)
            parms = [x.encode('utf_8') for x in shapers] + [None]
            shapersinfo = shaperstype(*parms)
        else :
            shapersinfo = None
        # printbuf(self.buffer, font.font)
        hbng.hb_shape_full(font.font, self.buffer, featinfo, lenfeats, shapersinfo)

    @property
    def glyphs(self) :
        length = c_uint(0)
        infos = hbng.hb_buffer_get_glyph_infos(self.buffer, byref(length))
        poses = hbng.hb_buffer_get_glyph_positions(self.buffer, byref(length))
        res = []
        for i in range(length.value) :
            res.append(Glyph(infos[i], poses[i]))
        return res

class FTFace(object) :
    def __init__(self, ftface) :
        self.ftface = ftface
        self.face = hbng.hb_ft_face_create(ftface._FT_Face, fndestroy(0))

    def __del__(self) :
        hbng.hb_face_destroy(self.face)

class FTFont(object) :
    def __init__(self, ftface) :
        self.ftface = ftface
        self.font = hbng.hb_ft_font_create(ftface._FT_Face, fndestroy(0))

    def __del__(self) :
        hbng.hb_font_destroy(self.font)

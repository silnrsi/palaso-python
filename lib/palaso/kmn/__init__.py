import re

__ALL__=["coverage"]

_modifiers = {
    'LShift'    : 0x01,
    'Caps'      : 0x02,
    'LCtrl'     : 0x04,
    'LAlt'      : 0x08,
    'RShift'    : 0x10,
    'NCaps'     : 0x20,
    'RCtrl'     : 0x40,
    'RAlt'      : 0x80,
    'AltGr'     : 0x80,
    'Shift'     : 0x11,
    'Ctrl'      : 0x44,
    'Control'   : 0x44,
    'Alt'       : 0x88
}

_modkeys = sorted(_modifiers.keys(), key=lambda x: _modifiers[x])
_modkeys.reverse()

_rawkeys = {
    'K_SPACE'   : 0x20,
    'K_QUOTE'   : 0x27,
    'K_0'       : 0x30,
    'K_1'       : 0x31,
    'K_2'       : 0x32,
    'K_3'       : 0x33,
    'K_4'       : 0x34,
    'K_5'       : 0x35,
    'K_6'       : 0x36,
    'K_7'       : 0x37,
    'K_8'       : 0x38,
    'K_9'       : 0x39,
    'K_A'       : 0x41,
    'K_B'       : 0x42,
    'K_C'       : 0x43,
    'K_D'       : 0x44,
    'K_E'       : 0x45,
    'K_F'       : 0x46,
    'K_G'       : 0x47,
    'K_H'       : 0x48,
    'K_I'       : 0x49,
    'K_J'       : 0x4A,
    'K_K'       : 0x4B,
    'K_L'       : 0x4C,
    'K_M'       : 0x4D,
    'K_N'       : 0x4E,
    'K_O'       : 0x4F,
    'K_P'       : 0x50,
    'K_Q'       : 0x51,
    'K_R'       : 0x52,
    'K_S'       : 0x53,
    'K_T'       : 0x54,
    'K_U'       : 0x55,
    'K_V'       : 0x56,
    'K_W'       : 0x57,
    'K_X'       : 0x58,
    'K_Y'       : 0x59,
    'K_Z'       : 0x5A,
    'K_BKQUOTE' : 0x60,
    'K_COMMA'   : 0x2C,
    'K_HYPHEN'  : 0x2D,
    'K_PERIOD'  : 0x2E,
    'K_SLASH'   : 0x2F,
    'K_COLON'   : 0x3A,
    'K_EQUAL'   : 0x3D,
    'K_LBRKT'   : 0x5B,
    'K_BKSLASH' : 0x5C,
    'K_RBRKT'   : 0x5D,
    'K_BKSP'    : 0xFF08,
    'K_TAB'     : 0xFF09,
    'K_ENTER'   : 0xFF0D,
    'K_PAUSE'   : 0xFF13,
    'K_SCROLL'  : 0xFF14,
    'K_ESC'     : 0xFF1B,
    'K_HOME'    : 0xFF50,
    'K_LEFT'    : 0xFF51,
    'K_UP'      : 0xFF52,
    'K_RIGHT'   : 0xFF53,
    'K_DOWN'    : 0xFF54,
    'K_PGUP'    : 0xFF55,
    'K_PGDN'    : 0xFF56,
    'K_END'     : 0xFF57,
    'K_INS'     : 0xFF63,
    'K_NUMLOCK' : 0xFF7F,
    'K_NPSTAR'  : 0xFFAA,
    'K_NPPLUS'  : 0xFFAB,
    'K_NPMINUS' : 0xFFAD,
    'K_NPDOT'   : 0xFFAE,
    'K_NPSLASH' : 0xFFAF,
    'K_NP0'     : 0xFFB0,
    'K_NP1'     : 0xFFB1,
    'K_NP2'     : 0xFFB2,
    'K_NP3'     : 0xFFB3,
    'K_NP4'     : 0xFFB4,
    'K_NP5'     : 0xFFB5,
    'K_NP6'     : 0xFFB6,
    'K_NP7'     : 0xFFB7,
    'K_NP8'     : 0xFFB8,
    'K_NP9'     : 0xFFB9,
    'K_F1'      : 0xFFBE,
    'K_F2'      : 0xFFBF,
    'K_F3'      : 0xFFC0,
    'K_F4'      : 0xFFC1,
    'K_F5'      : 0xFFC2,
    'K_F6'      : 0xFFC3,
    'K_F7'      : 0xFFC4,
    'K_F8'      : 0xFFC5,
    'K_F9'      : 0xFFC6,
    'K_F10'     : 0xFFC7,
    'K_F11'     : 0xFFC8,
    'K_F12'     : 0xFFC9,
    'K_F13'     : 0xFFCA,
    'K_F14'     : 0xFFCB,
    'K_F15'     : 0xFFCC,
    'K_F16'     : 0xFFCD,
    'K_F17'     : 0xFFCE,
    'K_F18'     : 0xFFCF,
    'K_F19'     : 0xFFD0,
    'K_F20'     : 0xFFD1,
    'K_F21'     : 0xFFD2,
    'K_F22'     : 0xFFD3,
    'K_F23'     : 0xFFD4,
    'K_F24'     : 0xFFD5,
    'K_SHIFT'   : 0xFFE1,
    'K_CONTROL' : 0xFFE3,
    'K_CAPS'    : 0xFFE5,
    'K_ALT'     : 0xFFE9,
    'K_oE2'     : 0x3C
}

_keynames = dict((v, k) for k, v in _rawkeys.items())

def keysyms_items(syms) :
    return [keysym_item(s) for s in re.split(ur'(\\.|\[[^\]]*\]|.)', syms)[1::2]]

def keysym_item(sym) :
    if re.match(r'^\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        mod = 0
        for w in words[:-1] :
            mod = mod | _modifiers[w]
        key = _rawkeys[words[-1]]
        return 0x1000000 | (mod << 16) | key
    elif sym[0] == '\\' :
        char = sym[1]
    else :
        char = sym[0]

    return ord(char)

def items_to_keys(items) :
    return "".join(item_to_key(o) for o in items)

def item_to_key(item) :
    if item > 0x1000000 :
        mods = (item & 0xFF0000) >> 16
        key = item & 0xFFFF
        modres = []
        for m in _modkeys :
            if (mods & _modifiers[m]) != 0 :
                modres.append(m)
                mods = mods & ~_modifiers[m]
            if mods == 0 :
                break
        if len(modres) > 0 :
            modstr = " ".join(modres) + " "
        elif key < 0x100 :
            return escape(unichr(key))
        else :
            modstr = ""

        if _keynames.has_key(key) :
            keystr = _keynames[key]
        else :
            keystr = "XK_" + unichr(key & 0xFF)
        return "[" + modstr + keystr + "]"
    else :
        return escape(unichr(item))
        
def escape(keyname) :
    if "\\[".find(keyname) >= 0 :
        return "\\" + keyname
    else :
        return keyname
        

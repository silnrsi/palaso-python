import re, itertools

# tuple in dict:
# 0 - kmn item code
# 1 - type 1 scan code
_modifiers = {
    'LShift'    : (0x01, 0x2A),
    'Caps'      : (0x02, 0x3A),
    'LCtrl'     : (0x04, 0x1D),
    'LAlt'      : (0x08, 0x38),
    'RShift'    : (0x10, 0x36),
    'NCaps'     : (0x20, 0x00),
    'RCtrl'     : (0x40, 0xE01D),
    'RAlt'      : (0x80, 0xE038),
    'AltGr'     : (0x80, 0x00),
    'Shift'     : (0x11, 0x2A),
    'Ctrl'      : (0x44, 0x1D),
    'Control'   : (0x44, 0x1D),
    'Alt'       : (0x88, 0x38)
}

_modkeys = sorted(_modifiers.keys(), key=lambda x: _modifiers[x][0])
_modkeys.reverse()

_rawkeys = {
    'K_SPACE'   : (0x20, 0x39),
    'K_QUOTE'   : (0x27, 0x28),
    'K_0'       : (0x30, 0x0B),
    'K_1'       : (0x31, 0x02),
    'K_2'       : (0x32, 0x03),
    'K_3'       : (0x33, 0x04),
    'K_4'       : (0x34, 0x05),
    'K_5'       : (0x35, 0x06),
    'K_6'       : (0x36, 0x07),
    'K_7'       : (0x37, 0x08),
    'K_8'       : (0x38, 0x09),
    'K_9'       : (0x39, 0x0A),
    'K_A'       : (0x41, 0x1E),
    'K_B'       : (0x42, 0x30),
    'K_C'       : (0x43, 0x2E),
    'K_D'       : (0x44, 0x20),
    'K_E'       : (0x45, 0x12),
    'K_F'       : (0x46, 0x21),
    'K_G'       : (0x47, 0x22),
    'K_H'       : (0x48, 0x23),
    'K_I'       : (0x49, 0x17),
    'K_J'       : (0x4A, 0x24),
    'K_K'       : (0x4B, 0x25),
    'K_L'       : (0x4C, 0x26),
    'K_M'       : (0x4D, 0x32),
    'K_N'       : (0x4E, 0x31),
    'K_O'       : (0x4F, 0x18),
    'K_P'       : (0x50, 0x19),
    'K_Q'       : (0x51, 0x10),
    'K_R'       : (0x52, 0x13),
    'K_S'       : (0x53, 0x1F),
    'K_T'       : (0x54, 0x14),
    'K_U'       : (0x55, 0x16),
    'K_V'       : (0x56, 0x2F),
    'K_W'       : (0x57, 0x11),
    'K_X'       : (0x58, 0x2D),
    'K_Y'       : (0x59, 0x15),
    'K_Z'       : (0x5A, 0x2C),
    'K_BKQUOTE' : (0x60, 0x01),
    'K_COMMA'   : (0x2C, 0x33),
    'K_HYPHEN'  : (0x2D, 0x0C),
    'K_PERIOD'  : (0x2E, 0x34),
    'K_SLASH'   : (0x2F, 0x35),
    'K_COLON'   : (0x3A, 0x27),
    'K_EQUAL'   : (0x3D, 0x0D),
    'K_LBRKT'   : (0x5B, 0x1A),
    'K_BKSLASH' : (0x5C, 0x2B),
    'K_RBRKT'   : (0x5D, 0x1B),
    'K_BKSP'    : (0xFF08, 0x0E),
    'K_TAB'     : (0xFF09, 0x0F),
    'K_ENTER'   : (0xFF0D, 0x1C),
    'K_PAUSE'   : (0xFF13, 0x59),
    'K_SCROLL'  : (0xFF14, 0x46),
    'K_ESC'     : (0xFF1B, 0x01),
    'K_HOME'    : (0xFF50, 0x47),
    'K_LEFT'    : (0xFF51, 0x4B),
    'K_UP'      : (0xFF52, 0x48),
    'K_RIGHT'   : (0xFF53, 0x4D),
    'K_DOWN'    : (0xFF54, 0x50),
    'K_PGUP'    : (0xFF55, 0x49),
    'K_PGDN'    : (0xFF56, 0x51),
    'K_END'     : (0xFF57, 0x4F),
    'K_INS'     : (0xFF63, 0x52),
    'K_NUMLOCK' : (0xFF7F, 0x45),
    'K_NPSTAR'  : (0xFFAA, 0x37),
    'K_NPPLUS'  : (0xFFAB, 0x4E),
    'K_NPMINUS' : (0xFFAD, 0x4A),
    'K_NPDOT'   : (0xFFAE, 0x53),
    'K_NPSLASH' : (0xFFAF, 0x35),
    'K_NP0'     : (0xFFB0, 0x52),
    'K_NP1'     : (0xFFB1, 0x4F),
    'K_NP2'     : (0xFFB2, 0x50),
    'K_NP3'     : (0xFFB3, 0x51),
    'K_NP4'     : (0xFFB4, 0x4B),
    'K_NP5'     : (0xFFB5, 0x4C),
    'K_NP6'     : (0xFFB6, 0x4D),
    'K_NP7'     : (0xFFB7, 0x47),
    'K_NP8'     : (0xFFB8, 0x48),
    'K_NP9'     : (0xFFB9, 0x49),
    'K_F1'      : (0xFFBE, 0x3B),
    'K_F2'      : (0xFFBF, 0x3C),
    'K_F3'      : (0xFFC0, 0x3D),
    'K_F4'      : (0xFFC1, 0x3E),
    'K_F5'      : (0xFFC2, 0x3F),
    'K_F6'      : (0xFFC3, 0x40),
    'K_F7'      : (0xFFC4, 0x41),
    'K_F8'      : (0xFFC5, 0x42),
    'K_F9'      : (0xFFC6, 0x43),
    'K_F10'     : (0xFFC7, 0x44),
    'K_F11'     : (0xFFC8, 0x57),
    'K_F12'     : (0xFFC9, 0x58),
    'K_F13'     : (0xFFCA, 0x00),
    'K_F14'     : (0xFFCB, 0x00),
    'K_F15'     : (0xFFCC, 0x00),
    'K_F16'     : (0xFFCD, 0x00),
    'K_F17'     : (0xFFCE, 0x00),
    'K_F18'     : (0xFFCF, 0x00),
    'K_F19'     : (0xFFD0, 0x00),
    'K_F20'     : (0xFFD1, 0x00),
    'K_F21'     : (0xFFD2, 0x00),
    'K_F22'     : (0xFFD3, 0x00),
    'K_F23'     : (0xFFD4, 0x00),
    'K_F24'     : (0xFFD5, 0x00),
    'K_SHIFT'   : (0xFFE1, 0x2A),
    'K_CONTROL' : (0xFFE3, 0x1D),
    'K_CAPS'    : (0xFFE5, 0x3A),
    'K_ALT'     : (0xFFE9, 0x38),
    'K_oE2'     : (0x3C, 0x00),
    'K_LWIN'    : (0x00, 0xE05B),
    'K_RWIN'    : (0x00, 0xE05C),
    'K_APP'     : (0x00, 0xE05D)
}

_keynames = dict((v[0], k) for k, v in _rawkeys.items())

_keysyms = {
    '~' : "Shift K_BKQUOTE",
    '`' : "K_BKQUOTE",
    '!' : "Shift K_1",
    '@' : "Shift K_2",
    '#' : "Shift K_3",
    '$' : "Shift K_4",
    '%' : "Shift K_5",
    '^' : "Shift K_6",
    '&' : "Shift K_7",
    '*' : "Shift K_8",
    '(' : "Shift K_9",
    ')' : "Shift K_0",
    '_' : "Shift K_HYPHEN",
    '-' : "K_HYPHEN",
    '+' : "Shift K_EQUAL",
    '=' : "K_EQUAL",
    "\t" : "K_TAB",
    '{' : "Shift K_LBRKT",
    '[' : "K_LBRKT",
    '}' : "Shift K_RBRKT",
    ']' : "K_RBRKT",
    "\n" : "K_ENTER",
    "'" : "K_QUOTE",
    '"' : "Shift K_QUOTE",
    '<' : "Shift K_COMMA",
    ',' : "K_COMMA",
    '>' : "Shift K_PERIOD",
    '.' : "K_PERIOD",
    '?' : "Shift K_SLASH",
    '/' : "K_SLASH",
    '|' : "Shift K_BKSLASH",
    '\\' : "K_BKSLASH"
}

def keysyms_items(syms) :
    return [keysym_item(s) for s in re.split(ur'(\\.|\[[^\]]*\]|.)', syms)[1::2]]

def keysym_item(sym) :
    if re.match(r'^\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        mod = 0
        for w in words[:-1] :
            mod = mod | _modifiers[w][0]
        key = _rawkeys[words[-1]][0]
        return 0x1000000 | (mod << 16) | key
    elif sym[0] == '\\' :
        char = sym[1]
    else :
        char = sym[0]

    return ord(char)

def items_to_keys(items) :
    r = ""
    for o in items: r += item_to_key(o)
    return r

def item_to_key(item) :
    if item > 0x1000000 :
        mods = (item & 0xFF0000) >> 16
        key = item & 0xFFFF
        modstr = ""
        for m in _modkeys :
            if mods == 0: break
            modifier = _modifiers[m]
            if (mods & modifier) != 0 :
                modstr += m + " "
                mods &= ~modifier
        if not modstr and key < 0x100:
            return escape(unichr(key))

        if _keynames.has_key(key) :
            keystr = _keynames[key]
        else :
            keystr = "XK_" + unichr(key & 0xFF)
        return "[" + modstr + keystr + "]"
    else :
        return escape(unichr(item))

def char_keysym(char) :
    if re.match(r'^\[[^\]]+\]$', char) :
        return char
    res = _keysyms.get(char)
    if not res :
        if char.isupper() :
            res = "Shift K_" + char
        elif char.islower() :
            res = "K_" + char.upper()
        else :
            res = "K_" + char
    return "[" + res + "]"
        
def chars_scancodes(syms) :
    return itertools.chain(*(keysym_scancodes(char_keysym(s)) for s in re.split(ur'(\\.|\[[^\]]*\]|.)', syms)[1::2]))

def keysym_scancodes(sym) :
    resdown = []
    resup = []
    if re.match(r'^\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        for w in words[:-1] :
            resdown.append(_modifiers[w][1])
            resup.append(_modifiers[w][1] | 0x80)
        key = _rawkeys[words[-1]][1]
        resdown.extend(filter(bool, [key >> 8, key & 0xFF]))
        resup.extend(filter(bool, [(key | 0x80) & 0xFF, key >> 8]))
    resup.reverse()
    return tuple(resdown + resup)
        
def escape(keyname) :
    return "\\" + keyname if "\\[".find(keyname) >= 0 else keyname
        
__all__=["keysyms_items","keysym_item",
         "items_to_keys","item_to_key",
         "keysym_scancodes", "chars_scancodes",
         "char_keysym",
         "escape",
         "coverage"]

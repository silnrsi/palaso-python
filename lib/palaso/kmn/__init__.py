import re, itertools

# tuple in dict:
# 0 - kmn item code
# 1 - type 1 scan code
# 2 - MSKLC Shift state
_modifiers = {
    'LShift'    : (0x01, 0x2A, 0x01),
    'Caps'      : (0x02, 0x3A, 0x00),
    'LCtrl'     : (0x04, 0x1D, 0x02),
    'LAlt'      : (0x08, 0x38, 0x04),
    'RShift'    : (0x10, 0x36, 0x01),
    'NCaps'     : (0x20, 0x00, 0x00),
    'RCtrl'     : (0x40, 0xE01D, 0x02),
    'RAlt'      : (0x80, 0xE038, 0x04),
    'AltGr'     : (0x80, 0x00, 0x04),
    'Shift'     : (0x11, 0x2A, 0x01),
    'Ctrl'      : (0x44, 0x1D, 0x02),
    'Control'   : (0x44, 0x1D, 0x02),
    'Alt'       : (0x88, 0x38, 0x04)
}

_modkeys = sorted(_modifiers.keys(), key=lambda x: _modifiers[x][0], reverse=True)

# 0 - KMN Item value
# 1 - Shifted KMN Item value
# 2 - MS Scan code
# 3 - MSKLC Keyname
# 4 - MSKLC Ext Keyname
_rawkeys = {
    'K_SPACE'   : (0x20, 0x20, 0x39, "Space", ""),
    'K_QUOTE'   : (0x27, 0x22, 0x28, "Apostrophe", ""),
    'K_0'       : (0x30, 0x29, 0x0B, "", ""),
    'K_1'       : (0x31, 0x21, 0x02, "", ""),
    'K_2'       : (0x32, 0x40, 0x03, "", ""),
    'K_3'       : (0x33, 0x23, 0x04, "", ""),
    'K_4'       : (0x34, 0x24, 0x05, "", ""),
    'K_5'       : (0x35, 0x25, 0x06, "", ""),
    'K_6'       : (0x36, 0x5E, 0x07, "", ""),
    'K_7'       : (0x37, 0x26, 0x08, "", ""),
    'K_8'       : (0x38, 0x2A, 0x09, "", ""),
    'K_9'       : (0x39, 0x28, 0x0A, "", ""),
    'K_A'       : (0x61, 0x41, 0x1E, "", ""),
    'K_B'       : (0x62, 0x42, 0x30, "", ""),
    'K_C'       : (0x63, 0x43, 0x2E, "", ""),
    'K_D'       : (0x64, 0x44, 0x20, "", ""),
    'K_E'       : (0x65, 0x45, 0x12, "", ""),
    'K_F'       : (0x66, 0x46, 0x21, "", ""),
    'K_G'       : (0x67, 0x47, 0x22, "", ""),
    'K_H'       : (0x68, 0x48, 0x23, "", ""),
    'K_I'       : (0x69, 0x49, 0x17, "", ""),
    'K_J'       : (0x6A, 0x4A, 0x24, "", ""),
    'K_K'       : (0x6B, 0x4B, 0x25, "", ""),
    'K_L'       : (0x6C, 0x4C, 0x26, "", ""),
    'K_M'       : (0x6D, 0x4D, 0x32, "", ""),
    'K_N'       : (0x6E, 0x4E, 0x31, "", ""),
    'K_O'       : (0x6F, 0x4F, 0x18, "", ""),
    'K_P'       : (0x70, 0x50, 0x19, "", ""),
    'K_Q'       : (0x71, 0x51, 0x10, "", ""),
    'K_R'       : (0x72, 0x52, 0x13, "", ""),
    'K_S'       : (0x73, 0x53, 0x1F, "", ""),
    'K_T'       : (0x74, 0x54, 0x14, "", ""),
    'K_U'       : (0x75, 0x55, 0x16, "", ""),
    'K_V'       : (0x76, 0x56, 0x2F, "", ""),
    'K_W'       : (0x77, 0x57, 0x11, "", ""),
    'K_X'       : (0x78, 0x58, 0x2D, "", ""),
    'K_Y'       : (0x79, 0x59, 0x15, "", ""),
    'K_Z'       : (0x7A, 0x5A, 0x2C, "", ""),
    'K_BKQUOTE' : (0x60, 0x7E, 0x29, "Esc", ""),
    'K_COMMA'   : (0x2C, 0x3C, 0x33, "", ""),
    'K_HYPHEN'  : (0x2D, 0x5F, 0x0C, "", ""),
    'K_PERIOD'  : (0x2E, 0x3E, 0x34, "", ""),
    'K_SLASH'   : (0x2F, 0x3F, 0x35, "", "Num /"),
    'K_COLON'   : (0x3B, 0x3A, 0x27, "", ""),
    'K_EQUAL'   : (0x3D, 0x2B, 0x0D, "", ""),
    'K_LBRKT'   : (0x5B, 0x7B, 0x1A, "", ""),
    'K_BKSLASH' : (0x5C, 0x7C, 0x2B, "", ""),
    'K_RBRKT'   : (0x5D, 0x7D, 0x1B, "", ""),
    'K_BKSP'    : (0xFF08, 0xFF08, 0x0E, "Backspace", ""),
    'K_TAB'     : (0xFF09, 0xFF09, 0x0F, "Tab", ""),
    'K_ENTER'   : (0xFF0D, 0xFF0D, 0x1C, "Enter", "Num Enter"),
    'K_PAUSE'   : (0xFF13, 0xFF13, 0x59, "", ""),
    'K_SCROLL'  : (0xFF14, 0xFF14, 0x46, "Scroll Lock", "Break"),
    'K_ESC'     : (0xFF1B, 0xFF1B, 0x01, "", ""),
    'K_HOME'    : (0xFF50, 0xFF50, 0x47, "Num 7", "Home"),
    'K_LEFT'    : (0xFF51, 0xFF51, 0x4B, "Num 4", "Left"),
    'K_UP'      : (0xFF52, 0xFF52, 0x48, "Num 8", "Up"),
    'K_RIGHT'   : (0xFF53, 0xFF53, 0x4D, "Num 6", "Right"),
    'K_DOWN'    : (0xFF54, 0xFF54, 0x50, "Num 2", "Down"),
    'K_PGUP'    : (0xFF55, 0xFF55, 0x49, "Num 9", "Page Up"),
    'K_PGDN'    : (0xFF56, 0xFF56, 0x51, "Num 3", "Page Down"),
    'K_END'     : (0xFF57, 0xFF57, 0x4F, "Num 1", "End"),
    'K_INS'     : (0xFF63, 0xFF63, 0x52, "Num 0", "Insert"),
    'K_NUMLOCK' : (0xFF7F, 0xFF7F, 0x45, "Pause", "Num Lock"),
    'K_NPSTAR'  : (0xFFAA, 0xFFAA, 0x37, "Num *", "Prnt Scrn"),
    'K_NPPLUS'  : (0xFFAB, 0xFFAB, 0x4E, "Num +", ""),
    'K_NPMINUS' : (0xFFAD, 0xFFAD, 0x4A, "Num -", ""),
    'K_NPDOT'   : (0xFFAE, 0xFFAE, 0x53, "Num Del", "Delete"),
    'K_NPSLASH' : (0xFFAF, 0xFFAF, 0x35, "", "Num /"),
    'K_NP0'     : (0xFFB0, 0xFFB0, 0x52, "Num 0", "Insert"),
    'K_NP1'     : (0xFFB1, 0xFFB1, 0x4F, "Num 1", "End"),
    'K_NP2'     : (0xFFB2, 0xFFB2, 0x50, "Num 2", "Down"),
    'K_NP3'     : (0xFFB3, 0xFFB3, 0x51, "Num 3", "Page Down"),
    'K_NP4'     : (0xFFB4, 0xFFB4, 0x4B, "Num 4", "Left"),
    'K_NP5'     : (0xFFB5, 0xFFB5, 0x4C, "Num 5", ""),
    'K_NP6'     : (0xFFB6, 0xFFB6, 0x4D, "Num 6", "Right"),
    'K_NP7'     : (0xFFB7, 0xFFB7, 0x47, "Num 7", "Home"),
    'K_NP8'     : (0xFFB8, 0xFFB8, 0x48, "Num 8", "Up"),
    'K_NP9'     : (0xFFB9, 0xFFB9, 0x49, "Num 9", "Page Up"),
    'K_F1'      : (0xFFBE, 0xFFBE, 0x3B, "F1", ""),
    'K_F2'      : (0xFFBF, 0xFFBF, 0x3C, "F2", ""),
    'K_F3'      : (0xFFC0, 0xFFC0, 0x3D, "F3", ""),
    'K_F4'      : (0xFFC1, 0xFFC1, 0x3E, "F4", ""),
    'K_F5'      : (0xFFC2, 0xFFC2, 0x3F, "F5", ""),
    'K_F6'      : (0xFFC3, 0xFFC3, 0x40, "F6", ""),
    'K_F7'      : (0xFFC4, 0xFFC4, 0x41, "F7", ""),
    'K_F8'      : (0xFFC5, 0xFFC5, 0x42, "F8", ""),
    'K_F9'      : (0xFFC6, 0xFFC6, 0x43, "F9", ""),
    'K_F10'     : (0xFFC7, 0xFFC7, 0x44, "F10", ""),
    'K_F11'     : (0xFFC8, 0xFFC8, 0x57, "F11", ""),
    'K_F12'     : (0xFFC9, 0xFFC9, 0x58, "F12", ""),
    'K_F13'     : (0xFFCA, 0xFFCA, 0x7C, "F13", ""),
    'K_F14'     : (0xFFCB, 0xFFCB, 0x7D, "F14", ""),
    'K_F15'     : (0xFFCC, 0xFFCC, 0x7E, "F15", ""),
    'K_F16'     : (0xFFCD, 0xFFCD, 0x7F, "F16", ""),
    'K_F17'     : (0xFFCE, 0xFFCE, 0x80, "F17", ""),
    'K_F18'     : (0xFFCF, 0xFFCF, 0x81, "F18", ""),
    'K_F19'     : (0xFFD0, 0xFFD0, 0x82, "F19", ""),
    'K_F20'     : (0xFFD1, 0xFFD1, 0x83, "F20", ""),
    'K_F21'     : (0xFFD2, 0xFFD2, 0x84, "F21", ""),
    'K_F22'     : (0xFFD3, 0xFFD3, 0x85, "F22", ""),
    'K_F23'     : (0xFFD4, 0xFFD4, 0x86, "F23", ""),
    'K_F24'     : (0xFFD5, 0xFFD5, 0x87, "F24", ""),
    'K_SHIFT'   : (0xFFE1, 0xFFE1, 0x2A, "Shift", ""),
    'K_CONTROL' : (0xFFE3, 0xFFE3, 0x1D, "Ctrl", "Right Ctrl"),
    'K_CAPS'    : (0xFFE5, 0xFFE5, 0x3A, "Caps Lock", ""),
    'K_ALT'     : (0xFFE9, 0xFFE9, 0x38, "Alt", "Right Alt"),
    'K_oE2'     : (0x3C, 0x3C, 0x00, "", ""),
    'K_LWIN'    : (0x00, 0x00, 0xE05B, "", "Left Windows"),
    'K_RWIN'    : (0x00, 0x00, 0xE05C, "", "Right Windows"),
    'K_APP'     : (0x00, 0x00, 0xE05D, "", "Application")
}

_msrawmap = {
    'K_HYPHEN' : 'OEM_MINUS',
    'K_EQUAL' : 'OEM_PLUS',
    'K_COMMA' : 'OEM_COMMA',
    'K_PERIOD' : 'OEM_PERIOD',
    'K_COLON' : 'OEM_1',
    'K_SLASH' : 'OEM_2',
    'K_BKQUOTE' : 'OEM_3',
    'K_LBRKT' : 'OEM_4',
    'K_BKSLASH' : 'OEM_5',
    'K_RBRKT' : 'OEM_6',
    'K_QUOTE' : 'OEM_7',
}

_keynames = dict((v[0], k) for k, v in _rawkeys.items())

_keysyms = {
    ' ' : "K_SPACE",
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
    '\\' : "K_BKSLASH",
    ';' : "K_COLON",
    ':' : "Shift K_COLON"
}

_symkeys = dict((v,k) for k,v in _keysyms.items())

def keysyms_items(syms) :
    return [keysym_item(s) for s in re.split(ur'(\\.|\[[^\]]*\]|.)', syms)[1::2]]

def keysym_item(sym) :
    if re.match(r'^\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        mod = 0
        for w in words[:-1] :
            mod = mod | _modifiers[w][0]
        key = _rawkeys[words[-1]][1 if mod & _modifiers['Shift'][0] != 0 else 0]
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
            modifier = _modifiers[m][0]
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

def item_to_char(item) :
    sym = item_to_key(item)
    if len(sym) > 2 and sym[0] == '[' and sym[-1] == ']' :
        words = re.split(r'\s+', sym[1:-1].strip())
        if len(words) == 2 and words[0].lower() == 'shift' :
            res = _symkeys.get("Shift " + words[-1])
            if res : return res
            res = words[-1].replace('K_', '')
            if len(res) == 1 : return res
        elif len(words) == 1 :
            res = _symkeys.get(words[0])
            if res : return res
            res = words[-1].replace('K_', '')
            if len(res) == 1 : return res.lower()
        elif len(words) == 2 and words[0].lower() == 'ctrl' :
            res = words[-1].replace('K_', '')
            if len(res) == 1 : return unichr(ord(res) - 64)
    elif len(sym) == 2 :
        return sym[1:]
    else :
        return sym

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
        key = _rawkeys[words[-1]][2]
        resdown.extend(filter(bool, [key >> 8, key & 0xFF]))
        resup.extend(filter(bool, [(key | 0x80) & 0xFF, key >> 8]))
    resup.reverse()
    return tuple(resdown + resup)

def keysym_klcinfo(sym) :
    """ returns a tupe (scancode, virtual key name, 
        modifier number, keyname, extended keyname) for a given
        key symbol"""
    mod = 0
    vkey = ""
    sc = 0
    kn = ""
    ekn = ""
    if re.match(r'\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        for w in words[:-1] :
            mod = mod | _modifiers[w][2]
        vkey = words[-1]
        item, cap, sc, kn, ekn = _rawkeys[words[-1]]
        if _msrawmap.has_key(vkey) :
            vkey = _msrawmap[vkey]
        else :
            vkey = vkey.replace("K_", "")
    return (sc, vkey, mod, kn, ekn)

def escape(keyname) :
    return "\\" + keyname if "\\[".find(keyname) >= 0 else keyname
        
__all__=["keysyms_items","keysym_item",
         "items_to_keys","item_to_key", "item_to_char"
         "keysym_scancodes", "chars_scancodes",
         "keysym_klcinfo",
         "char_keysym",
         "escape",
         "coverage"]

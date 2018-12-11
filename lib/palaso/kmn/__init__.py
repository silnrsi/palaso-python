import re, itertools
import os, collections
try:
    from palaso.kmfl import kmfl
    kmflorobject = kmfl
except ImportError:
    kmflorobject = object

keyboard_template = os.path.join(os.path.dirname(__file__), 'keyboard.svg')

# tuple in dict:
# 0 - kmn item code
# 1 - type 1 scan code
# 2 - MSKLC Shift state
# 3 - MS Scan code
# 4 - MS VK_ code
_modifiers = {
    'LShift'    : (0x01, 0x2A, 0x01, 0x2A, 0xA0),
    'Caps'      : (0x02, 0x3A, 0x00, 0x3A, 0x14),
    'LCtrl'     : (0x04, 0x1D, 0x02, 0x1D, 0xA2),
    'LAlt'      : (0x08, 0x38, 0x04, 0x38, 0xA4),
    'RShift'    : (0x10, 0x36, 0x01, 0x36, 0x01A1),
    'NCaps'     : (0x20, 0x00, 0x00, 0x00, 0xFF),
    'RCtrl'     : (0x40, 0xE01D, 0x02, 0x85, 0x01A3),
    'RAlt'      : (0x80, 0xE038, 0x06, 0x99, 0x01A5),
    'AltGr'     : (0x80, 0x00, 0x06, 0x00, 0xFF),
    'Shift'     : (0x11, 0x2A, 0x01, 0x80, 0x10),
    'Ctrl'      : (0x44, 0x1D, 0x02, 0xD3, 0x0211),
    'Control'   : (0x44, 0x1D, 0x02, 0xD3, 0x0211),
    'Alt'       : (0x88, 0x38, 0x04, 0xD4, 0x0412)
}

_modkeys = sorted(_modifiers.keys(), key=lambda x: _modifiers[x][0], reverse=True)

# 0 - KMN Item value
# 1 - Shifted KMN Item value
# 2 - MS Scan code
# 3 - MS VK_ code
# 4 - MSKLC Keyname
# 5 - MSKLC Ext Keyname
_rawkeys = {
    'K_SPACE'   : (0x20, 0x20, 0x39, 0x20, "Space", ""),
    'K_QUOTE'   : (0x27, 0x22, 0x28, 0xDE, "Apostrophe", ""),
    'K_0'       : (0x30, 0x29, 0x0B, 0x30, "", ""),
    'K_1'       : (0x31, 0x21, 0x02, 0x31, "", ""),
    'K_2'       : (0x32, 0x40, 0x03, 0x32, "", ""),
    'K_3'       : (0x33, 0x23, 0x04, 0x33, "", ""),
    'K_4'       : (0x34, 0x24, 0x05, 0x34, "", ""),
    'K_5'       : (0x35, 0x25, 0x06, 0x35, "", ""),
    'K_6'       : (0x36, 0x5E, 0x07, 0x36, "", ""),
    'K_7'       : (0x37, 0x26, 0x08, 0x37, "", ""),
    'K_8'       : (0x38, 0x2A, 0x09, 0x38, "", ""),
    'K_9'       : (0x39, 0x28, 0x0A, 0x39, "", ""),
    'K_A'       : (0x61, 0x41, 0x1E, 0x41, "", ""),
    'K_B'       : (0x62, 0x42, 0x30, 0x42, "", ""),
    'K_C'       : (0x63, 0x43, 0x2E, 0x43, "", ""),
    'K_D'       : (0x64, 0x44, 0x20, 0x44, "", ""),
    'K_E'       : (0x65, 0x45, 0x12, 0x45, "", ""),
    'K_F'       : (0x66, 0x46, 0x21, 0x46, "", ""),
    'K_G'       : (0x67, 0x47, 0x22, 0x47, "", ""),
    'K_H'       : (0x68, 0x48, 0x23, 0x48, "", ""),
    'K_I'       : (0x69, 0x49, 0x17, 0x49, "", ""),
    'K_J'       : (0x6A, 0x4A, 0x24, 0x4A, "", ""),
    'K_K'       : (0x6B, 0x4B, 0x25, 0x4B, "", ""),
    'K_L'       : (0x6C, 0x4C, 0x26, 0x4C, "", ""),
    'K_M'       : (0x6D, 0x4D, 0x32, 0x4D, "", ""),
    'K_N'       : (0x6E, 0x4E, 0x31, 0x4E, "", ""),
    'K_O'       : (0x6F, 0x4F, 0x18, 0x4F, "", ""),
    'K_P'       : (0x70, 0x50, 0x19, 0x50, "", ""),
    'K_Q'       : (0x71, 0x51, 0x10, 0x51, "", ""),
    'K_R'       : (0x72, 0x52, 0x13, 0x52, "", ""),
    'K_S'       : (0x73, 0x53, 0x1F, 0x53, "", ""),
    'K_T'       : (0x74, 0x54, 0x14, 0x54, "", ""),
    'K_U'       : (0x75, 0x55, 0x16, 0x55, "", ""),
    'K_V'       : (0x76, 0x56, 0x2F, 0x56, "", ""),
    'K_W'       : (0x77, 0x57, 0x11, 0x57, "", ""),
    'K_X'       : (0x78, 0x58, 0x2D, 0x58, "", ""),
    'K_Y'       : (0x79, 0x59, 0x15, 0x59, "", ""),
    'K_Z'       : (0x7A, 0x5A, 0x2C, 0x5A, "", ""),
    'K_BKQUOTE' : (0x60, 0x7E, 0x29, 0xC0, "Esc", ""),
    'K_COMMA'   : (0x2C, 0x3C, 0x33, 0xBC, "", ""),
    'K_HYPHEN'  : (0x2D, 0x5F, 0x0C, 0xBD, "", ""),
    'K_PERIOD'  : (0x2E, 0x3E, 0x34, 0xBE, "", ""),
    'K_SLASH'   : (0x2F, 0x3F, 0x35, 0xBF, "", "Num /"),
    'K_COLON'   : (0x3B, 0x3A, 0x27, 0xBA, "", ""),
    'K_EQUAL'   : (0x3D, 0x2B, 0x0D, 0xBB, "", ""),
    'K_LBRKT'   : (0x5B, 0x7B, 0x1A, 0xDB, "", ""),
    'K_BKSLASH' : (0x5C, 0x7C, 0x2B, 0xDC, "", ""),
    'K_RBRKT'   : (0x5D, 0x7D, 0x1B, 0xDD, "", ""),
    'K_BKSP'    : (0xFF08, 0xFF08, 0x0E, 0x08, "Backspace", ""),
    'K_TAB'     : (0xFF09, 0xFF09, 0x0F, 0x09, "Tab", ""),
    'K_ENTER'   : (0xFF0D, 0xFF0D, 0x1C, 0x0D, "Enter", "Num Enter"),
    'K_PAUSE'   : (0xFF13, 0xFF13, 0x59, 0x0C, "", ""),
    'K_SCROLL'  : (0xFF14, 0xFF14, 0x46, 0x0291, "Scroll Lock", "Break"),
    'K_ESC'     : (0xFF1B, 0xFF1B, 0x01, 0x1B, "", ""),
    'K_HOME'    : (0xFF50, 0xFF50, 0x47, 0x0C24, "Num 7", "Home"),
    'K_LEFT'    : (0xFF51, 0xFF51, 0x4B, 0x0C25, "Num 4", "Left"),
    'K_UP'      : (0xFF52, 0xFF52, 0x48, 0x0C26, "Num 8", "Up"),
    'K_RIGHT'   : (0xFF53, 0xFF53, 0x4D, 0x0C27, "Num 6", "Right"),
    'K_DOWN'    : (0xFF54, 0xFF54, 0x50, 0x0C28, "Num 2", "Down"),
    'K_PGUP'    : (0xFF55, 0xFF55, 0x49, 0x0C21, "Num 9", "Page Up"),
    'K_PGDN'    : (0xFF56, 0xFF56, 0x51, 0x0C22, "Num 3", "Page Down"),
    'K_END'     : (0xFF57, 0xFF57, 0x4F, 0x0C23, "Num 1", "End"),
    'K_INS'     : (0xFF63, 0xFF63, 0x52, 0x0C2D, "Num 0", "Insert"),
    'K_NUMLOCK' : (0xFF7F, 0xFF7F, 0x45, 0x0390, "Pause", "Num Lock"),
    'K_NPSTAR'  : (0xFFAA, 0xFFAA, 0x37, 0x026A, "Num *", "Prnt Scrn"),
    'K_NPPLUS'  : (0xFFAB, 0xFFAB, 0x4E, 0x6B, "Num +", ""),
    'K_NPMINUS' : (0xFFAD, 0xFFAD, 0x4A, 0x6D, "Num -", ""),
    'K_NPDOT'   : (0xFFAE, 0xFFAE, 0x53, 0x6E, "Num Del", "Delete"),
    'K_NPSLASH' : (0xFFAF, 0xFFAF, 0x35, 0x6F, "", "Num /"),
    'K_NP0'     : (0xFFB0, 0xFFB0, 0x52, 0x0C2D, "Num 0", "Insert"),
    'K_NP1'     : (0xFFB1, 0xFFB1, 0x4F, 0x0C23, "Num 1", "End"),
    'K_NP2'     : (0xFFB2, 0xFFB2, 0x50, 0x0C28, "Num 2", "Down"),
    'K_NP3'     : (0xFFB3, 0xFFB3, 0x51, 0x0C22, "Num 3", "Page Down"),
    'K_NP4'     : (0xFFB4, 0xFFB4, 0x4B, 0x0C25, "Num 4", "Left"),
    'K_NP5'     : (0xFFB5, 0xFFB5, 0x4C, 0x0C0C, "Num 5", ""),
    'K_NP6'     : (0xFFB6, 0xFFB6, 0x4D, 0x0C27, "Num 6", "Right"),
    'K_NP7'     : (0xFFB7, 0xFFB7, 0x47, 0x0C24, "Num 7", "Home"),
    'K_NP8'     : (0xFFB8, 0xFFB8, 0x48, 0x0C26, "Num 8", "Up"),
    'K_NP9'     : (0xFFB9, 0xFFB9, 0x49, 0x0C21, "Num 9", "Page Up"),
    'K_F1'      : (0xFFBE, 0xFFBE, 0x3B, 0x70, "F1", ""),
    'K_F2'      : (0xFFBF, 0xFFBF, 0x3C, 0x71, "F2", ""),
    'K_F3'      : (0xFFC0, 0xFFC0, 0x3D, 0x72, "F3", ""),
    'K_F4'      : (0xFFC1, 0xFFC1, 0x3E, 0x73, "F4", ""),
    'K_F5'      : (0xFFC2, 0xFFC2, 0x3F, 0x74, "F5", ""),
    'K_F6'      : (0xFFC3, 0xFFC3, 0x40, 0x75, "F6", ""),
    'K_F7'      : (0xFFC4, 0xFFC4, 0x41, 0x76, "F7", ""),
    'K_F8'      : (0xFFC5, 0xFFC5, 0x42, 0x77, "F8", ""),
    'K_F9'      : (0xFFC6, 0xFFC6, 0x43, 0x78, "F9", ""),
    'K_F10'     : (0xFFC7, 0xFFC7, 0x44, 0x79, "F10", ""),
    'K_F11'     : (0xFFC8, 0xFFC8, 0x57, 0x7A, "F11", ""),
    'K_F12'     : (0xFFC9, 0xFFC9, 0x58, 0x7B, "F12", ""),
    'K_F13'     : (0xFFCA, 0xFFCA, 0x64, 0x7C, "F13", ""),
    'K_F14'     : (0xFFCB, 0xFFCB, 0x65, 0x7D, "F14", ""),
    'K_F15'     : (0xFFCC, 0xFFCC, 0x66, 0x7E, "F15", ""),
    'K_F16'     : (0xFFCD, 0xFFCD, 0x67, 0x7F, "F16", ""),
    'K_F17'     : (0xFFCE, 0xFFCE, 0x68, 0x80, "F17", ""),
    'K_F18'     : (0xFFCF, 0xFFCF, 0x69, 0x81, "F18", ""),
    'K_F19'     : (0xFFD0, 0xFFD0, 0x6A, 0x82, "F19", ""),
    'K_F20'     : (0xFFD1, 0xFFD1, 0x6B, 0x83, "F20", ""),
    'K_F21'     : (0xFFD2, 0xFFD2, 0x6C, 0x84, "F21", ""),
    'K_F22'     : (0xFFD3, 0xFFD3, 0x6D, 0x85, "F22", ""),
    'K_F23'     : (0xFFD4, 0xFFD4, 0x6E, 0x86, "F23", ""),
    'K_F24'     : (0xFFD5, 0xFFD5, 0x76, 0x87, "F24", ""),
    'K_LSHIFT'   : (0xFFE1, 0xFFE1, 0x2A, 0xA0, "Shift", ""),
    'K_LCONTROL' : (0xFFE3, 0xFFE3, 0x1D, 0xA2, "Ctrl", "Right Ctrl"),
    'K_CAPS'    : (0xFFE5, 0xFFE5, 0x3A, 0x14, "Caps Lock", ""),
    'K_ALT'     : (0xFFE9, 0xFFE9, 0x38, 0x12, "Alt", "Right Alt"),
    'K_oE2'     : (0x3C, 0x3C, 0x56, 0xE2, "", ""),
    'K_LWIN'    : (0x00, 0x00, 0xE05B, 0x5B, "", "Left Windows"),
    'K_RWIN'    : (0x00, 0x00, 0xE05C, 0x5C, "", "Right Windows"),
    'K_APP'     : (0x00, 0x00, 0xE05D, 0x5D, "", "Application"),
    'K_CLEAR'   : (0x00, 0x00, 0x4C, 0x0C0C, "Clear", ""),
    'K_DEL'     : (0x00, 0x00, 0x53, 0x0C2E, "Del", ""),
    'K_SNAPSHOT' : (0x00, 0x00, 0x54, 0x2C, "Prnt Srn", "")
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

_vkextras = {
    'K_LBUTTON' : (1),
    'K_RBUTTON' : (2),
    'K_CANCEL' : (3),
    'K_MBUTTON' : (4),
    'K_XBUTTON1' : (5),
    'K_XBUTTON2' : (6),
    'K_BACK' : (8),
#    'K_CLEAR' : (12),
    'K_RETURN' : (13),
    'K_SHIFT' : (16),
    'K_CTRL' : (17),
    'K_MENU' : (18),
#    'K_PAUSE' : (19),
    'K_CAPITAL' : (20),
    'K_KANA' : (0x15),
    'K_HANGUL' : (0x15),
    'K_HANGEUL' : (0x15),
    'K_JUNJA' : (0x17),
    'K_FINAL' : (0x18),
    'K_HANJA' : (0x19),
    'K_KANJI' : (0x19),
    'K_ESCAPE' : (0x1B),
    'K_CONVERT' : (0x1C),
    'K_NONCONVERT' : (0x1D),
    'K_ACCEPT' : (0x1E),
    'K_MODECHANGE' : (0x1F),
    'K_PRIOR' : (0x21),
    'K_NEXT' : (0x22),
    'K_SELECT' : (41),
    'K_PRINT' : (42),
    'K_EXECUTE' : (43),
    'K_INSERT' : (45),
    'K_DELETE' : (46),
    'K_HELP' : (47),
    'K_SLEEP' : (0x5F),
    'K_NUMPAD0' : (0x60),
    'K_NUMPAD1' : (0x61),
    'K_NUMPAD2' : (0x62),
    'K_NUMPAD3' : (0x63),
    'K_NUMPAD4' : (0x64),
    'K_NUMPAD5' : (0x65),
    'K_NUMPAD6' : (0x66),
    'K_NUMPAD7' : (0x67),
    'K_NUMPAD7' : (0x68),
    'K_NUMPAD9' : (0x69),
    'K_MULTIPLY' : (0x6A),
    'K_ADD' : (0x6B),
    'K_SEPARATOR' : (0x6C),
    'K_SUBTRACT' : (0x6D),
    'K_DECIMAL' : (0x6E),
    'K_DIVIDE' : (0x6F),
#    'K_NUMLOCK' : (0x90),
#    'K_SCROLL' : (0x91),
    'K_RSHIFT' : (0xA1),
    'K_RCONTROL' : (0xA3),
    'K_LMENU' : (0xA4),
    'K_RMENU' : (0xA5),
    'K_BROWSER_BACK' : (0xA6),
    'K_BROWSER_FORWARD' : (0xA7),
    'K_BROWSER_REFRESH' : (0xA8),
    'K_BROWSER_STOP' : (0xA9),
    'K_BROWSER_SEARCH' : (0xAA),
    'K_BROWSER_FAVORITES' : (0xAB),
    'K_BROWSER_HOME' : (0xAC),
    'K_VOLUME_MUTE' : (0xAD),
    'K_VOLUME_DOWN' : (0xAE),
    'K_VOLUME_UP' : (0xAF),
    'K_MEDIA_NEXT_TRACK' : (0xB0),
    'K_MEDIA_PREV_TRACK' : (0xB1),
    'K_MEDIA_STOP' : (0xB2),
    'K_MEDIA_PLAY_PAUSE' : (0xB3),
    'K_LAUNCH_MAIL' : (0xB4),
    'K_LAUNCH_MEDIA_SELECT' : (0xB5),
    'K_LAUNCH_APP1' : (0xB6),
    'K_LAUNCH_APP2' : (0xB7),
    'K_OEM_8' : (0xDF),
    'K_OEM_102' : (0xE2),
    'K_ICO_HELP' : (0xE3),
    'K_ICO_00' : (0xE4),
    'K_PROCESSKEY' : (0xE5),
    'K_PACKET' : (0xE7),
    'K_OEM_RESET' : (0xE9),
    'K_OEM_JUMP' : (0xEA),
    'K_OEM_PA1' : (0xEB),
    'K_OEM_PA2' : (0xEC),
    'K_OEM_PA3' : (0xED),
    'K_OEM_WSCTRL' : (0xEE),
    'K_OEM_CUSEL' : (0xEF),
    'K_OEM_ATTN' : (0xF0),
    'K_OEM_FINISH' : (0xF1),
    'K_OEM_COPY' : (0xF2),
    'K_OEM_AUTO' : (0xF3),
    'K_OEM_ENLW' : (0xF4),
    'K_OEM_BACKTAB' : (0xF5),
    'K_ATTN' : (0xF6),
    'K_CRSEL' : (0xF7),
    'K_EXSEL' : (0xF8),
    'K_EREOF' : (0xF9),
    'K_PLAY' : (0xFA),
    'K_ZOOM' : (0xFB),
    'K_NONAME' : (0xFC),
    'K_PA1' : (0xFD),
    'K_OEM_CLEAR' : (0xFE)
}

_keynames = dict((v[0], k) for k, v in _rawkeys.items())
_keyshiftnames = dict((v[1], k) for k, v in _rawkeys.items())

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
    ':' : "Shift K_COLON",
    "\010" : "K_BKSP"
}

_symkeys = dict((v,k) for k,v in _keysyms.items())
sc_vks = [0xFF] * 256
for k, v in _rawkeys.items() :
    if v[2] < 0x100 : sc_vks[v[2]] = v[3]
for k, v in _modifiers.items() : sc_vks[v[3]] = v[4]
sc_E0vks = (
    (0x1C, 0x010D), (0x1D, 0x01A3), (0x35, 0x016F), (0x37, 0x012C),
    (0x38, 0x01A5), (0x47, 0x0124), (0x48, 0x0126), (0x49, 0x0121),
    (0x4B, 0x0125), (0x4D, 0x0127), (0x4F, 0x0123), (0x50, 0x0128),
    (0x51, 0x0122), (0x52, 0x012D), (0x53, 0x012E), (0x5B, 0x015B),
    (0x5C, 0x015C), (0x5D, 0x015D), (0x46, 0x0103))
sc_E1vks = ((0x1D, 0x0013))

def keysyms_items(syms) :
    return [keysym_item(s) for s in re.split(r'(\\.|(?:\[[^\]]+\])|.)', syms)[1::2]]

def keysym_item(sym) :
    if re.match(r'^\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        mod = 0
        for w in words[:-1] :
            mod = mod | _modifiers[w][0]
        key = _rawkeys[words[-1]][1 if mod & _modifiers['Shift'][0] != 0 else 0]
        return 0x1000000 | (mod << 16) | key
    elif sym[0] == '\\' and len(sym) > 1 :
        char = sym[1]
    else :
        char = sym[0]

    return ord(char)

def items_to_keys(items) :
    r = ""
    for o in items: r += item_to_key(o)
    return r

def item_to_key(item) :
    if (item >> 24) > 1 :
        return ""
    elif item > 0x1000000 :
        mods = (item & 0xFF0000) >> 16
        key = item & 0xFFFF
        modstr = ""
        for m in _modkeys :
            if mods == 0: break
            modifier = _modifiers[m][0]
            if (mods & modifier) == modifier :
                modstr += m + " "
                mods &= ~modifier
                # lowercase uppercase keys (0x11 any shift)
                if modifier & 0x11 and _keyshiftnames.has_key(key) :
                    key = _rawkeys[_keyshiftnames[key]][0]
        if not modstr and key < 0x100:
            return char_keysym(unichr(key))

        if _keynames.has_key(key) :
            keystr = _keynames[key]
        else :
            keystr = "XK_" + unichr(key & 0xFF)
        return "[" + modstr + keystr + "]"
    else :
        return char_keysym(unichr(item))

def item_to_char(item) :
    if item < 0x110000 :
        return unichr(item)
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
    vkc = 0
    if re.match(r'\[[^\]]+\]$', sym) :
        words = re.split(r'\s+', sym[1:-1].strip())
        for w in words[:-1] :
            mod = mod | _modifiers[w][2]
        vkey = words[-1]
        _, _, sc, vkc, kn, ekn = _rawkeys[words[-1]]
        if _msrawmap.has_key(vkey) :
            vkey = _msrawmap[vkey]
        else :
            vkey = vkey.replace("K_", "")
    else :
        if sym == sym.upper() : mod = _modifiers['Shift'][2]
        _, _, sc, vkc, kn, ekn = _rawkeys["K_" + sym.upper()]
    return (sc, vkey, mod, kn, ekn, vkc)

def escape(keyname) :
    return "\\" + keyname if "\\[".find(keyname) >= 0 else keyname
        
class Key(int) :
    """ Wraps a kmn item as a class for easier handling """

    @classmethod
    def fromstr(cls, s) :
        return cls(keysym_item(s))

    def __str__(self) :
        return item_to_char(self)

    def keysym(self) :
        return item_to_key(self)


class Keyman(kmflorobject) :
    def create_sequences(self, input, mode = 'all', cache = None, history=None) :
        """ Given an input string of items, return all the strings of items that
            would produce this input sequence if executed
                mode - which sequences to include for any given rule
        """
        cache = cache or {}
        history = history or collections.defaultdict(list)
        found = False
        for rule in xrange(0, self.numrules) :
            res = self.reverse_match(input, rule, mode = mode)
            if not res: continue
            for y in self._sequence(input, rule, res, cache, history, mode) :
                yield y
            found = True
        # No rule matched the last char of input, so pass it through
        if not found and len(input) :
            res = (1, [[input[-1]]])
            for y in self._sequence(input, rule, res, cache, history, mode) :
                yield y

    def _sequence(self, input, rule, res, cache, history, mode) :
        for output in res[1] :
            if output[-1] >= 0x100FF00 : continue   # ignore specials
            newinput = input[0:len(input) - res[0]] + output[:-1]
            newstr = u"".join(unichr(i) for i in newinput)
            if newstr and newstr in cache :
                for x in cache[newstr] :
                    yield x + [Key(output[-1])]
                continue
            else :
                cache[newstr] = []
            rule_history = history[rule]
            if newinput and (not rule_history or rule_history[-1] > len(newinput)):
                rule_history.append(len(newinput))
                for x in self.create_sequences(newinput, mode, cache, history) :
                    cache[newstr].append(x)
                    yield x + [Key(output[-1])]
                rule_history.pop()
            else :
                yield [Key(output[0])]

    def reverse(self, string, mode = 'shortest') :
        """ Given a output string, return a list of input item strings that if run
            would generate the given string"""
        submode = mode
        if mode == 'shortest' : submode = 'first1'
        input = [ord(i) for i in string]
        res = list(self.create_sequences(input, mode = submode))
        if mode == 'shortest' :
            res.sort(key=len)
        return res

    def coverage_test(self, mode = 'all') :
        """ Analyse the rules to come up with test input strings that will
            ensure that all rules are exercised"""
        cache = {}
        outputted = set()
        for i in xrange(0, self.numrules) :
            for c in self.flatten_context(i, side = 'l', mode = mode) :
                last_context_item = c[-1]
                if (last_context_item & 0xFFFF) > 0xFF00 : continue
                if len(c) > 1 :
                    for output in self.create_sequences(c[:-1], mode, cache) :
                        res = output + [last_context_item]
                        if res not in outputted :
                            outputted.add(res)
                            yield res
                else :
                    res = [last_context_item]
                    if not res in outputted :
                        outputted.add(res)
                        yield res



__all__=["keysyms_items","keysym_item",
         "items_to_keys","item_to_key", "item_to_char"
         "keysym_scancodes", "chars_scancodes",
         "keysym_klcinfo", "char_keysym", "escape",
         "Key", "Keyman"]

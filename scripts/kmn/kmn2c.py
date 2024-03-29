#!/usr/bin/env python3

import optparse, re, os, sys, unicodedata
from palaso import kmn
from palaso.kmfl import kmfl

header = r"""
#define NULL 0

typedef unsigned short wchar_t;
typedef wchar_t WCHAR;
typedef WCHAR *LPWSTR;
typedef unsigned char BYTE;
typedef unsigned short WORD;
typedef unsigned short USHORT;
/* is this right for 32/64 bit? */
typedef unsigned long DWORD;

  typedef struct _VK_TO_BIT {
    BYTE Vk;
    BYTE ModBits;
  } VK_TO_BIT, *PVK_TO_BIT;

  typedef struct _MODIFIERS {
    PVK_TO_BIT pVkToBit;
    WORD wMaxModBits;
    BYTE ModNumber[];
  } MODIFIERS, *PMODIFIERS;

#define TYPEDEF_VK_TO_WCHARS(i) \
  typedef struct _VK_TO_WCHARS ## i { \
    BYTE VirtualKey; \
    BYTE Attributes; \
    WCHAR wch[i]; \
  } VK_TO_WCHARS ## i, *PVK_TO_WCHARS ## i;

  TYPEDEF_VK_TO_WCHARS(1)
  TYPEDEF_VK_TO_WCHARS(2)
  TYPEDEF_VK_TO_WCHARS(3)
  TYPEDEF_VK_TO_WCHARS(4)
  TYPEDEF_VK_TO_WCHARS(5)
  TYPEDEF_VK_TO_WCHARS(6)
  TYPEDEF_VK_TO_WCHARS(7)
  TYPEDEF_VK_TO_WCHARS(8)

  typedef struct _VK_TO_WCHAR_TABLE {
    PVK_TO_WCHARS1 pVkToWchars;
    BYTE nModifications;
    BYTE cbSize;
  } VK_TO_WCHAR_TABLE, *PVK_TO_WCHAR_TABLE;

  typedef struct _DEADKEY {
    DWORD dwBoth;
    WCHAR wchComposed;
    USHORT uFlags;
  } DEADKEY, *PDEADKEY;

  typedef WCHAR *DEADKEY_LPWSTR;

#define DKF_DEAD 1

  typedef struct _VSC_LPWSTR {
    BYTE vsc;
    LPWSTR pwsz;
  } VSC_LPWSTR, *PVSC_LPWSTR;

  typedef struct _VSC_VK {
    BYTE Vsc;
    USHORT Vk;
  } VSC_VK, *PVSC_VK;

#define TYPEDEF_LIGATURE(i) \
typedef struct _LIGATURE ## i { \
  BYTE VirtualKey; \
  WORD ModificationNumber; \
  WCHAR wch[i]; \
} LIGATURE ## i, *PLIGATURE ## i;

  TYPEDEF_LIGATURE(1)
  TYPEDEF_LIGATURE(2)
  TYPEDEF_LIGATURE(3)
  TYPEDEF_LIGATURE(4)
  TYPEDEF_LIGATURE(5)

#define KBD_VERSION 1
#define GET_KBD_VERSION(p) (HIWORD((p)->fLocalFlags))
#define KLLF_ALTGR 1
#define KLLF_SHIFTLOCK 2
#define KLLF_LRM_RLM 4

  typedef struct _KBDTABLES {
    PMODIFIERS pCharModifiers;
    PVK_TO_WCHAR_TABLE pVkToWcharTable;
    PDEADKEY pDeadKey;
    VSC_LPWSTR *pKeyNames;
    VSC_LPWSTR *pKeyNamesExt;
    LPWSTR *pKeyNamesDead;
    USHORT *pusVSCtoVK;
    BYTE bMaxVSCtoVK;
    PVSC_VK pVSCtoVK_E0;
    PVSC_VK pVSCtoVK_E1;
    DWORD fLocalFlags;
    BYTE nLgMaxd;
    BYTE cbLgEntry;
    PLIGATURE1 pLigature;
    DWORD dwType;
    DWORD dwSubType;
  } KBDTABLES, *PKBDTABLES;

  /* Constants that help table decoding */
#define WCH_NONE 0xf000
#define WCH_DEAD 0xf001
#define WCH_LGTR 0xf002

#define CAPSLOK     1
#define SGCAPS      2
#define CAPLOKALTGR 4
#define KANALOK     8
#define GRPSELTAP   0x80

#define VK_ABNT_C1  0xC1
#define VK_ABNT_C2  0xC2

#ifdef _M_IA64
#define ROSDATA static __declspec(allocate(".data"))
#else
#ifdef _MSC_VER
#pragma data_seg(".data")
#define ROSDATA static
#else
#define ROSDATA static __attribute__((section(".data")))
#endif
#endif

#define MAKELONG(x, y) (((y) << 16) | (x))

#define VK_EMPTY 0xff   /* The non-existent VK */
#define KSHIFT   0x001  /* Shift modifier */
#define KCTRL    0x002  /* Ctrl modifier */
#define KALT     0x004  /* Alt modifier */
#define KEXT     0x100  /* Extended key code */
#define KMULTI   0x200  /* Multi-key */
#define KSPEC    0x400  /* Special key */
#define KNUMP    0x800  /* Number-pad */
#define KNUMS    0xc00  /* Special + number pad */
#define KMEXT    0x300  /* Multi + ext */

ROSDATA USHORT scancode_to_vk[] = {
  /* Numbers Row */
  /* - 00 - */
  /* 1 ...         2 ...         3 ...         4 ... */
  VK_EMPTY,     VK_ESCAPE,    '1',          '2',
  '3',          '4',          '5',          '6',
  '7',          '8',          '9',          '0',
  VK_OEM_MINUS, VK_OEM_PLUS,  VK_BACK,
  /* - 0f - */
  /* First Letters Row */
  VK_TAB,       'Q',          'W',          'E',
  'R',          'T',          'Y',          'U',
  'I',          'O',          'P',
  VK_OEM_4,     VK_OEM_6,     VK_RETURN,
  /* - 1d - */
  /* Second Letters Row */
  VK_LCONTROL,
  'A',          'S',          'D',          'F',
  'G',          'H',          'J',          'K',
  'L',          VK_OEM_1,     VK_OEM_7,     VK_OEM_3,
  VK_LSHIFT,    VK_OEM_5,
  /* - 2c - */
  /* Third letters row */
  'Z',          'X',          'C',          'V',
  'B',          'N',          'M',          VK_OEM_COMMA,
  VK_OEM_PERIOD,VK_OEM_2,     VK_RSHIFT | KEXT,
  /* - 37 - */
  /* Bottom Row */
  VK_MULTIPLY,  VK_LMENU,     VK_SPACE,     VK_CAPITAL,

  /* - 3b - */
  /* F-Keys */
  VK_F1, VK_F2, VK_F3, VK_F4, VK_F5, VK_F6,
  VK_F7, VK_F8, VK_F9, VK_F10,
  /* - 45 - */
  /* Locks */
  VK_NUMLOCK | KMEXT,
  VK_SCROLL  | KMULTI,
  /* - 47 - */
  /* Number-Pad */
  VK_HOME   | KNUMS,      VK_UP     | KNUMS,      VK_PGUP | KNUMS, VK_SUBTRACT,
  VK_LEFT   | KNUMS,      VK_CLEAR  | KNUMS,      VK_RIGHT | KNUMS, VK_ADD,
  VK_END    | KNUMS,      VK_DOWN   | KNUMS,      VK_PGDN  | KNUMS,
  VK_INSERT | KNUMS,      VK_DELETE | KNUMS,
  /* - 54 - */
  /* Presumably PrtSc */
  VK_SNAPSHOT,
  /* - 55 - */
  /* Oddities, and the remaining standard F-Keys */
  VK_EMPTY,     VK_OEM_102,     VK_F11,       VK_F12,
  /* - 59 - */
  VK_PAUSE,	  VK_OEM_WSCTRL, VK_OEM_FINISH, VK_OEM_JUMP, VK_EREOF, /* EREOF */
  VK_OEM_BACKTAB, VK_OEM_AUTO,   VK_EMPTY,      VK_ZOOM,               /* ZOOM */
  VK_HELP,
  /* - 64 - */
  /* Even more F-Keys (for example, NCR keyboards from the early 90's) */
  VK_F13, VK_F14, VK_F15, VK_F16, VK_F17, VK_F18, VK_F19, VK_F20,
  VK_F21, VK_F22, VK_F23,
  /* - 6f - */
  /* Not sure who uses these codes */
  VK_OEM_PA3, VK_EMPTY, VK_OEM_RESET,
  /* - 72 - */
  VK_EMPTY, 0xc1, VK_EMPTY, VK_EMPTY,
  /* - 76 - */
  /* One more f-key */
  VK_F24,
  /* - 77 - */
  VK_EMPTY, VK_EMPTY, VK_EMPTY, VK_EMPTY,
  VK_OEM_PA1, VK_TAB, VK_EMPTY, 0xc2,  /* PA1 */
  0,
  /* - 80 - */
  0
};

#define EXTCODE(x, y) { x, (y & 0xFF) | KEXT }
ROSDATA VSC_VK extcode0_to_vk[] = {
  EXTCODE(0x10, VK_MEDIA_PREV_TRACK),
  EXTCODE(0x19, VK_MEDIA_NEXT_TRACK),
  EXTCODE(0x1D, VK_RCONTROL),
  EXTCODE(0x20, VK_VOLUME_MUTE),
  EXTCODE(0x21, VK_LAUNCH_APP2),
  EXTCODE(0x22, VK_MEDIA_PLAY_PAUSE),
  EXTCODE(0x24, VK_MEDIA_STOP),
  EXTCODE(0x2E, VK_VOLUME_DOWN),
  EXTCODE(0x30, VK_VOLUME_UP),
  EXTCODE(0x32, VK_BROWSER_HOME),
  EXTCODE(0x35, VK_DIVIDE),
  EXTCODE(0x37, VK_SNAPSHOT),
  EXTCODE(0x38, VK_RMENU),
  EXTCODE(0x47, VK_HOME),
  EXTCODE(0x48, VK_UP),
  EXTCODE(0x49, VK_PRIOR),
  EXTCODE(0x4B, VK_LEFT),
  EXTCODE(0x4D, VK_RIGHT),
  EXTCODE(0x4F, VK_END),
  EXTCODE(0x50, VK_DOWN),
  EXTCODE(0x51, VK_NEXT),
  EXTCODE(0x52, VK_INSERT),
  EXTCODE(0x53, VK_DELETE),
  EXTCODE(0x5B, VK_LWIN),
  EXTCODE(0x5C, VK_RWIN),
  EXTCODE(0x5D, VK_APP),
  EXTCODE(0x5F, VK_SLEEP),
  EXTCODE(0x65, VK_BROWSER_SEARCH),
  EXTCODE(0x66, VK_BROWSER_FAVORITES),
  EXTCODE(0x67, VK_BROWSER_REFRESH),
  EXTCODE(0x68, VK_BROWSER_STOP),
  EXTCODE(0x69, VK_BROWSER_FORWARD),
  EXTCODE(0x6A, VK_BROWSER_BACK),
  EXTCODE(0x6B, VK_LAUNCH_APP1),
  EXTCODE(0x6C, VK_LAUNCH_MAIL),
  EXTCODE(0x6D, VK_LAUNCH_MEDIA_SELECT),
  EXTCODE(0x1C, VK_RETURN),
  EXTCODE(0x46, VK_CANCEL),
  { 0, 0 },
};

ROSDATA VSC_VK extcode1_to_vk[] = {
  { 0x1d, VK_PAUSE},
  { 0, 0 },
};

"""

key_tops  = r'''`1234567890-=QWERTYUIOP[]\ASDFGHJKL;'ZXCVBNM,./'''
shifted   = r'''~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'''
unshifted = r'''`1234567890-=qwertyuiop\[]\asdfghjkl;'zxcvbnm,./ '''

extkeys = ('[K_TAB]', '[K_ENTER]', '[K_BKSP]', '[K_ESC]')

parser = optparse.OptionParser(usage='%prog [options] <KEYMAN FILE>\n')
parser.add_option("-n","--name", action='store', help='MSKLC Project name')
parser.add_option("-o","--output", action="store", help='File to output .c to defaults to stdout')
#parser.add_option("-d","--deffile", action="store", help=".def file to output")
parser.add_option("-r","--resource", action="store", help='File to output .rc to defaults to stdout')
parser.add_option("-c","--capslockkeys", action="store", help="Enable capslock for keys in the given string")
parser.add_option("--copyright", action="store", help="Set copyright message overriding the COPYRIGHT store")
parser.add_option("--author", action="store", help="Set author overriding the AUTHOR store")
parser.add_option("--language", action="store", help="Override &ethnologuecode store")
parser.add_option("--version", action="store", help="Override &version with w.x.y.z")
parser.add_option("--langname", action="store", help="Set langauge name")

(opts,kmns) = parser.parse_args()
if len(kmns) == 0:
    sys.stderr.write(parser.expand_prog_name('%prog: missing KEYMAN FILE\n'))
    parser.print_help(file=sys.stderr)
    sys.exit(1)

kb = kmns[0]

overrides = {
    'name' : 'NAME',
    'copyright' : 'COPYRIGHT',
    'author' : 'AUTHOR',
    'language' : 'ETHNOLOGUE',
}
km = kmfl(kb)
for k, v in overrides.items() :
    opts.ensure_value(k, km.store(v))
if not opts.language : opts.language = "und"

if opts.output :
    outfile = file(opts.output, "w")
else :
    outfile = sys.stdout

if opts.resource :
    resfile = file(opts.resource, "w")
elif opts.output :
    resfile = file(os.path.splitext(opts.output)[0] + ".rc", "w")
else :
    resfile = sys.stdout

#if opts.deffile :
#    deffile = file(opts.deffile, "w")
#elif opts.output :
#    deffile = file(os.path.splitext(opts.output)[0] + ".def", "w")
#else :
#    deffile = sys.stdout

# iterate the rules to find all key rules and see if any have odd modifiers
# then make a map of modifier codes and count them. Then we know how
# big to make keys[255][n]
mods = [[] for i in range(8)]
modids = []
keytops = [''] * 256
for i in range(km._num_rules()) :
    (lhs, rhs, gpnum, flags) = km.rule(i)
    if not flags & 1 : continue
    sym = kmn.item_to_key(lhs[-1])
    if not sym : continue
    (sc, vkey, mod, kn, ekn, vkc) = kmn.keysym_klcinfo(sym)
    mods[mod].append(sym)
allkeys = list(kmn.char_keysym(c) for c in shifted + unshifted)
allkeys.extend(extkeys)
for ksym in allkeys :
    sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(ksym)
    mods[mod].append(ksym)
for k in unshifted :
    sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(kmn.char_keysym(k))
    keytops[vkc] = k
    
logmod = 1
modgroups = [15] * len(mods)
for i in range(len(mods)) :
    if len(mods[i]) or i < 2 :
        modgroups[i] = len(modids)
        modids.append(i)
        while (1 << logmod) <= i : logmod += 1

modres = '''
ROSDATA VK_TO_BIT aVkBits[] = {
    {VK_SHIFT, 1},'''
if (logmod > 1) :
    modres += '''
    {VK_CTRL, 2},'''
if (logmod > 2) :
    modres += '''
    {VK_ALT, 4},'''
modres += '''
    {0, 0}
};

ROSDATA MODIFIERS aModifiers = {
    aVkBits,
'''

modres += "    " + str((1 << logmod) - 1) + ",";
modres += '''
    {'''

modres += ", ".join(map(str, modgroups[0:(1 << logmod)]))
modres += "}\n};\n"


deads = []
keys = [[None] * (1 << logmod) for i in range(255)]    # declare array keys[255][2] !!
ligs = [[None] * (1 << logmod) for i in range(255)]    # declare array keys[255][2] !!
deadkeys = [[{} for j in range(len(modids))] for i in range(255)]    # declare array keys[255][2] !!
maxliglength = 0
keynames = {}
extkeynames = {}
reskeynames = ""
resextkeynames = ""
for m in mods :
    for ksym in m :
        sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(ksym)
        if kn :
            keynames[sc] = kn
        if ekn :
            extkeynames[sc] = ekn
        item = kmn.keysym_item(ksym)
        res = km.interpret_items([item])
        if not len(res) : res = [item]
        if (res[0] >> 24) == 5 :
            keys[vkc][mod] = chr(0xF001)
            deads.append(ksym)
        elif len(res) > 1 or ord(kmn.item_to_char(res[0])) > 0xFFFF :
            keys[vkc][mod] = chr(0xF002)
            ligs[vkc][mod] = res
            liglen = 0
            for r in res :
                if ord(kmn.item_to_char(r)) > 0xFFFF :
                    liglen += 2
                else :
                    liglen += 1
            if liglen > maxliglength : maxliglength = liglen
        else :
            keys[vkc][mod] = kmn.item_to_char(res[0])
            if keys[vkc][mod] == "\x0A" : keys[vkc][mod] = "\x0D"

for k, v in keynames.items() :
    reskeynames += "{ 0x%02X, L\"%s\" },\n" % (k, v)
if reskeynames :
    reskeynames = "ROSDATA VSC_LPWSTR aKeyName[] = {\n" + reskeynames + "    {0, NULL}\n};\n"

for k, v in extkeynames.items() :
    resextkeynames += "{ 0x%02X, L\"%s\" },\n" % (k, v)
if resextkeynames :
    resextkeynames = "ROSDATA VSC_LPWSTR aExtKeyName[] = {\n" + resextkeynames + "    {0, NULL}\n};\n"

dkeys = [[None] * (1 << logmod) for i in range(256)]
for d in deads :
    sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(d)
    for m in mods :
        for ksym in m :
            sc2, vkey2, mod2, kn2, ekn2, vkc2 = kmn.keysym_klcinfo(ksym)
            i = kmn.keysym_item(ksym)
            res = km.interpret_items([kmn.keysym_item(d), i])
            if len(res) > 2 :
                sys.stderr.write("Can't combine deadkeys and ligatures with %s and %s\n" % (d, ksym))
                # error
            elif len(res) > 1 :
                if res[0] >> 24 < 2 : 
                    dkeys[vkc][modgroups[mod]] = kmn.item_to_char(res[0])
            elif len(res) :
                deadkeys[vkc][modgroups[mod]][keys[vkc2][mod2]] = kmn.item_to_char(res[-1])

# U+F000 - ignore
# U+F001 - deadkey
# U+F002 - ligature
donekeys = [0] * 256
keyres = ""
listres = "ROSDATA VK_TO_WCHAR_TABLE aVkToWcharTable[] = {\n"
for l in range(len(modids), 0, -1) :
    res = []
    for v in range(len(keys)) :
        if donekeys[v] : continue
        if keys[v][modids[l-1]] :
            donekeys[v] = True
            attribs = 0
            if opts.capslockkeys and keytops[v] and keytops[v] in opts.capslockkeys :
                attribs = 1
            res.append([v, attribs])
            res[-1].extend([keys[v][modids[i]] for i in range(l)])
    if len(res) :
        keyres += "ROSDATA VK_TO_WCHARS%d aVkToWch%d[] = {\n" % (l, l)
        for r in res :
            keyres += "    { 0x%02x,    %d,  " % (r[0], r[1])
            keyres += ",\t".join("0x%04X" % (ord(x) if x else 0xF000) for x in r[2:]) + "},\n"
            if chr(0xF001) in r[2:] :
                keyres += "    { -1,    0,  "
                keyres += ",\t".join("0x%04X" % (ord(dkeys[r[0]][i]) if r[2+i] == chr(0xF001) else 0xF000) for x in range(0, len(r) - 2)) + "},\n"
        keyres += "{ " + ", ".join ("0" * (l + 2)) + "}};\n\n"
        listres += "    { (PVK_TO_WCHARS1)aVkToWch%d, %d, sizeof(aVkToWch%d[0]) },\n" % (l, l, l)
listres += "    { NULL, 0, 0 }\n};\n"

deadres = ""
for i in range(len(deadkeys)) :
    for m in range(len(deadkeys[i])) :
        for k, v in deadkeys[i][m].items() :
            if v : deadres += "{ MAKELONG(0x%04X, 0x%04X), 0x%04X, 1 },\n" % (ord(k), i, ord(v))

deadres = "ROSDATA DEADKEY aDeadKey[] = {\n" + deadres + "{ MAKELONG(0, 0), 0, 0}\n};\n"
resdeadname = "ROSDATA LPWSTR aDeadKeyName[] = {\n"
for d in dkeys :
    for m in d :
        if m : 
            try :
                nm = unicodedata.name(m)
            except ValueError :
                nm = "U%04X" % (ord(m))
            resdeadname += "    \"%s\",\n" % (nm)
resdeadname += '    NULL\n};'

ligres = ""
if maxliglength :
    ligres += "#define MAXLIGLENGTH %d\n#define LIGSIZE sizeof(LIGATURE%d)\n" % (maxliglength, maxliglength)
    ligres += "ROSDATA LIGATURE%d aLigature[] = {\n" % (maxliglength)
    for k in range(len(ligs)) :
        for m in range(len(ligs[k])) :
            l = ligs[k][m]
            if not l : continue
            t = []
            for c in l :
                char = ord(kmn.item_to_char(c))
                if char > 0xFFFF :
                    t.extend([0xD7C0 + char / 1024, 0xDC00 + (char & 1023)])
                else :
                    t.append(char)
            t.extend([0xF000] * (maxliglength - len(t)))
            ligres += "    { 0x%02x,   %d,  " % (k, modgroups[m])
            ligres += ",\t".join("0x%04X" % x for x in t)
            ligres += " },\n"
    ligres += "    { 0, 0, " + ", ".join("0" * maxliglength) + " }\n};\n"
else :
    ligres += "#define MAXLIGLENGTH 0\n#define LIGSIZE 0\n#define aLigature NULL\n"

from palaso.kmn import _rawkeys, _msrawmap, _vkextras

resvk = ""
for k, v in _rawkeys.items() :
    if len(k) <= 3 : continue
    if k in _msrawmap :
        resvk += "#define VK_%s\t%d\n" % (_msrawmap[k], v[3])
    else :
        resvk += "#define V%s\t%d\n" % (k, v[3])
for k, v in _vkextras.items() :
    resvk += "#define V%s\t%d\n" % (k, v)

tail = '''
ROSDATA KBDTABLES aKbdTables = {
    &aModifiers,
    aVkToWcharTable,
    aDeadKey,
    aKeyName,
    aExtKeyName,
    aDeadKeyName,
    scancode_to_vk,
    sizeof(scancode_to_vk) / sizeof(scancode_to_vk[0]),
    extcode0_to_vk,    
    extcode1_to_vk,
    0x00010001,
    MAXLIGLENGTH,
    LIGSIZE,
    (PLIGATURE1)aLigature,
    4, 0
};

PKBDTABLES KbdLayerDescriptor(void) {
    return &aKbdTables;
}
'''

outfile.write(resvk)
outfile.write(header)
outfile.write(modres)
outfile.write(keyres)
outfile.write(listres)
outfile.write(deadres)
outfile.write(ligres)
outfile.write(reskeynames)
outfile.write(resextkeynames)
outfile.write(resdeadname)
outfile.write(tail)
if outfile != sys.stdout : outfile.close()

strinfo = {
    '1000' : 'name',
    '1100' : 'langname',
    '1200' : 'language'
}
resstrings = {}
for s, v in strinfo.items() :
    resstrings[s] = getattr(opts, v)

resrheader = '''
LANGUAGE 9, 1

'''
for s, v in resstrings.items() :
    resrheader += "STRINGTABLE\nBEGIN\n  %s, \"%s\"\nEND\n\n" % (s, v)

rversion = ", ".join(((opts.version if opts.version else "0") + ".0.0.0").split(".")[0:4])

resrheader += '''
1 VERSIONINFO
 FILEVERSION %s
 PRODUCTVERSION %s
 FILEFLAGSMASK 0x3f
 FILEOS 0x40004
 FILETYPE 0x2
 FILESUBTYPE 0x2
BEGIN
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "000004B0"
    BEGIN
''' % (rversion, rversion)

sinfo = {}
if getattr(opts, 'author', None) : sinfo['CompanyName'] = opts.author
if getattr(opts, 'name', None) : sinfo['FileDescription'] = opts.name
sinfo['FileVersion'] = rversion
if getattr(opts, 'copyright', None) : sinfo['LegalCopyright'] = opts.copyright
sinfo['OriginalFilename'] = os.path.splitext(os.path.basename(kmns[0]))[0]
sinfo["ProductVersion"] = rversion
for s, v in sinfo.items() :
    resrheader += "      VALUE \"%s\", \"%s\"\n" % (s, v)
resrheader +='''
    END
  END
  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation", 0x0, 1200
  END
END
'''

resfile.write(resrheader)
if resfile != sys.stdout : resfile.close()

#deffile.write('''
#LIBRARY %s
#
#EXPORTS
#    KbdLayerDescriptor @1
#''' % (os.path.splitext(opts.output)[0].upper()))
#if deffile != sys.stdout : deffile.close()


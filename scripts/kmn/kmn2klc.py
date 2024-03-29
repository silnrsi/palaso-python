#!/usr/bin/env python3
'''
Generate a Microsoft Keyboard Layout Creator file from a keyman keyboard.
This program will also handle deadkeys in the KMN file.
'''
__version__ = '0.9'
__date__    = '15 October 2009'
__author__  = 'Martin Hosken <martin_hosken@sil.org>'

import optparse, os.path, re, sys
from palaso.kmfl import kmfl
from palaso import kmn

def res_str(res) :
    if len(res) > 4 or len(res) == 0 : return None
    codes = []
    for r in res :
        if item_type(r) > 0 : return None
        else :
            codes.append("%04X" % (r & 0xFFFF))
    return ("\t".join(codes))

def item_type(x) : return (x >> 24) & 0xFF

def myprint(s):
    print(s, end='\r\n')

key_tops  = r'''`1234567890-=QWERTYUIOP[]\ASDFGHJKL;'ZXCVBNM,./'''
shifted   = r'''~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'''
unshifted = r'''`1234567890-=qwertyuiop\[]\\asdfghjkl;'zxcvbnm,./'''


header = '''\
KBD	{0}	"{1}"

COPYRIGHT	"{2}"

COMPANY	"{3}"

LOCALENAME	"en-US"

LOCALEID	"00000409"

VERSION	1.0

SHIFTSTATE

0	// Column 4
1	// Column 5 : Shift
2	// Column 6 : Ctrl

LAYOUT		; an extra @ at the end is a dead key

//SC    VK_         Cap     0       1       2
//--    ----        ----    ----    ----    ----

'''.format

key = '''{0:02x}	{1}	{2}	{3}	{4}	-1'''.format

lighead = '''
LIGATURE

//VK_   Mod #   Char0   Char1   Char2   Char3
//---   -----   -----   -----   -----   -----
'''

lig = '''{0}     {1}     {2}'''.format

footer = '''
DESCRIPTIONS

0409    {0}
LANGUAGENAMES

0409    English (United States)
ENDKBD
'''.format

parser = optparse.OptionParser(usage='%prog [options] <KEYMAN FILE>\n' + __doc__)
parser.add_option("-n","--name", action='store', help='MSKLC Project name')

(opts,kmns) = parser.parse_args()
if len(kmns) == 0:
    sys.stderr.write(parser.expand_prog_name('%prog: missing KEYMAN FILE\n'))
    parser.print_help(file=sys.stderr)
    sys.exit(1)

kb = kmns[0]
if not opts.name :
    opts.name = re.sub(r'\..*$', '', os.path.basename(kb)).replace(' ', '')

km = kmfl(kb)
#sys.stdout = codecs.getwriter("utf_16_le")(sys.stdout)
myprint(header(opts.name, km.store('NAME'), km.store('COPYRIGHT') or "GPL", km.store('AUTHOR') or "me"))

deads = []
ligs = []
keys = [[None] * 2 for i in range(255)]    # declare array keys[255][2] !!
keynames = [None] * 255
ekeynames = [None] * 255
for k in shifted + unshifted :
    ksym = kmn.char_keysym(k)
    sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(ksym)
    keynames[sc] = kn
    ekeynames[sc] = ekn
    res = km.interpret_items([kmn.keysym_item(ksym)])
    if (res[0] >> 24) == 5 :
        deads.append([ksym,{},0])
    elif len(res) > 1 :
        ligs.append((vkey, mod, res))
        keys[sc][mod] = (sc, vkey, 2)
    else :
        keys[sc][mod] = (sc, vkey, 0, res)

for d in deads :
    for k in shifted + unshifted :
        ksym = kmn.char_keysym(k)
        res = km.interpret_items([d[0], kmn.keysym_item(ksym)])
        d[1][k] = res
        if ksym == d[0] :
            sc, vkey, mod, kn, ekn, vkc = kmn.keysym_klcinfo(ksym)
            keys[sc][mod] = (sc, vkey, 1, res)
            d[2] = res[0]

for s in keys :
    sc = None
    vk = None
    if not s : continue
    res = [-1] * 2
    for m in range(2) :
        if not s[m] : continue
        sc = s[m][0]
        vk = s[m][1]
        if s[m][2] == 2 :
            res[m] = '%%'
        else :
            res[m] = "%04x" % (ord(kmn.item_to_char(s[m][3][0])))
        if s[m][2] == 1 and res[m] != '-1' :
            res[m] += "@"
    if sc :
        myprint(key(sc, vk, 0, res[0], res[1]))

if len(deads) > 0 :
    for d in deads :
        if not d : continue
        myprint("\nDEADKEY %04X\n" % (d[2] & 0xFFFF))
        for k in d[1] :
            res = res_str(d[1][k])
            if res :
                myprint("%04X\t%s" % (ord(k), res))

if len(ligs) > 0 :
    myprint(lighead)
    for l in ligs :
        codestr = res_str(l[2])
        myprint(lig(l[0], l[1], codestr))

myprint('''

KEYNAME

01	Esc
0e	Backspace
0f	Tab
1c	Enter
1d	Ctrl
2a	Shift
36	"Right Shift"
37	"Num *"
38	Alt
39	Space
3a	"Caps Lock"
3b	F1
3c	F2
3d	F3
3e	F4
3f	F5
40	F6
41	F7
42	F8
43	F9
44	F10
45	Pause
46	"Scroll Lock"
47	"Num 7"
48	"Num 8"
49	"Num 9"
4a	"Num -"
4b	"Num 4"
4c	"Num 5"
4d	"Num 6"
4e	"Num +"
4f	"Num 1"
50	"Num 2"
51	"Num 3"
52	"Num 0"
53	"Num Del"
54	"Sys Req"
57	F11
58	F12
7c	F13
7d	F14
7e	F15
7f	F16
80	F17
81	F18
82	F19
83	F20
84	F21
85	F22
86	F23
87	F24

KEYNAME_EXT

1c	"Num Enter"
1d	"Right Ctrl"
35	"Num /"
37	"Prnt Scrn"
38	"Right Alt"
45	"Num Lock"
46	Break
47	Home
48	Up
49	"Page Up"
4b	Left
4d	Right
4f	End
50	Down
51	"Page Down"
52	Insert
53	Delete
54	<00>
56	Help
5b	"Left Windows"
5c	"Right Windows"
5d	Application

ENDKBD
''')
#myprint "\nKEYNAME\n"
#for i in xrange(len(keynames)) :
#    if keynames[i] :
#        if keynames[i].find(" ") >= 0 :
#            myprint '%02x\t"%s"' % (i, keynames[i])
#        else :
#            myprint '%02x\t%s' % (i, keynames[i])
#
#myprint "\nKEYNAME_EXT\n"
#for i in xrange(len(ekeynames)) :
#    if ekeynames[i] :
#        if ekeynames[i].find(" ") >= 0:
#            myprint '%02x\t"%s"' % (i, ekeynames[i])
#        else :
#            myprint '%02x\t%s' % (i, ekeynames[i])
#
#myprint "\nENDKBD"


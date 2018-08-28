#!/usr/bin/python

from collections import namedtuple, OrderedDict

def semireader(fname):
    with open(fname, "r") as f:
        for l in f.readlines():
            s = l.split('#', 1)[0].strip()
            res = [x.strip() for x in s.split(';')]
            if len(res) and res[0]:
                yield res

def binlookup(k, dat):
    last = len(dat) - 1
    first = 0

    while first <= last:
        mid = (last + first) // 2
        r = dat[mid][0]
        if r.has(k):
            return dat[mid][1]
        elif k < r.first:
            last = mid - 1
        else:
            first = mid + 1
    return None

CodeRange = namedtuple('CodeRange', ['first', 'last'])
def CodePoint(x):
    return CodeRange(x, x)

def inrange(self, x):
    return self.first <= x <= self.last
CodeRange.has = inrange

class UnicodeData:
    dataType = namedtuple('UnicodeDataType', ['name', 'category', 'ccc',
            'bidi', 'decomp', 'decimal', 'digit', 'numeric', 'mirrored',
            'iso1name', 'comment', 'upper', 'lower', 'title'])

    def __init__(self, fname):
        self.ranges = []
        self.parse(fname)

    def parse(self, fname):
        vals = []
        for l in semireader(fname):
            cp = int(l[0], base=16)
            if ', First' in l[1]:
                first = cp
                continue
            elif ', Last' in l[1]:
                r = CodeRange(first, cp)
            else:
                r = CodePoint(cp)
            vals.append((r, self.dataType(*l[1:])))
        self.ranges = sorted(vals)

    def __getitem__(self, k):
        return binlookup(k, self.ranges)

class CategoryFile:
    def __init__(self, fname):
        self.vals = OrderedDict()
        self.top = 1
        self.ranges = []
        self.parse(fname)

    def parse(self, fname):
        vals = []
        for l in semireader(fname):
            if '..' in l[0]:
                f, e = l[0].split('..')
                r = CodeRange(int(f, base=16), int(e, base=16))
            else:
                r = CodePoint(int(l[0], base=16))
            if l[1] not in self.vals:
                self.vals[l[1]] = self.top
                self.top += 1
            vals.append((r, self.vals[l[1]]))
        self.ranges = sorted(vals)

    def __getitem__(self, k):
        res = binlookup(k, self.ranges)
        if res is not None:
            return self.vals.keys()[res-1]
        return res

use_classes = (
    ('B', lambda i,u,s,p: s in ('Number', 'Consonant', 'Consonant_Head_letter', 'Tone_Letter', 'Vowel_Independent') or \
                        u.category == 'Lo' and s in ('Avagraha', 'Bindu', 'Consonant_Final', 'Consonant_Medial', \
                                        'Consonant_Subjoined', 'Vowel', 'Vowel_Dependent')),
    ('CGJ', lambda i,u,s,p: i == 0x034F),
    ('CM', lambda i,u,s,p: s in ('Nukta', 'Gemination_Mark', 'Consonant_Killer')),
    ('CS', lambda i,u,s,p: s == 'Consonant_With_Stacker'),
    ('F', lambda i,u,s,p: s == 'Consonant_Succeeding_Repha' or (u.category != 'Lo' and s == 'Consonant_Final')),
    ('FM', lambda i,u,s,p: s == 'Syllable_Modifier'),
    ('GB', lambda i,u,s,p: s == 'Consonant_Placeholder' or i in (0x2015, 0x2022, 0x25FB, 0x25FC, 0x25FD, 0x25FE)),
    ('H', lambda i,u,s,p: s in ('Virama', 'Invisible_Stacker')),
    ('HN', lambda i,u,s,p: s == 'Number_Joiner'),
    ('IND', lambda i,u,s,p: s in ('Consonant_Dead', 'Modifying_Letter') or (u.category == 'Po' and i not in (0x104E, 0x2022, 0x002D))),
    ('M', lambda i,u,s,p: (s == 'Consonant_Medial' and u.category != 'Lo') or (220 <= int(u.ccc) <= 232)),
    ('N', lambda i,u,s,p: s == 'Brahmi_Joining_Number'),
    ('O', lambda i,u,s,p: p == 'common' or u.category == 'Zs'),
    ('R', lambda i,u,s,p: s in ('Consonant_Preceding_Repha', 'Consonant_Prefixed')),
    ('S', lambda i,u,s,p: u.category in ('So', 'Sc') and i != 0x25CC),
    ('SM', lambda i,u,s,p: i in range(0x1B6B, 0x1B74)),
    ('SUB', lambda i,u,s,p: s == 'Consonant_Subjoined' and u.category != 'Lo'),
    ('V', lambda i,u,s,p: s == 'Pure_Killer' or (s in ('Vowel', 'Vowel_Dependent') and u.category != 'Lo') or 232 < int(u.ccc) < 240),
    ('VM', lambda i,u,s,p: s in ('Tone_Mark', 'Cantillation_Mark', 'Register_Shifter', 'Visarga') or (s == 'Bindu' and u.category != 'Lo')),
    ('VS', lambda i,u,s,p: i in range(0xFE00, 0xFE10)),
    ('WJ', lambda i,u,s,p: i == 0x2060),
    ('ZWJ', lambda i,u,s,p: s == 'Joiner'),
    ('ZWNJ', lambda i,u,s,p: s == 'Non_Joiner'))

use_subclasses = {
    'CM': ( ('CMAbv', lambda i,u,s,p: p == 'Top'),
            ('CMBlw', lambda i,u,s,p: p == 'Bottom')),
    'F': (  ('FAbv', lambda i,u,s,p: p == 'Top'),
            ('FBlw', lambda i,u,s,p: p == 'Bottom'),
            ('FPst', lambda i,u,s,p: p == 'Right')),
    'M': (  ('MAbv', lambda i,u,s,p: p == 'Top' or int(u.ccc) == 230),
            ('MBlw', lambda i,u,s,p: p == 'Bottom' or int(u.ccc) == 220),
            ('MPre', lambda i,u,s,p: p == 'Left'),
            ('MPst', lambda i,u,s,p: p == 'Right')),
    'SM': ( ('SMAbv', lambda i,u,s,p: i in [0x1B6B] + range(0x1B6D, 0x1B74)),
            ('SMBlw', lambda i,u,s,p: i == 0x1B6C)),
    'V': (  ('VAbv', lambda i,u,s,p: p in ('Top', 'Top_And_Bottom', 'Top_And_Bottom_And_Right', 'Top_And_Right')),
            ('VPre', lambda i,u,s,p: p == 'Left'),
            ('VBlw', lambda i,u,s,p: p in ('Bottom', 'Overstruck', 'Bottom_and_Right')),
            ('VPst', lambda i,u,s,p: p in ('Right', 'Top_And_Left', 'Top_And_Left_And_Right', 'Left_And_Right'))),
    'VM': ( ('VMAbv', lambda i,u,s,p: p == 'Top'),
            ('VMBlw', lambda i,u,s,p: p in ('Bottom', 'Overstruck')),
            ('VMPre', lambda i,u,s,p: p == 'Left'),
            ('VMPst', lambda i,u,s,p: p == 'Right'))}

def getuse_class(i, u, s, p, script):
    category = None
    subcategory = None
    for a in use_classes:
        if a[1](i, u, s, script):
            category = a[0]
            break
    if category in use_subclasses:
        for a in use_subclasses[category]:
            if a[1](i, u, s, p):
                subcategory = a[0]
                break
    return (category, subcategory)

keyorders = {
    'SUB': 5, 'H': 5, 'N': 5,
    'MPre': 10,
    'MAbv': 15, 'SMAbv': 15,
    'MBlw': 20, 'SMBlw': 20,
    'MPst': 25,
    'VPre': 30,
    'VAbv': 35,
    'VBlw': 40,
    'VPst': 45,
    'VMPre': 50,
    'VMAbv': 55,
    'VMBlw': 60,
    'VMPst': 65,
    'FAbv': 70,
    'FBlw': 75,
    'FPst': 80,
    'FM': 85
}

if __name__ == '__main__':
    import argparse, os

    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to ucd directory')
    args = parser.parse_args()

    unidb = UnicodeData(os.path.join(args.path, 'UnicodeData.txt'))
    indicSyllable = CategoryFile(os.path.join(args.path, 'IndicSyllabicCategory.txt'))
    indicPosition = CategoryFile(os.path.join(args.path, 'IndicPositionalCategory.txt'))
    scripts = CategoryFile(os.path.join(args.path, 'Scripts.txt'))
    for i in xrange(0x10000):
        u = unidb[i]
        s = indicSyllable[i]
        p = indicPosition[i]
        script = scripts[i]
        if u is not None:
            (cat, subcat) = getuse_class(i, u, s, p, script) 
            ko = keyorders.get(subcat, keyorders.get(cat, 0))
            if ko == 0 and not u.category.startswith('M'):
                continue
            print(",".join([hex(i), u.name, u.category or "", u.ccc or '0', s or "",
                            p or "", script or "", cat or "", subcat or "", str(ko)]))

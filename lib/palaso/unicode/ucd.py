#!/usr/bin/python3

"""ucd

This module contains the basic ucd information for every character in Unicode.

SYNOPSIS:

    from palaso.unicode.ucd import get_ucd, get_info, find_ucd, get_enums
    print(get_ucd(0x0041, 'scx'))
    print(get_info(0x0041))
    print(get_enums("indic position"))
    print(find_ucd("indic position", "Bottom")

Note cjk properties are not supported for space reasons.

If you want to use your own data file (perhaps the module data is stale) the use
the object interface:

    from palaso.unicode.ucd import UCD
    myucd = UCD(localfile="ucd.nounihan.flat.zip")   # localfile falls back to bundled data
    print(myucd.get(0x0041, 'scx'))

The second parameter specifies the property to be queried and must be coded using the
abbreviations that are defined in the XML expression of the Unicode Character Database.
For property abbreviation and value definitions, see Unicode Standard Annex #42 at
https://www.unicode.org/reports/tr42, especially section 4.4 Properties.

When a new version of Unicode is released, an updated ucdata_pickle.bz2
file should be created using the command:

    python3 ucd.py ucd.all.flat.zip ucdata_pickle.bz2

For characters not yet in Unicode, data for additional characters can
be temporarily appended to the bundled data:

    from palaso.unicode.ucd import get_ucd, loadxml
    loadxml("extra-ucd.xml")

or, with the object interface:

    from palaso.unicode.ucd import UCD
    myucd = UCD().loadxml("extra-ucd.xml")

The named file must be coded in the same form as the "flat" UCD XML data, though the only
required character attributes are "cp" and anything needed by the calling process. For example:

    <?xml version="1.0" encoding="utf-8" standalone="yes"?>
    <ucd xmlns="http://www.unicode.org/ns/2003/ucd/1.0">
        <description>Some additional characters</description>
        <repertoire>
            <char cp="10EC2" age="16.0" gc="Lo" bc="AL" na="ARABIC LETTER DAL WITH TWO DOTS VERTICALLY BELOW"></char>
            <char cp="10EC3" age="16.0" gc="Lo" bc="AL" na="ARABIC LETTER TAH WITH TWO DOTS VERTICALLY BELOW"></char>
            <char cp="10EC4" age="16.0" gc="Lo" bc="AL" na="ARABIC LETTER KAF WITH TWO DOTS VERTICALLY BELOW"></char>
        </repertoire>
    </ucd>

"""

import array, pickle, pprint
import xml.etree.ElementTree as et
import os, bz2, zipfile, io
import urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import platformdirs

__all__ = ['get_ucd', 'find_ucd', 'get_enums', 'get_info']

# Unicode data xml attributes
_binfieldnames = """AHex Alpha Bidi_C Bidi_M Cased CE CI Comp_Ex CWCF CWCM CWKCF CWL CWT CWU
    Dash Dep DI Dia Ext Gr_Base Gr_Ext Gr_Link Hex Hyphen IDC Ideo IDS IDSB
    IDST Join_C LOE Lower Math MCM NChar OAlpha ODI OGr_Ext OIDC OIDS OLower OMath
    OUpper Pat_Syn Pat_WS PCM QMark Radical RI SD STerm Term UIdeo Upper VS
    WSpace XIDC XIDS XO_NFC XO_NFD XO_NFKC XO_NFKD"""
_binmap = dict((x, i) for i, x in enumerate(_binfieldnames.split()))
_enumfieldnames = """age blk sc scx bc bpt ccc dt ea gc GCB hst InPC InSC jg jt lb
    NFC_QC NFD_QC NFKC_QC NFKD_QC nt SB vo WB nv JSN"""
_cpfieldnames = """cf dm FC_NFKC lc NFKC_CF scf slc stc suc tc uc bmg bpb"""
_cpfields = set(_cpfieldnames.split())
_fields = ['_b0', 'age', 'na', 'JSN', 'gc', 'ccc', 'dt', 'dm', 'nt', 'nv',
           'bc', 'bpt', 'bpb', 'bmg', 'suc', 'slc', 'stc', 'uc', 'lc', 'tc',
           'scf', 'cf', 'jt', 'jg', 'ea', 'lb', 'sc', 'scx', 'NFKC_CF', 'FC_NFKC', 'InSC',
           'InPC', 'vo', 'blk']
_fieldmap = dict((x, i) for i, x in enumerate(_fields))

_property_aliases = {
    "Numeric_Value": "nv",
    "Bidi_Mirroring_Glyph": "bmg",
    "Bidi_Paired_Bracket": "bpb",
    "Case_Folding": "cf",
    "Decomposition_Mapping": "dm",
    "FC_NFKC_Closure": "FC_NFKC",
    "Lowercase_Mapping": "lc",
    "NFKC_Casefold": "NFKC_CF",
    "NFKC_Simple_Casefold": "NFKC_SCF",
    "Simple_Case_Folding": "scf",
    "Simple_Lowercase_Mapping": "slc",
    "Simple_Titlecase_Mapping": "stc",
    "Simple_Uppercase_Mapping": "suc",
    "Titlecase_Mapping": "tc",
    "Uppercase_Mapping": "uc",
    "ISO_Comment": "isc",
    "Jamo_Short_Name": "JSN",
    "Name": "na",
    "Script_Extensions": "scx",
    "Age": "age",
    "Block": "blk",
    "Script": "sc",
    "Bidi_Class": "bc",
    "Bidi_Paired_Bracket_Type": "bpt",
    "Canonical_Combining_Class": "ccc",
    "Decomposition_Type": "dt",
    "East_Asian_Width": "ea",
    "General_Category": "gc",
    "Grapheme_Cluster_Break": "GCB",
    "Hangul_Syllable_Type": "hst",
    "Indic_Conjunct_Break": "InCB",
    "Indic_Positional_Category": "InPC",
    "Indic_Syllabic_Category": "InSC",
    "Joining_Group": "jg",
    "Joining_Type": "jt",
    "Line_Break": "lb",
    "NFC_Quick_Check": "NFC_QC",
    "NFD_Quick_Check": "NFD_QC",
    "NFKC_Quick_Check": "NFKC_QC",
    "NFKD_Quick_Check": "NFKD_QC",
    "Numeric_Type": "nt",
    "Sentence_Break": "SB",
    "Vertical_Orientation": "vo",
    "Word_Break": "WB",
    "ASCII_Hex_Digit": "AHex",
    "Alphabetic": "Alpha",
    "Bidi_Control": "Bidi_C",
    "Bidi_Mirrored": "Bidi_M",
    "Cased": "Cased",
    "Composition_Exclusion": "CE",
    "Case_Ignorable": "CI",
    "Full_Composition_Exclusion": "Comp_Ex",
    "Changes_When_Casefolded": "CWCF",
    "Changes_When_Casemapped": "CWCM",
    "Changes_When_NFKC_Casefolded": "CWKCF",
    "Changes_When_Lowercased": "CWL",
    "Changes_When_Titlecased": "CWT",
    "Changes_When_Uppercased": "CWU",
    "Dash": "Dash",
    "Deprecated": "Dep",
    "Default_Ignorable_Code_Point": "DI",
    "Diacritic": "Dia",
    "Extender": "Ext",
    "Grapheme_Base": "Gr_Base",
    "Grapheme_Extend": "Gr_Ext",
    "Grapheme_Link": "Gr_Link",
    "Hex_Digit": "Hex",
    "Hyphen": "Hyphen",
    "ID_Continue": "IDC",
    "Ideographic": "Ideo",
    "ID_Start": "IDS",
    "IDS_Binary_Operator": "IDSB",
    "IDS_Trinary_Operator": "IDST",
    "IDS_Unary_Operator": "IDSU",
    "Join_Control": "Join_C",
    "Logical_Order_Exception": "LOE",
    "Lowercase": "Lower",
    "Math": "Math",
    "Modifier_Combining_Mark": "MCM",
    "Noncharacter_Code_Point": "NChar",
    "Other_Alphabetic": "OAlpha",
    "Other_Default_Ignorable_Code_Point": "ODI",
    "Other_Grapheme_Extend": "OGr_Ext",
    "Other_ID_Continue": "OIDC",
    "Other_ID_Start": "OIDS",
    "Other_Lowercase": "OLower",
    "Other_Math": "OMath",
    "Other_Uppercase": "OUpper",
    "Pattern_Syntax": "Pat_Syn",
    "Pattern_White_Space": "Pat_WS",
    "Prepended_Concatenation_Mark": "PCM",
    "Quotation_Mark": "QMark",
    "Radical": "Radical",
    "Regional_Indicator": "RI",
    "Soft_Dotted": "SD",
    "Sentence_Terminal": "STerm",
    "Terminal_Punctuation": "Term",
    "Unified_Ideograph": "UIdeo",
    "Uppercase": "Upper",
    "Variation_Selector": "VS",
    "White_Space": "WSpace",
    "XID_Continue": "XIDC",
    "XID_Start": "XIDS",
    "Expands_On_NFC": "XO_NFC",
    "Expands_On_NFD": "XO_NFD",
    "Expands_On_NFKC": "XO_NFKC",
    "Expands_On_NFKD": "XO_NFKD",
}

_property_extras = {
    # -- hand-added informal aliases --
    "category": "gc",
}

# normalized (lowercased) name -> canonical key, built once from the
# canonical field names, the binary field names, and _property_aliases
_key_lookup = {}
for _k in _fields:
    if _k != '_b0':
        _key_lookup[_k.lower()] = _k
for _k in _binmap:
    _key_lookup[_k.lower()] = _k
for _alias, _canon in _property_aliases.items():
    _key_lookup[_alias.lower()] = _canon
for _alias, _canon in _property_extras.items():
    _key_lookup[_alias.lower()] = _canon

_fieldnames = {v:k.replace("_", " ") for k, v in _property_aliases.items()}

def _rebuild_ucd(items, enums):
    obj = list.__new__(UCD)
    obj.extend(items)
    obj.enums = enums
    return obj

def resolve_key(name):
    """ Translate the property name through the property aliases
    using fuzzy matching. Return the name itself on failure or
    ambiguous match. """
    normalized = name.strip().lower().replace(" ", "_")
    if normalized in _key_lookup:
        return _key_lookup[normalized]
    matches = {v for k, v in _key_lookup.items() if k.startswith(normalized)}
    return matches.pop() if len(matches) == 1 else name


class _Codepoint(tuple):
    """Represents the complete information for a particular codepoint"""
    def __new__(cls, *a, **kw):
        if len(a) == 1 and len(a[0]) == len(_fields):
            return tuple.__new__(cls, a[0])
        if len(kw):
            a = [0] * len(_fields)
            for k, v in kw.items():
                if k in _binmap and v == "Y":
                    #i = _fieldmap['_b'+str(_binmap[k][0])]
                    a[_fieldmap['_b0']] += (1 << _binmap[k])
                elif k in _fieldmap:
                    a[_fieldmap[k]] = v
        return tuple.__new__(cls, a)

    def __getitem__(self, key):
        if key in _fieldmap and key != "_b0":
            return super(_Codepoint, self).__getitem__(_fieldmap[key])
        elif key in _binmap:
            return True if (super(_Codepoint, self).__getitem__(_fieldmap['_b0']) >> _binmap[key]) & 1 else False
        else:
            raise KeyError("Unknown key: {}".format(key))

    def __contains__(self, key):
        return key in _fieldmap or key in _binmap

    def asdict(self, enums):
        ''' Returns a dictionary with nice keys and nice values '''
        res = {}
        for k, v in _fieldmap.items():
            val = super().__getitem__(v)
            if k == "_b0":
                for bk, bv in _binmap.items():
                    if (val >> bv) & 1 != 0:
                        res[bk] = True
            elif val:
                res[_fieldnames[k]] = enums[k][val] if k in enums else val
        return res


class UCD(list):
    _remote_url = "http://www.unicode.org/Public/latest/ucdxml/ucd.all.flat.zip"

    def __new__(cls, localfile=None, cache_period=30):
        if localfile is None:
            if cls.test_update(cache_period):
                return cls.force_update()
            localfile = cls._cache_path()
        if not os.path.exists(localfile):
            res = list.__new__(cls)
        elif localfile.endswith(".bz2"):
            with bz2.open(localfile, "rb") as inf:
                res = pickle.load(inf)
        elif localfile.endswith(".pickle"):
            with open(localfile, "rb") as inf:
                res = pickle.load(inf)
        else:
            res = list.__new__(cls)
        return res

    def __init__(self, localfile=None):
        if localfile is None:
            return
        elif localfile.endswith(".xml"):
            with open(localfile) as inf:
                enums = self._preproc(inf)
                inf.seek(0)
                self._loadxml(inf, enums=enums)
        elif localfile.endswith('.zip'):
            with zipfile.ZipFile(localfile, 'r') as z:
                firstf = z.namelist()[0]
                with z.open(firstf) as inf:
                    enums = self._preproc(inf)
                with z.open(firstf) as inf:
                    self._loadxml(inf, enums=enums)

    def __reduce__(self):
        return (_rebuild_ucd, (list(self), self.enums))

    def save(self, localfile):
        if localfile.endswith(".bz2"):
            with bz2.open(localfile, "wb") as outf:
                pickle.dump(self, outf)
        elif localfile.endswith(".pickle"):
            with open(localfile, "wb") as outf:
                pickle.dump(self, outf)
        else:
            raise ValueError("localfile must end in .bz2 or .pickle")

    @classmethod
    def _cache_path(cls):
        cache_dir = platformdirs.user_cache_dir("python_ucd")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "ucdata_pickle.bz2")

    @classmethod
    def test_update(cls, cache_period):
        """cache_period is in days. Returns True if the cache needs
        updating. If the cache file is younger than cache_period, assumes
        it's current (no network call). Otherwise does a HEAD request; if
        the remote isn't newer, touches the cache file's mtime to reset
        the clock and returns False."""
        cache_path = cls._cache_path()
        if not os.path.exists(cache_path):
            return True

        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path), tz=timezone.utc)
        if datetime.now(timezone.utc) - mtime < timedelta(days=cache_period):
            return False

        req = urllib.request.Request(cls._remote_url, method="HEAD")
        try:
            with urllib.request.urlopen(req) as resp:
                remote_lm = resp.headers.get("Last-Modified")
        except urllib.error.URLError:
            return False

        if remote_lm and parsedate_to_datetime(remote_lm) > mtime:
            return True

        os.utime(cache_path, None)
        return False

    @classmethod
    def force_update(cls):
        """Unconditionally fetch the remote zip, parse it into a fresh
        instance, and save it to the pickle cache."""
        with urllib.request.urlopen(cls._remote_url) as resp:
            data = resp.read()
        obj = list.__new__(cls)
        obj.enums = {}
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            firstf = z.namelist()[0]
            with z.open(firstf) as inf:
                enums = obj._preproc(inf)
            with z.open(firstf) as inf:
                obj._loadxml(inf, enums=enums)
        obj.save(cls._cache_path())
        return obj

    def _loadxml(self, fh, enums=None):
        if enums is None:
            enums = {}
            for k, v in self.enums.items():
                enums[k] = {x: i for i, x in enumerate(v)}
        for (ev, e) in et.iterparse(fh, events=['start']):
            if ev == 'start' and e.tag.endswith('char'):
                d = dict(e.attrib)
                if 'cp' in d:
                    firstcp = d.pop('cp')
                    lastcp = firstcp
                elif 'first-cp' in d:
                    firstcp = d.pop('first-cp')
                    lastcp = d.pop('last-cp')
                for n in _cpfields:
                    if n not in d or d[n] == "#":
                        d[n] = ""
                    d[n] = "".join(chr(int(x, 16)) for x in d[n].split())
                for n, v in enums.items():
                    if n in d:
                        try:
                            d[n] = v[d[n]]
                        except KeyError:
                            # add new allowed value to field:
                            i = len(self.enums[n])
                            self.enums[n].append(d[n])
                            enums[n][d[n]] = i
                            d[n] = i
                dat = _Codepoint(**d)
                firsti = int(firstcp, 16)
                lasti = int(lastcp, 16)
                if lasti >= len(self):
                    self.extend([None] * (lasti - len(self) + 1))
                for i in range(firsti, lasti+1):
                    self[i] = dat
        return self

    def _preproc(self, filename):
        enums = {}
        for e in _enumfieldnames.split():
            enums[e] = {}
        for (ev, e) in et.iterparse(filename, events=['start']):
            if e.tag.endswith('char'):
                for n, v in enums.items():
                    val = e.get(n, None)
                    if val is not None:
                        v.setdefault(val, len(v))
        self.enums = {}
        for k, v in enums.items():
            self.enums[k] = sorted(v.keys(), key=lambda x:v[x])
        return enums

    def loadxml(self, filename):
        """ Loads an additional UCDXML-formatted data file; commonly used for pipeline
            characters prior to inclusion in a Unicode release """
        with open(filename) as inf:
                self._loadxml(inf)
        return self

    def get(self, cp, key):
        """ Looks up a codepoint and returns the value for a given key. This
            includes mapping enums back to their strings"""
        v = self[cp]
        if v is None:
            raise KeyError("Undefined codepoint {:04X}".format(cp))
        key = resolve_key(key)
        if key not in v:
            raise KeyError(f"Unknown or ambiguous property: {key}")
        if key == "na":
            return v[key].replace("#", "{:04X}".format(cp))
        return self.enumstr(key, v[key])

    def get_info(self, cp):
        """ Returns a dictionary of nicely named properties and values where
            the value is set """
        v = self[cp]
        res = v.asdict(self.enums)
        return res

    def enumstr(self, key, v):
        """ Returns the string for an enum value given enum name and value """
        key = resolve_key(key)
        if key not in self.enums:
            raise KeyError(f"Unknown or ambiguous property: {key}")
        if key in self.enums:
            m = self.enums[key]
            return m[v] if v < len(m) else v
        return v

    def findall(self, key, val):
        """ Returns a list of all the codepoints whose key value is value. Value
            may be an enum name """
        key = resolve_key(key)
        if key in self.enums:
            try:
                enumval = self.enums[key].index(val)
            except ValueError:
                return []
        else:
            enumval = val
        return [cp for cp in range(len(self)) if self[cp] is not None and key in self[cp] and self[cp][key] == enumval]


local_ucd = None
def _get_local_ucd():
    global local_ucd
    if local_ucd is None:
        local_ucd = UCD()
    return local_ucd

def loadxml(filename):
    """ Ensures the global ucd is loaded into memory """
    _get_local_ucd().loadxml(filename)

def get_ucd(cp, key):
    """ Given codepoint and key, returns the property value. Key may be the
        identifier or a partial full name from ucd/PropertyAliases.xml """
    return _get_local_ucd().get(cp, key)

def get_info(cp):
    """ Given a codepoint returns a nice dictionary of properties """
    return _get_local_ucd().get_info(cp)

def find_ucd(key, val):
    """ Returns a list of codepoints whose property key is the given val """
    return _get_local_ucd().findall(key, val)

def get_enums(key):
    """ Returns a list of property value names, suitable for passing to find_ucd,
        for a given property key """
    u = _get_local_ucd()
    key = resolve_key(key)
    if key in u.enums:
        return u.enums[key]
    else:
        return []

if __name__ == '__main__':
    import sys
    from palaso.unicode.ucd import get_ucd

    if len(sys.argv) == 1:
        print(get_ucd(0x0041, "sc"))
        print(get_ucd(0x3400, "na"))
        # print(get_ucd(0x0301, "MCM"))
        print(["{:04X}".format(cp) for cp in find_ucd("InSC", "Invisible_Stacker")])
        print(["{:04X}".format(cp) for cp in find_ucd("MCM", True)])
    else:
        try:
            cp = int(sys.argv[1], 16)
        except ValueError:
            cp = None
        if cp is not None:
            if len(sys.argv) == 2:
                pprint.pprint(get_info(cp))
            if len(sys.argv) == 3:
                print(get_ucd(cp, sys.argv[2]))
        elif len(sys.argv) == 3:
            print(" ".join("%04X" % x for x in find_ucd(sys.argv[1], sys.argv[2])))
        elif len(sys.argv) == 2:
            print("\n".join(get_enums(sys.argv[1])))

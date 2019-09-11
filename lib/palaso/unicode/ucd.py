#!/usr/bin/python3

"""ucd

This module contains the basic ucd information for every character in Unicode.

SYNOPSIS:

    from palaso.unicode.ucd import UCD
    ucdata = UCD()
    print(ucdata.get(0x0041, 'scx'))
"""

import array, pickle
import xml.etree.ElementTree as et
import os, bz2, zipfile


# Unicode data xml attributes
_binfieldnames = """AHex Alpha Bidi_C Bidi_M Cased CE CI Comp_Ex CWCF CWCM CWKCF CWL CWT CWU
    Dash Dep DI Dia Ext Gr_Base Gr_Ext Gr_Link Hex Hyphen IDC Ideo IDS IDSB
    IDST Join_C LOE Lower Math NChar OAlpha ODI OGr_Ext OIDC OIDS OLower OMath
    OUpper Pat_Syn Pat_WS PCM QMark Radical RI SD STerm Term UIdeo Upper VS
    WSpace XIDC XIDS XO_NFC XO_NFD XO_NFKC XO_NFKD"""
_binmap = dict((x, i) for i, x in enumerate(_binfieldnames.split()))
_enumfieldnames = """age blk sc scx bc bpt ccc dt ea gc GCB hst InPC InSC jg jt lb
    NFC_QC NFD_QC NFKC_QC NFKD_QC nt SB vo WB"""
_cpfieldnames = """cf dm FC_NFKC lc NFKC_CF scf slc stc suc tc uc bmg bpb"""
_cpfields = set(_cpfieldnames.split())
_fields = ['_b0', 'age', 'name', 'JSN', 'gc', 'ccc', 'dt', 'dm', 'nt', 'nv',
           'bc', 'bpt', 'bpb', 'bmg', 'suc', 'slc', 'stc', 'uc', 'lc', 'tc',
           'scf', 'cf', 'jt', 'jg', 'ea', 'lb', 'sc', 'scx', 'NFKC_CF', 'FC_NFKC', 'InSC',
           'InPC', 'vo', 'blk']
_fieldmap = dict((x, i) for i, x in enumerate(_fields))

class Codepoint(tuple):
    """Represents the complete information for a particular codepoint"""
    def __new__(cls, *a, **kw):
        if len(a) == 1 and len(a[0]) == len(_fields):
            return tuple.__new__(cls, a[0])
        if len(kw):
            a = [0] * len(_fields)
            for k, v in kw.items():
                if k in _binmap and v == "Y":
                    #i = _fieldmap['_b'+str(_binmap[k][0])]
                    i = _fieldmap['_b0']
                    a[i] = a[i] + (1 << _binmap[k])
                elif k in _fieldmap:
                    a[_fieldmap[k]] = v
        return tuple.__new__(cls, a)

    def __getitem__(self, key):
        if key in _fieldmap:
            return super(Codepoint, self).__getitem__(_fieldmap[key])
        elif key in _binmap:
            return (super(Codepoint, self).__getitem__('_b'+str(_binmap[k][0])) >> _binmap[k][1]) & 1
        else:
            return None

class UCD(list):

    _singleton = None
    def __new__(cls, filename=None):
        if cls._singleton is not None:
            return cls._singleton
        else:
            cls._singleton = list.__new__(cls)
        if filename is None:
            localfile = os.path.join(os.path.dirname(__file__), "ucdata_pickle.bz2")
        else:
            localfile = filename
        if localfile.endswith(".bz2") and os.path.exists(localfile):
            with bz2.open(localfile, "rb") as inf:
                return pickle.load(inf)
        elif localfile.endswith(".pickle"):
            with open(localfile, "rb") as inf:
                return pickle.load(inf)
        if localfile.endswith(".xml"):
            with open(localfile) as inf:
                return cls._singleton._loadxml(inf)
        elif localfile.endswith('.zip'):
            with zipfile.ZipFile(localfile, 'r') as z:
                firstf = z.namelist()[0]
                with z.open(firstf) as inf:
                    return cls._singleton._loadxml(inf)

    def __init__(self, filename=None):
        pass

    def _loadxml(self, fh):
        enums = self._preproc(fh)
        fh.seek(0)
        for (ev, e) in et.iterparse(fh, events=['start']):
            if ev == 'start' and e.tag.endswith('char'):
                d = dict(e.attrib)
                if 'cp' in d:
                    firstcp = d.pop('cp')
                    lastcp = firstcp
                elif 'first-cp' in d:
                    firstcp = d.pop('first-cp')
                    lastcp = d.pop('last-cp')
                for n, v in enums.items():
                    if n in d:
                        d[n] = v[d[n]]
                for n in _cpfields:
                    if d[n] == "#":
                        d[n] = ""
                    d[n] = "".join(chr(int(x, 16)) for x in d[n].split())
                dat = Codepoint(**d)
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

    def get(self, cp, key):
        """ Looks up a codepoint and returns the value for a given key. This
            includes mapping enums back to their strings"""
        v = self[cp]
        return self.enumstr(key, v[key]) if v is not None else None

    def enumstr(self, key, v):
        """ Returns the string for an enum value given enum name and value """
        if key in self.enums:
            m = self.enums[key]
            return m[v] if v < len(m) else v
        return v


if __name__ == '__main__':
    import sys, pickle
    from palaso.unicode.ucd import UCD
                
    if len(sys.argv) < 3:
        ucdata = UCD()
        print(ucdata.get(0x0041, "sc"))
    else:
        ucdata = UCD(filename=sys.argv[1])
        with open(sys.argv[2], "wb") as outf:
            pickle.dump(ucdata, outf)

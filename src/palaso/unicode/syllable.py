
import re, inspect
from itertools import groupby
from palaso.unicode.ucd import get_ucd
import unicodedata      # sigh. Need this for normalize

def tolist(l) :
    """ convert space separated list into an actual list, and normalize on the way"""
    res = unicodedata.normalize('NFD', l).split()
    return res

def intersperse(main, *extras) :
    """Takes a list of strings. Intersperse substrings from extras into the clusters of the string
        such that the substrings are ordered according to normalization rules.
        extras is list of tuples (str, combiningorder)"""
    def isbase(char) :
        return get_ucd(char, 'gc').startswith("L")

    res = []
    extras = list(extras)
    #extras.sort(cmp=lambda a,b : cmp(a[1], b[1]))
    for m in main :
        groups = []
        base = ""
        for v in groupby(m, lambda x:get_ucd(x, 'gc')[0]) :
            k = v[0]
            d = "".join(v[1])
            if k == "L" :
                if base : groups.extend((base, ""))
                for c in d[:-1] :
                    groups.extend((c, ""))
                base = d[-1]
            elif k == "M" :
                base = base + d
            else :
                groups.extend((base, d))
                base = ""
        if base : groups.extend((base, ""))
        # groups is now 2n list where list[n] is base+dias, list[n+1] is punc separators
        for i in range(0, len(groups), 2) :
            dias = list(groups[i][1:])
            orders = [get_ucd(c, 'ccc') for c in dias]
            bases = list(zip(dias, orders))
            new = sorted(bases + extras, cmp=lambda a,b: cmp(a[1], b[1]))
            results = list(zip(*new))
            groups[i] = "".join([groups[i][0]] + list(results[0]))
        res.append("".join(groups))
    return res

def e(x) :
    """Expand {var} in string, if var is a string make it a regexp alternates"""
    myglobals = inspect.stack()[1][0].f_globals
    def unpack(m) :
        v = myglobals[m.group(1)]
        if isinstance(v, (tuple, list)):
            return "(?:" + "|".join(sorted(v, key=lambda x:(-len(x), x))) + ")"
        else :
            return v
    res = re.sub(r'\{([a-z_]+)\}', unpack, x)
    return res


class Reunpack(object) :
    ''' Turns regex groups into attributes for easier handling '''

    def __init__(self, reg, comps, special=""):
        self._caps = {}                             # which groups are capital/title cased
        self.sep = comps[0]                         # initial content is prematched material
        self.special = special                      # pass on the special string if any
        if special != "":                           # if there is a special, no syllable to analyse
            return
        self._caps['sep'] = 0                       # don't do capitals on prematched material
        for m, i in reg.groupindex.items():         # get name to index mapping
            if i >= len(comps) or not comps[i]:     # nothing there so short circuit
                setattr(self, m, "")
                continue
            setattr(self, m, comps[i].lower())      # store everything lowercase
            self._caps[m] = 0                       # default is lowercase
            for c in comps[i] :                                     # iterate chars
                if c.isupper() : self._caps[m] = 2                  # while uppercase then 2 = All caps
                elif c.islower() :                                  # hit lowercase
                    self._caps[m] = (1 if self._caps[m] else 0)         # all caps -> title, otherwise lower
                    break                                               # and we are done

    def join(self, *names):
        ''' Given a list of attributes, assemble an output string with casing '''
        res = []                                    # quicker to assemble list and join
        for n in names :
            s = getattr(self, n, "")                # get the string
            if s :                                  # no need to do anything if it's empty
                c = self._caps.get(n, 0)            # get the caps state for this attribute
                if c == 1 :                         # take appropriate action on the string
                    s = s.capitalize()
                elif c == 2 :
                    s = s.upper()
                res.append(s)                       # append to output
        return "".join(res)                        # list -> string


class ReSplit(object) :
    def __init__(self, regstr, specials={}) :
        self.re = re.compile(r"(?P<all>" + regstr + ")", re.I | re.X)   # group whole regex
        self.specials = specials                                        # dict of direct mappings
        # create regex input match of special words sorted longest first
        self.specialsre = re.compile(r"("+"|".join(sorted(specials.keys(), key=lambda s:(-len(s), s))) + ")")

    def splits(self, txt):
        pos = 0
        while pos < len(txt):                               # walk the text
            m = self.re.search(txt, pos=pos)                # do syllable analysis
            n = self.specialsre.search(txt, pos=pos)        # find special words
            if not m and (not n or not len(self.specials)):           # no matches
                self.final = txt[pos:]                      #   then finish
                return
            if n and len(self.specials) and n.start() <= m.start():    # if special came first
                yield Reunpack(self.re, [txt[pos:n.start()]], self.specials[n.group(1)])
                pos = n.end()
            else:                                           # syllable came first
                s = [txt[pos:m.start()]] + [m.group(i+1) for i in range(self.re.groups)]
                yield Reunpack(self.re, s)
                pos = m.end()
        self.final = ""                                     # no trailing unprocessed text



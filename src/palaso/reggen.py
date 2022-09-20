#!/usr/bin/python3

"""Module to generate strings from a regexp"""

import sre_parse
import sre_compile
from random import randrange, choice


class ExpandingList(list):
    def __init__(self, *p, **kw):
        if 'default' in kw:
            self.default = kw['default']
            del kw['default']
        else:
            self.default = None
        list.__init__(self, *p, **kw)

    def __setitem__(self, i, val):
        while i >= len(self):
            self.append(self.default)
        list.__setitem__(self, i, val)


class MatchObj:
    def __init__(self, pattern, str):
        self.string = str
        self.pattern = pattern
        self.startpos = ExpandingList([0], default=0)
        self.endpos = ExpandingList([0], default=0)
        self.patient = -1

    def __copy__(self):
        res = MatchObj(self.pattern, self.string)
        res.startpos = ExpandingList(self.startpos, default=0)
        res.endpos = ExpandingList(self.endpos, default=0)
        return res

    def copy(self):
        return self.__copy__()

    def end(self, groupid=0):
        if groupid:
            if self.endpos[groupid] > self.startpos[groupid]:
                return self.endpos[groupid]
            else:
                return self.patient
        else:
            return len(self.string) - 1

    def start(self, groupid=0):
        if groupid:
            if self.endpos[groupid] > self.startpos[groupid]:
                return self.startpos[groupid]
            else:
                return self.patient
        else:
            return 0

    def span(self, groupid=0):
        if groupid:
            if self.endpos[groupid] > self.startpos[groupid]:
                return (self.startpos[groupid], self.endpos[groupid])
            else:
                return (self.patient, self.patient)
        else:
            return (0, len(self.string) - 1)
        
    def group(self, groupid=0, *groupids):
        if len(groupids):
            res = []
            for g in ([groupid] + list(groupids)):
                res.append(self.resolve_group(g))
            return tuple(res)
        else:
            return self.resolve_group(groupid)

    def resolve_group(self, group):
        if type(group) != int:
            if group in self.pattern.pattern.groupdict:
                group = self.pattern.pattern.groupdict[group]
            else:
                return None
        if group == 0:
            return self.string
        elif group is None:
            return None
        if not self.patient and group >= len(self.endpos): 
            return ''
        return self.string[self.startpos[group]:self.endpos[group]]

    def groups(self, default=None):
        res = []
        for i in range(1, self.pattern.pattern.groups):
            if self.startpos[i] is None:
                res.append(default)
            else:
                res.append(self.string[self.startpos[i]:self.endpos[i]])
        return tuple(res)

    def groupdict(self, default=None):
        res = {}
        for k, v in self.pattern.pattern.groupdict:
            if self.startpos[v-1] is None:
                res[k] = default
            else:
                res[k] = self.string[self.startpos[v-1]:self.endpos[v-1]]
        return res

    def expand(self, template):
        template = sre_parse.parse_template(template, self.pattern)
        return sre_parse.expand_template(template, self)


def _iterate(pattern, data, match):
    """ Takes a pattern list from the parser and returns a list of match
        objects that corresponds to the strings that the pattern reflects,
        including group extraction"""
    for s in _rec_proc(pattern, data, 0, match):
        yield s


def _rec_proc(pattern, data, index, match):
    for s in _proc(pattern, data[index], match):
        if len(data) > index + 1:
            for s1 in _rec_proc(pattern, data, index + 1, s):
                yield s1
        else:
            yield s


def _proc(pattern, data, match):
    op = str(data[0])
    if op == 'LITERAL':        # ('literal', charcode)
        s = match.copy()
        s.string += chr(data[1])
        yield s
    elif op == 'MAX_REPEAT':   # ('max_repeat', (min, max, [contents]))
        if pattern.mode == 'random':
            subdata = [data[1][2][0]] * randrange(data[1][0], data[1][1])
        elif pattern.mode == 'first':
            subdata = [data[1][2][0]] * data[1][0]
        else:
            subdata = [data[1][2][0]] * data[1][1]
            for _ in range(data[1][1] - data[1][0], 0, -1):
                for s in _rec_proc(pattern, subdata, 0, match):
                    yield s
                del subdata[-1]
        if len(subdata) > 0:
            for s in _rec_proc(pattern, subdata, 0, match):
                yield s
        else:
            yield match
    elif op == 'SUBPATTERN':   # ('subpattern', (index | None, [contents]))
        if data[1][0]:
            match.startpos[data[1][0]] = len(match.string)
        for s in _iterate(pattern, data[1][3], match):
            if data[1][0]:
                s.endpos[data[1][0]] = len(s.string)
            yield s
    elif op == 'IN':           # ('in', [contents])
        allchars = []
        for r in data[1]:
            allchars.extend([c for c in _chars(r)])
        if pattern.mode == 'first':
            dochars = [allchars[0]]
        elif pattern.mode == 'random':
            dochars = [choice(allchars)]
        else:
            dochars = allchars
        for c in dochars:
            s = match.copy()
            s.string += chr(c)
            yield s
    elif op == 'BRANCH':  # ('branch', (None, [[contents1], [contents2], ...]))
        if pattern.mode == 'first':
            s = [data[1][1][0]]
        elif pattern.mode == 'random':
            s = [choice(data[1][1])]
        else:
            s = data[1][1]
        for d in s:
            for c in _iterate(pattern, s, match):
                yield c
    else:
        raise SyntaxError("Unprocessable regular expression operator: %s" % op)


def _chars(rdata):
    op = str(rdata[0])
    if op == 'RANGE':      # ('range', (first, last))
        for c in range(rdata[1][0], rdata[1][1] + 1):
            yield c
    elif op == 'LITERAL':  # ('literal', char)
        yield rdata[1]
    else:
        raise SyntaxError("Unrecognised character group operator: " + op)


def geom(a, x):
    if a == 1:
        return x
    return a * (1 - a ** x) / (1 - a)


def _len_proc(data):
    res = 1
    depth = 0
    for d in data:
        (r, dp) = _len(d)
        res *= r
        depth += dp
    return (res, depth)


def _len(data):
    op = str(data[0])
    if op == 'LITERAL':
        return (1, 1)
    elif op == 'MAX_REPEAT':
        minc = data[1][0]
        maxc = data[1][1]
        # mult = maxc - minc
        (res, depth) = _len_proc(data[1][2])
        if minc == 0:
            return (geom(res, maxc) + 1, depth * maxc)
        else:
            return (geom(res, maxc) - geom(res, minc), depth * maxc)
    elif op == 'SUBPATTERN':
        return _len_proc(data[1][3])
    elif op == 'IN':
        res = 0
        for r in data[1]:
            inop = str(r[0])
            if inop == 'RANGE':
                res += r[1][1] - r[1][0] + 1
            elif inop == 'LITERAL':
                res += 1
            else:
                raise SyntaxError(
                    "Unrecognised character group operator: " + inop)
        return (res, 1)
    elif op == 'BRANCH':
        res = 0
        depth = 0
        for r in data[1][1]:
            (l, d) = _len_proc(r)
            res += l
            if d > depth:
                depth = d
        return (res, depth)
    else:
        raise SyntaxError(
            "Unprocessable regular expression operator: %s" % str(op))


def expand_sub(string, template, debug=0, mode='all'):
    """ Given a regular expression and a replacement string, generate
        expansions of the regular expression and for each one return it and
        its transformation as applied by the replacement string.

        string: regular expression to expand
        template: transformation to apply to each regular expression
        mode: can take 3 values
            all: return all possible shortest strings that the regular
                 expression would match
            first: return the first string that all would return
            random: return one random string that the regular expression would match
    """
    pattern = sre_parse.parse(string, flags=sre_parse.SRE_FLAG_VERBOSE)
    pattern.mode = mode
    template = sre_parse.parse_template(template, sre_compile.compile(pattern))
    if debug:
        print(pattern)
        print(template)
    for s in _iterate(pattern, pattern.data, MatchObj(pattern, "")):
        s.patient = 0
        yield (s.string, sre_parse.expand_template(template, s))


def invert(string, mode='all'):
    """ Given a regular expression generate expansions of the regular expression and
        return them.

        string: regular expression to expand
        mode: can take 3 values
            all: return all possible shortest strings that the regular expression
                    would match
            first: return the first string that all would return
            random: return one random string that the regular expression would match
    """
    pattern = sre_parse.parse(string, flags=sre_parse.SRE_FLAG_VERBOSE)
    pattern.mode = mode
    for s in _iterate(pattern, pattern.data, MatchObj(pattern, "")):
        yield s.string


def inversionlength(string):
    """ Given a regular expression, returns the number of strings and maximum string length
        that the regular expression would generate if pass to invert(string, 'all')"""
    pattern = sre_parse.parse(string, flags=sre_parse.SRE_FLAG_VERBOSE)
    return _len_proc(pattern.data)


def pprint(string):
    pattern = sre_parse.parse(string, flags=sre_parse.SRE_FLAG_VERBOSE)
    print(pattern.data)


if __name__ == "__main__":
    tests=[
        ('([ab])([cd])', r'\2\1'),
        (u'([\u1000-\u1003])([\u103C-\u103D]?)(\u102F?|\u1030)([\u1000-\u1003]\u103A)', r'\1\2\4\3'),
        ('(x([ab]|[cd]?))', r'\1')
    ]
    for t in tests:
        print("-" * 50)
        print(t[0] + "\t" + t[1])
        for s in expand_sub(t[0], t[1]):
            print(s[0] + "\t" + s[1])


"""Module to generate strings from a regexp"""

import sre_parse

class MatchObj :
    def __init__(self, pattern, str) :
        self.string = str
        self.pattern = pattern
        self.startpos = [0]
        self.endpos = [0]
    def __copy__(self) :
        res = MatchObj(self.pattern, self.string)
        res.startpos = self.startpos[:]
        res.endpos = self.endpos[:]
        return res
    def copy(self) :
        return self.__copy__()
    def end(groupid = 0) :
        if groupid :
            if self.endpos[groupid] > self.startpos[groupid] :
                return self.endpos[groupid]
            else :
                return -1
        else :
            return len(self.string) - 1
    def start(groupid = 0) :
        if groupid :
            if self.endpos[groupid] > self.startpos[groupid] :
                return self.startpos[groupid]
            else :
                return -1
        else :
            return 0
    def span(groupid = 0) :
        if groupid :
            if self.endpos[groupid] > self.startpos[groupid] :
                return (self.startpos[groupid], self.endpos[groupid])
            else :
                return (-1, -1)
        else :
            return (0, len(self.string) - 1)
    def group(self, groupid = 0, *groupids) :
        if len(groupids) :
            res = []
            for g in ([groupid] + groupids) :
                res.append(self.resolve_group(g))
            return tuple(res)
        else :
            return self.resolve_group(groupid)
    def resolve_group(self, group) :
        if type(group) != int :
            if self.pattern.pattern.groupdict.has_key(group) :
                group = self.pattern.pattern.groupdict[group]
            else :
                return None
        if group == 0 :
            return self.string
        elif group == None :
            return None
        return self.string[self.startpos[group]:self.endpos[group]]
    def groups(self, default = None) :
        res = []
        for i in range(1, self.pattern.pattern.groups) :
            if self.startpos[i] == None :
                res.append(default)
            else :
                res.append(self.string[self.startpos[i]:self.endpos[i]])
        return tuple(res)
    def groupdict(self, default = None) :
        res = {}
        for k,v in self.pattern.pattern.groupdict :
            if self.startpos[v-1] == None :
                res[k] = default
            else :
                res[k] = self.string[self.startpos[v-1]:self.endpos[v-1]]
        return res
    def expand(self, template) :
        template = sre_parse.parse_template(template, self.pattern)
        return sre_parse.expand_template(template, self)

def _iterate(pattern, data, match) :
    """ Takes a pattern list from the parser and returns a list of match objects that corresponds to the strings that the pattern reflects, including group extraction"""
    for s in _rec_proc(pattern, data, 0, match) :
        yield s

def _rec_proc(pattern, data, index, match) :
    for s in _proc(pattern, data[index], match) :
        if len(data) > index + 1 :
            for s1 in _rec_proc(pattern, data, index + 1, s) :
                yield s1
        else :
            yield s

def _proc(pattern, data, match) :
    op = data[0]
    if op == 'literal' :        # ('literal', charcode)
        match.string += unichr(data[1])
        yield match
    elif op == 'max_repeat' :   # ('max_repeat', (min, max, [contents]))
        if data[1][0] :
            subdata = data[1][2] * data[1][0]
        else :
            subdata = []
        if len(subdata) > 0 :
            for s in _rec_proc(pattern, subdata, 0, match) :
                yield s
        else :
            yield match
        for n in range(0, data[1][1] - data[1][0]) :
            subdata.extend(data[1][2])
            for s in _rec_proc(pattern, subdata, 0, match) :
                yield s
    elif op == 'subpattern' :   # ('subpattern', (index | None, [contents]))
        if data[1][0] :
            match.startpos.insert(data[1][0], len(match.string))
        for s in _iterate(pattern, data[1][1], match) :
            if data[1][0] :
                s.endpos.insert(data[1][0], len(s.string))
            yield s
    elif op == 'in' :           # ('in', [contents])
        for r in data[1] :
            for c in _chars(r) :
                s = match.copy()
                s.string += unichr(c)
                yield s
    elif op == 'branch' :       # ('branch', (None, [[contents1], [contents2], ...]))
        for d in data[1][1] :
            for s in _iterate(pattern, d, match) :
                yield s
    else :
        raise SyntaxError, "Unprocessable regular expression operator: " + op

def _chars(rdata) :
    op = rdata[0]
    if op == 'range' :      # ('range', (first, last))
        for c in xrange(rdata[1][0], rdata[1][1] + 1) :
            yield c
    elif op == 'literal' :  # ('literal', char)
        yield rdata[1]
    else :
        raise SyntaxError, "Unrecognised character group operator: " + op

def expand_sub(string, template) :
    pattern = sre_parse.parse(string)
    template = sre_parse.parse_template(template, pattern)
    for s in _iterate(pattern, pattern.data, MatchObj(pattern, "")) :
        yield (s.string, sre_parse.expand_template(template, s))
    
def invert(string) :
    pattern = sre_parse.parse(string)
    for s in _iterate(pattern, pattern.data, MatchObj(pattern, "")) :
        yield s.string

def test() :
    tests=[
        ('([ab])([cd])', r'\2\1'),
        (u'([\u1000-\u1003])([\u103C-\u103D]?)([\u102F\u1030])([\u1000-\u1003]\u103A)', r'\1\2\4\3')
    ]
    for t in tests :
        print "-" * 50
        print (t[0] + "\t" + t[1]).encode('utf-8')
        for s in expand_sub(t[0], t[1]) :
            print (s[0] + "\t" + s[1]).encode('utf-8')

if __name__ == "__main__" :
    test()

#!/usr/bin/python

import re, os
import itertools
from pprint import pformat
from palaso.contrib.funcparserlib.lexer import make_tokenizer, Token, LexerError
from palaso.contrib.funcparserlib.parser import (some, a, maybe, many, skip, finished, NoParseError)

keyrowmap = {
    "E" : "1234567890-=",
    "D" : "qwertyuiop[]",
    "C" : "asdfghjkl;'",
    "B" : "zxcvbnm,./",
    "_E" : "!@#$%^&*()_+",
    "_D" : "QWERTYUIOP{}",
    "_C" : 'ASDFGHJKL:"',
    "_B" : "ZXCVBNM<>?"
}

keymap = dict([(k, ("{}{:02d}".format(rk[-1], i+1), rk.startswith("_"))) 
                for rk, r in keyrowmap.items() for i, k in enumerate(r)])
keymap.update({ "|" : ("B00", True), "\\" : ("B00", False),
                "`" : ("E00", False), "~" : ("E00", True)})

def mapkey(tok):
    if isinstance(tok, VKey):
        return tok.getkey()
    else:
        k = keymap[tok]
        return (k[0], ("shift" if k[1] else ""))

class Rule(object):

    def __init__(self, toklist):
        p = toklist.index(u'+')
        self.before = toklist[p-1]
        self.match = toklist[p+1]
        self.output = toklist[p+2]

    def __repr__(self):
        return str(self.before) + " + " + repr(self.match) + " > " + str(self.output)

    def _apply(self, allStores, x, val):
        if isinstance(x, AnyIndex):
            if x.index < 0:
                return allStores[x.name].values[val]
            else:
                return allStores[x.name].values[val[x.index]]
        elif isinstance(x, DeadKey):
            return x.char
        else:
            return x

    def apply(self, allStores, vec):
        before = []
        for i, b in enumerate(self.before):
            before.append(self._apply(allStores, b, vec[i]))
        match = self._apply(allStores, self.match, vec[len(self.before)])
        out = []
        for o in self.output:
            if hasattr(o, '__len__') and isinstance(o[0], Token):
                if o[0].value.lower() == 'context':
                    out.append(before[o[1] - 1])
                elif o[0].value.lower() == 'outs':
                    out.extend(allStores[o[1].lower()].values)
            elif isinstance(o, Token):
                if o.value.lower() == 'context':
                    out.extend(before)
            else:
                out.append(self._apply(allStores, o, vec))
        return Rule((before, '+', match, out))

    def _len(self, allStores, x):
        if isinstance(x, AnyIndex):
            return len(allStores[x.name].values)
        else:
            return 1

    def itervec(self, allStores, vec = None, start = 0):
        vec = []
        for b in self.before:
            vec.append(range(self._len(allStores, b)))
        vec.append(range(self._len(allStores, self.match)))
        return itertools.product(*vec)

    def flatten(self, allStores):
        for v in self.itervec(allStores):
            yield self.apply(allStores, v)

class AnyIndex(object):
    def __init__(self, toklist):
        self.name = toklist[1].lower()
        if len(toklist) > 2:
            self.index = toklist[2] - 1
        else:
            self.index = -1

    def __repr__(self):
        if self.index < 0:
            return "any(" + self.name + ")"
        else:
            return "index(" + self.name + ", " + str(self.index) + ")"

class DeadKey(object):
    missing = 0xFDD0

    def __init__(self, toklist):
        self.number = toklist[1]
        self.char = unichr(self.missing)
        self.missing += 1

specialkeys = {
    "quote": "C11", "bkquote": "E00", "comma": "B08", "bksp": "bksp",
    "hyphen": "E11", "period": "B09", "slash": "B10", "colon": "C10",
    "equal": "E12", "lbrkt": "D11", "bkslash": "B00", "rbrkt": "D12",
}

class VKey(object):
    def __init__(self, toklist):
        self.modifiers = []
        for t in toklist:
            s = t.lower()
            mod = ""
            if s.startswith("r"):
                mod = "R"
                s = s[1:]
            elif s.startswith("l"):
                mod = "L"
                s = s[1:]
            elif s == 'altgr':
                s = s[:4]
                mod = "R"
            if s.startswith("k_"):
                self.key = s[2:]
            else:
                self.modifiers += [s + mod]

    def getkey(self):
        if self.key in keymap:
            k = keymap[self.key][0]
        elif self.key in specialkeys:
            k = specialkeys[self.key]
        else:
            k = self.key
        m = "+".join(sorted(self.modifiers))
        return (k, m)

    def __str__(self):
        r = getkey(self)
        return "{} {}".format(r[1], r[0])

    def __repr__(self):
        return "[" + " ".join(self.modifiers + [self.key]) + "]"

class Store(object):

    def __init__(self, toklist):
        self.name = toklist[1].lower()
        self.seq = toklist[2]
        self.values = None

    def __repr__(self):
        return "store " + self.name + " " + \
                (str(self.values) if self.values is not None else str(self.seq))

    def flatten(self):
        if self.values is not None:
            return
        self.values = []
        for s in self.seq:
            if isinstance(s[0], Token):
                if s[0].value.lower() == 'outs':
                    sub = self.allStores[s[1].lower()]
                    sub.flatten()
                    self.values.extend(sub.values)
            else:
                self.values.extend(s)

def get_num(s):
    try:
        return int(s)
    except:
        return float(s)

class Parser(object):

    def __init__(self, s, debug=False):
        self.allRules = { "": [] }
        self.current_group = ""
        self.begins = {}
        self.allStores = {}
        self.allHeaders = {}
        seq = self.tokenize(s)
        if debug:
            print(seq)
        self.tree = self.parse(seq)

    def tokenize(self, text):
        lexer_specs = [
            ('SPACE', (r'(\\\r?\n|[ \t])+',re.MULTILINE)),
            ('COMMENT', (r'c\s+[^\n]*',)),
            ('NL', (r'\r?\n',re.MULTILINE)),
            ('KEYWORD', (r'any|index|store|outs|group|begin|use|beep|deadkey|dk|context|'
                          'if|match|nomatch|notany|return|reset|save|set|nul', re.I)),
            ('USINGKEYS', (r'using\s*keys', re.I)),
            ('HEADER', (r'name|hotkey|baselayout|bitmap|bitmaps|caps always off|caps on only|'
                         'shift frees caps|copyright|language|layer|layout|message|platform', re.I)),
            ('HEADERN', (r'version', re.I)),
            ('OP', (r'[(),\[\]>=]',)),
            ('STRING', (r'(["\']).*?\1',)),
            ('CHAR', (r'([uU]\+[0-9a-fA-F]{4,6})|([dD][0-9]+)',)),
            ('PLUS', (r'\+',)),
            ('NAME', (r'[A-Za-z&][A-Za-z0-9_]*',)),
            ('NUMBER', (r'[0-9]+(\.[0-9]+)?',)),
        ]
        useless = ['SPACE', 'COMMENT']
        t = make_tokenizer(lexer_specs)
        res = []
        blank = True
        for i, x in enumerate(t(text)):
            if x.type in useless:
                continue
            if blank and x.type == 'NL':
                continue
            blank = x.type == 'NL'
            res.append(x)
        return res

    def make_store(self, seq):
        s = Store(seq)
        if not s.name.startswith("&"):
            self.allStores[s.name] = s
        else:
            self.allHeaders[s.name] = s
        return s

    def set_group(self, seq):
        grp = seq[1]
        self.current_group = grp
        self.allRules[grp] = []

    def make_rule(self, seq):
        r = Rule(seq)
        self.allRules[self.current_group].append(r)
        return r

    def store_begin(self, seq):
        self.begins[seq[1].lower()] = seq[2][1]

    def parse(self, seq):
        const = lambda x: lambda _: x
        unarg = lambda f: lambda x: f(*x)
        tokval = lambda x: x.value
        toktype = lambda s: some(lambda x: x.type == s) >> tokval
        keyword = lambda s: some(lambda x: x.type == 'KEYWORD' and x.value.lower() == s)
        op = lambda s: a(Token('OP', s)) >> tokval
        op_ = lambda s: skip(op(s))
        name = toktype('NAME') | toktype('KEYWORD') | toktype('HEADER')
        number = toktype('NUMBER') >> get_num
        get_string = lambda v: v[1:-1]
        get_char = lambda v: unichr(int(v[2:], 16)) if v[0] in "uU" else unichr(int(v[1:], 10))
        string = (toktype('STRING') >> get_string) | (toktype('CHAR') >> get_char)
        nl = skip(toktype('NL'))
        simple_func = lambda k: keyword(k) + op_('(') + name + op_(')')
        assign_func = lambda k: keyword(k) + op_('(') + name + op_('=') + (name | string) + op_(')')

        # statement components
        vkey = op_('[') + many(name) + op_(']')
        context_statement = (keyword('context') + op_('(') + number + op_(')')) | keyword('context')
        index_statement = keyword('index') + op_('(') + name + op_(',') + number + op_(')')
        deadkey = (keyword('deadkey') | keyword('dk')) + op_('(') + number + op_(')')
        context = context_statement | keyword('beep') | keyword('nul') | simple_func('use') | \
                    (index_statement >> AnyIndex) | string | (deadkey >> DeadKey) | \
                    simple_func('reset') | simple_func('save') | assign_func('set') | \
                    simple_func('outs')
        match = (simple_func('any') >> AnyIndex) | string | (deadkey >> DeadKey) | simple_func('notany')

        # top level statements
        stripspace = lambda s: s.replace(' ', '')
        header = (((toktype('HEADER') >> stripspace) + string) | (toktype('HEADERN') + number)) + nl
        group  = (simple_func('group') >> self.set_group) + maybe(toktype('USINGKEYS')) + nl
        store = simple_func('store') + many(string | simple_func('outs')) + nl
        begin = keyword('begin') + name + op_('>') + simple_func('use') + nl
        rule = maybe(many(assign_func('if'))) + maybe(many(match)) + toktype('PLUS') + \
                ((vkey >> VKey) | string | (simple_func('any') >> AnyIndex)) + op_('>') + many(context) + nl
        matchrule = (keyword('match') | keyword('nomatch')) + op_('>') + many(context) + nl

        # a file is a sequence of certain types of statement
        make_header = lambda s: Store(['header', '&'+s[0], [s[1]]])
        kmfile = many((header >> make_header) | (store >> self.make_store) | skip(begin >> self.store_begin)) + \
                    maybe(many(group | (rule >> self.make_rule) | matchrule))
        return kmfile.parse(seq)


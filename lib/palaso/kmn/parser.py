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
keymap.update({ "|" : ("B00", True), "\\" : ("B00", False), " ": ("A03", False),
                "`" : ("E00", False), "~" : ("E00", True)})

def mapkey(tok):
    if tok is None:
        return tok
    elif isinstance(tok, VKey):
        return tok.getkey()
    else:
        k = keymap[tok]
        return (k[0], ("shift" if k[1] else ""))

class Rule(object):

    def __init__(self, toklist):
        for i,p in enumerate(toklist):
            try:
                if p is None:
                    p = [None, None]
                    break
                elif p[0] == '+':
                    break
            except AttributeError: pass
            except TypeError: pass
            except IndexError: pass

        self.before = toklist[i-1]
        self.match = p[1]
        self.output = toklist[i+1] if i < len(toklist)-1 else []

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
                    out.append(o)
            else:
                out.append(self._apply(allStores, o, vec))
        return Rule((before, ('+', match), out))

    def _len(self, allStores, x):
        if isinstance(x, AnyIndex):
            if x.name not in allStores:
                return 0
            return len(allStores[x.name].flatten().values)
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
    missing = 0xFDD2
    allkeys = {}

    @classmethod
    def increment(cls):
        cls.missing += 1
        if cls.missing == 0xFDE0:
            cls.missing = 0xEFFF0

    def __new__(cls, toklist):
        number = toklist[1]
        if number in cls.allkeys:
            return cls.allkeys[number]
        res = super(DeadKey, cls).__new__(cls)
        res.number = number
        res.char = unichr(cls.missing)
        cls.allkeys[number] = res
        cls.increment()
        return res

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
            elif s[0] in "ut" and s[1] == "_":
                self.key = s.replace("_","")
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
    allStores = {}

    def __init__(self, toklist):
        base = len(toklist) - 2
        self.name = toklist[base][1].lower()
        self.seq = toklist[base + 1]
        self.values = None
        self.allStores[self.name] = self

    def __repr__(self):
        return "store " + self.name + " " + \
                (str(self.values) if self.values is not None else str(self.seq))

    def flatten(self):
        if self.values is not None:
            return self
        self.values = []
        for s in self.seq:
            if isinstance(s, VKey):
                self.values.append(s)
            elif isinstance (s, Token) and s.value == 'beep':
                self.values.append(s)
            elif isinstance(s[0], Token):
                if s[0].value.lower() == 'outs':
                    sub = self.allStores[s[1].lower()]
                    sub.flatten()
                    self.values.extend(sub.values)
            else:
                self.values.extend(s)
        return self

def get_num(s):
    try:
        return int(s)
    except:
        return float(s)

def get_char(v):
    if v[0] in 'uU':
        return unichr(int(v[2:], 16))
    elif v[0] in 'xX':
        return unichr(int(v[1:], 16))
    elif v[0] in 'dD':
        return unichr(int(v[1:]))
    else:
        return unichr(int(v, 8))

class Parser(object):

    def __init__(self, s, debug=False, platform={}):
        self.allRules = { "": [] }
        self.uses = {}
        self.current_group = ""
        self.begins = {}
        self.allStores = {}
        self.allHeaders = {}
        self.platform = platform
        seq = self.tokenize(s)
        if debug:
            print(seq)
        self.tree = self.parse(seq)

    def tokenize(self, text):
        lexer_specs = [
            ('SPACE', (r'(\\[ \t]*\r?\n|[ \t])+',re.MULTILINE)),
            ('COMMENT', (r'[cC](?:[ \t]+[^\r\n]*)?(?=\r?\n)',)),
            ('NL', (r'\r?\n',re.MULTILINE)),
            ('KEYWORD', (r'any|index|store|outs|group|begin|use|beep|deadkey|dk|context|'
                          'if|match|nomatch|notany|return|reset|save|set|nul|platform', re.I)),
            ('USINGKEYS', (r'using\s*keys', re.I)),
            ('HEADER', (r'name|hotkey|baselayout|bitmap|bitmaps|caps always off|caps on only|'
                         'shift frees caps|copyright|language|layer|layout|message|platform', re.I)),
            ('HEADERN', (r'version', re.I)),
            ('OP', (r'[(),\[\]>=]',)),
            ('STRING', (r'(["\']).*?\1',)),
            ('CHAR', (r'([uU]\+[0-9a-fA-F]{4,6})|([dD][0-9]+)|([xX][0-9A-Fa-f]+)',)),
            ('PLUS', (r'\+',)),
            ('NAME', (r'[A-Za-z&][A-Za-z0-9_\-\.]*',)),
            ('NUMBER', (r'[0-9]+(\.[0-9]+)?',)),
            ('TARGET', (r'\$[a-z]+:',)),
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

    def prefix_test(self, s):
        if s is None or not len(s):
            return True
        if isinstance(s[0], Token):
            if s.type == 'KEYWORD' and s.value == 'platform':
                res = True
                for w in s[1].split(' '):
                    if w not in self.platform.values():
                        res = False
                return res
            else:
                return True
        if s == '$keyman:': return True
        if s == '$keymanonly:' and self.platform['ui'] == 'hardware': return True
        if s == '$keymanweb:' and self.platform['ui'] == 'touch': return True
        return False

    def make_store(self, seq):
        if not self.prefix_test(seq[0]):
            return None
        s = Store(seq[1:])
        if not s.name.startswith("&"):
            self.allStores[s.name] = s
        else:
            self.allHeaders[s.name] = s
        return s

    def set_group(self, seq):
        grp = seq[1].lower()
        self.current_group = grp
        self.allRules[grp] = []

    def make_rule(self, seq):
        if not self.prefix_test(seq[0]):
            return None
        r = Rule(seq)
        self.allRules[self.current_group].append(r)
        return r

    def make_match_rule(self, seq):
        if seq[0].value == 'match' and \
                isinstance(seq[1][0][0], Token) and seq[1][0][0].type == 'KEYWORD' and \
                    seq[1][0][0].value == 'use':
            self.uses.setdefault(self.current_group, set()).add(seq[1][0][1].lower())

    def store_begin(self, seq):
        self.begins[seq[1].lower()] = seq[2][1].lower()

    def parse(self, seq):
        const = lambda x: lambda _: x
        unarg = lambda f: lambda x: f(*x)
        tokval = lambda x: x.value
        toktype = lambda s: some(lambda x: x.type == s) >> tokval
        def sumstr(s):
            #import pdb; pdb.set_trace()
            return u"".join(unicode(x) for x in s)
        keyword = lambda s: some(lambda x: x.type == 'KEYWORD' and x.value.lower() == s)
        op = lambda s: a(Token('OP', s)) >> tokval
        op_ = lambda s: skip(op(s))
        onename = many(toktype('NAME') | toktype('KEYWORD') | toktype('HEADER') | toktype('NUMBER')) >> sumstr
        name = toktype('NAME') | toktype('KEYWORD') | toktype('HEADER')
        number = toktype('NUMBER') >> get_num
        get_string = lambda v: v[1:-1]
        string = (toktype('STRING') >> get_string) | (toktype('CHAR') >> get_char)
        nl = skip(toktype('NL'))
        typed_func = lambda k, c: keyword(k) + op_('(') + c + op_(')')
        simple_func = lambda k: typed_func(k, onename)
        assign_func = lambda k: keyword(k) + op_('(') + name + op_('=') + (name | string) + op_(')')

        # statement components
        vkey = op_('[') + many(name) + op_(']')
        prefix = toktype('TARGET') | assign_func('if') | typed_func('platform', string) 
        context_statement = (keyword('context') + op_('(') + number + op_(')')) | keyword('context')
        index_statement = keyword('index') + op_('(') + onename + op_(',') + number + op_(')')
        deadkey = (keyword('deadkey') | keyword('dk')) + op_('(') + (number | name) + op_(')')
        context = context_statement | keyword('beep') | keyword('nul') | simple_func('use') | \
                    (index_statement >> AnyIndex) | string | (deadkey >> DeadKey) | \
                    simple_func('reset') | simple_func('save') | assign_func('set') | \
                    simple_func('outs')
        match = (simple_func('any') >> AnyIndex) | string | (deadkey >> DeadKey) | simple_func('notany')

        # top level statements
        stripspace = lambda s: s.replace(' ', '')
        header = (((toktype('HEADER') >> stripspace) + string) | (toktype('HEADERN') + number)) + nl
        group  = (simple_func('group') >> self.set_group) + maybe(toktype('USINGKEYS')) + nl
        store = maybe(many(prefix)) + simple_func('store') + many(string | simple_func('outs') | \
                        (vkey >> VKey) | (deadkey >> DeadKey) | keyword('beep')) + nl
        begin = keyword('begin') + onename + op_('>') + simple_func('use') + nl
        rule = maybe(many(prefix)) + maybe(many(match)) + maybe(toktype('PLUS') + \
                ((vkey >> VKey) | string | (simple_func('any') >> AnyIndex))) + op_('>') + many(context) + nl
        matchrule = (keyword('match') | keyword('nomatch')) + op_('>') + many(context) + nl

        # a file is a sequence of certain types of statement
        make_header = lambda s: Store([(Token('HEADER', 'header'), '&'+s[0]), [s[1]]])
        kmfile = many((header >> make_header) | (store >> self.make_store) | \
                      skip(begin >> self.store_begin)) + \
                 maybe(many(group | (rule >> self.make_rule) | \
                            (matchrule >> self.make_match_rule) | \
                            (store >> self.make_store))) + finished
        return kmfile.parse(seq)


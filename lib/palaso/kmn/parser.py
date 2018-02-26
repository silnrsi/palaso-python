#!/usr/bin/python

import sys, re, os, codecs
import logging, itertools
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, skip, finished, NoParseError)
from funcparserlib.util import pretty_tree
from xml.etree import ElementTree as et
from xml.etree import ElementPath as ep

_elementprotect = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;' }
_attribprotect = dict(_elementprotect)
_attribprotect['"'] = '&quot;'

class ETWriter(object):
    """ General purpose ElementTree pretty printer complete with options for attribute order
        beyond simple sorting, and which elements should use cdata """

    nscount = 0
    indent = "\t"

    def __init__(self, et, namespaces = None, attributeOrder = {}, takesCData = set()):
        self.root = et
        if namespaces is None: namespaces = {}
        self.namespaces = namespaces
        self.attributeOrder = attributeOrder
        self.maxAts = max([0] + attributeOrder.values()) + 1
        self.takesCData = takesCData

    def _localisens(self, tag):
        if tag[0] == '{':
            ns, localname = tag[1:].split('}', 1)
            qname = self.namespaces.get(ns, '')
            if qname:
                return ('{}:{}'.format(qname, localname), qname, ns)
            else:
                self.nscount += 1
                return (localname, 'ns_' + str(self.nscount), ns)
        else:
            return (tag, None, None)

    def _protect(self, txt, base=_attribprotect):
        return re.sub(ur'['+ur"".join(base.keys())+ur"]", lambda m: base[m.group(0)], txt)

    def _nsprotectattribs(self, attribs, localattribs, namespaces):
        if attribs is not None:
            for k, v in attribs.items():
                (lt, lq, lns) = self._localisens(k)
                if lns and lns not in namespaces:
                    namespaces[lns] = lq
                    localattribs['xmlns:'+lq] = lns
                localattribs[lt] = v
        
    def _sortedattrs(self, n, attribs=None):
        def getorder(x):
            return self.attributeOrder.get(n.tag, {}).get(x, self.maxAts)
        def cmpat(x, y):
            return cmp(getorder(x), getorder(y)) or cmp(x, y)
        if attribs != None :
            return sorted(attribs, cmp=cmpat)
        else:
            return sorted(n.keys(), cmp=cmpat)

    def serialize_xml(self, write, base = None, indent = '', topns = True, namespaces = {}):
        """Output the object using write() in a normalised way:
                topns if set puts all namespaces in root element else put them as low as possible"""
        if base is None:
            base = self.root
            write('<?xml version="1.0" encoding="utf-8"?>\n')
        (tag, q, ns) = self._localisens(base.tag)
        localattribs = {}
        if ns and ns not in namespaces:
            namespaces[ns] = q
            localattribs['xmlns:'+q] = ns
        if topns:
            if base == self.root:
                for n,q in self.namespaces.items():
                    localattribs['xmlns:'+q] = n
                    namespaces[n] = q
        else:
            for c in base:
                (lt, lq, lns) = self._localisens(c.tag)
                if lns and lns not in namespaces:
                    namespaces[lns] = q
                    localattribs['xmlns:'+lq] = lns
        self._nsprotectattribs(getattr(base, 'attrib', None), localattribs, namespaces)
        for c in getattr(base, 'comments', []):
            write(u'{}<!--{}-->\n'.format(indent, c))
        write(u'{}<{}'.format(indent, tag))
        if len(localattribs):
            def getorder(x):
                return self.attributeOrder.get(tag, {}).get(x, self.maxAts)
            def cmpattrib(x, y):
                return cmp(getorder(x), getorder(y)) or cmp(x, y)
            for k in self._sortedattrs(base, localattribs):
                write(u' {}="{}"'.format(self._localisens(k)[0], self._protect(localattribs[k])))
        if len(base):
            write('>\n')
            for b in base:
                self.serialize_xml(write, base=b, indent=indent + self.indent, topns=topns, namespaces=namespaces.copy())
            write('{}</{}>\n'.format(indent, tag))
        elif base.text:
            if tag not in self.takesCData:
                t = self._protect(base.text.replace('\n', '\n' + indent), base=_elementprotect)
            else:
                t = "<![CDATA[\n\t" + indent + base.text.replace('\n', '\n\t' + indent) + "\n" + indent + "]]>"
            write(u'>{}</{}>\n'.format(t, tag))
        else:
            write('/>\n')
        for c in getattr(base, 'commentsafter', []):
            write(u'{}<!--{}-->\n'.format(indent, c))

_keyrowmap = {
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
                for rk, r in _keyrowmap.items() for i, k in enumerate(r)])
keymap.update({ "|" : ("B00", True), "\\" : ("B00", False),
                "`" : ("E00", False), "~" : ("E00", True)})

def mapkey(tok):
    if isinstance(tok, VKey):
        return tok.getkey()
    else:
        k = keymap[tok]
        return (k[0], ("shift" if k[1] else ""))

class AttrString(unicode):
    pass

class Rule(object):
    allRules = { "": [] }
    current_group = ""

    @classmethod
    def set_group(cls, grp):
        cls.current_group = grp
        cls.allRules[grp] = []

    def __init__(self, toklist, temp=False):
        p = toklist.index(u'+')
        self.before = toklist[p-1]
        self.match = toklist[p+1]
        self.output = toklist[p+2]
        if not temp:
            self.allRules[self.current_group].append(self)

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
                    out.append(before[o[1]])
                elif o[0].value.lower() == 'outs':
                    out.extend(allStores[o[1]].values)
            elif isinstance(o, Token):
                if o.value.lower() == 'context':
                    out.extend(before)
            else:
                out.append(self._apply(allStores, o, vec))
        return Rule((before, '+', match, out), temp=True)

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
        self.name = toklist[1]
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
    "quote": "C11", "space": "A03", "bkquote": "E00", "comma": "B08",
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
            elif s.startswith("l"):
                mod = "L"
            elif s == 'altgr':
                s = s[:4]
                mod = "R"
            if s.startswith("k_"):
                self.key = s[2:]
            else:
                self.modifiers += [s[1:] + mod]

    def getkey(self):
        if self.key in keymap:
            k = keymap[self.key][0]
        elif self.key in specialkeys:
            k = specialkeys[self.key]
        m = "+".join(sorted(self.modifiers))
        return (k, m)

class Store(object):
    allStores = {}
    allHeaders = {}

    def __init__(self, toklist):
        self.name = toklist[1]
        self.seq = toklist[2]
        self.values = None
        if not self.name.startswith("&"):
            self.allStores[self.name] = self
        else:
            self.allHeaders[self.name] = self

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
                    sub = self.allStores[s[1]]
                    sub.flatten()
                    self.values.extend(sub.values)
            else:
                self.values.extend(s)


class LDMLKeyboard(ETWriter):
    def __init__(self):
        doc = et.fromstring("""<?xml version="1.0"?>
<keyboard>
<version platform="1" number="1"/>
</keyboard>
""")
        let = et.ElementTree()
        let._setroot(doc)
        ETWriter.__init__(self, doc)

    def setname(self, name):
        nms = et.SubElement(self.root, "names")
        et.SubElement(nms, "name", {"value": name})

    def addKeyMap(self, keymap, modifiers):
        km = et.SubElement(self.root, "keyMap", attrib={'modifiers' : modifiers})
        for k, v in sorted(keymap.items()):
            a = {"iso": k, "to": v}
            if getattr(v, 'error', False):
                a['error'] = "fail"
            et.SubElement(km, "map", attrib=a)

    def addTransform(self, t, rules):
        ts = et.SubElement(self.root, "transforms", attrib={'type': t})
        for k, v in sorted(rules.items()):
            a = {'from': k, 'to': v}
            if getattr(v, 'error', False):
                a['error'] = "fail"
            et.SubElement(ts, 'transform', attrib=a)

def tokenize(text):
    lexer_specs = [
        ('SPACE', (r'(\\\r?\n|[ \t])+',re.MULTILINE)),
        ('COMMENT', (r'c\s+[^\n]*',)),
        ('NL', (r'\r?\n',re.MULTILINE)),
        ('KEYWORD', (r'any|index|store|outs|group|begin|use|beep|deadkey|dk|context|'
                      'if|match|nomatch|notany|return|reset|save|set', re.I)),
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

def get_num(s):
    try:
        return int(s)
    except:
        return float(s)

begins = {}
def store_begin(seq):
    global begins
    begins[seq[1].lower()] = seq[2][1]

def parse(seq):
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

    notany_statement = simple_func('notany')
    vkey = op_('[') + many(name) + op_(']')
    context_statement = (keyword('context') + op_('(') + number + op_(')')) | keyword('context')
    index_statement = keyword('index') + op_('(') + name + op_(',') + number + op_(')')
    use_statement = simple_func('use')
    deadkey = (keyword('deadkey') | keyword('dk')) + op_('(') + number + op_(')')
    context = context_statement | keyword('beep') | keyword('nul') | use_statement | \
                (index_statement >> AnyIndex) | string | (deadkey >> DeadKey) | \
                simple_func('reset') | simple_func('save') | assign_func('set')
    match = (simple_func('any') >> AnyIndex) | string | (deadkey >> DeadKey)

    stripspace = lambda s: s.replace(' ', '')
    header = (((toktype('HEADER') >> stripspace) + string) | (toktype('HEADERN') + number)) + nl
    group = keyword('group') + op_('(') + ((name | toktype('KEYWORD')) >> Rule.set_group) + op_(')') + \
                toktype('USINGKEYS') + nl
    store = simple_func('store') + many(string | simple_func('outs')) + nl
    begin = keyword('begin') + name + op_('>') + simple_func('use') + nl
    rule = maybe(many(assign_func('if'))) + maybe(many(match)) + toktype('PLUS') + \
            ((vkey >> VKey) | string | (simple_func('any') >> AnyIndex)) + op_('>') + many(context) + nl
    matchrule = (keyword('match') | keyword('nomatch')) + op_('>') + many(context) + nl

    make_header = lambda s: Store(['header', '&'+s[0], [s[1]]])
    kmfile = (many((header >> make_header) | (store >> Store) | skip(begin >> store_begin)) + \
                maybe(skip(group) + many((rule >> Rule) | matchrule)))
    return kmfile.parse(seq)

def loads(s):
    return parse(tokenize(s))

def main():
    logging.basicConfig(level=logging.DEBUG)
    f = codecs.open(sys.argv[1], "r", encoding="utf-8")
    input = "".join(f.readlines())
    try:
        tree = list(loads(input))
    except NoParseError as e:
        print(e)
    if len(sys.argv) > 2 and sys.argv[2] == "-z":
        print(pformat(tree))
    for s in Store.allStores.values():
        s.flatten()
    maps = { "" : {}, "shift" : {} }
    for r in Rule.allRules[begins['unicode']]:
        if len(r.before):
            continue
        error = False
        for o in r.output:
            if isinstance(o, Token) and o.type == 'KEYWORD' and o.value.lower() == 'beep':
                error = True
                break
        for re in r.flatten(Store.allStores):
            k = mapkey(re.match)
            if k[1] not in maps:
                maps[k[1]] = {}
            maps[k[1]][k[0]] = AttrString(u"".join(re.output))
            if error:
                maps[k[1]][k[0]].error = True
    ldml = LDMLKeyboard()
    if '&NAME' in Store.allHeaders:
        ldml.setname(Store.allHeaders['&NAME'].seq[0])
    for km in sorted(maps.keys()):
        ldml.addKeyMap(maps[km], km)

    simples = {}
    finals = {}
    for r in Rule.allRules[begins['unicode']]:
        if not len(r.before):
            continue
        isdead = any(filter(lambda x: isinstance(x, DeadKey), r.before))
        error = False
        for o in r.output:
            if isinstance(o, Token) and o.type == 'KEYWORD' and o.value.lower() == 'beep':
                error = True
                break
        for re in r.flatten(Store.allStores):
            k = mapkey(re.match)
            mp = maps[k[1]]
            if k[0] not in mp:
                mp[k[0]] = unichr(DeadKey.missing)
                finals[unichr(DeadKey.missing)] = ""
                DeadKey.missing += 1
            m = mp[k[0]]
            bs = []
            for b in re.before:
                bs.extend(b)
            btxt = u"".join(bs) + m
            otxt = AttrString(u"".join(re.output))
            if error:
                otxt.error = True
            if btxt == otxt and not error:
                continue
            if isdead:
                simples[btxt] = otxt
            else:
                finals[btxt] = otxt
    if len(simples):
        ldml.addTransform('simple', simples)
    if len(finals):
        ldml.addTransform('final', finals)

    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
    ldml.serialize_xml(sys.stdout.write)


if __name__ == '__main__':
    main()
    

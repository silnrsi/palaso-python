#!/usr/bin/env python3

from palaso import kmn
from palaso.kmfl import kmfl
import re, time
from optparse import OptionParser

item_char = 0
item_keysym = 1
item_any = 2
item_index = 3
item_outs = 4
item_deadkey = 5
item_context = 6
item_nul = 7
item_return = 8
item_beep = 9
item_use = 10
item_match = 11
item_nomatch = 12
item_plus = 13
item_call = 14
item_notany = 15

def item_type(x) : return (x >> 24) & 0xFF
def item_base(x) : return x & 0xFFFF
def item_index_offset(x) : return (x >> 16) & 0xFF

xmlentities = { "<" : '&lt;', '&' : '&amp;', '>' : '&gt;', '"' : '&quot;', "'" : '&apos;' }

def entity_escape(cs) :
    r = ''
    for c in cs :
        if ord(c) > 0x7F :
            ent = "&#x%04X;" % ord(c)
        else :
            ent = xmlentities.get(c)
        r += (ent if ent else c)
    return r

regexpentities = {x: "\\" + x for x in "[]{()?|."}

def regexp_escape(cs) :
    return "".join(regexpentities.get(x, x) for x in cs)

class rule(object) :
    def __init__(self, inputs, outputs, deadin = 0, deadout = 0, iskey = True, contextref = False) :
        self.key = inputs.pop() if iskey else None
        self.inputs = inputs
        self.outputs = outputs
        self.deadin = deadin
        self.deadout = deadout
        self.contextref = contextref

    def regexps(self) :
        deltas = [0]
        refed = [self.contextref] + [0] * len(self.inputs)
        currdelta = 0 if self.contextref else 1
        outs = ""
        ins = "(" if self.contextref else ""
        for i in self.outputs :
            m = re.match(r"\\(\d+)$", i)
            if m : refed[int(m.group(1)) - 1] = 1
        for i in range(len(self.inputs)) :
            inp = self.inputs[i]
            if not inp or not refed[i + 1] :
                currdelta += 1
                ins += entity_escape(inp)
            else :
                ins += "(" + entity_escape(inp) + ")"
            deltas.append(currdelta)
        ins += ")" if self.contextref else ""
        for i in self.outputs :
            m = re.match(r"\\(\d+)$", i)
            if m :
                offset = int(m.group(1))
                if len(self.inputs) and offset <= len(deltas) :
                    v = "\\" + str(offset - deltas[offset - 1])
                    outs += v
            else :
                outs += entity_escape(i)
        return (ins, outs)

    def asxml(self) :
        ins, outs = self.regexps()
        res = "<rule"
        if len(self.inputs) : res += " input='%s'" % ins
        if len(self.outputs) : res += " output='%s'" % outs
        if self.deadin : res += " deadin='%d'" % self.deadin
        if self.deadout : res += " deadout='%d'" % self.deadout
        if self.key : res += " key='%s'" % entity_escape(self.key)
        res += "/>"
        return res

def process_rule(lhs, rhs, presets, iskey = True, contextref = False) :
    flattens = set()
    output = []
    input = []
    deadin = 0
    deadout = 0
#    print str(map(lambda x: "%X" % x, lhs)) + ", " + str(map(lambda x: "%X" % x, rhs))
    for j in range(len(rhs)) :
        r = rhs[j]
        if item_type(r) == item_index :
            offset = item_index_offset(r)
            storenum = item_base(r)
            if item_type(lhs[offset - 1]) == item_any :
                lstorenum = item_base(lhs[offset - 1])
                if lstorenum != storenum :
                    newrhs = rhs[:]
                    newlhs = lhs[:]
                    store = kb.store(str(storenum))
                    lstore = kb.store(str(lstorenum))
                    npre = presets[:]
                    for k in range(len(lstore)) :
                        if k >= len(store) or k >= len(lstore): continue
                        npre[offset - 1] = k
                        newrhs[j] = ord(store[k])
                        newlhs[offset - 1] = ord(lstore[k])
                        for res in process_rule(newlhs, newrhs, npre, iskey, contextref) : yield res
                    return
                else :
                    output += ["\\" + str(offset + 1)]
            else :
                ind = presets[offset - 1]
#                print("storenum=%d index=%d" % (storenum, ind))
                output += [chr(ord(kb.store(str(storenum))[ind]))]
        elif item_type(r) == item_context :
            contextref = True
            output += ["\\" + str(item_base(r) + 1)]
        elif item_type(r) == item_outs :
            output += ["".join(chr(ord(x)) for x in kb.store(str(item_base(r))))]
        elif item_type(r) == item_char :
            output += [chr(r)]
        elif item_type(r) == item_deadkey :
            deadout = item_base(r)

    for j in range(len(lhs)) :
        l = lhs[j]
        if item_type(l) == item_char or item_type(l) == item_keysym :
            if iskey and j == len(lhs) - 1 :
                input += [kmn.item_to_key(l)]
            else :
                input += [regexp_escape(kmn.item_to_char(l))]
        elif item_type(l) == item_any  or item_type(l) == item_notany :
            store = kb.store(str(item_base(l)))
            if item_type(l) == item_any and len(store) == 1 :
                input += [regexp_escape(store)]
            else :
                input += [("[" if item_type(l) == item_any else "[^") + regexp_escape(store) + "]"]
        elif item_type(l) == item_deadkey :
            deadin = item_base(l)
        else :
#            print "found %X on lhs" % l
            input += [""]
    if len(input) and len(output) :
        yield rule(input, output, deadin, deadout, iskey = iskey, contextref = contextref)

parser = OptionParser()
parser.add_option("-l","--lang",help="Language tag for this LDML")

(opts, argv) = parser.parse_args()
id = {}
if opts.lang :
    m = re.match(r'^([^-_]+)(?:[-_]?([^-_]*)[-_]?(.*))$', opts.lang)
    id['language'] = m.group(1)
    if len(m.group(2)) == 4 :
        id['script'] = m.group(2)
    elif m.group(2) :
        id['territory'] = m.group(2)

kb = kmfl(argv[0])
rules = {}
name = kb.store("NAME")
mnemonic = kb.store("MNEMONIC")
mnemattr = ' mnemonic="1"' if mnemonic else ""
print("""<?xml version="1.0"?>
<ldml>
  <identity>""")

for k, v in id.items() :
    print('    <%s type="%s"/>' % (k, v))
print('    <generation date="%s"/>' % (time.strftime('%Y-%m-%d')))
print("""  </identity>
  <special>
    <keyboards xmlns="http://www.palaso.org/ldml/0.2">
      <keyboard name="%s"%s>""" % (name, mnemattr))
for i in range(kb._num_rules()) :
    (lhs, rhs, gpnum, flags) = kb.rule(i)
    for r in process_rule(lhs, rhs, [0] * len(lhs), iskey = (flags & 1)) :
        if r.key in rules :
            rules[r.key].append(r)
        else :
            rules[r.key] = [r]
for k in sorted(rules.keys()) :
    for r in sorted(rules[k], cmp = lambda a, b : cmp(len(b.inputs), len(a.inputs))) :
        print("        " + r.asxml())

print("""      </keyboard>
    </keyboards>
  </special>
</ldml>
""")

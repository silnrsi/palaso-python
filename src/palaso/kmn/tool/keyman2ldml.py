#!/usr/bin/env python3

import argparse, codecs, unicodedata, re, os, itertools
from palaso.kmn.parser import Parser, mapkey, Token, DeadKey, VKey, keyrowmap
from xml.etree import ElementTree as et
from xml.etree import ElementPath as ep
from pprint import pformat
import json

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

    def __init__(self, et, namespaces = None, attributeOrder = {}, takesCData = set(), elementOrder = []):
        self.root = et
        if namespaces is None: namespaces = {}
        self.namespaces = namespaces
        self.attributeOrder = attributeOrder
        self.maxAts = max([0] + list(attributeOrder.values())) + 1
        self.elementOrder = dict((x, i+1) for i,x in enumerate(elementOrder))
        self.maxTags = len(self.elementOrder) + 1
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
        return re.sub(f'[{"".join(base.keys())}]', lambda m: base[m.group(0)], txt)

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
            return self.attributeOrder.get(x, self.maxAts)
        def cmpat(x, y):
            return cmp(getorder(x), getorder(y)) or cmp(x, y)
        if attribs != None :
            return sorted(attribs, cmp=cmpat)
        else:
            return sorted(n.keys(), cmp=cmpat)

    def serialize_xml(self, write, base = None, indent = '', topns = True, namespaces = {}, doctype=""):
        """Output the object using write() in a normalised way:
                topns if set puts all namespaces in root element else put them as low as possible"""
        if base is None:
            base = self.root
            write('<?xml version="1.0" encoding="utf-8"?>\n')
            if doctype != "":
                write(doctype+"\n")
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
            write('{}<!--{}-->\n'.format(indent, c))
        write('{}<{}'.format(indent, tag))
        if len(localattribs):
            def getorder(x):
                return self.attributeOrder.get(tag, {}).get(x, self.maxAts)
            def cmpattrib(x, y):
                return cmp(getorder(x), getorder(y)) or cmp(x, y)
            for k in self._sortedattrs(base, localattribs):
                write(' {}="{}"'.format(self._localisens(k)[0], self._protect(localattribs[k])))
        if len(base):
            write('>\n')
            for b in sorted(base, key=lambda b:self.elementOrder.get(b.tag, self.maxTags)):
                self.serialize_xml(write, base=b, indent=indent + self.indent, topns=topns, namespaces=namespaces.copy())
            write('{}</{}>\n'.format(indent, tag))
        elif base.text:
            if tag not in self.takesCData:
                t = self._protect(base.text.replace('\n', '\n' + indent), base=_elementprotect)
            else:
                t = "<![CDATA[\n\t" + indent + base.text.replace('\n', '\n\t' + indent) + "\n" + indent + "]]>"
            write('>{}</{}>\n'.format(t, tag))
        else:
            write('/>\n')
        for c in getattr(base, 'commentsafter', []):
            write('{}<!--{}-->\n'.format(indent, c))

attributeorders = ('before', 'from', 'after', 'iso', 'to', 'layer', 'display')
#elementOrder = ('version', 'names', 'settings', 'import', 'keyMap', 'displayMap', 'layer', 'vkeys',
#                'transforms', 'reorders', 'backspaces')

class LDMLKeyboard(ETWriter):
    def __init__(self, locale, base=""):
        doc = et.fromstring("""<?xml version="1.0"?>
<keyboard locale="{}">
<version platform="1" number="1"/>
<import path="{}"/>
</keyboard>
""".format(locale, base))
        let = et.ElementTree()
        let._setroot(doc)
        ETWriter.__init__(self, doc, attributeOrder=dict((x, i+1) for i,x in enumerate(attributeorders)))

    def setname(self, name):
        nms = et.SubElement(self.root, "names")
        et.SubElement(nms, "name", {"value": name})

    def addKeyMap(self, keymap, modifiers):
        km = et.SubElement(self.root, "keyMap", attrib={'modifiers' : modifiers})
        for k, v in sorted(keymap.items()):
            a = {"iso": k, "to": readable(v)}
            if getattr(v, 'error', False):
                a['error'] = "fail"
            et.SubElement(km, "map", attrib=a)

    def mapKey(self, key, modifiers):
        k = self.root.find('.//keyMap[@modifiers="'+modifiers+'"]/map[@iso="'+key+'"]')
        if k is None and (modifiers == '' or modifiers == 'shift'):
            try:
                to = keyrowmap[("_" if modifiers == 'shift' else '')+key[0]][int(key[1:])-1]
            except:
                to = ''
        else:
            to = k.get('to', '') if k is not None else ''
        return to

    def addKey(self, modifiers, key, to):
        k = self.root.find('.//keyMap[@modifiers="'+modifiers+'"]')
        if k is None:
            k = et.SubElement(self.root, "keyMap", attrib={'modifiers': modifiers})
        return et.SubElement(k, 'map', attrib={'iso': key, 'to': to})

    def keyAddAttrs(self, modifiers, key, attrs):
        k = self.root.find('.//keyMap[@modifiers="'+modifiers+'"]/map[@iso="'+key+'"]')
        if k is None:
            k = self.addKey(modifiers, key, self.mapKey(key, modifiers))
        k.attrib.update(attrs)

    def addDisplay(self, to, display):
        k = self.root.find(".//displayMap")
        if k is None:
            k = et.SubElement(self.root, "displayMap")
        pto = ('"{}"' if '"' not in to else "'{}'").format(to)
        pdisplay = ('"{}"' if '"' not in display else "'{}'").format(display)
        if self.root.find('.//displayMap/display[@mapOutput='+pto+']') is None:
            et.SubElement(k, "display", attrib={'mapOutput': to, 'display': display})

    def addDeadkeySettings(self):
        #et.SubElement(self.root, "settings", attrib={'fallback': 'omit', 'transformPartial': 'hide'})
        pass

    def addTransform(self, t, rules, keyword="transform"):
        if t == keyword:
            ts = et.SubElement(self.root, keyword+"s")
        else:
            ts = et.SubElement(self.root, keyword+"s", attrib={'type': t})
        transforms = TransformElements()
        before = []
        end = []
        for k, v in sorted(rules.items(), key=lambda x:(-len(x[0]), x[0])):
            fr = str(k)
            to = str(v)
            c = min(len(to), len(fr))
            for i in range(c):
                if fr[i] != to[i]:
                    before = fr[:i]
                    fr = fr[i:]
                    to = to[i:]
                    break
            else:
                before = fr[:c]
                fr = fr[c:]
                to = to[c:]
            end = ""
            a = {}
            if len(before): a['before'] = before
            a['from'] = fr
            if len(end) : a['after'] = end
            a['to'] = to
            if getattr(v, 'error', False):
                a['error'] = "fail"
            if hasattr(v, 'comment'):
                a['comment'] = v.comment
            transforms.addElement(**a)
        transforms.contextPriority()
        for v in transforms.asReadable():
            et.SubElement(ts, keyword, attrib=v)

    def addLayer(self, rows, modifiers, switches, extras):
        ls = et.SubElement(self.root, "layer", attrib={'modifier': modifiers})
        for r in rows:
            a = {'keys': " ".join(zip(*r)[0])}
            w = zip(*r)[1]
            if extras and any(x for x in w if int(x) != 100):
                a['widths'] = " ".join(w)
            et.SubElement(ls, "row", attrib=a)
        for s in switches:
            et.SubElement(ls, "switch", attrib={'iso': s[0], 'layer': s[1], 'display': s[2]})

    def addImport(self, path):
        i = et.SubElement(self.root, "import", attrib={'path': path})

    def addPrebases(self, prebases):
        i = et.SubElement(self.root, "reorders")
        for p in prebases.keys():
            et.SubElement(i, "reorder", attrib={'from': readable(p), 'prebase': '1'})

def readable(s, regcontext=False):
    s1 = re.sub(r"([\[\].+?*&^$\\{}|\(\)])", r"\\\1", str(s)) if regcontext else str(s)
    return "".join("\\u{{{:04X}}}".format(ord(x)) \
            if unicodedata.category(x)[0] in "CM" else x for x in str(s1))

def iterSetList(l):
    if len(l) == 1:
        for p in l[0]:
            yield p
        return
    for e in l[-1]:
        for p in iterSetList(l[:-1]):
            yield p + e

def setlistmatch(this, other, rev=False):
    t = len(this)
    d = len(other) - t
    if d < 0:
        return False
    if rev:
        r = range(t-1, -1, -1)
    else:
        r = range(t)
    for i in r:
        o = i + d if rev else i
        if isinstance(this[i], set):
            if isinstance(other[o], set):
                if not len(this[i] & other[o]):
                    return False
            elif not other[o] in this[i]:
                return False
        elif isinstance(other[o], set):
            if not this[i] in other[o]:
                return False
        elif this[i] != other[o]:
            return False
    return True

class TransformElements:
    def __init__(self):
        self.froms = {}
        self.tos = {}
        self.elements = {}

    def addElement(self, **kw):
        to = kw['to']
        fr = kw['from']
        test = "{}|{}".format(fr, to)
        if to == fr:    # special high priority insertion
            self.elements.setdefault(test, []).append(kw)
        for l in self.froms.get(fr, []):
            for e in self.elements[l]:
                count = 0
                if e['to'] != kw['to']:
                    continue
                for k in ('before', 'after'):
                    if (k in kw) != (k in e):
                        break
                    if k not in kw: continue
                    count += self.countDiffs(kw[k], e[k])
                if count == 1:
                    for k in ('before', 'after'):
                        if k not in kw: continue
                        e[k] = self.mergeTransform(e[k], kw[k])
                        self.tos.setdefault(to, []).append(l)
                    return
                elif count == 0 and e['from'] == fr:
                    return
        for l in self.tos.get(to, []):
            for e in self.elements[l]:
                if self.countDiffs(fr, e['from']) != 1:
                    continue
                for k in ('before', 'after'):
                    if (k in kw) != (k in e): break
                    if k not in kw: continue
                    if self.countDiffs(kw[k], e[k]): break
                else:
                    e['from'] = self.mergeTransform(e['from'], fr)
                    self.froms.setdefault(fr, []).append(l)
                    return
        self.elements.setdefault(test, []).append(kw)
        self.froms.setdefault(fr, []).append(test)
        self.tos.setdefault(to, []).append(test)

    def countDiffs(self, new, old):
        if len(new) != len(old):
            return max(len(new), len(old))
        count = 0
        for i,o in enumerate(old):
            if isinstance(o, (str,bytes)):
                if o != new[i]:
                    count += 1
            elif new[i] not in o:
                count += 1
        return count

    def mergeTransform(self, old, new):
        if isinstance(old, (str,bytes)):
            old = [set(x) for x in old]
        for i, o in enumerate(old):
            if new[i] not in o:
                o.add(new[i])
        return old

    def contextPriority(self):
        for _, v in self.elements.items():
            for r in v:
                if 'before' not in r:
                    continue
                for i in range(len(r['before'])):
                    matched = False
                    for s in iterSetList(r['before'][-i-1:]):
                        if any(isinstance(x, set) for x in r['from']):
                            continue
                        other = self.matches(s+"".join(r['from']), r['before'][:-i-1], r.get('after', []))
                        if other is not None and s + r['to'] != other['to']:
                            kw = {'from': s+r['from'], 'to': s+r['to'], 'before': r['before'][:-i-1]}
                            if 'after' in r:
                                kw['after'] = r['after']
                            if 'comment' in r:
                                kw['comment'] = "From " + r['comment']
                            self.addElement(**kw)
                            matched = True

    def matches(self, fr, before, after):
        for l in self.froms.get(fr, []):
            for v in self.elements[l]:
                if not setlistmatch(after, v.get('after', [])):
                    continue
                if setlistmatch(before, v.get('before', []), rev=True):
                    return v
        return None
            
    def asReadable(self):
        for _, l in sorted(self.elements.items()):
            for v in l:
                if not len(v['from']) and not len(v['to']) and 'before' in v:
                    l = v['before'][-1]
                    v['before'] = v['before'][:-1]
                    if len(l) == 0:
                        pass
                    elif len(l) == 1:
                        v['from'] = list(l)[0]
                    else:
                        v['from'] = l
                    v['to'] = v['from']
                    if not len(v['before']):
                        del v['before']
                for k,b in v.items():
                    if k in ('before', 'after', 'from'):
                        if k == 'from' and isinstance(b, set):
                            continue
                        res = ""
                        for l in b:
                            if len(l) > 1:
                                res += "[" + "".join(readable(x, True) for x in sorted(l)) + "]"
                            else:
                                res += readable(list(l)[0], True)
                    else: 
                        res = readable(b, True)
                    v[k] = res
                if len(v['from']) and isinstance(v['from'], set):
                    l = v['from']
                    for f in l:
                        v['from'] = readable(f, True)
                        v['to'] = readable(f, False)
                        yield v
                else:
                    yield v
        

class OutputString:
    def __init__(self, toklist):
        self.str = ""
        self.error = False
        self.isreordering = False
        for t in toklist:
            if isinstance(t, str):
                self.str += t
            elif isinstance(t, Token) and t.type == 'KEYWORD':
                if t.value == 'beep':
                    self.error = True
            else:
                import pdb; pdb.set_trace()

    def replace(self, instr, repstr):
        if instr is None:
            return self
        res = self.str.replace(instr, repstr)
        if len(res) and res != self.str:
            self.str = res
            self.isreordering = True
        return self

    def __unicode__(self):
        return self.str

    def __eq__(self, other):
        return self.str == str(other)

def load_kmn(kmnfile, platform):
    with codecs.open(kmnfile, "r", encoding="utf-8-sig") as f:
        lines = "".join(f.readlines())
    p = Parser(lines, debug = (args.debug & 2), platform = platform)
    if (args.debug & 1):
        print(pformat(p.tree))
    for s in p.allStores.values():
        s.flatten()
    return p

def preprocess_kmn(p):
    allchars = set()
    for u in p.begins.values():
        for r in p.allRules[u]:
            for rf in r.flatten(p.allStores):
                outs = OutputString(rf.output)
                for c in str(outs):
                    allchars.add(c)
    return allchars

def process_uses(p, name, *extras):
    for t in p.uses.get(name, set()):
        for r in p.allRules[t]:
            make_transform(r, p, *extras)
        process_uses(p, t, *extras)

def process_kmn(ldml, p, reorder=False, reorderfile=None, base=None, name=None):
    prebases = {}
    maps = { "" : {}, "shift" : {} }
    simples = {}
    for r in p.allRules[p.begins['unicode']]:
        if len(r.before):
            continue
        error = False
        for rf in r.flatten(p.allStores):
            if rf.match is None: continue
            try:
                k = mapkey(rf.match)
            except KeyError:
                print("Warning: Failed to map {}".format(rf.match))
                continue
            if k[1] not in maps:
                maps[k[1]] = {}
            outs = OutputString(rf.output).replace(args.charreorder, "")
            if len(str(outs)) and any(outs == x and (k[0] != w or k[1] != y) \
                                        for y in maps.values() for w,x in y.items()):
                s = chr(DeadKey.missing)
                DeadKey.increment()
                simples[s] = outs
                outs = OutputString(s)
            maps[k[1]][k[0]] = outs
            if outs.isreordering:
                prebases[str(outs)] = True
    if name is not None:
        ldml.setname(name)
    elif '&NAME' in p.allHeaders:
        ldml.setname(p.allHeaders['&NAME'].seq[0])
    else:
        ldml.setname('Unknown')

    if base is not None:
        bmaps = overwrite_map(process_basefile(base), maps)
    finals = {}
    backups = {}
    deadkeys = {}
    uses = set()
    for r in p.allRules[p.begins['unicode']]:
        make_transform(r, p, maps, bmaps, deadkeys, simples, finals, backups, prebases)
    process_uses(p, p.begins['unicode'], maps, bmaps, deadkeys, simples, finals, backups, prebases)
    for km in sorted(maps.keys()):
        ldml.addKeyMap(maps[km], km)
    if len(deadkeys):
        ldml.addDeadkeySettings()
        ldml.addTransform('simple', deadkeys)
        nextsimple = 'simple2'
    else:
        nextsimple = 'simple'
    if len(simples):
        ldml.addTransform(nextsimple, simples)
    if reorder:
        ldml.addImport('shared/reorders.xml')
    if reorderfile:
        ldml.addImport(reorderfile)
    if len(prebases):
        ldml.addPrebases(prebases)
    if len(finals) or len(DeadKey.allkeys):
        for d in DeadKey.allkeys.values():
            finals[d.char] = OutputString([])
        ldml.addTransform('final', finals)
    if len(backups):
        ldml.addTransform('backspace', backups, keyword="backspace")

def overwrite_map(main, other):
    ''' unifies the two keymaps with preference for other, returning main '''
    for k,v in other.items():
        if k in main:
            main[k].update(v)
        else:
            main[k] = v
    return main

def find_file(fpath, bases=[]):
    ''' Scan all directories between here and project root (has .git) or /,
        for the given path and return first matching complete path else None '''
    for cur in ['.'] + bases:
        lastabs = None
        while os.path.abspath(cur) != lastabs:
            lastabs = os.path.abspath(cur)
            testpath = os.path.join(cur, fpath)
            if os.path.exists(testpath):
                return testpath
            if os.path.exists(os.path.join(cur, '.git')):
                break
            cur = os.path.join('..', cur)
    return None

def parse_modifiers(modifiers):
    '''Flatten a modifier list into a list of possible modifiers'''
    for m in modifiers.lower().split():
        resn = []
        reso = []
        for mod in m.lower().split('+'):
            if mod.endswith("?"):
                reso.append(mod)
            else:
                resn.append(mod)
        yield sorted(resn)
        for i in range(len(reso)):
            for c in itertools.combinations(reso, i):
                yield sorted(resn + list(c))

def process_basefile(basef):
    ''' recursively reads an ldml file building a keymap '''
    keymap = {}
    fname = find_file(basef)
    if fname is None:
        return {}
    doc = et.parse(fname)
    for c in doc.getroot():
        if c.tag == 'keyMap':
            if 'modifiers' in c.attrib:
                modifiers = ["+".join(x) for x in parse_modifiers(c.get('modifiers'))]
            else:
                modifiers = [""]
            for m in modifiers:
                if m not in keymap:
                    keymap[m] = {}
            if 'fallback' in c.attrib:
                fallbacks = ["+".join(x) for x in parse_modifiers(c.get('fallback'))]
                for f in fallbacks:
                    if f in keymap:
                        for m in modifiers:
                            keymap[m].update(keymap[f])
            for cm in c:
                if cm.tag == 'map':
                    for m in modifiers:
                        s = re.sub(r"\\u\{([0-9a-fA-F]+)\}|\\u([0-9A-Fa-f]{4,6})",
                                   lambda a: chr(int(a.group(a.lastindex), 16)), cm.get('to'))
                        keymap[m][cm.get('iso')] = OutputString([s])
        elif c.tag == 'import':
            overwrite_map(keymap, process_basefile(c.get('path')))
    return keymap

def make_transform(r, p, maps, bmaps, deadkeys, simples, finals, backups, prebases):
    if not len(r.before):
        return
    isdead = any(x for x in r.before if isinstance(x, DeadKey))
    for rf in r.flatten(p.allStores):
        bs = []
        for b in rf.before:
            bs.extend(b)
        btxt = "".join(bs)
        otxt = OutputString(rf.output)
        if args.debug & 4:
            otxt.comment = str(r)
        error = otxt.error
        try:
            k = mapkey(rf.match)
        except KeyError:
            continue
        if k is not None:
            if k[0] == 'bksp':
                if args.charreorder:
                    btxt = btxt.replace(args.charreorder, "\uFDDF")
                    backups[btxt] = otxt.replace(args.charreorder, "\uFDDF")
                else:
                    backups[btxt] = otxt
                continue
            mp = maps[k[1]]
            if k[0] not in mp and (k[1] not in bmaps or k[0] not in bmaps[k[1]]):
                mp[k[0]] = chr(DeadKey.missing)
                finals[chr(DeadKey.missing)] = ""
                DeadKey.increment()
            m = mp.get(k[0], bmaps[k[1]][k[0]])
            btxt += str(m)
        if btxt[0] in prebases and len(btxt) > 1 and str(otxt)[-1] == btxt[0] and str(otxt) != btxt:
            continue
        if args.charreorder is not None and btxt[0] == args.charreorder and btxt[1] in prebases \
                and len(btxt) > 2 and str(otxt)[-1] == btxt[1] and str(otxt) != btxt:
            continue
        if (any(x not in str(otxt) for x in btxt) and \
              any(x not in str(otxt) for x in (btxt.replace(args.charreorder, "") if args.charreorder else btxt))) or \
             str(otxt) == str(btxt): # skip reorderings
            if k is not None:
                if btxt not in simples:
                    simples[btxt] = otxt
            elif btxt not in finals:
                finals[btxt] = otxt

layermap = {"default": "", "shift": "shift", "leftctrl": "ctrlL", "rightctrl": "ctrlR",
            "ctrl": "ctrl", "leftalt": "altL", "rightalt": "altR", "lefctrl-rightalt": "altR+ctrlL",
            "ctrl-alt": "alt+ctrl"}
nonoutputkeys = set(("lshift", "rshift", "shift", "lcontrol", "lctrl", "rcontrol", "rctrl",
                    "ctrl", "lmenu", "lalt", "rmenu", "ralt", "alt", "altgr", "currencies",
                    "numerals", "shifted", "upper", "lower", "symbols", "bksp", "numlock",
                    "lopt", "ropt", "opt", "enter", "space"))
sparekeyCount = 1
def load_layout(jsfile):
    with codecs.open(jsfile, "r", encoding="utf-8") as f:
        linfo = json.load(f)
    return linfo

def preprocess_layout(linfo):
    allchars = set()
    for types in linfo.values():
        if "layer" not in types:
            continue
        for layer in types["layer"]:
            for r in layer["row"]:
                for c in r.get("text", ""):
                    allchars.add(c)
                for s in r.get("sk", []):
                    for c in s.get("text", ""):
                        allchars.add(c)
    return allchars

def process_layout(ldml, linfo, platform = {}, extras=False):
    layertype = platform['form']
    if layertype not in linfo:
        layertype = list(linfo.keys())[0]
    layers = dict((l["id"], i) for i, l in enumerate(linfo[layertype]["layer"]))
    jobs = set(["default"])
    jobsdone = set()
    while len(jobs):
        newjobs = set()
        for j in jobs:
            newjobs.update(process_layer(ldml, linfo, layertype, layers, j, extras))
            jobsdone.add(j)
        jobs = newjobs - jobsdone

def process_layer(ldml, linfo, layertype, layers, lid, extras):
    layer = linfo[layertype]["layer"][layers[lid]]
    mods = layermap.get(lid, lid)
    rows = []
    res = set()
    switches = []
    for r in layer["row"]:
        currrow = []
        rows.append(currrow)
        for k in r["key"]:
            if "id" not in k:
                continue
            kid, to = process_key(ldml, mods, k)
            longpress = []
            for sk in k.get("sk", []):
                (_, sto) = process_key(ldml, mods, sk, isSubKey=True)
                longpress.append(sto)
            if len(longpress):
                ldml.keyAddAttrs(mods, kid, {"longPress": " ".join(longpress)})
            if "width" not in k:
                currrow.append((kid, "100"))
            else:
                v = k["width"]
                if not re.match(r'[0-9]+$', v):
                    v = "100"
                currrow.append((kid, v))
            if "nextlayer" in k:
                res.add(k["nextlayer"])
                switches.append((kid, k["nextlayer"], k.get('text', '')))
    ldml.addLayer(rows, mods, switches, extras)
    return res

def process_key(ldml, mods, k, isSubKey=False):
    global sparekeyCount
    kid = ""
    if k["id"].startswith("K_"):
        vkey = VKey((k["id"],))
        vk = vkey.getkey()
        if "layer" in k:
            testmod = k["layer"]
        elif mods in layermap.values():
            testmod = mods
        else:
            testmod = ""
        to = ldml.mapKey(vk[0], layermap.get(testmod, testmod))
        if not isSubKey and vk[0] not in nonoutputkeys and (to == '' or testmod != mods):
            kid = "SK{:02}".format(sparekeyCount)
            sparekeyCount += 1
            ldml.addKey(mods, kid, to)
        else:
            kid = vk[0]
    elif k["id"].startswith("U_"):
        kid = k["id"].replace("_", "").lower()
        to = chr(int(k["id"][2:], 16))
        if not isSubKey:
            ldml.addKey(mods, kid, to)
    else:
        kid = k["id"].replace("_", "").lower()
        to = k.get("text", '')
    if to != '' and to != k.get("text", to):
        ldml.addDisplay(to, k["text"])
    return (kid, to)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile',help="Generated LDML file")
    parser.add_argument('-k','--kmn',help='Process kmn file')
    parser.add_argument('-l','--layout',help='Process layout .js file')
    parser.add_argument('-r','--reorder',action='store_true',help='Add reordering import')
    parser.add_argument('-R','--reorderfile',help='Specifies reorder file to import, can occur with -r for standard import')
    parser.add_argument('-i','--imprt',help='File to import at end of file')
    parser.add_argument('-b','--basefile',default='langs/e/en/en-us-win/en-us-win.xml',help='Base keyboard file')
    parser.add_argument('-L','--locale',default="und-Zyyy",help='Keyboard Locale identifier')
    parser.add_argument('-N','--name',help="Keyboard name")
    parser.add_argument('-f','--form',default='phone',help='form factor platform [phone]')
    parser.add_argument('-u','--ui',default='touch',help='User Interface platform [touch]')
    parser.add_argument('-O','--os',default='windows',help='Operating Systems platform [windows]')
    parser.add_argument('-F','--full',action="store_true",help="Output extra stuff")
    parser.add_argument('-C','--charreorder',help="Char in kmn that is inserted for reordering")
    parser.add_argument('-z','--debug',type=int,default=0)
    args = parser.parse_args()

    ldml = LDMLKeyboard(args.locale, args.basefile)

    platform = dict((x, getattr(args, x)) for x in ('form', 'ui', 'os'))

    if args.charreorder is not None:
        args.charreorder = chr(int(args.charreorder, 16))

    if args.kmn:
        p = load_kmn(args.kmn, platform)
        allchars = preprocess_kmn(p)
    if args.layout:
        linfo = load_layout(args.layout)
        allchars.update(preprocess_layout(linfo))
    DeadKey.set_excludes(allchars)

    if args.kmn:
        process_kmn(ldml, p, reorder=args.reorder,
                    reorderfile=args.reorderfile, base=args.basefile, name=args.name)

    if args.layout:
        process_layout(ldml, linfo, platform=platform, extras=args.full)

    if args.imprt is not None:
        ldml.addImport(args.imprt)

    with codecs.open(args.outfile, "w", encoding="utf-8") as f:
        ldml.serialize_xml(f.write, doctype='<!DOCTYPE keyboard SYSTEM "../dtd/ldmlKeyboard.dtd">')


if __name__ == "__main__":
    main()

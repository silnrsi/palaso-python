#!/usr/bin/python

from xml.etree import cElementTree as et
from io import StringIO
import re

def ETcanon(e, curr = 0, indent = 2) :
    n = len(e)
    if n :
        curr += indent
        children = sorted(e, key=lambda x: x.tag)
        for x in reversed(e) : e.remove(x)
        e.text = "\n" + (' ' * curr)
        for c in children :
            e.append(c)
            ETcanon(c, curr, indent)
            c.tail = "\n" + (' ' * (curr if len(e) < n else curr - indent))
        return e

class Style(dict) :
    def __init__(self, name, lang = None) :
        super(Style, self).__init__()
        self.name = name
        self.lang = lang

    def addToElement(self, parent) :
        s = et.SubElement(parent, 'style')
        prefs = " ".join(x + "=" + str(self[x]) for x in sorted(self.keys()))
        s.set('name', self.name)
        if not prefs and self.lang is None :
            parent.remove(s)
            return None
        if prefs : s.set('prefs', prefs)
        if self.lang : s.set('lang', self.lang)
        return s

class Test(object) :
    def __init__(self, name, text, cls = None, background = None, rtl = None, comment = None) :
        self.name = name
        self.text = text
        self.cls  = cls
        self.background = background
        self.rtl = rtl
        self.comment = comment

    def addToElement(self, parent, used) :
        e = et.SubElement(parent, 'test')
        if self.comment :
            c = et.SubElement(e, 'comment')
            c.text = self.comment
        t = et.SubElement(e, 'text')
        t.text = self.text
        e.set('label', self.name)
        if self.background : e.set('background', self.background)
        if self.rtl : e.set('rtl', 'True')
        if self.cls :
            e.set('class', self.cls)
            used.add(self.cls)
        return e

class Group(list) :
    def __init__(self, name, comment = None) :
        super(Group, self).__init__()
        self.name = name
        self.comment = comment

    def addToElement(self, parent, used) :
        e = et.SubElement(parent, 'testgroup')
        e.set('label', self.name)
        if self.comment :
            c = et.SubElement(e, 'comment')
            c.text = self.comment
        for t in self :
            t.addToElement(e, used)
        return e

class TestFile(object) :
    def __init__(self) :
        self.groups = []
        self.header = None
        self.styles = {}
    
    def fromFile(self, fname) :
        e = et.parse(fname)
        self.header = e.find('header')
        for s in self.header.iterfind('.//style') :
            n = s.get('name')
            st = Style(n, lang = s.get('lang'))
            self.styles[n] = st
            v = s.get('feats')
            if v is None : continue
            for ft in v.split(' ') :
                if '=' in ft :
                    (k1, v1) = ft.split('=')
                    st[k1] = int(v1)
        self.fontsrc = self.header.find
        for ge in e.iterfind('testgroup') :
            n = ge.get('label')
            ce = ge.find('comment')
            c = ce.text if ce is not None else None
            g = Group(n, c)
            self.groups.append(g)
            for t in ge.iterfind('test') :
                te = t.find('text')
                txt = te.text if te is not None else ""
                ce = t.find('comment')
                c = ce.text if ce is not None else ""
                g.append(Test(t.get('label'), txt, cls = t.get('class'),
                                background = t.get('background'), rtl = t.get('rtl'),
                                comment = c))
        return self

    def toFile(self, fname = None) :
        r = et.Element('testfile', {'version' : '1.0'})
        if self.header is not None :
            h = self.header
            r.append(h)
        else :
            h = et.SubElement(r, 'header')
        used = set()
        for g in self.groups :
            g.addToElement(r, used)
        s = h.find('styles')
        for k, v in self.styles.items() :
            if k not in used : del self.styles[k]
        if len(self.styles) :
            if s is not None :
                for x in reversed(s) : s.remove(x)
            else :
                s = et.SubElement(h, 'styles')
            for k in sorted(self.styles.keys()) :
                self.styles[k].addToElement(s)
        elif s :
            h.remove(s)
        sio = StringIO()
        sio.write('<?xml version="1.0" encoding="utf-8"?>\n')
        sio.write('<?xml-stylesheet type="text/xsl" href="Testing.xsl"?>\n')
        et.ElementTree(ETcanon(r)).write(sio, encoding="utf-8")
        res = sio.getvalue().replace(' />', '/>')
        sio.close()
        if fname :
            f = open(fname, "wb")
            f.write(res)
            f.close()
        else :
            return res

    def getFonts(self) :
        if not self.header : return []
        res = []
        t = self.header.findtext('fontsrc')
        for e in re.split(r'\s*,\s*', t) :
            m = re.match(r'local\(\s*([^)]+\s*)\)', e)
            if m :
                res.append(res.group(1))
                continue
            m = re.match(r'url\(\s*[^\s:]+://', e)
            if m : continue
            m = re.match(r'url\(\s*(.*?)\s*\)')
            if m :
                res.append(res.group(1))
                continue
        return res

if __name__ == "__main__" :
    import sys
    tests = TestFile().fromFile(sys.argv[1])
    tests.toFile(sys.argv[2])

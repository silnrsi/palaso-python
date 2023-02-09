#!/usr/bin/env python3

import argparse, tempfile, os, sys, re
from palaso.font.graphite import gr2
from palaso.font.shape import GrFont
from fontTools import ttLib
import json
from xml.etree import ElementTree as et
from collections import UserString
from palaso.font.glyphstring import Node, String, Position

class ManyStrings(UserString):
    def allStrings(self, musthave=""):
        s = self.data
        while (len(musthave) and musthave in s) or (not len(musthave) and len(s)):
            yield s
            s = s[:-1]

def runtext(face, text):
    (fd, debug) = tempfile.mkstemp()
    os.close(fd)
    gr2.gr_start_logging(face.grface.face, debug.encode("utf-8"))
    glyphs = face.glyphs(str(text), feats=getattr(text, 'feats', None), rtl=getattr(text, 'rtl', None))
    gr2.gr_stop_logging(face.grface.face)
    with open(debug) as fh:
        jobj = json.load(fh)
    os.unlink(debug)
    return (glyphs, jobj)

def makestring(face, text):
    glyphs, jobj = runtext(face, text)
    s = String(text=str(text))
    curr = s.pre
    for g in jobj[-1]['output']:
        if 'collision' in g:
            f = g['collision']['flags']
            if (f & 17) == 17: # and g['collision']['offset'] != [0, 0]:
                curr = s.addNode(Node(keys=[g['gid']], positions=[Position(*g['collision']['offset'])],
                                      index=g['charinfo']['original']), curr)
                continue
        curr = s.addNode(Node(keys=[g['gid']], index=g['charinfo']['original']), curr)
    return s

def parseFeat(f:str):
    m = re.match("""(['"])([a-zA-Z0-9]{4,4})\\1(?:\s+(\d+|on|off))?$""", f)
    if not m:
        raise ValueError(f'Invalid feature syntax: {f}')
    tag, value = m.group(2,3)
    value = 1 if value in (None, 'on') else 0 if value == 'off' else int(value)
    return (tag,value)

def parseftml(fnameorstr, feats=None):
    """parse an FTML document into a list ftmlstrings

    Args:
        root : ElementTree Element object representing FTML document
    Returns:
        list of ftmlstring objects, each representing one <test>, in document order

    Within <string> elements it removes <em> markup and converts backslash-u notation to Unicode characters.
    <testgroup> divisions are ignored and tests from all <testgroups> are collected together.
    """

    strs = []
    if os.path.exists(fnameorstr):
        root = et.parse(fnameorstr)
    else:
        root = et.fromstring(fnameorstr)
    for test in root.findall('.//test'):
        s = "".join(test.find('string').itertext())
        s = re.sub(r'\\u([a-fA-F0-9]{4,6})', lambda m: chr(int(m.group(1), 16)), s)
        stylename = test.get('stylename', None)
        if stylename is None:
            lfeats = None
            lang = None
        else:
            style = root.find(f'./head/styles/style[@name="{stylename}"]')
            lfeats = style.get('feats', None)
            if lfeats is not None:
                lfeats = dict(parseFeat(t.strip()) for t in lfeats.split(','))
                if feats is not None:
                    lfeats.update(feats)
            elif feats is not None:
                lfeats = feats
            else:
                lfeats = None
            lang = style.get('lang', None)
        rtl = test.get('rtl', "").lower() in ("true", "1")
        for w in s.split():
            s = UserString(w)
            s.feats = lfeats
            s.lang = lang
            s.rtl = rtl
            strs.append(s)
    return strs
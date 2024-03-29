#!/usr/bin/env python3

import os, sys, string
from xml.dom.minidom import *
import getopt
from palaso import kmn

_fontSize = 24
_font = 'Charis SIL'
_fontWeight = 'normal'
_unknown = ''

options = {
    'f': 'Charis SIL',
    's': '24',
    't': kmn.keyboard_template,
    'w': 'normal'
}

_codeMap = {
        'semi': ';',
        'slashf': '/',
        'tilde': '`',
        'sql': '[',
        'sqr': ']',
        'quote': "'",
        'comma': ',',
        'minus': '-',
        'period': '.',
        'equal':  '=',
        'slashb' : '\\'
}

_caseMap = {
    '`': '~',
    '1': '!',
    '2': '@',
    '3': '#',
    '4': '$',
    '5': '%',
    '6': '^',
    '7': '&',
    '8': '*',
    '9': '(',
    '0': ')',
    '-': '_',
    '=': '+',
    '[': '{',
    ']': '}',
    ';': ':',
    "'": '"',
    ',': '<',
    '.': '>',
    '/': '?',
    '\\': '|'
}

nonKeys = ('back', 'tab', 'capslock', 'enter', 'shiftl', 'shiftr', 'ctrll',
        'ctrlr', 'altl', 'altr', 'menu', 'winl', 'winr')

_keyMap = {}

def processFiles(keyboardFile,outputsvg):
    parseKeyboardFile(keyboardFile)
    processSVGFile(options['t'],outputsvg)

def parseKeyboardFile(file):
    global name
    dom = parse(file)
    kbd = dom.getElementsByTagName('keyboard')[0]
    name = kbd.getAttribute('name')
    m = kbd.getAttribute('modifiers')
    if m :
        name += " (" + m + ")"
    keys = dom.getElementsByTagName('key')
    for key in keys:
        keyId = key.getAttribute('id')
        keyId = keyId.lower();
        unshift = key.getAttribute('unshift')
        shift = key.getAttribute('shift')
        _keyMap[keyId] = (unshift, shift)
    # print(_keyMap)

def processSVGFile(file,outputsvg):
    global name
    dom = parse(file)
    if name :
        for t in dom.getElementsByTagName('text') :
            if t.getAttribute('id') == 'title' :
                span = t.getElementsByTagName('tspan')[0]
                span.replaceChild(dom.createTextNode(name), span.firstChild, )
    layers = dom.getElementsByTagName('g')
    for layer in layers:
        if layer.getAttribute('id') == 'labels':
            newLayer = layer.cloneNode(False)
            newLayer.setAttribute('inkscape:label', 'Key Overlay')
            newLayer.setAttribute('id', 'key_overlay')
            groups = layer.getElementsByTagName('g')
            for g in groups :
                rects = g.getElementsByTagName('rect')
                for rect in rects:
                    rectId = rect.getAttribute('id')
                    a = rectId.split('_', 1)
                    baseId = a[1]
                    if (baseId in _codeMap):
                        keyId = _codeMap[baseId]
                    else :
                        keyId = baseId
                    x = int(rect.getAttribute('x'))
                    y = int(rect.getAttribute('y'))

                    if (keyId in _keyMap):
                        (unshift, shift) = _keyMap[keyId]
                    elif keyId in nonKeys :
                        continue 
                    else:
                         unshift = _unknown
                         shift = _unknown

                    upperKey = _caseMap.get(keyId)
                    fontStyle = "font-size:%s;font-weight:%s;font-family:%s;" % (options['s'], options['w'], options['f'])
                    labelfontStyle = "font-size:%s;font-weight:%s;font-family:%s;" % (14, 'bold', 'Arial')
                    textDown = dom.createElement('text')
                    textDown.setAttribute('id', 'textd_' + baseId)
                    textDown.setAttribute('sodipodi:role', 'line')
                    textDown.setAttribute('style', fontStyle + 'fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1')
                    textDown.setAttribute('x', str(x + 25))
                    textDown.setAttribute('y', str(y + 50))
                    textDown.appendChild(dom.createTextNode(unshift))
                    g.appendChild(textDown)
                    textUp = dom.createElement('text')
                    textUp.setAttribute('id', 'textu_' + baseId)
                    textUp.setAttribute('sodipodi:role', 'line')
                    textUp.setAttribute('style', fontStyle + 'fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1')
                    textUp.setAttribute('x', str(x + 25))
                    textUp.setAttribute('y', str(y + 25))
                    textUp.appendChild(dom.createTextNode(shift))
                    g.appendChild(textUp)
                    # print(textDown.toxml())
                    textUpLabel = dom.createElement('text')
                    textUpLabel.setAttribute('id', 'textul_' + baseId)
                    textUpLabel.setAttribute('sodipodi:role', 'line')
                    textUpLabel.setAttribute('style', labelfontStyle + 'fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1')
                    textUpLabel.setAttribute('x', str(x + 5))
                    textUpLabel.setAttribute('y', str(y + 25))
                    textUpLabel.appendChild(dom.createTextNode(upperKey if upperKey else keyId.upper()))
                    g.appendChild(textUpLabel)

                    if upperKey != None :
                        textDownLabel = dom.createElement('text')
                        textDownLabel.setAttribute('id', 'textdl_' + baseId)
                        textDownLabel.setAttribute('sodipodi:role', 'line')
                        textDownLabel.setAttribute('style', labelfontStyle + 'fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1')
                        textDownLabel.setAttribute('x', str(x + 5))
                        textDownLabel.setAttribute('y', str(y + 50))
                        textDownLabel.appendChild(dom.createTextNode(keyId))
                        g.appendChild(textDownLabel)

            # print(newLayer.toprettyxml())
            dom.documentElement.appendChild(newLayer)  

            # print(dom.toprettyxml())
            outf = open(outputsvg, 'w')
            outf.write(dom.toxml('utf-8'))
            outf.close()
   
def usage():
    print("""%s [-f font] [-s point_size] [-w weight] [-t template.svg] input.xml output.svg
    -f font to use in svg file
    -s font point size
    -w font weight (defaults to normal)
    -t template .svg file (keyboard.svg)
    use inkscape to change svg into another format""" % (sys.argv[0]))
    
def main():
    try:
        optlist, args = getopt.getopt(sys.argv[1:], "hf:s:t:w:", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in optlist:
        options[o.replace('-', '')] = a
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) != 2:
        usage()
        sys.exit()
    processFiles(args[0], args[1])

if __name__ == "__main__":
#    processFiles('keyboard.svg', 'thailit.xml')
    main()


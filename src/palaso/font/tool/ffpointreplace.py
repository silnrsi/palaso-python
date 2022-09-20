#!/usr/bin/env python3

import fontforge
import argparse, os

def procvals(g, name, *vals) :
    anchors = []
    for a in g.anchorPoints :
        if a[0].startswith(name) and (a[1] == 'base' or a[1] == 'basemark') :
            anchors[int(a[0][len(name):])] = a[2:4]
    changed = False
    for i in range(len(vals)) :
        v = int(vals[i] * 10)
        if -10 < v < 10 :
            changed = True
            vals[i] = anchors[abs(v)][i & 1]
    if changed :
        return v
    else :
        return None
        

def main():
    parser = argparse.ArgumentParser(description='Replace magic values with point values')
    parser.add_argument('--prefix', default='val', help='Anchor point name prefix')
    parser.add_argument('infile', help='input font file')
    parser.add_argument('outfile', help='output font file')

    args = parser.parse_args()

    font = fontforge.open(os.path.abspath(args.infile))
    for n in font :
        g = font[n]
        for l in g.getPosSub('*') :
            if l[1] == 'Position' :
                v = procvals(g, args.prefix, *l[2:])
                if v :
                    g.addAnchor(l[0], l[1], *v)
            elif l[1] == 'Pair' :
                v = procvals(g, args.prefix, *l[3:7])
                w = procvals(font[l[2]], args.prefix, *l[7:])
                if v or w :
                    a = []
                    a.extend(v if v else l[3:7])
                    a.extend(w if w else l[7:])
                    g.addAnchor(l[0], l[1], l[2], *a)
    font.save(args.outfile)


if __name__ == "__main__":
    main()

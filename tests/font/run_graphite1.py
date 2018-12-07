#!/usr/bin/python

from palaso.font.graphite import Face, Font, Segment
import sys, os

face = Face(os.path.join(os.path.dirname(__file__), "Padauk-Regular.ttf"))
font = Font(face, 12 * 96 / 72.0)
seg = Segment(font, face, 0, sys.argv[1], 0)
for s in seg.slots :
    print "{0:d}({1[0]:f}, {1[1]:f}) ".format(s.gid, s.origin),


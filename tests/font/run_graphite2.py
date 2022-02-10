#!/usr/bin/python

from palaso.font.graphite import Face, Font, Segment
import os

face = Face(os.path.join(os.path.dirname(__file__), "Padauk.ttf"))
feats = face.get_featureval(0)
for r in face.featureRefs :
    name = r.name(0x0409)
    val = feats.get(r)
    print("{0} ({1})".format(name, val))

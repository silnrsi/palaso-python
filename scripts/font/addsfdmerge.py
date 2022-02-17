#!/usr/bin/env python3

import configparser, os, sys

conf = configparser.RawConfigParser(allow_no_value = 1)
base = os.path.abspath('.')
while base and not os.path.isdir(os.path.join(base, '.hg')) :
    base = os.path.split(base)[0]
if not base :
    sys.stderr.write("No mercurial directory found")
    sys.exit(1)

hgrc = os.path.join(base, '.hg', 'hgrc')
if os.path.isfile(hgrc) :
    conf.read(hgrc)

try:
    conf.set('merge-patterns', '**.sfd', 'sfdmerge')
except configparser.NoSectionError :
    conf.add_section('merge-patterns')
    conf.set('merge-patterns', '**.sfd', 'sfdmerge')

try:
    conf.set('merge-tools', 'sfdmerge.executable', 'sfdmerge')
except configparser.NoSectionError :
    conf.add_section('merge-tools')
    conf.set('merge-tools', 'sfdmerge.executable', 'sfdmerge')

conf.set('merge-tools', 'sfdmerge.args', '-r o $base $local $other $output')

inf = open(hgrc, 'w')
conf.write(inf)
inf.close()


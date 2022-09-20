#!/usr/bin/env python3

import urllib.request, urllib.parse, urllib.error, configparser, os, re
from optparse import OptionParser
from palaso.debian.sources import source_collection, getdistro, getbasever


def main():
    p = OptionParser(usage = "%prog [options] repo_url [package [package ...]]")
    p.set_defaults(distro = getdistro(), section = "main")
    p.add_option('-a', '--arch', help = 'Architecture to build for')
    p.add_option('-b', '--backport', action='store_true', help='add ~backport to version')
    p.add_option('-d', '--distro', help = 'distribution')
    p.add_option('-e', '--edits', help = 'config file giving control values per package')
    p.add_option('-l', '--list', action = 'store_true', help = 'Don\'t do anything, just list would be done')
    p.add_option('-n', '--newdistro', help = 'new distribution')
    p.add_option('-p', '--put' , help = 'dput target')
    p.add_option('-s', '--section', help = 'distribution section to process')
    (opts, args) = p.parse_args()
    host = args[0]

    url = f"{host}/dists/{opts.distro}/{opts.section}/source/Sources"
    x = source_collection(url)
    print(f"Found {len(x.sources)} packages in the original repository")

    y = source_collection(f"{host}/dists/{opts.newdistro}/{opts.section}/source/Sources")
    print(f"Found {len(y.sources)} packages in the target repository")

    edits = configparser.ConfigParser()
    if opts.edits :
        edits.read(opts.edits)
        
    for s in x.sources :
        if len(args) > 1 and s not in args[1:] : continue
        if s in y.sources : continue
        if edits.has_option(s, 'Remove') : continue
        src = x.sources[s]
        v = src['version']
        if edits.has_option(s, 'Version') :
            v = edits.get(s, 'Version') 
        newv = v.replace(opts.distro, opts.newdistro)
        if newv == v :
            if opts.backport :
                newv = v + "~backport"
            else :
                newv = v
            newv = newv + "+" + opts.newdistro + "1"
        basever = getbasever(v)
        print(f"{s!s}: {v!s}({basever!s}) -> {newv!s}")
        if opts.list : continue
        dir = "%s-%s" % (s, basever)
        x.download(s, dir, host)
        os.chdir(dir)
        cmd = f"dch --force-distribution -v '{newv}' -D {opts.newdistro} -m 'Transfer from {opts.distro}'"
        print(cmd)
        os.system(cmd)
        os.chdir("..")
        cmd = "dpkg-source"
        if edits.has_section(s) :
            for e in edits.items(s) :
                if e[0].lower() != 'version' :
                    cmd += " -D%s='%s'" % e
        cmd += f" -b {dir!r}"
        print(cmd)
        if os.system(cmd) == 0 :
            newv = re.sub(r"^\d:", "", newv)
            changes = f"'{s!s}_{newv}_source.changes'"
            os.chdir(dir)
            os.system(f"dpkg-genchanges -sa -S > ../{changes}")
            os.chdir('..')
            os.system(f"debsign -m'{os.environ['DEBEMAIL']}' {changes}")
            os.system(f"dput {opts.put} {changes}")
            print(f"dput {opts.put} {changes}")
        else :
            print(f"ERROR: BUILD {s!s} FAILED")
        os.system(f"rm -fr {dir!r}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import csv
import os
import re
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from optparse import OptionParser
from palaso.debian.sources import (
    source_collection,
    package_collection,
    arch_expects_bin,
    getdistro, getarch,
    getbasever)
from time import time, sleep

def load_packages(times, opts, host) :
    f = urllib.request.urlopen(host + "/dists/" + opts.distro + "/" + opts.section + "/binary-" + opts.arch + "/Packages")
    ptime = f.info().getdate('Last-modified')
    y = package_collection(f)
    f.close()
    for p in y.sources.values() :
        s = p.get('source') or p['package']
        if not s in times or times[s] < ptime : times[s] = ptime
    return (y, ptime)

def build_package(src, sources, opts, host, indep=True, updatep=False) :
    version = re.sub('^[0-9]+:', '', src['version'])
    if updatep :
        cmd = "sudo pbuilder --update --override-config --configfile " + opts.conf
        print(cmd)
        os.system(cmd)
    dir = "%s-%s" % (src['package'], getbasever(version))
    sources.download(src['package'], dir, host)
    os.chdir(dir)
    cmd = "pdebuild"
    if opts.conf : cmd += " --configfile " + opts.conf
    cmd += " --debbuildopts "
    if indep : cmd += "-b"
    else : cmd += "-B"
    cmd += " --buildresult .. -- --logfile ../" + src['package'] + ".log"
    print(cmd)
    state = os.system(cmd)
    os.chdir("..")
    if state == 0 :
        cmd = "debsign \"-e$DEBEMAIL\" %s_%s_%s.changes" % (src['package'], version, opts.arch)
        print(cmd)
        state = os.system(cmd)
    return state

def email(addr, fname, opts) :
    print(f"Email {addr} with {fname}")
    if opts.server != None :
        msg = MIMEMultipart()
        msg['Subject'] = 'Autobuild failure of %s on %s for %s' % (fname.replace(".log", ""), opts.arch, opts.distro)
        msg['From'] = opts.mfrom
        msg['To'] = addr
        msg.preamble = 'I tried to build this package and failed. Here is the build log. Can you help me out by submitting a fixed source package?\n\nThanks'
        fp = open(fname)
        addition = MIMEText(fp.read(), _subtype="x-log")
        fp.close()
        addition.add_header('Content-Disposition', 'attachment', filename=fname)
        msg.add(addition)

        server = smtplib.SMTP(opts.server)
        if opts.tls :  
            server.starttls()
        if opts.username :
            server.login(opts.username, opts.password)  
        server.sendmail(msg['From'], msg['To'], msg)  
        server.quit()

def dput(file, opts) :
    cmd = "dput " + opts.put + " " + file
    print(cmd)
    res = os.system(cmd)
    if res > 0 : return False
    else : return True

p = OptionParser(usage = "%prog [options] repo_url")
p.set_defaults(distro = getdistro(), arch = getarch(), section = 'main', wait = 1, conf = "~/.pbuilderrc", mfrom = os.getenv('DEBEMAIL'))
p.add_option('-a', '--arch', help = 'Architecture to build for')
p.add_option('-b', '--binary', action = 'store_true', help = 'only do binary builds, no all packages to be uploaded')
p.add_option('-c', '--conf', help = 'pdebuilder configfile')
p.add_option('-d', '--distro', help = 'distribution')
p.add_option('-f', '--failures', help = 'csv package,version of failed builds')
p.add_option('-l', '--list', action = 'store_true', help = 'Output list of packages and what needs to be done, but don\'t build anything')
p.add_option('-p', '--put' , help = 'dput target')
p.add_option('-s', '--section', help = 'distribution section to process')
p.add_option('-u', '--update', action = 'store_true', help = 'start by updating the pbuilder environment')
p.add_option('-w', '--wait', type = "int", help = 'repo updates this often (mins)')
p.add_option('--mail-server', dest = "server", help = 'mail server to send mail through')
p.add_option('--mail-from', dest = 'mfrom', help = "Send mail from this address")
p.add_option('--mail-tls', dest = 'tls', action = 'store_true', help = "Use TLS for mail connection")
p.add_option('--mail-user', dest = 'username', help = "username to use to login for mail connection")
p.add_option('--mail-pwd', dest = 'password', help = "password to login to mail server with, required if --mail-user given")
(opts, args) = p.parse_args()
host = args[0]

baseurl = f"{host}/dists/{opts.distro}/{opts.section}/source/Sources"
x = source_collection(baseurl)

times = {}
(y, ptime) = load_packages(times, opts, host)

if opts.failures != None :
    f = open(opts.failures)
    r = csv.reader(f)
    failures = dict(s for s in r)
    f.close()
else:
    failures = {}

res = x.all()
todo = []
buildindep = set()
for s in res :
    if opts.list :
        print(f"Testing {s}")
    for b in re.split(r"\s*,\s*", x.sources[s]['binary']) :
        if not b in y.sources and arch_expects_bin(opts.arch, b) :
            if len(todo) == 0 or todo[-1] != s : todo.append(s)
            if not opts.binary and (not b in y.sources or y.sources[b]['architecture'] == 'all') :
                buildindep.add(s)

for s in todo :
    print(f"Need to build {s}")
    if opts.list : continue
    src = x.sources[s]
    if s in failures and failures[s] == src['version'] : continue
    update_required = False
    skip = False
    if opts.update and s == todo[0] : update_required = True

    # do we have to wait and get a new packages due to dependency timings?
    for d in src.local_dependencies :
        if not d in times :
            print(f"Dependency for {s!s} unavailable, skipping.")
            skip = True
            break
        elif times[d] > ptime :
            sleep(times[d] - time() + 30)
            (y, ptime) = load_packages(times, opts, host)
            update_required = True
    if skip : continue

    state = build_package(src, x, opts, host, True if s in buildindep else False, update_required)
    print(f"Build result {state!s}")
    if state :
        email(src['maintainer'], src['package'] + ".log", opts)
    else :
        if dput(src['package'] + "_" + re.sub('^[0-9]+:', '', src['version']) + "_" + opts.arch + ".changes", opts) :
            times[s] = (int(time() / opts.wait / 60) + 1) * opts.wait * 60



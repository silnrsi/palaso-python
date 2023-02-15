
from debian_bundle.deb822 import Sources, Packages
from subprocess import Popen, PIPE
import re, itertools, os, subprocess, gzip, io, sys
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.parse, urllib.error

class unzipurlfile(gzip.GzipFile) :

    def __init__(self, f) :
        self.resf = io.StringIO()
        self.resf.write(f.read())
        self.resf.seek(0)
        super(unzipurlfile, self).__init__(fileobj = self.resf)

    def close(self) :
        super(unzipurlfile, self).close()
        self.resf.close()


class source_collection(object) :
    """Manages a Sources file of multiple source packages"""
    def __init__(self, seq) :
        self.sources = {}
        self.binaries = {}
        if isinstance(seq, (bytes, str)):
            url = seq
            f = urllib.request.urlopen(url)
            if f.getcode() >= 300 :
                f.close()
                fz = urllib.request.urlopen(url + ".gz")
                if fz.getcode() >= 300 :
                    fz.close()
                    print("Unable to open Sources file: " + url)
                    sys.exit(1)
                f = unzipurlfile(fz)
                fz.close()
            seq = f
        x = Sources(seq)
        while len(x) > 0 :
            if x['package'] not in self.sources or not subprocess.call(["dpkg", "--compare-versions", self.sources[x['package']]['version'], "lt", x['version']]):
                self.sources[x['package']] = x
                for b in re.split(r"\s*,\s*", x['binary']) :
                    self.binaries[b] = x['package']
            x = Sources(seq)
        if isinstance(seq, (bytes, str)) :
            f.close()

    def all(self) :
        """returns a list of source packages in dependency order. That is
        where a package has a build dependency on another package is
        guaranteed to be listed after the package it is dependent on."""
        todo = set()
        res = []
        done = {}
        for v in self.sources.values() :
            v.local_dependencies = set()
            for d in v.relations['build-depends'] :
                s = self.binaries.get(d[0]['name'])
                if s :
                    v.local_dependencies.add(s)
            if len(v.local_dependencies) > 0 :
                todo.add(v['package'])
            else :
                res.append([v['package']])
        res.sort(key = lambda x : x[0])
        for k in range(len(res)) : done[res[k][0]] = k
        oldtodolen = len(todo) + 1
        while oldtodolen > 0 and oldtodolen != len(todo) :
            oldtodolen = len(todo)
            for p in todo.copy() :
                r = None
                for b in self.sources[p].local_dependencies :
                    t = done.get(b)
                    if t == None :
                        r = None
                        break
                    elif r == None or t > r : r = t
                if not r == None :
                    res[r].append(p)
                    done[p] = r
                    todo.remove(p)
        return itertools.chain(*res)

    def download(self, spackage, dest, host) :
        src = self.sources[spackage]
        for f in src['files'] :
            name = f['name']
            if not os.path.exists(name) :
                (name, info) = urllib.request.urlretrieve(host + "/" + src['directory'] + "/" + name, name)
                print("Downloaded " + name)
            if name.endswith(".dsc") :
                dsc = name
        if os.path.exists(dest) :
            cmd = 'rm -fr ' + dest
            os.system(cmd)
        cmd = "dpkg-source -x " + dsc + " " + dest
        print(cmd)
        os.system(cmd)

class package_collection(object) :
    """Manages a Packages file of multiple binary packages"""
    def __init__(self, seq) :
        self.sources = {}
        x = Packages(seq)
        while len(x) > 0 :
            self.sources[x['package']] = x
            x = Packages(seq)

def arch_expects_bin(arch, package) :
    if not arch in ("amd64") :
        if package.startswith("lib32") : return False
    return True

def getdistro() :
    return Popen(["lsb_release", "-cs"], stdout = PIPE).communicate()[0].strip()

def getarch() :
    return re.findall(rb"^DEB_BUILD_ARCH=([^\n]*)", Popen(["dpkg-architecture"], stdout = PIPE).communicate()[0])[0]

def getbasever(version) :
    return re.sub(r"^(\d:)?(.*)[-].*?$", r"\2", version)

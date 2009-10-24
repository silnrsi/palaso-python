
from debian_bundle.deb822 import Sources
import re, itertools

class source_collection(object) :
    """Manages a Sources file of multiple source packages"""
    def __init__(self, seq) :
        self.sources = {}
        self.binaries = {}
        x = Sources(seq)
        while len(x) > 0 :
            self.sources[x['package']] = x
            for b in re.split("\s*,\s*", x['binary']) :
                self.binaries[b] = x['package']
            x = Sources(seq)

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
                    t = done[b]
                    if t == None :
                        r = None
                        break
                    elif r == None or t > r : r = t
                if not r == None :
                    res[r].append(p)
                    done[p] = r
                    todo.remove(p)
        print res
        return itertools.chain(*res)


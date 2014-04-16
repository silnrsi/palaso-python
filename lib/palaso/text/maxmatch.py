#!/usr/bin/python

class suffix(object) :
    def __init__(self, pref="") :
        if pref :
            self.words = [pref]
            self.unknowns = [1]
        else :
            self.words = []
            self.unknowns = []

    def copy(self) :
        res = suffix()
        res.words = list(self.words)
        res.unknowns = list(self.unknowns)
        return res

    def setword(self, t) :
        self.words[0] = t
        self.unknowns[0] = 0

    def addword(self, t) :
        self.words.insert(0, t)
        self.unknowns.insert(0, 0)

    def addprefix(self, t) :
        if self.unknowns[0] :
            self.words[0] = t + self.words[0]
        elif len(t) :
            self.words.insert(0, t)
            self.unknowns.insert(0, 1)

    def hasprefix(self) :
        return self.unknowns[0] == 1

    def cmp(self, o) :
        unks = "".join(self.words[i] if self.unknowns[i] else "" for i in range(len(self.words)))
        unko = "".join(o.words[i] if o.unknowns[i] else "" for i in range(len(o.words)))
        res = cmp(len(unks), len(unko))
        if res != 0 : return res
        res = cmp(sum(self.unknowns), sum(o.unknowns))
        if res != 0 : return res
        res = cmp(len(self.words), len(o.words))
        if res != 0 : return res
        res = cmp(len(self.words[0]), len(o.words[0]))
        return res

class WordBreak(object) :
    """Does dictionary based word breaking using maximal match algorithm"""

    def __init__(self, words) :
        """words is a set of strings"""
        self.words = words
        self.cache = {}
        self.lens = {}
        for w in words :
            self.lens[w[0]] = max(self.lens.get(w[0], 0), len(w))

    def breakwords(self, text, unknowns=None) :
        """breaks a given text string into a list of words. If unknowns is
           passed a list, it will be filled with 0 or 1 corresponding to each
           word returned where 0 means the word is known and 1 if the word
           consists of unrecognised text"""
        if len(text) < 2 : return [text]
        for i in range(1,len(text)) :
            self._makesuffix(text[-(i+1):])
        res = self.cache[text]
        if unknowns is not None : unknowns.extend(res.unknowns)
        return list(res.words)

    def _makesuffix(self, t) :
        if t in self.cache : return self.cache[t]
        tries = []
        top = min(len(t) - 1, self.lens.get(t[0], 1))
        if top == 0 :       # big speed up to short circuit here
            self.cache[t] = suffix(t)
            return self.cache[t]

        for i in range(1, top + 1) :
            if t[i:] in self.cache :
                s = self.cache[t[i:]].copy()
            else :
                s = suffix(t[i:])
            
            test = t[:i] + s.words[0]
            if s.hasprefix() and test in self.words :
                s.setword(test)
            elif t[:i] in self.words :
                s.addword(t[:i])
            else :
                s.addprefix(t[:i])
            tries.append(s)

        res = sorted(tries, cmp=lambda a,b: a.cmp(b))
        self.cache[t] = res[0]
        return res


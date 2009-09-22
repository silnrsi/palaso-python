from palaso.kmfl import kmfl
from palaso.kmn import items_to_keys
from random import choice
import sys

class Coverage :

    def __init__(self, fname) :
        self.kmfl = kmfl(fname)
        self.numrules = self.kmfl.num_rules()

    def create_sequences(self, input, cache = {}, mode = 'random') :
        for i in xrange(0, self.numrules) :
            res = self.kmfl.reverse_match(input, i, mode = mode)
            if res != None and len(res[1]) > 0:
                for output in res[1] :
                    if output[-1] >= 0x100FF00 : continue   # ignore specials
                    newinput = input[0:len(input) - res[0]] + output[:-1]
                    newstr = u"".join(unichr(i) for i in newinput)
                    if newstr != "" and newstr in cache :
                        for x in cache[newstr] :
                            yield x + [output[-1]]
                        continue
                    else :
                        cache[newstr] = []
                    if len(newinput) > 0 :
                        for x in self.create_sequences(newinput, cache = cache, mode = mode) :
                            cache[newstr].append(x)
                            yield x + [output[-1]]
                    else :
                        yield [output[0]]

    def find_input(self, string, mode = 'first1') :
        input = [ord(i) for i in string]
        for output in self.create_sequences(input, mode = mode) :
            yield items_to_keys(output)

    def coverage_test(self, mode = 'random') :
        cache = {}
        outputted = set()
        for i in xrange(0, self.numrules) :
#            print i, self.kmfl.rule(i)
            for c in self.kmfl.flatten_context(i, side = 'l', mode = mode) :
                if (c[-1] & 0xFFFF) > 0xFF00 : continue
#                print c
                if len(c) > 1 :
                    for output in self.create_sequences(c[:-1], cache = cache, mode = mode) :
                        res = items_to_keys(output + [c[-1]])
                        if not res in outputted :
                            outputted.add(res)
                            yield res
                else :
                    res = items_to_keys([c[-1]])
                    if not res in outputted :
                        outputted.add(res)
                        yield res


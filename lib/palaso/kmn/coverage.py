from palaso.kmfl import kmfl
from random import choice
import sys

class Coverage :

    def __init__(self, fname) :
        self.kmfl = kmfl(fname)
        self.numrules = self.kmfl.num_rules()

    def create_sequences(self, input, cache = {}, mode = 'first') :
        for i in xrange(0, self.numrules) :
            res = self.kmfl.reverse_match(input, i)
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

    def find_input(self, string, mode = 'first') :
        input = [ord(i) for i in string]
        for output in self.create_sequences(input, mode = mode) :
            yield self.item_to_keys(output)
            if mode == 'first' : break

    def coverage_test(self, mode = 'first') :
        cache = {}
        for i in xrange(0, self.numrules) :
            sys.stderr.write(str(i) + "\n")
            for c in self.kmfl.flatten_context(i, side = 'l') :
#                print c
                if len(c) > 1 :
                    for output in self.create_sequences(c[:-1], cache = cache, mode = mode) :
                        yield self.item_to_keys(output + [c[-1]])
                else :
                    yield self.item_to_keys([c[-1]])

    def item_to_keys(self, items) :
        res = u""
        for o in items :
            if o < 0xFFFFFF :
                res = res + unichr(o)
            elif o < 0x1FFFFFF :
                res = res + unichr(o - 0x1000000 - 32)
        return res

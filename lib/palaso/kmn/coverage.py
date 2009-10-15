from palaso.kmfl import kmfl
from palaso.kmn import items_to_keys
import sys
import collections

class Coverage :

    def __init__(self, fname) :
        self.kmfl = kmfl(fname)
        self.numrules = self.kmfl.num_rules()

    def create_sequences(self, input, mode = 'all', cache = None, history=None) :
        cache = cache or {}
        history = history or collections.defaultdict(list)
        for rule in xrange(0, self.numrules) :
            res = self.kmfl.reverse_match(input, rule, mode = mode)
            if not res: continue
            
            for output in res[1] :
                if output[-1] >= 0x100FF00 : continue   # ignore specials
                newinput = input[0:len(input) - res[0]] + output[:-1]
                newstr = u"".join(unichr(i) for i in newinput)
                if newstr and newstr in cache :
                    for x in cache[newstr] :
                        yield x + [output[-1]]
                    continue
                else :
                    cache[newstr] = []
                
                rule_history = history[rule]
                if newinput and (not rule_history or rule_history[-1] > len(newinput)):
                    rule_history.append(len(newinput))
                    for x in self.create_sequences(newinput, mode, cache, history) :
                        cache[newstr].append(x)
                        yield x + [output[-1]]
                    rule_history.pop()
                else :
                    yield [output[0]]

    def find_input(self, string, mode = 'first1') :
        input = [ord(i) for i in string]
        for output in self.create_sequences(input, mode = mode) :
            yield items_to_keys(output)

    def coverage_test(self, mode = 'all') :
        cache = {}
        outputted = set()
        for i in xrange(0, self.numrules) :
            for c in self.kmfl.flatten_context(i, side = 'l', mode = mode) :
                last_context_item = c[-1]
                if (last_context_item & 0xFFFF) > 0xFF00 : continue
                if len(c) > 1 :
                    for output in self.create_sequences(c[:-1], mode, cache) :
                        res = items_to_keys(output + [last_context_item])
                        if res not in outputted :
                            outputted.add(res)
                            yield res
                else :
                    res = items_to_keys([last_context_item])
                    if not res in outputted :
                        outputted.add(res)
                        yield res


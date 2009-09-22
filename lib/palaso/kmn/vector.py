from random import choice

class VectorIterator :

    def __init__(self, indices, mode = 'all') :
        self.indices = indices
        self.len = len(indices)
        self.mode = mode
        self.vector = [0] * self.len
        self.current = None
        for i in xrange(self.len) :
            if indices[i] != None :
                if self.current == None : self.current = i
                if (mode == 'random' and self.current != i) or mode == 'random1' :
                    self.vector[i] = choice(indices[i])
                else :
                    self.vector[i] = indices[i][0]

    def advance(self) :
        if self.mode == 'random1' or self.mode == 'first1' or self.current == None : return None
        if self.mode == 'all' :
            for i in xrange(self.len) :
                if self.indices[i] != None :
                    ind = self.indices[i].index(self.vector[i])
                    if ind < len(self.indices[i]) - 1 :
                        self.vector[i] = self.indices[i][ind + 1]
                        return self.vector
                    else :
                        self.vector[i] = self.indices[i][0]
            return None
        else :
            ind = self.indices[self.current].index(self.vector[self.current])
            if ind < len(self.indices[self.current]) - 1 :
                self.vector[self.current] = self.indices[self.current][ind + 1]
            else :
                self.vector[self.current] = self.indices[self.current][0]
                i = None
                for i in xrange(self.current + 1, self.len) :
                    if self.indices[i] != None :
                        self.current = i
                        self.vector[i] = self.indices[i][0]
                        break
                if i == None or i != self.current :
                    return None
            if self.mode == 'random' :
                for i in xrange(self.len) :
                    if self.indices[i] != None and self.current != i :
                        self.vector[i] = choice(self.indices[i])
        return self



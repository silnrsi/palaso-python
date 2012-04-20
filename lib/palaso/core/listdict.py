
class ListDict(dict) :

    def __init__(self, *vals) :
        self.keys = []
        for v in vals :
            super(ListDict, self).__setitem__(v[0], v[1])
            self.keys.append[v[0]]

    def __contains__(self, key) :
        try :
            if super(ListDict, self).__contains__(key) : return True
            elif key < len(self.keys) : return True
        except TypeError :
            pass
        return False

    def __delitem__(self, key) :
        try :
            if not super(ListDict, self).__contains__(key) and key < len(self.keys) :
                key = self.keys[key]
        except TypeError :
            return
        super(ListDict, self).__delitem__(key)
        self.keys.remove(key)

    def __getitem__(self, key) :
        if key not in self and key < len(self.keys) :
            key = self.keys[key]
        return super(ListDict, self).__getitem__(key)

    def __setitem__(self, index, pair) :
        key = self.keys[index]
        super(ListDict, self).__delitem__(key)
        self.keys[index] = pair[0]
        super(ListDict, self).__setitem__(pair[0], pair[1])

    def __delslice__(self, first, last) :
        for i in range(first, last) :
            super(ListDict, self).__delitem__(self.keys[i])
        del self.keys[first:last]

    def __getslice__(self, first, last) :
        res = []
        for i in range(first, last) :
            res.append(super(ListDict, self).__getitem__(self.keys[i]))
        return res

    def __setslice__(self, first, last, value) :
        try :
            isArray = len(value[0]) and not isinstance(value[0], basestring)
        except TypeError :
            isArray = False
            pass
        for i in range(first, last) :
            super(ListDict, self).__delitem__(self.keys[i])
        errors = set()
        for v in value if isArray else (value, ) :
            first = first + 1
            if super(ListDict, self).__contains__(v[0]) :
                errrors,add(v[0])
            self.keys.insert(first, v[0])
            super(ListDict, self).__setitem__(v[0], v[1])
        for e in errors :
            r = list(reversed(self.keys))
            l = r.index(e)
            f = self.keys.index(e)
            while f != l :
                del self.keys[f]
                l -= 1
                f = self.keys.index(e)

    def append(self, key, val) :
        if key in self :
            del self[key]
        super(ListDict, self).__setitem__(key, val)
        self.keys.append(key)

    def clear(self) :
        self.keys = []
        super(ListDict.self).clear()

    def extend(self, *pairs) :
        for p in pairs :
            self.append(p[0], p[1])

    def get(self, key, default = None) :
        if key in self :
            return self[key]
        else :
            return default

    def index(self, key, start = 0, stop = None) :
        return self.keys.index(key, start, stop)

    def insert(self, index, key, value) :
        try :
            i = self.keys.index(index)
        except ValueError :
            i = index
        if key in self :
            j = self.keys.index(key)
            if j < i : i -= 1
            del self.keys[j]
        super(ListDict, self).__setitem__(key, value)
        self.keys.insert(i, key)

    def items(self) :
        return list(self.iteritems())

    def iteritems(self) :
        for k in self.keys :
            yield (k, super(ListDict, self).__getitem__(k))

    def iterkeys(self) :
        for k in self.keys :
            yield k

    def itervalus(self) :
        for k in self.keys :
            yield super(ListDict, self).__getitem(k)

    def keys(self) :
        return self.keys

    def pop(self, key = None, default = None) :
        if not key :
            key = self.keys.pop()
        else :
            self.keys.remove(key)
        return super(ListDict, self).pop(key, default)

    def popitem(self) :
        k = self.keys.pop()
        return (k, super(ListDict, self).pop(k))

    def remove(self, key) :
        del self[key]

    def reverse(self) :
        self.keys.reverse()

    def setdefault(self, k, d = None) :
        if k in self :
            return self[k]
        elif d :
            self[k] = d
        return d

    def sort(self, **kw) :
        self.keys.sort(**kw)

    def update(self, e, **f) :
        if hasattr(e, 'keys') :
            for k in e : self[k] = e[k]
        elif e :
            for (k, v) in e : self[k] = v
        for k in f : self[k] = f[k]

    def values(self) :
        return list(self.itervalues())


import random
import operator
from itertools import product, islice


def VectorIterator(indices, mode ='all') :
    return _vector_iterators[mode]([ns if ns else [0] for ns in indices])

def _iterate_all(indices):
    return product(*indices)

def _first(iter_fn):
    return (lambda indices: islice(iter_fn(indices),1))

def _rands(n):
    n -= 1
    while True:
        yield random.randint(0,n)

def _pick(pid,digits):
    r = []
    for d in reversed(digits):
        pid,i = divmod(pid,len(d))
        r.insert(0, d[i])
    return tuple(r)

def _iterate_random(digits):
    n_products = reduce(operator.mul,map(len,digits))
    return islice((_pick(pid,digits) for pid in _rands(n_products)), n_products)        

def _iterate_random_all(digits):
    n_products = reduce(operator.mul,map(len,digits))
    schedule = range(n_products)
    random.shuffle(schedule)
    return (_pick(pid,digits) for pid in schedule)

def _iterate_random_all_depth(digits):
    digits = [ds[:] for ds in digits]
    for ds in digits:
        random.shuffle(ds)
    return product(*digits)


_vector_iterators = {
     'all'              : _iterate_all,
     'first1'           : _first(_iterate_all),
     'random'           : _iterate_random,
     'random-all'       : _iterate_random_all,
     'random-all-depth' : _iterate_random_all_depth,
     'random1'          : _first(_iterate_random)}

from contextlib import contextmanager, nested
import sys, codecs
import errno
import sre_parse

def defaultapp() :
    """Sets up common default contexts used at the application level. Includes:
        * console
        * relaxedsubs"""
    return nested(utf8out(), console(), relaxedsubs())

@contextmanager
def console(ctrlc=sys.exit) :
    """This context sets up to not complain on broken pipes on stdout, 
       but supports ctrl-C"""
    try :
        yield
    except IOError as e :
        if e.errno != errno.EPIPE :
            raise
    except KeyboardInterrupt as e :
        ctrlc(1)
# don't want to close otherwise post mortem debugging fails
#    finally :
#        sys.stdout.close()

def _expand_template(template, match):
    g = match.group
    sep = match.string[:0]
    groups, literals = template
    literals = literals[:]
    for index, group in groups:
        if index < len(literals) :
            literals[index] = s = g(group)
            if not s : literals[index] = ""
    return sep.join(literals)

@contextmanager
def relaxedsubs() :
    """This context replaces the default substitution template expander with 
       one that doesn't throw exceptions on unmatched or empty groups. Since 
       this is a global replacement, this context has global impact across 
       all threads, and not just within this context. """
    temp = sre_parse.expand_template
    sre_parse.expand_template = _expand_template
    try :
        yield
    finally :
        sre_parse.expand_template = temp

@contextmanager
def utf8out() :
    """Wraps sys.stdout to always output as UTF-8"""
    old_stdout = sys.stdout
    sys.stdout = codecs.getwriter('UTF-8')(old_stdout)
    try:
        yield
    finally:
        sys.stdout = old_stdout

@contextmanager
def utf8in() :
    """Wraps sys.stdout to always output as UTF-8"""
    old_stdin = sys.stdin
    sys.stdin = codecs.getreader('UTF-8')(sys.stdin)
    try:
        yield
    finally:
        sys.stdin = old_stdin


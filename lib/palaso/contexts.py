from contextlib import contextmanager
import sys
import errno

@contextmanager
def console(ctrlc=sys.exit) :
    try :
        yield
    except IOError as e :
        if e.errno != errno.EPIPE :
            raise
    except KeyboardInterrupt as e :
        ctrlc(1)
    finally :
        sys.stdout.close()

#!/usr/bin/env python3
'''
Created on Jul 1, 2009

@author: tim
'''
from palaso.teckit import compiler,engine

import codecs, contextlib, os, sys

class RoundTripError(UnicodeError): pass

def check_round_trip(mapping, data):
    if not isinstance(mapping, engine.Mapping): 
        raise TypeError("'mapping' is '%s' object: expected 'Mapping' object" % type(mapping))
    if not isinstance(data, str): 
        raise TypeError("'data' is '%s' object: expected a unicode str" % type(data))

    encoder = engine.Converter(mapping, False)
    decoder = engine.Converter(mapping, True)

    # Do all the coversions
    byte_data  = encoder.convert(data, True)
    data2      = decoder.convert(byte_data, True)
    byte_data2 = encoder.convert(data2, True)
    
    if data != data2:
        if byte_data == byte_data2:
            raise RoundTripError('unicode -> byte mapping is inconsistent')
        else:
            raise RoundTripError('unicode -> byte or byte -> unicode mapping is inconsistent')

@contextlib.contextmanager
def stage(title):
    try:
        sys.stdout.write(title + ': ')
        sys.stdout.flush()
        yield
    except:
        sys.stdout.write('FAILED\n')
        raise
    else:
        sys.stdout.write('OK\n')



def main(cmd, map_src, test_data, *argv):
    try:
        data = codecs.open(test_data,'rb','utf-8_sig').read()
    except IOError as err:
        sys.stderr.write("%s: cannot read test data: %s: '%s'\n" % (cmd, err.strerror, err.filename))
        sys.exit(1)
    
    try:
        src  = open(map_src,'rb').read()
        with stage('compiling %r' % map_src):
            mapping = compiler.compile(src)
    except IOError as err:
        sys.stderr.write("%s: cannot read TECKit source: %s: '%s'\n" % (cmd, err.strerror, err.filename))
        sys.exit(2)
    except compiler.CompilationError as msg:
        sys.stderr.write('%s: %r: %s\n' % (cmd, map_src, msg))
        sys.exit(3)
        
    
    try:
        with stage('checking roundtrip encoding'):
            check_round_trip(mapping, data)
    except RoundTripError as msg:
        sys.stderr.write('%s: %s: %r\n' % (cmd,msg,map_src))
    except err:
        sys.stderr.write("%s: %s\n" % (cmd,err))
    
if __name__ == '__main__':
    main(*sys.argv)
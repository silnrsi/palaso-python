from __future__ import with_statement

import unittest
import os.path
from palaso.teckit.compiler import compile, Opt
from palaso.teckit.engine   import Converter, Form, Mapping

class TestCompiler:
    def test_compilation(self):
        ref_map = Mapping(os.path.join('data',self.reference_file))
        source = open(os.path.join('data',self.source_file),'rb').read()
        com_map = compile(source, Opt.Compress if self.compress else 0)
        self.assertEqual(str(com_map), str(ref_map))
        self.assertEqual(com_map, ref_map,
                         'compiled %r (%scompressed) does not match reference %r' % 
                            (self.source_file, '' if self.compress else 'un', self.reference_file))
        del com_map
        del ref_map


class CompileGreekMapping(TestCompiler):
    mapping_name   = 'SIL-GREEK_GALATIA-2001 <-> UNICODE'
    source_file    = 'SILGreek2004-04-27.map'

class CompileGreekMappingUncrompressed(unittest.TestCase, CompileGreekMapping):
    reference_file = 'SILGreek2004-04-27.uncompressed.tec.orig'
    compress       = False

class CompileGreekMappingCompressed(unittest.TestCase, CompileGreekMapping):
    reference_file = 'SILGreek2004-04-27.tec.orig'
    compress       = True


if __name__ == "__main__":
    unittest.main()
    
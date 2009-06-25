from __future__ import with_statement

import unittest
import os.path
from palaso.teckit.compiler import compile, translate
from palaso.teckit.engine   import Converter, Form, Mapping

class TestCompiler:
    def test_compilation(self):
        if not hasattr(self, 'reference_file'): return
        ref_map = Mapping(os.path.join('data',self.reference_file))
        source  = open(os.path.join('data',self.source_file),'rb').read()
        com_map = compile(source, self.compress)
        self.assertEqual(str(com_map), str(ref_map))
        self.assertEqual(com_map, ref_map,
                         'compiled %r (%scompressed) does not match reference %r' % 
                            (self.source_file, '' if self.compress else 'un', self.reference_file))
        del com_map

    def test_translation(self):
        if not hasattr(self, 'reference_file_xml'): return
        ref_map = open(os.path.join('data',self.reference_file_xml)).read()
        source  = open(os.path.join('data',self.source_file),'rb').read()
        com_map = translate(source)
        self.assertEqual(com_map, ref_map,
                         'translated %r (xml) does not match reference %r' % 
                            (self.source_file, self.reference_file_xml))
        del com_map


class CompileGreekMapping(TestCompiler):
    mapping_name   = 'SIL-GREEK_GALATIA-2001 <-> UNICODE'
    source_file    = 'SILGreek2004-04-27.map'

class CompileGreekMappingUncrompressed(unittest.TestCase, CompileGreekMapping):
    reference_file = 'SILGreek2004-04-27.uncompressed.reference.tec'
    compress       = False

class CompileGreekMappingCompressed(unittest.TestCase, CompileGreekMapping):
    reference_file = 'SILGreek2004-04-27.reference.tec'
    compress       = True

class TranslateISO_8859_1_XML(unittest.TestCase, TestCompiler):
    source_file    = 'ISO-8859-1.map'
    reference_file_xml = 'ISO-8859-1.map.reference.xml'


if __name__ == "__main__":
    unittest.main()
    
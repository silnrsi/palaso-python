import unittest
import os.path
from palaso.teckit.compiler import compile, translate, CompilationError
from palaso.teckit.engine import Mapping


def resource(name):
    return os.path.join(os.path.dirname(__file__), 'data', name)

def open_resource(name):
    with open(resource(name),'rb') as f:
        res = f.read()
    return res


class Test:
    '''
    The Test class is here to soley to prevent these two base classes from
    being discovered as tests in their own right. These are shared
    implementations for suppling common test code to derived classes below.
    '''

    class Compiler(unittest.TestCase):
        reference_file: str
        source_file: str
        compress: bool = False

        def test_compilation(self):
            assert self.reference_file.endswith('.tec'), \
                'Not a complied reference file (.tec).'
            ref_map = Mapping(resource(self.reference_file))
            source  = open_resource(self.source_file)
            com_map = compile(source, self.compress)
            self.assertEqual(str(com_map), str(ref_map))
            self.assertEqual(
                com_map,
                ref_map,
                f'compiled {self.source_file!r}'
                f' ({"" if self.compress else "un"}compressed)'
                f' does not match reference {self.reference_file!r}')
            del com_map

    class Translator(unittest.TestCase):
        reference_file: str
        source_file: str

        def test_translation(self):
            assert self.reference_file.endswith('.xml'), \
                'Not a translated reference file (.xml).'
            ref_map = open_resource(self.reference_file_xml)
            source  = open_resource(self.source_file)
            com_map = translate(source)
            self.assertEqual(
                com_map,
                ref_map,
                f'translated {self.source_file!r} (xml) does not match'
                f' reference {self.reference_file!r}')
            del com_map


class CompileGreekMappingUncrompressed(Test.Compiler):
    source_file = 'SILGreek2004-04-27.map'
    reference_file = 'SILGreek2004-04-27.uncompressed.reference.tec'


class CompileGreekMappingCompressed(Test.Compiler):
    source_file = 'SILGreek2004-04-27.map'
    reference_file = 'SILGreek2004-04-27.reference.tec'
    compress = True


class TranslateISO_8859_1_XML(Test.Translator):
    source_file = 'ISO-8859-1.map'
    reference_file = 'ISO-8859-1.map.reference.xml'


class TestCompilerFailure(unittest.TestCase):
    def test_compile_fail(self):
        source = open_resource('ISO-8859-1.map.reference.xml')
        self.assertRaises(CompilationError, compile, source)

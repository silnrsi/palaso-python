import unittest
from . import resources
from palaso.teckit.compiler import compile, translate, CompilationError
from palaso.teckit.engine import Mapping


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
            ref_map = Mapping(resources / self.reference_file)  # type: ignore
            source = (resources / self.source_file).read_bytes()
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
            ref_map = (resources / self.reference_file).read_bytes()
            source = (resources / self.source_file).read_bytes()
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
        source = (resources / 'ISO-8859-1.map.reference.xml').read_bytes()
        self.assertRaises(CompilationError, compile, source)

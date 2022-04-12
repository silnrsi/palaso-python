from importlib import resources
import unittest
from . import pkg_data
from palaso.teckit.compiler import compile, translate, CompilationError
from palaso.teckit.engine import Mapping


class Test:
    '''
    The Test class is here to soley to prevent these two base classes from
    being discovered as tests in their own right. These are shared
    implementations for suppling common test code to derived classes below.
    '''

    class Compiler(unittest.TestCase):
        reference: str
        source: str
        compress: bool = False

        def test_compilation(self):
            assert self.reference.endswith('.tec'), \
                'Not a complied reference file (.tec).'
            with resources.as_file(pkg_data / self.reference) as path:
                ref_map = Mapping(path)  # type: ignore
            source = (pkg_data / self.source).read_bytes()
            com_map = compile(source, self.compress)
            self.assertEqual(str(com_map), str(ref_map))
            self.assertEqual(
                com_map,
                ref_map,
                f'compiled {self.source!r}'
                f' ({"" if self.compress else "un"}compressed)'
                f' does not match reference {self.reference!r}')
            del com_map

    class Translator(unittest.TestCase):
        reference: str
        source: str

        def test_translation(self):
            assert self.reference.endswith('.xml'), \
                'Not a translated reference file (.xml).'
            ref_map = (pkg_data / self.reference).read_bytes()
            source = (pkg_data / self.source).read_bytes()
            com_map = translate(source)
            self.assertEqual(
                com_map,
                ref_map,
                f'translated {self.source!r} (xml) does not match'
                f' reference {self.reference!r}')
            del com_map


class CompileGreekMappingUncrompressed(Test.Compiler):
    source = 'SILGreek2004-04-27.map'
    reference = 'SILGreek2004-04-27.uncompressed.reference.tec'


class CompileGreekMappingCompressed(Test.Compiler):
    source = 'SILGreek2004-04-27.map'
    reference = 'SILGreek2004-04-27.reference.tec'
    compress = True


class TranslateISO_8859_1_XML(Test.Translator):
    source_file = 'ISO-8859-1.map'
    reference_file = 'ISO-8859-1.map.reference.xml'


class TestCompilerFailure(unittest.TestCase):
    def test_compile_fail(self):
        source = (pkg_data / 'ISO-8859-1.map.reference.xml').read_bytes()
        self.assertRaises(CompilationError, compile, source)

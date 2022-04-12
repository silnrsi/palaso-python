from . import pkg_data

def load_tests(loader, tests, ignore):
    import doctest
    suite = doctest.DocFileSuite(
        'test_mapping.doctest',
        'test_engine_simple.doctest',
        globs={'resources': pkg_data},
        encoding='utf-8')
    tests.addTests(suite)
    return tests

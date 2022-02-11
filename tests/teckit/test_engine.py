
def load_tests(loader, tests, ignore):
    import doctest
    suite = doctest.DocFileSuite(
        'test_mapping.doctest',
        'test_engine_simple.doctest',
        encoding='utf-8')
    tests.addTests(suite)
    return tests

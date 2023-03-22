from doctest import DocTestSuite


def load_tests(loader, standard_tests, pattern):
    import unparse_html_element

    test_suite = DocTestSuite(unparse_html_element)
    standard_tests.addTests(test_suite)
    return standard_tests

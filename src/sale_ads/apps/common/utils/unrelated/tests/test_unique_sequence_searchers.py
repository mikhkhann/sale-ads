from doctest import DocTestSuite
from unittest import TestCase
from unittest.mock import patch

from unique_sequence_searchers import (
    UniqueSequenceSearcher,
    UniqueStringSearcher,
    find_unique_sequence,
    find_unique_string,
)


def load_tests(loader, standard_tests, pattern):
    import unique_sequence_searchers

    test_suite = DocTestSuite(unique_sequence_searchers)
    standard_tests.addTests(test_suite)
    return standard_tests


###############################################################################
# Searchers


class UniqueSequenceSearcherAdvanceItemIndicesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.searcher = UniqueSequenceSearcher(["a", "b", "c"], 5, [])

    def test_with_all_item_indices_not_last(self):
        item_indices = [0, 0, 0, 0, 0]
        self.searcher._advance_item_indices(item_indices, 4)
        self.assertEqual(item_indices, [0, 0, 0, 0, 1])

    def test_with_one_item_index_last(self):
        item_indices = [0, 0, 0, 0, 2]
        self.searcher._advance_item_indices(item_indices, 4)
        self.assertEqual(item_indices, [0, 0, 0, 1, 0])

    def test_with_all_item_indices_last(self):
        item_indices = [2, 2, 2, 2, 2]
        self.searcher._advance_item_indices(item_indices, 4)
        self.assertEqual(item_indices, [0, 0, 0, 0, 0])


###############################################################################
# Search functions


class SearchFunctionTextMixin:
    @classmethod
    @property
    def func(cls):
        raise NotImplementedError

    @classmethod
    @property
    def searcher_class(cls):
        raise NotImplementedError

    def test_delegates_to_searcher_class(self):
        args = [object() for i in range(100)]
        kwargs = {"test_kwarg_{i}": object() for i in range(100)}
        with (
            patch.object(
                self.searcher_class, "__init__", return_value=None
            ) as init_mock,
            patch.object(self.searcher_class, "find") as find_mock,
        ):
            result = type(self).func(*args, **kwargs)
        init_mock.assert_called_once_with(*args, **kwargs)
        find_mock.assert_called_once_with()
        self.assertIs(result, find_mock.return_value)


class FindUniqueSequenceTest(SearchFunctionTextMixin, TestCase):
    func = find_unique_sequence
    searcher_class = UniqueSequenceSearcher

    def test(self):
        result = find_unique_sequence([1, 2], 2, [[1, 1], [1, 2], [2, 2]])
        self.assertEqual(result, [2, 1])


class FindUniqueStringTest(SearchFunctionTextMixin, TestCase):
    func = find_unique_string
    searcher_class = UniqueStringSearcher

    def test(self):
        result = find_unique_string("ab", 2, ["aa", "ab", "bb"])
        self.assertEqual(result, "ba")

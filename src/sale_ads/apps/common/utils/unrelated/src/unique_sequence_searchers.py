from random import randrange
from typing import Callable, Collection, Container, Sequence, TypeVar

Item = TypeVar("Item")
Result = TypeVar("Result")


class UniqueSequenceNotFoundError(ValueError):
    pass


class UniqueSequenceSearcher:
    """
    Example:

    >>> items = [1, 2]
    >>> length = 2
    >>> existing = [[1, 1], [2, 2]]
    >>> searcher = UniqueSequenceSearcher(items, length, existing)
    >>> sorted(searcher.find_all())
    [[1, 2], [2, 1]]
    >>> searcher.find() # doctest: +SKIP
    [2, 1]
    >>> searcher.find() # doctest: +SKIP
    [2, 1]
    >>> searcher.find() # doctest: +SKIP
    [1, 2]
    >>>
    >>> items = [1, 2]
    >>> length = 2
    >>> existing = [[1, 1], [1, 2], [2, 1], [2, 2]]
    >>> searcher = UniqueSequenceSearcher(items, length, existing)
    >>> try:
    ...     searcher.find()
    ... except ValueError:
    ...     print("acceptable sequence wasn't found")
    acceptable sequence wasn't found
    >>> try:
    ...     searcher.find()
    ... except UniqueSequenceNotFoundError:
    ...     print("acceptable sequence wasn't found")
    acceptable sequence wasn't found
    >>>
    >>>
    >>> # ==========================================================
    >>> # `existing` parameter
    >>>
    >>> # --------------------------------------
    >>> # As callable
    >>>
    >>> existing = lambda: ([1, 1], [1, 2], [2, 1])
    >>> items = [1, 2]
    >>> length = 2
    >>> searcher = UniqueSequenceSearcher(items, length, existing)
    >>> list(searcher.find_all())
    [[2, 2]]
    >>>
    >>>
    >>> # ==========================================================
    >>> # `length` parameter
    >>>
    >>> length = [2, 1]
    >>> items = [1, 2]
    >>> existing = []
    >>> check = lambda sequence: print(sequence)
    >>> searcher = UniqueSequenceSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     first_random=False,
    ... )
    >>> list(searcher.find_all())
    [[1, 1], [1, 2], [2, 1], [2, 2], [1], [2]]
    >>>
    >>>
    >>> # ==========================================================
    >>> # `first_random` parameter
    >>>
    >>> items = [1, 2, 3]
    >>> length = 5
    >>> existing = []
    >>> searcher = UniqueSequenceSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     first_random=False,
    ... )
    >>> from itertools import islice
    >>> list(islice(searcher.find_all(), 3))
    [[1, 1, 1, 1, 1], [1, 1, 1, 1, 2], [1, 1, 1, 1, 3]]
    >>> list(islice(searcher.find_all(), 3))
    [[1, 1, 1, 1, 1], [1, 1, 1, 1, 2], [1, 1, 1, 1, 3]]
    >>> searcher.find(), searcher.find(), searcher.find()
    ([1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1])
    >>>
    >>>
    >>> # ==========================================================
    >>> # `prepare` parameter
    >>>
    >>> prepare = lambda sequence: [item * 10 for item in sequence]
    >>> items = [1, 2]
    >>> length = 2
    >>> existing = [[10, 10], [20, 20]]
    >>> searcher = UniqueSequenceSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     prepare=prepare,
    ... )
    >>> sorted(searcher.find_all())
    [[10, 20], [20, 10]]
    >>>
    >>>
    >>> # ==========================================================
    >>> # `check` parameter
    >>>
    >>> check = lambda sequence: sequence not in [[10, 10], [20, 20]]
    >>> items = [1, 2]
    >>> length = 2
    >>> existing = []
    >>> prepare = lambda sequence: [item * 10 for item in sequence]
    >>> searcher = UniqueSequenceSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     prepare=prepare,
    ...     check=check,
    ... )
    >>> sorted(searcher.find_all())
    [[10, 20], [20, 10]]
    """

    def __init__(
        self,
        items: Sequence[Item],
        length: int | Collection[int],
        existing: Container[Result] | Callable[[], Container[Result]],
        *,
        first_random: bool = True,
        prepare: Callable[[list[Item]], Result] = None,
        check: Callable[[Result], bool] = None
    ):
        self._items = items
        self._lengths = [length] if isinstance(length, int) else length
        self._existing = existing
        self._first_random = first_random
        self._prepare_func = prepare
        self._check_func = check
        self._item_count = len(items)

    def find_all(self):
        for length in self._lengths:
            yield from self._find_all_for_length(length)

    def find(self):
        try:
            return next(self.find_all())
        except StopIteration:
            raise UniqueSequenceNotFoundError from None

    def _find_all_for_length(self, length):
        start_item_indices = (
            [randrange(self._item_count) for index_in_sequence in range(length)]
            if self._first_random
            else [0] * length
        )
        item_indices = list(start_item_indices)
        while True:
            sequence = [self._items[i] for i in item_indices]
            sequence = self._prepare(sequence)
            if self._check(sequence) and self._is_sequence_unique(sequence):
                yield sequence
            self._advance_item_indices(item_indices, length - 1)
            if item_indices == start_item_indices:
                break

    def _advance_item_indices(self, item_indices, index_in_sequence):
        item_indices[index_in_sequence] += 1
        if item_indices[index_in_sequence] == self._item_count:
            item_indices[index_in_sequence] = 0
            if index_in_sequence:
                self._advance_item_indices(item_indices, index_in_sequence - 1)

    def _prepare(self, sequence):
        if self._prepare_func is not None:
            return self._prepare_func(sequence)
        return sequence

    def _check(self, sequence):
        if self._check_func is not None:
            return self._check_func(sequence)
        return True

    def _is_sequence_unique(self, sequence):
        existing = self._existing() if callable(self._existing) else self._existing
        return sequence not in existing


def find_unique_sequence(*args, **kwargs):
    """Shortcut for: `UniqueSequenceSearcher(*args, **kwargs).find()`"""
    return UniqueSequenceSearcher(*args, **kwargs).find()


class UniqueStringSearcher(UniqueSequenceSearcher):
    """
    All the parameters except `prepare` are the same as for
    UniqueSequenceSearcher.
    Example:

    >>> # ==============================================================
    >>> # Without `prepare` argument
    >>>
    >>> items = "ab"
    >>> length = 2
    >>> existing = ["aa", "bb"]
    >>> searcher = UniqueStringSearcher(items, length, existing)
    >>> sorted(searcher.find_all())
    ['ab', 'ba']
    >>>
    >>>
    >>> # ==============================================================
    >>> # With `prepare` argument as callable
    >>>
    >>> prepare = str.upper
    >>> items = "ab"
    >>> length = 2
    >>> existing = ["AA", "BB"]
    >>> searcher = UniqueStringSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     prepare=prepare,
    ... )
    >>> sorted(searcher.find_all())
    ['AB', 'BA']
    >>>
    >>>
    >>> # ==============================================================
    >>> # With `prepare` argument as template
    >>>
    >>> prepare = "_{}_"
    >>> items = "ab"
    >>> length = 2
    >>> existing = ["_aa_", "_bb_"]
    >>> searcher = UniqueStringSearcher(
    ...     items,
    ...     length,
    ...     existing,
    ...     prepare=prepare,
    ... )
    >>> sorted(searcher.find_all())
    ['_ab_', '_ba_']
    """

    def __init__(self, *args, prepare=None, **kwargs):
        if isinstance(prepare, str):
            template = prepare
            prepare_string = lambda string: template.format(string)
        elif prepare is None:
            prepare_string = lambda string: string
        else:
            prepare_string = prepare
        prepare = lambda sequence: prepare_string(str.join("", sequence))
        super().__init__(*args, prepare=prepare, **kwargs)


def find_unique_string(*args, **kwargs):
    """Shortcut for: `UniqueStringSearcher(*args, **kwargs).find()`"""
    return UniqueStringSearcher(*args, **kwargs).find()

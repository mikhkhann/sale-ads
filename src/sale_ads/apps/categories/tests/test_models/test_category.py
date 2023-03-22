from collections import Counter
from unittest.mock import Mock, patch

from django.db import models
from django.test import SimpleTestCase, TestCase

import categories.models
from ads.views import _AdListView
from categories.models import Category, _CategoryQuerySet
from common.tests import SaleAdsTestMixin
from common.tests.utils.doctest_in_unittest_mixin import DocTestInUnitTestMixin

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Primary key


class CategoryPKFromStringTest(SaleAdsTestMixin, TestCase):
    def test(self):
        category = self.create_category_factory().create()
        pk_as_string = str(category.pk)
        result = Category.pk_from_string(pk_as_string)
        self.assertEqual(result, category.pk)


# ==========================================================
# Canonical URL


class CategoryGetAbsoluteURLTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = cls.create_category_factory().create()

    def test(self):
        actual = self.category.get_absolute_url()
        expected = _AdListView.get_category_url(self.category.pk)
        self.assertURLEqual(actual, expected)

    def test_uses_ads_utils_get_category_ad_list_url(self):
        import ads.utils

        with patch.object(ads.utils, "get_category_ad_list_url", autospec=True) as mock:
            result = self.category.get_absolute_url()
        mock.assert_called_once_with(self.category.pk)
        self.assertEqual(result, mock.return_value)


# ==========================================================
# Admin


class CategoryStrTest(SaleAdsTestMixin, SimpleTestCase):
    def test(self):
        name_factory = self.create_category_name_factory()
        parent = Category(name=name_factory.get_unique())
        category = Category(name=name_factory.get_unique(), parent=parent)
        self.assertEqual(str(category), category.full_name)

    def test_uses_full_name(self):
        category = Category()
        mock = self.create_category_name_factory().get_unique()
        with (
            patch.object(Category, "full_name"),  # to be able to patch instance attr
            patch.object(category, "full_name", mock),
        ):
            result = str(category)
        self.assertEqual(result, mock)


# ==========================================================
# Utilities


class CategoryNameRelativeToTest(SaleAdsTestMixin, DocTestInUnitTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        name_factory = cls.create_category_name_factory()
        cls.ancestor_name = name_factory.get_unique()
        cls.child_name = name_factory.get_unique()
        cls.grandchild_name = name_factory.get_unique()
        cls.grandgrandchild_name = name_factory.get_unique()
        grandchild_relative_name = Category._concatenate_parent_and_child_names(
            cls.child_name, cls.grandchild_name
        )
        cls.grandgrandchild_relative_name = (
            Category._concatenate_parent_and_child_names(
                grandchild_relative_name, cls.grandgrandchild_name
            )
        )
        cls.non_ancestor_name = name_factory.get_unique()
        cls.root_name = name_factory.get_unique()
        cls.root_child_name = name_factory.get_unique()
        cls.root_grandchild_name = name_factory.get_unique()
        root_child_name_relative_to_none = Category._concatenate_parent_and_child_names(
            cls.root_name, cls.root_child_name
        )
        cls.root_grandchild_name_relative_to_none = (
            Category._concatenate_parent_and_child_names(
                root_child_name_relative_to_none, cls.root_grandchild_name
            )
        )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category_factory = cls.create_category_factory()

    def setUp(self):
        super().setUp()
        self.ancestor = self.category_factory.create(
            name=self.ancestor_name, parent=None, save=False
        )
        self.child = Category(name=self.child_name, parent=self.ancestor)
        self.grandchild = Category(name=self.grandchild_name, parent=self.child)
        self.grandgrandchild = Category(
            name=self.grandgrandchild_name, parent=self.grandchild
        )
        self.non_ancestor = self.category_factory.create(
            name=self.non_ancestor_name, save=False
        )
        self.root = Category(name=self.root_name)
        root_child = Category(name=self.root_child_name, parent=self.root)
        self.root_grandchild = Category(
            name=self.root_grandchild_name, parent=root_child
        )

    def test_with_direct_ancestor(self):
        result = self.child.name_relative_to(self.ancestor)
        self.assertEqual(result, self.child.name)

    def test_with_indirect_ancestor(self):
        result = self.grandgrandchild.name_relative_to(self.ancestor)
        self.assertEqual(result, self.grandgrandchild_relative_name)

    def test_with_pk_of_direct_ancestor(self):
        self.ancestor.save()
        result = self.child.name_relative_to(self.ancestor.pk)
        self.assertEqual(result, self.child.name)

    def test_with_pk_of_indirect_ancestor(self):
        self.ancestor.save()
        result = self.grandgrandchild.name_relative_to(self.ancestor.pk)
        self.assertEqual(result, self.grandgrandchild_relative_name)

    def test_with_none_on_root(self):
        result = self.root.name_relative_to(None)
        self.assertEqual(result, self.root.name)

    def test_with_none_on_non_root(self):
        result = self.root_grandchild.name_relative_to(None)
        self.assertEqual(result, self.root_grandchild_name_relative_to_none)

    def test_invalid_ancestor_error(self):
        expected = (
            f'Can\'t get the name of the "{self.ancestor.full_name}" category relative '
            f'to the "{self.non_ancestor.full_name}" category.'
        )
        with self.assertRaisesMessage(ValueError, expected):
            self.child.name_relative_to(self.non_ancestor)

    def test_invalid_ancestor_error_with_pk(self):
        self.non_ancestor.save()
        expected = (
            f'Can\'t get the name of the "{self.ancestor.full_name}" category relative '
            f"to the category with the primary key {repr(self.non_ancestor.pk)}."
        )
        with self.assertRaisesMessage(ValueError, expected):
            self.child.name_relative_to(self.non_ancestor.pk)

    def test_invalid_ancestor_error_uses_full_name(self):
        mock = self.create_category_name_factory().get_unique()
        with (
            patch.object(Category, "full_name"),  # to be able to patch instance attr
            patch.object(self.ancestor, "full_name", mock),
            self.assertRaises(ValueError) as error_cacher,
        ):
            self.child.name_relative_to(self.non_ancestor)
        self.assertIn(mock, str(error_cacher.exception))

    def test_with_indirect_ancestor_uses_concatenate_parent_and_child_names(self):
        with patch.object(
            Category, "_concatenate_parent_and_child_names", autospec=True
        ) as mock:
            result = self.grandchild.name_relative_to(self.ancestor)
        mock.assert_called_once_with(self.child.name, self.grandchild.name)
        self.assertEqual(result, mock.return_value)

    def test_docstring(self):
        self.doctest_object(Category.name_relative_to, vars(categories.models))


class CategoryCacheableReadOnlyPropertyTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.property_name = "test_property"
        cls.first_compute_result = object()
        cls.second_compute_result = object()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.non_cached_category = cls.create_category_factory().create()
        cls.cached_category = Category.objects.cache()[cls.non_cached_category.pk]

    def test_on_non_cached_category(self):
        compute = Mock(
            side_effect=[self.first_compute_result, self.second_compute_result]
        )
        property = Category._cacheable_readonly_property(compute)
        with self.patch(property):
            first_value = getattr(self.non_cached_category, self.property_name)
            second_value = getattr(self.non_cached_category, self.property_name)
        self.assertEqual(first_value, self.first_compute_result)
        self.assertEqual(second_value, self.second_compute_result)
        self.assertEqual(len(compute.mock_calls), 2)
        for actual_args, actual_kwargs in compute.call_args_list:
            self.assertEqual(list(actual_args), [self.non_cached_category])
            self.assertEqual(actual_kwargs, {})

    def test_on_cached_category(self):
        compute = Mock(
            side_effect=[self.first_compute_result, self.second_compute_result]
        )
        property = Category._cacheable_readonly_property(compute)
        with self.patch(property):
            first_value = getattr(self.cached_category, self.property_name)
            second_value = getattr(self.cached_category, self.property_name)
        self.assertEqual(first_value, self.first_compute_result)
        self.assertEqual(second_value, self.first_compute_result)
        compute.assert_called_once_with(self.cached_category)

    def test_on_class(self):
        property = Category._cacheable_readonly_property(Mock())
        with self.patch(property):
            value = getattr(Category, self.property_name)
        self.assertIs(value, property)

    # ==========================================================
    # Freezing

    def test_freezing_with_non_cached_category(self):
        compute = Mock()
        freeze = Mock()
        property = Category._cacheable_readonly_property(freeze=freeze)(compute)
        with self.patch(property):
            value = getattr(self.non_cached_category, self.property_name)
        compute.assert_called_once_with(self.non_cached_category)
        freeze.assert_not_called()
        self.assertEqual(value, compute.return_value)

    def test_freezing_with_cached_category(self):
        compute = Mock()
        freeze = Mock()
        property = Category._cacheable_readonly_property(freeze=freeze)(compute)
        with self.patch(property):
            value = getattr(self.cached_category, self.property_name)
        self.assertEqual(value, freeze.return_value)
        compute.assert_called_once_with(self.cached_category)
        freeze.assert_called_once_with(compute.return_value)

    def test_freezing_func_attr(self):
        # The attribute is tested in order to the tests of the instances
        # of the property were able to just check the attribute to test
        # whether the property freezes on cached categories
        freeze = Mock()
        property = Category._cacheable_readonly_property(freeze=freeze)(Mock())
        self.assertEqual(property._freeze, freeze)

    # ==========================================================
    # Docstring

    def test_docstring(self):
        docstring = "test docstring"

        def compute(self):
            pass

        compute.__doc__ = docstring
        property = Category._cacheable_readonly_property(compute)
        with self.patch(property):
            self.assertEqual(property.__doc__, docstring)

    # ==========================================================

    class patch:
        def __init__(self, property):
            self._property = property
            self._patch = patch.object(
                Category,
                CategoryCacheableReadOnlyPropertyTest.property_name,
                property,
                create=True,
            )

        def __enter__(self):
            self._patch.__enter__()
            self._property.__set_name__(
                Category, CategoryCacheableReadOnlyPropertyTest.property_name
            )
            return self._patch

        def __exit__(self, *args):
            return self._patch.__exit__(*args)


class CategoryConcatenateParentAndChildNamesTest(SaleAdsTestMixin, SimpleTestCase):
    def test(self):
        name_factory = self.create_category_name_factory()
        parent_name = name_factory.get_unique()
        child_name = name_factory.get_unique()
        actual = Category._concatenate_parent_and_child_names(parent_name, child_name)
        expected = f"{parent_name}{Category._NON_BREAKING_SPACE}/ {child_name}"
        self.assertEqual(actual, expected)


# ==========================================================
# Data attributes


class CategoryAllChildrenTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category_factory = cls.create_category_factory()
        cls.non_cached_branch = cls.category_factory.create()
        cls.children = tuple(
            Category.objects.bulk_create(
                cls.category_factory.create(parent=cls.non_cached_branch, save=False)
                for i in range(2)
            )
        )
        cls.non_cached_leaf = next(iter(cls.children))
        category_cache = Category.objects.cache()
        cls.cached_branch = category_cache[cls.non_cached_branch.pk]
        cls.cached_leaf = category_cache[cls.non_cached_leaf.pk]

    def test_on_non_cached_branch(self):
        value = self.non_cached_branch.all_children
        self.assertIsInstance(value, models.QuerySet)
        self.assertQuerysetEqual(value, self.children, ordered=False)

    def test_on_non_cached_leaf(self):
        value = self.non_cached_leaf.all_children
        self.assertIsInstance(value, models.QuerySet)
        self.assertFalse(value.exists())

    def test_on_non_cached_category_does_not_cache(self):
        self.assertQuerysetEqual(
            self.non_cached_branch.all_children, self.children, ordered=False
        )
        new_child = self.category_factory.create(parent=self.non_cached_branch)
        self.assertQuerysetEqual(
            self.non_cached_branch.all_children,
            [*self.children, new_child],
            ordered=False,
        )

    def test_on_cached_branch(self):
        value = self.cached_branch.all_children
        self.assertIsInstance(value, frozenset)
        self.assertDictEqual(Counter(value), Counter(self.children))

    def test_on_cached_leaf(self):
        value = self.cached_leaf.all_children
        self.assertIsInstance(value, frozenset)
        self.assertEqual(len(value), 0)

    def test_on_cached_category_caches(self):
        first_value = self.cached_branch.all_children
        self.category_factory.create(parent=self.cached_branch)
        self.assertEqual(self.cached_branch.all_children, first_value)


class CategoryDescendantsTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        cls.category_with_descendants = category_factory.create()
        chilren = Category.objects.bulk_create(
            category_factory.create(parent=cls.category_with_descendants, save=False)
            for i in range(2)
        )
        grandchilren = Category.objects.bulk_create(
            category_factory.create(parent=parent, save=False)
            for parent in chilren
            for i in range(2)
        )
        cls.descendants = (*chilren, *grandchilren)
        cls.category_without_descendants = next(iter(grandchilren))

    def test_computation_with_descendants(self):
        value = self.category_with_descendants.descendants
        self.assertDictEqual(Counter(value), Counter(self.descendants))

    def test_computation_without_descendants(self):
        self.assertEqual(len(self.category_without_descendants.descendants), 0)

    def test_on_non_cached_category_is_set(self):
        self.assertIsInstance(self.category_with_descendants.descendants, set)

    def test_is_cacheable_readonly_property(self):
        self.assertIsInstance(
            Category.descendants, Category._cacheable_readonly_property
        )

    def test_freezes_on_cached_category_to_frozenset(self):
        self.assertIs(Category.descendants._freeze, frozenset)


class CategoryFullNameTest(SaleAdsTestMixin, DocTestInUnitTestMixin, SimpleTestCase):
    def test_computation(self):
        name_factory = self.create_category_name_factory()
        parent = Category(name=name_factory.get_unique())
        category = Category(name=name_factory.get_unique(), parent=parent)
        self.assertEqual(category.full_name, category.name_relative_to(None))

    def test_computation_uses_name_relative_to(self):
        category = Category()
        with patch.object(category, "name_relative_to", autospec=True) as mock:
            value = category.full_name
        mock.assert_called_once_with(None)
        self.assertEqual(value, mock.return_value)

    def test_is_cacheable_readonly_property(self):
        self.assertIsInstance(Category.full_name, Category._cacheable_readonly_property)

    def test_docstring(self):
        self.doctest_object(Category.full_name, vars(categories.models))


class CategoryLowercasedFullNameTest(SaleAdsTestMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        name_factory = self.create_category_name_factory()
        self.root = Category(name=name_factory.get_unique(), parent=None)
        self.root_child = Category(name=name_factory.get_unique(), parent=self.root)

    def test_computation_on_root(self):
        self.assertEqual(self.root.lowercased_full_name, self.root.lowercased_name)

    def test_computation_on_root_uses_lowercased_name(self):
        with (
            patch.object(
                Category, "lowercased_name"
            ),  # to be able to patch instance attr
            patch.object(self.root, "lowercased_name") as mock,
        ):
            value = self.root.lowercased_full_name
        self.assertEqual(value, mock)

    def test_computation_on_non_root(self):
        actual = self.root_child.lowercased_full_name
        expected = Category._concatenate_parent_and_child_names(
            self.root.lowercased_full_name, self.root_child.lowercased_name
        )
        self.assertEqual(actual, expected)

    def test_computation_on_non_root_uses_parent_lowercased_full_name(self):
        property = Category.lowercased_full_name
        mock = self.create_category_name_factory().get_unique()
        with (
            patch.object(
                Category, "lowercased_full_name"
            ),  # to be able to patch instance attr
            patch.object(self.root, "lowercased_full_name", mock),
        ):
            value = property.__get__(self.root_child)
        self.assertIn(mock, value)

    def test_computation_on_non_root_uses_lowercased_name(self):
        mock = self.create_category_name_factory().get_unique()
        with (
            patch.object(
                Category, "lowercased_name"
            ),  # to be able to patch instance attr
            patch.object(self.root_child, "lowercased_name", mock),
        ):
            value = self.root_child.lowercased_full_name
        self.assertIn(mock, value)

    def test_computation_on_non_root_uses_concatenate_parent_and_child_names(self):
        with patch.object(
            Category, "_concatenate_parent_and_child_names", autospec=True
        ) as mock:
            value = self.root_child.lowercased_full_name
        mock.assert_called_once_with(
            self.root.lowercased_full_name, self.root_child.lowercased_name
        )
        self.assertEqual(value, mock.return_value)

    def test_is_cacheable_readonly_property(self):
        self.assertIsInstance(
            Category.lowercased_full_name, Category._cacheable_readonly_property
        )


class CategoryLowercasedNameTest(SaleAdsTestMixin, SimpleTestCase):
    def test_computation(self):
        name = "TEST NAME"
        self.create_category_name_factory().check(name)
        category = Category(name=name)
        self.assertEqual(category.lowercased_name, name.lower())

    def test_is_cacheable_readonly_property(self):
        self.assertIsInstance(
            Category.lowercased_name, Category._cacheable_readonly_property
        )


class CategorySortedChildrenTest(SaleAdsTestMixin, TestCase):
    def test_computation_on_branch(self):
        category_factory = self.create_category_factory()
        branch = category_factory.create()
        name_factory = self.create_category_name_factory()
        child_C, child_D, child_a, child_b = Category.objects.bulk_create(
            category_factory.create(
                name=name_factory.get_unique(prefix=name_prefix),
                parent=branch,
                save=False,
            )
            for name_prefix in "CDab"
        )
        self.assertEqual(
            list(branch.sorted_children), [child_a, child_b, child_C, child_D]
        )

    def test_computation_on_leaf(self):
        leaf = self.create_category_factory().create()
        self.assertEqual(len(leaf.sorted_children), 0)

    def test_is_cacheable_readonly_property(self):
        self.assertIsInstance(
            Category.sorted_children, Category._cacheable_readonly_property
        )

    def test_freezes_on_cached_category_to_tuple(self):
        self.assertIs(Category.sorted_children._freeze, tuple)


###############################################################################
# Queryset


# ==========================================================
# Unit tests


# --------------------------------------
# Utilities


class CategoryQuerySetCacheTest(SaleAdsTestMixin, DocTestInUnitTestMixin, TestCase):
    def test(self):
        category_factory = self.create_category_factory()
        non_cached_categories = Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(2)
        )
        result = Category.objects.all().cache()
        self.assertEqual(len(result), len(non_cached_categories))
        for non_cached_category in non_cached_categories:
            cached_category = result[non_cached_category.pk]
            self.assertEqual(cached_category, non_cached_category)

    def test_docstring(self):
        self.doctest_object(_CategoryQuerySet.cache, vars(categories.models))

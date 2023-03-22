from collections import Counter

from django.test import TestCase

from ads.forms import AdForm
from categories.models import Category
from common.tests import SaleAdsTestMixin


class AdFormRelatedTestMixin:
    def create_form(self, *args, **kwargs):
        return AdForm(*args, category_cache=Category.objects.cache(), **kwargs)


###############################################################################
# Integration tests


# ==========================================================
# Validation


# --------------------------------------
# Category


class AdFormCategoryValidationTest(AdFormRelatedTestMixin, SaleAdsTestMixin, TestCase):
    def test(self):
        category_factory = self.create_category_factory()
        category, unused_category = Category.objects.bulk_create(
            category_factory.create(ultimate=True, save=False) for i in range(2)
        )
        form = self.create_form({"category": str(category.pk)})
        form.full_clean()
        self.assertEqual(form.cleaned_data["category"], category)


###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Category


class AdFormCategoryChoicesTest(AdFormRelatedTestMixin, SaleAdsTestMixin, TestCase):
    def test_items(self):
        category_factory = self.create_category_factory()
        category_name_factory = self.create_category_name_factory()
        first_generation_categories = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(), ultimate=True, save=False
            )
            for i in range(2)
        )
        second_generation_categories = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(),
                parent=parent,
                ultimate=True,
                save=False,
            )
            for parent in first_generation_categories
        )
        form = self.create_form()
        actual = form.fields["category"].choices
        expected = [
            (category.pk, category.full_name)
            for category in first_generation_categories + second_generation_categories
        ]
        self.assertDictEqual(Counter(actual), Counter(expected))

    def test_is_sorted_by_full_name(self):
        category_factory = self.create_category_factory()
        category_name_factory = self.create_category_name_factory()
        a, b, c, d = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(prefix=name_prefix), save=False
            )
            for name_prefix in "abcd"
        )
        c_d, d_c, a_b, b_a = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(prefix=name_prefix),
                parent=parent,
                ultimate=True,
                save=False,
            )
            for parent, name_prefix in zip([c, d, a, b], "dcba")
        )
        form = self.create_form()
        actual_choices = form.fields["category"].choices
        actual_values = list(zip(*actual_choices))[0]
        expected_values = [category.pk for category in [a_b, b_a, c_d, d_c]]
        self.assertEqual(list(actual_values), expected_values)

    def test_is_sorted_case_insensitively(self):
        category_factory = self.create_category_factory()
        category_name_factory = self.create_category_name_factory()
        C, D, a, b = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(prefix=name_prefix),
                ultimate=True,
                save=False,
            )
            for name_prefix in "CDab"
        )
        form = self.create_form()
        actual_choices = form.fields["category"].choices
        actual_values = list(zip(*actual_choices))[0]
        expected_values = [category.pk for category in [a, b, C, D]]
        self.assertEqual(list(actual_values), expected_values)

    def test_excludes_non_ultimate(self):
        category_factory = self.create_category_factory()
        category_name_factory = self.create_category_name_factory()
        non_ultimate_category, ultimate_category = Category.objects.bulk_create(
            category_factory.create(
                name=category_name_factory.get_unique(), ultimate=ultimate, save=False
            )
            for ultimate in [False, True]
        )
        form = self.create_form()
        choices = form.fields["category"].choices
        values = list(zip(*choices))[0]
        self.assertDictEqual(Counter(values), Counter([ultimate_category.pk]))


# ==========================================================
# Utilities


class AdFormCreateNewWithCleanedAsInitial(
    AdFormRelatedTestMixin, SaleAdsTestMixin, TestCase
):
    def test(self):
        category_pk = self.create_category_factory().create(ultimate=True).pk
        price = self.create_ad_price_factory().get_unique()
        form = self.create_form({"category": str(category_pk), "price": str(price)})
        form.full_clean()
        actual = form.create_initial_from_cleaned()
        expected = {"category": category_pk, "price": price}
        self.assertEqual(actual, expected)

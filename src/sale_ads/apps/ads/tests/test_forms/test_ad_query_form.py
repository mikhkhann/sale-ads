import itertools
from collections import Counter
from collections.abc import Iterable
from importlib import import_module
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.utils.translation import get_language, get_language_info

from ads.forms import AdQueryForm
from categories.models import Category
from common.tests import SaleAdsTestMixin
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)
from common.tests.utils.http_request_query_comparison import HTTPRequestQueryTestMixin

###############################################################################
# Mixins


class AdQueryFormRelatedTestMixin(CompositeLanguagesSettingTestMixin):
    @classmethod
    def get_language_combinations(cls, number):
        field = cls.create_ad_query_form().fields["languages"]
        languages = list(zip(*field.choices))[0]
        non_empty_combinations = itertools.chain.from_iterable(
            itertools.combinations(languages, length)
            for length in range(len(languages), 0, -1)
        )
        default = set(AdQueryForm._get_default_languages())
        non_default_non_empty_combinations = filter(
            lambda languages: set(languages) != default, non_empty_combinations
        )
        return itertools.islice(non_default_non_empty_combinations, number)

    @classmethod
    def get_languages(cls):
        (languages,) = cls.get_language_combinations(1)
        return languages

    @classmethod
    def get_invalid_language(cls):
        return cls.create_ad_entry_language_factory().get_invalid()

    @classmethod
    def get_order_values(cls, number):
        field = cls.create_ad_query_form().fields["order"]
        orders = list(zip(*field.choices))[0]
        non_default_orders = set(orders) - {AdQueryForm._DEFAULT_ORDER}
        return list(non_default_orders)[:number]

    @classmethod
    def get_order(cls):
        (order,) = cls.get_order_values(1)
        return order

    @classmethod
    def get_invalid_order(cls):
        invalid_order = "invalid order"
        field = cls.create_ad_query_form().fields["order"]
        orders = list(zip(*field.choices))[0]
        assert invalid_order not in orders
        return invalid_order

    @classmethod
    def get_page_size_values(cls, number):
        field = cls.create_ad_query_form().fields["page_size"]
        sizes = list(zip(*field.choices))[0]
        non_default_sizes = set(sizes) - {AdQueryForm._DEFAULT_PAGE_SIZE}
        return list(non_default_sizes)[:number]

    @classmethod
    def get_page_size(cls):
        (size,) = cls.get_page_size_values(1)
        return size

    @classmethod
    def get_invalid_page_size(cls):
        field = cls.create_ad_query_form().fields["page_size"]
        sizes = list(zip(*field.choices))[0]
        return max(sizes) + 1

    @classmethod
    def get_search_values(cls, number):
        return [f"test search {i}" for i in range(number)]

    @classmethod
    def get_search(cls):
        (search,) = cls.get_search_values(1)
        return search

    @classmethod
    def get_search_field_combinations(cls, number):
        field = cls.create_ad_query_form().fields["search_fields"]
        search_fields = list(zip(*field.choices))[0]
        non_empty_combinations = itertools.chain.from_iterable(
            itertools.combinations(search_fields, length)
            for length in range(len(search_fields), 0, -1)
        )
        default = set(AdQueryForm._DEFAULT_SEARCH_FIELDS)
        non_default_non_empty_combinations = filter(
            lambda value: set(value) != default, non_empty_combinations
        )
        return itertools.islice(non_default_non_empty_combinations, number)

    @classmethod
    def get_search_fields(cls):
        (search_fields,) = cls.get_search_field_combinations(1)
        return search_fields

    @classmethod
    def get_invalid_search_field(cls):
        invalid_search_field = "invalid search field"
        field = cls.create_ad_query_form().fields["search_fields"]
        search_fields = list(zip(*field.choices))[0]
        assert invalid_search_field not in search_fields
        return invalid_search_field

    @classmethod
    def get_min_price_values(cls, number):
        prices = []
        field = cls.create_ad_query_form().fields["min_price"]
        min_value = field.min_value
        price_factory = cls.create_ad_price_factory()
        for addition in range(100, 100 + number):
            price = round(min_value + addition)
            price_factory.check(price)
            prices.append(price)
        return prices

    @classmethod
    def get_min_price(cls):
        (price,) = cls.get_min_price_values(1)
        return price

    @classmethod
    def get_invalid_min_price(cls):
        field = cls.create_ad_query_form().fields["min_price"]
        return round(field.min_value - 100)

    @classmethod
    def get_max_price_values(cls, number):
        prices = []
        field = cls.create_ad_query_form().fields["max_price"]
        external_limit = 10 ** (field.max_digits - field.decimal_places)
        price_factory = cls.create_ad_price_factory()
        for deduction in range(100, 100 + number):
            price = external_limit - deduction
            price_factory.check(price)
            prices.append(price)
        return prices

    @classmethod
    def get_max_price(cls):
        (price,) = cls.get_max_price_values(1)
        return price

    @classmethod
    def get_invalid_max_price(cls):
        field = cls.create_ad_query_form().fields["max_price"]
        return 10 ** (field.max_digits - field.decimal_places)

    @classmethod
    def get_limit_price_values(cls, number):
        min_prices = cls.get_min_price_values(number)
        max_prices = cls.get_max_price_values(number)
        assert max(min_prices) < min(max_prices)
        return min_prices, max_prices

    @classmethod
    def get_limit_prices(cls):
        (min_price,), (max_price,) = cls.get_limit_price_values(1)
        return min_price, max_price

    @classmethod
    def create_ad_query_form(cls, *args, **kwargs):
        return cls.create_query_form_factory().create(*args, **kwargs)

    @classmethod
    def create_query_form_factory(cls):
        return AdQueryForm.Factory(get_category_cache=Category.objects.cache)


class AdQueryFormTestMixin(AdQueryFormRelatedTestMixin):
    create_form = AdQueryFormRelatedTestMixin.create_ad_query_form


###############################################################################
# Integration tests


# ==========================================================
# Validation


class AdQueryFormFieldValidationTestMixin(
    AdQueryFormTestMixin, HTTPRequestQueryTestMixin
):
    @classmethod
    def create_form(cls, data=None, *args, value=None, **kwargs):
        if value is not None:
            if data is None:
                data = {}
            value = (
                list(map(str, value))
                if isinstance(value, Iterable) and not isinstance(value, str)
                else str(value)
            )
            data[AdQueryForm.URL_PARAMETERS[cls.field]] = value
        return super().create_form(data, *args, **kwargs)

    def _test(self, inputted, expected):
        form = self.create_form({}, value=inputted)
        actual = getattr(form, f"cleaned_{self.field}")
        self.assertHTTPRequestParameterEqual(actual, expected)


# --------------------------------------
# Categories


class AdQueryFormCategoriesValidationTest(
    AdQueryFormFieldValidationTestMixin, SaleAdsTestMixin, TestCase
):
    field = "categories"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pk_factory = getattr(cls, f"create_category_{Category._meta.pk.name}_factory")()
        cls.invalid_pk = pk_factory.get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        *categories, unused_category = Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(3)
        )
        cls.categories = tuple(categories)

    def test_with_valid_pks(self):
        self._test([category.pk for category in self.categories], self.categories)

    def test_with_invalid_pk(self):
        self._test([self.invalid_pk], [])

    def test_with_non_sequence(self):
        self._test(object(), [])

    def test_without_pks(self):
        self._test(None, [])

    def test_with_valid_and_invalid_pks(self):
        category = next(iter(self.categories))
        self._test([self.invalid_pk, category.pk], [category])


# --------------------------------------
# Languages


class AdQueryFormLanguagesValidationTest(
    AdQueryFormFieldValidationTestMixin, SaleAdsTestMixin, TestCase
):
    field = "languages"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.languages = tuple(cls.get_languages())
        cls.invalid_language = cls.get_invalid_language()

    def test_with_valid_languages(self):
        self._test(self.languages, self.languages)

    def test_with_invalid_language(self):
        self._test([self.invalid_language], AdQueryForm._get_default_languages())

    def test_with_invalid_language_uses_get_default_languages(self):
        with patch.object(AdQueryForm, "_get_default_languages", autospec=True) as mock:
            self._test([self.invalid_language], mock.return_value)
        mock.assert_called_once_with()

    def test_with_non_sequence(self):
        self._test(object(), AdQueryForm._get_default_languages())

    def test_with_non_sequence_uses_get_default_languages(self):
        with patch.object(AdQueryForm, "_get_default_languages", autospec=True) as mock:
            self._test(object(), mock.return_value)
        mock.assert_called_once_with()

    def test_without_languages(self):
        self._test(None, AdQueryForm._get_default_languages())

    def test_without_languages_uses_get_default_languages(self):
        with patch.object(AdQueryForm, "_get_default_languages", autospec=True) as mock:
            self._test(None, mock.return_value)
        mock.assert_called_once_with()

    def test_with_valid_and_invalid_languages(self):
        self._test([self.invalid_language, *self.languages], self.languages)


# --------------------------------------
# Order


class AdQueryFormOrderValidationTest(AdQueryFormFieldValidationTestMixin, TestCase):
    field = "order"

    def test_with_valid_order(self):
        order = self.get_order()
        self._test(order, order)

    def test_with_invalid_order(self):
        self._test(self.get_invalid_order(), AdQueryForm._DEFAULT_ORDER)

    def test_without_order(self):
        self._test(None, AdQueryForm._DEFAULT_ORDER)


# --------------------------------------
# Page size


class AdQueryFormPageSizeValidationTest(AdQueryFormFieldValidationTestMixin, TestCase):
    field = "page_size"

    def test_with_valid_page_size(self):
        page_size = self.get_page_size()
        self._test(page_size, page_size)

    def test_with_invalid_page_size(self):
        self._test(self.get_invalid_page_size(), AdQueryForm._DEFAULT_PAGE_SIZE)

    def test_without_page_size(self):
        self._test(None, AdQueryForm._DEFAULT_PAGE_SIZE)


# --------------------------------------
# Search


class AdQueryFormSearchValidationTest(AdQueryFormFieldValidationTestMixin, TestCase):
    field = "search"

    def test_with_value(self):
        search = self.get_search()
        self._test(search, search)

    def test_without_value(self):
        self._test(None, "")


# --------------------------------------
# Search fields


class AdQueryFormSearchFieldsValidationTest(
    AdQueryFormFieldValidationTestMixin, TestCase
):
    field = "search_fields"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.search_fields = tuple(cls.get_search_fields())
        cls.invalid_search_field = cls.get_invalid_search_field()

    def test_with_valid_search_fields(self):
        self._test(self.search_fields, self.search_fields)

    def test_with_invalid_search_field(self):
        self._test([self.invalid_search_field], AdQueryForm._DEFAULT_SEARCH_FIELDS)

    def test_with_non_sequence(self):
        self._test(object(), AdQueryForm._DEFAULT_SEARCH_FIELDS)

    def test_without_search_fields(self):
        self._test(None, AdQueryForm._DEFAULT_SEARCH_FIELDS)

    def test_with_valid_and_invalid_search_fields(self):
        inputted = [self.invalid_search_field, *self.search_fields]
        expected = self.search_fields
        self._test(inputted, expected)


# --------------------------------------
# Limit prices


class AdQueryFormLimitPriceValidationTestMixin(AdQueryFormFieldValidationTestMixin):
    def test_with_valid_limit_price(self):
        price = self.get_valid_price()
        self._test(price, price)

    def test_with_invalid_limit_price(self):
        self._test(self.get_invalid_price(), None)

    def test_without_limit_price(self):
        self._test(None, None)


# Min price


class AdQueryFormMinPriceValidationTest(
    AdQueryFormLimitPriceValidationTestMixin, SaleAdsTestMixin, TestCase
):
    field = "min_price"

    def get_valid_price(self):
        return self.get_min_price()

    def get_invalid_price(self):
        return self.get_invalid_min_price()


# Max price


class AdQueryFormMaxPriceValidationTest(
    AdQueryFormLimitPriceValidationTestMixin, SaleAdsTestMixin, TestCase
):
    field = "max_price"

    def get_valid_price(self):
        return self.get_max_price()

    def get_invalid_price(self):
        return self.get_invalid_max_price()


# All


class AdQueryFormValidationMinPriceIsLessThanOrEqualToMaxPriceCheckTest(
    AdQueryFormTestMixin, SaleAdsTestMixin, TestCase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.min_price, cls.max_price = cls.get_limit_prices()

    def test_with_min_less_than_max(self):
        self._test(
            inputted_min=self.min_price,
            inputted_max=self.max_price,
            expected_min=self.min_price,
            expected_max=self.max_price,
        )

    def test_with_min_equal_to_max(self):
        self._test(
            inputted_min=self.min_price,
            inputted_max=self.min_price,
            expected_min=self.min_price,
            expected_max=self.min_price,
        )

    def test_with_min_greater_than_max(self):
        self._test(
            inputted_min=self.max_price,
            inputted_max=self.min_price,
            expected_min=None,
            expected_max=self.min_price,
        )

    def test_without_min(self):
        self._test(
            inputted_max=self.max_price, expected_min=None, expected_max=self.max_price
        )

    def test_without_max(self):
        self._test(
            inputted_min=self.min_price, expected_min=self.min_price, expected_max=None
        )

    def _test(
        self, *, expected_min, expected_max, inputted_min=None, inputted_max=None
    ):
        data = {}
        if inputted_min is not None:
            data[AdQueryForm.URL_PARAMETERS["min_price"]] = str(inputted_min)
        if inputted_max is not None:
            data[AdQueryForm.URL_PARAMETERS["max_price"]] = str(inputted_max)
        form = self.create_form(data)
        form.cleaned_min_price
        form.cleaned_max_price
        self.assertEqual(form.cleaned_min_price, expected_min)
        self.assertEqual(form.cleaned_max_price, expected_max)


###############################################################################
# Unit tests


# ==========================================================
# Fields


class AdQueryFormGetInitialFieldValueFromCleanedTestMixin(
    AdQueryFormTestMixin, HTTPRequestQueryTestMixin
):
    @classmethod
    @property
    def field(cls):
        raise NotImplementedError

    def _test(self, cleaned, expected):
        form = self.create_form()
        if cleaned is not None:
            setattr(form, f"cleaned_{self.field}", cleaned)
        actual = getattr(form, f"_get_initial_{self.field}_from_cleaned")()
        self.assertHTTPRequestParameterEqual(actual, expected)


class AdQueryFormFieldHTMLNamesTest(SimpleTestCase):
    def test_differ(self):
        used = []
        for parameter in AdQueryForm.URL_PARAMETERS.values():
            self.assertNotIn(parameter, used)
            used.append(parameter)


# --------------------------------------
# Categories


class AdQueryFormCategoryChoicesTest(AdQueryFormTestMixin, SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_name_factory = cls.create_category_name_factory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category_factory = cls.create_category_factory()

    def test_items(self):
        first_generation_categories = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "ab"
        )
        second_generation_categories = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                parent=parent,
                save=False,
            )
            for parent, name_prefix in zip(first_generation_categories, "cd")
        )
        form = self.create_form()
        actual = form.fields["categories"].choices
        expected = [
            (category.pk, category.full_name)
            for category in first_generation_categories + second_generation_categories
        ]
        self.assertDictEqual(Counter(actual), Counter(expected))

    def test_in_unbound_forms_initial_first(self):
        a, b, c, d = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "cdab"
        )
        initial_categories_pks = [b.pk, d.pk]
        form = self.create_form(initial={"categories": initial_categories_pks})
        actual_choices = form.fields["categories"].choices
        actual_values = list(zip(*actual_choices))[0]
        self.assertEqual(set(actual_values[:2]), set(initial_categories_pks))

    def test_in_unbound_forms_initial_sorted_by_full_name(self):
        a, b, c, d = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "abcd"
        )
        c_a, a_b, d_c, b_d = initial_categories = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                parent=parent,
                save=False,
            )
            for parent, name_prefix in [(c, "a"), (a, "b"), (d, "c"), (b, "d")]
        )
        form = self.create_form(
            initial={"categories": [category.pk for category in initial_categories]}
        )
        actual_choices = form.fields["categories"].choices
        actual_values = list(zip(*actual_choices))[0]
        actual_initial_values = actual_values[: len(initial_categories)]
        expected_initial_values = [category.pk for category in [a_b, b_d, c_a, d_c]]
        self.assertEqual(list(actual_initial_values), expected_initial_values)

    def test_in_unbound_forms_initial_sorted_case_insensitively(self):
        C, D, a, b = categories = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "CDab"
        )
        form = self.create_form(
            initial={"categories": [category.pk for category in categories]}
        )
        actual_choices = form.fields["categories"].choices
        actual_values = list(zip(*actual_choices))[0]
        expected_values = [category.pk for category in [a, b, C, D]]
        self.assertEqual(list(actual_values), expected_values)

    def test_in_unbound_forms_non_initial_sorted_by_full_name(self):
        a, b, c, d = initial_categories = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "abcd"
        )
        c_a, a_b, d_c, b_d = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                parent=parent,
                save=False,
            )
            for parent, name_prefix in [(c, "a"), (a, "b"), (d, "c"), (b, "d")]
        )
        form = self.create_form(
            initial={"categories": [category.pk for category in initial_categories]}
        )
        actual_choices = form.fields["categories"].choices
        actual_values = list(zip(*actual_choices))[0]
        actual_non_initial_values = actual_values[len(initial_categories) :]
        expected_non_initial_values = [category.pk for category in [a_b, b_d, c_a, d_c]]
        self.assertEqual(list(actual_non_initial_values), expected_non_initial_values)

    def test_in_unbound_forms_non_initial_sorted_case_insensitively(self):
        C, D, a, b = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(prefix=name_prefix),
                save=False,
            )
            for name_prefix in "CDab"
        )
        form = self.create_form()
        actual_choices = form.fields["categories"].choices
        actual_values = list(zip(*actual_choices))[0]
        expected_values = [category.pk for category in [a, b, C, D]]
        self.assertEqual(list(actual_values), expected_values)


class AdQueryFormGetInitialCategoriesFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "categories"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        cls.categories = tuple(
            Category.objects.bulk_create(
                category_factory.create(save=False) for i in range(2)
            )
        )

    def test_with_categories(self):
        self._test(self.categories, [category.pk for category in self.categories])

    def test_without_categories(self):
        self._test(None, [])


# --------------------------------------
# Languages


class AdQueryFormLanguageChoicesTest(AdQueryFormTestMixin, TestCase):
    def test(self):
        with self.settings(LANGUAGE_PREFERENCE_ORDER=["de", "fr"]):
            form = self.create_form()
            actual = list(form.fields["languages"].choices)
        expected = [
            ("de", get_language_info("de")["name_local"]),
            ("fr", get_language_info("fr")["name_local"]),
        ]
        self.assertEqual(actual, expected)


class AdQueryFormGetDegaultLanguagesTest(SimpleTestCase):
    def test(self):
        result = AdQueryForm._get_default_languages()
        self.assertEqual(list(result), [settings.LANGUAGE_CODE])

    def test_uses_django_utils_translation_get_language(self):
        module = import_module(AdQueryForm._get_default_languages.__module__)
        self.assertIs(module.get_language, get_language)
        with patch.object(module, "get_language", autospec=True) as mock:
            result = AdQueryForm._get_default_languages()
        mock.assert_called_once_with()
        self.assertEqual(list(result), [mock.return_value])


class AdQueryFormGetInitialLanguagesFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "languages"

    def test(self):
        cleaned = self.get_languages()
        expected = list(cleaned)
        self._test(cleaned, expected)


# --------------------------------------
# Order


class AdQueryFormOrderEnumStrTest(SimpleTestCase):
    def test(self):
        order = next(iter(AdQueryForm.Order))
        self.assertEqual(str(order), str(order.value))


class AdQueryFormOrderEnumFromStringTest(SimpleTestCase):
    def test(self):
        order = next(iter(AdQueryForm.Order))
        order_as_string = str(order)
        self.assertEqual(AdQueryForm.Order.from_string(order_as_string), order)


class AdQueryFormOrderChoicesTest(AdQueryFormTestMixin, TestCase):
    def test_values_are_orders(self):
        form = self.create_form()
        choices = form.fields["order"].choices
        values = list(zip(*choices))[0]
        self.assertDictEqual(Counter(values), Counter(AdQueryForm.Order))


class AdQueryFormDefaultOrderTest(SimpleTestCase):
    def test(self):
        self.assertIsInstance(AdQueryForm._DEFAULT_ORDER, AdQueryForm.Order)


class AdQueryFormGetInitialOrderFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "order"

    def test(self):
        order = self.get_order()
        self._test(order, order)


# --------------------------------------
# Page size


class AdQueryFormDefaultPageSizeTest(AdQueryFormTestMixin, TestCase):
    def test_is_choice_value(self):
        form = self.create_form()
        choices = form.fields["page_size"].choices
        choice_values = list(zip(*choices))[0]
        self.assertIn(AdQueryForm._DEFAULT_PAGE_SIZE, choice_values)


class AdQueryFormGetInitialPageSizeFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "page_size"

    def test(self):
        page_size = self.get_page_size()
        self._test(page_size, page_size)


# --------------------------------------
# Search


class AdQueryFormGetInitialSearchFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "search"

    def test_with_search(self):
        search = "test search"
        self._test(search, search)

    def test_without_search(self):
        self._test(None, "")


# --------------------------------------
# Search fields


class AdQueryFormSearchFieldEnumStrTest(SimpleTestCase):
    def test(self):
        search_field = next(iter(AdQueryForm.SearchField))
        self.assertEqual(str(search_field), str(search_field.value))


class AdQueryFormSearchFieldEnumFromStringTest(SimpleTestCase):
    def test(self):
        search_field = next(iter(AdQueryForm.SearchField))
        search_field_as_string = str(search_field)
        result = AdQueryForm.SearchField.from_string(search_field_as_string)
        self.assertEqual(result, search_field)


class AdQueryFormSearchFieldsChoicesTest(AdQueryFormTestMixin, TestCase):
    def test_values_are_search_fields(self):
        form = self.create_form()
        choices = form.fields["search_fields"].choices
        values = list(zip(*choices))[0]
        self.assertDictEqual(Counter(values), Counter(AdQueryForm.SearchField))


class AdQueryFormDefaultSearchFieldsTest(SimpleTestCase):
    def test_consists_of_search_fields(self):
        value = AdQueryForm._DEFAULT_SEARCH_FIELDS
        self.assertLessEqual(set(value), set(AdQueryForm.SearchField))


class AdQueryFormGetInitialSearchFieldsFromCleaned(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "search_fields"

    def test(self):
        cleaned = self.get_search_fields()
        expected = list(cleaned)
        self._test(cleaned, expected)


# --------------------------------------
# Limit prices


class AdQueryFormGetInitialLimitPriceFromCleanedTestMixin(
    AdQueryFormGetInitialFieldValueFromCleanedTestMixin
):
    def test_with_price(self):
        price = self.get_price()
        self._test(price, price)

    def test_without_price(self):
        self._test(None, None)


# Min price


class AdQueryFormGetInitialMinPriceFromCleaned(
    AdQueryFormGetInitialLimitPriceFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "min_price"

    def get_price(self):
        return self.get_min_price()


# Max price


class AdQueryFormGetInitialMaxPriceFromCleaned(
    AdQueryFormGetInitialLimitPriceFromCleanedTestMixin, SaleAdsTestMixin, TestCase
):
    field = "max_price"

    def get_price(self):
        return self.get_max_price()


# ==========================================================
# Bound fields


class AdQueryFormBoundFieldsHTMLNamesTest(AdQueryFormTestMixin, TestCase):
    def test_are_custom(self):
        for field in self.create_form():
            self.assertEqual(field.html_name, AdQueryForm.URL_PARAMETERS[field.name])


# ==========================================================
# Creation of initial field values from cleaned field values


class AdQueryFormGetFieldInitialFromCleaned(
    AdQueryFormTestMixin, SaleAdsTestMixin, HTTPRequestQueryTestMixin, TestCase
):
    def test(self):
        inputted_languages = self.get_languages()
        expected_languages = list(inputted_languages)
        data = {AdQueryForm.URL_PARAMETERS["languages"]: inputted_languages}
        form = self.create_form(data)
        result = form.get_field_initial_from_cleaned("languages")
        self.assertHTTPRequestParameterEqual(result, expected_languages)

    def test_uses_get_initial_field_value_from_cleaned_methods(self):
        form = self.create_form()
        for field in form.fields:
            with patch.object(
                form, f"_get_initial_{field}_from_cleaned", autospec=True
            ) as mock:
                result = form.get_field_initial_from_cleaned(field)
            mock.assert_called_once_with()
            self.assertEqual(result, mock.return_value)


class AdQueryFormCreateInitialFromCleanedTest(
    AdQueryFormTestMixin, SaleAdsTestMixin, HTTPRequestQueryTestMixin, TestCase
):
    def test(self):
        inputted_languages = self.get_languages()
        expected_languages = list(inputted_languages)
        data = {AdQueryForm.URL_PARAMETERS["languages"]: inputted_languages}
        form = self.create_form(data)
        result = form.create_initial_from_cleaned()
        self.assertHTTPRequestParameterEqual(result["languages"], expected_languages)

    def test_uses_get_field_initial_from_cleaned(self):
        form = self.create_form({})
        return_values = {field: object() for field in form.fields}
        side_effect = lambda field: return_values[field]
        with patch.object(
            form,
            "get_field_initial_from_cleaned",
            autospec=True,
            side_effect=side_effect,
        ) as mock:
            result = form.create_initial_from_cleaned()
        self.assertEqual(mock.call_count, len(form.fields))
        for field_name in form.fields:
            mock.assert_any_call(field_name)
        self.assertEqual(result, return_values)


###############################################################################
# Factory


# ==========================================================
# Integration tests


class AdQueryFormFactoryTest(SaleAdsTestMixin, TestCase):
    def test(self):
        category_factory = self.create_category_factory()
        Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(2)
        )
        category_cache = Category.objects.cache()
        factory = AdQueryForm.Factory(get_category_cache=lambda: category_cache)
        with patch.object(
            AdQueryForm, "__init__", autospec=True, return_value=None
        ) as form_init_mock:
            form = factory.create()
        form_init_mock.assert_called_once()
        (self_arg,), kwargs = form_init_mock.call_args
        self.assertIs(self_arg, form)
        self.assertEqual(len(kwargs), 1)
        get_category_cache_arg = kwargs["get_category_cache"]
        self.assertIs(get_category_cache_arg(), category_cache)

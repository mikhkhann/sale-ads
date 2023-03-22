from collections import Counter
from types import MappingProxyType
from unittest.mock import Mock, patch
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.test import RequestFactory, SimpleTestCase, TestCase

from ads.forms import AdQueryForm
from ads.models import Ad, AdEntry
from ads.tests.test_views.test_ad_list_views.mixins import (
    AdListViewTestMixin,
    BaseAdListViewTestMixin,
    UserAdListViewTestMixin,
)
from ads.views import _AdListView
from categories.models import Category
from common.tests.utils.http_request_query_comparison import HTTPRequestQueryTestMixin

###############################################################################
# General


# ==========================================================
# URL parameters


class BaseAdListViewURLParametersDoNotCollideTestMixin(BaseAdListViewTestMixin):
    def test(self):
        self.assertNotIn(self.cls.page_kwarg, AdQueryForm.URL_PARAMETERS.values())


class AdListViewURLParametersDoNotCollideTest(
    AdListViewTestMixin,
    BaseAdListViewURLParametersDoNotCollideTestMixin,
    SimpleTestCase,
):
    pass


class UserAdListViewURLParametersDoNotCollideTest(
    UserAdListViewTestMixin,
    BaseAdListViewURLParametersDoNotCollideTestMixin,
    SimpleTestCase,
):
    pass


# ==========================================================
# Context


# --------------------------------------
# Category tree


# URL template


class BaseAdListViewCategoryTreeURLTemplateTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_factory = RequestFactory()

    def test(self):
        request = self.request_factory.get(self.get_url())
        self.setup_view(request)
        parameter_name = AdQueryForm.URL_PARAMETERS["categories"]
        expected_other_parameters = self.view._get_ad_query_url_parameters(
            set(self.view._AD_QUERY_URL_PARAMETERS) - {parameter_name}
        )
        expected = self.view._get_url_template_with_fillable_parameter(
            parameter_name, expected_other_parameters
        )
        category = self.create_category_factory().create()
        actual_url = self.view._category_tree_url_template.format(category.pk)
        expected_url = expected.format(category.pk)
        self.assertURLEqual(actual_url, expected_url)

    def test_uses_get_ad_query_url_parameters(self):
        request = self.request_factory.get(self.get_url())
        self.setup_view(request)
        with (
            patch.object(
                self.view, "_get_ad_query_url_parameters", autospec=True
            ) as mock,
            patch.object(
                self.view, "_get_url_template_with_fillable_parameter", autospec=True
            ) as get_url_template_with_fillable_parameter_mock,
        ):
            self.view._category_tree_url_template
        mock.assert_called_once()
        (actual_names,) = mock.call_args.args
        expected_names = set(self.cls._AD_QUERY_URL_PARAMETERS)
        expected_names -= {
            AdQueryForm.URL_PARAMETERS["categories"],
            self.cls.page_kwarg,
        }
        self.assertEqual(set(actual_names), expected_names)
        self.assertEqual(mock.call_args.kwargs, {})
        get_url_template_with_fillable_parameter_mock.assert_called_once()
        actual_args = get_url_template_with_fillable_parameter_mock.call_args.args
        actual_other_parameters = actual_args[1]
        self.assertEqual(actual_other_parameters, mock.return_value)

    def test_uses_get_url_template_with_fillable_parameter(self):
        request = self.request_factory.get(self.get_url())
        self.setup_view(request)
        with patch.object(
            self.view, "_get_url_template_with_fillable_parameter", autospec=True
        ) as mock:
            value = self.view._category_tree_url_template
        mock.assert_called_once()
        actual_name, actual_other_parameters = mock.call_args.args
        self.assertEqual(actual_name, AdQueryForm.URL_PARAMETERS["categories"])
        self.assertEqual(mock.call_args.kwargs, {})
        self.assertEqual(value, mock.return_value)


class AdListViewCategoryTreeURLTemplateTest(
    AdListViewTestMixin, BaseAdListViewCategoryTreeURLTemplateTestMixin, TestCase
):
    pass


class UserAdListViewCategoryTreeURLTemplateTest(
    UserAdListViewTestMixin, BaseAdListViewCategoryTreeURLTemplateTestMixin, TestCase
):
    pass


# Ad count


class BaseAdListViewGetCategoryAdCountTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_factory = RequestFactory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        cls.category_1, cls.category_2 = Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(2)
        )
        cls.category_1_1, cls.category_1_2 = Category.objects.bulk_create(
            category_factory.create(parent=cls.category_1, save=False) for i in range(2)
        )
        cls.category_1_1_1, cls.category_1_1_2 = [
            category_factory.create(parent=cls.category_1_1, save=False)
            for i in range(2)
        ]
        cls.category_1_2_1, cls.category_1_2_2 = [
            category_factory.create(parent=cls.category_1_2, save=False)
            for i in range(2)
        ]
        Category.objects.bulk_create(
            [
                cls.category_1_1_1,
                cls.category_1_1_2,
                cls.category_1_2_1,
                cls.category_1_2_2,
            ]
        )
        cls.ad_factory = cls.create_ad_factory(not_create=["category"])
        cls.entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        cls.user = cls.create_user_factory().create()

    def test_without_ads(self):
        self._test(0)

    def test_with_only_own_ads(self):
        own_count = 2
        self.create_dummy_ads_with_entries({self.category_1: own_count})
        self._test(own_count)

    def test_with_only_ads_in_direct_descendants(self):
        own_counts = {self.category_1_1: 1, self.category_1_2: 2}
        self.create_dummy_ads_with_entries(own_counts)
        self._test(sum(own_counts.values()))

    def test_with_only_ads_in_indirect_descendants(self):
        own_counts = {
            self.category_1_1_1: 1,
            self.category_1_1_2: 2,
            self.category_1_2_1: 3,
            self.category_1_2_2: 4,
        }
        self.create_dummy_ads_with_entries(own_counts)
        self._test(sum(own_counts.values()))

    def test_with_own_ads_and_ads_in_direct_and_indirect_descendants(self):
        own_counts = {
            self.category_1: 1,
            self.category_1_1: 2,
            self.category_1_2: 3,
            self.category_1_1_1: 4,
            self.category_1_1_2: 5,
            self.category_1_2_1: 6,
            self.category_1_2_2: 7,
        }
        self.create_dummy_ads_with_entries(own_counts)
        self._test(sum(own_counts.values()))

    def test_with_only_ads_in_other_non_descendant_category(self):
        self.create_dummy_ads_with_entries({self.category_2: 2})
        self._test(0)

    def test_with_other_ad_query_parameter(self):
        max_price = self.get_max_price()
        fitting_price = max_price
        unfitting_price = max_price + 1
        price_factory = self.create_ad_price_factory()
        for price in [fitting_price, unfitting_price]:
            price_factory.check(price)
        category_1_own_fitting_count = 1
        category_1_own_unfitting_count = 2
        category_1_1_own_fitting_count = 4
        category_1_1_own_unfitting_count = 8
        ad_factory = self.create_ad_factory(not_create=["category"])
        ads = Ad.objects.bulk_create(
            ad_factory.create(category=category, price=price, save=False)
            for category, (fitting_count, unfitting_count) in [
                (
                    self.category_1,
                    [category_1_own_fitting_count, category_1_own_unfitting_count],
                ),
                (
                    self.category_1_1,
                    [category_1_1_own_fitting_count, category_1_1_own_unfitting_count],
                ),
            ]
            for price, own_count in [
                (fitting_price, fitting_count),
                (unfitting_price, unfitting_count),
            ]
            for i in range(own_count)
        )
        entry_factory = self.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )
        url_parameters = {AdQueryForm.URL_PARAMETERS["max_price"]: max_price}
        expected = category_1_own_fitting_count + category_1_1_own_fitting_count
        self._test(expected, url_parameters)

    def test_with_category_ad_query_parameter(self):
        url_parameters = {AdQueryForm.URL_PARAMETERS["categories"]: self.category_2.pk}
        category_1_own_count = 2
        category_2_own_count = 3
        self.create_dummy_ads_with_entries(
            {
                self.category_1: category_1_own_count,
                self.category_2: category_2_own_count,
            }
        )
        self._test(category_1_own_count, url_parameters)

    def create_dummy_ads_with_entries(self, own_counts):
        ads = Ad.objects.bulk_create(
            self.ad_factory.create(category=category, save=False)
            for category, own_count in own_counts.items()
            for i in range(own_count)
        )
        AdEntry.objects.bulk_create(
            self.entry_factory.create(ad=ad, save=False) for ad in ads
        )
        return ads

    def _test(self, expected, url_parameters=None):
        if url_parameters is None:
            url_parameters = {}
        url = self.get_url(query=url_parameters)
        request = self.request_factory.get(url)
        request.user = self.user
        self.setup_view(request)
        actual = self.view._get_category_ad_count(self.category_1.pk)
        self.assertEqual(actual, expected)


class AdListViewGetCategoryAdCountTest(
    AdListViewTestMixin, BaseAdListViewGetCategoryAdCountTestMixin, TestCase
):
    pass


class UserAdListViewGetCategoryAdCountTest(
    UserAdListViewTestMixin, BaseAdListViewGetCategoryAdCountTestMixin, TestCase
):
    pass


# --------------------------------------
# Template of URLs of other pages


class BaseAdListViewGetPageURLHTMLTemplateTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_number = 10
        cls.request_factory = RequestFactory()

    def test(self):
        result = self.create()
        actual_url = result.render({"number": self.page_number})
        expected_other_parameters = self.view._get_ad_query_url_parameters(
            set(self.cls._AD_QUERY_URL_PARAMETERS) - {self.cls.page_kwarg}
        )
        expected_string_template = self.view._get_url_template_with_fillable_parameter(
            self.cls.page_kwarg, expected_other_parameters
        )
        expected_url = expected_string_template.format(self.page_number)
        self.assertURLEqual(actual_url, expected_url)

    def test_uses_get_ad_query_url_parameters(self):
        with (
            patch.object(
                self.view, "_get_ad_query_url_parameters", autospec=True
            ) as mock,
            patch.object(
                self.view, "_get_url_template_with_fillable_parameter", autospec=True
            ) as get_url_template_with_fillable_parameter_mock,
        ):
            self.create()
        mock.assert_called_once()
        actual_args, actual_kwargs = mock.call_args
        (actual_names,) = actual_args
        expected_names = set(self.cls._AD_QUERY_URL_PARAMETERS) - {self.cls.page_kwarg}
        self.assertEqual(Counter(actual_names), Counter(expected_names))
        self.assertEqual(actual_kwargs, {})
        self.assertEqual(
            get_url_template_with_fillable_parameter_mock.call_args.args[1],
            mock.return_value,
        )

    def test_uses_get_url_template_with_fillable_parameter(self):
        string_template_mock = Mock()
        string_template_mock.format = Mock(autospec=str.format)
        with patch.object(
            self.view,
            "_get_url_template_with_fillable_parameter",
            autospec=True,
            return_value=string_template_mock,
        ) as mock:
            result = self.create()
        expected_other_parameters = self.view._get_ad_query_url_parameters(
            set(self.cls._AD_QUERY_URL_PARAMETERS) - {self.cls.page_kwarg}
        )
        mock.assert_called_once_with(self.cls.page_kwarg, expected_other_parameters)
        string_template_mock.format.assert_not_called()
        result.render({"number": self.page_number})
        string_template_mock.format.assert_called_once_with(self.page_number)

    def create(self):
        request = self.request_factory.get(self.get_url())
        self.setup_view(request)
        return self.view._get_page_url_html_template()


class AdListViewGetPageURLHTMLTemplateTest(
    AdListViewTestMixin, BaseAdListViewGetPageURLHTMLTemplateTestMixin, TestCase
):
    pass


class UserAdListViewGetPageURLHTMLTemplateTest(
    UserAdListViewTestMixin, BaseAdListViewGetPageURLHTMLTemplateTestMixin, TestCase
):
    pass


# ==========================================================
# Utilities


# --------------------------------------
# Ad query URL parameters


class BaseAdListViewGetAdQueryURLParametersTestMixin(
    BaseAdListViewTestMixin, HTTPRequestQueryTestMixin
):
    @classmethod
    @property
    def request_parameters(cls):
        return cls._request_parameters

    @classmethod
    def setUpClass(cls):
        cls.max_price = None
        cls.min_price = None
        cls.languages = None
        cls.order = None
        cls.page_size = None
        cls.search = None
        cls.search_fields = None
        super().setUpClass()
        cls.non_query_form_parameters_names = tuple(
            set(cls.cls._AD_QUERY_URL_PARAMETERS)
            - set(AdQueryForm.URL_PARAMETERS.values())
        )
        cls.request_factory = RequestFactory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        categories = Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(2)
        )
        category_pks = tuple(category.pk for category in categories)
        if cls.languages is None:
            cls.languages = tuple(cls.get_languages())
        if cls.order is None:
            cls.order = cls.get_order()
        if cls.page_size is None:
            cls.page_size = cls.get_page_size()
        if cls.min_price is None and cls.max_price is None:
            cls.min_price, cls.max_price = cls.get_limit_prices()
        if cls.search is None:
            cls.search = cls.get_search()
        if cls.search_fields is None:
            cls.search_fields = tuple(cls.get_search_fields())
        cls._request_parameters = MappingProxyType(
            {
                AdQueryForm.URL_PARAMETERS["categories"]: category_pks,
                AdQueryForm.URL_PARAMETERS["languages"]: cls.languages,
                AdQueryForm.URL_PARAMETERS["max_price"]: cls.max_price,
                AdQueryForm.URL_PARAMETERS["min_price"]: cls.min_price,
                AdQueryForm.URL_PARAMETERS["order"]: cls.order,
                AdQueryForm.URL_PARAMETERS["page_size"]: cls.page_size,
                AdQueryForm.URL_PARAMETERS["search"]: cls.search,
                AdQueryForm.URL_PARAMETERS["search_fields"]: cls.search_fields,
                cls.cls.page_kwarg: 10,
            }
        )
        cls.user = cls.create_user_factory().create()

    def test_with_all_parameters(self):
        names = self.cls._AD_QUERY_URL_PARAMETERS
        expected = self.request_parameters
        request_parameters = self.request_parameters
        self._test(names, expected, request_parameters)

    def test_with_query_form_parameters(self):
        names = AdQueryForm.URL_PARAMETERS.values()
        request_parameters = {name: self.request_parameters[name] for name in names}
        expected = dict(request_parameters)
        self._test(names, expected, request_parameters)

    def test_with_query_form_parameters_uses_query_form_get_field_initial_from_cleaned(
        self,
    ):
        names = AdQueryForm.URL_PARAMETERS.values()
        request_parameters = {name: self.request_parameters[name] for name in names}
        request_url = self.get_url(query=request_parameters)
        request = self.request_factory.get(request_url)
        return_values = {name: object() for name in self.create_ad_query_form().fields}
        side_effect = lambda self, name: return_values[name]
        form_init_mock = Mock(wraps=AdQueryForm.__init__)
        with (
            patch.object(
                AdQueryForm,
                "__init__",
                lambda *args, **kwargs: form_init_mock(*args, **kwargs),
            ),
            patch.object(
                AdQueryForm,
                "get_field_initial_from_cleaned",
                autospec=True,
                side_effect=side_effect,
            ) as mock,
        ):
            self.setup_view(request)
            actual = self.view._get_ad_query_url_parameters(names)
        form_init_mock.assert_called_once()
        form, actual_data = form_init_mock.call_args.args[:2]
        self.assertHTTPRequestQueryEqual(dict(actual_data), request_parameters)
        self.assertEqual(mock.call_count, len(AdQueryForm.URL_PARAMETERS))
        for field_name in self.create_ad_query_form().fields:
            mock.assert_any_call(form, field_name)
        expected = {
            parameter: return_values[field]
            for field, parameter in AdQueryForm.URL_PARAMETERS.items()
        }
        self.assertEqual(actual, expected)

    def test_with_non_query_form_parameters_with_request_parameters(self):
        names = self.non_query_form_parameters_names
        request_parameters = {name: self.request_parameters[name] for name in names}
        expected = dict(request_parameters)
        self._test(names, expected, request_parameters)

    def test_with_non_query_form_parameters_without_request_parameters(self):
        names = self.non_query_form_parameters_names
        expected = {}
        self._test(names, expected)

    def _test(self, names, expected, request_parameters=None):
        if request_parameters is None:
            request_parameters = {}
        request_url = self.get_url(query=request_parameters)
        request = self.request_factory.get(request_url)
        request.user = self.user
        self.setup_view(request)
        actual = self.view._get_ad_query_url_parameters(names)
        self.assertHTTPRequestQueryEqual(actual, expected)


class AdListViewGetAdQueryURLParametersTest(
    AdListViewTestMixin, BaseAdListViewGetAdQueryURLParametersTestMixin, TestCase
):
    pass


class UserAdListViewGetAdQueryURLParametersTest(
    UserAdListViewTestMixin, BaseAdListViewGetAdQueryURLParametersTestMixin, TestCase
):
    pass


# --------------------------------------
# URL template with fillable parameter


class BaseAdListViewGetURLTemplateWithFillableParameterTestMixin(
    BaseAdListViewTestMixin
):
    @classmethod
    @property
    def other_parameters(cls):
        return MappingProxyType(cls._other_parameters)

    @classmethod
    @property
    def request_parameters(cls):
        return MappingProxyType(cls._request_parameters)

    @classmethod
    def setUpClass(cls):
        cls.page_number, cls.request_page_number = 10, 20
        cls.languages = None
        cls.request_languages = None
        cls.order = None
        cls.request_order = None
        cls.page_size = None
        cls.request_page_size = None
        cls.search = None
        cls.request_search = None
        cls.search_fields = None
        cls.request_search_fields = None
        cls.min_price = None
        cls.request_min_price = None
        cls.max_price = None
        cls.request_max_price = None
        super().setUpClass()
        cls.parameter_name = "test_parameter"
        cls.parameter_value = "test_parameter_value"
        cls.request_factory = RequestFactory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        categories, request_categories = [
            tuple(category_factory.create(save=False) for j in range(2))
            for i in range(2)
        ]
        Category.objects.bulk_create([*categories, *request_categories])
        category_pks, request_category_pks = [
            tuple(category.pk for category in categories)
            for categories in [categories, request_categories]
        ]
        if cls.languages is None and cls.request_languages is None:
            cls.languages, cls.request_languages = map(
                tuple, cls.get_language_combinations(2)
            )
        if cls.order is None and cls.request_order is None:
            cls.order, cls.request_order = cls.get_order_values(2)
        if cls.page_size is None and cls.request_page_size is None:
            cls.page_size, cls.request_page_size = cls.get_page_size_values(2)
        if cls.search is None and cls.request_search is None:
            cls.search, cls.request_search = cls.get_search_values(2)
        if cls.search_fields is None and cls.request_search_fields is None:
            cls.search_fields, cls.request_search_fields = map(
                tuple, cls.get_search_field_combinations(2)
            )
        if (
            cls.min_price is None
            and cls.request_min_price is None
            and cls.max_price is None
            and cls.request_max_price is None
        ):
            min_prices, max_prices = cls.get_limit_price_values(2)
            cls.min_price, cls.request_min_price = min_prices
            cls.max_price, cls.request_max_price = max_prices
        cls._other_parameters = MappingProxyType(
            {
                AdQueryForm.URL_PARAMETERS["categories"]: category_pks,
                AdQueryForm.URL_PARAMETERS["languages"]: cls.languages,
                AdQueryForm.URL_PARAMETERS["max_price"]: cls.max_price,
                AdQueryForm.URL_PARAMETERS["min_price"]: cls.min_price,
                AdQueryForm.URL_PARAMETERS["order"]: cls.order,
                AdQueryForm.URL_PARAMETERS["page_size"]: cls.page_size,
                AdQueryForm.URL_PARAMETERS["search"]: cls.search,
                AdQueryForm.URL_PARAMETERS["search_fields"]: cls.search_fields,
                cls.cls.page_kwarg: cls.page_number,
            }
        )
        cls._request_parameters = MappingProxyType(
            {
                AdQueryForm.URL_PARAMETERS["categories"]: request_category_pks,
                AdQueryForm.URL_PARAMETERS["languages"]: cls.request_languages,
                AdQueryForm.URL_PARAMETERS["max_price"]: cls.request_max_price,
                AdQueryForm.URL_PARAMETERS["min_price"]: cls.request_min_price,
                AdQueryForm.URL_PARAMETERS["order"]: cls.request_order,
                AdQueryForm.URL_PARAMETERS["page_size"]: cls.request_page_size,
                AdQueryForm.URL_PARAMETERS["search"]: cls.request_search,
                AdQueryForm.URL_PARAMETERS["search_fields"]: cls.request_search_fields,
                cls.cls.page_kwarg: cls.request_page_number,
            }
        )

    def test_with_other_parameters(self):
        self._test(self.other_parameters)

    def test_without_other_parameters(self):
        self._test()

    def test_with_request_parameters_and_with_other_parameters(self):
        self._test(self.other_parameters, request_parameters=self.request_parameters)

    def test_with_request_parameters_and_without_other_parameters(self):
        self._test(request_parameters=self.request_parameters)

    def test_with_curly_braces(self):
        self._test(self.other_parameters | {AdQueryForm.URL_PARAMETERS["search"]: "{}"})

    def _test(self, other_parameters=None, *, request_parameters=None):
        if request_parameters is None:
            request_parameters = {}
        request_url = self.get_url(query=request_parameters)
        request = self.request_factory.get(request_url)
        self.setup_view(request)
        if other_parameters is not None:
            self.assertNotIn(self.parameter_name, other_parameters)
        self.assertNotIn(self.parameter_name, request_parameters)
        result = self.view._get_url_template_with_fillable_parameter(
            self.parameter_name, other_parameters
        )
        actual_url = result.format(self.parameter_value)
        expected_parameters = {}
        if other_parameters is not None:
            expected_parameters |= other_parameters
        expected_parameters |= {self.parameter_name: self.parameter_value}
        expected_query_string = urlencode(expected_parameters, doseq=True)
        request_url_items = urlsplit(request_url)
        expected_url_items = [
            *request_url_items[:3],
            expected_query_string,
            *request_url_items[4:],
        ]
        expected_url = urlunsplit(expected_url_items)
        self.assertURLEqual(actual_url, expected_url)


class AdListViewGetURLTemplateWithFillableParameterTest(
    AdListViewTestMixin,
    BaseAdListViewGetURLTemplateWithFillableParameterTestMixin,
    TestCase,
):
    pass


class UserAdListViewGetURLTemplateWithFillableParameterTest(
    UserAdListViewTestMixin,
    BaseAdListViewGetURLTemplateWithFillableParameterTestMixin,
    TestCase,
):
    pass


###############################################################################
# Main list view


# ==========================================================
# Utilities


class AdListViewGetCategoryURL(AdListViewTestMixin, BaseAdListViewTestMixin, TestCase):
    def test(self):
        category = self.create_category_factory().create()
        actual = _AdListView.get_category_url(category.pk)
        expected_parameters = {AdQueryForm.URL_PARAMETERS["categories"]: category.pk}
        expected = self.get_url(query=expected_parameters)
        self.assertURLEqual(actual, expected)

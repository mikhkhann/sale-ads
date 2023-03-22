from http import HTTPStatus
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ads.forms import AdQueryForm
from ads.models import Ad, AdEntry
from ads.tests.test_views.test_ad_list_views.mixins import (
    AdListViewTestMixin,
    BaseAdListViewTestMixin,
    UserAdListViewTestMixin,
)
from categories.models import Category
from common.tests.utils.http_request_query_comparison import HTTPRequestQueryTestMixin

###############################################################################
# General


class BaseAdListViewGeneralTestMixin(
    BaseAdListViewTestMixin, HTTPRequestQueryTestMixin
):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

    # ==========================================================
    # Context

    # --------------------------------------
    # Template of URLs of other pages

    def test_context_other_page_url_template(self):
        specified_page_number = 100
        request_url = self.get_url()
        response = self.get(request_url, expected_status=HTTPStatus.OK)
        result_template = response.context["other_page_url_template"]
        result_url = result_template.render({"number": specified_page_number})
        result_parameters = parse_qs(urlsplit(result_url).query)
        result_page_number = result_parameters[self.cls.page_kwarg]
        self.assertHTTPRequestParameterEqual(result_page_number, specified_page_number)

    def test_context_other_page_url_template_uses_get_page_url_html_template(self):
        with patch.object(
            self.cls, "_get_page_url_html_template", autospec=True
        ) as mock:
            response = self.get(expected_status=HTTPStatus.OK)
        mock.assert_called_once()
        self.assertEqual(len(mock.call_args.args), 1)
        self.assertEqual(mock.call_args.kwargs, {})
        result_template = response.context["other_page_url_template"]
        self.assertEqual(result_template, mock.return_value)


class AdListViewGeneralTest(
    AdListViewTestMixin, BaseAdListViewGeneralTestMixin, TestCase
):
    template_name = "ads/list.html"


class UserAdListViewGeneralTest(
    UserAdListViewTestMixin, BaseAdListViewGeneralTestMixin, TestCase
):
    template_name = "ads/user_list.html"

    # ==========================================================
    # Context

    # --------------------------------------
    # Viewed user

    def test_context_viewed_user(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["viewed_user"], self.author)

    # ==========================================================
    # Miscellaneous

    def test_not_existing_user(self):
        username = self.create_user_username_factory().get_unique()
        url = self.get_url(username=username)
        self.get(url, expected_status=HTTPStatus.NOT_FOUND)


# ==========================================================
# Context


# --------------------------------------
# Ad count


class BaseAdListViewContextAdCountTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ad_factory = cls.create_ad_factory()
        cls.entry_factory = cls.create_ad_entry_factory(not_create=["ad"])

    def test_with_unfiltered_ads(self):
        count = 2
        ads = Ad.objects.bulk_create(
            self.ad_factory.create(save=False) for i in range(count)
        )
        AdEntry.objects.bulk_create(
            self.entry_factory.create(ad=ad, save=False) for ad in ads
        )
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["ad_count"], count)

    def test_with_filtered_ads(self):
        fitting_count = 2
        unfitting_count = 3
        price_factory = self.create_ad_price_factory()
        fitting_price = price_factory.get_unique()
        unfitting_price = fitting_price + 1
        price_factory.check(unfitting_price)
        fitting_ads = [
            self.ad_factory.create(price=fitting_price, save=False)
            for i in range(fitting_count)
        ]
        unfitting_ads = [
            self.ad_factory.create(price=unfitting_price, save=False)
            for i in range(unfitting_count)
        ]
        ads = Ad.objects.bulk_create(fitting_ads + unfitting_ads)
        AdEntry.objects.bulk_create(
            self.entry_factory.create(ad=ad, save=False) for ad in ads
        )
        url = self.get_url(
            query={AdQueryForm.URL_PARAMETERS["max_price"]: fitting_price}
        )
        response = self.get(url, expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["ad_count"], fitting_count)

    def test_without_ads(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["ad_count"], 0)


class AdListViewContextAdCountTest(
    AdListViewTestMixin, BaseAdListViewContextAdCountTestMixin, TestCase
):
    pass


class UserAdListViewContextAdCountTest(
    UserAdListViewTestMixin, BaseAdListViewContextAdCountTestMixin, TestCase
):
    pass


# --------------------------------------
# Category tree


class BaseAdListViewContextCategoryTreeTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_name_factory = cls.create_category_name_factory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category_factory = cls.create_category_factory()

    def test_coincides_with_category_object_tree(self):
        roots = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(), save=False
            )
            for i in range(2)
        )
        category_1 = next(iter(roots))
        category_1_children = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(),
                parent=category_1,
                save=False,
            )
            for i in range(2)
        )
        category_1_1 = next(iter(category_1_children))
        category_1_1_children = Category.objects.bulk_create(
            self.category_factory.create(
                name=self.category_name_factory.get_unique(),
                parent=category_1_1,
                save=False,
            )
            for i in range(2)
        )
        response = self.get(expected_status=HTTPStatus.OK)
        result_category_tree = response.context["category_tree"]
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_category_tree, roots
        ):
            self.assertEqual(result_node.name, category.name)
        result_node_1 = self.get_sibling_node(result_category_tree, category_1)
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_node_1.children, category_1_children
        ):
            self.assertEqual(result_node.name, category.name)
        result_node_1_1 = self.get_sibling_node(result_node_1.children, category_1_1)
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_node_1_1.children, category_1_1_children
        ):
            self.assertEqual(result_node.name, category.name)

    def test_siblings_sorted_case_insensitively_by_name_with_root_categories(self):
        name_a, name_b, name_C, name_D = [
            self.category_name_factory.get_unique(prefix=prefix) for prefix in "abCD"
        ]
        roots = Category.objects.bulk_create(
            self.category_factory.create(name=name, save=False)
            for name in [name_C, name_D, name_a, name_b]
        )
        response = self.get(expected_status=HTTPStatus.OK)
        result_category_tree = response.context["category_tree"]
        self.assertEqual(len(result_category_tree), len(roots))
        for result_node, expected_name in zip(
            result_category_tree, [name_a, name_b, name_C, name_D]
        ):
            self.assertEqual(result_node.name, expected_name)

    def test_siblings_sorted_case_insensitively_by_name_with_non_root_categories(self):
        name_a, name_b, name_C, name_D = [
            self.category_name_factory.get_unique(prefix=prefix) for prefix in "abCD"
        ]
        root = self.category_factory.create()
        root_children = Category.objects.bulk_create(
            self.category_factory.create(name=name, parent=root, save=False)
            for name in [name_C, name_D, name_a, name_b]
        )
        response = self.get(expected_status=HTTPStatus.OK)
        result_category_tree = response.context["category_tree"]
        (result_root_node,) = result_category_tree
        result_root_child_nodes = result_root_node.children
        self.assertEqual(len(result_root_child_nodes), len(root_children))
        for result_node, expected_name in zip(
            result_root_child_nodes, [name_a, name_b, name_C, name_D]
        ):
            self.assertEqual(result_node.name, expected_name)

    def test_url(self):
        category = self.category_factory.create()
        init_mock = Mock(wraps=self.cls.__init__)
        with patch.object(
            self.cls, "__init__", lambda *args, **kwargs: init_mock(*args, **kwargs)
        ):
            response = self.get(expected_status=HTTPStatus.OK)
        result_category_tree = response.context["category_tree"]
        init_mock.assert_called_once()
        view = init_mock.call_args.args[0]
        (result_node,) = result_category_tree
        expected_url = view._category_tree_url_template.format(category.pk)
        self.assertURLEqual(result_node.url, expected_url)

    def test_url_uses_category_tree_url_template(self):
        roots = Category.objects.bulk_create(
            self.category_factory.create(save=False) for i in range(2)
        )
        root_1 = next(iter(roots))
        root_1_children = Category.objects.bulk_create(
            self.category_factory.create(parent=root_1, save=False) for i in range(2)
        )
        categories = [*roots, *root_1_children]
        return_values = {category.pk: object() for category in categories}
        side_effect = lambda pk: return_values[pk]
        mock = Mock()
        mock.format = Mock(autospec=str.format, side_effect=side_effect)
        with patch.object(self.cls, "_category_tree_url_template", mock):
            response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(mock.format.call_count, len(categories))
        result_category_tree = response.context["category_tree"]
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_category_tree, roots
        ):
            self.assertEqual(result_node.url, return_values[category.pk])
        result_root_1_node = self.get_sibling_node(result_category_tree, root_1)
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_root_1_node.children, root_1_children
        ):
            self.assertEqual(result_node.url, return_values[category.pk])

    def test_ad_count(self):
        category = self.category_factory.create()
        ad_count = 2
        ad_factory = self.create_ad_factory(category=category)
        ads = Ad.objects.bulk_create(
            ad_factory.create(save=False) for i in range(ad_count)
        )
        entry_factory = self.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )
        response = self.get(expected_status=HTTPStatus.OK)
        result_category_tree = response.context["category_tree"]
        (result_node,) = result_category_tree
        self.assertEqual(result_node.ad_count, ad_count)

    def test_ad_count_uses_get_category_ad_count(self):
        roots = Category.objects.bulk_create(
            self.category_factory.create(save=False) for i in range(2)
        )
        root_1 = next(iter(roots))
        root_1_children = Category.objects.bulk_create(
            self.category_factory.create(parent=root_1, save=False) for i in range(2)
        )
        categories = [*roots, *root_1_children]
        return_values = {category.pk: object() for category in categories}
        side_effect = lambda self, pk: return_values[pk]
        with patch.object(
            self.cls, "_get_category_ad_count", autospec=True, side_effect=side_effect
        ) as mock:
            response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(mock.call_count, len(categories))
        result_category_tree = response.context["category_tree"]
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_category_tree, roots
        ):
            self.assertEqual(result_node.ad_count, return_values[category.pk])
        result_root_1_node = self.get_sibling_node(result_category_tree, root_1)
        for result_node, category in self.zip_sibling_nodes_and_categories(
            result_root_1_node.children, root_1_children
        ):
            self.assertEqual(result_node.ad_count, return_values[category.pk])

    def create_category(self, *args, name=None, **kwargs):
        if not name:
            name = self.category_name_factory.get_unique()
        return self.category_factory.create(*args, name=name, **kwargs)

    def get_sibling_node(self, nodes, category):
        (node,) = filter(lambda node: node.name == category.name, nodes)
        return node

    def zip_sibling_nodes_and_categories(self, nodes, categories):
        self.assertEqual(len(nodes), len(categories))
        return [
            (self.get_sibling_node(nodes, category), category)
            for category in categories
        ]


class AdListViewContextCategoryTreeTest(
    AdListViewTestMixin, BaseAdListViewContextCategoryTreeTestMixin, TestCase
):
    pass


class UserAdListViewContextCategoryTreeTest(
    UserAdListViewTestMixin, BaseAdListViewContextCategoryTreeTestMixin, TestCase
):
    pass


# --------------------------------------
# Query form


class BaseAdListViewContextQueryFormTestMixin(
    BaseAdListViewTestMixin, HTTPRequestQueryTestMixin
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        *categories, unused_category = Category.objects.bulk_create(
            category_factory.create(save=False) for i in range(3)
        )
        cls.category_pks = tuple(category.pk for category in categories)

    def test_with_field_values(self):
        expected = {}
        language_url_parameter = self.get_languages()
        expected["languages"] = list(language_url_parameter)
        order_url_parameter = self.get_order()
        expected["order"] = order_url_parameter
        page_size_url_parameter = self.get_page_size()
        expected["page_size"] = page_size_url_parameter
        search_url_parameter = self.get_search()
        expected["search"] = search_url_parameter
        search_field_url_parameter = self.get_search_fields()
        expected["search_fields"] = list(search_field_url_parameter)
        min_price_url_parameter, max_price_url_parameter = self.get_limit_prices()
        expected["min_price"] = min_price_url_parameter
        expected["max_price"] = max_price_url_parameter
        url_parameters = {
            AdQueryForm.URL_PARAMETERS["categories"]: self.category_pks,
            AdQueryForm.URL_PARAMETERS["languages"]: language_url_parameter,
            AdQueryForm.URL_PARAMETERS["max_price"]: max_price_url_parameter,
            AdQueryForm.URL_PARAMETERS["min_price"]: min_price_url_parameter,
            AdQueryForm.URL_PARAMETERS["order"]: order_url_parameter,
            AdQueryForm.URL_PARAMETERS["page_size"]: page_size_url_parameter,
            AdQueryForm.URL_PARAMETERS["search"]: search_url_parameter,
            AdQueryForm.URL_PARAMETERS["search_fields"]: search_field_url_parameter,
        }
        url = self.get_url(query=url_parameters)
        response = self.get(url, expected_status=HTTPStatus.OK)
        expected["categories"] = self.category_pks
        self._test(response, **expected)

    def test_with_invalid_field_values(self):
        create_category_pk_factory = getattr(
            self, f"create_category_{Category._meta.pk.name}_factory"
        )
        category_pk = create_category_pk_factory().get_invalid()
        url_parameters = {
            AdQueryForm.URL_PARAMETERS["categories"]: [category_pk],
            AdQueryForm.URL_PARAMETERS["languages"]: [self.get_invalid_language()],
            AdQueryForm.URL_PARAMETERS["max_price"]: self.get_invalid_max_price,
            AdQueryForm.URL_PARAMETERS["min_price"]: self.get_invalid_min_price,
            AdQueryForm.URL_PARAMETERS["order"]: self.get_invalid_order(),
            AdQueryForm.URL_PARAMETERS["page_size"]: self.get_invalid_page_size(),
            AdQueryForm.URL_PARAMETERS["search_fields"]: (
                self.get_invalid_search_field()
            ),
        }
        url = self.get_url(query=url_parameters)
        response = self.get(url, expected_status=HTTPStatus.OK)
        self._test_field_values_are_default(response)

    def test_without_field_values(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_field_values_are_default(response)

    def _test(
        self,
        response,
        *,
        categories,
        languages,
        max_price,
        min_price,
        order,
        page_size,
        search,
        search_fields,
    ):
        form = response.context["query_form"]
        self.assertHTTPRequestParameterEqual(form["categories"].value(), categories)
        self.assertHTTPRequestParameterEqual(form["languages"].value(), languages)
        self.assertHTTPRequestParameterEqual(form["max_price"].value(), max_price)
        self.assertHTTPRequestParameterEqual(form["min_price"].value(), min_price)
        self.assertHTTPRequestParameterEqual(form["order"].value(), order)
        self.assertHTTPRequestParameterEqual(form["page_size"].value(), page_size)
        self.assertEqual(form["search"].value(), search)
        self.assertHTTPRequestParameterEqual(
            form["search_fields"].value(), search_fields
        )

    def _test_field_values_are_default(self, response):
        self._test(
            response,
            categories=[],
            languages=AdQueryForm._get_default_languages(),
            max_price=None,
            min_price=None,
            order=AdQueryForm._DEFAULT_ORDER,
            page_size=AdQueryForm._DEFAULT_PAGE_SIZE,
            search="",
            search_fields=AdQueryForm._DEFAULT_SEARCH_FIELDS,
        )


class AdListViewContextQueryFormTest(
    AdListViewTestMixin, BaseAdListViewContextQueryFormTestMixin, TestCase
):
    pass


class UserAdListViewContextQueryFormTest(
    UserAdListViewTestMixin, BaseAdListViewContextQueryFormTestMixin, TestCase
):
    pass


# --------------------------------------
# Numbers of neighboring pages


class BaseAdListViewContextNeighboringPagesNumbersTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.part_of_max_one_side_neighboring_pages_number = (
            cls.cls._ONE_SIDE_NEIGHBORING_PAGES - 1
        )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        page_size_choices = cls.create_ad_query_form().fields["page_size"].choices
        page_sizes = list(zip(*page_size_choices))[0]
        cls.page_size = min(page_sizes)
        ad_factory = cls.create_ad_factory()
        cls.pages = cls.cls._ONE_SIDE_NEIGHBORING_PAGES + 1
        ads = Ad.objects.bulk_create(
            ad_factory.create(save=False)
            for i in range(cls.page_size * (cls.pages - 1) + 1)
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )

    def test_previous_pages_with_no_previous_pages(self):
        response = self.get(1)
        self._test_previous_pages(response, [])

    def test_next_pages_with_no_next_pages(self):
        response = self.get(self.pages)
        self._test_next_pages(response, [])

    def test_previous_pages_with_part_of_max_number_of_previous_pages(self):
        page = self.part_of_max_one_side_neighboring_pages_number + 1
        response = self.get(page)
        self._test_previous_pages(response, range(1, page))

    def test_next_pages_with_part_of_max_number_of_next_pages(self):
        page = self.pages - self.part_of_max_one_side_neighboring_pages_number
        response = self.get(page)
        self._test_next_pages(response, range(page + 1, self.pages + 1))

    def test_previous_pages_with_max_number_of_previous_pages(self):
        page = self.cls._ONE_SIDE_NEIGHBORING_PAGES + 1
        response = self.get(page)
        self._test_previous_pages(
            response, range(page - self.cls._ONE_SIDE_NEIGHBORING_PAGES, page)
        )

    def test_next_pages_with_max_number_of_next_pages(self):
        page = self.pages - self.cls._ONE_SIDE_NEIGHBORING_PAGES
        response = self.get(page)
        self._test_next_pages(
            response, range(page + 1, page + 1 + self.cls._ONE_SIDE_NEIGHBORING_PAGES)
        )

    def get(self, page):
        url_query = {
            self.cls.page_kwarg: page,
            AdQueryForm.URL_PARAMETERS["page_size"]: self.page_size,
        }
        url = self.get_url(query=url_query)
        return super().get(url, expected_status=HTTPStatus.OK)

    def _test_previous_pages(self, response, expected):
        self.assertEqual(list(response.context["previous_pages"]), list(expected))

    def _test_next_pages(self, response, expected):
        self.assertEqual(list(response.context["next_pages"]), list(expected))


class AdListViewContextNeighboringPagesNumbersTest(
    AdListViewTestMixin,
    BaseAdListViewContextNeighboringPagesNumbersTestMixin,
    TestCase,
):
    pass


class UserAdListViewContextNeighboringPagesNumbersTest(
    UserAdListViewTestMixin,
    BaseAdListViewContextNeighboringPagesNumbersTestMixin,
    TestCase,
):
    pass


###############################################################################
# Querying


# ==========================================================
# Filtration


# --------------------------------------
# Categories


class BaseAdListViewCategoryFiltrationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory(ultimate=True)
        cls.category_1 = category_factory.create()
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
        ad_factory = cls.create_ad_factory(not_create=["category"])
        create_ads = lambda category: tuple(
            ad_factory.create(category=category, save=False) for i in range(2)
        )
        cls.category_1_own_ads = create_ads(cls.category_1)
        cls.category_1_1_own_ads = create_ads(cls.category_1_1)
        cls.category_1_2_own_ads = create_ads(cls.category_1_2)
        cls.category_1_1_1_own_ads = create_ads(cls.category_1_1_1)
        cls.category_1_1_2_own_ads = create_ads(cls.category_1_1_2)
        cls.category_1_2_1_own_ads = create_ads(cls.category_1_2_1)
        cls.category_1_2_2_own_ads = create_ads(cls.category_1_2_2)
        cls.category_1_ads = (
            *cls.category_1_own_ads,
            *cls.category_1_1_own_ads,
            *cls.category_1_2_own_ads,
            *cls.category_1_1_1_own_ads,
            *cls.category_1_1_2_own_ads,
            *cls.category_1_2_1_own_ads,
            *cls.category_1_2_2_own_ads,
        )
        cls.ads = cls.category_1_ads
        Ad.objects.bulk_create(cls.ads)
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in cls.ads
        )

    def test_with_leaf_pk(self):
        self._test(self.category_1_1_1.pk, self.category_1_1_1_own_ads)

    def test_with_branch_pk(self):
        self._test(self.category_1.pk, self.category_1_ads)

    def test_with_multiple_pks(self):
        url_parameter = [self.category_1_1_1.pk, self.category_1_1_2.pk]
        expected = [*self.category_1_1_1_own_ads, *self.category_1_1_2_own_ads]
        self._test(url_parameter, expected)

    def test_with_invalid_pk(self):
        create_pk_factory = getattr(
            self, f"create_category_{Category._meta.pk.name}_factory"
        )
        pk = create_pk_factory().get_invalid()
        self._test([pk], self.ads)

    def test_without_pks(self):
        self._test(None, self.ads)

    def _test(self, url_parameter, expected):
        url_parameters = {}
        if url_parameter is not None:
            url_parameter_name = AdQueryForm.URL_PARAMETERS["categories"]
            url_parameters[url_parameter_name] = url_parameter
        self._test_filtration(url_parameters, expected)


class AdListViewCategoryFiltrationTest(
    AdListViewTestMixin, BaseAdListViewCategoryFiltrationTestMixin, TestCase
):
    pass


class UserAdListViewCategoryFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewCategoryFiltrationTestMixin, TestCase
):
    pass


# --------------------------------------
# Languages


class BaseAdListViewLanguageFiltrationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        cls.non_default_language = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if cls.non_default_language is None:
            cls.first_language = settings.LANGUAGE_CODE
            language_factory = cls.create_ad_entry_language_factory()
            some_languages = [language_factory.get_choice(index) for index in range(2)]
            some_non_default_languages = set(some_languages) - {settings.LANGUAGE_CODE}
            cls.non_default_language = next(iter(some_non_default_languages))
            cls.second_language = cls.non_default_language
        ad_factory = cls.create_ad_factory()
        cls.default_language_ads = tuple(
            ad_factory.create(save=False) for i in range(2)
        )
        cls.non_default_language_ads = tuple(
            ad_factory.create(save=False) for i in range(2)
        )
        cls.default_and_non_default_language_ads = tuple(
            ad_factory.create(save=False) for i in range(2)
        )
        Ad.objects.bulk_create(
            [
                *cls.default_language_ads,
                *cls.non_default_language_ads,
                *cls.default_and_non_default_language_ads,
            ]
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            [
                *[
                    entry_factory.create(
                        ad=ad, language=settings.LANGUAGE_CODE, save=False
                    )
                    for ad in cls.default_language_ads
                ],
                *[
                    entry_factory.create(
                        ad=ad, language=cls.non_default_language, save=False
                    )
                    for ad in cls.non_default_language_ads
                ],
                *[
                    entry_factory.create(ad=ad, language=language, save=False)
                    for ad in cls.default_and_non_default_language_ads
                    for language in [settings.LANGUAGE_CODE, cls.non_default_language]
                ],
            ]
        )
        cls.first_language_ads = cls.default_language_ads
        cls.second_language_ads = cls.non_default_language_ads
        cls.first_and_second_language_ads = cls.default_and_non_default_language_ads

    def test_with_single_language(self):
        url_parameter = [self.first_language]
        expected = [*self.first_language_ads, *self.first_and_second_language_ads]
        self._test(url_parameter, expected)

    def test_with_multiple_languages(self):
        url_parameter = [self.first_language, self.second_language]
        expected = [
            *self.first_language_ads,
            *self.second_language_ads,
            *self.first_and_second_language_ads,
        ]
        self._test(url_parameter, expected)

    def test_with_invalid_languages(self):
        url_parameter = [self.get_invalid_language()]
        expected = [
            *self.default_language_ads,
            *self.default_and_non_default_language_ads,
        ]
        self._test(url_parameter, expected)

    def test_without_languages(self):
        url_parameter = None
        expected = [
            *self.default_language_ads,
            *self.default_and_non_default_language_ads,
        ]
        self._test(url_parameter, expected)

    def _test(self, url_parameter, expected):
        url_parameters = {}
        if url_parameter is not None:
            url_parameters[AdQueryForm.URL_PARAMETERS["languages"]] = url_parameter
        self._test_filtration(url_parameters, expected)


class AdListViewLanguageFiltrationTest(
    AdListViewTestMixin, BaseAdListViewLanguageFiltrationTestMixin, TestCase
):
    pass


class UserAdListViewLanguageFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewLanguageFiltrationTestMixin, TestCase
):
    pass


# --------------------------------------
# Price


class BaseAdListViewPriceFiltrationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        cls.min_price = None
        cls.max_price = None
        cls.price_less_than_min = None
        cls.price_greater_than_min_and_less_than_max = None
        cls.price_greater_than_max = None
        super().setUpClass()
        cls.invalid_min_price = cls.get_invalid_min_price()
        cls.invalid_max_price = cls.get_invalid_max_price()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if cls.min_price is None and cls.max_price is None:
            cls.min_price, cls.max_price = limit_prices = cls.get_limit_prices()
            price_factory = cls.create_ad_price_factory()
            for price in limit_prices:
                price_factory.check(price)
        ad_factory = cls.create_ad_factory()
        create_ads = lambda price: tuple(
            ad_factory.create(price=price, save=False) for i in range(2)
        )
        if cls.price_less_than_min is None:
            cls.price_less_than_min = Ad._MIN_PRICE
            assert cls.price_less_than_min < cls.min_price
        cls.ads_with_price_less_than_min = create_ads(cls.price_less_than_min)
        cls.create_ad_price_factory().check(cls.min_price)
        cls.ads_with_price_equal_to_min = create_ads(cls.min_price)
        if cls.price_greater_than_min_and_less_than_max is None:
            cls.price_greater_than_min_and_less_than_max = int(
                (cls.min_price + cls.max_price) / 2
            )
            assert (
                cls.min_price
                < cls.price_greater_than_min_and_less_than_max
                < cls.max_price
            )
            cls.create_ad_price_factory().check(
                cls.price_greater_than_min_and_less_than_max
            )
        cls.ads_with_price_greater_than_min_and_less_than_max = create_ads(
            cls.price_greater_than_min_and_less_than_max
        )
        cls.ads_with_price_equal_to_max = create_ads(cls.max_price)
        if cls.price_greater_than_max is None:
            model_price_field = Ad._meta.get_field("price")
            cls.price_greater_than_max = (
                10 ** (model_price_field.max_digits - model_price_field.decimal_places)
                - 1
            )
            assert cls.price_greater_than_max > cls.max_price
            cls.create_ad_price_factory().check(cls.price_greater_than_max)
        cls.ads_with_price_greater_than_max = create_ads(cls.price_greater_than_max)
        ads = Ad.objects.bulk_create(
            [
                *cls.ads_with_price_less_than_min,
                *cls.ads_with_price_equal_to_min,
                *cls.ads_with_price_greater_than_min_and_less_than_max,
                *cls.ads_with_price_equal_to_max,
                *cls.ads_with_price_greater_than_max,
            ]
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )

    def test_with_min_price_and_with_max_price(self):
        expected = [
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
        ]
        self._test(self.min_price, self.max_price, expected)

    def test_with_min_price_and_with_invalid_max_price(self):
        expected = [
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(self.min_price, self.invalid_max_price, expected)

    def test_with_min_price_and_without_max_price(self):
        expected = [
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(self.min_price, None, expected)

    def test_with_invalid_min_price_and_with_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
        ]
        self._test(self.invalid_min_price, self.max_price, expected)

    def test_with_invalid_min_price_and_with_invalid_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(self.invalid_min_price, self.invalid_max_price, expected)

    def test_with_invalid_min_price_and_without_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(self.invalid_min_price, None, expected)

    def test_without_min_price_and_with_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
        ]
        self._test(None, self.max_price, expected)

    def test_without_min_price_and_with_invalid_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(None, self.invalid_max_price, expected)

    def test_without_min_price_and_without_max_price(self):
        expected = [
            *self.ads_with_price_less_than_min,
            *self.ads_with_price_equal_to_min,
            *self.ads_with_price_greater_than_min_and_less_than_max,
            *self.ads_with_price_equal_to_max,
            *self.ads_with_price_greater_than_max,
        ]
        self._test(None, None, expected)

    def _test(self, min_price, max_price, expected):
        url_parameters = {}
        if min_price is not None:
            url_parameters[AdQueryForm.URL_PARAMETERS["min_price"]] = min_price
        if max_price is not None:
            url_parameters[AdQueryForm.URL_PARAMETERS["max_price"]] = max_price
        self._test_filtration(url_parameters, expected)


class AdListViewPriceFiltrationTest(
    AdListViewTestMixin, BaseAdListViewPriceFiltrationTestMixin, TestCase
):
    pass


class UserAdListViewPriceFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewPriceFiltrationTestMixin, TestCase
):
    pass


# --------------------------------------
# Search


class BaseAdListViewSearchFiltrationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.search_keyword = "test_search_keyword"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ad_factory = cls.create_ad_factory()
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        ads = []
        entries = []
        description_factory = cls.create_ad_entry_description_factory()
        name_factory = cls.create_ad_entry_name_factory()

        def create_ads(name_words, description_words):
            description_words = ["", *description_words, ""]
            description = str.join(" some text ", description_words)
            description_factory.check(description)
            name_words = ["", *name_words, ""]
            name = str.join(" some text ", name_words)
            name_factory.check(name)
            result = []
            for i in range(2):
                ad = ad_factory.create(save=False)
                ads.append(ad)
                result.append(ad)
                entry = entry_factory.create(
                    ad=ad, description=description, name=name, save=False
                )
                entries.append(entry)
            return tuple(result)

        none = ()
        spam = ("spam",)
        eggs = ("eggs",)
        spam_eggs = ("spam", "eggs")

        cls.ads__name_none__descr_none = create_ads(none, none)
        cls.ads__name_none__descr_spam = create_ads(none, spam)
        cls.ads__name_none__descr_eggs = create_ads(none, eggs)
        cls.ads__name_none__descr_spam_eggs = create_ads(none, spam_eggs)

        cls.ads__name_spam__descr_none = create_ads(spam, none)
        cls.ads__name_spam__descr_spam = create_ads(spam, spam)
        cls.ads__name_spam__descr_eggs = create_ads(spam, eggs)
        cls.ads__name_spam__descr_spam_eggs = create_ads(spam, spam_eggs)

        cls.ads__name_eggs__descr_none = create_ads(eggs, none)
        cls.ads__name_eggs__descr_spam = create_ads(eggs, spam)
        cls.ads__name_eggs__descr_eggs = create_ads(eggs, eggs)
        cls.ads__name_eggs__descr_spam_eggs = create_ads(eggs, spam_eggs)

        cls.ads__name_spam_eggs__descr_none = create_ads(spam_eggs, none)
        cls.ads__name_spam_eggs__descr_spam = create_ads(spam_eggs, spam)
        cls.ads__name_spam_eggs__descr_eggs = create_ads(spam_eggs, eggs)
        cls.ads__name_spam_eggs__descr_spam_eggs = create_ads(spam_eggs, spam_eggs)

        cls.ads = tuple(Ad.objects.bulk_create(ads))
        AdEntry.objects.bulk_create(entries)

    # ==========================================================
    # Single/multiple keyword(s) in single/multiple field(s)

    def test_with_single_keyword_and_single_field(self):
        search_fields = [AdQueryForm.SearchField.NAME]
        expected = [
            *self.ads__name_spam__descr_none,
            *self.ads__name_spam__descr_spam,
            *self.ads__name_spam__descr_eggs,
            *self.ads__name_spam__descr_spam_eggs,
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam", search_fields, expected)

    def test_with_single_keyword_and_multiple_fields(self):
        search_fields = [
            AdQueryForm.SearchField.DESCRIPTION,
            AdQueryForm.SearchField.NAME,
        ]
        expected = [
            *self.ads__name_none__descr_spam,
            *self.ads__name_none__descr_spam_eggs,
            *self.ads__name_spam__descr_none,
            *self.ads__name_spam__descr_spam,
            *self.ads__name_spam__descr_eggs,
            *self.ads__name_spam__descr_spam_eggs,
            *self.ads__name_eggs__descr_spam,
            *self.ads__name_eggs__descr_spam_eggs,
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam", search_fields, expected)

    def test_with_multiple_keywords_and_single_field(self):
        search_fields = [AdQueryForm.SearchField.NAME]
        expected = [
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam eggs", search_fields, expected)

    def test_with_multiple_keywords_and_multiple_fields(self):
        search_fields = [
            AdQueryForm.SearchField.DESCRIPTION,
            AdQueryForm.SearchField.NAME,
        ]
        expected = [
            *self.ads__name_none__descr_spam_eggs,
            *self.ads__name_spam__descr_eggs,
            *self.ads__name_spam__descr_spam_eggs,
            *self.ads__name_eggs__descr_spam,
            *self.ads__name_eggs__descr_spam_eggs,
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam eggs", search_fields, expected)

    # ==========================================================
    # Without keywords/fields

    def test_without_keywords(self):
        self._test(None, [AdQueryForm.SearchField.NAME], self.ads)

    def test_without_fields(self):
        expected = [
            *self.ads__name_none__descr_spam,
            *self.ads__name_none__descr_spam_eggs,
            *self.ads__name_spam__descr_none,
            *self.ads__name_spam__descr_spam,
            *self.ads__name_spam__descr_eggs,
            *self.ads__name_spam__descr_spam_eggs,
            *self.ads__name_eggs__descr_spam,
            *self.ads__name_eggs__descr_spam_eggs,
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam", None, expected)

    # ==========================================================
    # Separate fields

    def test_search_in_description_field(self):
        unfitting_value = self.create_ad_entry_description_factory().get_unique()
        self._test_search_in_entry_field(
            AdQueryForm.SearchField.DESCRIPTION, "description", unfitting_value
        )

    def test_search_in_name_field(self):
        unfitting_value = self.create_ad_entry_name_factory().get_unique()
        self._test_search_in_entry_field(
            AdQueryForm.SearchField.NAME, "name", unfitting_value
        )

    def _test_search_in_entry_field(self, search_field, entry_field, unfitting_value):
        self.assertNotIn(self.search_keyword, unfitting_value)
        ad_factory = self.create_ad_factory()
        fitting_ads, unfitting_ads = [
            [ad_factory.create(save=False) for i in range(2)] for j in range(2)
        ]
        Ad.objects.bulk_create(fitting_ads + unfitting_ads)
        entry_factory = self.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, **{entry_field: value}, save=False)
            for ads, value in [
                (fitting_ads, self.search_keyword),
                (unfitting_ads, unfitting_value),
            ]
            for ad in ads
        )
        self._test(self.search_keyword, [search_field], fitting_ads)

    # ==========================================================
    # Invalid search field

    def test_with_invalid_search_fields(self):
        expected = [
            *self.ads__name_none__descr_spam,
            *self.ads__name_none__descr_spam_eggs,
            *self.ads__name_spam__descr_none,
            *self.ads__name_spam__descr_spam,
            *self.ads__name_spam__descr_eggs,
            *self.ads__name_spam__descr_spam_eggs,
            *self.ads__name_eggs__descr_spam,
            *self.ads__name_eggs__descr_spam_eggs,
            *self.ads__name_spam_eggs__descr_none,
            *self.ads__name_spam_eggs__descr_spam,
            *self.ads__name_spam_eggs__descr_eggs,
            *self.ads__name_spam_eggs__descr_spam_eggs,
        ]
        self._test("spam", self.get_invalid_search_field(), expected)

    # ==========================================================

    def _test(self, search, search_fields, expected):
        url_parameters = {}
        if search is not None:
            url_parameters[AdQueryForm.URL_PARAMETERS["search"]] = search
        if search_fields:
            url_parameters[AdQueryForm.URL_PARAMETERS["search_fields"]] = search_fields
        self._test_filtration(url_parameters, expected)


class AdListViewSearchFiltrationTest(
    AdListViewTestMixin, BaseAdListViewSearchFiltrationTestMixin, TestCase
):
    pass


class UserAdListViewSearchFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewSearchFiltrationTestMixin, TestCase
):
    pass


# --------------------------------------
# Combination


class BaseAdListViewCombinedFiltrationTestMixin(BaseAdListViewTestMixin):
    def test(self):
        category_factory = self.create_category_factory()
        category_1, category_2 = Category.objects.bulk_create(
            category_factory.create(ultimate=True, save=False) for i in range(2)
        )
        lower_price = self.get_min_price()
        higher_price = lower_price + 1
        price_factory = self.create_ad_price_factory()
        for price in [lower_price, higher_price]:
            price_factory.check(price)
        ad_factory = self.create_ad_factory(not_create=["category"])
        create_ads = lambda category, price: [
            ad_factory.create(category=category, price=price, save=False)
            for i in range(2)
        ]
        category_1_lower_price_ads = create_ads(category_1, lower_price)
        category_1_higher_price_ads = create_ads(category_1, higher_price)
        category_2_lower_price_ads = create_ads(category_2, lower_price)
        ads = Ad.objects.bulk_create(
            [
                *category_1_lower_price_ads,
                *category_1_higher_price_ads,
                *category_2_lower_price_ads,
            ]
        )
        entry_factory = self.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )
        url_parameters = {
            AdQueryForm.URL_PARAMETERS["categories"]: category_1.pk,
            AdQueryForm.URL_PARAMETERS["max_price"]: lower_price,
        }
        self._test_filtration(url_parameters, category_1_lower_price_ads)


class AdListViewCombinedFiltrationTest(
    AdListViewTestMixin, BaseAdListViewCombinedFiltrationTestMixin, TestCase
):
    pass


class UserAdListViewCombinedFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewCombinedFiltrationTestMixin, TestCase
):
    pass


# --------------------------------------
# Verification


class BaseAdListViewVerificationFiltrationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author, cls.not_author = cls.get_author_and_not_author()
        ad_factory = cls.create_ad_factory(verified=False, not_create=["author"])
        cls.ads = tuple(
            Ad.objects.bulk_create(
                ad_factory.create(author=cls.author, save=False) for i in range(2)
            )
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in cls.ads
        )

    @classmethod
    def get_author_and_not_author(cls):
        raise NotImplementedError

    def verify_ads(self):
        Ad.objects.filter(pk__in=[ad.pk for ad in self.ads]).update(verified=True)


class AdListViewVerificationFiltrationTest(
    AdListViewTestMixin, BaseAdListViewVerificationFiltrationTestMixin, TestCase
):
    @classmethod
    def get_author_and_not_author(cls):
        user_factory = cls.create_user_factory()
        return get_user_model().objects.bulk_create(
            user_factory.create(save=False) for i in range(2)
        )

    def test_verified_ads_as_author(self):
        self.verify_ads()
        self.client.force_login(self.author)
        self._test_filtration(None, self.ads)

    def test_verified_ads_as_not_author(self):
        self.verify_ads()
        self.client.force_login(self.not_author)
        self._test_filtration(None, self.ads)

    def test_verified_ads_as_anonymous(self):
        self.verify_ads()
        self._test_filtration(None, self.ads)

    def test_unverified_ads_as_author(self):
        self.client.force_login(self.author)
        self._test_filtration(None, [])

    def test_unverified_ads_as_not_author(self):
        self.client.force_login(self.not_author)
        self._test_filtration(None, [])

    def test_unverified_ads_as_anonymous(self):
        self._test_filtration(None, [])


class UserAdListViewVerificationFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewVerificationFiltrationTestMixin, TestCase
):
    @classmethod
    def get_author_and_not_author(cls):
        return cls.author, cls.create_user_factory().create()

    def test_verified_ads_as_author(self):
        self.verify_ads()
        self.client.force_login(self.author)
        self._test_filtration(None, self.ads)

    def test_verified_ads_as_not_author(self):
        self.verify_ads()
        self.client.force_login(self.not_author)
        self._test_filtration(None, self.ads)

    def test_verified_ads_as_anonymous(self):
        self.verify_ads()
        self._test_filtration(None, self.ads)

    def test_unverified_ads_as_author(self):
        self.client.force_login(self.author)
        self._test_filtration(None, self.ads)

    def test_unverified_ads_as_not_author(self):
        self.client.force_login(self.not_author)
        self._test_filtration(None, [])

    def test_unverified_ads_as_anonymous(self):
        self._test_filtration(None, [])


# --------------------------------------
# User list view


# Author


class UserAdListViewAuthorFiltrationTest(
    UserAdListViewTestMixin, BaseAdListViewTestMixin, TestCase
):
    def test(self):
        ad_factory = self.create_ad_factory(not_create=["author"])
        author_ads, another_author_ads = [
            [ad_factory.create(author=author, save=False) for i in range(2)]
            for author in [self.author, self.create_user_factory().create()]
        ]
        ads = Ad.objects.bulk_create(author_ads + another_author_ads)
        entry_factory = self.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )
        self._test_filtration(None, author_ads)


# ==========================================================
# Ordering


# --------------------------------------
# General


class BaseAdListViewGeneralOrderingTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        cls.low_price = None
        cls.high_price = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ad_factory = cls.create_ad_factory()
        if cls.low_price is None and cls.high_price is None:
            cls.low_price, cls.high_price = prices = cls.get_limit_prices()
            price_factory = cls.create_ad_price_factory()
            for price in prices:
                price_factory.check(price)
        ad_1 = ad_factory.create(price=cls.high_price)
        ad_2 = ad_factory.create(price=cls.low_price)
        ad_3 = ad_factory.create(price=cls.high_price)
        ad_4 = ad_factory.create(price=cls.low_price)
        cls.ads_sorted_by_creation_date_time_in_descending_order = (
            ad_4,
            ad_3,
            ad_2,
            ad_1,
        )
        cls.ads_sorted_by_price_and_creation_date_time_in_descending_order = (
            ad_4,
            ad_2,
            ad_3,
            ad_1,
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in [ad_1, ad_2, ad_3, ad_4]
        )

    def test_with_invalid_ordering(self):
        order = self.get_invalid_order()
        self._test_ordering(
            order, self.ads_sorted_by_creation_date_time_in_descending_order
        )

    def test_without_ordering(self):
        self._test_ordering(
            None, self.ads_sorted_by_creation_date_time_in_descending_order
        )

    def test_default_order_is_added_to_specified_order(self):
        self._test_ordering(
            AdQueryForm.Order.LOWEST_PRICE_FIRST,
            self.ads_sorted_by_price_and_creation_date_time_in_descending_order,
        )


class AdListViewGeneralOrderingTest(
    AdListViewTestMixin, BaseAdListViewGeneralOrderingTestMixin, TestCase
):
    pass


class UserAdListViewGeneralOrderingTest(
    UserAdListViewTestMixin, BaseAdListViewGeneralOrderingTestMixin, TestCase
):
    pass


# --------------------------------------
# Creation date & time


class BaseAdListViewCreationDateTimeOrderingTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ads_sorted_by_creation_date_time = []
        ad_factory = cls.create_ad_factory()
        entries = []
        entry_factory = cls.create_ad_entry_factory()
        for i in range(3):
            ad = ad_factory.create()
            ads_sorted_by_creation_date_time.append(ad)
            entries.append(entry_factory.create(ad=ad, save=False))
        cls.ads_sorted_by_creation_date_time = tuple(ads_sorted_by_creation_date_time)
        AdEntry.objects.bulk_create(entries)

    def test_newest_first(self):
        self._test_ordering(
            AdQueryForm.Order.NEWEST_FIRST,
            reversed(self.ads_sorted_by_creation_date_time),
        )

    def test_oldest_first(self):
        self._test_ordering(
            AdQueryForm.Order.OLDEST_FIRST, self.ads_sorted_by_creation_date_time
        )


class AdListViewCreationDateTimeOrderingTest(
    AdListViewTestMixin, BaseAdListViewCreationDateTimeOrderingTestMixin, TestCase
):
    pass


class UserAdListViewCreationDateTimeOrderingTest(
    UserAdListViewTestMixin, BaseAdListViewCreationDateTimeOrderingTestMixin, TestCase
):
    pass


# --------------------------------------
# Price


class BaseAdListViewPriceOrderingTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        cls.prices = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ad_factory = cls.create_ad_factory()
        if cls.prices is None:
            min_price = cls.get_min_price()
            cls.prices = (min_price + 2, min_price + 3, min_price, min_price + 1)
            price_factory = cls.create_ad_price_factory()
            for price in cls.prices:
                price_factory.check(price)
        ads = Ad.objects.bulk_create(
            [ad_factory.create(price=price, save=False) for price in cls.prices]
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )
        cls.ads_sorted_by_price = tuple(sorted(ads, key=lambda ad: ad.price))

    def test_lowest_price_first(self):
        self._test_ordering(
            AdQueryForm.Order.LOWEST_PRICE_FIRST, self.ads_sorted_by_price
        )

    def test_highest_price_first(self):
        self._test_ordering(
            AdQueryForm.Order.HIGHEST_PRICE_FIRST, reversed(self.ads_sorted_by_price)
        )


class AdListViewPriceOrderingTest(
    AdListViewTestMixin, BaseAdListViewPriceOrderingTestMixin, TestCase
):
    pass


class UserAdListViewPriceOrderingTest(
    UserAdListViewTestMixin, BaseAdListViewPriceOrderingTestMixin, TestCase
):
    pass


# ==========================================================
# Pagination


class BaseAdListViewPaginationTestMixin(BaseAdListViewTestMixin):
    @classmethod
    def setUpClass(cls):
        cls.page_count = 2
        cls.non_full_page_size = 1
        cls.page_size = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if cls.page_size is None:
            cls.page_size = cls.get_page_size()
            cls.ad_count = None
        cls.ad_count = cls.page_size * (cls.page_count - 1) + cls.non_full_page_size
        ad_factory = cls.create_ad_factory()
        ads = Ad.objects.bulk_create(
            [ad_factory.create(save=False) for i in range(cls.ad_count)]
        )
        entry_factory = cls.create_ad_entry_factory(not_create=["ad"])
        AdEntry.objects.bulk_create(
            entry_factory.create(ad=ad, save=False) for ad in ads
        )

    # ==========================================================
    # Page size

    def test_page_size_with_page_size_in_full_page(self):
        url = self.get_url(page_size=self.page_size)
        response = self.get(url, expected_status=HTTPStatus.OK)
        self._test_page_size(response, self.page_size)

    def test_page_size_with_page_size_in_non_full_page(self):
        url = self.get_url(page_size=self.page_size, page_number=self.page_count)
        response = self.get(url, expected_status=HTTPStatus.OK)
        self._test_page_size(response, self.non_full_page_size)

    def test_page_size_with_invalid_page_size(self):
        url = self.get_url(page_size=self.get_invalid_page_size())
        response = self.get(url, expected_status=HTTPStatus.OK)
        self._test_page_size(
            response, min(self.ad_count, AdQueryForm._DEFAULT_PAGE_SIZE)
        )

    def test_page_size_without_page_size(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_page_size(
            response, min(self.ad_count, AdQueryForm._DEFAULT_PAGE_SIZE)
        )

    def _test_page_size(self, response, expected):
        paje_obj = response.context["page_obj"]
        self.assertEqual(len(paje_obj), expected)

    # ==========================================================
    # Page number

    def test_page_number_with_page_number(self):
        url = self.get_url(page_number=self.page_count)
        response = self.get(url, expected_status=HTTPStatus.OK)
        self._test_valid_page_number(response, self.page_count)

    def test_page_number_with_invalid_page_number(self):
        url = self.get_url(page_size=self.page_size, page_number=self.page_count + 1)
        self.get(url, expected_status=HTTPStatus.NOT_FOUND)

    def test_page_number_without_page_number(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_valid_page_number(response, 1)

    def _test_valid_page_number(self, response, expected):
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, expected)

    # ==========================================================

    def get_url(self, *args, query=None, page_size=None, page_number=None, **kwargs):
        if query is None:
            query = {}
        if page_size is not None:
            query[AdQueryForm.URL_PARAMETERS["page_size"]] = page_size
        if page_number is not None:
            query[self.cls.page_kwarg] = page_number
        return super().get_url(*args, query=query, **kwargs)


class AdListViewPaginationTest(
    AdListViewTestMixin, BaseAdListViewPaginationTestMixin, TestCase
):
    pass


class UserAdListViewPaginationTest(
    UserAdListViewTestMixin, BaseAdListViewPaginationTestMixin, TestCase
):
    pass


###############################################################################
# Miscellaneous


# Query form factory usage


class BaseAdListViewQueryFormFactoryGetCategoryCacheArgTestMixin(
    BaseAdListViewTestMixin
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        categories = [category_factory.create() for i in range(2)]
        cls.category_cache = {category.pk: category for category in categories}

    def test(self):
        with patch.object(AdQueryForm, "Factory", wraps=AdQueryForm.Factory) as mock:
            self.get(expected_status=HTTPStatus.OK)
        mock.assert_called_once()
        self.assertEqual(
            mock.call_args.kwargs["get_category_cache"](), self.category_cache
        )


class AdListViewQueryFormFactoryGetCategoryCacheArgTestMixin(
    AdListViewTestMixin,
    BaseAdListViewQueryFormFactoryGetCategoryCacheArgTestMixin,
    TestCase,
):
    pass


class UserAdListViewQueryFormFactoryGetCategoryCacheArgTestMixin(
    UserAdListViewTestMixin,
    BaseAdListViewQueryFormFactoryGetCategoryCacheArgTestMixin,
    TestCase,
):
    pass

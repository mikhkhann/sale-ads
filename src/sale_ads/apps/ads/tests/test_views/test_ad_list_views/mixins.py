from collections import Counter
from functools import cached_property
from http import HTTPStatus

from ads.forms import AdQueryForm
from ads.tests.test_forms import AdQueryFormRelatedTestMixin
from ads.views import _AdListView, _UserAdListView
from common.tests import SaleAdsTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class BaseAdListViewTestMixin(
    AdQueryFormRelatedTestMixin, SaleAdsTestMixin, ViewTestMixin
):
    @classmethod
    def create_ad_factory(cls, *args, **kwargs):
        kwargs = cls.get_ad_factory_kwargs() | kwargs
        return super().create_ad_factory(*args, **kwargs)

    @classmethod
    def get_ad_factory_kwargs(cls):
        return {"verified": True}

    def setup_view(self, request, *args, **kwargs):
        self.view.setup(request, *args, **kwargs)

    @cached_property
    def view(self):
        return self.cls()

    def _test_querying_without_pagination(self, url_parameters, expected, prepare):
        actual = []
        if url_parameters is None:
            url_parameters = {}
        page_size_choices = self.create_ad_query_form().fields["page_size"].choices
        page_sizes = list(zip(*page_size_choices))[0]
        page_size = max(page_sizes)
        url_parameters[AdQueryForm.URL_PARAMETERS["page_size"]] = page_size
        url = self.get_url(query=url_parameters)
        response = self.get(url, expected_status=HTTPStatus.OK)
        actual.extend(response.context["page_obj"])
        paginator = response.context["paginator"]
        for page_number in paginator.page_range[1:]:
            url = self.get_url(
                query=url_parameters | {self.cls.page_kwarg: page_number}
            )
            response = self.get(url, expected_status=HTTPStatus.OK)
            actual.extend(response.context["page_obj"])
        self.assertEqual(prepare(actual), prepare(expected))

    def _test_filtration(self, url_parameters, expected):
        self._test_querying_without_pagination(url_parameters, expected, Counter)

    def _test_ordering(self, order, expected, url_parameters=None):
        if url_parameters is None:
            url_parameters = {}
        if order is not None:
            url_parameters[AdQueryForm.URL_PARAMETERS["order"]] = order
        self._test_querying_without_pagination(url_parameters, expected, list)


class AdListViewTestMixin:
    cls = _AdListView
    url_pattern_name = "ads_list"


class UserAdListViewTestMixin:
    cls = _UserAdListView
    url_pattern_name = "ads_user_list"

    @classmethod
    @property
    def author(cls):
        if cls._author is None:
            cls._author = cls.create_user_factory().create()
        return cls._author

    @classmethod
    def setUpTestData(cls):
        cls._author = None
        super().setUpTestData()
        cls.author

    @classmethod
    def get_ad_factory_kwargs(cls):
        return super().get_ad_factory_kwargs() | {"author": cls.author}

    def get_url_pattern_kwargs(self, *, username=None):
        if username is None:
            username = self.author.username
        return {"username": username}

    def setup_view(self, request, *args, username=None, **kwargs):
        if username is None:
            username = self.author.username
        super().setup_view(request, *args, username=username, **kwargs)

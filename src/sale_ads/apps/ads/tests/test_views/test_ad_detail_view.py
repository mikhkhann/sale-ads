from http import HTTPStatus
from importlib import import_module
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils.translation import get_language

from ads.models import Ad
from ads.views import _AdDetailView
from common.tests import (
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
)
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdDetailViewGetTest(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    ViewTestMixin,
    TestCase,
):
    url_pattern_name = "ads_detail"

    @classmethod
    def setUpClass(cls):
        cls.used_language = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ad = cls.create_ad_factory().create()
        entry_factory = cls.create_ad_entry_factory(ad=cls.ad)
        if cls.used_language is None:
            cls.used_language = settings.LANGUAGE_CODE
        cls.entry = entry_factory.create(language=cls.used_language)

    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "ads/detail.html")

    # ==========================================================
    # Context

    # --------------------------------------
    # Entry

    def test_context_entry(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["entry"], self.entry)

    def test_context_entry_retrieved_by_ad_get_entry_with_unspecified_language(self):
        module = import_module(_AdDetailView.__module__)
        self.assertIs(module.get_language, get_language)
        with (
            patch.object(module, "get_language", autospec=True) as get_language_mock,
            patch.object(Ad, "get_entry", autospec=True) as get_entry_mock,
        ):
            response = self.get(expected_status=HTTPStatus.OK)
        get_language_mock.assert_called_once_with()
        get_entry_mock.assert_called_once_with(self.ad, get_language_mock.return_value)
        self.assertEqual(response.context["entry"], get_entry_mock.return_value)

    def test_context_entry_retrieved_by_ad_get_entry_with_specified_language(self):
        language = "test_language"
        url = self.get_url(query={_AdDetailView._LANGUAGE_URL_PARAMETER: language})
        with patch.object(Ad, "get_entry", autospec=True) as get_entry_mock:
            response = self.get(url, expected_status=HTTPStatus.OK)
        get_entry_mock.assert_called_once_with(self.ad, language)
        self.assertEqual(response.context["entry"], get_entry_mock.return_value)

    # --------------------------------------
    # Entry choice form

    def test_context_entry_choice_form_without_language(self):
        with patch.object(Ad, "get_entry", autospec=True) as get_entry_mock:
            response = self.get(expected_status=HTTPStatus.OK)
        form = response.context["entry_choice_form"]
        entry = response.context["entry"]
        self.assertEqual(entry, get_entry_mock.return_value)
        self.assertEqual(form["language"].value(), entry.language)

    # --------------------------------------
    # Entry language URL parameter name

    def test_context_entry_language_url_parameter_name(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(
            response.context["entry_language_url_parameter_name"],
            _AdDetailView._LANGUAGE_URL_PARAMETER,
        )

    # --------------------------------------
    # Object

    def test_context_object(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["object"], self.ad)

    # ==========================================================

    def get_url_pattern_kwargs(self):
        return {"pk": self.ad.pk}

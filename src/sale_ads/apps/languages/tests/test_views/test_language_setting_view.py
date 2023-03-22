from http import HTTPStatus

from django.conf import settings
from django.test import TestCase
from django.utils import translation

from common.tests import (
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
)
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)
from common.tests.utils.view_test_mixin import ViewTestMixin
from languages.views import _LanguageSettingView


class LanguageSettingViewTestMixin(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    ViewTestMixin,
):
    url_pattern_name = "languages_setting"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        languages = list(zip(*settings.LANGUAGES))[0]
        non_default_languages = set(languages) - {settings.LANGUAGE_CODE}
        cls.new_language = next(iter(non_default_languages))
        cls.invalid_language = "invalid language"
        assert cls.invalid_language not in languages

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.authenticated_user = cls.create_user_factory().create()

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)
        super().tearDown()

    def _test_context_form(self, response, expected_language):
        form = response.context["form"]
        self.assertEqual(form["language"].value(), expected_language)


class LanguageSettingViewGeneralTest(LanguageSettingViewTestMixin, TestCase):
    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "languages/setting.html")


class LanguageSettingViewGetTest(LanguageSettingViewTestMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def test_context_form_without_language_cookie(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_form(response, settings.LANGUAGE_CODE)

    def test_context_form_with_language_cookie(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = self.new_language
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_form(response, self.new_language)


class LanguageSettingViewPostTest(LanguageSettingViewTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redirection_url = "/test_redirection_url"

    # ==========================================================
    # Model objects

    # --------------------------------------
    # User model

    def test_authenticated_user_with_new_language(self):
        self.client.force_login(self.authenticated_user)
        self.post_with_new_language(expected_status=HTTPStatus.FOUND)
        self._test_authenticated_user(self.new_language)

    def test_authenticated_user_with_invalid_language(self):
        self.client.force_login(self.authenticated_user)
        self.post_with_invalid_language(expected_status=HTTPStatus.OK)
        self._test_authenticated_user(settings.LANGUAGE_CODE)

    def test_authenticated_user_without_language(self):
        self.client.force_login(self.authenticated_user)
        self.post(expected_status=HTTPStatus.OK)
        self._test_authenticated_user(settings.LANGUAGE_CODE)

    # ==========================================================
    # Cookie

    def test_cookie_with_new_language(self):
        response = self.post_with_new_language(expected_status=HTTPStatus.FOUND)
        value = response.cookies[settings.LANGUAGE_COOKIE_NAME].value
        self.assertEqual(value, self.new_language)

    def test_cookie_with_invalid_language(self):
        response = self.post_with_invalid_language(expected_status=HTTPStatus.OK)
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)

    def test_cookie_without_language(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)

    # ==========================================================
    # Redirections

    def test_redirects_to_specified_redirection_url_on_success(self):
        url_query = {
            _LanguageSettingView._REDIRECTION_URL_URL_PARAMETER_NAME: (
                self.redirection_url
            )
        }
        url = self.get_url(query=url_query)
        response = self.post_with_new_language(url, expected_status=HTTPStatus.FOUND)
        self.assertRedirects(
            response, self.redirection_url, fetch_redirect_response=False
        )

    def test_redirects_to_default_redirection_url_on_success_if_not_specified(self):
        response = self.post_with_new_language(expected_status=HTTPStatus.FOUND)
        self.assertRedirects(response, _LanguageSettingView._DEFAULT_REDIRECTION_URL)

    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def test_context_form_with_invalid_language(self):
        response = self.post_with_invalid_language(expected_status=HTTPStatus.OK)
        self._test_context_form(response, self.invalid_language)

    def test_context_form_without_language(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_form(response, None)

    # --------------------------------------
    # User

    def test_context_user_authenticated_with_invalid_language(self):
        self.client.force_login(self.authenticated_user)
        response = self.post_with_invalid_language(expected_status=HTTPStatus.OK)
        self._test_context_user_authenticated(response)

    def test_context_user_authenticated_without_language(self):
        self.client.force_login(self.authenticated_user)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_user_authenticated(response)

    def _test_context_user_authenticated(self, response):
        user = response.context["user"]
        self._test_authenticated_user(settings.LANGUAGE_CODE, user)

    # ==========================================================

    def post_with_new_language(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["language"] = self.new_language
        return self.post(url, data, *args, **kwargs)

    def post_with_invalid_language(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["language"] = self.invalid_language
        return self.post(url, data, *args, **kwargs)

    def _test_authenticated_user(self, expected_language, user=None):
        if user is None:
            user = self.authenticated_user
            user.refresh_from_db(fields=["language"])
        self.assertEqual(user.language, expected_language)

from django.conf import settings
from django.test import TestCase
from django.utils import translation

from common.tests import SaleAdsTestMixin
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)


class LocaleMiddlewareTest(
    SaleAdsTestMixin, CompositeLanguagesSettingTestMixin, TestCase
):
    def test_activates_authenticated_user_language(self):
        try:
            language_factory = self.create_user_language_factory()
            some_languages = [language_factory.get_choice(index) for index in range(2)]
            some_non_default_languages = set(some_languages) - {settings.LANGUAGE_CODE}
            language = next(iter(some_non_default_languages))
            user = self.create_user_factory().create(language=language)
            self.client.force_login(user)
            response = self.client.get("/test_url")
            self.assertEqual(response.headers["Content-Language"], language)
        finally:
            translation.activate(settings.LANGUAGE_CODE)

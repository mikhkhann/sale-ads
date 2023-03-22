from django import forms
from django.conf import global_settings, settings
from django.test import SimpleTestCase

from languages.validators import _LANGUAGE_UNALLOWED_ERROR, validate_language_allowed


class ValidateLanguageAllowedTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        default_languages = list(zip(*settings.LANGUAGES))[0]
        global_languages = list(zip(*global_settings.LANGUAGES))[0]
        languages_not_in_setting = set(global_languages) - set(default_languages)
        cls.language_not_in_setting = next(iter(languages_not_in_setting))

    def setUp(self):
        super().setUp()
        field = forms.CharField(validators=[validate_language_allowed])
        self.form_class = type("TestForm", (forms.Form,), {"language": field})

    def test_with_allowed_language(self):
        validate_language_allowed(settings.LANGUAGE_CODE)

    def test_with_unallowed_language(self):
        form = self.form_class({"language": self.language_not_in_setting})
        with self.settings(
            LANGUAGES=[("de", "German"), ("fr", "French")],
            LANGUAGE_PREFERENCE_ORDER=["fr", "de"],
        ):
            form.full_clean()
        expected_params = {
            "allowed_languages": "French (fr), German (de)",
            "language": self.language_not_in_setting,
        }
        expected_error = _LANGUAGE_UNALLOWED_ERROR % expected_params
        self.assertFormError(form, "language", expected_error)

    def test_error_code(self):
        form = self.form_class({"language": self.language_not_in_setting})
        form.has_error("language", "unallowed")

    def test_uses_languages_setting(self):
        setting_mock = [
            *settings.LANGUAGES,
            (self.language_not_in_setting, "test language name"),
        ]
        with self.settings(LANGUAGES=setting_mock):
            validate_language_allowed(self.language_not_in_setting)


class LanguageUnallowedErrorTest(SimpleTestCase):
    def test_formatting(self):
        params = {"allowed_languages": "German (de), French (fr)", "language": "en"}
        actual = _LANGUAGE_UNALLOWED_ERROR % params
        expected = (
            '"en" isn\'t an allowed language. Choose one of allowed languages: '
            "German (de), French (fr)."
        )
        self.assertEqual(actual, expected)

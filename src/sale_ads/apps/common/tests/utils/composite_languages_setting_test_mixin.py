from django.conf import global_settings, settings
from django.test import override_settings


class CompositeLanguagesSettingTestMixin:
    required_language_count = 2

    @classmethod
    def setUpClass(cls):
        cls.composite_languages_setting_is_set_up = False
        super().setUpClass()
        if not cls.composite_languages_setting_is_set_up:
            cls.set_up_composite_languages_setting()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set_up_composite_languages_setting()
        cls.composite_languages_setting_is_set_up = True

    @classmethod
    def set_up_composite_languages_setting(cls):
        required_language_count = cls.get_required_language_count()
        if len(settings.LANGUAGES) < required_language_count:
            added_languages_count = required_language_count - len(settings.LANGUAGES)
            added_languages = global_settings.LANGUAGES[:added_languages_count]
            mock = [*settings.LANGUAGES, *added_languages]
            cls.enterClassContext(override_settings(LANGUAGES=mock))

    @classmethod
    def get_required_language_count(cls):
        return cls.required_language_count

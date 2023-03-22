from django.test import SimpleTestCase
from django.utils.translation import get_language_info

from languages.forms import LanguageSettingForm

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Language


class LanguageSettingFormLanguageChoicesTest(SimpleTestCase):
    def test(self):
        with self.settings(LANGUAGE_PREFERENCE_ORDER=["de", "fr"]):
            actual = list(LanguageSettingForm().fields["language"].choices)
        expected = [
            ("de", get_language_info("de")["name_local"]),
            ("fr", get_language_info("fr")["name_local"]),
        ]
        self.assertEqual(actual, expected)

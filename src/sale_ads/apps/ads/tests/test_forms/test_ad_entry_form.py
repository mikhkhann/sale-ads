from django.test import SimpleTestCase
from django.utils.translation import get_language_info

from ads.forms import AdEntryForm

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Language


class AdEntryFormLanguageChoicesTest(SimpleTestCase):
    def test(self):
        with self.settings(LANGUAGE_PREFERENCE_ORDER=["de", "fr"]):
            actual = list(AdEntryForm().fields["language"].choices)
        expected = [
            ("de", get_language_info("de")["name_local"]),
            ("fr", get_language_info("fr")["name_local"]),
        ]
        self.assertEqual(actual, expected)

from django.test import SimpleTestCase
from django.utils.translation import get_language_info

from ads.forms import AdDetailEntryChoiceForm

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Language


class AdDetailEntryChoiceFormLanguageChoicesTest(SimpleTestCase):
    def test(self):
        with self.settings(LANGUAGE_PREFERENCE_ORDER=["de", "es", "fr"]):
            form = AdDetailEntryChoiceForm(available_languages=["fr", "de"])
            actual = list(form.fields["language"].choices)
        expected = [
            ("de", get_language_info("de")["name_local"]),
            ("fr", get_language_info("fr")["name_local"]),
        ]
        self.assertEqual(actual, expected)

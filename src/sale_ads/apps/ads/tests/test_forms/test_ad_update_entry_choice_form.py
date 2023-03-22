from django.test import SimpleTestCase
from django.utils.translation import get_language_info

from ads.forms import AdUpdateEntryChoiceForm

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Language


class AdUpdateEntryChoiceFormLanguageChoicesTest(SimpleTestCase):
    def test(self):
        with self.settings(LANGUAGE_PREFERENCE_ORDER=["de", "fr"]):
            form = AdUpdateEntryChoiceForm(used_languages=["de"])
            actual = list(form.fields["language"].choices)
        expected = [
            ("de", f"{get_language_info('de')['name_local']} (created)"),
            ("fr", f"{get_language_info('fr')['name_local']} (not created)"),
        ]
        self.assertEqual(actual, expected)

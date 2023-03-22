from django import forms
from django.conf import settings
from django.utils.translation import get_language, get_language_info


class LanguageSettingForm(forms.Form):
    language = forms.ChoiceField(
        choices=lambda: [
            (language, get_language_info(language)["name_local"])
            for language in settings.LANGUAGE_PREFERENCE_ORDER
        ],
        initial=get_language,
    )

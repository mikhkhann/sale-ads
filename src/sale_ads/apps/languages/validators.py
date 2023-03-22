from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_language_allowed(language):
    """Check that language is in `LANGUAGES` setting."""
    allowed_languages = dict(settings.LANGUAGES)
    if language not in allowed_languages:
        allowed_languages_in_message = [
            f"{allowed_languages[language]} ({language})"
            for language in settings.LANGUAGE_PREFERENCE_ORDER
        ]
        params = {
            "allowed_languages": str.join(", ", allowed_languages_in_message),
            "language": language,
        }
        raise ValidationError(_LANGUAGE_UNALLOWED_ERROR, "unallowed", params)


_LANGUAGE_UNALLOWED_ERROR = _(
    '"%(language)s" isn\'t an allowed language. Choose one of allowed languages: '
    "%(allowed_languages)s."
)

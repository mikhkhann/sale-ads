import django.middleware.locale
from django.contrib.auth import get_user
from django.utils import translation


class LocaleMiddleware(django.middleware.locale.LocaleMiddleware):
    def process_request(self, request):
        user = get_user(request)
        if user.is_authenticated:
            translation.activate(user.language)
            request.LANGUAGE_CODE = user.language
        else:
            super().process_request(request)

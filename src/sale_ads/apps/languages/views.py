from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import FormView

from languages.forms import LanguageSettingForm


class _LanguageSettingView(FormView):
    form_class = LanguageSettingForm
    template_name = "languages/setting.html"

    _DEFAULT_REDIRECTION_URL = settings.HOME_URL
    _REDIRECTION_URL_URL_PARAMETER_NAME = "next"

    def form_valid(self, form):
        language = form.cleaned_data["language"]
        user = self.request.user
        if user.is_authenticated and form.has_changed():
            user.language = language
            user.save(update_fields=["language"])
        redirection_url = self.request.GET.get(
            self._REDIRECTION_URL_URL_PARAMETER_NAME,
            self._DEFAULT_REDIRECTION_URL,
        )
        response = redirect(redirection_url)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
        return response


setting = _LanguageSettingView.as_view()

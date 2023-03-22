from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = pgettext_lazy("app name", "accounts")

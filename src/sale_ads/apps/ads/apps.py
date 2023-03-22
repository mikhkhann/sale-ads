from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class AdsConfig(AppConfig):
    name = "ads"
    verbose_name = pgettext_lazy("app name", "ads")

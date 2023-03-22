from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class CategoriesConfig(AppConfig):
    name = "categories"
    verbose_name = pgettext_lazy("app name", "categories")

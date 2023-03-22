from functools import cached_property

from django.contrib import admin
from django.utils.translation import pgettext_lazy
from modeltranslation.admin import TranslationAdmin

from categories.models import Category


@admin.register(Category)
class _CategoryAdmin(TranslationAdmin):
    list_display = ("name", "parent", "ultimate")
    search_fields = ("name",)

    class _RootListFilter(admin.SimpleListFilter):
        parameter_name = "root"
        title = pgettext_lazy("admin category filter", "root")
        _CHOICES = (
            (1, pgettext_lazy("admin category root filter choice", "Yes")),
            (0, pgettext_lazy("admin category root filter choice", "No")),
        )

        def lookups(self, request, model_admin):
            return self._CHOICES

        def queryset(self, request, queryset):
            value = self.value()
            if value is not None:
                queryset = (
                    queryset.filter(parent=None)
                    if int(value)
                    else queryset.exclude(parent=None)
                )
            return queryset

    class _ParentListFilter(admin.SimpleListFilter):
        parameter_name = "parent"
        title = pgettext_lazy("admin category filter", "parent")

        def __init__(self, request, params, model, model_admin):
            self._choices = model_admin._parent_choices
            super().__init__(request, params, model, model_admin)

        def lookups(self, request, model_admin):
            return self._choices

        def queryset(self, request, queryset):
            value = self.value()
            if value is not None:
                queryset = queryset.filter(parent_id=value)
            return queryset

    @cached_property
    def _parent_choices(self):
        return [
            (category.pk, category.full_name)
            for category in sorted(
                Category.objects.cache().values(),
                key=lambda category: category.lowercased_full_name,
            )
        ]

    list_filter = (_RootListFilter, "ultimate", _ParentListFilter)

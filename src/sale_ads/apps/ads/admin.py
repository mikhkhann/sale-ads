from functools import cached_property

from django.contrib import admin
from django.utils.translation import pgettext_lazy

from ads.models import Ad, AdEntry, AdImage
from categories.models import Category


@admin.register(Ad)
class _AdAdmin(admin.ModelAdmin):
    list_display = ("ad", "price", "category", "author_as_string", "created")
    search_fields = ("entries__description", "entries__name")
    sortable_by = frozenset(set(list_display) - {"category"})

    class _CategoryListFilter(admin.SimpleListFilter):
        parameter_name = "category"
        title = pgettext_lazy("admin ad filter", "category")

        def __init__(self, request, params, model, model_admin):
            self._model_admin = model_admin
            super().__init__(request, params, model, model_admin)

        def lookups(self, request, model_admin):
            return self._model_admin._category_choices

        def queryset(self, request, queryset):
            value = self.value()
            if value is not None:
                pk = Category.pk_from_string(value)
                root_category = self._model_admin._category_cache[pk]
                categories = [root_category, *root_category.descendants]
                queryset = queryset.filter(
                    category__in=[category.pk for category in categories]
                )
            return queryset

    @cached_property
    def _category_choices(self):
        return [
            (category.pk, category.full_name)
            for category in sorted(
                self._category_cache.values(),
                key=lambda category: category.lowercased_full_name,
            )
        ]

    @cached_property
    def _category_cache(self):
        return Category.objects.cache()

    list_filter = ("created", _CategoryListFilter)

    @admin.display(
        description=pgettext_lazy("admin ad list column", "ad"), ordering="id"
    )
    def ad(self, obj):
        return str(obj)

    @admin.display(
        description=pgettext_lazy("admin ad list column", "author"),
        ordering="author__username",
    )
    def author_as_string(self, obj):
        return obj.author


@admin.register(AdEntry)
class _AdEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "ad_pk", "language")
    list_filter = ("language",)
    search_fields = ("description", "name")

    @admin.display(
        description=pgettext_lazy("admin ad entry list column", "ad ID"),
        ordering="ad__id",
    )
    def ad_pk(self, obj):
        return obj.ad_id


@admin.register(AdImage)
class _AdImageAdmin(admin.ModelAdmin):
    list_display = ("image", "ad_as_string", "number")
    search_fields = ("image",)

    @admin.display(
        description=pgettext_lazy("admin ad image list column", "ad"), ordering="ad__id"
    )
    def ad_as_string(self, obj):
        return str(obj.ad)

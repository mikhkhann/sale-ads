import enum
from functools import cached_property
from types import MappingProxyType

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import (
    get_language,
    get_language_info,
    ngettext_lazy,
    pgettext_lazy,
)

from ads.models import Ad, AdEntry, AdImage
from categories.models import Category


class AdForm(forms.ModelForm):
    # ==========================================================
    # Fields

    price = Ad._meta.get_field("price").formfield(min_value=Ad._MIN_PRICE)

    # --------------------------------------
    # Category

    def _create_category_field(self):
        self.fields["category"] = forms.TypedChoiceField(
            choices=self._create_category_choices(), coerce=self._coerce_to_category
        )

    def _create_category_choices(self):
        return tuple(
            (category.pk, category.full_name)
            for category in sorted(
                self._category_cache.values(),
                key=lambda category: category.lowercased_full_name,
            )
            if category.ultimate
        )

    def _coerce_to_category(self, pk_as_string):
        pk = Category.pk_from_string(pk_as_string)
        return self._category_cache[pk]

    # ==========================================================

    class Meta:
        model = Ad
        fields = ("category", "price")

    def __init__(self, *args, category_cache, **kwargs):
        super().__init__(*args, **kwargs)
        self._category_cache = category_cache
        self._create_category_field()

    def create_initial_from_cleaned(self):
        return {
            "category": self.cleaned_data["category"].pk,
            "price": self.cleaned_data["price"],
        }


class _BaseAdImageFormSet(forms.BaseModelFormSet):
    class _Form(forms.ModelForm):
        image = AdImage._meta.get_field("image").formfield(required=False)

        class Meta:
            fields = ("image",)
            model = AdImage

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._own_non_form_errors = []

    def add_invalid_images_error_to(self, other):
        """
        Add "invalid images" error to another ad image formset.

        Creates an "invalid images" error from the own data and adds it
        as a non-form error to the other formset.
        Example:

        >>> from django.core.files.uploadedfile import (
        ...     SimpleUploadedFile,
        ... )
        >>>
        >>> formset_class = ad_image_formset_factory(3)
        >>> uploaded_image = SimpleUploadedFile("spam.jpg", b"ham")
        >>> files = {"form-0-image": uploaded_image}
        >>> data = {"form-INITIAL_FORMS": 0, "form-TOTAL_FORMS": 3}
        >>> formset = formset_class(data, files)
        >>> other_formset = formset_class()
        >>> formset.add_invalid_images_error_to(other_formset)
        >>> other_formset.non_form_errors()
        ['Image "spam.jpg" is invalid.']
        """
        self.errors
        forms = [form for form in self if not form.is_valid()]
        names = [f'"{form["image"].data.name}"' for form in forms]
        params = {"count": len(forms), "names": str.join(", ", names)}
        error = ValidationError(self._INVALID_IMAGES_ERROR, "invalid_images", params)
        other._own_non_form_errors.append(error)

    _INVALID_IMAGES_ERROR = ngettext_lazy(
        "Image %(names)s is invalid.", "Images %(names)s are invalid.", "count"
    )

    def non_form_errors(self):
        return super().non_form_errors() + self._own_non_form_errors


def ad_image_formset_factory(extra):
    """Create `AdImage` model formset class with unrequired image fields."""
    return forms.modelformset_factory(
        AdImage, _BaseAdImageFormSet._Form, extra=extra, formset=_BaseAdImageFormSet
    )


class AdEntryForm(forms.ModelForm):
    description = AdEntry._meta.get_field("description").formfield()
    language = forms.ChoiceField(
        choices=lambda: [
            (language, get_language_info(language)["name_local"])
            for language in settings.LANGUAGE_PREFERENCE_ORDER
        ],
        initial=get_language,
    )
    name = AdEntry._meta.get_field("name").formfield()

    class Meta:
        model = AdEntry
        fields = ("description", "language", "name")


AdImageCreateFormSet = ad_image_formset_factory(Ad.MAX_IMAGES)


class AdQueryForm(forms.Form):
    # ==========================================================
    # Fields

    URL_PARAMETERS = MappingProxyType(
        {
            "categories": "c",
            "languages": "l",
            "max_price": "b",
            "min_price": "a",
            "order": "o",
            "page_size": "n",
            "search": "s",
            "search_fields": "f",
        }
    )

    # --------------------------------------
    # Categories

    def _create_category_field(self):
        self.fields["categories"] = forms.TypedMultipleChoiceField(
            choices=lambda: self._category_choices,
            coerce=self._coerce_to_category,
            required=False,
        )

    @property
    def _category_choices(self):
        if self.is_bound:
            return self._create_category_choice_subset(
                self._get_category_cache().values()
            )
        category_cache = self._get_category_cache()
        selected_categories = {
            category_cache[pk] for pk in self.initial.get("categories", ())
        }
        non_selected_categories = set(category_cache.values()) - selected_categories
        selected_choices = self._create_category_choice_subset(selected_categories)
        non_selected_choices = self._create_category_choice_subset(
            non_selected_categories
        )
        return selected_choices + non_selected_choices

    def _create_category_choice_subset(self, categories):
        return [
            (category.pk, category.full_name)
            for category in sorted(
                categories, key=lambda category: category.lowercased_full_name
            )
        ]

    def _coerce_to_category(self, pk_as_string):
        pk = Category.pk_from_string(pk_as_string)
        return self._get_category_cache()[pk]

    @cached_property
    def cleaned_categories(self):
        return tuple(self._clean_mutli_choice_field("categories"))

    def _get_initial_categories_from_cleaned(self):
        return [category.pk for category in self.cleaned_categories]

    # --------------------------------------
    # Languages

    languages = forms.MultipleChoiceField(
        choices=lambda: [
            (language, get_language_info(language)["name_local"])
            for language in settings.LANGUAGE_PREFERENCE_ORDER
        ],
        required=False,
    )

    @cached_property
    def cleaned_languages(self):
        value = self._clean_mutli_choice_field("languages")
        if not value:
            value = self._get_default_languages()
        return tuple(value)

    @staticmethod
    def _get_default_languages():
        return [get_language()]

    def _get_initial_languages_from_cleaned(self):
        return list(self.cleaned_languages)

    # --------------------------------------
    # Order

    @enum.unique
    class Order(enum.IntEnum):
        HIGHEST_PRICE_FIRST = enum.auto()
        LOWEST_PRICE_FIRST = enum.auto()
        NEWEST_FIRST = enum.auto()
        OLDEST_FIRST = enum.auto()

        from_string = staticmethod(int)

        def __str__(self):
            return str(self.value)

    _EMPTY_ORDER = None

    order = forms.TypedChoiceField(
        choices=[
            (Order.NEWEST_FIRST, pgettext_lazy("ad order choice", "Newest first")),
            (Order.OLDEST_FIRST, pgettext_lazy("ad order choice", "Oldest first")),
            (
                Order.LOWEST_PRICE_FIRST,
                pgettext_lazy("ad order choice", "Price: lowest first"),
            ),
            (
                Order.HIGHEST_PRICE_FIRST,
                pgettext_lazy("ad order choice", "Price: highest first"),
            ),
        ],
        coerce=Order.from_string,
        empty_value=_EMPTY_ORDER,
        required=False,
    )

    @cached_property
    def cleaned_order(self):
        value = self._clean_field("order", self._EMPTY_ORDER)
        if value == self._EMPTY_ORDER:
            value = self._DEFAULT_ORDER
        return value

    _DEFAULT_ORDER = Order.NEWEST_FIRST

    def _get_initial_order_from_cleaned(self):
        return self.cleaned_order

    # ---------------------------------------
    # Page size

    _EMPTY_PAGE_SIZE = None

    page_size = forms.TypedChoiceField(
        choices=[(size, size) for size in [10, 25, 50]],
        coerce=int,
        empty_value=_EMPTY_PAGE_SIZE,
        required=False,
    )

    @cached_property
    def cleaned_page_size(self):
        value = self._clean_field("page_size", self._EMPTY_PAGE_SIZE)
        if value == self._EMPTY_PAGE_SIZE:
            value = self._DEFAULT_PAGE_SIZE
        return value

    _DEFAULT_PAGE_SIZE = 10

    def _get_initial_page_size_from_cleaned(self):
        return self.cleaned_page_size

    # --------------------------------------
    # Search

    search = forms.CharField(max_length=200, required=False)

    @cached_property
    def cleaned_search(self):
        return self._clean_field("search")

    def _get_initial_search_from_cleaned(self):
        return self.cleaned_search

    # --------------------------------------
    # Search fields

    @enum.unique
    class SearchField(enum.IntEnum):
        DESCRIPTION = enum.auto()
        NAME = enum.auto()

        from_string = staticmethod(int)

        def __str__(self):
            return str(self.value)

    search_fields = forms.TypedMultipleChoiceField(
        choices=[
            (SearchField.NAME, pgettext_lazy("ad search field choice", "Name")),
            (
                SearchField.DESCRIPTION,
                pgettext_lazy("ad search field choice", "Description"),
            ),
        ],
        coerce=SearchField.from_string,
        required=False,
    )

    @cached_property
    def cleaned_search_fields(self):
        value = self._clean_mutli_choice_field("search_fields")
        if not value:
            value = self._DEFAULT_SEARCH_FIELDS
        return tuple(value)

    _DEFAULT_SEARCH_FIELDS = tuple(SearchField)

    def _get_initial_search_fields_from_cleaned(self):
        return list(self.cleaned_search_fields)

    # --------------------------------------
    # Minimum & maximum prices

    min_price, max_price = [
        Ad._meta.get_field("price").formfield(min_value=Ad._MIN_PRICE, required=False)
        for i in range(2)
    ]

    @cached_property
    def cleaned_min_price(self):
        min_price, max_price = self._cleaned_limit_prices
        return min_price

    @cached_property
    def cleaned_max_price(self):
        min_price, max_price = self._cleaned_limit_prices
        return max_price

    @cached_property
    def _cleaned_limit_prices(self):
        min_price = self._clean_field("min_price", None)
        max_price = self._clean_field("max_price", None)
        if min_price is not None and max_price is not None and min_price > max_price:
            min_price = None
        return min_price, max_price

    def _get_initial_min_price_from_cleaned(self):
        return self.cleaned_min_price

    def _get_initial_max_price_from_cleaned(self):
        return self.cleaned_max_price

    # ==========================================================

    def __init__(self, *args, get_category_cache, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_category_cache = get_category_cache
        self._create_category_field()
        self._renamed_bound_fields = []

    class Factory:
        def __init__(self, get_category_cache):
            self._get_category_cache = get_category_cache

        def create(self, *args, **kwargs):
            return AdQueryForm(
                *args, get_category_cache=lambda: self._category_cache, **kwargs
            )

        @cached_property
        def _category_cache(self):
            return self._get_category_cache()

    def __getitem__(self, name):
        field = super().__getitem__(name)
        if field not in self._renamed_bound_fields:
            field.html_name = self.URL_PARAMETERS[name]
            self._renamed_bound_fields.append(field)
        return field

    _UNSPECIFIED_DEFAULT_CLEANED_VALUE = object()

    def _clean_field(self, name, default=_UNSPECIFIED_DEFAULT_CLEANED_VALUE):
        try:
            return self.fields[name].clean(self[name].data)
        except ValidationError:
            if default is not self._UNSPECIFIED_DEFAULT_CLEANED_VALUE:
                return default
            raise

    def _clean_mutli_choice_field(self, name):
        """
        Clean multi-choice field.

        If the value is a valid iterable of choices, then extracts those
        of them that are valid.
        Otherwise, returns an empty container.
        """
        value = self[name].data
        field = self.fields[name]
        try:
            value = field.to_python(value)
        except ValidationError:
            value = []
        new_value = []
        for choice in value:
            try:
                (choice,) = field.clean([choice])
            except ValidationError:
                pass
            else:
                new_value.append(choice)
        return new_value

    def get_field_initial_from_cleaned(self, name):
        """Get initial for field value from value from cleaned data."""
        return getattr(self, f"_get_initial_{name}_from_cleaned")()

    def create_initial_from_cleaned(self):
        return {name: self.get_field_initial_from_cleaned(name) for name in self.fields}


class AdDetailEntryChoiceForm(forms.Form):
    # ==========================================================
    # Fields

    # --------------------------------------
    # Language

    def _create_language_field(self, available_languages):
        self.fields["language"] = forms.ChoiceField(
            choices=[
                (language, get_language_info(language)["name_local"])
                for language in settings.LANGUAGE_PREFERENCE_ORDER
                if language in available_languages
            ]
        )

    # ==========================================================

    def __init__(self, *args, available_languages, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_language_field(available_languages)


class AdUpdateEntryChoiceForm(forms.Form):
    # ==========================================================
    # Fields

    # --------------------------------------
    # Language

    def _create_language_field(self, used_languages):
        self.fields["language"] = forms.ChoiceField(
            choices=self._create_language_choices(used_languages)
        )

    @staticmethod
    def _create_language_choices(used_languages):
        for language in settings.LANGUAGE_PREFERENCE_ORDER:
            local_name = get_language_info(language)["name_local"]
            note = (
                AdUpdateEntryChoiceForm._CREATED_NOTE
                if language in used_languages
                else AdUpdateEntryChoiceForm._NOT_CREATED_NOTE
            )
            yield (language, f"{local_name} ({note})")

    _CREATED_NOTE = pgettext_lazy("ad entry is created", "created")
    _NOT_CREATED_NOTE = pgettext_lazy("ad entry is not created", "not created")

    # ==========================================================

    def __init__(self, *args, used_languages, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_language_field(used_languages)

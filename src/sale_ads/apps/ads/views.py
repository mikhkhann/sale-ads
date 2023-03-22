from collections import namedtuple
from functools import cached_property
from types import MappingProxyType
from urllib.parse import urlencode, urlsplit, urlunsplit

from allauth.account.decorators import verified_email_required
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from ads.forms import (
    AdDetailEntryChoiceForm,
    AdEntryForm,
    AdForm,
    AdImageCreateFormSet,
    AdQueryForm,
    AdUpdateEntryChoiceForm,
    ad_image_formset_factory,
)
from ads.models import Ad, AdEntry, AdImage
from categories.models import Category


class _AdAuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.pk == self.get_user_pk_for_authorship_test()

    def get_user_pk_for_authorship_test(self):
        raise NotImplementedError


class _AdCreateView(CreateView):
    template_name = "ads/create.html"

    _IMAGE_FORMSET_PREFIX = "image_formset"

    def post(self, request, *args, **kwargs):
        self.object = None
        ad_form = self._create_ad_form()
        entry_form = AdEntryForm(request.POST)
        image_formset = self._create_image_formset(request.POST, request.FILES)
        if ad_form.is_valid() and entry_form.is_valid() and image_formset.is_valid():
            ad_form.instance.author = request.user
            self.object = ad_form.save()
            entry_form.instance.ad = ad_form.instance
            entry_form.save()
            images = []
            valid_non_empty_image_forms = filter(
                lambda form: form.cleaned_data, image_formset
            )
            for number, form in enumerate(valid_non_empty_image_forms, 1):
                form.instance.ad = self.object
                form.instance.number = number
                images.append(form.instance)
            AdImage.objects.bulk_create(images)
            return redirect(self.get_success_url())
        if not image_formset.is_valid():
            output_image_formset = self._create_image_formset()
            image_formset.add_invalid_images_error_to(output_image_formset)
        else:
            output_image_formset = None
        context = self.get_context_data(
            ad_form=ad_form, entry_form=entry_form, image_formset=output_image_formset
        )
        return self.render_to_response(context)

    def get_context_data(
        self, *, ad_form=None, entry_form=None, image_formset=None, **kwargs
    ):
        context = super().get_context_data(form=None, **kwargs)
        if ad_form is None:
            ad_form = self._create_ad_form()
        context["ad_form"] = ad_form
        if entry_form is None:
            entry_form = AdEntryForm()
        context["entry_form"] = entry_form
        if image_formset is None:
            image_formset = self._create_image_formset(queryset=AdImage.objects.none())
        context["image_formset"] = image_formset
        return context

    def _create_ad_form(self, **kwargs):
        return AdForm(
            category_cache=Category.objects.cache(), **(self.get_form_kwargs() | kwargs)
        )

    @staticmethod
    def _create_image_formset(*args, **kwargs):
        return AdImageCreateFormSet(
            *args, prefix=_AdCreateView._IMAGE_FORMSET_PREFIX, **kwargs
        )


_base_create = _AdCreateView.as_view()


def create(request, *args, **kwargs):
    decorator = (
        verified_email_required
        if settings.ADS_VERIFIED_EMAIL_REQUIRED_FOR_CREATION
        else login_required
    )
    return decorator(_base_create)(request, *args, **kwargs)


class _BaseAdListView(ListView):
    model = Ad
    page_kwarg = "p"

    _ORDERINGS = MappingProxyType(
        {
            AdQueryForm.Order.HIGHEST_PRICE_FIRST: "-price",
            AdQueryForm.Order.LOWEST_PRICE_FIRST: "price",
            AdQueryForm.Order.NEWEST_FIRST: "-created",
            AdQueryForm.Order.OLDEST_FIRST: "created",
        }
    )
    _DEFAULT_ORDERING = _ORDERINGS[AdQueryForm.Order.NEWEST_FIRST]

    _AD_QUERY_URL_PARAMETERS = frozenset(
        [*AdQueryForm.URL_PARAMETERS.values(), page_kwarg]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._category_ad_counts = {}

    # ==========================================================
    # Queryset

    def get_queryset(self):
        return self._queryset

    @cached_property
    def _queryset(self):
        return (
            super()
            .get_queryset()
            .filter(self._get_condition())
            .distinct()
            .select_related("author", "category")
            .prefetch_related("entries", "images")
        )

    def get_ordering(self):
        orderings = [self._ORDERINGS[self._query_form.cleaned_order]]
        if self._DEFAULT_ORDERING not in orderings:
            orderings.append(self._DEFAULT_ORDERING)
        return orderings

    # ==========================================================
    # Context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ad_count"] = self._queryset.count()
        context["category_tree"] = self._get_context_category_tree()
        context["query_form"] = self._query_form_factory.create(
            initial=self._query_form.create_initial_from_cleaned()
        )
        context["other_page_url_template"] = self._get_page_url_html_template()
        context["one_side_neighboring_pages"] = self._ONE_SIDE_NEIGHBORING_PAGES
        context["previous_pages"] = self._get_previous_pages(context["page_obj"])
        context["next_pages"] = self._get_next_pages(
            context["page_obj"], context["paginator"]
        )
        return context

    def get_paginate_by(self, queryset):
        return self._query_form.cleaned_page_size

    # --------------------------------------
    # Category tree

    def _get_context_category_tree(self):
        roots = [
            category
            for category in self._category_cache.values()
            if category.parent is None
        ]
        sorted_roots = sorted(roots, key=lambda category: category.lowercased_name)
        return self._get_context_category_tree_siblings(sorted_roots)

    def _get_context_category_tree_siblings(self, siblings):
        result = []
        for sibling in siblings:
            url = self._category_tree_url_template.format(sibling.pk)
            ad_count = self._get_category_ad_count(sibling.pk)
            children = self._get_context_category_tree_siblings(sibling.sorted_children)
            node = self._CategoryTreeNode(sibling.name, url, ad_count, children)
            result.append(node)
        return result

    @cached_property
    def _category_tree_url_template(self):
        parameter_name = AdQueryForm.URL_PARAMETERS["categories"]
        other_url_parameters = self._get_ad_query_url_parameters(
            self._AD_QUERY_URL_PARAMETERS - {parameter_name, self.page_kwarg}
        )
        return self._get_url_template_with_fillable_parameter(
            parameter_name, other_url_parameters
        )

    def _get_category_ad_count(self, pk):
        try:
            return self._category_ad_counts[pk]
        except KeyError:
            category = self._category_cache[pk]
            count = category.own_ad_count
            for child in category.all_children:
                count += self._get_category_ad_count(child.pk)
            self._category_ad_counts[pk] = count
            return count

    _CategoryTreeNode = namedtuple(
        "_CategoryTreeNode", ["name", "url", "ad_count", "children"]
    )

    # --------------------------------------
    # Numbers of neighboring pages

    _ONE_SIDE_NEIGHBORING_PAGES = 3

    @staticmethod
    def _get_previous_pages(page):
        first = max(page.number - _BaseAdListView._ONE_SIDE_NEIGHBORING_PAGES, 1)
        return range(first, page.number)

    @staticmethod
    def _get_next_pages(page, paginator):
        last = min(
            page.number + _BaseAdListView._ONE_SIDE_NEIGHBORING_PAGES,
            paginator.num_pages,
        )
        return range(page.number + 1, last + 1)

    # --------------------------------------
    # Template of URLs of other pages

    def _get_page_url_html_template(self):
        other_parameters = self._get_ad_query_url_parameters(
            self._AD_QUERY_URL_PARAMETERS - {self.page_kwarg}
        )
        string_template = self._get_url_template_with_fillable_parameter(
            self.page_kwarg, other_parameters
        )
        return self._PageURLHTMLTemplate(string_template)

    class _PageURLHTMLTemplate:
        def __init__(self, string_template):
            self._string_template = string_template

        def render(self, context):
            return self._string_template.format(context["number"])

    # ==========================================================
    # Utilities

    # --------------------------------------
    # Ad query URL parameters

    def _get_ad_query_url_parameters(self, names):
        parameters = {}
        for name in names:
            for field in self._query_form:
                if field.html_name == name:
                    value = self._query_form.get_field_initial_from_cleaned(field.name)
                    break
            else:
                value = self.request.GET.get(name)
            if value is not None:
                parameters[name] = value
        return parameters

    # --------------------------------------
    # Condition

    def _get_condition(self, *, categories=True, prefix=""):
        condition = Q()

        # Categories
        if categories:
            root_categories = self._query_form.cleaned_categories
            if root_categories:
                categories = set(root_categories)
                for root_category in root_categories:
                    categories.update(root_category.descendants)
                condition &= Q(category__in=[category.pk for category in categories])

        # Languages
        language_condition = Q()
        for language in self._query_form.cleaned_languages:
            language_condition |= Q(**{f"{prefix}entries__language": language})
        condition &= language_condition

        # Price
        price_condition = Q()
        min_price = self._query_form.cleaned_min_price
        if min_price is not None:
            price_condition &= Q(**{f"{prefix}price__gte": min_price})
        max_price = self._query_form.cleaned_max_price
        if max_price is not None:
            price_condition &= Q(**{f"{prefix}price__lte": max_price})
        condition &= price_condition

        # Search
        search = self._query_form.cleaned_search
        if search:
            search_condition = Q()
            search_fields = self._query_form.cleaned_search_fields
            for keyword in set(search.split()):
                keyword_search_condition = Q()
                for field in search_fields:
                    keyword_search_condition |= (
                        self._create_field_keyword_search_condition(
                            field, keyword, prefix
                        )
                    )
                search_condition &= keyword_search_condition
            condition &= search_condition

        return condition

    def _create_field_keyword_search_condition(self, field, keyword, prefix=""):
        method = self._CREATE_FIELD_KEYWORD_SEARCH_CONDITION_METHODS[field]
        return method(self, keyword, prefix)

    def _create_description_keyword_search_condition(self, keyword, prefix=""):
        return self._create_entry_field_keyword_search_condition(
            "description", keyword, prefix
        )

    def _create_name_keyword_search_condition(self, keyword, prefix=""):
        return self._create_entry_field_keyword_search_condition(
            "name", keyword, prefix
        )

    @staticmethod
    def _create_entry_field_keyword_search_condition(name, keyword, prefix=""):
        return Q(**{f"{prefix}entries__{name}__icontains": keyword})

    _CREATE_FIELD_KEYWORD_SEARCH_CONDITION_METHODS = MappingProxyType(
        {
            AdQueryForm.SearchField.DESCRIPTION: (
                _create_description_keyword_search_condition
            ),
            AdQueryForm.SearchField.NAME: _create_name_keyword_search_condition,
        }
    )

    # --------------------------------------
    # Query string unparsing

    @staticmethod
    def _unparse_query_string(parameters):
        return urlencode(parameters, doseq=True)

    # --------------------------------------
    # URL template with fillable parameter

    def _get_url_template_with_fillable_parameter(self, name, other_parameters=None):
        query_string = (
            self._unparse_query_string(other_parameters)
            if other_parameters is not None
            else ""
        )
        query_string = self._double_curly_braces(query_string) + f"&{name}={{}}"
        own_url = self.request.get_full_path()
        own_url = self._double_curly_braces(own_url)
        old_url_items = urlsplit(own_url)
        return urlunsplit([*old_url_items[:3], query_string, *old_url_items[4:]])

    @staticmethod
    def _double_curly_braces(string):
        return string.replace("{", "{{").replace("}", "}}")

    # ==========================================================
    # Data attributes

    @cached_property
    def _category_cache(self):
        own_ad_count_condition = self._get_condition(categories=False, prefix="ad__")
        own_ad_count = Count("ad", filter=own_ad_count_condition)
        return Category.objects.annotate(own_ad_count=own_ad_count).cache()

    @cached_property
    def _query_form(self):
        return self._query_form_factory.create(self.request.GET)

    @cached_property
    def _query_form_factory(self):
        return AdQueryForm.Factory(get_category_cache=lambda: self._category_cache)


class _AdListView(_BaseAdListView):
    template_name = "ads/list.html"

    _URL_PATH = reverse_lazy("ads_list")

    def _get_condition(self, *args, prefix="", **kwargs):
        condition = super()._get_condition(*args, prefix=prefix, **kwargs)
        return condition & Q(**{f"{prefix}verified": True})

    @staticmethod
    def get_category_url(pk):
        parameters = {AdQueryForm.URL_PARAMETERS["categories"]: pk}
        query_string = _AdListView._unparse_query_string(parameters)
        return urlunsplit(["", "", str(_AdListView._URL_PATH), query_string, ""])


list_ = _AdListView.as_view()

get_category_ad_list_url = _AdListView.get_category_url


class _UserAdListView(_BaseAdListView):
    template_name = "ads/user_list.html"

    _URL_PATTERN_NAME = "ads_user_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["viewed_user"] = self._viewed_user
        return context

    def _get_condition(self, *args, prefix="", **kwargs):
        condition = super()._get_condition(*args, prefix=prefix, **kwargs)
        condition &= Q(**{f"{prefix}author": self._viewed_user})
        if self.request.user != self._viewed_user:
            condition &= Q(**{f"{prefix}verified": True})
        return condition

    @cached_property
    def _viewed_user(self):
        try:
            return get_user_model().objects.get(username=self.kwargs["username"])
        except get_user_model().DoesNotExist:
            raise Http404


user_list = _UserAdListView.as_view()


class _AdDetailView(DetailView):
    model = Ad
    template_name = "ads/detail.html"

    _LANGUAGE_URL_PARAMETER = "language"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related("author", "category")
        return queryset.prefetch_related("entries", "images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entry"] = self._entry
        context["entry_choice_form"] = self._get_entry_choice_form()
        context["entry_language_url_parameter_name"] = self._LANGUAGE_URL_PARAMETER
        return context

    def _get_entry_choice_form(self):
        data = {"language": self._entry.language}
        available_languages = [entry.language for entry in self.object.entries.all()]
        return AdDetailEntryChoiceForm(data, available_languages=available_languages)

    @cached_property
    def _entry(self):
        language = self.request.GET.get(self._LANGUAGE_URL_PARAMETER)
        if not language:
            language = get_language()
        return self.object.get_entry(language)


detail = _AdDetailView.as_view()


class _AdUpdateView(_AdAuthorRequiredMixin, UpdateView):
    model = Ad
    template_name = "ads/update.html"

    def get_user_pk_for_authorship_test(self):
        return self._object.author_id

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self._perform_post_action(request.POST["action"])

    def _perform_post_action(self, action):
        method = self._POST_ACTION_METHODS[action]
        return method(self)

    def _update(self):
        form = self._create_ad_form(self.request.POST)
        if form.is_valid():
            self.object.save(update_fields=form.changed_data)
        context = self.get_context_data(ad_form=form)
        return self.render_to_response(context)

    def _create_or_update_entry(self):
        form = self._create_entry_choice_form(self.request.POST)
        if form.is_valid():
            language = form.cleaned_data["language"]
            url_pattern_name = (
                "ads_update_entry"
                if any(entry.language == language for entry in self._entries)
                else "ads_create_entry"
            )
            return redirect(
                url_pattern_name, ad_pk=self.kwargs["pk"], language=language
            )
        context = self.get_context_data(entry_choice_form=form)
        return self.render_to_response(context)

    def _delete_entry(self):
        form = self._create_entry_choice_form(self.request.POST)
        output_form = None
        if form.is_valid():
            language = form.cleaned_data["language"]
            try:
                (entry,) = [
                    entry for entry in self._entries if entry.language == language
                ]
            except ValueError:
                pass
            else:
                if len(self._entries) > 1:
                    entry.delete()
                    self._entries.remove(entry)
                else:
                    error = ValidationError(
                        self._SINGLE_ENTRY_DELETION_ERROR, "single_entry_deletion"
                    )
                    form.add_error(None, error)
                    output_form = form
        else:
            output_form = form
        context = self.get_context_data(entry_choice_form=output_form)
        return self.render_to_response(context)

    _SINGLE_ENTRY_DELETION_ERROR = _(
        "The only remaining entry of an ad can't be removed."
    )

    _POST_ACTION_METHODS = MappingProxyType(
        {
            "create_or_update_entry": _create_or_update_entry,
            "delete_entry": _delete_entry,
            "update": _update,
        }
    )

    def get_object(self, queryset=None):
        return self._object

    @cached_property
    def _object(self):
        return super().get_object()

    def get_context_data(self, *, ad_form=None, entry_choice_form=None, **kwargs):
        context = super().get_context_data(form=None, **kwargs)
        if not ad_form:
            ad_form = self._create_ad_form()
        context["ad_form"] = ad_form
        if not entry_choice_form:
            entry_choice_form = self._create_entry_choice_form()
        context["entry_choice_form"] = entry_choice_form
        return context

    def _create_ad_form(self, *args, **kwargs):
        return AdForm(
            *args,
            category_cache=Category.objects.cache(),
            instance=self.object,
            **kwargs,
        )

    def _create_entry_choice_form(self, *args, **kwargs):
        used_languages = [entry.language for entry in self._entries]
        return AdUpdateEntryChoiceForm(*args, used_languages=used_languages, **kwargs)

    @cached_property
    def _entries(self):
        return list(self.object.entries.all())


update = _AdUpdateView.as_view()


class _AdEntryCreateOrUpdateMixin(_AdAuthorRequiredMixin):
    fields = ("description", "name")
    model = AdEntry

    @cached_property
    def _created(self):
        try:
            self._object
        except AdEntry.DoesNotExist:
            return False
        return True

    def form_valid(self, form):
        Ad.objects.filter(pk=self.kwargs["ad_pk"]).update(verified=False)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ads_update", kwargs={"pk": self.kwargs["ad_pk"]})

    @cached_property
    def _object(self):
        return self.get_queryset().get()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            ad_id=self.kwargs["ad_pk"], language=self.kwargs["language"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entry_language"] = self.kwargs["language"]
        return context


class _AdEntryCreateView(_AdEntryCreateOrUpdateMixin, CreateView):
    template_name = "ads/create_entry.html"

    def get_user_pk_for_authorship_test(self):
        return Ad.objects.get(pk=self.kwargs["ad_pk"]).author_id

    def dispatch(self, *args, ad_pk, language, **kwargs):
        if self._created:
            return redirect("ads_update_entry", ad_pk=ad_pk, language=language)
        return super().dispatch(*args, ad_pk=ad_pk, language=language, **kwargs)

    def form_valid(self, form):
        form.instance.ad_id = self.kwargs["ad_pk"]
        form.instance.language = self.kwargs["language"]
        return super().form_valid(form)


create_entry = _AdEntryCreateView.as_view()


class _AdEntryUpdateView(_AdEntryCreateOrUpdateMixin, UpdateView):
    template_name = "ads/update_entry.html"

    def get_user_pk_for_authorship_test(self):
        return self._object.ad.author_id

    def dispatch(self, *args, ad_pk, language, **kwargs):
        if not self._created:
            return redirect("ads_create_entry", ad_pk=ad_pk, language=language)
        return super().dispatch(*args, ad_pk=ad_pk, language=language, **kwargs)

    def get_object(self, queryset=None):
        return self._object

    def get_queryset(self):
        return super().get_queryset().select_related("ad")


update_entry = _AdEntryUpdateView.as_view()


class _AdImagesUpdateView(_AdAuthorRequiredMixin, UpdateView):
    model = Ad
    template_name = "ads/update_images.html"

    _ADDITION_FORMSET_PREFIX = "addition_formset"

    def get_user_pk_for_authorship_test(self):
        return self._object.author_id

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self._perform_post_action(request.POST["action"])

    def _perform_post_action(self, action):
        method = self._POST_ACTION_METHODS[action]
        return method(self)

    def _add(self):
        formset = self._create_addition_formset(self.request.POST, self.request.FILES)
        formset.full_clean()
        images = []
        valid_non_empty_forms = filter(
            lambda form: form.is_valid() and form.cleaned_data, formset
        )
        for number, form in enumerate(valid_non_empty_forms, len(self._images) + 1):
            form.instance.ad = self.object
            form.instance.number = number
            images.append(form.instance)
        AdImage.objects.bulk_create(images)
        self._images.extend(images)
        if images:
            self._unverify_ad()
        if not formset.is_valid():
            output_formset = self._create_output_addition_formset()
            formset.add_invalid_images_error_to(output_formset)
        else:
            output_formset = None
        context = self.get_context_data(addition_formset=output_formset)
        return self.render_to_response(context)

    def _delete(self):
        number = int(self.request.POST["number"])
        index = number - 1
        ordered_images = self._get_ordered_images()
        image = ordered_images.pop(index)
        image.delete()
        self._images.remove(image)
        next_images = ordered_images[index:]
        for next_image in next_images:
            next_image.number -= 1
        AdImage.objects.bulk_update(next_images, ["number"])
        self._unverify_ad()
        context = self.get_context_data()
        return self.render_to_response(context)

    def _reorder(self):
        direction = self.request.POST["direction"]
        number = int(self.request.POST["number"])
        self._move(direction, number)
        context = self.get_context_data()
        return self.render_to_response(context)

    def _move(self, direction, number):
        method = self._MOVE_METHODS[direction]
        method(self, number)

    def _move_up(self, number):
        self._move_in_direction(number, -1, exception=1)

    def _move_down(self, number):
        self._move_in_direction(number, +1, exception=len(self._images))

    def _move_in_direction(self, number, shift, exception):
        if number != exception:
            index = number - 1
            ordered_images = self._get_ordered_images()
            image = ordered_images[index]
            other_image = ordered_images[index + shift]
            image.number, other_image.number = other_image.number, image.number
            AdImage.objects.bulk_update([image, other_image], ["number"])
            self._unverify_ad()

    _MOVE_METHODS = MappingProxyType({"up": _move_up, "down": _move_down})

    def _unverify_ad(self):
        self._object.verified = False
        self._object.save(update_fields=["verified"])

    _POST_ACTION_METHODS = MappingProxyType(
        {"add": _add, "delete": _delete, "reorder": _reorder}
    )

    def get_object(self, queryset=None):
        return self._object

    @cached_property
    def _object(self):
        return super().get_object()

    def get_queryset(self):
        return super().get_queryset().prefetch_related("images")

    def _get_ordered_images(self):
        return sorted(self._images, key=lambda image: image.number)

    def get_context_data(self, *, addition_formset=None, **kwargs):
        context = super().get_context_data(form=None, **kwargs)
        if addition_formset is None:
            addition_formset = self._create_output_addition_formset()
        context["addition_formset"] = addition_formset
        return context

    def _create_output_addition_formset(self, *args, **kwargs):
        return self._create_addition_formset(
            *args, queryset=AdImage.objects.none(), **kwargs
        )

    def _create_addition_formset(self, *args, **kwargs):
        extra = Ad.MAX_IMAGES - len(self._images)
        formset_class = ad_image_formset_factory(extra)
        return formset_class(*args, prefix=self._ADDITION_FORMSET_PREFIX, **kwargs)

    @cached_property
    def _images(self):
        return list(self.object.images.all())


update_images = _AdImagesUpdateView.as_view()


class _AdDeleteView(_AdAuthorRequiredMixin, DeleteView):
    model = Ad
    template_name = "ads/delete.html"

    def get_user_pk_for_authorship_test(self):
        return self._object.author_id

    def get_object(self, queryset=None):
        return self._object

    @cached_property
    def _object(self):
        return super().get_object()

    def get_success_url(self):
        return reverse("ads_user_list", kwargs={"username": self.request.user.username})


delete = _AdDeleteView.as_view()

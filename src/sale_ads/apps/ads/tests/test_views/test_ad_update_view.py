from collections import Counter
from decimal import Decimal
from http import HTTPStatus

from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.urls import reverse

from ads.forms import AdUpdateEntryChoiceForm
from ads.views import _AdUpdateView
from categories.models import Category
from common.tests import (
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
)
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)
from common.tests.utils.http_request_query_comparison import HTTPRequestQueryTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdUpdateViewTestMixin(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    HTTPRequestQueryTestMixin,
    ViewTestMixin,
):
    required_language_count = 3
    url_pattern_name = "ads_update"

    @classmethod
    def setUpClass(cls):
        cls.old_price = None
        cls.used_language = None
        cls.unused_language = None
        super().setUpClass()
        cls.invalid_language = cls.create_ad_entry_language_factory().get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = cls.create_user_factory().create()
        cls.category_factory = cls.create_category_factory()
        cls.old_category = cls.category_factory.create()
        ad_factory = cls.create_ad_factory(author=cls.author, category=cls.old_category)
        if cls.old_price is None:
            cls.old_price = cls.create_ad_price_factory().get_unique()
        cls.ad = ad_factory.create(price=cls.old_price)
        cls.entry_factory = cls.create_ad_entry_factory(ad=cls.ad)
        if cls.used_language is None and cls.unused_language is None:
            language_factory = cls.create_ad_entry_language_factory()
            cls.used_language = language_factory.get_choice(0)
            cls.unused_language = language_factory.get_choice(1)
        cls.required_entry = cls.entry_factory.create(language=cls.used_language)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.author)

    def get_url_pattern_kwargs(self):
        return {"pk": self.ad.pk}

    def post_entry_choice_form_with_invalid_language(
        self, url=None, data=None, *args, **kwargs
    ):
        if data is None:
            data = {}
        data["language"] = self.invalid_language
        return self.post(url, data, *args, **kwargs)

    def _test_context_ad_form(self, response, *, category_pk, price):
        form = response.context["ad_form"]
        self.assertHTTPRequestParameterEqual(form["category"].value(), category_pk)
        self.assertHTTPRequestParameterEqual(
            form["price"].value(),
            price,
            unify=lambda price: format(Decimal(price).normalize(), "f"),
        )

    def prepare_ad_form_category_value(self, value):
        if value is not None:
            value = str(value)
        return value

    def _test_context_entry_choice_form(
        self, response, used_languages, expected_language
    ):
        form = response.context["entry_choice_form"]
        actual_choices = form.fields["language"].choices
        expected_choices = AdUpdateEntryChoiceForm._create_language_choices(
            used_languages
        )
        self.assertDictEqual(Counter(actual_choices), Counter(expected_choices))
        self.assertEqual(form["language"].value(), expected_language)


class AdUpdateViewGeneralTest(AdUpdateViewTestMixin, TestCase):
    # ==========================================================
    # User permissions

    def test_redirects_to_login_if_user_is_anonymous(self):
        self.client.logout()
        url = self.get_url()
        response = self.get(expected_status=HTTPStatus.FOUND)
        self._test_redirects_to_login(response, url)

    def test_forbidden_if_user_is_authenticated_but_is_not_author(self):
        self.client.logout()
        other_user = self.create_user_factory().create()
        self.client.force_login(other_user)
        self.get(expected_status=HTTPStatus.FORBIDDEN)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "ads/update.html")

    # ==========================================================
    # Context

    # --------------------------------------
    # Ad form

    def test_context_ad_form(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(
            response, category_pk=self.old_category.pk, price=self.old_price
        )

    # --------------------------------------
    # Entry choice form

    def test_context_entry_choice_form(self):
        self.entry_factory.create(language=self.unused_language)
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(
            response, [self.used_language, self.unused_language], None
        )


class AdUpdateViewGetTest(AdUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)


class AdUpdateViewPostUpdateTest(AdUpdateViewTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        price_factory = cls.create_ad_price_factory()
        cls.new_price = price_factory.get_unique()
        create_category_pk_factory = getattr(
            cls, f"create_category_{Category._meta.pk.name}_factory"
        )
        cls.invalid_category_pk = create_category_pk_factory().get_invalid()
        cls.invalid_price = price_factory.get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.new_category = cls.category_factory.create(ultimate=True)

    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad model

    def test_ad_with_new_field_values(self):
        self.post_with_new_field_values(expected_status=HTTPStatus.OK)
        self._test_ad(category_pk=self.new_category.pk, price=self.new_price)

    def test_ad_with_invalid_field_values(self):
        self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_ad_unchanged()

    def test_ad_with_without_field_values(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_ad_unchanged()

    def _test_ad(self, category_pk, price):
        self.ad.refresh_from_db(fields=["category", "price"])
        self.assertEqual(self.ad.category_id, category_pk)
        self.assertEqual(self.ad.price, price)

    def _test_ad_unchanged(self):
        self._test_ad(category_pk=self.old_category.pk, price=self.old_price)

    # ==========================================================
    # Context

    # --------------------------------------
    # Ad form

    def test_context_ad_form_with_new_field_values(self):
        response = self.post_with_new_field_values(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(
            response, category_pk=self.new_category.pk, price=self.new_price
        )

    def test_context_ad_form_with_invalid_field_values(self):
        response = self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(
            response, category_pk=self.invalid_category_pk, price=self.invalid_price
        )

    def test_context_ad_form_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(response, category_pk=None, price=None)

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "update"
        return super().post(url, data, *args, **kwargs)

    def post_with_new_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data.update({"category": self.new_category.pk, "price": self.new_price})
        return self.post(url, data, *args, **kwargs)

    def post_with_invalid_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data.update({"category": self.invalid_category_pk, "price": self.invalid_price})
        return self.post(url, data, *args, **kwargs)


class AdUpdateViewPostCreateOrUpdateEntryTest(AdUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Redirections

    def test_redirects_to_create_entry_with_language_of_not_existing_entry(self):
        response = self.post(
            data={"language": self.unused_language},
            expected_status=HTTPStatus.FOUND,
        )
        expected_url = reverse(
            "ads_create_entry",
            kwargs={"ad_pk": self.ad.pk, "language": self.unused_language},
        )
        self.assertRedirects(response, expected_url)

    def test_redirects_to_update_entry_with_language_of_existing_entry(self):
        response = self.post(
            data={"language": self.used_language}, expected_status=HTTPStatus.FOUND
        )
        expected_url = reverse(
            "ads_update_entry",
            kwargs={"ad_pk": self.ad.pk, "language": self.used_language},
        )
        self.assertRedirects(response, expected_url)

    # ==========================================================
    # Context

    # --------------------------------------
    # Entry choice form

    def test_context_entry_choice_form_with_invalid_language(self):
        response = self.post_entry_choice_form_with_invalid_language(
            expected_status=HTTPStatus.OK
        )
        self._test_context_entry_choice_form(
            response, [self.used_language], self.invalid_language
        )

    def test_context_entry_choice_form_without_language(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(response, [self.used_language], None)

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "create_or_update_entry"
        return super().post(url, data, *args, **kwargs)


class AdUpdateViewPostDeleteEntryTest(AdUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad entry model

    def test_entries(self):
        self.entry_factory.create(language=self.unused_language)
        self.post_with_unused_language(expected_status=HTTPStatus.OK)
        self.assertFalse(self.ad.entries.filter(language=self.unused_language).exists())

    # ==========================================================
    # Context

    # --------------------------------------
    # Entry choice form

    def test_context_entry_choice_form_with_language_of_one_existing_entries(self):
        self.entry_factory.create(language=self.unused_language)
        response = self.post_with_unused_language(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(response, [self.used_language], None)

    def test_context_entry_choice_form_with_language_of_not_existing_entry(self):
        response = self.post_with_unused_language(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(response, [self.used_language], None)

    def test_context_entry_choice_form_with_language_of_single_existing_entry(self):
        response = self.post_with_used_language(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(
            response, [self.used_language], self.used_language
        )

    def test_context_entry_choice_form_with_invalid_language(self):
        response = self.post_entry_choice_form_with_invalid_language(
            expected_status=HTTPStatus.OK
        )
        self._test_context_entry_choice_form(
            response, [self.used_language], self.invalid_language
        )

    def test_context_entry_choice_form_without_language(self):
        self.entry_factory.create(language=self.unused_language)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_entry_choice_form(
            response, [self.used_language, self.unused_language], None
        )

    # "Single entry deletion" error

    def test_context_entry_choice_form_single_entry_deletion_error_with_error(self):
        response = self.post_with_used_language(expected_status=HTTPStatus.OK)
        form = response.context["entry_choice_form"]
        (actual_error,) = form.non_field_errors()
        self.assertEqual(actual_error, _AdUpdateView._SINGLE_ENTRY_DELETION_ERROR)

    def test_context_entry_choice_form_single_entry_deletion_error_without_error(self):
        self.entry_factory.create(language=self.unused_language)
        response = self.post_with_unused_language(expected_status=HTTPStatus.OK)
        form = response.context["entry_choice_form"]
        self.assertEqual(len(form.non_field_errors()), 0)

    def test_context_entry_choice_form_single_entry_deletion_error_code(self):
        response = self.post_with_used_language(expected_status=HTTPStatus.OK)
        form = response.context["entry_choice_form"]
        self.assertTrue(form.has_error(NON_FIELD_ERRORS, "single_entry_deletion"))

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "delete_entry"
        return super().post(url, data, *args, **kwargs)

    def post_with_used_language(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["language"] = self.used_language
        return self.post(url, data, *args, **kwargs)

    def post_with_unused_language(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["language"] = self.unused_language
        return self.post(url, data, *args, **kwargs)

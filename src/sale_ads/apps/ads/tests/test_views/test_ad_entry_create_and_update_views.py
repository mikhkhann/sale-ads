from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from common.tests import SaleAdsTestMixin
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdEntryCreateOrUpdateViewTestMixin(
    SaleAdsTestMixin, CompositeLanguagesSettingTestMixin, ViewTestMixin
):
    @classmethod
    def setUpClass(cls):
        cls.used_language = None
        cls.unused_language = None
        super().setUpClass()
        cls.invalid_description = (
            cls.create_ad_entry_description_factory().get_invalid()
        )
        cls.invalid_name = cls.create_ad_entry_name_factory().get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if cls.used_language is None and cls.unused_language is None:
            language_factory = cls.create_ad_entry_language_factory()
            cls.used_language = language_factory.get_choice(0)
            cls.unused_language = language_factory.get_choice(1)
        cls.author = cls.create_user_factory().create()
        cls.ad = cls.create_ad_factory(author=cls.author).create()
        entry_factory = cls.create_ad_entry_factory(ad=cls.ad)
        cls.required_entry = entry_factory.create(**cls.get_required_entry_kwargs())

    @classmethod
    def get_required_entry_kwargs(cls):
        return {"language": cls.used_language}

    def setUp(self):
        super().setUp()
        self.client.force_login(self.author)

    def get_url_pattern_kwargs(self, *, ad_pk=None, language=None):
        if ad_pk is None:
            ad_pk = self.ad.pk
        if language is None:
            language = self.language
        return {"ad_pk": ad_pk, "language": language}

    def _test_entry(self, entry, *, description, name):
        self.assertEqual(entry.ad_id, self.ad.pk)
        self.assertEqual(entry.description, description)
        self.assertEqual(entry.name, name)

    def _test_context_form(self, response, *, description, name):
        form = response.context["form"]
        self.assertEqual(form["description"].value(), description)
        self.assertEqual(form["name"].value(), name)


class AdEntryCreateViewTestMixin:
    url_pattern_name = "ads_create_entry"

    @classmethod
    @property
    def language(cls):
        return cls.unused_language

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.description = cls.create_ad_entry_description_factory().get_unique()
        cls.name = cls.create_ad_entry_name_factory().get_unique()


class AdEntryUpdateViewTestMixin:
    url_pattern_name = "ads_update_entry"

    @classmethod
    @property
    def language(cls):
        return cls.used_language

    @classmethod
    def setUpClass(cls):
        cls._old_description = None
        cls._old_name = None
        super().setUpClass()
        cls.new_description = cls.create_ad_entry_description_factory().get_unique()
        cls.new_name = cls.create_ad_entry_name_factory().get_unique()
        cls.entry = cls.required_entry

    @classmethod
    @property
    def old_description(cls):
        if cls._old_description is None:
            cls._old_description = (
                cls.create_ad_entry_description_factory().get_unique()
            )
        return cls._old_description

    @classmethod
    @property
    def old_name(cls):
        if cls._old_name is None:
            cls._old_name = cls.create_ad_entry_name_factory().get_unique()
        return cls._old_name

    @classmethod
    def get_required_entry_kwargs(cls):
        kwargs = super().get_required_entry_kwargs()
        return kwargs | {"description": cls.old_description, "name": cls.old_name}


###############################################################################
# General


class AdEntryCreateOrUpdateViewGeneralTestMixin(AdEntryCreateOrUpdateViewTestMixin):
    # ==========================================================
    # User permissions

    def test_redirects_to_login_if_user_is_anonymous(self):
        self.client.logout()
        url = self.get_url()
        response = self.get(url, expected_status=HTTPStatus.FOUND)
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
        self.assertTemplateUsed(response, self.template_name)

    # ==========================================================
    # Context

    # --------------------------------------
    # Entry language

    def test_context_entry_language(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["entry_language"], self.language)

    # ==========================================================

    def _test_redirects_to_another_if_created_or_not_created(
        self, language, expected_url_pattern_name
    ):
        url = self.get_url(language=language)
        response = self.get(url, expected_status=HTTPStatus.FOUND)
        expected_url = reverse(
            expected_url_pattern_name,
            kwargs={"ad_pk": self.ad.pk, "language": language},
        )
        self.assertRedirects(response, expected_url)


class AdEntryCreateViewGeneralTest(
    AdEntryCreateViewTestMixin, AdEntryCreateOrUpdateViewGeneralTestMixin, TestCase
):
    template_name = "ads/create_entry.html"

    # ==========================================================
    # Redirections

    def test_redirects_to_update_if_created(self):
        self._test_redirects_to_another_if_created_or_not_created(
            self.used_language, "ads_update_entry"
        )


class AdEntryUpdateViewGeneralTest(
    AdEntryUpdateViewTestMixin, AdEntryCreateOrUpdateViewGeneralTestMixin, TestCase
):
    template_name = "ads/update_entry.html"

    # ==========================================================
    # Redirections

    def test_redirects_to_create_if_not_created(self):
        self._test_redirects_to_another_if_created_or_not_created(
            self.unused_language, "ads_create_entry"
        )


###############################################################################
# Get


class AdEntryCreateOrUpdateViewGetTestMixin(AdEntryCreateOrUpdateViewTestMixin):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def test_context_form(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_form(
            response, **self.get_context_form_expected_field_values()
        )


class AdEntryCreateViewGetTest(
    AdEntryCreateViewTestMixin, AdEntryCreateOrUpdateViewGetTestMixin, TestCase
):
    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def get_context_form_expected_field_values(self):
        return {"description": None, "name": None}


class AdEntryUpdateViewGetTest(
    AdEntryUpdateViewTestMixin, AdEntryCreateOrUpdateViewGetTestMixin, TestCase
):
    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def get_context_form_expected_field_values(self):
        return {"description": self.old_description, "name": self.old_name}


###############################################################################
# Post


class AdEntryCreateOrUpdateViewPostTestMixin(AdEntryCreateOrUpdateViewTestMixin):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_invalid_field_values(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    def test_ad_verified_without_field_values(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post(expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    # ==========================================================
    # Redirections

    def test_redirects_to_ads_update_on_success(self):
        data = self.get_success_field_values()
        response = self.post(data=data, expected_status=HTTPStatus.FOUND)
        expected_url = reverse("ads_update", kwargs={"pk": self.ad.pk})
        self.assertRedirects(response, expected_url)

    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def test_context_form_with_invalid_field_values(self):
        response = self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_context_form(
            response, description=self.invalid_description, name=self.invalid_name
        )

    def test_context_form_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_form(response, description=None, name=None)

    # ==========================================================

    def post_with_invalid_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["description"] = self.invalid_description
        data["name"] = self.invalid_name
        return self.post(url, data, *args, **kwargs)


class AdEntryCreateViewPostTest(
    AdEntryCreateViewTestMixin, AdEntryCreateOrUpdateViewPostTestMixin, TestCase
):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_field_values(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post_with_field_values(expected_status=HTTPStatus.FOUND)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    # --------------------------------------
    # Ad entry model

    def test_entry_with_field_values(self):
        self.post_with_field_values(expected_status=HTTPStatus.FOUND)
        entry = self.ad.entries.get(language=self.language)
        self._test_entry(entry, description=self.description, name=self.name)

    def test_entry_with_invalid_field_values(self):
        self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self.assertFalse(self.ad.entries.filter(language=self.language).exists())

    def test_entry_without_field_values(self):
        self.post(expected_status=HTTPStatus.OK)
        self.assertFalse(self.ad.entries.filter(language=self.language).exists())

    # ==========================================================
    # Redirections

    def get_success_field_values(self):
        return {"description": self.description, "name": self.name}

    # ==========================================================

    def post_with_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data.update({"description": self.description, "name": self.name})
        self.post(url, data, *args, **kwargs)


class AdEntryUpdateViewPostTest(
    AdEntryUpdateViewTestMixin, AdEntryCreateOrUpdateViewPostTestMixin, TestCase
):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad entry model

    def test_entry_with_new_field_values(self):
        self.post_with_new_field_values(expected_status=HTTPStatus.FOUND)
        self._test_entry(description=self.new_description, name=self.new_name)

    def test_entry_with_invalid_field_values(self):
        self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_entry(description=self.old_description, name=self.old_name)

    def test_entry_without_field_values(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_entry(description=self.old_description, name=self.old_name)

    def _test_entry(self, **expected_field_values):
        self.entry.refresh_from_db(fields=["description", "name"])
        super()._test_entry(self.entry, **expected_field_values)

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_new_field_values(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post_with_new_field_values(expected_status=HTTPStatus.FOUND)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    # ==========================================================
    # Redirections

    def get_success_field_values(self):
        return {"description": self.new_description, "name": self.new_name}

    # ==========================================================

    def post_with_new_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data.update({"description": self.new_description, "name": self.new_name})
        self.post(url, data, *args, **kwargs)

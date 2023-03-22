from importlib import import_module
from unittest.mock import patch

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import get_language, get_language_info

from ads.models import Ad, AdEntry, AdImage
from categories.models import Category
from common.tests import (
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
)
from common.tests.utils.composite_languages_setting_test_mixin import (
    CompositeLanguagesSettingTestMixin,
)

###############################################################################
# Integration tests


# ==========================================================
# Validation


class AdCategoryValidationUltimateTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.non_ultimate_category_name = None
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category_factory = cls.create_category_factory()
        cls.ultimate_category = category_factory.create(ultimate=True)
        if cls.non_ultimate_category_name is None:
            cls.non_ultimate_category_name = (
                cls.create_category_name_factory().get_unique()
            )
        cls.non_ultimate_category = category_factory.create(
            name=cls.non_ultimate_category_name, ultimate=False
        )

    def setUp(self):
        super().setUp()
        self.ad = Ad()

    def test_with_ultimate_category(self):
        self.ad.category = self.ultimate_category
        self.full_clean_category()

    def test_with_non_ultimate_category(self):
        self.ad.category = self.non_ultimate_category
        with self.assertRaises(ValidationError) as error_catcher:
            self.full_clean_category()
        actual_object_errors = error_catcher.exception.message_dict
        self.assertEqual(len(actual_object_errors), 1)
        (actual_error,) = actual_object_errors["category"]
        expected_params = {"category": self.non_ultimate_category.full_name}
        expected_error = Ad._CATEGORY_NON_ULTIMATE_ERROR % expected_params
        self.assertEqual(actual_error, expected_error)

    def test_with_non_ultimate_category_message_uses_category_full_name(self):
        self.ad.category = self.non_ultimate_category
        mock = "test full category name"
        with (
            patch.object(Category, "full_name", mock),
            self.assertRaises(ValidationError) as error_catcher,
        ):
            self.full_clean_category()
        (error,) = error_catcher.exception.message_dict["category"]
        self.assertIn(mock, error)

    def test_error_code(self):
        form_meta = type("Meta", (), {"model": Ad, "fields": ["category"]})
        form_class = type("TestAdCategoryForm", (forms.ModelForm,), {"Meta": form_meta})
        form = form_class({"category": self.non_ultimate_category})
        self.assertTrue(form.has_error("category", "non_ultimate"))

    def full_clean_category(self):
        self.ad.full_clean(exclude=self.FIELDS_OTHER_THAN_CATEGORY)

    FIELDS_OTHER_THAN_CATEGORY = tuple(
        {field.name for field in Ad._meta.get_fields()} - {"category"}
    )


###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Category


class AdCategoryNonUltimateErrorTest(SaleAdsTestMixin, SimpleTestCase):
    def test_formatting(self):
        category_name = "test category full name"
        self.create_category_name_factory().check(category_name)
        actual = Ad._CATEGORY_NON_ULTIMATE_ERROR % {"category": category_name}
        expected = (
            'Ads can be added only to ultimate categories. "test category full name" '
            "isn't an ultimate category."
        )
        self.assertEqual(actual, expected)


# ==========================================================
# Canonicial URL


class AdGetAbsoluteURLTest(SaleAdsTestMixin, TestCase):
    def test(self):
        ad = self.create_ad_factory().create()
        result = ad.get_absolute_url()
        self.assertURLEqual(result, reverse("ads_detail", kwargs={"pk": ad.pk}))


# ==========================================================
# Template data methods


class AdOrderedImagesTest(SaleAdsTestMixin, TestCase):
    def test(self):
        ad = self.create_ad_factory().create()
        image_factory = self.create_ad_image_factory(ad=ad)
        image_3, image_4, image_1, image_2 = AdImage.objects.bulk_create(
            image_factory.create(number=number, save=False) for number in [3, 4, 1, 2]
        )
        self.assertEqual(
            list(ad.ordered_images()), [image_1, image_2, image_3, image_4]
        )


# ==========================================================
# Admin


class AdStrTest(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    TestCase,
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.entry_name_factory = cls.create_ad_entry_name_factory()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ad = cls.create_ad_factory().create()
        cls.entry_factory = cls.create_ad_entry_factory(ad=cls.ad)

    def test_with_single_entry(self):
        language = self.create_ad_entry_language_factory().get_choice()
        name = self.entry_name_factory.get_unique()
        self.entry_factory.create(language=language, name=name)
        actual = str(self.ad)
        local_language_name = get_language_info(language)["name_local"]
        expected = f"{self.ad.pk} ({local_language_name}: {name})"
        self.assertEqual(actual, expected)

    def test_with_multiple_entries(self):
        languages = settings.LANGUAGE_PREFERENCE_ORDER[:2]
        names = [self.entry_name_factory.get_unique() for language in languages]
        primary_language_name, secondary_language_name = names
        AdEntry.objects.bulk_create(
            self.entry_factory.create(language=language, name=name, save=False)
            for language, name in zip(languages, names)
        )
        actual = str(self.ad)
        primary_language_local_name, secondary_language_local_name = [
            get_language_info(language)["name_local"] for language in languages
        ]
        expected = (
            f"{self.ad.pk} "
            f"({primary_language_local_name}: {primary_language_name}; "
            f"{secondary_language_local_name}: {secondary_language_name})"
        )
        self.assertEqual(actual, expected)

    def test_without_entries(self):
        self.assertEqual(str(self.ad), f"{self.ad.pk} ()")


# ==========================================================
# Utilities


class AdGetEntryTest(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    TestCase,
):
    required_language_count = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.primary_language = settings.LANGUAGE_PREFERENCE_ORDER[0]
        cls.secondary_language = settings.LANGUAGE_PREFERENCE_ORDER[1]
        cls.other_language = settings.LANGUAGE_PREFERENCE_ORDER[2]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ad = cls.create_ad_factory().create()
        cls.entry_factory = cls.create_ad_entry_factory(ad=cls.ad)

    # ==========================================================
    # In available language

    # --------------------------------------
    # With single available language

    def test_in_primary_language_with_only_primary_available(self):
        self._test_in_only_available_language(self.primary_language)

    def test_in_secondary_language_with_only_secondary_available(self):
        self._test_in_only_available_language(self.secondary_language)

    def _test_in_only_available_language(self, language):
        self._test_with_available_languages(
            available_languages=[language],
            requested_language=language,
            expected_language=language,
        )

    # --------------------------------------
    # with multiple availble languages

    def test_in_primary_language_with_primary_and_secondary_available(self):
        self._test_in_primary_or_secondary_language_with_them_available(
            self.primary_language
        )

    def test_in_secondary_language_with_primary_and_secondary_available(self):
        self._test_in_primary_or_secondary_language_with_them_available(
            self.secondary_language
        )

    def _test_in_primary_or_secondary_language_with_them_available(self, language):
        self._test_with_available_languages(
            available_languages=[self.primary_language, self.secondary_language],
            requested_language=language,
            expected_language=language,
        )

    # ==========================================================
    # In unavailable language

    # --------------------------------------
    # With single available language

    def test_in_primary_language_with_only_secondary_available(self):
        self._test_with_available_languages(
            available_languages=[self.secondary_language],
            requested_language=self.primary_language,
            expected_language=self.secondary_language,
        )

    def test_in_secondary_language_with_only_primary_available(self):
        self._test_with_available_languages(
            available_languages=[self.primary_language],
            requested_language=self.secondary_language,
            expected_language=self.primary_language,
        )

    # --------------------------------------
    # With multiple available languages

    def test_in_unavailable_language_with_multiple_available(self):
        self._test_with_available_languages(
            available_languages=[self.primary_language, self.secondary_language],
            requested_language=self.other_language,
            expected_language=self.primary_language,
        )

    # --------------------------------------
    # With no available languages

    def test_in_unavailable_language_with_no_available(self):
        with self.assertRaisesMessage(AdEntry.DoesNotExist, str(Ad._NO_ENTRIES_ERROR)):
            self.ad.get_entry(settings.LANGUAGE_CODE)

    # ==========================================================

    def _test_with_available_languages(
        self, *, available_languages, requested_language, expected_language
    ):
        entries = AdEntry.objects.bulk_create(
            self.entry_factory.create(language=language, save=False)
            for language in available_languages
        )
        actual = self.ad.get_entry(requested_language)
        (expected,) = filter(lambda entry: entry.language == expected_language, entries)
        self.assertEqual(actual, expected)


class AdGetEntryInCurrentLanguageTest(
    ConsistentLanguagePreferenceOrderSettingTestMixin,
    SaleAdsTestMixin,
    CompositeLanguagesSettingTestMixin,
    TestCase,
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ad = cls.create_ad_factory().create()

    def test(self):
        entry = self.create_ad_entry_factory(ad=self.ad).create()
        self.assertEqual(self.ad.get_entry_in_current_language(), entry)

    def test_uses_django_utils_translation_get_language_and_get_entry(self):
        module = import_module(Ad.get_entry_in_current_language.__module__)
        self.assertIs(module.get_language, get_language)
        with (
            patch.object(module, "get_language", autospec=True) as get_language_mock,
            patch.object(self.ad, "get_entry", autospec=True) as get_entry_mock,
        ):
            result = self.ad.get_entry_in_current_language()
        get_language_mock.assert_called_once_with()
        get_entry_mock.assert_called_once_with(get_language_mock.return_value)
        self.assertEqual(result, get_entry_mock.return_value)

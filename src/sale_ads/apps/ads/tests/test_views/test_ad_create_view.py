from collections import Counter
from http import HTTPStatus
from types import MappingProxyType

from django.conf import settings
from django.test import TestCase

from ads.forms import AdImageCreateFormSet
from ads.models import Ad, AdEntry, AdImage
from ads.views import _AdCreateView
from categories.models import Category
from common.tests import SaleAdsTestMixin
from common.tests.utils.http_request_query_comparison import HTTPRequestQueryTestMixin
from common.tests.utils.image_test_mixin import ImageTestMixin
from common.tests.utils.temp_media_root_test_mixin import TempMediaRootTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdCreateViewTextMixin(
    SaleAdsTestMixin, HTTPRequestQueryTestMixin, TempMediaRootTestMixin, ViewTestMixin
):
    url_pattern_name = "ads_create"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        description_factory = cls.create_ad_entry_description_factory()
        language_factory = cls.create_ad_entry_language_factory()
        name_factory = cls.create_ad_entry_name_factory()
        price_factory = cls.create_ad_price_factory()
        cls.description = description_factory.get_unique()
        cls.language = language_factory.get_choice()
        cls.name = name_factory.get_unique()
        cls.price = price_factory.get_unique()
        create_category_pk_factory = getattr(
            cls, f"create_category_{Category._meta.pk.name}_factory"
        )
        cls.invalid_category_pk = create_category_pk_factory().get_invalid()
        cls.invalid_description = description_factory.get_invalid()
        cls.invalid_language = language_factory.get_invalid()
        cls.invalid_name = name_factory.get_invalid()
        cls.invalid_price = price_factory.get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = cls.create_user_factory().create()
        cls.confirm_email(cls.author)
        category_factory = cls.create_category_factory()
        cls.category, unused_category = Category.objects.bulk_create(
            category_factory.create(ultimate=True, save=False) for i in range(2)
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.author)

    def _test_context_ad_form(self, response, *, category, price):
        form = response.context["ad_form"]
        self.assertHTTPRequestParameterEqual(form["category"].value(), category)
        self.assertHTTPRequestParameterEqual(form["price"].value(), price)

    def _test_context_entry_form(self, response, *, description, language, name):
        form = response.context["entry_form"]
        self.assertEqual(form["description"].value(), description)
        self.assertEqual(form["language"].value(), language)
        self.assertEqual(form["name"].value(), name)

    def _test_context_image_formset(self, response):
        formset = response.context["image_formset"]
        self._test_image_formset(formset, [None] * AdImageCreateFormSet.extra)

    def _test_image_formset(self, formset, expected_images):
        self.assertEqual(len(expected_images), AdImageCreateFormSet.extra)
        for form, expected_image in zip(formset, expected_images):
            if isinstance(expected_image, str):
                self.assertAlmostEquals(form["image"].value().name, expected_image)
            else:
                self.assertIs(expected_image, None)
                self.assertIs(form["image"].value(), None)


class AdCreateViewGeneralTest(AdCreateViewTextMixin, TestCase):
    # ==========================================================
    # User permissions

    def test_with_verified_email_required_setting_true_and_anonymous_user(self):
        self.client.logout()
        url = self.get_url()
        response = self.get(url, expected_status=HTTPStatus.FOUND)
        self._test_redirects_to_login(response, url)

    def test_with_verified_email_required_setting_true_and_unverified_email(self):
        self.author.emailaddress_set.update(verified=False)
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "account/verified_email_required.html")

    def test_with_verified_email_required_setting_false_and_anonymous_user(self):
        with self.settings(ADS_VERIFIED_EMAIL_REQUIRED_FOR_CREATION=False):
            self.client.logout()
            url = self.get_url()
            response = self.get(url, expected_status=HTTPStatus.FOUND)
            self._test_redirects_to_login(response, url)

    def test_with_verified_email_required_setting_false_and_unverified_email(self):
        with self.settings(ADS_VERIFIED_EMAIL_REQUIRED_FOR_CREATION=False):
            self.author.emailaddress_set.update(verified=False)
            response = self.get(expected_status=HTTPStatus.OK)
            self.assertTemplateUsed(response, "ads/create.html")

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "ads/create.html")


class AdCreateViewGetTest(AdCreateViewTextMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Context

    # --------------------------------------
    # Ad form

    def test_context_ad_form(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(response, category=None, price=None)

    # --------------------------------------
    # Entry form

    def test_context_entry_form(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_entry_form(
            response, description=None, language=settings.LANGUAGE_CODE, name=None
        )

    # --------------------------------------
    # Image formset

    def test_context_image_formset(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_image_formset(response)


class AdCreateViewPostTest(AdCreateViewTextMixin, ImageTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad model

    def test_ad_with_field_values(self):
        data = {"category": self.category.pk, "price": self.price}
        self.post(
            data=data, default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        ad = Ad.objects.get()
        self.assertEqual(ad.author_id, self.author.pk)
        self.assertEqual(ad.category_id, self.category.pk)
        self.assertEqual(ad.price, self.price)

    def test_ad_with_invalid_field_values(self):
        data = {"category": self.invalid_category_pk, "price": self.invalid_price}
        self.post(data=data, default_for_required=True, expected_status=HTTPStatus.OK)
        self.assertFalse(Ad.objects.exists())

    def test_ad_without_field_values(self):
        self.post(
            default_for_required=True,
            no_default=["category", "price"],
            expected_status=HTTPStatus.OK,
        )
        self.assertFalse(Ad.objects.exists())

    # --------------------------------------
    # Ad entry model

    def test_entry_with_field_values(self):
        data = {
            "description": self.description,
            "language": self.language,
            "name": self.name,
        }
        self.post(
            data=data, default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        entry = AdEntry.objects.get()
        (ad_pk,) = Ad.objects.values_list("pk", flat=True)
        self.assertEqual(entry.ad_id, ad_pk)
        self.assertEqual(entry.description, self.description)
        self.assertEqual(entry.language, self.language)
        self.assertEqual(entry.name, self.name)

    def test_entry_with_invalid_field_values(self):
        data = {
            "description": self.invalid_description,
            "language": self.invalid_language,
            "name": self.invalid_name,
        }
        self.post(data=data, default_for_required=True, expected_status=HTTPStatus.OK)
        self.assertFalse(AdEntry.objects.exists())

    def test_entry_without_field_values(self):
        self.post(
            default_for_required=True,
            no_default=["description", "language", "name"],
            expected_status=HTTPStatus.OK,
        )
        self.assertFalse(AdEntry.objects.exists())

    # --------------------------------------
    # Ad image model

    def test_images_with_maximum_images(self):
        test_images = [self.get_test_image() for i in range(AdImageCreateFormSet.extra)]
        data = {
            self.get_image_field(form_index): test_image.open()
            for form_index, test_image in enumerate(test_images)
        }
        self.post(
            data=data, default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        images = list(AdImage.objects.all())
        self.assertEqual(len(images), AdImageCreateFormSet.extra)
        # ad
        (ad_pk,) = Ad.objects.values_list("pk", flat=True)
        for image in images:
            self.assertEqual(image.ad_id, ad_pk)
        # image
        images_in_creation_order = sorted(images, key=lambda image: image.number)
        for image, test_image in zip(images_in_creation_order, test_images):
            self.assertEqual(image.image.read(), test_image.data)
        # number
        actual_numbers = [image.number for image in images]
        expected_numbers = range(1, AdImageCreateFormSet.extra + 1)
        self.assertDictEqual(Counter(actual_numbers), Counter(expected_numbers))

    def test_images_with_single_image(self):
        test_image = self.get_test_image()
        data = {self.get_image_field(0): test_image.open()}
        self.post(
            data=data, default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        image = AdImage.objects.get()
        (ad_pk,) = Ad.objects.values_list("pk", flat=True)
        self.assertEqual(image.ad_id, ad_pk)
        self.assertEqual(image.image.read(), test_image.data)
        self.assertEqual(image.number, 1)

    def test_images_with_invalid_images(self):
        data = {
            self.get_image_field(form_index): self.get_invalid_test_image().open()
            for form_index in range(AdImageCreateFormSet.extra)
        }
        self.post(data=data, default_for_required=True, expected_status=HTTPStatus.OK)
        self.assertFalse(AdImage.objects.exists())

    def test_images_without_images(self):
        self.post(default_for_required=True, expected_status=HTTPStatus.FOUND)
        self.assertFalse(AdImage.objects.exists())

    def test_images_with_valid_and_invalid_images(self):
        data = {
            self.get_image_field(0): self.get_invalid_test_image().open(),
            self.get_image_field(1): self.get_test_image().open(),
        }
        self.post(data=data, default_for_required=True, expected_status=HTTPStatus.OK)
        self.assertFalse(AdImage.objects.exists())

    # Numbers with skipped forms

    def test_image_numbers_with_skipped_forms(self):
        data = {self.get_image_field(1): self.get_test_image().open()}
        self.post(
            data=data, default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        image = AdImage.objects.get()
        self.assertEqual(image.number, 1)

    # ==========================================================
    # Redirections

    def test_redirects_to_canonicial_ad_url_on_success(self):
        response = self.post(
            default_for_required=True, expected_status=HTTPStatus.FOUND
        )
        ad = Ad.objects.get()
        self.assertRedirects(response, ad.get_absolute_url())

    # ==========================================================
    # Context

    # --------------------------------------
    # Ad form

    def test_context_ad_form_with_field_values(self):
        data = {"category": self.category.pk, "price": self.price}
        response = self.post(data=data, fail=True, expected_status=HTTPStatus.OK)
        self._test_context_ad_form(
            response, category=self.category.pk, price=self.price
        )

    def test_context_ad_form_with_invalid_field_values(self):
        data = {"category": self.invalid_category_pk, "price": self.invalid_price}
        response = self.post(data=data, expected_status=HTTPStatus.OK)
        self._test_context_ad_form(
            response, category=self.invalid_category_pk, price=self.invalid_price
        )

    def test_context_ad_form_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_ad_form(response, category=None, price=None)

    # --------------------------------------
    # Entry form

    def test_context_entry_form_with_field_values(self):
        data = {
            "description": self.description,
            "language": self.language,
            "name": self.name,
        }
        response = self.post(data=data, fail=True, expected_status=HTTPStatus.OK)
        self._test_context_entry_form(
            response,
            description=self.description,
            language=self.language,
            name=self.name,
        )

    def test_context_entry_form_with_invalid_field_values(self):
        data = {
            "description": self.invalid_description,
            "language": self.invalid_language,
            "name": self.invalid_name,
        }
        response = self.post(data=data, expected_status=HTTPStatus.OK)
        self._test_context_entry_form(
            response,
            description=self.invalid_description,
            language=self.invalid_language,
            name=self.invalid_name,
        )

    def test_context_entry_form_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_entry_form(
            response, description=None, language=None, name=None
        )

    # --------------------------------------
    # Image formset

    def test_context_image_formset_with_maximum_images(self):
        data = {
            self.get_image_field(form_index): self.get_invalid_test_image().open()
            for form_index in range(AdImageCreateFormSet.extra)
        }
        response = self.post(data=data, fail=True, expected_status=HTTPStatus.OK)
        self._test_context_image_formset(response)

    def test_context_image_formset_with_single_image(self):
        data = {self.get_image_field(0): self.get_invalid_test_image().open()}
        response = self.post(data=data, fail=True, expected_status=HTTPStatus.OK)
        self._test_context_image_formset(response)

    def test_context_image_formset_with_invalid_images(self):
        data = {
            self.get_image_field(form_index): self.get_invalid_test_image().open()
            for form_index in range(AdImageCreateFormSet.extra)
        }
        response = self.post(data=data, expected_status=HTTPStatus.OK)
        self._test_context_image_formset(response)

    def test_context_image_formset_without_images(self):
        response = self.post(
            fail=True, no_default_images=True, expected_status=HTTPStatus.OK
        )
        self._test_context_image_formset(response)

    def test_context_image_formset_with_valid_and_invalid_images(self):
        data = {
            self.get_image_field(1): self.get_invalid_test_image().open(),
            self.get_image_field(0): self.get_test_image().open(),
        }
        response = self.post(data=data, expected_status=HTTPStatus.OK)
        self._test_context_image_formset(response)

    # "Invalid images" error

    def test_context_image_formset_invalid_images_error_with_invalid_image(self):
        test_image = self.get_invalid_test_image()
        data = {self.get_image_field(0): test_image.open()}
        response = self.post(data=data, expected_status=HTTPStatus.OK)
        expected_params = {"count": 1, "names": f'"{test_image.name}"'}
        expected = AdImageCreateFormSet._INVALID_IMAGES_ERROR % expected_params
        self._test_context_image_formset_invalid_images_error(response, expected)

    def test_context_image_formset_invalid_images_error_with_valid_image(self):
        data = {self.get_image_field(0): self.get_test_image().open()}
        response = self.post(
            data=data, fail=True, no_default_images=True, expected_status=HTTPStatus.OK
        )
        self._test_context_image_formset_invalid_images_error(response, None)

    def test_context_image_formset_invalid_images_error_without_images(self):
        response = self.post(
            fail=True, no_default_images=True, expected_status=HTTPStatus.OK
        )
        self._test_context_image_formset_invalid_images_error(response, None)

    def _test_context_image_formset_invalid_images_error(self, response, expected):
        formset = response.context["image_formset"]
        if expected:
            self.assertEqual(formset.non_form_errors(), [expected])
        else:
            self.assertEqual(len(formset.non_form_errors()), 0)
        for form in formset:
            self.assertEqual(form.errors, {})

    # ==========================================================

    def get_image_field(self, form_index):
        return f"{_AdCreateView._IMAGE_FORMSET_PREFIX}-{form_index}-image"

    def post(
        self,
        url=None,
        data=None,
        *args,
        default_for_required=False,
        fail=False,
        no_default=(),
        no_default_images=False,
        **kwargs,
    ):
        if data is None:
            data = {}
        data |= self.IMAGE_FORMSET_MANAGEMENT_DATA
        if default_for_required:
            if "category" not in no_default:
                data.setdefault("category", self.category.pk)
            if "description" not in no_default:
                data.setdefault("description", self.description)
            if "language" not in no_default:
                data.setdefault("language", self.language)
            if "name" not in no_default:
                data.setdefault("name", self.name)
            if "price" not in no_default:
                data.setdefault("price", self.price)
        if fail:
            if "category" not in no_default and "category" not in data:
                data["category"] = self.invalid_category_pk
            elif "description" not in no_default and "description" not in data:
                data["description"] = self.invalid_description
            elif "language" not in no_default and "language" not in data:
                data["language"] = self.invalid_language
            elif "name" not in no_default and "name" not in data:
                data["name"] = self.invalid_name
            elif "price" not in no_default and "price" not in data:
                data["price"] = self.invalid_price
            else:
                failed = False
                if not no_default_images:
                    for form_index in range(AdImageCreateFormSet.extra):
                        field = self.get_image_field(form_index)
                        if field not in data:
                            data[field] = self.get_invalid_test_image().open()
                            failed = True
                            break
                if not failed:
                    raise AssertionError("not failed")
        return super().post(url, data, *args, **kwargs)

    IMAGE_FORMSET_MANAGEMENT_DATA = MappingProxyType(
        {
            f"{_AdCreateView._IMAGE_FORMSET_PREFIX}-TOTAL_FORMS": (
                AdImageCreateFormSet.extra
            ),
            f"{_AdCreateView._IMAGE_FORMSET_PREFIX}-INITIAL_FORMS": 0,
        }
    )

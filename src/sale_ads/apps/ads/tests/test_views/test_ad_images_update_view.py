from collections import Counter
from http import HTTPStatus

from django.test import TestCase

from ads.forms import _BaseAdImageFormSet
from ads.models import Ad, AdImage
from ads.views import _AdImagesUpdateView
from common.tests import SaleAdsTestMixin
from common.tests.utils.image_test_mixin import ImageTestMixin
from common.tests.utils.temp_media_root_test_mixin import TempMediaRootTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdImagesUpdateViewTestMixin(
    SaleAdsTestMixin, ImageTestMixin, TempMediaRootTestMixin, ViewTestMixin
):
    url_pattern_name = "ads_update_images"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = cls.create_user_factory().create()
        cls.ad = cls.create_ad_factory(author=cls.author).create()
        cls.image_factory = cls.create_ad_image_factory(ad=cls.ad)

    def setUp(self):
        super().setUp()
        self.prepare_client()

    def create_initial_images(self, count):
        return AdImage.objects.bulk_create(
            self.image_factory.create(number=number, save=False)
            for number in range(1, count + 1)
        )

    def prepare_client(self, client=None):
        if client is None:
            client = self.client
        client.force_login(self.author)

    def get_url_pattern_kwargs(self):
        return {"pk": self.ad.pk}

    def _test_image_numbers(self, expected):
        images = AdImage.objects.in_bulk(expected.keys())
        for pk, expected_number in expected.items():
            self.assertEqual(images[pk].number, expected_number)

    def _test_context_addition_formset(self, response, form_count):
        formset = response.context["addition_formset"]
        self._test_addition_formset(formset, [None] * form_count, form_count)

    def _test_addition_formset(self, formset, expected_images, expected_form_count):
        self.assertEqual(len(formset), expected_form_count)
        self.assertEqual(len(expected_images), expected_form_count)
        for form, expected_image in zip(formset, expected_images):
            if isinstance(expected_image, str):
                self.assertEqual(form["image"].value().name, expected_image)
            else:
                self.assertIs(expected_image, None)
                self.assertIs(form["image"].value(), None)


class AdImagesUpdateViewGeneralTest(AdImagesUpdateViewTestMixin, TestCase):
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
        self.assertTemplateUsed(response, "ads/update_images.html")

    # ==========================================================
    # Context

    # --------------------------------------
    # Addition formset

    def test_context_addition_formset_without_images(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_addition_formset(response, Ad.MAX_IMAGES)

    def test_context_addition_formset_with_single_image(self):
        self.create_initial_images(1)
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_addition_formset(response, Ad.MAX_IMAGES - 1)

    def test_context_addition_formset_with_maximum_images(self):
        self.create_initial_images(Ad.MAX_IMAGES)
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_addition_formset(response, 0)


class AdImagesUpdateViewGetTest(AdImagesUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)


class AdImagesUpdateViewPostAddTest(AdImagesUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad image model

    def test_images_with_maximum_images(self):
        test_images = [self.get_test_image() for i in range(Ad.MAX_IMAGES)]
        data = {
            self.get_field(form_index): test_image.open()
            for form_index, test_image in enumerate(test_images)
        }
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        images = list(AdImage.objects.all())
        self.assertEqual(len(images), Ad.MAX_IMAGES)
        # ad
        for image in images:
            self.assertEqual(image.ad_id, self.ad.pk)
        # image
        images_in_creation_order = sorted(images, key=lambda image: image.number)
        for image, test_image in zip(images_in_creation_order, test_images):
            self.assertEqual(image.image.read(), test_image.data)
        # number
        actual_numbers = [image.number for image in images]
        expected_numbers = range(1, Ad.MAX_IMAGES + 1)
        self.assertDictEqual(Counter(actual_numbers), Counter(expected_numbers))

    def test_images_with_single_image(self):
        test_image = self.get_test_image()
        data = {self.get_field(0): test_image.open()}
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        image = AdImage.objects.get()
        self.assertEqual(image.ad_id, self.ad.pk)
        self.assertEqual(image.image.read(), test_image.data)
        self.assertEqual(image.number, 1)

    def test_images_with_invalid_images(self):
        data = {
            self.get_field(form_index): self.get_invalid_test_image().open()
            for form_index in range(Ad.MAX_IMAGES)
        }
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.assertFalse(AdImage.objects.exists())

    def test_images_without_images(self):
        self.post(form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.assertFalse(AdImage.objects.exists())

    def test_images_with_initial_images(self):
        (initial_image,) = self.create_initial_images(1)
        test_image = self.get_test_image()
        data = {self.get_field(0): test_image.open()}
        self.post(
            data=data, form_count=Ad.MAX_IMAGES - 1, expected_status=HTTPStatus.OK
        )
        (added_image,) = set(AdImage.objects.all()) - {initial_image}
        self.assertEqual(added_image.ad_id, self.ad.pk)
        self.assertEqual(added_image.image.read(), test_image.data)
        self.assertEqual(added_image.number, 2)

    def test_images_with_valid_and_invalid_images(self):
        invalid_test_image = self.get_invalid_test_image()
        valid_test_image = self.get_test_image()
        data = {
            self.get_field(0): invalid_test_image.open(),
            self.get_field(1): valid_test_image.open(),
        }
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        image = AdImage.objects.get()
        self.assertEqual(image.ad_id, self.ad.pk)
        self.assertEqual(image.image.read(), valid_test_image.data)
        self.assertEqual(image.number, 1)

    def test_images_with_skipped_forms(self):
        test_image = self.get_test_image()
        data = {self.get_field(1): test_image.open()}
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        image = AdImage.objects.get()
        self.assertEqual(image.ad_id, self.ad.pk)
        self.assertEqual(image.image.read(), test_image.data)
        self.assertEqual(image.number, 1)

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_images(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        data = {self.get_field(0): self.get_test_image().open()}
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    def test_ad_verified_with_invalid_images(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        data = {self.get_field(0): self.get_invalid_test_image().open()}
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    def test_ad_verified_without_images(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post(form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    def test_ad_verified_with_valid_and_invalid_images(self):
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        data = {
            self.get_field(0): self.get_invalid_test_image().open(),
            self.get_field(1): self.get_test_image().open(),
        }
        self.post(data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    # ==========================================================
    # Context

    # --------------------------------------
    # Addition formset

    def test_context_formset_with_images(self):
        data = {self.get_field(0): self.get_test_image().open()}
        response = self.post(
            data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK
        )
        self._test_context_addition_formset(response, Ad.MAX_IMAGES - 1)

    def test_context_formset_with_invalid_images(self):
        data = {self.get_field(0): self.get_invalid_test_image().open()}
        response = self.post(
            data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK
        )
        self._test_context_addition_formset(response, Ad.MAX_IMAGES)

    def test_context_formset_without_images(self):
        response = self.post(form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self._test_context_addition_formset(response, Ad.MAX_IMAGES)

    def test_context_formset_with_valid_and_invalid_images(self):
        data = {
            self.get_field(0): self.get_invalid_test_image().open(),
            self.get_field(1): self.get_test_image().open(),
        }
        response = self.post(
            data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK
        )
        self._test_context_addition_formset(response, Ad.MAX_IMAGES - 1)

    # "Invalid images" error

    def test_context_formset_invalid_images_error_with_invalid_image(self):
        test_image = self.get_invalid_test_image()
        data = {self.get_field(0): test_image.open()}
        response = self.post(
            data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK
        )
        expected_params = {"count": 1, "names": f'"{test_image.name}"'}
        expected = _BaseAdImageFormSet._INVALID_IMAGES_ERROR % expected_params
        self._test_context_formset_invalid_images_error(response, expected)

    def test_context_formset_invalid_images_error_with_valid_image(self):
        data = {self.get_field(0): self.get_test_image().open()}
        response = self.post(
            data=data, form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK
        )
        self._test_context_formset_invalid_images_error(response, None)

    def test_context_formset_invalid_images_error_without_images(self):
        response = self.post(form_count=Ad.MAX_IMAGES, expected_status=HTTPStatus.OK)
        self._test_context_formset_invalid_images_error(response, None)

    def _test_context_formset_invalid_images_error(self, response, expected):
        formset = response.context["addition_formset"]
        if expected:
            self.assertEqual(formset.non_form_errors(), [expected])
        else:
            self.assertEqual(len(formset.non_form_errors()), 0)
        for form in formset:
            self.assertEqual(form.errors, {})

    # ==========================================================

    def get_field(self, form_index):
        return f"{_AdImagesUpdateView._ADDITION_FORMSET_PREFIX}-{form_index}-image"

    def post(self, url=None, data=None, *args, form_count, **kwargs):
        if data is None:
            data = {}
        data["action"] = "add"
        data.update(
            {
                f"{_AdImagesUpdateView._ADDITION_FORMSET_PREFIX}-TOTAL_FORMS": (
                    form_count
                ),
                f"{_AdImagesUpdateView._ADDITION_FORMSET_PREFIX}-INITIAL_FORMS": 0,
            }
        )
        return super().post(url, data, *args, **kwargs)


class AdImagesUpdateViewPostDeleteTest(AdImagesUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad image model

    def test_images_with_number(self):
        top, deleted, bottom = self.create_initial_images(3)
        expected_numbers = {top.pk: top.number, bottom.pk: deleted.number}
        self.post(data={"number": deleted.number}, expected_status=HTTPStatus.OK)
        self._test_images(deleted.pk, expected_numbers)

    def test_images_with_number_out_of_range(self):
        (image,) = self.create_initial_images(1)
        number = 2
        self.create_ad_image_number_factory().check(number)
        self.assertNotEqual(number, image.number)
        expected_numbers = {image.pk: image.number}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(
            data={"number": number},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self._test_images(None, expected_numbers)

    def test_images_with_non_number(self):
        (image,) = self.create_initial_images(1)
        expected_numbers = {image.pk: image.number}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(
            data={"number": "non-number test value"},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self._test_images(None, expected_numbers)

    def test_images_without_number(self):
        (image,) = self.create_initial_images(1)
        expected_numbers = {image.pk: image.number}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(client=client, expected_status=HTTPStatus.INTERNAL_SERVER_ERROR)
        self._test_images(None, expected_numbers)

    def _test_images(self, deleted_image_pk, expected_numbers):
        if deleted_image_pk is not None:
            self.assertFalse(AdImage.objects.filter(pk=deleted_image_pk).exists())
        self._test_image_numbers(expected_numbers)

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_valid_number(self):
        (image,) = self.create_initial_images(1)
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post(data={"number": image.number}, expected_status=HTTPStatus.OK)
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    def test_ad_verified_with_invalid_number(self):
        self.create_initial_images(1)
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(
            data={"number": "invalid number"},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    # ==========================================================
    # Context

    # --------------------------------------
    # Addition formset

    def test_context_addition_formset(self):
        remaining, deleted = self.create_initial_images(2)
        response = self.post(
            data={"number": deleted.number}, expected_status=HTTPStatus.OK
        )
        self._test_context_addition_formset(response, Ad.MAX_IMAGES - 1)

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "delete"
        return super().post(url, data, *args, **kwargs)


class AdImagesUpdateViewPostReorderTest(AdImagesUpdateViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad image model

    def test_images_lift(self):
        top, lowered, lifted, bottom = self.create_initial_images(4)
        expected_numbers = {
            lifted.pk: lowered.number,
            lowered.pk: lifted.number,
            top.pk: top.number,
            bottom.pk: bottom.number,
        }
        self.post_lift(data={"number": lifted.number}, expected_status=HTTPStatus.OK)
        self._test_image_numbers(expected_numbers)

    def test_images_lift_top(self):
        images = self.create_initial_images(2)
        top, other = images
        expected_numbers = {image.pk: image.number for image in images}
        self.post_lift(data={"number": top.number}, expected_status=HTTPStatus.OK)
        self._test_image_numbers(expected_numbers)

    def test_images_lower(self):
        top, lowered, lifted, bottom = self.create_initial_images(4)
        expected_numbers = {
            lowered.pk: lifted.number,
            lifted.pk: lowered.number,
            top.pk: top.number,
            bottom.pk: bottom.number,
        }
        self.post_lower(data={"number": lowered.number}, expected_status=HTTPStatus.OK)
        self._test_image_numbers(expected_numbers)

    def test_images_lower_bottom(self):
        images = self.create_initial_images(2)
        other, bottom = images
        expected_numbers = {image.pk: image.number for image in images}
        self.post_lower(data={"number": bottom.number}, expected_status=HTTPStatus.OK)
        self._test_image_numbers(expected_numbers)

    def test_images_with_number_out_of_range(self):
        images = self.create_initial_images(2)
        number = 3
        self.create_ad_image_number_factory().check(number)
        self.assertNotIn(number, [image.number for image in images])
        expected_numbers = {image.pk: image.number for image in images}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post_lift(
            data={"number": number},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self._test_image_numbers(expected_numbers)

    def test_images_without_number(self):
        images = self.create_initial_images(2)
        expected_numbers = {image.pk: image.number for image in images}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post_lift(client=client, expected_status=HTTPStatus.INTERNAL_SERVER_ERROR)
        self._test_image_numbers(expected_numbers)

    def test_images_with_invalid_direction(self):
        images = self.create_initial_images(2)
        other, bottom = images
        expected_numbers = {image.pk: image.number for image in images}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(
            data={"direction": "invalid direction", "number": bottom.number},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self._test_image_numbers(expected_numbers)

    def test_images_without_direction(self):
        images = self.create_initial_images(2)
        other, bottom = images
        expected_numbers = {image.pk: image.number for image in images}
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post(
            data={"number": bottom.number},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self._test_image_numbers(expected_numbers)

    # --------------------------------------
    # Ad model

    # "verified" field

    def test_ad_verified_with_valid_data(self):
        lowered_image, lifted_image = self.create_initial_images(2)
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post_lift(
            data={"number": lifted_image.number}, expected_status=HTTPStatus.OK
        )
        self.ad.refresh_from_db(fields=["verified"])
        self.assertFalse(self.ad.verified)

    def test_ad_verified_with_invalid_data(self):
        images = self.create_initial_images(2)
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        invalid_number = max(image.number for image in images) + 1
        client = self.client_class(raise_request_exception=False)
        self.prepare_client(client)
        self.post_lift(
            data={"number": invalid_number},
            client=client,
            expected_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    def test_ad_verified_with_top_lifting(self):
        lifted_image, other_image = self.create_initial_images(2)
        self.ad.verified = True
        self.ad.save(update_fields=["verified"])
        self.post_lift(
            data={"number": lifted_image.number}, expected_status=HTTPStatus.OK
        )
        self.ad.refresh_from_db(fields=["verified"])
        self.assertTrue(self.ad.verified)

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "reorder"
        return super().post(url, data, *args, **kwargs)

    def post_lift(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["direction"] = "up"
        return self.post(url, data, *args, **kwargs)

    def post_lower(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["direction"] = "down"
        return self.post(url, data, *args, **kwargs)

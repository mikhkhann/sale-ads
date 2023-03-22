from http import HTTPStatus

from django.test import TestCase

from common.tests import SaleAdsTestMixin
from common.tests.utils.image_test_mixin import ImageTestMixin
from common.tests.utils.temp_media_root_test_mixin import TempMediaRootTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class UpdateUserPhotoViewTestMixin(
    SaleAdsTestMixin, ImageTestMixin, TempMediaRootTestMixin, ViewTestMixin
):
    url_pattern_name = "accounts_update_photo"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_image = cls.get_test_image()
        cls.invalid_test_image = cls.get_invalid_test_image()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user_factory().create()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def _test_context_form(self, response, expected_photo):
        form = response.context["form"]
        if isinstance(expected_photo, str):
            self.assertEqual(form["photo"].value().name, expected_photo)
        elif expected_photo is False:
            self.assertIs(form["photo"].value(), False)
        else:
            self.assertIs(expected_photo, None)
            self.assertFalse(form["photo"].value().name)


class UpdateUserPhotoViewGeneralTest(UpdateUserPhotoViewTestMixin, TestCase):
    # ==========================================================
    # User permissions

    def test_redirects_to_login_if_user_is_anonymous(self):
        self.client.logout()
        url = self.get_url()
        response = self.get(url, expected_status=HTTPStatus.FOUND)
        self._test_redirects_to_login(response, url)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "accounts/settings_photo.html")


class UpdateUserPhotoViewGetTest(UpdateUserPhotoViewTestMixin, TestCase):
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
        self._test_context_form(response, None)


class UpdateUserPhotoViewPostTest(UpdateUserPhotoViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # User model

    def test_user_with_photo(self):
        self.post_with_photo(expected_status=HTTPStatus.OK)
        self._test_user(self.test_image.data)

    def test_user_with_invalid_photo(self):
        self.post_with_invalid_photo(expected_status=HTTPStatus.OK)
        self._test_user(None)

    def test_user_without_photo(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_user(None)

    def test_user_with_removal_flag(self):
        self.set_initial_photo()
        self.post_with_removal_flag(expected_status=HTTPStatus.OK)
        self._test_user(None)

    # ==========================================================
    # Context

    # --------------------------------------
    # Form

    def test_context_form_with_photo(self):
        response = self.post_with_photo(expected_status=HTTPStatus.OK)
        self._test_context_form(response, self.test_image.name)

    def test_context_form_with_invalid_photo(self):
        response = self.post_with_invalid_photo(expected_status=HTTPStatus.OK)
        self._test_context_form(response, self.invalid_test_image.name)

    def test_context_form_without_photo(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_form(response, None)

    def test_context_form_with_removal_flag(self):
        self.set_initial_photo()
        response = self.post_with_removal_flag(expected_status=HTTPStatus.OK)
        self._test_context_form(response, False)

    # --------------------------------------
    # User

    def test_context_user_with_photo(self):
        response = self.post_with_photo(expected_status=HTTPStatus.OK)
        self._test_context_user(response, self.test_image.data)

    def test_context_user_with_invalid_photo(self):
        response = self.post_with_invalid_photo(expected_status=HTTPStatus.OK)
        self._test_context_user(response, None)

    def test_context_user_without_photo(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_user(response, None)

    def test_context_user_with_removal_flag(self):
        self.set_initial_photo()
        response = self.post_with_removal_flag(expected_status=HTTPStatus.OK)
        self._test_context_user(response, None)

    def _test_context_user(self, response, expected_photo):
        user = response.context["user"]
        self._test_user(expected_photo, user)

    # ==========================================================

    def set_initial_photo(self):
        self.user.photo.save(self.test_image.name, self.test_image.open())
        self.user.save(update_fields=["photo"])

    def post_with_photo(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["photo"] = self.test_image.open()
        return self.post(url, data, *args, **kwargs)

    def post_with_invalid_photo(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["photo"] = self.invalid_test_image.open()
        return self.post(url, data, *args, **kwargs)

    def post_with_removal_flag(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["photo-clear"] = "on"
        return self.post(url, data, *args, **kwargs)

    def _test_user(self, expected_photo, user=None):
        if user is None:
            user = self.user
            user.refresh_from_db(fields=["photo"])
        if isinstance(expected_photo, bytes):
            self.assertEqual(user.photo.read(), expected_photo)
        else:
            self.assertIs(expected_photo, None)
            self.assertFalse(user.photo.name)

from http import HTTPStatus
from importlib import import_module
from unittest.mock import patch

from allauth.account.utils import send_email_confirmation
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.views import _UserSettingsView
from common.tests import SaleAdsTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin

UNSPECIFIED = object()


class UserSettingsViewTestMixin(SaleAdsTestMixin, ViewTestMixin):
    url_pattern_name = "accounts_settings"

    @classmethod
    def setUpClass(cls):
        cls.old_email = None
        cls.old_name = None
        cls.old_username = None
        super().setUpClass()
        email_factory = cls.create_user_email_factory()
        name_factory = cls.create_user_name_factory()
        username_factory = cls.create_user_username_factory()
        cls.new_email = email_factory.get_unique()
        cls.new_name = name_factory.get_unique()
        cls.new_username = username_factory.get_unique()
        cls.invalid_email = email_factory.get_invalid()
        cls.invalid_name = name_factory.get_invalid()
        cls.invalid_username = username_factory.get_invalid()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if cls.old_email is None:
            cls.old_email = cls.create_user_email_factory().get_unique()
        if cls.old_name is None:
            cls.old_name = cls.create_user_name_factory().get_unique()
        if cls.old_username is None:
            cls.old_username = cls.create_user_username_factory().get_unique()
        user_factory = cls.create_user_factory()
        cls.user = user_factory.create(
            email=cls.old_email, name=cls.old_name, username=cls.old_username
        )
        cls.user.emailaddress_set.create(email=cls.user.email)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def _test_email_object_existence_and_email_field_value(
        self, expected_email_field_value
    ):
        email_object = self.user.emailaddress_set.get()
        self.assertEqual(email_object.email, expected_email_field_value)

    def _test_email_object_verification(self, expected):
        email_object = self.user.emailaddress_set.get()
        self.assertIs(bool(email_object.verified), bool(expected))

    def _test_email_verification_sending(self, make_request, email):
        module = import_module(_UserSettingsView.__module__)
        self.assertIs(module.send_email_confirmation, send_email_confirmation)
        outbox_len_before = None
        outbox_len_after = None

        def send_email_confirmation_mock_wrapped(*args, **kwargs):
            nonlocal outbox_len_before, outbox_len_after
            outbox_len_before = len(mail.outbox)
            result = send_email_confirmation(*args, **kwargs)
            outbox_len_after = len(mail.outbox)
            return result

        with patch.object(
            module,
            "send_email_confirmation",
            autospec=True,
            side_effect=send_email_confirmation_mock_wrapped,
        ) as send_email_confirmation_mock:
            make_request()
        if email is not None:
            send_email_confirmation_mock.assert_called_once()
            actual_args, actual_kwargs = send_email_confirmation_mock.call_args
            actual_request, actual_user = actual_args
            self.assertEqual(actual_user, self.user)
            self.assertEqual(actual_kwargs, {"email": email})
            self.assertEqual(outbox_len_after - outbox_len_before, 1)
        else:
            send_email_confirmation_mock.assert_not_called()

    def _test_context_email_verified(self, response, expected):
        self.assertEqual(bool(response.context["email_verified"]), bool(expected))

    def _test_context_form(
        self, response, *, email=UNSPECIFIED, name=UNSPECIFIED, username=UNSPECIFIED
    ):
        form = response.context["form"]
        if email is not UNSPECIFIED:
            self.assertEqual(form["email"].value(), email)
        if name is not UNSPECIFIED:
            self.assertEqual(form["name"].value(), name)
        if username is not UNSPECIFIED:
            self.assertEqual(form["username"].value(), username)

    def _test_context_verification_sent(self, response, expected):
        self.assertIs(bool(response.context["verification_sent"]), bool(expected))

    def _test_context_user(self, response, **expected_field_values):
        self._test_user(response.context["user"], **expected_field_values)

    def _test_user(
        self, user=None, *, email=UNSPECIFIED, name=UNSPECIFIED, username=UNSPECIFIED
    ):
        if user is None:
            user = self.user
            fields = []
            if email is not UNSPECIFIED:
                fields.append("email")
            if name is not UNSPECIFIED:
                fields.append("name")
            if username is not UNSPECIFIED:
                fields.append("username")
            user.refresh_from_db(fields=fields)
        if email is not UNSPECIFIED:
            self.assertEqual(user.email, email)
        if name is not UNSPECIFIED:
            self.assertEqual(user.name, name)
        if username is not UNSPECIFIED:
            self.assertEqual(user.username, username)


class UserSettingsViewGeneralTest(UserSettingsViewTestMixin, TestCase):
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
        self.assertTemplateUsed(response, "accounts/settings.html")

    # ==========================================================
    # Context

    # --------------------------------------
    # Domain

    def test_context_domain(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertEqual(response.context["domain"], settings.DOMAIN)

    # --------------------------------------
    # Maximum username length

    def test_context_max_username_length(self):
        response = self.get(expected_status=HTTPStatus.OK)
        actual = response.context["max_username_length"]
        expected = get_user_model()._meta.get_field("username").max_length
        self.assertEqual(actual, expected)

    # --------------------------------------
    # Minimum username length

    def test_context_min_username_length(self):
        response = self.get(expected_status=HTTPStatus.OK)
        actual = response.context["min_username_length"]
        expected = get_user_model().MIN_USERNAME_LENGTH
        self.assertEqual(actual, expected)

    # --------------------------------------
    # User ad list URL path

    def test_context_user_ad_list_url_path(self):
        response = self.get(expected_status=HTTPStatus.OK)
        actual = response.context["user_ad_list_url_path"]
        expected = reverse("ads_user_list", kwargs={"username": self.user.username})
        expected = expected.rstrip("/")
        self.assertEqual(actual, expected)


class UserSettingsViewGetTest(UserSettingsViewTestMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Context

    # --------------------------------------
    # Email is verified

    def test_context_email_verified_with_unverified(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_verified(self):
        self.confirm_email(self.user)
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, True)

    # --------------------------------------
    # Form

    def test_context_form(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self._test_context_form(
            response,
            email=self.old_email,
            name=self.old_name,
            username=self.old_username,
        )


@override_settings(ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN=0)
class UserSettingsViewPostSaveTest(UserSettingsViewTestMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # User model

    def test_user_with_new_field_values(self):
        self.post_with_new_field_values(expected_status=HTTPStatus.OK)
        self._test_user(
            email=self.new_email, name=self.new_name, username=self.new_username
        )

    def test_user_with_invalid_field_values(self):
        self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_user(
            email=self.old_email, name=self.old_name, username=self.old_username
        )

    def test_user_without_field_values(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_user(
            email=self.old_email, name=self.old_name, username=self.old_username
        )

    def test_user_with_valid_and_invalid_field_values(self):
        self.post(
            data={"email": self.invalid_email, "name": self.new_name},
            old_as_default_for_required=True,
            expected_status=HTTPStatus.OK,
        )
        self._test_user(email=self.old_email, name=self.new_name)

    # --------------------------------------
    # Email model

    # Existence and email field value

    def test_email_object_existence_and_email_field_value_with_new_email(self):
        self.post(data={"email": self.new_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.new_email)

    def test_email_object_existence_and_email_field_value_with_invalid_email(self):
        self.post(data={"email": self.invalid_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.old_email)

    def test_email_object_existence_and_email_field_value_without_email(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.old_email)

    # Verification

    def test_email_object_verification_with_new_email_and_unverified_old_email(self):
        self.post(data={"email": self.new_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post(data={"email": self.new_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_invalid_email_and_unverified_old_email(
        self,
    ):
        self.post(data={"email": self.invalid_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post(data={"email": self.invalid_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    def test_email_object_verification_without_email_and_unverified_old_email(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    def test_email_object_verification_with_same_unverified_email(self):
        self.post(data={"email": self.old_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_same_verified_email(self):
        self.confirm_email(self.user)
        self.post(data={"email": self.old_email}, expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    # ==========================================================
    # Email verification sending

    def test_email_verification_sending_with_new_email_and_unverified_old_email(self):
        make_request = lambda: self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, self.new_email)

    def test_email_verification_sending_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, self.new_email)

    def test_email_verification_sending_with_invalid_email_and_unverified_old_email(
        self,
    ):
        make_request = lambda: self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_without_email_and_unverified_old_email(self):
        make_request = lambda: self.post(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_with_same_unverified_email(self):
        make_request = lambda: self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_with_same_verified_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    # ==========================================================
    # Context

    # --------------------------------------
    # Email is verified

    def test_context_email_verified_with_new_email_and_unverified_old_email(self):
        response = self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_new_email_and_verified_old_email(self):
        response = self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_invalid_email_and_unverified_old_email(self):
        response = self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, True)

    def test_context_email_verified_without_email_and_unverified_old_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, True)

    def test_context_email_verified_with_same_unverified_email(self):
        response = self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_same_verified_email(self):
        self.confirm_email(self.user)
        response = self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_email_verified(response, True)

    # --------------------------------------
    # Form

    def test_context_form_with_new_field_values(self):
        response = self.post_with_new_field_values(expected_status=HTTPStatus.OK)
        self._test_context_form(
            response,
            email=self.new_email,
            name=self.new_name,
            username=self.new_username,
        )

    def test_context_form_with_invalid_field_values(self):
        response = self.post_with_invalid_field_values(expected_status=HTTPStatus.OK)
        self._test_context_form(
            response,
            email=self.invalid_email,
            name=self.invalid_name,
            username=self.invalid_username,
        )

    def test_context_form_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_form(response, email=None, name=None, username=None)

    # --------------------------------------
    # User

    def test_context_user_with_new_field_values(self):
        response = self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_user(response, email=self.new_email)

    def test_context_user_with_invalid_field_values(self):
        response = self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_user(response, email=self.old_email)

    def test_context_user_without_field_values(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_user(response, email=self.old_email)

    # --------------------------------------
    # Verification sending

    def test_context_verification_sent_with_new_email_and_unverified_old_email(self):
        response = self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, True)

    def test_context_verification_sent_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(
            data={"email": self.new_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, True)

    def test_context_verification_sent_with_invalid_email_and_unverified_old_email(
        self,
    ):
        response = self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(
            data={"email": self.invalid_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_without_email_and_unverified_old_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_with_same_unverified_email(self):
        response = self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_with_same_verified_email(self):
        self.confirm_email(self.user)
        response = self.post(
            data={"email": self.old_email}, expected_status=HTTPStatus.OK
        )
        self._test_context_verification_sent(response, False)

    # ==========================================================

    def post(
        self, url=None, data=None, *args, old_as_default_for_required=False, **kwargs
    ):
        if data is None:
            data = {}
        data["action"] = "save"
        if old_as_default_for_required:
            data.setdefault("email", self.old_email)
            data.setdefault("name", self.old_name)
            data.setdefault("username", self.old_username)
        return super().post(url, data, *args, **kwargs)

    def post_with_new_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["email"] = self.new_email
        data["name"] = self.new_name
        data["username"] = self.new_username
        return self.post(url, data, *args, **kwargs)

    def post_with_invalid_field_values(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["email"] = self.invalid_email
        data["name"] = self.invalid_name
        data["username"] = self.invalid_username
        return self.post(url, data, *args, **kwargs)


@override_settings(ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN=0)
class UserSettingsViewPostSendEmailVerificationTest(
    UserSettingsViewTestMixin, TestCase
):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # User model

    def test_user_with_new_email(self):
        self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_user(email=self.new_email)

    def test_user_with_invalid_email(self):
        self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_user(email=self.old_email)

    def test_user_without_email(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_user(email=self.old_email)

    # Values of fields other than email

    def test_user_other_fields_values_without_field_values(self):
        self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_user(name=self.old_name)

    def test_user_other_fields_values_with_new_field_values(self):
        self.post_with_new_email(
            data={"name": self.new_name}, expected_status=HTTPStatus.OK
        )
        self._test_user(name=self.old_name)

    def test_user_other_fields_values_with_invalid_field_values(self):
        self.post_with_new_email(
            data={"name": self.invalid_name}, expected_status=HTTPStatus.OK
        )
        self._test_user(name=self.old_name)

    # --------------------------------------
    # Email model

    # Existence and email field value

    def test_email_object_existence_and_email_field_value_with_new_email(self):
        self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.new_email)

    def test_email_object_existence_and_email_field_value_with_invalid_email(self):
        self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.old_email)

    def test_email_object_existence_and_email_field_value_without_email(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_existence_and_email_field_value(self.old_email)

    # Verification

    def test_email_object_verification_with_same_unverified_email(self):
        self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_same_verified_email(self):
        self.confirm_email(self.user)
        self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    def test_email_object_verification_with_new_email_and_unverified_old_email(self):
        self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_invalid_email_and_unverified_old_email(
        self,
    ):
        self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    def test_email_object_verification_without_email_and_unverified_old_email(self):
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(False)

    def test_email_object_verification_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        self.post(expected_status=HTTPStatus.OK)
        self._test_email_object_verification(True)

    # ==========================================================
    # Email verification sending

    def test_email_verification_sending_with_same_unverified_email(self):
        make_request = lambda: self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, self.old_email)

    def test_email_verification_sending_with_same_verified_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_with_new_email_and_unverified_old_email(self):
        make_request = lambda: self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, self.new_email)

    def test_email_verification_sending_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, self.new_email)

    def test_email_verification_sending_with_invalid_email_and_unverified_old_email(
        self,
    ):
        make_request = lambda: self.post_with_invalid_email(
            expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post_with_invalid_email(
            expected_status=HTTPStatus.OK
        )
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_without_email_and_unverified_old_email(self):
        make_request = lambda: self.post(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, None)

    def test_email_verification_sending_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        make_request = lambda: self.post(expected_status=HTTPStatus.OK)
        self._test_email_verification_sending(make_request, None)

    # ==========================================================
    # Context

    # --------------------------------------
    # Email is verified

    def test_context_email_verified_with_same_unverified_email(self):
        response = self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_same_verified_email(self):
        self.confirm_email(self.user)
        response = self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, True)

    def test_context_email_verified_with_new_email_and_unverified_old_email(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_invalid_email_and_unverified_old_email(self):
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, True)

    def test_context_email_verified_without_email_and_unverified_old_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, False)

    def test_context_email_verified_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_email_verified(response, True)

    # --------------------------------------
    # Form

    def test_context_form_with_new_email(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_form(response, email=self.new_email)

    def test_context_form_with_invalid_email(self):
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_form(response, email=self.invalid_email)

    def test_context_form_without_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_form(response, email=None)

    # Values of fields other than email

    def test_context_form_other_fields_values_without_field_values(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_form(response, name=self.old_name)

    def test_context_form_other_fields_values_with_new_field_values(self):
        response = self.post_with_new_email(
            data={"name": self.new_name}, expected_status=HTTPStatus.OK
        )
        self._test_context_form(response, name=self.old_name)

    def test_context_form_other_fields_values_with_invalid_field_values(self):
        response = self.post_with_new_email(
            data={"name": self.invalid_name}, expected_status=HTTPStatus.OK
        )
        self._test_context_form(response, name=self.old_name)

    # --------------------------------------
    # User

    def test_context_user_with_new_email(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_user(response, email=self.new_email)

    def test_context_user_with_invalid_email(self):
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_user(response, email=self.old_email)

    def test_context_user_without_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_user(response, email=self.old_email)

    # Values of fields other than email

    def test_context_user_other_fields_values_without_field_values(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_user(response, name=self.old_name)

    def test_context_user_other_fields_values_with_new_field_values(self):
        response = self.post_with_new_email(
            data={"name": self.new_name}, expected_status=HTTPStatus.OK
        )
        self._test_context_user(response, name=self.old_name)

    def test_context_user_other_fields_values_with_invalid_field_values(self):
        response = self.post_with_new_email(
            data={"name": self.invalid_name}, expected_status=HTTPStatus.OK
        )
        self._test_context_user(response, name=self.old_name)

    # --------------------------------------
    # Verification sending

    def test_context_verification_sent_with_same_unverified_email(self):
        response = self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, True)

    def test_context_verification_sent_with_same_verified_email(self):
        self.confirm_email(self.user)
        response = self.post_with_old_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_with_new_email_and_unverified_old_email(self):
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, True)

    def test_context_verification_sent_with_new_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post_with_new_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, True)

    def test_context_verification_sent_with_invalid_email_and_unverified_old_email(
        self,
    ):
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_with_invalid_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post_with_invalid_email(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_without_email_and_unverified_old_email(self):
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    def test_context_verification_sent_without_email_and_verified_old_email(self):
        self.confirm_email(self.user)
        response = self.post(expected_status=HTTPStatus.OK)
        self._test_context_verification_sent(response, False)

    # ==========================================================

    def post(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["action"] = "send_email_verification"
        return super().post(url, data, *args, **kwargs)

    def post_with_old_email(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["email"] = self.old_email
        return self.post(url, data, *args, **kwargs)

    def post_with_new_email(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["email"] = self.new_email
        return self.post(url, data, *args, **kwargs)

    def post_with_invalid_email(self, url=None, data=None, *args, **kwargs):
        if data is None:
            data = {}
        data["email"] = self.invalid_email
        return self.post(url, data, *args, **kwargs)

from collections import Counter
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from common.tests import SaleAdsTestMixin

###############################################################################
# Integration tests


# ==========================================================
# Validation


class UserUsernameValidationTestMixin:
    def full_clean_username(self, user):
        user.full_clean(exclude=self.FIELDS_OTHER_THAN_USERNAME)

    FIELDS_OTHER_THAN_USERNAME = tuple(
        {field.name for field in User._meta.get_fields()} - {"username"}
    )


class UserUsernameValidationAllowedCharactersTest(
    UserUsernameValidationTestMixin, SaleAdsTestMixin, TestCase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        invalid_char = "."
        assert invalid_char not in User._USERNAME_CHARACTERS
        cls.invalid_username = (
            cls.create_user_username_factory().get_unique() + invalid_char
        )

    def setUp(self):
        super().setUp()
        self.user = User()

    def test_with_valid_username(self):
        self.user.username = self.create_user_username_factory().get_unique()
        self.full_clean_username(self.user)

    def test_with_invalid_username(self):
        self.user.username = self.invalid_username
        with self.assertRaises(ValidationError) as error_catcher:
            self.full_clean_username(self.user)
        actual_object_errors = error_catcher.exception.message_dict
        self.assertEqual(len(actual_object_errors), 1)
        (actual_error,) = actual_object_errors["username"]
        expected_error = User._UNALLOWED_USERNAME_CHARACTERS_ERROR
        self.assertEqual(actual_error, expected_error)

    def test_with_all_allowed_characters(self):
        untested_chars = User._USERNAME_CHARACTERS
        max_length = User._meta.get_field("username").max_length
        while untested_chars:
            username = untested_chars[:max_length]
            untested_chars = untested_chars[max_length:]
            self.user.username = username
            self.full_clean_username(self.user)

    def test_error_code(self):
        form_meta = type("Meta", (), {"model": User, "fields": ["username"]})
        form_class = type("TestUsernameForm", (forms.ModelForm,), {"Meta": form_meta})
        form = form_class({"username": self.invalid_username})
        self.assertTrue(form.has_error("username", "unallowed_characters"))


class UserUsernameValidationNotForbiddenTest(
    UserUsernameValidationTestMixin, SaleAdsTestMixin, TestCase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.forbidden_username = next(iter(User._FORBIDDEN_USERNAMES))

    def setUp(self):
        super().setUp()
        self.user = User()

    def test_with_not_forbidden_username(self):
        self.user.username = self.create_user_username_factory().get_unique()
        self.full_clean_username(self.user)

    def test_with_forbidden_username(self):
        self.user.username = self.forbidden_username
        with self.assertRaises(ValidationError) as error_catcher:
            self.full_clean_username(self.user)
        actual_object_errors = error_catcher.exception.message_dict
        self.assertEqual(len(actual_object_errors), 1)
        (actual_error,) = actual_object_errors["username"]
        expected_params = {"username": self.forbidden_username}
        expected_error = User._FORBIDDEN_USERNAME_ERROR % expected_params
        self.assertEqual(actual_error, expected_error)

    def test_error_code(self):
        form_meta = type("Meta", (), {"model": User, "fields": ["username"]})
        form_class = type("TestUsernameForm", (forms.ModelForm,), {"Meta": form_meta})
        form = form_class({"username": self.forbidden_username})
        self.assertTrue(form.has_error("username", "forbidden"))


###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Photo


class UserPhotoUploadToTest(SimpleTestCase):
    def test(self):
        file_name = "test image.jpg"
        user = User()
        field = User._meta.get_field("photo")
        result = Path(field.upload_to(user, file_name))
        self.assertEqual(result.parent, User._PHOTO_DIR)
        UUID(result.stem)
        self.assertEqual(result.suffix, Path(file_name).suffix)


# --------------------------------------
# Username


class UserUsernameGenerationLengthTest(SimpleTestCase):
    def test_not_less_than_min_length(self):
        min_length = User.MIN_USERNAME_LENGTH
        self.assertGreaterEqual(User.USERNAME_GENERATION_LENGTH, min_length)

    def test_not_greater_than_max_length(self):
        max_length = User._meta.get_field("username").max_length
        self.assertLessEqual(User.USERNAME_GENERATION_LENGTH, max_length)


class UserUsernameGenerationCharactersTest(SimpleTestCase):
    def test_is_subset_of_username_characters(self):
        value = User.USERNAME_GENERATION_CHARACTERS
        username_characters = User._USERNAME_CHARACTERS
        self.assertLessEqual(set(value), set(username_characters))


class UserForbiddenUsernameErrorTest(SaleAdsTestMixin, TestCase):
    def test_formatting(self):
        username = "test_username"
        self.create_user_username_factory().check(username)
        actual = User._FORBIDDEN_USERNAME_ERROR % {"username": username}
        expected = '"test_username" is a forbidden username.'
        self.assertEqual(actual, expected)


class UserIsGeneratedUsernameValidTest(SaleAdsTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User()

    def test_with_valid_username(self):
        self.user.username = self.create_user_username_factory().get_unique()
        self.assertTrue(self.user.is_generated_username_valid())

    def test_with_invalid_username(self):
        self.user.username = self.create_user_username_factory().get_invalid()
        self.assertFalse(self.user.is_generated_username_valid())

    def test_without_full_clean_errors(self):
        with patch.object(self.user, "full_clean", autospec=True):
            result = self.user.is_generated_username_valid()
        self.assertTrue(result)

    def test_with_username_full_clean_errors(self):
        error = ValidationError({"username": "test field error"})
        with patch.object(self.user, "full_clean", autospec=True, side_effect=error):
            result = self.user.is_generated_username_valid()
        self.assertFalse(result)

    def test_with_non_field_full_clean_errors(self):
        error = ValidationError({NON_FIELD_ERRORS: "non-field test error"})
        with patch.object(self.user, "full_clean", autospec=True, side_effect=error):
            result = self.user.is_generated_username_valid()
        self.assertTrue(result)

    def test_uses_full_clean(self):
        with patch.object(self.user, "full_clean", autospec=True) as mock:
            self.user.is_generated_username_valid()
        mock.assert_called_once()
        actual_args, actual_kwargs = mock.call_args
        self.assertEqual(len(actual_args), 0)
        self.assertEqual(len(actual_kwargs), 1)
        actual_exclude = actual_kwargs["exclude"]
        fields = {field.name for field in User._meta.get_fields()}
        expected_exclude = fields - {"username"}
        self.assertDictEqual(Counter(actual_exclude), Counter(expected_exclude))


# ==========================================================
# Canonicial URL


class UserGetAbsolutURLTest(SaleAdsTestMixin, TestCase):
    def test(self):
        username = self.create_user_username_factory().get_unique()
        user = User(username=username)
        actual = user.get_absolute_url()
        expected = reverse("ads_user_list", kwargs={"username": username})
        self.assertURLEqual(actual, expected)


# ==========================================================
# Admin


class UserStrTest(SaleAdsTestMixin, TestCase):
    def test(self):
        name = self.create_user_name_factory().get_unique()
        username = self.create_user_username_factory().get_unique()
        user = User(name=name, username=username)
        self.assertEqual(str(user), f"{name} (@{username})")

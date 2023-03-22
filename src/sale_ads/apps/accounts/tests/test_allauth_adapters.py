from collections import Counter
from http import HTTPStatus
from importlib import import_module
from unittest.mock import Mock, patch

from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user, get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.allauth_adapters import AccountAdapter, SocialAccountAdapter
from common.tests import SaleAdsTestMixin
from unique_sequence_searchers import find_unique_string


class AccountAdapterTest(SaleAdsTestMixin, TestCase):
    def test_name_saving(self):
        name = self.create_user_name_factory().get_unique()
        self.post_signup(name=name, expected_status=HTTPStatus.FOUND)
        user = get_user(self.client)
        self.assertEqual(user.name, name)

    def test_username_generation(self):
        self.post_signup(expected_status=HTTPStatus.FOUND)
        user = get_user(self.client)
        self.assertTrue(user.is_generated_username_valid())

    def test_username_generation_uses_user_username_generation_constants(self):
        self.post_signup(expected_status=HTTPStatus.FOUND)
        user = get_user(self.client)
        user_model = get_user_model()
        self.assertEqual(len(user.username), user_model.USERNAME_GENERATION_LENGTH)
        self.assertLessEqual(
            set(user.username), set(user_model.USERNAME_GENERATION_CHARACTERS)
        )

    def test_username_generation_uses_find_unique_string(self):
        username = self.create_user_username_factory().get_unique()
        module = import_module(AccountAdapter.__module__)
        self.assertIs(module.find_unique_string, find_unique_string)
        with (
            patch.object(
                module, "find_unique_string", autospec=True, return_value=username
            ) as mock,
            patch.object(
                AccountAdapter, "_GeneratedUsernameChecker", autospec=True
            ) as generated_username_checker_mock,
        ):
            self.post_signup(expected_status=HTTPStatus.FOUND)
        user = get_user(self.client)
        mock.assert_called_once()
        actual_args, actual_kwargs = mock.call_args
        actual_items, actual_length, actual_existing = actual_args
        expected_items = get_user_model().USERNAME_GENERATION_CHARACTERS
        self.assertDictEqual(Counter(actual_items), Counter(expected_items))
        self.assertEqual(actual_length, get_user_model().USERNAME_GENERATION_LENGTH)
        self.assertEqual(len(actual_existing), 0)
        expected_kwargs = {"check": generated_username_checker_mock.return_value}
        self.assertEqual(actual_kwargs, expected_kwargs)
        self.assertEqual(user.username, mock.return_value)

    def test_username_generation_uses_generated_username_checker(self):
        instance_mock = Mock(side_effect=[False, True])
        with patch.object(
            AccountAdapter,
            "_GeneratedUsernameChecker",
            autospec=True,
            return_value=instance_mock,
        ) as class_mock:
            self.post_signup(expected_status=HTTPStatus.FOUND)
        user = get_user(self.client)
        class_mock.assert_called_once_with(user)
        self.assertEqual(instance_mock.call_count, 2)
        actual_args_list, actual_kwargs_list = zip(*instance_mock.call_args_list)
        (actual_username_1,), (actual_username_2,) = actual_args_list
        self.assertNotEqual(actual_username_1, actual_username_2)
        self.assertEqual(actual_username_2, user.username)
        for actual_kwargs in actual_kwargs_list:
            self.assertEqual(actual_kwargs, {})

    def post_signup(self, *, expected_status, **field_values):
        if "email" not in field_values:
            field_values["email"] = self.create_user_email_factory().get_unique()
        if "name" not in field_values:
            field_values["name"] = self.create_user_name_factory().get_unique()
        password = self.create_user_password_factory().get_unique()
        for i in range(1, 3):
            field_values[f"password{i}"] = password
        with self.settings(
            # make faster
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
        ):
            response = self.client.post(reverse("account_signup"), field_values)
        self.assertEqual(response.status_code, expected_status)


class AccountAdapterGeneratedUsernameCheckerTest(SaleAdsTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_model = get_user_model()
        cls.username_factory = cls.create_user_username_factory()

    def setUp(self):
        super().setUp()
        self.user = self.user_model()

    def test_with_valid_username(self):
        checker = AccountAdapter._GeneratedUsernameChecker(self.user)
        username = self.username_factory.get_unique()
        self.assertTrue(checker(username))

    def test_with_invalid_username(self):
        checker = AccountAdapter._GeneratedUsernameChecker(self.user)
        username = self.username_factory.get_invalid()
        self.assertFalse(checker(username))

    def test_sets_initial_username_after_test(self):
        initial_username = self.username_factory.get_unique()
        tested_username = self.username_factory.get_unique()
        self.user.username = initial_username
        checker = AccountAdapter._GeneratedUsernameChecker(self.user)
        checker(tested_username)
        self.assertEqual(self.user.username, initial_username)

    def test_uses_user_is_generated_username_valid(self):
        initial_username = self.username_factory.get_unique()
        tested_username = self.username_factory.get_unique()
        self.user.username = initial_username
        username_in_call = None
        mock_result = object()

        def side_effect():
            nonlocal username_in_call
            username_in_call = self.user.username
            return mock_result

        checker = AccountAdapter._GeneratedUsernameChecker(self.user)
        with patch.object(
            self.user,
            "is_generated_username_valid",
            autospec=True,
            side_effect=side_effect,
        ) as mock:
            result = checker(tested_username)
        mock.assert_called_once_with()
        self.assertEqual(username_in_call, tested_username)
        self.assertEqual(result, mock_result)


class SocialAccountAdapterPopulateUserTest(SaleAdsTestMixin, SimpleTestCase):
    def test_saves_first_name_as_name(self):
        first_name = self.create_user_name_factory().get_unique()
        user = get_user_model()()
        adapter = SocialAccountAdapter()
        request = RequestFactory().get("/test_url")
        sociallogin = SocialLogin(user)
        data = {"first_name": first_name}
        adapter.populate_user(request, sociallogin, data)
        self.assertEqual(user.name, first_name)

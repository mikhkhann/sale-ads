from http import HTTPStatus

from django.test import SimpleTestCase
from django.urls import reverse

from common.tests.utils.view_test_mixin import ViewTestMixin


class EmailViewTest(ViewTestMixin, SimpleTestCase):
    url_pattern_name = "account_email"

    def test_redirects_to_user_settings(self):
        response = self.get(expected_status=HTTPStatus.FOUND)
        self.assertRedirects(
            response, reverse("accounts_settings"), fetch_redirect_response=False
        )

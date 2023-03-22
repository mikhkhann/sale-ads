from http import HTTPStatus

from django.conf import settings
from django.test import SimpleTestCase

from common.tests.utils.view_test_mixin import ViewTestMixin


class EmailVerificationSentViewTest(ViewTestMixin, SimpleTestCase):
    url_pattern_name = "account_email_verification_sent"

    def test_redirects_to_home(self):
        response = self.get(expected_status=HTTPStatus.FOUND)
        self.assertRedirects(response, settings.HOME_URL, fetch_redirect_response=False)

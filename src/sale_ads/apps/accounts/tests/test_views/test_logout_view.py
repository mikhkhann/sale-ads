from http import HTTPStatus

from django.test import SimpleTestCase

from common.tests.utils.view_test_mixin import ViewTestMixin


class LogoutViewGetTest(ViewTestMixin, SimpleTestCase):
    url_pattern_name = "account_logout"

    # ==========================================================
    # Not allowed

    def test_not_allowed(self):
        self.get(expected_status=HTTPStatus.METHOD_NOT_ALLOWED)

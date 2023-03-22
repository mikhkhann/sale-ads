from http import HTTPStatus

from django.test import SimpleTestCase

from common.tests.utils.view_test_mixin import ViewTestMixin


class AboutViewTest(ViewTestMixin, SimpleTestCase):
    url_pattern_name = "pages_about"

    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "pages/about.html")

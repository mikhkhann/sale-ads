from django.conf import settings
from django.test import RequestFactory, SimpleTestCase

from common.context_processors import home_url


class HomeURLTest(SimpleTestCase):
    def test(self):
        request = RequestFactory().get("test_url")
        self.assertEqual(home_url(request), {"home_url": settings.HOME_URL})

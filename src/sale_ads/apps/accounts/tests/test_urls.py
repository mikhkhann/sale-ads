from django.test import SimpleTestCase
from django.urls import resolve, reverse

from accounts.views import logout


class Test(SimpleTestCase):
    def test_account_logout_overridden_with_custom_view(self):
        view = resolve(reverse("account_logout")).func
        self.assertIs(view, logout)

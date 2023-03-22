from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from ads.models import Ad
from common.tests import SaleAdsTestMixin
from common.tests.utils.view_test_mixin import ViewTestMixin


class AdDeleteViewTextMixin(SaleAdsTestMixin, ViewTestMixin):
    url_pattern_name = "ads_delete"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = cls.create_user_factory().create()
        cls.confirm_email(cls.author)
        cls.ad = cls.create_ad_factory(author=cls.author).create()
        cls.create_ad_entry_factory(ad=cls.ad).create()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.author)

    def get_url_pattern_kwargs(self):
        return {"pk": self.ad.pk}


class AdDeleteViewGeneralTest(AdDeleteViewTextMixin, TestCase):
    # ==========================================================
    # User permissions

    def test_redirects_to_login_if_user_is_anonymous(self):
        self.client.logout()
        url = self.get_url()
        response = self.get(url, expected_status=HTTPStatus.FOUND)
        self._test_redirects_to_login(response, url)

    def test_forbidden_if_user_is_authenticated_but_is_not_author(self):
        self.client.logout()
        other_user = self.create_user_factory().create()
        self.client.force_login(other_user)
        self.get(expected_status=HTTPStatus.FORBIDDEN)

    # ==========================================================
    # Template

    def test_template(self):
        response = self.get(expected_status=HTTPStatus.OK)
        self.assertTemplateUsed(response, "ads/delete.html")


class AdDeleteViewGetTest(AdDeleteViewTextMixin, TestCase):
    # ==========================================================
    # Availability

    def test_availability(self):
        self.get(expected_status=HTTPStatus.OK)


class AdDeleteViewPostTest(AdDeleteViewTextMixin, TestCase):
    # ==========================================================
    # Model objects

    # --------------------------------------
    # Ad model

    def test_ad_deleted(self):
        self.post(expected_status=HTTPStatus.FOUND)
        self.assertFalse(Ad.objects.all())

    # ==========================================================
    # Redirections

    def test_redirects_to_ad_user_list_on_success(self):
        response = self.post(expected_status=HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            reverse("ads_user_list", kwargs={"username": self.author.username}),
        )

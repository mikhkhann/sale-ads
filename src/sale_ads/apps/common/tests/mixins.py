from urllib.parse import urlencode, urlunsplit

from allauth.account.views import LoginView
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings

from accounts.models import User
from ads.models import Ad, AdEntry, AdImage
from categories.models import Category
from common.tests.utils.model_field_test_value_factory import (
    ModelEmailFieldTestValueFactory,
    ModelFieldTestValueFactory,
    ModelPasswordFieldTestValueFactory,
    ModelStringFieldTestValueFactory,
)
from common.tests.utils.test_model_object_factory import TestModelObjectFactory


class SaleAdsTestMixin:
    # ==========================================================
    # Model field values

    # --------------------------------------
    # Accounts / user

    # Email

    class UserEmailFactory(ModelEmailFieldTestValueFactory):
        model = User
        field = "email"

    @classmethod
    def create_user_email_factory(cls, *args, **kwargs):
        return cls.UserEmailFactory(*args, **kwargs)

    # Language

    class UserLanguageFactory(ModelFieldTestValueFactory):
        model = User
        field = "language"

        def get_choices(self):
            return list(zip(*settings.LANGUAGES))[0]

    @classmethod
    def create_user_language_factory(cls, *args, **kwargs):
        return cls.UserLanguageFactory(*args, **kwargs)

    # Name

    class UserNameFactory(ModelStringFieldTestValueFactory):
        model = User
        field = "name"

    @classmethod
    def create_user_name_factory(cls, *args, **kwargs):
        return cls.UserNameFactory(*args, **kwargs)

    # Password

    class UserPasswordFactory(ModelPasswordFieldTestValueFactory):
        model = User
        field = "password"

    @classmethod
    def create_user_password_factory(cls, *args, **kwargs):
        return cls.UserPasswordFactory(*args, **kwargs)

    # Username

    class UserUsernameFactory(ModelStringFieldTestValueFactory):
        model = User
        field = "username"
        main_part = "test_username"

    @classmethod
    def create_user_username_factory(cls, *args, **kwargs):
        return cls.UserUsernameFactory(*args, **kwargs)

    # --------------------------------------
    # Ads / ad

    # Price

    class AdPriceFactory(ModelFieldTestValueFactory):
        model = Ad
        field = "price"
        default_invalid_value = 0

        def get_unique_value(self):
            return self.get_unique_value_number()

    @classmethod
    def create_ad_price_factory(cls, *args, **kwargs):
        return cls.AdPriceFactory(*args, **kwargs)

    # --------------------------------------
    # Ads / ad entry

    # Description

    class AdEntryDescriptionFactory(ModelStringFieldTestValueFactory):
        model = AdEntry
        field = "description"
        default_invalid_value = ""

    @classmethod
    def create_ad_entry_description_factory(cls, *args, **kwargs):
        return cls.AdEntryDescriptionFactory(*args, **kwargs)

    # Language

    class AdEntryLanguageFactory(ModelFieldTestValueFactory):
        model = AdEntry
        field = "language"
        default_invalid_value = "invalid test ad entry language"

        def get_choices(self, number=1):
            return list(zip(*settings.LANGUAGES))[0]

    @classmethod
    def create_ad_entry_language_factory(cls, *args, **kwargs):
        return cls.AdEntryLanguageFactory(*args, **kwargs)

    # Name

    class AdEntryNameFactory(ModelStringFieldTestValueFactory):
        model = AdEntry
        field = "name"

    @classmethod
    def create_ad_entry_name_factory(cls, *args, **kwargs):
        return cls.AdEntryNameFactory(*args, **kwargs)

    # --------------------------------------
    # Ads / ad image

    # Image

    class AdImageImageFactory(ModelStringFieldTestValueFactory):
        model = AdImage
        field = "image"

    @classmethod
    def create_ad_image_image_factory(cls, *args, **kwargs):
        return cls.AdImageImageFactory(*args, **kwargs)

    # Number

    class AdImageNumberFactory(ModelFieldTestValueFactory):
        model = AdImage
        field = "number"

    @classmethod
    def create_ad_image_number_factory(cls, *args, **kwargs):
        return cls.AdImageNumberFactory(*args, **kwargs)

    # --------------------------------------
    # Categories / category

    # ID

    class CategoryIDFactory(ModelFieldTestValueFactory):
        model = Category
        field = "id"
        default_invalid_value = "invalid test category id"

    @classmethod
    def create_category_id_factory(cls, *args, **kwargs):
        return cls.CategoryIDFactory(*args, **kwargs)

    # Name

    class CategoryNameFactory(ModelStringFieldTestValueFactory):
        model = Category
        field = "name"

    @classmethod
    def create_category_name_factory(cls, *args, **kwargs):
        return cls.CategoryNameFactory(*args, **kwargs)

    # ==========================================================
    # Model object creation

    # --------------------------------------
    # Accounts

    # User

    class UserFactory(TestModelObjectFactory):
        model = User

        def __init__(self, *args, test_class, **kwargs):
            super().__init__(*args, **kwargs)
            self.test_class = test_class

        @property
        def default_email(self):
            return self.test_class.create_user_email_factory().get_unique()

        @property
        def default_username(self):
            return self.test_class.create_user_username_factory().get_unique()

    @classmethod
    def create_user_factory(cls, *args, **kwargs):
        return cls.UserFactory(*args, test_class=cls, **kwargs)

    # --------------------------------------
    # Ads

    # Ad

    class AdFactory(TestModelObjectFactory):
        model = Ad

        def __init__(self, *args, test_class, **kwargs):
            self.test_class = test_class
            super().__init__(*args, **kwargs)

        def create_default_author(self):
            return self.test_class.create_user_factory().create()

        def create_default_category(self):
            return self.test_class.create_category_factory().create()

        @property
        def default_price(self):
            return self.test_class.create_ad_price_factory().get_unique()

    @classmethod
    def create_ad_factory(cls, *args, **kwargs):
        return cls.AdFactory(*args, test_class=cls, **kwargs)

    # Ad entry

    class AdEntryFactory(TestModelObjectFactory):
        model = AdEntry

        def __init__(self, *args, test_class, **kwargs):
            self.test_class = test_class
            super().__init__(*args, **kwargs)

        def create_default_ad(self):
            return self.test_class.create_ad_factory().create()

        @property
        def default_language(self):
            return self.test_class.create_ad_entry_language_factory().get_choice()

    @classmethod
    def create_ad_entry_factory(cls, *args, **kwargs):
        return cls.AdEntryFactory(*args, test_class=cls, **kwargs)

    # Ad image

    class AdImageFactory(TestModelObjectFactory):
        model = AdImage

        def __init__(self, *args, test_class, **kwargs):
            self.test_class = test_class
            super().__init__(*args, **kwargs)

        def create_default_ad(self):
            return self.test_class.create_ad_factory().create()

        @property
        def default_image(self):
            return self.test_class.create_ad_image_image_factory().get_unique()

    @classmethod
    def create_ad_image_factory(cls, *args, **kwargs):
        return cls.AdImageFactory(*args, test_class=cls, **kwargs)

    # --------------------------------------
    # Categories

    # Category

    class CategoryFactory(TestModelObjectFactory):
        model = Category

        def __init__(self, *args, test_class, **kwargs):
            super().__init__(*args, **kwargs)
            self.test_class = test_class

        @property
        def default_name(self):
            return self.test_class.create_category_name_factory().get_unique()

    @classmethod
    def create_category_factory(cls, *args, **kwargs):
        return cls.CategoryFactory(*args, test_class=cls, **kwargs)

    # ==========================================================
    # Miscellaneous

    @classmethod
    def confirm_email(cls, user):
        user.emailaddress_set.update_or_create(
            email=user.email, defaults={"verified": True}
        )

    def _test_redirects_to_login(self, response, original_url, *args, **kwargs):
        expected_query = {LoginView.redirect_field_name: original_url}
        expected_query_string = urlencode(expected_query)
        expected_url = urlunsplit(
            ["", "", resolve_url(settings.LOGIN_URL), expected_query_string, ""]
        )
        self.assertRedirects(response, expected_url, *args, **kwargs)


class ConsistentLanguagePreferenceOrderSettingTestMixin:
    @classmethod
    def setUpClass(cls):
        cls.consistent_language_preference_order_setting_is_set_up = False
        super().setUpClass()
        if not cls.consistent_language_preference_order_setting_is_set_up:
            cls.set_up_consistent_language_preference_order_setting()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set_up_consistent_language_preference_order_setting()
        cls.consistent_language_preference_order_setting_is_set_up = True

    @classmethod
    def set_up_consistent_language_preference_order_setting(cls):
        setting = list(zip(*settings.LANGUAGES))[0]
        cls.enterClassContext(override_settings(LANGUAGE_PREFERENCE_ORDER=setting))

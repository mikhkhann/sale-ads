from django.conf import global_settings
from django.urls import reverse_lazy
from environs import Env

from sale_ads.paths import LOCALE_DIR, STATIC_DIR, TEMPLATE_DIR

_env = Env()
_env.read_env()


# Main

HOME_URL = reverse_lazy("ads_list")


# Application definition

INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "anymail",
    "storages",
    "accounts",
    "ads",
    "categories",
    "demonstration",
    "frontend",
    "languages",
    "pages",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "languages.middleware.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "sale_ads.conf.urls"
WSGI_APPLICATION = "sale_ads.conf.wsgi.application"


# Authentication & authorization

ACCOUNT_ADAPTER = "accounts.allauth_adapters.AccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_FORMS = {"signup": "accounts.forms.SignupForm"}
ACCOUNT_USERNAME_REQUIRED = False
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    *global_settings.AUTHENTICATION_BACKENDS,
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = HOME_URL
LOGOUT_REDIRECT_URL = HOME_URL
SOCIALACCOUNT_ADAPTER = "accounts.allauth_adapters.SocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "AUTH_PARAMS": {"access_type": "online"},
        "SCOPE": ["email", "profile"],
    }
}


# Data

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Email

USE_MAILGUN = _env.bool("DJANGO_USE_MAILGUN", False)
if USE_MAILGUN:
    ANYMAIL = {
        "MAILGUN_API_KEY": _env("DJANGO_MAILGUN_API_KEY"),
        "MAILGUN_SENDER_DOMAIN": _env("DJANGO_MAILGUN_SENDER_DOMAIN"),
    }
    DEFAULT_FROM_EMAIL = _env("DJANGO_DEFAULT_FROM_EMAIL")
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"


# Internationalization

LANGUAGE_CODE = "en"
LANGUAGE_PREFERENCE_ORDER = ["en", "ru"]
LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
]
LOCALE_PATHS = [LOCALE_DIR]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static & media

STATICFILES_DIRS = [STATIC_DIR]
USE_S3 = _env.bool("DJANGO_USE_S3", False)
if USE_S3:
    AWS_ACCESS_KEY_ID = _env("DJANGO_AWS_ACCESS_KEY_ID")
    AWS_DEFAULT_ACL = None
    AWS_SECRET_ACCESS_KEY = _env("DJANGO_AWS_SECRET_ACCESS_KEY")
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_STORAGE_BUCKET_NAME = _env("DJANGO_AWS_STORAGE_BUCKET_NAME")
    DEFAULT_FILE_STORAGE = "common.storage_backends.MediaStorage"
    MEDIA_LOCATION = "media"
    STATIC_LOCATION = "static"
    STATICFILES_STORAGE = "common.storage_backends.StaticStorage"
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/"


# Frontend

TEMPLATES = [
    {
        "APP_DIRS": True,
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.home_url",
            ],
        },
    }
]


# Miscellaneous

ADS_VERIFIED_EMAIL_REQUIRED_FOR_CREATION = _env.bool(
    "DJANGO_ADS_VERIFIED_EMAIL_REQUIRED_FOR_CREATION", True
)

SITE_ID = 1

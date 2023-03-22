from sale_ads.conf.settings.base import *  # NOQA
from sale_ads.conf.settings.base import USE_MAILGUN, USE_S3
from sale_ads.paths import MEDIA_DIR

# Main

DEBUG = True


# Data

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": 5432,
    }
}


# Email

if not USE_MAILGUN:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Security

SECRET_KEY = "django-insecure-y+2-+=@vup29_+#w69!8r4o$kco2(2k=^gq8=3fu1#0z)u12v0"


# Static & media

if not USE_S3:
    STATIC_URL = "static/"
    MEDIA_ROOT = MEDIA_DIR
    MEDIA_URL = "media/"


# Miscellaneous

ADMIN_URL_PATH = "admin/"

DOMAIN = "127.0.0.1:8000"

from environs import Env, EnvError

from sale_ads.conf.settings.base import *  # NOQA

_env = Env()
_env.read_env()


# Data

DATABASES = {
    "default": _env.dj_db_url("DATABASE_URL", "postgres://postgres@db/postgres")
}


# Security

ALLOWED_HOSTS = _env.list("DJANGO_ALLOWED_HOSTS")
CSRF_COOKIE_SECURE = True
SECRET_KEY = _env("DJANGO_SECRET_KEY")
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 2592000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
try:
    SECURE_PROXY_SSL_HEADER = tuple(_env.list("DJANGO_SECURE_PROXY_SSL_HEADER"))
except EnvError:
    pass


# Miscellaneous

ADMIN_URL_PATH = _env("DJANGO_ADMIN_URL_PATH")

DOMAIN = _env("DJANGO_DOMAIN")

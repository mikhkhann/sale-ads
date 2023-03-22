from django.urls import include, path

from accounts.views import (
    email,
    email_verification_sent,
    logout,
    settings,
    update_photo,
)

_SEGMENT = "accounts"

_sub_urlpatterns = [
    # Overriding
    path("confirm-email/", email_verification_sent),
    path("email/", email),
    path("logout/", logout),
    # Main
    path("", include("allauth.urls")),
    path("settings/", settings, name="accounts_settings"),
    path("settings/photo/", update_photo, name="accounts_update_photo"),
]
urlpatterns = [path(_SEGMENT + "/", include(_sub_urlpatterns))]

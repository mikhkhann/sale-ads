from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from ads.urls import last_root_urlpattern

urlpatterns = [
    path("", include("accounts.urls")),
    path("", include("ads.urls")),
    path("", include("languages.urls")),
    path("", include("pages.urls")),
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    *(
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        if not int(settings.USE_S3)
        else []
    ),
    last_root_urlpattern,
]

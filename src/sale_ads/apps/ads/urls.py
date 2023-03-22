from django.urls import include, path

from ads.views import (
    create,
    create_entry,
    delete,
    detail,
    list_,
    update,
    update_entry,
    update_images,
    user_list,
)

_SEGMENT = "ads"

urlpatterns = [path("", list_, name="ads_list")]
_sub_urlpatterns = [
    path("create/", create, name="ads_create"),
    path("<uuid:pk>/", detail, name="ads_detail"),
    path("<uuid:pk>/delete", delete, name="ads_delete"),
    path("<uuid:pk>/update/", update, name="ads_update"),
    path(
        "<uuid:ad_pk>/update/entries/<str:language>/create/",
        create_entry,
        name="ads_create_entry",
    ),
    path(
        "<uuid:ad_pk>/update/entries/<str:language>/update/",
        update_entry,
        name="ads_update_entry",
    ),
    path("<uuid:pk>/update/images/", update_images, name="ads_update_images"),
]
urlpatterns.append(path(_SEGMENT + "/", include(_sub_urlpatterns)))

last_root_urlpattern = path("<str:username>/", user_list, name="ads_user_list")

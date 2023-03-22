from django.urls import include, path

from languages.views import setting

_SEGMENT = "languages"

_sub_urlpatterns = [path("", setting, name="languages_setting")]
urlpatterns = [path(_SEGMENT + "/", include(_sub_urlpatterns))]

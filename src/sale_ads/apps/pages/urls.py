from django.urls import path

from pages.views import about

urlpatterns = [path("about", about, name="pages_about")]

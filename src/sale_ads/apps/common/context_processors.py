from django.conf import settings


def home_url(request):
    return {"home_url": settings.HOME_URL}

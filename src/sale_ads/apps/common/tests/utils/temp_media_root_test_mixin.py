from tempfile import TemporaryDirectory

from django.test import override_settings


class TempMediaRootTestMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media_root = cls.enterClassContext(TemporaryDirectory())
        cls.enterClassContext(override_settings(MEDIA_ROOT=media_root))

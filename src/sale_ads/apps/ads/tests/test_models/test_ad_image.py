from pathlib import Path
from uuid import UUID

from django.test import SimpleTestCase

from ads.models import AdImage

###############################################################################
# Unit tests


# ==========================================================
# Fields


# --------------------------------------
# Image


class AdImageImageUploadToTest(SimpleTestCase):
    def test(self):
        file_name = "test image.jpg"
        image = AdImage()
        field = AdImage._meta.get_field("image")
        result = Path(field.upload_to(image, file_name))
        self.assertEqual(result.parent, AdImage._DIR)
        UUID(result.stem)
        self.assertEqual(result.suffix, Path(file_name).suffix)

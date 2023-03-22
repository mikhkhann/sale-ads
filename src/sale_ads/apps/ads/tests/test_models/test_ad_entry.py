from django.test import SimpleTestCase

from ads.models import AdEntry
from common.tests import SaleAdsTestMixin

###############################################################################
# Unit tests


# ==========================================================
# Admin


class AdEntryStrTest(SaleAdsTestMixin, SimpleTestCase):
    def test(self):
        name = self.create_ad_entry_name_factory().get_unique()
        entry = AdEntry(name=name)
        self.assertEqual(str(entry), name)

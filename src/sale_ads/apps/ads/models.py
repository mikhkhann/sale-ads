from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language, get_language_info
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from categories.models import Category
from languages.validators import validate_language_allowed


class Ad(models.Model):
    # ==========================================================
    # Fields

    MAX_IMAGES = 7

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=pgettext_lazy("ad field", "author"),
    )
    created = models.DateTimeField(
        pgettext_lazy("ad field", "creation date & time"), auto_now_add=True
    )
    id = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    verified = models.BooleanField(pgettext_lazy("ad field", "verified"), default=False)

    # --------------------------------------
    # Category

    def _validate_category_ultimate(pk):
        category = Category.objects.get(pk=pk)
        if not category.ultimate:
            params = {"category": category.full_name}
            raise ValidationError(
                Ad._CATEGORY_NON_ULTIMATE_ERROR, "non_ultimate", params
            )

    _CATEGORY_NON_ULTIMATE_ERROR = _(
        'Ads can be added only to ultimate categories. "%(category)s" isn\'t '
        "an ultimate category."
    )

    category = models.ForeignKey(
        Category,
        models.PROTECT,
        validators=[_validate_category_ultimate],
        verbose_name=pgettext_lazy("ad field", "category"),
    )

    # --------------------------------------
    # Price

    _MIN_PRICE = Decimal("0.01")

    price = models.DecimalField(
        pgettext_lazy("ad field", "price"),
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(_MIN_PRICE)],
    )

    # ==========================================================

    class Meta:
        verbose_name = pgettext_lazy("model", "ad")
        verbose_name_plural = pgettext_lazy("model plural", "ads")

    def get_absolute_url(self):
        return reverse("ads_detail", kwargs={"pk": self.pk})

    def ordered_images(self):
        """Get images ordered by number."""
        return self.images.order_by("number")

    def __str__(self):
        names = dict(self.entries.values_list("language", "name"))
        names_in_result = [
            f"{get_language_info(language)['name_local']}: {names[language]}"
            for language in settings.LANGUAGE_PREFERENCE_ORDER
            if language in names
        ]
        return f"{self.pk} ({str.join('; ', names_in_result)})"

    def get_entry(self, language):
        """
        Get entry in specified or most preferred language.

        Returns the entry of the ad in the current language if it
        exists.
        Otherwise, returns the entry of the ad in the most preferred
        available language.
        Raises `AdEntry.DoesNotExist` if the ad has no entries.
        """
        entries = {entry.language: entry for entry in self.entries.all()}
        try:
            return entries[language]
        except KeyError:
            for language in settings.LANGUAGE_PREFERENCE_ORDER:
                try:
                    return entries[language]
                except KeyError:
                    pass
            raise AdEntry.DoesNotExist(self._NO_ENTRIES_ERROR)

    def get_entry_in_current_language(self):
        """
        Get entry in current or most preferred language.

        Works the same as `get_entry()` method called with the current
        language.
        """
        return self.get_entry(get_language())

    _NO_ENTRIES_ERROR = _("The ad has no entries.")


class AdEntry(models.Model):
    ad = models.ForeignKey(
        Ad,
        models.CASCADE,
        "entries",
        verbose_name=pgettext_lazy("ad entry field", "ad"),
    )
    description = models.TextField(pgettext_lazy("ad entry field", "description"))
    language = models.CharField(
        pgettext_lazy("ad entry field", "language"),
        max_length=10,
        validators=[validate_language_allowed],
    )
    name = models.CharField(pgettext_lazy("ad entry field", "name"), max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ad", "language"], name="ad_and_language_unique_together"
            )
        ]
        verbose_name = pgettext_lazy("model", "ad entry")
        verbose_name_plural = pgettext_lazy("model plural", "ad entries")

    def __str__(self):
        return self.name


class AdImage(models.Model):
    # ==========================================================
    # Fields

    ad = models.ForeignKey(
        Ad, models.CASCADE, "images", verbose_name=pgettext_lazy("ad image field", "ad")
    )
    number = models.IntegerField(
        pgettext_lazy("ad image field", "number"),
        validators=[MinValueValidator(1), MaxValueValidator(Ad.MAX_IMAGES)],
    )

    # --------------------------------------
    # Image

    def _image_upload_to(instance, filename):
        stem = str(uuid4())
        suffix = Path(filename).suffix
        name = Path(stem).with_suffix(suffix)
        return AdImage._DIR / name

    _DIR = Path("ads/images")

    image = models.ImageField(
        pgettext_lazy("ad image field", "image"), upload_to=_image_upload_to
    )

    # ==========================================================

    class Meta:
        verbose_name = pgettext_lazy("model", "ad image")
        verbose_name_plural = pgettext_lazy("model plural", "ad images")

import itertools
import random
from functools import cached_property
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from ads.models import Ad, AdEntry, AdImage
from categories.models import Category


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Users
        user_model = get_user_model()
        users = user_model.objects.bulk_create(
            user_model(
                email=f"test_user_{i}@mail.com",
                name=f"Test User {i + 1}",
                photo=random.choice(self._images),
                username=f"test_user_{i + 1}",
            )
            for i in range(10)
        )

        # Ads
        ads = Ad.objects.bulk_create(
            Ad(
                author=random.choice(users),
                category=category,
                price=random.randrange(1, 101) * 10 ** random.randrange(4),
                verified=True,
            )
            for category in Category.objects.filter(ultimate=True)
            for i in range(random.randrange(2, 5))
        )

        # Entries
        languages = list(zip(*settings.LANGUAGES))[0]
        language_combinations = list(
            itertools.chain.from_iterable(
                itertools.combinations(languages, length)
                for length in range(1, len(languages) + 1)
            )
        )
        name_templates = {"en": "Ad {}", "ru": "Объявление {}"}
        description_templates = {
            "en": "Description of ad {}",
            "ru": "Описание объявления {}",
        }
        AdEntry.objects.bulk_create(
            AdEntry(
                ad=ad,
                name=name_templates[language].format(ad_number),
                description=description_templates[language].format(ad_number),
                language=language,
            )
            for ad_number, ad in enumerate(random.sample(ads, k=len(ads)), start=1)
            for language in random.choice(language_combinations)
        )

        # Images
        AdImage.objects.bulk_create(
            AdImage(ad=ad, image=image_field, number=number)
            for ad in ads
            for number, image_field in enumerate(
                random.sample(self._images, random.randrange(Ad.MAX_IMAGES + 1)),
                start=1,
            )
        )

    @cached_property
    def _images(self):
        value = []
        for color in ("red", "orange", "yellow", "green", "blue", "indigo", "violet"):
            image = Image.new("RGB", (200, 200), color)
            stream = BytesIO()
            image.save(stream, "png")
            value.append(ContentFile(stream.getvalue(), "image.png"))
        return tuple(value)

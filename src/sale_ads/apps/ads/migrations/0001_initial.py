# Generated by Django 4.1.4 on 2023-03-11 08:24

import ads.models
from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import languages.validators
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ad",
            fields=[
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation date & time"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "verified",
                    models.BooleanField(default=False, verbose_name="verified"),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="price",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="author",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="categories.category",
                        validators=[ads.models.Ad._validate_category_ultimate],
                        verbose_name="category",
                    ),
                ),
            ],
            options={
                "verbose_name": "ad",
                "verbose_name_plural": "ads",
            },
        ),
        migrations.CreateModel(
            name="AdImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(7),
                        ],
                        verbose_name="number",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=ads.models.AdImage._image_upload_to,
                        verbose_name="image",
                    ),
                ),
                (
                    "ad",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="ads.ad",
                        verbose_name="ad",
                    ),
                ),
            ],
            options={
                "verbose_name": "ad image",
                "verbose_name_plural": "ad images",
            },
        ),
        migrations.CreateModel(
            name="AdEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.TextField(verbose_name="description")),
                (
                    "language",
                    models.CharField(
                        max_length=10,
                        validators=[languages.validators.validate_language_allowed],
                        verbose_name="language",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                (
                    "ad",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="ads.ad",
                        verbose_name="ad",
                    ),
                ),
            ],
            options={
                "verbose_name": "ad entry",
                "verbose_name_plural": "ad entries",
            },
        ),
        migrations.AddConstraint(
            model_name="adentry",
            constraint=models.UniqueConstraint(
                fields=("ad", "language"), name="ad_and_language_unique_together"
            ),
        ),
    ]

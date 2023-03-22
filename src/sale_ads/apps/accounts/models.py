import string
from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from languages.validators import validate_language_allowed


class User(AbstractUser):
    # ==========================================================
    # Fields

    email = models.EmailField(pgettext_lazy("user field", "E-mail"), unique=True)
    language = models.CharField(
        pgettext_lazy("user field", "language"),
        default=get_language,
        max_length=10,
        validators=[validate_language_allowed],
    )
    name = models.CharField(pgettext_lazy("user field", "name"), max_length=50)

    # --------------------------------------
    # Photo

    def _photo_upload_to(instance, filename):
        stem = str(uuid4())
        suffix = Path(filename).suffix
        name = Path(stem).with_suffix(suffix)
        return User._PHOTO_DIR / name

    _PHOTO_DIR = Path("accounts/photos")

    photo = models.ImageField(
        pgettext_lazy("user field", "photo"), blank=True, upload_to=_photo_upload_to
    )

    # --------------------------------------
    # Username

    MIN_USERNAME_LENGTH = 4
    _USERNAME_CHARACTERS = string.ascii_lowercase + string.digits + "_"
    USERNAME_GENERATION_CHARACTERS = _USERNAME_CHARACTERS
    USERNAME_GENERATION_LENGTH = 8

    _UNALLOWED_USERNAME_CHARACTERS_ERROR = _("Use only allowed characters.")

    _allowed_characters_username_validator = RegexValidator(
        f"^[{_USERNAME_CHARACTERS}]*\Z",
        _UNALLOWED_USERNAME_CHARACTERS_ERROR,
        "unallowed_characters",
    )

    def _validate_username_not_forbidden(username):
        if username in User._FORBIDDEN_USERNAMES:
            raise ValidationError(
                User._FORBIDDEN_USERNAME_ERROR,
                "forbidden",
                params={"username": username},
            )

    _FORBIDDEN_USERNAMES = ("about", "accounts", "admin", "languages")
    _FORBIDDEN_USERNAME_ERROR = _('"%(username)s" is a forbidden username.')

    username = models.CharField(
        pgettext_lazy("user field", "username"),
        max_length=20,
        error_messages={
            "unique": AbstractUser._meta.get_field("username").error_messages["unique"]
        },
        unique=True,
        validators=[
            MinLengthValidator(MIN_USERNAME_LENGTH),
            _allowed_characters_username_validator,
            _validate_username_not_forbidden,
        ],
    )

    def is_generated_username_valid(self):
        exclude = {field.name for field in self._meta.get_fields()} - {"username"}
        try:
            self.full_clean(exclude=exclude)
        except ValidationError as error:
            return "username" not in error.message_dict
        return True

    # --------------------------------------
    # Removed

    first_name = ""
    last_name = ""

    # ==========================================================

    def get_absolute_url(self):
        return reverse("ads_user_list", kwargs={"username": self.username})

    @classmethod
    @property
    def REQUIRED_FIELDS(cls):
        if User._REQUIRED_FIELDS is None:
            User._REQUIRED_FIELDS = (*super().REQUIRED_FIELDS, "name")
        return User._REQUIRED_FIELDS

    _REQUIRED_FIELDS = None

    def __str__(self):
        return f"{self.name} (@{self.username})"

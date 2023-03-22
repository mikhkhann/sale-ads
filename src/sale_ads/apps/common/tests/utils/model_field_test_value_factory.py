import itertools
import random
import string
from functools import cached_property

from django.core.exceptions import ValidationError


class DefaultValueUnspecifiedError(ValueError):
    pass


class ModelFieldTestValueFactory:
    unique_value_count_start = 1

    def get_unique(self, *args, **kwargs):
        value = self.get_unique_value(*args, **kwargs)
        self.check(value)
        return value

    def get_choice(self, index=0, *args, **kwargs):
        value = self.get_choice_value(index, *args, **kwargs)
        self.check(value)
        return value

    def get_choice_value(self, index=0):
        return self.choices[index]

    @cached_property
    def choices(self):
        return tuple(self.get_choices())

    def check(self, value):
        self.run_check(value)

    def get_invalid(self, *args, **kwargs):
        try:
            return self.get_default_invalid(*args, **kwargs)
        except DefaultValueUnspecifiedError:
            return self.get_unique_invalid(*args, **kwargs)

    def get_unique_invalid(self, *args, **kwargs):
        value = self.get_unique_invalid_value(*args, **kwargs)
        self.check_invalid(value)
        return value

    def get_default_invalid(self, *args, **kwargs):
        value = self.get_default_invalid_value(*args, **kwargs)
        self.check_invalid(value)
        return value

    def get_default_invalid_value(self):
        try:
            return self.default_invalid_value
        except AttributeError:
            raise DefaultValueUnspecifiedError

    def check_invalid(self, value):
        try:
            self.run_check(value)
        except ValidationError:
            return
        raise AssertionError(
            f'{repr(value)} isn\'t an invalid value of the "{self.field}" field of '
            f"the `{self.model.__name__}` model."
        )

    def run_check(self, value):
        obj = self.model(**{self.field: value})
        obj.full_clean(exclude=self.get_unchecked_fields_names())

    def get_unchecked_fields_names(self):
        try:
            return self.unchecked_fields_names
        except AttributeError:
            pass
        return {field.name for field in self.model._meta.get_fields()} - {self.field}

    def get_unique_value_number(self):
        return next(self.unique_value_count)

    @property
    def unique_value_count(self):
        key = self.model, self.field
        try:
            return self.UNIQUE_VALUES_COUNTS[key]
        except KeyError:
            self.UNIQUE_VALUES_COUNTS[key] = itertools.count(
                self.unique_value_count_start
            )
            return self.UNIQUE_VALUES_COUNTS[key]

    UNIQUE_VALUES_COUNTS = {}


class ModelStringFieldTestValueFactory(ModelFieldTestValueFactory):
    separator = "_"
    invalid_value_filler = "a"

    def get_unique_value(self, *, prefix=None, suffix=None, main_part=None):
        if main_part is None:
            main_part = self.get_main_part()
        value = self.make_unique(main_part)
        value = self.add_prefix(value, prefix)
        return self.add_suffix(value, suffix)

    def get_unique_invalid_value(self, *args, main_part=None, **kwargs):
        main_part = self.get_invalid_main_part(main_part=main_part)
        return self.get_unique_value(*args, main_part=main_part, **kwargs)

    def get_invalid_main_part(self, main_part=None):
        if main_part is None:
            main_part = self.get_main_part()
        return main_part + (
            self.invalid_value_filler
            * self.model._meta.get_field(self.field).max_length
        )

    def get_main_part(self):
        try:
            return self.main_part
        except AttributeError:
            separator = self.get_separator()
            items = map(str, self.get_main_part_items())
            return str.join(separator, items)

    def get_main_part_items(self):
        return ["test", self.model._meta.model_name, self.field, "value"]

    def make_unique(self, value):
        return value + self.get_separator() + self.get_unique_part()

    def get_unique_part(self):
        return str(self.get_unique_value_number())

    def add_prefix(self, value, prefix):
        if prefix is not None:
            value = str(prefix) + self.get_separator() + value
        return value

    def add_suffix(self, value, suffix):
        if suffix is not None:
            value += self.get_separator() + str(suffix)
        return value

    def get_separator(self):
        return self.separator


class ModelEmailFieldTestValueFactory(ModelStringFieldTestValueFactory):
    default_invalid_value = "invalid test email"

    def get_unique_value(self, *args, **kwargs):
        return super().get_unique_value(*args, **kwargs) + "@mail.com"


class ModelPasswordFieldTestValueFactory(ModelStringFieldTestValueFactory):
    lowercase = True
    uppercase = False
    digits = False
    special_characters = False
    main_part_length = 8

    def get_main_part(self, *args, main_part_length=None, **kwargs):
        characters = self.get_characters(*args, **kwargs)
        if main_part_length is None:
            main_part_length = self.main_part_length
        return str.join("", random.choices(characters, k=main_part_length))

    def get_characters(
        self, lowercase=None, uppercase=None, digits=None, special_characters=None
    ):
        characters = ""
        if lowercase is None:
            lowercase = self.lowercase
        if lowercase if lowercase is not None else self.lowercase:
            characters += string.ascii_lowercase
        if uppercase if uppercase is not None else self.uppercase:
            characters += string.ascii_uppercase
        if digits if digits is not None else self.digits:
            characters += string.digits
        if (
            special_characters
            if special_characters is not None
            else self.special_characters
        ):
            characters += string.punctuation
        return characters

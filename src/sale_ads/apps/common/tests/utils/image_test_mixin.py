import itertools
from functools import cached_property
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


class ImageTestMixin:
    @classmethod
    def get_test_image(cls, *args, **kwargs):
        return cls.get_valid_or_invalid_test_image(cls.TestImage, *args, **kwargs)

    @classmethod
    def get_invalid_test_image(cls, *args, **kwargs):
        return cls.get_valid_or_invalid_test_image(
            cls.InvalidTestImage, *args, **kwargs
        )

    @classmethod
    def get_valid_or_invalid_test_image(cls, test_image_class, *args, **kwargs):
        return test_image_class(*args, enter_context=cls.enterClassContext, **kwargs)

    class BaseTestImage:
        _count = itertools.count(1)

        def __init__(self, format="jpg", *, enter_context):
            self._format = format
            self.enter_context = enter_context
            self._number = next(self._count)

        def open(self):
            stream = self.enter_context(BytesIO(self.data))
            stream.name = self.name
            return stream

        def get_uploaded(self):
            return SimpleUploadedFile(self.name, self.data)

        @property
        def data(self):
            return self._data

        @cached_property
        def _data(self):
            return self.generate_data()

        @property
        def format(self):
            return self._format

        @property
        def name(self):
            return self._name

        @cached_property
        def _name(self):
            return f"test image {self.number}.{self.format}"

        @property
        def number(self):
            return self._number

    class TestImage(BaseTestImage):
        def __init__(self, format="png", height=None, width=None, **kwargs):
            super().__init__(format, **kwargs)
            self._height = height
            self._width = width

        def generate_data(self):
            pixels = self.generate_pixels()
            if self._height is None:
                self._height = 1
            if self._width is None:
                self._width = len(pixels) // self._height + 1
            image = Image.new("RGB", (self._height, self._width))
            image.putdata(pixels)
            with BytesIO() as stream:
                image.save(stream, self.format)
                return stream.getvalue()

        def generate_pixels(self):
            image_number = self.number - 1
            colors = []
            while True:
                image_number, color = divmod(image_number, 256)
                colors.append(color)
                if not image_number:
                    break
            colors += [0] * (3 - len(colors) % 3)
            pixels = []
            while colors:
                pixel = tuple(colors[:3])
                colors = colors[3:]
                pixels.append(pixel)
            return pixels

        @property
        def height(self):
            if self._height is None:
                self.data
            return self._height

        @property
        def width(self):
            if self._width is None:
                self.data
            return self._width

    class InvalidTestImage(BaseTestImage):
        def generate_data(self):
            number_as_bytes = bytes(str(self.number), encoding="utf8")
            return b"invalid test image data " + number_as_bytes

        @property
        def name(self):
            return "invalid " + super().name

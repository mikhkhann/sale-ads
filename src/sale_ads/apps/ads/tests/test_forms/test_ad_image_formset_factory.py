from collections import Counter
from doctest import DocTestSuite

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ads.forms import _BaseAdImageFormSet, ad_image_formset_factory
from common.tests.utils.image_test_mixin import ImageTestMixin


def load_tests(loader, standard_tests, pattern):
    import ads.forms

    test_suite = DocTestSuite(ads.forms)
    standard_tests.addTests(test_suite)
    return standard_tests


###############################################################################
# Integration tests


class AdImageFormsetFactoryTest(SimpleTestCase):
    def test(self):
        extra = 2
        result = ad_image_formset_factory(extra)
        self.assertEqual(result.extra, extra)


###############################################################################
# Base formset


# ==========================================================
# Unit tests


# --------------------------------------
# "Invalid images" error


class BaseAdImageFormSetAddInvalidImagesErrorToTest(ImageTestMixin, SimpleTestCase):
    def test_with_single_invalid_image(self):
        test_image = self.get_invalid_test_image()
        formset_class = ad_image_formset_factory(1)
        files = {self.get_field(0): test_image.get_uploaded()}
        formset = self.create_formset(formset_class, files=files)
        other_formset = self.create_formset(formset_class)
        formset.add_invalid_images_error_to(other_formset)
        (actual,) = other_formset.non_form_errors()
        expected_params = {"count": 1, "names": f'"{test_image.name}"'}
        expected = _BaseAdImageFormSet._INVALID_IMAGES_ERROR % expected_params
        self.assertEqual(actual, expected)

    def test_with_multiple_invalid_images(self):
        test_images = [self.get_invalid_test_image() for i in range(2)]
        test_image_1, test_image_2 = test_images
        formset_class = ad_image_formset_factory(len(test_images))
        files = {
            self.get_field(form_index): test_image.get_uploaded()
            for form_index, test_image in enumerate(test_images)
        }
        formset = self.create_formset(formset_class, files=files)
        other_formset = self.create_formset(formset_class)
        formset.add_invalid_images_error_to(other_formset)
        (actual,) = other_formset.non_form_errors()
        expected_params = {
            "count": len(test_images),
            "names": f'"{test_image_1.name}", "{test_image_2.name}"',
        }
        expected = _BaseAdImageFormSet._INVALID_IMAGES_ERROR % expected_params
        self.assertEqual(actual, expected)

    def test_with_invalid_and_valid_images(self):
        valid_test_image = self.get_test_image()
        invalid_test_image = self.get_invalid_test_image()
        formset_class = ad_image_formset_factory(2)
        files = {
            self.get_field(form_index): test_image.get_uploaded()
            for form_index, test_image in enumerate(
                [valid_test_image, invalid_test_image]
            )
        }
        formset = self.create_formset(formset_class, files=files)
        other_formset = self.create_formset(formset_class)
        formset.add_invalid_images_error_to(other_formset)
        (actual,) = other_formset.non_form_errors()
        expected_params = {"count": 1, "names": f'"{invalid_test_image.name}"'}
        expected = _BaseAdImageFormSet._INVALID_IMAGES_ERROR % expected_params
        self.assertEqual(actual, expected)

    def test_error_code(self):
        formset_class = ad_image_formset_factory(1)
        files = {self.get_field(0): self.get_invalid_test_image().get_uploaded()}
        formset = self.create_formset(formset_class, files=files)
        other_formset = self.create_formset(formset_class)
        formset.add_invalid_images_error_to(other_formset)
        (error,) = other_formset.non_form_errors().as_data()
        self.assertEqual(error.code, "invalid_images")

    def test_with_base_non_form_erros(self):
        test_image = self.get_invalid_test_image()
        formset_class = ad_image_formset_factory(1)
        files = {self.get_field(0): test_image.get_uploaded()}
        formset = self.create_formset(formset_class, files=files)
        other_formset = self.create_formset(formset_class)
        base_error_message = "test base error message"
        base_error = ValidationError(base_error_message)
        other_formset.non_form_errors()
        other_formset._non_form_errors.append(base_error)
        formset.add_invalid_images_error_to(other_formset)
        actual_non_form_errors = other_formset.non_form_errors()
        expected_invalid_images_error = _BaseAdImageFormSet._INVALID_IMAGES_ERROR % {
            "count": 1,
            "names": f'"{test_image.name}"',
        }
        expected_non_form_errors = [expected_invalid_images_error, base_error_message]
        self.assertDictEqual(
            Counter(actual_non_form_errors), Counter(expected_non_form_errors)
        )

    def get_field(self, form_index):
        return f"form-{form_index}-image"

    def create_formset(self, formset_class, data=None, files=None, *args, **kwargs):
        if data is not None or files is not None:
            if data is None:
                data = {}
            data.update(
                {"form-INITIAL_FORMS": 0, "form-TOTAL_FORMS": formset_class.extra}
            )
        return formset_class(data, files, *args, **kwargs)


class BaseAdImageFormSetInvalidImagesErrorTest(SimpleTestCase):
    def test_formatting_with_single_image(self):
        params = {"count": 1, "names": '"1.jpg"'}
        expected = 'Image "1.jpg" is invalid.'
        self._test_formatting(params, expected)

    def test_formatting_with_multiple_images(self):
        params = {"count": 2, "names": '"1.jpg", "2.jpg"'}
        expected = 'Images "1.jpg", "2.jpg" are invalid.'
        self._test_formatting(params, expected)

    def _test_formatting(self, params, expected):
        self.assertEqual(_BaseAdImageFormSet._INVALID_IMAGES_ERROR % params, expected)

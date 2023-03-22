from collections.abc import Iterable

from django import forms
from django.utils.html import conditional_escape


class WidgetLibMixin:
    class WidgetMixin:
        default_invalid_css_class = None
        css_class_context_item = "widget_class"
        css_extra_class_context_item = "widget_extra_class"
        invalid_css_class_context_item = "widget_invalid_class"
        extra_invalid_css_class_context_item = "widget_extra_invalid_class"

        def add_autocomplete_attr(self, attrs):
            if self.context.autocomplete is not None:
                attrs["autocomplete"] = self.context.autocomplete

        def get_css_classes(self):
            classes = []
            classes.extend(self.get_base_css_classes())
            if not self.context.valid and self.context.valid is not None:
                classes.extend(self.get_invalid_css_classes())
            return classes

        def get_base_css_classes(self):
            return super().get_css_classes()

        def get_invalid_css_classes(self):
            classes = []
            cls = getattr(self.context, self.invalid_css_class_context_item)
            if cls:
                classes.append(cls)
            elif cls is not False:
                if self.default_invalid_css_class:
                    classes.append(self.default_invalid_css_class)
                extra = getattr(self.context, self.extra_invalid_css_class_context_item)
                if extra:
                    classes.append(extra)
            return classes

        def add_maxlength_attr(self, attrs):
            if self.context.maxlength is not None:
                attrs["maxlength"] = self.context.maxlength

        def add_minlength_attr(self, attrs):
            if self.context.minlength is not None:
                attrs["minlength"] = self.context.minlength

        def add_name_attr(self, attrs):
            if self.context.name is not None:
                attrs["name"] = self.context.name

        def add_placeholder_attr(self, attrs):
            if self.context.placeholder is not None:
                attrs["placeholder"] = self.context.placeholder

        def add_required_attr(self, attrs):
            if self.context.required or self.context.required is None:
                attrs["required"] = None

        def add_value_attr(self, attrs):
            if self.context.value is not None:
                attrs["value"] = self.context.safe_value

    @classmethod
    def get_widget_mixins(cls):
        return [cls.WidgetMixin]

    class ContextMixin:
        items = (
            "autocomplete",
            "maxlength",
            "minlength",
            "multi_choice",
            "name",
            "placeholder",
            "valid",
            "value",
            "safe_value",
            "widget_class",
            "widget_extra_class",
            "widget_invalid_class",
            "widget_extra_invalid_class",
        )

        def compute_maxlength(self):
            if not self.is_inherited("field"):
                return (
                    getattr(self.field.field, "max_length", None)
                    if self.field
                    else None
                )
            raise self.ItemComputationFailed

        def compute_minlength(self):
            if not self.is_inherited("field"):
                return (
                    getattr(self.field.field, "min_length", None)
                    if self.field
                    else None
                )
            raise self.ItemComputationFailed

        def compute_multi_choice(self):
            if not self.is_inherited("field") or not self.is_inherited("value"):
                if self.field:
                    return isinstance(self.field.field, forms.MultipleChoiceField)
                elif self.value is not None:
                    return (
                        isinstance(self.value, Iterable)
                        and not isinstance(self.value, str)
                    )  # fmt: skip
                return None
            raise self.ItemComputationFailed

        def clean_multi_choice(self, value):
            return self.clean_bool(value)

        def compute_name(self):
            if not self.is_inherited("field"):
                return self.field.html_name if self.field else None
            raise self.ItemComputationFailed

        def compute_valid(self):
            if not self.is_inherited("field") or not self.is_inherited("field_errors"):
                if self.field is not None:
                    return not self.field.errors if self.field else None
                return not self.field_errors if self.field_errors is not None else None
            raise self.ItemComputationFailed

        def clean_valid(self, value):
            return self.clean_bool(value)

        def compute_value(self):
            if not self.is_inherited("field"):
                return self.field.value() if self.field else None
            raise self.ItemComputationFailed

        def compute_safe_value(self):
            if not self.is_inherited("value"):
                if self.value is not None:
                    return (
                        conditional_escape(self.value)
                        if not self.multi_choice
                        else tuple(map(conditional_escape, self.value))
                    )
                return None
            raise self.ItemComputationFailed

    @classmethod
    def widget(cls, __element_object_class, field="", **kwargs):
        widget = cls.create_element(__element_object_class, field=field, **kwargs)
        return widget.render()

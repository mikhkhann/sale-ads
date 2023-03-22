from functools import cached_property

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class FieldLabelLibMixin:
    element_mixin_getters = {"FieldLabel": "get_field_label_mixins"}
    tags = ("field_label",)

    class FieldLabelMixin:
        tag = "label"
        css_class_context_item = "label_class"
        css_extra_class_context_item = "label_extra_class"
        default_required_mark = None

        def get_content(self):
            return self.label

        @cached_property
        def label(self):
            return self.get_label()

        def get_label(self):
            label = (
                conditional_escape(self.context.label)
                if self.context.label
                else _SAFE_EMPTY_STRING
            )
            suffix = self.get_suffix(label)
            if suffix:
                label += conditional_escape(suffix)
            return label

        def get_suffix(self, label):
            suffix = _SAFE_EMPTY_STRING
            if (
                (self.context.required or self.context.required is None)
                and (label or self.context.required_mark_if_empty)
            ):  # fmt: skip
                required_mark = self.get_required_mark()
                if required_mark:
                    suffix += conditional_escape(required_mark)
            return suffix

        def get_required_mark(self):
            return (
                self.context.required_mark
                if self.context.required_mark is not None
                else self.default_required_mark
            )

    @classmethod
    def get_field_label_mixins(cls):
        return [cls.FieldLabelMixin]

    class ContextMixin:
        items = (
            "label",
            "required_mark",
            "required_mark_if_empty",
            "label_class",
            "label_extra_class",
        )

        def clean_required_mark_if_empty(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_field_label(cls, __element_object_class, label="", field="", **kwargs):
        label = cls.create_element(
            __element_object_class, field=field, label=label, **kwargs
        )
        return label.render() if label.label else ""

    @classmethod
    def field_label(cls, *args, **kwargs):
        return cls.base_field_label(cls.FieldLabel, *args, **kwargs)

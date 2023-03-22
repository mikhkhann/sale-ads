from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class FieldLibMixin:
    class FieldMixin:
        tag = "div"
        css_class_context_item = "field_class"
        css_extra_class_context_item = "field_extra_class"
        label_element_object_class_name = "FieldLabel"
        widget_element_object_class_name = None
        error_list_element_object_class_name = "FieldErrorList"

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.label_element_object_class_name:
                cls.label_element_object_class = cls.lib.get_element_object_class(
                    cls.label_element_object_class_name
                )
            if cls.widget_element_object_class_name:
                cls.widget_element_object_class = cls.lib.get_element_object_class(
                    cls.widget_element_object_class_name
                )
            if cls.error_list_element_object_class_name:
                cls.error_list_element_object_class = cls.lib.get_element_object_class(
                    cls.error_list_element_object_class_name
                )

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            label = self.get_label_content()
            if label:
                content += conditional_escape(label)
            widget = self.get_widget_content()
            if widget:
                content += conditional_escape(widget)
            errors = self.get_errors_content()
            if errors:
                content += conditional_escape(errors)
            return content

        def get_label_content(self):
            label = self.create_child(self.label_element_object_class)
            return label.render() if label.label else None

        def get_widget_content(self):
            return self.create_child(self.widget_element_object_class).render()

        def get_errors_content(self):
            return (
                self.create_child(self.error_list_element_object_class).render()
                if self.context.field_errors
                else None
            )

    @classmethod
    def get_field_mixins(cls):
        return [cls.FieldMixin]

    class ContextMixin:
        items = ("field_class", "field_extra_class")

    @classmethod
    def field(cls, __element_object_class, field="", label="", **kwargs):
        element = cls.create_element(
            __element_object_class, field=field, label=label, **kwargs
        )
        return element.render()

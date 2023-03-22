from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class ClearableFileWidgetLibMixin:
    element_mixin_getters = {"ClearableFileWidget": "get_clearable_file_widget_mixins"}
    tags = ("clearable_file_widget",)

    class ClearableFileWidgetMixin:
        tag = "div"
        css_class_context_item = "clearable_file_widget_class"
        css_extra_class_context_item = "clearable_file_widget_extra_class"
        file_widget_element_object_class_name = "FileWidget"
        removal_widget_element_object_class_name = "LabeledFileRemovalSubwidget"

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.file_widget_element_object_class_name:
                cls.file_widget_element_object_class = cls.lib.get_element_object_class(
                    cls.file_widget_element_object_class_name
                )
            if cls.removal_widget_element_object_class_name:
                cls.removal_widget_element_object_class = (
                    cls.lib.get_element_object_class(
                        cls.removal_widget_element_object_class_name
                    )
                )

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            file_widget = self.get_file_widget_content()
            if file_widget:
                content += conditional_escape(file_widget)
            removal_widget = self.get_removal_widget_content()
            if removal_widget:
                content += conditional_escape(removal_widget)
            return content

        def get_file_widget_content(self):
            return self.create_child(self.file_widget_element_object_class).render()

        def get_removal_widget_content(self):
            if self.context.clear_file:
                widget = self.create_child(
                    self.removal_widget_element_object_class,
                    removable_file_field=self.context.field,
                )
                return widget.render()
            return None

    @classmethod
    def get_clearable_file_widget_mixins(cls):
        return [cls.ClearableFileWidgetMixin]

    class ContextMixin:
        items = (
            "clear_file",
            "clearable_file_widget_class",
            "clearable_file_widget_extra_class",
        )

        def compute_clear_file(self):
            if not self.is_inherited("value"):
                return bool(self.value)
            raise self.ItemComputationFailed

        def clean_clear_file(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_clearable_file_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def clearable_file_widget(cls, *args, **kwargs):
        return cls.base_clearable_file_widget(cls.ClearableFileWidget, *args, **kwargs)

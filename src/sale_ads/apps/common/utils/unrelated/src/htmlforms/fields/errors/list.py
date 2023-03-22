from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMTPY_STRING = mark_safe("")


class FieldErrorListLibMixin:
    element_mixin_getters = {"FieldErrorList": "get_field_error_list_mixins"}
    tags = ("field_errors",)

    class FieldErrorListMixin:
        tag = "div"
        css_class_context_item = "error_list_class"
        css_extra_class_context_item = "error_list_extra_class"
        error_element_object_class_name = "FieldError"

        @classmethod
        def init_class(cls):
            super().init_class()
            cls.error_element_object_class = cls.lib.get_element_object_class(
                cls.error_element_object_class_name
            )

        def get_content(self):
            content = _SAFE_EMTPY_STRING
            for error in self.context.field_errors or ():
                content += conditional_escape(self.get_error_content(error))
            return content

        def get_error_content(self, error):
            error = self.create_child(self.error_element_object_class, error=error)
            return error.render()

    @classmethod
    def get_field_error_list_mixins(cls):
        return [cls.FieldErrorListMixin]

    @classmethod
    def base_field_errors(cls, __element_object_class, field="", **kwargs):
        error_list = cls.create_element(__element_object_class, field=field, **kwargs)
        return error_list.render() if error_list.context.field_errors else ""

    @classmethod
    def field_errors(cls, *args, **kwargs):
        return cls.base_field_errors(cls.FieldErrorList, *args, **kwargs)

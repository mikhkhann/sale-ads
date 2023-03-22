from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMTPY_STRING = mark_safe("")


class FormErrorListLibMixin:
    element_mixin_getters = {"FormErrorList": "get_form_error_list_mixins"}
    tags = ("form_errors",)

    class FormErrorListMixin:
        tag = "div"
        css_class_context_item = "error_list_class"
        css_extra_class_context_item = "error_list_extra_class"
        error_element_object_class_name = "FormError"

        @classmethod
        def init_class(cls):
            super().init_class()
            cls.error_element_object_class = cls.lib.get_element_object_class(
                cls.error_element_object_class_name
            )

        def get_content(self):
            content = _SAFE_EMTPY_STRING
            for error in self.context.form_errors or ():
                content += conditional_escape(self.get_error_content(error))
            return content

        def get_error_content(self, error):
            error = self.create_child(self.error_element_object_class, error=error)
            return error.render()

    @classmethod
    def get_form_error_list_mixins(cls):
        return [cls.FormErrorListMixin]

    class ContextMixin:
        items = ("form_errors",)

        def compute_form_errors(self):
            if not self.is_inherited("form"):
                return self.form.non_field_errors() if self.form else None
            raise self.ItemComputationFailed

    @classmethod
    def base_form_errors(cls, __element_object_class, form="", **kwargs):
        error_list = cls.create_element(__element_object_class, form=form, **kwargs)
        return error_list.render() if error_list.context.form_errors else ""

    @classmethod
    def form_errors(cls, *args, **kwargs):
        return cls.base_form_errors(cls.FormErrorList, *args, **kwargs)

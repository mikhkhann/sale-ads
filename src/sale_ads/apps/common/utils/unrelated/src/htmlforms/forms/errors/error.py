class FormErrorLibMixin:
    element_mixin_getters = {"FormError": "get_form_error_mixins"}
    tags = ("form_error",)

    class FormErrorMixin:
        tag = "div"
        css_class_context_item = "error_class"
        css_extra_class_context_item = "error_extra_class"

        def get_content(self):
            return self.context.error

    @classmethod
    def get_form_error_mixins(cls):
        return [cls.FormErrorMixin]

    @classmethod
    def base_form_error(cls, __element_object_class, error="", **kwargs):
        error = cls.create_element(__element_object_class, error=error, **kwargs)
        return error.render()

    @classmethod
    def form_error(cls, *args, **kwargs):
        return cls.base_form_error(cls.FormError, *args, **kwargs)

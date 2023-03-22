class FieldErrorLibMixin:
    element_mixin_getters = {"FieldError": "get_field_error_mixins"}
    tags = ("field_error",)

    class FieldErrorMixin:
        tag = "div"
        css_class_context_item = "error_class"
        css_extra_class_context_item = "error_extra_class"

        def get_content(self):
            return self.context.error

    @classmethod
    def get_field_error_mixins(cls):
        return [cls.FieldErrorMixin]

    @classmethod
    def base_field_error(cls, __element_object_class, error="", **kwargs):
        error = cls.create_element(__element_object_class, error=error, **kwargs)
        return error.render()

    @classmethod
    def field_error(cls, *args, **kwargs):
        return cls.base_field_error(cls.FieldError, *args, **kwargs)

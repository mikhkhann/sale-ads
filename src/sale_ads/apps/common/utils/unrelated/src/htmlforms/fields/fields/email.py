class EmailFieldLibMixin:
    element_mixin_getters = {"EmailField": "get_email_field_mixins"}
    tags = ("email_field",)

    class EmailFieldMixin:
        widget_element_object_class_name = "EmailWidget"

    @classmethod
    def get_email_field_mixins(cls):
        return [cls.EmailFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_email_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def email_field(cls, *args, **kwargs):
        return cls.base_email_field(cls.EmailField, *args, **kwargs)

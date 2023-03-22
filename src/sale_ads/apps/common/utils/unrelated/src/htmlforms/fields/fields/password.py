class PasswordFieldLibMixin:
    element_mixin_getters = {"PasswordField": "get_password_field_mixins"}
    tags = ("password_field",)

    class PasswordFieldMixin:
        widget_element_object_class_name = "PasswordWidget"

    @classmethod
    def get_password_field_mixins(cls):
        return [cls.PasswordFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_password_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def password_field(cls, *args, **kwargs):
        return cls.base_password_field(cls.PasswordField, *args, **kwargs)

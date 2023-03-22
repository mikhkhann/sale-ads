class TextAreaFieldLibMixin:
    element_mixin_getters = {"TextAreaField": "get_textarea_field_mixins"}
    tags = ("textarea_field",)

    class TextAreaFieldMixin:
        widget_element_object_class_name = "TextAreaWidget"

    @classmethod
    def get_textarea_field_mixins(cls):
        return [cls.TextAreaFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_textarea_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def textarea_field(cls, *args, **kwargs):
        return cls.base_textarea_field(cls.TextAreaField, *args, **kwargs)

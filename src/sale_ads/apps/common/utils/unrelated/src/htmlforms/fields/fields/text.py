class TextFieldLibMixin:
    element_mixin_getters = {"TextField": "get_text_field_mixins"}
    tags = ("text_field",)

    class TextFieldMixin:
        widget_element_object_class_name = "TextWidget"

    @classmethod
    def get_text_field_mixins(cls):
        return [cls.TextFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_text_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def text_field(cls, *args, **kwargs):
        return cls.base_text_field(cls.TextField, *args, **kwargs)

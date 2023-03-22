class BooleanFieldLibMixin:
    element_mixin_getters = {"BooleanField": "get_boolean_field_mixins"}
    tags = ("boolean_field",)

    class BooleanFieldMixin:
        widget_element_object_class_name = "LabeledBooleanWidget"

    @classmethod
    def get_boolean_field_mixins(cls):
        return [cls.BooleanFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_boolean_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def boolean_field(cls, *args, **kwargs):
        return cls.base_boolean_field(cls.BooleanField, *args, **kwargs)

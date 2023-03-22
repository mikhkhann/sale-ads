class NumberFieldLibMixin:
    element_mixin_getters = {"NumberField": "get_number_field_mixins"}
    tags = ("number_field",)

    class NumberFieldMixin:
        widget_element_object_class_name = "NumberWidget"

    @classmethod
    def get_number_field_mixins(cls):
        return [cls.NumberFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_number_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def number_field(cls, *args, **kwargs):
        return cls.base_number_field(cls.NumberField, *args, **kwargs)

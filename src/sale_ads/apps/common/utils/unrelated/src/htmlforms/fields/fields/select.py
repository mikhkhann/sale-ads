class SelectFieldLibMixin:
    element_mixin_getters = {"SelectField": "get_select_field_mixins"}
    tags = ("select_field",)

    class SelectFieldMixin:
        widget_element_object_class_name = "SelectWidget"

    @classmethod
    def get_select_field_mixins(cls):
        return [cls.SelectFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_select_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def select_field(cls, *args, **kwargs):
        return cls.base_select_field(cls.SelectField, *args, **kwargs)

class CheckboxListFieldLibMixin:
    element_mixin_getters = {"CheckboxListField": "get_checkbox_list_field_mixins"}
    tags = ("checkbox_list_field",)

    class CheckboxListFieldMixin:
        widget_element_object_class_name = "CheckboxList"

    @classmethod
    def get_checkbox_list_field_mixins(cls):
        return [cls.CheckboxListFieldMixin, *cls.get_flag_widget_list_field_mixins()]

    @classmethod
    def base_checkbox_list_field(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_list_field(__element_object_class, *args, **kwargs)

    @classmethod
    def checkbox_list_field(cls, *args, **kwargs):
        return cls.base_checkbox_list_field(cls.CheckboxListField, *args, **kwargs)

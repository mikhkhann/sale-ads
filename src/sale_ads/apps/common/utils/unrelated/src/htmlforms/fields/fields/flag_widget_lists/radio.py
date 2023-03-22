class RadioListFieldLibMixin:
    element_mixin_getters = {"RadioListField": "get_radio_list_field_mixins"}
    tags = ("radio_list_field",)

    class RadioListFieldMixin:
        widget_element_object_class_name = "RadioList"

    @classmethod
    def get_radio_list_field_mixins(cls):
        return [cls.RadioListFieldMixin, *cls.get_flag_widget_list_field_mixins()]

    @classmethod
    def base_radio_list_field(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_list_field(__element_object_class, *args, **kwargs)

    @classmethod
    def radio_list_field(cls, *args, **kwargs):
        return cls.base_radio_list_field(cls.RadioListField, *args, **kwargs)

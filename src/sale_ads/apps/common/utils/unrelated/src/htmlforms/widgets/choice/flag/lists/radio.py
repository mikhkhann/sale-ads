class RadioListLibMixin:
    element_mixin_getters = {"RadioList": "get_radio_list_mixins"}
    tags = ("radio_list",)

    class RadioListMixin:
        choice_element_object_class_name = "LabeledRadioWidget"

    @classmethod
    def get_radio_list_mixins(cls):
        return [cls.RadioListMixin, *cls.get_flag_widget_list_mixins()]

    @classmethod
    def base_radio_list(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_list(__element_object_class, *args, **kwargs)

    @classmethod
    def radio_list(cls, *args, **kwargs):
        return cls.base_radio_list(cls.RadioList, *args, **kwargs)

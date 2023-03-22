class RadioLabelLibMixin:
    element_mixin_getters = {"RadioLabel": "get_radio_label_mixins"}
    tags = ("radio_label",)

    class RadioLabelMixin:
        pass

    @classmethod
    def get_radio_label_mixins(cls):
        return [cls.RadioLabelMixin, *cls.get_flag_widget_label_mixins()]

    @classmethod
    def base_radio_label(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_label(__element_object_class, *args, **kwargs)

    @classmethod
    def radio_label(cls, *args, **kwargs):
        return cls.base_radio_label(cls.RadioLabel, *args, **kwargs)

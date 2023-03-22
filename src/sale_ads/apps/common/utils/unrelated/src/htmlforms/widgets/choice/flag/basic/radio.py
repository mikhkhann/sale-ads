class RadioWidgetLibMixin:
    element_mixin_getters = {"RadioWidget": "get_radio_widget_mixins"}
    tags = ("radio_widget",)

    class RadioWidgetMixin:
        type = "radio"

    @classmethod
    def get_radio_widget_mixins(cls):
        return [cls.RadioWidgetMixin, *cls.get_flag_widget_mixins()]

    @classmethod
    def base_radio_widget(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget(__element_object_class, *args, **kwargs)

    @classmethod
    def radio_widget(cls, *args, **kwargs):
        return cls.base_radio_widget(cls.RadioWidget, *args, **kwargs)

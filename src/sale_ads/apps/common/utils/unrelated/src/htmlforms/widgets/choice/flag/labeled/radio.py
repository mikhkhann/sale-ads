class LabeledRadioWidgetLibMixin:
    element_mixin_getters = {"LabeledRadioWidget": "get_labeled_radio_widget_mixins"}
    tags = ("labeled_radio_widget",)

    class LabeledRadioWidgetMixin:
        widget_element_object_class_name = "RadioWidget"
        label_element_object_class_name = "RadioLabel"

    @classmethod
    def get_labeled_radio_widget_mixins(cls):
        return [cls.LabeledRadioWidgetMixin, *cls.get_labeled_flag_widget_mixins()]

    @classmethod
    def base_labeled_radio_widget(cls, __element_object_class, *args, **kwargs):
        return cls.labeled_flag_widget(__element_object_class, *args, **kwargs)

    @classmethod
    def labeled_radio_widget(cls, *args, **kwargs):
        return cls.base_labeled_radio_widget(cls.LabeledRadioWidget, *args, **kwargs)

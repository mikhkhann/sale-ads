class LabeledCheckboxWidgetLibMixin:
    element_mixin_getters = {
        "LabeledCheckboxWidget": "get_labeled_checkbox_widget_mixins"
    }
    tags = ("labeled_checkbox_widget",)

    class LabeledCheckboxWidgetMixin:
        widget_element_object_class_name = "CheckboxWidget"
        label_element_object_class_name = "CheckboxLabel"

    @classmethod
    def get_labeled_checkbox_widget_mixins(cls):
        return [cls.LabeledCheckboxWidgetMixin, *cls.get_labeled_flag_widget_mixins()]

    @classmethod
    def base_labeled_checkbox_widget(cls, __element_object_class, *args, **kwargs):
        return cls.labeled_flag_widget(__element_object_class, *args, **kwargs)

    @classmethod
    def labeled_checkbox_widget(cls, *args, **kwargs):
        return cls.base_labeled_checkbox_widget(
            cls.LabeledCheckboxWidget, *args, **kwargs
        )

class LabeledBooleanWidgetLibMixin:
    element_mixin_getters = {
        "LabeledBooleanWidget": "get_labeled_boolean_widget_mixins"
    }
    tags = ("labeled_boolean_widget",)

    class LabeledBooleanWidgetMixin:
        widget_element_object_class_name = "BooleanWidget"
        label_element_object_class_name = "BooleanWidgetLabel"

    @classmethod
    def get_labeled_boolean_widget_mixins(cls):
        return [
            cls.LabeledBooleanWidgetMixin,
            *cls.get_labeled_checkbox_widget_mixins(),
        ]

    @classmethod
    def base_labeled_boolean_widget(
        cls, __element_object_class, field="", *args, **kwargs
    ):
        return cls.base_labeled_checkbox_widget(
            __element_object_class, *args, field=field, **kwargs
        )

    @classmethod
    def labeled_boolean_widget(cls, *args, **kwargs):
        return cls.base_labeled_boolean_widget(
            cls.LabeledBooleanWidget, *args, **kwargs
        )

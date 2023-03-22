class BooleanWidgetLabelLibMixin:
    element_mixin_getters = {"BooleanWidgetLabel": "get_boolean_widget_label_mixins"}
    tags = ("boolean_widget_label",)

    class BooleanWidgetLabelMixin:
        pass

    @classmethod
    def get_boolean_widget_label_mixins(cls):
        return [cls.BooleanWidgetLabelMixin, *cls.get_checkbox_label_mixins()]

    @classmethod
    def base_boolean_widget_label(cls, __element_object_class, *args, **kwargs):
        return cls.base_checkbox_label(__element_object_class, *args, **kwargs)

    @classmethod
    def boolean_widget_label(cls, *args, **kwargs):
        return cls.base_boolean_widget_label(cls.BooleanWidgetLabel, *args, **kwargs)

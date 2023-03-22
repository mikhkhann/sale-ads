class BooleanWidgetLibMixin:
    element_mixin_getters = {"BooleanWidget": "get_boolean_widget_mixins"}
    tags = ("boolean_widget",)

    class BooleanWidgetMixin:
        def add_checked_attr(self, attrs):
            if self.context.value:
                attrs["checked"] = None

    @classmethod
    def get_boolean_widget_mixins(cls):
        return [cls.BooleanWidgetMixin, *cls.get_checkbox_widget_mixins()]

    @classmethod
    def base_boolean_widget(cls, __element_object_class, field="", *args, **kwargs):
        return cls.base_checkbox_widget(
            __element_object_class, *args, field=field, **kwargs
        )

    @classmethod
    def boolean_widget(cls, *args, **kwargs):
        return cls.base_boolean_widget(cls.BooleanWidget, *args, **kwargs)

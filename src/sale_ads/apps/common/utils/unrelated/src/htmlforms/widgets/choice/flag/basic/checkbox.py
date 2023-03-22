class CheckboxWidgetLibMixin:
    element_mixin_getters = {"CheckboxWidget": "get_checkbox_widget_mixins"}
    tags = ("checkbox_widget",)

    class CheckboxWidgetMixin:
        type = "checkbox"

        def add_required_attr(self, attrs):
            if self.context.checkbox_required is not None:
                if self.context.checkbox_required:
                    attrs["required"] = None
            else:
                super().add_required_attr(attrs)

    @classmethod
    def get_checkbox_widget_mixins(cls):
        return [cls.CheckboxWidgetMixin, *cls.get_flag_widget_mixins()]

    class ContextMixin:
        items = ("checkbox_required",)

        def clean_checkbox_required(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_checkbox_widget(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget(__element_object_class, *args, **kwargs)

    @classmethod
    def checkbox_widget(cls, *args, **kwargs):
        return cls.base_checkbox_widget(cls.CheckboxWidget, *args, **kwargs)

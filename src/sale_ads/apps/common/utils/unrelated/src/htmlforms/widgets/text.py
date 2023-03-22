class TextWidgetLibMixin:
    element_mixin_getters = {"TextWidget": "get_text_widget_mixins"}
    tags = ("text_widget",)

    class TextWidgetMixin:
        tag = "input"
        close = False

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_autocomplete_attr(attrs)
            self.add_maxlength_attr(attrs)
            self.add_minlength_attr(attrs)
            self.add_name_attr(attrs)
            self.add_placeholder_attr(attrs)
            self.add_required_attr(attrs)
            attrs["type"] = "text"
            self.add_value_attr(attrs)
            return attrs

    @classmethod
    def get_text_widget_mixins(cls):
        return [cls.TextWidgetMixin, *cls.get_widget_mixins()]

    @classmethod
    def base_text_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def text_widget(cls, *args, **kwargs):
        return cls.base_text_widget(cls.TextWidget, *args, **kwargs)

class TextAreaWidgetLibMixin:
    element_mixin_getters = {"TextAreaWidget": "get_textarea_widget_mixins"}
    tags = ("textarea_widget",)

    class TextAreaWidgetMixin:
        tag = "textarea"
        default_rows = None

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_maxlength_attr(attrs)
            self.add_minlength_attr(attrs)
            self.add_name_attr(attrs)
            self.add_required_attr(attrs)
            self.add_rows_attr(attrs)
            return attrs

        def add_rows_attr(self, attrs):
            rows = (
                self.context.rows
                if self.context.rows is not None
                else self.default_rows
            )
            if rows is not None:
                attrs["rows"] = rows

        def get_content(self):
            return self.context.safe_value

    @classmethod
    def get_textarea_widget_mixins(cls):
        return [cls.TextAreaWidgetMixin, *cls.get_widget_mixins()]

    class ContextMixin:
        items = ("rows",)

    @classmethod
    def base_textarea_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def textarea_widget(cls, *args, **kwargs):
        return cls.base_textarea_widget(cls.TextAreaWidget, *args, **kwargs)

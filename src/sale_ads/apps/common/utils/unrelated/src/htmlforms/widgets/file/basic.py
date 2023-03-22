class FileWidgetLibMixin:
    element_mixin_getters = {"FileWidget": "get_file_widget_mixins"}
    tags = ("file_widget",)

    class FileWidgetMixin:
        tag = "input"
        close = False

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_accept_attr(attrs)
            self.add_name_attr(attrs)
            self.add_required_attr(attrs)
            attrs["type"] = "file"
            return attrs

        def add_accept_attr(self, attrs):
            if self.context.accept:
                attrs["accept"] = self.context.accept

    @classmethod
    def get_file_widget_mixins(cls):
        return [cls.FileWidgetMixin, *cls.get_widget_mixins()]

    class ContextMixin:
        items = ("accept",)

    @classmethod
    def base_file_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def file_widget(cls, *args, **kwargs):
        return cls.base_file_widget(cls.FileWidget, *args, **kwargs)

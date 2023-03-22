class FileFieldLibMixin:
    element_mixin_getters = {"FileField": "get_file_field_mixins"}
    tags = ("file_field",)

    class FileFieldMixin:
        widget_element_object_class_name = "FileWidget"
        clearable_widget_element_object_class_name = "ClearableFileWidget"

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.clearable_widget_element_object_class_name:
                cls.clearable_widget_element_object_class = (
                    cls.lib.get_element_object_class(
                        cls.clearable_widget_element_object_class_name
                    )
                )

        def get_widget_content(self):
            return (
                self.get_unclearable_widget_content()
                if not self.context.clearable_file
                else self.get_clearable_widget_content()
            )

        def get_unclearable_widget_content(self):
            return super().get_widget_content()

        def get_clearable_widget_content(self):
            widget = self.create_child(self.clearable_widget_element_object_class)
            return widget.render()

    @classmethod
    def get_file_field_mixins(cls):
        return [cls.FileFieldMixin, *cls.get_field_mixins()]

    class ContextMixin:
        items = ("clearable_file",)

        def clean_clearable_file(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_file_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def file_field(cls, *args, **kwargs):
        return cls.base_file_field(cls.FileField, *args, **kwargs)

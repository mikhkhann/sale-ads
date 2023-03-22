class FileRemovalSubwidgetLibMixin:
    element_mixin_getters = {
        "FileRemovalSubwidget": "get_file_removal_subwidget_mixins"
    }
    tags = ("file_removal_subwidget",)

    class FileRemovalSubwidgetMixin:
        css_class_context_item = "file_removal_subwidget_class"
        css_extra_class_context_item = "file_removal_subwidget_extra_class"
        invalid_css_class_context_item = "file_removal_subwidget_invalid_class"
        extra_invalid_css_class_context_item = (
            "file_removal_subwidget_extra_invalid_class"
        )

        def add_checked_attr(self, attrs):
            if self.context.file_removal_subwidget_checked:
                attrs["checked"] = None

        def add_name_attr(self, attrs):
            if self.context.file_removal_subwidget_name:
                attrs["name"] = self.context.file_removal_subwidget_name

        def add_required_attr(self, attrs):
            if self.context.file_removal_subwidget_required:
                attrs["required"] = None

    @classmethod
    def get_file_removal_subwidget_mixins(cls):
        return [cls.FileRemovalSubwidgetMixin, *cls.get_boolean_widget_mixins()]

    class ContextMixin:
        items = (
            "file_removal_subwidget_checked",
            "file_removal_subwidget_name",
            "file_removal_subwidget_required",
            "removable_file_field",
            "removable_file_field_name",
            "file_removal_subwidget_class",
            "file_removal_subwidget_extra_class",
            "file_removal_subwidget_invalid_class",
            "file_removal_subwidget_extra_invalid_class",
        )

        def clean_file_removal_subwidget_checked(self, value):
            return self.clean_bool(value)

        def compute_file_removal_subwidget_name(self):
            if not self.is_inherited("removable_file_field_name"):
                return (
                    self.removable_file_field_name + "-clear"
                    if self.removable_file_field_name
                    else None
                )
            raise self.ItemComputationFailed

        def clean_file_removal_subwidget_required(self, value):
            return self.clean_bool(value)

        def compute_removable_file_field_name(self):
            if not self.is_inherited("removable_file_field"):
                return (
                    self.removable_file_field.html_name
                    if self.removable_file_field
                    else None
                )
            raise self.ItemComputationFailed

    @classmethod
    def base_file_removal_subwidget(
        cls, _element_object_class, removable_file_field="", *args, **kwargs
    ):
        return cls.base_boolean_widget(
            _element_object_class,
            *args,
            removable_file_field=removable_file_field,
            **kwargs
        )

    @classmethod
    def file_removal_subwidget(cls, *args, **kwargs):
        return cls.base_file_removal_subwidget(
            cls.FileRemovalSubwidget, *args, **kwargs
        )

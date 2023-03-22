class LabeledFileRemovalSubwidgetLibMixin:
    element_mixin_getters = {
        "LabeledFileRemovalSubwidget": "get_labeled_file_removal_subwidget_mixins"
    }
    tags = ("labeled_file_removal_subwidget",)

    class LabeledFileRemovalSubwidgetMixin:
        widget_element_object_class_name = "FileRemovalSubwidget"
        label_element_object_class_name = "FileRemovalSubwidgetLabel"

    @classmethod
    def get_labeled_file_removal_subwidget_mixins(cls):
        return [
            cls.LabeledFileRemovalSubwidgetMixin,
            *cls.get_labeled_boolean_widget_mixins(),
        ]

    @classmethod
    def base_labeled_file_removal_subwidget(
        cls, __element_object_class, removable_file_field="", *args, **kwargs
    ):
        return cls.base_labeled_boolean_widget(
            __element_object_class,
            *args,
            removable_file_field=removable_file_field,
            **kwargs
        )

    @classmethod
    def labeled_file_removal_subwidget(cls, *args, **kwargs):
        return cls.base_labeled_file_removal_subwidget(
            cls.LabeledFileRemovalSubwidget, *args, **kwargs
        )

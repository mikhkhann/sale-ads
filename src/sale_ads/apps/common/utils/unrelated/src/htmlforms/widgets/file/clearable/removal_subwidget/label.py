from django.utils.translation import pgettext_lazy


class FileRemovalSubwidgetLabelLibMixin:
    element_mixin_getters = {
        "FileRemovalSubwidgetLabel": "get_file_removal_subwidget_label_mixins"
    }
    tags = ("file_removal_subwidget_label",)

    class FileRemovalSubwidgetLabelMixin:
        default_label = pgettext_lazy("file removal sibwidget label", "Clear")

        def get_label(self):
            label = super().get_label()
            return label if label else self.default_label

    @classmethod
    def get_file_removal_subwidget_label_mixins(cls):
        return [
            cls.FileRemovalSubwidgetLabelMixin,
            *cls.get_boolean_widget_label_mixins(),
        ]

    @classmethod
    def base_file_removal_subwidget_label(cls, __element_object_class, *args, **kwargs):
        return cls.base_boolean_widget_label(__element_object_class, *args, **kwargs)

    @classmethod
    def file_removal_subwidget_label(cls, *args, **kwargs):
        return cls.base_file_removal_subwidget_label(
            cls.FileRemovalSubwidgetLabel, *args, **kwargs
        )

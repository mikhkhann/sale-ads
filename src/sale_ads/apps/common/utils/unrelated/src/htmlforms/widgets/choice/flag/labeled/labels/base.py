from functools import cached_property


class FlagWidgetLabelLibMixin:
    class FlagWidgetLabelMixin:
        tag = "label"
        css_class_context_item = "flag_widget_label_class"
        css_extra_class_context_item = "flag_widget_label_extra_class"

        def get_content(self):
            return self.label

        @cached_property
        def label(self):
            return self.get_label()

        def get_label(self):
            return self.context.choice_label

    @classmethod
    def get_flag_widget_label_mixins(cls):
        return [cls.FlagWidgetLabelMixin]

    class ContextMixin:
        items = ("flag_widget_label_class", "flag_widget_label_extra_class")

    @classmethod
    def flag_widget_label(cls, __element_object_class, choice_label="", **kwargs):
        label = cls.create_element(
            __element_object_class, choice_label=choice_label, **kwargs
        )
        return label.render() if label.label else ""

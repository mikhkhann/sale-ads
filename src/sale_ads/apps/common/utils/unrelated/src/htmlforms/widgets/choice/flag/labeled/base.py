from django.utils.html import conditional_escape


class LabeledFlagWidgetLibMixin:
    class LabeledFlagWidgetMixin:
        tag = "div"
        css_class_context_item = "labeled_flag_widget_class"
        css_extra_class_context_item = "labeled_flag_widget_extra_class"
        widget_element_object_class_name = None
        label_element_object_class_name = None

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.widget_element_object_class_name:
                cls.widget_element_object_class = cls.lib.get_element_object_class(
                    cls.widget_element_object_class_name
                )
            if cls.label_element_object_class_name:
                cls.label_element_object_class = cls.lib.get_element_object_class(
                    cls.label_element_object_class_name
                )

        def get_content(self):
            content = conditional_escape(self.get_widget_content())
            label = self.get_label_content()
            if label:
                content += conditional_escape(label)
            return content

        def get_widget_content(self):
            return self.create_child(self.widget_element_object_class).render()

        def get_label_content(self):
            label = self.create_child(self.label_element_object_class)
            return label.render() if label.label else None

    @classmethod
    def get_labeled_flag_widget_mixins(cls):
        return [cls.LabeledFlagWidgetMixin]

    class ContextMixin:
        items = ("labeled_flag_widget_class", "labeled_flag_widget_extra_class")

    @classmethod
    def labeled_flag_widget(
        cls, __element_object_class, name="", choice_value="", choice_label="", **kwargs
    ):
        widget = cls.create_element(
            __element_object_class,
            choice_label=choice_label,
            choice_value=choice_value,
            name=name,
            **kwargs
        )
        return widget.render()

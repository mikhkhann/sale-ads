from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class FlagWidgetListLibMixin:
    class FlagWidgetListMixin:
        tag = "div"
        css_class_context_item = "flag_widget_list_class"
        css_extra_class_context_item = "flag_widget_list_extra_class"
        choice_element_object_class_name = None

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.choice_element_object_class_name:
                cls.choice_element_object_class = cls.lib.get_element_object_class(
                    cls.choice_element_object_class_name
                )

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            extra_widget_kwargs = self.get_extra_widget_kwargs()
            for value, label in self.context.safe_choices or ():
                content += conditional_escape(
                    self.get_choice_content(value, label, extra_widget_kwargs)
                )
            return content

        def get_extra_widget_kwargs(self):
            return {}

        def get_choice_content(self, value, label, extra_widget_kwargs):
            choice = self.create_child(
                self.choice_element_object_class,
                choice_value=value,
                choice_label=label,
                **extra_widget_kwargs
            )
            return choice.render()

    @classmethod
    def get_flag_widget_list_mixins(cls):
        return [cls.FlagWidgetListMixin]

    class ContextMixin:
        items = ("flag_widget_list_class", "flag_widget_list_extra_class")

    @classmethod
    def flag_widget_list(cls, __element_object_class, field="", **kwargs):
        flag_widget_list = cls.create_element(
            __element_object_class, field=field, **kwargs
        )
        return flag_widget_list.render() if flag_widget_list.context.choices else ""

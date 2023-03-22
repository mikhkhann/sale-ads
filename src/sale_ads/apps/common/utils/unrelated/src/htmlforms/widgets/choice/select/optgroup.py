from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class SelectOptgroupLibMixin:
    element_mixin_getters = {"SelectOptgroup": "get_select_optgroup_mixins"}
    tags = ("select_optgroup",)

    class SelectOptgroupMixin:
        tag = "optgroup"
        css_class_context_item = "select_optgroup_class"
        css_extra_class_context_item = "select_optgroup_extra_class"
        choice_element_object_class_name = "SelectOption"

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.choice_element_object_class_name:
                cls.choice_element_object_class = cls.lib.get_element_object_class(
                    cls.choice_element_object_class_name
                )

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_label_attr(attrs)
            return attrs

        def add_label_attr(self, attrs):
            if self.context.choice_group_label is not None:
                attrs["label"] = self.context.choice_group_label

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            for value, label in self.context.choice_group or ():
                content += conditional_escape(self.get_choice_content(value, label))
            return content

        def get_choice_content(self, value, label):
            choice = self.create_child(
                self.choice_element_object_class, choice_value=value, choice_label=label
            )
            return choice.render()

    @classmethod
    def get_select_optgroup_mixins(cls):
        return [cls.SelectOptgroupMixin]

    class ContextMixin:
        items = (
            "choice_group",
            "choice_group_label",
            "select_optgroup_class",
            "select_optgroup_extra_class",
        )

    @classmethod
    def base_select_optgroup(cls, __element_object_class, **kwargs):
        optgroup = cls.create_element(__element_object_class, **kwargs)
        return optgroup.render() if optgroup.context.choice_group else ""

    @classmethod
    def select_optgroup(cls, *args, **kwargs):
        return cls.base_select_optgroup(cls.SelectOptgroup, *args, **kwargs)

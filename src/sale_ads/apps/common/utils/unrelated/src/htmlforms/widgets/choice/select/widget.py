from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class SelectWidgetLibMixin:
    element_mixin_getters = {"SelectWidget": "get_select_widget_mixins"}
    tags = ("select_widget",)

    class SelectWidgetMixin:
        tag = "select"
        choice_element_object_class_name = "SelectOption"
        choice_group_element_object_class_name = "SelectOptgroup"

        @classmethod
        def init_class(cls):
            super().init_class()
            if cls.choice_element_object_class_name:
                cls.choice_element_object_class = cls.lib.get_element_object_class(
                    cls.choice_element_object_class_name
                )
            if cls.choice_group_element_object_class_name:
                cls.choice_group_element_object_class = (
                    cls.lib.get_element_object_class(
                        cls.choice_group_element_object_class_name
                    )
                )

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_multiple_attr(attrs)
            self.add_name_attr(attrs)
            self.add_required_attr(attrs)
            return attrs

        def add_multiple_attr(self, attrs):
            if self.context.multi_choice:
                attrs["multiple"] = None

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            if (
                not self.context.multi_choice
                and (self.context.blank_select or self.context.blank_select is None)
            ):  # fmt: skip
                content += conditional_escape(self.get_blank_choice_content())
            for left, right in self.context.safe_choices or ():
                content += conditional_escape(
                    (
                        self.get_choice_content
                        if not isinstance(right, (list, tuple))
                        else self.get_choice_group_content
                    )(left, right)
                )
            return content

        def get_blank_choice_content(self):
            element = self.create_child(
                self.choice_element_object_class, select_option_hidden=True
            )
            return element.render()

        def get_choice_content(self, value, label):
            choice = self.create_child(
                self.choice_element_object_class, choice_value=value, choice_label=label
            )
            return choice.render()

        def get_choice_group_content(self, label, group):
            group = self.create_child(
                self.choice_group_element_object_class,
                choice_group_label=label,
                choice_group=group,
            )
            return group.render()

    @classmethod
    def get_select_widget_mixins(cls):
        return [cls.SelectWidgetMixin, *cls.get_widget_mixins()]

    class ContextMixin:
        items = ("blank_select",)

        def compute_blank_select(self):
            if not self.is_inherited("choices") or not self.is_inherited("value"):
                return (
                    self.string_value
                    not in _iter_choice_options(self.safe_choices or ())
                    if self.value is not None
                    else None
                )
            raise self.ItemComputationFailed

        def clean_blank_select(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_select_widget(cls, __element_object_class, field="", **kwargs):
        widget = cls.create_element(__element_object_class, field=field, **kwargs)
        return widget.render() if widget.context.choices else ""

    @classmethod
    def select_widget(cls, *args, **kwargs):
        return cls.base_select_widget(cls.SelectWidget, *args, **kwargs)


def _iter_choice_options(choices):
    for left, right in choices:
        if not isinstance(right, tuple):
            yield left
        else:
            nested_values, nested_labels = zip(*right)
            yield from nested_values

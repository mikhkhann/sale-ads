class SelectOptionLibMixin:
    element_mixin_getters = {"SelectOption": "get_select_option_mixins"}
    tags = ("select_option",)

    class SelectOptionMixin:
        tag = "option"

        css_class_context_item = "select_option_class"
        css_extra_class_context_item = "select_option_extra_class"

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_hidden_attr(attrs)
            self.add_selected_attr(attrs)
            self.add_value_attr(attrs)
            return attrs

        def add_hidden_attr(self, attrs):
            if self.context.select_option_hidden:
                attrs["hidden"] = None

        def add_selected_attr(self, attrs):
            if self.context.chosen:
                attrs["selected"] = None

        def add_value_attr(self, attrs):
            if self.context.choice_value is not None:
                attrs["value"] = self.context.safe_choice_value

        def get_content(self):
            return self.context.choice_label

    @classmethod
    def get_select_option_mixins(cls):
        return [cls.SelectOptionMixin]

    class ContextMixin:
        items = (
            "select_option_hidden",
            "select_option_class",
            "select_option_extra_class",
        )

        def clean_select_option_hidden(self, value):
            return self.clean_bool(value)

    @classmethod
    def base_select_option(cls, __element_object_class, choice_value="", **kwargs):
        option = cls.create_element(
            __element_object_class, choice_value=choice_value, **kwargs
        )
        return option.render()

    @classmethod
    def select_option(cls, *args, **kwargs):
        return cls.base_select_option(cls.SelectOption, *args, **kwargs)

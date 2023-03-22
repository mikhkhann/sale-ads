class FlagWidgetLibMixin:
    class FlagWidgetMixin:
        tag = "input"
        close = False

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_checked_attr(attrs)
            self.add_name_attr(attrs)
            self.add_required_attr(attrs)
            attrs["type"] = self.type
            self.add_value_attr(attrs)
            return attrs

        def add_checked_attr(self, attrs):
            if self.context.chosen:
                attrs["checked"] = None

        def add_value_attr(self, attrs):
            if self.context.choice_value is not None:
                attrs["value"] = self.context.safe_choice_value

    @classmethod
    def get_flag_widget_mixins(cls):
        return [cls.FlagWidgetMixin, *cls.get_widget_mixins()]

    @classmethod
    def flag_widget(cls, __element_object_class, name="", choice_value="", **kwargs):
        widget = cls.create_element(
            __element_object_class, choice_value=choice_value, name=name, **kwargs
        )
        return widget.render()

class SearchWidgetLibMixin:
    element_mixin_getters = {"SearchWidget": "get_search_widget_mixins"}
    tags = ("search_widget",)

    class SearchWidgetMixin:
        tag = "input"
        close = False

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_autocomplete_attr(attrs)
            self.add_maxlength_attr(attrs)
            self.add_minlength_attr(attrs)
            self.add_name_attr(attrs)
            self.add_placeholder_attr(attrs)
            self.add_required_attr(attrs)
            attrs["type"] = "search"
            self.add_value_attr(attrs)
            return attrs

    @classmethod
    def get_search_widget_mixins(cls):
        return [cls.SearchWidgetMixin, *cls.get_widget_mixins()]

    @classmethod
    def base_search_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def search_widget(cls, *args, **kwargs):
        return cls.base_search_widget(cls.SearchWidget, *args, **kwargs)

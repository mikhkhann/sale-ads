class PasswordWidgetLibMixin:
    element_mixin_getters = {"PasswordWidget": "get_password_widget_mixins"}
    tags = ("password_widget",)

    class PasswordWidgetMixin:
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
            attrs["type"] = "password"
            return attrs

    @classmethod
    def get_password_widget_mixins(cls):
        return [cls.PasswordWidgetMixin, *cls.get_widget_mixins()]

    @classmethod
    def base_password_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def password_widget(cls, *args, **kwargs):
        return cls.base_password_widget(cls.PasswordWidget, *args, **kwargs)

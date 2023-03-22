class CheckboxListLibMixin:
    element_mixin_getters = {"CheckboxList": "get_checkbox_list_mixins"}
    tags = ("checkbox_list",)

    class CheckboxListMixin:
        choice_element_object_class_name = "LabeledCheckboxWidget"

        def get_extra_widget_kwargs(self):
            kwargs = super().get_extra_widget_kwargs()
            kwargs["checkbox_required"] = (
                self.context.checkbox_required
                if self.context.checkbox_required is not None
                else False
            )
            return kwargs

    @classmethod
    def get_checkbox_list_mixins(cls):
        return [cls.CheckboxListMixin, *cls.get_flag_widget_list_mixins()]

    @classmethod
    def base_checkbox_list(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_list(__element_object_class, *args, **kwargs)

    @classmethod
    def checkbox_list(cls, *args, **kwargs):
        return cls.base_checkbox_list(cls.CheckboxList, *args, **kwargs)

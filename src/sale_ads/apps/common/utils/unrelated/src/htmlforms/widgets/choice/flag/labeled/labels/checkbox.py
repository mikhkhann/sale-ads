class CheckboxLabelLibMixin:
    element_mixin_getters = {"CheckboxLabel": "get_checkbox_label_mixins"}
    tags = ("checkbox_label",)

    class CheckboxLabelMixin:
        pass

    @classmethod
    def get_checkbox_label_mixins(cls):
        return [cls.CheckboxLabelMixin, *cls.get_flag_widget_label_mixins()]

    @classmethod
    def base_checkbox_label(cls, __element_object_class, *args, **kwargs):
        return cls.flag_widget_label(__element_object_class, *args, **kwargs)

    @classmethod
    def checkbox_label(cls, *args, **kwargs):
        return cls.base_checkbox_label(cls.CheckboxLabel, *args, **kwargs)

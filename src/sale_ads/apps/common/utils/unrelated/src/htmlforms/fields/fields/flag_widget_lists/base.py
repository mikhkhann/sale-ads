class FlagWidgetListFieldLibMixin:
    class FlagWidgetListFieldMixin:
        pass

    @classmethod
    def get_flag_widget_list_field_mixins(cls):
        return [cls.FlagWidgetListFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def flag_widget_list_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

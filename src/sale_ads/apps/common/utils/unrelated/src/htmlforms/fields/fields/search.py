class SearchFieldLibMixin:
    element_mixin_getters = {"SearchField": "get_search_field_mixins"}
    tags = ("search_field",)

    class SearchFieldMixin:
        widget_element_object_class_name = "SearchWidget"

    @classmethod
    def get_search_field_mixins(cls):
        return [cls.SearchFieldMixin, *cls.get_field_mixins()]

    @classmethod
    def base_search_field(cls, __element_object_class, *args, **kwargs):
        return cls.field(__element_object_class, *args, **kwargs)

    @classmethod
    def search_field(cls, *args, **kwargs):
        return cls.base_search_field(cls.SearchField, *args, **kwargs)

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

_SAFE_EMPTY_STRING = mark_safe("")


class HiddenFieldListLibMixin:
    element_mixin_getters = {"HiddenFieldList": "get_hidden_field_list_mixins"}
    tags = ("hidden_fields",)

    class HiddenFieldListMixin:
        tag = "div"

        def get_content(self):
            content = _SAFE_EMPTY_STRING
            for field in self.context.hidden_fields or ():
                content += conditional_escape(field)
            return content

    @classmethod
    def get_hidden_field_list_mixins(cls):
        return [cls.HiddenFieldListMixin]

    class ContextMixin:
        items = ("hidden_fields",)

        def compute_hidden_fields(self):
            if not self.is_inherited("form"):
                return self.form.hidden_fields() if self.form else None
            raise self.ItemComputationFailed

    @classmethod
    def base_hidden_fields(cls, __element_object_class, form="", **kwargs):
        element = cls.create_element(__element_object_class, form=form, **kwargs)
        return element.render() if element.context.hidden_fields else ""

    @classmethod
    def hidden_fields(cls, *args, **kwargs):
        return cls.base_hidden_fields(cls.HiddenFieldList, *args, **kwargs)

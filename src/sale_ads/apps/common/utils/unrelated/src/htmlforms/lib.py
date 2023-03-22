from inspect import getmro

from htmlforms.context import BaseContext
from htmlforms.element import Element
from htmlforms.fields import FIELD_LIB_MIXINS
from htmlforms.forms import FORM_LIB_MIXINS
from htmlforms.widgets import WIDGET_LIB_MIXINS


class _BaseHTMLFormsLib:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._element_mixins = cls.get_element_mixins()
        cls._element_object_classes = {}
        cls.create_element_classes()
        cls.Context = type("Context", (*cls.get_context_mixins(), BaseContext), {})

    @classmethod
    def get_element_mixins(cls):
        mixins = {}
        for class_in_mro in getmro(cls):
            try:
                getters = getattr(class_in_mro, "element_mixin_getters")
            except AttributeError:
                continue
            for element_name, getter_name in getters.items():
                if element_name not in mixins:
                    mixins[element_name] = getattr(cls, getter_name)()
        return mixins

    @classmethod
    def create_element_classes(cls):
        for name in cls._element_mixins:
            setattr(cls, name, cls.get_element_object_class(name))

    @classmethod
    def get_context_mixins(cls):
        mixins = set()
        for class_in_mro in getmro(cls):
            try:
                mixin = getattr(class_in_mro, "ContextMixin")
            except AttributeError:
                continue
            mixins.add(mixin)
        return mixins

    Element = Element

    class ElementMixin:
        pass

    @classmethod
    def get_element_object_class(cls, name):
        try:
            return cls._element_object_classes[name]
        except KeyError:
            mixins = cls._element_mixins[name]
            element_class = type(
                name, (*mixins, cls.ElementMixin, cls.Element), {}, lib=cls
            )
            cls._element_object_classes[name] = element_class
            setattr(cls, name, element_class)
            return element_class

    @classmethod
    def create_element(cls, element_class, **kwargs):
        return element_class(parent=None, **kwargs)

    @classmethod
    def update_register(cls, register):
        for name in cls.get_tag_names():
            cls.add_tag(register, name)

    @classmethod
    def get_tag_names(cls):
        names = set()
        for class_in_mro in getmro(cls):
            names.update(getattr(class_in_mro, "tags", ()))
        return names

    @classmethod
    def add_tag(cls, register, name):
        method = getattr(cls, name)
        tag = lambda *args, **kwargs: method(*args, **kwargs)
        register.simple_tag(tag, name=name)


class HTMLFormsLib(
    *FIELD_LIB_MIXINS, *FORM_LIB_MIXINS, *WIDGET_LIB_MIXINS, _BaseHTMLFormsLib
):
    pass

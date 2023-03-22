from functools import cached_property
from inspect import getmro


class BaseContext:
    items = (
        "error",
        "field",
        "field_errors",
        "required",
        "error_class",
        "error_extra_class",
        "error_list_class",
        "error_list_extra_class",
    )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.item_cleaners = {}
        for name in cls.get_item_names():
            cls.create_item_descriptor(name)

    @classmethod
    def get_item_names(cls):
        names = set()
        for class_in_mro in getmro(cls):
            names.update(getattr(class_in_mro, "items", ()))
        return names

    @classmethod
    def create_item_descriptor(cls, name):
        compute_method_name = "compute_" + name
        try:
            compute = getattr(cls, compute_method_name)
        except AttributeError:
            setattr(cls, compute_method_name, cls.default_compute)
            compute = cls.default_compute

        internal_name = "_" + name

        def get(self):
            try:
                return getattr(self, internal_name)
            except AttributeError:
                try:
                    value = compute(self)
                except cls.ItemComputationFailed:
                    if self._parent:
                        value = getattr(self._parent, name)
                        self._inherited.add(name)
                    else:
                        value = None
                setattr(self, internal_name, value)
                return value

        descriptor = property(get)
        setattr(cls, name, descriptor)
        descriptor.__set_name__(cls, name)

        clean_method_name = "clean_" + name
        try:
            clean = getattr(cls, clean_method_name)
        except AttributeError:
            setattr(cls, clean_method_name, cls.default_clean)
            clean = cls.default_clean
        cls.item_cleaners[name] = clean

    def __init__(self, *, element, **items):
        self.element = element
        for name, value in items.items():
            if value != "":
                setattr(self, "_" + name, self.item_cleaners[name](self, value))
        self._inherited = set()

    @cached_property
    def _parent(self):
        return getattr(self.element.parent, "context", None)

    def is_inherited(self, name):
        getattr(self, name)
        return name in self._inherited

    class ItemComputationFailed(Exception):
        pass

    def default_compute(self):
        raise self.ItemComputationFailed

    def clean_bool(self, value):
        if isinstance(value, bool):
            return value
        raise TypeError(
            "The value to be set must be a `bool` instance, not "
            f"`{type(value).__name__}`."
        )

    def default_clean(self, value):
        return value

    def compute_field_errors(self):
        if not self.is_inherited("field"):
            return self.field.errors if self.field else None
        raise self.ItemComputationFailed

    def compute_required(self):
        if not self.is_inherited("field"):
            return self.field.field.required if self.field else None
        raise self.ItemComputationFailed

    def clean_required(self, value):
        return self.clean_bool(value)

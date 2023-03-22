from types import MappingProxyType


class TestModelObjectFactory:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "model"):
            cls.field_names = frozenset(
                field.name for field in cls.model._meta.get_fields()
            )
            creatable_field_defaults = {}
            for attr_name in dir(cls):
                if attr_name.startswith("create_default_"):
                    field_name = attr_name.removeprefix("create_default_")
                    assert field_name in cls.field_names
                    creatable_field_defaults[field_name] = getattr(cls, attr_name)
            cls.creatable_field_defaults = MappingProxyType(creatable_field_defaults)

    def __init__(self, *, not_create=(), **field_defaults):
        assert field_defaults.keys() <= self.field_names
        self.field_defaults = field_defaults
        self.create_field_defaults(not_create)

    def create_field_defaults(self, not_create):
        assert set(not_create) <= self.creatable_field_defaults.keys()
        for name, create in self.creatable_field_defaults.items():
            if name not in self.field_defaults and name not in not_create:
                self.field_defaults[name] = create(self)

    def create(self, *args, save=True, **field_values):
        self.add_field_defaults(field_values)
        obj = self.model(*args, **field_values)
        if save:
            obj.save()
        return obj

    def add_field_defaults(self, field_values):
        for attr_name in dir(self):
            if attr_name.startswith("default_"):
                name = attr_name.removeprefix("default_")
                assert name in self.field_names
                if name not in field_values:
                    field_values[name] = getattr(self, attr_name)
        for name, value in self.field_defaults.items():
            if name not in field_values:
                field_values[name] = value

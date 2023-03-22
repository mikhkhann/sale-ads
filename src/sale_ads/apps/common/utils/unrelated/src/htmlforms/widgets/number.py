from decimal import Decimal

from django import forms


class NumberWidgetLibMixin:
    element_mixin_getters = {"NumberWidget": "get_number_widget_mixins"}
    tags = ("number_widget",)

    class NumberWidgetMixin:
        tag = "input"
        close = False

        def get_attrs(self):
            attrs = super().get_attrs()
            self.add_autocomplete_attr(attrs)
            self.add_max_attr(attrs)
            self.add_min_attr(attrs)
            self.add_name_attr(attrs)
            self.add_placeholder_attr(attrs)
            self.add_required_attr(attrs)
            self.add_step_attr(attrs)
            attrs["type"] = "number"
            self.add_value_attr(attrs)
            return attrs

        def add_max_attr(self, attrs):
            if self.context.max is not None:
                attrs["max"] = self.context.max

        def add_min_attr(self, attrs):
            if self.context.min is not None:
                attrs["min"] = self.context.min

        def add_step_attr(self, attrs):
            if self.context.step:
                attrs["step"] = self.context.step

    @classmethod
    def get_number_widget_mixins(cls):
        return [cls.NumberWidgetMixin, *cls.get_widget_mixins()]

    class ContextMixin:
        items = ("max", "min", "step")

        def compute_max(self):
            if not self.is_inherited("field"):
                if self.field:
                    field = self.field.field
                    specified_max_value = getattr(field, "max_value", None)
                    calculated_max_value = (
                        self.calculate_decimal_field_max(field)
                        if isinstance(field, forms.DecimalField)
                        and field.max_digits is not None
                        else None
                    )
                    if specified_max_value is None and calculated_max_value is None:
                        value = None
                    elif specified_max_value is None:
                        value = calculated_max_value
                    elif calculated_max_value is None:
                        value = specified_max_value
                    else:
                        value = (
                            specified_max_value
                            if Decimal(specified_max_value)
                            <= Decimal(calculated_max_value)
                            else calculated_max_value
                        )
                    return (
                        self.normalize_decimal_limit(value)
                        if value is not None
                        else None
                    )
                return None
            raise self.ItemComputationFailed

        def clean_max(self, value):
            return self.normalize_decimal_limit(value) if value is not None else None

        def compute_min(self):
            if not self.is_inherited("field"):
                if self.field:
                    field = self.field.field
                    specified_min_value = getattr(field, "min_value", None)
                    calculated_min_value = (
                        "-" + self.calculate_decimal_field_max(field)
                        if isinstance(field, forms.DecimalField)
                        and field.max_digits is not None
                        else None
                    )
                    if specified_min_value is None and calculated_min_value is None:
                        value = None
                    elif specified_min_value is None:
                        value = calculated_min_value
                    elif calculated_min_value is None:
                        value = specified_min_value
                    else:
                        value = (
                            specified_min_value
                            if Decimal(specified_min_value)
                            >= Decimal(calculated_min_value)
                            else calculated_min_value
                        )
                    return (
                        self.normalize_decimal_limit(value)
                        if value is not None
                        else None
                    )
                return None
            raise self.ItemComputationFailed

        def clean_min(self, value):
            return self.normalize_decimal_limit(value) if value is not None else None

        def compute_step(self):
            if not self.is_inherited("field"):
                if self.field:
                    field = self.field.field
                    specified_step = getattr(field, "step_size", None)
                    if (
                        isinstance(field, forms.DecimalField)
                        and field.decimal_places is not None
                    ):
                        calculated_step = Decimal(10) ** -field.decimal_places
                    elif (
                        isinstance(field, forms.IntegerField)
                        and not isinstance(
                            field, (forms.FloatField, forms.DecimalField)
                        )
                    ):  # fmt: skip
                        calculated_step = 1
                    else:
                        calculated_step = None
                    if specified_step is None and calculated_step is None:
                        value = None
                    elif specified_step is None:
                        value = calculated_step
                    elif calculated_step is None:
                        value = specified_step
                    else:
                        value = (
                            specified_step
                            if Decimal(specified_step) >= Decimal(calculated_step)
                            else calculated_step
                        )
                    return (
                        self.normalize_decimal_limit(value)
                        if value is not None
                        else None
                    )
                return None
            raise self.ItemComputationFailed

        def clean_step(self, value):
            return self.normalize_decimal_limit(value) if value is not None else None

        def calculate_decimal_field_max(self, field):
            decimal_places = (
                field.decimal_places if field.decimal_places is not None else 0
            )
            max_value = "9" * (field.max_digits - decimal_places)
            if decimal_places:
                max_value += "." + "9" * decimal_places
            return max_value

        def normalize_decimal_limit(self, value):
            return Decimal(format(Decimal(value).normalize(), "f"))

    @classmethod
    def base_number_widget(cls, __element_object_class, *args, **kwargs):
        return cls.widget(__element_object_class, *args, **kwargs)

    @classmethod
    def number_widget(cls, *args, **kwargs):
        return cls.base_number_widget(cls.NumberWidget, *args, **kwargs)

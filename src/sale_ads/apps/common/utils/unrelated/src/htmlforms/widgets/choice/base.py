from django.utils.html import conditional_escape


class ChoiceWidgetLibMixin:
    class ContextMixin:
        items = (
            "choice_label",
            "choice_value",
            "choices",
            "chosen",
            "safe_choice_value",
            "safe_choices",
            "string_choice_value",
            "string_value",
        )

        def compute_choices(self):
            if not self.is_inherited("field"):
                if self.field:
                    choices = getattr(self.field.field, "choices", None)
                    return tuple(choices) if choices is not None else None
                return None
            raise self.ItemComputationFailed

        def compute_chosen(self):
            if not self.is_inherited("choice_value") or not self.is_inherited("value"):
                if self.choice_value is not None and self.value is not None:
                    return (
                        self.string_choice_value == self.string_value
                        if not self.multi_choice
                        else self.string_choice_value in self.string_value
                    )
                return None
            raise self.ItemComputationFailed

        def clean_chosen(self, value):
            return self.clean_bool(value)

        def compute_safe_choice_value(self):
            if not self.is_inherited("choice_value"):
                return (
                    conditional_escape(self.choice_value)
                    if self.choice_value is not None
                    else None
                )
            raise self.ItemComputationFailed

        def compute_safe_choices(self):
            if not self.is_inherited("choices"):
                if self.choices is not None:
                    return tuple(
                        (conditional_escape(left), right)
                        if not isinstance(right, (list, tuple))
                        else (
                            left,
                            tuple(
                                (conditional_escape(nested_value), nested_label)
                                for nested_value, nested_label in right
                            ),
                        )
                        for left, right in self.choices
                    )
                return None
            raise self.ItemComputationFailed

        def compute_string_choice_value(self):
            if not self.is_inherited("choice_value"):
                return (
                    str(self.safe_choice_value)
                    if self.choice_value is not None
                    else None
                )
            raise self.ItemComputationFailed

        def compute_string_value(self):
            if not self.is_inherited("value"):
                if self.value is not None:
                    return (
                        str(self.safe_value)
                        if not self.multi_choice
                        else tuple(map(str, self.safe_value))
                    )
                return None
            raise self.ItemComputationFailed

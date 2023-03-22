from django.template import Library

from htmlforms import HTMLFormsLib

register = Library()


_base_lib = HTMLFormsLib


class _CustomHTMLFormsLib(_base_lib):
    class WidgetMixin(_base_lib.WidgetMixin):
        default_css_class = "widget"
        default_invalid_css_class = "widget-invalid"

    class FlagWidgetMixin(_base_lib.FlagWidgetMixin):
        default_css_class = "flag-widget"
        default_invalid_css_class = "flag-widget-invalid"

    class FlagWidgetLabelMixin(_base_lib.FlagWidgetLabelMixin):
        default_css_class = "flag-widget-label"

    class LabeledFlagWidgetMixin(_base_lib.LabeledFlagWidgetMixin):
        default_css_class = "flag-widget-block"

    class FlagWidgetListMixin(_base_lib.FlagWidgetListMixin):
        default_css_class = "flag-widget-list"

    class SelectWidgetMixin(_base_lib.SelectWidgetMixin):
        default_css_class = "select"

    class FieldLabelMixin(_base_lib.FieldLabelMixin):
        default_css_class = "field-label"
        default_required_mark = "*"

    class FieldErrorMixin(_base_lib.FieldErrorMixin):
        default_css_class = "field-error"

    class FieldMixin(_base_lib.FieldMixin):
        default_css_class = "field"

    class FormErrorListMixin(_base_lib.FormErrorListMixin):
        tag = "ul"
        default_css_class = "form-error-list"

    class FormErrorMixin(_base_lib.FormErrorMixin):
        tag = "li"


_CustomHTMLFormsLib.update_register(register)

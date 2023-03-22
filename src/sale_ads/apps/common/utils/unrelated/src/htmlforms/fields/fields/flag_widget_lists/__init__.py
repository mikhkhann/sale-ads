from htmlforms.fields.fields.flag_widget_lists.base import FlagWidgetListFieldLibMixin
from htmlforms.fields.fields.flag_widget_lists.checkbox import CheckboxListFieldLibMixin
from htmlforms.fields.fields.flag_widget_lists.radio import RadioListFieldLibMixin

FLAG_WIDGET_LIST_FIELD_LIB_MIXINS = (
    CheckboxListFieldLibMixin,
    FlagWidgetListFieldLibMixin,
    RadioListFieldLibMixin,
)

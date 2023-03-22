from htmlforms.widgets.choice.flag.boolean.basic import BooleanWidgetLibMixin
from htmlforms.widgets.choice.flag.boolean.label import BooleanWidgetLabelLibMixin
from htmlforms.widgets.choice.flag.boolean.labeled import LabeledBooleanWidgetLibMixin

BOOLEAN_WIDGET_LIB_MIXINS = (
    BooleanWidgetLabelLibMixin,
    BooleanWidgetLibMixin,
    LabeledBooleanWidgetLibMixin,
)

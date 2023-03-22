from htmlforms.widgets.choice.flag.labeled.base import LabeledFlagWidgetLibMixin
from htmlforms.widgets.choice.flag.labeled.checkbox import LabeledCheckboxWidgetLibMixin
from htmlforms.widgets.choice.flag.labeled.labels import FLAG_WIDGET_LABEL_LIB_MIXINS
from htmlforms.widgets.choice.flag.labeled.radio import LabeledRadioWidgetLibMixin

LABELED_WIDGET_LIB_MIXINS = (
    *FLAG_WIDGET_LABEL_LIB_MIXINS,
    LabeledCheckboxWidgetLibMixin,
    LabeledFlagWidgetLibMixin,
    LabeledRadioWidgetLibMixin,
)

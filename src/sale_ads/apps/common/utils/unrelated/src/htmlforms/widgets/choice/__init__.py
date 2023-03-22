from htmlforms.widgets.choice.base import ChoiceWidgetLibMixin
from htmlforms.widgets.choice.flag import FLAG_WIDGET_LIB_MIXINS
from htmlforms.widgets.choice.select import SELECT_WIDGET_LIB_MIXINS

CHOICE_WIDGET_LIB_MIXINS = (
    *FLAG_WIDGET_LIB_MIXINS,
    *SELECT_WIDGET_LIB_MIXINS,
    ChoiceWidgetLibMixin,
)

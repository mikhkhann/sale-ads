from htmlforms.widgets.choice.flag.basic import BASIC_FLAG_WIDGET_LIB_MIXINS
from htmlforms.widgets.choice.flag.boolean import BOOLEAN_WIDGET_LIB_MIXINS
from htmlforms.widgets.choice.flag.labeled import LABELED_WIDGET_LIB_MIXINS
from htmlforms.widgets.choice.flag.lists import FLAG_WIDGET_LIST_LIB_MIXINS

FLAG_WIDGET_LIB_MIXINS = (
    *BASIC_FLAG_WIDGET_LIB_MIXINS,
    *BOOLEAN_WIDGET_LIB_MIXINS,
    *FLAG_WIDGET_LIST_LIB_MIXINS,
    *LABELED_WIDGET_LIB_MIXINS,
)

from htmlforms.widgets.file.clearable.removal_subwidget import (
    FILE_REMOVAL_SUBWIDGET_LIB_MIXINS,
)
from htmlforms.widgets.file.clearable.widget import ClearableFileWidgetLibMixin

CLEARABLE_FILE_WIDGET_LIB_MIXINS = (
    *FILE_REMOVAL_SUBWIDGET_LIB_MIXINS,
    ClearableFileWidgetLibMixin,
)

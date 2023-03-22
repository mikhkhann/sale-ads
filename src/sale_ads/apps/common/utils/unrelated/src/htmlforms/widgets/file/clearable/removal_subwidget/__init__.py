from htmlforms.widgets.file.clearable.removal_subwidget.basic import (
    FileRemovalSubwidgetLibMixin,
)
from htmlforms.widgets.file.clearable.removal_subwidget.label import (
    FileRemovalSubwidgetLabelLibMixin,
)
from htmlforms.widgets.file.clearable.removal_subwidget.labeled import (
    LabeledFileRemovalSubwidgetLibMixin,
)

FILE_REMOVAL_SUBWIDGET_LIB_MIXINS = (
    FileRemovalSubwidgetLibMixin,
    FileRemovalSubwidgetLabelLibMixin,
    LabeledFileRemovalSubwidgetLibMixin,
)

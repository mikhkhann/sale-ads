from htmlforms.fields.errors import FIELD_ERROR_LIB_MIXINS
from htmlforms.fields.fields import FIELD_ELEMENT_LIB_MIXINS
from htmlforms.fields.label import FieldLabelLibMixin

FIELD_LIB_MIXINS = (
    *FIELD_ELEMENT_LIB_MIXINS,
    *FIELD_ERROR_LIB_MIXINS,
    FieldLabelLibMixin,
)

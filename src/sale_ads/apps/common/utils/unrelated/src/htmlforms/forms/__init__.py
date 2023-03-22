from htmlforms.forms.base import FormLibMixin
from htmlforms.forms.errors import FORM_ERROR_LIB_MIXINS
from htmlforms.forms.hidden_fields import HiddenFieldListLibMixin

FORM_LIB_MIXINS = (*FORM_ERROR_LIB_MIXINS, FormLibMixin, HiddenFieldListLibMixin)

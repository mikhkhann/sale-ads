from htmlforms.fields.fields.base import FieldLibMixin
from htmlforms.fields.fields.boolean import BooleanFieldLibMixin
from htmlforms.fields.fields.email import EmailFieldLibMixin
from htmlforms.fields.fields.file import FileFieldLibMixin
from htmlforms.fields.fields.flag_widget_lists import FLAG_WIDGET_LIST_FIELD_LIB_MIXINS
from htmlforms.fields.fields.number import NumberFieldLibMixin
from htmlforms.fields.fields.password import PasswordFieldLibMixin
from htmlforms.fields.fields.search import SearchFieldLibMixin
from htmlforms.fields.fields.select import SelectFieldLibMixin
from htmlforms.fields.fields.text import TextFieldLibMixin
from htmlforms.fields.fields.textarea import TextAreaFieldLibMixin

FIELD_ELEMENT_LIB_MIXINS = (
    *FLAG_WIDGET_LIST_FIELD_LIB_MIXINS,
    BooleanFieldLibMixin,
    EmailFieldLibMixin,
    FileFieldLibMixin,
    NumberFieldLibMixin,
    FieldLibMixin,
    PasswordFieldLibMixin,
    SearchFieldLibMixin,
    SelectFieldLibMixin,
    TextAreaFieldLibMixin,
    TextFieldLibMixin,
)

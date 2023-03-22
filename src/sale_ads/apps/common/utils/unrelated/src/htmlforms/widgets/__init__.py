from htmlforms.widgets.base import WidgetLibMixin
from htmlforms.widgets.choice import CHOICE_WIDGET_LIB_MIXINS
from htmlforms.widgets.email import EmailWidgetLibMixin
from htmlforms.widgets.file import FILE_WIDGET_LIB_MIXINS
from htmlforms.widgets.number import NumberWidgetLibMixin
from htmlforms.widgets.password import PasswordWidgetLibMixin
from htmlforms.widgets.search import SearchWidgetLibMixin
from htmlforms.widgets.text import TextWidgetLibMixin
from htmlforms.widgets.textarea import TextAreaWidgetLibMixin

WIDGET_LIB_MIXINS = (
    *CHOICE_WIDGET_LIB_MIXINS,
    *FILE_WIDGET_LIB_MIXINS,
    EmailWidgetLibMixin,
    NumberWidgetLibMixin,
    PasswordWidgetLibMixin,
    SearchWidgetLibMixin,
    TextAreaWidgetLibMixin,
    TextWidgetLibMixin,
    WidgetLibMixin,
)

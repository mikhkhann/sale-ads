from django.template import Library

register = Library()


@register.filter("not")
def not_(value):
    return not value


@register.filter("bool")
def bool_(value):
    return bool(value)

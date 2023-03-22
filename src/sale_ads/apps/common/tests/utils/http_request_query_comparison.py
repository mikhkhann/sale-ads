from collections.abc import Container


def unify_http_request_query_for_comparison(query, **kwargs):
    items = query.items() if hasattr(query, "items") else query
    return {
        name: unify_http_request_parameter_for_comparison(value, **kwargs)
        for name, value in items
    }


def unify_http_request_parameter_for_comparison(
    value,
    *,
    is_multi_value=lambda value: (
        isinstance(value, Container) and not isinstance(value, str)
    ),
    unify_multi_value=list,
    unify=lambda value: value
):
    if is_multi_value(value):
        if len(value) == 1:
            (value,) = value
            value = str(value)
        elif not len(value):
            value = None
        else:
            value = unify_multi_value(map(str, map(unify, value)))
    elif value is not None:
        value = str(unify(value))
    return value


class HTTPRequestQueryTestMixin:
    def assertHTTPRequestQueryEqual(self, first, second, msg=None, **kwargs):
        first, second = [
            unify_http_request_query_for_comparison(value, **kwargs)
            for value in [first, second]
        ]
        self.assertEqual(first, second, msg)

    def assertHTTPRequestParameterEqual(self, first, second, msg=None, **kwargs):
        first, second = [
            unify_http_request_parameter_for_comparison(value, **kwargs)
            for value in [first, second]
        ]
        self.assertEqual(first, second, msg)

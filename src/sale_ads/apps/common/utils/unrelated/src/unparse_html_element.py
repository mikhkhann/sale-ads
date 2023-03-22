from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


def unparse_html_element(name, attrs=None, content=None, *, close=True):
    """
    Example:

    >>> from django.utils.html import escape
    >>> from django.utils.safestring import SafeString
    >>>
    >>>
    >>> result = unparse_html_element(
    ...     "spam", {"a": "ham", "b": 1, "c": None}, "eggs"
    ... )
    >>>
    >>> result
    '<spam a="ham" b="1" c>eggs</spam>'
    >>>
    >>> isinstance(result, SafeString)
    True
    >>>
    >>>
    >>> # ==========================================================
    >>> # Unclosed
    >>>
    >>> result = unparse_html_element("spam", close=False)
    >>>
    >>> result
    '<spam>'
    >>>
    >>> isinstance(result, SafeString)
    True
    >>>
    >>>
    >>> # ==========================================================
    >>> # Escaping
    >>>
    >>>
    >>> # --------------------------------------
    >>> # Unsafe
    >>>
    >>> result = unparse_html_element("spam", {"ham": "&"}, "&")
    >>>
    >>> result
    '<spam ham="&amp;">&amp;</spam>'
    >>>
    >>> isinstance(result, SafeString)
    True
    >>>
    >>>
    >>> # --------------------------------------
    >>> # Safe
    >>>
    >>> result = unparse_html_element(
    ...     "spam", {"ham": mark_safe("&")}, mark_safe("&")
    ... )
    >>>
    >>> result
    '<spam ham="&">&</spam>'
    >>>
    >>> isinstance(result, SafeString)
    True
    """
    if attrs is None:
        attrs = {}
    escaped_element = _unparse_and_escape_start_tag(name, attrs)
    if close:
        if content is not None:
            escaped_element += conditional_escape(content)
        escaped_element += f"</{name}>"
    return mark_safe(escaped_element)


def _unparse_and_escape_start_tag(name, attrs):
    escaped_tag_content = name
    escaped_attr_string = _unparse_and_escape_attrs(attrs)
    if escaped_attr_string:
        escaped_tag_content += " " + escaped_attr_string
    return f"<{escaped_tag_content}>"


def _unparse_and_escape_attrs(attrs):
    escaped_substrings = []
    for name, value in attrs.items():
        escaped_substring = name
        if value is not None:
            escaped_substring += f'="{conditional_escape(value)}"'
        escaped_substrings.append(escaped_substring)
    return str.join(" ", escaped_substrings)
